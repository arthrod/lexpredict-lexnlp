"""Date extraction for Portuguese (pt-BR).

Built on top of dateparser's Portuguese locale, with additional heuristics for
Brazilian legal prose:

- Inherits years from a trailing anchor in a coordinated sequence
  ("15 de fevereiro, 28 de abril e 17 de novembro de 1995" → three dates in 1995).
- Normalises ordinal day markers ("1º de janeiro", "1.º de janeiro").
- Recognises the numeric Brazilian short form ``dd/mm/aaaa`` and the legal long
  form ``Brasília, 12 de março de 2024``.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import datetime
import string
from typing import Any

import regex as re

# noinspection PyUnresolvedReferences
from dateparser.data.date_translation_data.pt import info

from lexnlp.extract.all_locales.languages import Locale
from lexnlp.extract.common.annotations.date_annotation import DateAnnotation
from lexnlp.extract.common.dates import DateParser

_MONTHS_EN = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)

PT_MONTHS: list[str] = sorted(
    [y.lower() for k, v in info.items() if k in _MONTHS_EN for y in v],
    key=lambda i: (-len(i), i),
)

# Canonical month-name → month-number map used by the ordinal/Brasília
# shortcuts. We rebuild it from ``info`` so the two ordering variants
# (long/abbreviated) stay in sync.
_MONTH_NUMBER: dict[str, int] = {}
for english_month, idx in zip(_MONTHS_EN, range(1, 13), strict=True):
    for alias in info.get(english_month, []):
        _MONTH_NUMBER[alias.lower()] = idx

PT_ALPHABET = "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝàáâãäåæçèéêëìíîïðñòóôõöøùúûüýÿ"
DATE_MODEL_CHARS: list[str] = []
DATE_MODEL_CHARS.extend(PT_ALPHABET + string.ascii_letters)
DATE_MODEL_CHARS.extend(string.digits)
DATE_MODEL_CHARS.extend(["-", "/", " ", "%", "#", "$", "º", "ª"])


class PtDateParser(DateParser):
    """Portuguese date parser with Brazilian legal conventions."""

    DEFAULT_DATEPARSER_SETTINGS = {
        "PREFER_DAY_OF_MONTH": "first",
        "STRICT_PARSING": False,
        "DATE_ORDER": "DMY",
    }

    # Sequential phrases like "15 de fevereiro, 28 de abril e 17 de novembro de 1995"
    SEQUENTIAL_DATES_RE = re.compile(
        r"(?P<text>(?P<day>\d{{1,2}})(?:[ºª°]\s*|\s+)"
        r"de\s+(?P<month>{pt_months})(?:,\s|\s+e\s+|\s+de\s+(?P<year>\d{{4}})))".format(
            pt_months="|".join(PT_MONTHS),
        ),
        re.I | re.M,
    )

    # Ordinal date: "1º de janeiro", "1.º de janeiro de 2020", "01.° de junho".
    ORDINAL_DATES_RE = re.compile(
        r"(?P<day>\d{{1,2}})\s*(?:[ºª°]\.?|\.?[ºª°])\s*"
        r"de\s+(?P<month>{pt_months})"
        r"(?:\s+de\s+(?P<year>\d{{4}}))?".format(pt_months="|".join(PT_MONTHS)),
        re.I | re.M,
    )

    # "Brasília, 12 de março de 2024" / "Rio de Janeiro, 12 mar 2024"
    # Canonical Brazilian legal-gazette date.
    LOCALITY_DATE_RE = re.compile(
        r"(?:Brasília|Rio\s+de\s+Janeiro|São\s+Paulo|Belo\s+Horizonte|"
        r"Porto\s+Alegre|Salvador|Recife|Fortaleza|Manaus|Curitiba|Belém|"
        r"Goiânia|Florianópolis|Vitória),?\s+"
        r"(?P<day>\d{{1,2}})\s+de\s+(?P<month>{pt_months})\s+de\s+(?P<year>\d{{4}})".format(
            pt_months="|".join(PT_MONTHS),
        ),
        re.I | re.M,
    )

    # "15.02.2020" / "15-02-2020" / "15/02/2020" — Brazilian DMY numeric.
    NUMERIC_DMY_RE = re.compile(
        r"(?<!\d)(?P<day>\d{1,2})[./-](?P<month>\d{1,2})[./-](?P<year>\d{2,4})(?!\d)",
        re.I | re.M,
    )

    WEIRD_DATES_NORM = [
        (
            re.compile(
                r"(\d+[ºª°]\.?\s?de\s+(?:{pt_months})(?:\s+de\s+\d{{4}})?)".format(
                    pt_months="|".join(PT_MONTHS),
                ),
                re.I | re.M,
            ),
            lambda i: re.sub(r"\s*[ºª°]\.?\s*", " ", i),
        )
    ]

    # Surface-form rejects: dateparser on Portuguese text aggressively matches
    # abbreviated weekdays ("ter", "qui"), short prepositions or stray two-digit
    # numbers as dates. We require at least one digit AND some substance before
    # accepting the candidate.
    _SHORT_REJECT_RE = re.compile(r"^\s*(?:[a-zà-ÿ]{1,4}|\d{1,2}\s*[,;]?\s*[a-zà-ÿ]?)\s*$", re.I)
    _WEEKDAY_PREFIXES = frozenset(
        {
            "seg",
            "ter",
            "qua",
            "qui",
            "sex",
            "sab",
            "dom",
            "segunda",
            "terca",
            "terça",
            "quarta",
            "quinta",
            "sexta",
            "sabado",
            "sábado",
            "domingo",
        }
    )

    def __init__(
        self,
        text: str | None = None,
        locale: Locale = Locale("pt-BR"),
        dateparser_settings: dict[str, Any] | None = None,
        enable_classifier_check: bool = False,
        classifier_model: Any | None = None,
        classifier_threshold: float = 0.5,
    ):
        """
        Configure a PtDateParser for Brazilian Portuguese text with optional classifier validation.

        Parameters:
            text: Optional input text to parse; if omitted the parser is not preloaded with text.
            locale: Locale to use for parsing; defaults to Portuguese (pt-BR).
            dateparser_settings: Optional settings passed through to the underlying dateparser.
            enable_classifier_check: If True, enable post-extraction classifier validation.
            classifier_model: Optional classifier to use when classifier validation is enabled.
            classifier_threshold: Acceptance threshold for the classifier between 0.0 and 1.0.
        """
        super().__init__(
            DATE_MODEL_CHARS,
            text,
            locale,
            dateparser_settings,
            enable_classifier_check,
            classifier_model,
            classifier_threshold,
        )

    # ---------- helpers ----------

    def passed_general_check(self, date_str: str, _date) -> bool:
        """
        Decide whether a parsed date surface should be accepted by applying additional Portuguese-specific surface checks.

        Parameters:
            date_str (str): Candidate surface text for the date.
            _date: Parsed date value from the underlying parser (may be unused by this check).

        Returns:
            `true` if the candidate passes additional length, content, and weekday-prefix checks and should be kept, `false` otherwise.
        """
        if not super().passed_general_check(date_str, _date):
            return False
        token = date_str.strip()
        if not token or len(token) < 3:
            return False
        if self._SHORT_REJECT_RE.match(token):
            # Still allow numeric-only surfaces that look like a DMY candidate.
            if not re.search(r"\d{1,2}[./-]\d{1,2}", token):
                return False
        # Reject raw weekday abbreviations.
        first_word = re.split(r"[\s,.;]", token.lower(), maxsplit=1)[0]
        if first_word in self._WEEKDAY_PREFIXES and not re.search(r"\d{4}", token):
            return False
        return True

    @staticmethod
    def _coerce_year(raw: str) -> int | None:
        """
        Normalize a numeric year string into a four-digit calendar year.

        Parameters:
            raw (str): Year text, typically two or four digits.

        Returns:
            int | None: Four-digit year where `00`–`49` map to `2000`–`2049`, `50`–`99` map to `1950`–`1999`, and any empty or non-integer input yields `None`.
        """
        if not raw:
            return None
        try:
            val = int(raw)
        except (TypeError, ValueError):
            return None
        if val < 100:
            return 2000 + val if val < 50 else 1900 + val
        return val

    def _build_date(self, day: int, month: int, year: int | None) -> datetime.datetime | None:
        """
        Construct a validated datetime from day, month, and year, or return None if the components do not form a valid calendar date.

        Parameters:
            day (int): Day of month; must be between 1 and 31.
            month (int): Month number; must be between 1 and 12.
            year (int | None): Four-digit year to use; if falsy (`None` or `0`), the current calendar year is used.

        Returns:
            datetime.datetime | None: The constructed datetime for the supplied date, or `None` if the inputs are out of range or represent an impossible date (e.g., April 31).
        """
        if not (1 <= day <= 31 and 1 <= month <= 12):
            return None
        y = year or datetime.datetime.now().year
        try:
            return datetime.datetime(y, month, day)
        except ValueError:
            return None

    # ---------- extra pattern extraction ----------

    def get_extra_dates(self, strict: bool) -> None:
        """
        Extend the parser's `dates` list with additional Brazilian Portuguese date forms and inferred years.

        This adds dates found by: inheriting trailing years in coordinated sequences (e.g., "15 de fevereiro, 28 de abril e 17 de novembro de 1995"), normalizing ordinal day glyphs before parsing (e.g., "1º de janeiro"), extracting locality-prefixed legal-gazette dates (e.g., "Brasília, 12 de março de 2024") and numeric DMY forms including two-digit years and dot-separated variants; results are de-duplicated and stored back to `self.dates`.

        Parameters:
            strict (bool): If True, require strict parsing when re-parsing normalized or derived date substrings; passed through to the underlying dateparser-based parsing helpers.
        """
        dateparser_dates_dict = {i[0]: i for i in self.dates}

        # 1. Year inheritance across "A, B e C de YYYY" sequences.
        last_match_start: int | None = None
        last_match_year: int | None = None
        dates_rev = reversed(list(self.SEQUENTIAL_DATES_RE.finditer(self.text)))
        for match in dates_rev:
            capture = match.capturesdict()
            capture_text = "".join(capture["text"]).strip(",e ")
            match_start, match_end = match.span()
            if capture["year"]:
                last_match_year = int("".join(capture["year"]))
                if capture_text not in dateparser_dates_dict:
                    parsed = self.get_dateparser_dates(capture_text, strict)
                    if parsed:
                        dateparser_dates_dict[parsed[0][0]] = parsed[0]
            elif last_match_year and last_match_start is not None and last_match_start == match_end:
                if capture_text not in dateparser_dates_dict:
                    parsed = self.get_dateparser_dates(capture_text, strict)
                    if parsed:
                        date_str, a_date = parsed[0]
                        a_date = a_date.replace(year=last_match_year)
                        dateparser_dates_dict[date_str] = (capture_text, a_date)
                else:
                    a_date = dateparser_dates_dict[capture_text][1].replace(year=last_match_year)
                    dateparser_dates_dict[capture_text] = (
                        dateparser_dates_dict[capture_text][0],
                        a_date,
                    )
            last_match_start = match_start

        dates = list(dateparser_dates_dict.values())

        # 2. Ordinal form ("1º de janeiro [de YYYY]") — strip the ordinal glyph
        #    and re-feed the normalised form to dateparser.
        for w_date_re, w_date_norm in self.WEIRD_DATES_NORM:
            for w_date_str in w_date_re.findall(self.text):
                date_str = w_date_norm(w_date_str)
                parsed = self.get_dateparser_dates(date_str, strict)
                if parsed:
                    dates.append((w_date_str, parsed[0][1]))

        # 3. Locality-prefixed Brazilian legal dates ("Brasília, 12 de março de 2024").
        for m in self.LOCALITY_DATE_RE.finditer(self.text):
            try:
                day = int(m.group("day"))
                month = _MONTH_NUMBER.get(m.group("month").lower())
                year = int(m.group("year"))
            except (TypeError, ValueError):
                continue
            if not month:
                continue
            dt = self._build_date(day, month, year)
            if dt:
                surface = m.group(0)
                # Only keep the date portion, not the locality prefix, so the
                # annotation coords land on the actual date span.
                date_portion_start = m.start("day")
                dates.append((self.text[date_portion_start : m.end()], dt))

        # 4. Brazilian numeric DMY. dateparser already handles a lot of this but
        #    we explicitly cover 2-digit years and `.`-separated variants which
        #    are common in legal e-filing.
        for m in self.NUMERIC_DMY_RE.finditer(self.text):
            day = int(m.group("day"))
            month = int(m.group("month"))
            year = self._coerce_year(m.group("year"))
            dt = self._build_date(day, month, year)
            if dt:
                dates.append((m.group(0), dt))

        # De-duplicate by (surface, date) pair while preserving order.
        seen: set[tuple[str, datetime.datetime]] = set()
        unique: list[tuple[str, datetime.datetime]] = []
        for surface, dt in dates:
            key = (surface, dt)
            if key in seen:
                continue
            seen.add(key)
            unique.append((surface, dt))
        self.dates = unique


parser = PtDateParser(
    enable_classifier_check=False,
    locale=Locale("pt-BR"),
    dateparser_settings={
        "PREFER_DAY_OF_MONTH": "first",
        "STRICT_PARSING": False,
        "DATE_ORDER": "DMY",
    },
)


get_dates = parser.get_dates
get_date_list = parser.get_date_list
get_date_annotations = parser.get_date_annotations
get_date_annotation_list = parser.get_date_annotation_list


__all__ = [
    "DATE_MODEL_CHARS",
    "PT_MONTHS",
    "DateAnnotation",
    "PtDateParser",
    "get_date_annotation_list",
    "get_date_annotations",
    "get_date_list",
    "get_dates",
    "parser",
]
