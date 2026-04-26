"""Citation-reporter variation normalization powered by ``reporters_db``.

``reporters_db`` ships three dictionaries:

* ``REPORTERS`` — canonical reporter definitions (already used).
* ``EDITIONS`` — citation abbreviation → canonical reporter key
  (already used).
* ``VARIATIONS_ONLY`` — non-canonical abbreviations that should map
  back to canonical reporters (e.g. ``"U.S."`` → ``"United States
  Reports"``).

The original :mod:`lexnlp.extract.en.citations` only imports the first
two. This module adds variation-aware normalization so callers can map
a legacy/typographic variant back to its canonical form before running
citation extraction or comparison.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from functools import lru_cache

# ``VARIATIONS_ONLY`` has existed in ``reporters_db`` for a long time,
# but older releases expose the name differently. We accept both spellings
# so LexNLP stays compatible across the supported pin range.
try:
    from reporters_db import VARIATIONS_ONLY as _VARIATIONS_RAW
except ImportError:  # pragma: no cover
    try:
        # type: ignore[attr-defined] — older ``reporters_db`` releases expose
        # the dictionary as ``VARIATIONS`` instead of ``VARIATIONS_ONLY``;
        # the fallback is intentional and not declared in modern stubs.
        from reporters_db import VARIATIONS as _VARIATIONS_RAW  # type: ignore[attr-defined]
    except ImportError:  # pragma: no cover
        _VARIATIONS_RAW = {}

from reporters_db import EDITIONS


@lru_cache(maxsize=1)
def variation_map() -> dict[str, tuple[str, ...]]:
    """Return variation → canonical citations map.

    ``reporters_db`` models variations as ``variant -> [canonical1, ...]``
    because some abbreviations are ambiguous. We expose the exhaustive
    list so callers can decide how to disambiguate.
    """
    result: dict[str, tuple[str, ...]] = {}
    for key, value in _VARIATIONS_RAW.items():
        if isinstance(value, list):
            result[key] = tuple(value)
        elif isinstance(value, str):
            result[key] = (value,)
    return result


@lru_cache(maxsize=1)
def _normalized_variation_index() -> dict[str, tuple[str, ...]]:
    """Pre-built whitespace-stripped index used by :func:`canonical_for`.

    Avoids the O(n) per-call scan of ``variation_map()`` for the common
    "user typed extra spaces around a period" case.
    """
    return {variation.replace(" ", ""): canons for variation, canons in variation_map().items()}


def canonical_for(variant: str) -> tuple[str, ...]:
    """Return the canonical citation(s) for a given variant.

    Returns an empty tuple when ``variant`` is unknown. Callers that
    only want the first (most common) canonical form can index with
    ``[0]`` and fall back to the original string:

        canonical_for("U. S.")[:1] or (variant,)
    """
    if not variant:
        return ()
    direct = variation_map().get(variant)
    if direct is not None:
        return direct
    # Mild normalization: strip whitespace around "." segments. Use the
    # pre-built index so this stays an O(1) hash lookup.
    return _normalized_variation_index().get(variant.replace(" ", ""), ())


def is_known_reporter(name: str) -> bool:
    """Check whether ``name`` is either a canonical or variation reporter."""
    if not name:
        return False
    return name in EDITIONS or name in variation_map()


def normalize_reporter(name: str) -> str:
    """Return the canonical reporter for ``name`` or ``name`` unchanged.

    Chooses the *first* canonical candidate when multiple exist, matching
    ``reporters_db`` ordering. Callers that need to expose all candidates
    should use :func:`canonical_for` directly.
    """
    if not name:
        return name
    if name in EDITIONS:
        return name
    variants = canonical_for(name)
    return variants[0] if variants else name


__all__ = [
    "canonical_for",
    "is_known_reporter",
    "normalize_reporter",
    "variation_map",
]
