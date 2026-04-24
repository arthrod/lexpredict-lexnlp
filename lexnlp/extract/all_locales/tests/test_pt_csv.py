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
    """
    Parse a CSV file into a list of dictionaries keyed by header names.

    Parameters:
        path (pathlib.Path): Path to the CSV file to read.

    Returns:
        list[dict[str, str]]: List of rows where each dict maps a column header to its string value.
    """
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# pt_courts.csv
# ---------------------------------------------------------------------------


class TestPtCourtsCsvExists:
    def test_file_exists(self) -> None:
        """
        Verify that the Portuguese courts CSV file exists at the expected repository path.

        Raises:
            AssertionError: If the file does not exist; the assertion message includes the expected file path.
        """
        assert _PT_COURTS_CSV.exists(), f"Missing: {_PT_COURTS_CSV}"

    def test_file_is_nonempty(self) -> None:
        """
        Verify that the pt_courts.csv file is not empty.
        """
        assert _PT_COURTS_CSV.stat().st_size > 0


class TestPtCourtsCsvSchema:
    """Verify column headers match the documented schema."""

    @pytest.fixture(scope="class")
    def rows(self) -> list[dict[str, str]]:
        """
        Load all rows from the Portuguese courts CSV.

        Returns:
            list[dict[str, str]]: Row dictionaries keyed by CSV column names, one entry per CSV row.
        """
        return _read_csv(_PT_COURTS_CSV)

    def test_expected_columns_present(self, rows: list[dict[str, str]]) -> None:
        """
        Validate that the parsed CSV rows use the exact expected header columns for pt_courts.csv.

        Expects the header set to be exactly: "Term Locale", "Term Category", "Court ID", "Level", "Jurisdiction", "Court Type", "Court Name", and "Alias".

        Parameters:
            rows (list[dict[str, str]]): Parsed CSV rows as produced by csv.DictReader; the first row's keys are checked.
        """
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
        """
        Assert the parsed CSV contains exactly 98 data rows.

        Parameters:
            rows (list[dict[str, str]]): Rows produced by csv.DictReader for the PT courts CSV.
        """
        assert len(rows) == 98

    def test_all_rows_have_pt_br_locale(self, rows: list[dict[str, str]]) -> None:
        bad = [r for r in rows if r["Term Locale"] != "pt-BR"]
        assert bad == [], f"Unexpected locale in rows: {bad}"

    def test_all_rows_have_brazilian_courts_category(self, rows: list[dict[str, str]]) -> None:
        """
        Verify every row in the pt_courts CSV has "Term Category" equal to "Brazilian Courts".
        """
        bad = [r for r in rows if r["Term Category"] != "Brazilian Courts"]
        assert bad == [], f"Unexpected category in rows: {bad}"

    def test_all_rows_have_non_empty_court_name(self, rows: list[dict[str, str]]) -> None:
        """
        Ensure every row in the parsed pt_courts.csv has a non-empty 'Court Name' field.

        Parameters:
            rows (list[dict[str, str]]): Parsed CSV rows keyed by column names.
        """
        empty = [r for r in rows if not r["Court Name"].strip()]
        assert empty == []

    def test_all_rows_have_non_empty_alias(self, rows: list[dict[str, str]]) -> None:
        """
        Verify every row has a non-empty 'Alias' value.

        Asserts that no row's "Alias" field is empty or consists only of whitespace after stripping.
        """
        empty = [r for r in rows if not r["Alias"].strip()]
        assert empty == []

    def test_court_ids_are_sequential(self, rows: list[dict[str, str]]) -> None:
        ids = [int(r["Court ID"]) for r in rows]
        assert ids == list(range(1, 99))


class TestPtCourtsCsvSpotChecks:
    """Spot-check a sample of known courts."""

    @pytest.fixture(scope="class")
    def alias_to_row(self) -> dict[str, dict[str, str]]:
        """
        Create a mapping from each court alias to its CSV row dictionary.

        Returns:
            dict[str, dict[str, str]]: Mapping where each key is an `Alias` and each value is the corresponding row dictionary. Row dictionaries include the keys: "Term Locale", "Term Category", "Court ID", "Level", "Jurisdiction", "Court Type", "Court Name", and "Alias".
        """
        rows = _read_csv(_PT_COURTS_CSV)
        return {r["Alias"]: r for r in rows}

    @pytest.mark.parametrize(
        "alias,court_name",
        [
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
        ],
    )
    def test_known_court_present(self, alias: str, court_name: str, alias_to_row: dict[str, dict[str, str]]) -> None:
        """
        Check that a given court alias exists in the CSV mapping and its "Court Name" equals the expected value.

        Parameters:
            alias (str): The court alias to look up.
            court_name (str): The expected exact "Court Name" for the alias.
            alias_to_row (dict[str, dict[str, str]]): Mapping from alias to row dictionaries parsed from the CSV.
        """
        assert alias in alias_to_row, f"Alias '{alias}' not found"
        assert alias_to_row[alias]["Court Name"] == court_name

    def test_all_27_tjs_present(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        """
        Verify the CSV contains at least 27 state court aliases that start with "TJ".

        Checks aliases in the provided mapping that begin with "TJ" and have length <= 6, and asserts there are at least 27 such aliases.

        Parameters:
            alias_to_row (dict[str, dict[str, str]]): Mapping from alias to the corresponding CSV row dictionary.
        """
        tj_aliases = [a for a in alias_to_row if a.startswith("TJ") and len(a) <= 6]
        # 27 TJs + TJDFT + 3 TJM state military + one TJDFT anomaly = up to 31
        # but at minimum 27 standard TJs
        assert len(tj_aliases) >= 27

    def test_all_tre_aliases_present(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        """
        Verify there are exactly 27 aliases that start with "TRE-".

        Parameters:
            alias_to_row (dict[str, dict[str, str]]): Mapping from alias to the CSV row dictionary for that alias.
        """
        tre_aliases = [a for a in alias_to_row if a.startswith("TRE-")]
        assert len(tre_aliases) == 27

    def test_stf_level_is_supremo(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        """
        Verify that the 'STF' court entry has its "Level" field set to "Supremo".

        Parameters:
            alias_to_row (dict[str, dict[str, str]]): Mapping from court alias to the CSV row dictionary for that court; each row contains fields such as "Level", "Court Name", and "Alias".
        """
        assert alias_to_row["STF"]["Level"] == "Supremo"

    def test_stj_level_is_superior(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        """
        Verify the CSV entry for alias "STJ" has its "Level" field equal to "Superior".

        Parameters:
            alias_to_row (dict[str, dict[str, str]]): Mapping from court alias to the parsed CSV row dictionary for that alias.
        """
        assert alias_to_row["STJ"]["Level"] == "Superior"

    def test_tjsp_level_is_estadual(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        assert alias_to_row["TJSP"]["Level"] == "Estadual"

    def test_tjsp_jurisdiction_is_sao_paulo(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        """
        Check that the 'TJSP' alias has jurisdiction 'São Paulo'.

        Parameters:
            alias_to_row (dict[str, dict[str, str]]): Mapping from court alias to the parsed CSV row dictionary.
        """
        assert alias_to_row["TJSP"]["Jurisdiction"] == "São Paulo"

    def test_no_duplicate_aliases(self, alias_to_row: dict[str, dict[str, str]]) -> None:
        """
        Verify that the pt_courts CSV contains no duplicate values in the "Alias" column.

        Parameters:
            alias_to_row (dict[str, dict[str, str]]): Fixture mapping each alias to its parsed CSV row.
        """
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
        """
        Verify the Portuguese regulations CSV file is not empty.
        """
        assert _PT_REGS_CSV.stat().st_size > 0


class TestPtRegsCsvSchema:
    """Verify column headers and basic constraints."""

    @pytest.fixture(scope="class")
    def rows(self) -> list[dict[str, str]]:
        """
        Load rows from the Portuguese regulations CSV as a list of dictionaries.

        Returns:
            list[dict[str, str]]: Row dictionaries from pt_regulations.csv mapping each column header to its string value.
        """
        return _read_csv(_PT_REGS_CSV)

    def test_expected_columns_present(self, rows: list[dict[str, str]]) -> None:
        """
        Assert that the pt_regulations.csv header contains exactly the columns "trigger" and "position".

        Parameters:
            rows (list[dict[str, str]]): Parsed CSV rows from pt_regulations.csv (each dict keyed by header names).
        """
        assert set(rows[0].keys()) == {"trigger", "position"}

    def test_has_78_data_rows(self, rows: list[dict[str, str]]) -> None:
        """
        Verify the list contains exactly 78 CSV data rows.

        Parameters:
            rows (list[dict[str, str]]): Parsed CSV rows from the regulations CSV file.
        """
        assert len(rows) == 78

    def test_all_positions_are_start(self, rows: list[dict[str, str]]) -> None:
        """
        Check that every row's `position` field equals "start".

        Parameters:
            rows (list[dict[str, str]]): Parsed rows from pt_regulations.csv, each row as a dict keyed by column name.
        """
        bad = [r for r in rows if r["position"] != "start"]
        assert bad == [], f"Non-'start' position rows: {bad}"

    def test_all_triggers_non_empty(self, rows: list[dict[str, str]]) -> None:
        """
        Ensure every row's "trigger" field contains a non-empty string after trimming surrounding whitespace.

        Parameters:
            rows (list[dict[str, str]]): Parsed CSV rows (dicts keyed by column names) where each row is expected to include a "trigger" key.
        """
        empty = [r for r in rows if not r["trigger"].strip()]
        assert empty == []

    def test_no_duplicate_triggers(self, rows: list[dict[str, str]]) -> None:
        """
        Assert that no two rows have the same `trigger` value.

        Parameters:
            rows (list[dict[str, str]]): CSV rows where each dict contains a `"trigger"` key.
        """
        triggers = [r["trigger"] for r in rows]
        assert len(triggers) == len(set(triggers)), "Duplicate triggers found"


class TestPtRegsCsvSpotChecks:
    """Spot-check key regulation triggers."""

    @pytest.fixture(scope="class")
    def triggers(self) -> set[str]:
        """
        Collect the trigger strings defined in the Portuguese regulations CSV.

        Reads the configured pt_regulations.csv and returns the set of all values from the `trigger` column.

        Returns:
            triggers (set[str]): Set of trigger strings present in the CSV.
        """
        rows = _read_csv(_PT_REGS_CSV)
        return {r["trigger"] for r in rows}

    @pytest.mark.parametrize(
        "trigger",
        [
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
        ],
    )
    def test_known_trigger_present(self, trigger: str, triggers: set[str]) -> None:
        """
        Asserts that a specific regulation trigger string is present in the provided set of triggers.

        Parameters:
            trigger (str): The expected trigger string to check for.
            triggers (set[str]): Set of trigger strings extracted from the CSV.
        """
        assert trigger in triggers, f"Trigger '{trigger}' not found"

    def test_triggers_are_lowercase(self, triggers: set[str]) -> None:
        """
        Ensure every trigger string is lowercase.

        Parameters:
            triggers (set[str]): Set of trigger strings to validate.
        """
        for t in triggers:
            assert t == t.lower(), f"Trigger not lowercase: '{t}'"
