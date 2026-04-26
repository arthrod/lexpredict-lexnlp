"""Hybrid NER fallback for entities the rule stack misses.

LexNLP's rule-based extractors (``lexnlp.extract.en.entities`` /
``lexnlp.extract.common``) cover most legal-domain entities (parties,
agreement types, dates, money, …) but their precision/recall trade-off is
tuned for surface-level pattern matching. For the long tail —
non-canonical party-name spellings, novel agreement types, OCR-ed proper
nouns — a small on-device statistical model recovers significant recall
without rewriting the pipeline.

This module provides:

* :func:`spacy_is_available` — boolean probe for the optional ``[ner]``
  extra.
* :func:`extract_entities` — main entry point. Returns a list of
  :class:`HybridNERMatch` records produced by spaCy when available, or by
  an NLTK-only fallback (``averaged_perceptron_tagger`` + ``ne_chunk``)
  otherwise. Both backends emit the same dataclass so consumers don't
  branch on the backend.
* :func:`augment_rule_matches` — merges hybrid matches with an existing
  iterable of ``(start, end, label)`` annotations from the rule stack,
  dropping spans that overlap a rule annotation by ≥50 % so the rule
  stack remains the source of truth.

The optional ``[ner]`` extra (``spacy>=3.7``) is required for the spaCy
backend; the NLTK fallback works with the NLTK release that LexNLP
already pins. Either backend feeds
``lexnlp.extract.ml`` CRF features through the existing
``feature_data`` pipeline — no consumer code changes required.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import importlib
import os
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HybridNERMatch:
    """A single hybrid-NER match.

    Attributes:
        start: Inclusive character offset of the match.
        end: Exclusive character offset.
        text: Surface form, ``text == source[start:end]``.
        label: Backend-specific entity label (e.g. ``"PERSON"`` /
            ``"ORG"``). Both backends emit the spaCy-style upper-case label
            namespace.
        backend: ``"spacy"`` or ``"nltk"``; lets callers down-weight the
            fallback if they want strict spaCy semantics.
        score: Optional confidence in [0, 1]. spaCy's pretrained pipelines
            do not expose calibrated probabilities, so this is ``None``
            unless the caller plugged in a scorer.
    """

    start: int
    end: int
    text: str
    label: str
    backend: str
    score: float | None = None


def spacy_is_available() -> bool:
    """Return ``True`` when the ``[ner]`` extra (``spacy>=3.7``) is importable."""

    try:
        importlib.import_module("spacy")
    except ImportError:
        return False
    return True


def _resolve_spacy_model_name() -> str:
    """Return the spaCy model identifier, honouring ``LEXNLP_SPACY_MODEL``."""

    return os.getenv("LEXNLP_SPACY_MODEL", "en_core_web_sm")


def _spacy_extract(text: str) -> list[HybridNERMatch]:
    """spaCy backend: defers ``import spacy`` to first use to keep the
    optional dependency truly optional."""

    from lexnlp.extract.ml.classifier.spacy_token_sequence_model import (
        _load_spacy_pipeline,
    )

    pipeline = _load_spacy_pipeline(_resolve_spacy_model_name())
    doc = pipeline(text)
    matches: list[HybridNERMatch] = []
    for ent in doc.ents:
        matches.append(
            HybridNERMatch(
                start=ent.start_char,
                end=ent.end_char,
                text=ent.text,
                label=ent.label_,
                backend="spacy",
            )
        )
    return matches


# spaCy entity labels we surface from the NLTK fallback. NLTK chunk types
# differ ("PERSON" / "ORGANIZATION" / "GPE" / "FACILITY" / "GSP" / "LOCATION")
# from spaCy's slightly broader set, so we map onto the spaCy namespace to
# keep the contract uniform across backends.
_NLTK_TO_SPACY_LABEL = {
    "PERSON": "PERSON",
    "ORGANIZATION": "ORG",
    "GPE": "GPE",
    "FACILITY": "FAC",
    "GSP": "GPE",
    "LOCATION": "LOC",
}


def _nltk_extract(text: str) -> list[HybridNERMatch]:
    """NLTK fallback backend (``averaged_perceptron_tagger`` + ``ne_chunk``).

    NLTK is already a hard dependency of LexNLP, so this path costs no extra
    install. The on-device tagger has lower accuracy than ``en_core_web_sm``
    but is enough to recover obvious party / org spans missed by the rule
    stack.
    """

    from nltk import ne_chunk, pos_tag, word_tokenize  # local: keep import-free top

    tokens = list(word_tokenize(text))
    if not tokens:
        return []
    tagged = pos_tag(tokens)
    tree = ne_chunk(tagged, binary=False)

    matches: list[HybridNERMatch] = []
    cursor = 0
    for chunk in tree:
        # Sub-tree => named entity (label_, [(token, pos), ...])
        if hasattr(chunk, "label"):
            entity_tokens = [tok for tok, _pos in chunk.leaves()]
            if not entity_tokens:
                continue
            # Walk forward from the cursor to find the surface span.
            start = text.find(entity_tokens[0], cursor)
            if start == -1:
                continue
            end = start
            local_cursor = start
            for tok in entity_tokens:
                idx = text.find(tok, local_cursor)
                if idx == -1:
                    end = local_cursor
                    break
                local_cursor = idx + len(tok)
                end = local_cursor
            cursor = end
            matches.append(
                HybridNERMatch(
                    start=start,
                    end=end,
                    text=text[start:end],
                    label=_NLTK_TO_SPACY_LABEL.get(chunk.label(), chunk.label()),
                    backend="nltk",
                )
            )
        else:
            # Plain tagged token; advance the cursor past it so the next NE
            # search starts at or after this token's surface form.
            tok = chunk[0]
            idx = text.find(tok, cursor)
            if idx != -1:
                cursor = idx + len(tok)
    return matches


def extract_entities(text: str, *, prefer_spacy: bool = True) -> list[HybridNERMatch]:
    """Extract entities using spaCy when available, otherwise NLTK.

    ``prefer_spacy=False`` forces the NLTK fallback even when spaCy is
    importable (useful in tests and benchmark sweeps where you want to
    measure the rule + on-device baseline without the heavier spaCy load).
    """

    if not isinstance(text, str):  # pragma: no cover - defensive
        raise TypeError(f"text must be str, got {type(text).__name__}")

    if prefer_spacy and spacy_is_available():
        try:
            return _spacy_extract(text)
        except OSError:
            # spaCy importable but the model file is missing locally; degrade
            # gracefully to the NLTK fallback so callers don't get an
            # ``OSError: [E050] Can't find model 'en_core_web_sm'``.
            pass
    return _nltk_extract(text)


def _overlap_ratio(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Return the overlap length of two ``(start, end)`` spans / shorter span."""

    overlap = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    shorter = min(a[1] - a[0], b[1] - b[0])
    if shorter <= 0:
        return 0.0
    return overlap / shorter


def augment_rule_matches(
    rule_spans: Iterable[tuple[int, int, str]],
    hybrid_matches: Iterable[HybridNERMatch],
    *,
    overlap_threshold: float = 0.5,
) -> list[HybridNERMatch]:
    """Merge ``rule_spans`` with ``hybrid_matches``.

    Hybrid matches that overlap any rule span by ``>= overlap_threshold``
    of the shorter span are dropped — the rule stack is treated as the
    source of truth for those positions. The remaining hybrid matches are
    returned in document order.
    """

    rule_list = [(s, e) for s, e, _label in rule_spans]
    out: list[HybridNERMatch] = []
    for match in hybrid_matches:
        m_span = (match.start, match.end)
        keep = True
        for r_span in rule_list:
            if _overlap_ratio(m_span, r_span) >= overlap_threshold:
                keep = False
                break
        if keep:
            out.append(match)
    out.sort(key=lambda m: (m.start, m.end))
    return out


__all__ = [
    "HybridNERMatch",
    "augment_rule_matches",
    "extract_entities",
    "spacy_is_available",
]
