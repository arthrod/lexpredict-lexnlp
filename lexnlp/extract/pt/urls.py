"""URL extraction for Portuguese (pt-BR).

URLs follow RFC 3986 / RFC 3987 regardless of surrounding natural
language, so the pattern in :mod:`lexnlp.extract.en.urls` is fully reusable
for pt-BR text. To avoid duplicating that regex (and the maintenance
burden that would come with two copies drifting), this module re-exports
the EN extractors and locale-tags any annotations it produces as ``"pt"``.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Iterator

from lexnlp.extract.common.annotations.url_annotation import UrlAnnotation
from lexnlp.extract.en.urls import URL_PTN_RE, get_url_list, get_urls


def get_url_annotations(text: str) -> Iterator[UrlAnnotation]:
    """Yield :class:`UrlAnnotation` (locale ``"pt"``) for every URL in *text*.

    The underlying regex is locale-agnostic; this wrapper only swaps the
    ``locale`` field so downstream code can route the annotation through
    pt-BR pipelines.
    """
    for match in URL_PTN_RE.finditer(text):
        coords = match.span()
        yield UrlAnnotation(coords=coords, url=match.group(), text=match.group(), locale="pt")


def get_url_annotation_list(text: str) -> list[UrlAnnotation]:
    """Return all URL annotations in *text* as a list."""
    return list(get_url_annotations(text))


__all__ = [
    "URL_PTN_RE",
    "get_url_annotation_list",
    "get_url_annotations",
    "get_url_list",
    "get_urls",
]
