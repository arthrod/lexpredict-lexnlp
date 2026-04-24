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
        """
        Initialize the RegulationsParser and prepare trigger phrases and compiled start-trigger regexes.

        Parameters:
            regulations_dataframe (DataFrame | None): Optional DataFrame containing trigger rows to use as the source for trigger phrases; if omitted, the parser will load the default Portuguese trigger CSV.
        """
        self.regulations_dataframe = regulations_dataframe
        self.start_triggers: list[str] = []
        self.reg_start_triggers: list[Pattern] = []
        self.load_trigger_words()
        self.setup_regexes()

    # --- initial setup -------------------------------------------------

    def setup_regexes(self) -> None:
        """
        Compile and store regex patterns that detect configured regulation start triggers.

        If no start triggers are configured, sets `self.reg_start_triggers` to an empty list.
        Otherwise, orders triggers from longest to shortest, escapes them for safe inclusion in a pattern,
        and stores a single compiled regex (as a one-element list in `self.reg_start_triggers`)
        that matches a trigger when preceded by whitespace or start-of-string and captures the trigger
        plus following contiguous text up to common delimiters (comma, semicolon, period, or newline).
        """
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
        """
        Populate the parser's start_triggers list from the provided DataFrame or, if none was provided, from the module's default pt-BR CSV.

        If no DataFrame was supplied at construction, the function loads lexnlp/config/pt/pt_regulations.csv (UTF-8) and expects rows with "trigger" and "position" columns; it selects and stores the "trigger" values whose "position" equals "start" in self.start_triggers. Malformed CSV lines are skipped.
        """
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
    def _annotate(
        name: str, coords: tuple[int, int], surface: str, locale: str, country: str = "Brazil"
    ) -> RegulationAnnotation:
        """
        Create a RegulationAnnotation for a matched regulation fragment.

        Parameters:
            name (str): Canonical label for the regulation (e.g., act name or trigger phrase).
            coords (tuple[int, int]): Start and end character offsets of the match in the source text.
            surface (str): Exact matched text to store in the annotation's `text` field.
            locale (str): Locale or language code associated with the source text (e.g., "pt").
            country (str): Country associated with the regulation; defaults to "Brazil".

        Returns:
            RegulationAnnotation: Annotation populated with the provided name, coords, text, locale, and country.
        """
        return RegulationAnnotation(
            name=name,
            coords=coords,
            text=surface,
            locale=locale,
            country=country,
        )

    def _parse_trigger_phrases(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        """
        Find configured start-trigger phrases in the text and yield a RegulationAnnotation for each match.

        Parameters:
            text (str): Text to scan for start-trigger phrases.
            locale (str): Locale identifier to assign to each produced annotation.

        Returns:
            Generator[RegulationAnnotation]: Yields annotations whose `name` and `text` are the matched surface string, `coords` are the match span (start, end), and `locale` is the provided value.
        """
        for reg in self.reg_start_triggers:
            for match in reg.finditer(text):
                surface = match.group()
                yield self._annotate(surface, match.span(), surface, locale)

    def _parse_formal_citations(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        """
        Extract formal Brazilian act citations and yield RegulationAnnotation objects for each match.

        Each yielded annotation has its `name` and `text` set to the matched citation surface, `coords` set to the match span, and `locale` set to the provided locale.

        Parameters:
            text (str): Input text to scan for formal citations.
            locale (str): Locale identifier to attach to produced annotations (e.g., "pt").

        Returns:
            Generator[RegulationAnnotation]: Yields a RegulationAnnotation for each formal citation found in `text`.
        """
        for match in FORMAL_CITATION_RE.finditer(text):
            surface = match.group("full")
            yield self._annotate(surface, match.span("full"), surface, locale)

    def _parse_article_references(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        """
        Extracts article-style references from text and yields a RegulationAnnotation for each match.

        Parameters:
            text (str): Text to search for article references (for example, "art. 5º" or "§ 2º do art. 12").
            locale (str): Locale tag to set on each produced annotation.

        Returns:
            Generator[RegulationAnnotation]: An iterator yielding annotations whose `name` and `text` are the exact matched surface and whose `coords` span the match.
        """
        for match in ARTICLE_REFERENCE_RE.finditer(text):
            surface = match.group("full")
            # art references by themselves are so common we lower-case normalise
            yield self._annotate(surface, match.span("full"), surface, locale)

    def _parse_constitutional(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        """
        Emit annotations for Brazilian constitutional references normalized to the canonical name "Constituição Federal".

        Scans `text` for constitutional reference patterns and yields a RegulationAnnotation for each match.

        Parameters:
                text (str): Text to scan for constitutional references.
                locale (str): Locale label to attach to produced annotations.

        Returns:
                Generator[RegulationAnnotation]: Yields one annotation per match with `name` set to "Constituição Federal", `coords` set to the match span, and `text` set to the matched surface form.
        """
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
        """
        Produce RegulationAnnotation objects for regulatory references found in Portuguese (Brazilian) legal text.

        Emits annotations in this order: trigger-word phrases, formal act citations, article references, constitutional references.

        Parameters:
            text (str): Text to scan for regulatory references.
            locale (str): Locale tag placed on each annotation's `locale` field (default "pt").

        Returns:
            Generator[RegulationAnnotation]: An iterator of RegulationAnnotation objects for each match.
        """
        yield from self._parse_trigger_phrases(text, locale)
        yield from self._parse_formal_citations(text, locale)
        yield from self._parse_article_references(text, locale)
        yield from self._parse_constitutional(text, locale)


parser = RegulationsParser()


def get_regulation_annotations(text: str, language: str = "pt") -> Generator[RegulationAnnotation]:
    """
    Yield annotations for each regulation reference found in the text.

    Parameters:
        language (str): Locale code used to select parsing rules (for example, "pt").

    Returns:
        Each yielded RegulationAnnotation corresponds to a detected regulation reference.
    """
    yield from parser.parse(text, language)


def get_regulation_annotation_list(text: str, language: str = "pt") -> list[RegulationAnnotation]:
    """
    Extract regulation references from the given text and return them as a list of RegulationAnnotation objects.

    Parameters:
        text (str): Text to scan for regulation references.
        language (str): Locale/language code used to select parsing rules (default: "pt").

    Returns:
        list[RegulationAnnotation]: List of annotations, one per detected regulation reference.
    """
    return list(parser.parse(text, language))


def get_regulations(text: str, language: str = "pt") -> Generator[dict]:
    """
    Yield regulation annotations extracted from text as dictionaries.

    Parameters:
        text (str): Text to scan for regulation references.
        language (str): Locale code used by the parser (default "pt").

    Returns:
        dict: A dictionary for each RegulationAnnotation produced from the input text.
    """
    for reg in parser.parse(text, language):
        yield reg.to_dictionary()


def get_regulation_list(text: str, language: str | None = None) -> list[dict]:
    """
    Return regulation annotations as dictionaries extracted from the input text.

    Parameters:
        text (str): Text to scan for regulation references.
        language (str | None): Language code for parsing; when None, defaults to "pt" (Portuguese/Brazil).

    Returns:
        list[dict]: A list of dictionaries where each dictionary represents a regulation annotation with keys for `name`, `text`, `locale`, `country`, and `coords` (start and end offsets).
    """
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
