"""Tests for :mod:`lexnlp.extract.pt.urls`."""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest import TestCase

from lexnlp.extract.pt.urls import (
    URL_PTN_RE,
    get_url_annotation_list,
    get_urls,
)


class TestPtUrls(TestCase):
    def test_extracts_https(self):
        text = "Disponível em https://www.planalto.gov.br/ccivil_03/leis/L12527.htm"
        urls = list(get_urls(text))
        self.assertEqual(1, len(urls))
        self.assertIn("planalto.gov.br", urls[0])

    def test_locale_is_pt(self):
        text = "Vide https://example.com.br para detalhes."
        ants = get_url_annotation_list(text)
        self.assertEqual(1, len(ants))
        self.assertEqual("pt", ants[0].locale)

    def test_reuses_en_pattern_object(self):
        """The pt module exports the same regex object as EN to avoid drift."""
        from lexnlp.extract.en.urls import URL_PTN_RE as EN_URL_PTN_RE

        self.assertIs(URL_PTN_RE, EN_URL_PTN_RE)

    def test_no_match_in_plain_text(self):
        self.assertEqual([], list(get_urls("Sem links aqui.")))
