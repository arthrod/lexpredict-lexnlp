"""Tests for :mod:`lexnlp.extract.common.countries`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.countries import (
    CountryInfo,
    currency_codes,
    fuzzy_country,
    is_currency_code,
    is_language_code,
    language_codes,
    lookup_country,
)


class TestLookupCountry:
    def test_alpha_2(self) -> None:
        info = lookup_country("US")
        assert isinstance(info, CountryInfo)
        assert info.alpha_3 == "USA"
        assert info.name == "United States"

    def test_alpha_3(self) -> None:
        info = lookup_country("FRA")
        assert info is not None
        assert info.alpha_2 == "FR"

    def test_name_case_insensitive(self) -> None:
        info = lookup_country("germany")
        assert info is not None
        assert info.alpha_2 == "DE"

    def test_unknown_returns_none(self) -> None:
        assert lookup_country("Narnia") is None

    def test_empty_returns_none(self) -> None:
        assert lookup_country("") is None


class TestFuzzyCountry:
    def test_multiple_matches_when_requested(self) -> None:
        matches = fuzzy_country("United", max_results=3)
        names = [m.name for m in matches]
        # Some variation of "United" exists in multiple names.
        assert any("United" in n for n in names)

    def test_empty_returns_empty_tuple(self) -> None:
        assert fuzzy_country("") == ()

    def test_no_match_returns_empty_tuple(self) -> None:
        assert fuzzy_country("Valyria") == ()


class TestCurrencyCodes:
    def test_has_usd(self) -> None:
        assert "USD" in currency_codes()
        assert is_currency_code("usd")

    def test_rejects_unknown(self) -> None:
        assert not is_currency_code("XYZ")

    def test_empty_string(self) -> None:
        assert not is_currency_code("")


class TestLanguageCodes:
    def test_has_en(self) -> None:
        assert "en" in language_codes()
        assert is_language_code("EN")

    def test_rejects_unknown(self) -> None:
        assert not is_language_code("zz")
