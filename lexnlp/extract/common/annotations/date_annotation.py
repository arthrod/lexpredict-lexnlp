__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from datetime import date as _date

from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class DateAnnotation(TextAnnotation):
    """
    create an object of ActAnnotation like
    cp = ActAnnotation(name='name', coords=(0, 100), text='text text')
    """
    record_type = 'date'

    def __init__(self,
                 coords: tuple[int, int],
                 locale: str = 'en',
                 text: str | None = None,
                 date: _date = None,
                 score: float | None = None):
        """
                 Initialize a DateAnnotation with the annotation span, locale, optional text, associated date value, and an optional confidence score.
                 
                 Parameters:
                     coords (tuple[int, int]): Start and end character offsets for the annotation span.
                     locale (str): Locale code used to interpret the text (default 'en').
                     text (str | None): Extracted text for the annotation, or None if not provided.
                     date (datetime.date | None): Associated date value for the annotation, or None if unavailable.
                     score (float | None): Optional numeric confidence score for the annotation, or None if not provided.
                 """
        super().__init__(
            name='',
            locale=locale,
            coords=coords,
            text=text)
        self.date = date
        self.score = score

    def get_cite_value_parts(self) -> list[str]:
        return [str(self.date or '')]

    def get_dictionary_values(self) -> dict:
        df = {
            "tags": {
                'Extracted Entity Date': str(self.date or ''),
                'Extracted Entity Text': self.text
            }
        }
        return df
