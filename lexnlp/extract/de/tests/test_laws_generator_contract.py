"""Regression test for ``get_law_annotations`` generator contract.

Before the PR fix, ``get_law_annotations`` returned ``None`` when the
module-level parser was unset. Because the function is declared as
``Generator[LawAnnotation]``, that fallback broke downstream callers like
``get_law_annotation_list`` which immediately pass the result to ``list()``.

The fix replaces ``return None`` with a bare ``return`` so the function
exits as an empty generator. This test mocks the module-level parser to
``None`` and confirms the helpers no longer explode.
"""

from __future__ import annotations

from unittest.mock import patch

from lexnlp.extract.de import laws


class TestLawAnnotationsEmptyGenerator:
    @patch.object(laws, "parser", new=None)
    def test_generator_is_empty_when_parser_missing(self) -> None:
        assert list(laws.get_law_annotations("some text")) == []

    @patch.object(laws, "parser", new=None)
    def test_list_helper_returns_empty_list(self) -> None:
        assert laws.get_law_annotation_list("some text") == []
