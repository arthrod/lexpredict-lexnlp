__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal

from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class DurationAnnotation(TextAnnotation):
    """
    create an object of DurationAnnotation like
    cp = DurationAnnotation(coords=(0, 100), value='101 ms')
    """

    record_type = "duration"

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = "en",
        text: str | None = None,
        amount: Decimal | None = None,
        prefix: str | None = None,
        duration_days: Decimal | None = None,
        duration_type: str | None = None,
        duration_type_en: str | None = None,
        is_complex: bool = False,
        value_dict: dict | None = None,
    ) -> None:
        """
        Initialize a DurationAnnotation representing a detected duration entity.

        Parameters:
            coords (tuple[int, int]): Start and end character offsets of the annotation in the source text.
            locale (str): Locale code used for parsing/normalization (default 'en').
            text (str | None): Exact substring of the source corresponding to the annotation, if available.
            amount (Decimal | None): Numeric magnitude of the duration (e.g., '3' for "3 years"), if parsed.
            prefix (str | None): Any prefix text associated with the duration (e.g., 'about', 'approximately').
            duration_days (Decimal | None): Total duration expressed in days; set only when `amount` is provided.
            duration_type (str | None): Original duration unit extracted from the text (e.g., 'years', 'months').
            duration_type_en (str | None): English-normalized duration unit.
            is_complex (bool): True when the duration expression is compound or composed of multiple parts.
            value_dict (dict | None): Optional additional metadata or parsed values to attach to the annotation.
        """
        super().__init__(name="", locale=locale, coords=coords, text=text)
        self.amount: Decimal = amount
        self.prefix: str = prefix
        self.duration_days: Decimal = duration_days if amount is not None else None
        self.duration_type: str = duration_type
        self.duration_type_en: str = duration_type_en
        self.is_complex: bool = is_complex
        self.value_dict: dict = value_dict

    def get_cite_value_parts(self) -> list[str]:
        parts = [str(self.amount or ""), self.duration_type or ""]
        return parts

    def get_dictionary_values(self) -> dict:
        df = {"tags": {"Extracted Entity Value": str(self.amount or ""), "Extracted Entity Text": self.text}}
        return df
