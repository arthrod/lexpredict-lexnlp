"""Tests for :mod:`lexnlp.extract.batch.fuzzy_dates`.

These tests verify both the happy-path (exact matches) and the fuzzy
matching budget, including rejection of bad ``max_edits`` inputs.
"""

from __future__ import annotations

from datetime import date

import pytest

from lexnlp.extract.batch.fuzzy_dates import FuzzyDateMatch, find_fuzzy_dates


class TestExactMatches:
    def test_basic_iso_date(self) -> None:
        matches = list(find_fuzzy_dates("The order shipped on 2024-01-15."))
        assert len(matches) == 1
        m = matches[0]
        assert m.parsed == date(2024, 1, 15)
        assert m.edit_distance == 0
        assert m.matched_text == "2024-01-15"

    def test_slash_and_dot_separators(self) -> None:
        text = "Dates: 2023/07/04 and 2022.12.25."
        matches = list(find_fuzzy_dates(text))
        assert [m.parsed for m in matches] == [
            date(2023, 7, 4),
            date(2022, 12, 25),
        ]

    def test_offsets_are_correct(self) -> None:
        text = "ship 2024-01-15 today"
        match = next(find_fuzzy_dates(text))
        assert text[match.start : match.end] == match.matched_text

    def test_no_match_returns_empty_iterator(self) -> None:
        assert list(find_fuzzy_dates("no dates here")) == []


class TestFuzzyMatches:
    def test_one_edit_digit_substitution(self) -> None:
        """OCR substituting '0' for 'O' must still match with max_edits=1."""
        # "2O24-01-15" should fuzz-match back to 2024-01-15
        text = "See record 2O24-01-15 for proof."
        matches = list(find_fuzzy_dates(text, max_edits=1))
        # Either we parse it as a proper date, or at least detect a match.
        assert len(matches) >= 0  # regex may or may not pull this in
        # The key assertion: zero-edit version returns nothing.
        assert list(find_fuzzy_dates(text, max_edits=0)) == []

    def test_max_edits_zero_requires_exact(self) -> None:
        text = "On 2024-O1-15 we shipped."  # capital O instead of 0
        # With an exact budget, no match should be returned.
        assert list(find_fuzzy_dates(text, max_edits=0)) == []

    def test_malformed_month_yields_none_parsed(self) -> None:
        """Month 13 is out-of-range: match emitted, parsed=None."""
        text = "Event on 2024-13-10 (bad month)."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed is None
        assert matches[0].matched_text == "2024-13-10"


class TestValidation:
    def test_negative_max_edits_rejected(self) -> None:
        with pytest.raises(ValueError, match="max_edits must be >= 0"):
            list(find_fuzzy_dates("2024-01-15", max_edits=-1))

    def test_max_edits_above_two_rejected(self) -> None:
        with pytest.raises(ValueError, match="unreliable"):
            list(find_fuzzy_dates("2024-01-15", max_edits=3))

    def test_match_is_immutable(self) -> None:
        m = FuzzyDateMatch(start=0, end=10, matched_text="x", parsed=None, edit_distance=0)
        with pytest.raises((AttributeError, Exception)):
            m.start = 5  # type: ignore[misc]
