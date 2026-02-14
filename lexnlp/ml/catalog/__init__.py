"""
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


# standard library
from pathlib import Path
from typing import Dict, Optional

# NLTK
import nltk.data


def _resolve_nltk_data_dir() -> Path:
    """
    Resolve a writable NLTK data directory for LexNLP assets.

    Historically LexNLP used ``nltk.data.find('')`` to discover the root of the
    NLTK data path. On fresh environments (e.g., CI runners), NLTK's internal
    implementation can raise when no candidate directories exist yet.

    This resolver prefers the first non-empty entry in ``nltk.data.path`` and
    creates it if needed. If none are usable, it falls back to ``~/nltk_data``.
    """
    candidates = [Path(p).expanduser() for p in nltk.data.path if p]
    candidates.append(Path.home() / "nltk_data")

    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
        except PermissionError:
            continue

    # Last resort: current working directory.
    fallback = Path.cwd() / "nltk_data"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _resolve_catalog_dir() -> Path:
    """
    Resolve and create the LexNLP catalog directory where model/data assets live.

    This directory is expected to exist for callers that scan the catalog.
    """
    root = _resolve_nltk_data_dir()
    catalog = root / "lexpredict-lexnlp"
    try:
        catalog.mkdir(parents=True, exist_ok=True)
        return catalog
    except PermissionError:
        # Fallback to a best-effort writable path.
        fallback = Path.cwd() / "nltk_data" / "lexpredict-lexnlp"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


CATALOG: Path = _resolve_catalog_dir()


def _build_tag_dict() -> Dict[str, Path]:
    """
    Builds a dictionary with the following structure:

    - keys (str): directory paths relative to CATALOG, each corresponding to GitHub release tags.
    - values (Path): file path under the directory ("tag").

    Returns:
        A dictionary.
    """
    return {
        str(path.parent.relative_to(CATALOG)): path
        for path in CATALOG.rglob('*')
        if path.is_file()
    }


def get_path_from_catalog(tag: str) -> Path:
    """
    Args:
        tag (str):

    Returns:
        A file path.
    """
    d: Dict[str, Path] = _build_tag_dict()
    path: Optional[Path] = d.get(tag)
    if path is None:
        raise FileNotFoundError(
            f'Could not find tag={tag} in CATALOG={CATALOG}. '
            f'Please download using `lexnlp.ml.catalog.download.download_github_release("{tag}")`'
        )
    else:
        return path
