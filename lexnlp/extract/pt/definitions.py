__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import re
from collections.abc import Generator

from lexnlp.extract.common.annotations.definition_annotation import DefinitionAnnotation
from lexnlp.extract.common.definitions.common_definition_patterns import CommonDefinitionPatterns
from lexnlp.extract.common.definitions.universal_definition_parser import UniversalDefinitionsParser
from lexnlp.extract.common.pattern_found import PatternFound
from lexnlp.extract.pt.language_tokens import PtLanguageTokens
from lexnlp.utils.lines_processing.line_processor import LineSplitParams


class PortugueseParsingMethods:
    """
    the class contains methods with the same signature:
        def method_name(phrase: str) -> List[DefinitionMatch]:
    the methods are used for finding definition "candidates"
    """
    reg_hereafter = re.compile(
        "(?<=((?:doravante|a seguir denominad[oa])[,\\s]))[\\w\\s*\\\"*]+",
        re.UNICODE | re.IGNORECASE,
    )
    reg_reffered = re.compile("^.+(?=(?:refere-se a|significa))", re.UNICODE | re.IGNORECASE)
    reg_first_word_is = re.compile(r"^.+?(?=é\s+\w+\W+\w+|são\s+\w+\W+\w+)", re.UNICODE | re.IGNORECASE)

    @staticmethod
    def match_pt_def_by_hereafter(phrase: str) -> list[PatternFound]:
        """
        :param phrase: as instruções de uso do software ou todas as descrições
                       de uso do mesmo (doravante, a "Documentação");
        :return: {name: 'Documentação', probability: 100, ...}
        """
        reg = PortugueseParsingMethods.reg_hereafter
        dfs = CommonDefinitionPatterns. \
            collect_regex_matches_with_quoted_chunks(phrase, reg, 100,
                                                     lambda p, m, e: 0,
                                                     lambda p, m, e: m.start() + e.end(),
                                                     lambda p, m: 0,
                                                     lambda p, m: m.end())
        return dfs

    @staticmethod
    def match_pt_def_by_reffered(phrase: str) -> list[PatternFound]:
        """
        :param phrase: Neste acordo, o termo "Software" refere-se a: (i) o programa de computador
                       que acompanha este Acordo e todos os seus componentes;
        :return: definitions (objects)
        """
        reg = PortugueseParsingMethods.reg_reffered
        dfs = CommonDefinitionPatterns. \
            collect_regex_matches_with_quoted_chunks(phrase, reg, 100,
                                                     lambda p, m, e: m.start() + e.start(),
                                                     lambda p, m, e: len(phrase),
                                                     lambda p, m: m.start(),
                                                     lambda p, m: len(p))
        return dfs

    @staticmethod
    def match_first_word_is(phrase: str) -> list[PatternFound]:
        """
        :param phrase: O tabagismo é o vício do tabaco, provocado principalmente.
        :return: definitions (objects)
        """
        reg = PortugueseParsingMethods.reg_first_word_is
        dfs = CommonDefinitionPatterns.\
            collect_regex_matches_with_quoted_chunks(phrase, reg, 65,
                                                     lambda p, m, e: m.start() + e.start(),
                                                     lambda p, m, e: len(phrase),
                                                     lambda p, m: m.start(),
                                                     lambda p, m: len(p))
        return dfs


def make_pt_definitions_parser():
    split_params = LineSplitParams()
    split_params.line_breaks = {'\n', '.', ';', '!', '?'}
    split_params.abbreviations = PtLanguageTokens.abbreviations
    split_params.abbr_ignore_case = True

    functions = [CommonDefinitionPatterns.match_es_def_by_semicolon,
                 CommonDefinitionPatterns.match_acronyms,
                 PortugueseParsingMethods.match_pt_def_by_hereafter,
                 PortugueseParsingMethods.match_pt_def_by_reffered,
                 PortugueseParsingMethods.match_first_word_is]

    return UniversalDefinitionsParser(functions, split_params)


parser = make_pt_definitions_parser()


def get_definition_annotations(text: str, language: str = 'pt') -> Generator[DefinitionAnnotation]:
    yield from parser.parse(text, language)


def get_definition_annotation_list(text: str, language: str = 'pt') -> list[DefinitionAnnotation]:
    return list(get_definition_annotations(text, language))


def get_definitions(text: str, language: str = 'pt') -> Generator[dict]:
    for annotation in parser.parse(text, language):
        yield annotation.to_dictionary()


def get_definition_list(text: str, language: str = 'pt') -> list[dict]:
    return list(get_definitions(text, language))
