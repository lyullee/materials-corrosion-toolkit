"""Explicit CO2-star partition and mol/L-to-mol/m3 mapping for transport boundaries."""

from pydantic import Field

from .contracts import AssessmentResult, Contract, Positive, canonical_digest


class CarbonateBoundarySelection(Contract):
    boundary_id: str = Field(min_length=1)
    hydrated_carbonic_fraction_of_co2star: float = Field(ge=0, le=1)
    water_concentration_mol_m3: Positive
    partition_provider_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    co2star_partition_and_water_basis_reviewed: bool


class CarbonateTransportBoundary(Contract):
    boundary_id: str
    equilibrium_result_sha256: str
    selection_sha256: str
    species_ids: tuple[str, ...]
    concentration_mol_m3: tuple[float, ...]
    temperature_K: Positive
    solvent_composition_sha256: str
    interpretation: str


def carbonate_transport_boundary(
    result: AssessmentResult, selection: CarbonateBoundarySelection
) -> CarbonateTransportBoundary:
    if result.model_id != "chemistry.fixed_fugacity_carbonate_equilibrium" or result.status != "computed":
        raise ValueError("a completed fixed-fugacity carbonate equilibrium result is required")
    if not selection.co2star_partition_and_water_basis_reviewed:
        raise ValueError("CO2-star partition and water concentration require explicit review")
    values = result.values
    fraction = selection.hydrated_carbonic_fraction_of_co2star
    co2star = values["co2star_mol_L"] * 1000.0
    species = ("CO2_aq", "H2O", "H2CO3", "H_plus", "HCO3_minus", "CO3_2minus", "OH_minus")
    concentrations = (
        co2star * (1 - fraction),
        selection.water_concentration_mol_m3,
        co2star * fraction,
        values["h_mol_L"] * 1000.0,
        values["hco3_mol_L"] * 1000.0,
        values["co3_mol_L"] * 1000.0,
        values["oh_mol_L"] * 1000.0,
    )
    if any(value < 0 for value in concentrations):
        raise ValueError("equilibrium concentrations must be nonnegative")
    return CarbonateTransportBoundary(
        boundary_id=selection.boundary_id,
        equilibrium_result_sha256=canonical_digest(result.model_dump(mode="json")),
        selection_sha256=canonical_digest(selection.model_dump(mode="json")),
        species_ids=species,
        concentration_mol_m3=concentrations,
        temperature_K=values["temperature_K"],
        solvent_composition_sha256=values["sample_solvent_composition_sha256"],
        interpretation="Caller-reviewed CO2-star split and explicit water concentration; carbonate-only boundary excludes unreported counterions and does not establish electroneutrality of the complete solution.",
    )
