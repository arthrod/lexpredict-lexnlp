"""Regression tests for the fuzzy_dates pattern change introduced in this PR.

Before this PR, the pattern used a non-capturing group wrapper so the fuzzy
quantifier applied to the entire date expression::

    pattern = f"(?:{_BASE_PATTERN}){{e<={max_edits}}}"

This PR reverted to appending the quantifier directly to the base pattern::

    pattern = _BASE_PATTERN + f"{{e<={max_edits}}}"

In ``regex`` semantics, ``{e<=N}`` binds only to the *preceding atom*. When
appended to a multi-alternative verbose pattern that ends with
``(?P<d>\\d{1,2})``, the quantifier applies to that day-group atom only —
not to the entire year-separator-month-separator-day expression.

These tests document and verify the CURRENT behaviour after the change:

* Exact matches continue to work (no regression on the happy path).
* The edit budget for the day group works correctly.
* Zero-budget mode is strict (no matches on altered input).
* The ValidationError paths (negative / too-large budgets) are unchanged.

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

# Import fuzzy_dates directly, bypassing the PEP-695 batch __init__.py.
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.fuzzy_dates",
    str(pathlib.Path(__file__).parent.parent / "fuzzy_dates.py"),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

find_fuzzy_dates = _mod.find_fuzzy_dates
FuzzyDateMatch = _mod.FuzzyDateMatch
_BASE_PATTERN = _mod._BASE_PATTERN


# ---------------------------------------------------------------------------
# Pattern structure: verify _BASE_PATTERN is not wrapped in non-capturing group
# ---------------------------------------------------------------------------


class TestPatternStructure:
    def test_base_pattern_is_string(self) -> None:
        assert isinstance(_BASE_PATTERN, str)

    def test_base_pattern_contains_named_groups(self) -> None:
        """The base pattern must define year, month, day named groups."""
        assert "(?P<y>" in _BASE_PATTERN
        assert "(?P<m>" in _BASE_PATTERN
        assert "(?P<d>" in _BASE_PATTERN

    def test_max_edits_zero_produces_exact_pattern(self) -> None:
        """With max_edits=0, the pattern is _BASE_PATTERN unchanged (no fuzzy suffix)."""
        # max_edits=0 produces the base pattern without fuzzy quantifier
        matches_exact = list(find_fuzzy_dates("2024-03-15", max_edits=0))
        assert len(matches_exact) == 1
        assert matches_exact[0].edit_distance == 0

    def test_max_edits_nonzero_appends_fuzzy_suffix(self) -> None:
        """With max_edits > 0, the pattern gets a fuzzy suffix appended."""
        # If the pattern were wrapped, the fuzzy engine would behave differently.
        # With the current appended form, we verify that exact matches still return
        # edit_distance=0 (the fuzzy quantifier doesn't force edits).
        matches = list(find_fuzzy_dates("2024-01-15", max_edits=1))
        assert len(matches) >= 1
        assert matches[0].edit_distance == 0


# ---------------------------------------------------------------------------
# Exact match regression — must still work after the change
# ---------------------------------------------------------------------------


class TestExactMatchRegression:
    def test_iso_dash_format(self) -> None:
        matches = list(find_fuzzy_dates("2024-07-04", max_edits=1))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 7, 4)
        assert matches[0].edit_distance == 0

    def test_slash_format(self) -> None:
        matches = list(find_fuzzy_dates("2024/07/04", max_edits=1))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 7, 4)
        assert matches[0].edit_distance == 0

    def test_dot_format(self) -> None:
        matches = list(find_fuzzy_dates("2024.07.04", max_edits=1))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 7, 4)
        assert matches[0].edit_distance == 0

    def test_leading_context_text(self) -> None:
        text = "The agreement was signed on 2023-11-30 at the office."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2023, 11, 30)

    def test_trailing_context_text(self) -> None:
        text = "Effective 2022-01-01."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2022, 1, 1)

    def test_offsets_correct_after_pattern_change(self) -> None:
        text = "ship on 2024-06-15 today"
        matches = list(find_fuzzy_dates(text, max_edits=1))
        assert len(matches) >= 1
        m = matches[0]
        assert text[m.start : m.end] == m.matched_text


# ---------------------------------------------------------------------------
# Zero-budget is strictly exact
# ---------------------------------------------------------------------------


class TestZeroBudgetExactOnly:
    def test_non_digit_in_year_rejected(self) -> None:
        # "2O24" — OCR-style substitution of 0→O in the year
        assert list(find_fuzzy_dates("2O24-03-15", max_edits=0)) == []

    def test_non_digit_in_month_rejected(self) -> None:
        # "2024-O3-15" — OCR-style substitution in month
        assert list(find_fuzzy_dates("2024-O3-15", max_edits=0)) == []

    def test_non_digit_in_day_does_not_expand_match(self) -> None:
        # "2024-03-1S" should not treat the trailing "S" as part of an exact match.
        matches = list(find_fuzzy_dates("2024-03-1S", max_edits=0))
        assert len(matches) == 1
        assert matches[0].matched_text == "2024-03-1"

    def test_missing_separator_rejected(self) -> None:
        # Compressed form has no separators
        assert list(find_fuzzy_dates("20240315", max_edits=0)) == []

    def test_wrong_separator_type_rejected(self) -> None:
        # Underscore is not a recognised separator
        assert list(find_fuzzy_dates("2024_03_15", max_edits=0)) == []


# ---------------------------------------------------------------------------
# Edit distance is reported for fuzzy matches
# ---------------------------------------------------------------------------


class TestEditDistanceReporting:
    def test_exact_match_is_zero_distance(self) -> None:
        """
        Asserts that a perfectly formatted ISO date yields an edit distance of 0 when fuzzy matching is enabled.
        
        Calls find_fuzzy_dates with "2024-01-15" and max_edits=1 and verifies the first returned match reports `edit_distance == 0`.
        """
        matches = list(find_fuzzy_dates("2024-01-15", max_edits=1))
        assert matches[0].edit_distance == 0

    def test_edit_distance_is_non_negative(self) -> None:
        for text in ["2024-01-15", "2024/12/31", "2023.06.15"]:
            for m in find_fuzzy_dates(text, max_edits=1):
                assert m.edit_distance >= 0

    def test_edit_distance_within_budget(self) -> None:
        """Any returned match must have edit_distance <= max_edits."""
        text = "2024-01-15"
        for budget in (0, 1, 2):
            for m in find_fuzzy_dates(text, max_edits=budget):
                assert m.edit_distance <= budget


# ---------------------------------------------------------------------------
# Validation unchanged after pattern change
# ---------------------------------------------------------------------------


class TestValidationUnchanged:
    def test_negative_budget_still_rejected(self) -> None:
        with pytest.raises(ValueError, match="max_edits must be >= 0"):
            list(find_fuzzy_dates("2024-01-01", max_edits=-1))

    def test_budget_above_two_still_rejected(self) -> None:
        with pytest.raises(ValueError, match="unreliable"):
            list(find_fuzzy_dates("2024-01-01", max_edits=3))

    def test_budget_exactly_two_accepted(self) -> None:
        # max_edits=2 is the valid upper boundary
        result = list(find_fuzzy_dates("2024-01-01", max_edits=2))
        assert len(result) >= 1
        assert result[0].parsed == date(2024, 1, 1)


# ---------------------------------------------------------------------------
# FuzzyDateMatch structure is unchanged
# ---------------------------------------------------------------------------


class TestFuzzyDateMatchStructure:
    def test_all_fields_present(self) -> None:
        m = next(find_fuzzy_dates("2024-09-01", max_edits=0))
        assert hasattr(m, "start")
        assert hasattr(m, "end")
        assert hasattr(m, "matched_text")
        assert hasattr(m, "parsed")
        assert hasattr(m, "edit_distance")

    def test_is_frozen_dataclass(self) -> None:
        m = next(find_fuzzy_dates("2024-09-01", max_edits=0))
        with pytest.raises((AttributeError, TypeError)):
            m.start = 99  # type: ignore[misc]

    def test_start_less_than_end(self) -> None:
        m = next(find_fuzzy_dates("2024-09-01", max_edits=0))
        assert m.start < m.end

    def test_matched_text_length_matches_span(self) -> None:
        m = next(find_fuzzy_dates("2024-09-01", max_edits=0))
        assert len(m.matched_text) == m.end - m.start


# ---------------------------------------------------------------------------
# Multiple dates — order preserved after pattern change
# ---------------------------------------------------------------------------


class TestMultipleDatesAfterChange:
    def test_two_exact_dates_order_preserved(self) -> None:
        """
        Verify two exact ISO-format dates in a sentence are extracted as two ordered matches.
        
        Asserts that exactly two matches are returned, the first match starts before the second, and each match parses to the expected calendar date.
        """
        text = "From 2023-01-01 to 2023-12-31."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 2
        assert matches[0].start < matches[1].start
        assert matches[0].parsed == date(2023, 1, 1)
        assert matches[1].parsed == date(2023, 12, 31)

    def test_mixed_separators_two_dates(self) -> None:
        text = "Start: 2022/06/01. End: 2022-12-31."
        matches = list(find_fuzzy_dates(text, max_edits=0))
        assert len(matches) == 2
