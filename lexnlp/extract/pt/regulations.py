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
        Initialize the RegulationsParser and prepare trigger phrases and compiled regexes.
        
        Parameters:
            regulations_dataframe (pandas.DataFrame | None): Optional DataFrame containing regulation trigger rows.
                If provided, it will be used as the source of trigger phrases; if omitted, the parser will load
                the default Portuguese trigger CSV during initialization.
        """
        self.regulations_dataframe = regulations_dataframe
        self.start_triggers: list[str] = []
        self.reg_start_triggers: list[Pattern] = []
        self.load_trigger_words()
        self.setup_regexes()

    # --- initial setup -------------------------------------------------

    def setup_regexes(self) -> None:
        """
        Prepare and store compiled regex patterns that match configured regulation start trigger phrases.
        
        If no start triggers are configured, sets `reg_start_triggers` to an empty list. Otherwise compiles a single regex (stored as a one-element list in `reg_start_triggers`) that matches any configured trigger (longer triggers are prioritized) when preceded by whitespace or start-of-string and captures the trigger plus following contiguous text up to common delimiters (comma, semicolon, period, newline).
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
        Load regulation trigger phrases into the instance's start_triggers list.
        
        If a DataFrame was provided to the parser instance, use it; otherwise read
        lexnlp/config/pt/pt_regulations.csv (UTF-8) to obtain trigger entries. The
        method selects rows with columns "trigger" and "position" and stores the
        "trigger" values whose "position" equals "start" in self.start_triggers.
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
    def _annotate(name: str, coords: tuple[int, int], surface: str, locale: str,
                  country: str = "Brazil") -> RegulationAnnotation:
        """
                  Create a RegulationAnnotation for a matched regulation fragment.
                  
                  Parameters:
                      name (str): Canonical name or label for the regulation (e.g., matched phrase or act name).
                      coords (tuple[int, int]): Start and end character offsets of the match in the source text.
                      surface (str): Exact matched text (surface form) to include in the annotation's `text` field.
                      locale (str): Locale or language code associated with the source text (e.g., "pt").
                      country (str): Country associated with the regulation; defaults to "Brazil".
                  
                  Returns:
                      RegulationAnnotation: Annotation populated with the provided name, coords, text (surface), locale, and country.
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
        Yield RegulationAnnotation objects for trigger-word phrase matches found in the input text.
        
        Parameters:
            text (str): Text to scan for configured start-trigger phrases.
            locale (str): Locale identifier to assign to each produced annotation.
        
        Returns:
            Generator[RegulationAnnotation]: An iterator yielding an annotation for each matched trigger phrase where the annotation's name and text are the matched surface string and coords are the match span; locale is set to the provided value.
        """
        for reg in self.reg_start_triggers:
            for match in reg.finditer(text):
                surface = match.group()
                yield self._annotate(surface, match.span(), surface, locale)

    def _parse_formal_citations(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        """
        Extract formal Brazilian act citations from `text` and yield corresponding RegulationAnnotation objects.
        
        Each yielded annotation represents a formal citation (e.g., "Lei nº ...") found by the module's citation pattern; the annotation's `name` and `text` are set to the matched citation surface and `coords` to the match span, with `locale` set from the `locale` parameter.
        
        Parameters:
            text (str): Input text to scan for formal citations.
            locale (str): Locale identifier to attach to produced annotations (e.g., "pt").
        
        Returns:
            Generator[RegulationAnnotation]: Yields annotations for each formal citation match.
        """
        for match in FORMAL_CITATION_RE.finditer(text):
            surface = match.group("full")
            yield self._annotate(surface, match.span("full"), surface, locale)

    def _parse_article_references(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        """
        Yield RegulationAnnotation objects for each article reference found in the given text.
        
        Parameters:
            text (str): Input text to search for article references (e.g., "art. 5º", "§ 2º do art. 12").
            locale (str): Locale/language tag to set on produced annotations.
        
        Returns:
            generator (Generator[RegulationAnnotation]): Yields annotations whose `name` and `text` are the matched surface form and whose `coords` span the match.
        """
        for match in ARTICLE_REFERENCE_RE.finditer(text):
            surface = match.group("full")
            # art references by themselves are so common we lower-case normalise
            yield self._annotate(surface, match.span("full"), surface, locale)

    def _parse_constitutional(self, text: str, locale: str) -> Generator[RegulationAnnotation]:
        """
        Yield annotations for matches of Brazilian constitutional references, normalized to the canonical name "Constituição Federal".
        
        Parameters:
            text (str): Text to scan for constitutional references.
            locale (str): Locale label to attach to produced annotations.
        
        Returns:
            Generator[RegulationAnnotation]: An annotation for each match with `name` set to "Constituição Federal", `coords` set to the match span, and `text` set to the matched surface form.
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
        Parse the input text and yield regulation annotations found in Portuguese (Brazilian) legal text.
        
        Parameters:
        	text (str): Text to scan for regulatory references.
        	locale (str): Language/locale tag (default "pt"); affects annotation locale field.
        
        Returns:
        	Generator[RegulationAnnotation]: An iterator of RegulationAnnotation objects for each match. Annotations are emitted in the following order: trigger-word phrases, formal act citations, article references, and constitutional references.
        """
        yield from self._parse_trigger_phrases(text, locale)
        yield from self._parse_formal_citations(text, locale)
        yield from self._parse_article_references(text, locale)
        yield from self._parse_constitutional(text, locale)


parser = RegulationsParser()


def get_regulation_annotations(text: str, language: str = "pt") -> Generator[RegulationAnnotation]:
    """
    Extract regulation annotations from the given text.
    
    Parameters:
        text (str): Text to scan for regulatory references.
        language (str): Language/locale code for parsing rules (default "pt").
    
    Returns:
        Generator[RegulationAnnotation]: An iterator that yields RegulationAnnotation objects for each detected regulation reference.
    """
    yield from parser.parse(text, language)


def get_regulation_annotation_list(text: str, language: str = "pt") -> list[RegulationAnnotation]:
    """
    Produce a list of regulation annotations found in the given text.
    
    Parameters:
        text (str): Input text to scan for regulation references.
        language (str): Language code for parsing rules (default "pt").
    
    Returns:
        list[RegulationAnnotation]: A list of RegulationAnnotation objects for each detected regulation reference.
    """
    return list(parser.parse(text, language))


def get_regulations(text: str, language: str = "pt") -> Generator[dict]:
    """
    Yield regulation annotations found in `text` as dictionaries.
    
    Parameters:
        text (str): Input text to scan for regulation references.
        language (str): Language/locale code used by the parser (default "pt").
    
    Returns:
        Generator[dict]: A generator that yields each RegulationAnnotation serialized to a dictionary via `to_dictionary()`.
    """
    for reg in parser.parse(text, language):
        yield reg.to_dictionary()


def get_regulation_list(text: str, language: str | None = None) -> list[dict]:
    """
    Return a list of regulation annotation dictionaries extracted from the given text.
    
    Parameters:
        text (str): Input text to scan for regulation references.
        language (str | None): Language code for parsing; when None defaults to "pt" (Portuguese/Brazil).
    
    Returns:
        list[dict]: A list of dictionaries produced by calling `to_dictionary()` on each `RegulationAnnotation` found in the text.
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
