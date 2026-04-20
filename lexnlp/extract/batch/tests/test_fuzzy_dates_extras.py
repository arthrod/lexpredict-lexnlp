"""Additional tests for :mod:`lexnlp.extract.batch.fuzzy_dates`.

Supplements ``test_fuzzy_dates.py`` with boundary conditions and internal
helper coverage not exercised in the primary suite:

* ``_safe_parse`` with out-of-range values (month 0, day 0, month 13)
* max_edits=2 (valid upper boundary)
* Multiple distinct dates in a single string
* February 29 in a non-leap year → parsed=None
* February 29 in a leap year → parsed is a valid date
* Empty string input
* FuzzyDateMatch attribute access (all five attributes)
* Separator mixing within a single string
* ``find_fuzzy_dates`` returns an iterator (lazy), not a list
"""

from __future__ import annotations

import importlib.util
from datetime import date

import pytest

# Import fuzzy_dates directly, bypassing the batch __init__.py which uses
# PEP 695 syntax (Python 3.12+). The fuzzy_dates module itself is compatible
# with Python 3.11+.
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.fuzzy_dates",
    str(
        __import__("pathlib").Path(__file__).parent.parent / "fuzzy_dates.py"
    ),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

FuzzyDateMatch = _mod.FuzzyDateMatch
_safe_parse = _mod._safe_parse
find_fuzzy_dates = _mod.find_fuzzy_dates


# ---------------------------------------------------------------------------
# _safe_parse — internal helper
# ---------------------------------------------------------------------------


class TestSafeParse:
    def test_valid_date(self) -> None:
        assert _safe_parse("2024", "6", "15") == date(2024, 6, 15)

    def test_month_zero_returns_none(self) -> None:
        assert _safe_parse("2024", "0", "1") is None

    def test_day_zero_returns_none(self) -> None:
        assert _safe_parse("2024", "1", "0") is None

    def test_month_thirteen_returns_none(self) -> None:
        assert _safe_parse("2024", "13", "1") is None

    def test_day_out_of_range_returns_none(self) -> None:
        assert _safe_parse("2024", "2", "30") is None  # Feb 30 never exists

    def test_leap_year_feb_29_valid(self) -> None:
        assert _safe_parse("2024", "2", "29") == date(2024, 2, 29)

    def test_non_leap_year_feb_29_returns_none(self) -> None:
        # 2023 is not a leap year
        assert _safe_parse("2023", "2", "29") is None

    def test_year_zero_returns_none(self) -> None:
        # datetime.date does not support year 0
        assert _safe_parse("0", "1", "1") is None

    def test_non_numeric_string_returns_none(self) -> None:
        assert _safe_parse("ABCD", "01", "01") is None

    def test_day_31_valid_for_january(self) -> None:
        assert _safe_parse("2024", "1", "31") == date(2024, 1, 31)

    def test_day_31_invalid_for_april_returns_none(self) -> None:
        assert _safe_parse("2024", "4", "31") is None  # April has 30 days


# ---------------------------------------------------------------------------
# Multiple dates in a single string
# ---------------------------------------------------------------------------


class TestMultipleDatesInText:
    def test_two_dates(self) -> None:
        text = "From 2023-01-01 to 2023-12-31."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 2
        assert matches[0].parsed == date(2023, 1, 1)
        assert matches[1].parsed == date(2023, 12, 31)

    def test_three_dates(self) -> None:
        text = "Signed 2020-01-01, renewed 2021-06-15, expires 2025-09-30."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        parsed = [m.parsed for m in matches]
        assert date(2020, 1, 1) in parsed
        assert date(2021, 6, 15) in parsed
        assert date(2025, 9, 30) in parsed

    def test_dates_maintain_left_to_right_order(self) -> None:
        text = "2019-03-10 then 2024-07-04 then 2030-11-11"
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert matches[0].start < matches[1].start < matches[2].start

    def test_mixed_separators_in_one_string(self) -> None:
        text = "Start: 2022/06/01. End: 2022-12-31."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 2


# ---------------------------------------------------------------------------
# Boundary: max_edits=2
# ---------------------------------------------------------------------------


class TestMaxEdits2:
    def test_valid_upper_boundary_accepted(self) -> None:
        # max_edits=2 must not raise.
        result = list(find_fuzzy_dates("2024-01-15", max_edits=2))
        assert len(result) >= 1
        assert result[0].parsed == date(2024, 1, 15)

    def test_exact_match_has_edit_distance_zero_even_with_budget_two(self) -> None:
        result = list(find_fuzzy_dates("2024-01-15", max_edits=2))
        assert result[0].edit_distance == 0


# ---------------------------------------------------------------------------
# Calendar boundaries
# ---------------------------------------------------------------------------


class TestCalendarBoundaries:
    def test_leap_year_feb_29(self) -> None:
        matches = list(find_fuzzy_dates("2024-02-29", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 2, 29)

    def test_non_leap_year_feb_29_parsed_none(self) -> None:
        matches = list(find_fuzzy_dates("2023-02-29", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed is None

    def test_dec_31(self) -> None:
        matches = list(find_fuzzy_dates("2024-12-31", max_edits=0))
        assert matches[0].parsed == date(2024, 12, 31)

    def test_jan_1(self) -> None:
        matches = list(find_fuzzy_dates("2000-01-01", max_edits=0))
        assert matches[0].parsed == date(2000, 1, 1)


# ---------------------------------------------------------------------------
# Empty and whitespace inputs
# ---------------------------------------------------------------------------


class TestEdgeInputs:
    def test_empty_string_yields_nothing(self) -> None:
        assert list(find_fuzzy_dates("", max_edits=0)) == []

    def test_whitespace_only_yields_nothing(self) -> None:
        assert list(find_fuzzy_dates("   \n\t  ", max_edits=0)) == []

    def test_no_date_content_yields_nothing(self) -> None:
        assert list(find_fuzzy_dates("The quick brown fox.", max_edits=0)) == []

    def test_partial_date_not_matched(self) -> None:
        # "2024-01" alone is not a full ISO date
        assert list(find_fuzzy_dates("2024-01", max_edits=0)) == []


# ---------------------------------------------------------------------------
# FuzzyDateMatch attribute access
# ---------------------------------------------------------------------------


class TestFuzzyDateMatchAttributes:
    def test_all_attributes_accessible(self) -> None:
        m = next(find_fuzzy_dates("Order dated 2024-07-04 here.", max_edits=0))
        assert isinstance(m.start, int)
        assert isinstance(m.end, int)
        assert isinstance(m.matched_text, str)
        assert m.parsed == date(2024, 7, 4) or m.parsed is None
        assert isinstance(m.edit_distance, int)

    def test_start_end_slice_matches_matched_text(self) -> None:
        text = "Filed on 2021-11-05 for review."
        m = next(find_fuzzy_dates(text, max_edits=0))
        assert text[m.start : m.end] == m.matched_text

    def test_edit_distance_is_zero_for_exact(self) -> None:
        m = next(find_fuzzy_dates("2024-03-15", max_edits=0))
        assert m.edit_distance == 0


# ---------------------------------------------------------------------------
# find_fuzzy_dates returns an iterator (lazy)
# ---------------------------------------------------------------------------


class TestLazyIterator:
    def test_returns_iterator_not_list(self) -> None:
        from collections.abc import Iterator

        result = find_fuzzy_dates("2024-01-01", max_edits=0)
        assert isinstance(result, Iterator)

    def test_can_iterate_multiple_times_via_list(self) -> None:
        matches = list(find_fuzzy_dates("2024-01-01 and 2024-06-15", max_edits=0))
        assert len(matches) == 2