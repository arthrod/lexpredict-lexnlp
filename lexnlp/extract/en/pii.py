"""PII extraction for English.

This module implements PII extraction functionality in English.

Todo:
  * http://www.doncio.navy.mil/contentview.aspx?id=2428
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

import regex as re

from lexnlp.extract.common.annotations.phone_annotation import PhoneAnnotation
from lexnlp.extract.common.annotations.ssn_annotation import SsnAnnotation
from lexnlp.extract.common.annotations.text_annotation import TextAnnotation

SSN_PATTERN = r"""
(?P<block1>[0-9]{3})[\-]?(?P<block2>[0-9]{2})[\-]?(?P<block3>[0-9]{4})
"""
RE_SSN = re.compile(SSN_PATTERN, re.IGNORECASE | re.UNICODE | re.DOTALL | re.VERBOSE)

US_PHONE_PATTERN = r"""
[\(]?(?P<area_code>[0-9]{3})[\)]?
[\-\s]+
(?P<exchange>[0-9]{3})
[\-\s]+
(?P<last4>[0-9]{4})
"""
RE_US_PHONE = re.compile(US_PHONE_PATTERN, re.IGNORECASE | re.UNICODE | re.DOTALL | re.VERBOSE)


def get_ssns(
    text: str,
    return_sources: bool = False,
) -> Generator[str | None | tuple[str | None, str]]:
    """
    Find possible SSN references in the text.
    """

    # Iterate through all potential matches
    for ant in get_ssn_annotations(text):
        if return_sources:
            yield ant.number, ant.text
        else:
            yield ant.number


def get_ssn_list(
    text: str,
    return_sources: bool = False,
) -> list[str | None | tuple[str | None, str]]:
    """ """
    return list(get_ssns(text, return_sources))


def get_ssn_annotations(text: str) -> Generator[SsnAnnotation]:
    for match in RE_SSN.finditer(text):  # type: re.Match
        # Get individual group matches
        captures = match.capturesdict()
        blocks = [int(captures[f"block{i + 1}"].pop()) for i in range(3)]
        if not all(blocks):
            continue

        ssn = f"{blocks[0]:03d}-{blocks[1]:02d}-{blocks[2]:04d}"
        ant = SsnAnnotation(coords=match.span(), number=ssn, text=match.group())
        yield ant


def get_ssn_annotation_list(text: str) -> list[SsnAnnotation]:
    """ """
    return list(get_ssn_annotations(text))


def get_us_phones(
    text: str,
    return_sources: bool = False,
) -> Generator[str | None | tuple[str | None, str]]:
    """
    Find possible telephone numbers in the text.
    """
    for ant in get_us_phone_annotations(text):
        if return_sources:
            yield ant.phone, ant.text
        else:
            yield ant.phone


def get_us_phone_list(
    text: str,
    return_sources: bool = False,
) -> list[str | None | tuple[str | None, str]]:
    """ """
    return list(get_us_phones(text, return_sources))


def get_us_phone_annotations(text: str) -> Generator[PhoneAnnotation]:
    """
    Find possible telephone numbers in the text.
    """

    # Iterate through all potential matches
    for match in RE_US_PHONE.finditer(text):
        # Get individual group matches
        captures = match.capturesdict()
        phone = "({area_code}) {exchange}-{last4}".format(
            area_code=captures["area_code"].pop(),
            exchange=captures["exchange"].pop(),
            last4=captures["last4"].pop(),
        )
        ant = PhoneAnnotation(coords=match.span(), phone=phone, text=match.group(0))
        yield ant


def get_us_phone_annotation_list(text: str) -> list[PhoneAnnotation]:
    """
    Get a list of PhoneAnnotations representing possible US phone numbers found
    in the text.
    """
    return list(get_us_phone_annotations(text))


def get_pii(text: str, return_sources: bool = False) -> Generator[tuple]:
    """
    Find possible PII references in the text.
    :param text:
    :param return_sources:
    :return:
    """

    for ssn in get_ssns(text, return_sources):
        if isinstance(ssn, (tuple, list)):
            row = ["ssn"]
            for v in ssn:
                row.append(v)
            yield tuple(row)
        else:
            yield "ssn", ssn

    for phone in get_us_phones(text, return_sources):
        if isinstance(phone, (tuple, list)):
            row = ["us_phone"]
            for v in phone:
                row.append(v)
            yield tuple(row)
        else:
            yield "us_phone", phone


def get_pii_list(text: str, return_sources: bool = False) -> list[tuple]:
    """
    Get a list of tuples representing PII references found in text.
    """
    return list(get_pii(text, return_sources))


def get_pii_annotations(text: str) -> Generator[TextAnnotation]:
    """
    Find possible PII references in the text.
    """

    yield from get_ssn_annotations(text)
    yield from get_us_phone_annotations(text)


def get_pii_annotation_list(text: str) -> list[TextAnnotation]:
    """
    Get a list of TextAnnotations representing PII references found in text.
    """
    return list(get_pii_annotations(text))
