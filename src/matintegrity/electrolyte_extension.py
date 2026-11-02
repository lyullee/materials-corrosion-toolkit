"""Explicit species extensions for carbonate transport without counterion inference."""

import math

from pydantic import Field, model_validator

from .carbonate_transport_adapter import CarbonateTransportBoundary
from .contracts import Contract, Nonnegative, canonical_digest
from .reaction_network import MassActionNetwork, MassActionReaction


class ElectrolyteSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: int
    elemental_composition: dict[str, int]
    boundary_concentration_mol_m3: Nonnegative
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def elements(self):
        if not self.elemental_composition or any(value < 0 for value in self.elemental_composition.values()):
            raise ValueError("explicit nonnegative elemental composition is required")
        return self


def extend_electrolyte_network(
    network: MassActionNetwork,
    boundary: CarbonateTransportBoundary,
    additions: tuple[ElectrolyteSpecies, ...],
    reactions: tuple[MassActionReaction, ...] = (),
) -> dict:
    if network.species_ids != boundary.species_ids:
        raise ValueError("base network and boundary species order must match")
    if network.elemental_composition is None:
        raise ValueError("base network requires elemental composition for explicit extension")
    added = [row.species_id for row in additions]
    if len(set(added)) != len(added) or set(added) & set(network.species_ids):
        raise ValueError("additional species IDs must be unique and absent from base network")
    species = network.species_ids + tuple(added)
    charges = network.charge_numbers + tuple(row.charge_number for row in additions)
    concentrations = boundary.concentration_mol_m3 + tuple(
        row.boundary_concentration_mol_m3 for row in additions
    )
    elements = network.elemental_composition | {
        row.species_id: row.elemental_composition for row in additions
    }
    extended = MassActionNetwork(
        network_id=network.network_id + ":extended",
        species_ids=species,
        charge_numbers=charges,
        reactions=network.reactions + reactions,
        concentration_activity_approximation_and_rates_reviewed=network.concentration_activity_approximation_and_rates_reviewed,
        elemental_composition=elements,
    )
    charge = math.fsum(z * c for z, c in zip(charges, concentrations, strict=True))
    return dict(
        network=extended.model_dump(mode="json"),
        network_sha256=canonical_digest(extended.model_dump(mode="json")),
        species_ids=species,
        mouth_concentration_mol_m3=concentrations,
        net_molar_charge_mol_m3=charge,
        boundary_sha256=canonical_digest(boundary.model_dump(mode="json")),
        additions_sha256=canonical_digest([row.model_dump(mode="json") for row in additions]),
        basis="Explicit species and reaction extension only; residual charge is reported and no compensating species or concentration is invented.",
    )
