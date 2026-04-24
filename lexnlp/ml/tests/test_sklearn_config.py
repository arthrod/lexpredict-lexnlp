"""Tests for :mod:`lexnlp.ml.sklearn_config`."""

from __future__ import annotations

__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


import pytest

from lexnlp.ml.sklearn_config import (
    configure_pipeline_for_dataframes,
    enable_pandas_output,
    new_hist_gradient_boosting_classifier,
)


class TestEnablePandasOutput:
    def test_sets_config(self) -> None:
        from sklearn import get_config, set_config

        # Cache existing config and restore it after the test
        previous = get_config().get("transform_output", "default")
        try:
            enable_pandas_output()
            assert get_config()["transform_output"] == "pandas"
        finally:
            set_config(transform_output=previous)


class TestHistGradientBoostingFactory:
    def test_returns_classifier(self) -> None:
        from sklearn.ensemble import HistGradientBoostingClassifier

        clf = new_hist_gradient_boosting_classifier()
        assert isinstance(clf, HistGradientBoostingClassifier)
        assert clf.max_iter == 200
        assert clf.early_stopping is True

    def test_kwargs_override_defaults(self) -> None:
        clf = new_hist_gradient_boosting_classifier(max_iter=50, learning_rate=0.05)
        assert clf.max_iter == 50
        assert clf.learning_rate == 0.05


class TestConfigurePipeline:
    def test_sets_output_on_pipeline(self) -> None:
        pytest.importorskip("sklearn")
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        pipe = Pipeline([("scaler", StandardScaler())])
        result = configure_pipeline_for_dataframes(pipe)
        assert result is pipe
        # Round-trip a tiny DataFrame through the pipeline to confirm
        # the transformer emits a DataFrame rather than an ndarray.
        pd = pytest.importorskip("pandas")
        df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]})
        pipe.fit(df)
        out = pipe.transform(df)
        assert isinstance(out, pd.DataFrame)
        assert list(out.columns) == ["a", "b"]
