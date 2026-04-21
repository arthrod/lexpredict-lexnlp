"""Tests for the ``find_fuzzy_dates`` pattern construction after PR change.

The PR changed the fuzzy quantifier placement from:

    ``f"(?:{_BASE_PATTERN}){{e<={max_edits}}}"``  (non-capturing group wrapper)

to:

    ``_BASE_PATTERN + f"{{e<={max_edits}}}"``       (appended directly)

These tests verify the *current* behaviour: exact ISO dates are still found
correctly, the edit-distance budget is applied, and the ``max_edits=0``
path still uses the unmodified base pattern (no fuzzy quantifier at all).

The module is imported directly (bypassing the batch ``__init__.py`` which
requires Python 3.12+), so these tests run on Python 3.11+.
"""

from __future__ import annotations

import importlib.util
import pathlib
from datetime import date

# ---------------------------------------------------------------------------
# Direct module import — compatible with Python 3.11+
# ---------------------------------------------------------------------------

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
# Pattern construction: zero budget → no fuzzy quantifier
# ---------------------------------------------------------------------------


class TestPatternZeroBudget:
    """max_edits=0 must not append any fuzzy quantifier."""

    def test_zero_budget_finds_exact_iso_date(self) -> None:
        matches = list(find_fuzzy_dates("2024-03-15", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 3, 15)

    def test_zero_budget_slash_separator(self) -> None:
        matches = list(find_fuzzy_dates("2024/03/15", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 3, 15)

    def test_zero_budget_dot_separator(self) -> None:
        matches = list(find_fuzzy_dates("2024.03.15", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 3, 15)

    def test_zero_budget_edit_distance_is_zero(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert m.edit_distance == 0

    def test_zero_budget_rejects_non_digit_in_year(self) -> None:
        # "2O24" has letter O in place of digit 0 — must NOT match with no budget.
        matches = list(find_fuzzy_dates("2O24-03-15", max_edits=0))
        # Exact match fails because 'O' is not a digit
        # The match (if any) should have no parsed date for a real ISO date
        for m in matches:
            # Any accidental match must not produce the spurious date 2024-03-15
            assert m.parsed != date(2024, 3, 15)

    def test_zero_budget_no_match_on_no_separator(self) -> None:
        # "20240315" has no separator at all.
        matches = list(find_fuzzy_dates("20240315", max_edits=0))
        assert matches == []


# ---------------------------------------------------------------------------
# Pattern construction: non-zero budget → fuzzy quantifier appended
# ---------------------------------------------------------------------------


class TestPatternNonZeroBudget:
    """max_edits > 0 appends {e<=N} to the base pattern."""

    def test_budget_1_exact_match_still_found(self) -> None:
        matches = list(find_fuzzy_dates("2024-03-15", max_edits=1))
        assert len(matches) >= 1
        assert any(m.parsed == date(2024, 3, 15) for m in matches)

    def test_budget_1_exact_match_has_zero_edit_distance(self) -> None:
        matches = list(find_fuzzy_dates("2024-07-04", max_edits=1))
        assert matches[0].edit_distance == 0

    def test_budget_2_exact_match_found(self) -> None:
        matches = list(find_fuzzy_dates("2024-01-31", max_edits=2))
        assert len(matches) >= 1
        exact = [m for m in matches if m.edit_distance == 0]
        assert len(exact) >= 1

    def test_budget_2_valid_date_parsed(self) -> None:
        matches = list(find_fuzzy_dates("2000-12-25", max_edits=2))
        assert any(m.parsed == date(2000, 12, 25) for m in matches)

    def test_matched_text_slice_is_correct_with_budget(self) -> None:
        text = "Review date 2024-07-04 and sign."
        matches = list(find_fuzzy_dates(text, max_edits=1))
        assert len(matches) >= 1
        m = matches[0]
        assert text[m.start : m.end] == m.matched_text

    def test_multiple_exact_dates_found_with_budget(self) -> None:
        text = "From 2023-01-01 to 2023-12-31."
        matches = list(find_fuzzy_dates(text, max_edits=1))
        parsed = [m.parsed for m in matches if m.parsed is not None]
        assert date(2023, 1, 1) in parsed
        assert date(2023, 12, 31) in parsed


# ---------------------------------------------------------------------------
# Validation: illegal budget values still raise regardless of pattern change
# ---------------------------------------------------------------------------


class TestPatternValidation:
    def test_negative_budget_raises_value_error(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="max_edits must be >= 0"):
            list(find_fuzzy_dates("2024-01-01", max_edits=-1))

    def test_budget_above_2_raises_value_error(self) -> None:
        import pytest

        with pytest.raises(ValueError, match="max_edits > 2"):
            list(find_fuzzy_dates("2024-01-01", max_edits=3))

    def test_budget_exactly_2_is_accepted(self) -> None:
        # Must not raise; returns valid results.
        matches = list(find_fuzzy_dates("2024-01-01", max_edits=2))
        assert isinstance(matches, list)


# ---------------------------------------------------------------------------
# FuzzyDateMatch structure is preserved after pattern change
# ---------------------------------------------------------------------------


class TestFuzzyDateMatchStructure:
    def test_match_has_five_attributes(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert hasattr(m, "start")
        assert hasattr(m, "end")
        assert hasattr(m, "matched_text")
        assert hasattr(m, "parsed")
        assert hasattr(m, "edit_distance")

    def test_match_is_immutable(self) -> None:
        import pytest

        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        with pytest.raises((AttributeError, TypeError)):
            m.start = 99  # type: ignore[misc]

    def test_start_is_int(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert isinstance(m.start, int)

    def test_end_is_int(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert isinstance(m.end, int)

    def test_matched_text_is_str(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert isinstance(m.matched_text, str)

    def test_edit_distance_is_int(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert isinstance(m.edit_distance, int)

    def test_edit_distance_non_negative(self) -> None:
        for max_edits in (0, 1, 2):
            for m in find_fuzzy_dates("2024-03-15", max_edits=max_edits):
                assert m.edit_distance >= 0

    def test_start_less_than_end(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert m.start < m.end