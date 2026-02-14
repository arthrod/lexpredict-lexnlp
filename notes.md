# LexNLP Dependency Modernization Notes

Date: February 14, 2026
Repo: `/Users/jackeames/Downloads/LexNLP`

## Objective

Modernize dependency and test tooling so LexNLP is reproducible with `uv`, Python 3.11, and a strict no-test-bypass policy while keeping behavior stable.

## What was required

1. Move install/runtime metadata to `pyproject.toml` and lock with `uv.lock`.
2. Align dependency versions to combinations that build and run on modern Python.
3. Make optional runtime assets deterministic (NLTK, contract model, Stanford, optional Tika).
4. Enforce test integrity (no new skip/xfail bypasses).
5. Verify packaging artifacts are clean and installable.

## Issues encountered and how they were fixed

### 1) Legacy dependency pins were not viable on current interpreters/toolchains
- Problem: historical pins were brittle on newer Python/packaging tooling.
- Fix: standardized on Python 3.11 and curated compatible ranges in `pyproject.toml`, then generated and used `uv.lock` in CI/local runs.

### 2) Serialized sklearn artifacts were loaded under newer sklearn
- Problem: older serialized models triggered compatibility warnings and runtime attribute mismatches (notably GaussianNB legacy attributes).
- Fix: pinned to `scikit-learn>=1.2.2,<1.3` and added compatibility handling in `lexnlp/ml/predictor.py` for legacy `sigma_` data.

### 3) Pandas API drift broke a parser path
- Problem: deprecated `error_bad_lines` behavior caused incompatibility on modern pandas.
- Fix: updated `lexnlp/extract/es/regulations.py` to use `on_bad_lines='skip'` with backward-compatible fallback.

### 4) Test reliability depended on non-Python assets
- Problem: failing/skipped tests when corpora/models/Stanford jars were missing.
- Fix: introduced `scripts/bootstrap_assets.py` with deterministic flags for:
  - NLTK corpora
  - contract model artifact
  - Stanford jars/models (plus Java requirement)
  - optional Tika

### 5) Skips/xfails could hide regressions
- Problem: policy needed to prevent making builds green by bypassing tests.
- Fix: added `ci/skip_audit.py` and `ci/skip_audit_allowlist.txt`, wired into CI to fail on unapproved new skip/xfail markers.

### 6) Packaging artifacts included unwanted content risk
- Problem: release artifacts could unintentionally include local runtime blobs (`libs/stanford_nlp`), bytecode caches, and deprecated manifest files.
- Fix:
  - tightened `MANIFEST.in`
  - added `ci/check_dist_contents.py`
  - enforced artifact content audit in CI packaging job

## Final validation results

- Skip audit: `skip-audit: OK (markers=11, allowlisted=11, annotated_new=0)`
- Base suite (`./.venv311/bin/python -m pytest -q`): `497 passed, 11 skipped, 0 failed`
- Stanford-gated suite (`LEXNLP_USE_STANFORD=true` targeted files): `11 passed, 0 failed`
- Net demonstrated pass count: `508/508`
- Packaging:
  - `uv build` succeeds
  - `python3 ci/check_dist_contents.py` succeeds
- wheel install smoke test succeeds and imports `lexnlp==2.3.0`

## Follow-up completed (quality gate in CI)

- Added committed baseline metrics fixture:
  - `test_data/model_quality/is_contract_baseline_metrics.json`
- Extended `scripts/model_quality_gate.py` to:
  - consume baseline metrics JSON directly
  - validate fixture/min-probability alignment
  - optionally write canonical baseline metrics JSON
- Added a dedicated GitHub Actions job `model-quality` in
  - `.github/workflows/ci.yml`
  - This runs the contract-model quality gate and uploads the JSON result as an artifact.

## Operational guidance

Reliable full-validation flow on this machine:

```bash
cd /Users/jackeames/Downloads/LexNLP

# env
uv venv --python 3.11 .venv311
uv sync --frozen --python .venv311/bin/python --extra dev --extra test

# assets
./.venv311/bin/python scripts/bootstrap_assets.py --nltk --contract-model
./.venv311/bin/python scripts/bootstrap_assets.py --stanford

# base tests
./.venv311/bin/python -m pytest -q

# stanford-only tests
PATH=/opt/homebrew/opt/openjdk/bin:$PATH \
LEXNLP_USE_STANFORD=true \
./.venv311/bin/python -m pytest -q \
  lexnlp/nlp/en/tests/test_stanford.py \
  lexnlp/extract/en/entities/tests/test_stanford_ner.py

# policy + packaging
python3 ci/skip_audit.py
uv build
python3 ci/check_dist_contents.py
```
