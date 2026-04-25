"""Hugging Face Hub mirror for the LexNLP model catalog.

Provides an optional fall-back to :func:`huggingface_hub.hf_hub_download`
so consumers can pull LexNLP model artifacts from the Hub when the GitHub
release backend is unavailable (e.g. in air-gapped CI). The import is
kept lazy so ``huggingface_hub`` remains an *optional* dependency.

Usage::

    from lexnlp.ml.catalog.hub import get_path_from_hub

    path = get_path_from_hub("addresses_clf", revision="v2.3.0")

The dependency is declared under the ``[hub]`` extra in
``pyproject.toml`` rather than as a hard runtime dependency.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import importlib
from pathlib import Path

DEFAULT_HUB_REPO: str = "lexpredict/lexnlp-models"


class HubUnavailableError(RuntimeError):
    """Raised when ``huggingface_hub`` is not importable."""


class HubMirrorError(RuntimeError):
    """Wraps any error raised by :func:`huggingface_hub.hf_hub_download`."""


def hub_is_available() -> bool:
    """Return ``True`` when :mod:`huggingface_hub` is importable."""
    try:
        importlib.import_module("huggingface_hub")
    except ImportError:
        return False
    return True


def get_path_from_hub(
    tag: str,
    *,
    repo_id: str = DEFAULT_HUB_REPO,
    revision: str | None = None,
) -> Path:
    """Download the artifact named ``tag`` from the Hub and return its path.

    Mirrors :func:`lexnlp.ml.catalog.get_path_from_catalog` in intent —
    the caller hands in the catalog tag, the function returns a local
    :class:`pathlib.Path`. ``revision`` pins a specific git revision of
    the Hub repo when supplied.
    """
    try:
        hub = importlib.import_module("huggingface_hub")
    except ImportError as exc:
        raise HubUnavailableError(
            "huggingface_hub is not installed. Install with `uv pip install lexnlp[hub]`."
        ) from exc

    try:
        local = hub.hf_hub_download(repo_id=repo_id, filename=tag, revision=revision)
    except Exception as exc:  # noqa: BLE001 — upstream error surface is broad
        raise HubMirrorError(f"Failed to fetch '{tag}' from Hub repo '{repo_id}': {exc}") from exc
    return Path(local)


__all__ = [
    "DEFAULT_HUB_REPO",
    "HubMirrorError",
    "HubUnavailableError",
    "get_path_from_hub",
    "hub_is_available",
]
