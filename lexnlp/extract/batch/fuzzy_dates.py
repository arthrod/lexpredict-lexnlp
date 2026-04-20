"""Fuzzy ISO-style date detection using the ``regex`` 2024+ backend.

The main ``lexnlp.extract.en.dates`` module is precision-first: it refuses to
emit a date when the surface form looks even slightly off. That is the right
default for extraction from clean text, but OCR output and user-entered text
often contain single-character transcription errors ("2O24" instead of
"2024", "Jamuary" instead of "January") that a fuzzy regex can still match.

This helper implements a narrow, opt-in detector for ISO-style dates
(``YYYY-MM-DD``) with a configurable edit budget. It only depends on
the ``regex`` package, not on NLTK / dateparser, so it is cheap to
import and safe to run inside loops.

The intent is *complementary* to the existing date parser: run the main
parser first, then fall back to this helper on chunks that did not yield a
match but look date-ish.
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
from datetime import date

import regex as re

# Precompile with a small fuzzy budget. The pattern is written so that fuzz
# can only perturb digits / the dash separator — the numeric lengths stay
# enforced. Supports up to one edit (``{e<=1}``) by default, configurable
# per call via :func:`find_fuzzy_dates`.
_BASE_PATTERN = r"""
    (?P<y>\d{4}) [-./] (?P<m>\d{1,2}) [-./] (?P<d>\d{1,2})
"""


@dataclass(slots=True, frozen=True)
class FuzzyDateMatch:
    """A single fuzzy-matched ISO date.

    Attributes:
        start: Inclusive character offset in the source string.
        end: Exclusive character offset.
        matched_text: The exact slice of the source that matched.
        parsed: The date parsed from the match, or ``None`` when the
            month or day portion fell outside the calendar (e.g. ``13`` for
            the month). Kept as ``None`` rather than raising so callers can
            still inspect the surface form.
        edit_distance: Levenshtein-style distance reported by the
            ``regex`` backend. ``0`` for exact matches; larger values
            indicate ``regex`` needed to substitute / insert / delete.
    """

    start: int
    end: int
    matched_text: str
    parsed: date | None
    edit_distance: int


def _safe_parse(y: str, m: str, d: str) -> date | None:
    """
    Attempt to construct a datetime.date from numeric year, month, and day strings.
    
    Parameters:
        y (str): Four-digit year string.
        m (str): One- or two-digit month string.
        d (str): One- or two-digit day string.
    
    Returns:
        date | None: A datetime.date for the provided components, or `None` if conversion or date construction fails.
    """
    try:
        return date(int(y), int(m), int(d))
    except (ValueError, TypeError):
        return None


def find_fuzzy_dates(
    text: str,
    *,
    max_edits: int = 1,
) -> Iterator[FuzzyDateMatch]:
    """Yield ISO-style dates in ``text``, tolerating a small edit budget.

    Args:
        text: The text to scan.
        max_edits: Maximum Levenshtein edits the fuzzy matcher is allowed
            to apply. Must be non-negative. ``0`` degrades to an exact
            match; ``1`` catches typical OCR errors; values above ``2``
            start producing false positives so they are rejected to keep
            callers honest.

    Yields:
        :class:`FuzzyDateMatch` values in left-to-right order.

    Raises:
        ValueError: If ``max_edits`` is negative or greater than 2.
    """
    if max_edits < 0:
        raise ValueError(f"max_edits must be >= 0, got {max_edits}")
    if max_edits > 2:
        raise ValueError(f"max_edits > 2 produces unreliable results; got {max_edits}")

    pattern = _BASE_PATTERN + f"{{e<={max_edits}}}" if max_edits else _BASE_PATTERN
    compiled = re.compile(pattern, flags=re.VERBOSE | re.BESTMATCH)

    for match in compiled.finditer(text):
        # ``regex`` populates ``fuzzy_counts`` as (substitutions, insertions,
        # deletions). The sum is the edit distance.
        counts = getattr(match, "fuzzy_counts", (0, 0, 0))
        edit_distance = sum(counts)
        parsed = _safe_parse(match.group("y"), match.group("m"), match.group("d"))
        yield FuzzyDateMatch(
            start=match.start(),
            end=match.end(),
            matched_text=match.group(0),
            parsed=parsed,
            edit_distance=edit_distance,
        )


__all__ = ["FuzzyDateMatch", "find_fuzzy_dates"]
