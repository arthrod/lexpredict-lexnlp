"""Backwards-compatible unpickler for bundled sklearn models.

The legacy pickles under ``lexnlp/`` and ``test_data/`` were serialised under
sklearn 1.2.x / numpy 1.x. Two compatibility layers are applied on load so
they keep working on the modern (sklearn >=1.5, numpy >=2.1) runtime declared
in ``pyproject.toml``:

1. **Module renames** — old sklearn private-module paths
   (``sklearn.tree.tree`` → ``sklearn.tree``, etc.) are remapped via
   :class:`RenameUnpickler.find_class`.

2. **sklearn ``_tree.Tree`` node-array dtype upgrade** — sklearn 1.3 added a
   ``missing_go_to_left`` ``u1`` field to every Tree's ``nodes`` struct
   dtype. Loading a 1.2-era pickle under 1.5+ therefore raises
   ``ValueError: node array from the pickle has an incompatible dtype``.
   :func:`renamed_load` runs inside the same ``_patched_sklearn_tree_loader``
   context manager used by :mod:`lexnlp.ml.model_io` so the struct is
   upgraded transparently at load time.

Both layers are read-only — no pickle files are rewritten on disk — so the
artifacts under ``test_data/`` stay reproducible across checkouts.
"""

from __future__ import annotations

import pickle


class RenameUnpickler(pickle.Unpickler):
    """Unpickler that remaps renamed sklearn private-module paths."""

    _MODULE_RENAMES = {
        "sklearn.tree.tree": "sklearn.tree",
        "sklearn.ensemble.forest": "sklearn.ensemble._forest",
    }

    def find_class(self, module, name):
        return super().find_class(self._MODULE_RENAMES.get(module, module), name)


def renamed_load(file_obj):
    """Load a pickle while applying module-rename and sklearn-tree-ABI shims.

    The sklearn-tree patch is imported lazily from
    :mod:`lexnlp.ml.model_io` to avoid pulling sklearn / joblib into the
    import graph of modules that only need the rename layer.
    """

    from lexnlp.ml.model_io import (
        _patch_legacy_sklearn_estimator,
        _patched_sklearn_tree_loader,
    )

    with _patched_sklearn_tree_loader():
        return _patch_legacy_sklearn_estimator(RenameUnpickler(file_obj).load())
