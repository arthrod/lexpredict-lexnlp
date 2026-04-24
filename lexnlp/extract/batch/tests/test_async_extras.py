"""Additional tests for :mod:`lexnlp.extract.batch.async_extract`.

Supplements the main ``test_async_extract.py`` with boundary and branch
conditions not covered there:

* serial execution (max_workers=1)
* single-document batches
* all-successful / all-failed partitioning
* flatten with all-failed, all-ok, and empty inputs
* result index alignment when failures are interspersed
* BaseException subclass propagation (not just RuntimeError)
* group_successful / flatten on empty input

Note: The batch package uses PEP 695 type-parameter syntax (``class Foo[T]:``)
which requires Python 3.12+. Tests are skipped on older runtimes.
* extract_batch with raise_on_error=True and single failure
"""

from __future__ import annotations

import asyncio
import logging
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="lexnlp.extract.batch uses PEP 695 syntax (Python 3.12+)",
)

if sys.version_info >= (3, 12):
    from lexnlp.extract.batch.async_extract import (
        BatchExtractionResult,
        extract_batch,
        extract_batch_async,
        flatten,
        group_successful,
    )
else:
    # Provide stubs so module-level class bodies can be parsed on Python < 3.12.
    BatchExtractionResult = None  # type: ignore[assignment,misc]
    extract_batch = None  # type: ignore[assignment]
    extract_batch_async = None  # type: ignore[assignment]
    flatten = None  # type: ignore[assignment]
    group_successful = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _words(text: str) -> list[str]:
    return text.split()


def _always_raises(text: str) -> list[str]:
    raise ValueError(f"forced error: {text!r}")


# ---------------------------------------------------------------------------
# max_workers=1 — serial execution still returns correct results
# ---------------------------------------------------------------------------


class TestSerialExecution:
    def test_max_workers_one_returns_all_results(self) -> None:
        texts = ["alpha beta", "gamma delta", "epsilon"]
        results = extract_batch(_words, texts, max_workers=1)
        assert len(results) == 3
        assert results[0].annotations == ["alpha", "beta"]
        assert results[1].annotations == ["gamma", "delta"]
        assert results[2].annotations == ["epsilon"]

    def test_max_workers_one_preserves_index_order(self) -> None:
        texts = [f"doc{i}" for i in range(5)]
        results = extract_batch(_words, texts, max_workers=1)
        assert [r.index for r in results] == list(range(5))


# ---------------------------------------------------------------------------
# Single-document batch
# ---------------------------------------------------------------------------


class TestSingleDocument:
    def test_single_doc_ok(self) -> None:
        results = extract_batch(_words, ["hello world"])
        assert len(results) == 1
        assert results[0].ok
        assert results[0].index == 0

    def test_single_doc_failure_swallowed(self) -> None:
        results = extract_batch(_always_raises, ["x"])
        assert len(results) == 1
        assert results[0].ok is False
        assert isinstance(results[0].error, ValueError)

    def test_single_doc_raise_on_error(self) -> None:
        with pytest.raises(BaseExceptionGroup) as exc_info:
            extract_batch(_always_raises, ["x"], raise_on_error=True)
        errors = exc_info.value.exceptions
        assert any(isinstance(e, ValueError) for e in errors)


# ---------------------------------------------------------------------------
# Index alignment when failures are interspersed
# ---------------------------------------------------------------------------


class TestIndexAlignment:
    def test_failure_at_first_position(self) -> None:
        def boom_first(text: str) -> list[str]:
            if text == "FAIL":
                raise RuntimeError("boom")
            return text.split()

        results = extract_batch(boom_first, ["FAIL", "ok one", "ok two"])
        assert results[0].ok is False
        assert results[0].index == 0
        assert results[1].annotations == ["ok", "one"]
        assert results[2].annotations == ["ok", "two"]

    def test_failure_at_last_position(self) -> None:
        def boom_last(text: str) -> list[str]:
            if text == "FAIL":
                raise RuntimeError("boom")
            return text.split()

        results = extract_batch(boom_last, ["ok", "good", "FAIL"])
        assert results[2].ok is False
        assert results[2].index == 2
        assert results[0].ok and results[1].ok

    def test_alternating_failures(self) -> None:
        texts = ["BOOM" if i % 2 == 0 else "ok" for i in range(6)]

        def boom_on_keyword(text: str) -> list[str]:
            if text == "BOOM":
                raise RuntimeError()
            return [text]

        results = extract_batch(boom_on_keyword, texts)
        assert len(results) == 6
        for i, r in enumerate(results):
            if i % 2 == 0:
                assert r.ok is False
            else:
                assert r.ok is True


# ---------------------------------------------------------------------------
# group_successful edge cases
# ---------------------------------------------------------------------------


class TestGroupSuccessfulEdgeCases:
    def test_all_ok(self) -> None:
        results = [BatchExtractionResult[str](index=i, annotations=["x"]) for i in range(3)]
        ok, failed = group_successful(results)
        assert len(ok) == 3
        assert len(failed) == 0

    def test_all_failed(self) -> None:
        results = [BatchExtractionResult[str](index=i, error=RuntimeError()) for i in range(3)]
        ok, failed = group_successful(results)
        assert len(ok) == 0
        assert len(failed) == 3

    def test_empty_input(self) -> None:
        ok, failed = group_successful([])
        assert ok == []
        assert failed == []

    def test_order_preserved_in_ok_list(self) -> None:
        results = [
            BatchExtractionResult[str](index=0, annotations=["a"]),
            BatchExtractionResult[str](index=1, error=RuntimeError()),
            BatchExtractionResult[str](index=2, annotations=["b"]),
            BatchExtractionResult[str](index=3, annotations=["c"]),
        ]
        ok, _ = group_successful(results)
        assert [r.index for r in ok] == [0, 2, 3]


# ---------------------------------------------------------------------------
# flatten edge cases
# ---------------------------------------------------------------------------


class TestFlattenEdgeCases:
    def test_all_failed_returns_empty(self) -> None:
        results = [BatchExtractionResult[str](index=i, error=RuntimeError()) for i in range(3)]
        assert flatten(results) == []

    def test_all_ok_concatenates_all(self) -> None:
        results = [
            BatchExtractionResult[str](index=0, annotations=["a", "b"]),
            BatchExtractionResult[str](index=1, annotations=["c"]),
        ]
        assert flatten(results) == ["a", "b", "c"]

    def test_mixed_skips_failed(self) -> None:
        results = [
            BatchExtractionResult[str](index=0, annotations=["x"]),
            BatchExtractionResult[str](index=1, error=RuntimeError()),
            BatchExtractionResult[str](index=2, annotations=["y", "z"]),
        ]
        assert flatten(results) == ["x", "y", "z"]

    def test_empty_annotations_in_ok_result(self) -> None:
        # A successful extractor that produced no annotations.
        results = [BatchExtractionResult[str](index=0, annotations=[])]
        assert flatten(results) == []

    def test_flatten_accepts_generator_of_results(self) -> None:
        def _gen():
            yield BatchExtractionResult[int](index=0, annotations=[1, 2])
            yield BatchExtractionResult[int](index=1, annotations=[3])

        assert flatten(_gen()) == [1, 2, 3]


# ---------------------------------------------------------------------------
# BaseException subclass propagation
# ---------------------------------------------------------------------------


class TestBaseExceptionPropagation:
    """BaseException subclasses outside ``Exception`` must propagate.

    The batch wrapper only captures :class:`Exception`, so signals such as
    :class:`KeyboardInterrupt` and :class:`SystemExit` — which are
    deliberately modelled outside the regular exception hierarchy —
    surface to the caller instead of being silently stored in a
    :class:`BatchExtractionResult`. This matches the CodeRabbit review
    guidance and preserves structured-concurrency semantics.
    """

    def test_keyboard_interrupt_propagates(self) -> None:
        def interrupt(_: str) -> list[str]:
            raise KeyboardInterrupt("simulated interrupt")

        with pytest.raises(KeyboardInterrupt):
            extract_batch(interrupt, ["x"])

    def test_system_exit_propagates(self) -> None:
        def quitter(_: str) -> list[str]:
            raise SystemExit(1)

        with pytest.raises((SystemExit, BaseException)):
            extract_batch(quitter, ["x"])


# ---------------------------------------------------------------------------
# Logging on failure
# ---------------------------------------------------------------------------


class TestLoggingOnFailure:
    def test_failure_is_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.ERROR, logger="lexnlp.extract.batch.async_extract"):
            extract_batch(_always_raises, ["test text"])
        assert any("Batch extractor failed" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# extract_batch_async — native async tests
# ---------------------------------------------------------------------------


class TestExtractBatchAsyncAdditional:
    def test_raise_on_error_true_single_doc(self) -> None:
        async def _run() -> None:
            await extract_batch_async(_always_raises, ["x"], raise_on_error=True)

        with pytest.raises(BaseExceptionGroup):
            asyncio.run(_run())

    def test_max_workers_must_be_at_least_one_async(self) -> None:
        async def _run() -> None:
            await extract_batch_async(_words, ["x"], max_workers=0)

        with pytest.raises(ValueError, match="max_workers"):
            asyncio.run(_run())

    def test_empty_sequence_async(self) -> None:
        async def _run():
            return await extract_batch_async(_words, [])

        result = asyncio.run(_run())
        assert result == []

    def test_result_count_matches_input_count(self) -> None:
        async def _run():
            return await extract_batch_async(_words, ["a", "b", "c"])

        results = asyncio.run(_run())
        assert len(results) == 3


# ---------------------------------------------------------------------------
# BatchExtractionResult additional coverage
# ---------------------------------------------------------------------------


class TestBatchExtractionResultAdditional:
    def test_ok_true_with_non_empty_annotations(self) -> None:
        r = BatchExtractionResult[str](index=0, annotations=["a", "b"])
        assert r.ok is True

    def test_ok_false_with_error_and_annotations_empty(self) -> None:
        r = BatchExtractionResult[str](index=2, annotations=[], error=TypeError("t"))
        assert r.ok is False

    def test_index_preserved(self) -> None:
        for i in [0, 1, 99, 1000]:
            r = BatchExtractionResult[int](index=i)
            assert r.index == i

    def test_repr_contains_index(self) -> None:
        r = BatchExtractionResult[str](index=42)
        assert "42" in repr(r)
