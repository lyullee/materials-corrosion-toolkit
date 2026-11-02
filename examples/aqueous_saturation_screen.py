"""Synthetic candidate-solid saturation-screen example; values are illustrative."""

from matintegrity.models.aqueous_saturation_screening import (
    AqueousSaturationScreen,
    CandidateSolid,
    SaturationScreenSpecies,
    SaturationScreenTerm,
    aqueous_saturation_screen,
    screen_mass_action_calculation,
)
from matintegrity.contracts import Calculation, Evidence


request = AqueousSaturationScreen(
    assessment_id="synthetic-screen-001",
    solution_id="synthetic-solution-001",
    temperature_K=298.15,
    activity_standard_state="dimensionless molarity standard state declared by the example",
    species=(
        SaturationScreenSpecies(
            species_id="M2+",
            dimensionless_activity=1e-3,
            log10_activity_absolute_bound=0.05,
        ),
        SaturationScreenSpecies(
            species_id="A-",
            dimensionless_activity=2e-3,
            log10_activity_absolute_bound=0.02,
        ),
    ),
    candidate_solids=(
        CandidateSolid(
            solid_id="MA2-alpha",
            log10_solubility_product=-8.5,
            log10_solubility_product_absolute_bound=0.1,
            solubility_record_id="synthetic-ksp-alpha",
            solubility_evidence_source_id="synthetic-example",
            terms=(
                SaturationScreenTerm(species_id="M2+", stoichiometric_exponent=1),
                SaturationScreenTerm(species_id="A-", stoichiometric_exponent=2),
            ),
        ),
        CandidateSolid(
            solid_id="MA2-beta",
            log10_solubility_product=-7.0,
            log10_solubility_product_absolute_bound=0.1,
            solubility_record_id="synthetic-ksp-beta",
            solubility_evidence_source_id="synthetic-example",
            terms=(
                SaturationScreenTerm(species_id="M2+", stoichiometric_exponent=1),
                SaturationScreenTerm(species_id="A-", stoichiometric_exponent=2),
            ),
        ),
    ),
    activity_state_provider_id="synthetic-input",
    activity_state_digest="1" * 64,
    solubility_data_provider_id="synthetic-input",
    solubility_data_digest="2" * 64,
    complete_species_inventory_reviewed=True,
    compatible_standard_states_reviewed=True,
    equilibrium_constants_temperature_reviewed=True,
    activity_interval_bounds_reviewed=True,
    solubility_product_interval_bounds_reviewed=True,
    evidence=(Evidence(source_id="synthetic-example", origin="synthetic", citation="Synthetic demonstration only", license_id="CC0-1.0"),),
)

print(aqueous_saturation_screen(request).model_dump_json(indent=2))

# A caller can also compose a computed upstream activity result with external
# log-activity bounds. This result is synthetic and demonstrates the contract;
# it is not a chemistry calculation or a measured uncertainty estimate.
synthetic_activity_result = Calculation(
    status="computed",
    values={
        "temperature_K": 298.15,
        "activity_standard_state": "dimensionless molarity standard state declared by the example",
        "species": [
            {"species_id": "M2+", "dimensionless_activity": 1e-3},
            {"species_id": "A-", "dimensionless_activity": 2e-3},
        ],
        "activity_provider_id": "synthetic-upstream-activity",
        "activity_provider_revision": "example-1",
        "activity_record_digest": "3" * 64,
    },
)
composed = screen_mass_action_calculation(
    synthetic_activity_result,
    assessment_id="synthetic-composed-screen-001",
    solution_id="synthetic-solution-001",
    candidate_solids=request.candidate_solids,
    activity_log10_absolute_bounds={"M2+": 0.05, "A-": 0.02},
    solubility_data_provider_id="synthetic-solubility-provider",
    solubility_data_digest="2" * 64,
    complete_species_inventory_reviewed=True,
    compatible_standard_states_reviewed=True,
    equilibrium_constants_temperature_reviewed=True,
    activity_interval_bounds_reviewed=True,
    solubility_product_interval_bounds_reviewed=True,
    evidence=request.evidence,
)
print(composed.model_dump_json(indent=2))
