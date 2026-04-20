
__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

from lexnlp.extract.all_locales.languages import DEFAULT_LANGUAGE, LANG_DE, LANG_EN, Locale
from lexnlp.extract.common.annotations.copyright_annotation import CopyrightAnnotation
from lexnlp.extract.de.copyrights import get_copyright_annotations as get_copyright_annotations_de
from lexnlp.extract.en.copyright import get_copyright_annotations as get_copyright_annotations_en

ROUTINE_BY_LOCALE = {
    LANG_EN.code: get_copyright_annotations_en,
    LANG_DE.code: get_copyright_annotations_de
}


def get_copyright_annotations(
        locale: str,
        text: str,
        return_sources: bool = False) -> \
        Generator[CopyrightAnnotation]:
    routine = ROUTINE_BY_LOCALE.get(Locale(locale).language, ROUTINE_BY_LOCALE[DEFAULT_LANGUAGE.code])
    yield from routine(text, return_sources)
