"""Cosine similarity built on :func:`numpy.vecdot`.

``numpy.vecdot`` is a generalised ufunc (NumPy 2.1+) that computes the
dot product along the last axis in a single C call, so it replaces the
multi-step ``dot / linalg.norm / linalg.norm`` idiom that used to live
inside :mod:`lexnlp.extract.common.ocr_rating.ocr_rating_calculator`.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

from collections.abc import Sequence

import numpy as np
from numpy.typing import ArrayLike, NDArray


def cosine_similarity(a: ArrayLike | Sequence[float], b: ArrayLike | Sequence[float]) -> float:
    """Return the cosine similarity between two 1-D vectors.

    Returns ``0.0`` when either vector has zero magnitude rather than
    raising or producing ``NaN``. Raises :class:`ValueError` if either
    input is not 1-D or if the two vectors have different lengths.
    """
    va: NDArray[np.floating] = np.asarray(a, dtype=np.float64)
    vb: NDArray[np.floating] = np.asarray(b, dtype=np.float64)
    if va.ndim != 1 or vb.ndim != 1:
        raise ValueError(f"cosine_similarity expects 1-D vectors, got shapes {va.shape} and {vb.shape}")
    if va.shape != vb.shape:
        raise ValueError(f"shape mismatch: {va.shape} vs {vb.shape}")
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.vecdot(va, vb)) / (na * nb)


__all__ = ["cosine_similarity"]
