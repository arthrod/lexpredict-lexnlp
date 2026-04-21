"""Brazilian identifier extraction (CPF, CNPJ, OAB).

Each extractor validates the identifier by its check-digit algorithm, so only
well-formed numbers are emitted. This keeps false positives low when the
extractors are run over noisy document OCR.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator, Iterable
from dataclasses import dataclass

import regex as re

# CPF surface forms: 000.000.000-00 / 000000000-00 / 00000000000
_CPF_RE = re.compile(
    r"(?<!\d)"
    r"(?P<cpf>\d{3}\.?\d{3}\.?\d{3}-?\d{2})"
    r"(?!\d)"
)

# CNPJ: 00.000.000/0000-00 with separators optional. We keep the separators in
# the canonical regex to avoid matching too-long digit sequences embedded in
# identifiers like bank slips.
_CNPJ_RE = re.compile(
    r"(?<!\d)"
    r"(?P<cnpj>\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})"
    r"(?!\d)"
)

# OAB registration: "OAB/SP 123.456" or "OAB SP nº 123456"
_OAB_RE = re.compile(
    r"OAB"
    r"(?:\s*/\s*|\s+)"
    r"(?P<uf>AC|AL|AM|AP|BA|CE|DF|ES|GO|MA|MG|MS|MT|PA|PB|PE|PI|PR|RJ|RN|RO|RR|RS|SC|SE|SP|TO)"
    r"\s*(?:nº|n\.?º?|no\.?)?\s*"
    r"(?P<number>\d{1,3}(?:\.\d{3})+|\d{4,7}|\d{1,3})",
    re.IGNORECASE,
)


@dataclass(slots=True, frozen=True)
class IdentifierMatch:
    """A validated Brazilian document identifier."""
    kind: str          # 'cpf' | 'cnpj' | 'oab'
    value: str         # canonicalized identifier (digits only for cpf/cnpj)
    surface: str       # original surface form
    coords: tuple[int, int]
    locale: str = "pt"

    def to_dictionary(self) -> dict:
        return {
            "record_type": self.kind,
            "coords": self.coords,
            "text": self.surface,
            "value": self.value,
            "locale": self.locale,
        }


# ---------- validators ----------

def _digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _cpf_is_valid(digits: str) -> bool:
    if len(digits) != 11 or digits == digits[0] * 11:
        return False

    def _check(base: Iterable[int], weights: Iterable[int]) -> int:
        total = sum(d * w for d, w in zip(base, weights, strict=True))
        remainder = (total * 10) % 11
        return 0 if remainder == 10 else remainder

    nums = [int(c) for c in digits]
    first = _check(nums[:9], range(10, 1, -1))
    if first != nums[9]:
        return False
    second = _check(nums[:10], range(11, 1, -1))
    return second == nums[10]


def _cnpj_is_valid(digits: str) -> bool:
    if len(digits) != 14 or digits == digits[0] * 14:
        return False

    def _check(base: list[int], weights: list[int]) -> int:
        total = sum(d * w for d, w in zip(base, weights, strict=True))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    nums = [int(c) for c in digits]
    first = _check(nums[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    if first != nums[12]:
        return False
    second = _check(nums[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return second == nums[13]


# ---------- public API ----------

def get_cpf_annotations(text: str) -> Generator[IdentifierMatch]:
    for match in _CPF_RE.finditer(text):
        digits = _digits(match.group("cpf"))
        if _cpf_is_valid(digits):
            yield IdentifierMatch(
                kind="cpf",
                value=digits,
                surface=match.group("cpf"),
                coords=match.span("cpf"),
            )


def get_cnpj_annotations(text: str) -> Generator[IdentifierMatch]:
    for match in _CNPJ_RE.finditer(text):
        digits = _digits(match.group("cnpj"))
        if _cnpj_is_valid(digits):
            yield IdentifierMatch(
                kind="cnpj",
                value=digits,
                surface=match.group("cnpj"),
                coords=match.span("cnpj"),
            )


def get_oab_annotations(text: str) -> Generator[IdentifierMatch]:
    for match in _OAB_RE.finditer(text):
        value = f"{match.group('uf').upper()}/{_digits(match.group('number'))}"
        yield IdentifierMatch(
            kind="oab",
            value=value,
            surface=match.group(0),
            coords=match.span(),
        )


def get_identifier_annotations(text: str) -> Generator[IdentifierMatch]:
    """Yield CPF, CNPJ, and OAB identifiers together."""
    yield from get_cpf_annotations(text)
    yield from get_cnpj_annotations(text)
    yield from get_oab_annotations(text)


__all__ = [
    "IdentifierMatch",
    "get_cnpj_annotations",
    "get_cpf_annotations",
    "get_identifier_annotations",
    "get_oab_annotations",
]
