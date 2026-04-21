__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class UrlAnnotation(TextAnnotation):
    """
    create an object of UrlAnnotation like
    cp = UrlAnnotation(name='name', coords=(0, 100), url='www.google.com')
    """
    record_type = 'url'

    def __init__(self,
                 coords: tuple[int, int],
                 locale: str = 'en',
                 text: str | None = None,
                 url: str | None = None):
        """
                 Initialize a UrlAnnotation with location, locale, optional display text, and URL.
                 
                 Parameters:
                     coords (tuple[int, int]): Start and end character offsets for the annotation.
                     locale (str): Locale code for the annotation (default 'en').
                     text (str | None): Optional extracted or display text associated with the URL.
                     url (str | None): Optional URL value for the annotation; stored on the instance as `self.url`.
                 """
        super().__init__(
            name='',
            locale=locale,
            coords=coords,
            text=text)
        self.url = url

    def get_cite_value_parts(self) -> list[str]:
        return [self.url]

    def get_dictionary_values(self) -> dict:
        df = {
            'tags': {
                'Extracted Entity URL': self.url,
                'Extracted Entity Text': self.text
            }
        }
        return df
