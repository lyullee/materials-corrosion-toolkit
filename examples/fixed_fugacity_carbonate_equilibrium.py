"""Synthetic closed-form example for fixed-fugacity carbonate equilibrium."""

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.co2_fixed_fugacity_equilibrium import FixedFugacityCarbonateEquilibrium
from matintegrity.registry import default_registry

DIGEST = "a" * 64
EVIDENCE = Evidence(
    source_id="synthetic-carbonate-fixture",
    origin="synthetic",
    citation="Synthetic closed-form values for API demonstration",
)

INPUT = FixedFugacityCarbonateEquilibrium(
    assessment_id="synthetic-co2-equilibrium-01",
    asset_id="synthetic-loop",
    location_id="test-sample-port",
    sample_id="sample-01",
    temperature_K=298.15,
    co2_fugacity_Pa=100_000.0,
    gas_fugacity_provider_id="synthetic-gas-provider",
    gas_fugacity_provider_revision="fixture-1",
    gas_fugacity_configuration_digest=DIGEST,
    gas_fugacity_record_digest=DIGEST,
    sample_solvent_composition_sha256=DIGEST,
    henry={
        "temperature_K": 298.15,
        "coefficient_mol_L_Pa": 1e-7,
        "convention": "aqueous_CO2star_concentration_over_gas_fugacity",
        "solvent_composition_sha256": DIGEST,
        "provider_id": "synthetic-henry-provider",
        "provider_revision": "fixture-1",
        "configuration_digest": DIGEST,
        "record_digest": DIGEST,
        "evidence": (EVIDENCE,),
    },
    constants={
        "temperature_K": 298.15,
        "K1_activity": 1e-6,
        "K2_activity": 1e-9,
        "Kw_activity": 1e-14,
        "gamma_h_plus": 1.0,
        "gamma_hco3_minus": 1.0,
        "gamma_co3_double_minus": 1.0,
        "gamma_oh_minus": 1.0,
        "constants_provider_id": "synthetic-equilibrium-provider",
        "constants_provider_revision": "fixture-1",
        "constants_configuration_digest": DIGEST,
        "constants_record_digest": DIGEST,
        "evidence": (EVIDENCE,),
    },
    measured_total_alkalinity_mol_L=0.102,
    alkalinity_provider_id="synthetic-alkalinity-provider",
    alkalinity_provider_revision="fixture-1",
    alkalinity_configuration_digest=DIGEST,
    alkalinity_record_digest=DIGEST,
    expanded_total_alkalinity_uncertainty_mol_L=0.001,
    alkalinity_uncertainty_basis="synthetic expanded uncertainty with caller-declared coverage convention",
    ph_search_lower=4.0,
    ph_search_upper=10.0,
    ph_tolerance=1e-10,
    alkalinity_closure_tolerance_mol_L=1e-12,
    carbonate_only_alkalinity_reviewed=True,
    gas_fugacity_reviewed=True,
    fixed_fugacity_reservoir_reviewed=True,
    henry_convention_reviewed=True,
    solvent_composition_match_reviewed=True,
    activity_scales_reviewed=True,
    constants_temperature_basis_reviewed=True,
    alkalinity_measurement_reviewed=True,
    gas_equilibrium_review_id="synthetic-gas-review-01",
    henry_record_review_id="synthetic-henry-review-01",
    alkalinity_record_review_id="synthetic-alkalinity-review-01",
    evidence=(EVIDENCE,),
)

if __name__ == "__main__":
    result = default_registry().run(
        "chemistry.fixed_fugacity_carbonate_equilibrium",
        INPUT,
        RunContext(asset_id="synthetic-loop", location_id="test-sample-port", time_basis="sample collection"),
    )
    print(result.model_dump_json(indent=2))
