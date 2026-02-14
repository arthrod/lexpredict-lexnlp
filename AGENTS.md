# AGENTS.md

This document is a quick-start guide for coding agents working in this repository.

## Project Summary

- Project: `lexpredict-lexnlp` (LexNLP)
- Purpose: legal-text NLP and information extraction library
- Primary package: `lexnlp/`
- Packaging: `pyproject.toml` (setuptools backend; version in repo: `2.3.0`)
- Python requirement in `pyproject.toml`: `>=3.10,<3.13` (default to Python `3.11`)

## Directory Structure

```text
.
|-- lexnlp/                     # Main package
|   |-- config/                 # Locale-specific configuration (en, de, es)
|   |-- extract/                # Extraction modules by locale and domain
|   |   |-- common/
|   |   |-- en/
|   |   |-- de/
|   |   |-- es/
|   |   `-- ml/
|   |-- ml/                     # ML utilities/catalog helpers
|   |-- nlp/                    # NLP components and training helpers
|   |-- tests/                  # Shared test helpers + tests
|   `-- utils/                  # Utility modules and utility tests
|-- test_data/                  # Fixtures, sample inputs, expected outputs
|-- scripts/                    # Helper scripts (Tika, release, data helpers)
|-- libs/                       # Download/runtime helper scripts and assets
|-- notebooks/                  # Exploratory notebooks by topic
|-- documentation/              # Sphinx docs source
|-- pyproject.toml              # Canonical packaging/dependency metadata
|-- python-requirements.txt     # Deprecated legacy dependency snapshot
|-- python-requirements-dev.txt # Deprecated legacy dev/test snapshot
|-- Pipfile                     # Deprecated legacy pipenv workflow
|-- .pylintrc                   # Lint configuration
|-- .travis.yml                 # Historical CI reference
|-- setup.py                    # Legacy compatibility wrapper
`-- AGENTS.md
```

## Environment Setup (Recommended: uv)

Use Python 3.11 in a local `.venv`.

```bash
cd /Users/jackeames/Downloads/LexNLP
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[dev,test]"
```

### Deprecated setup variants

`Pipfile`, `python-requirements.txt`, and `python-requirements-dev.txt` are deprecated. Use `uv` with `pyproject.toml` for all new local setup and CI updates.

## Required Runtime/Test Assets

Use the bootstrap script for deterministic setup:

```bash
./.venv/bin/python scripts/bootstrap_assets.py --nltk --contract-model --contract-type-model
```

Optional assets:

```bash
# Stanford
./.venv/bin/python scripts/bootstrap_assets.py --stanford

# Tika
./.venv/bin/python scripts/bootstrap_assets.py --tika
```

## Stanford-Dependent Tests

Stanford tests are gated by `LEXNLP_USE_STANFORD=true`.

1. Install Java:
```bash
brew install openjdk
```

2. Ensure Java is on path for test commands:
```bash
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"
```

3. Download Stanford assets to `libs/stanford_nlp`:
- `stanford-postagger-full-2017-06-09`
- `stanford-ner-2017-06-09`

Expected files:
- `libs/stanford_nlp/stanford-postagger-full-2017-06-09/stanford-postagger.jar`
- `libs/stanford_nlp/stanford-postagger-full-2017-06-09/models/english-bidirectional-distsim.tagger`
- `libs/stanford_nlp/stanford-ner-2017-06-09/stanford-ner.jar`
- `libs/stanford_nlp/stanford-ner-2017-06-09/classifiers/english.all.3class.distsim.crf.ser.gz`

## Tika Notes

`scripts/download_tika.sh` can fail on macOS because it assumes GNU `mkdir --parents` and `wget`.
If needed, manually download `tika-app-1.16.jar` and `tika-server-1.16.jar` into `bin/` using `curl`.

Migration and troubleshooting details are in `MIGRATION_RUNBOOK.md`.

## Test Integrity Policy

- Do not add, remove, or modify `skip`, `skipif`, or `xfail` markers to bypass failures.
- Fix failing behavior or document a real external blocker; never mask regressions by changing skip behavior.
- Validation target is **100% pass** for required suites.

## Full Validation Commands (100% pass target)

Run in two phases:

1. Base suite:
```bash
./.venv/bin/pytest lexnlp
```

2. Stanford-only suite:
```bash
PATH=/opt/homebrew/opt/openjdk/bin:$PATH \
LEXNLP_USE_STANFORD=true \
./.venv/bin/pytest \
  lexnlp/nlp/en/tests/test_stanford.py \
  lexnlp/extract/en/entities/tests/test_stanford_ner.py
```

When Stanford assets are installed and enabled, both phases must pass (0 failures) for a **100% pass** result.

Note: a single monolithic `LEXNLP_USE_STANFORD=true` run can occasionally hang in non-Stanford modules on this machine, so prefer the two-phase approach.

## Common Commands

```bash
# quick dependency sanity
./.venv/bin/pip check

# packaging content sanity
python3 ci/check_dist_contents.py

# contract model quality gate (baseline metrics)
./.venv/bin/python scripts/model_quality_gate.py \
  --baseline-tag pipeline/is-contract/0.1 \
  --candidate-tag pipeline/is-contract/0.1 \
  --baseline-metrics-json test_data/model_quality/is_contract_baseline_metrics.json

# build a runtime-compatible contract-type model artifact
./.venv/bin/python scripts/train_contract_type_model.py \
  --target-tag pipeline/contract-type/0.2-runtime

# create a re-exported candidate model tag and validate it
./.venv/bin/python scripts/reexport_contract_model.py \
  --source-tag pipeline/is-contract/0.1 \
  --target-tag pipeline/is-contract/0.2 \
  --baseline-metrics-json test_data/model_quality/is_contract_baseline_metrics.json

# run one file
./.venv/bin/pytest lexnlp/extract/en/tests/test_dates.py

# historical CI-style command
./.venv/bin/pytest --cov lexnlp --pylint --pylint-rcfile=.pylintrc lexnlp
```

## Implementation Guidelines

- Keep changes scoped to the relevant locale/module (`extract/en`, `extract/de`, etc.).
- Add or update tests alongside behavior changes.
- Prefer existing utilities under `lexnlp/utils/` over introducing duplicates.
- When adding extraction patterns/models, include representative fixtures in `test_data/`.
- Avoid committing downloaded/generated third-party assets unless explicitly required.

## Pull Request Checklist

- Editable install works: `uv pip install --python .venv/bin/python -e ".[dev,test]"`
- Targeted tests for changed modules pass.
- Full base run (`pytest lexnlp`) passes.
- If Stanford assets are enabled, Stanford-only suite with `LEXNLP_USE_STANFORD=true` passes.
- Contract model quality gate passes against `test_data/model_quality/is_contract_baseline_metrics.json`.
- Contract-type smoke flow works (`scripts/bootstrap_assets.py --contract-type-model` + predictor instantiation).
- No `skip`/`skipif`/`xfail` policy bypasses were introduced.
- Document any required asset downloads (NLTK, pipeline models, Stanford, Tika) in PR notes.
