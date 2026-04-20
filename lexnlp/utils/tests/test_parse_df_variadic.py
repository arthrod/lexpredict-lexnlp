"""Tests for the ``tuple[str, ...]`` annotation fix in ``parse_df``.

PR #14 review flagged ``parse_columns: list[str] | tuple[str]`` as a 1-item
tuple type hint. The fix uses a variadic ``tuple[str, ...]``. The test
verifies both ``list`` and arbitrary-length tuples are accepted at runtime
by constructing a ``DataframeEntityParser`` and checking that the
``parse_columns`` attribute survives intact.
"""

from __future__ import annotations

import pandas as pd

from lexnlp.utils.parse_df import DataframeEntityParser


def _dummy_df() -> pd.DataFrame:
    """
    Construct a pandas DataFrame with three sample columns used by tests.
    
    Returns:
        pd.DataFrame: DataFrame with columns:
            - "Kurztitel": ["BGB", "StGB", "ZPO"]
            - "Titel": ["Bürgerliches Gesetzbuch", "Strafgesetzbuch", "Zivilprozessordnung"]
            - "Abkürzung": ["BGB", "StGB", "ZPO"]
    """
    return pd.DataFrame(
        {
            "Kurztitel": ["BGB", "StGB", "ZPO"],
            "Titel": [
                "Bürgerliches Gesetzbuch",
                "Strafgesetzbuch",
                "Zivilprozessordnung",
            ],
            "Abkürzung": ["BGB", "StGB", "ZPO"],
        }
    )


class TestParseColumnsTypes:
    def test_accepts_list(self) -> None:
        parser = DataframeEntityParser(
            dataframe=_dummy_df(),
            parse_columns=["Kurztitel", "Titel"],
        )
        assert list(parser.parse_columns) == ["Kurztitel", "Titel"]

    def test_accepts_two_element_tuple(self) -> None:
        """
        Verifies that DataframeEntityParser accepts a two-element tuple for `parse_columns` and preserves it.
        
        Asserts that `parser.parse_columns == ("Kurztitel", "Titel")`.
        """
        parser = DataframeEntityParser(
            dataframe=_dummy_df(),
            parse_columns=("Kurztitel", "Titel"),
        )
        assert parser.parse_columns == ("Kurztitel", "Titel")

    def test_accepts_three_element_tuple(self) -> None:
        parser = DataframeEntityParser(
            dataframe=_dummy_df(),
            parse_columns=("Kurztitel", "Titel", "Abkürzung"),
        )
        assert len(parser.parse_columns) == 3

    def test_single_column_tuple(self) -> None:
        parser = DataframeEntityParser(
            dataframe=_dummy_df(),
            parse_columns=("Titel",),
        )
        assert parser.parse_columns == ("Titel",)
