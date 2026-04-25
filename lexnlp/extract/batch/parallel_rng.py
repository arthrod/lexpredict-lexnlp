"""Deterministic child RNG streams for parallel batch extraction.

Built on :meth:`numpy.random.Generator.spawn`, which became part of the
public API in NumPy 2.3 and guarantees that the returned sub-streams are
statistically independent. That replaces the legacy
``RandomState(seed + worker_id)`` idiom, which is known to collide for
adjacent worker ids.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

import numpy as np

SeedLike = int | np.random.Generator


def spawn_child_generators(seed: SeedLike, n: int) -> list[np.random.Generator]:
    """Return ``n`` independent child :class:`numpy.random.Generator` streams.

    Parameters
    ----------
    seed:
        Integer seed, or a parent :class:`numpy.random.Generator`
        directly. Passing an integer is the common case and makes the
        call reproducible across runs.
    n:
        Number of child streams to create. Must be non-negative.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    if n == 0:
        return []
    parent = seed if isinstance(seed, np.random.Generator) else np.random.default_rng(seed)
    return list(parent.spawn(n))


__all__ = ["SeedLike", "spawn_child_generators"]
