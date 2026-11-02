import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.welding_preheat import (
    WeldPreheatProcedureAssessment,
    specifications,
    weld_preheat_procedure_envelope,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored preheat test"}


def test_declared_interpass_minimum_requires_its_own_measurements():
    base = payload()
    envelope = base.candidate_envelopes[0].model_copy(
        update={"minimum_supported_interpass_temperature_K": 420.0}
    )
    result = weld_preheat_procedure_envelope(payload(candidate_envelopes=(envelope,)))
    assert result.status == "needs_data"


def test_interpass_record_extrema_order_is_enforced():
    with pytest.raises(ValueError,match="recorded interpass extrema"):
        payload(minimum_recorded_interpass_temperature_K=500.)


def test_interpass_lower_excursion_is_not_hidden_by_upper_compliance():
    base = payload()
    envelope = base.candidate_envelopes[0].model_copy(
        update={"minimum_supported_interpass_temperature_K": 420.0}
    )
    result = weld_preheat_procedure_envelope(
        payload(
            candidate_envelopes=(envelope,),
            minimum_recorded_interpass_temperature_K=390.0,
            below_interpass_duration_s=5.0,
        )
    )
    assert result.status == "computed"
    assert result.values["minimum_interpass_temperature_margin_K"] == -30.0
    assert result.values["record_within_declared_procedure_envelope"] is False


def test_preheat_requirement_and_interpass_limits_are_independent_phases():
    from matintegrity.models.welding_preheat import DeclaredPreheatProcedureEnvelope

    raw = payload().candidate_envelopes[0].model_dump()
    raw.update(minimum_required_preheat_temperature_K=500.0, minimum_supported_interpass_temperature_K=420.0)
    envelope = DeclaredPreheatProcedureEnvelope(**raw)
    result = weld_preheat_procedure_envelope(
        payload(
            candidate_envelopes=(envelope,),
            minimum_recorded_preheat_temperature_K=510.0,
            minimum_recorded_interpass_temperature_K=430.0,
            below_interpass_duration_s=0.0,
        )
    )
    assert result.values["record_within_declared_procedure_envelope"] is True


def payload(**updates):
    value = {
        "assessment_id": "preheat-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "weld_id": "weld-1",
        "material_condition_id": "material-1",
        "joint_configuration_id": "joint-a",
        "welding_process_id": "process-a",
        "consumable_condition_id": "consumable-a",
        "hydrogen_control_descriptor": "control-a",
        "restraint_descriptor": "restraint-a",
        "governing_thickness_m": 0.02,
        "net_heat_input_J_m": 1e6,
        "minimum_recorded_preheat_temperature_K": 380.0,
        "maximum_recorded_interpass_temperature_K": 450.0,
        "below_preheat_duration_s": 0.0,
        "above_interpass_duration_s": 0.0,
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "material_condition_id": "material-1",
                "joint_configuration_id": "joint-a",
                "welding_process_id": "process-a",
                "consumable_condition_id": "consumable-a",
                "hydrogen_control_descriptor": "control-a",
                "restraint_descriptor": "restraint-a",
                "minimum_thickness_m": 0.01,
                "maximum_thickness_m": 0.03,
                "minimum_net_heat_input_J_m": 0.5e6,
                "maximum_net_heat_input_J_m": 1.5e6,
                "minimum_required_preheat_temperature_K": 370.0,
                "maximum_supported_interpass_temperature_K": 460.0,
                "applicability_basis": "caller procedure qualification",
                "evidence": (EVIDENCE,),
            },
        ),
        "material_and_joint_identity_reviewed": True,
        "consumable_and_hydrogen_control_reviewed": True,
        "restraint_reviewed": True,
        "thickness_and_heat_input_reviewed": True,
        "temperature_records_reviewed": True,
        "procedure_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return WeldPreheatProcedureAssessment(**value)


def test_unique_supported_envelope_reports_temperature_margins():
    result = weld_preheat_procedure_envelope(payload())
    assert result.status == "computed"
    assert result.values["preheat_temperature_margin_K"] == pytest.approx(10.0)
    assert result.values["record_within_declared_procedure_envelope"] is True


def test_record_excursion_is_visible_without_acceptance_claim():
    result = weld_preheat_procedure_envelope(payload(below_preheat_duration_s=10.0))
    assert result.status == "computed"
    assert result.values["record_within_declared_procedure_envelope"] is False


def test_identity_or_review_missing_needs_data_and_range_outside_is_out_of_scope():
    assert weld_preheat_procedure_envelope(payload(restraint_descriptor="different")).status == "needs_data"
    assert weld_preheat_procedure_envelope(payload(restraint_reviewed=False)).status == "needs_data"
    assert weld_preheat_procedure_envelope(payload(governing_thickness_m=0.05)).status == "out_of_scope"


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.preheat_procedure_envelope",
            payload(),
            RunContext(asset_id="other", location_id="joint-1", time_basis="authored"),
        )
