"""Tests for scripts/train_contract_type_model.py.

Covers changes introduced in the PR:
  - main(): stratification fallback (try/except ValueError on train_test_split)
  - main(): wrote_artifact is included in the JSON report
  - main(): returns exit code 1 when wrote=False (artifact already exists)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Make the scripts package importable.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_argv(tmp_path: Path, *, force: bool = False, extra: list | None = None) -> list[str]:
    output_json = tmp_path / "report.json"
    argv = [
        "--target-tag", "pipeline/test/0.1",
        "--output-json", str(output_json),
    ]
    if force:
        argv.append("--force")
    if extra:
        argv.extend(extra)
    return argv


def _patch_runtime_model(
    monkeypatch: pytest.MonkeyPatch,
    *,
    corpus_path: Path,
    texts: list[str],
    labels: list[str],
    pipeline: object,
    destination: Path,
    wrote: bool,
) -> None:
    """Patch all the lexnlp.extract.en.contracts.runtime_model imports used in the script."""
    import train_contract_type_model as script_mod

    monkeypatch.setattr(script_mod, "ensure_tag_downloaded", lambda tag: corpus_path)
    monkeypatch.setattr(
        script_mod,
        "collect_contract_type_samples",
        lambda _archive, *, max_docs_per_label, head_character_n: (texts, labels, {}),
    )
    monkeypatch.setattr(
        script_mod,
        "train_contract_type_pipeline",
        lambda _texts, _labels, *, random_state: pipeline,
    )
    monkeypatch.setattr(
        script_mod,
        "write_pipeline_to_catalog",
        lambda *, pipeline, target_tag, force: (destination, wrote),
    )


# ---------------------------------------------------------------------------
# wrote_artifact in report
# ---------------------------------------------------------------------------


class TestWroteArtifactInReport:
    """The JSON report must include a 'wrote_artifact' key."""

    def test_report_includes_wrote_artifact_true(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import train_contract_type_model as script_mod

        corpus = tmp_path / "corpus.tar.xz"
        corpus.write_bytes(b"")
        destination = tmp_path / "pipeline_contract_type_classifier.cloudpickle"
        destination.write_bytes(b"model")

        texts = [f"document {i}" for i in range(10)]
        labels = (["A"] * 5) + (["B"] * 5)
        pipeline = MagicMock()
        pipeline.predict.side_effect = lambda X: ["A"] * len(X)

        _patch_runtime_model(
            monkeypatch,
            corpus_path=corpus,
            texts=texts,
            labels=labels,
            pipeline=pipeline,
            destination=destination,
            wrote=True,
        )

        output_json = tmp_path / "report.json"
        rc = script_mod.main(
            [
                "--target-tag", "pipeline/test/0.1",
                "--output-json", str(output_json),
                "--force",
            ]
        )

        assert rc == 0
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert "wrote_artifact" in report
        assert report["wrote_artifact"] is True

    def test_report_includes_wrote_artifact_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import train_contract_type_model as script_mod

        corpus = tmp_path / "corpus.tar.xz"
        corpus.write_bytes(b"")
        destination = tmp_path / "pipeline_contract_type_classifier.cloudpickle"
        destination.write_bytes(b"model")

        texts = [f"document {i}" for i in range(10)]
        labels = (["A"] * 5) + (["B"] * 5)
        pipeline = MagicMock()
        pipeline.predict.side_effect = lambda X: ["A"] * len(X)

        _patch_runtime_model(
            monkeypatch,
            corpus_path=corpus,
            texts=texts,
            labels=labels,
            pipeline=pipeline,
            destination=destination,
            wrote=False,  # artifact already exists
        )

        output_json = tmp_path / "report.json"
        rc = script_mod.main(
            [
                "--target-tag", "pipeline/test/0.1",
                "--output-json", str(output_json),
            ]
        )

        # Returns 1 when wrote=False.
        assert rc == 1
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert "wrote_artifact" in report
        assert report["wrote_artifact"] is False


# ---------------------------------------------------------------------------
# Exit code 1 when artifact already exists (wrote=False)
# ---------------------------------------------------------------------------


class TestExitCodeWhenNotWrote:
    def test_exit_code_1_when_wrote_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import train_contract_type_model as script_mod

        corpus = tmp_path / "corpus.tar.xz"
        corpus.write_bytes(b"")
        destination = tmp_path / "model.pkl"
        destination.write_bytes(b"existing")

        texts = [f"doc {i}" for i in range(6)]
        labels = (["X"] * 3) + (["Y"] * 3)
        pipeline = MagicMock()
        pipeline.predict.side_effect = lambda X: ["A"] * len(X)

        _patch_runtime_model(
            monkeypatch,
            corpus_path=corpus,
            texts=texts,
            labels=labels,
            pipeline=pipeline,
            destination=destination,
            wrote=False,
        )

        output_json = tmp_path / "report.json"
        rc = script_mod.main(
            ["--target-tag", "pipeline/test/0.1", "--output-json", str(output_json)]
        )
        assert rc == 1

    def test_exit_code_0_when_wrote_true(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import train_contract_type_model as script_mod

        corpus = tmp_path / "corpus.tar.xz"
        corpus.write_bytes(b"")
        destination = tmp_path / "model.pkl"
        destination.write_bytes(b"new")

        texts = [f"doc {i}" for i in range(6)]
        labels = (["X"] * 3) + (["Y"] * 3)
        pipeline = MagicMock()
        pipeline.predict.side_effect = lambda X: ["A"] * len(X)

        _patch_runtime_model(
            monkeypatch,
            corpus_path=corpus,
            texts=texts,
            labels=labels,
            pipeline=pipeline,
            destination=destination,
            wrote=True,
        )

        output_json = tmp_path / "report.json"
        rc = script_mod.main(
            ["--target-tag", "pipeline/test/0.1", "--output-json", str(output_json), "--force"]
        )
        assert rc == 0


# ---------------------------------------------------------------------------
# Stratification fallback
# ---------------------------------------------------------------------------


class TestStratificationFallback:
    """
    When train_test_split raises ValueError due to stratification constraints,
    the script must retry without stratification rather than propagating the error.
    """

    def test_stratification_fallback_succeeds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Simulate a corpus where one label has only one sample so stratification
        fails; the retry without stratification must succeed.
        """
        import train_contract_type_model as script_mod

        corpus = tmp_path / "corpus.tar.xz"
        corpus.write_bytes(b"")
        destination = tmp_path / "model.pkl"
        destination.write_bytes(b"model")

        # Both labels have >= 2 samples so can_stratify is True.
        # The mock will then simulate a stratification failure.
        texts = [f"doc {label} {i}" for i in range(3) for label in ["A", "B"]]
        labels = ["A", "B", "A", "B", "A", "B"]
        # Use a pipeline whose predict() adapts to input size.
        pipeline = MagicMock()
        pipeline.predict.side_effect = lambda X: ["A"] * len(X)

        _patch_runtime_model(
            monkeypatch,
            corpus_path=corpus,
            texts=texts,
            labels=labels,
            pipeline=pipeline,
            destination=destination,
            wrote=True,
        )

        # Patch train_test_split to raise ValueError on first call (stratified),
        # then succeed on second call (no stratification).
        from sklearn.model_selection import train_test_split as real_split

        call_count = [0]

        def mock_split(X, y, *, test_size, random_state, stratify, shuffle):
            call_count[0] += 1
            if call_count[0] == 1 and stratify is not None:
                raise ValueError("stratify error: not enough members")
            return real_split(
                X, y, test_size=test_size, random_state=random_state, shuffle=shuffle
            )

        monkeypatch.setattr(script_mod, "train_test_split", mock_split)

        output_json = tmp_path / "report.json"
        rc = script_mod.main(
            ["--target-tag", "pipeline/test/0.1", "--output-json", str(output_json), "--force"]
        )

        assert rc == 0
        # Ensure train_test_split was called twice (once with stratify, once without).
        assert call_count[0] == 2

    def test_stratification_used_when_possible(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        When min samples per label >= 2, stratification must be attempted first.
        """
        import train_contract_type_model as script_mod

        corpus = tmp_path / "corpus.tar.xz"
        corpus.write_bytes(b"")
        destination = tmp_path / "model.pkl"
        destination.write_bytes(b"model")

        texts = [f"doc {i}" for i in range(8)]
        labels = (["A"] * 4) + (["B"] * 4)
        pipeline = MagicMock()
        pipeline.predict.side_effect = lambda X: ["A"] * len(X)

        _patch_runtime_model(
            monkeypatch,
            corpus_path=corpus,
            texts=texts,
            labels=labels,
            pipeline=pipeline,
            destination=destination,
            wrote=True,
        )

        from sklearn.model_selection import train_test_split as real_split

        stratify_calls = []

        def mock_split(X, y, *, test_size, random_state, stratify, shuffle):
            stratify_calls.append(stratify)
            return real_split(
                X, y, test_size=test_size, random_state=random_state,
                stratify=stratify, shuffle=shuffle
            )

        monkeypatch.setattr(script_mod, "train_test_split", mock_split)

        output_json = tmp_path / "report.json"
        script_mod.main(
            ["--target-tag", "pipeline/test/0.1", "--output-json", str(output_json), "--force"]
        )

        # The first call must use stratify (not None).
        assert stratify_calls[0] is not None