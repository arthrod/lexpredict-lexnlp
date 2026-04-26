"""Tests for :mod:`lexnlp.extract.ner` hybrid NER fallback."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from unittest.mock import patch

import pytest

from lexnlp.extract.ner import (
    HybridNERMatch,
    augment_rule_matches,
    extract_entities,
    spacy_is_available,
)


def _nltk_data_available() -> bool:
    """Best-effort probe: NLTK ``punkt_tab`` and ``averaged_perceptron_tagger``
    must be downloaded for the NLTK fallback to run end-to-end. CI workers
    that haven't run ``nltk.download(...)`` should skip those tests rather
    than fail."""

    try:
        import nltk

        nltk.data.find("tokenizers/punkt_tab")
        nltk.data.find("taggers/averaged_perceptron_tagger_eng")
        nltk.data.find("chunkers/maxent_ne_chunker_tab")
        nltk.data.find("corpora/words")
    except (ImportError, LookupError):
        return False
    return True


_REQUIRES_NLTK_DATA = pytest.mark.skipif(
    not _nltk_data_available(),
    reason=(
        "NLTK data (punkt_tab, averaged_perceptron_tagger_eng, "
        "maxent_ne_chunker_tab, words) not available in this environment"
    ),
)


class TestSpacyAvailability:
    def test_returns_bool(self) -> None:
        """spacy_is_available() must always return a bool, never raise."""
        result = spacy_is_available()
        assert isinstance(result, bool)

    def test_false_when_spacy_missing(self) -> None:
        """When spaCy is hidden from sys.modules the probe returns False."""
        with patch.dict("sys.modules", {"spacy": None}):
            assert spacy_is_available() is False


class TestExtractEntitiesType:
    def test_text_must_be_str(self) -> None:
        """Non-str input raises TypeError."""
        with pytest.raises(TypeError, match="text must be str"):
            extract_entities(123)  # type: ignore[arg-type]

    @_REQUIRES_NLTK_DATA
    def test_returns_list(self) -> None:
        """extract_entities returns a list (possibly empty), not a generator."""
        result = extract_entities("Acme Corp signed an NDA.", prefer_spacy=False)
        assert isinstance(result, list)

    @_REQUIRES_NLTK_DATA
    def test_returns_match_dataclass(self) -> None:
        """Each item is a HybridNERMatch dataclass with the documented fields."""
        result = extract_entities(
            "John Smith works at Acme Corporation in New York.",
            prefer_spacy=False,
        )
        for item in result:
            assert isinstance(item, HybridNERMatch)
            assert isinstance(item.start, int)
            assert isinstance(item.end, int)
            assert item.start >= 0
            assert item.end > item.start
            assert isinstance(item.label, str) and item.label
            assert item.backend in {"spacy", "nltk"}

    @_REQUIRES_NLTK_DATA
    def test_match_offsets_round_trip(self) -> None:
        """``text[start:end] == match.text`` for every emitted match."""
        sample = "John Smith works at Acme Corporation in New York."
        result = extract_entities(sample, prefer_spacy=False)
        for match in result:
            assert sample[match.start : match.end] == match.text


class TestPreferSpacyToggle:
    @_REQUIRES_NLTK_DATA
    def test_prefer_spacy_false_forces_nltk(self) -> None:
        """prefer_spacy=False uses NLTK regardless of spaCy availability."""
        result = extract_entities("Apple announced a product.", prefer_spacy=False)
        assert all(m.backend == "nltk" for m in result)


class TestAugmentRuleMatches:
    def test_drops_hybrid_match_overlapping_rule(self) -> None:
        """Hybrid matches that overlap >=50% of the shorter span are dropped."""
        rule_spans = [(0, 10, "PARTY")]
        hybrid = [
            HybridNERMatch(start=0, end=10, text="Acme Corp.", label="ORG", backend="nltk"),
            HybridNERMatch(start=20, end=29, text="John Doe", label="PERSON", backend="nltk"),
        ]
        merged = augment_rule_matches(rule_spans, hybrid)
        assert [(m.start, m.end) for m in merged] == [(20, 29)]

    def test_keeps_hybrid_match_with_no_overlap(self) -> None:
        """Hybrid matches that don't overlap any rule span are kept in order."""
        rule_spans = [(50, 60, "MONEY")]
        hybrid = [
            HybridNERMatch(start=20, end=29, text="John Doe", label="PERSON", backend="nltk"),
            HybridNERMatch(start=0, end=10, text="Acme Corp", label="ORG", backend="nltk"),
        ]
        merged = augment_rule_matches(rule_spans, hybrid)
        assert [(m.start, m.end) for m in merged] == [(0, 10), (20, 29)]

    def test_partial_overlap_below_threshold_kept(self) -> None:
        """An overlap strictly below the threshold (default 0.5) keeps both."""
        rule_spans = [(0, 10, "PARTY")]  # length 10
        hybrid = [
            # Hybrid span (8, 30) -> overlap=2, shorter=10, ratio=0.2 < 0.5 keep.
            HybridNERMatch(start=8, end=30, text="...", label="ORG", backend="nltk"),
        ]
        merged = augment_rule_matches(rule_spans, hybrid)
        assert len(merged) == 1

    def test_threshold_is_configurable(self) -> None:
        """Lower threshold means more aggressive suppression."""
        rule_spans = [(0, 10, "PARTY")]
        hybrid = [
            HybridNERMatch(start=8, end=30, text="...", label="ORG", backend="nltk"),
        ]
        # threshold 0.1 should now suppress the hybrid match.
        merged = augment_rule_matches(rule_spans, hybrid, overlap_threshold=0.1)
        assert merged == []
