__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator
from datetime import datetime

from lexnlp.extract.all_locales.languages import DEFAULT_LANGUAGE, LANG_DE, LANG_EN, LANG_PT, Locale
from lexnlp.extract.common.annotations.date_annotation import DateAnnotation
from lexnlp.extract.de.dates import get_date_annotations as get_date_annotations_de
from lexnlp.extract.en.dates import get_date_annotations as get_date_annotations_en
from lexnlp.extract.pt.dates import get_date_annotations as get_date_annotations_pt

ROUTINE_BY_LOCALE = {
    LANG_EN.code: get_date_annotations_en,
    LANG_DE.code: get_date_annotations_de,
    LANG_PT.code: get_date_annotations_pt,
}


def get_date_annotations(
    locale: str, text: str, strict: bool | None = None, base_date: datetime | None = None, threshold: float = 0.50
) -> Generator[DateAnnotation]:
    routine = ROUTINE_BY_LOCALE.get(Locale(locale).language, ROUTINE_BY_LOCALE[DEFAULT_LANGUAGE.code])
    yield from routine(text, strict, locale, base_date, threshold)
