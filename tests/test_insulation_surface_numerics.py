import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.insulation_surface import InsulationSurfaceRequest, solve_insulation_surface
from matintegrity.registry import default_registry


def payload(**updates):
    return InsulationSurfaceRequest(
        **(
            {
                "inner_radius_m": 0.1,
                "outer_radius_m": 0.2,
                "length_m": 1.0,
                "conductivity_W_m_K": 0.05,
                "inner_surface_temperature_K": 500.0,
                "ambient_temperature_K": 300.0,
                "radiative_surroundings_temperature_K": 300.0,
                "convection_W_m2_K": 10.0,
                "emissivity": 0.0,
                "steady_constant_conductivity_reviewed": True,
            }
            | updates
        )
    )


def test_convection_only_matches_independent_resistance_solution():
    result = solve_insulation_surface(payload())
    conductance = 2 * math.pi * 0.05 / math.log(2)
    external = 2 * math.pi * 0.2 * 10
    expected = (conductance * 500 + external * 300) / (conductance + external)
    assert result["status"] == "computed"
    assert result["outer_surface_temperature_K"] == pytest.approx(expected, rel=1e-10)
    assert abs(result["balance_residual_W"]) < 1e-6


def test_disabled_radiation_boundary_cannot_change_bracket_or_result():
    baseline = solve_insulation_surface(payload())
    result = solve_insulation_surface(payload(radiative_surroundings_temperature_K=1e200))
    assert result["status"] == "computed"
    assert result["outer_surface_temperature_K"] == baseline["outer_surface_temperature_K"]
    assert result["radiative_heat_out_W"] == 0.0


def test_disabled_convection_boundary_cannot_change_radiation_solution():
    baseline = solve_insulation_surface(payload(convection_W_m2_K=0.0, emissivity=0.5))
    result = solve_insulation_surface(
        payload(convection_W_m2_K=0.0, emissivity=0.5, ambient_temperature_K=1e200)
    )
    assert result["status"] == "computed"
    assert result["outer_surface_temperature_K"] == baseline["outer_surface_temperature_K"]
    assert result["convective_heat_out_W"] == 0.0


def test_isothermal_extreme_temperature_has_zero_heat_flow():
    result = solve_insulation_surface(
        payload(
            inner_surface_temperature_K=1e200,
            ambient_temperature_K=1e200,
            radiative_surroundings_temperature_K=1e200,
            emissivity=0.5,
        )
    )
    assert result["status"] == "computed"
    assert result["balance_residual_W"] == 0.0
    json.dumps(result, allow_nan=False)


def test_unresolvable_thin_gap_never_claims_converged_energy_balance():
    result = solve_insulation_surface(
        payload(inner_radius_m=1.0, outer_radius_m=math.nextafter(1.0, math.inf))
    )
    assert result["status"] == "out_of_scope"
    assert "did not converge" in result["reason"]
    json.dumps(result, allow_nan=False)


def test_true_heat_flow_range_failure_and_missing_review():
    result = solve_insulation_surface(payload(inner_surface_temperature_K=1e200, emissivity=0.5))
    assert result["status"] == "out_of_scope"
    json.dumps(result, allow_nan=False)
    assert (
        solve_insulation_surface(payload(steady_constant_conductivity_reviewed=False))["status"]
        == "needs_data"
    )


def test_default_registry_python_json():
    registry = default_registry()
    value = payload()
    context = RunContext(asset_id="asset", location_id="insulation", time_basis="synthetic")
    direct = registry.run("thermal.insulation_surface_balance", value, context)
    assert direct.status == "computed" and direct.model_version == "1.0.1"
    assert (
        direct.model_dump()
        == registry.run_json(
            "thermal.insulation_surface_balance", value.model_dump_json(), context
        ).model_dump()
    )
