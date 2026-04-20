"""Tests for :mod:`lexnlp.extract.batch.pandas_output`.

These tests exercise the lightweight annotation-to-DataFrame conversion with
plain stub objects so they do not pull in the full extraction stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

pd = pytest.importorskip("pandas")

from lexnlp.extract.batch.pandas_output import annotations_to_dataframe  # noqa: E402


@dataclass
class _StubAnnotation:
    """Minimal stand-in for :class:`TextAnnotation`."""

    coords: tuple[int, int]
    text: str
    locale: str = "en"
    record_type: str = "stub"
    extra_field: Any = None


class TestAnnotationsToDataFrame:
    def test_returns_dataframe_with_core_columns(self) -> None:
        annots = [_StubAnnotation(coords=(0, 5), text="Hello")]
        df = annotations_to_dataframe(annots, prefer_arrow=False)
        assert set(df.columns) == {"record_type", "locale", "text", "start", "end"}
        assert df.iloc[0]["start"] == 0
        assert df.iloc[0]["end"] == 5
        assert df.iloc[0]["text"] == "Hello"

    def test_empty_input_returns_empty_frame_with_columns(self) -> None:
        df = annotations_to_dataframe([], prefer_arrow=False)
        assert df.empty
        assert list(df.columns) == ["record_type", "locale", "text", "start", "end"]

    def test_extra_columns_are_appended(self) -> None:
        annots = [
            _StubAnnotation(coords=(0, 3), text="abc", extra_field="deadbeef"),
            _StubAnnotation(coords=(4, 7), text="xyz"),
        ]
        df = annotations_to_dataframe(
            annots,
            prefer_arrow=False,
            extra_columns=("extra_field",),
        )
        assert "extra_field" in df.columns
        assert df.iloc[0]["extra_field"] == "deadbeef"
        # pandas coerces ``None`` to ``NaN`` in object columns under certain
        # dtype flags; accept both forms.
        assert pd.isna(df.iloc[1]["extra_field"]) or df.iloc[1]["extra_field"] is None

    def test_malformed_coords_become_none(self) -> None:
        annots = [_StubAnnotation(coords=(1, 2, 3), text="bad")]  # type: ignore[arg-type]
        df = annotations_to_dataframe(annots, prefer_arrow=False)
        assert pd.isna(df.iloc[0]["start"]) or df.iloc[0]["start"] is None
        assert pd.isna(df.iloc[0]["end"]) or df.iloc[0]["end"] is None
        assert df.iloc[0]["text"] == "bad"

    def test_prefer_arrow_falls_back_when_pyarrow_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If pyarrow is not importable, the helper must still return a frame."""
        import builtins

        real_import = builtins.__import__

        def patched(name: str, *args: object, **kwargs: object):
            if name == "pyarrow":
                raise ImportError("simulated missing pyarrow")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", patched)
        annots = [_StubAnnotation(coords=(0, 1), text="x")]
        df = annotations_to_dataframe(annots, prefer_arrow=True)
        # frame exists even without pyarrow; dtypes may be numpy-backed.
        assert len(df) == 1

    def test_output_preserves_one_row_per_annotation(self) -> None:
        annots = [_StubAnnotation(coords=(i, i + 1), text=str(i)) for i in range(5)]
        df = annotations_to_dataframe(annots, prefer_arrow=False)
        assert len(df) == 5
        assert list(df["text"]) == ["0", "1", "2", "3", "4"]
