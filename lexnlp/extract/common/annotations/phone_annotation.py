__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class PhoneAnnotation(TextAnnotation):
    """
    create an object of PhoneAnnotation (Social Secutiry Number) like
    cp = PhoneAnnotation(coords=(0, 100), phone='+9 915 710 42 24')
    """

    record_type = "phone"

    def __init__(self, coords: tuple[int, int], locale: str = "en", text: str | None = None, phone: str | None = None):
        """
        Create a PhoneAnnotation for a character-span with optional covered text and an optional normalized phone number.

        Parameters:
            coords (tuple[int, int]): Start and end character offsets for the annotation span.
            locale (str): Locale code for the annotation (e.g., 'en').
            text (str | None): Covered or extracted text for the span, if available.
            phone (str | None): Extracted or normalized phone number associated with the annotation, if available.
        """
        super().__init__(name="", locale=locale, coords=coords, text=text)
        self.phone = phone

    def get_cite_value_parts(self) -> list[str]:
        return [self.phone]

    def get_dictionary_values(self) -> dict:
        df = {"tags": {"Extracted Entity Phone": self.phone or "", "Extracted Entity Text": self.text}}
        return df
