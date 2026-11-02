from scripts.fetch_data import fetch_asset, selected_assets


def test_selected_asset_policies_require_explicit_id_and_optional_flag():
    dataset = {
        "acquisition_policy": "allowed_selected_assets",
        "assets": [{"filename": "reviewed.csv", "default": False}],
    }
    assert selected_assets(dataset, explicit_ids=False, include_optional=True) == []
    assert selected_assets(dataset, explicit_ids=True, include_optional=False) == []
    assert selected_assets(dataset, explicit_ids=True, include_optional=True) == dataset["assets"]


def test_metadata_only_and_prohibited_policies_never_select_assets():
    for policy in ("metadata_only", "do_not_download"):
        dataset = {"acquisition_policy": policy, "assets": [{"filename": "data.csv"}]}
        assert selected_assets(dataset, explicit_ids=True, include_optional=True) == []


def test_cached_asset_must_match_declared_size_even_without_publisher_checksum(tmp_path, monkeypatch):
    import scripts.fetch_data as fetcher

    monkeypatch.setattr(fetcher, "ROOT", tmp_path)
    target = tmp_path / "data/raw/synthetic/data.bin"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"wrong-size")
    result = fetch_asset(
        {"id": "synthetic"},
        {"filename": "data.bin", "url": "https://example.org/data", "bytes": 3, "max_bytes": 20},
    )
    assert result["status"] == "failed"
    assert "byte count differs from catalog" in result["error"]
