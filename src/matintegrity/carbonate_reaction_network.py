"""Explicit-water carbonate reaction assembly using caller-supplied kinetic constants."""

from pydantic import Field

from .contracts import Contract, Nonnegative
from .reaction_network import MassActionNetwork, MassActionReaction


class CarbonateReactionConstants(Contract):
    network_id: str = Field(min_length=1)
    # Order: hydration, first acid dissociation, bicarbonate dissociation, water dissociation.
    forward_rate_constants: tuple[Nonnegative, Nonnegative, Nonnegative, Nonnegative]
    reverse_rate_constants: tuple[Nonnegative, Nonnegative, Nonnegative, Nonnegative]
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    explicit_water_concentration_rate_basis_reviewed: bool


def build_carbonate_reaction_network(request: CarbonateReactionConstants) -> MassActionNetwork:
    definitions = (
        ("co2_hydration", {"CO2_aq": 1, "H2O": 1}, {"H2CO3": 1}),
        ("carbonic_dissociation", {"H2CO3": 1}, {"H_plus": 1, "HCO3_minus": 1}),
        ("bicarbonate_dissociation", {"HCO3_minus": 1}, {"H_plus": 1, "CO3_2minus": 1}),
        ("water_dissociation", {"H2O": 1}, {"H_plus": 1, "OH_minus": 1}),
    )
    reactions = []
    for index, (name, reactants, products) in enumerate(definitions):

        def unit(side):
            order = sum(side.values())
            return "1/s" if order == 1 else f"(mol/m3)^{1 - order}/s"

        reactions.append(
            MassActionReaction(
                reaction_id=name,
                reactants=reactants,
                products=products,
                forward_rate_constant=request.forward_rate_constants[index],
                reverse_rate_constant=request.reverse_rate_constants[index],
                forward_rate_constant_unit=unit(reactants),
                reverse_rate_constant_unit=unit(products),
                calibration_sha256=request.calibration_sha256,
            )
        )
    return MassActionNetwork(
        network_id=request.network_id,
        species_ids=("CO2_aq", "H2O", "H2CO3", "H_plus", "HCO3_minus", "CO3_2minus", "OH_minus"),
        charge_numbers=(0, 0, 0, 1, -1, -2, -1),
        reactions=tuple(reactions),
        concentration_activity_approximation_and_rates_reviewed=request.explicit_water_concentration_rate_basis_reviewed,
        elemental_composition={
            "CO2_aq": {"C": 1, "O": 2},
            "H2O": {"H": 2, "O": 1},
            "H2CO3": {"H": 2, "C": 1, "O": 3},
            "H_plus": {"H": 1},
            "HCO3_minus": {"H": 1, "C": 1, "O": 3},
            "CO3_2minus": {"C": 1, "O": 3},
            "OH_minus": {"H": 1, "O": 1},
        },
    )
