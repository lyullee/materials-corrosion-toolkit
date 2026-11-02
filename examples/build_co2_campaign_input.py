"""Build an authored synthetic nested request without running transport or corrosion solvers."""

import json
from pathlib import Path

from matintegrity.carbonate_reaction_network import (
    CarbonateReactionConstants,
    build_carbonate_reaction_network,
)
from matintegrity.carbonate_transport_adapter import CarbonateTransportBoundary
from matintegrity.co2_corrosion_campaign import Co2CorrosionCampaign
from matintegrity.dissolution_adapter import DissolutionSelection, WallMetalLossSelection
from matintegrity.electrochemical_transport import assemble_electrochemical_transport
from matintegrity.electrode_kinetics import ButlerVolmerReaction
from matintegrity.electrolyte_extension import ElectrolyteSpecies, extend_electrolyte_network
from matintegrity.equilibrium_reactive_transport import EquilibriumReactiveTransport
from matintegrity.reaction_network import MassActionNetwork
from matintegrity.single_solid_equilibrium import SingleSolidEquilibrium


def build_request(include_single_solid_phase=False, include_wall_loss=False):
    network = build_carbonate_reaction_network(
        CarbonateReactionConstants(
            network_id="synthetic-carbonate",
            forward_rate_constants=(1e-8, 1e-8, 1e-8, 1e-8),
            reverse_rate_constants=(1e-8, 1e-8, 1e-8, 1e-8),
            calibration_sha256="a" * 64,
            explicit_water_concentration_rate_basis_reviewed=True,
        )
    )
    boundary = CarbonateTransportBoundary(
        boundary_id="synthetic-boundary",
        equilibrium_result_sha256="b" * 64,
        selection_sha256="c" * 64,
        species_ids=network.species_ids,
        concentration_mol_m3=(1.0, 55000.0, 0.01, 0.001, 0.001, 1e-6, 1e-6),
        temperature_K=298.15,
        solvent_composition_sha256="d" * 64,
        interpretation="Authored nonequilibrium example only; no experimental equilibrium or material calibration claimed.",
    )
    additions = (
        ElectrolyteSpecies(
            species_id="Fe_2plus",
            charge_number=2,
            elemental_composition={"Fe": 1},
            boundary_concentration_mol_m3=0.001,
            source_sha256="e" * 64,
        ),
        ElectrolyteSpecies(
            species_id="H2_aq",
            charge_number=0,
            elemental_composition={"H": 2},
            boundary_concentration_mol_m3=0.01,
            source_sha256="f" * 64,
        ),
    )
    extension = extend_electrolyte_network(network, boundary, additions)
    network = MassActionNetwork.model_validate_json(json.dumps(extension["network"]))
    common = dict(
        exchange_current_density_A_m2=1e-6,
        electron_count=2,
        anodic_transfer_coefficient=0.5,
        cathodic_transfer_coefficient=0.5,
        temperature_K=298.15,
        minimum_overpotential_V=-0.8,
        maximum_overpotential_V=0.8,
        calibration_sha256="a" * 64,
        calibration_and_reaction_direction_reviewed=True,
    )
    surfaces = (
        ButlerVolmerReaction(
            reaction_id="synthetic-iron",
            equilibrium_potential_V=-0.4,
            stoichiometric_species_coefficients={"Fe_2plus": 1.0},
            **common,
        ),
        ButlerVolmerReaction(
            reaction_id="synthetic-hydrogen",
            equilibrium_potential_V=0.0,
            stoichiometric_species_coefficients={"H_plus": 2.0, "H2_aq": -1.0},
            **common,
        ),
    )
    wall_surfaces = (
        (
            ButlerVolmerReaction(
                reaction_id="synthetic-wall-iron",
                equilibrium_potential_V=-0.4,
                stoichiometric_species_coefficients={"Fe_2plus": 1.0},
                **common,
            ),
        )
        if include_wall_loss
        else ()
    )
    mouth = tuple(extension["mouth_concentration_mol_m3"])
    electrochemistry = assemble_electrochemical_transport(
        campaign_id="synthetic-electrochemistry",
        network=network,
        transport_parameters=dict(
            simulation_id="synthetic-transport",
            length_m=1e-4,
            cell_count=4,
            diffusivity_m2_s=tuple(1e-9 for _ in mouth),
            initial_concentration_mol_m3=tuple(tuple(value for _ in range(4)) for value in mouth),
            mouth_concentration_mol_m3=mouth,
            output_times_s=(0.0, 1e-5, 1e-4),
            geometry_diffusion_reaction_basis_reviewed=True,
            prescribed_potential_V=(0.0, 0.0, 0.0, 0.0, 0.0),
            migration_temperature_K=298.15,
            prescribed_field_migration_reviewed=True,
            tip_surface_flux_basis_reviewed=True,
            cell_cross_section_m2=tuple(1e-6 for _ in range(4)) if include_wall_loss else None,
            face_cross_section_m2=tuple(1e-6 for _ in range(5)) if include_wall_loss else None,
            reference_cross_section_m2=1e-6 if include_wall_loss else None,
            variable_area_one_dimensional_reduction_reviewed=include_wall_loss,
            wall_area_per_volume_m2_m3=tuple(1e4 for _ in range(4)) if include_wall_loss else None,
            wall_surface_flux_basis_reviewed=include_wall_loss,
            callbacks_cell_locality_reviewed=True,
        ),
        surface_reactions=surfaces,
        surface_provider_id="synthetic-surface",
        metal_potential_V=-0.2,
        common_potential_reference_id="authored-reference",
        surface_composition_and_reference_reviewed=True,
        free_corrosion_zero_current_reviewed=True,
        wall_surface_reactions=wall_surfaces,
        wall_surface_provider_id="synthetic-wall-provider" if include_wall_loss else None,
        wall_surface_composition_and_reference_reviewed=include_wall_loss,
        equipotential_wall_and_metal_potential_reviewed=include_wall_loss,
    )
    selection = DissolutionSelection(
        history_id="synthetic-loss",
        surface_reaction_id="synthetic-iron",
        metal_species_id="Fe_2plus",
        electron_count=2,
        metal_molar_mass_kg_mol=0.055845,
        metal_density_kg_m3=7800.0,
        dissolution_current_efficiency=1.0,
        selected_reaction_is_dissolution_only_reviewed=True,
        uniform_recession_and_output_clock_resolution_reviewed=True,
        current_component="gross_anodic",
    )
    phase_transport = None
    if include_single_solid_phase:
        authored = json.loads(Path(__file__).with_name("model_inputs.json").read_text(encoding="utf-8"))[
            "models"
        ]["chemistry.single_solid_precipitation_equilibrium"]
        initial = dict(
            zip(
                electrochemistry.transport.species_ids,
                electrochemistry.transport.initial_concentration_mol_m3,
                strict=True,
            )
        )
        phases = []
        for cell in range(electrochemistry.transport.cell_count):
            payload = json.loads(json.dumps(authored))
            payload["equilibrium_id"] = f"authored-CO2-phase-cell:{cell}"
            payload["dimensionless_solubility_product"] = 1e-18
            for species in payload["aqueous_species"]:
                species["initial_concentration_mol_m3"] = initial[species["species_id"]][cell]
            phases.append(SingleSolidEquilibrium.model_validate_json(json.dumps(payload)))
        phase_transport = EquilibriumReactiveTransport(
            campaign_id="authored-CO2-phase-splitting",
            transport=electrochemistry.transport,
            initial_cell_equilibria=tuple(phases),
            uniform_temperature_K=boundary.temperature_K,
            initial_equilibrium_projection_reviewed=True,
            instantaneous_phase_equilibrium_and_output_clock_splitting_reviewed=True,
            fixed_geometry_and_immobile_solid_basis_reviewed=True,
        )
    wall_loss_selection = (
        WallMetalLossSelection(
            selection_id="synthetic-wall-iron-loss",
            metal_species_id="Fe_2plus",
            metal_molar_mass_kg_mol=0.055845,
            metal_density_kg_m3=7800.0,
            reference_cross_section_m2=1e-6,
            boundary_species_is_one_metal_atom_per_mole_reviewed=True,
            wall_flux_is_signed_dissolution_or_redeposition_reviewed=True,
            reactive_wall_and_reference_areas_reviewed=True,
            area_average_recession_interpretation_reviewed=True,
        )
        if include_wall_loss
        else None
    )
    return Co2CorrosionCampaign(
        campaign_id="synthetic-co2-campaign",
        carbonate_boundary=boundary,
        electrochemistry=electrochemistry,
        dissolution=selection,
        wall_metal_loss_selection=wall_loss_selection,
        phase_transport=phase_transport,
        carbonate_species_boundary_and_mechanism_reviewed=True,
    )


if __name__ == "__main__":
    print(build_request(include_wall_loss=True).model_dump_json(indent=2))
