"""Constructor tests for annotation classes whose ``__init__`` docstrings
were reformatted in PR-16.

The PR fixed indentation in the docstrings of eleven annotation classes.
While the change is doc-only, we add constructor tests here to verify
that the ``__init__`` bodies still work correctly after the edit, and to
establish a stable baseline for future refactors.

Covered classes:
* ActAnnotation
* CitationAnnotation
* ConditionAnnotation
* ConstraintAnnotation
* CourtCitationAnnotation
* CusipAnnotation (constructor path only — field-level tests live in
  test_cusip_annotation_optional.py)
* DateAnnotation
* DefinitionAnnotation
* GeoAnnotation
* PhoneAnnotation
* RegulationAnnotation
* SsnAnnotation
"""

from __future__ import annotations

from datetime import date

from lexnlp.extract.common.annotations.act_annotation import ActAnnotation
from lexnlp.extract.common.annotations.citation_annotation import CitationAnnotation
from lexnlp.extract.common.annotations.condition_annotation import ConditionAnnotation
from lexnlp.extract.common.annotations.constraint_annotation import ConstraintAnnotation
from lexnlp.extract.common.annotations.court_citation_annotation import CourtCitationAnnotation
from lexnlp.extract.common.annotations.cusip_annotation import CusipAnnotation
from lexnlp.extract.common.annotations.date_annotation import DateAnnotation
from lexnlp.extract.common.annotations.definition_annotation import DefinitionAnnotation
from lexnlp.extract.common.annotations.geo_annotation import GeoAnnotation
from lexnlp.extract.common.annotations.phone_annotation import PhoneAnnotation
from lexnlp.extract.common.annotations.regulation_annotation import RegulationAnnotation
from lexnlp.extract.common.annotations.ssn_annotation import SsnAnnotation

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


# ---------------------------------------------------------------------------
# ActAnnotation
# ---------------------------------------------------------------------------


class TestActAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = ActAnnotation(coords=(0, 50))
        assert ann.coords == (0, 50)
        assert ann.locale == "en"
        assert ann.record_type == "act"

    def test_all_fields(self) -> None:
        ann = ActAnnotation(
            coords=(10, 80),
            locale="de",
            act_name="Securities Act",
            section="§ 12",
            year=1933,
            ambiguous=True,
            text="Securities Act § 12",
        )
        assert ann.act_name == "Securities Act"
        assert ann.section == "§ 12"
        assert ann.year == 1933
        assert ann.ambiguous is True
        assert ann.text == "Securities Act § 12"
        assert ann.locale == "de"

    def test_defaults_are_falsy(self) -> None:
        ann = ActAnnotation(coords=(0, 10))
        assert ann.act_name == ""
        assert ann.section == ""
        assert ann.year is None
        assert ann.ambiguous is False

    def test_get_cite_value_parts(self) -> None:
        ann = ActAnnotation(coords=(0, 5), act_name="APA", section="3", year=2001)
        parts = ann.get_cite_value_parts()
        assert "APA" in parts
        assert "3" in parts
        assert "2001" in parts

    def test_to_dictionary_legacy(self) -> None:
        ann = ActAnnotation(coords=(5, 20), act_name="ERISA", text="ERISA")
        d = ann.to_dictionary_legacy()
        assert d["location_start"] == 5
        assert d["location_end"] == 20
        assert d["act_name"] == "ERISA"


# ---------------------------------------------------------------------------
# CitationAnnotation
# ---------------------------------------------------------------------------


class TestCitationAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = CitationAnnotation(coords=(0, 100))
        assert ann.coords == (0, 100)
        assert ann.record_type == "citation"
        assert ann.locale == "en"

    def test_all_optional_fields_default_none(self) -> None:
        ann = CitationAnnotation(coords=(0, 1))
        assert ann.volume is None
        assert ann.volume_str is None
        assert ann.year is None
        assert ann.reporter is None
        assert ann.reporter_full_name is None
        assert ann.page is None
        assert ann.page_range is None
        assert ann.court is None
        assert ann.source is None
        assert ann.article is None
        assert ann.paragraph is None
        assert ann.subparagraph is None
        assert ann.letter is None
        assert ann.sentence is None
        assert ann.date is None
        assert ann.part is None
        assert ann.year_str is None

    def test_full_construction(self) -> None:
        ann = CitationAnnotation(
            coords=(10, 60),
            locale="en",
            text="410 U.S. 113",
            volume=410,
            reporter="U.S.",
            reporter_full_name="United States Reports",
            page=113,
            year=1973,
            court="SCOTUS",
        )
        assert ann.volume == 410
        assert ann.reporter == "U.S."
        assert ann.reporter_full_name == "United States Reports"
        assert ann.page == 113
        assert ann.year == 1973
        assert ann.court == "SCOTUS"

    def test_text_stored(self) -> None:
        ann = CitationAnnotation(coords=(0, 5), text="F.3d 200")
        assert ann.text == "F.3d 200"

    def test_to_dictionary_legacy_keys(self) -> None:
        ann = CitationAnnotation(coords=(0, 10), volume=1, reporter="F.3d", page=1)
        d = ann.to_dictionary_legacy()
        assert "volume" in d
        assert "reporter" in d
        assert "page" in d


# ---------------------------------------------------------------------------
# ConditionAnnotation
# ---------------------------------------------------------------------------


class TestConditionAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = ConditionAnnotation(coords=(0, 30))
        assert ann.coords == (0, 30)
        assert ann.record_type == "condition"
        assert ann.locale == "en"

    def test_optional_fields_default_none(self) -> None:
        ann = ConditionAnnotation(coords=(0, 1))
        assert ann.condition is None
        assert ann.pre is None
        assert ann.post is None
        assert ann.text is None

    def test_all_fields(self) -> None:
        ann = ConditionAnnotation(
            coords=(5, 40),
            locale="en",
            text="if party defaults",
            condition="if",
            pre="In the event that",
            post="then penalties apply",
        )
        assert ann.condition == "if"
        assert ann.pre == "In the event that"
        assert ann.post == "then penalties apply"

    def test_get_cite_value_parts(self) -> None:
        ann = ConditionAnnotation(
            coords=(0, 10), condition="unless", pre="prior", post="remedy"
        )
        parts = ann.get_cite_value_parts()
        assert "unless" in parts
        assert "prior" in parts
        assert "remedy" in parts


# ---------------------------------------------------------------------------
# ConstraintAnnotation
# ---------------------------------------------------------------------------


class TestConstraintAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = ConstraintAnnotation(coords=(0, 20))
        assert ann.coords == (0, 20)
        assert ann.record_type == "constraint"
        assert ann.locale == "en"

    def test_optional_fields_default_none(self) -> None:
        ann = ConstraintAnnotation(coords=(0, 1))
        assert ann.constraint is None
        assert ann.pre is None
        assert ann.post is None
        assert ann.text is None

    def test_all_fields(self) -> None:
        ann = ConstraintAnnotation(
            coords=(0, 30),
            locale="en",
            constraint="must not",
            pre="The party",
            post="exceed the limit",
            text="The party must not exceed the limit",
        )
        assert ann.constraint == "must not"
        assert ann.pre == "The party"
        assert ann.post == "exceed the limit"
        assert ann.text == "The party must not exceed the limit"

    def test_get_cite_value_parts_empty_defaults(self) -> None:
        ann = ConstraintAnnotation(coords=(0, 5))
        parts = ann.get_cite_value_parts()
        assert parts == ["", "", ""]


# ---------------------------------------------------------------------------
# CourtCitationAnnotation
# ---------------------------------------------------------------------------


class TestCourtCitationAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = CourtCitationAnnotation(coords=(0, 15))
        assert ann.coords == (0, 15)
        assert ann.record_type == "court citation"
        assert ann.locale == "en"

    def test_optional_fields_default_none(self) -> None:
        ann = CourtCitationAnnotation(coords=(0, 1))
        assert ann.short_name is None
        assert ann.translated_name is None
        assert ann.text is None

    def test_all_fields(self) -> None:
        ann = CourtCitationAnnotation(
            coords=(0, 50),
            locale="de",
            name="Bundesgerichtshof",
            short_name="BGH",
            text="BGH",
            translated_name="Federal Court of Justice",
        )
        assert ann.name == "Bundesgerichtshof"
        assert ann.short_name == "BGH"
        assert ann.translated_name == "Federal Court of Justice"
        assert ann.text == "BGH"
        assert ann.locale == "de"

    def test_get_cite_value_parts(self) -> None:
        ann = CourtCitationAnnotation(
            coords=(0, 10), name="Supreme Court", short_name="SC"
        )
        parts = ann.get_cite_value_parts()
        assert "Supreme Court" in parts
        assert "SC" in parts


# ---------------------------------------------------------------------------
# CusipAnnotation (additional constructor path)
# ---------------------------------------------------------------------------


class TestCusipAnnotationCtorExtended:
    """Supplements test_cusip_annotation_optional.py with fields added in PR-16."""

    def test_coords_stored(self) -> None:
        ann = CusipAnnotation(coords=(5, 14))
        assert ann.coords == (5, 14)

    def test_issuer_and_issue_id(self) -> None:
        ann = CusipAnnotation(
            coords=(0, 9), issuer_id="037833", issue_id="10", code="037833100"
        )
        assert ann.issuer_id == "037833"
        assert ann.issue_id == "10"
        assert ann.code == "037833100"

    def test_internal_flag(self) -> None:
        ann = CusipAnnotation(coords=(0, 9), internal=True)
        assert ann.internal is True

    def test_checksum(self) -> None:
        ann = CusipAnnotation(coords=(0, 9), checksum="0")
        assert ann.checksum == "0"


# ---------------------------------------------------------------------------
# DateAnnotation
# ---------------------------------------------------------------------------


class TestDateAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = DateAnnotation(coords=(0, 10))
        assert ann.coords == (0, 10)
        assert ann.record_type == "date"
        assert ann.locale == "en"

    def test_optional_fields_default_none(self) -> None:
        ann = DateAnnotation(coords=(0, 10))
        assert ann.date is None
        assert ann.score is None
        assert ann.text is None

    def test_all_fields(self) -> None:
        d = date(2024, 6, 1)
        ann = DateAnnotation(
            coords=(10, 30),
            locale="en",
            text="June 1, 2024",
            date=d,
            score=0.95,
        )
        assert ann.date == d
        assert ann.score == 0.95
        assert ann.text == "June 1, 2024"

    def test_get_cite_value_parts_with_date(self) -> None:
        d = date(2023, 12, 31)
        ann = DateAnnotation(coords=(0, 10), date=d)
        parts = ann.get_cite_value_parts()
        assert "2023-12-31" in parts[0]

    def test_get_cite_value_parts_no_date(self) -> None:
        ann = DateAnnotation(coords=(0, 10))
        parts = ann.get_cite_value_parts()
        assert parts == [""]


# ---------------------------------------------------------------------------
# DefinitionAnnotation
# ---------------------------------------------------------------------------


class TestDefinitionAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = DefinitionAnnotation(coords=(0, 20))
        assert ann.coords == (0, 20)
        assert ann.record_type == "definition"
        assert ann.locale == "en"

    def test_name_stored(self) -> None:
        ann = DefinitionAnnotation(coords=(0, 10), name="Agreement")
        assert ann.name == "Agreement"

    def test_text_defaults_none(self) -> None:
        ann = DefinitionAnnotation(coords=(0, 10))
        assert ann.text is None

    def test_all_fields(self) -> None:
        ann = DefinitionAnnotation(
            coords=(5, 25),
            locale="en",
            name="Effective Date",
            text="the date of full execution",
        )
        assert ann.name == "Effective Date"
        assert ann.text == "the date of full execution"

    def test_get_cite_value_parts(self) -> None:
        ann = DefinitionAnnotation(coords=(0, 5), name="Term")
        parts = ann.get_cite_value_parts()
        assert "Term" in parts


# ---------------------------------------------------------------------------
# GeoAnnotation
# ---------------------------------------------------------------------------


class TestGeoAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = GeoAnnotation(coords=(0, 15))
        assert ann.coords == (0, 15)
        assert ann.record_type == "geoentity"
        assert ann.locale == "en"

    def test_all_optional_fields_default_none(self) -> None:
        ann = GeoAnnotation(coords=(0, 1))
        assert ann.name is None
        assert ann.alias is None
        assert ann.name_en is None
        assert ann.source is None
        assert ann.entity_category is None
        assert ann.iso_3166_2 is None
        assert ann.iso_3166_3 is None
        assert ann.year is None
        assert ann.entity_id is None
        assert ann.entity_priority is None

    def test_all_fields(self) -> None:
        ann = GeoAnnotation(
            coords=(0, 7),
            locale="de",
            text="Germany",
            name="Deutschland",
            alias="Germany",
            name_en="Germany",
            source="geonames",
            entity_category="country",
            iso_3166_2="DE",
            iso_3166_3="DEU",
            year=None,
            entity_id=2921044,
            entity_priority=100,
        )
        assert ann.name == "Deutschland"
        assert ann.alias == "Germany"
        assert ann.name_en == "Germany"
        assert ann.iso_3166_2 == "DE"
        assert ann.iso_3166_3 == "DEU"
        assert ann.entity_id == 2921044
        assert ann.entity_priority == 100

    def test_to_dictionary_keys(self) -> None:
        ann = GeoAnnotation(
            coords=(0, 5),
            entity_id=1,
            entity_category="country",
            name_en="France",
            entity_priority=50,
        )
        d = ann.to_dictionary()
        assert "Entity ID" in d
        assert "Entity Category" in d
        assert "Entity Name" in d


# ---------------------------------------------------------------------------
# PhoneAnnotation
# ---------------------------------------------------------------------------


class TestPhoneAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = PhoneAnnotation(coords=(0, 14))
        assert ann.coords == (0, 14)
        assert ann.record_type == "phone"
        assert ann.locale == "en"

    def test_optional_fields_default_none(self) -> None:
        ann = PhoneAnnotation(coords=(0, 1))
        assert ann.phone is None
        assert ann.text is None

    def test_all_fields(self) -> None:
        ann = PhoneAnnotation(
            coords=(5, 19),
            locale="en",
            text="+1-800-555-1234",
            phone="+18005551234",
        )
        assert ann.phone == "+18005551234"
        assert ann.text == "+1-800-555-1234"

    def test_get_cite_value_parts(self) -> None:
        ann = PhoneAnnotation(coords=(0, 10), phone="+1234567890")
        parts = ann.get_cite_value_parts()
        assert "+1234567890" in parts


# ---------------------------------------------------------------------------
# RegulationAnnotation
# ---------------------------------------------------------------------------


class TestRegulationAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = RegulationAnnotation(coords=(0, 20))
        assert ann.coords == (0, 20)
        assert ann.record_type == "regulation"
        assert ann.locale == "en"

    def test_defaults(self) -> None:
        ann = RegulationAnnotation(coords=(0, 1))
        assert ann.name == ""
        assert ann.source == ""
        assert ann.country == ""
        assert ann.text is None

    def test_all_fields(self) -> None:
        ann = RegulationAnnotation(
            coords=(0, 30),
            locale="en",
            name="17 CFR § 240.10b-5",
            text="17 CFR § 240.10b-5",
            source="SEC",
            country="US",
        )
        assert ann.name == "17 CFR § 240.10b-5"
        assert ann.source == "SEC"
        assert ann.country == "US"
        assert ann.text == "17 CFR § 240.10b-5"

    def test_to_dictionary_legacy(self) -> None:
        ann = RegulationAnnotation(
            coords=(0, 10), name="§ 5", source="BaFin", text="§ 5"
        )
        d = ann.to_dictionary_legacy()
        assert d["regulation_type"] == "BaFin"
        assert d["regulation_code"] == "§ 5"
        assert d["regulation_text"] == "§ 5"

    def test_get_cite_value_parts(self) -> None:
        ann = RegulationAnnotation(
            coords=(0, 10), name="§ 12", source="BaFin", country="DE"
        )
        parts = ann.get_cite_value_parts()
        assert "DE" in parts
        assert "BaFin" in parts
        assert "§ 12" in parts


# ---------------------------------------------------------------------------
# SsnAnnotation
# ---------------------------------------------------------------------------


class TestSsnAnnotationCtor:
    def test_minimal_construction(self) -> None:
        ann = SsnAnnotation(coords=(0, 11))
        assert ann.coords == (0, 11)
        assert ann.record_type == "ssn"
        assert ann.locale == "en"

    def test_optional_fields_default_none(self) -> None:
        ann = SsnAnnotation(coords=(0, 1))
        assert ann.number is None
        assert ann.text is None

    def test_all_fields(self) -> None:
        ann = SsnAnnotation(
            coords=(5, 16),
            locale="en",
            text="123-45-6789",
            number="123-45-6789",
        )
        assert ann.number == "123-45-6789"
        assert ann.text == "123-45-6789"

    def test_get_cite_value_parts(self) -> None:
        ann = SsnAnnotation(coords=(0, 11), number="987-65-4321")
        parts = ann.get_cite_value_parts()
        assert "987-65-4321" in parts

    def test_locale_default(self) -> None:
        ann = SsnAnnotation(coords=(0, 11))
        assert ann.locale == "en"

    def test_custom_locale(self) -> None:
        ann = SsnAnnotation(coords=(0, 11), locale="de")
        assert ann.locale == "de"