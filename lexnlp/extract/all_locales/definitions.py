
__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator

from lexnlp.extract.all_locales.languages import DEFAULT_LANGUAGE, LANG_DE, LANG_EN, LANG_PT, Locale
from lexnlp.extract.common.annotations.definition_annotation import DefinitionAnnotation
from lexnlp.extract.de.definitions import get_definition_annotations as get_definition_annotations_de
from lexnlp.extract.en.definitions import get_definition_annotations as get_definition_annotations_en
from lexnlp.extract.pt.definitions import get_definition_annotations as get_definition_annotations_pt

ROUTINE_BY_LOCALE = {
    LANG_EN.code: get_definition_annotations_en,
    LANG_DE.code: get_definition_annotations_de,
    LANG_PT.code: get_definition_annotations_pt,
}


def get_definition_annotations(
        locale: str,
        text: str,
        **kwargs) \
        -> Generator[DefinitionAnnotation]:
    routine = ROUTINE_BY_LOCALE.get(Locale(locale).language, ROUTINE_BY_LOCALE[DEFAULT_LANGUAGE.code])
    yield from routine(text, **kwargs)
