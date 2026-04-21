"""Integration tests against real Brazilian federal legislation.

The corpus lives in ``test_data/lexnlp/extract/pt/corpus/`` and was downloaded
from the jonasabreu/leis-federais mirror of planalto.gov.br. These tests do
**not** pin exact counts — planalto occasionally republishes compiled texts
with minor corrections. Instead we assert conservative lower bounds that would
only drop if an extractor regresses.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from pathlib import Path
from unittest import TestCase

import pytest

from lexnlp.extract.pt.dates import get_date_annotations
from lexnlp.extract.pt.definitions import get_definition_annotations
from lexnlp.extract.pt.regulations import (
    FORMAL_CITATION_RE,
    get_regulation_annotations,
)


CORPUS_DIR = Path(__file__).resolve().parents[4] / "test_data" / "lexnlp" / "extract" / "pt" / "corpus"


def _load(name: str) -> str:
    path = CORPUS_DIR / name
    if not path.exists():
        pytest.skip(f"corpus file missing: {path}")
    return path.read_text(encoding="utf-8")


class TestLeiAcessoInformacao(TestCase):
    """Lei nº 12.527/2011 — Lei de Acesso à Informação."""

    @classmethod
    def setUpClass(cls):
        cls.text = _load("lei_12527_lai.txt")

    def test_non_trivial_length(self):
        self.assertGreater(len(self.text), 40_000)

    def test_dates_extraction_is_sane(self):
        dates = list(get_date_annotations(self.text, strict=False))
        self.assertGreater(len(dates), 10)
        years = [d.date.year for d in dates]
        # LAI is from 2011 and cites laws back to the 80s/90s
        in_range = [y for y in years if 1980 <= y <= 2025]
        # All extracted dates should be in the realistic legislative range.
        self.assertEqual(len(dates), len(in_range))

    def test_formal_citations_include_lai(self):
        import regex as re
        flat_text = re.sub(r"\s+", " ", self.text)
        citations = [m.group("full") for m in FORMAL_CITATION_RE.finditer(flat_text)]
        joined = " | ".join(citations)
        self.assertIn("12.527", joined)

    def test_article_references_present(self):
        regs = list(get_regulation_annotations(self.text))
        art_refs = [r for r in regs if r.name.lower().startswith(("art.", "artigo"))]
        self.assertGreater(len(art_refs), 30)

    def test_constitutional_references(self):
        regs = list(get_regulation_annotations(self.text))
        cfs = [r for r in regs if "Constituição" in r.name]
        self.assertGreaterEqual(len(cfs), 1)


class TestCodigoDefesaConsumidor(TestCase):
    """Lei nº 8.078/1990 — Código de Defesa do Consumidor."""

    @classmethod
    def setUpClass(cls):
        cls.text = _load("lei_8078_cdc.txt")

    def test_non_trivial_length(self):
        self.assertGreater(len(self.text), 70_000)

    def test_definitions_present(self):
        # CDC has explicit definitions in art. 2º, 3º ("consumidor é toda pessoa ...")
        defs = list(get_definition_annotations(self.text[:20_000]))
        self.assertGreaterEqual(len(defs), 3)

    def test_regulations_are_plentiful(self):
        regs = list(get_regulation_annotations(self.text))
        self.assertGreater(len(regs), 100)


class TestConstituicaoFederal(TestCase):
    """Constituição Federal de 1988."""

    @classmethod
    def setUpClass(cls):
        cls.text = _load("constituicao_federal.txt")

    def test_non_trivial_length(self):
        self.assertGreater(len(self.text), 300_000)

    def test_self_reference(self):
        regs = list(get_regulation_annotations(self.text))
        cfs = [r for r in regs if "Constituição" in r.name]
        # Constitution references itself dozens of times
        self.assertGreater(len(cfs), 10)
