"""Explicit concentration-based mass-action reaction networks for transport callbacks."""

from collections.abc import Callable
import math

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, canonical_digest


class MassActionReaction(Contract):
    reaction_id: str = Field(min_length=1)
    reactants: dict[str, int]
    products: dict[str, int]
    forward_rate_constant: Nonnegative
    reverse_rate_constant: Nonnegative
    forward_rate_constant_unit: str = Field(min_length=1)
    reverse_rate_constant_unit: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def stoichiometry(self):
        if (
            not self.reactants
            or not self.products
            or any(n <= 0 for n in (*self.reactants.values(), *self.products.values()))
        ):
            raise ValueError("reaction sides require positive integer stoichiometry")
        for side, unit in (
            (self.reactants, self.forward_rate_constant_unit),
            (self.products, self.reverse_rate_constant_unit),
        ):
            order = sum(side.values())
            expected = "1/s" if order == 1 else f"(mol/m3)^{1 - order}/s"
            if unit != expected:
                raise ValueError(f"declared concentration rate constant requires unit token {expected}")
        return self


class MassActionNetwork(Contract):
    network_id: str = Field(min_length=1)
    species_ids: tuple[str, ...] = Field(min_length=1)
    charge_numbers: tuple[int, ...]
    reactions: tuple[MassActionReaction, ...] = Field(min_length=1)
    concentration_activity_approximation_and_rates_reviewed: bool
    elemental_composition: dict[str, dict[str, int]] | None = None

    @model_validator(mode="after")
    def species_and_charge(self):
        if len(set(self.species_ids)) != len(self.species_ids) or len(self.charge_numbers) != len(
            self.species_ids
        ):
            raise ValueError("network species and charges must align uniquely")
        charges = dict(zip(self.species_ids, self.charge_numbers, strict=True))
        if self.elemental_composition is not None:
            if set(self.elemental_composition) != set(self.species_ids):
                raise ValueError("elemental composition must cover every species explicitly")
            if any(
                value < 0 for elements in self.elemental_composition.values() for value in elements.values()
            ):
                raise ValueError("element counts cannot be negative")
        if len({r.reaction_id for r in self.reactions}) != len(self.reactions):
            raise ValueError("reaction IDs must be unique")
        for row in self.reactions:
            if not set(row.reactants | row.products) <= set(charges):
                raise ValueError("reaction contains undeclared species")
            if sum(charges[s] * n for s, n in row.reactants.items()) != sum(
                charges[s] * n for s, n in row.products.items()
            ):
                raise ValueError("homogeneous reaction must conserve charge")
            if self.elemental_composition is not None:
                elements = set().union(
                    *(self.elemental_composition[s] for s in row.reactants.keys() | row.products.keys())
                )
                for element in elements:
                    before = sum(
                        n * self.elemental_composition[s].get(element, 0) for s, n in row.reactants.items()
                    )
                    after = sum(
                        n * self.elemental_composition[s].get(element, 0) for s, n in row.products.items()
                    )
                    if before != after:
                        raise ValueError(
                            f"reaction {row.reaction_id} does not conserve declared element {element}"
                        )
        return self


def mass_action_callback(
    network: MassActionNetwork,
    *,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
) -> Callable[[float, np.ndarray], np.ndarray]:
    """Build a homogeneous reaction source with an optional reviewed gamma correction.

    When enabled, each supplied concentration is multiplied by its caller-provided
    species activity coefficient before applying the existing concentration-basis
    rate constants. This is an explicit effective-concentration kinetic model; it
    does not infer equilibrium activities, standard-state conversions, or rates.
    """
    if not network.concentration_activity_approximation_and_rates_reviewed:
        raise ValueError("concentration approximation and reaction rates require review")
    lookup = {name: i for i, name in enumerate(network.species_ids)}

    def source(time: float, concentrations: np.ndarray) -> np.ndarray:
        values = np.asarray(concentrations, dtype=float)
        if (
            isinstance(time, bool)
            or not isinstance(time, (int, float, np.number))
            or not math.isfinite(float(time))
            or time < 0
        ):
            raise ValueError("reaction-network time must be finite and nonnegative")
        if (
            values.ndim != 2
            or values.shape[0] != len(lookup)
            or not np.isfinite(values).all()
            or np.any(values < 0)
        ):
            raise ValueError("network concentrations must be finite nonnegative species-by-cell arrays")
        if activity_coefficients is not None:
            gamma = np.asarray(activity_coefficients(float(time), values), dtype=float)
            if gamma.shape != values.shape or not np.isfinite(gamma).all() or np.any(gamma <= 0.0):
                raise ValueError("activity coefficients must be finite positive species-by-cell values")
            values = values * gamma
            if not np.isfinite(values).all():
                raise ValueError("activity-corrected effective concentrations exceed finite numeric support")
        output = np.zeros_like(values)
        for row in network.reactions:
            forward = np.full(values.shape[1], row.forward_rate_constant)
            reverse = np.full(values.shape[1], row.reverse_rate_constant)
            for species, power in row.reactants.items():
                forward *= values[lookup[species]] ** power
            for species, power in row.products.items():
                reverse *= values[lookup[species]] ** power
            extent = forward - reverse
            for species in row.reactants.keys() | row.products.keys():
                output[lookup[species]] += (
                    row.products.get(species, 0) - row.reactants.get(species, 0)
                ) * extent
        if not np.isfinite(output).all():
            raise ValueError("reaction source exceeds numerical range")
        return output

    source.configuration_sha256 = canonical_digest(network.model_dump(mode="json"))
    source.provider_id = "matintegrity.mass_action_network"
    source.provider_revision = "1"
    source.network_id = network.network_id
    source.species_ids = network.species_ids
    source.activity_correction_enabled = activity_coefficients is not None
    source.activity_provider_id = getattr(activity_coefficients, "provider_id", None)
    source.activity_provider_revision = getattr(activity_coefficients, "provider_revision", None)
    source.activity_configuration_sha256 = getattr(activity_coefficients, "configuration_sha256", None)
    return source
