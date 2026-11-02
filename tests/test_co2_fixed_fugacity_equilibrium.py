import math

import pytest

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.carbonate_alkalinity import CarbonateActivityConstants
from matintegrity.models.co2_fixed_fugacity_equilibrium import (
    Co2HenrySolubilityRecord,
    FixedFugacityCarbonateEnsemble,
    FixedFugacityCarbonateEquilibrium,
    FixedFugacityCarbonateScenario,
    fixed_fugacity_carbonate_equilibrium,
    fixed_fugacity_carbonate_scenario_ensemble,
)
from matintegrity.registry import default_registry


def _evidence(source_id):
    return Evidence(source_id=source_id, origin="synthetic", citation="Synthetic closed-form fixture")


def _input(**changes):
    digest = "a" * 64
    constants = CarbonateActivityConstants(
        temperature_K=298.15,
        K1_activity=1e-6,
        K2_activity=1e-9,
        Kw_activity=1e-14,
        gamma_h_plus=1.0,
        gamma_hco3_minus=1.0,
        gamma_co3_double_minus=1.0,
        gamma_oh_minus=1.0,
        constants_provider_id="synthetic-equilibrium-provider",
        constants_provider_revision="fixture-1",
        constants_configuration_digest=digest,
        constants_record_digest=digest,
        evidence=(_evidence("synthetic-carbonate-constants"),),
    )
    henry = Co2HenrySolubilityRecord(
        temperature_K=298.15,
        coefficient_mol_L_Pa=1e-7,
        convention="aqueous_CO2star_concentration_over_gas_fugacity",
        solvent_composition_sha256=digest,
        provider_id="synthetic-henry-provider",
        provider_revision="fixture-1",
        configuration_digest=digest,
        record_digest=digest,
        evidence=(_evidence("synthetic-henry-coefficient"),),
    )
    payload = dict(
        assessment_id="synthetic-co2-equilibrium-01",
        asset_id="synthetic-loop",
        location_id="test-sample-port",
        sample_id="sample-01",
        temperature_K=298.15,
        co2_fugacity_Pa=100_000.0,
        gas_fugacity_provider_id="synthetic-gas-provider",
        gas_fugacity_provider_revision="fixture-1",
        gas_fugacity_configuration_digest=digest,
        gas_fugacity_record_digest=digest,
        sample_solvent_composition_sha256=digest,
        henry=henry,
        constants=constants,
        measured_total_alkalinity_mol_L=0.102,
        alkalinity_provider_id="synthetic-alkalinity-provider",
        alkalinity_provider_revision="fixture-1",
        alkalinity_configuration_digest=digest,
        alkalinity_record_digest=digest,
        expanded_total_alkalinity_uncertainty_mol_L=0.001,
        alkalinity_uncertainty_basis="synthetic expanded uncertainty, k declared by fixture owner",
        ph_search_lower=4.0,
        ph_search_upper=10.0,
        ph_tolerance=1e-10,
        alkalinity_closure_tolerance_mol_L=1e-12,
        maximum_iterations=128,
        carbonate_only_alkalinity_reviewed=True,
        gas_fugacity_reviewed=True,
        fixed_fugacity_reservoir_reviewed=True,
        henry_convention_reviewed=True,
        solvent_composition_match_reviewed=True,
        activity_scales_reviewed=True,
        constants_temperature_basis_reviewed=True,
        alkalinity_measurement_reviewed=True,
        gas_equilibrium_review_id="review-gas-01",
        henry_record_review_id="review-henry-01",
        alkalinity_record_review_id="review-alkalinity-01",
        evidence=(_evidence("synthetic-equilibrium-calculation"),),
    )
    payload.update(changes)
    return FixedFugacityCarbonateEquilibrium(**payload)


def test_fixed_fugacity_solution_reproduces_closed_form_carbonate_state():
    result = fixed_fugacity_carbonate_equilibrium(_input())
    assert result.status == "computed"
    assert result.values["ph_activity"] == pytest.approx(7.0, abs=1e-9)
    assert result.values["co2star_mol_L"] == pytest.approx(0.01)
    assert result.values["hco3_mol_L"] == pytest.approx(0.1)
    assert result.values["co3_mol_L"] == pytest.approx(0.001)
    assert result.values["calculated_total_alkalinity_mol_L"] == pytest.approx(0.102, abs=1e-12)
    assert result.values["expanded_pH_uncertainty_from_alkalinity_only"] == pytest.approx(
        0.001 / (math.log(10.0) * 0.1040002)
    )


def test_missing_physical_review_returns_needs_data_without_a_solution():
    result = fixed_fugacity_carbonate_equilibrium(_input(gas_fugacity_reviewed=False))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["gas_fugacity_reviewed"]


def test_temperature_mismatch_and_unbracketed_alkalinity_are_not_extrapolated():
    mismatch = _input(temperature_K=303.15)
    temperature_result = fixed_fugacity_carbonate_equilibrium(mismatch)
    assert temperature_result.status == "needs_data"
    assert "temperature_matched_Henry_solubility_record" in temperature_result.values["missing_reviews"]

    unbracketed = fixed_fugacity_carbonate_equilibrium(
        _input(measured_total_alkalinity_mol_L=1.0, ph_search_lower=6.9, ph_search_upper=7.1)
    )
    assert unbracketed.status == "out_of_scope"
    assert unbracketed.values["reason"] == "measured_alkalinity_not_bracketed"


def test_henry_coefficient_must_match_sample_solvent_digest():
    result = fixed_fugacity_carbonate_equilibrium(_input(sample_solvent_composition_sha256="b" * 64))
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["Henry_record_matches_sample_solvent_composition"]


def test_registered_json_api_preserves_review_and_provider_lineage():
    payload = _input().model_dump_json()
    result = default_registry().run_json(
        "chemistry.fixed_fugacity_carbonate_equilibrium",
        payload,
        RunContext(asset_id="synthetic-loop", location_id="test-sample-port", time_basis="sample collection"),
    )
    assert result.values["henry_record_review_id"] == "review-henry-01"
    assert result.values["constants_record_digest"] == "a" * 64
    assert result.probability_semantics == {}


def _ensemble(scenarios, **updates):
    payload = dict(
        ensemble_id="synthetic-co2-ensemble",
        asset_id="synthetic-loop",
        location_id="test-sample-port",
        physical_scope_id="sample-volume-01",
        sample_id="sample-01",
        exposure_interval_id="hold-01",
        source_group_id="synthetic-study-01",
        scenarios=tuple(scenarios),
        scenario_weights_reviewed=True,
        common_sample_scope_reviewed=True,
        weight_meaning="caller_distribution_weights_model_implied_uncertainty",
        input_distribution_id="synthetic-joint-input-draws",
        input_distribution_digest="b" * 64,
        evidence=(_evidence("synthetic-ensemble"),),
    )
    payload.update(updates)
    return FixedFugacityCarbonateEnsemble(**payload)


def test_weighted_scenario_ensemble_preserves_rows_and_computes_weighted_summaries():
    low = _input(measured_total_alkalinity_mol_L=0.101)
    high = _input(measured_total_alkalinity_mol_L=0.103)
    ensemble = _ensemble(
        (
            FixedFugacityCarbonateScenario(scenario_id="low", normalized_weight=0.25, equilibrium=low),
            FixedFugacityCarbonateScenario(scenario_id="high", normalized_weight=0.75, equilibrium=high),
        )
    )
    result = fixed_fugacity_carbonate_scenario_ensemble(ensemble)
    assert result.status == "computed"
    assert result.values["aggregate_returned"] is True
    assert result.values["scenario_count"] == 2
    assert len(result.values["scenario_results"]) == 2
    assert result.values["summaries"]["ph_activity"]["weighted_mean"] > 7.0
    assert result.values["event_probability_inferred"] is False
    assert result.values["corrosion_rate_inferred"] is False


def test_scenario_ensemble_with_any_unresolved_row_returns_no_partial_aggregate():
    valid = _input(measured_total_alkalinity_mol_L=0.101)
    outside = _input(measured_total_alkalinity_mol_L=1.0, ph_search_lower=6.9, ph_search_upper=7.1)
    result = fixed_fugacity_carbonate_scenario_ensemble(
        _ensemble(
            (
                FixedFugacityCarbonateScenario(scenario_id="valid", normalized_weight=0.5, equilibrium=valid),
                FixedFugacityCarbonateScenario(
                    scenario_id="outside", normalized_weight=0.5, equilibrium=outside
                ),
            )
        )
    )
    assert result.status == "needs_data"
    assert result.values["failed_scenario_ids"] == ["outside"]
    assert result.values["aggregate_returned"] is False


def test_scenario_ensemble_requires_normalized_weights_and_common_scope():
    case = _input()
    with pytest.raises(ValueError, match="normalized"):
        _ensemble(
            (
                FixedFugacityCarbonateScenario(scenario_id="a", normalized_weight=0.4, equilibrium=case),
                FixedFugacityCarbonateScenario(scenario_id="b", normalized_weight=0.4, equilibrium=case),
            )
        )
    ensemble = _ensemble(
        (FixedFugacityCarbonateScenario(scenario_id="a", normalized_weight=1.0, equilibrium=case),),
        common_sample_scope_reviewed=False,
    )
    result = fixed_fugacity_carbonate_scenario_ensemble(ensemble)
    assert result.status == "needs_data"
    assert result.values["missing_reviews"] == ["common_sample_scope_reviewed"]
