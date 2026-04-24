__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation
from lexnlp.utils.map import Map


class ActAnnotation(TextAnnotation):
    """
    create an object of ActAnnotation like
    cp = ActAnnotation(name='name', coords=(0, 100), text='text text')
    """

    record_type = "act"

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = "en",
        act_name: str = "",
        section: str = "",
        year: int | None = None,
        ambiguous: bool = False,
        text: str = "",
    ):
        """
        Create an ActAnnotation representing a legislative act extracted from a span of text.

        Parameters:
            coords (tuple[int, int]): Start and end character offsets of the annotation in the source text.
            locale (str): Locale of the annotation (default 'en').
            act_name (str): Extracted name of the legislative act or statute.
            section (str): Extracted section or provision within the act, if any.
            year (int | None): Year associated with the act, or None if unknown.
            ambiguous (bool): True if the extraction is ambiguous, False if confidently identified.
            text (str): The original text span covered by the annotation.
        """
        super().__init__(name="", locale=locale, coords=coords, text=text)

        self.act_name = act_name
        self.section = section
        self.year = year
        self.ambiguous = ambiguous

    def get_cite_value_parts(self) -> list[str]:
        parts = [self.act_name or "", self.section or "", str(self.year or "")]
        return parts

    def get_dictionary_values(self) -> dict:
        df = Map({"tags": {"Extracted Entity Name": self.act_name, "Extracted Entity Text": self.text}})
        if self.section:
            df.tags["Extracted Entity Section"] = self.section
        if self.year:
            df.tags["Extracted Entity Year"] = str(self.year)
        if self.ambiguous is not None:
            df.tags["Extracted Entity Ambiguous"] = str(self.ambiguous)
        return df

    def to_dictionary_legacy(self) -> dict:
        return {
            "location_start": self.coords[0],
            "location_end": self.coords[1],
            "act_name": self.act_name,
            "section": self.section,
            "year": str(self.year) if self.year else "",
            "ambiguous": self.ambiguous,
            "value": self.text,
        }
