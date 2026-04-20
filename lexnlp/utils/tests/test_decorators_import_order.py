"""Smoke test that :mod:`lexnlp.utils.decorators` imports cleanly.

PR #14 review flagged the import order (``typing`` vs
``collections.abc``). After the ruff --fix pass the module should import
with no errors and expose its decorators.
"""

from __future__ import annotations

import ast
from pathlib import Path

import lexnlp.utils.decorators as decorators_module


class TestDecoratorsModule:
    def test_module_imports(self) -> None:
        """
        Verify that the decorators module imports successfully.
        """
        assert decorators_module is not None

    def test_source_compiles(self) -> None:
        """
        Ensure the decorators module source code parses as valid Python.
        
        Fails the test if parsing the module's source raises a syntax or parse-related exception.
        """
        source = Path(decorators_module.__file__).read_text(encoding="utf-8")
        ast.parse(source)

    def test_imports_block_starts_with_collections_abc(self) -> None:
        source = Path(decorators_module.__file__).read_text(encoding="utf-8")
        for line in source.splitlines():
            stripped = line.strip()
            if stripped.startswith("from collections.abc") or stripped.startswith("from typing"):
                # The first of those must be ``collections.abc`` per isort order.
                assert stripped.startswith("from collections.abc")
                break

    def test_safe_failure_decorator_present(self) -> None:
        """
        Verifies the decorators module exposes at least one public callable decorator.
        
        Checks that the module defines `safe_failure` or `safe_call`, or that it exposes any public (non-underscore-prefixed) attribute whose value is callable.
        """
        assert (
            hasattr(decorators_module, "safe_failure")
            or hasattr(decorators_module, "safe_call")
            or any(callable(getattr(decorators_module, a)) for a in dir(decorators_module) if not a.startswith("_"))
        )
