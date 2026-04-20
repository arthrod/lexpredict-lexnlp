"""Tests for :class:`RatioAnnotation` Optional field cleanup."""

from __future__ import annotations

from decimal import Decimal

from lexnlp.extract.common.annotations.ratio_annotation import RatioAnnotation


class TestRatioAnnotationConstruction:
    def test_required_only(self) -> None:
        ann = RatioAnnotation(coords=(0, 5))
        assert ann.coords == (0, 5)

    def test_left_right_ratio(self) -> None:
        ann = RatioAnnotation(
            coords=(0, 9),
            left=Decimal("2"),
            right=Decimal("3"),
            ratio=Decimal("0.6666"),
        )
        assert ann.left == Decimal("2")
        assert ann.right == Decimal("3")

    def test_none_ratio_fields_are_valid(self) -> None:
        ann = RatioAnnotation(coords=(0, 1), left=None, right=None, ratio=None)
        assert ann.left is None
