__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

from lexnlp.extract.common.annotations.definition_annotation import DefinitionAnnotation
from lexnlp.extract.pt.definitions import (
    get_definition_annotation_list,
    get_definition_annotations,
    make_pt_definitions_parser,
)
from lexnlp.tests.typed_annotations_tests import TypedAnnotationsTester


class TestParsePortugueseDefinitions(TestCase):
    def test_parse_pt_def_semicolon(self):
        """
        Verify the Portuguese definitions parser extracts a quoted term followed by a colon as a single definition annotation.
        
        Asserts that exactly one annotation is produced and that its `name` equals the quoted term without surrounding quotation marks.
        """
        parser = make_pt_definitions_parser()
        text = """
        Eu gosto de tocar violão.
        "O ser humano": uma anatomia moderna humana.
        Eu gosto de cantar ao sol"""

        ret = list(parser.parse(text))
        assert len(ret) == 1
        name = ret[0].name
        self.assertEqual("O ser humano", name.strip('"'))

    def test_parse_pt_def_quotes(self):
        """
        Verify the Portuguese definitions parser extracts a quoted term introduced by a colon.
        
        Asserts that parsing the sample text yields exactly one definition annotation and that the annotation's `name`, after stripping surrounding double quotes, equals "Software".
        """
        parser = make_pt_definitions_parser()
        text = 'Mariachi me acompanha quando canto minha canção. Neste acordo, o termo "Software" refere-se a: (i) o programa de computador e todos os seus componentes;'

        ret = list(parser.parse(text))
        assert len(ret) == 1
        name = ret[0].name
        self.assertEqual("Software", name.strip('"'))

    def test_grab_just_quoted_words(self):
        text = """(doravante, "ESET" ou "o Fornecedor") e você"""
        ret = get_definition_annotation_list(text, "ru")
        self.assertEqual(2, len(ret))
        self.assertEqual("ru", ret[1].locale)

        ret = get_definition_annotation_list(text)
        self.assertEqual("pt", ret[1].locale)

    def test_acronym(self):
        parser = make_pt_definitions_parser()

        text = "Pico della Mirandola (PDM)"
        ret = list(parser.parse(text))
        self.assertEqual(1, len(ret))

        text = "pico della Mirandola (PDM)"
        ret = list(parser.parse(text))
        self.assertEqual(0, len(ret))

    def test_file_samples(self):
        tester = TypedAnnotationsTester()
        tester.test_and_raise_errors(
            get_definition_annotations,
            "lexnlp/typed_annotations/pt/definition/definitions.txt",
            DefinitionAnnotation,
        )
