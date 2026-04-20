"""Tests for :class:`PercentAnnotation` Optional field cleanup."""

from __future__ import annotations

from decimal import Decimal

from lexnlp.extract.common.annotations.percent_annotation import PercentAnnotation


class TestPercentAnnotation:
    def test_constructs_with_only_coords(self) -> None:
        ann = PercentAnnotation(coords=(0, 3))
        assert ann.coords == (0, 3)

    def test_amount_and_fraction_store(self) -> None:
        ann = PercentAnnotation(coords=(0, 5), amount=Decimal("12.5"), fraction=Decimal("0.125"))
        assert ann.amount == Decimal("12.5")
        assert ann.fraction == Decimal("0.125")

    def test_default_fraction_is_none(self) -> None:
        ann = PercentAnnotation(coords=(0, 3))
        assert ann.fraction is None
