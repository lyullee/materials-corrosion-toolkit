import json

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    SolutionConcentrationConversion,
    solution_concentration_conversion,
)
from matintegrity.registry import default_registry


def payload(**updates):
    values = {
        "component_id": "component",
        "solution_state_id": "solution-state",
        "input_basis": "mass_fraction",
        "input_value": 0.2,
        "solution_density_kg_m3": 1000.0,
        "molar_mass_kg_mol": 0.05,
        "pure_component_density_kg_m3": 2000.0,
        "pure_component_state_id": "pure-state",
    } | updates
    digest = canonical_digest(
        SolutionConcentrationConversion.model_construct(**values).model_dump(mode="json", exclude={"basis"})
    )
    basis = {
        "source_id": "authored",
        "revision": "1",
        "license_id": "authored-test",
        "record_sha256": digest,
        "applicability_and_units_reviewed": True,
        "computational_use_authorized": True,
        "evidence": [
            {
                "source_id": "authored",
                "origin": "synthetic",
                "citation": "authored concentration states",
                "license_id": "authored-test",
                "sha256": digest,
            }
        ],
    }
    return SolutionConcentrationConversion.model_validate_json(json.dumps(values | {"basis": basis}))


@pytest.mark.parametrize(
    "basis,value",
    [
        ("mass_fraction", 0.2),
        ("mass_concentration_kg_m3", 200.0),
        ("amount_concentration_mol_m3", 4000.0),
        ("pure_component_volume_per_final_solution_volume", 0.1),
    ],
)
def test_explicit_basis_routes_agree_without_assuming_equal_mass_and_volume_fractions(basis, value):
    result = solution_concentration_conversion(payload(input_basis=basis, input_value=value))
    assert result.status == "computed"
    assert result.values["mass_fraction"] == pytest.approx(0.2)
    assert result.values["mass_concentration_kg_m3"] == pytest.approx(200.0)
    assert result.values["amount_concentration_mol_m3"] == pytest.approx(4000.0)
    assert result.values["pure_component_volume_per_final_solution_volume"] == pytest.approx(0.1)


def test_unsupplied_properties_produce_unknown_conversions():
    result = solution_concentration_conversion(
        payload(molar_mass_kg_mol=None, pure_component_density_kg_m3=None, pure_component_state_id=None)
    )
    assert result.status == "computed"
    assert result.values["amount_concentration_mol_m3"] is None
    assert result.values["pure_component_volume_per_final_solution_volume"] is None


@pytest.mark.parametrize(
    "updates",
    [
        {"input_basis": "amount_concentration_mol_m3", "molar_mass_kg_mol": None},
        {
            "input_basis": "pure_component_volume_per_final_solution_volume",
            "pure_component_density_kg_m3": None,
            "pure_component_state_id": None,
        },
        {"input_basis": "mass_fraction", "input_value": 1.1},
    ],
)
def test_missing_basis_properties_and_invalid_mass_fraction_are_rejected(updates):
    with pytest.raises(ValueError):
        payload(**updates)


def test_component_mass_cannot_exceed_total_solution_mass():
    result = solution_concentration_conversion(
        payload(input_basis="mass_concentration_kg_m3", input_value=2000.0)
    )
    assert result.status == "out_of_scope"


def test_zero_and_numeric_range_are_distinguished():
    assert solution_concentration_conversion(payload(input_value=0.0)).values["mass_fraction"] == 0.0
    result = solution_concentration_conversion(
        payload(input_basis="amount_concentration_mol_m3", input_value=1e308, molar_mass_kg_mol=1e308)
    )
    assert result.status == "out_of_scope"
    json.dumps(result.values, allow_nan=False)


def test_default_registry_python_json_exchange():
    registry = default_registry()
    value = payload()
    context = RunContext(asset_id="asset", location_id="bath", time_basis="synthetic")
    direct = registry.run("chemistry.solution_concentration_conversion", value, context)
    assert direct.status == "computed"
    assert (
        direct.model_dump()
        == registry.run_json(
            "chemistry.solution_concentration_conversion", value.model_dump_json(), context
        ).model_dump()
    )
