"""Brazilian identifier extraction (CPF, CNPJ, OAB).

CPF and CNPJ extractors validate identifiers by the Receita Federal
check-digit algorithm (``_cpf_is_valid`` / ``_cnpj_is_valid``), so only
well-formed numbers are emitted. The OAB extractor
(``get_oab_annotations``) is regex-only — the Ordem dos Advogados do
Brasil does not publish a checksum — so callers should treat OAB matches
as surface-level candidates rather than validated identifiers. Together
these keep false positives low when the extractors are run over noisy
document OCR.
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

# OAB registration: "OAB/SP 123.456" or "OAB SP nº 123456".
# - ``(?<!\w)`` prevents matches inside a larger word like "FOOBAROAB/SP …".
# - ``(?!\d)`` after the number group stops ``\d{4,7}`` from truncating a
#   longer run ("12345678" would otherwise yield "1234567").
_OAB_RE = re.compile(
    r"(?<!\w)OAB"
    r"(?:\s*/\s*|\s+)"
    r"(?P<uf>AC|AL|AM|AP|BA|CE|DF|ES|GO|MA|MG|MS|MT|PA|PB|PE|PI|PR|RJ|RN|RO|RR|RS|SC|SE|SP|TO)"
    r"\s*(?:nº|n\.?º?|no\.?)?\s*"
    # Require ≥4 digits total so "OAB/SP 1" does not produce a spurious match.
    r"(?P<number>\d{1,3}(?:\.\d{3})+|\d{4,7})"
    r"(?!\d)",
    re.IGNORECASE,
)


@dataclass(slots=True, frozen=True)
class IdentifierMatch:
    """A validated Brazilian document identifier."""

    kind: str  # 'cpf' | 'cnpj' | 'oab'
    value: str  # canonicalized identifier (digits only for cpf/cnpj)
    surface: str  # original surface form
    coords: tuple[int, int]
    locale: str = "pt"

    def to_dictionary(self) -> dict:
        """
        Produce a dictionary representation of the IdentifierMatch.

        Returns:
            dict: Mapping with keys:
                - `record_type` (str): identifier type — `"cpf"`, `"cnpj"`, or `"oab"`.
                - `coords` (tuple[int, int]): (start, end) character offsets of the match.
                - `text` (str): original matched surface text.
                - `value` (str): canonical identifier value (digits-only for CPF/CNPJ; `UF/number` for OAB).
                - `locale` (str): locale string (defaults to `"pt"`).
        """
        return {
            "record_type": self.kind,
            "coords": self.coords,
            "text": self.surface,
            "value": self.value,
            "locale": self.locale,
        }


# ---------- validators ----------


def _digits(value: str) -> str:
    """
    Extracts decimal digits from the input string.

    Parameters:
        value (str): Input text from which non-digit characters will be removed.

    Returns:
        str: String containing only the decimal digits from `value`.
    """
    return re.sub(r"\D", "", value)


def _cpf_is_valid(digits: str) -> bool:
    """
    Validate a CPF number string using Brazil's check-digit algorithm.

    Parameters:
        digits (str): Digits-only CPF candidate; expected to contain exactly 11 characters.

    Returns:
        true if `digits` is a well-formed CPF with correct check digits, `false` otherwise.
    """
    if len(digits) != 11 or digits == digits[0] * 11:
        return False

    def _check(base: Iterable[int], weights: Iterable[int]) -> int:
        """
        Compute the CPF-style check digit for a sequence of base digits using the provided weights.

        Parameters:
            base (Iterable[int]): Sequence of integer digits forming the base number; must align with `weights`.
            weights (Iterable[int]): Sequence of integer weights to apply to each base digit; must be the same length as `base`.

        Returns:
            int: The computed check digit (0–9). A modulus result of 10 is mapped to `0`.
        """
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
    """
    Validate a CNPJ number using the standard mod-11 check-digit algorithm.

    Accepts a digits-only string of length 14 and rejects strings composed of the same repeated digit.

    Returns:
        True if the input is a valid CNPJ (14 digits and both check digits match), False otherwise.
    """
    if len(digits) != 14 or digits == digits[0] * 14:
        return False

    def _check(base: list[int], weights: list[int]) -> int:
        """
        Compute a mod-11 check digit from a sequence of digits and corresponding weights.

        Parameters:
            base (list[int]): Sequence of integer digits (most-significant first).
            weights (list[int]): Weight factors aligned with `base`; must have the same length.

        Returns:
            int: The computed check digit: `0` if (weighted sum % 11) is less than 2, otherwise `11 - (weighted sum % 11)`.
        """
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
    """
    Finds and yields validated CPF identifiers in the given text.

    Returns:
        IdentifierMatch: An iterator yielding `IdentifierMatch` objects for each valid CPF; each match has `value` as the digits-only CPF, `surface` as the original matched text, and `coords` as the (start, end) character offsets.
    """
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
    """
    Finds and yields validated CNPJ identifiers from the given text.

    Each yielded IdentifierMatch has kind="cnpj", value as the digits-only canonical CNPJ, surface as the original matched substring, and coords as the (start, end) character span corresponding to the match.

    Returns:
        Generator[IdentifierMatch]: Yields one IdentifierMatch for each regex match that passes CNPJ check-digit validation.
    """
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
    """
    Extracts OAB registration mentions from the input text and yields normalized identifier matches.

    Matches recognized OAB surface forms (e.g., "OAB/SP 123.456", "OAB SP nº 123456") and canonicalizes each match to the format `UF/number` (UF uppercased, number digits-only). This function does not perform any check-digit validation; it yields results based on regex recognition and digit normalization.

    Returns:
        Generator[IdentifierMatch]: Yields an IdentifierMatch for each recognized OAB mention. Each match's `value` is the canonical `UF/number`, `surface` is the original matched text, and `coords` are the (start, end) character offsets.
    """
    for match in _OAB_RE.finditer(text):
        value = f"{match.group('uf').upper()}/{_digits(match.group('number'))}"
        yield IdentifierMatch(
            kind="oab",
            value=value,
            surface=match.group(0),
            coords=match.span(),
        )


def get_identifier_annotations(text: str) -> Generator[IdentifierMatch]:
    """
    Extract CPF, CNPJ, and OAB identifier occurrences from the input text.

    Identifiers are yielded as IdentifierMatch objects in the detection order: CPF, then CNPJ, then OAB.

    Returns:
        IdentifierMatch: `IdentifierMatch` objects for each recognized identifier; CPF matches first, then CNPJ, then OAB.
    """
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
