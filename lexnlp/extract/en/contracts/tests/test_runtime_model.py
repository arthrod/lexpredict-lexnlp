__author__ = "ContraxSuite, LLC; LexPredict, LLC"
__copyright__ = "Copyright 2015-2021, ContraxSuite, LLC"
__license__ = "https://github.com/LexPredict/lexpredict-lexnlp/blob/2.3.0/LICENSE"
__version__ = "2.3.0"
__maintainer__ = "LexPredict, LLC"
__email__ = "support@contraxsuite.com"


def test_ensure_runtime_contract_type_model_force_trains(monkeypatch, tmp_path):
    """
    Regression test: force=True should bypass reusing/downloading the target tag and
    retrain + overwrite the runtime model.
    """
    from lexnlp.extract.en.contracts import runtime_model

    calls = []

    def ensure_tag_downloaded(tag: str):
        calls.append(("ensure_tag_downloaded", tag))
        if tag == runtime_model.RUNTIME_CONTRACT_TYPE_TAG:
            raise AssertionError("force=True should not attempt to download the target tag")
        return tmp_path / "corpus.tar.xz"

    def collect_samples(_archive_path, *, max_docs_per_label: int, head_character_n: int):
        calls.append(("collect_contract_type_samples", max_docs_per_label, head_character_n))
        return ["doc-a", "doc-b"], ["A", "B"], {"A": 1, "B": 1}

    def train_pipeline(texts, labels, *, random_state: int):
        calls.append(("train_contract_type_pipeline", len(texts), len(labels), random_state))
        return object()

    def write_pipeline(*, pipeline, target_tag: str, force: bool):
        calls.append(("write_pipeline_to_catalog", target_tag, force))
        destination = tmp_path / "pipeline_contract_type_classifier.cloudpickle"
        destination.write_bytes(b"dummy")
        return destination, True

    monkeypatch.setattr(runtime_model, "ensure_tag_downloaded", ensure_tag_downloaded)
    monkeypatch.setattr(runtime_model, "collect_contract_type_samples", collect_samples)
    monkeypatch.setattr(runtime_model, "train_contract_type_pipeline", train_pipeline)
    monkeypatch.setattr(runtime_model, "write_pipeline_to_catalog", write_pipeline)

    import lexnlp.ml.catalog

    def get_path_from_catalog(_tag: str):
        raise AssertionError("force=True should not consult the existing catalog path")

    monkeypatch.setattr(lexnlp.ml.catalog, "get_path_from_catalog", get_path_from_catalog)

    result = runtime_model.ensure_runtime_contract_type_model(
        target_tag=runtime_model.RUNTIME_CONTRACT_TYPE_TAG,
        force=True,
    )

    assert result == tmp_path / "pipeline_contract_type_classifier.cloudpickle"
    assert ("write_pipeline_to_catalog", runtime_model.RUNTIME_CONTRACT_TYPE_TAG, True) in calls


# ---------------------------------------------------------------------------
# write_pipeline_to_catalog – returns Tuple[Path, bool]
# ---------------------------------------------------------------------------


def test_write_pipeline_to_catalog_returns_path_and_true_when_new(monkeypatch, tmp_path):
    """
    When the destination does not yet exist, write_pipeline_to_catalog must
    serialize the pipeline and return (path, True).
    """
    from lexnlp.extract.en.contracts import runtime_model
    from lexnlp.ml.model_io import load_model

    monkeypatch.setattr(runtime_model, "CATALOG", tmp_path, raising=False)

    # Patch the CATALOG import inside write_pipeline_to_catalog
    import lexnlp.ml.catalog as catalog_mod

    monkeypatch.setattr(catalog_mod, "CATALOG", tmp_path)

    # Use a simple picklable object as the "pipeline".
    dummy_pipeline = {"weights": [1, 2, 3]}

    destination, wrote = runtime_model.write_pipeline_to_catalog(
        pipeline=dummy_pipeline,
        target_tag="pipeline/test/0.1",
        force=False,
    )

    assert wrote is True
    assert destination.exists()
    assert destination.name == runtime_model.CONTRACT_TYPE_MODEL_FILENAME
    # Verify the content is the serialized pipeline.
    loaded = load_model(destination, trusted=True)
    assert loaded == dummy_pipeline


def test_write_pipeline_to_catalog_returns_false_when_artifact_exists(monkeypatch, tmp_path):
    """
    When the destination already exists and force=False, the function must
    NOT overwrite it and must return (path, False).
    """
    import lexnlp.ml.catalog as catalog_mod
    from lexnlp.extract.en.contracts import runtime_model

    monkeypatch.setattr(catalog_mod, "CATALOG", tmp_path)

    # Pre-create the destination file.
    target_dir = tmp_path / "pipeline" / "test" / "0.1"
    target_dir.mkdir(parents=True)
    existing_file = target_dir / runtime_model.CONTRACT_TYPE_MODEL_FILENAME
    existing_file.write_bytes(b"original content")

    dummy_pipeline = {"weights": [9, 9, 9]}

    destination, wrote = runtime_model.write_pipeline_to_catalog(
        pipeline=dummy_pipeline,
        target_tag="pipeline/test/0.1",
        force=False,
    )

    assert wrote is False
    assert destination == existing_file
    # Content must be unchanged.
    assert destination.read_bytes() == b"original content"


def test_write_pipeline_to_catalog_force_overwrites_existing(monkeypatch, tmp_path):
    """
    When force=True, an existing artifact must be overwritten and (path, True)
    must be returned.
    """
    import lexnlp.ml.catalog as catalog_mod
    from lexnlp.extract.en.contracts import runtime_model
    from lexnlp.ml.model_io import load_model

    monkeypatch.setattr(catalog_mod, "CATALOG", tmp_path)

    target_dir = tmp_path / "pipeline" / "test" / "0.2"
    target_dir.mkdir(parents=True)
    existing_file = target_dir / runtime_model.CONTRACT_TYPE_MODEL_FILENAME
    existing_file.write_bytes(b"old content")

    new_pipeline = {"version": 2}

    destination, wrote = runtime_model.write_pipeline_to_catalog(
        pipeline=new_pipeline,
        target_tag="pipeline/test/0.2",
        force=True,
    )

    assert wrote is True
    assert destination == existing_file
    loaded = load_model(destination, trusted=True)
    assert loaded == new_pipeline


def test_write_pipeline_to_catalog_creates_parent_directories(monkeypatch, tmp_path):
    """
    The function must create any missing parent directories for the destination.
    """
    import lexnlp.ml.catalog as catalog_mod
    from lexnlp.extract.en.contracts import runtime_model

    monkeypatch.setattr(catalog_mod, "CATALOG", tmp_path)

    # Ensure the nested tag directories do not exist yet.
    deep_tag = "pipeline/deep/nested/tag/0.1"
    destination, wrote = runtime_model.write_pipeline_to_catalog(
        pipeline={"x": 1},
        target_tag=deep_tag,
        force=False,
    )

    assert wrote is True
    assert destination.parent.is_dir()


def test_write_pipeline_to_catalog_skips_when_legacy_file_exists(monkeypatch, tmp_path):
    """
    PR change: the no-overwrite check was updated from checking only the new
    .skops path to also checking for the legacy .cloudpickle file.
    When force=False and the legacy artifact exists, the function must
    return (legacy_path, False) without writing a new file.
    """
    import lexnlp.ml.catalog as catalog_mod
    from lexnlp.extract.en.contracts import runtime_model

    monkeypatch.setattr(catalog_mod, "CATALOG", tmp_path)

    # Pre-create a legacy .cloudpickle artifact (not the new .skops filename).
    target_dir = tmp_path / "pipeline" / "test" / "0.1"
    target_dir.mkdir(parents=True)
    legacy_file = target_dir / runtime_model.LEGACY_CONTRACT_TYPE_MODEL_FILENAME
    legacy_file.write_bytes(b"legacy content")

    dummy_pipeline = {"weights": [1, 2, 3]}

    destination, wrote = runtime_model.write_pipeline_to_catalog(
        pipeline=dummy_pipeline,
        target_tag="pipeline/test/0.1",
        force=False,
    )

    assert wrote is False
    assert destination == legacy_file
    # The legacy file must be untouched.
    assert destination.read_bytes() == b"legacy content"
    # The new .skops file must NOT have been created.
    skops_file = target_dir / runtime_model.CONTRACT_TYPE_MODEL_FILENAME
    assert not skops_file.exists()


def test_write_pipeline_to_catalog_force_true_overwrites_even_with_legacy(monkeypatch, tmp_path):
    """
    When force=True, even a legacy artifact must be overwritten with a new
    .skops file and (path, True) returned.
    """
    import lexnlp.ml.catalog as catalog_mod
    from lexnlp.extract.en.contracts import runtime_model
    from lexnlp.ml.model_io import load_model

    monkeypatch.setattr(catalog_mod, "CATALOG", tmp_path)

    target_dir = tmp_path / "pipeline" / "test" / "force"
    target_dir.mkdir(parents=True)
    # Pre-create a legacy .cloudpickle to simulate an old catalog entry.
    legacy_file = target_dir / runtime_model.LEGACY_CONTRACT_TYPE_MODEL_FILENAME
    legacy_file.write_bytes(b"old legacy content")

    new_pipeline = {"version": "new"}

    destination, wrote = runtime_model.write_pipeline_to_catalog(
        pipeline=new_pipeline,
        target_tag="pipeline/test/force",
        force=True,
    )

    assert wrote is True
    # The new artifact must use the .skops name.
    assert destination.name == runtime_model.CONTRACT_TYPE_MODEL_FILENAME
    loaded = load_model(destination, trusted=True)
    assert loaded == new_pipeline


def test_write_pipeline_to_catalog_contract_type_model_filename_is_skops():
    """
    Regression: CONTRACT_TYPE_MODEL_FILENAME must use .skops extension now.
    """
    from lexnlp.extract.en.contracts.runtime_model import CONTRACT_TYPE_MODEL_FILENAME

    assert CONTRACT_TYPE_MODEL_FILENAME.endswith(".skops")


def test_write_pipeline_to_catalog_legacy_filename_is_cloudpickle():
    """
    LEGACY_CONTRACT_TYPE_MODEL_FILENAME must reference the old .cloudpickle file.
    """
    from lexnlp.extract.en.contracts.runtime_model import LEGACY_CONTRACT_TYPE_MODEL_FILENAME

    assert LEGACY_CONTRACT_TYPE_MODEL_FILENAME.endswith(".cloudpickle")


def test_ensure_runtime_contract_type_model_no_force_returns_cached(monkeypatch, tmp_path):
    """
    When force=False and the catalog already has the target tag, the existing
    path is returned immediately without retraining.
    """
    from lexnlp.extract.en.contracts import runtime_model

    existing_path = tmp_path / "model.cloudpickle"
    existing_path.write_bytes(b"cached")

    import lexnlp.ml.catalog as catalog_mod

    def fake_get_path(tag: str) -> object:
        if tag == runtime_model.RUNTIME_CONTRACT_TYPE_TAG:
            return existing_path
        raise FileNotFoundError(tag)

    monkeypatch.setattr(catalog_mod, "get_path_from_catalog", fake_get_path)

    result = runtime_model.ensure_runtime_contract_type_model(
        target_tag=runtime_model.RUNTIME_CONTRACT_TYPE_TAG,
        force=False,
    )

    assert result == existing_path
