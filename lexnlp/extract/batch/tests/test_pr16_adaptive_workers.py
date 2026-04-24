"""Tests for ``adaptive_max_workers`` introduced in PR-16.

The function was added to :mod:`lexnlp.extract.batch.async_extract` and
re-exported from :mod:`lexnlp.extract.batch.progress`. It uses ``psutil``
to derive a worker count from physical CPU cores and available RAM.

The module itself is PEP-695-free, so these tests run on Python 3.11+.
We import from the progress module (also PEP-695-free) to avoid the
batch ``__init__.py`` which requires Python 3.12.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

import importlib.util
import pathlib
import sys
from unittest.mock import MagicMock, patch

# Import async_extract via the normal package path. It's already PEP 695
# compatible on Python 3.13 (the project floor), so the previous
# importlib-based bypass is no longer necessary.
from lexnlp.extract.batch.async_extract import adaptive_max_workers

# ---------------------------------------------------------------------------
# Basic contract
# ---------------------------------------------------------------------------


class TestAdaptiveMaxWorkersContract:
    def test_returns_int(self) -> None:
        result = adaptive_max_workers()
        assert isinstance(result, int)

    def test_returns_at_least_one(self) -> None:
        assert adaptive_max_workers() >= 1

    def test_deterministic_on_repeated_calls(self) -> None:
        # Repeated calls on the same machine should return consistent values
        # (assuming available RAM does not fluctuate wildly between calls).
        first = adaptive_max_workers()
        second = adaptive_max_workers()
        # Allow a small variance of ±1 in case available RAM shifts.
        assert abs(first - second) <= 1


# ---------------------------------------------------------------------------
# Mocked psutil — verify cap-at-physical-cores logic
# ---------------------------------------------------------------------------


class TestAdaptiveMaxWorkersWithMockedPsutil:
    """Mock psutil so the test is deterministic regardless of the host machine."""

    def _call_with_mocked_psutil(self, physical_cores: int, available_gb: float) -> int:
        """Run ``adaptive_max_workers`` with deterministic psutil responses."""
        mock_psutil = MagicMock()
        mock_psutil.cpu_count.return_value = physical_cores
        mem_mock = MagicMock()
        mem_mock.available = int(available_gb * 1024**3)
        mock_psutil.virtual_memory.return_value = mem_mock

        with patch.dict(sys.modules, {"psutil": mock_psutil}):
            # Re-execute the module so it picks up the patched psutil import.
            module_name = "lexnlp.extract.batch.async_extract_patched"
            spec = importlib.util.spec_from_file_location(
                module_name,
                str(pathlib.Path(__file__).parent.parent / "async_extract.py"),
            )
            patched_mod = importlib.util.module_from_spec(spec)  # type: ignore
            # Register in sys.modules BEFORE exec_module so PEP 695 generic
            # dataclass machinery (which resolves annotations via
            # ``sys.modules.get(cls.__module__)``) can find the module.
            sys.modules[module_name] = patched_mod
            try:
                spec.loader.exec_module(patched_mod)  # type: ignore
                return patched_mod.adaptive_max_workers()
            finally:
                sys.modules.pop(module_name, None)

    def test_caps_at_physical_cores(self) -> None:
        # 4 cores, 32 GiB RAM → by_memory = 64, capped at 4 cores.
        result = self._call_with_mocked_psutil(physical_cores=4, available_gb=32.0)
        assert result == 4

    def test_limited_by_memory(self) -> None:
        # 16 cores, 0.5 GiB RAM → by_memory=1, so result=1.
        result = self._call_with_mocked_psutil(physical_cores=16, available_gb=0.5)
        assert result == 1

    def test_single_core_machine_returns_one(self) -> None:
        result = self._call_with_mocked_psutil(physical_cores=1, available_gb=8.0)
        assert result == 1

    def test_low_memory_returns_at_least_one(self) -> None:
        # Even with 0 GiB available, must return at least 1.
        result = self._call_with_mocked_psutil(physical_cores=8, available_gb=0.0)
        assert result >= 1

    def test_zero_physical_cores_falls_back_to_four(self) -> None:
        # psutil.cpu_count(logical=False) can return None on some systems.
        # The code does ``psutil.cpu_count(logical=False) or 4``.
        mock_psutil = MagicMock()
        mock_psutil.cpu_count.return_value = None  # simulate unavailable
        mem_mock = MagicMock()
        mem_mock.available = 32 * 1024**3  # 32 GiB
        mock_psutil.virtual_memory.return_value = mem_mock

        with patch.dict(sys.modules, {"psutil": mock_psutil}):
            module_name = "lexnlp.extract.batch.async_extract_patched2"
            spec = importlib.util.spec_from_file_location(
                module_name,
                str(pathlib.Path(__file__).parent.parent / "async_extract.py"),
            )
            patched_mod = importlib.util.module_from_spec(spec)  # type: ignore
            sys.modules[module_name] = patched_mod
            try:
                spec.loader.exec_module(patched_mod)  # type: ignore
                result = patched_mod.adaptive_max_workers()
            finally:
                sys.modules.pop(module_name, None)
        # Falls back to 4 physical cores → capped at 4, memory allows many.
        assert result == 4

    def test_eight_cores_abundant_ram(self) -> None:
        # 8 cores, 16 GiB → by_memory = 32, capped at 8.
        result = self._call_with_mocked_psutil(physical_cores=8, available_gb=16.0)
        assert result == 8

    def test_two_cores_one_gb_available(self) -> None:
        # 2 cores, 1 GiB RAM → by_memory = 2, capped at 2.
        result = self._call_with_mocked_psutil(physical_cores=2, available_gb=1.0)
        assert result == 2


# ---------------------------------------------------------------------------
# Integration with extract_batch_with_progress
# ---------------------------------------------------------------------------


class TestAdaptiveWorkersUsedByProgressModule:
    """Verify that ``extract_batch_with_progress`` picks up adaptive_max_workers
    when max_workers is not provided."""

    def test_no_max_workers_uses_default(self) -> None:
        # Import progress module directly.
        spec = importlib.util.spec_from_file_location(
            "lexnlp.extract.batch.progress",
            str(pathlib.Path(__file__).parent.parent / "progress.py"),
        )
        prog_mod = importlib.util.module_from_spec(spec)  # type: ignore
        spec.loader.exec_module(prog_mod)  # type: ignore

        extract_batch_with_progress = prog_mod.extract_batch_with_progress

        def _words(text: str) -> list[str]:
            return text.split()

        results = extract_batch_with_progress(_words, ["hello world", "foo bar"], show_progress=False)
        assert len(results) == 2
        assert all(r.ok for r in results)
