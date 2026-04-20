"""Tests for scripts/contract_type_quality_gate.py.

Covers changes introduced in the PR:
  - parse_args: --max-accuracy-topn-regression and --max-accuracy-top3-regression
    argument order / dest swap (both map to max_accuracy_topn_regression).
  - score_pipeline: zip(..., strict=True) raises ValueError on length mismatch.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Make the scripts package importable.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import contract_type_quality_gate  # noqa: E402  # required: import follows sys.path insertion for test-only script module resolution

# ---------------------------------------------------------------------------
# parse_args – argument mapping
# ---------------------------------------------------------------------------


class TestParseArgs:
    """Verify that both CLI argument names map to max_accuracy_topn_regression."""

    def test_max_accuracy_topn_regression_flag(self) -> None:
        args = contract_type_quality_gate.parse_args(
            ["--candidate-tag", "t", "--max-accuracy-topn-regression", "0.05"]
        )
        assert args.max_accuracy_topn_regression == pytest.approx(0.05)

    def test_max_accuracy_top3_regression_deprecated_alias(self) -> None:
        """--max-accuracy-top3-regression is a deprecated alias that sets the same dest."""
        args = contract_type_quality_gate.parse_args(
            ["--candidate-tag", "t", "--max-accuracy-top3-regression", "0.07"]
        )
        assert args.max_accuracy_topn_regression == pytest.approx(0.07)

    def test_both_flags_last_one_wins(self) -> None:
        """When both flags are given, argparse uses the last value."""
        args = contract_type_quality_gate.parse_args(
            [
                "--candidate-tag",
                "t",
                "--max-accuracy-topn-regression",
                "0.01",
                "--max-accuracy-top3-regression",
                "0.09",
            ]
        )
        # Both map to the same dest; last value on command line wins.
        assert args.max_accuracy_topn_regression == pytest.approx(0.09)

    def test_defaults_are_zero(self) -> None:
        args = contract_type_quality_gate.parse_args(["--candidate-tag", "t"])
        assert args.max_accuracy_topn_regression == pytest.approx(0.0)
        assert args.max_accuracy_top1_regression == pytest.approx(0.0)
        assert args.max_f1_macro_regression == pytest.approx(0.0)
        assert args.max_f1_weighted_regression == pytest.approx(0.0)

    def test_candidate_tag_required(self) -> None:
        with pytest.raises(SystemExit):
            contract_type_quality_gate.parse_args([])

    def test_top_n_default(self) -> None:
        args = contract_type_quality_gate.parse_args(["--candidate-tag", "t"])
        assert args.top_n == 3


# ---------------------------------------------------------------------------
# score_pipeline – zip strict=True
# ---------------------------------------------------------------------------


class _DummyPipeline:
    """Minimal sklearn-like pipeline stub."""

    def __init__(self, classes: list[str], top1_predictions: list[str], probas: np.ndarray):
        self._classes = classes
        self._top1 = top1_predictions
        self._probas = probas
        self.classes_ = classes

    def predict(self, texts):
        return self._top1

    def predict_proba(self, texts):
        return self._probas


class TestScorePipeline:
    def _make_pipeline(
        self, n: int = 4, n_classes: int = 3
    ) -> tuple[_DummyPipeline, list[str], list[str]]:
        rng = np.random.default_rng(42)
        classes = [f"class_{i}" for i in range(n_classes)]
        labels = [classes[i % n_classes] for i in range(n)]
        probas = rng.dirichlet(np.ones(n_classes), size=n)
        pipeline = _DummyPipeline(classes, labels, probas)
        return pipeline, labels, classes

    def test_returns_all_required_metrics(self) -> None:
        pipeline, labels, _ = self._make_pipeline(n=6, n_classes=2)
        texts = [f"doc {i}" for i in range(len(labels))]
        result = contract_type_quality_gate.score_pipeline(pipeline, texts, labels, top_n=2)
        assert set(result.keys()) == {
            "accuracy_top1",
            "accuracy_topn",
            "f1_macro",
            "f1_weighted",
        }

    def test_perfect_predictions(self) -> None:
        classes = ["A", "B", "C"]
        labels = ["A", "B", "C", "A"]
        # probas: each row has 1.0 for the true class
        probas = np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0],
            ]
        )
        pipeline = _DummyPipeline(classes, labels, probas)
        texts = ["t1", "t2", "t3", "t4"]
        result = contract_type_quality_gate.score_pipeline(pipeline, texts, labels, top_n=1)
        assert result["accuracy_top1"] == pytest.approx(1.0)
        assert result["accuracy_topn"] == pytest.approx(1.0)

    def test_top_n_larger_than_n_classes_clips_to_n_classes(self) -> None:
        """top_n > number of classes still works (argsort selects all)."""
        classes = ["A", "B"]
        labels = ["A", "B"]
        probas = np.array([[0.9, 0.1], [0.2, 0.8]])
        pipeline = _DummyPipeline(classes, labels, probas)
        texts = ["t1", "t2"]
        # No exception expected.
        result = contract_type_quality_gate.score_pipeline(pipeline, texts, labels, top_n=10)
        assert "accuracy_topn" in result

    def test_strict_zip_raises_on_mismatched_lengths(self) -> None:
        """
        After the fix, zip(labels, top_indices, strict=True) should raise
        ValueError when labels and top_indices have different lengths.

        We trigger this by monkeypatching predict_proba to return a
        shorter array than the number of labels.
        """
        classes = ["A", "B"]
        labels = ["A", "B", "A"]  # 3 labels
        probas_short = np.array([[0.9, 0.1], [0.2, 0.8]])  # only 2 rows

        pipeline = _DummyPipeline(classes, labels[:2], probas_short)
        # Override predict to return all 3 labels (consistent with len(texts))
        pipeline._top1 = labels  # type: ignore[attr-defined]
        texts = ["t1", "t2", "t3"]

        with pytest.raises(ValueError):
            contract_type_quality_gate.score_pipeline(pipeline, texts, labels, top_n=1)

    def test_pipeline_without_predict_proba_raises(self) -> None:
        """Pipeline missing predict_proba raises ValueError."""

        class NoProbaPipeline:
            classes_ = ["A", "B"]

            def predict(self, texts):
                return texts

        with pytest.raises(ValueError, match="predict_proba"):
            contract_type_quality_gate.score_pipeline(
                NoProbaPipeline(), ["t1"], ["A"], top_n=1
            )

    def test_pipeline_without_classes_raises(self) -> None:
        """Pipeline missing classes_ raises ValueError."""
        probas = np.array([[0.6, 0.4]])
        pipeline = MagicMock()
        pipeline.predict.return_value = ["A"]
        pipeline.predict_proba.return_value = probas
        del pipeline.classes_  # Remove the attribute

        with pytest.raises((ValueError, AttributeError)):
            contract_type_quality_gate.score_pipeline(pipeline, ["t"], ["A"], top_n=1)


# ---------------------------------------------------------------------------
# parse_metrics – backward compatibility with accuracy_top3
# ---------------------------------------------------------------------------


class TestParseMetrics:
    def test_accuracy_top3_backwards_compat(self) -> None:
        raw = {
            "accuracy_top1": 0.8,
            "accuracy_top3": 0.9,
            "f1_macro": 0.75,
            "f1_weighted": 0.76,
        }
        result = contract_type_quality_gate.parse_metrics(raw, "test")
        assert "accuracy_topn" in result
        assert result["accuracy_topn"] == pytest.approx(0.9)

    def test_missing_key_raises(self) -> None:
        raw = {
            "accuracy_top1": 0.8,
            # accuracy_topn missing
            "f1_macro": 0.75,
            "f1_weighted": 0.76,
        }
        with pytest.raises(ValueError, match="accuracy_topn"):
            contract_type_quality_gate.parse_metrics(raw, "test")


# ---------------------------------------------------------------------------
# load_fixture
# ---------------------------------------------------------------------------


class TestLoadFixture:
    def _write_fixture(self, path: Path, rows: list[dict]) -> None:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Text", "Contract_Type"])
            writer.writeheader()
            writer.writerows(rows)

    def test_valid_fixture_loads(self, tmp_path: Path) -> None:
        fixture = tmp_path / "fix.csv"
        self._write_fixture(
            fixture,
            [{"Text": "sample contract", "Contract_Type": "NDA"}],
        )
        texts, labels = contract_type_quality_gate.load_fixture(fixture)
        assert texts == ["sample contract"]
        assert labels == ["NDA"]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            contract_type_quality_gate.load_fixture(tmp_path / "no_file.csv")

    def test_missing_text_column_raises(self, tmp_path: Path) -> None:
        fixture = tmp_path / "fix.csv"
        with fixture.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Text", "Contract_Type"])
            writer.writeheader()
            writer.writerow({"Text": "", "Contract_Type": "NDA"})
        with pytest.raises(ValueError, match="missing Text"):
            contract_type_quality_gate.load_fixture(fixture)

    def test_missing_label_column_raises(self, tmp_path: Path) -> None:
        fixture = tmp_path / "fix.csv"
        with fixture.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["Text", "Contract_Type"])
            writer.writeheader()
            writer.writerow({"Text": "some text", "Contract_Type": ""})
        with pytest.raises(ValueError, match="missing Contract_Type"):
            contract_type_quality_gate.load_fixture(fixture)