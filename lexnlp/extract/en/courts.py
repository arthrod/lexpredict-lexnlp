"""Court extraction for English.

This module implements extraction functionality for courts in English, including formal names, abbreviations,
and aliases.

Todo:
  * Add utilities for loading court data
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

from lexnlp.extract.all_locales.languages import LANG_EN
from lexnlp.extract.common.annotations.court_annotation import CourtAnnotation
from lexnlp.extract.common.base_path import lexnlp_base_path
from lexnlp.extract.common.universal_court_parser import ParserInitParams, UniversalCourtsParser
from lexnlp.extract.en.dict_entities import (
    DictionaryEntry,
    DictionaryEntryAlias,
    conflicts_take_first_by_id,
    find_dict_entities,
)
from lexnlp.extract.en.en_language_tokens import EnLanguageTokens
from lexnlp.utils.lines_processing.line_processor import LineSplitParams


def _get_courts(
    text: str,
    court_config_list: list[DictionaryEntry],
    priority: bool = False,
    text_languages: list[str] | None = None,
    simplified_normalization: bool = False,
) -> Generator[tuple[DictionaryEntry, DictionaryEntryAlias], Any, Any]:
    """
    Searches the text for court entries defined in the provided configuration and yields matching dictionary entries.

    This function is deprecated and emits a DeprecationWarning when called.

    Parameters:
        text (str): Source text to search for court names and aliases.
        court_config_list (list[DictionaryEntry]): List of court definitions to match against. Each entry should be a dictionary-style
            court record (id, name, aliases).
        priority (bool): If True, resolves exact-match conflicts by selecting the entry with the lowest id.
        text_languages (list[str] | None): If provided, restricts matching to aliases in these language(s).
        simplified_normalization (bool): If True, skip heavier NLP normalization and use a simpler text normalization.

    Returns:
        Generator[DictionaryEntry, Any, Any]: Yields matched court dictionary entries found in the text.
    """
    warnings.warn("This function will be removed in a future version of LexNLP", DeprecationWarning)
    for ent in find_dict_entities(
        text,
        court_config_list,
        default_language=LANG_EN.code,
        conflict_resolving_func=conflicts_take_first_by_id if priority else None,
        text_languages=text_languages,
        simplified_normalization=simplified_normalization,
    ):
        yield ent.entity


def setup_en_parser():
    ptrs = ParserInitParams()
    file_path = os.path.join(lexnlp_base_path, "lexnlp/config/en")
    ptrs.dataframe_paths = ["us_state_courts.csv", "us_courts.csv", "ca_courts.csv", "au_courts.csv"]
    ptrs.dataframe_paths = [os.path.join(file_path, p) for p in ptrs.dataframe_paths]

    ptrs.split_ptrs = LineSplitParams()
    ptrs.split_ptrs.line_breaks = {"\n", ".", ";", ","}.union(set(EnLanguageTokens.conjunctions))
    ptrs.split_ptrs.abbreviations = EnLanguageTokens.abbreviations
    ptrs.split_ptrs.abbr_ignore_case = True
    ptrs.court_pattern_checker = re.compile("court", re.IGNORECASE)
    return UniversalCourtsParser(ptrs)


parser = setup_en_parser()


def get_court_annotations(text: str, language: str = "en") -> Generator[CourtAnnotation]:
    yield from parser.parse(text, language)


def get_court_annotation_list(text: str, language: str = "en") -> list[CourtAnnotation]:
    return list(parser.parse(text, language))


def get_courts(text: str, language: str = "en") -> Generator[dict]:
    for court_annotation in parser.parse(text, language):
        yield court_annotation.to_dictionary()


def get_court_list(text: str, language: str = "en") -> list[CourtAnnotation]:
    return list(parser.parse(text, language))
