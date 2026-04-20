"""Arrow-backed pandas helpers for LexNLP annotations.

``pandas>=2.2`` makes PyArrow-backed dtypes stable and enables Copy-on-Write
by default. This module converts a batch of
:class:`~lexnlp.extract.common.annotations.text_annotation.TextAnnotation`
objects into a :class:`pandas.DataFrame` that uses PyArrow storage
(``dtype_backend="pyarrow"``) whenever PyArrow is available, and transparently
falls back to the NumPy backend if it isn't.

The conversion is intentionally lossy — annotations contain rich per-class
metadata, but the DataFrame keeps the common surface every
:class:`TextAnnotation` exposes (``coords``, ``text``, ``locale``, ``record_type``).
Consumers that need the extra fields should use ``to_dictionary()`` on each
annotation directly.

Keeping the helper in a dedicated module also lets callers opt into the
pandas + PyArrow cost only when they need it; importing
:mod:`lexnlp.extract.batch` does not require pyarrow to be installed.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pandas as pd


_CORE_COLUMNS: tuple[str, ...] = (
    "record_type",
    "locale",
    "text",
    "start",
    "end",
)


def _row_from_annotation(annotation: Any) -> dict[str, Any]:
    """Extract the common fields every ``TextAnnotation`` exposes.

    Uses attribute access rather than ``to_dictionary`` because the latter
    flattens non-primitive sub-structures (tags, attributes) in a way that
    pandas cannot infer a single dtype for.
    """
    coords = getattr(annotation, "coords", (None, None))
    start: int | None
    end: int | None
    try:
        start, end = coords  # type: ignore[misc]
    except (TypeError, ValueError):
        start, end = None, None
    return {
        "record_type": getattr(annotation, "record_type", None),
        "locale": getattr(annotation, "locale", None),
        "text": getattr(annotation, "text", None),
        "start": start,
        "end": end,
    }


def annotations_to_dataframe(
    annotations: Iterable[Any],
    *,
    prefer_arrow: bool = True,
    extra_columns: tuple[str, ...] = (),
) -> pd.DataFrame:
    """Convert an iterable of annotations into a DataFrame.

    Args:
        annotations: Any iterable of annotation instances — typically the
            output of ``list(get_*_annotations(text))`` or the flattened
            output of :func:`lexnlp.extract.batch.extract_batch`.
        prefer_arrow: When ``True`` (the default) and ``pyarrow`` is
            importable, request ``dtype_backend="pyarrow"`` so text columns
            use ``string[pyarrow]`` and integers use Arrow's nullable int
            family. Falls back to the default NumPy backend otherwise.
        extra_columns: Additional annotation attributes to extract
            alongside the five core columns. Missing attributes are stored
            as ``None``.

    Returns:
        A :class:`pandas.DataFrame` with one row per annotation. The column
        order is ``record_type, locale, text, start, end`` followed by
        ``extra_columns``.
    """
    import pandas as pd  # local import to keep module import cheap

    rows: list[dict[str, Any]] = []
    for ann in annotations:
        row = _row_from_annotation(ann)
        for extra in extra_columns:
            row[extra] = getattr(ann, extra, None)
        rows.append(row)

    if not rows:
        columns = list(_CORE_COLUMNS) + list(extra_columns)
        empty = pd.DataFrame({c: [] for c in columns})
        return _maybe_convert_to_arrow(empty, prefer_arrow)

    frame = pd.DataFrame(rows)
    return _maybe_convert_to_arrow(frame, prefer_arrow)


def _maybe_convert_to_arrow(frame: pd.DataFrame, prefer_arrow: bool) -> pd.DataFrame:
    """Return ``frame`` with a pyarrow-backed dtype when possible."""
    if not prefer_arrow:
        return frame
    try:
        import pyarrow  # noqa: F401 — just to verify availability
    except ImportError:
        return frame
    # pandas 2.2+: ``convert_dtypes(dtype_backend="pyarrow")`` is the stable,
    # documented entry point. Older pandas versions raise TypeError; the
    # fallback silently keeps the NumPy backend.
    try:
        return frame.convert_dtypes(dtype_backend="pyarrow")
    except TypeError:
        return frame


__all__ = ["annotations_to_dataframe"]
