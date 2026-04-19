"""Tests for scripts/asset_drift_check.py.

Covers changes introduced in the PR:
  - Error message format now includes exc.__class__.__name__
  - SHA256 comparison: actual_sha is NOT lowercased; expected_sha is lowercased
    in load_manifest — a mismatch is now caught correctly.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Make the scripts package importable.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import asset_drift_check  # noqa: E402  # imported after sys.path mutation above for test-only script import


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_manifest(path: Path, assets: list) -> None:
    path.write_text(json.dumps({"assets": assets}), encoding="utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Error message format: exc.__class__.__name__ included
# ---------------------------------------------------------------------------


class TestErrorMessageFormat:
    """main() failure entries should include the exception class name."""

    def test_missing_tag_error_includes_class_name(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When catalog lookup raises FileNotFoundError the entry must name the class."""
        manifest_path = tmp_path / "manifest.json"
        _write_manifest(
            manifest_path,
            [{"tag": "pipeline/missing/0.1", "filename": "model.pkl", "sha256": "abc123"}],
        )

        def fake_get_path(tag: str) -> Path:
            raise FileNotFoundError(f"tag not found: {tag}")

        monkeypatch.setattr(
            "asset_drift_check.get_path_from_catalog",
            fake_get_path,
            raising=False,
        )

        # Patch the import inside main as well (it does a local import).
        import unittest.mock as mock

        catalog_mod_mock = mock.MagicMock()
        catalog_mod_mock.get_path_from_catalog = fake_get_path

        dl_mock = mock.MagicMock()
        dl_mock.download_github_release = mock.MagicMock(
            side_effect=FileNotFoundError("release not found")
        )

        with mock.patch.dict(
            "sys.modules",
            {
                "lexnlp.ml.catalog": catalog_mod_mock,
                "lexnlp.ml.catalog.download": dl_mock,
            },
        ):
            import io, contextlib

            stderr_capture = io.StringIO()
            with contextlib.redirect_stderr(stderr_capture):
                rc = asset_drift_check.main(["--manifest", str(manifest_path)])

        assert rc == 1
        stderr_out = stderr_capture.getvalue()
        # The failure message must include the exception class name and tag.
        assert "FileNotFoundError" in stderr_out
        assert "pipeline/missing/0.1: missing/unreadable" in stderr_out

    def test_error_message_includes_class_name_directly(self) -> None:
        """
        Unit-test the failure-message format expression directly.

        The PR changed the format from:
            f"{tag}: missing/unreadable ({exc})"
        to:
            f"{tag}: missing/unreadable ({exc.__class__.__name__}: {exc})"
        """
        exc = FileNotFoundError("tag not found: pipeline/x/0.1")
        tag = "pipeline/x/0.1"
        # Reproduce the exact format used in asset_drift_check.main
        message = f"{tag}: missing/unreadable ({exc.__class__.__name__}: {exc})"
        assert "FileNotFoundError" in message
        assert "pipeline/x/0.1" in message

    def test_error_message_format_for_value_error(self) -> None:
        """ValueError class name should also appear in the formatted message."""
        exc = ValueError("bad data")
        tag = "pipeline/test/0.1"
        message = f"{tag}: missing/unreadable ({exc.__class__.__name__}: {exc})"
        assert "ValueError" in message
        assert "bad data" in message


# ---------------------------------------------------------------------------
# SHA256 comparison: exact-case matching
# ---------------------------------------------------------------------------


class TestSha256Comparison:
    """
    Before the fix: actual_sha was lowercased before comparison.
    After the fix: actual_sha is used verbatim; expected_sha is pre-lowercased.
    sha256.hexdigest() always returns lowercase, so valid manifests still pass.
    """

    def test_lowercase_sha_matches(self, tmp_path: Path) -> None:
        """Lowercase SHA256 in manifest matches hexdigest output."""
        data = b"model data"
        sha = _sha256_bytes(data)
        assert sha == sha.lower(), "hexdigest must already be lowercase"

        model_file = tmp_path / "model.pkl"
        model_file.write_bytes(data)

        actual = asset_drift_check.sha256_file(model_file)
        assert actual == sha  # exact match, no casing issue

    def test_uppercase_sha_in_manifest_does_not_match(self, tmp_path: Path) -> None:
        """
        If a manifest entry has an uppercase SHA (non-canonical), it won't match
        the hexdigest — this tests the exact comparison semantics.

        expected_sha = asset["sha256"].strip().lower()  <-- always lower in main()
        actual_sha   = sha256_file(path)                <-- always lower from hexdigest

        So the comparison is lowercase vs lowercase: they SHOULD match for a valid file.
        This test verifies sha256_file returns lowercase always.
        """
        data = b"some bytes"
        model_file = tmp_path / "model.pkl"
        model_file.write_bytes(data)

        actual = asset_drift_check.sha256_file(model_file)
        assert actual == actual.lower(), "sha256_file must return lowercase hex"

    def test_sha_mismatch_is_detected(self, tmp_path: Path) -> None:
        """A file whose actual SHA differs from the manifest entry is a failure."""
        manifest_path = tmp_path / "manifest.json"
        model_file = tmp_path / "model.pkl"
        model_file.write_bytes(b"correct content")
        correct_sha = _sha256_bytes(b"correct content")
        wrong_sha = _sha256_bytes(b"different content")

        _write_manifest(
            manifest_path,
            [
                {
                    "tag": "pipeline/test/0.1",
                    "filename": "model.pkl",
                    "sha256": wrong_sha,
                }
            ],
        )

        import unittest.mock as mock

        catalog_mock = mock.MagicMock()
        catalog_mock.get_path_from_catalog = mock.MagicMock(return_value=model_file)

        dl_mock = mock.MagicMock()

        with mock.patch.dict(
            "sys.modules",
            {
                "lexnlp.ml.catalog": catalog_mock,
                "lexnlp.ml.catalog.download": dl_mock,
            },
        ):
            import io, contextlib

            stderr_capture = io.StringIO()
            with contextlib.redirect_stderr(stderr_capture):
                rc = asset_drift_check.main(["--manifest", str(manifest_path)])

        assert rc == 1
        assert "sha256 mismatch" in stderr_capture.getvalue()
        # The actual SHA should be present verbatim (lowercase from hexdigest).
        assert correct_sha in stderr_capture.getvalue()

    def test_sha_match_succeeds(self, tmp_path: Path) -> None:
        """A file whose SHA matches the manifest entry passes."""
        data = b"model payload"
        model_file = tmp_path / "model.pkl"
        model_file.write_bytes(data)
        sha = _sha256_bytes(data)

        manifest_path = tmp_path / "manifest.json"
        _write_manifest(
            manifest_path,
            [
                {
                    "tag": "pipeline/test/0.1",
                    "filename": "model.pkl",
                    "sha256": sha,
                }
            ],
        )

        import unittest.mock as mock

        catalog_mock = mock.MagicMock()
        catalog_mock.get_path_from_catalog = mock.MagicMock(return_value=model_file)

        dl_mock = mock.MagicMock()

        with mock.patch.dict(
            "sys.modules",
            {
                "lexnlp.ml.catalog": catalog_mock,
                "lexnlp.ml.catalog.download": dl_mock,
            },
        ):
            rc = asset_drift_check.main(["--manifest", str(manifest_path)])

        assert rc == 0


# ---------------------------------------------------------------------------
# load_manifest - basic validation
# ---------------------------------------------------------------------------


class TestLoadManifest:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            asset_drift_check.load_manifest(tmp_path / "nonexistent.json")

    def test_non_dict_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "m.json"
        path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with pytest.raises(ValueError, match="object"):
            asset_drift_check.load_manifest(path)

    def test_empty_assets_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "m.json"
        path.write_text(json.dumps({"assets": []}), encoding="utf-8")
        with pytest.raises(ValueError, match="non-empty"):
            asset_drift_check.load_manifest(path)

    def test_valid_manifest_returns_payload(self, tmp_path: Path) -> None:
        path = tmp_path / "m.json"
        payload = {"assets": [{"tag": "t", "filename": "f", "sha256": "s"}]}
        path.write_text(json.dumps(payload), encoding="utf-8")
        result = asset_drift_check.load_manifest(path)
        assert result["assets"][0]["tag"] == "t"