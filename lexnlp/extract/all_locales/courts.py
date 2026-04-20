__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

from lexnlp.extract.all_locales.languages import Locale
from lexnlp.extract.common.annotations.court_annotation import CourtAnnotation
from lexnlp.extract.en.dict_entities import DictionaryEntry, conflicts_take_first_by_id, find_dict_entities


def get_court_annotations(
        locale: str,
        text: str,
        court_config_list: list[DictionaryEntry],
        priority: bool = False,
        text_locales: list[str] = (),
        simplified_normalization: bool = False) -> Generator[CourtAnnotation]:
    """
        Create CourtAnnotation objects for courts found in text using the provided dictionary configurations.
        
        Parameters:
            locale (str): Locale string used to derive the default language for matching (e.g., "en_US").
            text (str): Text to search for court mentions.
            court_config_list (list[DictionaryEntry]): Dictionary entries configuring court names and metadata.
            priority (bool): If True, resolve overlapping/conflicting matches by keeping the first match by identifier.
            text_locales (list[str]): Additional locale strings whose languages are included when matching.
            simplified_normalization (bool): If True, apply simplified normalization during dictionary matching.
        
        Returns:
            Generator[CourtAnnotation]: Yields a CourtAnnotation for each match. Each annotation contains coordinates, entity identifiers, category, priority, English and original names, any extra columns set as attributes, alias (if matched), and a locale (alias language if available, otherwise the default language derived from `locale`).
        """
        locale_obj = Locale(locale)
    dic_entries = find_dict_entities(
        text,
        court_config_list,
        default_language=locale_obj.language,
        conflict_resolving_func=conflicts_take_first_by_id if priority else None,
        text_languages=[Locale(item).language for item in text_locales],
        simplified_normalization=simplified_normalization)
    for ent in dic_entries:
        ant = CourtAnnotation(coords=ent.coords)
        if ent.entity[0]:
            toponym: DictionaryEntry = ent.entity[0]
            ant.entity_id = toponym.id
            ant.entity_category = toponym.category
            ant.entity_priority = toponym.priority
            ant.name_en = toponym.entity_name
            ant.name = toponym.name
            if toponym.extra_columns:
                for extr_col in toponym.extra_columns:
                    setattr(ant, extr_col, toponym.extra_columns[extr_col])
        if ent.entity[1]:  # alias
            ant.alias = ent.entity[1].alias
            ant.locale = ent.entity[1].language
        if not ant.locale:
            ant.locale = locale_obj.language
        yield ant
