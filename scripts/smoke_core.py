"""Execute with an independently installed wheel and no optional dependencies."""

import importlib.util
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

from matintegrity import evaluate
from matintegrity.catalogs import load_catalog
from matintegrity.contracts import AssessmentResult, RunContext
from matintegrity.registry import default_registry
from matintegrity.sensitivity import SobolInputBatch


def main():
    optional = {
        name: importlib.util.find_spec(name) is not None
        for name in ("scipy", "CoolProp", "rainflow", "pandas")
    }
    if any(optional.values()):
        raise RuntimeError("Use a clean environment without optional dependencies for this core-only check")
    registry = default_registry()
    catalog_models = {
        row["id"] for row in load_catalog("capabilities")["capabilities"] if row["status"] == "implemented"
    }
    assert set(registry.list_models()) == catalog_models
    result = evaluate(
        "corrosion.coupon_loss",
        dict(mass_loss_kg=0.001, exposed_area_m2=0.01, density_kg_m3=1000.0, duration_s=100.0),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="synthetic seconds"),
    )
    assert abs(result.values["mean_penetration_m"] - 0.0001) < 1e-15
    assert result.inputs["mass_loss_kg"] == 0.001
    assert AssessmentResult.model_validate_json(result.model_dump_json()).input_digest == result.input_digest
    batch = SobolInputBatch(
        design_digest="0" * 64,
        request_digest="0" * 64,
        evaluator_id="worker-contract",
        evaluator_revision="1",
        replicate_index=0,
        block_id="A",
        point_indices=[0],
        parameters={"mass": [1.0]},
        parameter_units={"mass": "mg"},
    )
    assert SobolInputBatch.model_validate_json(batch.model_dump_json()).parameter_units == {"mass": "mg"}
    evidence = dict(
        schema_version="matintegrity.clean_install.v1",
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),
        runtime=result.runtime,
        models=len(registry.list_models()),
        catalog_datasets=len(load_catalog("datasets")["datasets"]),
        optional_dependencies_present=optional,
        checks=[
            "installed core imports without optional dependencies",
            "registry matches packaged catalog",
            "coupon independent expected penetration",
            "input snapshot and JSON round trip",
            "sensitivity native-unit worker contract imports and round-trips without SciPy",
        ],
        status="passed",
    )
    target = Path(__file__).resolve().parents[1] / "validation/clean_install.json"
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
