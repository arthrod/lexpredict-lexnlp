__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

import pandas as pd

from lexnlp.utils.pandas_config import read_csv_arrow


class TestReadCsvArrow(TestCase):
    def setUp(self) -> None:
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sample.csv"
        self.path.write_text(
            "alias,name,country\nSTF,Supremo Tribunal Federal,Brazil\nTSE,Tribunal Superior Eleitoral,Brazil\n",
            encoding="utf-8",
        )

    def test_returns_dataframe(self) -> None:
        frame = read_csv_arrow(self.path)
        self.assertIsInstance(frame, pd.DataFrame)

    def test_parses_expected_shape(self) -> None:
        frame = read_csv_arrow(self.path)
        self.assertEqual(frame.shape, (2, 3))
        self.assertEqual(list(frame.columns), ["alias", "name", "country"])

    def test_parses_content(self) -> None:
        frame = read_csv_arrow(self.path)
        self.assertEqual(frame.iloc[0]["alias"], "STF")
        self.assertEqual(frame.iloc[1]["alias"], "TSE")

    def test_accepts_string_path(self) -> None:
        frame = read_csv_arrow(str(self.path))
        self.assertEqual(frame.shape, (2, 3))

    def test_forwards_kwargs_to_read_csv(self) -> None:
        frame = read_csv_arrow(self.path, usecols=["alias", "country"])
        self.assertEqual(list(frame.columns), ["alias", "country"])

    def test_falls_back_when_pyarrow_missing(self) -> None:
        """When pyarrow is unavailable the helper still returns a valid
        DataFrame (using the default pandas backend) and does NOT push a
        ``dtype_backend="pyarrow"`` argument through to ``pandas.read_csv``."""

        # Force the ImportError branch in ``read_csv_arrow`` by hiding
        # ``pyarrow`` from ``sys.modules``. Setting the entry to ``None``
        # makes ``import pyarrow`` raise ``ImportError`` deterministically
        # whether or not the package is installed in the environment.
        captured: dict[str, dict] = {}
        original_read_csv = pd.read_csv

        def spy_read_csv(*args, **kwargs):
            captured["kwargs"] = dict(kwargs)
            return original_read_csv(*args, **kwargs)

        with patch.dict("sys.modules", {"pyarrow": None}):
            with patch("pandas.read_csv", side_effect=spy_read_csv):
                frame = read_csv_arrow(self.path)
        self.assertEqual(frame.shape, (2, 3))
        # The helper must have skipped the pyarrow backend on this path.
        self.assertNotIn("dtype_backend", captured["kwargs"])

    def test_uses_pyarrow_backend_when_available(self) -> None:
        """When pyarrow can be imported the helper forwards
        ``dtype_backend="pyarrow"`` through to ``pandas.read_csv``."""

        pa = pytest_importorskip_pyarrow()
        if pa is None:
            self.skipTest("pyarrow not installed in this environment")
        captured: dict[str, dict] = {}
        original_read_csv = pd.read_csv

        def spy_read_csv(*args, **kwargs):
            captured["kwargs"] = dict(kwargs)
            return original_read_csv(*args, **kwargs)

        with patch("pandas.read_csv", side_effect=spy_read_csv):
            read_csv_arrow(self.path)
        self.assertEqual(captured["kwargs"].get("dtype_backend"), "pyarrow")


def pytest_importorskip_pyarrow():
    """Return the imported pyarrow module if it is installed, else ``None``."""
    try:
        import pyarrow  # noqa: F401 — availability probe only
    except ImportError:
        return None
    return pyarrow
