import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_spray_thickness_uncertainty import (
    ThermalSprayThicknessUncertainty,
    specifications,
    thermal_spray_thickness_uncertainty,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def measurement(identifier, value):
    return {
        "measurement_id": identifier,
        "calibration_id": "calibration-1",
        "measured_thickness_m": value,
        "thickness_unit_token": "m",
        "measurement_standard_uncertainty_m": 1e-6,
        "method_id": "method-1",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "input_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def location(identifier, partition, specimen, source, spatial_group, values, reference=None):
    value = {
        "location_record_id": identifier,
        "physical_specimen_id": specimen,
        "source_group_id": source,
        "independence_group_id": f"ind-{specimen}",
        "spatial_group_id": spatial_group,
        "partition": partition,
        "physical_location_id": f"physical-{identifier}",
        "coordinate_frame_id": "frame-1",
        "x_coordinate_m": 0.01,
        "y_coordinate_m": 0.02,
        "layer_id": "layer-1",
        "substrate_condition_id": "substrate-1",
        "spray_batch_id": "batch-1",
        "process_condition_id": "process-1",
        "measurements": tuple(
            measurement(f"{identifier}-measurement-{index}", item) for index, item in enumerate(values)
        ),
        "evidence": (EVIDENCE,),
    }
    if reference is not None:
        value.update(
            {
                "reference_thickness_m": reference,
                "reference_standard_uncertainty_m": 1.5e-6,
                "reference_provider_id": "reference-provider",
                "reference_result_digest": DIGEST_B,
            }
        )
    return value


def locations():
    return (
        location(
            "cal-1", "calibration", "spec-cal-1", "source-cal-a", "spatial-cal-a", (100e-6, 102e-6, 101e-6)
        ),
        location(
            "cal-2", "calibration", "spec-cal-2", "source-cal-b", "spatial-cal-b", (105e-6, 107e-6, 106e-6)
        ),
        location(
            "hold-1",
            "holdout",
            "spec-hold-1",
            "source-hold",
            "spatial-hold",
            (103e-6, 105e-6, 104e-6),
            102e-6,
        ),
    )


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "coating-location-1",
        "physical_scope_id": "coating-scope-1",
        "coating_system_id": "coating-system-1",
        "layer_id": "layer-1",
        "substrate_condition_id": "substrate-1",
        "spray_batch_id": "batch-1",
        "process_condition_id": "process-1",
        "calibrations": (
            {
                "calibration_id": "calibration-1",
                "instrument_id": "instrument-1",
                "instrument_configuration_id": "configuration-1",
                "additive_bias_correction_m": -1e-6,
                "calibration_standard_uncertainty_m": 0.5e-6,
                "minimum_supported_thickness_m": 50e-6,
                "maximum_supported_thickness_m": 200e-6,
                "provider_id": "calibration-provider",
                "provider_revision": "1",
                "configuration_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "locations": locations(),
        "minimum_repeats_per_location": 3,
        "expanded_uncertainty_coverage_factor": 2.0,
        "specimen_location_layer_and_process_identity_reviewed": True,
        "instrument_calibration_support_and_uncertainty_reviewed": True,
        "repeated_measurement_method_units_and_digests_reviewed": True,
        "spatial_groups_and_coordinate_frame_reviewed": True,
        "specimen_source_independence_and_spatial_partitions_reviewed": True,
        "holdout_reference_identity_and_uncertainty_reviewed": True,
        "uncertainty_independence_and_coverage_factor_reviewed": True,
        "missing_invalid_and_support_policy_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ThermalSprayThicknessUncertainty(**value)


def test_repeated_summary_uncertainty_and_holdout_diagnostics_compute():
    result = thermal_spray_thickness_uncertainty(payload())
    assert result.status == "computed"
    first = result.values["location_rows"][0]
    assert first["mean_corrected_thickness_m"] == pytest.approx(100e-6)
    assert first["combined_standard_uncertainty_m"] > 0
    holdout = result.values["location_rows"][2]
    assert holdout["holdout_error_m"] == pytest.approx(1e-6)
    assert result.values["partition_summaries"][1]["holdout_rmse_m"] == pytest.approx(1e-6)


def test_missing_review_or_insufficient_repeats_needs_data():
    assert (
        thermal_spray_thickness_uncertainty(
            payload(uncertainty_independence_and_coverage_factor_reviewed=False)
        ).status
        == "needs_data"
    )
    rows = list(locations())
    rows[0] = {**rows[0], "measurements": rows[0]["measurements"][:2]}
    result = thermal_spray_thickness_uncertainty(payload(locations=tuple(rows)))
    assert result.status == "needs_data"
    assert result.values["insufficient_repeat_location_ids"] == ["cal-1"]


def test_measurement_outside_calibration_support_is_not_extrapolated():
    rows = list(locations())
    changed = list(rows[0]["measurements"])
    changed[0] = measurement("cal-1-measurement-0", 250e-6)
    rows[0] = {**rows[0], "measurements": tuple(changed)}
    result = thermal_spray_thickness_uncertainty(payload(locations=tuple(rows)))
    assert result.status == "out_of_scope"
    assert result.values["outside_calibration_support_measurement_ids"] == ["cal-1-measurement-0"]


def test_partition_leakage_and_context_identity_are_enforced():
    rows = list(locations())
    rows[2] = {**rows[2], "spatial_group_id": "spatial-cal-a"}
    with pytest.raises(ValueError, match="spatial group"):
        payload(locations=tuple(rows))
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.thermal_spray_thickness_uncertainty",
            payload(),
            RunContext(asset_id="other", location_id="coating-location-1", time_basis="authored"),
        )
