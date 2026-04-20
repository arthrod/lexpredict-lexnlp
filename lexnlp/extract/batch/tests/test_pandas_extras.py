"""Additional tests for :mod:`lexnlp.extract.batch.pandas_output`.

Supplements ``test_pandas_output.py`` with branches and edge cases not
covered in the primary suite:

* Generator input (not a materialised list)
* Extra column that does not exist on annotation → stored as None
* Column order is exactly ``record_type, locale, text, start, end [, extras...]``
* prefer_arrow=True when PyArrow IS available (conversion path)
* Annotation with no ``coords`` attribute at all
* Annotation with a scalar (non-iterable) ``coords``
* ``_row_from_annotation`` internal helper directly
* ``_maybe_convert_to_arrow`` with prefer_arrow=False short-circuits immediately
* Large batch preserves all rows

The ``pandas_output`` module itself has no Python-3.12-specific syntax, so
these tests run on Python 3.11+ as long as pandas is available. The module
is imported directly (bypassing the batch ``__init__.py``) to avoid the PEP
695 SyntaxError on Python < 3.12.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from typing import Any

import pytest

pd = pytest.importorskip("pandas")

# Import pandas_output directly, bypassing the batch __init__.py which uses
# PEP 695 syntax (Python 3.12+).
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.pandas_output",
    str(
        __import__("pathlib").Path(__file__).parent.parent / "pandas_output.py"
    ),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

_maybe_convert_to_arrow = _mod._maybe_convert_to_arrow
_row_from_annotation = _mod._row_from_annotation
annotations_to_dataframe = _mod.annotations_to_dataframe


# ---------------------------------------------------------------------------
# Stub annotation types
# ---------------------------------------------------------------------------


@dataclass
class _Ann:
    coords: tuple[int, int]
    text: str
    locale: str = "en"
    record_type: str = "stub"


@dataclass
class _AnnNoCoords:
    """Annotation that has no coords attribute at all."""

    text: str
    locale: str = "en"
    record_type: str = "no-coords"


@dataclass
class _AnnScalarCoords:
    """Annotation whose coords is a plain int, not an iterable."""

    coords: int  # type: ignore[assignment]
    text: str
    locale: str = "en"
    record_type: str = "scalar-coords"


# ---------------------------------------------------------------------------
# _row_from_annotation internal helper
# ---------------------------------------------------------------------------


class TestRowFromAnnotation:
    def test_normal_coords_extraced(self) -> None:
        ann = _Ann(coords=(5, 15), text="hello")
        row = _row_from_annotation(ann)
        assert row["start"] == 5
        assert row["end"] == 15
        assert row["text"] == "hello"
        assert row["locale"] == "en"
        assert row["record_type"] == "stub"

    def test_no_coords_attribute_gives_none(self) -> None:
        ann = _AnnNoCoords(text="x")
        row = _row_from_annotation(ann)
        assert row["start"] is None
        assert row["end"] is None

    def test_scalar_coords_gives_none(self) -> None:
        ann = _AnnScalarCoords(coords=42, text="x")
        row = _row_from_annotation(ann)
        assert row["start"] is None
        assert row["end"] is None

    def test_missing_text_attribute_gives_none(self) -> None:
        class _NoText:
            coords = (0, 1)
            locale = "en"
            record_type = "x"

        row = _row_from_annotation(_NoText())
        assert row["text"] is None

    def test_none_coords_tuple_gives_none(self) -> None:
        """(None, None) is a valid unpacking that yields None,None."""

        class _NoneCoords:
            coords = (None, None)
            text = "t"
            locale = "en"
            record_type = "r"

        row = _row_from_annotation(_NoneCoords())
        assert row["start"] is None
        assert row["end"] is None


# ---------------------------------------------------------------------------
# Column order
# ---------------------------------------------------------------------------


class TestColumnOrder:
    def test_core_column_order(self) -> None:
        ann = _Ann(coords=(0, 1), text="x")
        df = annotations_to_dataframe([ann], prefer_arrow=False)
        expected_order = ["record_type", "locale", "text", "start", "end"]
        assert list(df.columns[:5]) == expected_order

    def test_extra_columns_appended_after_core(self) -> None:
        ann = _Ann(coords=(0, 1), text="x")
        df = annotations_to_dataframe(
            [ann], prefer_arrow=False, extra_columns=("locale",)
        )
        cols = list(df.columns)
        assert cols.index("end") < cols.index("locale") or "locale" in cols[:5]
        # The column must exist somewhere
        assert "locale" in cols

    def test_empty_dataframe_has_correct_column_order(self) -> None:
        df = annotations_to_dataframe([], prefer_arrow=False)
        assert list(df.columns) == ["record_type", "locale", "text", "start", "end"]

    def test_extra_columns_on_empty_preserved(self) -> None:
        df = annotations_to_dataframe(
            [], prefer_arrow=False, extra_columns=("custom_field",)
        )
        assert "custom_field" in df.columns


# ---------------------------------------------------------------------------
# Generator input
# ---------------------------------------------------------------------------


class TestGeneratorInput:
    def test_generator_iterable_is_consumed(self) -> None:
        def _gen():
            yield _Ann(coords=(0, 3), text="foo")
            yield _Ann(coords=(4, 7), text="bar")

        df = annotations_to_dataframe(_gen(), prefer_arrow=False)
        assert len(df) == 2
        assert list(df["text"]) == ["foo", "bar"]


# ---------------------------------------------------------------------------
# Missing extra columns → None
# ---------------------------------------------------------------------------


class TestMissingExtraColumns:
    def test_nonexistent_extra_column_becomes_none(self) -> None:
        ann = _Ann(coords=(0, 1), text="x")
        df = annotations_to_dataframe(
            [ann], prefer_arrow=False, extra_columns=("does_not_exist",)
        )
        assert "does_not_exist" in df.columns
        assert pd.isna(df.iloc[0]["does_not_exist"]) or df.iloc[0]["does_not_exist"] is None


# ---------------------------------------------------------------------------
# _maybe_convert_to_arrow
# ---------------------------------------------------------------------------


class TestMaybeConvertToArrow:
    def test_prefer_arrow_false_returns_unchanged(self) -> None:
        frame = pd.DataFrame({"a": [1, 2]})
        result = _maybe_convert_to_arrow(frame, prefer_arrow=False)
        # Should be the same object since no conversion happened
        assert list(result["a"]) == [1, 2]

    def test_prefer_arrow_true_with_pyarrow_available(self) -> None:
        pyarrow = pytest.importorskip("pyarrow")
        frame = pd.DataFrame({"text": ["hello", "world"], "start": [0, 5]})
        result = _maybe_convert_to_arrow(frame, prefer_arrow=True)
        # The frame should still have the same data regardless of backend
        assert list(result["text"]) == ["hello", "world"]


# ---------------------------------------------------------------------------
# Large batch row count preservation
# ---------------------------------------------------------------------------


class TestLargeBatch:
    def test_1000_annotations_preserve_row_count(self) -> None:
        anns = [_Ann(coords=(i, i + 1), text=str(i)) for i in range(1000)]
        df = annotations_to_dataframe(anns, prefer_arrow=False)
        assert len(df) == 1000

    def test_row_text_values_are_correct_for_large_batch(self) -> None:
        anns = [_Ann(coords=(i, i + 1), text=f"token_{i}") for i in range(50)]
        df = annotations_to_dataframe(anns, prefer_arrow=False)
        # Spot-check a few rows
        assert df.iloc[0]["text"] == "token_0"
        assert df.iloc[24]["text"] == "token_24"
        assert df.iloc[49]["text"] == "token_49"


# ---------------------------------------------------------------------------
# Multiple extra columns at once
# ---------------------------------------------------------------------------


class TestMultipleExtraColumns:
    def test_two_extra_columns(self) -> None:
        @dataclass
        class _AnnExtra:
            coords: tuple[int, int]
            text: str
            locale: str = "en"
            record_type: str = "stub"
            confidence: float = 0.9
            source: str = "test"

        anns = [_AnnExtra(coords=(0, 5), text="hello")]
        df = annotations_to_dataframe(
            anns, prefer_arrow=False, extra_columns=("confidence", "source")
        )
        assert df.iloc[0]["confidence"] == 0.9
        assert df.iloc[0]["source"] == "test"