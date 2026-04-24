__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation
from lexnlp.utils.map import Map


class GeoAnnotation(TextAnnotation):
    """
    create an object of GeoAnnotation like
    cp = GeoAnnotation(coords=(0, 100), value='101st Maple Street')
    """

    record_type = "geoentity"

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = "en",
        text: str | None = None,
        name: str | None = None,
        alias: str | None = None,
        name_en: str | None = None,
        source: str | None = None,
        entity_category: str | None = None,
        iso_3166_2: str | None = None,
        iso_3166_3: str | None = None,
        year: int | None = None,
        entity_id: int | None = None,
        entity_priority: int | None = None,
    ):
        """
        Create a geographic entity annotation with character offsets and optional metadata.

        Parameters:
            coords (tuple[int, int]): Start and end character offsets of the annotation in the source text.
            locale (str): Locale code for the annotation (default 'en').
            text (str | None): Extracted source text covered by the annotation.
            name (str | None): Extracted entity name in its original language.
            alias (str | None): Alternative or alternate name for the entity.
            name_en (str | None): English version of the entity name, if available.
            source (str | None): Identifier or provenance of the extraction (e.g., dataset or tool).
            entity_category (str | None): Category or class of the entity (for example, administrative unit).
            iso_3166_2 (str | None): ISO 3166-2 code for the entity, when applicable.
            iso_3166_3 (str | None): ISO 3166-3 code for the entity, when applicable.
            year (int | None): Year associated with the entity or extraction, if relevant.
            entity_id (int | None): External or internal identifier for the entity.
            entity_priority (int | None): Priority or ranking used to prefer this entity among multiple matches.
        """
        super().__init__(name=name, locale=locale, coords=coords, text=text)
        self.alias = alias
        self.name_en = name_en
        self.year = year
        self.source = source
        self.entity_category = entity_category
        self.entity_id = entity_id
        self.entity_priority = entity_priority
        self.iso_3166_2 = iso_3166_2
        self.iso_3166_3 = iso_3166_3

    def get_cite_value_parts(self) -> list[str]:
        parts = [str(self.name or ""), str(self.year or "")]
        return parts

    def get_dictionary_values(self) -> dict:
        df = Map({"tags": {"Extracted Entity Name": self.name, "Extracted Entity Text": self.text}})
        if self.year:
            df.tags["year"] = self.year
        return df

    def to_dictionary(self) -> dict:
        return {
            "location_start": self.coords[0],
            "location_end": self.coords[1],
            "source": self.source,  # 'Georgien',
            "Entity ID": self.entity_id,  # 999,
            "Entity Category": self.entity_category,  # 'Dummy',
            "Entity Name": self.name_en,  # 'Georgia',
            "Entity Priority": self.entity_priority,  # 700,
            "German Name": self.name,  # 'Georgien',
            "ISO-3166-2": self.iso_3166_2,
            "ISO-3166-3": self.iso_3166_3,
            "Alias": self.alias,
            "Entity Type": "geo entity",
        }
