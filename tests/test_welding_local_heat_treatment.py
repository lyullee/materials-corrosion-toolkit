import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.welding_local_heat_treatment import (
    LocalHeatTreatmentAssessment,
    local_heat_treatment,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def payload(**updates):
    envelope = {
        "envelope_id": "lht-envelope-1",
        "material_condition_id": "material-1",
        "joint_configuration_id": "joint-1",
        "treatment_procedure_id": "procedure-1",
        "qualified_heat_zone_ids": ("zone-1",),
        "minimum_hold_temperature_K": 600.0,
        "maximum_hold_temperature_K": 650.0,
        "minimum_hold_duration_s": 20.0,
        "maximum_heating_rate_K_s": 20.0,
        "maximum_cooling_rate_K_s": 20.0,
        "maximum_spatial_gradient_K_m": 500.0,
        "procedure_provider_id": "caller-procedure-store",
        "procedure_provider_version": "1",
        "procedure_state_digest": DIGEST_A,
        "applicability_basis": "caller-reviewed procedure qualification",
        "evidence": (EVIDENCE,),
    }
    histories = (
        {
            "sensor_id": "sensor-a",
            "heat_zone_id": "zone-1",
            "sensor_position_m": 0.0,
            "time_s": (0.0, 20.0, 40.0, 60.0),
            "temperature_K": (300.0, 610.0, 620.0, 400.0),
            "acquisition_provider_id": "logger",
            "acquisition_provider_version": "2",
            "acquisition_state_digest": DIGEST_B,
            "evidence": (EVIDENCE,),
        },
        {
            "sensor_id": "sensor-b",
            "heat_zone_id": "zone-1",
            "sensor_position_m": 0.1,
            "time_s": (0.0, 20.0, 40.0, 60.0),
            "temperature_K": (300.0, 605.0, 615.0, 405.0),
            "acquisition_provider_id": "logger",
            "acquisition_provider_version": "2",
            "acquisition_state_digest": DIGEST_C,
            "evidence": (EVIDENCE,),
        },
    )
    value = {
        "assessment_id": "lht-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "weld_id": "weld-1",
        "material_condition_id": "material-1",
        "joint_configuration_id": "joint-1",
        "treatment_procedure_id": "procedure-1",
        "sensor_histories": histories,
        "candidate_envelopes": (envelope,),
        "sensor_layout_reviewed": True,
        "time_and_temperature_records_reviewed": True,
        "material_and_joint_identity_reviewed": True,
        "procedure_identity_reviewed": True,
        "provider_state_digests_reviewed": True,
        "procedure_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return LocalHeatTreatmentAssessment(**value)


def test_history_metrics_and_spatial_gradient_are_compared_to_envelope():
    result = local_heat_treatment(payload())
    assert result.status == "computed"
    assert result.values["minimum_sensor_hold_band_duration_s"] == pytest.approx(21.756440281030443)
    assert result.values["maximum_spatial_gradient_K_m"] == pytest.approx(50.0)
    assert result.values["record_within_declared_procedure_envelope"] is True
    assert any("linearly interpolates" in note for note in result.notes)
    assert any("cannot detect unrecorded peaks" in note for note in result.notes)


def test_interpolated_hold_duration_handles_heating_cooling_and_flat_segments():
    assessment = payload()
    envelope = assessment.candidate_envelopes[0].model_copy(
        update={"minimum_hold_temperature_K": 600.0, "maximum_hold_temperature_K": 650.0}
    )
    history = assessment.sensor_histories[0].model_copy(
        update={"time_s": (0.0, 10.0, 20.0, 30.0), "temperature_K": (500.0, 700.0, 625.0, 500.0)}
    )
    other = history.model_copy(update={"sensor_id": "sensor-b", "sensor_position_m": 0.1})
    result = local_heat_treatment(
        assessment.model_copy(
            update={"candidate_envelopes": (envelope,), "sensor_histories": (history, other)}
        )
    )
    assert result.status == "computed"
    assert result.values["minimum_sensor_hold_band_duration_s"] == pytest.approx(7.833333333333334)


def test_excursion_is_visible_without_acceptance_claim():
    assessment = payload()
    changed = assessment.model_copy(
        update={
            "sensor_histories": tuple(
                row.model_copy(update={"temperature_K": (300.0, 605.0, 615.0, 1000.0)})
                if row.sensor_id == "sensor-b"
                else row
                for row in assessment.sensor_histories
            )
        }
    )
    result = local_heat_treatment(changed)
    assert result.status == "computed"
    assert result.values["record_within_declared_procedure_envelope"] is False


def test_missing_review_and_heat_zone_mismatch_have_explicit_states():
    assert local_heat_treatment(payload(sensor_layout_reviewed=False)).status == "needs_data"
    assessment = payload()
    outside = assessment.model_copy(
        update={
            "candidate_envelopes": (
                assessment.candidate_envelopes[0].model_copy(
                    update={"qualified_heat_zone_ids": ("different-zone",)}
                ),
            )
        }
    )
    assert local_heat_treatment(outside).status == "out_of_scope"


def test_record_validation_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="aligned"):
        payload(
            sensor_histories=(
                payload().sensor_histories[0],
                payload().sensor_histories[1].model_copy(update={"time_s": (0.0, 21.0, 40.0, 60.0)}),
            )
        )

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.local_heat_treatment",
            payload(),
            RunContext(asset_id="other", location_id="weld-1", time_basis="authored"),
        )
