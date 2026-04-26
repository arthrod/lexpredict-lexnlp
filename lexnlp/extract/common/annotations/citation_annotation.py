__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from typing import Any

from lexnlp.extract.common.annotations.text_annotation import TextAnnotation
from lexnlp.utils.map import Map


class CitationAnnotation(TextAnnotation):
    """
    create an object of CitationAnnotation like
    cp = CitationAnnotation(name='name', coords=(0, 100), text='text text')
    """

    record_type = "citation"

    def __init__(
        self,
        coords: tuple[int, int],
        locale: str = "en",
        text: str = "",
        volume: int | None = None,
        volume_str: str | None = None,
        year: int | None = None,
        reporter: str | None = None,
        reporter_full_name: str | None = None,
        page: int | None = None,
        page_range: str | None = None,
        court: str | None = None,
        source: str | None = None,
        article: int | None = None,
        paragraph: str | None = None,
        subparagraph: str | None = None,
        letter: str | None = None,
        sentence: int | None = None,
        date: str | None = None,
        part: str | None = None,
        year_str: str | None = None,
    ):
        """
        Initialize a CitationAnnotation with location, text, and parsed citation fields.

        Parameters:
            coords (tuple[int, int]): Bounding coordinates of the annotation.
            locale (str): Locale/language of the annotation text.
            text (str): Extracted entity text for the citation.
            volume (int | None): Numeric volume number, if available.
            volume_str (str | None): Volume represented as a string (when non-numeric or formatted).
            year (int | None): Year associated with the citation.
            reporter (str | None): Short reporter abbreviation (e.g., "U.S.", "F.3d").
            reporter_full_name (str | None): Full reporter name.
            page (int | None): Page number within the reporter.
            page_range (str | None): Page range string (e.g., "123-125").
            court (str | None): Court identifier or name.
            source (str | None): Original source string for the citation.
            article (int | None): Article number within a source, when applicable.
            paragraph (str | None): Paragraph identifier within the cited document.
            subparagraph (str | None): Subparagraph identifier.
            letter (str | None): Lettered subunit identifier.
            sentence (int | None): Sentence number within the cited unit.
            date (str | None): Date string associated with the citation.
            part (str | None): Part identifier within the source (e.g., "Part I").
            year_str (str | None): Year represented as a string (when non-numeric or formatted).
        """
        super().__init__(name="", locale=locale, coords=coords, text=text)

        self.volume = volume
        self.volume_str = volume_str
        self.year = year
        self.reporter = reporter
        self.reporter_full_name = reporter_full_name
        self.page = page
        self.page_range = page_range
        self.court = court
        self.source = source
        self.article = article
        self.paragraph = paragraph
        self.subparagraph = subparagraph
        self.letter = letter
        self.sentence = sentence
        self.date = date
        self.part = part
        self.year_str = year_str

    def get_cite_value_parts(self) -> list[str]:
        pages = str(self.page_range or self.page or "")
        parts = [
            self.source or "",
            str(self.volume or ""),
            str(self.year or ""),
            pages,
            self.court,
            self.reporter or self.reporter_full_name,
        ]
        return parts

    def get_dictionary_values(self) -> dict:
        df = Map({"tags": {"Extracted Entity Text": self.text}})
        if self.volume:
            df.tags["Extracted Entity Volume"] = self.volume
        if self.year:
            df.tags["Extracted Entity Year"] = str(self.year)
        if self.page:
            df.tags["Extracted Entity Page"] = str(self.page)
        if self.page_range:
            df.tags["Extracted Entity Page Range"] = str(self.page_range)
        if self.reporter:
            df.tags["Extracted Entity Reporter"] = str(self.reporter)
        if self.reporter_full_name:
            df.tags["Extracted Entity Reporter Full Name"] = str(self.reporter_full_name)
        if self.court:
            df.tags["Extracted Entity Court"] = str(self.court)
        if self.source:
            df.tags["Extracted Entity Source"] = str(self.source)

        return df

    def to_dictionary_legacy(self) -> dict[str, Any]:
        return {
            "citation_str": str(self.source),
            "court": self.court,
            "page": self.page,
            "page2": self.page_range,
            "reporter": self.reporter,
            "reporter_full_name": self.reporter_full_name,
            "volume": self.volume,
            "year": self.year,
        }
