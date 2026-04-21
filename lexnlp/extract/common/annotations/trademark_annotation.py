__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class TrademarkAnnotation(TextAnnotation):
    """
    create an object of TrademarkAnnotation like
    cp = TrademarkAnnotation(name='name', coords=(0, 100), trademark='CZ')
    """
    record_type = 'trademark'

    def __init__(self,
                 coords: tuple[int, int],
                 locale: str = 'en',
                 text: str | None = None,
                 trademark: str = ''):
        """
                 Create a TrademarkAnnotation with character offsets, locale, optional covered text, and the extracted trademark.
                 
                 Parameters:
                     coords (tuple[int, int]): Start and end character offsets for the annotation.
                     locale (str): Language/locale code (default 'en').
                     text (str | None): Optional text covered by the annotation.
                     trademark (str): Extracted trademark value to store on the instance.
                 """
        super().__init__(
            name='',
            locale=locale,
            coords=coords,
            text=text)
        self.trademark = trademark

    def get_cite_value_parts(self) -> list[str]:
        return [self.trademark]

    def get_dictionary_values(self) -> dict:
        df = {
            'tags': {
                'Extracted Entity Trademark': self.trademark,
                'Extracted Entity Text': self.text
            }
        }
        return df
