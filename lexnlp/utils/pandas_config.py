"""Pandas 2.2+ configuration helpers.

pandas 2.2 introduced a Copy-on-Write opt-in (``copy_on_write``) and a
future-string inference opt-in (``future.infer_string``). Both become
the default in pandas 3.0. LexNLP ships its own defaults here so
downstream extractors and scripts can call a single helper rather than
each learning the incantation.

The helpers are idempotent and cheap; call them once near the top of a
script or notebook.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


def enable_copy_on_write(*, warn_mode: bool = False) -> None:
    """Opt into pandas 2.2 Copy-on-Write semantics.

    Args:
        warn_mode: When ``True``, set the option to ``"warn"`` instead of
            ``True``. The warn mode surfaces every case where a chained
            assignment would behave differently — useful while migrating
            older extractor code.
    """
    import pandas as pd

    pd.options.mode.copy_on_write = "warn" if warn_mode else True


def enable_future_string_dtype() -> None:
    """Opt into pandas 3.0's future Arrow-backed string dtype inference.

    Reduces memory use for string columns in extractor outputs roughly 3x
    versus the legacy ``object`` dtype.
    """
    import pandas as pd

    pd.options.future.infer_string = True


def convert_to_arrow(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert ``frame`` to use PyArrow-backed dtypes when available.

    Returns ``frame`` unchanged when PyArrow is missing or the pandas
    build in use does not support ``convert_dtypes(dtype_backend=...)``.
    """
    try:
        import pyarrow  # noqa: F401 — availability probe only
    except ImportError:
        return frame
    try:
        return frame.convert_dtypes(dtype_backend="pyarrow")
    except TypeError:
        return frame


def read_csv_arrow(path: str | Path, **kwargs: Any) -> pd.DataFrame:
    """Read a CSV into a pandas DataFrame, preferring the PyArrow backend.

    When :mod:`pyarrow` is importable the call forwards
    ``dtype_backend="pyarrow"`` to :func:`pandas.read_csv`, which is
    both faster and more memory-efficient for the typical LexNLP
    catalog CSVs (geoentities, regulations, courts). When PyArrow is
    missing the helper silently falls back to the default NumPy backend
    so downstream callers do not have to guard the import.
    """
    import pandas as pd

    try:
        import pyarrow  # noqa: F401 — availability probe only
    except ImportError:
        return pd.read_csv(path, **kwargs)
    kwargs.setdefault("dtype_backend", "pyarrow")
    return pd.read_csv(path, **kwargs)


def apply_default_options() -> dict[str, Any]:
    """Turn on CoW + future-string inference together.

    Returns a small report dict describing which toggles were applied so
    callers can log or assert the outcome.
    """
    enable_copy_on_write()
    enable_future_string_dtype()
    return {"copy_on_write": True, "future.infer_string": True}


__all__ = [
    "apply_default_options",
    "convert_to_arrow",
    "enable_copy_on_write",
    "enable_future_string_dtype",
    "read_csv_arrow",
]
