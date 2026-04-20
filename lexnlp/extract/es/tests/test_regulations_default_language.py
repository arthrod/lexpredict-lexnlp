"""Tests for the ``language`` Optional fix in :mod:`lexnlp.extract.es.regulations`.

PR #14 review flagged ``get_regulation_list(text: str, language: str = None)``
as an implicit Optional. The updated signature is ``language: str | None = None``
and the function now substitutes the default ``'es'`` when ``None`` is passed.
"""

from __future__ import annotations

from unittest.mock import patch

from lexnlp.extract.es import regulations


class TestGetRegulationListLanguageFallback:
    @patch.object(regulations, "get_regulations", return_value=iter([]))
    def test_none_language_uses_default_es(self, mock_get: object) -> None:
        regulations.get_regulation_list("texto español", language=None)
        mock_get.assert_called_once()  # type: ignore[attr-defined]
        args, _kwargs = mock_get.call_args  # type: ignore[attr-defined]
        assert args[1] == "es"

    @patch.object(regulations, "get_regulations", return_value=iter([]))
    def test_explicit_language_passes_through(self, mock_get: object) -> None:
        regulations.get_regulation_list("texto", language="pt")
        args, _kwargs = mock_get.call_args  # type: ignore[attr-defined]
        assert args[1] == "pt"

    @patch.object(regulations, "get_regulations", return_value=iter([]))
    def test_returns_list(self, _mock_get: object) -> None:
        result = regulations.get_regulation_list("texto")
        assert result == []
