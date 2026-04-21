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


# pylint: disable=unused-argument

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
    Yield dictionary matches for courts found in the given text.
    
    Deprecated: emits a DeprecationWarning and will be removed in a future version.
    
    Parameters:
        text (str): Text to search for court entries.
        court_config_list (list[DictionaryEntry]): Dictionary entries and their aliases used to match courts.
        priority (bool): If True, resolve conflicts by taking the first match by identifier.
        text_languages (list[str] | None): Optional list of language codes to restrict matching.
        simplified_normalization (bool): If True, apply simplified normalization during matching.
    
    Returns:
        generator: Yields tuples of (DictionaryEntry, DictionaryEntryAlias) for each matched court.
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
    Configure and return a UniversalCourtsParser tuned for Portuguese court-name extraction.
    
    Sets the parser to use the Portuguese courts dataset, Portuguese-specific line-splitting rules and abbreviation handling, and a case-insensitive keyword pattern for common court-related terms.
    
    Returns:
        UniversalCourtsParser: A parser instance configured for extracting Portuguese (Brazilian) court names and aliases.
    """
    ptrs = ParserInitParams()
    ptrs.dataframe_paths = [os.path.join(lexnlp_base_path, 'lexnlp/config/pt/pt_courts.csv')]
    ptrs.split_ptrs = LineSplitParams()
    # line_breaks is matched character-by-character; only multi-character
    # conjunctions are no-ops there. Single-letter PT conjunctions ("e", "ou")
    # would shatter phrases mid-word, so they are intentionally excluded.
    ptrs.split_ptrs.line_breaks = {'\n', '.', ';', ','}
    ptrs.split_ptrs.abbreviations = PtLanguageTokens.abbreviations
    ptrs.split_ptrs.abbr_ignore_case = True
    ptrs.court_pattern_checker = re.compile(r'tribunal|juízo|vara|turma|câmara|seção|plenário', re.IGNORECASE)
    return UniversalCourtsParser(ptrs)


parser = setup_pt_parser()


def get_court_annotations(text: str, language: str = 'pt') -> Generator[CourtAnnotation]:
    """
    Yield CourtAnnotation objects for court mentions found in the provided text.
    
    Parameters:
        text (str): Text to search for court mentions.
        language (str): ISO language code to guide parsing; defaults to 'pt' (Portuguese).
    
    Returns:
        Generator[CourtAnnotation]: Generator yielding `CourtAnnotation` objects for each detected court mention.
    """
    yield from parser.parse(text, language)


def get_court_annotation_list(text: str, language: str = 'pt') -> list[CourtAnnotation]:
    """
    Return a list of CourtAnnotation objects found in the given text.
    
    Returns:
        list[CourtAnnotation]: Extracted CourtAnnotation objects; empty list if none found.
    """
    return list(get_court_annotations(text, language))


def get_courts(text: str, language: str = 'pt') -> Generator[dict]:
    """
    Generate dictionary representations of court annotations found in the input text.
    
    Parameters:
        text (str): Text to parse for court mentions.
        language (str): Language code used by the parser (defaults to 'pt').
    
    Returns:
        dict: Dictionary representation of a detected court annotation.
    """
    for court_annotation in parser.parse(text, language):
        yield court_annotation.to_dictionary()


def get_court_list(text: str, language: str = 'pt') -> list[CourtAnnotation]:
    """
    Extract court annotations from the given text.
    
    Parameters:
        text (str): Text to parse for court names and aliases.
        language (str): ISO 639-1 language code used to guide parsing (default 'pt').
    
    Returns:
        list[CourtAnnotation]: List of extracted CourtAnnotation objects.
    """
    return list(parser.parse(text, language))
