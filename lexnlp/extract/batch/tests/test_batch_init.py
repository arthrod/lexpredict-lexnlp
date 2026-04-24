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
        import asyncio

        from lexnlp.extract.batch import extract_batch_async

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
        from datetime import date

        from lexnlp.extract.batch import FuzzyDateMatch

        m = FuzzyDateMatch(start=0, end=10, matched_text="2024-01-01", parsed=date(2024, 1, 1), edit_distance=0)
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
        assert expected.issubset(set(batch_pkg.__all__))

    def test_extract_batch_and_async_extract_batch_are_consistent(self) -> None:
        """Both sync/async variants should operate identically on simple input."""
        import asyncio

        from lexnlp.extract.batch import extract_batch, extract_batch_async

        texts = ["hello world", "foo bar"]
        sync_results = extract_batch(str.split, texts)

        async def _run():
            return await extract_batch_async(str.split, texts)

        async_results = asyncio.run(_run())

        assert [r.annotations for r in sync_results] == [r.annotations for r in async_results]
