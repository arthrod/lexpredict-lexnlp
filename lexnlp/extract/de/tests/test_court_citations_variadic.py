"""Tests for the variadic ``tuple[re.Match, ...]`` annotation fix.

PR #14 review noted that ``matches: tuple[re.Match] = tuple(...)`` was
incorrect (``tuple[re.Match]`` is a 1-element tuple type in PEP 585).
The new annotation is ``tuple[re.Match, ...]`` and allows an arbitrary
number of elements.

The test verifies :meth:`CourtCitationsParser.split_text_by_keywords`
handles multi-match inputs correctly, which would have been the failure
mode if the static-analysis constraint were enforced at runtime.
"""

from __future__ import annotations

from lexnlp.extract.de.court_citations import CourtCitationsParser


class TestSplitTextByKeywords:
    def test_empty_text_yields_no_chunks(self) -> None:
        assert CourtCitationsParser.split_text_by_keywords("") == []

    def test_single_match(self) -> None:
        text = "BFH Urteil 2024"
        chunks = CourtCitationsParser.split_text_by_keywords(text)
        assert len(chunks) == 1

    def test_multiple_matches_produce_multiple_chunks(self) -> None:
        text = "BFH Urteil 2023; BStBl Urteil 2024; GrS Beschluss 2025"
        chunks = CourtCitationsParser.split_text_by_keywords(text)
        # At least two chunks for three registry mentions (stride of two).
        assert len(chunks) >= 2

    def test_chunks_are_str_int_tuples(self) -> None:
        text = "BFH"
        chunks = CourtCitationsParser.split_text_by_keywords(text)
        for c in chunks:
            assert isinstance(c, tuple)
            assert isinstance(c[0], str)
            assert isinstance(c[1], int)
