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
  Unicode lookup, CSV/DataFrame helpers.
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
| numpy | `1.23.4` | **2.4.4** | `>=2.3,<3` | **NumPy 2.0 (Jun 2024)**: NEP 50 default scalar promotion (cleaner int/float rules), removal of deprecated aliases (`np.int`, `np.float`, `np.NaN`, `np.product`, `np.trapz`, `np.in1d`, `np.round_`, `np.sometrue`, …), new `numpy.exceptions` namespace, strict type promotion, stable `numpy.typing.NDArray`, revamped C/Python ABI, `numpy.strings` Unicode vectorised ops. **NumPy 2.1 (Aug 2024)**: default `np.dtype` repr, `matvec`/`vecmat`/`vecdot` generalised ufuncs, improved `__array_namespace__` for Array API, `numpy.dtypes.StringDType`, Windows Py3.13 wheels. **NumPy 2.2 (Dec 2024)**: `numpy.lib.array_utils.normalize_axis_index`, nanquantile fast path, faster f-contiguous reductions, `out=` kwarg on `np.unique*`, `numpy.strings.slice()`. **NumPy 2.3 (Jun 2025)**: `np.random.Generator.spawn`, SIMD-accelerated string functions, free-threaded CPython support, extended Array API compliance. **NumPy 2.4 (Oct 2025)**: SVE/SME kernels on ARM, `out=` support in more ufuncs, faster `setdiff1d`, BLAS vendored wheels. Features the codebase specifically benefits from: stable `numpy.typing`, Array API passthrough for sklearn 1.8 GPU path, strict scalar promotion (eliminates silent float→int coercion), new `exceptions` namespace for precise error handling. |
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
| reporters-db | `3.2.32` | **3.2.63** | `>=3.2.61` | expanded US reporter coverage, federal/state updates, Canadian additions |
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

### 2.0.1 Optional dependency extras

Capabilities the runtime can light up incrementally. None of these are
required for the rule-based extractors; install only what the consuming
project needs.

| Extra | Pin | Powers | Notes |
| --- | --- | --- | --- |
| `[arrow]` | `pyarrow>=17` | `lexnlp.utils.pandas_config.read_csv_arrow` (`dtype_backend="pyarrow"`); `lexnlp.extract.batch.annotations_to_dataframe(prefer_arrow=True)` | Falls back to the NumPy-backend `read_csv` when missing |
| `[hub]` | `huggingface_hub>=0.25` | `lexnlp.ml.catalog.hub.get_path_from_hub` for HF Hub mirror downloads when GitHub releases are unavailable | `hub_is_available()` reports the install status |
| `[ner]` | `spacy>=3.7` | Optional spaCy backend for `lexnlp.extract.ner.extract_entities(prefer_spacy=True)` and `SpacyTokenSequenceClassifierModel` | The default NER backend is NLTK so this extra is *not* required for `lexnlp.extract.ner` to work — see §2.0.2 |
| `[tika]` | `tika>=2.6.0` | Apache Tika document-parsing helpers under `scripts/run_tika.sh` | Tika needs a JVM; covered in `scripts/download_tika.sh` |
| `[stanford]` | _(empty)_ | Hooks for Stanford NER / POS — kept as a flag for callers that ship their own jars locally via `enable_stanford()` | Empty until upstream publishes a pip-installable stanford-corenlp wheel |

### 2.0.2 Substituting the gated `en_core_web_sm` model

`en_core_web_sm` is the spaCy English pipeline our token-sequence
classifier historically loaded at module-import time. spaCy *models* (as
opposed to the `spacy` package itself) are not on PyPI; they ship from
the `explosion/spacy-models` GitHub releases CDN and require a separate
`python -m spacy download en_core_web_sm` step. That extra step makes
the model "gated" relative to a normal `pip install` flow — CI workers
behind firewalls, immutable container builds and air-gapped lab
environments fail without the manual download.

**Substitution in place** (April 2026,
`claude/review-pr-comments-HTZkT`): the default backend for
`lexnlp.extract.ner.extract_entities` is now **NLTK**
(`averaged_perceptron_tagger_eng` + `maxent_ne_chunker_tab`). NLTK is
already a hard dependency of LexNLP and exposes the same
PERSON/ORG/GPE/LOC label namespace as `en_core_web_sm`'s NER head, so
the substitution is a true equivalent for the rule-stack-augmentation
use case. Data sets are fetched once via `nltk.download(...)` and
persisted to `~/nltk_data`, working identically under air-gapped /
mirror-only setups once they are mirrored alongside the rest of the
NLTK corpora that LexNLP already requires.

`prefer_spacy=True` opts back into the spaCy backend for callers that
want it; the ``[ner]`` extra and a separate `python -m spacy download
en_core_web_sm` (or `LEXNLP_SPACY_MODEL=<package>`) are required in that
mode. The `spacy_token_sequence_model` module's eager
`spacy.load("en_core_web_sm")` was replaced with a lazy, cached
`_load_spacy_pipeline(name)` so the import chain no longer touches the
gated model unless a caller actually exercises the spaCy code path.

NLTK data needed for the default backend (one-time download):

```python
import nltk
for pkg in ("punkt_tab", "averaged_perceptron_tagger_eng",
            "maxent_ne_chunker_tab", "words"):
    nltk.download(pkg)
```

### 2.1 NumPy 2.x migration notes (April 2026)

The floor moved from **1.26 → 2.1** on branch
`claude/mirror-spanish-module-architecture-cUI6Z`, and was bumped again
to **2.3** on branch `claude/numpy-upgrade-features-qVF34` so that the
library can unconditionally rely on a handful of newer primitives:

- `numpy.random.Generator.spawn` (2.3) — deterministic child streams for
  parallel batch extraction without the legacy `RandomState` global.
- `numpy.strings.slice()` (2.2) — vectorised substring slicing for bulk
  text windowing.
- `numpy.lib.array_utils.normalize_axis_index` (2.2) — formerly private
  axis-bounds helper now promoted to the public API.
- SIMD-accelerated `numpy.strings` string ufuncs (2.3) — `lower`,
  `upper`, `strip`, `startswith`, `count`, `slice` run orders of
  magnitude faster than the equivalent Python-level listcomp.
- `numpy.vecdot` ufunc (2.1) — single-call cosine-similarity numerator
  (used by `lexnlp.utils.cosine`).

The upper cap remains at `<3` because NumPy 3.0 is not yet released
and the ABI break is known-upcoming.

Relevant findings from the earlier 1.26 → 2.1 migration:

- **Codebase surface**: `ruff`-grep across `lexnlp/` + `scripts/` found
  **zero** uses of the removed aliases (`np.int`, `np.float`, `np.bool`,
  `np.object`, `np.NaN`, `np.product`, `np.cumproduct`, `np.round_`,
  `np.sometrue`, `np.alltrue`, `np.asfarray`, `np.trapz`, `np.in1d`). No
  code fixes required for the runtime.
- **Bundled sklearn pickles** (11 sklearn artifacts that lived as 10
  ``.pickle`` files under ``lexnlp/`` — the layered-definition zip
  carried two pickles internally) used to fail to unpickle under
  numpy 2.x with ``ValueError: node array from the pickle has an
  incompatible dtype``. ✅ *Resolved on
  `claude/review-pr-comments-HTZkT` — every artifact has been
  re-exported via ``scripts/reexport_bundled_sklearn_models.py
  --format skops`` and the legacy ``.pickle`` files were deleted. The
  DE court-citation and ML token-sequence tests collect cleanly on
  sklearn 1.8 + numpy 2.4. See §2.3 for the full per-file table and
  Tier B.12 for the user-facing description.*
- **`dateparser` integration**: `dateparser.search` is fine under numpy 2;
  the only parser-level adjustment was in
  `lexnlp/extract/common/dates.py` where ``get_dateparser_dates`` is now
  fed the newline-normalised `self.text` instead of the original `text`.
  This fixes a latent bug where coordinated date phrases split by a
  newline (``"28 de abril e 17 de\nnovembro de 1995"``) produced
  spurious year-2017 annotations because dateparser hallucinated the
  trailing ``17`` as a two-digit year.
- **Docstring-indent regression**: 28 Python files under `lexnlp/` had
  over-indented statements immediately after auto-generated docstrings
  (commit ``17a7b87`` by coderabbitai[bot]). These were syntax errors
  that blocked any `ast.parse` / import — *not* caused by numpy 2 but
  surfaced only when we tried to run the suite under the new floor.
  All 28 files are now clean.

## 2.2 Work completed on `claude/mirror-spanish-module-architecture-cUI6Z`

| Area | What changed |
| --- | --- |
| NumPy floor | `1.26,<3` → `2.1,<3`; uv.lock resolves to `2.4.4` |
| `lexnlp.extract.pt` | new language module (see §4.-1) with 6 submodules, 2 CSVs, 98 courts, 78 regulation triggers, 5 fixture files, 47 passing tests |
| `lexnlp/extract/all_locales/{dates,definitions,copyrights}.py` | PT routed via `ROUTINE_BY_LOCALE[LANG_PT.code]` |
| `lexnlp/extract/common/dates.py` | dateparser now receives newline-normalised text; 5 over-indented docstring statements fixed |
| `lexnlp/extract/common/fact_extracting.py` | 3 over-indented statements fixed |
| `lexnlp/extract/de/geoentities.py` | 3 over-indented statements fixed |
| 25 other files under `lexnlp/` | single over-indented statement after auto-generated docstring fixed |
| `test_data/lexnlp/extract/pt/corpus/` | 1.5 MB of real planalto legislation (LAI, CDC, Código Civil, Biossegurança, Constituição Federal) mirrored for integration tests |

## 2.3 Work completed on `claude/review-pr-comments-HTZkT` (April 2026)

Triage of the open PR review threads from #19, #21 and #22 plus four
explicit carry-overs from §2.3:

| Area | What changed |
| --- | --- |
| `scripts/reexport_bundled_sklearn_models.py` | rewritten to emit `.skops` siblings via `dump_model`; sanitises stray `pandas.Index` attributes that skops can't reduce; layered-definition zip becomes `definition_model_layered.skops.zip` |
| `lexnlp/ml/model_io.py` | new `load_bundled_model(legacy_path)` helper that prefers the `.skops` sibling; trusted allow-list extended for NLTK Punkt types, sklearn `ExtraTreesClassifier`, `SelectKBest` and the univariate-selection score functions |
| 6 loader sites (`lexnlp/extract/{de,en}/...`, `lexnlp/nlp/en/segments/{pages,paragraphs,sections,sentences,titles}.py`, `lexnlp/extract/en/addresses/addresses.py`) | switched from `load_model(...pickle)` to `load_bundled_model(...)` so the safer `.skops` artifacts are picked up automatically |
| `lexnlp/extract/ner/` | new package: `HybridNERMatch`, `extract_entities(prefer_spacy=False)`, `spacy_is_available()`, `augment_rule_matches`. **NLTK is the default backend** (substitution for the gated `en_core_web_sm` — see §2.0.2); spaCy is opt-in via `[ner]` + `prefer_spacy=True` |
| `lexnlp/extract/ml/classifier/spacy_token_sequence_model.py` | `import spacy` and `spacy.load("en_core_web_sm")` are now lazy (cached `_load_spacy_pipeline`); model name overridable via `LEXNLP_SPACY_MODEL`. The module imports cleanly without the optional `[ner]` extra |
| `pyproject.toml` | new `[ner]` optional extra (`spacy>=3.7`) |
| `lexnlp/extract/pt/regulations.py` | trigger regex now allows `\.(?=\d)` so Brazilian act numbers like `Lei nº 12.527` are not split on the thousands-separator dot; trigger phrases that swallow a formal citation are dropped in `parse()`; new `PARAGRAPH_LEADING_REFERENCE_RE` matches `§ 2º do art. 14`, `inciso II do art. 5º`, `alínea a do art. 12` |
| `lexnlp/extract/pt/definitions.py` | new `match_pt_def_by_parenthesised_label` matcher registered in `make_pt_definitions_parser`; existing `reg_parenthesised_label` regex now reachable from the dispatcher |
| `lexnlp/extract/de/de_date_parser.py` | early-return guard before `re.sub` when neither the call argument nor `self.text` is set, preventing a confusing `RuntimeError` deep in `_parse_text_part` |
| `lexnlp/extract/common/countries.py` | `fuzzy_country(max_results=...)` now rejects non-int / `bool` values with `TypeError` so float / string callers don't silently slice |
| `lexnlp/extract/common/tests/test_us_states.py` | tautological `is None or is not None` assertion removed; only the meaningful `lookup_state("CA.")` contract is exercised now |
| `lexnlp/extract/common/tests/test_countries.py` | frozen-dataclass mutation test uses `setattr()` instead of `# type: ignore[misc]`; new `test_max_results_non_int_raises_type_error` covers the new `TypeError` guard |
| `lexnlp/utils/tests/test_pandas_config.py` | `except Exception:` blocks gain `# noqa: BLE001 - best-effort option restore across pandas versions` justifications |
| `lexnlp/extract/pt/tests/test_real_corpus.py` | year upper bound now reads `datetime.date.today().year + 1` rather than the hardcoded `2025` (which has now passed) |
| `lexnlp/ml/tests/test_model_io.py` | `test_extra_trusted_extends_allow_list` actually captures the `trusted` argument that flows into `_skops_load` and asserts the custom type made it through, instead of just observing that no exception was raised |
| `test_data/lexnlp/typed_annotations/pt/regulation/regulations.txt` | fixture cleaned up: drops the truncated `Lei nº 12` / `Decreto nº 7` / `Decreto nº 10` annotations that were artifacts of the over-eager trigger regex |
| `lexnlp/extract/en/contracts/tests/test_runtime_model_sklearn18.py` | new smoke suite: `train_contract_type_pipeline` fits + `write_pipeline_to_catalog` + `load_model` round-trip on a synthetic 9-doc / 3-label corpus, catching sklearn 1.8 deprecations without depending on the GitHub corpus tag |

## 2.4 Carry-overs from `claude/mirror-spanish-module-architecture-cUI6Z`

These were explicit carry-overs at the time the PT branch shipped. Items
marked ✅ have since been resolved on
`claude/review-pr-comments-HTZkT`:

- **Bundled sklearn 1.2 pickles** ✅ *Resolved on
  `claude/review-pr-comments-HTZkT` — the 10 ``.pickle`` artifacts under
  ``lexnlp/extract/{de,en}/`` and ``lexnlp/nlp/en/segments/`` (the
  roadmap's "11" count includes the two inner pickles inside
  ``definition_model_layered.pickle.gzip``) were re-exported as
  ``.skops`` siblings through the updated
  ``scripts/reexport_bundled_sklearn_models.py``. The script now (a)
  walks loads through ``lexnlp.ml.model_io._patched_sklearn_tree_loader``
  so pre-1.3 tree node arrays grow the missing
  ``missing_go_to_left`` byte on the fly, (b) replaces stray
  ``pandas.Index`` attributes (which carry an unreducible
  ``BlockValuesRefs``) with plain lists, and (c) writes via
  ``skops.io.dump`` to preserve the safe-by-default load gate. Loaders
  call the new ``load_bundled_model`` helper that prefers the ``.skops``
  sibling, so existing tests stop ERRORing on collection under sklearn
  1.8 + numpy 2.4.*
- **Constituição Federal and LGPD planalto downloads**: direct
  `planalto.gov.br` requests return **HTTP 403** from this runtime sandbox
  (bot protection). The Constituição is sourced from the
  `jonasabreu/leis-federais` GitHub mirror instead; LGPD (Lei nº
  13.709/2018) is not present in that mirror and was not added to the
  corpus. Acceptable because LAI, CDC and Civil Code provide 1.5 MB of
  representative text.
- **PT metadata-routing / structured outputs**: the PT extractors still
  return plain annotation objects. The sklearn 1.8 metadata-routing
  work (Tier B.9) is independent of PT.
- **PT model cards / HF Hub publishing**: no ML artifacts exist for PT
  yet, so Tier C.17 / §4.3 are not blocked-by-this-branch.
- **`regex` 2025+ fuzzy dates for PT**: `lexnlp.extract.batch`'s
  `find_fuzzy_dates` already works language-agnostically; adding a
  PT-specific fuzzy matcher (e.g. ``{e<=1}`` on
  ``1[º°] de janeiro``) is tracked as future work, not shipped.

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
3. **Pre-commit hooks**: ✅ *Done on
   `claude/numpy-upgrade-features-qVF34` — `.pre-commit-config.yaml`
   wires `ruff`, `ruff-format`, `uv lock`, `ty check` and the standard
   whitespace / YAML / TOML hygiene hooks.*
4. **PEP 735 dependency groups**: migrate `[project.optional-dependencies]
   dev/test` to `[dependency-groups]` so `uv sync --group test` works.
5. **Replace `cloudpickle` usage on model persistence** with
   `lexnlp.ml.model_io.dump_model` consistently. Audit the 26 files
   that still import `joblib`/`pickle`/`cloudpickle`.
6. **Delete unused Pipfile / Pipfile.lock / requirements*.txt** now that
   `uv` / `pyproject` is the source of truth.
   *Pipfile + Pipfile.lock removed on branch
   `claude/mirror-spanish-module-architecture-cUI6Z` — the Pipfile pin of
   `scikit-learn == 0.24` directly contradicted the `>=1.5` constraint in
   `pyproject.toml` and was flagged by CodeRabbit as a conflict-of-
   truth. `ci/check_dist_contents.py` continues to ban both filenames
   from built artifacts. The `python-requirements*.txt` snapshots are
   still retained for now.*
7. **Run `ruff check --select UP,B,SIM,RUF,PERF,PIE --fix`** —
   modern Python idioms and small-perf wins, file-by-file review.

### Tier B — structural improvements (days to weeks)

8. **Structured sklearn outputs**: ✅ *Done —
   `lexnlp.ml.sklearn_config.enable_pandas_output()` /
   `configure_pipeline_for_dataframes()` set
   `set_config(transform_output="pandas")` so tfidf/logreg pipelines
   emit DataFrames.*
9. **Sklearn metadata routing**: ✅ *Done on
   `claude/numpy-upgrade-features-qVF34` —
   `lexnlp.ml.sklearn_config.enable_metadata_routing()` flips
   `enable_metadata_routing=True` and returns the previous value so
   tests / scripts can restore it.*
10. **Emit skops model cards**: ✅ *Done on
    `claude/numpy-upgrade-features-qVF34` — new
    `lexnlp.ml.model_card` module with `ModelCardMetadata`,
    `write_model_card` and `dump_model_with_card` so every release
    artifact ships a sibling ``.md`` card containing the description,
    license, authors, tags, metrics and hyper-parameters.*
11. **Trusted skops allow-list**: ✅ *Done on
    `claude/numpy-upgrade-features-qVF34` —
    `lexnlp.ml.model_io.DEFAULT_TRUSTED_ALLOWLIST` intersects the
    artifact's declared untrusted types with an explicit sklearn /
    numpy estimator-class allow-list. `trusted=True` now rejects any
    type outside that set even if the caller asserted trust; callers
    with legitimate custom estimators extend via ``extra_trusted``.*
12. **Re-export bundled sklearn pickles**: ✅ *Done on this branch
    (`claude/review-pr-comments-HTZkT`) —
    `scripts/reexport_bundled_sklearn_models.py` was extended to (a) walk
    pipelines through ``lexnlp.ml.model_io.load_model`` so the in-tree
    sklearn-tree dtype migration (``missing_go_to_left``) runs on
    pre-1.3 pickles, (b) sanitize stray ``pandas.Index`` attributes that
    skops can't reduce, (c) emit ``.skops`` siblings via ``dump_model``,
    and (d) re-pack the layered-definitions zip as
    ``definition_model_layered.skops.zip``. Ten ``.skops`` files now ship
    next to the legacy pickles; loaders (``lexnlp/extract/de/dates.py``,
    ``lexnlp/extract/en/date_model.py``, ``lexnlp/extract/en/addresses``,
    and the four NLP segmenters) call the new
    ``lexnlp.ml.model_io.load_bundled_model`` helper which prefers the
    ``.skops`` sibling and falls back to the pickle on absence. The
    previously-failing ``ValueError: node array from the pickle has an
    incompatible dtype`` no longer surfaces during test collection on
    sklearn 1.8 + numpy 2.4.*
13. **Re-train `pipeline/contract-type/0.2-runtime`** on sklearn 1.8: ✅
    *Done on this branch — ``runtime_model.train_contract_type_pipeline``
    already pins ``LogisticRegression(solver="lbfgs",
    class_weight="balanced", max_iter=1000)`` (no deprecated
    ``multi_class`` arg) and ``write_pipeline_to_catalog`` writes
    ``pipeline_contract_type_classifier.skops`` via ``dump_model``. New
    regression suite ``lexnlp/extract/en/contracts/tests/
    test_runtime_model_sklearn18.py`` exercises the end-to-end fit +
    skops round-trip on a synthetic corpus so sklearn API drift is
    caught even when the GitHub-release corpus tag is unreachable in
    CI.*
14. **Adopt `pyarrow`-backed pandas for catalog CSVs**: ✅ *Done on
    `claude/numpy-upgrade-features-qVF34` —
    `lexnlp.utils.pandas_config.read_csv_arrow(path, **kwargs)`
    forwards `dtype_backend="pyarrow"` when PyArrow is importable and
    falls back to the default NumPy backend otherwise. The ``[arrow]``
    extra declares the dependency without making it a hard runtime
    requirement.*
15. **Replace `datetime.utcnow()`**: ✅ *Done earlier —
    `lexnlp/tests/lexnlp_tests.py` and
    `lexnlp/tests/upload_benchmarks.py` now call
    `datetime.now(UTC).isoformat()` / `.date()`.*
16. **Kill dead compatibility shims** under `lexnlp/extract/common/`
    that were added for sklearn 1.2; trim once pickles are re-exported.

### Tier C — new capability (weeks)

17. **Embedding-based entity linking**: introduce an optional
    `[embeddings]` extra with `sentence-transformers` + an opt-in
    similarity scorer for citations / court names / regulations. Keeps
    the rule-based core as default; transformers run as a re-ranker
    when the rule-based matcher is ambiguous.
18. **Hybrid NER fallback**: ✅ *Done on this branch
    (`claude/review-pr-comments-HTZkT`) — new ``[ner]`` optional extra
    declaring ``spacy>=3.7`` plus a new ``lexnlp.extract.ner`` module with
    ``HybridNERMatch`` (``slots=True``/``frozen=True``),
    ``extract_entities(text, prefer_spacy=False)``, ``spacy_is_available()``
    and ``augment_rule_matches(rule_spans, hybrid_matches,
    overlap_threshold=0.5)``. **NLTK is the default backend** —
    deliberate substitution for the gated ``en_core_web_sm`` (see
    §2.0.2); the NLTK ``averaged_perceptron_tagger_eng`` +
    ``maxent_ne_chunker_tab`` data sets emit the same
    PERSON/ORG/GPE/LOC label namespace and require no extra install
    beyond NLTK (already a hard dep) plus a one-time
    ``nltk.download(...)`` for the corpora. Callers who explicitly want
    spaCy pass ``prefer_spacy=True`` and install the optional extra. The
    companion update made the ``en_core_web_sm`` import lazy in
    ``lexnlp.extract.ml.classifier.spacy_token_sequence_model`` (model
    name overridable via ``LEXNLP_SPACY_MODEL``); the module no longer
    imports ``spacy`` at top level so consumers of
    ``lexnlp.extract.ml.classifier`` don't need the heavy install.
    Coverage: 12 tests under ``lexnlp/extract/ner/tests/test_hybrid_ner.py``
    — all 12 pass once the four NLTK corpora are downloaded;
    spacy-availability and overlap-merge tests run unconditionally.*
19. **HF Hub publishing / mirror**: ✅ *Done on
    `claude/numpy-upgrade-features-qVF34` — new
    `lexnlp.ml.catalog.hub` module with `get_path_from_hub(tag, *,
    repo_id=DEFAULT_HUB_REPO, revision=None)` for pulling artifacts
    from the Hub when the GitHub release path is unavailable, plus
    `hub_is_available()` / `HubUnavailableError` / `HubMirrorError`
    for graceful handling of missing `huggingface_hub`. The dependency
    is shipped under the ``[hub]`` optional extra.*
20. **`rapidfuzz`-based matcher** for fuzzy legal-term lookups
    (currently done with regex alternation). Faster and
    Unicode-aware.
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
27. **Bump CI Python matrix**: ✅ *Done on
    `claude/numpy-upgrade-features-qVF34` —
    `.github/workflows/ci.yml` gained a non-blocking
    `base-tests-py314` job that runs the base suite on Python 3.14
    (`continue-on-error: true`) so forward regressions surface without
    blocking merges.*
28. **Delete `Pipfile*`** once CI / docs reference `uv` only. ✅ *Done
    on branch `claude/mirror-spanish-module-architecture-cUI6Z` — see
    §3 Tier-A.6 for context.*

## 4. New functionality proposals (concrete designs)

### 4.-1 `lexnlp.extract.pt` — Portuguese (pt-BR) extraction *(shipped on this branch)*

New first-class language module mirroring the Spanish (`lexnlp.extract.es`)
architecture and extended for Brazilian legal prose. The branch
`claude/mirror-spanish-module-architecture-cUI6Z` added:

* **`lexnlp/extract/pt/__init__.py`** — public API re-exports.
* **`lexnlp/extract/pt/language_tokens.py`** — curated abbreviations (`art.`,
  `nº`, `Ltda.`, `S.A.`, `Exmo.`, …), articles, conjunctions, preposition
  contractions (`do`, `da`, `no`, `na`, `pelo`, `pela`, …), and ordinal
  suffix markers (``º``, ``ª``, ``°``). Curated from Brazilian legal
  writing conventions, not a carryover from another language.
* **`lexnlp/extract/pt/dates.py`** — ``PtDateParser(DateParser)`` backed by
  dateparser's `pt` locale with DMY ordering. Adds:
  - Year inheritance across coordinated phrases
    (``"15 de fev, 28 de abr e 17 de nov de 1995"`` → three dates in 1995).
  - Ordinal-day normalisation (``1º de janeiro``, ``1.º de janeiro``,
    ``1° de maio``).
  - Brasília/Rio/São Paulo legal-gazette date prefixes.
  - Brazilian numeric DMY (``15/02/2020``, ``15.02.2020``, ``15-02-2020``)
    including 2-digit years with a 50-year pivot.
  - Stricter ``passed_general_check`` that rejects dateparser's
    over-matches on weekday abbreviations (``ter``, ``qui``) and stray
    short tokens.
* **`lexnlp/extract/pt/definitions.py`** — ``PortugueseParsingMethods``
  with six matcher families:
  - hereinafter aliases (``doravante``, ``a seguir denominado``,
    ``doravante designado``);
  - explicit definition verbs (``refere-se a``, ``significa``,
    ``é definido como``, ``quer dizer``, ``denota``, ``compreende``,
    ``corresponde a``, ``equivale a``);
  - copula sentences (``X é Y``, ``X são Y``, ``X é uma Y``);
  - ``para os fins desta lei / deste contrato, X significa Y`` (typical
    of Brazilian statutes);
  - parenthesised quoted labels (``(o "Contratante")``);
  - the common acronym matcher (shared with ES/EN).
* **`lexnlp/extract/pt/copyrights.py`** — ``CopyrightPtParser`` subclasses
  ``CopyrightEnStyleParser`` with a Portuguese-tuned line splitter. Sets
  ``locale='pt'`` on every yielded annotation.
* **`lexnlp/extract/pt/courts.py`** — ``UniversalCourtsParser`` wired with
  a **98-row** Brazilian court catalogue
  (`lexnlp/config/pt/pt_courts.csv`) covering STF, STJ, TST, TSE, STM,
  CNJ, CNMP, CJF, CSJT, all six TRFs, all 24 TRTs, all 27 TREs, all 27
  TJs, the three state military justice tribunals (TJMs), TNU and TRU.
  Each row includes a standard alias (``STF``, ``TJSP``, ``TRF5``, …)
  so textual short forms are matched as precisely as formal names.
  Pattern checker broadened to ``tribunal|juízo|vara|turma|câmara|seção|
  plenário``. ``line_breaks`` intentionally excludes single-letter
  conjunctions (``e``, ``o``, ``a``) to avoid shattering phrases.
* **`lexnlp/extract/pt/regulations.py`** — Four extraction layers in one
  parser:
  1. Trigger-word scanner driven by **78-row**
     `lexnlp/config/pt/pt_regulations.csv` (leis, decretos, medidas
     provisórias, resoluções, portarias, instruções normativas, órgãos
     reguladores, etc.).
  2. Formal Brazilian act citation regex
     (``Lei nº 12.527, de 18 de novembro de 2011``,
     ``Decreto-Lei nº 4.657/1942``, ``Lei Complementar nº 101/2000``) —
     tolerant of the planalto-mirror glitch where ``nº`` renders as
     ``n o`` across a line break.
  3. Article / paragraph / incision / alínea references
     (``art. 5º, inciso XXXIII``, ``§ 2º do art. 12``).
  4. Constitutional references (``Constituição Federal``,
     ``CRFB/88``, ``CF/88``).
  All annotations carry ``country='Brazil'``.
* **`lexnlp/extract/pt/identifiers.py`** — New module with
  **checksum-validated** CPF, CNPJ, and OAB extractors. Pure-Python
  validators (no deps); invalid numbers are silently skipped so the
  extractor is safe to run over noisy OCR. Emits ``IdentifierMatch``
  (``slots=True``, ``frozen=True``) with ``kind``, ``value`` (canonical
  digits), ``surface`` and ``coords``.
* **Dispatcher wiring**: ``lexnlp.extract.all_locales.{dates,definitions,
  copyrights}`` now include ``LANG_PT.code`` in their
  ``ROUTINE_BY_LOCALE``. ``LANG_PT = Language('pt', 'por', 'Portuguese')``
  is registered alongside ``LANG_EN``/``LANG_DE``/``LANG_ES``.
* **Real-corpus tests** — ``lexnlp/extract/pt/tests/test_real_corpus.py``
  exercises the extractors against a 1.5 MB corpus of planalto-sourced
  legislation (LAI, CDC, Código Civil, Biossegurança, Constituição
  Federal). Tests assert conservative lower bounds on extraction counts
  so planalto's minor textual revisions don't break CI. Corpus lives at
  ``test_data/lexnlp/extract/pt/corpus/`` (mirrored from the
  [jonasabreu/leis-federais](https://github.com/jonasabreu/leis-federais)
  GitHub archive of planalto.gov.br).
* **Typed-annotation fixtures** under
  ``test_data/lexnlp/typed_annotations/pt/{date,definition,copyright,
  court,regulation}/`` drive the same `TypedAnnotationsTester` plumbing
  used for ES/DE.
* **Tests**: **47 tests** under ``lexnlp/extract/pt/tests/`` all green
  on Python 3.13 + numpy 2.4.4.

### 4.0 `lexnlp.extract.batch` — concurrent & Arrow-native extraction *(shipped)*

The `claude/arthrod-lexpredict-pr-review-e1948` branch adds a brand-new
`lexnlp.extract.batch` subpackage that operationalises several of the
Python-3.13 wins listed above:

* `extract_batch_async(extractor, texts, max_workers=...)` — a structured
  concurrency helper built on `asyncio.TaskGroup` (PEP 654). Extractors
  run on a bounded thread pool via `loop.run_in_executor`; failures either
  propagate as an `ExceptionGroup` (`raise_on_error=True`) or are captured
  per document in a `BatchExtractionResult` dataclass with an `ok`
  property. A synchronous `extract_batch` wrapper drives the event loop
  for scripts.
* `annotations_to_dataframe(annotations, *, prefer_arrow=True)` — converts
  any iterable of `TextAnnotation` subclasses into a
  `pandas.DataFrame`. When PyArrow is available the frame uses the
  `dtype_backend="pyarrow"` that became the supported entrypoint in
  pandas 2.2, otherwise it silently falls back to the NumPy backend. Five
  stable columns (`record_type`, `locale`, `text`, `start`, `end`) plus
  user-provided `extra_columns` keep the surface small.
* `find_fuzzy_dates(text, max_edits=1)` — ISO-style date detector that
  leans on the ``regex`` 2024+ fuzzy engine (`{e<=n}`) to survive
  single-character OCR errors. Matches emit both the surface form and a
  safely parsed `datetime.date` (or `None` when outside the calendar).

Every helper ships with ``slots=True`` / ``frozen=True`` dataclasses and
uses PEP 695 ``def f[T](...)`` type-parameter syntax (Python 3.12+), so the
subpackage is a reference for how to spell generic helpers in the rest of
the repo. Coverage: 34 dedicated tests under
`lexnlp/extract/batch/tests/`.

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

### 4.4 NumPy 2.3+ feature uplift *(shipped on `claude/numpy-upgrade-features-qVF34`)*

Three focused helpers convert the existing Python-loop idioms into
vectorised calls that the NumPy ≥ 2.3 floor unlocks:

* **`lexnlp.utils.text_vectors`** — a thin, typed wrapper around
  `numpy.strings` so bulk text preprocessing (normalising whitespace,
  lower-casing, prefix filtering, substring-counting, fixed-width
  slicing) runs as a single SIMD-accelerated C call instead of a Python
  listcomp. Signature is deliberately small and NumPy-native:

  ```python
  from lexnlp.utils.text_vectors import (
      vectorized_lower, vectorized_strip, vectorized_startswith,
      vectorized_substring_count, vectorized_slice,
  )
  ```

  Inputs accept any iterable of strings; outputs are `numpy.ndarray`
  with the `StringDType()` (NumPy 2.1+) or the matching boolean/integer
  result dtype. Used by downstream extractors that currently run
  `[t.lower().strip() for t in texts]` over tens of thousands of
  snippets.

* **`lexnlp.extract.batch.parallel_rng`** — deterministic child
  `numpy.random.Generator` streams for parallel batch extraction. Built
  on `Generator.spawn` (NumPy 2.3), which guarantees statistically
  independent sub-streams from a single parent seed — the legacy
  `RandomState(seed + worker_id)` idiom is known to collide. Returns
  `n` fully-seeded `Generator` instances for use inside
  `extract_batch_async`'s thread pool.

* **`lexnlp.utils.cosine`** — single-line cosine-similarity helper built
  on `numpy.vecdot` (NumPy 2.1+ generalised ufunc). Replaces the
  three-term `dot / linalg.norm / linalg.norm` expression inside
  `lexnlp.extract.common.ocr_rating.ocr_rating_calculator`; the OCR
  rating path now calls the shared helper so the same numerics back
  every cosine comparison in the library.

All three helpers are **`slots=True`** / **`frozen=True`** where
applicable and carry full `numpy.typing.NDArray` hints, so ty can
verify shapes across the batch-extraction stack. Coverage: dedicated
red-first / green tests under
`lexnlp/utils/tests/` and
`lexnlp/extract/batch/tests/`.

### 4.5 Roadmap backlog shipped on `claude/numpy-upgrade-features-qVF34`

The second pass of this branch closes several Tier-A / Tier-B / Tier-C
roadmap items. Every item below was built red-first with a dedicated
unittest module that reproduces the intended contract:

* **Tier A.3 — Pre-commit hooks** — `.pre-commit-config.yaml` wires
  `ruff` (with `--fix` + format), `uv-lock`, the standard
  end-of-file / YAML / TOML / trailing-whitespace hooks, and a local
  `ty check` step. Contributors can install it with
  ``uv run --group lint pre-commit install``.

* **Tier B.9 — `enable_metadata_routing(enabled=True)`** in
  `lexnlp.ml.sklearn_config`. Flips
  ``set_config(enable_metadata_routing=...)`` globally and returns the
  previous value so tests / scripts can restore it (tested in
  `lexnlp/ml/tests/test_sklearn_config.py::TestEnableMetadataRouting`).

* **Tier B.10 — `lexnlp.ml.model_card`** — new module exposing
  `ModelCardMetadata` (frozen, slotted dataclass), `write_model_card`,
  and `dump_model_with_card` which writes the ``.skops`` plus a
  sibling ``.md`` card in one call. Built on ``skops.card`` (already a
  runtime dep). Coverage:
  `lexnlp/ml/tests/test_model_card.py` (7 tests).

* **Tier B.11 — `DEFAULT_TRUSTED_ALLOWLIST`** in
  `lexnlp.ml.model_io`. An explicit frozenset of sklearn / NumPy type
  names is intersected against the artifact's declared untrusted
  types before skops is asked to load — so ``trusted=True`` is no
  longer "accept anything the artifact declares", it is "accept only
  types known to this codebase". Callers with legitimate custom
  estimators extend via the new ``extra_trusted`` argument on
  `load_model` / `_load_skops`. Coverage:
  `lexnlp/ml/tests/test_model_io.py::TestTrustedAllowlist` (5 tests).

* **Tier B.14 — `read_csv_arrow(path, **kwargs)`** in
  `lexnlp.utils.pandas_config`. Passes ``dtype_backend="pyarrow"``
  when PyArrow is importable, otherwise falls back to the default
  NumPy backend. The dependency ships under the new ``[arrow]``
  optional extra in ``pyproject.toml``. Coverage:
  `lexnlp/utils/tests/test_pandas_config_read_csv.py` (6 tests).

* **Tier C.19 — `lexnlp.ml.catalog.hub`** — new module with
  `get_path_from_hub(tag, *, repo_id=DEFAULT_HUB_REPO, revision=None)`,
  `hub_is_available()`, and typed `HubUnavailableError` /
  `HubMirrorError`. Lazy import of `huggingface_hub` keeps it truly
  optional (declared under the ``[hub]`` extra). Coverage:
  `lexnlp/ml/catalog/tests/test_hub.py` (9 tests).

* **Tier D.27 — CI matrix** — `.github/workflows/ci.yml` adds a
  non-blocking `base-tests-py314` job so forward regressions on
  Python 3.14 surface without gating merges.

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
