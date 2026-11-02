"""Run every audited physical model through its public JSON registry API."""

import importlib
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = None


def initialize():
    global REGISTRY
    from matintegrity.registry import default_registry

    REGISTRY = default_registry()


def execute(task):
    from matintegrity.contracts import RunContext

    model, candidates, contexts = task
    attempts = []
    for source, payload in candidates:
        started = time.monotonic()
        try:
            values = contexts.get(model, {}) if source == "example" else {}
            scope = payload.get("stress_history", payload)
            if not isinstance(scope, dict):
                scope = payload
            context = RunContext(
                asset_id=values.get("asset_id", payload.get("asset_id", scope.get("asset_id", "synthetic"))),
                location_id=values.get(
                    "location_id", payload.get("location_id", scope.get("location_id", "synthetic"))
                ),
                time_basis=values.get(
                    "time_basis",
                    payload.get(
                        "time_basis",
                        payload.get("clock_id", scope.get("time_basis_id", "API contract check")),
                    ),
                ),
            )
            dependencies = {
                name: importlib.import_module(name)
                for name in REGISTRY._models[model].runtime_dependency_names
            }
            if "scipy" in dependencies:
                importlib.import_module("scipy.integrate")
                importlib.import_module("scipy.optimize")
            result = REGISTRY.run_json(
                model, json.dumps(payload, allow_nan=False), context, runtime_dependencies=dependencies
            )
            serialized = result.model_dump(mode="json")
            json.dumps(serialized, allow_nan=False)
            attempts.append(
                {
                    "source": source,
                    "status": result.status,
                    "seconds": time.monotonic() - started,
                    "result": serialized,
                }
            )
            if result.status == "computed":
                break
        except Exception as error:
            attempts.append(
                {
                    "source": source,
                    "status": "error",
                    "seconds": time.monotonic() - started,
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            )
    return {
        "model_id": model,
        "status": attempts[-1]["status"] if attempts else "missing_input",
        "attempts": attempts,
    }


def main():
    manifest = json.loads((ROOT / "tests/data/core_physics_full_run_targets.json").read_text(encoding="utf8"))
    examples = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))
    baselines = json.loads(
        (ROOT / "tests/data/core_physics_valid_input_baselines.json").read_text(encoding="utf8")
    )["model_inputs"]
    models = sorted({m for g in manifest["groups"] for m in g["model_ids"]})
    output = ROOT / "artifacts/validation/full_core_calculations"
    output.mkdir(parents=True, exist_ok=True)
    local_path = output / "execution_inputs.local.json"
    local = json.loads(local_path.read_text(encoding="utf8"))["model_inputs"] if local_path.exists() else {}
    records = []
    if "--pending" in sys.argv and (output / "summary.json").exists():
        records = [
            r
            for r in json.loads((output / "summary.json").read_text(encoding="utf8"))["records"]
            if r["status"] == "computed"
        ]
    completed = {r["model_id"] for r in records}
    tasks = [
        (
            m,
            [
                (source, data[m])
                for source, data in [
                    ("execution_fixture", local),
                    ("baseline", baselines),
                    ("example", examples["models"]),
                ]
                if m in data
            ],
            examples.get("run_contexts", {}),
        )
        for m in models
        if m not in completed
    ]
    with ProcessPoolExecutor(max_workers=4, initializer=initialize) as pool:
        futures = [pool.submit(execute, t) for t in tasks]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            (output / (record["model_id"] + ".json")).write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
            )
            print(f"{len(records)}/{len(models)} {record['status']} {record['model_id']}", flush=True)
    summary = {
        "target_models": len(models),
        "computed": sum(r["status"] == "computed" for r in records),
        "records": sorted(records, key=lambda r: r["model_id"]),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    print("computed", summary["computed"], "/", len(models))
    return 0 if summary["computed"] == len(models) else 1


if __name__ == "__main__":
    raise SystemExit(main())
