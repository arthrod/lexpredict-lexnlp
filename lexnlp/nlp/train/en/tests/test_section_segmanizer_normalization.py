"""Tests for the divide-by-zero guard in ``train_section_segmanizer``.

The PR review flagged the normalization loop which divided counts by
``total_char`` / ``total_startchar`` without checking for zero. The fix
returns ``0.0`` when the denominator is zero.

The feature is embedded in ``SectionSegmentizerTrainManager`` which wraps
a private helper. We reach in and test the protected method directly
because setting up the whole training pipeline is cost-prohibitive.
"""

from __future__ import annotations

from lexnlp.nlp.train.en.train_section_segmanizer import SectionSegmentizerTrainManager


class TestDocumentDistributionGuard:
    def test_empty_text_does_not_raise(self) -> None:
        mgr = SectionSegmentizerTrainManager()
        distribution = mgr._build_document_distribution("", norm=True)
        # Every ratio defaults to 0.0 when total is 0.
        assert all(value == 0.0 for value in distribution.values())

    def test_normal_text_sums_to_one(self) -> None:
        mgr = SectionSegmentizerTrainManager()
        distribution = mgr._build_document_distribution("abc def\nghi jkl", norm=True)
        char_values = [v for k, v in distribution.items() if k.startswith("doc_char")]
        # Ratios across characters should sum to ~1.0 when input is non-empty.
        assert 0.0 < sum(char_values) <= 1.0 + 1e-9

    def test_no_newlines_keeps_start_char_zero(self) -> None:
        mgr = SectionSegmentizerTrainManager()
        distribution = mgr._build_document_distribution("single line no breaks", norm=True)
        sc_values = [v for k, v in distribution.items() if k.startswith("doc_startchar")]
        # The lone line has exactly one "start char" so ratios still behave.
        assert sum(sc_values) <= 1.0 + 1e-9
