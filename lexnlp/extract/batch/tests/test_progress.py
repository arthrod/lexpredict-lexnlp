"""Tests for :mod:`lexnlp.extract.batch.progress`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.batch.async_extract import adaptive_max_workers
from lexnlp.extract.batch.progress import extract_batch_with_progress


def _split(text: str) -> list[str]:
    return text.split()


class TestAdaptiveMaxWorkers:
    def test_returns_at_least_one(self) -> None:
        assert adaptive_max_workers() >= 1


class TestExtractBatchWithProgress:
    def test_preserves_order(self) -> None:
        texts = [f"doc {i}" for i in range(20)]
        results = extract_batch_with_progress(
            _split, texts, show_progress=False, max_workers=4
        )
        assert [r.index for r in results] == list(range(20))

    def test_captures_failures(self) -> None:
        def flaky(text: str) -> list[str]:
            if "boom" in text:
                raise RuntimeError("boom")
            return text.split()

        results = extract_batch_with_progress(
            flaky, ["good", "boom please", "also good"], show_progress=False
        )
        assert results[0].ok
        assert not results[1].ok
        assert isinstance(results[1].error, RuntimeError)
        assert results[2].ok

    def test_empty_returns_empty(self) -> None:
        assert extract_batch_with_progress(_split, [], show_progress=False) == []
