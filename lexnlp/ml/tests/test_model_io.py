"""Tests for lexnlp/ml/model_io.py.

Covers the new skops-based model serialization helpers introduced in this PR:
- is_skops_path
- dump_model
- load_model (skops and legacy paths)
- _load_legacy (pickle / joblib dispatch)
- _load_skops (trusted type resolution)
"""

from __future__ import annotations

import pickle
from pathlib import Path
from unittest.mock import patch

import pytest

from lexnlp.ml.model_io import (
    _LEGACY_SUFFIXES,
    CANONICAL_SUFFIX,
    DEFAULT_TRUSTED_ALLOWLIST,
    _load_legacy,
    _load_skops,
    dump_model,
    is_skops_path,
    load_model,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_pickle(path: Path, obj: object) -> Path:
    """Write *obj* to *path* using stdlib pickle."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        pickle.dump(obj, fh)
    return path


# ---------------------------------------------------------------------------
# is_skops_path
# ---------------------------------------------------------------------------


class TestIsSkopsPath:
    def test_true_for_skops_extension(self, tmp_path: Path) -> None:
        assert is_skops_path(Path("model.skops")) is True

    def test_true_for_uppercase_skops_extension(self, tmp_path: Path) -> None:
        assert is_skops_path(Path("model.SKOPS")) is True

    def test_false_for_pickle_extension(self) -> None:
        assert is_skops_path(Path("model.pickle")) is False

    def test_false_for_pkl_extension(self) -> None:
        assert is_skops_path(Path("model.pkl")) is False

    def test_false_for_cloudpickle_extension(self) -> None:
        assert is_skops_path(Path("model.cloudpickle")) is False

    def test_false_for_joblib_extension(self) -> None:
        assert is_skops_path(Path("model.joblib")) is False

    def test_false_for_no_extension(self) -> None:
        assert is_skops_path(Path("model")) is False

    def test_false_for_txt_extension(self) -> None:
        assert is_skops_path(Path("model.txt")) is False

    def test_accepts_path_string_coercion(self) -> None:
        # dump_model converts str→Path; test that is_skops_path itself handles Path objects.
        assert is_skops_path(Path("/some/deep/dir/artifact.skops")) is True


# ---------------------------------------------------------------------------
# dump_model
# ---------------------------------------------------------------------------


class TestDumpModel:
    """Tests for dump_model: suffix normalization, parent directory creation,
    return value, and round-trip fidelity."""

    def test_returns_path_with_skops_suffix(self, tmp_path: Path) -> None:
        obj = {"key": "value"}
        result = dump_model(obj, tmp_path / "model.skops")
        assert result.suffix == CANONICAL_SUFFIX

    def test_normalizes_non_skops_suffix_to_skops(self, tmp_path: Path) -> None:
        """If the caller passes a .pickle path, dump_model rewrites it to .skops."""
        result = dump_model({"x": 1}, tmp_path / "model.pickle")
        assert result.suffix == CANONICAL_SUFFIX
        assert result.stem == "model"

    def test_normalizes_pkl_suffix_to_skops(self, tmp_path: Path) -> None:
        result = dump_model({"x": 1}, tmp_path / "artifact.pkl")
        assert result.suffix == CANONICAL_SUFFIX

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        deep_path = tmp_path / "a" / "b" / "c" / "model.skops"
        dump_model({"y": 2}, deep_path)
        assert deep_path.parent.is_dir()

    def test_written_file_exists(self, tmp_path: Path) -> None:
        dest = tmp_path / "model.skops"
        dump_model(42, dest)
        assert dest.exists()

    def test_roundtrip_dict(self, tmp_path: Path) -> None:
        obj = {"a": 1, "b": [2, 3]}
        path = dump_model(obj, tmp_path / "model.skops")
        loaded = load_model(path, trusted=True)
        assert loaded == obj

    def test_roundtrip_list(self, tmp_path: Path) -> None:
        obj = [1, "two", 3.0]
        path = dump_model(obj, tmp_path / "model.skops")
        loaded = load_model(path, trusted=True)
        assert loaded == obj

    def test_roundtrip_integer(self, tmp_path: Path) -> None:
        path = dump_model(42, tmp_path / "model.skops")
        loaded = load_model(path, trusted=True)
        assert loaded == 42

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        """dump_model should coerce str paths to Path internally."""
        str_path = str(tmp_path / "model.skops")
        result = dump_model({"z": 0}, str_path)
        assert isinstance(result, Path)
        assert result.exists()

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        dest = tmp_path / "model.skops"
        dump_model({"v": 1}, dest)
        dump_model({"v": 99}, dest)
        loaded = load_model(dest, trusted=True)
        assert loaded == {"v": 99}

    def test_returns_normalized_path(self, tmp_path: Path) -> None:
        """Even when the input uses a non-skops suffix, the returned path has .skops."""
        result = dump_model({"q": 1}, tmp_path / "something.bin")
        assert result == tmp_path / "something.skops"


# ---------------------------------------------------------------------------
# _load_legacy
# ---------------------------------------------------------------------------


class TestLoadLegacy:
    """Tests for the _load_legacy private helper that dispatches on suffix."""

    def test_loads_pickle_file(self, tmp_path: Path) -> None:
        path = _write_pickle(tmp_path / "model.pickle", {"a": 1})
        assert _load_legacy(path) == {"a": 1}

    def test_loads_pkl_file(self, tmp_path: Path) -> None:
        path = _write_pickle(tmp_path / "model.pkl", [1, 2, 3])
        assert _load_legacy(path) == [1, 2, 3]

    def test_loads_joblib_file(self, tmp_path: Path) -> None:
        import joblib

        path = tmp_path / "model.joblib"
        joblib.dump({"jl": True}, path)
        assert _load_legacy(path) == {"jl": True}

    def test_loads_joblib_compressed_pickle_file(self, tmp_path: Path) -> None:
        import joblib

        path = tmp_path / "model.pickle"
        joblib.dump({"jl_pickle": True}, path, compress=3)
        assert _load_legacy(path) == {"jl_pickle": True}

    def test_unknown_suffix_raises_value_error(self, tmp_path: Path) -> None:
        """Unknown extensions must be rejected rather than blindly pickle-loaded."""
        path = tmp_path / "model.bin"
        _write_pickle(path, "hello")
        with pytest.raises(ValueError, match="Unsupported file suffix"):
            _load_legacy(path)

    def test_pickle_file_invalid_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "corrupt.pickle"
        path.write_bytes(b"not a pickle")
        with pytest.raises(pickle.UnpicklingError):
            _load_legacy(path)

    def test_loads_cloudpickle_file(self, tmp_path: Path) -> None:
        import cloudpickle

        path = tmp_path / "model.cloudpickle"
        with path.open("wb") as fh:
            cloudpickle.dump({"cp": 1}, fh)
        assert _load_legacy(path) == {"cp": 1}


# ---------------------------------------------------------------------------
# load_model - routing logic
# ---------------------------------------------------------------------------


class TestLoadModel:
    """Tests for load_model's routing logic (skops vs legacy vs unknown suffix)."""

    def test_loads_skops_file(self, tmp_path: Path) -> None:
        obj = {"model": "data"}
        path = dump_model(obj, tmp_path / "model.skops")
        loaded = load_model(path, trusted=True)
        assert loaded == obj

    def test_loads_skops_file_without_trusted_flag(self, tmp_path: Path) -> None:
        """Calling with trusted=False should still load a simple object."""
        path = dump_model({"safe": True}, tmp_path / "model.skops")
        loaded = load_model(path, trusted=False)
        assert loaded == {"safe": True}

    def test_loads_pickle_file(self, tmp_path: Path) -> None:
        path = _write_pickle(tmp_path / "model.pickle", {"legacy": True})
        loaded = load_model(path)
        assert loaded == {"legacy": True}

    def test_loads_pkl_file(self, tmp_path: Path) -> None:
        path = _write_pickle(tmp_path / "model.pkl", 99)
        loaded = load_model(path)
        assert loaded == 99

    def test_loads_joblib_file(self, tmp_path: Path) -> None:
        import joblib

        path = tmp_path / "model.joblib"
        joblib.dump({"jl": "data"}, path)
        loaded = load_model(path)
        assert loaded == {"jl": "data"}

    def test_no_suffix_raises_value_error(self, tmp_path: Path) -> None:
        """A path with no suffix must be rejected (no silent pickle fallback)."""
        path = tmp_path / "modelfile"
        _write_pickle(path, "bare_pickle")
        with pytest.raises(ValueError, match="Unsupported model suffix"):
            load_model(path)

    def test_unknown_suffix_raises_value_error(self, tmp_path: Path) -> None:
        """An unrecognised suffix must be rejected to avoid widening
        unsafe deserialization surface."""
        path = tmp_path / "model.bin"
        _write_pickle(path, "fallback")
        with pytest.raises(ValueError, match="Unsupported model suffix"):
            load_model(path, trusted=True)

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        obj = [10, 20]
        skops_path = dump_model(obj, tmp_path / "model.skops")
        loaded = load_model(str(skops_path), trusted=True)
        assert loaded == obj

    def test_skops_path_dispatches_to_skops_loader(self, tmp_path: Path) -> None:
        """Verify _load_skops is called (not _load_legacy) for .skops paths."""
        obj = {"check": "dispatch"}
        path = dump_model(obj, tmp_path / "model.skops")

        with patch("lexnlp.ml.model_io._load_legacy") as mock_legacy:
            result = load_model(path, trusted=True)
        mock_legacy.assert_not_called()
        assert result == obj

    def test_pickle_path_dispatches_to_legacy_loader(self, tmp_path: Path) -> None:
        """Verify _load_skops is NOT called for .pickle paths."""
        path = _write_pickle(tmp_path / "model.pickle", {"p": 1})

        with patch("lexnlp.ml.model_io._load_skops") as mock_skops:
            result = load_model(path)
        mock_skops.assert_not_called()
        assert result == {"p": 1}


# ---------------------------------------------------------------------------
# _load_skops - trusted type resolution
# ---------------------------------------------------------------------------


class TestLoadSkops:
    """Tests for the _load_skops helper that resolves the trusted type list."""

    def test_loads_simple_object_trusted(self, tmp_path: Path) -> None:
        path = dump_model({"simple": 42}, tmp_path / "model.skops")
        result = _load_skops(path, trusted=True)
        assert result == {"simple": 42}

    def test_loads_simple_object_untrusted(self, tmp_path: Path) -> None:
        """trusted=False should still work for basic built-in types."""
        path = dump_model([1, 2, 3], tmp_path / "model.skops")
        result = _load_skops(path, trusted=False)
        assert result == [1, 2, 3]

    def test_get_untrusted_types_called(self, tmp_path: Path) -> None:
        """get_untrusted_types must be called to enumerate the artifact's types."""
        path = dump_model({"x": 1}, tmp_path / "model.skops")
        with patch("lexnlp.ml.model_io.get_untrusted_types", return_value=[]) as mock_gut:
            _load_skops(path, trusted=True)
        mock_gut.assert_called_once_with(file=path)


# ---------------------------------------------------------------------------
# CANONICAL_SUFFIX / _LEGACY_SUFFIXES constants
# ---------------------------------------------------------------------------


class TestTrustedAllowlist:
    """Tests for the explicit allow-list-based trusted loading path."""

    def test_default_allowlist_is_non_empty(self) -> None:
        assert len(DEFAULT_TRUSTED_ALLOWLIST) > 0

    def test_default_allowlist_includes_common_sklearn_types(self) -> None:
        assert "sklearn.pipeline.Pipeline" in DEFAULT_TRUSTED_ALLOWLIST
        assert "numpy.ndarray" in DEFAULT_TRUSTED_ALLOWLIST

    def test_default_allowlist_is_frozenset(self) -> None:
        assert isinstance(DEFAULT_TRUSTED_ALLOWLIST, frozenset)

    def test_load_rejects_type_outside_allowlist(self, tmp_path: Path) -> None:
        """trusted=True without override rejects artifacts containing a
        type that is not in DEFAULT_TRUSTED_ALLOWLIST."""

        path = dump_model({"x": 1}, tmp_path / "m.skops")
        # Inject a fake untrusted type by patching get_untrusted_types.
        with patch(
            "lexnlp.ml.model_io.get_untrusted_types",
            return_value=["evil.Module.RemoteCodeExecution"],
        ):
            with pytest.raises(Exception):  # noqa: B017 - skops raises its own
                _load_skops(path, trusted=True)

    def test_load_accepts_additional_allowed_type(self, tmp_path: Path) -> None:
        """Callers may extend the allow-list with extra type names."""

        path = dump_model({"x": 1}, tmp_path / "m.skops")
        # No untrusted types are actually present; call should succeed.
        result = _load_skops(path, trusted=True, extra_trusted=("my.Custom.Class",))
        assert result == {"x": 1}


class TestConstants:
    def test_canonical_suffix_is_skops(self) -> None:
        assert CANONICAL_SUFFIX == ".skops"

    def test_legacy_suffixes_includes_pickle(self) -> None:
        assert ".pickle" in _LEGACY_SUFFIXES

    def test_legacy_suffixes_includes_pkl(self) -> None:
        assert ".pkl" in _LEGACY_SUFFIXES

    def test_legacy_suffixes_includes_cloudpickle(self) -> None:
        assert ".cloudpickle" in _LEGACY_SUFFIXES

    def test_legacy_suffixes_includes_joblib(self) -> None:
        assert ".joblib" in _LEGACY_SUFFIXES

    def test_legacy_suffixes_is_frozenset(self) -> None:
        assert isinstance(_LEGACY_SUFFIXES, frozenset)
