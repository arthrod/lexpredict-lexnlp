"""Tests for :mod:`lexnlp.extract.pt.distances`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from decimal import Decimal
from unittest import TestCase

from lexnlp.extract.pt.distances import (
    get_distance_annotation_list,
    get_distance_list,
)


class TestPtDistances(TestCase):
    def test_extracts_kilometers_word(self):
        text = "A obra cobre 12,5 quilômetros de estrada."
        ants = get_distance_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("12.5"), ants[0].amount)
        self.assertEqual("kilometer", ants[0].distance_type)
        self.assertEqual("pt", ants[0].locale)

    def test_extracts_km_symbol(self):
        text = "Distância máxima: 100 km do litoral."
        ants = get_distance_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("100"), ants[0].amount)
        self.assertEqual("kilometer", ants[0].distance_type)

    def test_extracts_metros(self):
        text = "Recuo mínimo de 5 metros do alinhamento."
        ants = get_distance_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual("meter", ants[0].distance_type)

    def test_extracts_milhas(self):
        text = "Distância oficial de 26 milhas."
        ants = get_distance_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual("mile", ants[0].distance_type)

    def test_thousands_separator(self):
        text = "O perímetro chega a 1.234,56 metros."
        ants = get_distance_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual(Decimal("1234.56"), ants[0].amount)

    def test_get_distance_list_with_sources(self):
        results = get_distance_list("100 km", return_sources=True)
        self.assertEqual(1, len(results))
        self.assertEqual(Decimal("100"), results[0][0])
        self.assertEqual("kilometer", results[0][1])
        self.assertIn("100", results[0][2])

    def test_no_match_in_unrelated_text(self):
        self.assertEqual([], get_distance_annotation_list("Sem distâncias citadas."))
