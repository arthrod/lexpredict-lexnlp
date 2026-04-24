"""Tests for ``feature_mask`` Optional fix.

PR #14 review required ``feature_mask: list[int] | None = None`` (RUF013).
This test inspects the abstract base signature so it stays honest even
if subclasses drift.
"""

from __future__ import annotations

import inspect

import numpy as np

from lexnlp.extract.ml.classifier.base_token_sequence_classifier_model import (
    BaseTokenSequenceClassifierModel,
)


class TestFeatureMaskSignature:
    def test_get_feature_data_default_is_none(self) -> None:
        """
        Ensure BaseTokenSequenceClassifierModel.get_feature_data declares a `feature_mask` parameter whose default value is None.
        """
        sig = inspect.signature(BaseTokenSequenceClassifierModel.get_feature_data)
        assert sig.parameters["feature_mask"].default is None

    def test_run_model_default_is_none(self) -> None:
        """
        Verify that BaseTokenSequenceClassifierModel.run_model declares a `feature_mask` parameter with a default value of None.
        """
        sig = inspect.signature(BaseTokenSequenceClassifierModel.run_model)
        assert sig.parameters["feature_mask"].default is None

    def test_run_model_positional_args_are_typed(self) -> None:
        sig = inspect.signature(BaseTokenSequenceClassifierModel.run_model)
        assert "outer_class" in sig.parameters
        assert "start_class" in sig.parameters
        assert "inner_class" in sig.parameters
        assert "end_class" in sig.parameters


class _StubModel:
    def __init__(self, predictions: list[int]) -> None:
        self._predictions = np.array(predictions)

    def predict(self, _feature_data):
        return self._predictions


class _StubSequenceModel(BaseTokenSequenceClassifierModel):
    def get_feature_list(self, *args):
        del args
        return []

    def get_feature_data(self, text: str, feature_mask: list[int] | None = None):
        del text, feature_mask
        return np.empty((3, 0)), [(0, 1), (2, 3), (4, 5)]


class TestRunModelNonStrict:
    def test_end_without_start_does_not_yield_negative_index_span(self) -> None:
        model = _StubSequenceModel()
        model.model = _StubModel([3, 0, 0])

        assert list(model.run_model("abc", strict=False)) == []
