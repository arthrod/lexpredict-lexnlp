"""Tests for :func:`GitHubReleaseDownloader.download_asset` Path handling.

PR #14 review noted ``destination_directory`` accepts ``Path | str`` but the
implementation called ``.mkdir`` on the raw argument, which would explode
with ``AttributeError`` when a ``str`` was passed. After the fix, the
helper normalizes the argument via ``Path(destination_directory)`` before
use.

We mock out the network-touching ``requests.get`` so the test does not hit
GitHub. The focus is on the filesystem branch.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from lexnlp.ml.catalog.download import GitHubReleaseDownloader


def _fake_response(payload: bytes) -> MagicMock:
    """
    Create a mocked HTTP response that simulates streaming `payload` as a download.
    
    Parameters:
        payload (bytes): The byte content to be yielded by the response's stream.
    
    Returns:
        MagicMock: A mock response with:
            - `raise_for_status()` as a no-op,
            - `headers["Content-Length"]` set to the length of `payload`,
            - `iter_content(chunk_size)` yielding a single chunk equal to `payload`.
    """
    response = MagicMock()
    response.raise_for_status = lambda: None
    response.headers = {"Content-Length": str(len(payload))}
    response.iter_content = lambda chunk_size=8192: iter([payload])
    return response


class TestDownloadAssetNormalizesPath:
    @patch("lexnlp.ml.catalog.download.get")
    def test_str_destination_does_not_raise(self, mock_get: MagicMock, tmp_path: Path) -> None:
        mock_get.return_value = _fake_response(b"payload")
        asset = {"url": "https://example.invalid/", "name": "thing.bin", "size": 7}
        # Pass the directory as a *str* on purpose to exercise the fix.
        GitHubReleaseDownloader.download_asset(asset, str(tmp_path))
        assert (tmp_path / "thing.bin").read_bytes() == b"payload"

    @patch("lexnlp.ml.catalog.download.get")
    def test_path_destination_still_works(self, mock_get: MagicMock, tmp_path: Path) -> None:
        mock_get.return_value = _fake_response(b"abc")
        asset = {"url": "https://example.invalid/", "name": "abc.bin", "size": 3}
        GitHubReleaseDownloader.download_asset(asset, tmp_path)
        assert (tmp_path / "abc.bin").read_bytes() == b"abc"

    @patch("lexnlp.ml.catalog.download.get")
    def test_nested_destination_is_created(self, mock_get: MagicMock, tmp_path: Path) -> None:
        mock_get.return_value = _fake_response(b"ok")
        nested = tmp_path / "a" / "b" / "c"
        asset = {"url": "https://example.invalid/", "name": "n.bin", "size": 2}
        GitHubReleaseDownloader.download_asset(asset, str(nested))
        assert (nested / "n.bin").exists()
