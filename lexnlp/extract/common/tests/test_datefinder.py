__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import codecs
import datetime
import os
import time
from unittest import TestCase

from lexnlp.extract.all_locales.languages import Locale
from lexnlp.extract.common.date_parsing.datefinder import DateFinder


class TestDateFinder(TestCase):
    def test_parse_str(self):
        """
        Checks that DateFinder extracts at least one date-like string from a numeric, table-formatted multiline text.

        Uses a base date of January 1 of the current year and calls DateFinder.extract_date_strings(..., strict=False); the test asserts that the extractor returns at least one candidate.
        """
        text = """
        ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 -                     569                -                     15                  -                     -                     -                     -                     -                     -                     -                     -                     -                     +
 1,195             1,339             3,019             1,820             13,831
        """
        base_date = datetime.datetime.now().replace(day=1, month=1, hour=0, minute=0, second=0, microsecond=0)

        # Find potential dates
        date_finder = DateFinder(base_date=base_date)
        possible_dates = list(date_finder.extract_date_strings(text, strict=False))
        self.assertGreater(len(possible_dates), 0)

    def test_parse_time(self):
        """
        Measure that DateFinder.extract_date_strings parses a large test file within 15 seconds.

        Reads test_data/long_parsed_text.txt, creates a DateFinder with base_date set to January 1 of the current year at 00:00:00, runs extract_date_strings on the file content with strict=False, and asserts the operation completes in under 15 seconds.
        """
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = dir_path + "/../../../../test_data/long_parsed_text.txt"
        with codecs.open(file_path, "r", encoding="utf-8") as fr:
            text = fr.read()

        base_date = datetime.datetime.now().replace(day=1, month=1, hour=0, minute=0, second=0, microsecond=0)
        date_finder = DateFinder(base_date=base_date)
        t1 = time.time()
        _ = list(date_finder.extract_date_strings(text, strict=False))
        d1 = time.time() - t1
        self.assertLess(d1, 15)


class TestParseDateStringLocale(TestCase):
    """Direct unit coverage for ``DateFinder.parse_date_string`` branching on locale.

    The method's fallback chain changed multiple times during PR19 review;
    these tests pin the two major branches (no-locale vs. real-locale) so
    future edits can't silently re-break locale-aware parsing.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Fix the base date at 2000-01-01 so every dateparser call returns a
        deterministic value regardless of when the test runs."""
        cls.base_date = datetime.datetime(2000, 1, 1)
        cls.finder = DateFinder(base_date=cls.base_date)
        # All captures are accepted; the fallback chain only inspects it when
        # ``_find_and_replace`` needs to strip timezone / extra tokens.
        cls.empty_captures: dict[str, list] = {
            "delimiters": [],
            "extra_tokens": [],
            "digits": [],
            "time": [],
            "digits_modifier": [],
            "days": [],
            "months": [],
            "timezones": [],
            "time_periods": [],
            "hours": [],
            "minutes": [],
            "seconds": [],
            "microseconds": [],
        }

    def test_no_locale_parses_with_dateparser(self) -> None:
        """Without a locale, a well-formed date string parses via dateparser."""
        result = self.finder.parse_date_string("January 5, 2024", self.empty_captures, locale=None)
        self.assertIsNotNone(result)
        assert result is not None  # narrows type for the remaining asserts
        self.assertEqual(2024, result.year)
        self.assertEqual(1, result.month)
        self.assertEqual(5, result.day)

    def test_empty_locale_treated_as_no_locale(self) -> None:
        """``Locale("")`` — the default when callers don't pass anything — must
        behave exactly like ``locale=None`` so we don't try to look up the
        bogus ``'-'`` locale code that ``Locale("").get_locale()`` produces."""
        result = self.finder.parse_date_string("January 5, 2024", self.empty_captures, locale=Locale(""))
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(datetime.datetime(2024, 1, 5), result)

    def test_en_gb_locale_prefers_dmy(self) -> None:
        """``Locale("en-GB")`` should parse numeric ``dd/mm/yyyy`` as DMY,
        not MDY. This is the regression the PR19 review fixed — dateparser's
        locale-aware path must not fall through to the US-centric dateutil
        cleanup fallback."""
        result = self.finder.parse_date_string("09/12/2022", self.empty_captures, locale=Locale("en-GB"))
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(2022, result.year)
        self.assertEqual(12, result.month)
        self.assertEqual(9, result.day)

    def test_pt_br_locale_prefers_dmy(self) -> None:
        """Same DMY semantics for a second real locale — Portuguese (pt-BR)."""
        result = self.finder.parse_date_string("15/02/2020", self.empty_captures, locale=Locale("pt-BR"))
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(datetime.datetime(2020, 2, 15), result)

    def test_locale_unparseable_returns_none(self) -> None:
        """When a locale is supplied but neither the locale- nor language-only
        dateparser call can make sense of the input, the function returns
        ``None`` rather than falling through to the MDY dateutil fallback."""
        result = self.finder.parse_date_string("xxxxxxxxxx", self.empty_captures, locale=Locale("en-GB"))
        self.assertIsNone(result)
