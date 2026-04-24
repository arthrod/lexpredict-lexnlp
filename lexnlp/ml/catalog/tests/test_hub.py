__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from lexnlp.ml.catalog.hub import (
    DEFAULT_HUB_REPO,
    HubMirrorError,
    HubUnavailableError,
    get_path_from_hub,
    hub_is_available,
)


class TestHubAvailability(TestCase):
    def test_returns_false_when_huggingface_hub_missing(self) -> None:
        """When huggingface_hub is not installed the probe reports False
        rather than raising."""
        with patch.dict("sys.modules", {"huggingface_hub": None}):
            self.assertFalse(hub_is_available())

    def test_returns_true_when_import_works(self) -> None:
        import types

        fake = types.ModuleType("huggingface_hub")
        fake.hf_hub_download = lambda **kwargs: "/tmp/fake"  # type: ignore[attr-defined]
        with patch.dict("sys.modules", {"huggingface_hub": fake}):
            self.assertTrue(hub_is_available())


class TestGetPathFromHub(TestCase):
    def test_raises_hub_unavailable_when_missing(self) -> None:
        with patch.dict("sys.modules", {"huggingface_hub": None}):
            with self.assertRaises(HubUnavailableError):
                get_path_from_hub("some-tag")

    def test_calls_hf_hub_download_with_default_repo(self) -> None:
        import types

        calls: list[dict] = []

        def fake_download(**kwargs):
            calls.append(kwargs)
            return "/tmp/mock/path"

        fake = types.ModuleType("huggingface_hub")
        fake.hf_hub_download = fake_download  # type: ignore[attr-defined]
        with patch.dict("sys.modules", {"huggingface_hub": fake}):
            result = get_path_from_hub("addresses_clf")
        self.assertEqual(result, Path("/tmp/mock/path"))
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["repo_id"], DEFAULT_HUB_REPO)
        self.assertEqual(calls[0]["filename"], "addresses_clf")

    def test_forwards_revision(self) -> None:
        import types

        calls: list[dict] = []

        def fake_download(**kwargs):
            calls.append(kwargs)
            return "/tmp/rev"

        fake = types.ModuleType("huggingface_hub")
        fake.hf_hub_download = fake_download  # type: ignore[attr-defined]
        with patch.dict("sys.modules", {"huggingface_hub": fake}):
            get_path_from_hub("tag", revision="v2.3.0")
        self.assertEqual(calls[0]["revision"], "v2.3.0")

    def test_honours_custom_repo_id(self) -> None:
        import types

        calls: list[dict] = []

        def fake_download(**kwargs):
            calls.append(kwargs)
            return "/tmp/custom"

        fake = types.ModuleType("huggingface_hub")
        fake.hf_hub_download = fake_download  # type: ignore[attr-defined]
        with patch.dict("sys.modules", {"huggingface_hub": fake}):
            get_path_from_hub("tag", repo_id="my-org/my-models")
        self.assertEqual(calls[0]["repo_id"], "my-org/my-models")

    def test_returns_pathlib_path(self) -> None:
        import types

        fake = types.ModuleType("huggingface_hub")
        fake.hf_hub_download = lambda **kwargs: "/tmp/abc"  # type: ignore[attr-defined]
        with patch.dict("sys.modules", {"huggingface_hub": fake}):
            result = get_path_from_hub("tag")
        self.assertIsInstance(result, Path)

    def test_wraps_hub_errors(self) -> None:
        import types

        def fake_download(**kwargs):
            raise RuntimeError("404 not found")

        fake = types.ModuleType("huggingface_hub")
        fake.hf_hub_download = fake_download  # type: ignore[attr-defined]
        with patch.dict("sys.modules", {"huggingface_hub": fake}):
            with self.assertRaises(HubMirrorError):
                get_path_from_hub("missing-tag")


class TestDefaultRepo(TestCase):
    def test_default_repo_shape(self) -> None:
        self.assertIn("/", DEFAULT_HUB_REPO)
