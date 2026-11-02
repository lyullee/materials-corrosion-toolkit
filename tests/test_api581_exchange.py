import pytest
from pydantic import ValidationError

from matintegrity.api581_exchange import api581_damage_exchange_record

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
D = "a" * 64


def payload(**updates):
    value = {
        "exchange_id": "exchange-1",
        "asset_id": "asset-1",
        "component_id": "component-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "horizon_start_s": 0.0,
        "horizon_end_s": 31536000.0,
        "survival_conditioning": "survived to horizon start",
        "damage_mechanism_id": "mechanism-1",
        "damage_mechanism_definition": "authored external damage mechanism",
        "wall_flaw_material_state": {
            "state_id": "state-1",
            "wall_thickness_value": 0.01,
            "wall_thickness_unit_token": "m",
            "wall_thickness_basis": "authored measured minimum",
            "flaw_definition_id": "flaw-state-1",
            "flaw_state_digest": D,
            "material_id": "material-1",
            "material_condition_id": "condition-1",
            "material_state_digest": D,
            "state_record_digest": D,
            "evidence": (E,),
        },
        "inspection_lineage": (
            {
                "inspection_id": "inspection-1",
                "procedure_id": "procedure-1",
                "procedure_revision": "1",
                "inspection_time_s": 0.0,
                "physical_scope_id": "scope-1",
                "method_id": "method-1",
                "provider_id": "inspection-provider",
                "provider_revision": "1",
                "inspection_record_digest": D,
                "evidence": (E,),
            },
        ),
        "status": "computed",
        "status_basis": "external provider completed calculation",
        "damage_factor": 2.0,
        "damage_factor_definition": "authored dimensionless provider factor",
        "damage_factor_unit_token": "1",
        "probability_of_failure": 0.01,
        "probability_semantics": "conditional_first_failure_in_period",
        "probability_event_definition": "first failure during the declared horizon given start survival",
        "inspection_pod": 0.8,
        "inspection_pod_semantics": "detection_given_flaw_and_procedure",
        "spatial_exceedance_probability": 0.2,
        "spatial_probability_semantics": "spatial_size_exceedance_at_one_exposure",
        "provider_id": "external-provider",
        "provider_revision": "1",
        "model_id": "external-api581-model",
        "model_revision": "1",
        "provider_configuration_digest": D,
        "provider_input_digest": D,
        "provider_result_digest": D,
        "evidence": (E,),
        "limitations": (
            "External provider result; schema receipt does not establish physical validation.",
            "Damage factor, POD and spatial exceedance are not converted to PoF.",
        ),
    }
    value.update(updates)
    return value


def test_computed_exchange_preserves_distinct_probability_semantics():
    record = api581_damage_exchange_record(**payload())
    assert record.schema_version == "matintegrity.api581_damage_exchange.v1"
    assert record.probability_semantics == "conditional_first_failure_in_period"
    assert record.inspection_pod_semantics == "detection_given_flaw_and_procedure"
    assert record.spatial_probability_semantics == "spatial_size_exceedance_at_one_exposure"


def test_pof_requires_period_first_failure_semantics_and_event_definition():
    with pytest.raises(ValidationError, match="PoF value, semantics"):
        api581_damage_exchange_record(**payload(probability_semantics=None))
    with pytest.raises(ValidationError):
        api581_damage_exchange_record(**payload(probability_semantics="unscoped_event_probability"))


def test_noncomputed_status_cannot_carry_results():
    with pytest.raises(ValidationError, match="cannot carry computed"):
        api581_damage_exchange_record(**payload(status="needs_data", provider_result_digest=None))
    value = payload(
        status="needs_data",
        provider_result_digest=None,
        damage_factor=None,
        damage_factor_definition=None,
        damage_factor_unit_token=None,
        probability_of_failure=None,
        probability_semantics=None,
        probability_event_definition=None,
        inspection_pod=None,
        inspection_pod_semantics=None,
        spatial_exceedance_probability=None,
        spatial_probability_semantics=None,
    )
    assert api581_damage_exchange_record(**value).status == "needs_data"


def test_payload_digest_and_scope_binding_are_strict():
    record = api581_damage_exchange_record(**payload())
    with pytest.raises(ValidationError, match="payload digest"):
        record.model_copy(update={"damage_factor": 3.0}).model_validate(
            record.model_copy(update={"damage_factor": 3.0}).model_dump()
        )
    bad_lineage = list(payload()["inspection_lineage"])
    bad_lineage[0] = {**bad_lineage[0], "physical_scope_id": "other"}
    with pytest.raises(ValidationError, match="physical scope"):
        api581_damage_exchange_record(**payload(inspection_lineage=tuple(bad_lineage)))
