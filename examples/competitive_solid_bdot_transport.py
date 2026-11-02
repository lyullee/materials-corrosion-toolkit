"""Synthetic contract example for B-dot solid projections during transport."""

from pathlib import Path
from runpy import run_path

from matintegrity.contracts import Evidence
from matintegrity.models.aqueous_activity_iteration import BdotSpeciesParameter
from matintegrity.models.competitive_solid_bdot_iteration import CompetitiveSolidBdotIteration
from matintegrity.multiphase_equilibrium_transport import CompetitiveSolidEquilibriumTransport


base = run_path(str(Path(__file__).with_name("competitive_solid_equilibrium_transport.py")))
source_request = base["request"]
provider_id = "synthetic-bdot-provider"
configuration_sha = "a" * 64
parameter_sha = "b" * 64
transport = source_request.transport.model_copy(update={
    "activity_provider_id": provider_id,
    "activity_configuration_sha256": configuration_sha,
})
cells = []
for index, template in enumerate(source_request.initial_cell_equilibria):
    parameters = tuple(BdotSpeciesParameter(
        species_id=species.species_id,
        ion_size_angstrom=4.0,
        bdot_kg_per_mol=0.02,
        source_id=provider_id,
        source_record_id=f"synthetic-{species.species_id}-Bdot",
        source_record_sha256=parameter_sha,
    ) for species in template.equilibrium.aqueous_species)
    cells.append(CompetitiveSolidBdotIteration(
        equilibrium=template.equilibrium.model_copy(update={"equilibrium_id": f"synthetic-Bdot-cell-{index}"}),
        water_mass_per_solution_volume_kg_L=template.water_mass_per_solution_volume_kg_L,
        debye_huckel_A_at_temperature=0.509,
        debye_huckel_B_at_temperature_sqrt_kg_mol_per_angstrom=0.328,
        parameter_temperature_K=source_request.uniform_temperature_K,
        provider_id=provider_id,
        provider_revision="fixture-1",
        configuration_sha256=configuration_sha,
        parameter_record_sha256=parameter_sha,
        species_parameters=parameters,
        evidence=(Evidence(source_id=provider_id, origin="synthetic", citation="Synthetic wiring values only; not a chemical parameter source.", sha256=parameter_sha),),
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
    ))

request = CompetitiveSolidEquilibriumTransport(
    campaign_id="synthetic-Bdot-solid-transport",
    physical_scope_id="synthetic-fixture-only",
    transport=transport,
    initial_cell_equilibria=tuple(cells),
    uniform_temperature_K=source_request.uniform_temperature_K,
    initial_equilibrium_projection_reviewed=True,
    instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed=True,
    fixed_geometry_and_immobile_solid_basis_reviewed=True,
    transport_activity_to_phase_davies_mapping_reviewed=True,
)

if __name__ == "__main__":
    # Contract-only example: no transport or equilibrium calculation is executed.
    print(request.model_dump_json(indent=2))
