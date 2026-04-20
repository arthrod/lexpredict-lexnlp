"""Tests for :class:`DurationAnnotation` signature after Optional cleanup.

PR #14 review required replacing implicit-Optional defaults with explicit
``T | None`` unions. This test instantiates the annotation with and without
optional fields to ensure both paths still work.
"""

from __future__ import annotations

from decimal import Decimal

from lexnlp.extract.common.annotations.duration_annotation import DurationAnnotation


class TestDurationAnnotationConstruction:
    def test_required_fields_only(self) -> None:
        ann = DurationAnnotation(coords=(0, 5))
        assert ann.coords == (0, 5)
        assert ann.amount is None
        assert ann.prefix is None

    def test_all_optional_fields(self) -> None:
        ann = DurationAnnotation(
            coords=(0, 10),
            amount=Decimal("2"),
            prefix="at least",
            duration_days=Decimal("730"),
            duration_type="years",
            duration_type_en="years",
            is_complex=False,
            value_dict={"raw": "2 years"},
        )
        assert ann.amount == Decimal("2")
        assert ann.duration_type == "years"
        assert ann.value_dict == {"raw": "2 years"}

    def test_default_locale_is_en(self) -> None:
        ann = DurationAnnotation(coords=(0, 1))
        assert ann.locale == "en"

    def test_text_defaults_to_none(self) -> None:
        ann = DurationAnnotation(coords=(0, 1))
        # text is explicitly typed ``str | None`` via the Optional fixes.
        assert ann.text is None or ann.text == ""
