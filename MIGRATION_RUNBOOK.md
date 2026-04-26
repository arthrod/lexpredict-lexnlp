# Dependency Migration Runbook

This runbook is the operational guide for maintaining a modern, reproducible LexNLP environment with a zero-skip testing policy.

## 1) Toolchain Baseline

- Python: `3.13` (default), supported range in `pyproject.toml`: `>=3.13,<3.15`
- Packaging/dependencies: `pyproject.toml` + `uv.lock`
- Installer/runner: `uv`
- Build backend: `uv_build` (Astral's native backend)

Legacy files are retained for historical reproduction only:
- `python-requirements.txt`
- `python-requirements-dev.txt`
- `python-requirements-full.txt`

`Pipfile` / `Pipfile.lock` have been removed; `ci/check_dist_contents.py`
still bans both filenames from built artifacts.

Optional dependency extras (off by default):

| Extra | Pin | Powers |
| --- | --- | --- |
| `[arrow]` | `pyarrow>=17` | `read_csv_arrow`; PyArrow-backed extraction DataFrames |
| `[hub]` | `huggingface_hub>=0.25` | `lexnlp.ml.catalog.hub` HF Hub mirror downloads |
| `[ner]` | `spacy>=3.7` | Optional spaCy backend for `lexnlp.extract.ner` (default backend is NLTK) |
| `[tika]` | `tika>=2.6.0` | Apache Tika document-parsing helpers |
| `[stanford]` | _(empty)_ | Hooks for Stanford CoreNLP (callers ship their own jars) |

## 2) Fresh Setup

```bash
cd /path/to/LexNLP
uv python install 3.13
uv venv --python 3.13 .venv
uv sync --frozen --python .venv/bin/python --extra dev --extra test
```

Notes:
- `uv sync` installs the project editable by default (good for local development).
- If you want a non-editable install (closer to a wheel install), add `--no-editable`.

```bash
# Only needed if you used --no-install-project above:
uv pip install --python .venv/bin/python -e ".[dev,test]"
```

## 3) Bootstrap Required Assets

```bash
# NLTK + required model artifacts
./.venv/bin/python scripts/bootstrap_assets.py --nltk --contract-model --contract-type-model

# Optional: Stanford assets for Stanford-gated tests
./.venv/bin/python scripts/bootstrap_assets.py --stanford

# Optional: Tika jars
./.venv/bin/python scripts/bootstrap_assets.py --tika

# Default `lexnlp.extract.ner` backend uses NLTK's chunker; ensure the
# four corpora are installed (idempotent; safe to re-run):
./.venv/bin/python -c "import nltk; [nltk.download(p) for p in ('punkt_tab', 'averaged_perceptron_tagger_eng', 'maxent_ne_chunker_tab', 'words')]"

# Opt into the spaCy backend for `lexnlp.extract.ner` (only needed when
# callers pass `prefer_spacy=True` or use SpacyTokenSequenceClassifierModel):
uv pip install --python .venv/bin/python -e ".[ner]"
./.venv/bin/python -m spacy download en_core_web_sm
# (or override the model name via `LEXNLP_SPACY_MODEL=<package>`)
```

## 4) Policy Checks

```bash
# Fail if unapproved skip/skipif/xfail markers were added
./.venv/bin/python ci/skip_audit.py
```

## 5) Full Validation (100% pass target)

```bash
# Base suite
./.venv/bin/pytest lexnlp

# Stanford-only suite (requires Stanford assets + Java)
PATH=/opt/homebrew/opt/openjdk@11/bin:$PATH \
LEXNLP_USE_STANFORD=true \
./.venv/bin/pytest \
  lexnlp/nlp/en/tests/test_stanford.py \
  lexnlp/extract/en/entities/tests/test_stanford_ner.py
```

Passing both commands is the required 100% result for a fully provisioned environment.

## 6) Packaging Validation

```bash
uv build
python3 ci/check_dist_contents.py
uv venv --python 3.11 .venv-smoke
uv pip install --python .venv-smoke/bin/python dist/*.whl
.venv-smoke/bin/python -c "import lexnlp; print(lexnlp.__version__)"
```

## 7) Model Upgrade Quality Gate

Use the quality gate script before adopting a new contract-model artifact.

The committed baseline metrics file is:
- `test_data/model_quality/is_contract_baseline_metrics.json`

To create a modern candidate artifact by re-serializing the baseline model
under the current runtime (Python/scikit-learn), use:

```bash
./.venv/bin/python scripts/reexport_contract_model.py \
  --source-tag pipeline/is-contract/0.1 \
  --target-tag pipeline/is-contract/0.2 \
  --baseline-metrics-json test_data/model_quality/is_contract_baseline_metrics.json
```

This writes model-export metadata to
`artifacts/model_reexports/pipeline__is-contract__0.2.metadata.json` by default.

### Retrain candidate classifier from corpora (phase 2 path)

For a fuller upgrade than pure re-serialization, train a new classifier while
reusing LexNLP baseline preprocessing/vectorization steps:

```bash
./.venv/bin/python scripts/train_contract_model.py \
  --baseline-tag pipeline/is-contract/0.1 \
  --candidate-tag pipeline/is-contract/0.2 \
  --baseline-metrics-json test_data/model_quality/is_contract_baseline_metrics.json \
  --max-f1-regression 0.0 \
  --max-accuracy-regression 0.0 \
  --force
```

Training report output:
- `artifacts/model_training/contract_model_training_report.json`

The script automatically:
- downloads configured corpora tags if missing,
- trains multiple estimator candidates,
- selects best by validation metrics (F1 first),
- writes candidate artifact to catalog,
- runs `scripts/model_quality_gate.py` unless skipped.

Candidate evaluation command:

```bash
./.venv/bin/python scripts/model_quality_gate.py \
  --baseline-tag pipeline/is-contract/0.1 \
  --candidate-tag pipeline/is-contract/0.2 \
  --baseline-metrics-json test_data/model_quality/is_contract_baseline_metrics.json \
  --fixture test_data/lexnlp/extract/en/contracts/tests/test_contracts/test_is_contract.csv \
  --max-f1-regression 0.0 \
  --max-accuracy-regression 0.0
```

Default policy is non-regression against baseline metrics from
`pipeline/is-contract/0.1` on the fixed fixture above.

### Runtime model-tag overrides

Predictors can select newer validated tags without API/signature changes:

```bash
# is-contract classifier
export LEXNLP_IS_CONTRACT_MODEL_TAG="pipeline/is-contract/0.2"

# contract-type classifier
export LEXNLP_CONTRACT_TYPE_MODEL_TAG="pipeline/contract-type/0.2-runtime"
```

### Models repo override (advanced)

By default, model/corpus tags are downloaded from the upstream LexPredict
repository via the GitHub API (`lexnlp.DEFAULT_MODELS_REPO`).

For forks or air-gapped mirrors, you can redirect downloads:

```bash
# Option A: set a full GitHub API base URL (must point at `/releases/tags/`)
export LEXNLP_MODELS_REPO="https://api.github.com/repos/<owner>/<repo>/releases/tags/"

# Option B: set the slug (LexNLP constructs the GitHub API tags endpoint)
export LEXNLP_MODELS_REPO_SLUG="<owner>/<repo>"
```

### Contract-type runtime fallback model

The legacy `pipeline/contract-type/0.1` artifact may fail to unpickle on modern
Python runtimes. LexNLP now supports a deterministic runtime-compatible fallback
artifact (`pipeline/contract-type/0.2-runtime`) trained from
`corpus/contract-types/0.1`.

The committed contract-type fixture and baseline metrics file are:
- Fixture: `test_data/lexnlp/extract/en/contracts/tests/test_contracts/test_contract_type.csv`
- Baseline: `test_data/model_quality/contract_type_baseline_metrics.json`

Run the contract-type quality gate:

```bash
./.venv/bin/python scripts/contract_type_quality_gate.py \
  --baseline-tag pipeline/contract-type/0.2-runtime \
  --candidate-tag pipeline/contract-type/0.2-runtime \
  --baseline-metrics-json test_data/model_quality/contract_type_baseline_metrics.json \
  --output-json artifacts/contract_type_quality_gate.json \
  --max-accuracy-top1-regression 0.0 \
  --max-accuracy-topn-regression 0.0 \
  --max-f1-macro-regression 0.0 \
  --max-f1-weighted-regression 0.0
```

Build/rebuild it explicitly:

```bash
./.venv/bin/python scripts/bootstrap_assets.py --contract-type-model
```

Or run full training with report output:

```bash
./.venv/bin/python scripts/train_contract_type_model.py \
  --target-tag pipeline/contract-type/0.2-runtime \
  --output-json artifacts/model_training/contract_type_model_training_report.json
```

On first use of `ProbabilityPredictorContractType`, if legacy default loading
fails and no env override is set, LexNLP automatically builds/loads this runtime
fallback tag.

If baseline-tag model behavior is intentionally changed, regenerate and review
the baseline metrics file in the same PR:

```bash
./.venv/bin/python scripts/model_quality_gate.py \
  --baseline-tag pipeline/is-contract/0.1 \
  --candidate-tag pipeline/is-contract/0.1 \
  --fixture test_data/lexnlp/extract/en/contracts/tests/test_contracts/test_is_contract.csv \
  --write-baseline-metrics-json test_data/model_quality/is_contract_baseline_metrics.json
```

### Refresh bundled sklearn artifacts

The 10 bundled sklearn artifacts that previously shipped as `.pickle`
files (`lexnlp/extract/{de,en}/...`, `lexnlp/extract/en/addresses/`,
`lexnlp/extract/ml/en/data/`, `lexnlp/nlp/en/segments/`) were re-exported
as `.skops` siblings on `claude/review-pr-comments-HTZkT`. Loaders use
`lexnlp.ml.model_io.load_bundled_model(legacy_path)` which prefers the
`.skops` sibling and falls back to a legacy pickle when present. To
re-run the migration on a downstream fork (default mode is `--format
skops`; use `--format pickle` for the legacy joblib re-dump):

```bash
# Default: write ``.skops`` siblings (preferred)
./.venv/bin/python scripts/reexport_bundled_sklearn_models.py

# Optionally delete the legacy ``.pickle`` after a successful skops export
./.venv/bin/python scripts/reexport_bundled_sklearn_models.py --remove-legacy

# Legacy mode: re-dump the existing ``.pickle`` via joblib (no format change)
./.venv/bin/python scripts/reexport_bundled_sklearn_models.py --format pickle
```

The script reuses
`lexnlp.ml.model_io._patched_sklearn_tree_loader` so pre-1.3 tree node
arrays gain the missing `missing_go_to_left` byte on the fly, and it
strips stray `pandas.Index` attributes (which carry an unreducible
`BlockValuesRefs` under pandas 2) before handing the pipeline to
`skops.io.dump`.

## 8) Failure Triage

- `LookupError` for NLTK resources:
  - Re-run `scripts/bootstrap_assets.py --nltk`
  - For `lexnlp.extract.ner`'s default NLTK backend, also run the four
    corpora downloads listed in §3.
- Contract tests failing with missing model tag:
  - Re-run `scripts/bootstrap_assets.py --contract-model`
- Stanford tests failing due missing jars/models:
  - Re-run `scripts/bootstrap_assets.py --stanford`
- `OSError: [E050] Can't find model 'en_core_web_sm'`:
  - Either install it (`python -m spacy download en_core_web_sm`) and
    pass `prefer_spacy=True`, or rely on the default NLTK backend (no
    spaCy install required).
- `ValueError: node array from the pickle has an incompatible dtype`:
  - The bundled `.pickle` artifacts must be replaced by `.skops`
    siblings. Run
    `scripts/reexport_bundled_sklearn_models.py --format skops` and
    confirm `lexnlp/.../*.skops` exists alongside (or replaces) each
    legacy pickle. See §7 ("Refresh bundled sklearn artifacts").
- Skip-audit failure:
  - Remove the marker, or add annotation:
    - `# skip-audit: issue=<ticket> expires=YYYY-MM-DD`
  - In rare cases where annotation is not feasible, allowlist the marker:
    - Use the stable key format (not line-number based)
    - Generate keys with: `python ci/skip_audit.py --print-markers`
    - Add the stable key to `ci/skip_audit_allowlist.txt`
- Packaging smoke failure:
  - Ensure build artifacts are generated with `uv build` and install into a clean venv
