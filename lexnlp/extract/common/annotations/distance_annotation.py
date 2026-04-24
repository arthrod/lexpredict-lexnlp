__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal

from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class DistanceAnnotation(TextAnnotation):
    """
    create an object of DistanceAnnotation like
    cp = DistanceAnnotation(coords=(0, 100), value='101 km')
    """

    record_type = "distance"

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = "en",
        text: str | None = None,
        amount: Decimal | None = None,
        distance_type: str | None = None,
    ) -> None:
        """
        Initialize a DistanceAnnotation with location, locale, optional text, numeric amount, and distance type.

        Parameters:
            coords (tuple[int, int]): Start and end character indices for the annotation within the source text.
            locale (str): Locale code for the annotation (e.g., 'en').
            text (str | None): The matched text span for the annotation, or None if unavailable.
            amount (Decimal | None): Numeric distance value, or None if not provided.
            distance_type (str | None): Unit or descriptor for the distance (e.g., 'miles', 'feet'), or None if unspecified.
        """
        super().__init__(
            name="",
            locale=locale,
            coords=coords,
            text=text,
        )
        self.amount: Decimal = amount
        self.distance_type: str = distance_type

    def get_cite_value_parts(self) -> list[str]:
        parts = [str(self.amount or ""), self.distance_type or ""]
        return parts

    def get_dictionary_values(self) -> dict:
        df = {"tags": {"Extracted Entity Value": str(self.amount or ""), "Extracted Entity Text": self.text}}
        return df
