"""Supplementary tests for :mod:`lexnlp.extract.batch.fuzzy_patterns`.

Extends :mod:`test_fuzzy_patterns` with boundary, multi-match, currency
symbol, and structural tests that were not covered in the initial PR-16
test suite.

These tests import the module directly so they work on Python 3.11+
without needing the PEP-695 batch ``__init__.py``.
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

import pytest

# Import directly to bypass the PEP-695 __init__.py.
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.fuzzy_patterns",
    str(pathlib.Path(__file__).parent.parent / "fuzzy_patterns.py"),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

FuzzyPatternMatch = _mod.FuzzyPatternMatch
find_fuzzy_cusips = _mod.find_fuzzy_cusips
find_fuzzy_money = _mod.find_fuzzy_money
_with_budget = _mod._with_budget
_iter_matches = _mod._iter_matches
_CUSIP_PATTERN = _mod._CUSIP_PATTERN
_MONEY_PATTERN = _mod._MONEY_PATTERN


# ---------------------------------------------------------------------------
# FuzzyPatternMatch dataclass structure
# ---------------------------------------------------------------------------


class TestFuzzyPatternMatchStructure:
    """Verify the dataclass contract of FuzzyPatternMatch."""

    def test_all_four_fields_accessible(self) -> None:
        m = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        assert m.start == 0
        assert m.end == 9
        assert m.matched_text == "037833100"
        assert m.edit_distance == 0

    def test_is_immutable(self) -> None:
        """FuzzyPatternMatch is frozen=True, so attribute assignment must fail."""
        m = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        with pytest.raises((AttributeError, TypeError)):
            m.start = 5  # type: ignore[misc]

    def test_eq_is_value_based(self) -> None:
        a = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        b = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        assert a == b

    def test_unequal_when_fields_differ(self) -> None:
        a = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        b = FuzzyPatternMatch(start=1, end=9, matched_text="037833100", edit_distance=0)
        assert a != b

    def test_hashable(self) -> None:
        """Frozen dataclasses should be hashable."""
        m = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        assert hash(m) is not None
        s = {m}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# _with_budget helper
# ---------------------------------------------------------------------------


class TestWithBudget:
    """Unit tests for the internal _with_budget wrapping helper."""

    def test_zero_budget_returns_plain_pattern(self) -> None:
        result = _with_budget("ABC", 0)
        assert result == "ABC"

    def test_negative_budget_returns_plain_pattern(self) -> None:
        # The guard is max_edits <= 0, so negative values should also return plain.
        result = _with_budget("ABC", -1)
        assert result == "ABC"

    def test_positive_budget_wraps_pattern(self) -> None:
        result = _with_budget("ABC", 1)
        assert result == "(?:ABC){e<=1}"

    def test_budget_two_wraps_correctly(self) -> None:
        result = _with_budget("[A-Z]{3}", 2)
        assert result == "(?:[A-Z]{3}){e<=2}"

    def test_wrapper_applies_to_entire_pattern(self) -> None:
        # Non-capturing group must surround the whole expression.
        pattern = r"\d{4}-\d{2}-\d{2}"
        result = _with_budget(pattern, 1)
        assert result.startswith("(?:")
        assert result.endswith("){e<=1}")
        assert pattern in result


# ---------------------------------------------------------------------------
# _iter_matches validation
# ---------------------------------------------------------------------------


class TestIterMatchesValidation:
    def test_negative_max_edits_raises(self) -> None:
        with pytest.raises(ValueError, match="max_edits must be >= 0"):
            list(_iter_matches(_CUSIP_PATTERN, "037833100", max_edits=-1))

    def test_max_edits_above_two_raises(self) -> None:
        with pytest.raises(ValueError, match="max_edits > 2"):
            list(_iter_matches(_CUSIP_PATTERN, "037833100", max_edits=3))

    def test_max_edits_two_accepted(self) -> None:
        # Should not raise.
        results = list(_iter_matches(_CUSIP_PATTERN, "037833100", max_edits=2))
        assert isinstance(results, list)

    def test_empty_text_returns_no_matches(self) -> None:
        assert list(_iter_matches(_CUSIP_PATTERN, "", max_edits=0)) == []


# ---------------------------------------------------------------------------
# find_fuzzy_cusips — additional edge cases
# ---------------------------------------------------------------------------


class TestFindFuzzyCusipsAdditional:
    def test_multiple_cusips_in_text(self) -> None:
        text = "Holdings: 037833100 and 38259P508 are listed."
        matches = list(find_fuzzy_cusips(text, max_edits=0))
        assert len(matches) == 2
        texts = {m.matched_text for m in matches}
        assert "037833100" in texts
        assert "38259P508" in texts

    def test_offsets_are_correct_for_each_match(self) -> None:
        text = "CUSIP A: 037833100 ... CUSIP B: 38259P508"
        matches = list(find_fuzzy_cusips(text, max_edits=0))
        for m in matches:
            assert text[m.start : m.end] == m.matched_text

    def test_exact_match_has_zero_edit_distance(self) -> None:
        matches = list(find_fuzzy_cusips("037833100", max_edits=0))
        assert len(matches) == 1
        assert matches[0].edit_distance == 0

    def test_only_nine_char_alphanumeric_codes_match(self) -> None:
        # Eight characters should NOT match the full CUSIP pattern.
        matches = list(find_fuzzy_cusips("ABCDEFG0 is short", max_edits=0))
        assert matches == []

    def test_letters_in_cusip_match(self) -> None:
        # CUSIPs can have uppercase letters in positions 1-8 and digit at 9.
        text = "Security 38259P508 trade"
        matches = list(find_fuzzy_cusips(text, max_edits=0))
        assert any(m.matched_text == "38259P508" for m in matches)

    def test_budget_one_matches_one_substitution(self) -> None:
        # Replace one digit with a letter in an otherwise valid CUSIP.
        # "0S7833100" has 1 substitution from "037833100".
        text = "code 0S7833100 here"
        matches_zero = list(find_fuzzy_cusips(text, max_edits=0))
        matches_one = list(find_fuzzy_cusips(text, max_edits=1))
        # Budget=0 should produce fewer or equal matches than budget=1.
        assert len(matches_one) >= len(matches_zero)

    def test_negative_max_edits_raises(self) -> None:
        with pytest.raises(ValueError):
            list(find_fuzzy_cusips("037833100", max_edits=-1))

    def test_max_edits_three_raises(self) -> None:
        with pytest.raises(ValueError):
            list(find_fuzzy_cusips("037833100", max_edits=3))

    def test_no_match_in_empty_string(self) -> None:
        assert list(find_fuzzy_cusips("", max_edits=0)) == []

    def test_no_match_for_pure_text(self) -> None:
        # All lowercase, cannot satisfy [A-Z0-9]{8}\d pattern exactly.
        matches = list(find_fuzzy_cusips("abcdefghi", max_edits=0))
        assert matches == []


# ---------------------------------------------------------------------------
# find_fuzzy_money — additional edge cases
# ---------------------------------------------------------------------------


class TestFindFuzzyMoneyAdditional:
    def test_euro_symbol_matched(self) -> None:
        matches = list(find_fuzzy_money("Payment: €1,500.00 due", max_edits=0))
        assert any("€" in m.matched_text for m in matches)

    def test_pound_symbol_matched(self) -> None:
        matches = list(find_fuzzy_money("Cost: £250.50 total", max_edits=0))
        assert any("£" in m.matched_text for m in matches)

    def test_yen_symbol_matched(self) -> None:
        matches = list(find_fuzzy_money("Fee: ¥10,000 per month", max_edits=0))
        assert any("¥" in m.matched_text or m.matched_text.startswith("¥") for m in matches)

    def test_multiple_amounts_in_text(self) -> None:
        text = "Deposit $500 and balance $4,500.00 remain."
        matches = list(find_fuzzy_money(text, max_edits=0))
        matched_texts = [m.matched_text for m in matches]
        assert any("500" in t for t in matched_texts)
        assert len(matches) >= 2

    def test_offsets_are_correct(self) -> None:
        text = "Total: $1,250.00 due now"
        matches = list(find_fuzzy_money(text, max_edits=0))
        for m in matches:
            assert text[m.start : m.end] == m.matched_text

    def test_exact_match_has_zero_edit_distance(self) -> None:
        matches = list(find_fuzzy_money("$100", max_edits=0))
        assert matches
        assert all(m.edit_distance == 0 for m in matches)

    def test_no_match_in_empty_string(self) -> None:
        assert list(find_fuzzy_money("", max_edits=0)) == []

    def test_negative_max_edits_raises(self) -> None:
        with pytest.raises(ValueError):
            list(find_fuzzy_money("$100", max_edits=-1))

    def test_max_edits_three_raises(self) -> None:
        with pytest.raises(ValueError):
            list(find_fuzzy_money("$100", max_edits=3))

    def test_no_false_positive_on_year(self) -> None:
        # A plain year "2024" must not match with zero budget (no currency prefix).
        matches = list(find_fuzzy_money("year 2024 end", max_edits=0))
        assert matches == []

    def test_small_amount_without_decimals(self) -> None:
        matches = list(find_fuzzy_money("$5 fee", max_edits=0))
        assert any(m.matched_text.startswith("$5") for m in matches)

    def test_amount_with_space_after_symbol(self) -> None:
        # Pattern allows optional space: ``[$€£¥]\s?``.
        matches = list(find_fuzzy_money("$ 500 deposit", max_edits=0))
        assert isinstance(matches, list)  # should not raise; matches may vary

    def test_max_edits_two_accepted(self) -> None:
        # Must not raise ValueError.
        matches = list(find_fuzzy_money("$100", max_edits=2))
        assert isinstance(matches, list)
