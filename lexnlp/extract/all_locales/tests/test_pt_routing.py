"""Tests for Portuguese (pt) locale routing in all_locales dispatchers.

PR added ``LANG_PT`` to the ``ROUTINE_BY_LOCALE`` dictionaries in:
- :mod:`lexnlp.extract.all_locales.copyrights`
- :mod:`lexnlp.extract.all_locales.dates`
- :mod:`lexnlp.extract.all_locales.definitions`

These tests verify that:
* The 'pt' key is present in each dispatcher's ``ROUTINE_BY_LOCALE``.
* A 'pt' locale routes to the Portuguese extractor (not the fallback).
* Unknown locales fall back to the English extractor.
* The registered routines are callable.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# copyrights dispatcher
# ---------------------------------------------------------------------------


class TestCopyrightsRoutineByLocale:
    def test_pt_key_registered(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert "pt" in ROUTINE_BY_LOCALE

    def test_en_key_registered(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert "en" in ROUTINE_BY_LOCALE

    def test_de_key_registered(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert "de" in ROUTINE_BY_LOCALE

    def test_pt_routine_is_callable(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert callable(ROUTINE_BY_LOCALE["pt"])

    def test_pt_routine_differs_from_en_routine(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE["pt"] is not ROUTINE_BY_LOCALE["en"]

    def test_pt_routine_differs_from_de_routine(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE["pt"] is not ROUTINE_BY_LOCALE["de"]

    def test_three_locales_registered(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert set(ROUTINE_BY_LOCALE.keys()) >= {"en", "de", "pt"}


class TestCopyrightsGetAnnotationsRouting:
    """get_copyright_annotations routes 'pt' locale to the PT extractor."""

    def test_pt_locale_calls_pt_routine(self) -> None:
        """
        Verifies that requesting annotations with the "pt" locale dispatches to the Portuguese routine.
        
        Patches ROUTINE_BY_LOCALE so the "pt" key maps to a mock, calls the dispatcher with locale "pt" and sample text, and asserts the Portuguese routine mock was invoked exactly once.
        """
        from lexnlp.extract.all_locales import copyrights as mod

        mock_pt = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"pt": mock_pt}):
            list(mod.get_copyright_annotations("pt", "some text"))
        mock_pt.assert_called_once()

    def test_pt_br_locale_calls_pt_routine(self) -> None:
        """'pt-BR' should route to the 'pt' routine (language prefix extracted)."""
        from lexnlp.extract.all_locales import copyrights as mod

        mock_pt = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"pt": mock_pt}):
            list(mod.get_copyright_annotations("pt-BR", "some text"))
        mock_pt.assert_called_once()

    def test_unknown_locale_falls_back_to_en(self) -> None:
        """An unregistered locale code should fall back to the EN routine."""
        from lexnlp.extract.all_locales import copyrights as mod

        mock_en = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"en": mock_en}):
            list(mod.get_copyright_annotations("xx", "some text"))
        mock_en.assert_called_once()

    def test_en_locale_calls_en_routine(self) -> None:
        from lexnlp.extract.all_locales import copyrights as mod

        mock_en = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"en": mock_en}):
            list(mod.get_copyright_annotations("en", "some text"))
        mock_en.assert_called_once()


# ---------------------------------------------------------------------------
# dates dispatcher
# ---------------------------------------------------------------------------


class TestDatesRoutineByLocale:
    def test_pt_key_registered(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert "pt" in ROUTINE_BY_LOCALE

    def test_en_key_registered(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert "en" in ROUTINE_BY_LOCALE

    def test_de_key_registered(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert "de" in ROUTINE_BY_LOCALE

    def test_pt_routine_is_callable(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert callable(ROUTINE_BY_LOCALE["pt"])

    def test_pt_routine_differs_from_en_routine(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE["pt"] is not ROUTINE_BY_LOCALE["en"]

    def test_three_locales_registered(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert set(ROUTINE_BY_LOCALE.keys()) >= {"en", "de", "pt"}


class TestDatesGetAnnotationsRouting:
    """get_date_annotations routes 'pt' locale to the PT extractor."""

    def test_pt_locale_calls_pt_routine(self) -> None:
        from lexnlp.extract.all_locales import dates as mod

        mock_pt = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"pt": mock_pt}):
            list(mod.get_date_annotations("pt", "15 de março de 2024"))
        mock_pt.assert_called_once()

    def test_pt_br_locale_calls_pt_routine(self) -> None:
        from lexnlp.extract.all_locales import dates as mod

        mock_pt = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"pt": mock_pt}):
            list(mod.get_date_annotations("pt-BR", "15 de março de 2024"))
        mock_pt.assert_called_once()

    def test_unknown_locale_falls_back_to_en(self) -> None:
        from lexnlp.extract.all_locales import dates as mod

        mock_en = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"en": mock_en}):
            list(mod.get_date_annotations("zz", "some text"))
        mock_en.assert_called_once()

    def test_de_locale_calls_de_routine(self) -> None:
        from lexnlp.extract.all_locales import dates as mod

        mock_de = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"de": mock_de}):
            list(mod.get_date_annotations("de", "some text"))
        mock_de.assert_called_once()


# ---------------------------------------------------------------------------
# definitions dispatcher
# ---------------------------------------------------------------------------


class TestDefinitionsRoutineByLocale:
    def test_pt_key_registered(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert "pt" in ROUTINE_BY_LOCALE

    def test_en_key_registered(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert "en" in ROUTINE_BY_LOCALE

    def test_de_key_registered(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert "de" in ROUTINE_BY_LOCALE

    def test_pt_routine_is_callable(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert callable(ROUTINE_BY_LOCALE["pt"])

    def test_pt_routine_differs_from_en_routine(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE["pt"] is not ROUTINE_BY_LOCALE["en"]

    def test_three_locales_registered(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert set(ROUTINE_BY_LOCALE.keys()) >= {"en", "de", "pt"}


class TestDefinitionsGetAnnotationsRouting:
    """get_definition_annotations routes 'pt' locale to the PT extractor."""

    def test_pt_locale_calls_pt_routine(self) -> None:
        from lexnlp.extract.all_locales import definitions as mod

        mock_pt = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"pt": mock_pt}):
            list(mod.get_definition_annotations("pt", "X significa Y"))
        mock_pt.assert_called_once()

    def test_pt_br_locale_calls_pt_routine(self) -> None:
        from lexnlp.extract.all_locales import definitions as mod

        mock_pt = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"pt": mock_pt}):
            list(mod.get_definition_annotations("pt-BR", "X significa Y"))
        mock_pt.assert_called_once()

    def test_unknown_locale_falls_back_to_en(self) -> None:
        from lexnlp.extract.all_locales import definitions as mod

        mock_en = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"en": mock_en}):
            list(mod.get_definition_annotations("zz", "some text"))
        mock_en.assert_called_once()

    def test_en_locale_calls_en_routine(self) -> None:
        from lexnlp.extract.all_locales import definitions as mod

        mock_en = MagicMock(return_value=iter([]))
        with patch.dict(mod.ROUTINE_BY_LOCALE, {"en": mock_en}):
            list(mod.get_definition_annotations("en", "some text"))
        mock_en.assert_called_once()


# ---------------------------------------------------------------------------
# Cross-dispatcher consistency: all three have the same set of locale keys
# ---------------------------------------------------------------------------


class TestAllDispatchersSameLocales:
    def test_all_dispatchers_have_pt(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE as cr
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE as dr
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE as dfr

        assert "pt" in cr
        assert "pt" in dr
        assert "pt" in dfr

    def test_all_dispatchers_have_en(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE as cr
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE as dr
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE as dfr

        assert "en" in cr
        assert "en" in dr
        assert "en" in dfr

    def test_all_dispatchers_have_de(self) -> None:
        """
        Assert that the German locale key ("de") is registered in the ROUTINE_BY_LOCALE mapping of all three dispatchers.
        
        Checks that the `ROUTINE_BY_LOCALE` dictionaries in the copyrights, dates,
        and definitions dispatchers each contain the key "de".
        """
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE as cr
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE as dr
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE as dfr

        assert "de" in cr
        assert "de" in dr
        assert "de" in dfr