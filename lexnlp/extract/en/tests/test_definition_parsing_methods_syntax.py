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
        """
        Ensure the target module's source file is valid Python syntax.
        
        Reads the module source from disk and attempts to parse it with the AST parser; a SyntaxError will be raised if the source is not syntactically valid.
        """
        source = Path(dpm.__file__).read_text(encoding="utf-8")
        ast.parse(source)

    def test_paren_quote_pattern_exists(self) -> None:
        """
        Verify that the module exports a non-empty string for `PAREN_QUOTE_PTN`.
        
        Asserts that `dpm.PAREN_QUOTE_PTN` is a `str` and contains at least one character.
        """
        assert isinstance(dpm.PAREN_QUOTE_PTN, str)
        assert dpm.PAREN_QUOTE_PTN  # non-empty

    def test_paren_pattern_exists(self) -> None:
        """
        Asserts that the module's PAREN_PTN export is a string.
        
        Raises:
            AssertionError: If `dpm.PAREN_PTN` is not an instance of `str`.
        """
        assert isinstance(dpm.PAREN_PTN, str)

    def test_anchor_quotes_pattern_exists(self) -> None:
        """
        Check that the ANCHOR_QUOTES_PTN constant in the definition_parsing_methods module is a string.
        
        Asserts that dpm.ANCHOR_QUOTES_PTN is an instance of `str`.
        """
        assert isinstance(dpm.ANCHOR_QUOTES_PTN, str)

    def test_anchor_subject_quotes_pattern_exists(self) -> None:
        assert isinstance(dpm.ANCHOR_SUBJECT_QUOTES_PTN, str)

    def test_patterns_contain_expected_markers(self) -> None:
        # Sanity: the f-string conversion should still interpolate MAX_TERM_CHARS.
        """
        Asserts that the PAREN_QUOTE_PTN pattern contains the textual value of MAX_TERM_CHARS.
        
        Raises:
        	AssertionError: If the string form of `dpm.MAX_TERM_CHARS` is not found in `dpm.PAREN_QUOTE_PTN`.
        """
        assert str(dpm.MAX_TERM_CHARS) in dpm.PAREN_QUOTE_PTN
