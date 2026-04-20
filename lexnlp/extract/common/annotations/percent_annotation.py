__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal

from lexnlp.extract.common.annotations.text_annotation import TextAnnotation
from lexnlp.utils.map import Map


class PercentAnnotation(TextAnnotation):
    """
    create an object of PercentAnnotation like
    cp = PercentAnnotation(coords=(0, 100), value='10 000 USD')
    """
    record_type = 'percent'

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = 'en',
        text: str | None = None,
        amount: Decimal | None = None,
        sign: str | None = None,
        fraction: Decimal | None = None
    ) -> None:
        """
        Initialize a PercentAnnotation with coordinates, optional textual content, and parsed numeric components.
        
        Parameters:
            coords (tuple[int, int]): Bounding box coordinates for the annotation.
            locale (str): Locale code used for parsing/formatting (default 'en').
            text (str | None): Original extracted text for the percent annotation.
            amount (Decimal | None): Whole-number percent value (e.g., 5 for '5%').
            sign (str | None): Sign associated with the value (e.g., '+' or '-'), if present.
            fraction (Decimal | None): Fractional part of the percent value (e.g., 0.5 for '5.5%').
        """
        super().__init__(
            name='',
            locale=locale,
            coords=coords,
            text=text
        )
        self.amount: Decimal = amount
        self.sign: str = sign
        self.fraction: Decimal = fraction

    def get_cite_value_parts(self) -> list[str]:
        return [str(self.amount or '0'),
                self.sign or '']

    def get_dictionary_values(self) -> dict:
        df = Map({
            'tags': {
                'Extracted Entity Value': str(self.amount or ''),
                'Extracted Entity Text': self.text
            }
        })
        if self.sign:
            df.tags['sign'] = self.sign
        return df
