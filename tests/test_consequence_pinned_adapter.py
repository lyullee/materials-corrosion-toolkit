from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.consequence_exchange import consequence_scenario_handoff
from matintegrity.consequence_pinned_adapter import (
    MATINTEGRITY_SETTINGS_KEY,
    PINNED_COMMIT,
    PINNED_PROVIDER_REQUEST_ADDITIONAL_PROPERTIES,
    PINNED_PROVIDER_REQUEST_PROPERTIES,
    PINNED_PROVIDER_REQUEST_REQUIRED,
    PINNED_PROVIDER_REQUEST_SCHEMA_SHA256,
    PinnedProviderRequestEnvelope,
    PinnedProviderRequestOptions,
    export_pinned_provider_request,
)

SHA = "a" * 64


def requested_model(stage):
    return {
        "stage": stage,
        "provider_id": "process-risk-provider",
        "model_id": f"{stage}-model",
        "model_revision": "1",
        "configuration_digest": SHA,
    }


def handoff():
    return consequence_scenario_handoff(
        handoff_id="handoff-1",
        scenario_id="scenario-1",
        event={
            "event_id": "event-1",
            "asset_id": "asset-1",
            "location_id": "location-1",
            "failure_mode": "caller-defined loss of containment",
            "physical_scope_id": "scope-1",
            "clock_id": "clock-1",
            "horizon_start_s": 100.0,
            "horizon_end_s": 200.0,
            "event_probability": 0.01,
            "probability_semantics": "conditional_first_failure_in_period",
            "probability_conditioning": "survival to the declared horizon start",
            "integrity_model_id": "integrity-model",
            "integrity_model_version": "1",
            "integrity_input_digest": SHA,
            "integrity_result_digest": SHA,
        },
        process_state={
            "pressure_pa": 2_000_000.0,
            "pressure_basis": "absolute",
            "temperature_k": 350.0,
            "temperature_basis": "upstream bulk state",
            "composition": (
                {
                    "component_id": "methane",
                    "fraction": 0.9,
                    "fraction_basis": "mole_fraction",
                    "source_id": "composition-1",
                },
                {
                    "component_id": "nitrogen",
                    "fraction": 0.1,
                    "fraction_basis": "mole_fraction",
                    "source_id": "composition-1",
                },
            ),
            "composition_basis_description": "reviewed dry mole fractions",
            "state_source_digest": SHA,
        },
        release={
            "release_scenario_id": "release-1",
            "inventory_id": "inventory-1",
            "release_location_id": "location-1",
            "release_phase_basis": "gas",
            "release_geometry_basis": "caller_defined",
            "release_geometry_description": "caller-declared circular opening",
            "opening_area_m2": 1e-4,
            "release_direction_basis": "surface normal",
            "release_duration_s": 10.0,
            "isolation_basis": "caller-declared isolation clock",
            "source_boundary_basis": "declared process state",
            "source_digest": SHA,
        },
        requested_models=tuple(
            requested_model(stage) for stage in ("source", "release", "dispersion", "effect")
        ),
        handoff_status="ready",
        limitations=(
            "Opening geometry is caller supplied rather than derived from wall loss.",
            "Event probability semantics must remain unchanged.",
        ),
    )


def options(**changes):
    values = {
        "operating_case_id": "case-1",
        "context_mode": "engineering_review_required",
        "evidence": (
            {
                "id": "source-evidence-1",
                "kind": "user_supplied",
                "citation": "caller-supplied reviewed source term",
                "locator": "source-term-record-1",
                "sha256": SHA,
            },
        ),
        "source": {
            "asset_id": "asset-1",
            "scenario_id": "scenario-1",
            "operating_case_id": "case-1",
            "origin": "user_supplied",
            "source_digest": SHA,
            "source_code_digest": SHA,
            "evidence_ids": ("source-evidence-1",),
            "phase": "vapour",
            "mass_rate_kg_s": 2.0,
            "duration_s": 10.0,
            "released_mass_kg": 20.0,
        },
        "engine": "user_supplied",
        "model_id": "reviewed-dispersion-model",
        "expected_engine_code_digest": SHA,
        "receptor_id": "receptor-1",
        "distance_m": 25.0,
        "quantity": "concentration_kg_m3",
        "provider_settings": {"weather_case_id": "weather-1"},
    }
    values.update(changes)
    return PinnedProviderRequestOptions.model_validate(values)


def test_exports_exact_pinned_closed_request_and_preserves_lossless_extension():
    envelope = export_pinned_provider_request(handoff(), options())
    request = envelope.request

    assert envelope.commit == PINNED_COMMIT
    assert envelope.provider_request_schema_sha256 == PINNED_PROVIDER_REQUEST_SCHEMA_SHA256
    assert set(envelope.provider_request_required) == PINNED_PROVIDER_REQUEST_REQUIRED
    assert not PINNED_PROVIDER_REQUEST_ADDITIONAL_PROPERTIES
    assert set(request) == PINNED_PROVIDER_REQUEST_PROPERTIES
    assert request["schema_version"] == "ccps.provider-request.v1"
    assert request["source"]["mass_rate_kg_s"] == 2.0

    extension = request["settings"][MATINTEGRITY_SETTINGS_KEY]
    assert extension["process_state"]["pressure_pa"] == 2_000_000.0
    assert extension["process_state"]["pressure_basis"] == "absolute"
    assert extension["process_state"]["composition"][0]["fraction"] == 0.9
    assert extension["event"]["horizon_start_s"] == 100.0
    assert extension["event"]["probability_semantics"] == ("conditional_first_failure_in_period")
    assert extension["event"]["event_probability"] == 0.01
    assert not envelope.wall_loss_to_opening_conversion_performed
    assert not envelope.consequence_to_failure_probability_conversion_performed

    restored = PinnedProviderRequestEnvelope.model_validate_json(envelope.model_dump_json())
    assert restored.request_digest == envelope.request_digest


def test_source_term_is_required_and_never_derived_from_opening_or_wall_loss():
    bad_source = options().source.model_copy(update={"released_mass_kg": 19.0})
    with pytest.raises(ValidationError, match="mass rate times duration"):
        PinnedProviderRequestOptions.model_validate(
            {**options().model_dump(mode="python"), "source": bad_source.model_dump(mode="python")}
        )

    bad_duration = options().source.model_copy(update={"duration_s": 20.0, "released_mass_kg": 40.0})
    with pytest.raises(ValueError, match="duration differs"):
        export_pinned_provider_request(handoff(), options(source=bad_duration))


def test_probability_output_and_reserved_extension_override_are_rejected():
    with pytest.raises(ValidationError):
        options(quantity="harm_probability")
    with pytest.raises(ValidationError, match="reserved"):
        options(provider_settings={MATINTEGRITY_SETTINGS_KEY: {"event": "lost"}})


def test_asset_scenario_and_all_source_evidence_must_match():
    wrong_source = options().source.model_copy(update={"scenario_id": "different"})
    with pytest.raises(ValueError, match="asset and scenario"):
        export_pinned_provider_request(handoff(), options(source=wrong_source))

    with pytest.raises(ValidationError, match="must exist"):
        options(evidence=())


def test_request_or_schema_pin_tampering_is_rejected():
    payload = deepcopy(export_pinned_provider_request(handoff(), options()).model_dump(mode="python"))
    payload["request"]["unexpected"] = True
    with pytest.raises(ValidationError, match="closed reviewed schema"):
        PinnedProviderRequestEnvelope.model_validate(payload)

    payload = export_pinned_provider_request(handoff(), options()).model_dump(mode="python")
    payload["provider_request_schema_sha256"] = "b" * 64
    with pytest.raises(ValidationError):
        PinnedProviderRequestEnvelope.model_validate(payload)
