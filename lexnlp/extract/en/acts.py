__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Generator
from typing import Any

import regex as re

from lexnlp.extract.common.annotations.act_annotation import ActAnnotation
from lexnlp.extract.common.annotations.text_annotation import TextAnnotation

ACT_PARTS_RE = re.compile(r'''
(?P<text>
    (?:sections?\s+
        (?P<section>(?:\d+(?:\(\w\))*|,\s+|,?\s+and\s+)+)\s+of\s+the\s+
    )?
    (?P<act_name>
        (?:(?:[A-Z]\w+|[A-Z&]+|and|\d+(?:[a-z]{1,3})?),?\s*)*
        (?<=\s)Act
    )
    (?:\W+|$)
    (?:of\s+(?P<year>\d{4}))?
)''', re.VERBOSE | re.MULTILINE)


def get_acts(text: str) -> Generator[dict[str, Any]]:
    for act in get_acts_annotations(text):
        yield act.to_dictionary_legacy()


def get_act_list(*args, **kwargs) -> list[dict[str, str]]:
    return list(get_acts(*args, **kwargs))


def get_acts_annotations(text: str) -> Generator[ActAnnotation]:
    for match in ACT_PARTS_RE.finditer(text):  # type: re.Match
        captures = match.capturesdict()
        act_name = ''.join(captures.get('act_name') or [])
        year_str = ''.join(captures.get('year') or [])
        year = TextAnnotation.safe_cast(year_str, int)
        act = ActAnnotation(act_name=act_name,
                            coords=match.span(),
                            section=''.join(captures.get('section') or []),
                            year=year,
                            ambiguous=act_name == 'Act',
                            text=''.join(captures.get('text') or []),
                            locale='en')
        yield act


def get_acts_annotations_list(text: str) -> list[ActAnnotation]:
    return list(get_acts_annotations(text))
