"""Regulation extraction for Portuguese (pt-BR).

Recognises Brazilian legal and administrative references:

- Named acts / norms via a curated trigger list from
  ``lexnlp/config/pt/pt_regulations.csv`` ("Lei nº ...", "Decreto ...",
  "Resolução ...", "Ministério ...").
- Formal Brazilian citation of federal norms in the format
  ``Lei nº 12.527, de 18 de novembro de 2011`` / ``Decreto-Lei nº 4.657/1942``.
- Article references such as ``art. 5º, inciso XXXIII`` and
  ``§ 2º do art. 12``.
- Constitutional references (``art. 5º da Constituição Federal``) produce a
  dedicated ``country='Brazil'`` annotation with the act name set to
  "Constituição Federal".
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import os
from collections.abc import Generator
from re import Pattern

import regex as re
from pandas import DataFrame, read_csv

from lexnlp.extract.common.annotations.regulation_annotation import RegulationAnnotation
from lexnlp.extract.common.base_path import lexnlp_base_path

# --- formal Brazilian citation patterns -------------------------------------------------
# "Lei nº 12.527, de 18 de novembro de 2011"
# "Lei Complementar nº 101/2000"
# "Decreto-Lei nº 4.657, de 4 de setembro de 1942"
# "Medida Provisória nº 1.040/2021"
_ACT_TYPE_RE = (
    r"(?:"
    r"Lei(?:\s+Complementar|\s+Orgânica|\s+Delegada|\s+Ordinária)?|"
    r"Decreto(?:-Lei|\s+Legislativo)?|"
    r"Medida\s+Provisória|"
    r"Emenda\s+Constitucional|"
    r"Resolução(?:\s+Conjunta)?|"
    r"Portaria(?:\s+Interministerial|\s+Normativa)?|"
    r"Instrução\s+Normativa|"
    r"Ato\s+Normativo|"
    r"Provimento|"
    r"Súmula(?:\s+Vinculante)?|"
    r"Circular|"
    r"Deliberação"
    r")"
)
FORMAL_CITATION_RE = re.compile(
    rf"(?P<full>{_ACT_TYPE_RE}\s+"
    r"(?:nº|n\.º|n°|n\.\s*[º°]|no\.|n\s+o\s*)?\s*"
    r"(?P<number>\d{1,3}(?:\.\d{3})*)"
    r"(?:[/,-]?\s*(?P<year>\d{4}))?"
    r"(?:\s*,?\s*de\s+\d{1,2}\s+de\s+\p{L}+\s+de\s+\d{4})?)",
    re.UNICODE | re.IGNORECASE,
)

# "art. 5º", "artigo 1º-A", "§ 2º", "inciso II do art. 14"
ARTICLE_REFERENCE_RE = re.compile(
    r"(?P<full>(?:art\.?|artigo)\s*"
    r"(?P<number>\d+(?:[ºª°]|-[A-Z])?)"
    r"(?:\s*,\s*(?:§|parágrafo)\s*(?P<para>\d+[ºª°]?|único))?"
    r"(?:\s*,\s*inciso\s*(?P<inc>[IVXLCDM]+))?"
    r"(?:\s*,\s*alínea\s*[\"']?(?P<alinea>[a-z])[\"']?)?)",
    re.UNICODE | re.IGNORECASE,
)

# Constitutional references: "Constituição Federal", "CF/88", "CRFB", "CRFB/88"
CONSTITUTIONAL_REF_RE = re.compile(
    r"(?P<full>Constituição\s+(?:Federal|da\s+República(?:\s+Federativa\s+do\s+Brasil)?)|"
    r"CRFB(?:/\d{2,4})?|CF(?:/\d{2,4})?)",
    re.UNICODE,
)


class RegulationsParser:
    """Parses Portuguese (Brazilian) legal references.

    ``parse()`` yields :class:`RegulationAnnotation` objects for:

    1. Trigger-word phrases listed in ``lexnlp/config/pt/pt_regulations.csv``
       (backwards-compatible with the Spanish baseline).
    2. Formal Brazilian act citations (``Lei nº 12.527/2011``,
       ``Decreto-Lei nº 4.657/1942``).
    3. Article references (``art. 5º``, ``§ 2º do art. 12``).
    4. Constitutional references (``Constituição Federal``, ``CF/88``).
    """

    DEFAULT_COUNTRY = "Brazil"

    def __init__(self, regulations_dataframe: DataFrame | None = None):
        self.regulations_dataframe = regulations_dataframe
        self.start_triggers: list[str] = []
        self.reg_start_triggers: list[Pattern] = []
        self.load_trigger_words()
        self.setup_regexes()

    # --- initial setup -------------------------------------------------

    def setup_regexes(self) -> None:
        """Build a combined regex alternation from the loaded trigger words."""
        if not self.start_triggers:
            self.reg_start_triggers = []
            return
        # Sort long-to-short so e.g. "lei complementar" matches before "lei".
        triggers_ordered = sorted(self.start_triggers, key=len, reverse=True)
        triggers_escaped = [re.escape(t) for t in triggers_ordered]
        triggers_str = "|".join(triggers_escaped)
        pattern = re.compile(
            rf"(?:(?<=[\s\b])|(?<=^))({triggers_str})[^,\b;\.\n]+",
            re.UNICODE | re.IGNORECASE,
        )
        self.reg_start_triggers = [pattern]

    def load_trigger_words(self) -> None:
        dtypes = {"trigger": str, "position": str}
        if self.regulations_dataframe is None:
            path = os.path.join(lexnlp_base_path, "lexnlp/config/pt/pt_regulations.csv")
            self.regulations_dataframe = read_csv(
                path,
                encoding="utf-8",
                on_bad_lines="skip",
                converters=dtypes,
            )
        subset = self.regulations_dataframe[["trigger", "position"]]
        tuples = [tuple(x) for x in subset.values]
        self.start_triggers = [t[0] for t in tuples if t[1] == "start"]

    # --- extraction helpers --------------------------------------------

    @staticmethod
    def _annotate(name: str, coords: tuple[int, int], surface: str, locale: str,
                  country: str = "Brazil") -> RegulationAnnotation:
        return RegulationAnnotation(
            name=name,
            coords=coords,
            text=surface,
            locale=locale,
            country=country,
        )

    def _parse_trigger_phrases(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        for reg in self.reg_start_triggers:
            for match in reg.finditer(text):
                surface = match.group()
                yield self._annotate(surface, match.span(), surface, locale)

    def _parse_formal_citations(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        for match in FORMAL_CITATION_RE.finditer(text):
            surface = match.group("full")
            yield self._annotate(surface, match.span("full"), surface, locale)

    def _parse_article_references(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        for match in ARTICLE_REFERENCE_RE.finditer(text):
            surface = match.group("full")
            # art references by themselves are so common we lower-case normalise
            yield self._annotate(surface, match.span("full"), surface, locale)

    def _parse_constitutional(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        for match in CONSTITUTIONAL_REF_RE.finditer(text):
            surface = match.group("full")
            yield self._annotate(
                "Constituição Federal",
                match.span("full"),
                surface,
                locale,
            )

    # --- public API ----------------------------------------------------

    def parse(self, text: str, locale: str = "pt") -> Generator[RegulationAnnotation]:
        yield from self._parse_trigger_phrases(text, locale)
        yield from self._parse_formal_citations(text, locale)
        yield from self._parse_article_references(text, locale)
        yield from self._parse_constitutional(text, locale)


parser = RegulationsParser()


def get_regulation_annotations(text: str, language: str = "pt") -> Generator[RegulationAnnotation]:
    yield from parser.parse(text, language)


def get_regulation_annotation_list(text: str, language: str = "pt") -> list[RegulationAnnotation]:
    return list(parser.parse(text, language))


def get_regulations(text: str, language: str = "pt") -> Generator[dict]:
    """Yield regulation annotations as plain dicts."""
    for reg in parser.parse(text, language):
        yield reg.to_dictionary()


def get_regulation_list(text: str, language: str | None = None) -> list[dict]:
    return list(get_regulations(text, language or "pt"))


__all__ = [
    "ARTICLE_REFERENCE_RE",
    "CONSTITUTIONAL_REF_RE",
    "FORMAL_CITATION_RE",
    "RegulationsParser",
    "get_regulation_annotation_list",
    "get_regulation_annotations",
    "get_regulation_list",
    "get_regulations",
    "parser",
]
