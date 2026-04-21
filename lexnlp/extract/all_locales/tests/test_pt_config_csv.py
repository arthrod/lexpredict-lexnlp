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
    """Locate the lexnlp/config/pt/ directory relative to this test file."""
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
    """Return (fieldnames, rows) from the given CSV path."""
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
        fieldnames, rows = _read_csv(_COURTS_CSV)
        return fieldnames, rows

    def test_file_exists(self) -> None:
        assert _COURTS_CSV.exists(), f"File not found: {_COURTS_CSV}"

    def test_has_98_data_rows(self, courts_data) -> None:
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
        _, rows = courts_data
        ids = sorted(int(row["Court ID"]) for row in rows)
        assert ids == list(range(1, 99))

    def test_all_rows_have_non_empty_court_name(self, courts_data) -> None:
        _, rows = courts_data
        for row in rows:
            assert row["Court Name"].strip(), (
                f"Row {row['Court ID']} has empty Court Name"
            )

    def test_all_rows_have_non_empty_alias(self, courts_data) -> None:
        _, rows = courts_data
        for row in rows:
            assert row["Alias"].strip(), (
                f"Row {row['Court ID']} has empty Alias"
            )

    def test_stf_is_row_1(self, courts_data) -> None:
        _, rows = courts_data
        row1 = next(r for r in rows if r["Court ID"] == "1")
        assert row1["Alias"] == "STF"
        assert "Supremo Tribunal Federal" in row1["Court Name"]

    def test_stj_is_row_2(self, courts_data) -> None:
        _, rows = courts_data
        row2 = next(r for r in rows if r["Court ID"] == "2")
        assert row2["Alias"] == "STJ"

    def test_tst_is_row_3(self, courts_data) -> None:
        _, rows = courts_data
        row3 = next(r for r in rows if r["Court ID"] == "3")
        assert row3["Alias"] == "TST"

    def test_tjsp_present_as_alias(self, courts_data) -> None:
        _, rows = courts_data
        aliases = {row["Alias"] for row in rows}
        assert "TJSP" in aliases

    def test_all_trf_aliases_present(self, courts_data) -> None:
        """TRF1 through TRF6 must all be in the catalogue."""
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
        _, rows = courts_data
        aliases = {row["Alias"] for row in rows}
        assert "CNJ" in aliases

    def test_tnu_present(self, courts_data) -> None:
        _, rows = courts_data
        aliases = {row["Alias"] for row in rows}
        assert "TNU" in aliases

    def test_federal_jurisdiction_rows_present(self, courts_data) -> None:
        _, rows = courts_data
        jurisdictions = {row["Jurisdiction"] for row in rows}
        assert "Federal" in jurisdictions

    def test_estadual_level_rows_present(self, courts_data) -> None:
        _, rows = courts_data
        levels = {row["Level"] for row in rows}
        assert "Estadual" in levels

    def test_regional_level_rows_present(self, courts_data) -> None:
        _, rows = courts_data
        levels = {row["Level"] for row in rows}
        assert "Regional" in levels


# ---------------------------------------------------------------------------
# pt_regulations.csv structural tests
# ---------------------------------------------------------------------------


class TestPtRegulationsCSV:
    @pytest.fixture(scope="class")
    def regs_data(self):
        fieldnames, rows = _read_csv(_REGULATIONS_CSV)
        return fieldnames, rows

    def test_file_exists(self) -> None:
        assert _REGULATIONS_CSV.exists(), f"File not found: {_REGULATIONS_CSV}"

    def test_has_78_data_rows(self, regs_data) -> None:
        _, rows = regs_data
        assert len(rows) == 78

    def test_required_columns_present(self, regs_data) -> None:
        fieldnames, _ = regs_data
        assert "trigger" in fieldnames
        assert "position" in fieldnames

    def test_all_rows_have_non_empty_trigger(self, regs_data) -> None:
        _, rows = regs_data
        for row in rows:
            assert row["trigger"].strip(), f"Empty trigger found: {row!r}"

    def test_all_positions_are_start(self, regs_data) -> None:
        _, rows = regs_data
        for row in rows:
            assert row["position"] == "start", (
                f"Unexpected position {row['position']!r} for trigger {row['trigger']!r}"
            )

    def test_triggers_are_unique(self, regs_data) -> None:
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
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "medida provisória" in triggers

    def test_instrucao_normativa_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "instrução normativa" in triggers

    def test_all_triggers_are_lowercase(self, regs_data) -> None:
        _, rows = regs_data
        for row in rows:
            trigger = row["trigger"]
            # Triggers should be lowercase (may include accented chars and spaces)
            assert trigger == trigger.lower(), (
                f"Trigger not lowercase: {trigger!r}"
            )

    def test_senado_federal_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "senado federal" in triggers

    def test_ministerio_da_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "ministério da" in triggers

    def test_codigo_civil_trigger_present(self, regs_data) -> None:
        _, rows = regs_data
        triggers = {row["trigger"] for row in rows}
        assert "código civil" in triggers

    def test_exact_column_count(self, regs_data) -> None:
        fieldnames, _ = regs_data
        assert len(fieldnames) == 2