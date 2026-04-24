__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

from lexnlp.extract.common.annotations.court_annotation import CourtAnnotation
from lexnlp.extract.pt.courts import get_court_annotations, get_court_list, get_courts
from lexnlp.tests.typed_annotations_tests import TypedAnnotationsTester


class TestParsePtCourts(TestCase):
    def test_parse_empty_text(self):
        """
        Verify that get_court_list returns no annotations for empty or whitespace-only input.
        """
        ret = get_court_list("")
        self.assertEqual(0, len(ret))
        ret = get_court_list("""

         """)
        self.assertEqual(0, len(ret))

    def test_parse_full_entry(self):
        """
        Verifies that a full Portuguese court name is extracted correctly from a sentence.

        Asserts that exactly one court annotation is returned and that its "Extracted Entity Court Name"
        tag equals "Tribunal de Justiça do Estado de São Paulo".
        """
        text = (
            "O atual Tribunal de Justiça do Estado de São Paulo foi criado em 1874 e é um dos mais antigos do Brasil."
        )
        ret = list(get_courts(text))
        self.assertEqual(1, len(ret))
        court_name = ret[0]["tags"]["Extracted Entity Court Name"]
        self.assertEqual("Tribunal de Justiça do Estado de São Paulo", court_name)

    def test_parse_stf(self):
        """
        Verify the extractor recognizes "Supremo Tribunal Federal" as a Portuguese court.

        Asserts that exactly one court annotation is returned and that its `locale` is "pt".
        """
        text = "A decisão do Supremo Tribunal Federal foi publicada ontem."
        ret = get_court_list(text)
        self.assertEqual(1, len(ret))
        self.assertEqual("pt", ret[0].locale)

    def test_file_samples(self):
        """
        Run typed-annotation validation for Portuguese court annotations using the sample file.

        This test constructs a TypedAnnotationsTester and invokes its test_and_raise_errors method
        to validate get_court_annotations against "lexnlp/typed_annotations/pt/court/courts.txt"
        expecting annotations of type CourtAnnotation; the test fails if validation errors are raised.
        """
        tester = TypedAnnotationsTester()
        tester.test_and_raise_errors(
            get_court_annotations, "lexnlp/typed_annotations/pt/court/courts.txt", CourtAnnotation
        )
