"""Additional tests for :mod:`lexnlp.extract.all_locales.languages`.

Supplements ``test_locale_context_manager.py`` and ``test_locales.py`` with
coverage of the parts that were not exercised in the primary suites:

* ``Language`` class: attributes and ``__str__``
* ``Locale`` class: ``get_locale()`` method, edge case inputs
* Module-level constants: ``LANG_EN``, ``LANG_DE``, ``LANG_ES``, ``LANGUAGES``,
  ``DEFAULT_LANGUAGE``
* ``LocaleContextManager.__exit__`` actually restores the original locale
"""

from __future__ import annotations

import locale

import pytest

from lexnlp.extract.all_locales.languages import (
    DEFAULT_LANGUAGE,
    LANG_DE,
    LANG_EN,
    LANG_ES,
    LANG_PT,
    LANGUAGES,
    Locale,
    LocaleContextManager,
)

try:
    from lexnlp.extract.all_locales.languages import Language
except ImportError:
    Language = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Language class
# ---------------------------------------------------------------------------


@pytest.mark.skipif(Language is None, reason="Language not importable")
class TestLanguageClass:
    def test_code_attribute(self) -> None:
        from lexnlp.extract.all_locales.languages import Language

        lang = Language("fr", "fra", "French")
        assert lang.code == "fr"

    def test_code_3_attribute(self) -> None:
        from lexnlp.extract.all_locales.languages import Language

        lang = Language("fr", "fra", "French")
        assert lang.code_3 == "fra"

    def test_title_attribute(self) -> None:
        from lexnlp.extract.all_locales.languages import Language

        lang = Language("fr", "fra", "French")
        assert lang.title == "French"

    def test_str_returns_code(self) -> None:
        from lexnlp.extract.all_locales.languages import Language

        lang = Language("de", "ger", "German")
        assert str(lang) == "de"

    def test_str_en(self) -> None:
        assert str(LANG_EN) == "en"

    def test_str_de(self) -> None:
        assert str(LANG_DE) == "de"

    def test_str_es(self) -> None:
        assert str(LANG_ES) == "es"


# ---------------------------------------------------------------------------
# Module-level Language constants
# ---------------------------------------------------------------------------


class TestLanguageConstants:
    def test_lang_en_code(self) -> None:
        assert LANG_EN.code == "en"

    def test_lang_en_code_3(self) -> None:
        assert LANG_EN.code_3 == "eng"

    def test_lang_de_code(self) -> None:
        assert LANG_DE.code == "de"

    def test_lang_de_code_3(self) -> None:
        assert LANG_DE.code_3 == "ger"

    def test_lang_es_code(self) -> None:
        assert LANG_ES.code == "es"

    def test_lang_es_code_3(self) -> None:
        assert LANG_ES.code_3 == "spa"

    def test_languages_list_contains_all_three(self) -> None:
        codes = {lang.code for lang in LANGUAGES}
        assert codes >= {"en", "de", "es"}

    def test_default_language_is_en(self) -> None:
        assert DEFAULT_LANGUAGE is LANG_EN

    def test_default_language_code(self) -> None:
        assert DEFAULT_LANGUAGE.code == "en"


# ---------------------------------------------------------------------------
# Locale class
# ---------------------------------------------------------------------------


class TestLocaleClass:
    def test_language_extracted_from_two_char_code(self) -> None:
        loc = Locale("en")
        assert loc.language == "en"

    def test_locale_code_uppercased(self) -> None:
        loc = Locale("en-us")
        assert loc.locale_code == "US"

    def test_language_lowercased(self) -> None:
        loc = Locale("EN-US")
        assert loc.language == "en"

    def test_locale_code_uses_language_when_no_region(self) -> None:
        # When only a language code is given (no region), locale_code == language.upper()
        loc = Locale("de")
        assert loc.locale_code == "DE"

    def test_get_locale_format(self) -> None:
        loc = Locale("en-US")
        assert loc.get_locale() == "en-US"

    def test_get_locale_with_underscore_input(self) -> None:
        loc = Locale("en_GB")
        # language is first 2 chars, locale_code is chars 3+
        result = loc.get_locale()
        # Should be in language-LOCALE_CODE format
        assert "-" in result

    def test_empty_locale_string(self) -> None:
        loc = Locale("")
        # Should not raise; language and locale_code will be empty strings
        assert loc.language == ""

    def test_slash_separator(self) -> None:
        loc = Locale("en/GB")
        assert loc.language == "en"
        # locale_code from position 3+ should be "GB" (upper)
        assert loc.locale_code == "GB"

    @pytest.mark.parametrize("raw,expected_lang,expected_locale", [
        ("de-DE", "de", "DE"),
        ("es-ES", "es", "ES"),
        ("en-AU", "en", "AU"),
        ("fr-CA", "fr", "CA"),
    ])
    def test_parametrized_locale_parsing(
        self, raw: str, expected_lang: str, expected_locale: str
    ) -> None:
        loc = Locale(raw)
        assert loc.language == expected_lang
        assert loc.locale_code == expected_locale


# ---------------------------------------------------------------------------
# LocaleContextManager.__exit__ restores the original locale
# ---------------------------------------------------------------------------


class TestLocaleContextManagerExit:
    def test_exit_restores_original_locale_after_invalid(self) -> None:
        original = locale.getlocale()
        with LocaleContextManager(locale.LC_ALL, "zz_ZZ.INVALID"):
            pass
        # After the context exits, the locale should be restored
        restored = locale.getlocale()
        assert restored == original

    def test_exit_restores_original_locale_after_valid(self) -> None:
        original = locale.getlocale()
        # Try a locale that may or may not be installed; either way exit must restore
        with LocaleContextManager(locale.LC_ALL, "en_US.UTF-8"):
            pass
        assert locale.getlocale() == original

    def test_can_nest_context_managers(self) -> None:
        """Nested managers should each restore the locale correctly."""
        original = locale.getlocale()
        with LocaleContextManager(locale.LC_ALL, "zz_ZZ.INVALID"):
            with LocaleContextManager(locale.LC_ALL, "zz_ZZ.INVALID_2"):
                pass
            # inner restored; outer should still be "invalid" setlocale state
        # After both exit, we should be back to original
        assert locale.getlocale() == original

    def test_enter_returns_none_on_invalid_locale(self) -> None:
        cm = LocaleContextManager(locale.LC_ALL, "zz_ZZ.GARBAGE")
        result = cm.__enter__()
        cm.__exit__(None, None, None)
        assert result is None

    def test_exit_called_manually_restores_locale(self) -> None:
        original = locale.getlocale()
        cm = LocaleContextManager(locale.LC_ALL, "zz_ZZ.INVALID")
        cm.__enter__()
        cm.__exit__(None, None, None)
        assert locale.getlocale() == original


# ---------------------------------------------------------------------------
# LANG_PT constant (added in this PR)
# ---------------------------------------------------------------------------


class TestLangPt:
    """Tests for the ``LANG_PT`` constant added alongside the Portuguese module."""

    def test_lang_pt_code(self) -> None:
        assert LANG_PT.code == "pt"

    def test_lang_pt_code_3(self) -> None:
        assert LANG_PT.code_3 == "por"

    def test_lang_pt_title(self) -> None:
        assert LANG_PT.title == "Portuguese"

    def test_lang_pt_str(self) -> None:
        assert str(LANG_PT) == "pt"

    def test_lang_pt_is_distinct_from_en(self) -> None:
        assert LANG_PT is not LANG_EN

    def test_lang_pt_is_distinct_from_de(self) -> None:
        assert LANG_PT is not LANG_DE

    def test_lang_pt_is_distinct_from_es(self) -> None:
        assert LANG_PT is not LANG_ES


class TestLanguagesListWithPt:
    """LANGUAGES now contains four entries including Portuguese."""

    def test_languages_list_has_four_entries(self) -> None:
        assert len(LANGUAGES) == 4

    def test_languages_list_contains_pt(self) -> None:
        codes = {lang.code for lang in LANGUAGES}
        assert "pt" in codes

    def test_languages_list_contains_en_de_es_pt(self) -> None:
        codes = {lang.code for lang in LANGUAGES}
        assert codes == {"en", "de", "es", "pt"}

    def test_lang_pt_identity_in_languages_list(self) -> None:
        """LANG_PT constant is the same object as the 'pt' entry in LANGUAGES."""
        pt_entries = [lang for lang in LANGUAGES if lang.code == "pt"]
        assert len(pt_entries) == 1
        assert pt_entries[0] is LANG_PT

    def test_languages_list_code_3_for_pt(self) -> None:
        pt_entry = next(lang for lang in LANGUAGES if lang.code == "pt")
        assert pt_entry.code_3 == "por"

    def test_default_language_is_still_en(self) -> None:
        """Adding LANG_PT must not change the DEFAULT_LANGUAGE."""
        assert DEFAULT_LANGUAGE is LANG_EN