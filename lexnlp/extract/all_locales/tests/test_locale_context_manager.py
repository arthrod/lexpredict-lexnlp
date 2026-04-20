"""Tests for ``LocaleContextManager.__enter__`` return-type fix.

PR #14 review pointed out ``__enter__`` was annotated ``str | str`` (redundant)
and could implicitly return ``None`` on ``locale.Error``. The new signature
is ``str | None`` with an explicit ``return None`` inside the ``except``
block, which this test exercises.
"""

from __future__ import annotations

import locale

import pytest

from lexnlp.extract.all_locales.languages import LocaleContextManager


class TestLocaleContextManager:
    def test_invalid_locale_returns_none(self) -> None:
        cm = LocaleContextManager(locale.LC_ALL, "zz_ZZ.INVALID")
        assert cm.__enter__() is None
        cm.__exit__(None, None, None)

    def test_context_manager_protocol(self) -> None:
        """
        Verify that LocaleContextManager binds None to the context variable when given an invalid locale.
        
        Uses a `with` statement to exercise the context manager protocol and asserts the value bound by `as` is `None`.
        """
        with LocaleContextManager(locale.LC_ALL, "zz_ZZ.INVALID") as value:
            # With an invalid locale, ``value`` is ``None`` by contract.
            assert value is None

    def test_category_and_locale_stored(self) -> None:
        cm = LocaleContextManager(locale.LC_ALL, "en_US.UTF-8")
        assert cm.category == locale.LC_ALL
        assert cm.locale == "en_US.UTF-8"

    def test_original_locale_snapshot_is_sequence(self) -> None:
        cm = LocaleContextManager(locale.LC_ALL, "en_US.UTF-8")
        # ``locale.getlocale`` returns a 2-tuple; keep that contract.
        assert isinstance(cm._original_locale, tuple)

    @pytest.mark.parametrize("lang_code", ["zz_NOPE.X", "Not-a-locale", ""])
    def test_every_invalid_locale_is_tolerated(self, lang_code: str) -> None:
        cm = LocaleContextManager(locale.LC_ALL, lang_code)
        cm.__enter__()  # must not raise
        cm.__exit__(None, None, None)
