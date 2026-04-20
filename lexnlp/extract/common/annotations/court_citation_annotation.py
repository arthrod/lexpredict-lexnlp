__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation
from lexnlp.utils.map import Map


class CourtCitationAnnotation(TextAnnotation):
    """
    create an object of CourtCitationAnnotation like
    cp = CourtCitationAnnotation(name='name', coords=(0, 100), text='text text')
    """
    record_type = 'court citation'

    def __init__(self,
                 coords: tuple[int, int],
                 locale: str = 'en',
                 name: str = '',
                 short_name: str | None = None,
                 text: str | None = None,
                 translated_name: str | None = None):
        """
        Initialize a CourtCitationAnnotation with document coordinates and optional citation naming fields.
                 
        Parameters:
        coords (tuple[int, int]): Start and end character offsets for the annotation within the source text.
        locale (str): Locale code for the annotation (e.g., 'en').
        name (str): Primary name of the cited entity.
        short_name (str | None): Optional abbreviated form of the citation.
        text (str | None): Optional extracted entity text; used as the displayed text when present.
        translated_name (str | None): Optional translated version of the citation name.
        """
        super().__init__(
            coords=coords,
            name=name,
            locale=locale,
            text=text)
        self.short_name = short_name
        self.translated_name = translated_name

    def get_cite_value_parts(self) -> list[str]:
        parts = [self.name or '',
                 self.short_name or '',
                 self.translated_name or '']
        return parts

    def get_dictionary_values(self) -> dict:
        dc = Map({
            'tags': {
                'Extracted Entity Text': self.text or self.name
            }
        })
        if self.name:
            dc.tags["Extracted Entity Name"] = self.name
        if self.short_name:
            dc.tags["Extracted Entity Short Name"] = self.short_name
        return dc
