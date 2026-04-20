"""Tests for the implicit-Optional fix on ``_get_courts.text_languages``.

PR #14 review required ``text_languages: list[str] | None = None`` for
consistency with the Spanish version. We inspect the signature because
actually running ``_get_courts`` requires the (large) court dictionaries.
"""

from __future__ import annotations

import inspect

from lexnlp.extract.en.courts import _get_courts


class TestGetCourtsSignature:
    def test_text_languages_default_is_none(self) -> None:
        """
        Verify that the `_get_courts` function's `text_languages` parameter has a default value of `None`.
        """
        sig = inspect.signature(_get_courts)
        assert sig.parameters["text_languages"].default is None

    def test_priority_default_is_false(self) -> None:
        sig = inspect.signature(_get_courts)
        assert sig.parameters["priority"].default is False

    def test_simplified_normalization_default_is_false(self) -> None:
        sig = inspect.signature(_get_courts)
        assert sig.parameters["simplified_normalization"].default is False
