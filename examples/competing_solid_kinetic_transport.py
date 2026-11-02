"""Synthetic operator-split transport/kinetics wiring; values are illustrative only."""

from __future__ import annotations

import numpy as np

from matintegrity.multiphase_kinetic_ledger import KineticAqueousSpeciesDefinition, KineticSolidReaction
from matintegrity.multiphase_kinetic_ledger import SolidSaturationRateLaw
from matintegrity.multiphase_kinetic_transport import (
    CellwiseCompetingSolidRateInterval,
    CompetingSolidKineticTransport,
    solve_competing_solid_kinetic_transport,
)
from matintegrity.restricted_transport import RestrictedTransportRequest


transport = RestrictedTransportRequest(
    simulation_id="synthetic-multiphase-transport",
    species_ids=("A2+", "B2-", "C2-"),
    length_m=0.02,
    cell_count=2,
    cell_widths_m=(0.01, 0.01),
    diffusivity_m2_s=(1e-9, 1e-9, 1e-9),
    initial_concentration_mol_m3=((4.0, 4.0), (3.0, 3.0), (3.0, 3.0)),
    mouth_concentration_mol_m3=(4.0, 3.0, 3.0),
    output_times_s=(0.0, 10.0),
    reaction_provider_id="synthetic-zero-homogeneous-reaction",
    reaction_configuration_sha256="1" * 64,
    geometry_diffusion_reaction_basis_reviewed=True,
    callbacks_cell_locality_reviewed=True,
)

campaign = CompetingSolidKineticTransport(
    campaign_id="synthetic-multiphase-kinetic-transport",
    physical_scope_id="synthetic-coupon-domain",
    transport=transport,
    aqueous_species=(
        KineticAqueousSpeciesDefinition(
            species_id="A2+", charge_number=2, elemental_composition={"A": 1}, source_sha256="2" * 64
        ),
        KineticAqueousSpeciesDefinition(
            species_id="B2-", charge_number=-2, elemental_composition={"B": 1}, source_sha256="3" * 64
        ),
        KineticAqueousSpeciesDefinition(
            species_id="C2-", charge_number=-2, elemental_composition={"C": 1}, source_sha256="4" * 64
        ),
    ),
    candidate_solid_phases=(
        KineticSolidReaction(
            solid_species_id="AB(s)",
            precipitation_stoichiometry={"A2+": 1.0, "B2-": 1.0},
            solid_elemental_composition={"A": 1, "B": 1},
            source_sha256="5" * 64,
        ),
        KineticSolidReaction(
            solid_species_id="AC(s)",
            precipitation_stoichiometry={"A2+": 1.0, "C2-": 1.0},
            solid_elemental_composition={"A": 1, "C": 1},
            source_sha256="6" * 64,
        ),
    ),
    initial_solid_inventory_mol_m3_by_phase={"AB(s)": (0.5, 0.5), "AC(s)": (0.0, 0.0)},
    kinetic_intervals=(
        CellwiseCompetingSolidRateInterval(
            interval_id="kinetics-0-10s",
            start_time_s=0.0,
            end_time_s=10.0,
            phase_extent_rate_mol_m3_s_by_cell={"AB(s)": (-0.01, 0.0), "AC(s)": (0.02, 0.01)},
        ),
    ),
    provider_id="synthetic-caller-kinetics",
    provider_revision="0",
    kinetic_configuration_sha256="7" * 64,
    kinetic_parameter_source_sha256="8" * 64,
    temperature_K=298.15,
    phase_stoichiometry_and_solution_volume_reviewed=True,
    caller_rate_law_units_temperature_and_support_reviewed=True,
    transport_then_kinetics_split_order_reviewed=True,
    computational_use_authorized=True,
)


def zero_homogeneous_reaction(_time_s: float, concentration_mol_m3: np.ndarray) -> np.ndarray:
    return np.zeros_like(concentration_mol_m3)


result = solve_competing_solid_kinetic_transport(campaign, reaction=zero_homogeneous_reaction)
print(result)

# Optional saturation-driven variant. The ratios below are fixture outputs from
# a synthetic provider; they are not a speciation or thermodynamic calculation.
saturation_campaign = CompetingSolidKineticTransport.model_validate(
    campaign.model_dump(mode="python")
    | {
        "kinetic_intervals": (),
        "phase_rate_laws": (
            SolidSaturationRateLaw(
                solid_species_id="AB(s)", precipitation_rate_constant_mol_m3_s=0.02,
                precipitation_order=1.0, dissolution_rate_constant_mol_m3_s=0.01,
                dissolution_order=1.0, source_sha256="9" * 64,
            ),
            SolidSaturationRateLaw(
                solid_species_id="AC(s)", precipitation_rate_constant_mol_m3_s=0.01,
                precipitation_order=1.0, dissolution_rate_constant_mol_m3_s=0.005,
                dissolution_order=1.0, source_sha256="a" * 64,
            ),
        ),
        "saturation_ratio_provider_id": "synthetic-saturation-fixture",
        "saturation_ratio_provider_revision": "0",
        "saturation_ratio_provider_configuration_sha256": "b" * 64,
        "saturation_ratio_and_standard_state_reviewed": True,
    }
)


def synthetic_saturation_ratios(
    _global_time_s: float,
    cell_index: int,
    _aqueous_concentration_mol_m3: np.ndarray,
    _solid_inventory_mol_m3_by_phase: dict[str, float],
) -> dict[str, float]:
    return {"AB(s)": 1.2 if cell_index == 0 else 0.8, "AC(s)": 1.1}


synthetic_saturation_ratios.configuration_sha256 = "b" * 64
saturation_result = solve_competing_solid_kinetic_transport(
    saturation_campaign,
    reaction=zero_homogeneous_reaction,
    saturation_ratios=synthetic_saturation_ratios,
)
print(saturation_result)
