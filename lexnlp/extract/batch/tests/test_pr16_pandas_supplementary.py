"""Supplementary tests for :mod:`lexnlp.extract.batch.pandas_output`.

Extends the existing test_pandas_output.py and test_pr16_pandas_isinstance.py
with additional coverage of:
- ``annotations_to_dataframe`` with multiple extra_columns
- Generator input (not just list)
- All-None annotation attributes
- ``prefer_arrow=False`` explicit path
- Column ordering guarantee
- ``_maybe_convert_to_arrow`` with prefer_arrow=False
- Row values correctly reflect annotation attributes

The module is imported directly to stay compatible with Python < 3.12.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

import importlib.util
import pathlib

import pytest

# pandas is an optional runtime dependency.
pytest.importorskip("pandas")
import pandas as pd  # noqa: E402

# Import pandas_output directly to bypass the PEP-695 __init__.py.
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.pandas_output",
    str(pathlib.Path(__file__).parent.parent / "pandas_output.py"),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

annotations_to_dataframe = _mod.annotations_to_dataframe
_row_from_annotation = _mod._row_from_annotation
_maybe_convert_to_arrow = _mod._maybe_convert_to_arrow


# ---------------------------------------------------------------------------
# Stub annotation types
# ---------------------------------------------------------------------------


class _FullAnn:
    """Annotation-like with all core fields plus extras."""

    def __init__(
        self,
        coords=(0, 10),
        text="hello",
        locale="en",
        record_type="test",
        category=None,
        score=None,
    ):
        self.coords = coords
        self.text = text
        self.locale = locale
        self.record_type = record_type
        self.category = category
        self.score = score


class _NoAttrs:
    """Annotation-like with none of the expected attributes."""
    pass


# ---------------------------------------------------------------------------
# annotations_to_dataframe — core columns
# ---------------------------------------------------------------------------


class TestAnnotationsToDataframeCoreCols:
    def test_column_order_is_record_locale_text_start_end(self) -> None:
        anns = [_FullAnn()]
        df = annotations_to_dataframe(anns, prefer_arrow=False)
        assert list(df.columns[:5]) == ["record_type", "locale", "text", "start", "end"]

    def test_correct_values_in_row(self) -> None:
        ann = _FullAnn(coords=(5, 15), text="word", locale="de", record_type="date")
        df = annotations_to_dataframe([ann], prefer_arrow=False)
        row = df.iloc[0]
        assert row["record_type"] == "date"
        assert row["locale"] == "de"
        assert row["text"] == "word"
        assert row["start"] == 5
        assert row["end"] == 15

    def test_single_annotation_one_row(self) -> None:
        df = annotations_to_dataframe([_FullAnn()], prefer_arrow=False)
        assert len(df) == 1

    def test_ten_annotations_ten_rows(self) -> None:
        anns = [_FullAnn(coords=(i, i + 1), text=str(i)) for i in range(10)]
        df = annotations_to_dataframe(anns, prefer_arrow=False)
        assert len(df) == 10


# ---------------------------------------------------------------------------
# annotations_to_dataframe — empty input
# ---------------------------------------------------------------------------


class TestAnnotationsToDataframeEmpty:
    def test_empty_list_returns_empty_dataframe(self) -> None:
        df = annotations_to_dataframe([], prefer_arrow=False)
        assert df.empty
        assert "record_type" in df.columns
        assert "start" in df.columns

    def test_empty_generator_returns_empty_dataframe(self) -> None:
        def _gen():
            return
            yield  # make it a generator

        df = annotations_to_dataframe(_gen(), prefer_arrow=False)
        assert df.empty

    def test_empty_with_extra_columns_has_those_columns(self) -> None:
        df = annotations_to_dataframe(
            [], prefer_arrow=False, extra_columns=("category",)
        )
        assert "category" in df.columns


# ---------------------------------------------------------------------------
# annotations_to_dataframe — generator input
# ---------------------------------------------------------------------------


class TestAnnotationsToDataframeGenerator:
    def test_accepts_generator(self) -> None:
        def _gen():
            for i in range(3):
                yield _FullAnn(coords=(i * 10, i * 10 + 5), text=f"text{i}")

        df = annotations_to_dataframe(_gen(), prefer_arrow=False)
        assert len(df) == 3

    def test_accepts_tuple_input(self) -> None:
        anns = tuple(_FullAnn() for _ in range(5))
        df = annotations_to_dataframe(anns, prefer_arrow=False)
        assert len(df) == 5


# ---------------------------------------------------------------------------
# annotations_to_dataframe — extra_columns
# ---------------------------------------------------------------------------


class TestAnnotationsToDataframeExtraColumns:
    def test_single_extra_column_present(self) -> None:
        ann = _FullAnn(category="geoentity")
        df = annotations_to_dataframe([ann], prefer_arrow=False, extra_columns=("category",))
        assert "category" in df.columns
        assert df.iloc[0]["category"] == "geoentity"

    def test_multiple_extra_columns(self) -> None:
        ann = _FullAnn(category="date", score=0.9)
        df = annotations_to_dataframe(
            [ann], prefer_arrow=False, extra_columns=("category", "score")
        )
        assert "category" in df.columns
        assert "score" in df.columns
        assert df.iloc[0]["score"] == 0.9

    def test_missing_extra_attr_becomes_none_or_na(self) -> None:
        """Annotation missing the requested extra attribute should yield None/NaN."""
        ann = _FullAnn()  # has no 'missing_field' attribute
        df = annotations_to_dataframe(
            [ann], prefer_arrow=False, extra_columns=("missing_field",)
        )
        val = df.iloc[0]["missing_field"]
        assert val is None or pd.isna(val)

    def test_extra_columns_appear_after_core_columns(self) -> None:
        ann = _FullAnn(category="act")
        df = annotations_to_dataframe(
            [ann], prefer_arrow=False, extra_columns=("category",)
        )
        cols = list(df.columns)
        # Core columns must come before extra columns.
        assert cols.index("end") < cols.index("category")

    def test_extra_column_with_none_value(self) -> None:
        ann = _FullAnn(category=None)
        df = annotations_to_dataframe(
            [ann], prefer_arrow=False, extra_columns=("category",)
        )
        val = df.iloc[0]["category"]
        assert val is None or pd.isna(val)


# ---------------------------------------------------------------------------
# annotations_to_dataframe — annotation with missing core attrs
# ---------------------------------------------------------------------------


class TestAnnotationsWithMissingAttrs:
    def test_no_attrs_annotation_row_is_all_none(self) -> None:
        df = annotations_to_dataframe([_NoAttrs()], prefer_arrow=False)
        row = df.iloc[0]
        assert row["record_type"] is None or pd.isna(row["record_type"])
        assert row["start"] is None or pd.isna(row["start"])
        assert row["end"] is None or pd.isna(row["end"])

    def test_annotation_with_wrong_coords_type(self) -> None:
        """An annotation where coords is an integer gets start=None, end=None."""
        ann = _FullAnn(coords=42)
        df = annotations_to_dataframe([ann], prefer_arrow=False)
        row = df.iloc[0]
        assert row["start"] is None or pd.isna(row["start"])
        assert row["end"] is None or pd.isna(row["end"])
        # But text should still be extracted.
        assert row["text"] == "hello"


# ---------------------------------------------------------------------------
# prefer_arrow parameter
# ---------------------------------------------------------------------------


class TestPreferArrow:
    def test_prefer_arrow_false_returns_dataframe(self) -> None:
        df = annotations_to_dataframe([_FullAnn()], prefer_arrow=False)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_prefer_arrow_true_returns_dataframe(self) -> None:
        """prefer_arrow=True must return a DataFrame regardless of pyarrow availability."""
        df = annotations_to_dataframe([_FullAnn()], prefer_arrow=True)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1


# ---------------------------------------------------------------------------
# _maybe_convert_to_arrow
# ---------------------------------------------------------------------------


class TestMaybeConvertToArrow:
    def test_prefer_arrow_false_returns_frame_unchanged(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = _maybe_convert_to_arrow(df, prefer_arrow=False)
        assert isinstance(result, pd.DataFrame)
        assert list(result["a"]) == [1, 2, 3]

    def test_prefer_arrow_true_returns_frame(self) -> None:
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = _maybe_convert_to_arrow(df, prefer_arrow=True)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2

    def test_empty_frame_prefer_arrow_false(self) -> None:
        df = pd.DataFrame({"a": []})
        result = _maybe_convert_to_arrow(df, prefer_arrow=False)
        assert result.empty


# ---------------------------------------------------------------------------
# _row_from_annotation — PR-16 isinstance path additional cases
# ---------------------------------------------------------------------------


class TestRowFromAnnotationAdditional:
    def test_bytearray_coords_gives_none(self) -> None:
        """bytearray is not a tuple or list."""
        class _ByteCoords:
            coords = bytearray(b"\x00\x01")
            text = "t"
            locale = "en"
            record_type = "x"

        row = _row_from_annotation(_ByteCoords())
        assert row["start"] is None
        assert row["end"] is None

    def test_set_coords_gives_none(self) -> None:
        """Sets are not tuples or lists."""
        class _SetCoords:
            coords = {0, 10}
            text = "t"
            locale = "en"
            record_type = "x"

        row = _row_from_annotation(_SetCoords())
        assert row["start"] is None
        assert row["end"] is None

    def test_negative_coords_are_valid(self) -> None:
        """Negative offsets are unusual but technically valid for the isinstance check."""
        class _NegCoords:
            coords = (-5, -1)
            text = "t"
            locale = "en"
            record_type = "x"

        row = _row_from_annotation(_NegCoords())
        assert row["start"] == -5
        assert row["end"] == -1