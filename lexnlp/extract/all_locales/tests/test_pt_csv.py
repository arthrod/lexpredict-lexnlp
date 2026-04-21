"""Tests for the Portuguese court and regulation CSV configuration files.

These CSVs were added in this PR as part of the new ``lexnlp.extract.pt``
module:
- ``lexnlp/config/pt/pt_courts.csv`` — 98 Brazilian court entries
- ``lexnlp/config/pt/pt_regulations.csv`` — 78 regulation trigger entries

Tests verify:
* The files are parseable as CSV.
* Column headers match the expected schema.
* Row counts match documented values.
* All entries have the expected locale/position values.
* Key courts and triggers are present (spot checks).
"""

from __future__ import annotations

import csv
import pathlib

import pytest

# Paths are relative to the repo root
_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent.parent.parent
_PT_COURTS_CSV = _REPO_ROOT / "lexnlp" / "config" / "pt" / "pt_courts.csv"
_PT_REGS_CSV = _REPO_ROOT / "lexnlp" / "config" / "pt" / "pt_regulations.csv"


def _read_csv(path: pathlib.Path) -> list[dict[str, str]]:
    """Read a CSV file and return a list of row dicts."""
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# pt_courts.csv
# ---------------------------------------------------------------------------


class TestPtCourtsCsvExists:
    def test_file_exists(self) -> None:
        assert _PT_COURTS_CSV.exists(), f"Missing: {_PT_COURTS_CSV}"

    def test_file_is_nonempty(self) -> None:
        assert _PT_COURTS_CSV.stat().st_size > 0


class TestPtCourtsCsvSchema:
    """Verify column headers match the documented schema."""

    @pytest.fixture(scope="class")
    def rows(self) -> list[dict[str, str]]:
        return _read_csv(_PT_COURTS_CSV)

    def test_expected_columns_present(self, rows: list[dict[str, str]]) -> None:
        expected_cols = {
            "Term Locale",
            "Term Category",
            "Court ID",
            "Level",
            "Jurisdiction",
            "Court Type",
            "Court Name",
            "Alias",
        }
        assert expected_cols == set(rows[0].keys())

    def test_has_98_data_rows(self, rows: list[dict[str, str]]) -> None:
        assert len(rows) == 98

    def test_all_rows_have_pt_br_locale(self, rows: list[dict[str, str]]) -> None:
        bad = [r for r in rows if r["Term Locale"] != "pt-BR"]
        assert bad == [], f"Unexpected locale in rows: {bad}"

    def test_all_rows_have_brazilian_courts_category(
        self, rows: list[dict[str, str]]
    ) -> None:
        bad = [r for r in rows if r["Term Category"] != "Brazilian Courts"]
        assert bad == [], f"Unexpected category in rows: {bad}"

    def test_all_rows_have_non_empty_court_name(
        self, rows: list[dict[str, str]]
    ) -> None:
        empty = [r for r in rows if not r["Court Name"].strip()]
        assert empty == []

    def test_all_rows_have_non_empty_alias(self, rows: list[dict[str, str]]) -> None:
        empty = [r for r in rows if not r["Alias"].strip()]
        assert empty == []

    def test_court_ids_are_sequential(self, rows: list[dict[str, str]]) -> None:
        ids = [int(r["Court ID"]) for r in rows]
        assert ids == list(range(1, 99))


class TestPtCourtsCsvSpotChecks:
    """Spot-check a sample of known courts."""

    @pytest.fixture(scope="class")
    def alias_to_row(self) -> dict[str, dict[str, str]]:
        rows = _read_csv(_PT_COURTS_CSV)
        return {r["Alias"]: r for r in rows}

    @pytest.mark.parametrize("alias,court_name", [
        ("STF", "Supremo Tribunal Federal"),
        ("STJ", "Superior Tribunal de Justiça"),
        ("TST", "Tribunal Superior do Trabalho"),
        ("TSE", "Tribunal Superior Eleitoral"),
        ("STM", "Superior Tribunal Militar"),
        ("CNJ", "Conselho Nacional de Justiça"),
        ("TRF1", "Tribunal Regional Federal da 1ª Região"),
        ("TRF6", "Tribunal Regional Federal da 6ª Região"),
        ("TRT1", "Tribunal Regional do Trabalho da 1ª Região"),
        ("TJSP", "Tribunal de Justiça do Estado de São Paulo"),
        ("TJRJ", "Tribunal de Justiça do Estado do Rio de Janeiro"),
        ("TJMG", "Tribunal de Justiça do Estado de Minas Gerais"),
        ("TNU", "Turma Nacional de Uniformização dos Juizados Especiais Federais"),
        ("TRU", "Turma Regional de Uniformização dos Juizados Especiais"),
    ])
    def test_known_court_present(
        self, alias: str, court_name: str, alias_to_row: dict[str, dict[str, str]]
    ) -> None:
        assert alias in alias_to_row, f"Alias '{alias}' not found"
        assert alias_to_row[alias]["Court Name"] == court_name

    def test_all_27_tjs_present(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        tj_aliases = [a for a in alias_to_row if a.startswith("TJ") and len(a) <= 6]
        # 27 TJs + TJDFT + 3 TJM state military + one TJDFT anomaly = up to 31
        # but at minimum 27 standard TJs
        assert len(tj_aliases) >= 27

    def test_all_tre_aliases_present(
        self, alias_to_row: dict[str, dict[str, str]]
    ) -> None:
        tre_aliases = [a for a in alias_to_row if a.startswith("TRE-")]
        assert len(tre_aliases) == 27

    def test_stf_level_is_supremo(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        assert alias_to_row["STF"]["Level"] == "Supremo"

    def test_stj_level_is_superior(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        assert alias_to_row["STJ"]["Level"] == "Superior"

    def test_tjsp_level_is_estadual(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        assert alias_to_row["TJSP"]["Level"] == "Estadual"

    def test_tjsp_jurisdiction_is_sao_paulo(
        self, alias_to_row: dict[str, dict[str, str]]
    ) -> None:
        assert alias_to_row["TJSP"]["Jurisdiction"] == "São Paulo"

    def test_no_duplicate_aliases(
        self, alias_to_row: dict[str, dict[str, str]]
    ) -> None:
        rows = _read_csv(_PT_COURTS_CSV)
        aliases = [r["Alias"] for r in rows]
        assert len(aliases) == len(set(aliases)), "Duplicate aliases found"


# ---------------------------------------------------------------------------
# pt_regulations.csv
# ---------------------------------------------------------------------------


class TestPtRegsCsvExists:
    def test_file_exists(self) -> None:
        assert _PT_REGS_CSV.exists(), f"Missing: {_PT_REGS_CSV}"

    def test_file_is_nonempty(self) -> None:
        assert _PT_REGS_CSV.stat().st_size > 0


class TestPtRegsCsvSchema:
    """Verify column headers and basic constraints."""

    @pytest.fixture(scope="class")
    def rows(self) -> list[dict[str, str]]:
        return _read_csv(_PT_REGS_CSV)

    def test_expected_columns_present(self, rows: list[dict[str, str]]) -> None:
        assert set(rows[0].keys()) == {"trigger", "position"}

    def test_has_78_data_rows(self, rows: list[dict[str, str]]) -> None:
        assert len(rows) == 78

    def test_all_positions_are_start(self, rows: list[dict[str, str]]) -> None:
        bad = [r for r in rows if r["position"] != "start"]
        assert bad == [], f"Non-'start' position rows: {bad}"

    def test_all_triggers_non_empty(self, rows: list[dict[str, str]]) -> None:
        empty = [r for r in rows if not r["trigger"].strip()]
        assert empty == []

    def test_no_duplicate_triggers(self, rows: list[dict[str, str]]) -> None:
        triggers = [r["trigger"] for r in rows]
        assert len(triggers) == len(set(triggers)), "Duplicate triggers found"


class TestPtRegsCsvSpotChecks:
    """Spot-check key regulation triggers."""

    @pytest.fixture(scope="class")
    def triggers(self) -> set[str]:
        rows = _read_csv(_PT_REGS_CSV)
        return {r["trigger"] for r in rows}

    @pytest.mark.parametrize("trigger", [
        "lei",
        "decreto",
        "medida provisória",
        "resolução",
        "portaria",
        "instrução normativa",
        "emenda constitucional",
        "constituição federal",
        "código civil",
        "código penal",
        "lei complementar",
        "decreto-lei",
        "câmara dos deputados",
        "senado federal",
        "ministério público",
        "banco central",
        "receita federal",
        "tribunal de contas",
    ])
    def test_known_trigger_present(self, trigger: str, triggers: set[str]) -> None:
        assert trigger in triggers, f"Trigger '{trigger}' not found"

    def test_triggers_are_lowercase(self, triggers: set[str]) -> None:
        """All trigger strings must be lowercase (for case-insensitive matching)."""
        for t in triggers:
            assert t == t.lower(), f"Trigger not lowercase: '{t}'"