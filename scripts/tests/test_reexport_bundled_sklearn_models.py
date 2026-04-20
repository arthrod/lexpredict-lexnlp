"""Tests for scripts/reexport_bundled_sklearn_models.py.

Covers changes introduced in the PR:
  - load_model: catches (pickle.UnpicklingError, ValueError, KeyError) instead
    of bare Exception for the addresses_clf.pickle fallback.
  - reexport_layered_definition_models: try/finally ensures tmp_path is cleaned
    up on exception.
"""

from __future__ import annotations

import io
import pickle
import sys
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile

import pytest

# ---------------------------------------------------------------------------
# Make the scripts package importable.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import reexport_bundled_sklearn_models as script_mod  # noqa: E402  # required: import follows sys.path insertion for test-only script module resolution

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_layered_zip(term_obj: object, definition_obj: object) -> bytes:
    """Build an in-memory zip with term.pickle and definition.pickle entries."""
    buf = io.BytesIO()
    with ZipFile(buf, "w", compression=ZIP_STORED) as zf:
        zf.writestr("term.pickle", pickle.dumps(term_obj, protocol=pickle.HIGHEST_PROTOCOL))
        zf.writestr(
            "definition.pickle", pickle.dumps(definition_obj, protocol=pickle.HIGHEST_PROTOCOL)
        )
    return buf.getvalue()


# ---------------------------------------------------------------------------
# load_model: narrowed exception handling for addresses_clf.pickle
# ---------------------------------------------------------------------------


class TestLoadModelExceptionNarrowing:
    """
    load_model catches (pickle.UnpicklingError, ValueError, KeyError) for
    addresses_clf.pickle.  Other exceptions must propagate.
    """

    def test_unpickling_error_falls_back_to_joblib(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """pickle.UnpicklingError triggers the joblib fallback."""
        fake_model = {"model": "data"}
        addr_clf = tmp_path / "addresses_clf.pickle"
        # Write a joblib-style dump so joblib.load succeeds.
        import joblib
        joblib.dump(fake_model, addr_clf)

        def failing_renamed_load(_f):
            raise pickle.UnpicklingError("bad pickle")

        import lexnlp.utils.unpickler as unpickler_mod
        monkeypatch.setattr(unpickler_mod, "renamed_load", failing_renamed_load)

        result = script_mod.load_model(addr_clf)
        assert result == fake_model

    def test_value_error_falls_back_to_joblib(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ValueError triggers the joblib fallback."""
        fake_model = {"v": 42}
        addr_clf = tmp_path / "addresses_clf.pickle"
        import joblib
        joblib.dump(fake_model, addr_clf)

        def failing_renamed_load(_f):
            raise ValueError("version mismatch")

        import lexnlp.utils.unpickler as unpickler_mod
        monkeypatch.setattr(unpickler_mod, "renamed_load", failing_renamed_load)

        result = script_mod.load_model(addr_clf)
        assert result == fake_model

    def test_key_error_falls_back_to_joblib(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """KeyError triggers the joblib fallback."""
        fake_model = {"k": "v"}
        addr_clf = tmp_path / "addresses_clf.pickle"
        import joblib
        joblib.dump(fake_model, addr_clf)

        def failing_renamed_load(_f):
            raise KeyError("missing_module")

        import lexnlp.utils.unpickler as unpickler_mod
        monkeypatch.setattr(unpickler_mod, "renamed_load", failing_renamed_load)

        result = script_mod.load_model(addr_clf)
        assert result == fake_model

    def test_other_exception_propagates(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Exceptions OTHER than (UnpicklingError, ValueError, KeyError) must NOT
        be swallowed — they should propagate to the caller.
        """
        addr_clf = tmp_path / "addresses_clf.pickle"
        addr_clf.write_bytes(b"irrelevant")

        def exploding_renamed_load(_f):
            raise RuntimeError("unexpected infrastructure error")

        import lexnlp.utils.unpickler as unpickler_mod
        monkeypatch.setattr(unpickler_mod, "renamed_load", exploding_renamed_load)

        with pytest.raises(RuntimeError, match="unexpected infrastructure error"):
            script_mod.load_model(addr_clf)

    def test_non_addresses_model_uses_joblib_directly(
        self, tmp_path: Path
    ) -> None:
        """For non-addresses_clf.pickle files, joblib.load is called directly."""
        fake_model = {"type": "segmenter"}
        model_path = tmp_path / "section_segmenter.pickle"
        import joblib
        joblib.dump(fake_model, model_path)

        result = script_mod.load_model(model_path)
        assert result == fake_model


# ---------------------------------------------------------------------------
# reexport_layered_definition_models: tmp cleanup on exception
# ---------------------------------------------------------------------------


class TestReexportLayeredDefinitionModelsTmpCleanup:
    """
    reexport_layered_definition_models must delete the .part temp file
    if an exception occurs during the ZipFile write phase.
    """

    def test_tmp_file_cleaned_up_on_exception(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        When ZipFile.writestr raises, the .part file must not be left behind.
        """
        # Create a valid layered model zip so load succeeds.
        payload_zip = _make_layered_zip(
            term_obj={"term": "data"},
            definition_obj={"def": "data"},
        )
        model_path = tmp_path / "definition_model_layered.pickle.gzip"
        model_path.write_bytes(payload_zip)

        # Patch load_layered_definition_models to succeed.
        fake_payload = {
            "term.pickle": {"term": "data"},
            "definition.pickle": {"def": "data"},
        }
        monkeypatch.setattr(
            script_mod, "load_layered_definition_models", lambda _p: fake_payload
        )

        # Patch pickle.dumps to raise during the write loop.
        original_dumps = pickle.dumps
        call_count = [0]

        def failing_dumps(obj, protocol=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                raise RuntimeError("simulated serialization failure")
            return original_dumps(obj, protocol=protocol)

        monkeypatch.setattr(pickle, "dumps", failing_dumps)

        with pytest.raises(RuntimeError, match="simulated serialization failure"):
            script_mod.reexport_layered_definition_models(model_path)

        # The .part file must have been removed.
        tmp_part = model_path.with_name(model_path.name + ".part")
        assert not tmp_part.exists(), ".part file must be cleaned up on exception"

    def test_original_file_not_corrupted_on_exception(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The original model file must not be replaced when an exception occurs.
        """
        payload_zip = _make_layered_zip({"term": "original"}, {"def": "original"})
        model_path = tmp_path / "definition_model_layered.pickle.gzip"
        model_path.write_bytes(payload_zip)
        original_content = model_path.read_bytes()

        fake_payload = {
            "term.pickle": {"term": "original"},
            "definition.pickle": {"def": "original"},
        }
        monkeypatch.setattr(
            script_mod, "load_layered_definition_models", lambda _p: fake_payload
        )

        original_dumps = pickle.dumps
        call_count = [0]

        def failing_dumps(obj, protocol=None):
            call_count[0] += 1
            if call_count[0] >= 1:
                raise RuntimeError("write failed")
            return original_dumps(obj, protocol=protocol)

        monkeypatch.setattr(pickle, "dumps", failing_dumps)

        with pytest.raises(RuntimeError):
            script_mod.reexport_layered_definition_models(model_path)

        # The original file must be intact.
        assert model_path.read_bytes() == original_content

    def test_successful_reexport_replaces_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        On success, the model file is replaced and the .part file is gone.
        """
        payload_zip = _make_layered_zip({"term": "v1"}, {"def": "v1"})
        model_path = tmp_path / "definition_model_layered.pickle.gzip"
        model_path.write_bytes(payload_zip)

        fake_payload = {
            "term.pickle": {"term": "v2"},
            "definition.pickle": {"def": "v2"},
        }
        monkeypatch.setattr(
            script_mod, "load_layered_definition_models", lambda _p: fake_payload
        )

        script_mod.reexport_layered_definition_models(model_path)

        # The .part file must not remain.
        tmp_part = model_path.with_name(model_path.name + ".part")
        assert not tmp_part.exists()

        # The model file must now contain the updated payload.
        assert model_path.exists()
        with ZipFile(model_path) as zf:
            reloaded_term = pickle.loads(zf.read("term.pickle"))
            reloaded_def = pickle.loads(zf.read("definition.pickle"))
        assert reloaded_term == {"term": "v2"}
        assert reloaded_def == {"def": "v2"}

    def test_preexisting_part_file_is_removed_before_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        If a stale .part file already exists, it must be removed before writing.
        """
        payload_zip = _make_layered_zip({"t": 1}, {"d": 1})
        model_path = tmp_path / "definition_model_layered.pickle.gzip"
        model_path.write_bytes(payload_zip)

        # Create a stale .part file.
        tmp_part = model_path.with_name(model_path.name + ".part")
        tmp_part.write_bytes(b"stale content")

        fake_payload = {
            "term.pickle": {"t": 2},
            "definition.pickle": {"d": 2},
        }
        monkeypatch.setattr(
            script_mod, "load_layered_definition_models", lambda _p: fake_payload
        )

        # Should succeed even with the stale .part file.
        script_mod.reexport_layered_definition_models(model_path)

        assert not tmp_part.exists()
        assert model_path.exists()