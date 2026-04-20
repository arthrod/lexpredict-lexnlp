"""Tests for :mod:`lexnlp.extract.batch.fuzzy_patterns`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import pytest

from lexnlp.extract.batch.fuzzy_patterns import (
    FuzzyPatternMatch,
    find_fuzzy_cusips,
    find_fuzzy_money,
)


class TestFindFuzzyCusips:
    def test_finds_exact_cusip(self) -> None:
        text = "CUSIP 037833100 appears"
        matches = list(find_fuzzy_cusips(text))
        assert len(matches) == 1
        match = matches[0]
        assert isinstance(match, FuzzyPatternMatch)
        assert match.matched_text == "037833100"
        assert match.edit_distance == 0

    def test_allows_ocr_substitution_with_budget(self) -> None:
        # Insert a lowercase character (invalid in the base pattern) so
        # it can only match with a substitution edit.
        text = "OCR'd code 03x833100 looks off"
        matches = list(find_fuzzy_cusips(text, max_edits=1))
        assert len(matches) == 1
        assert matches[0].edit_distance >= 1
        assert matches[0].matched_text.replace("x", "").replace("X", "").endswith("833100")

    def test_zero_budget_refuses_invalid_character(self) -> None:
        text = "code 03x833100 fine"
        matches = list(find_fuzzy_cusips(text, max_edits=0))
        assert matches == []

    def test_rejects_budget_above_two(self) -> None:
        with pytest.raises(ValueError):
            list(find_fuzzy_cusips("whatever", max_edits=3))


class TestFindFuzzyMoney:
    def test_finds_dollar_amount(self) -> None:
        matches = list(find_fuzzy_money("Total: $1,250.00 charged"))
        assert any(m.matched_text.startswith("$1,250") for m in matches)

    def test_no_match_on_plain_number_with_zero_budget(self) -> None:
        # A currency symbol is required by the base pattern. With no edit
        # budget, a plain number cannot fuzzy into a currency-prefixed
        # match.
        matches = list(find_fuzzy_money("Contract 12345 revision", max_edits=0))
        assert matches == []

    def test_budget_allows_small_ocr_errors(self) -> None:
        # S substituted for $ is a typical OCR mistake.
        matches = list(find_fuzzy_money("Total: S1,250.00 charged", max_edits=1))
        assert any("1,250.00" in m.matched_text for m in matches)
