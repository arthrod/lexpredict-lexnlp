__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator
from typing import Any

from lexnlp.extract.common.annotations.geo_annotation import GeoAnnotation
from lexnlp.extract.en.dict_entities import (
    DictionaryEntry,
    DictionaryEntryAlias,
    conflicts_take_first_by_id,
    conflicts_top_by_priority,
    find_dict_entities,
)


class GeoEntityLocator:
    """
    Searches for geo entities from the provided config list and yields pairs of (entity, alias).
                Entity is: (entity_id, name, [list of aliases])
                Alias is: (alias_text, lang, is_abbrev, alias_id)
    """
    def __init__(
            self,
            language: str,
            geo_config_list: list[DictionaryEntry],
            prepared_alias_ban_list: None | dict[str, tuple[list[str], list[str]]],
            conflict_resolving_field: str = 'none',
            priority_direction: str = 'asc',
            text_languages: list[str] | None = None,
            min_alias_len: int = 2,
            simplified_normalization: bool = False):
        """
            Initialize locator configuration for finding geographic entities in text.
            
            Parameters:
                language: Default language to assign to annotations when no alias locale is available.
                geo_config_list: List of known geographic dictionary entries defining entities and their aliases.
                prepared_alias_ban_list: Optional map of language -> (normalized non-abbreviation aliases, normalized abbreviation aliases) to exclude from matching.
                conflict_resolving_field: Strategy to resolve exact-alias conflicts: 'id' to prefer lower id, 'priority' to prefer top priority, or 'none' to keep all matches.
                priority_direction: Order ('asc' or 'desc') used by the priority-based conflict resolution.
                text_languages: Optional list of languages of the source text; when provided, only aliases in these languages are considered.
                min_alias_len: Minimum length of an alias to be considered for matching.
                simplified_normalization: If true, use a simplified normalization pipeline (skip NLTK-based normalization).
            """
        self.language = language
        self.geo_config_list = geo_config_list
        self.prepared_alias_ban_list = prepared_alias_ban_list
        self.conflict_resolving_func = conflicts_take_first_by_id if conflict_resolving_field == 'id' \
            else conflicts_top_by_priority if conflict_resolving_field == 'priority' else None
        self.priority_direction = priority_direction
        self.text_languages = text_languages
        self.min_alias_len = min_alias_len
        self.simplified_normalization = simplified_normalization

    def get_geoentity_entries(
            self,
            text: str) -> Generator[tuple[DictionaryEntry, DictionaryEntryAlias], Any, Any]:
        """
        This method uses general searching routines for dictionary entities from dict_entities.py module.
        Methods of dict_entities module can be used for comfortable creating the config: entity_config(),
        entity_alias(), add_aliases_to_entity().
        """
        for ent in find_dict_entities(text,
                                      self.geo_config_list,
                                      conflict_resolving_func=self.conflict_resolving_func,
                                      priority_direction=self.priority_direction,
                                      default_language=self.language,
                                      text_languages=self.text_languages,
                                      min_alias_len=self.min_alias_len,
                                      prepared_alias_ban_list=self.prepared_alias_ban_list,
                                      simplified_normalization=self.simplified_normalization):
            yield ent.entity

    def get_geoentity_annotations(
            self,
            text: str) -> Generator[GeoAnnotation]:
        """
        This method uses general searching routines for dictionary entities from dict_entities.py module.
        Methods of dict_entities module can be used for comfortable creating the config: entity_config(),
        entity_alias(), add_aliases_to_entity().
        """
        dic_entries = find_dict_entities(text,
                                         self.geo_config_list,
                                         self.language,
                                         conflict_resolving_func=self.conflict_resolving_func,
                                         priority_direction=self.priority_direction,
                                         text_languages=self.text_languages,
                                         min_alias_len=self.min_alias_len,
                                         prepared_alias_ban_list=self.prepared_alias_ban_list,
                                         simplified_normalization=self.simplified_normalization)

        for ent in dic_entries:
            ant = GeoAnnotation(coords=ent.coords)
            if ent.entity[0]:
                toponym = ent.entity[0]  # type: DictionaryEntry
                ant.entity_id = toponym.id
                ant.entity_category = toponym.category
                ant.entity_priority = toponym.priority
                ant.name_en = toponym.entity_name
                # year = TextAnnotation.get_int_value(toponym.id)  # ?
                # if year:
                #     ant.year = year
                ant.name = toponym.name
                if toponym.extra_columns:
                    for extr_col in toponym.extra_columns:
                        setattr(ant, extr_col, toponym.extra_columns[extr_col])

            if ent.entity[1]:  # alias
                ant.alias = ent.entity[1].alias
                ant.locale = ent.entity[1].language
            if not ant.locale:
                ant.locale = self.language
            yield ant
