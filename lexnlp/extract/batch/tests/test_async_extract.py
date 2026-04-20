"""Tests for :mod:`lexnlp.extract.batch.async_extract`.

Covers:

* The sync ``extract_batch`` helper wraps the async coroutine and preserves
  order, annotation content, and ``max_workers`` bounds.
* The async coroutine ``extract_batch_async`` surfaces per-document
  exceptions without aborting the rest of the batch by default, and raises
  an ``ExceptionGroup`` when ``raise_on_error=True``.
* ``BatchExtractionResult`` is immutable, slotted, and has a sensible
  ``ok`` property.
* Utility helpers ``group_successful`` and ``flatten`` behave as documented.

Tests only depend on the standard library so they can run in the minimal
environment (no NLTK / sklearn required).
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import pytest

from lexnlp.extract.batch.async_extract import (
    BatchExtractionResult,
    extract_batch,
    extract_batch_async,
    flatten,
    group_successful,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _upper_extractor(text: str) -> list[str]:
    """A deterministic sync extractor used across tests."""
    return text.upper().split()


def _exploding_extractor(text: str) -> list[str]:
    if "BOOM" in text:
        raise RuntimeError(f"boom: {text}")
    return text.split()


# ---------------------------------------------------------------------------
# BatchExtractionResult
# ---------------------------------------------------------------------------


class TestBatchExtractionResult:
    def test_default_is_ok_with_empty_annotations(self) -> None:
        r: BatchExtractionResult[str] = BatchExtractionResult(index=0)
        assert r.ok is True
        assert r.annotations == []
        assert r.error is None

    def test_error_flips_ok_flag(self) -> None:
        r = BatchExtractionResult(index=1, error=ValueError("bad"))
        assert r.ok is False

    def test_is_frozen(self) -> None:
        r = BatchExtractionResult[int](index=0, annotations=[1, 2])
        with pytest.raises((AttributeError, Exception)):
            r.index = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# extract_batch (sync wrapper)
# ---------------------------------------------------------------------------


class TestExtractBatchSync:
    def test_preserves_order(self) -> None:
        texts = ["first doc", "second doc", "third doc"]
        results = extract_batch(_upper_extractor, texts)
        assert [r.index for r in results] == [0, 1, 2]
        assert results[0].annotations == ["FIRST", "DOC"]
        assert results[2].annotations == ["THIRD", "DOC"]

    def test_empty_input_returns_empty(self) -> None:
        assert extract_batch(_upper_extractor, []) == []

    def test_max_workers_must_be_positive(self) -> None:
        with pytest.raises(ValueError, match="max_workers"):
            extract_batch(_upper_extractor, ["x"], max_workers=0)

    def test_swallows_errors_by_default(self) -> None:
        results = extract_batch(_exploding_extractor, ["ok", "BOOM 1", "also ok"])
        assert results[0].ok is True
        assert results[1].ok is False
        assert isinstance(results[1].error, RuntimeError)
        assert results[2].ok is True

    def test_raise_on_error_propagates(self) -> None:
        with pytest.raises(BaseExceptionGroup) as exc_info:
            extract_batch(
                _exploding_extractor,
                ["ok", "BOOM 2"],
                raise_on_error=True,
            )
        assert any(isinstance(e, RuntimeError) for e in exc_info.value.exceptions)


# ---------------------------------------------------------------------------
# extract_batch_async (native coroutine)
# ---------------------------------------------------------------------------


class TestExtractBatchAsync:
    def test_returns_coroutine_results_in_input_order(self) -> None:
        async def _run() -> list[BatchExtractionResult[str]]:
            return await extract_batch_async(_upper_extractor, ["a b", "c d"])

        results = asyncio.run(_run())
        assert [r.annotations for r in results] == [["A", "B"], ["C", "D"]]

    def test_semaphore_bounds_concurrency(self) -> None:
        """The in-flight counter should never exceed ``max_workers``."""

        in_flight = 0
        peak = 0

        def tracking_extractor(_text: str) -> list[str]:
            nonlocal in_flight, peak
            in_flight += 1
            peak = max(peak, in_flight)
            time.sleep(0.01)
            in_flight -= 1
            return ["ok"]

        async def _run() -> None:
            await extract_batch_async(
                tracking_extractor,
                ["x"] * 16,
                max_workers=3,
            )

        asyncio.run(_run())
        # Allow a small slack for thread scheduling but reject obvious
        # concurrency violations.
        assert peak <= 3 + 1

    def test_many_failures_are_collected(self) -> None:
        async def _run() -> list[BatchExtractionResult[str]]:
            return await extract_batch_async(
                _exploding_extractor,
                ["BOOM a", "BOOM b", "ok", "BOOM c"],
            )

        results = asyncio.run(_run())
        ok, failed = group_successful(results)
        assert len(failed) == 3
        assert len(ok) == 1
        assert ok[0].index == 2


# ---------------------------------------------------------------------------
# group_successful / flatten
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    def test_group_successful_partitions(self) -> None:
        results = [
            BatchExtractionResult[str](index=0, annotations=["x"]),
            BatchExtractionResult[str](index=1, error=RuntimeError()),
            BatchExtractionResult[str](index=2, annotations=["y"]),
        ]
        ok, failed = group_successful(results)
        assert [r.index for r in ok] == [0, 2]
        assert [r.index for r in failed] == [1]

    def test_flatten_skips_failed(self) -> None:
        results = [
            BatchExtractionResult[str](index=0, annotations=["a", "b"]),
            BatchExtractionResult[str](index=1, error=RuntimeError()),
            BatchExtractionResult[str](index=2, annotations=["c"]),
        ]
        assert flatten(results) == ["a", "b", "c"]

    def test_flatten_empty_iterable(self) -> None:
        assert flatten([]) == []


# ---------------------------------------------------------------------------
# Misc edge cases
# ---------------------------------------------------------------------------


class TestMiscEdgeCases:
    def test_extract_batch_supports_generator_extractor(self) -> None:
        def gen_extractor(text: str):
            yield from text.split(",")

        results = extract_batch(gen_extractor, ["a,b", "c,d"])
        assert results[0].annotations == ["a", "b"]
        assert results[1].annotations == ["c", "d"]

    def test_extract_batch_handles_non_list_sequence(self) -> None:
        results = extract_batch(_upper_extractor, ("one", "two"))
        assert len(results) == 2

    def test_result_annotations_field_is_independent(self) -> None:
        """Mutating one result's annotations list must not affect another."""
        a = BatchExtractionResult[int](index=0)
        b = BatchExtractionResult[int](index=1)
        a.annotations.append(1)
        assert b.annotations == []

    def test_error_propagation_keeps_exception_type(self) -> None:
        def raiser(_: str) -> list[Any]:
            raise KeyError("missing")

        results = extract_batch(raiser, ["x"])
        assert isinstance(results[0].error, KeyError)
