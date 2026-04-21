__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation
from lexnlp.utils.map import Map


class RegulationAnnotation(TextAnnotation):
    """
    create an object of RegulationAnnotation like
    cp = RegulationAnnotation(name='name', coords=(0, 100), text='text text')
    """
    record_type = 'regulation'

    def __init__(self,
                 coords: tuple[int, int],
                 locale: str = 'en',
                 name: str = '',
                 text: str | None = None,
                 source: str = '',
                 country: str = ''):
        """
                 Initialize a RegulationAnnotation with coordinates, locale, identifier text, and source/country metadata.
                 
                 Parameters:
                     coords (tuple[int, int]): Character span (start, end) of the annotation in the source text.
                     locale (str): Locale code for the annotation (default 'en').
                     name (str): Identifier or code of the regulation (e.g., section number or code).
                     text (str | None): Extracted annotation text; if None, the `name` may be used as display text.
                     source (str): Issuing source or authority for the regulation (e.g., agency or publication).
                     country (str): Issuing country for the external reference.
                 """
        super().__init__(
            name=name,
            locale=locale,
            coords=coords,
            text=text)
        self.country = country
        self.source = source

    def get_cite_value_parts(self) -> list[str]:
        parts = [self.country or '',
                 self.source or '',
                 self.name or '']
        return parts

    def get_dictionary_values(self) -> dict:
        dic = Map({
            'tags': {
                'External Reference Issuing Country': self.country,
                'External Reference Text': self.name,
                'Extracted Entity Text': self.text or self.name
            }
        })
        if self.source:
            dic.tags['External Reference Source'] = self.source
        return dic

    def to_dictionary_legacy(self) -> dict:
        return {"regulation_type": self.source,
                "regulation_code": self.name,
                "regulation_text": self.text}
