"""Regression test for the ``date | None = None`` assignment bug.

Ruff's over-eager auto-fix once rewrote the ``date = None`` reset inside an
``except:`` clause to ``date | None = None`` (invalid syntax). The fix
restores the plain assignment with a specific ``except Exception:``. This
test simply imports the module and compiles it from source, which is the
cheapest possible regression check.
"""

from __future__ import annotations

import ast
from pathlib import Path

import lexnlp.extract.en.dates as dates_module


class TestDatesModuleCompiles:
    def test_module_imports(self) -> None:
        assert dates_module is not None

    def test_module_source_is_valid_python(self) -> None:
        """
        Ensure the dates module's source file is valid Python syntax.

        Reads the module file referenced by dates_module.__file__ and parses its contents with the AST parser; a SyntaxError will be raised if the source is not valid Python.
        """
        source = Path(dates_module.__file__).read_text(encoding="utf-8")
        ast.parse(source)  # raises SyntaxError on regression

    def test_get_month_by_name_present(self) -> None:
        mapping = dates_module.get_month_by_name()
        assert mapping["january"] == 1
        assert mapping["dec"] == 12
