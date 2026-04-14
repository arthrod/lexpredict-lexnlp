"""Tests for scripts/bootstrap_assets.py.

Covers changes introduced in the PR:
  - download_file: URL scheme validation (only http/https allowed)
  - extract_zip: zip-slip protection
  - run_selected_tasks: lambda closure fix for contract_model_tag /
    contract_type_model_tag
"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Make the scripts package importable from within the test suite.
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import bootstrap_assets  # noqa: E402  (module-level import after sys.path tweak)


# ---------------------------------------------------------------------------
# download_file – URL scheme validation
# ---------------------------------------------------------------------------


class TestDownloadFileSchemeValidation:
    """URL scheme guard introduced in this PR."""

    def test_http_scheme_proceeds_to_download(self, tmp_path: Path) -> None:
        """http:// URLs must pass the scheme check and attempt an actual download."""
        destination = tmp_path / "out.zip"
        with patch("bootstrap_assets.urlopen") as mock_urlopen:
            mock_response = io.BytesIO(b"data")
            mock_response.__enter__ = lambda s: s  # type: ignore[attr-defined]
            mock_response.__exit__ = lambda *a: None  # type: ignore[attr-defined]
            mock_urlopen.return_value = mock_response
            # Should not raise; urlopen is expected to be called.
            # We can't easily let the full flow complete without network, so
            # we patch urlopen to raise a controlled error after the check.
            mock_urlopen.side_effect = OSError("no network")
            with pytest.raises(OSError, match="no network"):
                bootstrap_assets.download_file(
                    "http://example.com/file.zip",
                    destination,
                    force=True,
                    dry_run=False,
                    timeout=5,
                )
            # Crucially: no ValueError was raised first.

    def test_https_scheme_proceeds_to_download(self, tmp_path: Path) -> None:
        """https:// URLs must pass the scheme check."""
        destination = tmp_path / "out.zip"
        with patch("bootstrap_assets.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = OSError("no network")
            with pytest.raises(OSError, match="no network"):
                bootstrap_assets.download_file(
                    "https://example.com/file.zip",
                    destination,
                    force=True,
                    dry_run=False,
                    timeout=5,
                )

    def test_ftp_scheme_raises_value_error(self, tmp_path: Path) -> None:
        """ftp:// URLs must be rejected before any network call."""
        destination = tmp_path / "out.zip"
        with pytest.raises(ValueError, match="unsupported scheme"):
            bootstrap_assets.download_file(
                "ftp://example.com/file.zip",
                destination,
                force=True,
                dry_run=False,
                timeout=5,
            )

    def test_file_scheme_raises_value_error(self, tmp_path: Path) -> None:
        """file:// URLs must be rejected."""
        destination = tmp_path / "out.zip"
        with pytest.raises(ValueError, match="unsupported scheme"):
            bootstrap_assets.download_file(
                "file:///etc/passwd",
                destination,
                force=True,
                dry_run=False,
                timeout=5,
            )

    def test_scheme_error_message_contains_scheme_and_url(self, tmp_path: Path) -> None:
        """ValueError message should name the offending scheme."""
        destination = tmp_path / "out.zip"
        with pytest.raises(ValueError, match="'ftp'"):
            bootstrap_assets.download_file(
                "ftp://example.com/resource",
                destination,
                force=True,
                dry_run=False,
                timeout=5,
            )

    def test_dry_run_skips_scheme_check(self, tmp_path: Path) -> None:
        """In dry-run mode the scheme check is not reached; no error expected."""
        destination = tmp_path / "out.zip"
        # dry_run=True logs and returns before the scheme check – no error.
        bootstrap_assets.download_file(
            "ftp://example.com/file.zip",
            destination,
            force=True,
            dry_run=True,
            timeout=5,
        )

    def test_existing_destination_skips_scheme_check_when_not_forced(
        self, tmp_path: Path
    ) -> None:
        """When destination already exists and force=False, skip before scheme check."""
        destination = tmp_path / "out.zip"
        destination.write_bytes(b"existing")
        # No error even for an invalid URL scheme because the function returns early.
        bootstrap_assets.download_file(
            "ftp://example.com/file.zip",
            destination,
            force=False,
            dry_run=False,
            timeout=5,
        )


# ---------------------------------------------------------------------------
# extract_zip – zip-slip protection
# ---------------------------------------------------------------------------


def _make_zip(members: dict[str, bytes]) -> bytes:
    """Build an in-memory ZIP archive with the given {filename: content} mapping."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return buf.getvalue()


class TestExtractZipSlipProtection:
    """Zip-slip guard introduced in this PR."""

    def test_safe_members_extracted_correctly(self, tmp_path: Path) -> None:
        """Normal archive members are extracted to the correct location."""
        archive_bytes = _make_zip(
            {
                "subdir/file.txt": b"hello",
                "toplevel.txt": b"world",
            }
        )
        archive_path = tmp_path / "archive.zip"
        archive_path.write_bytes(archive_bytes)
        dest = tmp_path / "out"

        bootstrap_assets.extract_zip(archive_path, dest, dry_run=False)

        assert (dest / "subdir" / "file.txt").read_bytes() == b"hello"
        assert (dest / "toplevel.txt").read_bytes() == b"world"

    def test_path_traversal_raises_runtime_error(self, tmp_path: Path) -> None:
        """Members whose resolved path escapes the destination raise RuntimeError."""
        archive_bytes = _make_zip({"../escape.txt": b"evil"})
        archive_path = tmp_path / "evil.zip"
        archive_path.write_bytes(archive_bytes)
        dest = tmp_path / "out"

        with pytest.raises(RuntimeError, match="unsafe path"):
            bootstrap_assets.extract_zip(archive_path, dest, dry_run=False)

    def test_absolute_path_member_raises_runtime_error(self, tmp_path: Path) -> None:
        """Absolute-path member names that resolve outside the destination are rejected."""
        # Build a zip with an absolute-path member using a raw ZipInfo.
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            info = zipfile.ZipInfo("/tmp/absolute.txt")
            zf.writestr(info, b"evil")
        archive_path = tmp_path / "abs.zip"
        archive_path.write_bytes(buf.getvalue())
        dest = tmp_path / "out"

        with pytest.raises(RuntimeError, match="unsafe path"):
            bootstrap_assets.extract_zip(archive_path, dest, dry_run=False)

    def test_deep_traversal_raises_runtime_error(self, tmp_path: Path) -> None:
        """Deep path-traversal sequences are also caught."""
        archive_bytes = _make_zip({"a/b/../../../../../../etc/passwd": b"evil"})
        archive_path = tmp_path / "deep.zip"
        archive_path.write_bytes(archive_bytes)
        dest = tmp_path / "out"

        with pytest.raises(RuntimeError, match="unsafe path"):
            bootstrap_assets.extract_zip(archive_path, dest, dry_run=False)

    def test_dry_run_does_not_extract(self, tmp_path: Path) -> None:
        """dry_run=True must not create any files."""
        archive_bytes = _make_zip({"file.txt": b"data"})
        archive_path = tmp_path / "archive.zip"
        archive_path.write_bytes(archive_bytes)
        dest = tmp_path / "out"

        bootstrap_assets.extract_zip(archive_path, dest, dry_run=True)

        assert not dest.exists()


# ---------------------------------------------------------------------------
# Lambda closure fix in run_selected_tasks
# ---------------------------------------------------------------------------


class TestLambdaClosureFix:
    """
    Before the fix, both lambda callbacks captured the loop variables by
    reference, meaning every callback used the *last* value assigned to
    contract_model_tag / contract_type_model_tag.  After the fix each
    lambda binds the tag value at construction time via a default argument.
    """

    def _make_args(
        self,
        *,
        dry_run: bool = True,
        all_tasks: bool = False,
        contract_model: bool = False,
        contract_type_model: bool = False,
    ) -> "bootstrap_assets.argparse.Namespace":
        import argparse

        ns = argparse.Namespace(
            nltk=False,
            contract_model=contract_model,
            contract_type_model=contract_type_model,
            stanford=False,
            tika=False,
            all=all_tasks,
            dry_run=dry_run,
            force=False,
            timeout=30,
            stanford_dir=str(bootstrap_assets.DEFAULT_STANFORD_DIR),
            tika_dir=str(bootstrap_assets.DEFAULT_TIKA_DIR),
            verbose=False,
        )
        return ns

    def test_contract_model_lambda_captures_tag_at_construction(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The lambda for contract-model task must capture the tag resolved
        at task-list construction time, not any later mutation.
        """
        captured_tags: list[str] = []

        def fake_bootstrap_contract_model(*, dry_run: bool, tag: str) -> None:
            captured_tags.append(tag)

        monkeypatch.setattr(
            bootstrap_assets, "bootstrap_contract_model", fake_bootstrap_contract_model
        )
        monkeypatch.setattr(
            bootstrap_assets,
            "resolve_contract_model_tag",
            lambda: "pipeline/is-contract/TEST-TAG",
        )

        args = self._make_args(contract_model=True)
        bootstrap_assets.run_selected_tasks(args)

        assert captured_tags == ["pipeline/is-contract/TEST-TAG"]

    def test_contract_type_model_lambda_captures_tag_at_construction(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The lambda for contract-type-model task must capture the tag resolved
        at task-list construction time.
        """
        captured_tags: list[str] = []

        def fake_bootstrap_contract_type_model(*, dry_run: bool, tag: str) -> None:
            captured_tags.append(tag)

        monkeypatch.setattr(
            bootstrap_assets,
            "bootstrap_contract_type_model",
            fake_bootstrap_contract_type_model,
        )
        monkeypatch.setattr(
            bootstrap_assets,
            "resolve_contract_type_model_tag",
            lambda: "pipeline/contract-type/TEST-TAG",
        )

        args = self._make_args(contract_type_model=True)
        bootstrap_assets.run_selected_tasks(args)

        assert captured_tags == ["pipeline/contract-type/TEST-TAG"]

    def test_both_lambdas_capture_independent_tags(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When both tasks are scheduled they each use their own tag."""
        captured: list[tuple[str, str]] = []

        def fake_contract_model(*, dry_run: bool, tag: str) -> None:
            captured.append(("contract-model", tag))

        def fake_contract_type_model(*, dry_run: bool, tag: str) -> None:
            captured.append(("contract-type-model", tag))

        monkeypatch.setattr(bootstrap_assets, "bootstrap_contract_model", fake_contract_model)
        monkeypatch.setattr(
            bootstrap_assets, "bootstrap_contract_type_model", fake_contract_type_model
        )
        monkeypatch.setattr(
            bootstrap_assets, "resolve_contract_model_tag", lambda: "tag-contract"
        )
        monkeypatch.setattr(
            bootstrap_assets, "resolve_contract_type_model_tag", lambda: "tag-contract-type"
        )

        args = self._make_args(contract_model=True, contract_type_model=True)
        bootstrap_assets.run_selected_tasks(args)

        assert ("contract-model", "tag-contract") in captured
        assert ("contract-type-model", "tag-contract-type") in captured