import math

import pytest
from pydantic import ValidationError

from matintegrity.adapters import (
    OperatingHistory,
    cavitation_history_inputs_from_operating_history,
)
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.thermo import (
    cavitation_history_inputs_from_coolprop,
    cavitation_inputs_from_coolprop,
)

CONTEXT = RunContext(
    asset_id="synthetic-loop",
    location_id="synthetic-throat",
    time_basis="steady authored screening point",
)


def inputs(**overrides):
    base = {
        "fluid_id": "synthetic-liquid",
        "temperature_K": 300.0,
        "pressure_basis": "absolute",
        "local_static_pressure_Pa": 80_000.0,
        "vapor_pressure_Pa": 3_500.0,
        "liquid_density_kg_m3": 997.0,
        "characteristic_velocity_m_s": 12.0,
        "property_provider_id": "synthetic-provider",
        "property_provider_version": "1.0",
        "property_state_digest": "a" * 64,
        "local_pressure_definition": "authored local absolute static pressure",
        "velocity_definition": "authored section mean velocity",
        "absolute_pressure_reviewed": True,
        "thermodynamic_state_reviewed": True,
    }
    return base | overrides


def run(payload):
    return default_registry().run("degradation.cavitation_margin", payload, CONTEXT)


def history_inputs(**overrides):
    base = {
        "history_id": "authored-dip",
        "asset_id": "synthetic-loop",
        "location_id": "synthetic-throat",
        "clock_id": "authored-clock",
        "history_origin": "synthetic",
        "hydraulic_source_digest": "e" * 64,
        "fluid_id": "synthetic-liquid",
        "pressure_basis": "absolute",
        "sample_ids": ["t0", "t1", "t2"],
        "time_s": [0.0, 1.0, 2.0],
        "local_static_pressure_Pa": [5_000.0, 3_000.0, 5_000.0],
        "temperature_K": [300.0, 300.0, 300.0],
        "vapor_pressure_Pa": [4_000.0, 4_000.0, 4_000.0],
        "liquid_density_kg_m3": [997.0, 997.0, 997.0],
        "characteristic_velocity_m_s": [10.0, 10.0, 10.0],
        "sample_valid": [True, True, True],
        "property_provider_id": "synthetic-provider",
        "property_provider_version": "1.0",
        "property_state_digests": ["a" * 64, "b" * 64, "c" * 64],
        "property_history_digest": "d" * 64,
        "local_pressure_definition": "authored local absolute static pressure",
        "velocity_definition": "authored section mean velocity",
        "interpolation": "linear",
        "absolute_pressure_reviewed": True,
        "thermodynamic_state_reviewed": True,
    }
    return base | overrides


def run_history(payload):
    return default_registry().run("degradation.cavitation_history", payload, CONTEXT)


def test_cavitation_margin_matches_independent_pressure_and_head_relations():
    payload = inputs()
    result = run(payload)
    margin = 80_000.0 - 3_500.0
    dynamic = 0.5 * 997.0 * 12.0**2
    assert result.values["static_pressure_margin_Pa"] == margin
    assert result.values["static_head_margin_m"] == pytest.approx(margin / (997.0 * 9.80665))
    assert result.values["characteristic_dynamic_pressure_Pa"] == dynamic
    assert result.values["local_cavitation_number"] == pytest.approx(margin / dynamic)
    assert result.values["thermodynamic_cavitation_possible"] is False
    assert result.inputs["property_state_digest"] == "a" * 64


def test_nonpositive_margin_is_reported_without_claiming_damage():
    result = run(inputs(local_static_pressure_Pa=3_000.0))
    assert result.values["static_pressure_margin_Pa"] == -500.0
    assert result.values["thermodynamic_cavitation_possible"] is True
    assert "damage" in " ".join(result.notes)


@pytest.mark.parametrize("review", ["absolute_pressure_reviewed", "thermodynamic_state_reviewed"])
def test_unreviewed_hydraulic_or_thermodynamic_state_needs_data(review):
    result = run(inputs(**{review: False}))
    assert result.status == "needs_data"
    assert result.values == {}


def test_zero_velocity_and_nonpositive_absolute_pressure_are_rejected():
    with pytest.raises(ValidationError):
        run(inputs(characteristic_velocity_m_s=0.0))
    with pytest.raises(ValidationError):
        run(inputs(local_static_pressure_Pa=0.0))
    with pytest.raises(ValidationError):
        run(inputs(pressure_basis="gauge"))


def test_coolprop_adapter_preserves_versioned_saturation_state():
    payload = cavitation_inputs_from_coolprop(
        fluid="Water",
        temperature_K=300.0,
        local_static_pressure_Pa=80_000.0,
        characteristic_velocity_m_s=12.0,
        local_pressure_definition="authored local absolute static pressure",
        velocity_definition="authored section mean velocity",
    )
    assert payload["vapor_pressure_Pa"] == pytest.approx(3536.80675, rel=1e-5)
    assert payload["liquid_density_kg_m3"] == pytest.approx(996.513, rel=1e-5)
    assert payload["property_provider_id"] == "CoolProp:HEOS"
    assert len(payload["property_state_digest"]) == 64
    result = run(payload)
    expected = (80_000.0 - payload["vapor_pressure_Pa"]) / (0.5 * payload["liquid_density_kg_m3"] * 12.0**2)
    assert result.values["local_cavitation_number"] == pytest.approx(expected)
    assert math.isfinite(result.values["local_cavitation_number"])


def test_history_finds_linear_crossings_duration_and_clipped_deficit_integral():
    result = run_history(history_inputs())
    assert result.values["static_pressure_margin_Pa"] == [1_000.0, -1_000.0, 1_000.0]
    assert result.values["thermodynamic_possible_intervals_s"] == [[0.5, 1.5]]
    assert result.values["total_thermodynamic_possible_duration_s"] == 1.0
    assert result.values["thermodynamic_possible_time_fraction"] == 0.5
    assert result.values["pressure_deficit_exposure_Pa_s"] == pytest.approx(500.0)
    assert result.values["minimum_margin_sample_id"] == "t1"
    assert result.values["minimum_margin_time_s"] == 1.0


def test_history_all_below_and_zero_tangent_are_not_confused():
    below = run_history(history_inputs(local_static_pressure_Pa=[3_999.0, 3_998.0, 3_999.0]))
    assert below.values["thermodynamic_possible_intervals_s"] == [[0.0, 2.0]]
    assert below.values["total_thermodynamic_possible_duration_s"] == 2.0
    assert below.values["pressure_deficit_exposure_Pa_s"] == pytest.approx(3.0)

    tangent = run_history(history_inputs(local_static_pressure_Pa=[4_001.0, 4_000.0, 4_001.0]))
    assert tangent.values["thermodynamic_possible_intervals_s"] == [[1.0, 1.0]]
    assert tangent.values["total_thermodynamic_possible_duration_s"] == 0.0
    assert tangent.values["pressure_deficit_exposure_Pa_s"] == 0.0
    assert tangent.values["any_thermodynamic_cavitation_possible"] is True


def test_history_refuses_invalid_samples_and_unreviewed_state():
    assert run_history(history_inputs(sample_valid=[True, False, True])).status == "needs_data"
    assert run_history(history_inputs(absolute_pressure_reviewed=False)).status == "needs_data"


@pytest.mark.parametrize(
    "overrides",
    [
        {"time_s": [0.0, 1.0, 1.0]},
        {"sample_ids": ["same", "same", "t2"]},
        {"property_state_digests": ["a" * 64, "bad", "c" * 64]},
        {"vapor_pressure_Pa": [4_000.0, 4_000.0]},
    ],
)
def test_history_contract_rejects_misalignment_and_identity_errors(overrides):
    with pytest.raises(ValidationError):
        run_history(history_inputs(**overrides))


def test_coolprop_history_adapter_preserves_each_state_and_composes():
    payload = cavitation_history_inputs_from_coolprop(
        history_id="water-dip",
        asset_id="synthetic-loop",
        location_id="synthetic-throat",
        clock_id="authored-clock",
        history_origin="synthetic",
        hydraulic_source_digest="e" * 64,
        fluid="Water",
        sample_ids=["t0", "t1", "t2"],
        time_s=[0.0, 1.0, 2.0],
        temperature_K=[300.0, 301.0, 302.0],
        local_static_pressure_Pa=[5_000.0, 3_000.0, 5_000.0],
        characteristic_velocity_m_s=[10.0, 10.0, 10.0],
        sample_valid=[True, True, True],
        local_pressure_definition="authored local absolute static pressure",
        velocity_definition="authored section mean velocity",
    )
    assert len(set(payload["property_state_digests"])) == 3
    assert len(payload["property_history_digest"]) == 64
    assert payload["vapor_pressure_Pa"][0] < payload["vapor_pressure_Pa"][1]
    result = run_history(payload)
    assert result.status == "computed"
    assert result.inputs["property_history_digest"] == payload["property_history_digest"]


def test_history_context_identity_mismatch_is_rejected():
    other_context = CONTEXT.model_copy(update={"location_id": "other-location"})
    with pytest.raises(ValueError, match="asset and location"):
        default_registry().run("degradation.cavitation_history", history_inputs(), other_context)


def operating_history():
    return OperatingHistory(
        asset_id="synthetic-loop",
        location_id="synthetic-throat",
        clock_id="operating-clock",
        origin="measured",
        time_s=[0.0, 1.0, 2.0],
        pressure_absolute_Pa=[5_000.0, 3_000.0, 5_000.0],
        temperature_K=[300.0, 300.0, 300.0],
        valid=[True, True, True],
        source_digest="f" * 64,
    )


def test_operating_history_adapter_preserves_identity_clock_and_source_digest():
    payload = cavitation_history_inputs_from_operating_history(
        operating_history(),
        context=CONTEXT,
        fluid="Water",
        characteristic_velocity_m_s=[10.0, 10.0, 10.0],
        local_pressure_definition="reviewed local absolute static pressure channel",
        velocity_definition="reviewed section mean velocity channel",
        pressure_represents_local_static_reviewed=True,
    )
    assert payload["asset_id"] == CONTEXT.asset_id
    assert payload["location_id"] == CONTEXT.location_id
    assert payload["clock_id"] == "operating-clock"
    assert payload["history_origin"] == "measured"
    assert payload["hydraulic_source_digest"] == "f" * 64
    assert payload["sample_ids"] == [
        "operating-clock:0",
        "operating-clock:1",
        "operating-clock:2",
    ]
    assert run_history(payload).status == "computed"


def test_operating_history_adapter_requires_local_static_pressure_review_and_alignment():
    with pytest.raises(ValueError, match="local absolute static"):
        cavitation_history_inputs_from_operating_history(
            operating_history(),
            context=CONTEXT,
            fluid="Water",
            characteristic_velocity_m_s=[10.0, 10.0, 10.0],
            local_pressure_definition="bulk vessel pressure",
            velocity_definition="reviewed section mean velocity channel",
            pressure_represents_local_static_reviewed=False,
        )
    with pytest.raises(ValueError, match="velocity history"):
        cavitation_history_inputs_from_operating_history(
            operating_history(),
            context=CONTEXT,
            fluid="Water",
            characteristic_velocity_m_s=[10.0, 10.0],
            local_pressure_definition="reviewed local absolute static pressure channel",
            velocity_definition="reviewed section mean velocity channel",
            pressure_represents_local_static_reviewed=True,
        )
