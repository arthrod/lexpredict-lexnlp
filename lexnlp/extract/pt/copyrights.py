# pylint: disable=unused-import
# pylint: enable=unused-import

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

from lexnlp.extract.common.annotations.copyright_annotation import CopyrightAnnotation
from lexnlp.extract.common.copyrights.copyright_en_style_parser import CopyrightEnStyleParser
from lexnlp.extract.pt.language_tokens import PtLanguageTokens
from lexnlp.utils.lines_processing.line_processor import LineProcessor, LineSplitParams


class CopyrightPtParser(CopyrightEnStyleParser):
    line_processor = None  # type:LineProcessor

    @staticmethod
    def init_parser():
        """
        Configure and assign the class-level LineProcessor for Portuguese text splitting.
        
        Sets line/phrase break characters to newline and common sentence punctuation, loads Portuguese abbreviations, enables case-insensitive abbreviation matching, and assigns the resulting LineProcessor to the class attribute `line_processor`.
        """
        split_params = LineSplitParams()
        split_params.line_breaks = {'\n', '.', ';', '!', '?'}
        split_params.abbreviations = PtLanguageTokens.abbreviations
        split_params.abbr_ignore_case = True
        CopyrightPtParser.line_processor = LineProcessor(
            line_split_params=split_params)

    @classmethod
    def extract_phrases_with_coords(cls, sentence: str) -> list[tuple[str, int, int]]:
        """
        Extract phrase fragments from a sentence with their character start and end offsets.
        
        Parameters:
            sentence (str): Input text to split into phrase fragments.
        
        Returns:
            A list of (phrase_text, start_index, end_index) tuples where `start_index` is the character index of the phrase's first character and `end_index` is the character index immediately after the phrase's last character in the input sentence.
        """
        return [(t.text, t.start, t.get_end()) for t in
                cls.line_processor.split_text_on_line_with_endings(sentence)]


CopyrightPtParser.init_parser()


def get_copyright_annotations(text: str, return_sources=False) -> Generator[CopyrightAnnotation]:
    """
    Extract copyright annotations from Portuguese text.
    
    Each yielded annotation will have its `locale` attribute set to 'pt'.
    
    Parameters:
        text (str): Input text to scan for copyright statements.
        return_sources (bool): If True, include source span information in produced annotations.
    
    Returns:
        Generator[CopyrightAnnotation]: Generator that yields CopyrightAnnotation objects with `locale` set to 'pt'.
    """
    for ant in CopyrightPtParser.get_copyright_annotations(text, return_sources):
        ant.locale = 'pt'
        yield ant


def get_copyright_annotation_list(text: str, return_sources=False) -> list[CopyrightAnnotation]:
    """
    Extract all copyright annotations from Portuguese text and return them as a list.
    
    Parameters:
        text (str): Input text to scan for copyright notices.
        return_sources (bool): If True, include source/span information with each annotation.
    
    Returns:
        list[CopyrightAnnotation]: Extracted copyright annotation objects.
    """
    return list(get_copyright_annotations(text, return_sources))


def get_copyrights(text: str, return_sources=False) -> Generator[dict]:
    """
    Produce structured representations of copyright annotations found in the given text.
    
    Parameters:
        text (str): Input text to scan for copyright statements.
        return_sources (bool): If True, include source location details in each annotation.
    
    Returns:
        Generator[dict]: An iterator yielding a dictionary for each detected copyright annotation.
            Each dictionary contains the annotation fields (e.g., extracted text, spans, metadata)
            and has its `locale` set to 'pt'.
    """
    for ant in get_copyright_annotations(text, return_sources):
        yield ant.to_dictionary()


def get_copyright_list(text: str, return_sources=False) -> list[dict]:
    """
    Collect all detected copyright annotations from the input text as dictionaries.
    
    Parameters:
        text (str): Text to search for copyright notices.
        return_sources (bool): If True, include source span information in each annotation dictionary.
    
    Returns:
        list[dict]: A list of annotation dictionaries; each dictionary represents a detected copyright annotation and includes a 'locale' key set to 'pt'.
    """
    return list(get_copyrights(text, return_sources))
