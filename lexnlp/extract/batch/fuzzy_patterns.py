"""Fuzzy regex patterns for OCR-tolerant entity extraction.

The main extractors in :mod:`lexnlp.extract.en` are precision-first — they
won't match ``2O24`` when they expect ``2024``. For OCR output the
opposite trade-off is usually preferable: accept a small edit budget to
recover entities that would otherwise be lost. This module is the
counterpart to :mod:`lexnlp.extract.batch.fuzzy_dates` for CUSIP codes
and money amounts, the two entity types the PR review identified as the
highest-value OCR targets.

All matchers use :mod:`regex` (``regex>=2024``) with ``BESTMATCH`` so the
backend returns the candidate with the fewest edits rather than the
first acceptable one.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Iterator
from dataclasses import dataclass

import regex as re

# Basic CUSIP shape: 9 alphanumeric characters; the last is a checksum
# digit. Surface errors in OCR usually take the form of ``0↔O``,
# ``1↔I``, and ``5↔S`` substitutions, so we rely on ``regex`` fuzzy
# matching to recover those without hand-rolling a substitution table.
_CUSIP_PATTERN = r"[A-Z0-9]{8}\d"

# A money amount written numerically: currency prefix followed by digits
# with optional thousands separators and decimal fraction. Requiring the
# currency prefix keeps the fuzz budget from eating into plain numbers
# and producing false positives from phone numbers or years.
_MONEY_PATTERN = r"[$€£¥]\s?\d{1,3}(?:[,\s]\d{3})*(?:\.\d{1,2})?"


def _with_budget(pattern: str, max_edits: int) -> str:
    """Return ``pattern`` wrapped so fuzzy edits apply across the whole match."""
    if max_edits <= 0:
        return pattern
    return f"(?:{pattern}){{e<={max_edits}}}"


@dataclass(frozen=True, slots=True)
class FuzzyPatternMatch:
    """A single fuzzy pattern match.

    Attributes:
        start: Inclusive character offset in the source string.
        end: Exclusive character offset.
        matched_text: The exact slice of the source that matched.
        edit_distance: Levenshtein-style distance reported by ``regex``.
    """

    start: int
    end: int
    matched_text: str
    edit_distance: int


def _iter_matches(pattern: str, text: str, max_edits: int) -> Iterator[FuzzyPatternMatch]:
    if max_edits < 0:
        raise ValueError(f"max_edits must be >= 0, got {max_edits}")
    if max_edits > 2:
        raise ValueError(f"max_edits > 2 produces unreliable results; got {max_edits}")

    compiled = re.compile(_with_budget(pattern, max_edits), flags=re.BESTMATCH)
    for match in compiled.finditer(text):
        counts = getattr(match, "fuzzy_counts", (0, 0, 0))
        yield FuzzyPatternMatch(
            start=match.start(),
            end=match.end(),
            matched_text=match.group(0),
            edit_distance=sum(counts),
        )


def find_fuzzy_cusips(text: str, *, max_edits: int = 1) -> Iterator[FuzzyPatternMatch]:
    """Yield fuzzy-matched 9-character CUSIP codes in ``text``."""
    yield from _iter_matches(_CUSIP_PATTERN, text, max_edits)


def find_fuzzy_money(text: str, *, max_edits: int = 1) -> Iterator[FuzzyPatternMatch]:
    """Yield fuzzy-matched money amounts in ``text``."""
    yield from _iter_matches(_MONEY_PATTERN, text, max_edits)


__all__ = [
    "FuzzyPatternMatch",
    "find_fuzzy_cusips",
    "find_fuzzy_money",
]
