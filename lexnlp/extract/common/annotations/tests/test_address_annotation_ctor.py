"""Regression test for the ``__int__`` → ``__init__`` typo fix.

PR #14 review (coderabbit) flagged that
:class:`AddressAnnotation.__int__` was a broken initializer: instances
never had their parent class wired up, so ``text`` / ``coords`` were
silently lost. This test proves the fixed class now carries its data.
"""

from __future__ import annotations

from lexnlp.extract.common.annotations.address_annotation import AddressAnnotation


class TestAddressAnnotationInit:
    def test_constructor_stores_coords(self) -> None:
        ann = AddressAnnotation(coords=(10, 25), text="221B Baker Street")
        assert ann.coords == (10, 25)

    def test_constructor_stores_text(self) -> None:
        ann = AddressAnnotation(coords=(0, 4), text="1600 Pennsylvania Ave")
        assert ann.text == "1600 Pennsylvania Ave"

    def test_default_locale_is_en(self) -> None:
        ann = AddressAnnotation(coords=(0, 1), text="x")
        assert ann.locale == "en"

    def test_explicit_locale_propagates(self) -> None:
        ann = AddressAnnotation(coords=(0, 1), text="x", locale="de")
        assert ann.locale == "de"

    def test_record_type_is_address(self) -> None:
        """``record_type`` must be a class attribute, not a constructor arg."""
        ann = AddressAnnotation(coords=(0, 1), text="x")
        assert ann.record_type == "address"

    def test_get_cite_value_parts_echoes_text(self) -> None:
        """
        Verify that get_cite_value_parts returns a single-item list containing the annotation's text.
        """
        ann = AddressAnnotation(coords=(0, 4), text="echo")
        assert ann.get_cite_value_parts() == ["echo"]

    def test_dictionary_values_exposes_text(self) -> None:
        ann = AddressAnnotation(coords=(0, 4), text="echo")
        payload = ann.get_dictionary_values()
        assert payload["tags"]["Extracted Entity Text"] == "echo"
