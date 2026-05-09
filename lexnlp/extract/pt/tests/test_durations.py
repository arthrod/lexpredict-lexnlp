"""Tests for :mod:`lexnlp.extract.pt.durations`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal
from unittest import TestCase

from lexnlp.extract.pt.durations import (
    get_duration_annotation_list,
    get_duration_annotations,
    get_duration_list,
)


class TestPtDurations(TestCase):
    def test_extracts_simple_year(self):
        ants = get_duration_annotation_list("O contrato tem prazo de 3 anos.")
        self.assertEqual(1, len(ants))
        ant = ants[0]
        self.assertEqual(Decimal("3"), ant.amount)
        self.assertEqual("year", ant.duration_type_en)
        self.assertEqual(Decimal(3) * Decimal(365), ant.duration_days)
        self.assertEqual("pt", ant.locale)

    def test_extracts_meses(self):
        ants = get_duration_annotation_list("Aviso prévio de 30 dias.")
        self.assertEqual(1, len(ants))
        self.assertEqual("day", ants[0].duration_type_en)
        self.assertEqual(Decimal("30"), ants[0].amount)

    def test_extracts_compound_e(self):
        """`2 anos e 6 meses` collapses into a single complex annotation."""
        text = "Vigência de 2 anos e 6 meses, prorrogável."
        ants = get_duration_annotation_list(text)
        self.assertEqual(1, len(ants))
        ant = ants[0]
        self.assertTrue(ant.is_complex)
        self.assertEqual("month", ant.duration_type_en)  # last unit
        # 2*365 + 6*30 = 730 + 180 = 910
        self.assertEqual(Decimal("910"), ant.duration_days)

    def test_separate_durations_not_grouped(self):
        """Sentence terminator ``.`` must break grouping even when the
        second unit is shorter (descending pair) than the first.
        """
        text = "Prazo de 2 anos. Carência de 6 meses."
        ants = get_duration_annotation_list(text)
        self.assertEqual(2, len(ants))

    def test_prefix_captured(self):
        text = "Aproximadamente 5 anos para conclusão."
        ants = get_duration_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertIsNotNone(ants[0].prefix)

    def test_get_duration_list_returns_dicts(self):
        results = get_duration_list("Pagamento em 60 dias.")
        self.assertEqual(1, len(results))
        self.assertEqual(Decimal("60"), results[0]["amount"])
        self.assertEqual("dias", results[0]["duration_type"])

    def test_no_match_in_unrelated_text(self):
        self.assertEqual([], list(get_duration_annotations("Sem prazo definido.")))

    def test_quinzena_recognized(self):
        ants = get_duration_annotation_list("Pagamento a cada 2 quinzenas.")
        self.assertEqual(1, len(ants))
        self.assertEqual("fortnight", ants[0].duration_type_en)
        self.assertEqual(Decimal("28"), ants[0].duration_days)

    def test_compound_text_preserves_separators(self):
        """``2 anos e 6 meses`` keeps the full surface (incl. connector ``e``)."""
        text = "Vigência de 2 anos e 6 meses, prorrogável."
        ants = get_duration_annotation_list(text)
        self.assertEqual(1, len(ants))
        # Exact match — would fail if the separator were dropped (e.g.
        # ``2 anos6 meses``) because of an in-place text concatenation.
        self.assertEqual("2 anos e 6 meses", ants[0].text)

    def test_quarter_unit_does_not_raise(self):
        """``trimestre`` resolves through the Fraction(365, 4) ratio."""
        ants = get_duration_annotation_list("Pagamento em 3 trimestres.")
        self.assertEqual(1, len(ants))
        self.assertEqual("quarter", ants[0].duration_type_en)
        # 3 * 365/4 = 273.75
        self.assertEqual(Decimal("273.75"), ants[0].duration_days)
