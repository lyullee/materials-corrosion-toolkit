import math

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    WellMixedGasPurge,
    WellMixedPurgeStage,
    well_mixed_gas_purge,
)
from matintegrity.registry import default_registry

HALF_LIFE_DURATION = math.log(2)


def stage(identifier="s", duration=HALF_LIFE_DURATION, flow=1.0, inlet=0.0):
    return WellMixedPurgeStage(
        stage_id=identifier,
        duration_s=duration,
        inlet_actual_volume_flow_m3_s=flow,
        inlet_component_mole_fraction=inlet,
    )


def request(**updates):
    raw = dict(
        compartment_id="c",
        component_id="authored-tracer",
        clock_id="clock",
        gas_state_basis_id="constant-state",
        compartment_volume_m3=1.0,
        initial_component_mole_fraction=0.5,
        flow_volume_basis="compartment_actual_volume",
        constant_volume_pressure_temperature_and_perfect_mixing_reviewed=True,
        equal_inlet_outlet_no_reaction_leak_or_adsorption_reviewed=True,
        stages=(stage(),),
    )
    raw.update(updates)
    digest = canonical_digest(
        WellMixedGasPurge.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return WellMixedGasPurge(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored dilution balance.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_half_life_analytic_case():
    result = well_mixed_gas_purge(request())
    assert result.values["final_component_mole_fraction"] == pytest.approx(0.25)


def test_stage_partition_invariance():
    a = well_mixed_gas_purge(request(stages=(stage(duration=2.0),)))
    b = well_mixed_gas_purge(request(stages=(stage("a", duration=1.0), stage("b", duration=1.0))))
    assert a.values["final_component_mole_fraction"] == pytest.approx(
        b.values["final_component_mole_fraction"]
    )
    assert b.values["history"][-1]["end_time_s"] == 2.0


def test_inlet_contamination_increases_concentration_and_retains_order():
    result = well_mixed_gas_purge(request(stages=(stage("a"), stage("b", inlet=0.75))))
    assert [r["stage_id"] for r in result.values["history"]] == ["a", "b"]
    assert result.values["final_component_mole_fraction"] == pytest.approx(0.5)


def test_zero_flow_is_stagnation_not_replacement():
    result = well_mixed_gas_purge(request(stages=(stage(flow=0.0, inlet=1.0),)))
    assert result.values["final_component_mole_fraction"] == 0.5


def test_constant_equal_composition_stays_bounded_at_unity():
    assert (
        well_mixed_gas_purge(request(initial_component_mole_fraction=1.0, stages=(stage(inlet=1.0),))).values[
            "final_component_mole_fraction"
        ]
        == 1.0
    )


def test_unreviewed_mixing_needs_data():
    assert (
        well_mixed_gas_purge(
            request(constant_volume_pressure_temperature_and_perfect_mixing_reviewed=False)
        ).status
        == "needs_data"
    )


def test_duplicate_stage_ids_rejected():
    with pytest.raises(ValueError, match="identities must be unique"):
        request(stages=(stage(), stage()))


def test_nonzero_residual_underflow_withholds_entire_history():
    result = well_mixed_gas_purge(request(stages=(stage("first"), stage("last", duration=10000.0))))
    assert result.status == "out_of_scope"
    assert "history" not in result.values


def test_standard_flow_cannot_be_used_as_actual_volume_flow():
    with pytest.raises(ValueError):
        request(flow_volume_basis="standard_volume")


def test_python_json_exchange():
    x = request()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    registry = default_registry()
    a = registry.run("welding.well_mixed_gas_purge", x.model_dump(), context)
    b = registry.run_json("welding.well_mixed_gas_purge", x.model_dump_json(), context)
    assert a.values == b.values
