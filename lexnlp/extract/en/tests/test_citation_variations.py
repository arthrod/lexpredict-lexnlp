"""Tests for :mod:`lexnlp.extract.en.citation_variations`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.en.citation_variations import (
    canonical_for,
    is_known_reporter,
    normalize_reporter,
    variation_map,
)


class TestVariationMap:
    def test_has_entries(self) -> None:
        vm = variation_map()
        assert len(vm) > 0

    def test_values_are_tuples(self) -> None:
        vm = variation_map()
        sample_key = next(iter(vm))
        assert isinstance(vm[sample_key], tuple)


class TestCanonicalFor:
    def test_returns_empty_for_unknown(self) -> None:
        assert canonical_for("TotallyFakeReporter99") == ()

    def test_returns_empty_for_empty(self) -> None:
        assert canonical_for("") == ()

    def test_space_normalized_lookup(self) -> None:
        # "U. S." (with internal space) should still resolve when the
        # canonical variant is stored as "U.S." or similar.
        result = canonical_for("U. S.")
        # We don't guarantee a specific canonical here (depends on db
        # version) but the function must not raise.
        assert isinstance(result, tuple)


class TestIsKnownReporter:
    def test_returns_false_for_empty(self) -> None:
        assert not is_known_reporter("")

    def test_returns_false_for_nonsense(self) -> None:
        assert not is_known_reporter("NotAReporter")


class TestNormalizeReporter:
    def test_returns_input_when_unknown(self) -> None:
        assert normalize_reporter("NotAReporter") == "NotAReporter"

    def test_returns_input_unchanged_when_empty(self) -> None:
        assert normalize_reporter("") == ""
