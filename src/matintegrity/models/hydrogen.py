"""Local, single-occupancy hydrogen partition with replaceable trap evidence."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

R_J_mol_K = 8.31446261815324


class HydrogenTrapPopulation(Contract):
    trap_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    site_density_mol_m3: Positive
    binding_energy_J_mol: Nonnegative
    maximum_supported_occupancy: float = Field(gt=0, le=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HydrogenPartition(Contract):
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    total_hydrogen_atoms_mol_m3: Nonnegative
    lattice_site_density_mol_m3: Positive
    lattice_diffusivity_m2_s: Positive
    temperature_K: Positive
    maximum_supported_lattice_occupancy: float = Field(gt=0, le=1)
    traps: list[HydrogenTrapPopulation] = Field(max_length=100)
    local_equilibrium_confirmed: bool
    independent_single_occupancy_sites_confirmed: bool
    fixed_trap_population_and_uniform_temperature_confirmed: bool

    @model_validator(mode="after")
    def unique(self):
        if len({t.trap_id for t in self.traps}) != len(self.traps):
            raise ValueError("distinct trap population IDs are required")
        return self


def partition(x: HydrogenPartition) -> Calculation:
    from scipy.optimize import brentq
    from scipy.special import expit, log_expit, logsumexp

    if not all(
        (
            x.local_equilibrium_confirmed,
            x.independent_single_occupancy_sites_confirmed,
            x.fixed_trap_population_and_uniform_temperature_confirmed,
        )
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Review fast local equilibration, independent single-occupancy sites, fixed populations and uniform temperature. Kinetic, interacting and multiple-occupancy traps need another model.",
            ),
        )
    if any(
        (t.material_condition_id, t.reference_lattice_id) != (x.material_condition_id, x.reference_lattice_id)
        for t in x.traps
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Trap material condition and reference lattice must match the assessed material and lattice basis exactly.",
            ),
        )
    density = np.array([x.lattice_site_density_mol_m3, *[t.site_density_mol_m3 for t in x.traps]])
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        energy = np.array([0.0, *[t.binding_energy_J_mol for t in x.traps]]) / R_J_mol_K / x.temperature_K
    capacity = float(np.sum(density))
    if not np.isfinite(energy).all() or float(energy.max()) > 1e6 or not math.isfinite(capacity):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Site capacities or binding exponents exceed the finite numerical range.",),
        )
    total = x.total_hydrogen_atoms_mol_m3
    if total > capacity:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Supplied hydrogen exceeds the declared single-occupancy site capacity.",),
        )
    log_density = np.log(density)
    if total == 0:
        occupancy = np.zeros_like(density)
        concentrations = np.zeros_like(density)
        log_derivative = energy
        u = None
        residual = 0.0
    elif total == capacity:
        occupancy = np.ones_like(density)
        concentrations = density.copy()
        log_derivative = -energy
        u = None
        residual = 0.0
    else:
        # Solve mass in logarithmic coordinates; near filling solve vacancies instead.
        vacancy = total > capacity / 2
        target = capacity - total if vacancy else total
        log_target = math.log(target)

        def balance(u):
            return float(
                logsumexp(log_density + log_expit(-u - energy if vacancy else u + energy)) - log_target
            )

        low = (
            -float(energy.max()) - 2 if vacancy else log_target - math.log(capacity) - float(energy.max()) - 2
        )
        high = math.log(capacity) - log_target + 2 if vacancy else 0.0
        u = float(brentq(balance, low, high, xtol=1e-12, rtol=8 * np.finfo(float).eps, maxiter=300))
        if abs(balance(u)) > 1e-8:
            return Calculation(
                status="out_of_scope",
                values={},
                notes=(
                    "The mass/vacancy root cannot be resolved at the supplied energy and concentration scales.",
                ),
            )
        occupancy = expit(u + energy)
        concentrations = np.exp(log_density + log_expit(u + energy))
        # d(theta_T)/d(theta_L); softplus terms avoid rounded saturated fractions.
        log_derivative = energy + 2 * np.logaddexp(0, u) - 2 * np.logaddexp(0, u + energy)
        log_derivative[0] = 0.0
        residual = float(concentrations.sum() - total)
    if occupancy[0] > x.maximum_supported_lattice_occupancy or any(
        float(v) > t.maximum_supported_occupancy for t, v in zip(x.traps, occupancy[1:], strict=True)
    ):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Equilibrium occupancy exceeds a caller-declared lattice or trap validity bound.",),
        )
    log_retardation = float(logsumexp(log_density - math.log(x.lattice_site_density_mol_m3) + log_derivative))
    log_effective = math.log(x.lattice_diffusivity_m2_s) - log_retardation
    effective = math.exp(log_effective) if log_effective >= math.log(math.ulp(0.0)) else None
    retardation = math.exp(log_retardation) if log_retardation <= math.log(np.finfo(float).max) else None
    return Calculation(
        status="computed" if effective is not None else "out_of_scope",
        values=dict(
            lattice_hydrogen_atoms_mol_m3=float(concentrations[0]),
            lattice_occupancy=float(occupancy[0]),
            lattice_log_odds=u,
            site_fraction_resolution_limited=bool(
                0 < total < capacity and np.any((occupancy == 0) | (occupancy == 1))
            ),
            traps=[
                dict(
                    trap_id=t.trap_id,
                    hydrogen_atoms_mol_m3=float(c),
                    occupancy=float(v),
                    population_digest=canonical_digest(t.model_dump(mode="json")),
                )
                for t, c, v in zip(x.traps, concentrations[1:], occupancy[1:], strict=True)
            ],
            mass_balance_residual_mol_m3=residual,
            differential_retardation_factor=retardation,
            log_differential_retardation=log_retardation,
            local_differential_diffusivity_m2_s=effective,
            log_local_differential_diffusivity_m2_s=log_effective,
        ),
        notes=(
            "All concentrations count mol of hydrogen atoms, not hydrogen molecules. Positive binding is relative to a lattice site. The local coefficient D_L/(1+sum dC_T/dC_L) assumes flux -D_L grad(C_L); it is concentration dependent and is not a global constant fitted to an entire permeation transient.",
            "No surface gas-to-lattice conversion, thermal desorption kinetics, stress-gradient transport, embrittlement threshold or failure probability is inferred. Parameters and validity limits require independent material evidence.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_trap_equilibrium",
            HydrogenPartition,
            partition,
            {
                "lattice_hydrogen_atoms_mol_m3": "mol/m^3",
                "lattice_occupancy": "1",
                "lattice_log_odds": "1",
                "mass_balance_residual_mol_m3": "mol/m^3",
                "differential_retardation_factor": "1",
                "log_differential_retardation": "1",
                "local_differential_diffusivity_m2_s": "m^2/s",
                "log_local_differential_diffusivity_m2_s": "1",
            },
            (
                "Fast local equilibrium of fixed, independent single-occupancy trap populations in one uniform-temperature material condition.",
            ),
            ("oriani_equilibrium", "hydrogen_partition_derivation"),
        )
    ]
