"""Tests for :mod:`lexnlp.extract.pt.percents`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal
from unittest import TestCase

from lexnlp.extract.pt.percents import (
    get_percent_annotation_list,
    get_percent_annotations,
    get_percent_list,
)


class TestPtPercents(TestCase):
    def test_extracts_simple_percent_with_symbol(self):
        text = "A taxa de juros é de 12,5% ao mês."
        results = list(get_percent_annotations(text))
        self.assertEqual(1, len(results))
        ant = results[0]
        self.assertEqual(Decimal("12.5"), ant.amount)
        self.assertEqual(Decimal("0.125"), ant.fraction)
        self.assertEqual("%", ant.sign)
        self.assertEqual("pt", ant.locale)

    def test_extracts_with_thousands_separator(self):
        text = "Aplicou-se o juros de 1.234,56% sobre o valor."
        ants = get_percent_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("1234.56"), ants[0].amount)

    def test_extracts_por_cento(self):
        text = "Aplicou-se uma alíquota de 27,5 por cento."
        ants = get_percent_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("27.5"), ants[0].amount)
        self.assertEqual("por cento", ants[0].sign)

    def test_no_match_for_plain_number(self):
        self.assertEqual([], get_percent_annotation_list("o valor é 100"))

    def test_get_percent_list_returns_dicts(self):
        text = "A meta é 5,5% do PIB."
        results = get_percent_list(text)
        self.assertEqual(1, len(results))
        self.assertEqual(Decimal("5.5"), results[0]["amount"])
        self.assertEqual("%", results[0]["unit_name"])

    def test_extracts_multiple_percents(self):
        text = "Em 2020, 12,5% dos contratos; em 2021, 25%."
        ants = get_percent_annotation_list(text)
        self.assertEqual(2, len(ants))
        amounts = sorted(a.amount for a in ants)
        self.assertEqual([Decimal("12.5"), Decimal("25")], amounts)

    def test_float_digits_zero_rounds(self):
        """``float_digits=0`` is a valid rounding request, not "skip rounding"."""
        ants = get_percent_annotation_list("12,7%", float_digits=0)
        self.assertEqual(1, len(ants))
        # 12.7 * 0.01 = 0.127, rounded to 0 places = 0
        self.assertEqual(Decimal("0"), ants[0].fraction)
