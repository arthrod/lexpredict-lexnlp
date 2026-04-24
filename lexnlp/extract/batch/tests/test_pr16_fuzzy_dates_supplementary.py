"""Supplementary tests for :mod:`lexnlp.extract.batch.fuzzy_dates`.

Extends the existing test suite with:
- Direct unit tests for ``_safe_parse`` (boundary and error cases)
- Multi-date extraction
- Immutability of FuzzyDateMatch
- Pattern fix verifications for the PR-16 bug

The module is imported directly to stay compatible with Python < 3.12.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

import importlib.util
import pathlib
from datetime import date

import pytest

# Import directly to bypass the PEP-695 __init__.py.
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.fuzzy_dates",
    str(pathlib.Path(__file__).parent.parent / "fuzzy_dates.py"),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

find_fuzzy_dates = _mod.find_fuzzy_dates
FuzzyDateMatch = _mod.FuzzyDateMatch
_safe_parse = _mod._safe_parse


# ---------------------------------------------------------------------------
# _safe_parse — direct unit tests
# ---------------------------------------------------------------------------


class TestSafeParse:
    """Unit tests for the private ``_safe_parse`` helper."""

    def test_valid_date_returns_date_object(self) -> None:
        result = _safe_parse("2024", "3", "15")
        assert result == date(2024, 3, 15)

    def test_month_boundary_12_valid(self) -> None:
        assert _safe_parse("2024", "12", "31") == date(2024, 12, 31)

    def test_day_boundary_1_valid(self) -> None:
        assert _safe_parse("2024", "1", "1") == date(2024, 1, 1)

    def test_invalid_month_13_returns_none(self) -> None:
        assert _safe_parse("2024", "13", "1") is None

    def test_invalid_month_0_returns_none(self) -> None:
        assert _safe_parse("2024", "0", "1") is None

    def test_invalid_day_0_returns_none(self) -> None:
        assert _safe_parse("2024", "1", "0") is None

    def test_invalid_day_32_returns_none(self) -> None:
        assert _safe_parse("2024", "1", "32") is None

    def test_feb_29_leap_year_valid(self) -> None:
        assert _safe_parse("2024", "2", "29") == date(2024, 2, 29)

    def test_feb_29_non_leap_year_returns_none(self) -> None:
        # 2023 is not a leap year.
        assert _safe_parse("2023", "2", "29") is None

    def test_non_numeric_year_returns_none(self) -> None:
        assert _safe_parse("XXXX", "1", "1") is None

    def test_non_numeric_month_returns_none(self) -> None:
        assert _safe_parse("2024", "XX", "1") is None

    def test_non_numeric_day_returns_none(self) -> None:
        assert _safe_parse("2024", "1", "XX") is None

    def test_empty_strings_return_none(self) -> None:
        assert _safe_parse("", "", "") is None

    def test_leading_zeros_are_valid(self) -> None:
        # "01" and "07" should parse fine.
        assert _safe_parse("2024", "07", "04") == date(2024, 7, 4)

    def test_year_1_is_valid(self) -> None:
        result = _safe_parse("1", "1", "1")
        assert result == date(1, 1, 1)


# ---------------------------------------------------------------------------
# Multiple dates in a single text
# ---------------------------------------------------------------------------


class TestMultipleDatesInText:
    def test_two_adjacent_dates(self) -> None:
        text = "From 2024-01-01 to 2024-12-31."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        parsed = [m.parsed for m in matches]
        assert date(2024, 1, 1) in parsed
        assert date(2024, 12, 31) in parsed

    def test_three_dates_in_long_text(self) -> None:
        text = "Contract signed 2020-03-01, amended 2021-06-15, and terminated 2023-09-30."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        parsed = {m.parsed for m in matches}
        assert date(2020, 3, 1) in parsed
        assert date(2021, 6, 15) in parsed
        assert date(2023, 9, 30) in parsed

    def test_mixed_separators_in_same_text(self) -> None:
        text = "Dates: 2024-01-15 and 2024/02/20 and 2024.03.25"
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 3

    def test_offsets_do_not_overlap(self) -> None:
        """Adjacent date matches must not have overlapping character ranges."""
        text = "From 2024-01-01 to 2024-12-31."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        matches.sort(key=lambda m: m.start)
        for i in range(len(matches) - 1):
            assert matches[i].end <= matches[i + 1].start

    def test_no_dates_returns_empty(self) -> None:
        assert list(find_fuzzy_dates("no dates at all", max_edits=0)) == []

    def test_single_date_in_long_text(self) -> None:
        text = "This agreement is effective as of 2024-07-04 and continues in full force."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 7, 4)


# ---------------------------------------------------------------------------
# FuzzyDateMatch dataclass contract
# ---------------------------------------------------------------------------


class TestFuzzyDateMatchContract:
    def test_is_immutable(self) -> None:
        m = FuzzyDateMatch(start=0, end=10, matched_text="2024-01-01", parsed=date(2024, 1, 1), edit_distance=0)
        with pytest.raises((AttributeError, TypeError)):
            m.start = 5  # type: ignore[misc]

    def test_eq_value_based(self) -> None:
        a = FuzzyDateMatch(start=0, end=10, matched_text="2024-01-01", parsed=date(2024, 1, 1), edit_distance=0)
        b = FuzzyDateMatch(start=0, end=10, matched_text="2024-01-01", parsed=date(2024, 1, 1), edit_distance=0)
        assert a == b

    def test_eq_differs_on_parsed(self) -> None:
        a = FuzzyDateMatch(start=0, end=10, matched_text="2024-01-01", parsed=date(2024, 1, 1), edit_distance=0)
        b = FuzzyDateMatch(start=0, end=10, matched_text="2024-01-01", parsed=None, edit_distance=0)
        assert a != b

    def test_all_fields_accessible(self) -> None:
        d = date(2024, 6, 15)
        m = FuzzyDateMatch(start=5, end=15, matched_text="2024-06-15", parsed=d, edit_distance=0)
        assert m.start == 5
        assert m.end == 15
        assert m.matched_text == "2024-06-15"
        assert m.parsed == d
        assert m.edit_distance == 0

    def test_hashable(self) -> None:
        m = FuzzyDateMatch(start=0, end=10, matched_text="2024-01-01", parsed=date(2024, 1, 1), edit_distance=0)
        s = {m}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# find_fuzzy_dates — max_edits boundary values
# ---------------------------------------------------------------------------


class TestMaxEditsBoundaryValues:
    def test_max_edits_zero_exact_match(self) -> None:
        matches = list(find_fuzzy_dates("2024-03-15", max_edits=0))
        assert len(matches) == 1
        assert matches[0].edit_distance == 0

    def test_max_edits_one_accepted(self) -> None:
        matches = list(find_fuzzy_dates("2024-03-15", max_edits=1))
        assert len(matches) >= 1

    def test_max_edits_two_accepted(self) -> None:
        matches = list(find_fuzzy_dates("2024-03-15", max_edits=2))
        assert len(matches) >= 1

    def test_max_edits_negative_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="max_edits must be >= 0"):
            list(find_fuzzy_dates("2024-03-15", max_edits=-1))

    def test_max_edits_three_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="unreliable"):
            list(find_fuzzy_dates("2024-03-15", max_edits=3))

    def test_max_edits_defaults_to_one(self) -> None:
        # Default should be 1; exact match should always be found.
        matches = list(find_fuzzy_dates("2024-03-15"))
        assert len(matches) >= 1


# ---------------------------------------------------------------------------
# Matched text slice alignment
# ---------------------------------------------------------------------------


class TestMatchedTextSliceAlignment:
    def test_slice_matches_matched_text_zero_budget(self) -> None:
        text = "Signed 2024-07-04 today."
        for m in find_fuzzy_dates(text, max_edits=0):
            assert text[m.start : m.end] == m.matched_text

    def test_slice_matches_matched_text_fuzzy(self) -> None:
        text = "Signed 2024-07-04 today."
        for m in find_fuzzy_dates(text, max_edits=1):
            assert text[m.start : m.end] == m.matched_text

    def test_start_less_than_end(self) -> None:
        text = "Date: 2023-11-30."
        for m in find_fuzzy_dates(text, max_edits=0):
            assert m.start < m.end


# ---------------------------------------------------------------------------
# Malformed dates that parse to None
# ---------------------------------------------------------------------------


class TestMalformedDateParsed:
    def test_invalid_month_parsed_none(self) -> None:
        matches = list(find_fuzzy_dates("2024-13-10", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed is None

    def test_invalid_day_parsed_none(self) -> None:
        matches = list(find_fuzzy_dates("2024-01-32", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed is None

    def test_matched_text_still_present_when_parsed_none(self) -> None:
        matches = list(find_fuzzy_dates("2024-13-01", max_edits=0))
        assert len(matches) == 1
        assert "2024-13-01" in matches[0].matched_text
