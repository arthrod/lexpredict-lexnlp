"""
Utilities to build and load a Python 3.11-compatible contract-type classifier.
"""

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


# standard library
import logging
import tarfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

# third-party imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from lexnlp.ml.model_io import dump_model, load_model


LOGGER = logging.getLogger(__name__)

LEGACY_CONTRACT_TYPE_TAG = "pipeline/contract-type/0.1"
RUNTIME_CONTRACT_TYPE_TAG = "pipeline/contract-type/0.2-runtime"
CONTRACT_TYPE_CORPUS_TAG = "corpus/contract-types/0.1"
CONTRACT_TYPE_MODEL_FILENAME = "pipeline_contract_type_classifier.skops"
# Legacy filename kept for backwards-compatible catalog lookups of
# pre-skops artifacts shipped with earlier releases.
LEGACY_CONTRACT_TYPE_MODEL_FILENAME = "pipeline_contract_type_classifier.cloudpickle"


def ensure_tag_downloaded(tag: str) -> Path:
    from lexnlp.ml.catalog import get_path_from_catalog
    from lexnlp.ml.catalog.download import download_github_release

    try:
        return get_path_from_catalog(tag)
    except FileNotFoundError:
        LOGGER.info("Catalog tag missing; downloading release tag=%s", tag)
        download_github_release(tag, prompt_user=False)
        return get_path_from_catalog(tag)


def load_pipeline_for_tag(tag: str) -> Pipeline:
    path = ensure_tag_downloaded(tag)
    # ``trusted=True`` because this path loads artifacts this project
    # produced itself (training pipelines pinned to sklearn estimators).
    return load_model(path, trusted=True)


def _extract_label(member_name: str) -> str:
    # Expected shape: CONTRACT_TYPES/<LABEL>/<filename>.txt
    parts: Sequence[str] = Path(member_name).parts
    if len(parts) < 3:
        raise ValueError(f"Unexpected corpus member path: {member_name}")
    return parts[-2]


def collect_contract_type_samples(
    archive_path: Path,
    *,
    max_docs_per_label: int,
    head_character_n: int,
) -> Tuple[List[str], List[str], Dict[str, int]]:
    if max_docs_per_label <= 0:
        raise ValueError("max_docs_per_label must be > 0")
    if head_character_n <= 0:
        raise ValueError("head_character_n must be > 0")

    texts: List[str] = []
    labels: List[str] = []
    counts: Dict[str, int] = defaultdict(int)

    with tarfile.open(archive_path, mode="r:*") as archive:
        # Sort member names for deterministic sampling across environments.
        members: Iterable[tarfile.TarInfo] = sorted(
            archive.getmembers(),
            key=lambda item: item.name,
        )
        for member in members:
            if not member.isfile() or not member.name.lower().endswith(".txt"):
                continue

            label = _extract_label(member.name)
            if counts[label] >= max_docs_per_label:
                continue

            file_obj = archive.extractfile(member)
            if file_obj is None:
                continue
            payload = file_obj.read(head_character_n * 2)
            text = payload.decode("utf-8", errors="ignore").strip()
            if not text:
                continue

            texts.append(text[:head_character_n])
            labels.append(label)
            counts[label] += 1

    if not texts:
        raise RuntimeError(f"No samples collected from {archive_path}")
    if len(set(labels)) < 2:
        raise RuntimeError(
            "Contract-type training requires at least two labels; "
            f"found {len(set(labels))}"
        )

    return texts, labels, dict(counts)


def train_contract_type_pipeline(
    texts: Sequence[str],
    labels: Sequence[str],
    *,
    random_state: int,
) -> Pipeline:
    if len(texts) != len(labels):
        raise ValueError("texts and labels length mismatch")

    pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_features=120000,
                    sublinear_tf=True,
                ),
            ),
            (
                "logistic_regression",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    multi_class="multinomial",
                    random_state=random_state,
                    solver="lbfgs",
                ),
            ),
        ]
    )
    pipeline.fit(texts, labels)
    return pipeline


def write_pipeline_to_catalog(
    *,
    pipeline: Pipeline,
    target_tag: str,
    force: bool,
) -> Tuple[Path, bool]:
    """
    Returns:
        A ``(destination_path, wrote)`` tuple where ``wrote`` is ``True`` when
        the pipeline was serialized to disk (i.e., either ``force`` was set or
        the destination did not already exist).
    """
    from lexnlp.ml.catalog import CATALOG

    destination_dir = CATALOG / target_tag
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination_path = destination_dir / CONTRACT_TYPE_MODEL_FILENAME
    legacy_destination_path = destination_dir / LEGACY_CONTRACT_TYPE_MODEL_FILENAME

    if not force and (destination_path.exists() or legacy_destination_path.exists()):
        existing = destination_path if destination_path.exists() else legacy_destination_path
        LOGGER.debug(
            "Artifact already exists, skipping write (force=False): %s",
            existing,
        )
        return existing, False

    written = dump_model(pipeline, destination_path)
    return written, True


def ensure_runtime_contract_type_model(
    *,
    target_tag: str = RUNTIME_CONTRACT_TYPE_TAG,
    force: bool = False,
    max_docs_per_label: int = 120,
    head_character_n: int = 4000,
    random_state: int = 7,
) -> Path:
    from lexnlp.ml.catalog import get_path_from_catalog

    if not force:
        try:
            return get_path_from_catalog(target_tag)
        except FileNotFoundError:
            pass

        # Prefer downloading a published runtime-compatible artifact when
        # available to avoid retraining in CI environments.
        try:
            return ensure_tag_downloaded(target_tag)
        except Exception as exc:
            LOGGER.warning(
                "Unable to download runtime contract-type model tag=%s; falling back to training. error=%s",
                target_tag,
                exc,
                exc_info=True,
            )

    corpus_archive = ensure_tag_downloaded(CONTRACT_TYPE_CORPUS_TAG)
    texts, labels, _counts = collect_contract_type_samples(
        corpus_archive,
        max_docs_per_label=max_docs_per_label,
        head_character_n=head_character_n,
    )
    pipeline = train_contract_type_pipeline(texts, labels, random_state=random_state)
    destination_path, _wrote = write_pipeline_to_catalog(
        pipeline=pipeline,
        target_tag=target_tag,
        force=True,
    )
    LOGGER.info("Trained runtime contract-type model tag=%s at %s", target_tag, destination_path)
    return destination_path
