"""Tests for :class:`CusipAnnotation` Optional field cleanup."""

from __future__ import annotations

from lexnlp.extract.common.annotations.cusip_annotation import CusipAnnotation


class TestCusipAnnotation:
    def test_required_only(self) -> None:
        ann = CusipAnnotation(coords=(0, 9))
        assert ann.coords == (0, 9)

    def test_all_optionals_default_none(self) -> None:
        ann = CusipAnnotation(coords=(0, 9))
        assert ann.code is None
        assert ann.internal is None
        assert ann.ppn is None
        assert ann.tba is None
        assert ann.checksum is None
        assert ann.issue_id is None
        assert ann.issuer_id is None

    def test_tba_accepts_dict(self) -> None:
        ann = CusipAnnotation(coords=(0, 9), tba={"details": True})
        assert ann.tba == {"details": True}
