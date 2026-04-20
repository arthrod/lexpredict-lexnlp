"""Regression tests for ``definition_parsing_methods.py`` syntax fix.

Gemini flagged four orphaned line continuations introduced during the
.format→f-string migration. Each orphaned ``\\`` was followed by an empty
line, which Python refuses to compile. This test asserts the module
both imports successfully and exposes the patterns it constructs.
"""

from __future__ import annotations

import ast
from pathlib import Path

import lexnlp.extract.en.definition_parsing_methods as dpm


class TestDefinitionParsingMethodsSyntax:
    def test_source_parses(self) -> None:
        source = Path(dpm.__file__).read_text(encoding="utf-8")
        ast.parse(source)

    def test_paren_quote_pattern_exists(self) -> None:
        assert isinstance(dpm.PAREN_QUOTE_PTN, str)
        assert dpm.PAREN_QUOTE_PTN  # non-empty

    def test_paren_pattern_exists(self) -> None:
        assert isinstance(dpm.PAREN_PTN, str)

    def test_anchor_quotes_pattern_exists(self) -> None:
        assert isinstance(dpm.ANCHOR_QUOTES_PTN, str)

    def test_anchor_subject_quotes_pattern_exists(self) -> None:
        assert isinstance(dpm.ANCHOR_SUBJECT_QUOTES_PTN, str)

    def test_patterns_contain_expected_markers(self) -> None:
        # Sanity: the f-string conversion should still interpolate MAX_TERM_CHARS.
        assert str(dpm.MAX_TERM_CHARS) in dpm.PAREN_QUOTE_PTN
