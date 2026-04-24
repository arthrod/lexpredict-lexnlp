"""US state / territory normalization helpers built on the ``us`` package.

The ``us`` library ships a curated list of US states and territories with
full metadata (name, abbreviation, FIPS code, demonym, capital). It was
declared as a runtime dependency but never imported anywhere in the
codebase before this module. Wrapping it behind a tiny helper layer gives
the geoentity and address detectors a fast, correct source of truth for
state normalization without having to ship their own table.

The helpers below are all ``lru_cache``-decorated so repeated lookups in
hot paths (one call per token during address classification) cost a
dict hit after the first invocation.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from dataclasses import dataclass
from functools import lru_cache

import us


@dataclass(frozen=True, slots=True)
class StateInfo:
    """Minimal projection of ``us.states.State`` for downstream use.

    The real ``us.states.State`` object carries dozens of attributes we
    don't need. This frozen projection keeps only what LexNLP uses so it
    serialises cleanly (e.g. in a pandas column).
    """

    name: str
    abbr: str
    fips: str
    is_territory: bool

    @classmethod
    def from_state(cls, state: us.states.State) -> StateInfo:
        """Build a :class:`StateInfo` from a ``us`` package state object."""
        return cls(
            name=state.name,
            abbr=state.abbr,
            fips=str(state.fips or ""),
            is_territory=bool(getattr(state, "is_territory", False)),
        )


@lru_cache(maxsize=1)
def _state_index() -> dict[str, us.states.State]:
    """Build an upper-cased index of names, abbreviations, and FIPS codes.

    ``us.states.lookup`` relies on ``jellyfish.metaphone`` for its fuzzy
    fall-back, which has a known incompatibility in some ``jellyfish``
    releases. We bypass that path by building our own exact index from
    the same underlying data, which is all the callers in LexNLP need.
    """
    index: dict[str, us.states.State] = {}
    for state in us.STATES_AND_TERRITORIES:
        index[state.name.upper()] = state
        index[state.abbr.upper()] = state
        if state.fips:
            index[str(state.fips)] = state
    return index


# Bounded cache: noisy corpora produce many unique tokens; unbounded @cache
# would leak memory over long-running services. 4096 entries covers every
# US state / territory plus common punctuation variants many times over.
@lru_cache(maxsize=4096)
def lookup_state(text: str) -> StateInfo | None:
    """Return a :class:`StateInfo` for the given name or abbreviation.

    Args:
        text: Any case/whitespace variation of a state name (e.g.
            ``"California"``, ``"CA"``, ``"ca"``, ``"06"``).

    Returns:
        A :class:`StateInfo` on match, ``None`` otherwise.
    """
    if not text:
        return None
    key = text.strip().upper().rstrip(".")
    state = _state_index().get(key)
    if state is None:
        return None
    return StateInfo.from_state(state)


@lru_cache(maxsize=1)
def state_name_to_abbr() -> dict[str, str]:
    """Return an upper-cased ``name → abbr`` mapping including territories.

    The mapping is cached because ``us.states.mapping`` walks every state
    each call; it's fine once, wasteful in a tokenisation loop.
    """
    mapping: dict[str, str] = {}
    for state in us.STATES_AND_TERRITORIES:
        mapping[state.name.upper()] = state.abbr
    return mapping


@lru_cache(maxsize=1)
def state_abbr_to_name() -> dict[str, str]:
    """Return an upper-cased ``abbr → name`` mapping including territories."""
    return {state.abbr: state.name for state in us.STATES_AND_TERRITORIES}


@lru_cache(maxsize=1)
def all_state_abbreviations() -> frozenset[str]:
    """Return every US state & territory abbreviation (``"CA"``, ``"PR"`` …)."""
    return frozenset(state.abbr for state in us.STATES_AND_TERRITORIES)


@lru_cache(maxsize=1)
def all_state_names() -> frozenset[str]:
    """Return every US state & territory *full name* in upper case."""
    return frozenset(state.name.upper() for state in us.STATES_AND_TERRITORIES)


def is_us_state(text: str) -> bool:
    """Check whether ``text`` matches any US state or territory."""
    return lookup_state(text) is not None


def normalize_state(text: str) -> str | None:
    """Return the canonical abbreviation for ``text`` (e.g. ``"CA"``).

    Returns ``None`` when ``text`` does not resolve to a US state or
    territory — callers typically fall back to the original string.
    """
    info = lookup_state(text)
    return info.abbr if info else None


__all__ = [
    "StateInfo",
    "all_state_abbreviations",
    "all_state_names",
    "is_us_state",
    "lookup_state",
    "normalize_state",
    "state_abbr_to_name",
    "state_name_to_abbr",
]
