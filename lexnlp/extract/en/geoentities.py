"""
Geo Entity extraction for English.

This module implements extraction functionality for geo entities in English, including formal names, abbreviations,
and aliases.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator
from typing import Any

from lexnlp.config.en import geoentities_config
from lexnlp.extract.all_locales.languages import LANG_EN
from lexnlp.extract.common.annotations.geo_annotation import GeoAnnotation
from lexnlp.extract.common.geoentity_detector import GeoEntityLocator
from lexnlp.extract.en.dict_entities import DictionaryEntry, DictionaryEntryAlias, prepare_alias_banlist_dict

_ALIAS_BAN_LIST_PREPARED = prepare_alias_banlist_dict(geoentities_config.ALIAS_BLACK_LIST)


def get_geoentities(
    text: str,
    geo_config_list: list[DictionaryEntry],
    conflict_resolving_field: str = 'none',
    priority_direction: str = 'asc',
    text_languages: list[str] | None = None,
    min_alias_len: int | None = None,
    prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
    simplified_normalization: bool = False,
) -> Generator[tuple[DictionaryEntry, DictionaryEntryAlias], Any, Any]:
    """
    Locate English geo-entity matches in `text` using the provided geo-entity dictionary configuration and yield matching dictionary entry / alias pairs.
    
    Parameters:
        text (str): Input text to search for geo-entity aliases.
        geo_config_list (list[DictionaryEntry]): Dictionary entries and their aliases used for matching.
        conflict_resolving_field (str): Field name used to resolve conflicting matches.
        priority_direction (str): Ordering direction for priority resolution, e.g. 'asc' or 'desc'.
        text_languages (list[str] | None): Optional list of language codes to restrict matching to specific languages.
        min_alias_len (int | None): Minimum alias length to consider; falls back to configured default when `None`.
        prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional prepared alias ban-list mapping an alias to a tuple of two lists (entry IDs, alias IDs) to exclude; uses the module default when `None`.
        simplified_normalization (bool): When true, apply a simplified normalization strategy to aliases before matching.
    
    Returns:
        Generator[tuple[DictionaryEntry, DictionaryEntryAlias], Any, Any]: Generator yielding (dictionary entry, matching alias) pairs for each found geo-entity in `text`.
    """
    prepared_alias_ban_list = (
        prepared_alias_ban_list
        if prepared_alias_ban_list is not None
        else _ALIAS_BAN_LIST_PREPARED
    )

    min_alias_len = min_alias_len if min_alias_len else geoentities_config.MIN_ALIAS_LEN

    locator = GeoEntityLocator(
        LANG_EN.code,
        geo_config_list,
        prepared_alias_ban_list,
        conflict_resolving_field=conflict_resolving_field,
        priority_direction=priority_direction,
        text_languages=text_languages,
        min_alias_len=min_alias_len,
        simplified_normalization=simplified_normalization
    )

    yield from locator.get_geoentity_entries(text)


def get_geoentity_list(
    text: str,
    geo_config_list: list[DictionaryEntry],
    conflict_resolving_field: str = 'none',
    priority_direction: str = 'asc',
    text_languages: list[str] | None = None,
    min_alias_len: int | None = None,
    prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
    simplified_normalization: bool = False,
) -> list[tuple[DictionaryEntry, DictionaryEntryAlias]]:
    """
    Return all geo-entity dictionary entries and their matching aliases found in the input text as a list.
    
    Parameters:
        text (str): Input text to search for geo-entity aliases.
        geo_config_list (list[DictionaryEntry]): Ordered list of geo-entity dictionary entries used for matching.
        conflict_resolving_field (str): Field name used to resolve conflicts between overlapping matches.
        priority_direction (str): Ordering direction for entry priority resolution (`'asc'` or `'desc'`).
        text_languages (list[str] | None): Optional list of language codes to use for language-specific matching; `None` disables language filtering.
        min_alias_len (int | None): Minimum alias length to consider; when `None` the module default is used.
        prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional precomputed alias ban-list mapping; when `None` the module default is used.
        simplified_normalization (bool): When true, apply simplified normalization to input and aliases before matching.
    
    Returns:
        list[tuple[DictionaryEntry, DictionaryEntryAlias]]: A list of tuples where each tuple contains the matched dictionary entry and the specific alias that matched.
    """
    return list(
        get_geoentities(
            text=text,
            geo_config_list=geo_config_list,
            conflict_resolving_field=conflict_resolving_field,
            priority_direction=priority_direction,
            text_languages=text_languages,
            min_alias_len=min_alias_len,
            prepared_alias_ban_list=prepared_alias_ban_list,
            simplified_normalization=simplified_normalization,
        )
    )


def get_geoentity_annotations(
    text: str,
    geo_config_list: list[DictionaryEntry],
    conflict_resolving_field: str = 'none',
    priority_direction: str = 'asc',
    text_languages: list[str] | None = None,
    min_alias_len: int | None = None,
    prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
    simplified_normalization: bool = False,
) -> Generator[GeoAnnotation]:

    """
    Extract English geo-entity annotations from input text using the provided geo-entity configuration.
    
    Parameters:
        text (str): Input text to analyze.
        geo_config_list (list[DictionaryEntry]): Ordered list of dictionary entries that define geo-entities and their aliases.
        conflict_resolving_field (str): Field name used to resolve conflicts between overlapping matches (default 'none').
        priority_direction (str): Ordering direction for priority when resolving ties; typically 'asc' or 'desc'.
        text_languages (list[str] | None): Optional list of language codes to filter or influence matching; None to skip language filtering.
        min_alias_len (int | None): Minimum alias length to consider; if falsy, uses geoentities_config.MIN_ALIAS_LEN.
        prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Precomputed alias ban-list mapping; if None, uses the module default.
        simplified_normalization (bool): If True, apply a simplified normalization pipeline to aliases before matching.
    
    Returns:
        Generator[GeoAnnotation]: A generator yielding GeoAnnotation objects for each detected geo-entity in the text.
    """
    prepared_alias_ban_list = (
        prepared_alias_ban_list
        if prepared_alias_ban_list is not None
        else _ALIAS_BAN_LIST_PREPARED
    )

    min_alias_len = min_alias_len if min_alias_len else geoentities_config.MIN_ALIAS_LEN

    locator = GeoEntityLocator(
        LANG_EN.code,
        geo_config_list,
        prepared_alias_ban_list,
        conflict_resolving_field=conflict_resolving_field,
        priority_direction=priority_direction,
        text_languages=text_languages,
        min_alias_len=min_alias_len,
        simplified_normalization=simplified_normalization,
    )

    yield from locator.get_geoentity_annotations(text)


def get_geoentity_annotation_list(
    text: str,
    geo_config_list: list[DictionaryEntry],
    conflict_resolving_field: str = 'none',
    priority_direction: str = 'asc',
    text_languages: list[str] | None = None,
    min_alias_len: int | None = None,
    prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
    simplified_normalization: bool = False,
) -> list[GeoAnnotation]:
    """
    Return a list of GeoAnnotation objects extracted from the provided English text.
    
    Parameters:
        text (str): Input text to search for geo-entities.
        geo_config_list (list[DictionaryEntry]): Dictionary entries used for matching geo-entities.
        conflict_resolving_field (str): Field name used to resolve conflicts between overlapping matches (e.g., 'none').
        priority_direction (str): Ordering direction for entry priority, either 'asc' or 'desc'.
        text_languages (list[str] | None): Optional list of language codes to filter aliases by language; `None` disables language filtering.
        min_alias_len (int | None): Minimum alias length to consider; if `None`, the module default is used.
        prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional precomputed alias ban-list mapping; if `None`, the module default is used.
        simplified_normalization (bool): If true, apply simplified normalization to text and aliases before matching.
    
    Returns:
        list[GeoAnnotation]: A list of geo-entity annotations found in the text.
    """
    return list(
        get_geoentity_annotations(
            text=text,
            geo_config_list=geo_config_list,
            conflict_resolving_field=conflict_resolving_field,
            priority_direction=priority_direction,
            text_languages=text_languages,
            min_alias_len=min_alias_len,
            prepared_alias_ban_list=prepared_alias_ban_list,
            simplified_normalization=simplified_normalization,
        )
    )
