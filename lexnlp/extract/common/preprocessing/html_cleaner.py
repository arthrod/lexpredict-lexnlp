"""HTML → plain-text cleaning helpers backed by ``beautifulsoup4`` + ``lxml``.

Contracts arrive as HTML surprisingly often (DocuShare exports, scraped
filings, Office-saved HTML). Feeding raw HTML into the extractors
produces noisy matches — tags, scripts, and style blocks look like
prose. This module turns HTML into the kind of clean plain text the
extractors already expect.

The module is deliberately small: a single ``html_to_text`` call covers
the common case, ``clean_html`` returns sanitised HTML when callers want
to keep structure, and ``extract_clauses`` gives structured-extraction
users the paragraph-level nodes they need.

``beautifulsoup4`` (``bs4``) is listed in ``pyproject.toml`` as a hard
runtime dependency, with ``lxml`` providing the parser backend. Both
were declared but never imported in the codebase before this module.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from collections.abc import Iterable

from bs4 import BeautifulSoup

# ``lxml`` is the fastest parser available to bs4 and round-trips
# malformed markup cleanly; we fall back to the stdlib ``html.parser``
# only when lxml is unavailable for some reason (e.g. wheels-less
# musllinux build environment).
try:  # pragma: no cover - import-time fallback
    import lxml  # noqa: F401  # imported for availability check only
    _DEFAULT_PARSER = "lxml"
except ImportError:  # pragma: no cover
    _DEFAULT_PARSER = "html.parser"


# Tags whose contents are not human-readable prose and should be dropped
# entirely before text extraction. Keeps the helper output focused on
# the actual contract body.
_NOISE_TAGS: tuple[str, ...] = ("script", "style", "noscript", "meta", "link")


def html_to_text(
    html: str,
    *,
    separator: str = "\n",
    strip: bool = True,
    parser: str | None = None,
) -> str:
    """Extract plain text from an HTML fragment.

    Args:
        html: The raw HTML string.
        separator: String used to join text from adjacent nodes. The default
            ``"\\n"`` preserves paragraph boundaries, which sentence
            segmenters then rely on.
        strip: If ``True``, whitespace is stripped from the text of each
            node before joining. Keeps the output free of stray spaces
            around tags.
        parser: Optional bs4 parser override (``"lxml"``, ``"html.parser"``,
            ``"html5lib"``). Defaults to ``lxml`` when installed.

    Returns:
        Plain text suitable for feeding into LexNLP extractors.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, parser or _DEFAULT_PARSER)
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()
    return soup.get_text(separator=separator, strip=strip)


def clean_html(
    html: str,
    *,
    drop_tags: Iterable[str] = _NOISE_TAGS,
    parser: str | None = None,
) -> str:
    """Return sanitised HTML with noise tags removed.

    Useful when downstream code still wants to parse structure (tables,
    headings) but not the boilerplate ``<script>``/``<style>`` chaff.

    Args:
        html: The raw HTML string.
        drop_tags: Tag names whose elements should be decomposed. Defaults
            to ``("script", "style", "noscript", "meta", "link")``.
        parser: Optional bs4 parser override; defaults to ``lxml``.

    Returns:
        The HTML serialised as a string after the drop-list tags have
        been removed.
    """
    if not html:
        return ""
    soup = BeautifulSoup(html, parser or _DEFAULT_PARSER)
    for tag in soup.find_all(tuple(drop_tags)):
        tag.decompose()
    return str(soup)


def extract_clauses(
    html: str,
    *,
    selector: str = "p, li, h1, h2, h3, h4, h5, h6",
    parser: str | None = None,
) -> list[str]:
    """Extract clause-level text nodes from an HTML contract.

    Many contracts wrap each clause in a ``<p>`` or list item. This
    helper returns the stripped text of every matching node so callers
    can run clause-level extractors (e.g. definitions, durations) in
    isolation instead of on the whole-document text blob.

    Args:
        html: The raw HTML string.
        selector: A CSS selector identifying clause-bearing nodes.
        parser: Optional bs4 parser override; defaults to ``lxml``.

    Returns:
        A list of stripped text fragments, one per matched node. Empty
        fragments are skipped so callers don't need to filter.
    """
    if not html:
        return []
    soup = BeautifulSoup(html, parser or _DEFAULT_PARSER)
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()
    fragments: list[str] = []
    for node in soup.select(selector):
        text = node.get_text(separator=" ", strip=True)
        if text:
            fragments.append(text)
    return fragments


__all__ = ["clean_html", "extract_clauses", "html_to_text"]
