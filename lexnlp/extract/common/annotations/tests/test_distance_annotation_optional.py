"""Tests for :class:`DistanceAnnotation` Optional field cleanup."""

from __future__ import annotations

from decimal import Decimal

from lexnlp.extract.common.annotations.distance_annotation import DistanceAnnotation


class TestDistanceAnnotation:
    def test_required_only(self) -> None:
        ann = DistanceAnnotation(coords=(0, 3))
        assert ann.coords == (0, 3)

    def test_amount_store(self) -> None:
        ann = DistanceAnnotation(coords=(0, 5), amount=Decimal("500"))
        assert ann.amount == Decimal("500")

    def test_distance_type_optional(self) -> None:
        ann = DistanceAnnotation(coords=(0, 1), distance_type="km")
        assert ann.distance_type == "km"
