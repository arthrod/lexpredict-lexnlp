"""Supplementary tests for the PR-16 additions to :mod:`lexnlp.extract.batch`.

PR-16 added several new exports to the package ``__all__``:
- ``adaptive_max_workers``
- ``flatten``
- ``group_successful``
- ``FuzzyPatternMatch``
- ``find_fuzzy_cusips``
- ``find_fuzzy_money``
- ``extract_batch_with_progress``

These tests verify that all new exports are importable from the top-level
package namespace and behave correctly when called.

Note: The batch package uses PEP 695 syntax (Python 3.12+). Tests are
automatically skipped on older runtimes.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="lexnlp.extract.batch uses PEP 695 syntax (Python 3.12+)",
)


# ---------------------------------------------------------------------------
# New exports are importable
# ---------------------------------------------------------------------------


class TestNewExportsImportable:
    def test_adaptive_max_workers_importable(self) -> None:
        from lexnlp.extract.batch import adaptive_max_workers

        assert callable(adaptive_max_workers)

    def test_flatten_importable(self) -> None:
        from lexnlp.extract.batch import flatten

        assert callable(flatten)

    def test_group_successful_importable(self) -> None:
        from lexnlp.extract.batch import group_successful

        assert callable(group_successful)

    def test_fuzzy_pattern_match_importable(self) -> None:
        from lexnlp.extract.batch import FuzzyPatternMatch

        m = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        assert m.matched_text == "037833100"

    def test_find_fuzzy_cusips_importable(self) -> None:
        from lexnlp.extract.batch import find_fuzzy_cusips

        assert callable(find_fuzzy_cusips)

    def test_find_fuzzy_money_importable(self) -> None:
        from lexnlp.extract.batch import find_fuzzy_money

        assert callable(find_fuzzy_money)

    def test_extract_batch_with_progress_importable(self) -> None:
        from lexnlp.extract.batch import extract_batch_with_progress

        assert callable(extract_batch_with_progress)


# ---------------------------------------------------------------------------
# New exports are present in __all__
# ---------------------------------------------------------------------------


class TestNewExportsInAll:
    def test_all_new_names_in_all(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        new_names = {
            "adaptive_max_workers",
            "flatten",
            "group_successful",
            "FuzzyPatternMatch",
            "find_fuzzy_cusips",
            "find_fuzzy_money",
            "extract_batch_with_progress",
        }
        assert new_names.issubset(set(batch_pkg.__all__))

    def test_all_is_a_list(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert isinstance(batch_pkg.__all__, list)

    def test_no_duplicates_in_all(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert len(batch_pkg.__all__) == len(set(batch_pkg.__all__))


# ---------------------------------------------------------------------------
# Functional smoke tests for each new export
# ---------------------------------------------------------------------------


class TestAdaptiveMaxWorkersFunctional:
    def test_returns_positive_int(self) -> None:
        from lexnlp.extract.batch import adaptive_max_workers

        result = adaptive_max_workers()
        assert isinstance(result, int)
        assert result >= 1


class TestFlattenFunctional:
    def test_empty_input(self) -> None:
        from lexnlp.extract.batch import flatten

        assert flatten([]) == []

    def test_flattens_successful_results(self) -> None:
        from lexnlp.extract.batch import BatchExtractionResult, flatten

        results = [
            BatchExtractionResult(index=0, annotations=["a", "b"]),
            BatchExtractionResult(index=1, annotations=["c"]),
        ]
        assert flatten(results) == ["a", "b", "c"]

    def test_skips_failed_results(self) -> None:
        from lexnlp.extract.batch import BatchExtractionResult, flatten

        results = [
            BatchExtractionResult(index=0, annotations=["x"]),
            BatchExtractionResult(index=1, error=RuntimeError()),
        ]
        assert flatten(results) == ["x"]


class TestGroupSuccessfulFunctional:
    def test_partitions_correctly(self) -> None:
        from lexnlp.extract.batch import BatchExtractionResult, group_successful

        ok_r = BatchExtractionResult(index=0, annotations=["x"])
        fail_r = BatchExtractionResult(index=1, error=ValueError())
        ok, failed = group_successful([ok_r, fail_r])
        assert len(ok) == 1
        assert len(failed) == 1
        assert ok[0].index == 0
        assert failed[0].index == 1

    def test_empty_input(self) -> None:
        from lexnlp.extract.batch import group_successful

        ok, failed = group_successful([])
        assert ok == []
        assert failed == []


class TestFuzzyPatternMatchFunctional:
    def test_immutable_field_assignment_raises(self) -> None:
        from lexnlp.extract.batch import FuzzyPatternMatch

        m = FuzzyPatternMatch(start=0, end=9, matched_text="037833100", edit_distance=0)
        with pytest.raises((AttributeError, TypeError)):
            m.start = 5  # type: ignore[misc]


class TestFindFuzzyCusipsFunctional:
    def test_exact_match_found(self) -> None:
        from lexnlp.extract.batch import find_fuzzy_cusips

        matches = list(find_fuzzy_cusips("CUSIP 037833100 ends"))
        assert len(matches) == 1
        assert matches[0].matched_text == "037833100"

    def test_invalid_budget_raises(self) -> None:
        from lexnlp.extract.batch import find_fuzzy_cusips

        with pytest.raises(ValueError):
            list(find_fuzzy_cusips("text", max_edits=5))


class TestFindFuzzyMoneyFunctional:
    def test_dollar_amount_found(self) -> None:
        from lexnlp.extract.batch import find_fuzzy_money

        matches = list(find_fuzzy_money("$500 deposit", max_edits=0))
        assert any("$500" in m.matched_text for m in matches)

    def test_invalid_budget_raises(self) -> None:
        from lexnlp.extract.batch import find_fuzzy_money

        with pytest.raises(ValueError):
            list(find_fuzzy_money("$100", max_edits=-1))


class TestExtractBatchWithProgressFunctional:
    def test_returns_ordered_results(self) -> None:
        from lexnlp.extract.batch import extract_batch_with_progress

        results = extract_batch_with_progress(
            str.split, ["a b", "c d e"], show_progress=False
        )
        assert len(results) == 2
        assert results[0].index == 0
        assert results[1].index == 1

    def test_empty_returns_empty(self) -> None:
        from lexnlp.extract.batch import extract_batch_with_progress

        assert extract_batch_with_progress(str.split, [], show_progress=False) == []

    def test_failure_captured(self) -> None:
        from lexnlp.extract.batch import extract_batch_with_progress

        def fail(text: str) -> list[str]:
            raise RuntimeError("oops")

        results = extract_batch_with_progress(fail, ["x"], show_progress=False)
        assert len(results) == 1
        assert not results[0].ok
        assert isinstance(results[0].error, RuntimeError)


# ---------------------------------------------------------------------------
# Cross-module consistency: flatten ∘ extract_batch_with_progress
# ---------------------------------------------------------------------------


class TestCrossModuleConsistency:
    def test_flatten_and_extract_batch_with_progress_compose(self) -> None:
        from lexnlp.extract.batch import extract_batch_with_progress, flatten

        results = extract_batch_with_progress(
            str.split, ["hello world", "foo bar"], show_progress=False
        )
        flat = flatten(results)
        assert set(flat) == {"hello", "world", "foo", "bar"}

    def test_group_successful_and_extract_batch_compose(self) -> None:
        from lexnlp.extract.batch import extract_batch, group_successful

        def maybe_fail(text: str) -> list[str]:
            if text == "FAIL":
                raise RuntimeError()
            return text.split()

        results = extract_batch(maybe_fail, ["good", "FAIL", "also good"])
        ok, failed = group_successful(results)
        assert len(ok) == 2
        assert len(failed) == 1