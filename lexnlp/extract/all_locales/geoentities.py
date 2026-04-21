__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

from lexnlp.extract.all_locales.languages import DEFAULT_LANGUAGE, LANG_DE, LANG_EN, Locale
from lexnlp.extract.common.annotations.geo_annotation import GeoAnnotation
from lexnlp.extract.de.geoentities import get_geoentity_annotations as get_geoentity_annotations_de
from lexnlp.extract.en.dict_entities import DictionaryEntry
from lexnlp.extract.en.geoentities import get_geoentity_annotations as get_geoentity_annotations_en

ROUTINE_BY_LOCALE = {
    LANG_EN.code: get_geoentity_annotations_en,
    LANG_DE.code: get_geoentity_annotations_de
}


def get_geoentity_annotations(
        locale: str,
        text: str,
        geo_config_list: list[DictionaryEntry],
        conflict_resolving_field: str = 'none',
        priority_direction: str = 'asc',
        text_languages: list[str] | None = None,
        min_alias_len: int | None = None,
        prepared_alias_ban_list: dict[str, tuple[list[str], list[str]]] | None = None,
        simplified_normalization: bool = False) -> Generator[GeoAnnotation]:
    """
        Return geoentity annotations for the given text using locale-appropriate extraction rules.
        
        Parameters:
            locale (str): Locale identifier (e.g., 'en_US') used to select language-specific extraction.
            text (str): Input text to analyze for geographic entities.
            geo_config_list (list[DictionaryEntry]): Configuration entries defining geographic dictionaries and metadata used during extraction.
            conflict_resolving_field (str): Field name used to resolve conflicting matches; 'none' disables conflict resolution.
            priority_direction (str): Match priority direction, 'asc' or 'desc', determining which candidate is preferred when resolving ties.
            text_languages (list[str] | None): Optional list of language tags to consider for ambiguous aliases; pass None to use defaults.
            min_alias_len (int | None): Optional minimum alias token length to consider; pass None to disable length filtering.
            prepared_alias_ban_list (dict[str, tuple[list[str], list[str]]] | None): Optional mapping of dictionary keys to tuples of (exact_bans, prefix_bans) to exclude specific aliases.
            simplified_normalization (bool): If True, apply a faster, reduced normalization routine when matching aliases.
        
        Returns:
            Generator[GeoAnnotation]: Yields GeoAnnotation objects representing detected geographic entities in the text.
        """
    routine = ROUTINE_BY_LOCALE.get(Locale(locale).language, ROUTINE_BY_LOCALE[DEFAULT_LANGUAGE.code])
    yield from routine(text, geo_config_list, conflict_resolving_field,
                       priority_direction, text_languages, min_alias_len,
                       prepared_alias_ban_list, simplified_normalization)
