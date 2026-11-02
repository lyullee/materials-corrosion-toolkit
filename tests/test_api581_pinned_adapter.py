import pytest
from pydantic import ValidationError

from matintegrity.api581_exchange import api581_damage_exchange_record
from matintegrity.api581_pinned_adapter import (
    PINNED_COMMIT,
    PINNED_SCHEMA_PATH,
    PINNED_SCHEMA_SHA256,
    TARGET_ADDITIONAL_PROPERTIES,
    TARGET_REQUIRED_FIELDS,
    PinnedPofMethodSelectionRequest,
    api581_pinned_method_selection_request,
)

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored adapter test"}
D = "a" * 64


def exchange_payload(**updates):
    value = {
        "exchange_id": "exchange-1",
        "asset_id": "asset-1",
        "component_id": "component-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "horizon_start_s": 0.0,
        "horizon_end_s": 100.0,
        "survival_conditioning": "survived to horizon start",
        "damage_mechanism_id": "mechanism-1",
        "damage_mechanism_definition": "caller-defined failure mechanism",
        "wall_flaw_material_state": {
            "state_id": "state-1",
            "wall_thickness_value": 0.01,
            "wall_thickness_unit_token": "m",
            "wall_thickness_basis": "measured minimum",
            "flaw_definition_id": "flaw-1",
            "flaw_state_digest": D,
            "material_id": "material-1",
            "material_condition_id": "condition-1",
            "material_state_digest": D,
            "state_record_digest": D,
            "evidence": (E,),
        },
        "inspection_lineage": (),
        "status": "computed",
        "status_basis": "external provider calculation completed",
        "probability_of_failure": 0.02,
        "probability_semantics": "conditional_first_failure_in_period",
        "probability_event_definition": "first failure in the declared period given start survival",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "model_id": "model-1",
        "model_revision": "1",
        "provider_configuration_digest": D,
        "provider_input_digest": D,
        "provider_result_digest": D,
        "evidence": (E,),
        "limitations": ("Numeric PoF remains in its source exchange contract.",),
    }
    value.update(updates)
    return value


def adapt(record):
    return api581_pinned_method_selection_request(
        record,
        method="structural_reliability",
        qualification_basis="Caller-reviewed provider qualification record QB-1.",
        uncertainty_quantified=True,
        acknowledge_numeric_pof_not_transferred=True,
    )


def test_pinned_constants_and_exact_minimal_request_shape():
    record = api581_damage_exchange_record(**exchange_payload())
    request = adapt(record)

    assert PINNED_COMMIT == "7c8badb829f84b19c7b84d07fbc476601d9194eb"
    assert PINNED_SCHEMA_PATH == "docs/python-api.schema.json"
    assert PINNED_SCHEMA_SHA256 == "bcb2ee8ee001d26e7ca40fe69a23f31358532fd13b29634d3349a9296054b51a"
    assert TARGET_ADDITIONAL_PROPERTIES is False
    assert tuple(request.model_dump()) == TARGET_REQUIRED_FIELDS
    assert request.model_dump() == {
        "method": "structural_reliability",
        "qualification_basis": "Caller-reviewed provider qualification record QB-1.",
        "uncertainty_quantified": True,
    }


def test_target_request_forbids_additional_properties_and_invalid_enum():
    with pytest.raises(ValidationError):
        PinnedPofMethodSelectionRequest.model_validate(
            {
                "method": "external_method_result",
                "qualification_basis": "QB-1",
                "uncertainty_quantified": True,
                "probability_of_failure": 0.02,
            }
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("damage_factor", 2.0, "damage factor"),
        ("inspection_pod", 0.8, "inspection POD"),
        ("spatial_exceedance_probability", 0.2, "spatial exceedance"),
    ],
)
def test_semantically_different_metrics_are_rejected(field, value, message):
    additions = {field: value}
    if field == "damage_factor":
        additions.update(damage_factor_definition="caller factor", damage_factor_unit_token="1")
    elif field == "inspection_pod":
        additions["inspection_pod_semantics"] = "detection_given_flaw_and_procedure"
    else:
        additions["spatial_probability_semantics"] = "spatial_size_exceedance_at_one_exposure"
    record = api581_damage_exchange_record(**exchange_payload(**additions))
    with pytest.raises(ValueError, match=message):
        adapt(record)


def test_damage_only_record_cannot_be_relabelled_as_pof():
    record = api581_damage_exchange_record(
        **exchange_payload(
            probability_of_failure=None,
            probability_semantics=None,
            probability_event_definition=None,
            damage_factor=2.0,
            damage_factor_definition="caller factor",
            damage_factor_unit_token="1",
        )
    )
    with pytest.raises(ValueError, match="conditional period PoF"):
        adapt(record)


def test_explicit_nontransfer_acknowledgement_is_required():
    record = api581_damage_exchange_record(**exchange_payload())
    with pytest.raises(ValueError, match="acknowledge"):
        api581_pinned_method_selection_request(
            record,
            method="expert_judgment",
            qualification_basis="QB-2",
            uncertainty_quantified=False,
            acknowledge_numeric_pof_not_transferred=False,  # type: ignore[arg-type]
        )
