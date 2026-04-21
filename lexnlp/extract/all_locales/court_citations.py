__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

from lexnlp.extract.all_locales.languages import LANG_DE, Locale
from lexnlp.extract.common.annotations.court_citation_annotation import CourtCitationAnnotation
from lexnlp.extract.de.court_citations import get_court_citation_annotations as get_court_citation_annotations_de

ROUTINE_BY_LOCALE = {
    LANG_DE.code: get_court_citation_annotations_de
}


def get_court_citation_annotations(locale: str, text: str, language: str | None = None) -> \
        Generator[CourtCitationAnnotation]:
    """
        Extract court citation annotations from text using a locale-specific extraction routine.
        
        If no routine is registered for the locale's language, falls back to the German extraction routine.
        
        Parameters:
            locale (str): Locale identifier used to select the extraction routine (e.g., "de_DE").
            text (str): Text to scan for court citation annotations.
            language (str | None): Optional language code to pass to the extraction routine to refine or override locale selection.
        
        Returns:
            Generator[CourtCitationAnnotation]: Yields CourtCitationAnnotation objects found in the text.
        """
    routine = ROUTINE_BY_LOCALE.get(Locale(locale).language, ROUTINE_BY_LOCALE[LANG_DE.code])
    yield from routine(text, language)
