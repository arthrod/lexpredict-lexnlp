"""Supplementary tests for :mod:`lexnlp.extract.batch.progress`.

Extends the existing test_progress.py with:
- max_workers=0 and max_workers=None use adaptive_max_workers
- show_progress=True path (tqdm installed)
- Single-item batches
- Ordering guarantee with many workers
- _wrap_extractor adapter behaviour
- desc parameter doesn't crash

progress.py uses PEP 695 type-parameter syntax (Python 3.12+). The module-
level imports are guarded so the file can be collected on Python 3.11 without
raising a SyntaxError.
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
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="progress.py uses PEP 695 syntax (Python 3.12+)",
)

if sys.version_info >= (3, 12):
    # Import directly to bypass the PEP-695 __init__.py.
    _spec = importlib.util.spec_from_file_location(
        "lexnlp.extract.batch.progress",
        str(pathlib.Path(__file__).parent.parent / "progress.py"),
    )
    _mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]

    extract_batch_with_progress = _mod.extract_batch_with_progress
    _wrap_extractor = _mod._wrap_extractor

    # Also import BatchExtractionResult directly.
    _ae_spec = importlib.util.spec_from_file_location(
        "lexnlp.extract.batch.async_extract",
        str(pathlib.Path(__file__).parent.parent / "async_extract.py"),
    )
    _ae_mod = importlib.util.module_from_spec(_ae_spec)  # type: ignore[arg-type]
    _ae_spec.loader.exec_module(_ae_mod)  # type: ignore[union-attr]
    BatchExtractionResult = _ae_mod.BatchExtractionResult
else:
    # Stubs so module-level class bodies can be parsed on Python < 3.12.
    extract_batch_with_progress = None  # type: ignore[assignment]
    _wrap_extractor = None  # type: ignore[assignment]
    BatchExtractionResult = None  # type: ignore[assignment,misc]


def _words(text: str) -> list[str]:
    return text.split()


# ---------------------------------------------------------------------------
# max_workers edge cases
# ---------------------------------------------------------------------------


class TestMaxWorkersFallback:
    def test_max_workers_none_uses_adaptive(self) -> None:
        """max_workers=None must not crash — falls back to adaptive_max_workers."""
        results = extract_batch_with_progress(_words, ["hello world"], max_workers=None, show_progress=False)
        assert len(results) == 1
        assert results[0].ok

    def test_max_workers_zero_uses_adaptive(self) -> None:
        """max_workers=0 is treated as 'use default', not as 'zero threads'."""
        results = extract_batch_with_progress(_words, ["hello world"], max_workers=0, show_progress=False)
        assert len(results) == 1
        assert results[0].ok

    def test_max_workers_one_sequential(self) -> None:
        results = extract_batch_with_progress(_words, ["a b", "c d", "e f"], max_workers=1, show_progress=False)
        assert len(results) == 3
        assert all(r.ok for r in results)

    def test_max_workers_large_does_not_crash(self) -> None:
        texts = [f"doc {i}" for i in range(5)]
        results = extract_batch_with_progress(_words, texts, max_workers=32, show_progress=False)
        assert len(results) == 5


# ---------------------------------------------------------------------------
# Single-item batch
# ---------------------------------------------------------------------------


class TestSingleItemBatch:
    def test_single_item_ok(self) -> None:
        results = extract_batch_with_progress(_words, ["hello world"], show_progress=False)
        assert len(results) == 1
        assert results[0].ok
        assert results[0].index == 0
        assert results[0].annotations == ["hello", "world"]

    def test_single_item_failure_captured(self) -> None:
        def always_fail(text: str) -> list[str]:
            raise RuntimeError("forced")

        results = extract_batch_with_progress(always_fail, ["trigger"], show_progress=False)
        assert len(results) == 1
        assert not results[0].ok
        assert isinstance(results[0].error, RuntimeError)


# ---------------------------------------------------------------------------
# show_progress=True (tqdm path)
# ---------------------------------------------------------------------------


class TestShowProgressTrue:
    def test_progress_true_does_not_crash(self) -> None:
        """With show_progress=True, the function must still return correct results
        regardless of whether tqdm is installed (it will fall back silently)."""
        results = extract_batch_with_progress(_words, ["alpha beta", "gamma"], max_workers=2, show_progress=True)
        assert len(results) == 2
        assert all(r.ok for r in results)

    def test_progress_true_order_preserved(self) -> None:
        texts = [f"item {i}" for i in range(10)]
        results = extract_batch_with_progress(_words, texts, max_workers=4, show_progress=True)
        assert [r.index for r in results] == list(range(10))


# ---------------------------------------------------------------------------
# desc parameter
# ---------------------------------------------------------------------------


class TestDescParameter:
    def test_custom_desc_does_not_crash(self) -> None:
        results = extract_batch_with_progress(
            _words,
            ["hello"],
            desc="my-custom-label",
            show_progress=False,
        )
        assert len(results) == 1

    def test_empty_desc_does_not_crash(self) -> None:
        results = extract_batch_with_progress(_words, ["hello"], desc="", show_progress=False)
        assert len(results) == 1


# ---------------------------------------------------------------------------
# Ordering guarantee with many workers
# ---------------------------------------------------------------------------


class TestOrderingGuarantee:
    def test_results_sorted_by_index_many_workers(self) -> None:
        texts = [f"word{i}" for i in range(50)]
        results = extract_batch_with_progress(_words, texts, max_workers=8, show_progress=False)
        indices = [r.index for r in results]
        assert indices == list(range(50))

    def test_index_field_matches_position(self) -> None:
        texts = ["alpha", "beta", "gamma", "delta"]
        results = extract_batch_with_progress(_words, texts, max_workers=2, show_progress=False)
        for i, r in enumerate(results):
            assert r.index == i

    def test_annotations_match_input_position(self) -> None:
        texts = ["one", "one two", "one two three"]
        results = extract_batch_with_progress(_words, texts, show_progress=False)
        assert results[0].annotations == ["one"]
        assert results[1].annotations == ["one", "two"]
        assert results[2].annotations == ["one", "two", "three"]


# ---------------------------------------------------------------------------
# _wrap_extractor adapter
# ---------------------------------------------------------------------------


class TestWrapExtractor:
    """Unit tests for the internal _wrap_extractor adapter."""

    def test_success_returns_batch_result_with_annotations(self) -> None:
        fn = _wrap_extractor(_words)
        result = fn((7, "hello world"))
        assert result.index == 7
        assert result.annotations == ["hello", "world"]
        assert result.ok

    def test_failure_captured_in_result(self) -> None:
        def boom(text: str) -> list[str]:
            raise ValueError("bad")

        fn = _wrap_extractor(boom)
        result = fn((3, "anything"))
        assert result.index == 3
        assert result.ok is False
        assert isinstance(result.error, ValueError)
        assert result.annotations == []

    def test_index_zero_handled(self) -> None:
        fn = _wrap_extractor(_words)
        result = fn((0, "x"))
        assert result.index == 0

    def test_extractor_returning_empty_list(self) -> None:
        fn = _wrap_extractor(lambda text: [])
        result = fn((5, "anything"))
        assert result.ok
        assert result.annotations == []
        assert result.index == 5

    def test_extractor_receiving_empty_string(self) -> None:
        fn = _wrap_extractor(_words)
        result = fn((2, ""))
        assert result.ok
        assert result.annotations == []


# ---------------------------------------------------------------------------
# Return type is always a list
# ---------------------------------------------------------------------------


class TestReturnType:
    def test_returns_list(self) -> None:
        result = extract_batch_with_progress(_words, ["hello"], show_progress=False)
        assert isinstance(result, list)

    def test_each_element_is_batch_extraction_result(self) -> None:
        results = extract_batch_with_progress(_words, ["a", "b"], show_progress=False)
        for r in results:
            assert hasattr(r, "index")
            assert hasattr(r, "annotations")
            assert hasattr(r, "error")
            assert hasattr(r, "ok")
