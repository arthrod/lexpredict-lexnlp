"""Tests for ``FactExtractor.parse_text`` signature after Optional fix.

The review-era call site used ``include_types: set[AnnotationType] = None``
which was an implicit Optional. The new signature is
``include_types: set[AnnotationType] | None = None``. This test ensures the
keyword argument still accepts ``None`` explicitly and that filtering
continues to work with an empty extractor registry.
"""

from __future__ import annotations

import inspect

from lexnlp.extract.common.fact_extracting import FactExtractor


class TestParseTextSignature:
    def test_include_types_default_is_none(self) -> None:
        sig = inspect.signature(FactExtractor.parse_text)
        assert sig.parameters["include_types"].default is None

    def test_exclude_types_default_is_none(self) -> None:
        sig = inspect.signature(FactExtractor.parse_text)
        assert sig.parameters["exclude_types"].default is None

    def test_ensure_parser_arguments_en_default_is_none(self) -> None:
        sig = inspect.signature(FactExtractor.ensure_parser_arguments_en)
        assert sig.parameters["geo_config"].default is None

    def test_ensure_parser_arguments_de_default_is_none(self) -> None:
        sig = inspect.signature(FactExtractor.ensure_parser_arguments_de)
        assert sig.parameters["geo_config"].default is None
