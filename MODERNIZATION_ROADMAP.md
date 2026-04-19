# LexNLP Modernization Roadmap

Status of the Python 3.13 / dependency modernization branch
(`claude/modernize-python-dependencies-UUxLl`) and what remains.

## 1. Original package capabilities (what we are preserving)

LexNLP is a legal-domain NLP toolkit. The public surface is:

- **`lexnlp.extract.en/de/es`** — rule-based extractors emitting typed
  annotation objects (subclasses of `TextAnnotation`) for amounts,
  money, percents, durations, distances, ratios, dates, date periods,
  addresses, courts, citations, regulations, acts, conditions, copyrights,
  definitions, trademarks, URLs, PII, geoentities, companies.
- **`lexnlp.nlp.en`** — classic segmentation pipeline built on NLTK
  (tokens / sentences / paragraphs / sections / titles / pages /
  heading heuristics / stopwords / collocations).
- **`lexnlp.extract.ml`** — supervised extractors layered on top of
  sklearn pipelines (layered-definition detector, token-sequence CRF).
- **`lexnlp.ml`** — asset catalog, gensim helpers, sklearn transformers,
  and now `model_io` (skops + legacy pickle fallback).
- **`lexnlp.utils`** — locale-aware amount delimiting, decorators,
  unicode lookup, CSV/DataFrame helpers.
- **`scripts/`** — training / evaluation / quality-gate / bootstrap /
  drift-check utilities, plus release publishing workflows.

## 2. How the dependencies evolved (and what they now unlock)

| Package | Was | Now | What changed that we can use |
| --- | --- | --- | --- |
| Python | `>=3.10,<3.13` | **`>=3.13`** | PEP 604 `X \| Y`, PEP 585 builtin generics, PEP 695 `type` alias, PEP 698 `@override`, PEP 701 f-strings, PEP 709 inlined comprehensions, PEP 667 frame semantics, free-threaded build, `tomllib` stdlib, better error messages |
| scikit-learn | `1.2.2` | **`>=1.5,<2`** (picks 1.8) | `set_config(transform_output="pandas")`, metadata routing (SLEP006), `TunedThresholdClassifierCV`, `HistGradientBoosting` categorical handling, `feature_names_out` standardized, `_get_tags`/`__sklearn_tags__` API, `ColumnTransformer.set_output` |
| numpy | `<2` | **`>=1.26,<3`** | NEP 50 scalar semantics (cleaner promotion), `np.random.Generator`, strict typing |
| pandas | `2.2.0` | **`>=2.2.0,<3`** | Copy-on-Write default, PyArrow-backed dtypes, `read_csv(dtype_backend="pyarrow")`, nullable dtypes stable |
| regex | `==2022.3.2` | **`>=2024,<2026`** | Possessive quantifiers, improved unicode property matching, fuzzy matching, grapheme-cluster `\X` |
| nltk | `>=3.8.1,<3.9` | **`>=3.9,<4`** | `punkt_tab` replaces `punkt`, security fixes, updated taggers |
| dateparser | `==1.1.3` | **`>=1.2,<2`** | zoneinfo-based timezones, faster language detection, `regex` backend |
| skops | (new) | **`>=0.11,<1`** | `skops.io` secure serialization (CVE-2024-37065 safe), model cards, HF Hub push |
| gensim | `>=4.3.2,<5` | **`>=4.3.3,<5`** | bugfix release; 4.x removed deprecated `Phraser`, `Word2Vec.iter` |
| joblib | `>=1.2,<2` | **`>=1.4,<2`** | `parallel_config` context manager, zstd compression |
| lxml | `>=4.9.1,<6` | **`>=5.3,<7`** | typing stubs, parser improvements |
| elasticsearch | `>=8.5,<9` | **`>=8.15,<10`** | async client, kNN / vector search helpers, ES\|QL |
| pycountry | `>=22.3,<25` | **`>=23,<26`** | ISO 4217 updates, data refresh |
| requests | `>=2.28,<3` | **`>=2.32,<3`** | security patches, removed deprecated `chunked` param |
| beautifulsoup4 | `>=4.11,<5` | **`>=4.12,<5`** | type hints, soup improvements |
| num2words | `>=0.5.12` | **`>=0.5.13`** | more locales, bugfixes |
| tqdm | `>=4.64,<5` | **`>=4.67,<5`** | `contrib.rich`, better notebooks |
| Unidecode | `>=1.3.6,<2` | **`>=1.4,<2`** | data update |
| zahlwort2num | `>=0.4.2` | **`>=0.4.3`** | bugfixes |

## 3. Immediate next-step backlog (ordered by leverage)

### Tier A — low-risk plumbing (days)

1. **`py.typed` marker** (done in this branch) — downstream users get
   type information from our code.
2. **Typing modernization**: rewrite `typing.List/Dict/Tuple/Set/
   Optional/Union` to PEP 585 / PEP 604 (`list[str]`, `dict[str, int]`,
   `str | None`). ~107 files use `typing.X`; a scripted rewrite via
   `ruff check --select UP006,UP007,UP035,UP045 --fix` handles it in
   one pass. Follow up with `ruff --select UP` repo-wide.
3. **Pre-commit hooks**: add `.pre-commit-config.yaml` with
   `ruff`, `ruff-format`, `ty check` (pre-release), `uv lock --check`,
   `pyproject-fmt`.
4. **PEP 735 dependency groups**: migrate `[project.optional-dependencies]
   dev/test` to `[dependency-groups]` so `uv sync --group test` works.
5. **Replace `cloudpickle` usage on model persistence** with
   `lexnlp.ml.model_io.dump_model` consistently. Audit the 26 files
   that still import `joblib`/`pickle`/`cloudpickle`.
6. **Delete unused Pipfile / Pipfile.lock / requirements*.txt** now that
   `uv` / `pyproject` is the source of truth.
7. **Run `ruff check --select UP,B,SIM,RUF,PERF,PIE --fix`** —
   modern Python idioms and small-perf wins, file-by-file review.

### Tier B — structural improvements (days to weeks)

8. **Structured sklearn outputs**: adopt
   `set_config(transform_output="pandas")` for the tfidf/logreg
   pipelines so downstream users can reason about feature columns by
   name, and so interpretability stack (e.g., `shap`, `ELI5`) plugs in
   natively.
9. **Sklearn metadata routing** (`enable_metadata_routing=True`):
   lets training pipelines propagate `sample_weight` / `groups`
   cleanly — replaces the current private `pipeline._final_estimator`
   / `pipeline._iter()` patterns.
10. **Emit skops model cards** for every release artifact. `skops.card`
    automates: model description, input/output specs, metric tables,
    license. The publish workflows already output
    `contract_type_quality_gate.json`; wire that into card generation.
11. **Trusted skops allow-list**: restrict `get_untrusted_types(...)`
    in `lexnlp/ml/model_io.py` to an explicit allow-list of sklearn
    estimator class names so an attacker-controlled artifact can't
    smuggle unknown types even with `trusted=True`.
12. **Re-export bundled sklearn pickles** via
    `scripts/reexport_bundled_sklearn_models.py` and replace the
    11 `test_data/**/*.pickle` files so tests stop ERRORing on
    collection under sklearn >=1.3. Skops format preferred.
13. **Re-train `pipeline/contract-type/0.2-runtime`** on sklearn 1.8
    and publish as `.skops`.
14. **Adopt `pyarrow`-backed pandas for catalog CSVs**: faster
    parse, lower memory. Entry points are `read_csv(...,
    dtype_backend="pyarrow")` in geoentities/regulations/dates
    configuration loaders.
15. **Replace `datetime.utcnow()`** (`lexnlp/tests/lexnlp_tests.py:344`)
    with `datetime.now(datetime.UTC)` — removes a warning that spams
    every test run and will be an error in a future Python.
16. **Kill dead compatibility shims** under `lexnlp/extract/common/`
    that were added for sklearn 1.2; trim once pickles are re-exported.

### Tier C — new capability (weeks)

17. **Embedding-based entity linking**: introduce an optional
    `[embeddings]` extra with `sentence-transformers` + an opt-in
    similarity scorer for citations / court names / regulations. Keeps
    the rule-based core as default; transformers run as a re-ranker
    when the rule-based matcher is ambiguous.
18. **Hybrid NER fallback**: optional `[ner]` extra with `spacy>=3.7`
    + a small on-device model for entities the rule stack misses
    (parties, agreement types). spaCy can feed
    `lexnlp.extract.ml`'s CRF features, improving recall without
    rewriting the pipeline.
19. **HF Hub publishing**: `skops.hub_utils.push` alongside the
    existing GitHub release workflow so consumers can `from
    huggingface_hub import snapshot_download` the model catalog.
    `lexnlp.ml.catalog.download` already has a pluggable repo slug.
20. **`rapidfuzz`-based matcher** for fuzzy legal-term lookups
    (currently done with regex alternation). Faster and
    unicode-aware.
21. **Async / parallel asset download**: `httpx.AsyncClient` with
    `tqdm.asyncio.gather` in
    `scripts/bootstrap_assets.py::download_many` — right now each
    file downloads sequentially.
22. **Selectolax fast path** for HTML parsing where lxml+bs4 is
    the hot loop (contract ingestion scripts).
23. **polars** experimental fast path for catalog-level reports
    (`scripts/model_quality_gate.py`, quality-gate aggregation).
24. **Jupyter-book / MkDocs Material docs** replacing the
    Sphinx-only build so the extraction catalogue is browsable with
    live examples.

### Tier D — housekeeping & release (ongoing)

25. **Re-run `uvx ty check .`** on every merge; bake the diagnostic
    count (558 on this branch) into a CI budget that must not
    regress.
26. **Address ty diagnostics by category**:
    - `invalid-parameter-default` (148): fix `def f(x: T = None)`
      patterns — change annotation to `T | None`.
    - `unresolved-attribute` (295): largely sklearn / pandas dynamic
      attributes; add targeted `# ty: ignore[unresolved-attribute]`
      or narrow stubs.
    - `invalid-argument-type` (117): mostly numpy 2 scalar
      promotion — explicit casts or dtype arguments.
    - `deprecated` (18): drop `datetime.utcnow`, `multi_class` arg
      on `LogisticRegression`, etc.
27. **Bump CI Python matrix**: add 3.14-nightly to catch forward
    regressions (Python 3.14 is already in RC stages).
28. **Delete `Pipfile*`** once CI / docs reference `uv` only.

## 4. New functionality proposals (concrete designs)

### 4.1 `lexnlp.ml.model_card` — automatic model cards

```python
from skops import card
from lexnlp.ml.model_io import dump_model

def dump_model_with_card(estimator, path, *, metrics, dataset_info, metadata):
    dump_model(estimator, path)
    c = card.Card(estimator)
    c.add(**metadata)
    c.add_metrics(**metrics)
    c.add_plot(**dataset_info)
    c.save(path.with_suffix(".md"))
```

Wired into `write_pipeline_to_catalog` so every release includes a
machine-readable `.md` next to the `.skops`. Drops cleanly into
GitHub release assets.

### 4.2 `lexnlp.extract.semantic` — optional transformer re-ranker

Opt-in module that takes the top-N candidate annotations from the
rule-based extractor and re-ranks them by cosine similarity to a
canonical dictionary (e.g., courts, regulations) using a small
sentence-transformer. Entry point mirrors the existing extractor
signature so consumers can drop it in.

### 4.3 `lexnlp.ml.catalog.hub` — HuggingFace Hub mirror

```python
def get_path_from_hub(tag: str, *, revision: str | None = None) -> Path:
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(repo_id=HUB_REPO, filename=tag, revision=revision))
```

`get_path_from_catalog` falls back to the Hub if
`download_github_release` 404s.

## 5. Verification plan

For each Tier change:

1. `uvx ty check .` — count must not exceed 558 (current budget).
2. `.venv/bin/python -m pytest lexnlp/ scripts/tests/ -q` — currently
   483 passing / 11 skipped (excluding 14 tests blocked on re-exported
   pickles).
3. Smoke: `ensure_runtime_contract_type_model(force=False)` loads
   without `InconsistentVersionWarning`.
4. CI: `asset-drift.yml` must stay green against the re-published
   catalog.

## 6. Tracking

Open follow-up tasks live on the PR associated with branch
`claude/modernize-python-dependencies-UUxLl`. This roadmap is the
single source of truth; updating it in-tree keeps reviewers aligned.
