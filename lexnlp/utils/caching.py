"""Disk-backed caching helpers built on :mod:`joblib.Memory`.

LexNLP loads several artefacts that are expensive to rebuild — compiled
:mod:`regex` patterns, scikit-learn models, NLTK resources, gensim
embeddings. The cost is borne by every script invocation even when the
underlying inputs haven't changed. :class:`joblib.Memory` turns any
pure callable into one whose first call persists its output to disk and
subsequent calls replay that output without rerunning.

Rather than forcing every module to instantiate its own ``Memory``, this
helper centralises a single process-local cache rooted at
``~/.cache/lexnlp`` (overridable via the ``LEXNLP_CACHE_DIR``
environment variable). Modules that want to cache a function just wrap
it with :func:`cache`.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

DEFAULT_CACHE_ENV = "LEXNLP_CACHE_DIR"


def _default_cache_dir() -> Path:
    override = os.environ.get(DEFAULT_CACHE_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cache" / "lexnlp"


@lru_cache(maxsize=1)
def get_memory(verbose: int = 0) -> joblib.Memory:
    """Return the process-local :class:`joblib.Memory` instance.

    The returned object is cached so every module shares a single cache
    root and thus a single on-disk footprint. The directory is created
    lazily on first write (joblib does this internally), so importing
    this module is free even on read-only filesystems.
    """
    cache_dir = _default_cache_dir()
    return joblib.Memory(location=str(cache_dir), verbose=verbose)


def cache[F: Callable[..., Any]](func: F) -> F:
    """Decorate ``func`` with disk-backed memoisation.

    Equivalent to ``get_memory().cache(func)`` but cleaner at call
    sites. Mirrors the signature of ``functools.lru_cache`` so callers
    can swap between in-memory and on-disk caching by changing one
    decorator.
    """
    # type: ignore[return-value] — joblib.Memory.cache returns a
    # ``MemorizedFunc`` wrapper that mimics ``func`` at runtime but is not
    # statically a subtype of ``F``; the decorator's contract is that the
    # call signature is preserved, which the wrapper honours.
    return get_memory().cache(func)  # type: ignore[return-value]


def clear_cache() -> None:
    """Remove every cached entry. Useful for ``conftest.py`` fixtures."""
    get_memory().clear(warn=False)


__all__ = ["cache", "clear_cache", "get_memory"]
