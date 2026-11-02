from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.consequence_exchange import (
    ConsequenceScenarioHandoff,
    ConsequenceScenarioResultRecord,
    consequence_scenario_handoff,
    consequence_scenario_result_record,
)

SHA = "a" * 64


def model(stage):
    return {
        "stage": stage,
        "provider_id": "external-process-risk-provider",
        "model_id": f"{stage}-model",
        "model_revision": "2026.1",
        "configuration_digest": SHA,
    }


def handoff():
    return consequence_scenario_handoff(
        handoff_id="handoff-1",
        scenario_id="scenario-1",
        event={
            "event_id": "loss-of-containment-1",
            "asset_id": "vessel-1",
            "location_id": "nozzle-1",
            "failure_mode": "caller-defined loss-of-containment event",
            "physical_scope_id": "nozzle-segment-1",
            "clock_id": "operating-clock-1",
            "horizon_start_s": 0.0,
            "horizon_end_s": 31_536_000.0,
            "event_probability": 0.002,
            "probability_semantics": "conditional_first_failure_in_period",
            "probability_conditioning": "survival to horizon start under the declared state",
            "integrity_model_id": "integrity-provider-model",
            "integrity_model_version": "1.2",
            "integrity_input_digest": SHA,
            "integrity_result_digest": SHA,
        },
        process_state={
            "pressure_pa": 2_000_000.0,
            "pressure_basis": "absolute",
            "temperature_k": 350.0,
            "temperature_basis": "bulk upstream state",
            "composition": (
                {
                    "component_id": "methane",
                    "fraction": 0.9,
                    "fraction_basis": "mole_fraction",
                    "source_id": "stream-analysis-1",
                },
                {
                    "component_id": "nitrogen",
                    "fraction": 0.1,
                    "fraction_basis": "mole_fraction",
                    "source_id": "stream-analysis-1",
                },
            ),
            "composition_basis_description": "reviewed dry-gas mole fractions",
            "state_source_digest": SHA,
        },
        release={
            "release_scenario_id": "release-1",
            "inventory_id": "inventory-1",
            "release_location_id": "nozzle-1",
            "release_phase_basis": "provider_to_determine",
            "release_geometry_basis": "caller_defined",
            "release_geometry_description": "independently declared circular opening",
            "opening_area_m2": 1e-4,
            "release_direction_basis": "normal to local surface",
            "release_duration_s": 120.0,
            "isolation_basis": "caller-declared isolation time",
            "source_boundary_basis": "upstream process state in this handoff",
            "source_digest": SHA,
        },
        requested_models=tuple(model(stage) for stage in ("source", "release", "dispersion", "effect")),
        handoff_status="ready",
        missing_items=(),
        limitations=(
            "Opening geometry is caller supplied and is not derived from wall loss.",
            "Consequences do not alter the integrity-event probability.",
        ),
    )


def quantity(stage):
    units = {
        "source": "kg",
        "release": "kg/s",
        "dispersion": "kg/m^3",
        "effect": "W/m^2",
    }
    return {
        "quantity_id": f"{stage}-quantity-1",
        "quantity_definition": f"authored {stage} result quantity",
        "value": 1.25,
        "unit_token": units[stage],
        "standard_uncertainty": 0.05,
        "receptor_id": "receptor-1",
        "receptor_type": "point receptor",
        "receptor_location_id": "grid-point-10",
        "clock_id": "operating-clock-1",
        "time_s": 10.0,
        "time_basis": "seconds after declared release initiation",
    }


def stage_result(stage, status="computed"):
    return {
        **model(stage),
        "input_digest": SHA,
        "result_digest": SHA,
        "status": status,
        "quantities": (quantity(stage),) if status == "computed" else (),
        "missing_items": () if status == "computed" else ("provider input unavailable",),
        "notes": (f"authored {stage} exchange result",),
    }


def result_record():
    return consequence_scenario_result_record(
        handoff=handoff(),
        result_record_id="result-1",
        stage_results=tuple(stage_result(stage) for stage in ("source", "release", "dispersion", "effect")),
        scenario_status="complete",
        limitations=("No consequence quantity is interpreted as failure probability.",),
    )


def test_round_trip_preserves_state_probability_models_receptor_time_and_units():
    source = handoff()
    restored_handoff = ConsequenceScenarioHandoff.model_validate_json(source.model_dump_json())
    assert restored_handoff.process_state.pressure_basis == "absolute"
    assert restored_handoff.process_state.composition[0].fraction_basis == "mole_fraction"
    assert not restored_handoff.release.wall_loss_to_opening_conversion_performed

    result = result_record()
    restored = ConsequenceScenarioResultRecord.model_validate_json(result.model_dump_json())
    assert restored.probability_semantics == "conditional_first_failure_in_period"
    assert restored.event_probability == 0.002
    assert restored.stage_results[-1].quantities[0].unit_token == "W/m^2"
    assert restored.stage_results[-1].quantities[0].receptor_id == "receptor-1"
    assert restored.stage_results[-1].quantities[0].time_s == 10.0
    assert not restored.consequence_to_failure_probability_conversion_performed


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("probability_semantics", "unscoped_event_probability"),
        ("event_probability", 0.5),
        ("handoff_payload_digest", "b" * 64),
    ],
)
def test_result_record_rejects_probability_or_lineage_tampering(field, replacement):
    payload = deepcopy(result_record().model_dump(mode="json"))
    payload[field] = replacement
    with pytest.raises(ValidationError):
        ConsequenceScenarioResultRecord.model_validate(payload)


def test_incomplete_stage_cannot_be_labelled_complete_and_model_identity_must_match():
    rows = [stage_result(stage) for stage in ("source", "release", "dispersion", "effect")]
    rows[-1] = stage_result("effect", status="needs_data")
    with pytest.raises(ValidationError, match="all stages"):
        consequence_scenario_result_record(
            handoff=handoff(),
            result_record_id="incomplete",
            stage_results=tuple(rows),
            scenario_status="complete",
            limitations=("negative control",),
        )

    rows[-1] = {**stage_result("effect"), "model_revision": "different"}
    with pytest.raises(ValidationError, match="identity"):
        consequence_scenario_result_record(
            handoff=handoff(),
            result_record_id="wrong-provider-model",
            stage_results=tuple(rows),
            scenario_status="complete",
            limitations=("negative control",),
        )


def test_composition_and_scenario_status_completeness_are_strict():
    values = handoff().model_dump(mode="python", exclude={"payload_digest"})
    values["process_state"]["composition"][0]["fraction"] = 0.8
    with pytest.raises(ValidationError, match="sum to one"):
        consequence_scenario_handoff(**values)

    values = handoff().model_dump(mode="python", exclude={"payload_digest"})
    values["handoff_status"] = "needs_data"
    with pytest.raises(ValidationError, match="must identify"):
        consequence_scenario_handoff(**values)
