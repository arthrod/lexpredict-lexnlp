"""Tests for :mod:`lexnlp.extract.pt.money`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal
from unittest import TestCase

from lexnlp.extract.pt.money import (
    get_money,
    get_money_annotation_list,
    get_money_annotations,
)


class TestPtMoney(TestCase):
    def test_extracts_real_with_prefix(self):
        text = "O valor do contrato é R$ 1.234,56."
        ants = get_money_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("1234.56"), ants[0].amount)
        self.assertEqual("BRL", ants[0].currency)
        self.assertEqual("pt", ants[0].locale)

    def test_extracts_real_no_space(self):
        text = "Multa de R$10.000,00 será aplicada."
        ants = get_money_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("10000.00"), ants[0].amount)
        self.assertEqual("BRL", ants[0].currency)

    def test_extracts_reais_suffix(self):
        text = "O custo é de 1.500,00 reais por mês."
        ants = get_money_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("1500.00"), ants[0].amount)
        self.assertEqual("BRL", ants[0].currency)

    def test_extracts_iso_code_prefix(self):
        text = "Pagamento de USD 1.000,00 deve ser feito."
        ants = get_money_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual("USD", ants[0].currency)

    def test_extracts_iso_code_suffix(self):
        text = "Saldo final: 250,00 EUR ao final do contrato."
        ants = get_money_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual("EUR", ants[0].currency)

    def test_dedupes_prefix_and_suffix(self):
        # If a number has a "R$" prefix the suffix-form (e.g. "reais") should
        # not yield a duplicate annotation for the same amount.
        text = "O custo é R$ 1.500,00 reais."
        ants = get_money_annotation_list(text)
        # We accept either single (preferred) or two non-overlapping matches
        # but never the same span twice.
        spans = {a.coords for a in ants}
        self.assertEqual(len(spans), len(ants))

    def test_get_money_returns_dicts(self):
        text = "Valor: R$ 50,00."
        results = list(get_money(text))
        self.assertEqual(1, len(results))
        self.assertEqual(Decimal("50.00"), results[0]["amount"])
        self.assertEqual("BRL", results[0]["currency"])

    def test_no_money_in_plain_text(self):
        self.assertEqual([], list(get_money_annotations("Sem valores aqui.")))

    def test_overlapping_prefix_and_suffix_dedupe(self):
        """``R$ 100 reais`` overlaps without containment; only one annotation."""
        text = "Pagamento de R$ 100 reais."
        ants = get_money_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("100"), ants[0].amount)

    def test_float_digits_zero_rounds_to_integer(self):
        text = "Valor: R$ 12,7."
        ants = get_money_annotation_list(text, float_digits=0)
        self.assertEqual(1, len(ants))
        # 12.7 rounded to 0 places = 13 (banker's rounding to nearest int)
        self.assertEqual(Decimal("13"), ants[0].amount)
