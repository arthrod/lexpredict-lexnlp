__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator
from typing import Any

import pandas as pd

from lexnlp.extract.all_locales.languages import LANG_DE
from lexnlp.extract.common.annotations.geo_annotation import GeoAnnotation
from lexnlp.extract.common.geoentity_detector import GeoEntityLocator
from lexnlp.extract.en.dict_entities import DictionaryEntry, DictionaryEntryAlias


def get_geoentity_annotations_custom_settings(
        text: str,
        config: pd.DataFrame,
        alias_columns: list[DictionaryEntryAlias] | None = None,
        priority_sort_column: str | None = 'Entity Priority',
        conflict_resolving_field: str = 'none',
        priority_direction: str = 'asc',
        text_languages: list[str] | None = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False,
        local_name_column: str | None = None,
        extra_columns: dict[str, str] | None = None) -> Generator[GeoAnnotation]:
    """
        Detect geographic entities in text using dictionary entries loaded from a DataFrame and yield GeoAnnotation objects for each match.
        
        Parameters:
            text: Text to search for geographic entities.
            config: DataFrame with dictionary entries and related columns; passed to the dictionary loader to produce matching entries.
            alias_columns: Columns or alias definitions used to extract matching aliases from `config`.
            priority_sort_column: Column name in `config` that defines entity priority (defaults to 'Entity Priority').
            conflict_resolving_field: Field name used to resolve overlapping matches; 'none' disables resolution.
            priority_direction: 'asc' or 'desc' to control priority sorting direction when resolving conflicts.
            text_languages: Optional list of language codes to guide language-sensitive matching.
            min_alias_len: Minimum alias length to consider; when falsy, behaves as 2.
            prepared_alias_ban_list: Optional per-key ban lists of aliases to ignore, mapping keys to (ban_list, whitelist).
            simplified_normalization: If True, use a simplified normalization strategy for alias matching.
            local_name_column: Optional column name in `config` holding local/native names.
            extra_columns: Optional mapping of additional column names to include on loaded entries.
        
        Returns:
            Generator yielding `GeoAnnotation` for each detected geographic entity.
        """
    entries = DictionaryEntry.load_entities_from_single_df(
        config,
        LANG_DE.code,
        alias_columns=alias_columns,
        priority_column=priority_sort_column,
        local_name_column=local_name_column,
        extra_columns=extra_columns)

    yield from get_geoentity_annotations(
        text,
        entries,
        conflict_resolving_field=conflict_resolving_field,
        priority_direction=priority_direction,
        text_languages=text_languages,
        min_alias_len=min_alias_len,
        prepared_alias_ban_list=prepared_alias_ban_list,
        simplified_normalization=simplified_normalization)


def get_geoentity_annotations(
        text: str,
        geo_config_list: list[DictionaryEntry],
        conflict_resolving_field: str = 'none',
        priority_direction: str = 'asc',
        text_languages: list[str] | None = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False) -> Generator[GeoAnnotation]:

    """
        Detect geographic entities in text using the provided dictionary entries.
        
        Parameters:
            text: Text to search for geographic entities.
            geo_config_list: List of dictionary entries that define geographic entities and their aliases.
            conflict_resolving_field: Field name used to resolve overlapping or conflicting matches; defaults to 'none'.
            priority_direction: How to interpret entry priority values — 'asc' or 'desc'; defaults to 'asc'.
            text_languages: Optional list of language codes to guide detection heuristics.
            min_alias_len: Minimum alias length to consider; if falsy, treated as 2.
            prepared_alias_ban_list: Optional mapping from entry identifier to a tuple of two lists: exact banned aliases and banned alias patterns.
            simplified_normalization: If True, apply a simplified normalization strategy when matching aliases.
        
        Returns:
            A generator that yields a GeoAnnotation for each detected geographic entity in the text.
        """
    min_alias_len = min_alias_len if min_alias_len else 2
    locator = GeoEntityLocator(LANG_DE.code,
                               geo_config_list,
                               prepared_alias_ban_list,
                               conflict_resolving_field=conflict_resolving_field,
                               priority_direction=priority_direction,
                               text_languages=text_languages,
                               min_alias_len=min_alias_len,
                               simplified_normalization=simplified_normalization)

    yield from locator.get_geoentity_annotations(text)


def get_geoentities_custom_settings(
        text: str,
        config: pd.DataFrame,
        alias_columns: list[DictionaryEntryAlias] | None = None,
        priority_sort_column: str | None = 'Entity Priority',
        conflict_resolving_field: str = 'none',
        priority_direction: str = 'asc',
        text_languages: list[str] | None = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False,
        local_name_column: str | None = None,
        extra_columns: dict[str, str] | None = None) -> \
        Generator[dict[str, Any], Any, Any]:

    """
        Yield dictionary representations of geographic entity annotations found in the given text using dictionary entries loaded from a DataFrame.
        
        Parameters:
            text (str): Text to scan for geographic entities.
            config (pd.DataFrame): DataFrame containing dictionary entries; columns are mapped via parameters below.
            alias_columns (list[DictionaryEntryAlias] | None): Columns in `config` that contain alias definitions.
            priority_sort_column (str | None): Column in `config` that provides entity priority (defaults to 'Entity Priority').
            conflict_resolving_field (str): Field used to resolve overlapping matches.
            priority_direction (str): 'asc' or 'desc' to determine how priority values are ordered.
            text_languages (list[str] | None): Optional list of language codes to guide detection.
            min_alias_len (int | None): Minimum alias length to consider; when falsy, detection uses 2.
            prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Precomputed per-source ban lists of aliases.
            simplified_normalization (bool): If True, apply simplified normalization rules to matched text.
            local_name_column (str | None): Column in `config` containing local/native names for entities.
            extra_columns (dict[str, str] | None): Mapping of additional `config` column names to annotation fields.
        
        Returns:
            Generator[dict[str, Any], Any, Any]: Yields dictionaries mapping annotation field names to values for each detected geographic entity.
        """
    for ant in get_geoentity_annotations_custom_settings(
            text,
            config,
            alias_columns=alias_columns,
            priority_sort_column=priority_sort_column,
            conflict_resolving_field=conflict_resolving_field,
            priority_direction=priority_direction,
            text_languages=text_languages,
            min_alias_len=min_alias_len,
            prepared_alias_ban_list=prepared_alias_ban_list,
            simplified_normalization=simplified_normalization,
            local_name_column=local_name_column,
            extra_columns=extra_columns):
        yield ant.to_dictionary()


def get_geoentities(
        text: str,
        geo_config_list: list[DictionaryEntry],
        conflict_resolving_field: str = 'none',
        priority_direction: str = 'asc',
        text_languages: list[str] | None = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False) -> Generator[dict[str, Any]]:

    """
        Yield dictionaries for geographic entity annotations found in the provided text.
        
        Parameters:
            text (str): Text to scan for geographic entities.
            geo_config_list (list[DictionaryEntry]): Dictionary entries defining target geographic entities.
            conflict_resolving_field (str): Field name used to resolve overlaps between matching annotations.
            priority_direction (str): Direction to interpret entry priority, e.g., 'asc' or 'desc'.
            text_languages (list[str] | None): Optional language codes to guide matching.
            min_alias_len (int | None): Minimum alias length to consider; if falsy, treated as 2.
            prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional mapping from entry key to a tuple of (aliases to ban, full-word strings to ban).
            simplified_normalization (bool): If True, apply a simplified normalization strategy when matching aliases.
        
        Returns:
            dict[str, Any]: Dictionary representation of a detected geographic annotation; one yielded per match.
        """
    min_alias_len = min_alias_len if min_alias_len else 2
    locator = GeoEntityLocator(LANG_DE.code,
                               geo_config_list,
                               prepared_alias_ban_list,
                               conflict_resolving_field=conflict_resolving_field,
                               priority_direction=priority_direction,
                               text_languages=text_languages,
                               min_alias_len=min_alias_len,
                               simplified_normalization=simplified_normalization)

    for ant in locator.get_geoentity_annotations(text):
        yield ant.to_dictionary()
