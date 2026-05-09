"""PII extraction for Portuguese (pt-BR).

Mirrors :mod:`lexnlp.extract.en.pii`, scoped to the PII surface that
applies in Brazilian contracts:

- Brazilian phone numbers — landline ``(11) 1234-5678`` and mobile
  ``(11) 91234-5678`` formats, optional international prefix ``+55``,
  optional area-code parentheses, optional dash separator.
- Email addresses — same syntax everywhere; we re-export the canonical
  RFC-5321 style regex from :mod:`lexnlp.extract.common`.

CPF and CNPJ are already covered by :mod:`lexnlp.extract.pt.identifiers`,
so this module deliberately omits them to avoid duplicate annotations.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Iterator

import regex as re

from lexnlp.extract.common.annotations.phone_annotation import PhoneAnnotation

# Brazilian phone number formats:
#   ``+55 11 91234-5678`` (international prefix + DDD + mobile 9-digit)
#   ``(11) 91234-5678``    (DDD in parens + 9-digit mobile)
#   ``11 1234-5678``       (DDD + 8-digit landline)
#   ``0800 123 4567``      (toll-free)
# We accept variable separators (space, dot, hyphen) between the DDD and
# the body. ``9`` as the leading mobile digit is optional so legacy
# 8-digit numbers (residential) still match.
PHONE_PTN_RE = re.compile(
    r"(?<!\d)"
    r"(?P<phone>"
    r"(?:\+?55[\s.-]?)?"  # optional country code
    r"(?:\(0?\d{2}\)|0?\d{2})"  # DDD with or without parens
    r"[\s.-]?"
    r"9?\d{4}"  # 8- or 9-digit body, leading "9" optional
    r"[\s.-]?"
    r"\d{4}"
    r"|0800[\s.-]?\d{3}[\s.-]?\d{3,4}"  # 0800 toll-free
    r")"
    r"(?!\d)"
)

# Pragmatic email regex — matches the vast majority of legitimate
# addresses without trying to fully cover RFC 5321.
EMAIL_PTN_RE = re.compile(
    r"(?<![\w.+-])"
    r"(?P<email>[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
    r"(?![\w.])"
)


def _digits_only(value: str) -> str:
    """Strip every non-digit character (including ``+``)."""
    return re.sub(r"\D", "", value)


def get_phone_annotations(text: str) -> Iterator[PhoneAnnotation]:
    """Yield :class:`PhoneAnnotation` for every Brazilian phone number.

    The ``phone`` field is the canonical digits-only form (without the
    ``+``); the ``text`` field preserves the original surface (with
    whatever separators the source used). Numbers shorter than 10 digits
    or longer than 13 are rejected as false positives.
    """
    for match in PHONE_PTN_RE.finditer(text):
        surface = match.group("phone")
        digits = _digits_only(surface)
        if len(digits) not in (10, 11, 12, 13):
            continue
        yield PhoneAnnotation(
            coords=match.span("phone"),
            phone=digits,
            text=surface,
            locale="pt",
        )


def get_phones(text: str) -> Iterator[str]:
    """Yield the canonical digits-only phone for every match in *text*."""
    for ant in get_phone_annotations(text):
        yield ant.phone


def get_phone_list(text: str) -> list[str]:
    """Return all canonical phone strings in *text* as a list."""
    return list(get_phones(text))


def get_phone_annotation_list(text: str) -> list[PhoneAnnotation]:
    """Return all phone annotations in *text* as a list."""
    return list(get_phone_annotations(text))


def get_emails(text: str) -> Iterator[str]:
    """Yield every email address found in *text*."""
    for match in EMAIL_PTN_RE.finditer(text):
        yield match.group("email")


def get_email_list(text: str) -> list[str]:
    """Return all email addresses in *text* as a list."""
    return list(get_emails(text))


def get_pii_annotations(text: str) -> Iterator[PhoneAnnotation]:
    """Yield phone PII annotations for *text*.

    Email addresses are surfaced via :func:`get_emails` (no dedicated
    annotation class exists in lexnlp/common). Callers that want both
    streams can iterate ``get_phone_annotations`` and ``get_emails``
    side-by-side.
    """
    yield from get_phone_annotations(text)


__all__ = [
    "EMAIL_PTN_RE",
    "PHONE_PTN_RE",
    "get_email_list",
    "get_emails",
    "get_phone_annotation_list",
    "get_phone_annotations",
    "get_phone_list",
    "get_phones",
    "get_pii_annotations",
]
