"""Validate partition-aware pressure comparison with independently authored synthetic values."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.burst_validation import BurstPressureComparison, BurstPressureComparisonRow
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = tuple(
        BurstPressureComparisonRow(
            observation_id=f"synthetic-{index}",
            physical_specimen_id=f"synthetic-specimen-{index}",
            source_group_id="synthetic-calibration" if index == 0 else "synthetic-holdout",
            partition="calibration" if index == 0 else "holdout",
            material_condition_id="synthetic-steel",
            geometry_id=f"synthetic-geometry-{index}",
            load_case_id="synthetic-monotonic-pressure",
            observed_pressure_basis="internal_minus_external",
            predicted_pressure_basis="internal_minus_external",
            observed_burst_pressure_Pa=10e6,
            predicted_failure_pressure_Pa=10e6 * ratio,
            observation_source_sha256=hashlib.sha256(f"observation-{index}".encode()).hexdigest(),
            prediction_input_digest=hashlib.sha256(f"prediction-{index}".encode()).hexdigest(),
            observation_use_authorized=True,
            experimental_endpoint_reviewed=True,
            geometry_and_material_reviewed=True,
            pressure_basis_reviewed=True,
        )
        for index, ratio in enumerate((1.0, 0.8, 1.25))
    )
    request = BurstPressureComparison(
        comparison_id="synthetic-partition-check",
        prediction_provider_id="synthetic.pressure-provider",
        prediction_provider_version="1.0.0",
        prediction_configuration_digest=hashlib.sha256(b"synthetic configuration").hexdigest(),
        rows=rows,
        physical_specimen_independence_reviewed=True,
        source_group_partitioning_reviewed=True,
        prediction_frozen_before_evaluation=True,
    )
    result = default_registry().run(
        "structural.burst_pressure_comparison",
        request,
        RunContext(
            asset_id="synthetic-pipe-tests",
            location_id="synthetic-defects",
            time_basis="monotonic burst endpoint",
        ),
    )
    holdout = result.values["partition_summaries"]["holdout"]
    expected_rmse = math.sqrt((math.log(0.8) ** 2 + math.log(1.25) ** 2) / 2)
    if holdout["arithmetic_mean_predicted_to_observed_ratio"] != 1.025:
        raise AssertionError("synthetic ratio mean changed")
    if not math.isclose(holdout["root_mean_square_log_error"], expected_rmse, rel_tol=1e-14):
        raise AssertionError("synthetic log-error identity changed")
    validation = {
        "schema_version": "matintegrity.burst_prediction_comparison_math.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": result.model_id,
        "model_version": result.model_version,
        "input_digest": result.input_digest,
        "result_digest": canonical_digest(result.model_dump(mode="json")),
        "observations": result.values["observation_count"],
        "partition_counts": {
            key: value["observations"] for key, value in result.values["partition_summaries"].items()
        },
        "expected_holdout_arithmetic_mean_ratio": 1.025,
        "expected_holdout_root_mean_square_log_error": expected_rmse,
        "model_source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/burst_validation.py").read_bytes()
        ).hexdigest(),
        "validation_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "qualification": (
            "Synthetic arithmetic and partition-contract verification only. It is not a pressure-model "
            "calibration, experimental qualification, standard acceptance, remaining-life estimate or "
            "failure probability."
        ),
    }
    target = ROOT / "validation/burst_prediction_comparison_math.json"
    target.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
