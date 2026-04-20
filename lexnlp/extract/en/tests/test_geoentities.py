#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""Geo entity unit tests for English.

This module implements unit tests for the geo entity extraction functionality in English.

"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import os
from collections.abc import Generator
from typing import Any

from lexnlp.extract.common.base_path import lexnlp_test_path
from lexnlp.extract.en.dict_entities import (
    AliasBanRecord,
    DictionaryEntry,
    DictionaryEntryAlias,
    prepare_alias_banlist_dict,
)
from lexnlp.extract.en.geoentities import get_geoentities
from lexnlp.tests import lexnlp_tests


def load_entities_dict():
    """
    Load geo-entity definitions and their aliases from the repository's test CSV files.
    
    This function locates the test CSV files for geo entities and aliases within the test data directory and loads them into DictionaryEntry objects using the library's file loader.
    
    Returns:
        list[DictionaryEntry]: Loaded geo-entity entries, each possibly containing alias records.
    """
    base_path = os.path.join(lexnlp_test_path, "lexnlp/extract/en/tests/test_geoentities")
    entities_fn = os.path.join(base_path, "geoentities.csv")
    aliases_fn = os.path.join(base_path, "geoaliases.csv")
    return DictionaryEntry.load_entities_from_files(entities_fn, aliases_fn)


_CONFIG = list(load_entities_dict())


def get_geoentities_routine(
    text: str,
    geo_config_list: list[DictionaryEntry],
    conflict_resolving_field: str = "none",
    priority_direction: str = "asc",
    text_languages: str | None = None,
    min_alias_len: int | None = None,
    prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
    simplified_normalization: bool = False,
) -> Generator[tuple[DictionaryEntry, DictionaryEntryAlias], Any, Any]:
    """
    Yield geo-entity matches found in `text` according to `geo_config_list`.
    
    Parameters:
        text_languages (str | None): If provided, the single language to consider; it will be wrapped into a one-item list for matching.
        prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional precomputed alias ban mapping used to filter aliases; keys are alias strings and values are two lists used by the matching logic to determine bans.
        min_alias_len (int | None): Optional minimum alias length to consider when matching.
        conflict_resolving_field (str): Field name used to resolve conflicting matches (e.g., "id" or "priority").
        priority_direction (str): Direction for priority comparison ("asc" or "desc").
        simplified_normalization (bool): If true, apply a simplified normalization strategy when matching aliases.
    
    Returns:
        Generator of tuples (DictionaryEntry, DictionaryEntryAlias) for each extracted geo-entity match.
    """
    yield from get_geoentities(
        text,
        geo_config_list,
        conflict_resolving_field,
        priority_direction,
        [text_languages] if text_languages else None,
        min_alias_len,
        prepared_alias_ban_list,
        simplified_normalization,
    )


def test_geoentities():
    """
    Validate geo-entity extraction against the CSV test cases.
    
    Runs the extraction routine on the test dataset, converts actual results to a list of extracted entity names, and asserts they match the expected values; enables debug printing for test output.
    """
    lexnlp_tests.test_extraction_func_on_test_data(
        get_geoentities_routine,
        geo_config_list=_CONFIG,
        actual_data_converter=lambda actual: [c[0].name for c in actual],
        debug_print=True,
    )


def test_geoentities_counting():
    text = "And AND AND AND And"
    actual = list(get_geoentities(text, geo_config_list=_CONFIG))
    assert len(actual) == 3


def test_geoentities_en_equal_match_take_lowest_id():
    lexnlp_tests.test_extraction_func_on_test_data(
        get_geoentities_routine,
        geo_config_list=_CONFIG,
        conflict_resolving_field="id",
        text_languages="en",
        actual_data_converter=lambda actual: [(c[0].name, c[1].alias) for c in actual],
        debug_print=True,
    )


def test_geoentities_en_equal_match_take_top_prio():
    """
    Verifies that when multiple geoentity matches have equal match quality, the extractor selects the alias with the highest priority.
    
    Runs the extraction test on English test data with conflict_resolving_field="priority" and compares actual results to expected (entity name, alias) pairs.
    """
    lexnlp_tests.test_extraction_func_on_test_data(
        get_geoentities_routine,
        geo_config_list=_CONFIG,
        conflict_resolving_field="priority",
        text_languages="en",
        actual_data_converter=lambda actual: [(c[0].name, c[1].alias) for c in actual],
        debug_print=True,
    )


def test_geoentities_alias_filtering():
    prepared_alias_banlist = prepare_alias_banlist_dict(
        [
            AliasBanRecord("Afghanistan", None, False),
            AliasBanRecord("Mississippi", "en", False),
            AliasBanRecord("AL", "en", True),
        ]
    )
    lexnlp_tests.test_extraction_func_on_test_data(
        get_geoentities_routine,
        geo_config_list=_CONFIG,
        prepared_alias_ban_list=prepared_alias_banlist,
        actual_data_converter=lambda actual: [c[0].name for c in actual],
        debug_print=True,
        start_from_csv_line=6,
    )
