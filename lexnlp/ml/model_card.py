"""Skops-based model-card generation for LexNLP artifacts.

Every release pipeline that serialises an estimator with
:func:`lexnlp.ml.model_io.dump_model` can now emit a sibling
``.md`` model card so consumers see the description, license, metrics
and hyperparameters inline with the artifact.

The module is a thin, typed wrapper around :mod:`skops.card` — it does
not add new dependencies (``skops`` is already a hard runtime
dependency of LexNLP).
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from lexnlp.ml.model_io import dump_model


@dataclass(frozen=True, slots=True)
class ModelCardMetadata:
    """Minimal metadata block used by :func:`write_model_card`."""

    description: str
    license: str = ""
    authors: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ModelArtifacts:
    """Pair of paths returned by :func:`dump_model_with_card`."""

    model: Path
    card: Path


def write_model_card(
    estimator: Any,
    path: str | Path,
    *,
    metadata: ModelCardMetadata,
    metrics: dict[str, float] | None = None,
) -> Path:
    """Render a skops model card for ``estimator`` and write it to ``path``.

    ``path`` is normalised to end with ``.md``. Returns the path actually
    written.
    """
    from skops import card

    dest = Path(path)
    if dest.suffix.lower() != ".md":
        dest = dest.with_suffix(".md")
    dest.parent.mkdir(parents=True, exist_ok=True)

    c = card.Card(estimator)
    c.add(description=metadata.description)
    if metadata.license:
        c.add(license=metadata.license)
    if metadata.authors:
        c.add(authors=metadata.authors)
    if metadata.tags:
        c.add(tags=", ".join(metadata.tags))
    if metrics:
        c.add_metrics(**{k: str(v) for k, v in metrics.items()})
    dest.write_text(c.render(), encoding="utf-8")
    return dest


def dump_model_with_card(
    estimator: Any,
    path: str | Path,
    *,
    metadata: ModelCardMetadata,
    metrics: dict[str, float] | None = None,
) -> ModelArtifacts:
    """Persist ``estimator`` as a ``.skops`` artifact plus a sibling ``.md`` card."""
    base = Path(path)
    model_path = dump_model(estimator, base)
    card_path = write_model_card(
        estimator,
        model_path.with_suffix(".md"),
        metadata=metadata,
        metrics=metrics,
    )
    return ModelArtifacts(model=model_path, card=card_path)


__all__ = [
    "ModelArtifacts",
    "ModelCardMetadata",
    "dump_model_with_card",
    "write_model_card",
]
