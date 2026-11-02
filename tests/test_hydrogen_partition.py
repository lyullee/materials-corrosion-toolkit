import copy
import json
import math

import pytest
from pydantic import ValidationError

from examples.hydrogen_partition import inputs
from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen import HydrogenPartition
from matintegrity.registry import default_registry


def run(x):
    return default_registry().run_json(
        "transport.hydrogen_trap_equilibrium",
        json.dumps(x),
        RunContext(asset_id="synthetic", location_id="point", time_basis="equilibrium"),
    )


def test_zero_binding_partition_and_diffusivity_have_closed_form():
    x = inputs()
    for t in x["traps"]:
        t["binding_energy_J_mol"] = 0.0
    result = run(x)
    assert result.status == "computed"
    capacity = x["lattice_site_density_mol_m3"] + sum(t["site_density_mol_m3"] for t in x["traps"])
    expected = x["total_hydrogen_atoms_mol_m3"] / capacity
    assert result.values["lattice_occupancy"] == pytest.approx(expected, rel=1e-11)
    assert all(t["occupancy"] == pytest.approx(expected) for t in result.values["traps"])
    assert result.values["local_differential_diffusivity_m2_s"] == pytest.approx(
        x["lattice_diffusivity_m2_s"] * x["lattice_site_density_mol_m3"] / capacity
    )


@pytest.mark.parametrize("total", [0.0, 0.2, 100000.0])
def test_untrapped_and_empty_or_filled_limits(total):
    x = inputs()
    x.update(traps=[], total_hydrogen_atoms_mol_m3=total, maximum_supported_lattice_occupancy=1.0)
    r = run(x)
    assert r.status == "computed"
    assert r.values["lattice_hydrogen_atoms_mol_m3"] == pytest.approx(total)
    assert r.values["local_differential_diffusivity_m2_s"] == pytest.approx(x["lattice_diffusivity_m2_s"])


def test_multitrap_mass_and_chemical_potential_balance():
    x = inputs()
    r = run(x)
    assert r.status == "computed"
    values = r.values
    total = values["lattice_hydrogen_atoms_mol_m3"] + sum(t["hydrogen_atoms_mol_m3"] for t in values["traps"])
    assert total == pytest.approx(x["total_hydrogen_atoms_mol_m3"], rel=1e-11)
    theta_l = values["lattice_occupancy"]
    for t, p in zip(values["traps"], x["traps"], strict=True):
        theta = t["occupancy"]
        assert math.log(theta / (1 - theta)) - math.log(theta_l / (1 - theta_l)) == pytest.approx(
            p["binding_energy_J_mol"] / 8.31446261815324 / x["temperature_K"]
        )


def test_differential_storage_matches_independent_forward_finite_difference():
    x = inputs()
    x["lattice_site_density_mol_m3"] = 1000.0
    for t in x["traps"]:
        t["binding_energy_J_mol"] = 5000.0
    k = math.exp(5000 / 8.31446261815324 / x["temperature_K"])

    def total(cl):
        theta = cl / 1000
        return cl + sum(t["site_density_mol_m3"] * k * theta / (1 + (k - 1) * theta) for t in x["traps"])

    cl = 0.1
    h = 1e-5
    x["total_hydrogen_atoms_mol_m3"] = total(cl)
    r = run(x)
    derivative = (total(cl + h) - total(cl - h)) / (2 * h)
    assert r.values["lattice_hydrogen_atoms_mol_m3"] == pytest.approx(cl, rel=1e-10)
    assert r.values["differential_retardation_factor"] == pytest.approx(derivative, rel=1e-8)


def test_population_permutation_and_equivalent_splitting_preserve_solution():
    x = inputs()
    baseline = run(x).values
    t = copy.deepcopy(x["traps"][0])
    t["trap_id"] = "split"
    t["site_density_mol_m3"] /= 2
    x["traps"][0]["site_density_mol_m3"] /= 2
    x["traps"].append(t)
    x["traps"].reverse()
    r = run(x).values
    assert r["lattice_hydrogen_atoms_mol_m3"] == pytest.approx(baseline["lattice_hydrogen_atoms_mol_m3"])
    assert r["local_differential_diffusivity_m2_s"] == pytest.approx(
        baseline["local_differential_diffusivity_m2_s"]
    )


def test_scope_guards_preserve_missing_kinetics_and_occupancy_limits():
    x = inputs()
    x["traps"][0]["reference_lattice_id"] = "another-reference"
    assert run(x).status == "needs_data"
    x = inputs()
    x["local_equilibrium_confirmed"] = False
    assert run(x).status == "needs_data"
    x = inputs()
    x["maximum_supported_lattice_occupancy"] = 1e-30
    assert run(x).status == "out_of_scope"
    x = inputs()
    x["traps"][1]["maximum_supported_occupancy"] = 1e-8
    assert run(x).status == "out_of_scope"
    x = inputs()
    x["total_hydrogen_atoms_mol_m3"] = 1e6
    assert run(x).status == "out_of_scope"
    x = inputs()
    x["traps"][1]["trap_id"] = x["traps"][0]["trap_id"]
    with pytest.raises(ValidationError, match="distinct"):
        HydrogenPartition.model_validate_json(json.dumps(x))


def test_extreme_exponent_and_diffusivity_underflow_are_explicit():
    x = inputs()
    x["traps"][0]["binding_energy_J_mol"] = 1000 * 8.31446261815324 * x["temperature_K"]
    r = run(x)
    assert r.status == "out_of_scope"
    assert r.values["local_differential_diffusivity_m2_s"] is None
    assert math.isfinite(r.values["log_local_differential_diffusivity_m2_s"])
    x["traps"][0]["binding_energy_J_mol"] *= 1e6
    assert run(x).status == "out_of_scope"


def test_trace_concentration_is_not_lost_when_site_fraction_underflows():
    x = inputs()
    x.update(traps=[], lattice_site_density_mol_m3=1e100, total_hydrogen_atoms_mol_m3=1e-250)
    r = run(x)
    assert r.status == "computed"
    assert r.values["lattice_hydrogen_atoms_mol_m3"] == pytest.approx(1e-250, rel=1e-11, abs=0)
    assert r.values["site_fraction_resolution_limited"]
