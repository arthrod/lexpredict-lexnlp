#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Multi-language unit tests for Portuguese Dates.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from functools import partial
from unittest import TestCase

from lexnlp.extract.common.annotations.date_annotation import DateAnnotation
from lexnlp.extract.pt.dates import get_date_annotations
from lexnlp.tests.typed_annotations_tests import TypedAnnotationsTester


class TestParsePtDates(TestCase):
    def test_pt_dates(self):
        """
        Verify that Portuguese date expressions in a sample text are detected.

        Asserts that calling get_date_annotations on a Portuguese sample text with strict=False produces at least three date annotations.
        """
        text = (
            "Algum texto de exemplo com data em português como 15 de fevereiro, "
            + "28 de abril e 17 de novembro de 1995, 1ºde janeiro de 1999 "
        )
        ants = list(get_date_annotations(text=text, strict=False))
        self.assertGreaterEqual(len(ants), 3)

    def test_file_samples(self):
        """
        Run validation of Portuguese date annotations against the sample file.

        Uses TypedAnnotationsTester to run get_date_annotations (with strict=False) on examples from
        "lexnlp/typed_annotations/pt/date/dates.txt" and raises an error if any produced annotation
        does not match the expected DateAnnotation type.
        """
        tester = TypedAnnotationsTester()
        tester.test_and_raise_errors(
            partial(get_date_annotations, strict=False), "lexnlp/typed_annotations/pt/date/dates.txt", DateAnnotation
        )
