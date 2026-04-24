"""Vectorised text helpers built on :mod:`numpy.strings` (NumPy ≥ 2.3).

These are thin wrappers that pay off whenever the library has already
gathered a batch of strings — extraction pipelines, corpus preprocessing,
OCR post-processing, Arrow/pandas DataFrame columns — and would otherwise
drop into a Python-level list comprehension.

Every helper accepts any iterable of ``str`` and returns a NumPy array
with the SIMD-accelerated implementation that shipped in NumPy 2.3.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

from collections.abc import Iterable

import numpy as np
from numpy.typing import NDArray


def _as_string_array(texts: Iterable[str]) -> NDArray[np.str_]:
    if isinstance(texts, np.ndarray):
        return texts.astype(np.str_, copy=False)
    return np.asarray(list(texts), dtype=np.str_)


def vectorized_lower(texts: Iterable[str]) -> NDArray[np.str_]:
    """Return ``texts`` lowercased via the NumPy 2.3 SIMD string kernel."""
    return np.strings.lower(_as_string_array(texts))


def vectorized_strip(texts: Iterable[str]) -> NDArray[np.str_]:
    """Strip surrounding whitespace from every element of ``texts``."""
    return np.strings.strip(_as_string_array(texts))


def vectorized_startswith(texts: Iterable[str], prefix: str) -> NDArray[np.bool_]:
    """Boolean mask of whether each element of ``texts`` begins with ``prefix``."""
    return np.strings.startswith(_as_string_array(texts), prefix)


def vectorized_substring_count(texts: Iterable[str], substring: str) -> NDArray[np.int64]:
    """Count (non-overlapping) occurrences of ``substring`` in each element."""
    return np.strings.count(_as_string_array(texts), substring)


def vectorized_slice(texts: Iterable[str], start: int, stop: int) -> NDArray[np.str_]:
    """Return the ``[start:stop]`` slice of every element of ``texts``.

    ``stop`` past the end of any individual element is handled the same
    way Python slicing does — the result is simply truncated.
    """
    return np.strings.slice(_as_string_array(texts), start, stop)


__all__ = [
    "vectorized_lower",
    "vectorized_slice",
    "vectorized_startswith",
    "vectorized_strip",
    "vectorized_substring_count",
]
