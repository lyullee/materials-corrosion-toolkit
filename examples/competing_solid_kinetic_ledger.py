"""Synthetic contract example; rates are illustrative caller inputs, not fitted data."""

from matintegrity.multiphase_kinetic_ledger import (
    CompetingSolidKineticInterval,
    CompetingSolidKineticLedger,
    KineticAqueousSpecies,
    KineticSolidPhase,
    evaluate_competing_solid_kinetic_ledger,
)


request = CompetingSolidKineticLedger(
    assessment_id="synthetic-solid-rate-ledger",
    physical_scope_id="synthetic-batch-01",
    provider_id="illustrative-rate-provider",
    provider_revision="0",
    kinetic_configuration_sha256="1" * 64,
    temperature_K=298.15,
    kinetic_parameter_source_sha256="2" * 64,
    aqueous_species=(
        KineticAqueousSpecies(
            species_id="A2+",
            initial_concentration_mol_m3=4.0,
            charge_number=2,
            elemental_composition={"A": 1},
            source_sha256="3" * 64,
        ),
        KineticAqueousSpecies(
            species_id="B2-",
            initial_concentration_mol_m3=3.0,
            charge_number=-2,
            elemental_composition={"B": 1},
            source_sha256="4" * 64,
        ),
        KineticAqueousSpecies(
            species_id="C2-",
            initial_concentration_mol_m3=3.0,
            charge_number=-2,
            elemental_composition={"C": 1},
            source_sha256="5" * 64,
        ),
    ),
    candidate_solid_phases=(
        KineticSolidPhase(
            solid_species_id="AB(s)",
            precipitation_stoichiometry={"A2+": 1.0, "B2-": 1.0},
            solid_elemental_composition={"A": 1, "B": 1},
            initial_solid_moles_per_solution_volume_mol_m3=0.5,
            source_sha256="6" * 64,
        ),
        KineticSolidPhase(
            solid_species_id="AC(s)",
            precipitation_stoichiometry={"A2+": 1.0, "C2-": 1.0},
            solid_elemental_composition={"A": 1, "C": 1},
            initial_solid_moles_per_solution_volume_mol_m3=0.0,
            source_sha256="7" * 64,
        ),
    ),
    intervals=(
        CompetingSolidKineticInterval(
            interval_id="interval-1",
            start_time_s=0.0,
            end_time_s=10.0,
            phase_extent_rate_mol_m3_s={"AB(s)": -0.01, "AC(s)": 0.02},
        ),
    ),
    phase_stoichiometry_and_solution_volume_reviewed=True,
    caller_rate_law_units_temperature_and_support_reviewed=True,
    dissolution_then_precipitation_split_order_reviewed=True,
    computational_use_authorized=True,
)

result = evaluate_competing_solid_kinetic_ledger(request)
print(result.model_dump(mode="json"))
