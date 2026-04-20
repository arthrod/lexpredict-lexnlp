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
    Extracts court dictionary matches from the given text using the provided dictionary entries.

    This function is deprecated and emits a DeprecationWarning when called.
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
    ptrs = ParserInitParams()
    ptrs.dataframe_paths = [os.path.join(lexnlp_base_path, 'lexnlp/config/pt/pt_courts.csv')]
    ptrs.split_ptrs = LineSplitParams()
    ptrs.split_ptrs.line_breaks = {'\n', '.', ';', ','}.union(set(PtLanguageTokens.conjunctions))
    ptrs.split_ptrs.abbreviations = PtLanguageTokens.abbreviations
    ptrs.split_ptrs.abbr_ignore_case = True
    ptrs.court_pattern_checker = re.compile(r'tribunal|juízo|vara', re.IGNORECASE)
    return UniversalCourtsParser(ptrs)


parser = setup_pt_parser()


def get_court_annotations(text: str, language: str = 'pt') -> Generator[CourtAnnotation]:
    yield from parser.parse(text, language)


def get_court_annotation_list(text: str, language: str = 'pt') -> list[CourtAnnotation]:
    return list(get_court_annotations(text, language))


def get_courts(text: str, language: str = 'pt') -> Generator[dict]:
    for court_annotation in parser.parse(text, language):
        yield court_annotation.to_dictionary()


def get_court_list(text: str, language: str = 'pt') -> list[CourtAnnotation]:
    return list(parser.parse(text, language))
