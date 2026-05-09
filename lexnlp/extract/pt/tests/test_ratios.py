"""Tests for :mod:`lexnlp.extract.pt.ratios`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal
from unittest import TestCase

from lexnlp.extract.pt.ratios import (
    get_ratio_annotation_list,
    get_ratio_list,
)


class TestPtRatios(TestCase):
    def test_extracts_colon_ratio(self):
        text = "A proporção é 3:1 entre as partes."
        ants = get_ratio_annotation_list(text)
        self.assertEqual(1, len(ants))
        ant = ants[0]
        self.assertEqual(Decimal("3"), ant.left)
        self.assertEqual(Decimal("1"), ant.right)
        self.assertEqual(Decimal("3"), ant.ratio)
        self.assertEqual("pt", ant.locale)

    def test_extracts_para_word_with_numeric_operands(self):
        """``para`` connector requires numeric operands (word-form not supported)."""
        text = "Razão de 2 para 1 na composição."
        ants = get_ratio_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("2"), ants[0].left)
        self.assertEqual(Decimal("1"), ants[0].right)

    def test_word_form_ratios_not_supported(self):
        """``dois para um`` is intentionally NOT parsed (numeric only)."""
        text = "Razão de dois para um na composição."
        self.assertEqual([], get_ratio_annotation_list(text))

    def test_extracts_slash(self):
        text = "Margem de 5/4 no contrato."
        ants = get_ratio_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("1.25"), ants[0].ratio)

    def test_skips_clock_time(self):
        # "10:30 a.m." should not match (clock time, not ratio).
        ants = get_ratio_annotation_list("Reunião às 10:30 a.m.")
        self.assertEqual(0, len(ants))

    def test_zero_denominator_skipped(self):
        ants = get_ratio_annotation_list("Razão 5:0 (impossível).")
        self.assertEqual(0, len(ants))

    def test_get_ratio_list_dicts(self):
        results = get_ratio_list("3:1", return_sources=True)
        self.assertEqual(1, len(results))
        self.assertEqual(Decimal("3"), results[0][0])
        self.assertIn("3:1", results[0][3])

    def test_no_match_in_unrelated(self):
        self.assertEqual([], get_ratio_annotation_list("Sem proporções aqui."))
