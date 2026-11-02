import importlib.util
import io
import json
from pathlib import Path

import pytest


def load_fetcher():
    script = Path(__file__).resolve().parents[1] / "scripts/fetch_data.py"
    spec = importlib.util.spec_from_file_location("fetch_data_for_check", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_git_blob_hash_matches_canonical_hello_object(tmp_path):
    module = load_fetcher()
    path = tmp_path / "hello.txt"
    path.write_bytes(b"hello\n")
    assert module.digest(path, "git-blob-sha1") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_download_ledger_omits_redirect_queries_and_credentials(tmp_path, monkeypatch):
    module = load_fetcher()
    monkeypatch.setattr(module, "ROOT", tmp_path)

    class Response(io.BytesIO):
        def geturl(self):
            return "https://synthetic-user:synthetic-pass@example.org/object?X-Amz-Signature=synthetic-only#fragment"

    monkeypatch.setattr(module.urllib.request, "urlopen", lambda *args, **kwargs: Response(b"synthetic"))
    record = module.fetch_asset(
        {"id": "synthetic"}, {"filename": "data.bin", "url": "https://example.org/public?download=1"}
    )
    assert record["status"] == "downloaded"
    assert record["url"] == "https://example.org/public"
    assert record["resolved_url"] == "https://example.org/object"
    assert record["url_query_or_credentials_removed"]
    assert record["resolved_url_query_or_credentials_removed"]
    assert record["bytes"] == 9 and len(record["sha256"]) == 64


def test_cached_checksum_mismatch_is_not_a_success(tmp_path, monkeypatch):
    module = load_fetcher()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    folder = tmp_path / "data/raw/synthetic"
    folder.mkdir(parents=True)
    (folder / "data.bin").write_bytes(b"altered")
    record = module.fetch_asset(
        {"id": "synthetic"},
        {"filename": "data.bin", "url": "https://example.org/data", "checksum": "sha256:" + "0" * 64},
    )
    assert record["status"] == "failed"
    assert "checksum mismatch" in record["error"]


def test_partial_download_resumes_only_when_server_honors_range(tmp_path, monkeypatch):
    module = load_fetcher()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    folder = tmp_path / "data/raw/synthetic"
    folder.mkdir(parents=True)
    (folder / "data.bin.part").write_bytes(b"first-")
    seen = {}

    class Response(io.BytesIO):
        status = 206

        def geturl(self):
            return "https://example.org/data"

    def urlopen(request, **kwargs):
        seen["range"] = request.get_header("Range")
        return Response(b"second")

    monkeypatch.setattr(module.urllib.request, "urlopen", urlopen)
    record = module.fetch_asset(
        {"id": "synthetic"},
        {
            "filename": "data.bin",
            "url": "https://example.org/data",
            "checksum": "sha256:" + module.hashlib.sha256(b"first-second").hexdigest(),
        },
    )
    assert seen["range"] == "bytes=6-"
    assert record["status"] == "downloaded" and record["resumed_from_bytes"] == 6
    assert (folder / "data.bin").read_bytes() == b"first-second"


def test_optional_assets_need_explicit_ids_and_preserve_acquisition_policy(tmp_path, monkeypatch):
    module = load_fetcher()
    monkeypatch.setattr(module, "ROOT", tmp_path)
    path = tmp_path / "catalog.json"
    path.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "id": "open",
                        "acquisition_policy": "allowed",
                        "assets": [
                            {"filename": "small", "default": True},
                            {"filename": "large", "default": False},
                        ],
                    },
                    {
                        "id": "held",
                        "acquisition_policy": "metadata_only",
                        "assets": [{"filename": "held", "default": False}],
                    },
                    {
                        "id": "selected",
                        "acquisition_policy": "allowed_selected_assets",
                        "assets": [{"filename": "reviewed", "default": False}],
                    },
                    {
                        "id": "selected-text",
                        "acquisition_policy": "allowed_selected_text_assets",
                        "assets": [{"filename": "reviewed.txt", "default": False}],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "CATALOG", path)
    (tmp_path / "data").mkdir()
    monkeypatch.setattr(
        module,
        "fetch_asset",
        lambda d, a: dict(dataset_id=d["id"], filename=a["filename"], status="synthetic_no_download"),
    )
    assert [r["filename"] for r in module.acquire(["open", "held"])] == ["small"]
    assert [r["filename"] for r in module.acquire(["open", "held"], include_optional=True)] == [
        "small",
        "large",
    ]
    assert module.acquire(["selected", "selected-text"], include_optional=True) == [
        {
            "dataset_id": "selected",
            "filename": "reviewed",
            "status": "synthetic_no_download",
        },
        {
            "dataset_id": "selected-text",
            "filename": "reviewed.txt",
            "status": "synthetic_no_download",
        },
    ]
    with pytest.raises(ValueError, match="explicit dataset IDs"):
        module.acquire([], include_optional=True)
