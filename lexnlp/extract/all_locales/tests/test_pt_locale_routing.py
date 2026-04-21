"""Tests for Portuguese locale routing in all_locales dispatchers.

PR added LANG_PT.code to ROUTINE_BY_LOCALE in:
- lexnlp.extract.all_locales.copyrights
- lexnlp.extract.all_locales.dates
- lexnlp.extract.all_locales.definitions

These tests verify the routing keys exist without running the full PT
extraction stack (which requires language models / NLTK data).

Requires NLTK (and the full LexNLP extraction stack) to import the locale
dispatchers. Tests are skipped automatically when NLTK is not installed.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import pytest

# The all_locales dispatcher modules import from lexnlp.extract.en, which
# requires NLTK. Skip all tests in this file when NLTK is not installed.
pytest.importorskip("nltk", reason="NLTK required for all_locales dispatchers")

from lexnlp.extract.all_locales.languages import LANG_DE, LANG_EN, LANG_PT


# ---------------------------------------------------------------------------
# copyrights.py ROUTINE_BY_LOCALE
# ---------------------------------------------------------------------------


class TestCopyrightsRoutineByLocale:
    def test_lang_pt_code_present(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert LANG_PT.code in ROUTINE_BY_LOCALE

    def test_lang_en_code_still_present(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert LANG_EN.code in ROUTINE_BY_LOCALE

    def test_lang_de_code_still_present(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert LANG_DE.code in ROUTINE_BY_LOCALE

    def test_routine_by_locale_has_three_entries(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert len(ROUTINE_BY_LOCALE) == 3

    def test_pt_routine_is_callable(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        routine = ROUTINE_BY_LOCALE[LANG_PT.code]
        assert callable(routine)

    def test_en_and_pt_routines_are_distinct(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE[LANG_EN.code] is not ROUTINE_BY_LOCALE[LANG_PT.code]

    def test_de_and_pt_routines_are_distinct(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE[LANG_DE.code] is not ROUTINE_BY_LOCALE[LANG_PT.code]


# ---------------------------------------------------------------------------
# dates.py ROUTINE_BY_LOCALE
# ---------------------------------------------------------------------------


class TestDatesRoutineByLocale:
    def test_lang_pt_code_present(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert LANG_PT.code in ROUTINE_BY_LOCALE

    def test_lang_en_code_still_present(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert LANG_EN.code in ROUTINE_BY_LOCALE

    def test_lang_de_code_still_present(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert LANG_DE.code in ROUTINE_BY_LOCALE

    def test_routine_by_locale_has_three_entries(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert len(ROUTINE_BY_LOCALE) == 3

    def test_pt_routine_is_callable(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        routine = ROUTINE_BY_LOCALE[LANG_PT.code]
        assert callable(routine)

    def test_en_and_pt_routines_are_distinct(self) -> None:
        from lexnlp.extract.all_locales.dates import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE[LANG_EN.code] is not ROUTINE_BY_LOCALE[LANG_PT.code]


# ---------------------------------------------------------------------------
# definitions.py ROUTINE_BY_LOCALE
# ---------------------------------------------------------------------------


class TestDefinitionsRoutineByLocale:
    def test_lang_pt_code_present(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert LANG_PT.code in ROUTINE_BY_LOCALE

    def test_lang_en_code_still_present(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert LANG_EN.code in ROUTINE_BY_LOCALE

    def test_lang_de_code_still_present(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert LANG_DE.code in ROUTINE_BY_LOCALE

    def test_routine_by_locale_has_three_entries(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert len(ROUTINE_BY_LOCALE) == 3

    def test_pt_routine_is_callable(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        routine = ROUTINE_BY_LOCALE[LANG_PT.code]
        assert callable(routine)

    def test_en_and_pt_routines_are_distinct(self) -> None:
        from lexnlp.extract.all_locales.definitions import ROUTINE_BY_LOCALE

        assert ROUTINE_BY_LOCALE[LANG_EN.code] is not ROUTINE_BY_LOCALE[LANG_PT.code]


# ---------------------------------------------------------------------------
# Locale object routing (integration: Locale('pt-BR').language == 'pt')
# ---------------------------------------------------------------------------


class TestLocaleObjectPtRouting:
    def test_pt_br_locale_language_is_pt(self) -> None:
        from lexnlp.extract.all_locales.languages import Locale

        loc = Locale("pt-BR")
        assert loc.language == "pt"
        assert loc.language == LANG_PT.code

    def test_pt_locale_language_is_pt(self) -> None:
        from lexnlp.extract.all_locales.languages import Locale

        loc = Locale("pt")
        assert loc.language == "pt"

    def test_pt_br_language_matches_routine_key(self) -> None:
        from lexnlp.extract.all_locales.copyrights import ROUTINE_BY_LOCALE
        from lexnlp.extract.all_locales.languages import Locale

        loc = Locale("pt-BR")
        assert loc.language in ROUTINE_BY_LOCALE

    def test_pt_language_key_is_exactly_two_chars(self) -> None:
        assert len(LANG_PT.code) == 2