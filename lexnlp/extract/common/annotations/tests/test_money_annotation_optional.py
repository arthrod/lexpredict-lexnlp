"""Tests for :class:`MoneyAnnotation` Optional field cleanup."""

from __future__ import annotations

from decimal import Decimal

from lexnlp.extract.common.annotations.money_annotation import MoneyAnnotation


class TestMoneyAnnotation:
    def test_required_only(self) -> None:
        ann = MoneyAnnotation(coords=(0, 3))
        assert ann.coords == (0, 3)

    def test_amount_store(self) -> None:
        ann = MoneyAnnotation(coords=(0, 6), amount=Decimal("1234.56"))
        assert ann.amount == Decimal("1234.56")

    def test_default_amount_is_none(self) -> None:
        ann = MoneyAnnotation(coords=(0, 1))
        assert ann.amount is None
