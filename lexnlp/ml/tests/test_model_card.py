__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


from pathlib import Path
from unittest import TestCase

from sklearn.linear_model import LogisticRegression

from lexnlp.ml.model_card import (
    ModelCardMetadata,
    dump_model_with_card,
    write_model_card,
)


class TestWriteModelCard(TestCase):
    def setUp(self) -> None:
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmpdir = Path(self.tmp.name)

    def _fitted_estimator(self) -> LogisticRegression:
        clf = LogisticRegression(max_iter=50, solver="lbfgs")
        # tiny fixture so add_hyperparams works without errors
        clf.fit([[0.0], [1.0]], [0, 1])
        return clf

    def test_returns_path_with_md_extension(self) -> None:
        clf = self._fitted_estimator()
        md = ModelCardMetadata(
            description="LexNLP date classifier",
            license="AGPL-3.0-or-later",
            authors="ContraxSuite, LLC",
        )
        out = write_model_card(clf, self.tmpdir / "date_model", metadata=md)
        self.assertEqual(out.suffix, ".md")
        self.assertTrue(out.exists())

    def test_card_contains_metadata(self) -> None:
        clf = self._fitted_estimator()
        md = ModelCardMetadata(
            description="LexNLP date classifier",
            license="AGPL-3.0-or-later",
            authors="ContraxSuite, LLC",
        )
        out = write_model_card(clf, self.tmpdir / "date_model.md", metadata=md)
        content = out.read_text(encoding="utf-8")
        self.assertIn("LexNLP date classifier", content)

    def test_card_metrics_table_included(self) -> None:
        clf = self._fitted_estimator()
        md = ModelCardMetadata(description="x", license="", authors="")
        out = write_model_card(
            clf,
            self.tmpdir / "m.md",
            metadata=md,
            metrics={"accuracy": 0.91, "f1_macro": 0.87},
        )
        content = out.read_text(encoding="utf-8")
        self.assertIn("accuracy", content)
        self.assertIn("0.91", content)

    def test_dump_model_with_card_writes_both_artifacts(self) -> None:
        clf = self._fitted_estimator()
        md = ModelCardMetadata(description="x", license="", authors="")
        paths = dump_model_with_card(
            clf,
            self.tmpdir / "contract_type",
            metadata=md,
            metrics={"accuracy": 0.95},
        )
        self.assertTrue(paths.model.exists())
        self.assertEqual(paths.model.suffix, ".skops")
        self.assertTrue(paths.card.exists())
        self.assertEqual(paths.card.suffix, ".md")

    def test_dump_model_with_card_returns_sibling_paths(self) -> None:
        clf = self._fitted_estimator()
        md = ModelCardMetadata(description="x", license="", authors="")
        paths = dump_model_with_card(
            clf,
            self.tmpdir / "x",
            metadata=md,
        )
        self.assertEqual(paths.model.stem, paths.card.stem)
        self.assertEqual(paths.model.parent, paths.card.parent)


class TestModelCardMetadataValidation(TestCase):
    def test_required_description(self) -> None:
        with self.assertRaises((TypeError, ValueError)):
            ModelCardMetadata()  # type: ignore[call-arg]

    def test_frozen(self) -> None:
        md = ModelCardMetadata(description="x", license="", authors="")
        with self.assertRaises((AttributeError, Exception)):
            md.description = "changed"  # type: ignore[misc]
