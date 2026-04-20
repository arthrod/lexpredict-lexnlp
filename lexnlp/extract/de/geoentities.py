__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from typing import Any
from collections.abc import Generator

import pandas as pd

from lexnlp.extract.all_locales.languages import LANG_DE
from lexnlp.extract.common.geoentity_detector import GeoEntityLocator
from lexnlp.extract.en.dict_entities import DictionaryEntry, DictionaryEntryAlias
from lexnlp.extract.common.annotations.geo_annotation import GeoAnnotation


def get_geoentity_annotations_custom_settings(
        text: str,
        config: pd.DataFrame,
        alias_columns: list[DictionaryEntryAlias] | None = None,
        priority_sort_column: str | None = 'Entity Priority',
        conflict_resolving_field: str = 'none',
        priority_direction: str = 'asc',
        text_languages: list[str] = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False,
        local_name_column: str | None = None,
        extra_columns: dict[str, str] | None = None) -> Generator[GeoAnnotation]:
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
        text_languages: list[str] = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False) -> Generator[GeoAnnotation]:

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
        text_languages: list[str] = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False,
        local_name_column: str | None = None,
        extra_columns: dict[str, str] | None = None) -> \
        Generator[dict[str, Any], Any, Any]:

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
        text_languages: list[str] = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False) -> Generator[dict[str, Any]]:

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
