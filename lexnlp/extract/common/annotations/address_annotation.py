__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class AddressAnnotation(TextAnnotation):
    """
    create an object of CopyrightAnnotation like
    cp = CopyrightAnnotation(name='name', coords=(0, 100), text='text text')
    """
    record_type = 'address'

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = 'en',
        text: str = '',
    ):
        """
        Initialize an AddressAnnotation with its span, locale, and extracted text.
        
        Parameters:
            coords (tuple[int, int]): Pair of integer coordinates (start, end) indicating the annotated span.
            locale (str): Language/locale code for the annotation (default 'en').
            text (str): Extracted address text for the annotation (default '').
        """
        super().__init__(
            name='',
            locale=locale,
            coords=coords,
            text=text
        )

    def get_cite_value_parts(self) -> list[str]:
        return [self.text]

    def get_dictionary_values(self) -> dict:
        df = {
            'tags': {
                'Extracted Entity Text': self.text,
            }
        }
        return df
