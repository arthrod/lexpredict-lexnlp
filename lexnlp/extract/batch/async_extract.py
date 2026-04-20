"""Async batch extraction built on ``asyncio.TaskGroup``.

The rule-based extractors in :mod:`lexnlp.extract` are synchronous and
CPU-light; the natural way to process many documents is to dispatch each
document to a worker thread.  Python 3.13's ``asyncio.TaskGroup`` provides
structured concurrency and proper exception aggregation (``ExceptionGroup``),
which makes it a good fit for "extract N documents, collect all results, surface
every failure" workloads.

The public surface is intentionally small:

* :func:`extract_batch_async` — the coroutine.
* :func:`extract_batch` — a thin synchronous wrapper that drives the event
  loop for callers that do not want to ``await`` themselves.
* :class:`BatchExtractionResult` — a typed container for the per-document
  outcome so callers can distinguish success from failure without having to
  catch ``ExceptionGroup`` manually.

Concurrency is bounded by an :class:`asyncio.Semaphore` so we never exceed
``max_workers`` concurrent extractors; this matches the shape of
``concurrent.futures.ThreadPoolExecutor`` but keeps everything within the
asyncio event loop for easier composition.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import asyncio
import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

LOGGER = logging.getLogger(__name__)


# PEP 695 type parameter syntax (Python 3.12+) replaces the older
# ``TypeVar``/``Generic`` pattern. Every public generic entry point below uses
# the new form; internal helpers reuse the class-scoped ``T``.


@dataclass(slots=True, frozen=True)
class BatchExtractionResult[T]:
    """Outcome of a single document inside a batch.

    Attributes:
        index: Position in the original input sequence (0-based). Callers
            rely on this to join extraction results back to whatever metadata
            they keep alongside the raw text.
        annotations: The extractor's output, materialised as a list so
            consumers can iterate more than once without re-running it.
            Empty when ``error`` is set.
        error: The exception raised by the extractor (if any). ``None`` for
            successful extractions. We keep the exception object rather than
            just a string so callers can inspect the type.
    """

    index: int
    annotations: list[T] = field(default_factory=list)
    error: BaseException | None = None

    @property
    def ok(self) -> bool:
        """``True`` if the extractor ran to completion without error."""
        return self.error is None


async def _run_one[T](
    index: int,
    text: str,
    extractor: Callable[[str], Iterable[T]],
    semaphore: asyncio.Semaphore,
    raise_on_error: bool,
) -> BatchExtractionResult[T]:
    """Run ``extractor(text)`` under the semaphore on a worker thread."""
    async with semaphore:
        loop = asyncio.get_running_loop()
        try:
            annotations = await loop.run_in_executor(None, lambda: list(extractor(text)))
        except BaseException as exc:
            LOGGER.exception("Batch extractor failed at index %d", index)
            if raise_on_error:
                raise
            return BatchExtractionResult(index=index, annotations=[], error=exc)
        return BatchExtractionResult(index=index, annotations=annotations)


async def extract_batch_async[T](
    extractor: Callable[[str], Iterable[T]],
    texts: Sequence[str],
    *,
    max_workers: int = 8,
    raise_on_error: bool = False,
) -> list[BatchExtractionResult[T]]:
    """Run ``extractor`` concurrently over ``texts``.

    Uses :class:`asyncio.TaskGroup` so every task is structured: when
    ``raise_on_error=True`` failures propagate as an ``ExceptionGroup`` after
    all other tasks have been cancelled. When ``raise_on_error=False``
    (the default), failures are captured in the returned
    :class:`BatchExtractionResult` objects so partial batches still return.

    Args:
        extractor: A callable that turns a text string into an iterable of
            annotations. Typical callers pass in
            ``lexnlp.extract.en.amounts.get_amount_annotations`` or any
            other ``get_*_annotations`` function from the package.
        texts: Input documents. Accepts any :class:`Sequence` so callers can
            pass lists, tuples, or their own lightweight wrappers.
        max_workers: Maximum number of extractors to run concurrently.
            Defaults to 8, which matches the default worker count of
            :class:`concurrent.futures.ThreadPoolExecutor`.
        raise_on_error: If True, re-raise the first exception once the
            task group closes. If False (default), surface exceptions via
            the ``error`` attribute of each result.

    Returns:
        A list of :class:`BatchExtractionResult`, aligned by index with
        the input ``texts`` sequence.
    """
    if max_workers < 1:
        raise ValueError(f"max_workers must be >= 1, got {max_workers}")
    if not texts:
        return []

    semaphore = asyncio.Semaphore(max_workers)
    results: list[BatchExtractionResult[T] | None] = [None] * len(texts)

    async with asyncio.TaskGroup() as tg:
        for idx, text in enumerate(texts):
            tg.create_task(
                _collect(
                    idx,
                    text,
                    extractor,
                    semaphore,
                    raise_on_error,
                    results,
                ),
                name=f"lexnlp-batch-extract-{idx}",
            )

    # results are guaranteed to all be set because TaskGroup only exits
    # after every child task completes (success or cancel).
    return [r for r in results if r is not None]


async def _collect[T](
    index: int,
    text: str,
    extractor: Callable[[str], Iterable[T]],
    semaphore: asyncio.Semaphore,
    raise_on_error: bool,
    sink: list[BatchExtractionResult[T] | None],
) -> None:
    sink[index] = await _run_one(index, text, extractor, semaphore, raise_on_error)


def extract_batch[T](
    extractor: Callable[[str], Iterable[T]],
    texts: Sequence[str],
    *,
    max_workers: int = 8,
    raise_on_error: bool = False,
) -> list[BatchExtractionResult[T]]:
    """Synchronous wrapper around :func:`extract_batch_async`.

    Creates a fresh event loop via :func:`asyncio.run` so this helper is
    safe to call from scripts and test suites. If you already run inside
    an event loop, call :func:`extract_batch_async` directly — this
    helper will raise :class:`RuntimeError` because ``asyncio.run`` cannot
    be nested.

    The argument semantics mirror :func:`extract_batch_async` exactly.
    """

    async def _run() -> list[BatchExtractionResult[T]]:
        return await extract_batch_async(
            extractor,
            texts,
            max_workers=max_workers,
            raise_on_error=raise_on_error,
        )

    return asyncio.run(_run())


def group_successful[T](
    results: Sequence[BatchExtractionResult[T]],
) -> tuple[list[BatchExtractionResult[T]], list[BatchExtractionResult[T]]]:
    """Partition a batch of results into (ok, failed) lists.

    Purely a convenience: callers typically want to post-process successful
    extractions and separately log failures without writing the same
    comprehension everywhere.
    """
    ok: list[BatchExtractionResult[T]] = []
    failed: list[BatchExtractionResult[T]] = []
    for r in results:
        (ok if r.ok else failed).append(r)
    return ok, failed


def flatten[T](results: Iterable[BatchExtractionResult[T]]) -> list[T]:
    """Flatten successful batch results into a single list of annotations.

    Failed results are skipped silently; pair with :func:`group_successful`
    when you need to separately handle them.
    """
    out: list[T] = []
    for r in results:
        if r.ok:
            out.extend(r.annotations)
    return out


__all__ = [
    "BatchExtractionResult",
    "extract_batch",
    "extract_batch_async",
    "flatten",
    "group_successful",
]
