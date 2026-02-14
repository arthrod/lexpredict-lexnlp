from lexnlp.extract.en.contracts.predictors import (
    ProbabilityPredictorContractType,
    ProbabilityPredictorIsContract,
)


def test_is_contract_default_pipeline_tag_no_env(monkeypatch):
    monkeypatch.delenv("LEXNLP_IS_CONTRACT_MODEL_TAG", raising=False)
    assert ProbabilityPredictorIsContract.get_default_pipeline_tag() == "pipeline/is-contract/0.1"


def test_is_contract_default_pipeline_tag_with_env(monkeypatch):
    monkeypatch.setenv("LEXNLP_IS_CONTRACT_MODEL_TAG", "pipeline/is-contract/0.2")
    assert ProbabilityPredictorIsContract.get_default_pipeline_tag() == "pipeline/is-contract/0.2"


def test_contract_type_default_pipeline_tag_no_env(monkeypatch):
    monkeypatch.delenv("LEXNLP_CONTRACT_TYPE_MODEL_TAG", raising=False)
    assert ProbabilityPredictorContractType.get_default_pipeline_tag() == "pipeline/contract-type/0.1"


def test_contract_type_default_pipeline_tag_with_env(monkeypatch):
    monkeypatch.setenv("LEXNLP_CONTRACT_TYPE_MODEL_TAG", "pipeline/contract-type/0.2")
    assert ProbabilityPredictorContractType.get_default_pipeline_tag() == "pipeline/contract-type/0.2"
