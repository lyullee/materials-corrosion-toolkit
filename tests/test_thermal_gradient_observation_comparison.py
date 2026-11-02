import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_gradient_observation_comparison import (
    ThermalGradientObservationComparison,
    specifications,
    thermal_gradient_observation_comparison,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored comparison test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
DIGEST_E = "e" * 64
DIGEST_F = "f" * 64


def pair(identifier, partition, sequence, specimen, source, independence, sensor, time, measured, predicted):
    return {
        "pair_id": identifier,
        "partition": partition,
        "sequence_id": sequence,
        "physical_specimen_id": specimen,
        "source_group_id": source,
        "independence_group_id": independence,
        "sensor_id": sensor,
        "observation_clock_id": "clock-1",
        "measured_elapsed_time_s": time,
        "predicted_elapsed_time_s": time,
        "predicted_sensor_position_m": 0.0 if sensor == "sensor-1" else 1.0,
        "measured_temperature_K": measured,
        "expanded_measured_temperature_uncertainty_K": 0.5,
        "predicted_temperature_K": predicted,
        "expanded_predicted_temperature_uncertainty_K": 0.4,
        "sample_weight": 1.0,
        "measured_history_digest": DIGEST_D,
        "predicted_history_digest": DIGEST_E,
        "pair_record_digest": DIGEST_F,
        "record_available": True,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "comparison_id": "thermal-comparison-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "component_id": "component-1",
        "campaign_id": "campaign-1",
        "material_id": "material-1",
        "material_state_id": "state-1",
        "physical_scope_definition": "reviewed transient specimen scope",
        "time_basis": "experiment elapsed seconds",
        "provider": {
            "provider_id": "provider-1",
            "solver_id": "solver-1",
            "solver_revision": "rev-1",
            "geometry_id": "geometry-1",
            "geometry_digest": DIGEST_A,
            "boundary_condition_id": "boundary-1",
            "boundary_condition_digest": DIGEST_B,
            "material_property_state_id": "property-state-1",
            "configuration_digest": DIGEST_C,
            "input_digest": DIGEST_D,
            "result_digest": DIGEST_E,
            "minimum_supported_time_s": 0.0,
            "maximum_supported_time_s": 20.0,
            "minimum_supported_position_m": 0.0,
            "maximum_supported_position_m": 1.0,
            "support_definition": "reviewed solver time and sensor-position support",
            "support_digest": DIGEST_F,
            "evidence": (EVIDENCE,),
        },
        "sensors": (
            {
                "sensor_id": "sensor-1",
                "position_m": 0.0,
                "expanded_position_uncertainty_m": 0.001,
                "clock_id": "clock-1",
                "calibration_id": "cal-1",
                "calibration_provider_id": "cal-provider",
                "calibration_provider_revision": "cal-rev-1",
                "calibration_digest": DIGEST_A,
                "calibration_valid": True,
                "invalid_or_missing_basis": None,
                "evidence": (EVIDENCE,),
            },
            {
                "sensor_id": "sensor-2",
                "position_m": 1.0,
                "expanded_position_uncertainty_m": 0.001,
                "clock_id": "clock-1",
                "calibration_id": "cal-2",
                "calibration_provider_id": "cal-provider",
                "calibration_provider_revision": "cal-rev-1",
                "calibration_digest": DIGEST_B,
                "calibration_valid": True,
                "invalid_or_missing_basis": None,
                "evidence": (EVIDENCE,),
            },
        ),
        "observation_pairs": (
            pair(
                "cal-pair-1",
                "calibration",
                "seq-cal",
                "spec-cal",
                "source-cal",
                "ind-cal",
                "sensor-1",
                0.0,
                301.0,
                300.0,
            ),
            pair(
                "cal-pair-2",
                "calibration",
                "seq-cal",
                "spec-cal",
                "source-cal",
                "ind-cal",
                "sensor-2",
                10.0,
                309.0,
                310.0,
            ),
            pair(
                "hold-pair-1",
                "holdout",
                "seq-hold",
                "spec-hold",
                "source-hold",
                "ind-hold",
                "sensor-1",
                5.0,
                307.0,
                305.0,
            ),
        ),
        "maximum_time_alignment_error_s": 0.1,
        "maximum_position_alignment_error_m": 0.001,
        "minimum_calibration_pair_count": 2,
        "minimum_holdout_pair_count": 1,
        "minimum_calibration_sequence_count": 1,
        "minimum_holdout_sequence_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "specimen_material_state_and_scope_reviewed": True,
        "geometry_boundary_solver_and_property_state_reviewed": True,
        "sensor_position_clock_calibration_and_uncertainty_reviewed": True,
        "measured_and_predicted_history_units_reviewed": True,
        "time_and_sensor_alignment_reviewed": True,
        "calibration_holdout_partition_and_independence_reviewed": True,
        "provider_support_and_holdout_interpolation_reviewed": True,
        "source_and_result_digests_reviewed": True,
        "missing_and_invalid_records_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return ThermalGradientObservationComparison.model_validate(row)


def test_aligned_histories_produce_partition_metrics_and_weighted_residuals():
    result = thermal_gradient_observation_comparison(payload())
    assert result.status == "computed"
    assert result.values["calibration_metrics"]["weighted_bias_K"] == pytest.approx(0.0)
    assert result.values["calibration_metrics"]["weighted_rmse_K"] == pytest.approx(1.0)
    assert result.values["holdout_metrics"]["weighted_bias_K"] == pytest.approx(2.0)
    assert result.values["holdout_metrics"]["weighted_rmse_K"] == pytest.approx(2.0)
    holdout = [row for row in result.values["residual_rows"] if row["partition"] == "holdout"][0]
    assert holdout["residual_K"] == pytest.approx(2.0)
    assert holdout["weighted_residual_K"] == pytest.approx(2.0)


def test_provider_or_calibration_support_extrapolation_is_out_of_scope():
    data = payload().model_dump()
    data["observation_pairs"][2]["measured_elapsed_time_s"] = 30.0
    data["observation_pairs"][2]["predicted_elapsed_time_s"] = 30.0
    result = thermal_gradient_observation_comparison(
        ThermalGradientObservationComparison.model_validate(data)
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_provider_support_pair_ids"] == ["hold-pair-1"]
    assert result.values["residual_rows"] == []

    data = payload().model_dump()
    data["observation_pairs"][2]["measured_elapsed_time_s"] = 15.0
    data["observation_pairs"][2]["predicted_elapsed_time_s"] = 15.0
    result = thermal_gradient_observation_comparison(
        ThermalGradientObservationComparison.model_validate(data)
    )
    assert result.status == "out_of_scope"
    assert result.values["holdout_outside_calibration_support_pair_ids"] == ["hold-pair-1"]


def test_review_missing_invalid_and_alignment_gates_need_data():
    assert thermal_gradient_observation_comparison(
        payload(time_and_sensor_alignment_reviewed=False)
    ).status == ("needs_data")
    data = payload().model_dump()
    data["observation_pairs"][0]["predicted_elapsed_time_s"] = 1.0
    result = thermal_gradient_observation_comparison(
        ThermalGradientObservationComparison.model_validate(data)
    )
    assert result.status == "needs_data"
    assert result.values["time_misaligned_pair_ids"] == ["cal-pair-1"]

    data = payload().model_dump()
    data["observation_pairs"][0]["record_valid"] = False
    data["observation_pairs"][0]["invalid_or_missing_basis"] = "reviewed acquisition fault"
    result = thermal_gradient_observation_comparison(
        ThermalGradientObservationComparison.model_validate(data)
    )
    assert result.status == "needs_data"
    assert result.values["invalid_pair_ids"] == ["cal-pair-1"]


def test_partition_leakage_and_nonmonotonic_history_are_rejected():
    data = payload().model_dump()
    data["observation_pairs"][2]["source_group_id"] = "source-cal"
    with pytest.raises(ValueError, match="source group identifiers cannot cross"):
        ThermalGradientObservationComparison.model_validate(data)

    data = payload().model_dump()
    extra = dict(data["observation_pairs"][0])
    extra["pair_id"] = "cal-pair-extra"
    data["observation_pairs"] = (data["observation_pairs"][0], extra, *data["observation_pairs"][1:])
    with pytest.raises(ValueError, match="history times must strictly increase"):
        ThermalGradientObservationComparison.model_validate(data)


def test_specification_identity_input_source_and_context():
    spec = specifications()[0]
    assert spec.model_id == "structural.thermal_gradient_observation_comparison"
    assert spec.input_type is ThermalGradientObservationComparison
    assert spec.source_ids == ("authored_transient_temperature_observation_comparison",)
    context = RunContext(
        asset_id="asset-1", location_id="location-1", time_basis="experiment elapsed seconds"
    )
    spec.context_validator(payload(), context)
    with pytest.raises(ValueError, match="identity and clock must match"):
        spec.context_validator(
            payload(),
            RunContext(asset_id="asset-1", location_id="location-1", time_basis="other"),
        )
