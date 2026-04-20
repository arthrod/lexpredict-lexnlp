"""Batch and concurrent extraction helpers for LexNLP.

This subpackage provides Python 3.13-era conveniences on top of the
single-document rule-based extractors:

* :mod:`lexnlp.extract.batch.async_extract` uses ``asyncio.TaskGroup``
  (PEP 654 / Python 3.11+, with 3.13 performance improvements) to run
  many single-threaded extractors concurrently via a bounded thread pool.
* :mod:`lexnlp.extract.batch.pandas_output` exposes an Arrow-backed
  ``pandas.DataFrame`` view over extraction results so downstream code
  can benefit from Copy-on-Write semantics and PyArrow-native dtypes.
* :mod:`lexnlp.extract.batch.fuzzy_dates` shows how to take advantage of
  the ``regex`` fuzzy-matching backend (``{e<=n}``) that became available
  with the ``>=2024`` pin in ``pyproject.toml``.

All helpers are lazy imports so that users who do not opt in pay no
startup cost.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.batch.async_extract import (
    BatchExtractionResult,
    adaptive_max_workers,
    extract_batch,
    extract_batch_async,
    flatten,
    group_successful,
)
from lexnlp.extract.batch.fuzzy_dates import FuzzyDateMatch, find_fuzzy_dates
from lexnlp.extract.batch.fuzzy_patterns import (
    FuzzyPatternMatch,
    find_fuzzy_cusips,
    find_fuzzy_money,
)
from lexnlp.extract.batch.pandas_output import annotations_to_dataframe
from lexnlp.extract.batch.progress import extract_batch_with_progress

__all__ = [
    "BatchExtractionResult",
    "FuzzyDateMatch",
    "FuzzyPatternMatch",
    "adaptive_max_workers",
    "annotations_to_dataframe",
    "extract_batch",
    "extract_batch_async",
    "extract_batch_with_progress",
    "find_fuzzy_cusips",
    "find_fuzzy_dates",
    "find_fuzzy_money",
    "flatten",
    "group_successful",
]
