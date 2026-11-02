"""Fetch explicitly catalogued research assets and record content fingerprints."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/catalogs/datasets.json"


def public_record_url(value: str) -> str:
    """Record stable URL components without redirect credentials, query tokens or fragments."""
    parts = urlsplit(value)
    return urlunsplit((parts.scheme, parts.netloc.rsplit("@", 1)[-1], parts.path, "", ""))


def digest(path: Path, algorithm: str = "sha256") -> str:
    h = hashlib.new("sha1" if algorithm == "git-blob-sha1" else algorithm)
    if algorithm == "git-blob-sha1":
        h.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def selected_assets(dataset: dict, *, explicit_ids: bool, include_optional: bool) -> list[dict]:
    """Select assets only under the catalog's acquisition policy and explicit caller intent."""
    policy = dataset.get("acquisition_policy")
    if policy == "allowed":
        permitted = True
    elif policy in {"allowed_selected_assets", "allowed_selected_text_assets"}:
        permitted = explicit_ids and include_optional
    else:
        permitted = False
    if not permitted:
        return []
    return [asset for asset in dataset.get("assets", []) if include_optional or asset.get("default", True)]


def fetch_asset(dataset: dict, asset: dict) -> dict:
    folder = ROOT / "data/raw" / dataset["id"]
    folder.mkdir(parents=True, exist_ok=True)
    name = asset["filename"]
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError("catalog asset filename must be a basename")
    target = folder / name
    record = {
        "dataset_id": dataset["id"],
        "filename": name,
        "url": public_record_url(asset["url"]),
        "url_query_or_credentials_removed": public_record_url(asset["url"]) != asset["url"],
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        if not target.exists():
            temporary = target.with_suffix(target.suffix + ".part")
            existing_size = temporary.stat().st_size if temporary.exists() else 0
            headers = {"User-Agent": "MatIntegrity-data/0.1"}
            if existing_size:
                headers["Range"] = f"bytes={existing_size}-"
            request = urllib.request.Request(asset["url"], headers=headers)
            with (
                urllib.request.urlopen(request, timeout=asset.get("read_timeout_s", 60)) as response,
            ):
                range_honored = existing_size > 0 and getattr(response, "status", 200) == 206
                mode = "ab" if range_honored else "wb"
                size = existing_size if range_honored else 0
                with temporary.open(mode) as stream:
                    while chunk := response.read(1024 * 1024):
                        size += len(chunk)
                        if size > asset.get("max_bytes", 512 * 1024 * 1024):
                            raise ValueError("asset exceeds declared download size budget")
                        stream.write(chunk)
                resolved_url = response.geturl()
                record["resolved_url"] = public_record_url(resolved_url)
                record["resolved_url_query_or_credentials_removed"] = record["resolved_url"] != resolved_url
                record["resumed_from_bytes"] = existing_size if range_honored else 0
            temporary.replace(target)
        actual_bytes = target.stat().st_size
        if actual_bytes > asset.get("max_bytes", 512 * 1024 * 1024):
            raise ValueError("asset exceeds declared download size budget")
        expected_bytes = asset.get("bytes")
        if expected_bytes is not None and actual_bytes != expected_bytes:
            raise ValueError("asset byte count differs from catalog")
        checksum = asset.get("checksum")
        if checksum:
            algorithm, expected = checksum.split(":", 1)
            if digest(target, algorithm) != expected:
                raise ValueError("publisher checksum mismatch; cached file is not qualified")
        record.update(
            status="downloaded",
            bytes=actual_bytes,
            sha256=digest(target),
            publisher_checksum=checksum,
            path=target.relative_to(ROOT).as_posix(),
        )
    except Exception as exc:
        record.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    return record


def acquire(
    ids: list[str], workers: int = 3, research_cache: Path | None = None, *, include_optional: bool = False
) -> list[dict]:
    if include_optional and not ids:
        raise ValueError("optional acquisition requires explicit dataset IDs")
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass  # Use Python's verified default TLS context when the optional system store is absent.
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    chosen = [d for d in catalog["datasets"] if not ids or d["id"] in ids]
    if ids and {d["id"] for d in chosen} != set(ids):
        raise ValueError("unknown dataset identifier")
    jobs = []
    for dataset in chosen:
        assets = selected_assets(dataset, explicit_ids=bool(ids), include_optional=include_optional)
        for asset in assets:
            if research_cache and asset.get("research_cache_name"):
                source = research_cache / asset["research_cache_name"]
                target = ROOT / "data/raw" / dataset["id"] / asset["filename"]
                if source.is_file() and not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            jobs.append((dataset, asset))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda pair: fetch_asset(*pair), jobs))
    ledger = ROOT / "data/acquisition_log.json"
    previous = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else {"attempts": []}
    previous["attempts"].extend(results)
    ledger.write_text(json.dumps(previous, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*", default=[])
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--research-cache", type=Path)
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Explicitly include nondefault assets of the selected datasets, subject to each asset size budget.",
    )
    args = parser.parse_args()
    for result in acquire(
        args.ids, args.workers, args.research_cache, include_optional=args.include_optional
    ):
        print(json.dumps(result, ensure_ascii=False), flush=True)
