"""Tests for :mod:`lexnlp.extract.batch` package-level exports.

Verifies that the public API declared in ``__all__`` is importable directly
from the top-level ``lexnlp.extract.batch`` namespace and that each exported
name resolves to the correct underlying object.

Note: The batch package uses PEP 695 type-parameter syntax (``class Foo[T]:``)
which requires Python 3.12+. Tests are skipped on older runtimes.
"""

from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="lexnlp.extract.batch uses PEP 695 syntax (Python 3.12+)",
)


class TestBatchPackageImports:
    """Verify that all ``__all__`` exports are importable from the package."""

    def test_extract_batch_importable(self) -> None:
        from lexnlp.extract.batch import extract_batch

        assert callable(extract_batch)

    def test_extract_batch_async_importable(self) -> None:
        from lexnlp.extract.batch import extract_batch_async

        import asyncio

        assert asyncio.iscoroutinefunction(extract_batch_async)

    def test_batch_extraction_result_importable(self) -> None:
        from lexnlp.extract.batch import BatchExtractionResult

        # Verify it is instantiable with just an index.
        r = BatchExtractionResult(index=0)
        assert r.ok is True

    def test_find_fuzzy_dates_importable(self) -> None:
        from lexnlp.extract.batch import find_fuzzy_dates

        assert callable(find_fuzzy_dates)

    def test_fuzzy_date_match_importable(self) -> None:
        from lexnlp.extract.batch import FuzzyDateMatch

        from datetime import date

        m = FuzzyDateMatch(
            start=0, end=10, matched_text="2024-01-01", parsed=date(2024, 1, 1), edit_distance=0
        )
        assert m.parsed == date(2024, 1, 1)

    def test_annotations_to_dataframe_importable(self) -> None:
        pytest.importorskip("pandas")
        from lexnlp.extract.batch import annotations_to_dataframe

        assert callable(annotations_to_dataframe)

    def test_all_exports_present(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        expected = {
            "BatchExtractionResult",
            "FuzzyDateMatch",
            "annotations_to_dataframe",
            "extract_batch",
            "extract_batch_async",
            "find_fuzzy_dates",
        }
        assert expected == set(batch_pkg.__all__)

    def test_extract_batch_and_async_extract_batch_are_consistent(self) -> None:
        """Both sync/async variants should operate identically on simple input."""
        import asyncio

        from lexnlp.extract.batch import extract_batch, extract_batch_async

        texts = ["hello world", "foo bar"]
        sync_results = extract_batch(str.split, texts)

        async def _run():
            return await extract_batch_async(str.split, texts)

        async_results = asyncio.run(_run())

        assert [r.annotations for r in sync_results] == [
            r.annotations for r in async_results
        ]


class TestRemovedExports:
    """Verify that symbols removed in this PR are NOT importable from the package.

    PR removed the following exports from ``lexnlp.extract.batch.__all__``:
    - ``adaptive_max_workers``
    - ``flatten``
    - ``group_successful``
    - ``FuzzyPatternMatch``
    - ``find_fuzzy_cusips``
    - ``find_fuzzy_money``
    - ``extract_batch_with_progress``
    """

    def test_adaptive_max_workers_not_in_all(self) -> None:
        """
        Verify that 'adaptive_max_workers' is not included in the public exports of lexnlp.extract.batch.
        """
        import lexnlp.extract.batch as batch_pkg

        assert "adaptive_max_workers" not in batch_pkg.__all__

    def test_flatten_not_in_all(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert "flatten" not in batch_pkg.__all__

    def test_group_successful_not_in_all(self) -> None:
        """
        Verify that the symbol 'group_successful' is not listed in lexnlp.extract.batch.__all__.
        """
        import lexnlp.extract.batch as batch_pkg

        assert "group_successful" not in batch_pkg.__all__

    def test_fuzzy_pattern_match_not_in_all(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert "FuzzyPatternMatch" not in batch_pkg.__all__

    def test_find_fuzzy_cusips_not_in_all(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert "find_fuzzy_cusips" not in batch_pkg.__all__

    def test_find_fuzzy_money_not_in_all(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert "find_fuzzy_money" not in batch_pkg.__all__

    def test_extract_batch_with_progress_not_in_all(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert "extract_batch_with_progress" not in batch_pkg.__all__

    def test_adaptive_max_workers_not_importable_from_batch(self) -> None:
        """
        Verifies that importing `adaptive_max_workers` from `lexnlp.extract.batch` raises ImportError.
        
        This test ensures `adaptive_max_workers` is not exposed as a public import from the `lexnlp.extract.batch` package.
        """
        with pytest.raises(ImportError):
            from lexnlp.extract.batch import adaptive_max_workers  # noqa: F401

    def test_fuzzy_pattern_match_not_importable_from_batch(self) -> None:
        """
        Verifies that attempting to import `FuzzyPatternMatch` from `lexnlp.extract.batch` raises ImportError.
        
        The test asserts the public API no longer exposes `FuzzyPatternMatch` by expecting an ImportError when the import is attempted.
        """
        with pytest.raises(ImportError):
            from lexnlp.extract.batch import FuzzyPatternMatch  # noqa: F401

    def test_find_fuzzy_cusips_not_importable_from_batch(self) -> None:
        with pytest.raises(ImportError):
            from lexnlp.extract.batch import find_fuzzy_cusips  # noqa: F401

    def test_find_fuzzy_money_not_importable_from_batch(self) -> None:
        """
        Verifies that `find_fuzzy_money` is not importable from `lexnlp.extract.batch`.
        
        Asserts that attempting to import `find_fuzzy_money` directly from the package raises ImportError.
        """
        with pytest.raises(ImportError):
            from lexnlp.extract.batch import find_fuzzy_money  # noqa: F401

    def test_extract_batch_with_progress_not_importable_from_batch(self) -> None:
        with pytest.raises(ImportError):
            from lexnlp.extract.batch import extract_batch_with_progress  # noqa: F401

    def test_fuzzy_patterns_module_deleted(self) -> None:
        """The fuzzy_patterns module was removed; importing it must fail."""
        with pytest.raises(ImportError):
            import lexnlp.extract.batch.fuzzy_patterns  # noqa: F401

    def test_progress_module_deleted(self) -> None:
        """The progress module was removed; importing it must fail."""
        with pytest.raises(ImportError):
            import lexnlp.extract.batch.progress  # noqa: F401

    def test_all_contains_exactly_six_names(self) -> None:
        import lexnlp.extract.batch as batch_pkg

        assert len(batch_pkg.__all__) == 6