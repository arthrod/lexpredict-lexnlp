"""Tests for :mod:`lexnlp.utils.pandas_config`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import pytest

pd = pytest.importorskip("pandas")

from lexnlp.utils.pandas_config import (  # noqa: E402 - after pytest.importorskip
    apply_default_options,
    convert_to_arrow,
    enable_copy_on_write,
    enable_future_string_dtype,
)


@pytest.fixture(autouse=True)
def _reset_pandas_options():
    previous_cow = getattr(pd.options.mode, "copy_on_write", None)
    previous_infer = getattr(pd.options.future, "infer_string", None)
    yield
    try:
        pd.options.mode.copy_on_write = previous_cow
    except Exception:
        pass
    try:
        pd.options.future.infer_string = previous_infer
    except Exception:
        pass


class TestToggles:
    def test_enable_copy_on_write(self) -> None:
        enable_copy_on_write()
        assert pd.options.mode.copy_on_write is True

    def test_warn_mode(self) -> None:
        enable_copy_on_write(warn_mode=True)
        assert pd.options.mode.copy_on_write == "warn"

    def test_enable_future_string(self) -> None:
        enable_future_string_dtype()
        assert pd.options.future.infer_string is True

    def test_apply_default_options(self) -> None:
        result = apply_default_options()
        assert result == {"copy_on_write": True, "future.infer_string": True}
        assert pd.options.mode.copy_on_write is True
        assert pd.options.future.infer_string is True


class TestConvertToArrow:
    def test_without_pyarrow_returns_same_frame(self) -> None:
        frame = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        result = convert_to_arrow(frame)
        # The helper is a no-op if pyarrow is missing, otherwise returns
        # an arrow-backed copy. Either way, it must return a DataFrame.
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ["a", "b"]
