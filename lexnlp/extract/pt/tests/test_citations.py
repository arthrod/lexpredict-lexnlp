"""Tests for :mod:`lexnlp.extract.pt.citations`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

from lexnlp.extract.pt.citations import (
    get_case_citation_annotations,
    get_citation_annotation_list,
    get_cnj_process_annotations,
)


class TestBrazilianCaseCitations(TestCase):
    def test_extracts_resp_with_uf(self):
        text = "Vide o REsp 12.345/SP julgado em 2020."
        ants = list(get_case_citation_annotations(text))
        self.assertEqual(1, len(ants))
        ant = ants[0]
        self.assertEqual("REsp", ant.reporter)
        self.assertEqual("SP", ant.court)
        self.assertEqual("pt", ant.locale)

    def test_extracts_re(self):
        text = "Conforme o RE 123.456 do STF."
        ants = list(get_case_citation_annotations(text))
        self.assertEqual(1, len(ants))
        self.assertEqual("RE", ants[0].reporter)
        self.assertEqual(123456, ants[0].volume)

    def test_extracts_adi(self):
        text = "A ADI 1.234 foi julgada procedente."
        ants = list(get_case_citation_annotations(text))
        self.assertEqual(1, len(ants))
        self.assertEqual("ADI", ants[0].reporter)

    def test_extracts_agrg_no_aresp(self):
        text = "Posteriormente, AgRg no AREsp 234.567/RS confirmou o entendimento."
        ants = list(get_case_citation_annotations(text))
        self.assertEqual(1, len(ants))
        self.assertEqual("AgRg no AREsp", ants[0].reporter)

    def test_extracts_hc(self):
        text = "Concedido o HC 99.999 em decisão monocrática."
        ants = list(get_case_citation_annotations(text))
        self.assertEqual(1, len(ants))
        self.assertEqual("HC", ants[0].reporter)

    def test_year_normalisation(self):
        text = "Conforme RE 123/85 do plenário."
        ants = list(get_case_citation_annotations(text))
        self.assertEqual(1, len(ants))
        self.assertEqual(1985, ants[0].year)


class TestCnjProcessNumbers(TestCase):
    def test_extracts_full_cnj_format(self):
        text = "O processo 1234567-89.2020.5.04.0001 foi distribuído."
        ants = list(get_cnj_process_annotations(text))
        self.assertEqual(1, len(ants))
        ant = ants[0]
        self.assertEqual(2020, ant.year)
        self.assertIn("seg=5", ant.volume_str)
        self.assertIn("tr=04", ant.volume_str)
        self.assertIn("orig=0001", ant.volume_str)
        self.assertEqual("pt", ant.locale)

    def test_no_match_for_partial_format(self):
        text = "Número parcial 1234567-89."
        self.assertEqual([], list(get_cnj_process_annotations(text)))


class TestGetCitationAnnotations(TestCase):
    def test_combined_stream(self):
        text = "REsp 1.000/SP combinado com 9876543-21.2019.8.26.0100."
        ants = get_citation_annotation_list(text)
        # One short-form + one CNJ-format = 2 annotations.
        self.assertEqual(2, len(ants))

    def test_no_match_in_plain_text(self):
        self.assertEqual([], get_citation_annotation_list("Sem citações aqui."))
