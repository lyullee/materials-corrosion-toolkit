"""Synthetic wiring example for caller-reviewed gamma-corrected rates."""

import numpy as np

from matintegrity.reaction_network import MassActionNetwork, MassActionReaction, mass_action_callback


network = MassActionNetwork(
    network_id="synthetic-A-to-B",
    species_ids=("A", "B"),
    charge_numbers=(0, 0),
    reactions=(
        MassActionReaction(
            reaction_id="A_to_B",
            reactants={"A": 1},
            products={"B": 1},
            forward_rate_constant=0.5,
            reverse_rate_constant=0.1,
            forward_rate_constant_unit="1/s",
            reverse_rate_constant_unit="1/s",
            calibration_sha256="a" * 64,
        ),
    ),
    concentration_activity_approximation_and_rates_reviewed=True,
    elemental_composition={"A": {"X": 1}, "B": {"X": 1}},
)


def synthetic_gamma(time_s: float, concentration_mol_m3: np.ndarray) -> np.ndarray:
    """Synthetic, dimensionless coefficients; not physical activity data."""
    del time_s
    return np.vstack((np.full(concentration_mol_m3.shape[1], 2.0), np.ones(concentration_mol_m3.shape[1])))


synthetic_gamma.provider_id = "synthetic-gamma-provider"
synthetic_gamma.provider_revision = "1"
synthetic_gamma.configuration_sha256 = "b" * 64

reaction_source = mass_action_callback(network, activity_coefficients=synthetic_gamma)
concentration = np.array([[1.0], [0.0]])
print(reaction_source(0.0, concentration))
