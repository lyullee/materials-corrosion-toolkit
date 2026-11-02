"""Verify generated schema files against every currently registered API input."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def audit_schema_coverage(target, registry):
    index = json.loads((target / "schema_index.json").read_text(encoding="utf-8"))
    if index.get("schema_version") != "matintegrity.public_schema_index.v1":
        raise ValueError("unsupported schema index version")
    records = index["contracts"]
    by_id = {row["contract_id"]: row for row in records}
    if len(by_id) != len(records) or len({row["filename"] for row in records}) != len(records):
        raise ValueError("schema index contract identities and filenames must be unique")
    if index["contract_count"] != len(records):
        raise ValueError("schema index contract count mismatch")
    models = registry.list_models()
    if set(index["models"]) != set(models) or index["registered_model_count"] != len(models):
        raise ValueError("schema index does not exactly cover the registered model set")
    for row in records:
        name = row["filename"]
        if Path(name).name != name or not name.endswith(".json"):
            raise ValueError("schema filename must be a direct JSON child of the schema directory")
        payload = (target / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError(f"generated schema digest mismatch:{name}")
    verified = set()
    for model in models:
        contract = registry.input_type(model)
        identifier = f"{contract.__module__}.{contract.__qualname__}"
        row = index["models"][model]
        if row["contract_id"] != identifier or by_id.get(identifier) != row:
            raise ValueError(f"model-to-contract mapping mismatch:{model}")
        if identifier in verified:
            continue
        stored = json.loads((target / row["filename"]).read_text(encoding="utf-8"))
        if stored != contract.model_json_schema():
            raise ValueError(f"generated schema differs from executable input contract:{model}")
        verified.add(identifier)
    return dict(
        registered_models=len(models),
        covered_models=len(models),
        unique_registered_input_contracts=len(verified),
        exported_contracts=len(records),
        missing_models=[],
        mismatched_schemas=[],
        scope="Schema coverage only; not API execution, numerical or physical validation.",
    )


def main():
    report = audit_schema_coverage(ROOT / "docs/schemas", default_registry())
    output = ROOT / "artifacts/validation/registry_schema_coverage.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
