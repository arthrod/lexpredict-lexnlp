"""Tests for :mod:`lexnlp.extract.common.preprocessing.html_cleaner`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from lexnlp.extract.common.preprocessing.html_cleaner import (
    clean_html,
    extract_clauses,
    html_to_text,
)

SAMPLE = """
<html>
  <head>
    <style>body{color:red}</style>
    <script>alert(1)</script>
  </head>
  <body>
    <h1>Agreement</h1>
    <p>This Agreement is made on <strong>January 1, 2024</strong>.</p>
    <p>The parties agree to the following terms:</p>
    <ul>
      <li>Term one.</li>
      <li>Term two.</li>
    </ul>
  </body>
</html>
"""


class TestHtmlToText:
    def test_strips_scripts_and_styles(self) -> None:
        out = html_to_text(SAMPLE)
        assert "alert(1)" not in out
        assert "color:red" not in out

    def test_preserves_prose(self) -> None:
        out = html_to_text(SAMPLE)
        assert "Agreement" in out
        assert "January 1, 2024" in out
        assert "Term one." in out

    def test_empty_input(self) -> None:
        assert html_to_text("") == ""


class TestCleanHtml:
    def test_drops_style_script(self) -> None:
        out = clean_html(SAMPLE)
        assert "<script" not in out.lower()
        assert "<style" not in out.lower()

    def test_preserves_structure(self) -> None:
        out = clean_html(SAMPLE)
        assert "<p>" in out
        assert "<li>" in out


class TestExtractClauses:
    def test_emits_paragraphs_and_list_items(self) -> None:
        clauses = extract_clauses(SAMPLE)
        assert any("January 1, 2024" in c for c in clauses)
        assert "Term one." in clauses
        assert "Term two." in clauses

    def test_returns_empty_for_empty_html(self) -> None:
        assert extract_clauses("") == []

    def test_custom_selector(self) -> None:
        clauses = extract_clauses("<div><span>a</span><span>b</span></div>", selector="span")
        assert clauses == ["a", "b"]
