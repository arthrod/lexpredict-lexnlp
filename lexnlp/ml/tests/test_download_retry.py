"""Tests for the retry-capable session builder in ``lexnlp.ml.catalog.download``."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from lexnlp.ml.catalog.download import build_retry_session


class TestBuildRetrySession:
    def test_returns_session(self) -> None:
        session = build_retry_session()
        assert isinstance(session, Session)

    def test_adapters_configured(self) -> None:
        session = build_retry_session()
        for scheme in ("http://", "https://"):
            adapter = session.adapters[scheme]
            assert isinstance(adapter, HTTPAdapter)

    def test_retry_policy_applies(self) -> None:
        session = build_retry_session(total_retries=5, backoff_factor=2.0)
        adapter: HTTPAdapter = session.adapters["https://"]
        retry: Retry = adapter.max_retries
        assert retry.total == 5
        assert retry.backoff_factor == 2.0
        assert 429 in retry.status_forcelist
        assert 503 in retry.status_forcelist
