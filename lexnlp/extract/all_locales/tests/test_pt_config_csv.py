"""Tests for the Portuguese configuration CSV files.

Verifies structural integrity of the new CSV files added in this PR:
- lexnlp/config/pt/pt_courts.csv   (98 data rows + 1 header = 99 lines)
- lexnlp/config/pt/pt_regulations.csv (78 data rows + 1 header = 79 lines)

These tests do not import the extraction stack; they only parse the CSV
files as plain text to verify well-formedness, required columns, expected
row counts, and key invariants documented in the PR description.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import csv
import pathlib
from typing import Any

import pytest


def _find_config_dir() -> pathlib.Path:
    """
    Locate the repository's config/pt directory relative to this test file.
    
    Returns:
        pathlib.Path: Path to the `config/pt` directory.
    
    Raises:
        FileNotFoundError: If `config/pt` cannot be found relative to this file.
    """
    here = pathlib.Path(__file__).resolve()
    # lexnlp/extract/all_locales/tests/test_pt_config_csv.py → go up 4 levels
    # to reach the lexnlp/ package root, then descend to config/pt/
    candidate = here.parent.parent.parent.parent / "config" / "pt"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Cannot locate config/pt/ relative to {here}")


_CONFIG_PT = _find_config_dir()
_COURTS_CSV = _CONFIG_PT / "pt_courts.csv"
_REGULATIONS_CSV = _CONFIG_PT / "pt_regulations.csv"


def _read_csv(path: pathlib.Path) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Read a UTF-8 CSV file and return its header field names and parsed rows.
    
    Parameters:
        path (pathlib.Path): Path to the CSV file to read.
    
    Returns:
        tuple[list[str], list[dict[str, Any]]]: A pair where the first element is the list of header field names (an empty list if the CSV has no header) and the second element is the list of rows as dictionaries mapping column names to values.
    """
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    return fieldnames, rows


# ---------------------------------------------------------------------------
# pt_courts.csv structural tests
# ---------------------------------------------------------------------------


class TestPtCourtsCSV:
    @pytest.fixture(scope="class")
    def courts_data(self):
        """
        Provide parsed field names and rows from the Portuguese courts CSV used by the tests.
        
        Returns:
            tuple[list[str], list[dict[str, str]]]: `fieldnames` is a list of column headers (or an empty list if none),
            `rows` is a list of dictionaries mapping column names to string values for each data row.
        """
        fieldnames, rows = _read_csv(_COURTS_CSV)
        return fieldnames, rows

    def test_file_exists(self) -> None:
        """
        Assert that the Portuguese courts CSV file exists at the expected config path.
        
        If the file is missing, the test fails with an AssertionError that includes the resolved path.
        """
        assert _COURTS_CSV.exists(), f"File not found: {_COURTS_CSV}"

    def test_has_98_data_rows(self, courts_data) -> None:
        """
        Assert the Portuguese courts CSV contains exactly 98 data rows.
        
        Raises:
            AssertionError: if the parsed CSV row count is not 98.
        """
        _, rows = courts_data
        assert len(rows) == 98

    def test_required_columns_present(self, courts_data) -> None:
        fieldnames, _ = courts_data
        required = {"Term Locale", "Term Category", "Court ID", "Level",
                    "Jurisdiction", "Court Type", "Court Name", "Alias"}
        assert required.issubset(set(fieldnames))

    def test_all_rows_have_term_locale_pt_br(self, courts_data) -> None:
        _, rows = courts_data
        for row in rows:
            assert row["Term Locale"] == "pt-BR", (
                f"Row {row['Court ID']} has unexpected locale: {row['Term Locale']!r}"
            )

    def test_all_rows_have_term_category_brazilian_courts(self, courts_data) -> None:
        _, rows = courts_data
        for row in rows:
            assert row["Term Category"] == "Brazilian Courts", (
                f"Row {row['Court ID']} has unexpected category: {row['Term Category']!r}"
            )

    def test_court_ids_are_sequential_1_to_98(self, courts_data) -> None:
        """
        Asserts that the Court ID values in the courts CSV form the consecutive sequence from 1 through 98.
        
        Parameters:
            courts_data (tuple[list[str], list[dict[str, Any]]]): Parsed CSV data as (fieldnames, rows) where each row is a dict containing a "Court ID" key.
        """
        _, rows = courts_data
        ids = sorted(int(row["Court ID"]) for row in rows)
        assert ids == list(range(1, 99))

    def test_all_rows_have_non_empty_court_name(self, courts_data) -> None:
        """
        Assert every parsed court row has a non-empty 'Court Name' field.
        
        Parameters:
            courts_data (tuple[list[str], list[dict]]): (fieldnames, rows) returned by the CSV reader; `rows` is a list of row dicts from pt_courts.csv. On failure the assertion message includes the offending row's `Court ID`.
        """
        _, rows = courts_data
        for row in rows:
            assert row["Court Name"].strip(), (
                f"Row {row['Court ID']} has empty Court Name"
            )

    def test_all_rows_have_non_empty_alias(self, courts_data) -> None:
        """
        Assert every row in the courts CSV has a non-empty Alias.
        
        Raises an assertion failure that includes the Court ID when a row's `Alias` is empty or only whitespace.
        """
        _, rows = courts_data
        for row in rows:
            assert row["Alias"].strip(), (
                f"Row {row['Court ID']} has empty Alias"
            )

    def test_stf_is_row_1(self, courts_data) -> None:
        """
        Assert that the court with Court ID "1" has alias "STF" and its Court Name contains "Supremo Tribunal Federal".
        
        Verifies a row with "Court ID" == "1" exists, that its "Alias" equals "STF", and that "Supremo Tribunal Federal" appears in its "Court Name".
        """
        _, rows = courts_data
        row1 = next(r for r in rows if r["Court ID"] == "1")
        assert row1["Alias"] == "STF"
        assert "Supremo Tribunal Federal" in row1["Court Name"]

    def test_stj_is_row_2(self, courts_data) -> None:
        """
        Asserts that the CSV row with Court ID "2" uses the alias "STJ".
        """
        _, rows = courts_data
        row2 = next(r for r in rows if r["Court ID"] == "2")
        assert row2["Alias"] == "STJ"

    def test_tst_is_row_3(self, courts_data) -> None:
        _, rows = courts_data
        row3 = next(r for r in rows if r["Court ID"] == "3")
        assert row3["Alias"] == "TST"

    def test_tjsp_present_as_alias(self, courts_data) -> None:
        """
        Asserts that the court alias "TJSP" appears in the CSV's Alias column.
        """
        _, rows = courts_data
        aliases = {row["Alias"] for row in rows}
        assert "TJSP" in aliases

    def test_all_trf_aliases_present(self, courts_data) -> None:
        """
        Assert that the PT courts CSV contains the aliases "TRF1" through "TRF6".
        
        Each of the aliases TRF1, TRF2, TRF3, TRF4, TRF5, and TRF6 must appear in the file's Alias column.
        """
        _, rows = courts_data
        aliases = {row["Alias"] for row in rows}
        for i in range(1, 7):
            assert f"TRF{i}" in aliases, f"TRF{i} missing from pt_courts.csv"

    def test_aliases_are_unique(self, courts_data) -> None:
        _, rows = courts_data
        aliases = [row["Alias"] for row in rows]
        assert len(aliases) == len(set(aliases)), "Duplicate aliases found in pt_courts.csv"

    def test_court_ids_are_unique(self, courts_data) -> None:
        _, rows = courts_data
        ids = [row["Court ID"] for row in rows]
        assert len(ids) == len(set(ids)), "Duplicate court IDs in pt_courts.csv"

    def test_supremo_level_row_exists(self, courts_data) -> None:
        _, rows = courts_data
        levels = {row["Level"] for row in rows}
        assert "Supremo" in levels

    def test_cnj_present(self, courts_data) -> None:
        """
        Asserts that the courts CSV contains the alias "CNJ".
        
        Parameters:
            courts_data (tuple[list[str], list[dict[str, Any]]]): Fixture returning `(fieldnames, rows)` parsed from the courts CSV, where `rows` is a list of row dictionaries.
        """
        _, rows = courts_data
        aliases = {row["Alias"] for row in rows}
        assert "CNJ" in aliases

    def test_tnu_present(self, courts_data) -> None:
        """
        Asserts that the courts configuration includes an alias 'TNU'.
        """
        _, rows = courts_data
        aliases = {row["Alias"] for row in rows}
        assert "TNU" in aliases

    def test_federal_jurisdiction_rows_present(self, courts_data) -> None:
        """
        Asserts that at least one row in the courts CSV has the "Jurisdiction" field equal to "Federal".
        
        If no row contains "Federal" in its "Jurisdiction" column, the test will fail.
        """
        _, rows = courts_data
        jurisdictions = {row["Jurisdiction"] for row in rows}
        assert "Federal" in jurisdictions

    def test_estadual_level_rows_present(self, courts_data) -> None:
        _, rows = courts_data
        levels = {row["Level"] for row in rows}
        assert "Estadual" in levels

    def test_regional_level_rows_present(self, courts_data) -> None:
        """
        Verify the courts CSV contains at least one row with Level "Regional".
        
        Checks the parsed court rows' Level values and asserts that "Regional" is present.
        """
        _, rows = courts_data
        levels = {row["Level"] for row in rows}
        assert "Regional" in levels


# ---------------------------------------------------------------------------
# pt_regulations.csv structural tests
# ---------------------------------------------------------------------------


class TestPtRegulationsCSV:
    @pytest.fixture(scope="class")
    def regs_data(self):
        """
        Load and return the parsed CSV fieldnames and rows from the Portuguese regulations config.
        
        Returns:
            (fieldnames, rows) (tuple[list[str], list[dict[str, Any]]]): `fieldnames` is the list of column names from pt_regulations.csv; `rows` is a list of dictionaries representing each CSV row.
        """
        fieldnames, rows = _read_csv(_REGULATIONS_CSV)
        return fieldnames, rows

    def test_file_exists(self) -> None:
        assert _REGULATIONS_CSV.exists(), f"File not found: {_REGULATIONS_CSV}"

    def test_has_78_data_rows(self, regs_data) -> None:
        _, rows = regs_data
        assert len(rows) == 78

    def test_required_columns_present(self, regs_data) -> None:
        """
        Asserts the regulations CSV includes the required columns "trigger" and "position".
        
        Parameters:
            regs_data (tuple[list[str], list[dict]]): Parsed CSV contents as (fieldnames, rows).
        """
        fieldnames, _ = regs_data
        assert "trigger" in fieldnames
        assert "position" in fieldnames

    def test_all_rows_have_non_empty_trigger(self, regs_data) -> None:
        _, rows = regs_data
        for row in rows:
            assert row["trigger"].strip(), f"Empty trigger found: {row!r}"

    def test_all_positions_are_start(self, regs_data) -> None:
        """
        Verify that every regulation row has its `position` set to "start".
        
        This test fails if any row's `position` value is not exactly "start".
        """
        _, rows = regs_data
        for row in rows:
            assert row["position"] == "start", (
                f"Unexpected position {row['position']!r} for trigger {row['trigger']!r}"
            )

    def test_triggers_are_unique(self, regs_data) -> None:
        """
        Verify that every 'trigger' value in the Portuguese regulations CSV is unique.
        """
        _, rows = regs_data
        triggers = [row["trigger"] for row in rows]
        assert len(triggers) == len(set(triggers)), "Duplicate triggers in pt_regulations.csv"

    def test_lei_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "lei" in triggers

    def test_decreto_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "decreto" in triggers

    def test_constituicao_federal_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "constituição federal" in triggers

    def test_medida_provisoria_trigger_present(self, regs_data) -> None:
        """
        Asserts that the regulations CSV contains a trigger equal to "medida provisória".
        """
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "medida provisória" in triggers

    def test_instrucao_normativa_trigger_present(self, regs_data) -> None:
        """
        Ensure the regulations CSV contains the trigger "instrução normativa".
        
        Checks that one of the `trigger` values in the provided regulations data is exactly "instrução normativa".
        """
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "instrução normativa" in triggers

    def test_all_triggers_are_lowercase(self, regs_data) -> None:
        """
        Ensure every regulation trigger string is lowercase.
        
        Asserts that for each row in the provided regulations data, the value of `trigger` equals its lowercase form; if not, the assertion fails showing the offending trigger.
        """
        _, rows = regs_data
        for row in rows:
            trigger = row["trigger"]
            # Triggers should be lowercase (may include accented chars and spaces)
            assert trigger == trigger.lower(), (
                f"Trigger not lowercase: {trigger!r}"
            )

    def test_senado_federal_trigger_present(self, regs_data) -> None:
        """
        Verify the regulations CSV contains the trigger "senado federal".
        
        Raises:
            AssertionError: if "senado federal" is not present among the `trigger` values.
        """
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "senado federal" in triggers

    def test_ministerio_da_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "ministério da" in triggers

    def test_codigo_civil_trigger_present(self, regs_data) -> None:
        """
        Asserts that the regulations CSV includes the trigger "código civil".
        """
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "código civil" in triggers

    def test_exact_column_count(self, regs_data) -> None:
        """
        Asserts the regulations CSV has exactly two columns.
        
        This test verifies that the parsed `fieldnames` list for `pt_regulations.csv` contains exactly 2 entries.
        """
        fieldnames, _ = regs_data
        assert len(fieldnames) == 2