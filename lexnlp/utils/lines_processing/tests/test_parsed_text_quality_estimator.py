"""Tests for :mod:`lexnlp.utils.lines_processing.parsed_text_quality_estimator`.

The PR review flagged:
* ambiguous ``l`` parameter/variable names (renamed to ``line_or_phrase``);
* a mutable class-level ``sentence_break_chars`` which should be
  ``ClassVar`` for PEP 526 compliance (and to silence RUF012).

This test doesn't exercise the full estimator (that requires NLTK + data),
but it verifies the public surface that the rename and annotation
adjustments touched.
"""

from __future__ import annotations

from typing import get_type_hints

from lexnlp.utils.lines_processing.parsed_text_quality_estimator import (
    ParsedTextQualityEstimator,
)


class TestClassAttributes:
    def test_sentence_break_chars_is_classvar(self) -> None:
        hints = get_type_hints(ParsedTextQualityEstimator, include_extras=True)
        annotation = hints["sentence_break_chars"]
        # ``get_type_hints`` unwraps ``ClassVar``, so reach for the raw form.
        raw = ParsedTextQualityEstimator.__annotations__["sentence_break_chars"]
        assert "ClassVar" in str(raw)
        # Sanity check the payload type lines up.
        assert annotation is set[str] or hasattr(annotation, "__origin__")

    def test_sentence_break_chars_defaults(self) -> None:
        assert ParsedTextQualityEstimator.sentence_break_chars == {
            ".",
            ";",
            "!",
            "?",
            ",",
        }


class TestHeaderDetection:
    def test_short_capitalized_line_is_probably_header(self) -> None:
        est = ParsedTextQualityEstimator()
        est.estimate.avg_line_length = 100
        assert est.estimate_line_is_header_prob("Section One") == 65

    def test_line_ending_in_punctuation_is_not_header(self) -> None:
        est = ParsedTextQualityEstimator()
        est.estimate.avg_line_length = 100
        assert est.estimate_line_is_header_prob("This sentence ends.") == 0

    def test_numbered_line_is_header(self) -> None:
        est = ParsedTextQualityEstimator()
        est.estimate.avg_line_length = 100
        assert est.estimate_line_is_header_prob("1. Introduction") == 100
