"""Tests for :mod:`lexnlp.extract.pt.trademarks`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

from lexnlp.extract.pt.trademarks import (
    get_entity_suffix_list,
    get_trademark_annotation_list,
    get_trademark_list,
)


class TestPtTrademarks(TestCase):
    def test_detects_registered_symbol(self):
        text = "A Empresa® está registrada."
        results = get_trademark_list(text)
        self.assertTrue(any("®" in r for r in results))

    def test_detects_tm_symbol(self):
        text = "Marca™ pertence à empresa."
        results = get_trademark_list(text)
        self.assertTrue(any("™" in r for r in results))

    def test_locale_is_pt(self):
        ants = get_trademark_annotation_list("Foo® bar")
        self.assertTrue(all(a.locale == "pt" for a in ants))

    def test_no_match_in_plain_text(self):
        self.assertEqual([], get_trademark_list("Sem marca registrada aqui."))


class TestPtEntitySuffixes(TestCase):
    def test_detects_ltda(self):
        text = "A Construtora ABC Ltda. assinou o contrato."
        ants = get_entity_suffix_list(text)
        self.assertEqual(1, len(ants))
        self.assertIn("Ltda", ants[0].trademark)
        self.assertIn("ABC", ants[0].trademark)

    def test_detects_sa(self):
        text = "Empresa XYZ S.A. é a contratante."
        ants = get_entity_suffix_list(text)
        self.assertEqual(1, len(ants))
        self.assertIn("S.A.", ants[0].trademark)

    def test_detects_eireli(self):
        text = "A Foo Bar EIRELI emitiu a nota."
        ants = get_entity_suffix_list(text)
        self.assertEqual(1, len(ants))
        self.assertIn("EIRELI", ants[0].trademark)

    def test_detects_s_slash_a(self):
        text = "A Empresa Z S/A pagou o débito."
        ants = get_entity_suffix_list(text)
        self.assertEqual(1, len(ants))

    def test_no_suffix_match(self):
        self.assertEqual([], get_entity_suffix_list("Texto sem empresa."))
