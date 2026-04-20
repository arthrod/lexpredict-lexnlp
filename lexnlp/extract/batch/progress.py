"""Synchronous batch extraction with live progress reporting.

``async_extract.extract_batch`` is the right entry point for structured
concurrency, but scripts often want the one-liner ergonomics of
``tqdm.contrib.concurrent.thread_map``: give it an iterable of texts, a
function, and get back results in the same order with a progress bar.

This module provides that shape on top of the LexNLP extractor contract.
It uses ``tqdm`` (already a runtime dependency) and falls back to a
no-op iterator when ``tqdm`` is unavailable so CI runs without a TTY
don't explode.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor

from lexnlp.extract.batch.async_extract import (
    BatchExtractionResult,
    adaptive_max_workers,
)


def _wrap_extractor[T](
    extractor: Callable[[str], Iterable[T]],
) -> Callable[[tuple[int, str]], BatchExtractionResult[T]]:
    """Adapt a text-only extractor to the ``(index, text) -> result`` shape."""

    def run(pair: tuple[int, str]) -> BatchExtractionResult[T]:
        index, text = pair
        try:
            annotations = list(extractor(text))
        except Exception as exc:
            return BatchExtractionResult(index=index, annotations=[], error=exc)
        return BatchExtractionResult(index=index, annotations=annotations)

    return run


def extract_batch_with_progress[T](
    extractor: Callable[[str], Iterable[T]],
    texts: Sequence[str],
    *,
    max_workers: int | None = None,
    desc: str = "lexnlp-extract",
    show_progress: bool = True,
) -> list[BatchExtractionResult[T]]:
    """Run ``extractor`` on every text with a live progress bar.

    Args:
        extractor: Any ``get_*_annotations`` callable from LexNLP.
        texts: The documents to process.
        max_workers: Override thread count. Defaults to
            :func:`adaptive_max_workers`.
        desc: Progress bar label.
        show_progress: Set to ``False`` to suppress the bar (e.g. in CI).

    Returns:
        A list of :class:`BatchExtractionResult`, one per input text.
    """
    if not texts:
        return []
    workers = max_workers if max_workers and max_workers > 0 else adaptive_max_workers()
    fn = _wrap_extractor(extractor)
    pairs = list(enumerate(texts))

    iterator: Iterable[BatchExtractionResult[T]]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        raw_iterator = pool.map(fn, pairs)
        if show_progress:
            try:
                from tqdm.auto import tqdm

                iterator = tqdm(raw_iterator, total=len(pairs), desc=desc)
            except ImportError:  # pragma: no cover
                iterator = raw_iterator
        else:
            iterator = raw_iterator
        results = list(iterator)
    # Restore original order since ``ThreadPoolExecutor.map`` preserves
    # submission order. The sort is a paranoid guard against future
    # regressions; it's O(n log n) but tiny compared to extraction cost.
    results.sort(key=lambda r: r.index)
    return results


__all__ = ["extract_batch_with_progress"]
