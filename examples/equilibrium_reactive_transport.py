"""Construct an authored ideal single-solid/variable-area transport request only."""

import json
from pathlib import Path

from matintegrity.equilibrium_reactive_transport import EquilibriumReactiveTransport
from matintegrity.restricted_transport import RestrictedTransportRequest
from matintegrity.single_solid_equilibrium import SingleSolidEquilibrium


def build_request():
    examples = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))
    phase_input = examples["models"]["chemistry.single_solid_precipitation_equilibrium"]
    phases = []
    for index in range(4):
        payload = dict(phase_input, equilibrium_id=f"authored-cell:{index}")
        phases.append(SingleSolidEquilibrium.model_validate_json(json.dumps(payload)))
    phase = phases[0]
    concentrations = tuple(row.initial_concentration_mol_m3 for row in phase.aqueous_species)
    transport = RestrictedTransportRequest(
        simulation_id="authored-variable-area-transport",
        species_ids=tuple(row.species_id for row in phase.aqueous_species),
        length_m=1e-4,
        cell_count=4,
        cell_widths_m=(1e-5, 2e-5, 3e-5, 4e-5),
        cell_cross_section_m2=(1e-7, 8e-8, 6e-8, 4e-8),
        face_cross_section_m2=(1e-7, 9e-8, 7e-8, 5e-8, 4e-8),
        reference_cross_section_m2=1e-7,
        variable_area_one_dimensional_reduction_reviewed=True,
        diffusivity_m2_s=(1e-9, 1e-9),
        initial_concentration_mol_m3=tuple((value,) * 4 for value in concentrations),
        mouth_concentration_mol_m3=concentrations,
        output_times_s=(0.0, 1.0, 2.0),
        reaction_provider_id="authored-zero-homogeneous-source",
        reaction_configuration_sha256="b" * 64,
        geometry_diffusion_reaction_basis_reviewed=True,
        callbacks_cell_locality_reviewed=True,
    )
    return EquilibriumReactiveTransport(
        campaign_id="authored-phase-transport",
        transport=transport,
        initial_cell_equilibria=tuple(phases),
        uniform_temperature_K=phase.temperature_K,
        initial_equilibrium_projection_reviewed=True,
        instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed=True,
        fixed_geometry_and_immobile_solid_basis_reviewed=True,
    )


if __name__ == "__main__":
    # No numerical equilibrium/transport evaluator is called by this entry point.
    print(build_request().model_dump_json(indent=2))
