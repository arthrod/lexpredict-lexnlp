"""Duration extraction for Portuguese (pt-BR).

Mirrors :mod:`lexnlp.extract.de.durations`, tuned to the Brazilian
Portuguese unit lexicon (``segundo`` / ``minuto`` / ``hora`` / ``dia`` /
``semana`` / ``mês`` / ``trimestre`` / ``ano``) and to Brazilian numeric
formatting (``.`` thousands, ``,`` decimal). Produces
:class:`DurationAnnotation` records, including grouped multi-part
expressions like ``2 anos e 6 meses``.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Iterator
from decimal import Decimal
from fractions import Fraction

import regex as re

from lexnlp.extract.common.annotations.duration_annotation import DurationAnnotation

# Days per unit (matches the convention used in the DE/EN duration parsers).
_DURATION_DAYS = {
    "second": Fraction(1, 60 * 60 * 24),
    "minute": Fraction(1, 60 * 24),
    "hour": Fraction(1, 24),
    "day": Fraction(1),
    "week": Fraction(7),
    "fortnight": Fraction(14),
    "month": Fraction(30),
    "quarter": Fraction(365, 4),
    "semester": Fraction(365, 2),
    "year": Fraction(365),
}

# pt-BR unit lexicon -> English duration_type (singular).
_PT_UNITS = {
    "segundo": "second",
    "segundos": "second",
    "minuto": "minute",
    "minutos": "minute",
    "hora": "hour",
    "horas": "hour",
    "dia": "day",
    "dias": "day",
    "semana": "week",
    "semanas": "week",
    "quinzena": "fortnight",
    "quinzenas": "fortnight",
    "mês": "month",
    "meses": "month",
    "mes": "month",  # OCR-friendly fallback (sem o til)
    "trimestre": "quarter",
    "trimestres": "quarter",
    "semestre": "semester",
    "semestres": "semester",
    "ano": "year",
    "anos": "year",
}

_UNIT_PART = "|".join(sorted(_PT_UNITS.keys(), key=len, reverse=True))

# Brazilian number: optional ``.`` thousands groups, optional ``,`` decimal.
_PT_NUMBER_PTN = r"\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:,\d+)?"

# Optional prefix ("aproximadamente", "cerca de", "no mínimo", "no máximo")
_PREFIX_PTN = (
    r"(?:aproximadamente|cerca\s+de|no\s+m[ií]nimo|no\s+m[áa]ximo|pelo\s+menos|"
    r"até|aprox\.|aprox)?"
)

DURATION_PTN_RE = re.compile(
    rf"(?P<text>(?:(?P<prefix>{_PREFIX_PTN})\s*)?"
    rf"(?P<num>{_PT_NUMBER_PTN})\s+(?P<unit>{_UNIT_PART}))",
    re.IGNORECASE | re.UNICODE,
)

_INNER_CONJUNCTIONS = ("e", "mais", "y")
_INNER_PUNCT_RE = re.compile(r"[\s,;.]+")


def _parse_pt_number(raw: str) -> Decimal:
    """Convert a Brazilian-formatted numeric string to :class:`Decimal`."""
    return Decimal(raw.replace(".", "").replace(",", "."))


def _fraction_to_decimal(value: Fraction) -> Decimal:
    """Convert a :class:`Fraction` to :class:`Decimal` exactly.

    ``Decimal(Fraction(...))`` is not supported in Python 3.x — it raises
    ``TypeError``. We instead build the Decimal as numerator / denominator,
    which preserves the rational value without going through ``float``.
    """
    return Decimal(value.numerator) / Decimal(value.denominator)


def _make_simple_annotation(match: "re.Match[str]") -> DurationAnnotation:
    """Build a single-part DurationAnnotation from one regex match."""
    raw_unit = match.group("unit").lower()
    duration_en = _PT_UNITS[raw_unit]
    amount = _parse_pt_number(match.group("num"))
    duration_days = _fraction_to_decimal(_DURATION_DAYS[duration_en]) * amount
    prefix = (match.group("prefix") or "").strip() or None
    return DurationAnnotation(
        coords=match.span("text"),
        locale="pt",
        text=match.group("text"),
        amount=amount,
        prefix=prefix,
        duration_days=duration_days,
        duration_type=raw_unit,
        duration_type_en=duration_en,
    )


def _is_continuation(prev: DurationAnnotation, curr: DurationAnnotation, text: str) -> bool:
    """Return True when *curr* should be grouped with *prev* into one duration.

    Continuation requires the second unit to be strictly shorter than the
    first and the gap between matches to contain only whitespace,
    punctuation, or an accepted Portuguese conjunction.
    """
    prev_days = _DURATION_DAYS.get(prev.duration_type_en, Fraction(1))
    curr_days = _DURATION_DAYS.get(curr.duration_type_en, Fraction(1))
    if curr_days >= prev_days:
        return False
    gap = text[prev.coords[1] : curr.coords[0]].lower()
    for conj in _INNER_CONJUNCTIONS:
        gap = re.sub(rf"\b{conj}\b", "", gap)
    return _INNER_PUNCT_RE.sub("", gap) == ""


def _sum_group(group: list[DurationAnnotation], text: str) -> DurationAnnotation:
    """Merge a list of contiguous DurationAnnotations into a complex one.

    ``text`` is the original source string; we slice it by the merged
    coordinates so the surface preserves the gap separators ("e", "mais",
    whitespace, punctuation) instead of dropping them by concatenation.
    """
    coords = (group[0].coords[0], group[-1].coords[1])
    merged = DurationAnnotation(coords=coords, locale="pt", is_complex=True)
    merged.duration_days = sum((d.duration_days for d in group), start=Decimal(0))
    merged.amount = merged.duration_days
    merged.duration_type = group[-1].duration_type
    merged.duration_type_en = group[-1].duration_type_en
    merged.text = text[coords[0] : coords[1]]
    value_dict: dict[str, float] = {}
    for ant in group:
        key = ant.duration_type or ""
        value_dict[key] = value_dict.get(key, 0.0) + float(ant.amount or 0)
    merged.value_dict = value_dict
    return merged


def get_duration_annotations(text: str) -> Iterator[DurationAnnotation]:
    """Yield :class:`DurationAnnotation` records for *text*.

    Adjacent matches that progress from a longer to a shorter unit and are
    separated only by punctuation / conjunctions (``e``, ``mais``) are
    grouped into a single ``is_complex=True`` annotation whose
    ``duration_days`` is the sum of the parts.
    """
    flat = [_make_simple_annotation(m) for m in DURATION_PTN_RE.finditer(text)]
    if not flat:
        return
    if len(flat) == 1:
        yield flat[0]
        return
    group: list[DurationAnnotation] = [flat[0]]
    grouped: list[list[DurationAnnotation]] = [group]
    for ant in flat[1:]:
        if _is_continuation(group[-1], ant, text):
            group.append(ant)
        else:
            group = [ant]
            grouped.append(group)
    for grp in grouped:
        yield grp[0] if len(grp) == 1 else _sum_group(grp, text)


def get_durations(text: str) -> Iterator[dict]:
    """Yield dictionaries describing each duration expression in *text*."""
    for ant in get_duration_annotations(text):
        yield {
            "location_start": ant.coords[0],
            "location_end": ant.coords[1],
            "source_text": ant.text,
            "amount": ant.amount,
            "duration_type": ant.duration_type,
            "duration_days": ant.duration_days,
            "is_complex": ant.is_complex,
        }


def get_duration_annotation_list(text: str) -> list[DurationAnnotation]:
    """Return all duration annotations in *text* as a list."""
    return list(get_duration_annotations(text))


def get_duration_list(text: str) -> list[dict]:
    """Return all duration annotations as a list of plain dictionaries."""
    return list(get_durations(text))


__all__ = [
    "DURATION_PTN_RE",
    "get_duration_annotation_list",
    "get_duration_annotations",
    "get_duration_list",
    "get_durations",
]
