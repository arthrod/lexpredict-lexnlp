__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from pathlib import Path
from unittest import TestCase

import pandas as pd

from lexnlp.utils.pandas_config import read_csv_arrow


class TestReadCsvArrow(TestCase):
    def setUp(self) -> None:
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sample.csv"
        self.path.write_text(
            "alias,name,country\nSTF,Supremo Tribunal Federal,Brazil\n"
            "TSE,Tribunal Superior Eleitoral,Brazil\n",
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
        DataFrame (using the default pandas backend)."""
        frame = read_csv_arrow(self.path)
        self.assertEqual(frame.shape, (2, 3))
