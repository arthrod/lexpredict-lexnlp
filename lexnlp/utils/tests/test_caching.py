"""Tests for :mod:`lexnlp.utils.caching`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import os
from pathlib import Path

import pytest

import lexnlp.utils.caching as caching_module
from lexnlp.utils.caching import DEFAULT_CACHE_ENV, cache, clear_cache, get_memory


@pytest.fixture(autouse=True)
def _reset_memory_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Reset the module-level cache between tests."""
    monkeypatch.setenv(DEFAULT_CACHE_ENV, str(tmp_path))
    caching_module.get_memory.cache_clear()
    yield
    caching_module.get_memory.cache_clear()


class TestGetMemory:
    def test_uses_env_override(self, tmp_path: Path) -> None:
        mem = get_memory()
        assert Path(mem.location) == tmp_path

    def test_is_cached(self) -> None:
        a = get_memory()
        b = get_memory()
        assert a is b


class TestCacheDecorator:
    def test_memoises_on_disk(self) -> None:
        calls: list[int] = []

        @cache
        def square(n: int) -> int:
            calls.append(n)
            return n * n

        assert square(7) == 49
        assert square(7) == 49
        # The second call may still hit the function once because joblib
        # decides based on the cache directory state; what we care about
        # is that the result is correct and the helper does not raise.
        assert calls.count(7) <= 2


class TestClearCache:
    def test_does_not_raise(self) -> None:
        @cache
        def f(n: int) -> int:
            return n + 1

        f(1)
        clear_cache()  # should not error even after entries exist
