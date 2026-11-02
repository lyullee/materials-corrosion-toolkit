"""Synthetic direct example for self-consistent B-dot solid equilibrium."""

from runpy import run_path
from pathlib import Path

from matintegrity.contracts import Evidence
from matintegrity.models.aqueous_activity_iteration import BdotSpeciesParameter
from matintegrity.models.competitive_solid_bdot_iteration import (
    CompetitiveSolidBdotIteration,
    competitive_solid_bdot_self_consistent_equilibrium,
)


equilibrium_input = run_path(str(Path(__file__).with_name("competitive_solid_equilibrium.py")))["inputs"]
equilibrium_input["aqueous_species"][2]["initial_concentration_mol_m3"] = 10.0
species_ids = [row["species_id"] for row in equilibrium_input["aqueous_species"]]
provider_id = "synthetic-bdot-provider"
record_sha = "a" * 64
parameter_rows = tuple(BdotSpeciesParameter(
    species_id=species_id,
    ion_size_angstrom=4.0,
    bdot_kg_per_mol=0.02,
    source_id=provider_id,
    source_record_id=f"synthetic-{species_id}-Bdot",
    source_record_sha256=record_sha,
) for species_id in species_ids)

request = CompetitiveSolidBdotIteration(
    equilibrium=equilibrium_input,
    water_mass_per_solution_volume_kg_L=0.997,
    debye_huckel_A_at_temperature=0.509,
    debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom=0.328,
    parameter_temperature_K=298.15,
    provider_id=provider_id,
    provider_revision="fixture-1",
    configuration_sha256="b" * 64,
    parameter_record_sha256=record_sha,
    species_parameters=parameter_rows,
    evidence=(Evidence(
        source_id=provider_id,
        origin="synthetic",
        citation="Synthetic wiring values only; not a chemical parameter source.",
        sha256=record_sha,
    ),),
    maximum_supported_ionic_strength_mol_kg=1.0,
    charge_balance_tolerance_mol_kg=1e-10,
    maximum_outer_iterations=100,
    log_gamma_tolerance=1e-8,
    damping_fraction=0.5,
    water_mass_conversion_reviewed=True,
    temperature_parameter_and_standard_state_reviewed=True,
    complete_species_parameter_set_and_applicability_reviewed=True,
    competing_solid_bdot_applicability_reviewed=True,
    charge_scope_and_solver_settings_reviewed=True,
)

if __name__ == "__main__":
    print(competitive_solid_bdot_self_consistent_equilibrium(request).model_dump(mode="json"))
