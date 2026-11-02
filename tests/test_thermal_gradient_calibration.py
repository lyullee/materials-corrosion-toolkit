import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_gradient_calibration import (
    ThermalGradientParameterCalibration,
    specifications,
    thermal_gradient_parameter_calibration,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored thermal test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
DIGEST_E = "e" * 64
DIGEST_F = "f" * 64


def observation(
    identifier,
    partition,
    sequence,
    specimen,
    source,
    independence,
    sensor,
    time,
    baseline,
    sensitivity,
    observed,
    digest,
):
    return {
        "observation_id": identifier,
        "partition": partition,
        "sequence_id": sequence,
        "physical_specimen_id": specimen,
        "source_group_id": source,
        "independence_group_id": independence,
        "sensor_id": sensor,
        "observation_clock_id": "clock-1",
        "observed_elapsed_time_s": time,
        "provider_elapsed_time_s": time,
        "provider_sensor_position_m": 0.0 if sensor == "sensor-1" else 1.0,
        "observed_temperature_K": observed,
        "expanded_observed_temperature_uncertainty_K": 0.5,
        "baseline_predicted_temperature_K": baseline,
        "expanded_baseline_prediction_uncertainty_K": 0.4,
        "predicted_temperature_sensitivity_K_per_parameter_unit": sensitivity,
        "sample_weight": 1.0,
        "sequence_record_digest": digest,
        "provider_response_digest": DIGEST_E,
        "observation_record_digest": DIGEST_F,
        "record_available": True,
        "record_valid": True,
        "invalid_or_missing_basis": None,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    row = {
        "calibration_id": "thermal-fit-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "component_id": "component-1",
        "experiment_or_campaign_id": "campaign-1",
        "specimen_material_id": "material-1",
        "specimen_material_state_id": "state-1",
        "physical_scope_definition": "reviewed one-dimensional specimen response scope",
        "time_basis": "experiment elapsed seconds",
        "provider": {
            "response_basis": "external_provider_sensitivity",
            "provider_id": "provider-1",
            "solver_or_response_id": "response-1",
            "provider_revision": "rev-1",
            "geometry_id": "geometry-1",
            "geometry_digest": DIGEST_A,
            "boundary_condition_id": "boundary-1",
            "boundary_condition_digest": DIGEST_B,
            "provider_configuration_digest": DIGEST_C,
            "provider_state_digest": DIGEST_D,
            "analytical_response_definition": None,
            "evidence": (EVIDENCE,),
        },
        "parameter": {
            "parameter_id": "conductivity-multiplier",
            "parameter_kind": "thermal_property_multiplier",
            "parameter_definition": "caller-defined multiplier applied by the response provider",
            "unit_token": "1",
            "reference_value": 1.0,
            "minimum_supported_value": 0.5,
            "maximum_supported_value": 1.5,
            "support_basis": "reviewed provider sensitivity support",
            "evidence": (EVIDENCE,),
        },
        "sensors": (
            {
                "sensor_id": "sensor-1",
                "position_m": 0.0,
                "expanded_position_uncertainty_m": 0.001,
                "clock_id": "clock-1",
                "sensor_calibration_id": "sensor-cal-1",
                "sensor_calibration_provider_id": "cal-provider",
                "sensor_calibration_provider_revision": "cal-rev-1",
                "sensor_calibration_digest": DIGEST_A,
                "calibration_valid": True,
                "invalid_or_missing_basis": None,
                "evidence": (EVIDENCE,),
            },
            {
                "sensor_id": "sensor-2",
                "position_m": 1.0,
                "expanded_position_uncertainty_m": 0.001,
                "clock_id": "clock-1",
                "sensor_calibration_id": "sensor-cal-2",
                "sensor_calibration_provider_id": "cal-provider",
                "sensor_calibration_provider_revision": "cal-rev-1",
                "sensor_calibration_digest": DIGEST_B,
                "calibration_valid": True,
                "invalid_or_missing_basis": None,
                "evidence": (EVIDENCE,),
            },
        ),
        "observations": (
            observation(
                "cal-1",
                "calibration",
                "seq-cal",
                "spec-cal",
                "source-cal",
                "ind-cal",
                "sensor-1",
                0.0,
                300.0,
                10.0,
                302.0,
                DIGEST_A,
            ),
            observation(
                "cal-2",
                "calibration",
                "seq-cal",
                "spec-cal",
                "source-cal",
                "ind-cal",
                "sensor-2",
                10.0,
                310.0,
                20.0,
                314.0,
                DIGEST_A,
            ),
            observation(
                "hold-1",
                "holdout",
                "seq-hold",
                "spec-hold",
                "source-hold",
                "ind-hold",
                "sensor-1",
                5.0,
                305.0,
                15.0,
                308.5,
                DIGEST_B,
            ),
        ),
        "maximum_time_alignment_error_s": 0.1,
        "maximum_sensor_position_alignment_error_m": 0.001,
        "minimum_calibration_observation_count": 2,
        "minimum_holdout_observation_count": 1,
        "minimum_calibration_sequence_count": 1,
        "minimum_holdout_sequence_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "minimum_weighted_sensitivity_information": 1.0,
        "specimen_material_state_and_scope_reviewed": True,
        "geometry_boundary_and_provider_identity_reviewed": True,
        "sensor_positions_clocks_calibrations_and_uncertainty_reviewed": True,
        "parameter_definition_units_and_support_reviewed": True,
        "source_specimen_independence_partitions_reviewed": True,
        "observation_provider_alignment_reviewed": True,
        "provider_response_and_record_digests_reviewed": True,
        "missing_invalid_and_support_gates_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return ThermalGradientParameterCalibration.model_validate(row)


def test_weighted_single_parameter_fit_and_holdout_residual():
    result = thermal_gradient_parameter_calibration(payload())
    assert result.status == "computed"
    assert result.values["fitted_parameter_value"] == pytest.approx(1.2)
    assert result.values["calibration_weighted_rmse_K"] == pytest.approx(0.0)
    assert result.values["holdout_weighted_bias_K"] == pytest.approx(0.5)
    assert result.values["holdout_weighted_rmse_K"] == pytest.approx(0.5)
    assert result.values["holdout_residuals"][0]["predicted_temperature_K"] == pytest.approx(308.0)


def test_parameter_or_holdout_outside_support_emits_no_residuals():
    data = payload().model_dump()
    data["observations"][0]["observed_temperature_K"] = 320.0
    data["observations"][1]["observed_temperature_K"] = 350.0
    result = thermal_gradient_parameter_calibration(ThermalGradientParameterCalibration.model_validate(data))
    assert result.status == "out_of_scope"
    assert result.values["holdout_residuals"] == []

    data = payload().model_dump()
    data["observations"][2]["observed_elapsed_time_s"] = 20.0
    data["observations"][2]["provider_elapsed_time_s"] = 20.0
    result = thermal_gradient_parameter_calibration(ThermalGradientParameterCalibration.model_validate(data))
    assert result.status == "out_of_scope"
    assert result.values["out_of_support_holdout_observation_ids"] == ["hold-1"]
    assert result.values["holdout_residuals"] == []


def test_missing_invalid_alignment_and_identifiability_gates_need_data():
    assert thermal_gradient_parameter_calibration(
        payload(observation_provider_alignment_reviewed=False)
    ).status == ("needs_data")
    data = payload().model_dump()
    data["observations"][0]["provider_elapsed_time_s"] = 1.0
    result = thermal_gradient_parameter_calibration(ThermalGradientParameterCalibration.model_validate(data))
    assert result.status == "needs_data"
    assert result.values["time_misaligned_observation_ids"] == ["cal-1"]

    data = payload().model_dump()
    for row in data["observations"][:2]:
        row["predicted_temperature_sensitivity_K_per_parameter_unit"] = 0.0
    result = thermal_gradient_parameter_calibration(ThermalGradientParameterCalibration.model_validate(data))
    assert result.status == "needs_data"
    assert result.values["identifiable_parameter_response"] is False


def test_partition_leakage_and_history_order_are_rejected():
    data = payload().model_dump()
    data["observations"][2]["physical_specimen_id"] = "spec-cal"
    with pytest.raises(ValueError, match="physical specimen identifiers cannot cross"):
        ThermalGradientParameterCalibration.model_validate(data)

    data = payload().model_dump()
    extra = dict(data["observations"][0])
    extra["observation_id"] = "cal-extra"
    extra["observed_elapsed_time_s"] = 0.0
    extra["provider_elapsed_time_s"] = 0.0
    data["observations"] = (data["observations"][0], extra, *data["observations"][1:])
    with pytest.raises(ValueError, match="history times must strictly increase"):
        ThermalGradientParameterCalibration.model_validate(data)


def test_specification_identity_input_source_and_context():
    spec = specifications()[0]
    assert spec.model_id == "structural.thermal_gradient_parameter_calibration"
    assert spec.input_type is ThermalGradientParameterCalibration
    assert spec.source_ids == ("authored_weighted_transient_temperature_sensitivity_calibration",)
    context = RunContext(
        asset_id="asset-1", location_id="location-1", time_basis="experiment elapsed seconds"
    )
    spec.context_validator(payload(), context)
    with pytest.raises(ValueError, match="identity and clock must match"):
        spec.context_validator(
            payload(),
            RunContext(asset_id="asset-1", location_id="location-1", time_basis="other clock"),
        )
