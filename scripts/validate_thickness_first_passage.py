"""Verify sampled linear first passage and its schedule composition with exact rows."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    payload = {
        "forecast_id": "authored-linear-first-passage",
        "asset_id": "authored",
        "location_id": "cml-1",
        "physical_scope_id": "authored-circuit/cml-1",
        "physical_location_id": "cml-1",
        "time_basis": "authored elapsed seconds",
        "assessment_time_s": 0.0,
        "conditioning": "authored threshold has not been crossed at assessment",
        "event_id": "authored-minimum-thickness-first-crossing",
        "event_definition": "first crossing of 0.006 m remaining thickness",
        "required_thickness_m": 0.006,
        "distribution_definition_id": "authored-three-row-joint-distribution",
        "sample_design_id": "authored-exact-discrete-design",
        "joint_sample_source_sha256": hashlib.sha256(b"authored joint rows").hexdigest(),
        "samples": [
            {
                "sample_id": "cross-40m",
                "remaining_thickness_at_assessment_m": 0.010,
                "nonnegative_loss_rate_m_s": 1e-10,
                "normalized_weight": 0.2,
            },
            {
                "sample_id": "cross-30m",
                "remaining_thickness_at_assessment_m": 0.012,
                "nonnegative_loss_rate_m_s": 2e-10,
                "normalized_weight": 0.5,
            },
            {
                "sample_id": "never-cross",
                "remaining_thickness_at_assessment_m": 0.009,
                "nonnegative_loss_rate_m_s": 0.0,
                "normalized_weight": 0.3,
            },
        ],
        "candidate_horizon_end_s": [20e6, 30e6, 40e6, 50e6],
        "maximum_weight_sum_error": 1e-12,
        "samples_conditioned_on_survival_to_assessment": True,
        "constant_nonnegative_loss_model_reviewed": True,
        "joint_sample_distribution_reviewed": True,
        "required_thickness_basis_reviewed": True,
        "candidate_horizons_reviewed": True,
    }
    context = RunContext(asset_id="authored", location_id="cml-1", time_basis="authored elapsed seconds")
    registry = default_registry()
    forecast = registry.run("reliability.sampled_linear_thickness_first_passage", payload, context)
    expected_crossing_times = {"cross-40m": 40e6, "cross-30m": 30e6, "never-cross": None}
    expected_probabilities = [0.0, 0.5, 0.7, 0.7]
    actual_crossing_times = {
        row["sample_id"]: row["first_crossing_time_s"] for row in forecast.values["sample_results"]
    }
    actual_probabilities = [
        row["cumulative_probability_given_survival"] for row in forecast.values["forecast_points"]
    ]
    finite_crossing_errors = {
        sample_id: abs(actual_crossing_times[sample_id] - expected)
        for sample_id, expected in expected_crossing_times.items()
        if expected is not None
    }
    probability_errors = [
        abs(actual - expected)
        for actual, expected in zip(actual_probabilities, expected_probabilities, strict=True)
    ]
    if max(finite_crossing_errors.values()) > 1e-8 or max(probability_errors) > 1e-15:
        raise AssertionError("sampled first-passage calculation changed")
    if actual_crossing_times["never-cross"] is not None:
        raise AssertionError("zero-rate row must not receive a finite crossing time")

    schedule_payload = {
        "schedule_id": "authored-schedule-composition",
        "asset_id": payload["asset_id"],
        "location_id": payload["location_id"],
        "physical_scope_id": payload["physical_scope_id"],
        "event_id": payload["event_id"],
        "event_definition": payload["event_definition"],
        "assessment_time_s": payload["assessment_time_s"],
        "conditioning": payload["conditioning"],
        "event_probability_meaning": forecast.values["event_probability_meaning"],
        "forecast_model_id": forecast.model_id,
        "forecast_model_revision": forecast.model_version,
        "forecast_input_sha256": forecast.values["forecast_input_sha256"],
        "forecast_points": forecast.values["forecast_points"],
        "probability_basis": "estimate",
        "maximum_probability_before_inspection": 0.6,
        "minimum_notice_s": 0.0,
        "maximum_deferral_s": 50e6,
        "forecast_identity_reviewed": True,
        "event_scope_and_conditioning_reviewed": True,
        "cumulative_probability_curve_reviewed": True,
        "scheduling_criterion_user_approved": True,
        "evidence": [
            {
                "source_id": "authored-composition-validation",
                "origin": "synthetic",
                "citation": "authored exact first-passage and schedule composition",
            }
        ],
    }
    schedule = registry.run("inspection.threshold_inspection_schedule", schedule_payload, context)
    if schedule.values["selected_inspection_time_s"] != 30e6:
        raise AssertionError("first-passage forecast did not compose with threshold scheduling")
    record = {
        "schema_version": "matintegrity.validation.sampled_linear_thickness_first_passage.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Authored constant-linear crossing-time, discrete-mass and schedule-composition verification; "
            "not calibration of corrosion, a posterior distribution, threshold, field interval or inspection effect."
        ),
        "model_id": forecast.model_id,
        "forecast_input_digest": forecast.input_digest,
        "expected_crossing_times_s": expected_crossing_times,
        "actual_crossing_times_s": actual_crossing_times,
        "finite_crossing_absolute_errors_s": finite_crossing_errors,
        "expected_cumulative_probabilities": expected_probabilities,
        "actual_cumulative_probabilities": actual_probabilities,
        "probability_absolute_errors": probability_errors,
        "never_crossing_probability": forecast.values["never_crossing_probability_under_constant_rate"],
        "schedule_model_id": schedule.model_id,
        "selected_inspection_time_s": schedule.values["selected_inspection_time_s"],
        "selected_probability_given_survival": schedule.values["selected_probability_given_survival"],
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/models/reliability.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/sampled_linear_thickness_first_passage_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
