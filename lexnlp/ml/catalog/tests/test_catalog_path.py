import importlib
import threading


def test_catalog_path_resolves_on_fresh_environment(tmp_path):
    import nltk.data

    import lexnlp.ml.catalog as catalog

    original_paths = list(nltk.data.path)
    try:
        candidate_root = tmp_path / "nltk_data"
        nltk.data.path = [str(candidate_root)]
        importlib.reload(catalog)

        assert candidate_root / "lexpredict-lexnlp" == catalog.CATALOG
        assert not catalog.CATALOG.exists()
    finally:
        nltk.data.path = original_paths
        importlib.reload(catalog)


def test_catalog_path_falls_back_to_home_when_nltk_path_empty(tmp_path, monkeypatch):
    import nltk.data

    import lexnlp.ml.catalog as catalog

    original_paths = list(nltk.data.path)
    try:
        fake_home = tmp_path / "home"
        monkeypatch.setenv("HOME", str(fake_home))
        nltk.data.path = []
        importlib.reload(catalog)

        assert str(catalog.CATALOG).startswith(str(fake_home))
        assert catalog.CATALOG.name == "lexpredict-lexnlp"
        assert not catalog.CATALOG.exists()
    finally:
        nltk.data.path = original_paths
        importlib.reload(catalog)


# ---------------------------------------------------------------------------
# Thread-safe double-checked locking for _get_tag_dict_cached
# ---------------------------------------------------------------------------


def test_get_tag_dict_cached_builds_cache_once(tmp_path):
    """
    _get_tag_dict_cached must populate _TAG_DICT_CACHE exactly once, even when
    called multiple times sequentially.
    """
    import lexnlp.ml.catalog as catalog

    catalog.invalidate_catalog_cache()

    # Create a single file under CATALOG so _build_tag_dict returns something.
    fake_tag_dir = tmp_path / "pipeline" / "test" / "0.1"
    fake_tag_dir.mkdir(parents=True)
    fake_file = fake_tag_dir / "model.pkl"
    fake_file.write_bytes(b"model")

    original_catalog = catalog.CATALOG
    catalog.CATALOG = tmp_path
    try:
        result1 = catalog._get_tag_dict_cached()
        result2 = catalog._get_tag_dict_cached()
        assert result1 is result2  # Same dict object – no rebuild.
    finally:
        catalog.CATALOG = original_catalog
        catalog.invalidate_catalog_cache()


def test_get_tag_dict_cached_thread_safety(tmp_path, monkeypatch):
    """
    Concurrent calls to _get_tag_dict_cached must not build the cache more
    than once (double-checked locking correctness).
    """
    import lexnlp.ml.catalog as catalog

    build_count = []
    original_build = catalog._build_tag_dict

    def counting_build():
        build_count.append(1)
        return original_build()

    catalog.invalidate_catalog_cache()
    monkeypatch.setattr(catalog, "_build_tag_dict", counting_build)
    monkeypatch.setattr(catalog, "CATALOG", tmp_path)

    errors: list[Exception] = []
    results: list[object] = []

    def call_cached():
        try:
            results.append(catalog._get_tag_dict_cached())
        except Exception as exc:
            errors.append(exc)

    threads = [threading.Thread(target=call_cached) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    catalog.invalidate_catalog_cache()

    assert not errors, f"Thread errors: {errors}"
    assert len(results) == 10
    # All threads must receive the same dict object.
    first = results[0]
    assert all(r is first for r in results)
    # _build_tag_dict must have been called exactly once.
    assert len(build_count) == 1


def test_invalidate_catalog_cache_is_thread_safe(tmp_path, monkeypatch):
    """
    Concurrent calls to invalidate_catalog_cache must not race with
    _get_tag_dict_cached: after all threads finish, the cache is either
    None (invalidated) or a fresh dict (rebuilt), never a stale/corrupt value.
    """
    from concurrent.futures import ThreadPoolExecutor

    import lexnlp.ml.catalog as catalog

    monkeypatch.setattr(catalog, "CATALOG", tmp_path)
    catalog.invalidate_catalog_cache()

    def do_invalidate() -> None:
        catalog.invalidate_catalog_cache()

    def do_read() -> None:
        """
        Access the catalog tag-dictionary cache to trigger its build or retrieval.

        Used as a concurrent reader in tests to exercise thread-safe cache access.
        """
        catalog._get_tag_dict_cached()

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(do_invalidate) for _ in range(5)] + [pool.submit(do_read) for _ in range(5)]
        for future in futures:
            future.result()

    # After all operations the cache is in a defined state: None or a dict.
    assert catalog._TAG_DICT_CACHE is None or isinstance(catalog._TAG_DICT_CACHE, dict)
    catalog.invalidate_catalog_cache()


def test_invalidate_catalog_cache_clears_cache(tmp_path):
    """
    invalidate_catalog_cache must reset _TAG_DICT_CACHE so the next call to
    _get_tag_dict_cached rebuilds it.
    """
    import lexnlp.ml.catalog as catalog

    original_catalog = catalog.CATALOG
    catalog.CATALOG = tmp_path
    try:
        # Warm up the cache.
        first = catalog._get_tag_dict_cached()
        assert catalog._TAG_DICT_CACHE is not None

        catalog.invalidate_catalog_cache()
        assert catalog._TAG_DICT_CACHE is None

        # Rebuilding after invalidation yields a fresh dict.
        second = catalog._get_tag_dict_cached()
        assert second is not first
    finally:
        catalog.CATALOG = original_catalog
        catalog.invalidate_catalog_cache()
