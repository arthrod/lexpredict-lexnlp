__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.annotations.text_annotation import TextAnnotation


class SsnAnnotation(TextAnnotation):
    """
    create an object of SsnAnnotation (Social Secutiry Number) like
    cp = SsnAnnotation(coords=(0, 100), value='1234 4321 1234')
    """

    record_type = "ssn"

    def __init__(self, coords: tuple[int, int], locale: str = "en", text: str | None = None, number: str | None = None):
        """
        Create an SsnAnnotation representing a detected Social Security Number within source text.

        Parameters:
            coords (tuple[int, int]): Start and end character offsets of the annotation within the source text.
            locale (str): Locale code for the annotation (default 'en').
            text (str | None): The extracted display text for the annotation, if available.
            number (str | None): The extracted Social Security Number value, if available.
        """
        super().__init__(name="", locale=locale, coords=coords, text=text)
        self.number = number

    def get_cite_value_parts(self) -> list[str]:
        return [self.number]

    def get_dictionary_values(self) -> dict:
        df = {"tags": {"Extracted Entity SSN": self.number or "", "Extracted Entity Text": self.text}}
        return df
