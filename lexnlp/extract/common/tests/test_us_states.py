"""Tests for :mod:`lexnlp.extract.common.us_states`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.us_states import (
    StateInfo,
    all_state_abbreviations,
    all_state_names,
    is_us_state,
    lookup_state,
    normalize_state,
    state_abbr_to_name,
    state_name_to_abbr,
)


class TestLookupState:
    def test_full_name(self) -> None:
        info = lookup_state("California")
        assert isinstance(info, StateInfo)
        assert info.abbr == "CA"
        assert info.fips == "06"
        assert info.is_territory is False

    def test_abbreviation_lowercase(self) -> None:
        info = lookup_state("ca")
        assert info is not None
        assert info.name == "California"

    def test_territory_flag(self) -> None:
        info = lookup_state("Puerto Rico")
        assert info is not None
        assert info.is_territory is True

    def test_unknown_returns_none(self) -> None:
        assert lookup_state("Atlantis") is None

    def test_empty_returns_none(self) -> None:
        assert lookup_state("") is None

    def test_strips_trailing_period(self) -> None:
        # Trailing period must not crash and "CA." must resolve to California.
        info = lookup_state("CA.")
        assert info is not None
        assert info.abbr == "CA"


class TestNormalizeState:
    def test_returns_abbreviation(self) -> None:
        assert normalize_state("Texas") == "TX"

    def test_idempotent_on_abbreviation(self) -> None:
        assert normalize_state("tx") == "TX"

    def test_unknown_returns_none(self) -> None:
        assert normalize_state("Gondor") is None


class TestIsUsState:
    def test_recognises_state(self) -> None:
        assert is_us_state("New York")

    def test_rejects_city(self) -> None:
        assert not is_us_state("Paris")


class TestMappings:
    def test_name_to_abbr_has_50_plus_territories(self) -> None:
        mapping = state_name_to_abbr()
        assert len(mapping) >= 50
        assert mapping["CALIFORNIA"] == "CA"

    def test_abbr_to_name_has_50_plus(self) -> None:
        mapping = state_abbr_to_name()
        assert len(mapping) >= 50
        assert mapping["CA"] == "California"

    def test_abbr_set_includes_territories(self) -> None:
        abbrs = all_state_abbreviations()
        assert "CA" in abbrs
        assert "PR" in abbrs

    def test_name_set_upper_case(self) -> None:
        names = all_state_names()
        assert "CALIFORNIA" in names
