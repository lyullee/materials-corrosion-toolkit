"""Verify discrete threshold scheduling against an independently authored candidate scan."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    points = [
        ("y1", 31_557_600.0, 0.01, 0.02),
        ("y2", 63_115_200.0, 0.03, 0.05),
        ("y3", 94_672_800.0, 0.07, 0.09),
        ("y4", 126_230_400.0, 0.12, 0.14),
    ]
    payload = {
        "schedule_id": "authored-threshold-schedule",
        "asset_id": "authored",
        "location_id": "cml-1",
        "physical_scope_id": "authored-circuit/cml-1",
        "event_id": "authored-first-crossing",
        "event_definition": "first crossing of an authored threshold",
        "assessment_time_s": 0.0,
        "conditioning": "authored asset remains above the threshold at assessment",
        "event_probability_meaning": "conditional_first_failure_in_period",
        "forecast_model_id": "authored.monotone-forecast",
        "forecast_model_revision": "1",
        "forecast_input_sha256": hashlib.sha256(b"authored monotone forecast").hexdigest(),
        "forecast_points": [
            {
                "forecast_point_id": point_id,
                "horizon_end_s": time_s,
                "cumulative_probability_given_survival": estimate,
                "cumulative_probability_upper_bound": upper,
            }
            for point_id, time_s, estimate, upper in points
        ],
        "probability_basis": "estimate",
        "maximum_probability_before_inspection": 0.08,
        "minimum_notice_s": 0.0,
        "maximum_deferral_s": points[-1][1],
        "forecast_identity_reviewed": True,
        "event_scope_and_conditioning_reviewed": True,
        "cumulative_probability_curve_reviewed": True,
        "scheduling_criterion_user_approved": True,
        "evidence": [
            {
                "source_id": "authored-scheduling-validation",
                "origin": "synthetic",
                "citation": "independently authored monotone candidate table",
            }
        ],
    }
    context = RunContext(asset_id="authored", location_id="cml-1", time_basis="elapsed seconds")
    registry = default_registry()
    estimate_result = registry.run("inspection.threshold_inspection_schedule", payload, context)
    upper_payload = {**payload, "probability_basis": "upper_bound"}
    upper_result = registry.run("inspection.threshold_inspection_schedule", upper_payload, context)
    expected_estimate_id = max(
        (row for row in points if row[2] <= payload["maximum_probability_before_inspection"]),
        key=lambda row: row[1],
    )[0]
    expected_upper_id = max(
        (row for row in points if row[3] <= payload["maximum_probability_before_inspection"]),
        key=lambda row: row[1],
    )[0]
    actual_estimate_id = estimate_result.values["selected_forecast_point_id"]
    actual_upper_id = upper_result.values["selected_forecast_point_id"]
    if actual_estimate_id != expected_estimate_id or actual_upper_id != expected_upper_id:
        raise AssertionError("threshold schedule does not match the independent candidate scan")
    record = {
        "schema_version": "matintegrity.validation.inspection_scheduling.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Authored monotone-table and discrete-selection verification only; not calibration of a "
            "damage forecast, probability threshold, inspection effectiveness, consequence or field interval."
        ),
        "model_id": estimate_result.model_id,
        "estimate_basis": {
            "expected_selected_forecast_point_id": expected_estimate_id,
            "actual_selected_forecast_point_id": actual_estimate_id,
            "input_digest": estimate_result.input_digest,
        },
        "upper_bound_basis": {
            "expected_selected_forecast_point_id": expected_upper_id,
            "actual_selected_forecast_point_id": actual_upper_id,
            "input_digest": upper_result.input_digest,
        },
        "continuous_time_interpolation_performed": estimate_result.values[
            "continuous_time_interpolation_performed"
        ],
        "consequence_optimization_performed": estimate_result.values["consequence_optimization_performed"],
        "probability_semantics": estimate_result.probability_semantics,
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/inspection.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/inspection_scheduling_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
