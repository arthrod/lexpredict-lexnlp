"""Tests targeting the PR-16 change to ``_row_from_annotation`` in
:mod:`lexnlp.extract.batch.pandas_output`.

The PR replaced a ``try/except (TypeError, ValueError)`` guard around
``start, end = coords`` with an explicit ``isinstance(coords, (tuple, list))
and len(coords) == 2`` check. Both should produce the same observable
behaviour for the common cases, but the isinstance path additionally:

* Accepts a **list** of length 2 (was silently accepted via tuple-unpack
  before, but the intent is now explicit).
* Rejects tuples or lists of length != 2 with ``None, None`` rather than
  raising ``ValueError``.
* Rejects non-sequence types (int, str, dict, …) with ``None, None``
  rather than raising ``TypeError``.

The module does not use PEP-695 syntax, so these tests run on Python 3.11+
as long as pandas is installed.  We import the module directly to bypass
the batch ``__init__.py`` which does require Python 3.12.
"""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

import importlib.util
import pathlib

import pytest

# pandas is an optional runtime dependency for batch output helpers.
pytest.importorskip("pandas")

# Import pandas_output directly so we work on Python < 3.12 as well.
_spec = importlib.util.spec_from_file_location(
    "lexnlp.extract.batch.pandas_output",
    str(pathlib.Path(__file__).parent.parent / "pandas_output.py"),
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

_row_from_annotation = _mod._row_from_annotation


# ---------------------------------------------------------------------------
# Helpers — minimal annotation-like objects
# ---------------------------------------------------------------------------


class _Ann:
    """Minimal annotation object with configurable coords."""

    def __init__(self, coords, *, text="t", locale="en", record_type="stub"):
        self.coords = coords
        self.text = text
        self.locale = locale
        self.record_type = record_type


class _NoCoords:
    text = "t"
    locale = "en"
    record_type = "no-coords"


# ---------------------------------------------------------------------------
# isinstance branch — tuple-based coords (existing behaviour)
# ---------------------------------------------------------------------------


class TestTupleCoords:
    def test_valid_tuple_extracts_start_end(self) -> None:
        row = _row_from_annotation(_Ann(coords=(10, 25)))
        assert row["start"] == 10
        assert row["end"] == 25

    def test_zero_based_tuple(self) -> None:
        row = _row_from_annotation(_Ann(coords=(0, 0)))
        assert row["start"] == 0
        assert row["end"] == 0

    def test_large_offsets(self) -> None:
        row = _row_from_annotation(_Ann(coords=(50_000, 99_999)))
        assert row["start"] == 50_000
        assert row["end"] == 99_999


# ---------------------------------------------------------------------------
# isinstance branch — list-based coords (NEW explicit path in PR-16)
# ---------------------------------------------------------------------------


class TestListCoords:
    """The PR-16 isinstance check explicitly handles ``list`` in addition to
    ``tuple``.  A list of length 2 must unpack correctly, not return None.
    """

    def test_list_coords_extracts_start_end(self) -> None:
        row = _row_from_annotation(_Ann(coords=[5, 20]))
        assert row["start"] == 5
        assert row["end"] == 20

    def test_list_with_zero_values(self) -> None:
        row = _row_from_annotation(_Ann(coords=[0, 0]))
        assert row["start"] == 0
        assert row["end"] == 0

    def test_list_single_element_gives_none(self) -> None:
        # A list with only one element fails the len()==2 guard.
        row = _row_from_annotation(_Ann(coords=[7]))
        assert row["start"] is None
        assert row["end"] is None

    def test_list_three_elements_gives_none(self) -> None:
        row = _row_from_annotation(_Ann(coords=[1, 2, 3]))
        assert row["start"] is None
        assert row["end"] is None

    def test_empty_list_gives_none(self) -> None:
        row = _row_from_annotation(_Ann(coords=[]))
        assert row["start"] is None
        assert row["end"] is None


# ---------------------------------------------------------------------------
# isinstance branch — wrong-length tuples (PR-16 change: explicit None,None)
# ---------------------------------------------------------------------------


class TestWrongLengthTuple:
    def test_tuple_length_one_gives_none(self) -> None:
        row = _row_from_annotation(_Ann(coords=(42,)))
        assert row["start"] is None
        assert row["end"] is None

    def test_tuple_length_three_gives_none(self) -> None:
        row = _row_from_annotation(_Ann(coords=(1, 2, 3)))
        assert row["start"] is None
        assert row["end"] is None

    def test_empty_tuple_gives_none(self) -> None:
        row = _row_from_annotation(_Ann(coords=()))
        assert row["start"] is None
        assert row["end"] is None


# ---------------------------------------------------------------------------
# isinstance branch — non-sequence coords (PR-16 change: explicit None,None)
# ---------------------------------------------------------------------------


class TestNonSequenceCoords:
    def test_integer_coords_gives_none(self) -> None:
        row = _row_from_annotation(_Ann(coords=42))
        assert row["start"] is None
        assert row["end"] is None

    def test_string_coords_gives_none(self) -> None:
        # A string of length 2 ("ab") IS iterable but is NOT a tuple/list.
        row = _row_from_annotation(_Ann(coords="ab"))
        assert row["start"] is None
        assert row["end"] is None

    def test_dict_coords_gives_none(self) -> None:
        row = _row_from_annotation(_Ann(coords={"start": 0, "end": 5}))
        assert row["start"] is None
        assert row["end"] is None

    def test_none_coords_attr_gives_none(self) -> None:
        # When coords is None itself (not a tuple/list).
        row = _row_from_annotation(_Ann(coords=None))
        assert row["start"] is None
        assert row["end"] is None


# ---------------------------------------------------------------------------
# Missing coords attribute entirely
# ---------------------------------------------------------------------------


class TestMissingCoordsAttribute:
    def test_no_coords_attribute_gives_none(self) -> None:
        row = _row_from_annotation(_NoCoords())
        assert row["start"] is None
        assert row["end"] is None


# ---------------------------------------------------------------------------
# (None, None) tuple — valid 2-element tuple containing None values
# ---------------------------------------------------------------------------


class TestNoneTupleCoords:
    def test_none_none_tuple_yields_none_start_end(self) -> None:
        """(None, None) is a valid 2-tuple; start/end become None after unpack."""
        row = _row_from_annotation(_Ann(coords=(None, None)))
        assert row["start"] is None
        assert row["end"] is None

    def test_none_none_list_yields_none_start_end(self) -> None:
        row = _row_from_annotation(_Ann(coords=[None, None]))
        assert row["start"] is None
        assert row["end"] is None


# ---------------------------------------------------------------------------
# Other row fields are unaffected by coords changes
# ---------------------------------------------------------------------------


class TestNonCoordsFields:
    def test_record_type_extracted(self) -> None:
        row = _row_from_annotation(_Ann(coords=(0, 1), record_type="date"))
        assert row["record_type"] == "date"

    def test_locale_extracted(self) -> None:
        row = _row_from_annotation(_Ann(coords=(0, 1), locale="de"))
        assert row["locale"] == "de"

    def test_text_extracted(self) -> None:
        row = _row_from_annotation(_Ann(coords=(0, 5), text="hello"))
        assert row["text"] == "hello"

    def test_coords_error_does_not_affect_other_fields(self) -> None:
        # Even when coords cannot be parsed, the rest of the row is populated.
        row = _row_from_annotation(_Ann(coords="invalid", text="ok", locale="fr"))
        assert row["start"] is None
        assert row["end"] is None
        assert row["text"] == "ok"
        assert row["locale"] == "fr"
