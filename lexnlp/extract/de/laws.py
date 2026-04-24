__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

from pandas import DataFrame

from lexnlp.extract.common.annotations.law_annotation import LawAnnotation
from lexnlp.extract.de.language_tokens import DeLanguageTokens
from lexnlp.utils.lines_processing.line_processor import LineProcessor, LineSplitParams
from lexnlp.utils.parse_df import DataframeEntityParser

ANNOTATION_SET_NAME = "Laws and Rules"


class LawsParser:
    def __init__(self, gesetze_df: DataFrame, verordnungen_df: DataFrame, concept_df: DataFrame):
        parse_columns = ("Kurztitel", "Titel", "Abkürzung")
        dependent_columns = {"Titel": "External Reference Normalized"}
        preformed_entity = {
            "External Reference Type": "Laws and Rules",
            "External Reference Source": "BaFin",
            "External Reference Issuing Country": "Germany",
        }
        split_params = LineSplitParams()
        split_params.line_breaks = {".", ";", "!", "?"}
        split_params.abbreviations = DeLanguageTokens.abbreviations
        split_params.abbr_ignore_case = True
        proc = LineProcessor(line_split_params=split_params)

        self.gesetze_parser = DataframeEntityParser(
            gesetze_df,
            parse_columns,
            result_columns=dependent_columns,
            preformed_entity=preformed_entity,
            line_processor=proc,
        )

        self.verordnungen_parser = DataframeEntityParser(
            verordnungen_df,
            parse_columns,
            result_columns=dependent_columns,
            preformed_entity=preformed_entity,
            line_processor=proc,
        )

        parse_columns = ("b",)
        dependent_columns = {"b": "External Reference Normalized", "a": "External Reference Type"}
        preformed_entity.pop("External Reference Type")

        self.concept_parser = DataframeEntityParser(
            concept_df,
            parse_columns,
            result_columns=dependent_columns,
            preformed_entity=preformed_entity,
            line_processor=proc,
        )

    def parse(self, text: str, locale: str = "de") -> Generator[LawAnnotation]:

        for entity in self.gesetze_parser.get_entity_list(text):
            annotation = LawAnnotation(
                name=entity["source"],
                coords=(entity["location_start"], entity["location_end"]),
                text=entity["source"],
                locale=locale,
            )
            yield annotation

        for entity in self.verordnungen_parser.get_entity_list(text):
            annotation = LawAnnotation(
                name=entity["source"],
                coords=(entity["location_start"], entity["location_end"]),
                text=entity["source"],
                locale=locale,
            )
            yield annotation

        for entity in self.concept_parser.get_entity_list(text):
            annotation = LawAnnotation(
                name=entity["source"],
                coords=(entity["location_start"], entity["location_end"]),
                text=entity["source"],
                locale=locale,
            )
            yield annotation


parser: LawsParser | None = None


def get_law_annotations(text: str, language: str = "de") -> Generator[LawAnnotation]:
    """
    Yield law and rule annotations found in the given text.

    If the module-level parser is not initialized, nothing is yielded.

    Parameters:
        text (str): Text to scan for law or rule mentions.
        language (str): Locale code used for parsing (e.g., 'de').

    Returns:
        Generator[LawAnnotation]: `LawAnnotation` objects for each detected law or rule.
    """
    if not parser:
        return
    yield from parser.parse(text, language)


def get_law_annotation_list(text: str, language: str = "de") -> list[LawAnnotation]:
    return list(get_law_annotations(text, language))


def get_laws(text: str, language: str = "de") -> Generator[dict]:
    for annotation in get_law_annotations(text, language):
        yield annotation.to_dictionary()


def get_law_list(text: str, language: str = "de") -> list[dict]:
    return list(get_laws(text, language))
