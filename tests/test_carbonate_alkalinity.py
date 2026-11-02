import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.carbonate_alkalinity import (
    CarbonateAlkalinitySpeciation,
    carbonate_alkalinity_speciation,
    specifications,
)

EVIDENCE = {
    "source_id": "synthetic-carbonate-case",
    "origin": "synthetic",
    "citation": "independently authored synthetic carbonate-only balance",
}


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "sample-location-1",
        "sample_id": "sample-1",
        "temperature_K": 298.15,
        "ph_activity": 8.3,
        "measured_total_alkalinity_mol_L": 0.002,
        "expanded_total_alkalinity_uncertainty_mol_L": 0.00002,
        "alkalinity_uncertainty_basis": "synthetic expanded uncertainty",
        "closure_absolute_tolerance_mol_L": 1e-14,
        "constants": {
            "activity_standard_state": "molarity_1_mol_L",
            "temperature_K": 298.15,
            "K1_activity": 10**-6.3,
            "K2_activity": 10**-10.3,
            "Kw_activity": 1e-14,
            "gamma_h_plus": 0.9,
            "gamma_hco3_minus": 0.85,
            "gamma_co3_double_minus": 0.7,
            "gamma_oh_minus": 0.9,
            "constants_provider_id": "synthetic-provider",
            "constants_provider_revision": "revision-1",
            "constants_configuration_digest": "a" * 64,
            "constants_record_digest": "b" * 64,
            "evidence": (EVIDENCE,),
        },
        "measurement_provider_id": "synthetic-laboratory",
        "measurement_provider_revision": "revision-1",
        "measurement_configuration_digest": "c" * 64,
        "measurement_record_digest": "d" * 64,
        "carbonate_only_alkalinity_basis_reviewed": True,
        "ph_activity_scale_reviewed": True,
        "equilibrium_constants_activity_basis_reviewed": True,
        "activity_coefficients_reviewed": True,
        "activity_standard_state_reviewed": True,
        "aqueous_co2_star_definition_reviewed": True,
        "temperature_and_provider_lineage_reviewed": True,
        "alkalinity_measurement_units_and_uncertainty_reviewed": True,
        "numerical_closure_tolerance_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return CarbonateAlkalinitySpeciation.model_validate(value)


def test_closed_form_aqueous_species_match_independent_synthetic_balance():
    model = payload()
    result = carbonate_alkalinity_speciation(model)
    assert result.status == "computed"

    a_h = 10 ** (-model.ph_activity)
    hydrogen = a_h / model.constants.gamma_h_plus
    hydroxide = model.constants.Kw_activity / a_h / model.constants.gamma_oh_minus
    ratio = (
        model.constants.K2_activity
        * model.constants.gamma_hco3_minus
        / (model.constants.gamma_co3_double_minus * a_h)
    )
    bicarbonate = (model.measured_total_alkalinity_mol_L - hydroxide + hydrogen) / (1 + 2 * ratio)
    carbonate = ratio * bicarbonate
    aqueous_co2_star = a_h * model.constants.gamma_hco3_minus * bicarbonate / model.constants.K1_activity

    assert result.values["hydrogen_concentration_mol_L"] == pytest.approx(hydrogen)
    assert result.values["hydroxide_concentration_mol_L"] == pytest.approx(hydroxide)
    assert result.values["carbonate_to_bicarbonate_ratio"] == pytest.approx(ratio)
    assert result.values["bicarbonate_concentration_mol_L"] == pytest.approx(bicarbonate)
    assert result.values["carbonate_concentration_mol_L"] == pytest.approx(carbonate)
    assert result.values["aqueous_co2_star_concentration_mol_L"] == pytest.approx(aqueous_co2_star)
    hco3_u = model.expanded_total_alkalinity_uncertainty_mol_L / (1 + 2 * ratio)
    assert result.values["bicarbonate_expanded_uncertainty_mol_L"] == pytest.approx(hco3_u)
    assert result.values["carbonate_expanded_uncertainty_mol_L"] == pytest.approx(ratio * hco3_u)
    assert result.values["aqueous_co2_star_expanded_uncertainty_mol_L"] == pytest.approx(
        a_h * model.constants.gamma_hco3_minus / model.constants.K1_activity * hco3_u
    )
    assert result.values["expanded_uncertainty_scope"] == "exact_linear_propagation_of_total_alkalinity_only"
    assert result.values["reconstructed_total_alkalinity_mol_L"] == pytest.approx(0.002)
    assert abs(result.values["alkalinity_closure_residual_mol_L"]) <= 1e-14
    assert result.values["gas_liquid_equilibrium_evaluated"] is False
    assert result.values["activity_standard_state"] == "molarity_1_mol_L"
    assert result.values["activity_standard_state_reviewed"] is True
    assert result.values["activity_constants"]["activity_standard_state"] == "molarity_1_mol_L"
    assert result.values["gas_pressure_evaluated"] is False
    assert "pco2_Pa" not in result.values


def test_missing_review_gate_returns_needs_data_with_lineage():
    result = carbonate_alkalinity_speciation(payload(aqueous_co2_star_definition_reviewed=False))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["aqueous_co2_star_definition_reviewed"]
    assert result.values["constants_record_digest"] == "b" * 64
    assert result.values["measurement_record_digest"] == "d" * 64


def test_activity_standard_state_must_be_explicitly_reviewed():
    result = carbonate_alkalinity_speciation(payload(activity_standard_state_reviewed=False))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["activity_standard_state_reviewed"]


def test_non_molarity_standard_state_is_rejected_by_contract():
    data = payload().model_dump(mode="json")
    data["constants"]["activity_standard_state"] = "molality_1_mol_kg"
    with pytest.raises(ValueError, match="Input should be 'molarity_1_mol_L'"):
        CarbonateAlkalinitySpeciation.model_validate(data)


def test_temperature_mismatched_constants_are_not_extrapolated():
    data = payload().model_dump(mode="json")
    data["constants"]["temperature_K"] = 303.15
    result = carbonate_alkalinity_speciation(CarbonateAlkalinitySpeciation.model_validate_json(json.dumps(data)))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["temperature_matched_equilibrium_constants"]


def test_negative_carbonate_alkalinity_numerator_is_out_of_scope():
    result = carbonate_alkalinity_speciation(payload(measured_total_alkalinity_mol_L=-0.001))
    assert result.status == "out_of_scope"
    assert result.values["out_of_scope_reason"] == "nonphysical_carbonate_alkalinity_numerator"
    assert result.values["diagnostics"]["carbonate_alkalinity_numerator_mol_L"] < 0.0


def test_underflowed_hydrogen_activity_is_out_of_scope_without_nonfinite_output():
    result = carbonate_alkalinity_speciation(payload(ph_activity=400.0))
    assert result.status == "out_of_scope"
    assert result.values["out_of_scope_reason"] == "nonfinite_primary_activity_state"
    assert len(result.values["input_digest"]) == 64


def test_contract_and_local_spec_preserve_exact_provider_identity():
    with pytest.raises(ValueError):
        data = payload().model_dump()
        data["constants"]["K1_activity"] = 0.0
        CarbonateAlkalinitySpeciation.model_validate(data)

    spec = specifications()[0]
    assert spec.model_id == "chemistry.carbonate_alkalinity_speciation"
    assert spec.input_type is CarbonateAlkalinitySpeciation
    assert spec.source_ids == ("usgs_advanced_carbonate_speciation",)
    assert spec.units["hydrogen_activity"] == "1"
    assert spec.units["bicarbonate_activity"] == "1"
    assert spec.units["activity_standard_state"] == "1"
    spec.context_validator(
        payload(),
        RunContext(
            asset_id="asset-1",
            location_id="sample-location-1",
            time_basis="sample time",
        ),
    )
    with pytest.raises(ValueError, match="must match run context"):
        spec.context_validator(
            payload(),
            RunContext(asset_id="other", location_id="sample-location-1", time_basis="sample time"),
        )
