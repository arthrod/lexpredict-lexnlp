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
        Detect geographic entities in `text` by loading dictionary entries from a pandas DataFrame and yield corresponding GeoAnnotation objects.
        
        Parameters:
            text (str): Text to search for geographic entities.
            config (pd.DataFrame): DataFrame containing dictionary entries and related columns.
            alias_columns (list[DictionaryEntryAlias] | None): Columns or alias definitions to use for matching aliases.
            priority_sort_column (str | None): Column name in `config` that defines entity priority (default 'Entity Priority').
            conflict_resolving_field (str): Field used to resolve conflicting matches (default 'none').
            priority_direction (str): 'asc' or 'desc' ordering for priority resolution (default 'asc').
            text_languages (list[str] | None): Optional list of languages present in `text`.
            min_alias_len (int | None): Minimum alias length to consider; defaults to 2 when falsy.
            prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Precomputed ban lists for aliases per dictionary key.
            simplified_normalization (bool): If True, use simplified normalization for matching.
            local_name_column (str | None): Column name in `config` for local/native names.
            extra_columns (dict[str, str] | None): Mapping of extra column names to include in loaded entries.
        
        Returns:
            Generator[GeoAnnotation]: Yields a GeoAnnotation for each detected geographic entity in the text.
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
        Detects geographic entities in the given text using the provided dictionary entries.
        
        Parameters:
            text (str): Text to search for geographic entities.
            geo_config_list (list[DictionaryEntry]): List of dictionary entries defining geographic entities and their aliases.
            conflict_resolving_field (str): Field name used to resolve overlapping or conflicting matches; defaults to 'none'.
            priority_direction (str): Direction used to interpret priority values from entries ('asc' or 'desc'); defaults to 'asc'.
            text_languages (list[str] | None): Optional list of language codes to guide detection heuristics; forwarded to the locator as-is.
            min_alias_len (int | None): Minimum length for an alias to be considered; if falsy, treated as 2.
            prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional precomputed mapping of entries to banned aliases (exact and pattern lists).
            simplified_normalization (bool): If True, use a simplified normalization strategy when matching aliases.
        
        Returns:
            Generator[GeoAnnotation]: Yields a GeoAnnotation for each detected geographic entity in the text.
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
        Yield detected geographic entity annotations as dictionaries using dictionary entries loaded from a DataFrame.
        
        Parameters:
            text (str): Text to scan for geographic entities.
            config (pd.DataFrame): DataFrame containing dictionary entries used to detect entities.
            alias_columns (list[DictionaryEntryAlias] | None): Columns in `config` that contain alias definitions.
            priority_sort_column (str | None): Column name in `config` that provides entity priority (defaults to 'Entity Priority').
            conflict_resolving_field (str): Field used to resolve conflicts between overlapping matches.
            priority_direction (str): 'asc' or 'desc' to determine how priority values are ordered.
            text_languages (list[str] | None): Optional list of language codes to guide detection.
            min_alias_len (int | None): Minimum alias length to consider; defaults to 2 when not provided.
            prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Precomputed ban lists of aliases keyed by source.
            simplified_normalization (bool): If True, apply simplified normalization rules to matched text.
            local_name_column (str | None): Column name in `config` containing local/native names for entities.
            extra_columns (dict[str, str] | None): Mapping of additional `config` column names to annotation fields.
        
        Returns:
            dict[str, Any]: Generator that yields dictionaries representing detected geo annotations (one per match).
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
        Yield dictionaries for geographic entities detected in the given text.
        
        Parameters:
            text (str): Input text to scan for geographic entities.
            geo_config_list (list[DictionaryEntry]): List of dictionary entries that configure which geographic entities to detect.
            conflict_resolving_field (str): Field name used to resolve conflicting matches between entries (default 'none').
            priority_direction (str): Direction used when comparing entity priority; typically 'asc' or 'desc' (default 'asc').
            text_languages (list[str] | None): Optional list of language codes to guide detection; forwarded to the locator as provided.
            min_alias_len (int | None): Minimum alias length to consider; if falsy, treated as 2.
            prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional mapping from entry keys to a tuple of two lists: the first list contains aliases to ban, the second list contains full-word strings to ban.
            simplified_normalization (bool): If True, use a simplified normalization strategy when matching aliases.
        
        Returns:
            dict[str, Any]: A dictionary representation of each detected geographic annotation (one yielded per match).
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
