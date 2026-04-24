"""Court extraction for Portuguese.

This module implements extraction functionality for Brazilian courts, including formal names, abbreviations,
and aliases.

"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


# pylint: disable=unused-argument  # deprecated _get_courts keeps legacy kwargs for API parity

import os
import re
import warnings
from collections.abc import Generator
from typing import Any

from lexnlp.extract.all_locales.languages import LANG_PT
from lexnlp.extract.common.annotations.court_annotation import CourtAnnotation
from lexnlp.extract.common.base_path import lexnlp_base_path
from lexnlp.extract.common.universal_court_parser import ParserInitParams, UniversalCourtsParser
from lexnlp.extract.en.dict_entities import (
    DictionaryEntry,
    DictionaryEntryAlias,
    conflicts_take_first_by_id,
    find_dict_entities,
)
from lexnlp.extract.pt.language_tokens import PtLanguageTokens
from lexnlp.utils.lines_processing.line_processor import LineSplitParams


def _get_courts(
    text: str,
    court_config_list: list[DictionaryEntry],
    priority: bool = False,
    text_languages: list[str] | None = None,
    simplified_normalization: bool = False,
) -> Generator[tuple[DictionaryEntry, DictionaryEntryAlias], Any, Any]:
    """
    Yield tuples of dictionary entries and their matched aliases for court names found in the input text.

    This function is deprecated and emits a DeprecationWarning; it will be removed in a future version.

    Parameters:
        text (str): Text to search for court entries.
        court_config_list (list[DictionaryEntry]): Dictionary entries (with aliases) used for matching courts.
        priority (bool): When True, resolve conflicting matches by taking the first match for an identifier.
        text_languages (list[str] | None): Optional list of language codes to restrict matching.
        simplified_normalization (bool): If True, apply a simplified normalization routine during matching.

    Returns:
        generator: Yields `(DictionaryEntry, DictionaryEntryAlias)` for each matched court.
    """
    warnings.warn("This function will be removed in a future version of LexNLP", DeprecationWarning)
    for ent in find_dict_entities(
        text,
        court_config_list,
        default_language=LANG_PT.code,
        conflict_resolving_func=conflicts_take_first_by_id if priority else None,
        text_languages=text_languages,
        simplified_normalization=simplified_normalization,
    ):
        yield ent.entity


def setup_pt_parser():
    """
    Build a UniversalCourtsParser configured for Portuguese court-name extraction.

    Configures parser initialization parameters to use the Portuguese courts CSV dataset, Portuguese-specific line-splitting rules (line breaks: newline, period, semicolon, comma), case-insensitive abbreviation handling, and a case-insensitive keyword pattern matching common court terms (e.g., tribunal, juízo, vara).

    Returns:
        UniversalCourtsParser: A parser instance configured for extracting Portuguese court names and aliases.
    """
    ptrs = ParserInitParams()
    ptrs.dataframe_paths = [os.path.join(lexnlp_base_path, "lexnlp/config/pt/pt_courts.csv")]
    ptrs.split_ptrs = LineSplitParams()
    # line_breaks is matched character-by-character; only multi-character
    # conjunctions are no-ops there. Single-letter PT conjunctions ("e", "ou")
    # would shatter phrases mid-word, so they are intentionally excluded.
    ptrs.split_ptrs.line_breaks = {"\n", ".", ";", ","}
    ptrs.split_ptrs.abbreviations = PtLanguageTokens.abbreviations
    ptrs.split_ptrs.abbr_ignore_case = True
    ptrs.court_pattern_checker = re.compile(r"tribunal|juízo|vara|turma|câmara|seção|plenário", re.IGNORECASE)
    return UniversalCourtsParser(ptrs)


parser = setup_pt_parser()


def get_court_annotations(text: str, language: str = "pt") -> Generator[CourtAnnotation]:
    """
    Yield CourtAnnotation objects for court mentions found in the provided text.

    Parameters:
        text (str): Text to search for court mentions.
        language (str): ISO language code to guide parsing; defaults to 'pt' (Portuguese).

    Returns:
        Generator[CourtAnnotation]: Generator yielding `CourtAnnotation` objects for each detected court mention.
    """
    yield from parser.parse(text, language)


def get_court_annotation_list(text: str, language: str = "pt") -> list[CourtAnnotation]:
    """
    Collects court annotations from the input text.

    Parameters:
        text (str): Text to analyze for court mentions.
        language (str): Language code to use for parsing (default: 'pt').

    Returns:
        list[CourtAnnotation]: List of extracted CourtAnnotation objects; empty list if none found.
    """
    return list(get_court_annotations(text, language))


def get_courts(text: str, language: str = "pt") -> Generator[dict]:
    """
    Yield dictionary representations of court annotations found in the input text.

    Yields:
        dict: Dictionary representation of each detected court annotation.
    """
    for court_annotation in parser.parse(text, language):
        yield court_annotation.to_dictionary()


def get_court_list(text: str, language: str = "pt") -> list[CourtAnnotation]:
    """
    Extract court annotations from the given text.

    Parameters:
        text (str): Text to parse for court names and aliases.
        language (str): ISO 639-1 language code used to guide parsing (default 'pt').

    Returns:
        list[CourtAnnotation]: List of extracted CourtAnnotation objects.
    """
    return list(parser.parse(text, language))
