"""Register explicitly licensed Zenodo assets after reviewing the scientific scope."""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def register(record_id: str, identifier: str, category: str, limitations: list[str]):
    if not record_id.isdigit() or not identifier or not all(c.isalnum() or c == "-" for c in identifier):
        raise ValueError("numeric record ID and simple dataset identifier required")
    try:
        import truststore

        truststore.inject_into_ssl()
    except ImportError:
        pass
    url = f"https://zenodo.org/api/records/{record_id}"
    request = urllib.request.Request(url, headers={"User-Agent": "MatIntegrity-data/0.1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        metadata = json.load(response)
    license_id = metadata["metadata"].get("license", {}).get("id", "").lower()
    allowed = {
        "cc-by-4.0": ("CC-BY-4.0", "https://creativecommons.org/licenses/by/4.0/"),
        "cc0-1.0": ("CC0-1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
        "cc-zero": ("CC0-1.0", "https://creativecommons.org/publicdomain/zero/1.0/"),
    }
    if license_id not in allowed:
        raise ValueError("license is outside the reviewed acquisition allowlist")
    evidence = ROOT / "data/evidence" / identifier
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "zenodo_record.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    catalog_path = ROOT / "data/catalogs/datasets.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if any(row["id"] == identifier for row in catalog["datasets"]):
        raise ValueError("dataset ID already exists; reconcile revisions explicitly")
    creators = "; ".join(person["name"] for person in metadata["metadata"]["creators"])
    license_name, license_url = allowed[license_id]
    assets = [
        dict(
            filename=f["key"],
            url=f["links"]["self"],
            checksum=f["checksum"],
            bytes=f["size"],
            max_bytes=f["size"],
            default=f["size"] < 128 * 1024 * 1024
            and Path(f["key"]).suffix.lower()
            in {".csv", ".txt", ".md", ".json", ".xlsx", ".xlsm", ".h5", ".lis", ".zip", ".m", ".mat"},
        )
        for f in metadata.get("files", [])
    ]
    catalog["datasets"].append(
        dict(
            id=identifier,
            title=metadata["metadata"]["title"],
            category=category,
            citation=f"{creators}; https://doi.org/10.5281/zenodo.{record_id}",
            license=license_name,
            license_url=license_url,
            rights_evidence_url=f"https://zenodo.org/records/{record_id}",
            rights_status="reviewed_license",
            acquisition_policy="allowed",
            checked_on=date.today().isoformat(),
            limitations=limitations,
            assets=assets,
        )
    )
    catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    print(dict(id=identifier, assets=len(assets), license=license_name))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("record_id")
    parser.add_argument("identifier")
    parser.add_argument("--category", required=True)
    parser.add_argument("--limitation", action="append", required=True)
    args = parser.parse_args()
    register(args.record_id, args.identifier, args.category, args.limitation)
