"""Tests for ``feature_mask`` Optional fix.

PR #14 review required ``feature_mask: list[int] | None = None`` (RUF013).
This test inspects the abstract base signature so it stays honest even
if subclasses drift.
"""

from __future__ import annotations

import inspect

from lexnlp.extract.ml.classifier.base_token_sequence_classifier_model import (
    BaseTokenSequenceClassifierModel,
)


class TestFeatureMaskSignature:
    def test_get_feature_data_default_is_none(self) -> None:
        sig = inspect.signature(BaseTokenSequenceClassifierModel.get_feature_data)
        assert sig.parameters["feature_mask"].default is None

    def test_run_model_default_is_none(self) -> None:
        sig = inspect.signature(BaseTokenSequenceClassifierModel.run_model)
        assert sig.parameters["feature_mask"].default is None

    def test_run_model_positional_args_are_typed(self) -> None:
        sig = inspect.signature(BaseTokenSequenceClassifierModel.run_model)
        assert "outer_class" in sig.parameters
        assert "start_class" in sig.parameters
        assert "inner_class" in sig.parameters
        assert "end_class" in sig.parameters
