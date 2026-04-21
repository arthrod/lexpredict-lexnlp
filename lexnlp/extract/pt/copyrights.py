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
        Initialize the shared LineProcessor for Portuguese text parsing.
        
        Configures sentence-splitting parameters (newline and common punctuation boundaries), loads Portuguese abbreviations, enables case-insensitive abbreviation matching, and assigns the resulting LineProcessor to the class-level `line_processor`.
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
        Extract phrases from a sentence along with their character start and end positions.
        
        Parameters:
            sentence (str): Input sentence to split into phrases.
        
        Returns:
            list[tuple[str, int, int]]: List of tuples (phrase_text, start_index, end_index) giving each phrase and its start and end character indices within the input sentence.
        """
        return [(t.text, t.start, t.get_end()) for t in
                cls.line_processor.split_text_on_line_with_endings(sentence)]


CopyrightPtParser.init_parser()


def get_copyright_annotations(text: str, return_sources=False) -> Generator[CopyrightAnnotation]:
    """
    Yield copyright annotations extracted from Portuguese text.
    
    Iterates over annotations produced by the Portuguese parser, sets each annotation's
    `locale` to 'pt', and yields them.
    
    Parameters:
    	text (str): Input text to search for copyright annotations.
    	return_sources (bool): If True, include source span information in produced annotations.
    
    Returns:
    	Generator[CopyrightAnnotation]: Generator yielding CopyrightAnnotation objects with `locale` set to 'pt'.
    """
    for ant in CopyrightPtParser.get_copyright_annotations(text, return_sources):
        ant.locale = 'pt'
        yield ant


def get_copyright_annotation_list(text: str, return_sources=False) -> list[CopyrightAnnotation]:
    """
    Return all copyright annotations extracted from Portuguese text as a list.
    
    Parameters:
        text (str): Input text to scan for copyright notices.
        return_sources (bool): If True, include source information with each annotation.
    
    Returns:
        list[CopyrightAnnotation]: List of extracted copyright annotations.
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
    Return all detected copyright annotations in the input text as dictionaries.
    
    Parameters:
        text (str): Text to search for copyright notices.
        return_sources (bool): If true, include source span information in each annotation dictionary.
    
    Returns:
        list[dict]: A list of dictionaries where each dictionary represents a detected copyright annotation and includes a 'locale' key set to 'pt'.
    """
    return list(get_copyrights(text, return_sources))
