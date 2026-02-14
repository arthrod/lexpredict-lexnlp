# Dependency Migration Runbook

This runbook is the operational guide for maintaining a modern, reproducible LexNLP environment with a zero-skip testing policy.

## 1) Toolchain Baseline

- Python: `3.11` (default), supported range in `pyproject.toml`: `>=3.10,<3.13`
- Packaging/dependencies: `pyproject.toml` + `uv.lock`
- Installer/runner: `uv`

Legacy files are retained for historical reproduction only:
- `Pipfile`
- `python-requirements.txt`
- `python-requirements-dev.txt`
- `python-requirements-full.txt`

## 2) Fresh Setup

```bash
cd /Users/jackeames/Downloads/LexNLP
uv python install 3.11
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -e ".[dev,test]"
```

## 3) Bootstrap Required Assets

```bash
# NLTK + required model artifact
./.venv/bin/python scripts/bootstrap_assets.py --nltk --contract-model

# Optional: Stanford assets for Stanford-gated tests
./.venv/bin/python scripts/bootstrap_assets.py --stanford

# Optional: Tika jars
./.venv/bin/python scripts/bootstrap_assets.py --tika
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
PATH=/opt/homebrew/opt/openjdk/bin:$PATH \
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

If bundled sklearn artifacts emit legacy-version warnings, re-serialize them on
the current runtime and re-run targeted tests. Example for date parser model:

```bash
./.venv/bin/python - <<'PY'
import joblib
joblib.dump(joblib.load("lexnlp/extract/en/date_model.pickle"), "lexnlp/extract/en/date_model.pickle", compress=3)
PY
```

## 8) Failure Triage

- `LookupError` for NLTK resources:
  - Re-run `scripts/bootstrap_assets.py --nltk`
- Contract tests failing with missing model tag:
  - Re-run `scripts/bootstrap_assets.py --contract-model`
- Stanford tests failing due missing jars/models:
  - Re-run `scripts/bootstrap_assets.py --stanford`
- Skip-audit failure:
  - Remove the marker, or add annotation:
    - `# skip-audit: issue=<ticket> expires=YYYY-MM-DD`
  - For approved legacy skips only, update `ci/skip_audit_allowlist.txt`
- Packaging smoke failure:
  - Ensure build artifacts are generated with `uv build` and install into a clean venv
