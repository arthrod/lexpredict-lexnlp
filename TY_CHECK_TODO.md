# `ty check` Diagnostic Backlog

Snapshot taken on branch `claude/mirror-spanish-module-architecture-cUI6Z`
under Python 3.13.12 + numpy 2.4.4. Reproduce with:

```bash
uv run ty check .
```

**Total: 283 diagnostics** (269 errors + 14 warnings). Budget recorded in
`MODERNIZATION_ROADMAP.md` was 558-562; this branch already burnt ~275
down by fixing the over-indented docstrings and adding PT with clean
types.

Order reflects **blast radius × fix cost**: things that block other fixes
or ship unsafe behaviour first, bulk typing chores last.

---

## Tier 1 — correctness blockers (fix first, small surface)

- [ ] **`error[invalid-method-override]` (1)** — `DeDateParser.passed_general_check`
      signature disagrees with base class
      ([de_date_parser.py:46](lexnlp/extract/de/de_date_parser.py)). The
      PT override is already correct; align DE with the base signature so
      `DateParser` subclasses are interchangeable.
- [ ] **`error[index-out-of-bounds]` (1)** — review the single case that ty flags
      and add a bounds guard.
- [ ] **`error[call-non-callable]` (1)** — investigate; almost always a
      bug (calling a property / None / class-stored dict).
- [ ] **`error[missing-argument]` (1)** — fix the incorrect call site.
- [ ] **`error[unknown-argument]` (2)** — remove / rename the bad kwargs.
- [ ] **`error[too-many-positional-arguments]` (2)** — both in
      `lexnlp/extract/all_locales/dates.py` where the dispatcher calls
      `routine(text, strict, locale, base_date, threshold)` but the
      `DateParser.get_date_annotations` signature is
      `(text, locale, strict)`. Fix the dispatcher to invoke the parser
      with keyword arguments so EN/DE/PT/ES share one contract.
- [ ] **`error[unresolved-import]` (2)** — `pyarrow` in
      `lexnlp/extract/batch/pandas_output.py` and `spacy` in
      `lexnlp/extract/ml/classifier/spacy_token_sequence_model.py`. Both
      are optional extras: guard imports with `try/except ImportError` or
      move under `TYPE_CHECKING` and expose them through extras in
      `pyproject.toml`.
- [ ] **`error[invalid-return-type]` (12)** — non-generator functions
      annotated as generators and vice-versa. Walk each and either
      change the annotation or add the missing `yield`.

## Tier 2 — silent-surface correctness (Optional / None handling)

- [ ] **`error[invalid-parameter-default]` (19)** — classic
      `def f(x: T = None)` with no `| None`. Run
      `ruff check --select RUF013 --fix` then audit the callers — some
      intentionally pass `None` and need the annotation to widen rather
      than the default to change.
- [ ] **`error[invalid-assignment]` (51)** — majority are
      `foo: Decimal = maybe_decimal()` where `maybe_decimal` returns
      `Decimal | None`. Either tighten the return type of the helper
      or add an `assert foo is not None` at the assignment. Hotspots:
  - [ ] `lexnlp/extract/common/annotations/text_annotation.py` (21)
  - [ ] `lexnlp/extract/common/annotations/duration_annotation.py` (8)
  - [ ] `lexnlp/extract/en/definition_parsing_methods.py` (several)
  - [ ] one case in `scripts/train_contract_model.py:503` where a
        `bool | str` dict value is assigned an `int` — widen to
        `dict[str, bool | str | int]`.

## Tier 3 — annotation / attribute plumbing

- [ ] **`error[unresolved-attribute]` (53)** — largely dynamic attribute
      access on annotation subclasses (`CourtAnnotation.entity_category`,
      `.entity_priority`, `.name_en`, `.alias`, etc.) and on sklearn /
      pandas objects. Split into three stages:
  - [ ] Declare the annotation attributes in the dataclass directly,
        not via `setattr`. Applies to `CourtAnnotation`,
        `GeoAnnotation`, `RegulationAnnotation`, `DefinitionAnnotation`.
  - [ ] Add `# ty: ignore[unresolved-attribute]` to `ast.AST.lineno` /
        `.col_offset` access (stdlib stubs don't expose them on the base
        class; the concrete subclasses do).
  - [ ] Narrow pandas dynamic access with
        `typing.cast(Series[str], df[col])` where ty can't follow.
- [ ] **`error[not-subscriptable]` (5)** — most are `.values` on pandas
      returning `ndarray` that ty treats as non-subscriptable. Replace
      with `.to_numpy()` + indexing on a typed view.
- [ ] **`error[not-iterable]` (4)** — functions returning `Iterator | None`
      iterated without a None guard.
- [ ] **`error[invalid-argument-type]` (92)** — dominant category. Break
      up by module:
  - [ ] `lexnlp/extract/common/annotations/text_annotation.py` — 21
        `__init__` call sites pass `None` where `str | Decimal` is
        expected.
  - [ ] `lexnlp/extract/common/dates.py` (7) + `lexnlp/extract/pt/dates.py` (5)
        — `get_date_annotations` chain; needs the Tier 1 dispatcher
        contract fix first.
  - [ ] `lexnlp/extract/en/dict_entities.py` (18) — `find_dict_entities`
        expects `list[DictionaryEntry]` but receives `Iterable`.
  - [ ] `lexnlp/extract/common/dates_classifier_model.py` (13) — numpy
        array type narrowing; explicit `dtype=` / cast may fix most.
  - [ ] `lexnlp/nlp/en/segments/sections.py` (10) — legacy list/tuple
        coercions.
  - [ ] `lexnlp/extract/common/date_parsing/datefinder.py` (8).
- [ ] **`error[invalid-yield]` (8)** — each is a `Generator[T]`
      annotation where the yielded expression is `T | None`. Add a
      `if x is not None:` filter before yielding or widen the
      generator type to `T | None`.
- [ ] **`error[unsupported-operator]` (7)** — usually
      `Decimal + float` or `datetime - None`. Coerce explicitly.

## Tier 4 — overload / library surface

- [ ] **`error[no-matching-overload]` (7)** — these point at pandas /
      sklearn overload signatures that moved in 2.x:
  - [ ] `pandas.concat` with `None`-first branch
        (`lexnlp/extract/common/ocr_rating/ocr_rating_calculator.py:96`)
        — guard the `None` case.
  - [ ] `pandas.read_csv` with a dtypes converters dict
        (`lexnlp/extract/common/universal_court_parser.py:169`) — pass
        `converters=dtypes` already works at runtime; cast to
        `Mapping[int, Callable[[str], str]]`.
  - [ ] DE amounts / durations — `.join()` receives an `Iterable` that
        ty narrows to `Iterable[str | None]`.

## Tier 5 — warnings (fast wins)

- [ ] **`warning[deprecated]` (5)** — all five are `codecs.open`-like
      calls to the deprecated `open` helper in
      `lexnlp/extract/common/language_dictionary_reader.py`,
      `…/ocr_rating/lang_vector_distribution_builder.py`,
      `…/ocr_rating/ocr_rating_calculator.py`,
      `…/ml/en/definitions/layered_definition_detector.py`,
      `…/nlp/train/en/train_section_segmanizer.py`. Replace with
      builtin `open(..., encoding=...)`.
- [ ] **`warning[invalid-type-form]` (9)** — mix of
      `Generator[T]` (missing second param) and `List` / `Dict`
      remnants. `ruff check --select UP006,UP007 --fix` handles most.
- [ ] **`warning[unknown-rule]` (1)** — we reference a ty rule that
      doesn't exist on the current release; remove or rename it in
      `pyproject.toml [tool.ty.rules]`.

---

## File-level hotspots (parallelisable)

Run a focused `ty check <file>` while fixing:

| Count | File |
| --- | --- |
| 21 | `lexnlp/extract/common/annotations/text_annotation.py` |
| 18 | `lexnlp/extract/en/dict_entities.py` |
| 13 | `lexnlp/extract/common/dates_classifier_model.py` |
| 12 | `lexnlp/extract/en/definition_parsing_methods.py` |
| 10 | `lexnlp/nlp/en/segments/sections.py` |
| 8 | `lexnlp/extract/common/date_parsing/datefinder.py` |
| 8 | `lexnlp/extract/common/annotations/duration_annotation.py` |
| 7 | `lexnlp/extract/common/dates.py` |
| 7 | `lexnlp/extract/common/copyrights/copyright_parsing_methods.py` |
| 6 | `lexnlp/extract/ml/detector/artifact_detector.py` |
| 6 | `lexnlp/extract/en/entities/company_detector.py` |
| 6 | `lexnlp/extract/all_locales/dates.py` |
| 6 | `lexnlp/extract/all_locales/courts.py` |
| 5 | `lexnlp/ml/sklearn_transformers.py` |
| 5 | `lexnlp/extract/pt/dates.py` |
| 5 | `lexnlp/extract/ml/en/definitions/layered_definition_detector.py` |
| 5 | `lexnlp/extract/de/amounts.py` |
| 5 | `lexnlp/extract/common/text_pattern_collector.py` |
| 4 | `lexnlp/nlp/en/stanford.py` |
| 4 | `lexnlp/extract/ml/detector/phrase_constructor.py` |
| 4 | `lexnlp/extract/en/amounts.py` |
| 4 | `lexnlp/extract/en/addresses/addresses.py` |
| 4 | `lexnlp/extract/de/definitions.py` |
| 4 | `lexnlp/extract/de/de_date_parser.py` |
| 4 | `lexnlp/extract/common/ocr_rating/ocr_rating_calculator.py` |
| 4 | `lexnlp/extract/common/geoentity_detector.py` |
| 4 | `lexnlp/extract/common/copyrights/copyright_parser.py` |

Fix the top-10 files first: that's ~60 % of the backlog.

## Verification

After each tier:

```bash
uv run ty check . 2>&1 | tail -3
```

and gate on the number shrinking. Then re-run the PT/ES/EN test suites:

```bash
uv run pytest lexnlp/extract/pt/tests lexnlp/extract/es/tests -q
```
