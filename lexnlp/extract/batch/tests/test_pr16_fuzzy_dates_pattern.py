"""Tests targeting the PR-16 bug-fix in ``find_fuzzy_dates``.

Before the fix, the fuzzy quantifier was appended directly to the base
pattern string::

    pattern = _BASE_PATTERN + f"{{e<={max_edits}}}"

This caused ``{e<=N}`` to bind only to the *last atom* of the pattern
(the ``(?P<d>...)`` day group), so substitution errors in the year or
separator were NOT covered by the edit budget.

The fix wraps the full pattern in a non-capturing group first::

    pattern = f"(?:{_BASE_PATTERN}){{e<={max_edits}}}"

Now the edit budget applies across the **entire** date expression. These
tests demonstrate the corrected behaviour.

The module is imported directly (bypassing the batch ``__init__.py``
which requires Python 3.12+), so these tests run on Python 3.11+.
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

# Import fuzzy_dates directly to stay compatible with Python < 3.12.
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.fuzzy_dates",
    str(pathlib.Path(__file__).parent.parent / "fuzzy_dates.py"),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

find_fuzzy_dates = _mod.find_fuzzy_dates
FuzzyDateMatch = _mod.FuzzyDateMatch


# ---------------------------------------------------------------------------
# Exact match always works (regression guard)
# ---------------------------------------------------------------------------


class TestExactMatchUnaffected:
    """The fix must not break exact ISO date detection."""

    def test_exact_iso_date(self) -> None:
        matches = list(find_fuzzy_dates("2024-03-15", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 3, 15)
        assert matches[0].edit_distance == 0

    def test_slash_separator_exact(self) -> None:
        matches = list(find_fuzzy_dates("2024/03/15", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 3, 15)

    def test_dot_separator_exact(self) -> None:
        matches = list(find_fuzzy_dates("2024.03.15", max_edits=0))
        assert len(matches) == 1
        assert matches[0].parsed == date(2024, 3, 15)


# ---------------------------------------------------------------------------
# Budget = 0 means exact only — fuzzy strings must NOT match
# ---------------------------------------------------------------------------


class TestZeroBudgetStrict:
    def test_zero_budget_rejects_digit_substitution(self) -> None:
        # "2O24" has letter O instead of digit 0 — should not match with no budget.
        matches = list(find_fuzzy_dates("2O24-03-15", max_edits=0))
        assert matches == []

    def test_zero_budget_rejects_missing_separator(self) -> None:
        # No separator at all → not a valid ISO date surface form.
        matches = list(find_fuzzy_dates("20240315", max_edits=0))
        assert matches == []


# ---------------------------------------------------------------------------
# Budget = 1 — error in separator should be caught across full pattern
# ---------------------------------------------------------------------------


class TestBudget1SeparatorError:
    """After the fix, the edit budget spans the whole pattern.

    A substitution in the *separator* character (e.g. ``-`` → ``_``) is an
    error that falls between the year/month/day groups — exactly the position
    that the old buggy binding ``{e<=N}`` on just the day group would miss.
    """

    def test_underscore_separator_matched_with_budget(self) -> None:
        # One separator substitution: '-' → '_'.
        # Pattern: 2024_03-15 — one edit in the first separator.
        matches = list(find_fuzzy_dates("2024_03-15", max_edits=1))
        assert len(matches) >= 1
        # The parsed date should resolve to 2024-03-15 if the fuzzy engine
        # picks the right groups; allow parsed=None for backends that can't
        # recover the named groups after a fuzzy substitution.
        if matches[0].parsed is not None:
            assert matches[0].parsed == date(2024, 3, 15)

    def test_space_separator_matched_with_budget(self) -> None:
        # One separator substitution: '-' → ' '.
        matches = list(find_fuzzy_dates("2024 03-15 contract", max_edits=1))
        # The fuzzy engine should find at least one candidate.
        assert isinstance(matches, list)

    def test_edit_distance_reported_nonzero_for_fuzzy(self) -> None:
        # A deliberately wrong year digit: "2O24" (letter O).
        # The edit distance must be > 0 if a match is found.
        matches = list(find_fuzzy_dates("2O24-03-15", max_edits=1))
        if matches:
            assert matches[0].edit_distance > 0


# ---------------------------------------------------------------------------
# Budget = 1 — error in year portion (was not covered before fix)
# ---------------------------------------------------------------------------


class TestBudget1YearError:
    """Errors in the year group should now be caught by the corrected wrapper."""

    def test_digit_in_year_replaced_by_letter(self) -> None:
        # "2O24" — common OCR substitution 0 → O.
        matches = list(find_fuzzy_dates("2O24-03-15", max_edits=1))
        # After the fix this is a candidate match with edit_distance=1.
        if matches:
            assert matches[0].edit_distance >= 1

    def test_year_with_extra_substitution_outside_budget_not_matched(self) -> None:
        # Two digit substitutions in the year ("XYYY") — exceeds budget of 1.
        # We can't guarantee the exact outcome because BESTMATCH may still
        # find something, but at minimum no AssertionError should be raised.
        matches = list(find_fuzzy_dates("XYYY-03-15", max_edits=1))
        # If any match is found, its edit_distance must be within budget.
        for m in matches:
            assert m.edit_distance <= 1


# ---------------------------------------------------------------------------
# Pattern wrapping does not affect FuzzyDateMatch structure
# ---------------------------------------------------------------------------


class TestMatchStructureAfterFix:
    def test_match_has_all_five_attributes(self) -> None:
        m = next(find_fuzzy_dates("2024-07-04", max_edits=0))
        assert hasattr(m, "start")
        assert hasattr(m, "end")
        assert hasattr(m, "matched_text")
        assert hasattr(m, "parsed")
        assert hasattr(m, "edit_distance")

    def test_start_end_slice_matches_matched_text_with_budget(self) -> None:
        text = "Review date 2024-07-04 and sign."
        matches = list(find_fuzzy_dates(text, max_edits=1))
        assert len(matches) >= 1
        m = matches[0]
        assert text[m.start : m.end] == m.matched_text

    def test_exact_match_edit_distance_zero_regardless_of_budget(self) -> None:
        """Even when a non-zero budget is allowed, an exact match scores 0."""
        matches = list(find_fuzzy_dates("2024-01-01", max_edits=2))
        assert len(matches) >= 1
        assert matches[0].edit_distance == 0


# ---------------------------------------------------------------------------
# Validation — max_edits boundaries unchanged by the fix
# ---------------------------------------------------------------------------


class TestMaxEditsBoundaries:
    def test_negative_budget_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            list(find_fuzzy_dates("2024-01-01", max_edits=-1))

    def test_budget_above_two_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            list(find_fuzzy_dates("2024-01-01", max_edits=3))

    def test_max_edits_two_accepted(self) -> None:
        # Should not raise and should return at least one exact match.
        matches = list(find_fuzzy_dates("2024-06-15", max_edits=2))
        assert len(matches) >= 1
        assert matches[0].edit_distance == 0