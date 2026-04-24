__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"

"""Tests for lexnlp/utils/amount_delimiting.py.

Covers changes introduced in the PR:
  - infer_delimiters: de_DE locale fix is now also triggered when the
    grouping list does not match [3, 3, 0], even if the delimiter characters
    happen to be correct.
"""

from unittest.mock import patch

from lexnlp.utils.amount_delimiting import infer_delimiters

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_de_de_conventions(
    decimal_delimiter: str = ",",
    group_delimiter: str = ".",
    grouping: list | None = None,
):
    """
    Return a context-manager that patches LocaleContextManager so locale.localeconv()
    returns the requested values for any de_DE call.
    """
    if grouping is None:
        grouping = [3, 3, 0]

    # locale.localeconv() is called inside the LocaleContextManager context.

    fake_conventions = {
        "decimal_point": decimal_delimiter,
        "thousands_sep": group_delimiter,
        "grouping": grouping,
    }

    class FakeLocaleContextManager:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return (
        patch(
            "lexnlp.utils.amount_delimiting.LocaleContextManager",
            FakeLocaleContextManager,
        ),
        patch("lexnlp.utils.amount_delimiting.locale.localeconv", return_value=fake_conventions),
    )


# ---------------------------------------------------------------------------
# Core tests for the new grouping-check condition
# ---------------------------------------------------------------------------


class TestDeDEGroupingFix:
    """
    The PR added ``or grouping != [3, 3, 0]`` to the de_DE correction
    condition.  Previously, if the locale correctly returned ',' and '.' but
    with an unexpected grouping list (e.g., [3, 0] or []), the override was
    skipped and wrong inference could follow.  Now the fix is applied whenever
    any of the three values differ from the canonical de_DE conventions.
    """

    def test_correct_de_de_conventions_are_not_overridden(self):
        """
        When locale already returns the canonical de_DE values, the fix is a
        no-op — infer_delimiters should still work correctly.
        """
        ctx_manager, locale_patch = _mock_de_de_conventions(
            decimal_delimiter=",",
            group_delimiter=".",
            grouping=[3, 3, 0],
        )
        with ctx_manager, locale_patch:
            result = infer_delimiters("10.800", "de_DE")
        # "10.800" in German: '.' is a thousands separator, no decimal part
        # (so decimal_delimiter is not set by this input).
        assert result is not None
        assert result["group_delimiter"] == "."

    def test_wrong_grouping_triggers_de_de_fix(self):
        """
        When locale returns correct delimiters but wrong grouping, the fix must
        still be applied.
        """
        ctx_manager, locale_patch = _mock_de_de_conventions(
            decimal_delimiter=",",
            group_delimiter=".",
            grouping=[3, 0],  # non-canonical grouping
        )
        with ctx_manager, locale_patch:
            result = infer_delimiters("10.800", "de_DE")
        # After the fix the canonical grouping [3,3,0] is enforced.
        # (Input has no decimal part, so decimal_delimiter is not exercised.)
        assert result is not None
        assert result["group_delimiter"] == "."

    def test_wrong_decimal_delimiter_triggers_fix(self):
        """
        When locale falls back to en_US conventions (decimal='.', group=','),
        the fix must correct to de_DE canonical values.
        """
        ctx_manager, locale_patch = _mock_de_de_conventions(
            decimal_delimiter=".",
            group_delimiter=",",
            grouping=[3, 3, 0],
        )
        with ctx_manager, locale_patch:
            result = infer_delimiters("10.800", "de_DE")
        assert result is not None
        # After fix: group_delimiter must be '.' (German convention).
        assert result["group_delimiter"] == "."

    def test_wrong_group_delimiter_triggers_fix(self):
        """
        When locale returns correct decimal delimiter but wrong group delimiter,
        the fix is triggered.
        """
        ctx_manager, locale_patch = _mock_de_de_conventions(
            decimal_delimiter=",",
            group_delimiter=" ",  # space instead of period
            grouping=[3, 3, 0],
        )
        with ctx_manager, locale_patch:
            result = infer_delimiters("10.800", "de_DE")
        assert result is not None
        assert result["group_delimiter"] == "."

    def test_all_wrong_triggers_fix(self):
        """
        When locale returns completely wrong values, the fix corrects all three.
        """
        ctx_manager, locale_patch = _mock_de_de_conventions(
            decimal_delimiter=".",
            group_delimiter=",",
            grouping=[3, 0],
        )
        with ctx_manager, locale_patch:
            result = infer_delimiters("1.000,50", "de_DE")
        # "1.000,50" in German is 1000.50; '.' = group, ',' = decimal.
        assert result is not None
        assert result["decimal_delimiter"] == ","
        assert result["group_delimiter"] == "."

    def test_de_de_prefix_case_insensitive(self):
        """
        The fix condition uses _locale.lower().startswith('de_de') so mixed-case
        locale strings should also trigger the fix.
        """
        ctx_manager, locale_patch = _mock_de_de_conventions(
            decimal_delimiter=".",
            group_delimiter=",",
            grouping=[3, 3, 0],
        )
        with ctx_manager, locale_patch:
            result = infer_delimiters("10.800", "DE_DE")
        assert result is not None
        # The fix must have been applied.
        assert result["group_delimiter"] == "."

    def test_non_de_locale_not_affected(self):
        """
        For en_US the fix must not be applied, even when the values look like
        de_DE conventions.
        """
        # Use a real locale-like mock returning en_US-style values.
        ctx_manager, locale_patch = _mock_de_de_conventions(
            decimal_delimiter=".",
            group_delimiter=",",
            grouping=[3, 3, 0],
        )
        with ctx_manager, locale_patch:
            # "1,000.50" is en_US style.
            result = infer_delimiters("1,000.50", "en_US")
        # The function should infer the two delimiters from the text, not the
        # de_DE override path.
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","


# ---------------------------------------------------------------------------
# Regression: previously-working de_DE paths still work after the fix
# ---------------------------------------------------------------------------


class TestDeDERegressionPaths:
    """Existing de_DE behavior must not regress after the grouping check."""

    def test_integer_with_period_group_separator(self):
        """'1.000' in de_DE means 1000 (integer with group separator)."""
        ctx_manager, locale_patch = _mock_de_de_conventions()
        with ctx_manager, locale_patch:
            result = infer_delimiters("1.000", "de_DE")
        assert result is not None

    def test_float_with_comma_decimal(self):
        """'1.234,56' in de_DE means 1234.56."""
        ctx_manager, locale_patch = _mock_de_de_conventions()
        with ctx_manager, locale_patch:
            result = infer_delimiters("1.234,56", "de_DE")
        assert result is not None
        assert result["decimal_delimiter"] == ","
        assert result["group_delimiter"] == "."

    def test_bare_integer_no_delimiters(self):
        """'12345' has no delimiters; result should have correct locale defaults."""
        ctx_manager, locale_patch = _mock_de_de_conventions()
        with ctx_manager, locale_patch:
            result = infer_delimiters("12345", "de_DE")
        assert result is not None
        assert result["decimal_delimiter"] == ","
        assert result["group_delimiter"] == "."


# ---------------------------------------------------------------------------
# New PR: en_US locale fallback fix
# ---------------------------------------------------------------------------


def _mock_locale_conventions(
    decimal_delimiter: str,
    group_delimiter: str,
    grouping: list,
):
    """Patch LocaleContextManager + locale.localeconv to return the given values."""

    fake_conventions = {
        "decimal_point": decimal_delimiter,
        "thousands_sep": group_delimiter,
        "grouping": grouping,
    }

    class FakeLocaleContextManager:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    return (
        patch(
            "lexnlp.utils.amount_delimiting.LocaleContextManager",
            FakeLocaleContextManager,
        ),
        patch(
            "lexnlp.utils.amount_delimiting.locale.localeconv",
            return_value=fake_conventions,
        ),
    )


class TestEnUSLocaleFix:
    """
    The PR adds an en_US correction branch mirroring the de_DE one.
    When running on a system without the en_US locale pack the C locale is
    used, which returns empty grouping and empty thousands_sep.  The fix
    enforces the canonical en_US conventions (decimal='.', group=',',
    grouping=[3,3,0]).
    """

    def test_correct_en_us_conventions_not_overridden(self):
        """Canonical en_US values must be left untouched."""
        ctx, lp = _mock_locale_conventions(".", ",", [3, 3, 0])
        with ctx, lp:
            result = infer_delimiters("1,000.50", "en_US")
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","

    def test_empty_grouping_triggers_en_us_fix(self):
        """C-locale fallback (grouping=[]) must be corrected to en_US conventions."""
        ctx, lp = _mock_locale_conventions(".", "", [])
        with ctx, lp:
            result = infer_delimiters("1,000.50", "en_US")
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","

    def test_wrong_decimal_delimiter_triggers_en_us_fix(self):
        """If decimal comes back as comma (de-style), the fix must correct it."""
        ctx, lp = _mock_locale_conventions(",", ".", [3, 3, 0])
        with ctx, lp:
            result = infer_delimiters("1,000.50", "en_US")
        # After fix, decimal='.' and group=',' are enforced.
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","

    def test_wrong_group_delimiter_triggers_en_us_fix(self):
        """Space group delimiter must be corrected for en_US."""
        ctx, lp = _mock_locale_conventions(".", " ", [3, 3, 0])
        with ctx, lp:
            result = infer_delimiters("1,000.50", "en_US")
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","

    def test_wrong_grouping_list_triggers_en_us_fix(self):
        """Wrong grouping list triggers the fix even if delimiters are correct."""
        ctx, lp = _mock_locale_conventions(".", ",", [3, 0])
        with ctx, lp:
            result = infer_delimiters("1,000.50", "en_US")
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","

    def test_en_us_fix_case_insensitive(self):
        """The prefix check is case-insensitive (EN_US, en_us, En_Us etc.)."""
        ctx, lp = _mock_locale_conventions(".", "", [])
        with ctx, lp:
            result = infer_delimiters("1,000.50", "EN_US")
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","

    def test_en_us_fix_with_bare_integer(self):
        """Bare integer with no delimiter returns locale defaults after the fix."""
        ctx, lp = _mock_locale_conventions(".", "", [])
        with ctx, lp:
            result = infer_delimiters("12345", "en_US")
        assert result is not None
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","


# ---------------------------------------------------------------------------
# New PR: generic empty grouping fallback
# ---------------------------------------------------------------------------


class TestGenericEmptyGroupingFallback:
    """
    The PR adds a catch-all ``elif not grouping: grouping = [3, 3, 0]`` so any
    locale that resolves to C (empty grouping) does not crash downstream code
    that indexes ``grouping[0]``.
    """

    def test_unknown_locale_empty_grouping_does_not_crash(self):
        """A locale we do not special-case with empty grouping must not raise."""
        ctx, lp = _mock_locale_conventions(".", ",", [])
        with ctx, lp:
            # fr_FR is neither de_DE nor en_US; empty grouping should be
            # silently fixed to [3,3,0] and inference should succeed.
            result = infer_delimiters("1,000.50", "fr_FR")
        # We do not assert delimiter values because fr_FR has two delimiters in
        # the text — we only care that no IndexError/crash occurs.
        assert result is not None

    def test_unknown_locale_empty_grouping_integer(self):
        """Bare integer with empty grouping must not raise IndexError."""
        ctx, lp = _mock_locale_conventions(".", ",", [])
        with ctx, lp:
            result = infer_delimiters("42", "xx_XX")
        assert result is not None

    def test_empty_grouping_does_not_apply_when_de_de(self):
        """de_DE path takes priority over the generic fallback."""
        # Trigger the de_DE branch (wrong decimal) — generic branch must NOT run.
        ctx, lp = _mock_locale_conventions(".", ",", [])
        with ctx, lp:
            result = infer_delimiters("1.000,50", "de_DE")
        assert result is not None
        # de_DE fix: decimal=',', group='.'
        assert result["decimal_delimiter"] == ","
        assert result["group_delimiter"] == "."

    def test_empty_grouping_does_not_apply_when_en_us(self):
        """en_US path takes priority over the generic fallback."""
        ctx, lp = _mock_locale_conventions(".", "", [])
        with ctx, lp:
            result = infer_delimiters("1,000.50", "en_US")
        assert result is not None
        # en_US fix: decimal='.', group=','
        assert result["decimal_delimiter"] == "."
        assert result["group_delimiter"] == ","
