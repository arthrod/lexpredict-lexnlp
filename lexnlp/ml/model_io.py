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
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from skops.io import dump as _skops_dump
from skops.io import get_untrusted_types
from skops.io import load as _skops_load

LOGGER = logging.getLogger(__name__)

CANONICAL_SUFFIX = ".skops"
_LEGACY_SUFFIXES = frozenset({".pickle", ".pkl", ".cloudpickle", ".joblib"})
_sklearn_patch_lock = threading.Lock()


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
            try:
                return pickle.load(file)
            except (pickle.UnpicklingError, ValueError, EOFError, AttributeError):
                if not _looks_like_joblib_pickle(path):
                    raise
                LOGGER.debug("Falling back to joblib-compatible legacy loader: %s", path)
        return _load_legacy_joblib(path)
    if suffix == ".cloudpickle":
        from cloudpickle import load as cloudpickle_load

        with path.open("rb") as file:
            return cloudpickle_load(file)
    if suffix == ".joblib":
        return _load_legacy_joblib(path)
    # Reject unknown suffixes instead of attempting unsafe deserialization
    raise ValueError(
        f"Unsupported file suffix '{suffix}' for legacy model loading. "
        f"Expected one of: {', '.join(sorted(_LEGACY_SUFFIXES))}"
    )


def _load_legacy_joblib(path: Path) -> Any:
    """Load a legacy joblib artifact with sklearn tree ABI shims when needed."""

    import joblib

    with _patched_sklearn_tree_loader():
        return _patch_legacy_sklearn_estimator(joblib.load(path))


def _looks_like_joblib_pickle(path: Path) -> bool:
    """Return ``True`` when a legacy ``.pickle`` file looks joblib-compressed."""

    with path.open("rb") as file:
        return file.read(1) == b"\x78"


def _patch_legacy_sklearn_estimator(obj: Any) -> Any:
    """Populate sklearn runtime attrs that older pickles did not persist."""

    if isinstance(obj, dict):
        for value in obj.values():
            _patch_legacy_sklearn_estimator(value)
        return obj
    if isinstance(obj, (list, tuple, set)):
        for value in obj:
            _patch_legacy_sklearn_estimator(value)
        return obj

    if hasattr(obj, "steps"):
        for _, step in obj.steps:
            _patch_legacy_sklearn_estimator(step)

    if hasattr(obj, "base_estimator") and not hasattr(obj, "estimator"):
        obj.estimator = obj.base_estimator
    if hasattr(obj, "tree_") and not hasattr(obj, "monotonic_cst"):
        obj.monotonic_cst = None
    if hasattr(obj, "estimators_") and not hasattr(obj, "monotonic_cst"):
        obj.monotonic_cst = None
        for estimator in obj.estimators_:
            _patch_legacy_sklearn_estimator(estimator)
        if hasattr(obj, "estimator"):
            _patch_legacy_sklearn_estimator(obj.estimator)

    return obj


@contextmanager
def _patched_sklearn_tree_loader():
    """Patch sklearn's tree-node validator so pre-1.3 models still load."""

    _sklearn_patch_lock.acquire()
    try:
        try:
            import numpy
            from sklearn.tree import _tree
        except ImportError:
            yield
            return

        original = _tree._check_node_ndarray

        def compat(node_ndarray, expected_dtype):
            names = getattr(getattr(node_ndarray, "dtype", None), "names", None)
            expected_names = getattr(expected_dtype, "names", None)
            if names and expected_names and "missing_go_to_left" in expected_names and "missing_go_to_left" not in names:
                patched = numpy.empty(node_ndarray.shape, dtype=expected_dtype)
                for name in names:
                    patched[name] = node_ndarray[name]
                patched["missing_go_to_left"] = 0
                node_ndarray = patched
            return original(node_ndarray, expected_dtype)

        _tree._check_node_ndarray = compat
        try:
            yield
        finally:
            _tree._check_node_ndarray = original
    finally:
        _sklearn_patch_lock.release()


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

    if path.suffix.lower() in _LEGACY_SUFFIXES:
        LOGGER.debug("Loading legacy model via pickle-family loader: %s", path)
        return _load_legacy(path)

    # Unknown suffixes must not silently fall back to pickle-family loaders
    # because that broadens the unsafe deserialization surface. Try skops
    # (some skops artifacts may not use the canonical suffix); otherwise
    # surface a ValueError listing the supported suffixes.
    try:
        return _load_skops(path, trusted=trusted)
    except Exception as exc:
        raise ValueError(
            f"Unsupported model suffix '{path.suffix}'. "
            f"Use '{CANONICAL_SUFFIX}' or one of {sorted(_LEGACY_SUFFIXES)}."
        ) from exc


def _load_skops(path: Path, *, trusted: bool) -> Any:
    """Invoke :func:`skops.io.load` with a ``trusted`` argument that
    matches the current skops API (list of allowed custom type names)."""

    # When the caller passes ``trusted=True`` we explicitly accept every
    # custom type referenced by the artifact. Otherwise pass an empty
    # list so skops enforces its own default trusted set and raises
    # UntrustedTypesFoundException if unknown types appear.
    untrusted = list(get_untrusted_types(file=path) or [])
    return _skops_load(path, trusted=untrusted if trusted else [])