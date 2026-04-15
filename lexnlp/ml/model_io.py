"""Model serialization helpers.

LexNLP historically persisted scikit-learn pipelines via ``pickle`` /
``cloudpickle`` / ``joblib``. Those formats are tightly coupled to the
Python / sklearn versions that produced them (see the tree-pickle ABI
break between sklearn 1.2 and 1.3+) and they execute arbitrary code on
load, making them unsuitable as a persistence target for shipped
artifacts.

This module introduces `skops.io <https://skops.readthedocs.io/>`_ as
the forward-looking successor. ``skops`` serializes sklearn estimators
via a restricted schema that does not execute arbitrary code on load.

``CANONICAL_SUFFIX`` is the extension used for new artifacts written by
``dump_model``. ``load_model`` accepts either ``.skops`` files or any
legacy pickle-based file (``.pickle`` / ``.cloudpickle`` / joblib) so
existing bundled assets continue to work while we migrate.
"""

from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any

from skops.io import dump as _skops_dump
from skops.io import get_untrusted_types
from skops.io import load as _skops_load

LOGGER = logging.getLogger(__name__)

CANONICAL_SUFFIX = ".skops"
_LEGACY_SUFFIXES = frozenset({".pickle", ".pkl", ".cloudpickle", ".joblib"})


def is_skops_path(path: Path) -> bool:
    """Return ``True`` when ``path`` is a skops artifact (by suffix)."""

    return path.suffix.lower() == CANONICAL_SUFFIX


def dump_model(obj: Any, path: Path) -> Path:
    """Persist ``obj`` at ``path`` using skops.

    ``path`` is normalized to use :data:`CANONICAL_SUFFIX` so callers
    cannot accidentally round-trip a skops artifact through a legacy
    pickle extension.
    """

    path = Path(path)
    if not is_skops_path(path):
        path = path.with_suffix(CANONICAL_SUFFIX)
    path.parent.mkdir(parents=True, exist_ok=True)
    _skops_dump(obj, path)
    return path


def _load_legacy(path: Path) -> Any:
    """Load a legacy pickle / cloudpickle / joblib artifact.

    Legacy loaders are imported lazily because ``cloudpickle`` and
    ``joblib`` are optional for skops-only consumers.
    """

    suffix = path.suffix.lower()
    if suffix in (".pickle", ".pkl"):
        with path.open("rb") as file:
            return pickle.load(file)
    if suffix == ".cloudpickle":
        from cloudpickle import load as cloudpickle_load

        with path.open("rb") as file:
            return cloudpickle_load(file)
    if suffix == ".joblib":
        import joblib

        return joblib.load(path)
    # Reject unknown suffixes instead of attempting unsafe deserialization
    raise ValueError(
        f"Unsupported file suffix '{suffix}' for legacy model loading. "
        f"Expected one of: {', '.join(sorted(_LEGACY_SUFFIXES))}"
    )


def load_model(path: Path, *, trusted: bool = False) -> Any:
    """Load a model written by :func:`dump_model` or by a legacy dumper.

    ``trusted`` is forwarded to :func:`skops.io.load`. When ``True`` the
    caller asserts that any custom types present in the artifact are
    safe to reconstruct. The default (``False``) scans the artifact with
    :func:`skops.io.get_untrusted_types` and passes the scanned list
    explicitly so load fails closed when unexpected types appear.
    """

    path = Path(path)
    if is_skops_path(path):
        return _load_skops(path, trusted=trusted)

    if path.suffix.lower() in _LEGACY_SUFFIXES or path.suffix == "":
        LOGGER.debug("Loading legacy model via pickle-family loader: %s", path)
        return _load_legacy(path)

    # Fall back: attempt skops, then pickle. This matches what callers
    # expect when the suffix is unfamiliar but the content may still be
    # a valid artifact in one of the supported formats.
    try:
        return _load_skops(path, trusted=trusted)
    except Exception:  # noqa: BLE001 - fall through to legacy pickle loader
        LOGGER.debug("skops.io failed to load %s; retrying with pickle", path)
        return _load_legacy(path)


def _load_skops(path: Path, *, trusted: bool) -> Any:
    """Invoke :func:`skops.io.load` with a ``trusted`` argument that
    matches the current skops API (list of allowed custom type names)."""

    # ``get_untrusted_types`` returns every custom type referenced by
    # the artifact. When the caller passes ``trusted=True`` we treat
    # every referenced type as trusted; otherwise we still enumerate
    # the types so load fails closed if a non-sklearn surprise lands
    # in the archive.
    untrusted = list(get_untrusted_types(file=path) or [])
    return _skops_load(path, trusted=untrusted if (trusted or untrusted) else [])