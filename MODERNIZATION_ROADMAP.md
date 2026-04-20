# LexNLP Modernization Roadmap

Status of the Python 3.13 / dependency modernization branch
(`claude/modernize-python-dependencies-Fly7d`) and what remains.

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

The **"Original"** column shows the version pin in the legacy
`python-requirements.txt`; the **"Installed"** column is what `uv
lock` currently resolves on Python 3.13; the **"Range"** column is the
relaxed constraint we now expose in `pyproject.toml`. Upper caps were
removed where majors are non-breaking so downstream consumers can
freely pick up security / feature releases.

| Package | Original | Installed | Range | Representative features gained |
| --- | --- | --- | --- | --- |
| Python | `3.10.*` | **3.13.12** | `>=3.13,<3.15` | PEP 604 `X \| Y`, PEP 585 builtin generics, PEP 695 `type` alias, PEP 698 `@override`, PEP 701 multiline f-strings, PEP 709 inlined comprehensions, PEP 667 frame semantics, free-threaded build (`--disable-gil`), `tomllib` stdlib, `asyncio.TaskGroup`, `Self` type, JIT (experimental), better error messages and tracebacks, faster interpreter startup, improved `typing.override` |
| scikit-learn | `0.24.0` | **1.8.0** | `>=1.5` | `set_config(transform_output="pandas")`, full metadata routing (SLEP006), `TunedThresholdClassifierCV`, `HistGradientBoosting` native categorical handling, `feature_names_out` standardised across all transformers, `__sklearn_tags__` API (1.6+), `ColumnTransformer.set_output`, `FrozenEstimator`, Array API support (GPU arrays), `roc_auc_score(multi_class="ovr", average="macro")` defaults, `PartialDependenceDisplay` categorical support, constrained linear models |
| numpy | `1.23.4` | **1.26.4** | `>=1.26,<3` | NEP 50 scalar semantics (cleaner int/float promotion), `np.random.Generator`, strict type promotion, stable `numpy.typing.NDArray`, `np.exceptions` module, faster `np.isin`, improved `np.linalg` stability |
| pandas | `1.5.1` | **2.3.3** | `>=2.2.0,<3` | Copy-on-Write default, PyArrow-backed dtypes, `read_csv(dtype_backend="pyarrow")`, nullable dtypes stable, `DataFrame.map`, `Series.case_when`, deprecated `inplace=True` path removed, `.from_records` on Arrow types, `.agg` preserves dtype |
| regex | `2022.3.2` | **2025.11.3** | `>=2024.0` | Possessive quantifiers, improved unicode property matching, fuzzy matching (`{e<=n}`), grapheme-cluster `\X`, named-group recursion, multi-threaded compile cache |
| nltk | `3.7` | **3.9.4** | `>=3.9` | `punkt_tab` replaces `punkt` (faster, deterministic), security fixes (CVE-2024-39705 pickle), updated averaged-perceptron tagger, POS tagging on OOV tokens, stopwords refresh |
| dateparser | `1.1.3` | **1.2.1** | `>=1.2` | zoneinfo-based timezones, faster language detection, `regex` backend, `PREFER_LOCALE_DATE_ORDER`, relative-date expansion improvements |
| skops | _(new)_ | **0.13.0** | `>=0.11` | `skops.io` secure serialization (CVE-2024-37065 safe; `trusted=True` removed), model cards, HF Hub push, get_untrusted_types audit API |
| cloudpickle | `2.2.0` | **3.1.2** | `>=3.0` | Python 3.13 support, faster reducer dispatch, better `dynamic_subimport` handling, PyPy 3.10+ compatibility |
| gensim | `4.1.2` | **4.4.0** | `>=4.3.3` | 4.x removed deprecated `Phraser` / `Word2Vec.iter`; newer Cython for Python 3.13, bugfix releases |
| joblib | `1.2.0` | **1.5.3** | `>=1.4` | `parallel_config` context manager, zstd compression, `return_as="generator"` iterators, reduced-memory dispatch, python 3.13 support |
| lxml | `4.9.1` | **5.4.0** | `>=5.3` | typing stubs (`lxml-stubs` merged in), parser improvements, HTML5 parser improvements, faster XPath, Python 3.13 wheels |
| elasticsearch | `8.5.0` | **8.19.3** | `>=8.15` | async client, kNN / vector search helpers, ES\|QL pipelines, async pool reuse, native `retry_on_timeout` |
| pycountry | `22.3.5` | **24.6.1** | `>=23` | ISO 4217 updates (BYN, VES, SLE), ISO 3166 refresh, historic currency support |
| python-dateutil | `2.8.2` | **2.9.0** | `>=2.9` | New year heuristics, tz fallback fixes, removed deprecated `tzlocal`, Py3.13 support |
| requests | `2.28.1` | **2.32.5** | `>=2.32` | CVE-2024-35195 patched, charset_normalizer >=3.0, removed deprecated `chunked` param, `RequestField` improvements |
| reporters-db | `3.2.32` | **3.2.63` | `>=3.2.61` | expanded US reporter coverage, federal/state updates, Canadian additions |
| beautifulsoup4 | `4.11.1` | **4.14.3** | `>=4.12` | type hints, soupsieve 2.5 selectors, XML namespace fixes, warning on old parsers |
| num2words | `0.5.12` | **0.5.14** | `>=0.5.13` | more locales (Vietnamese, Marathi), unit-aware numbers, ordinal forms, bugfixes |
| psutil | `5.9.4` | **6.1.1** | `>=6` | Py3.13 support, Linux cgroup v2, new Windows counters, connection state refresh |
| scipy | `1.9.3` | **1.17.0** | `>=1.11.0` | `scipy.stats` new distributions, `signal.windows` fixes, `sparse.linalg` API cleanup, Array API support for `scipy.special`, removal of distutils |
| tqdm | `4.64.1` | **4.67.3** | `>=4.67` | `contrib.rich`, better notebook rendering, `disable=None` auto-detect, `.write` thread safety |
| Unidecode | `1.3.6` | **1.4.0** | `>=1.4` | data refresh, broader CJK coverage |
| us | `2.0.2` | **2.0.2** | `>=2.0.2` | — (stable; kept) |
| zahlwort2num | `0.4.2` | **0.4.3** | `>=0.4.3` | bugfixes for compound numbers |

Upper caps retained:

- `numpy<3` / `pandas<3` — the next majors are known-breaking.
- `python<3.15` — upcoming 3.15 is unreleased; hold until verified.

## 3. Status of PR13 review feedback (addressed in `Fly7d`)

| Finding | Fix |
| --- | --- |
| `_load_skops` passed untrusted list as trusted when `trusted=False` | `trusted=untrusted if trusted else []` (fail-closed) |
| `load_model` silently fell back to pickle for unknown suffixes | explicit `ValueError` naming supported suffixes |
| `_load_legacy` accepted empty/unknown suffix as pickle | rejects any non-legacy suffix |
| `pytest.raises(Exception)` on corrupt pickle | narrowed to `pickle.UnpicklingError` |
| Thread workers swallowed exceptions with `except Exception` | replaced with `ThreadPoolExecutor.future.result()` |
| EN DASH in comments (RUF003) | replaced with ASCII hyphen-minus |
| Unused `import locale as _locale_mod`, unused `pytest` | removed |
| `amount_delimiting.py` imports unordered (I001) | reordered |
| `requires-python` / classifier mismatch | aligned at 3.13 / 3.14 |
| FTP error assertion didn't cover full URL | asserts `"ftp://example.com/resource"` in message |
| `runtime_model.py` docstring still said "Python 3.11" | updated to "Python 3.13+" |



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

1. `uvx ty check .` — count must not exceed **562** (current budget
   after the `Fly7d` relaxation).
2. `.venv/bin/python -m pytest lexnlp/ scripts/tests/ -q` — PR13-touched
   suites currently pass 96/96 (`test_model_io.py` 45, `test_catalog_path.py`
   5, `test_amount_delimiting.py` ~19, `test_regulations.py` ~10,
   `test_bootstrap_assets.py` ~17). Wider suite blocked on legacy sklearn
   1.2.2 pickles (see Tier B.12).
3. Smoke: `ensure_runtime_contract_type_model(force=False)` loads
   without `InconsistentVersionWarning`.
4. CI: `asset-drift.yml` must stay green against the re-published
   catalog.

## 6. Tracking

Open follow-up tasks live on the PR associated with branch
`claude/modernize-python-dependencies-Fly7d`. This roadmap is the
single source of truth; updating it in-tree keeps reviewers aligned.
