"""Tests for :mod:`lexnlp.utils.iterating_helpers` after import cleanup.

The PR review flagged a degenerate ``try/except ImportError`` that imported
``Iterable`` from the same location in both branches. The cleanup imports
``Iterable`` once from :mod:`collections.abc`.
"""

from __future__ import annotations

import pytest

from lexnlp.utils.iterating_helpers import (
    collapse_sequence,
    count_sequence_matches,
)


class TestCollapseSequence:
    def test_sum_via_collapse(self) -> None:
        assert collapse_sequence([1, 2, 3, 4], lambda i, a: a + i, 0) == 10

    def test_empty_returns_accumulator(self) -> None:
        assert collapse_sequence([], lambda i, a: a + i, 42) == 42

    def test_generator_input_is_supported(self) -> None:
        def gen() -> object:
            """
            Yield a fixed sequence of integers 10, 20, and 30.

            Returns:
                generator: Yields the integers 10, 20, and 30 in order.
            """
            yield from (10, 20, 30)

        assert collapse_sequence(gen(), lambda i, a: a + i, 0) == 60


class TestCountSequenceMatches:
    def test_counts_even_numbers(self) -> None:
        assert count_sequence_matches([1, 2, 3, 4, 5, 6], lambda x: x % 2 == 0) == 3

    def test_no_matches(self) -> None:
        assert count_sequence_matches([1, 3, 5], lambda x: x % 2 == 0) == 0

    @pytest.mark.parametrize(
        "seq,predicate,expected",
        [
            ([], lambda _: True, 0),
            (["a", "b", "c"], lambda s: s == "b", 1),
            (range(100), lambda n: n < 5, 5),
        ],
    )
    def test_parametrized(self, seq: object, predicate: object, expected: int) -> None:
        assert count_sequence_matches(seq, predicate) == expected  # type: ignore[arg-type]
