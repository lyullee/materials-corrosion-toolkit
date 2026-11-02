"""Conservative planar transport with fixed, independent kinetic hydrogen traps."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .hydrogen import HydrogenTrapPopulation, R_J_mol_K


class HydrogenKineticTrap(Contract):
    population: HydrogenTrapPopulation
    rate_model: Literal["binding_energy_ratio", "independent_frequencies"] = "binding_energy_ratio"
    capture_frequency_per_s: list[Nonnegative] = Field(min_length=2)
    release_frequency_per_s: list[Nonnegative] | None = None
    initial_occupancy: list[Fraction] = Field(min_length=2)
    independent_rate_histories_reviewed: bool = False
    rate_evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def rate_inputs(self):
        if self.rate_model == "binding_energy_ratio":
            if self.release_frequency_per_s is not None:
                raise ValueError(
                    "binding-energy ratio traps derive release frequency and cannot accept a release history"
                )
            if self.independent_rate_histories_reviewed:
                raise ValueError("independent-rate review cannot be asserted for a binding-energy ratio trap")
        elif self.release_frequency_per_s is None:
            raise ValueError("independent-frequency traps require a release-frequency history")
        return self


class LatticeBoundary(Contract):
    boundary_id: str = Field(min_length=1)
    kind: Literal[
        "prescribed_lattice_concentration",
        "linear_surface_transfer",
        "dissociative_surface_reaction",
        "no_flux",
    ]
    lattice_hydrogen_atoms_mol_m3: list[Nonnegative] | None = None
    equilibrium_lattice_hydrogen_atoms_mol_m3: list[Nonnegative] | None = None
    transfer_coefficient_m_s: list[Positive] | None = None
    absorption_capacity_flux_mol_m2_s: list[Nonnegative] | None = None
    desorption_capacity_flux_mol_m2_s: list[Nonnegative] | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def boundary_values(self):
        prescribed = self.lattice_hydrogen_atoms_mol_m3 is not None
        equilibrium = self.equilibrium_lattice_hydrogen_atoms_mol_m3 is not None
        transfer = self.transfer_coefficient_m_s is not None
        absorption = self.absorption_capacity_flux_mol_m2_s is not None
        desorption = self.desorption_capacity_flux_mol_m2_s is not None
        if self.kind == "no_flux" and any((prescribed, equilibrium, transfer, absorption, desorption)):
            raise ValueError("no-flux boundaries have no concentration, transfer or reaction histories")
        if self.kind == "prescribed_lattice_concentration" and not (
            prescribed and not any((equilibrium, transfer, absorption, desorption))
        ):
            raise ValueError("prescribed boundaries require only a lattice concentration history")
        if self.kind == "linear_surface_transfer" and not (
            equilibrium and transfer and not any((prescribed, absorption, desorption))
        ):
            raise ValueError(
                "linear surface transfer requires equilibrium concentration and positive transfer histories"
            )
        if self.kind == "dissociative_surface_reaction":
            if not (absorption and desorption) or any((prescribed, equilibrium, transfer)):
                raise ValueError(
                    "dissociative surface reaction requires only absorption and desorption capacity histories"
                )
            if len(self.absorption_capacity_flux_mol_m2_s) != len(
                self.desorption_capacity_flux_mol_m2_s
            ) or any(
                inward + outward <= 0
                for inward, outward in zip(
                    self.absorption_capacity_flux_mol_m2_s,
                    self.desorption_capacity_flux_mol_m2_s,
                    strict=True,
                )
            ):
                raise ValueError(
                    "reaction capacity histories must align and have positive combined capacity at every knot"
                )
        return self


class HydrogenSlab(Contract):
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    elapsed_time_origin_id: str = Field(min_length=1)
    thickness_m: Positive
    cell_count: int = Field(ge=2, le=512)
    lattice_site_density_mol_m3: Positive
    initial_lattice_hydrogen_atoms_mol_m3: list[Nonnegative]
    elapsed_time_s: list[Nonnegative] = Field(min_length=2, max_length=4096)
    uniform_temperature_K: list[Positive]
    lattice_diffusivity_m2_s: list[Positive]
    left_boundary: LatticeBoundary
    right_boundary: LatticeBoundary
    traps: list[HydrogenKineticTrap] = Field(default_factory=list, max_length=16)
    maximum_supported_lattice_occupancy: float = Field(gt=0, le=1)
    maximum_supported_total_trap_to_lattice_site_ratio: float = Field(gt=0, lt=1)
    planar_geometry_reviewed: bool = False
    fixed_populations_and_uniform_temperature_reviewed: bool = False
    independent_single_occupancy_and_dilute_trap_regime_reviewed: bool = False
    negligible_stress_gradient_reviewed: bool = False
    detailed_balance_rate_ratio_reviewed: bool = False
    relative_tolerance: float = Field(default=1e-4, ge=1e-9, le=0.01)
    absolute_occupancy_tolerance: float = Field(default=1e-10, ge=1e-18, le=0.001)
    maximum_step_s: Positive | None = None
    maximum_step_attempts: int = Field(default=50000, ge=1, le=500000)
    maximum_relative_mass_balance_error: float = Field(default=1e-7, ge=1e-12, le=0.01)
    store_profiles: bool = False

    @model_validator(mode="after")
    def aligned_inputs(self):
        count = len(self.elapsed_time_s)
        if self.elapsed_time_s[0] != 0 or any(
            b <= a for a, b in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("elapsed times must start at zero and strictly increase")
        if len(self.initial_lattice_hydrogen_atoms_mol_m3) != self.cell_count:
            raise ValueError("initial lattice profile must have one cell-average value per cell")
        if len(self.uniform_temperature_K) != count or len(self.lattice_diffusivity_m2_s) != count:
            raise ValueError("temperature and diffusivity must match all time knots")
        if self.left_boundary.boundary_id == self.right_boundary.boundary_id:
            raise ValueError("left and right boundary identities must differ")
        for boundary in (self.left_boundary, self.right_boundary):
            histories = (
                boundary.lattice_hydrogen_atoms_mol_m3,
                boundary.equilibrium_lattice_hydrogen_atoms_mol_m3,
                boundary.transfer_coefficient_m_s,
                boundary.absorption_capacity_flux_mol_m2_s,
                boundary.desorption_capacity_flux_mol_m2_s,
            )
            if any(values is not None and len(values) != count for values in histories):
                raise ValueError("boundary histories must match all elapsed-time knots")
        ids = []
        for trap in self.traps:
            population = trap.population
            ids.append(population.trap_id)
            if (population.material_condition_id, population.reference_lattice_id) != (
                self.material_condition_id,
                self.reference_lattice_id,
            ):
                raise ValueError("trap material condition and lattice reference must match")
            if len(trap.capture_frequency_per_s) != count or len(trap.initial_occupancy) != self.cell_count:
                raise ValueError("capture history or initial trap profile has the wrong length")
            if trap.release_frequency_per_s is not None and len(trap.release_frequency_per_s) != count:
                raise ValueError("release history must match all time knots")
        if len(set(ids)) != len(ids):
            raise ValueError("trap IDs must be unique")
        return self


class _StepFailure(Exception):
    pass


def _trap_update(lattice, previous, capture_dt, release_dt):
    """Eliminate backward-Euler trap states; derivative is nonnegative."""
    a, b = capture_dt[:, None], release_dt[:, None]
    denominator = 1 + b + (a - b) * lattice[None, :]
    trapped = (previous + a * lattice[None, :]) / denominator
    derivative = (a * (1 - previous) + b * (previous + a)) / denominator**2
    return trapped, derivative


def _trap_frequencies(traps, times, time, temperature, energies):
    """Interpolate explicit rates or derive the reviewed detailed-balance release rate."""
    capture = np.asarray([np.interp(time, times, trap.capture_frequency_per_s) for trap in traps])
    release = np.zeros_like(capture)
    for index, trap in enumerate(traps):
        if trap.rate_model == "independent_frequencies":
            release[index] = np.interp(time, times, trap.release_frequency_per_s)
            continue
        if capture[index] == 0:
            continue
        log_release = math.log(capture[index]) - energies[index] / (R_J_mol_K * temperature)
        if not math.isfinite(log_release) or log_release < math.log(math.ulp(0.0)):
            raise _StepFailure(
                "release rate cannot be represented; no irreversible-trap substitution is made"
            )
        release[index] = math.exp(log_release)
    if np.any(~np.isfinite(capture)) or np.any(~np.isfinite(release)):
        raise _StepFailure("trap frequencies are outside floating-point resolution")
    return capture, release


def _rate_assumptions_reviewed(x):
    return all(
        (
            x.detailed_balance_rate_ratio_reviewed
            if trap.rate_model == "binding_energy_ratio"
            else trap.independent_rate_histories_reviewed
        )
        for trap in x.traps
    )


def _boundary_target_and_velocity(boundary, times, time, diffusivity, distance, lattice_density):
    """Combine one declared surface law with the adjacent half-cell diffusion resistance."""
    if boundary.kind == "no_flux":
        return None
    if boundary.kind == "prescribed_lattice_concentration":
        target = float(np.interp(time, times, boundary.lattice_hydrogen_atoms_mol_m3)) / lattice_density
        return target, diffusivity / distance
    if boundary.kind == "linear_surface_transfer":
        target = (
            float(np.interp(time, times, boundary.equilibrium_lattice_hydrogen_atoms_mol_m3))
            / lattice_density
        )
        coefficient = float(np.interp(time, times, boundary.transfer_coefficient_m_s))
        return target, 1 / (1 / coefficient + distance / diffusivity)
    absorption = float(np.interp(time, times, boundary.absorption_capacity_flux_mol_m2_s))
    desorption = float(np.interp(time, times, boundary.desorption_capacity_flux_mol_m2_s))
    combined = absorption + desorption
    target = absorption / combined
    return target, 1 / (lattice_density / combined + distance / diffusivity)


class _SlabSolver:
    def __init__(self, x):
        from scipy.linalg import solve_banded

        self.solve_banded = solve_banded
        self.x = x
        self.dx = x.thickness_m / x.cell_count
        self.nl = x.lattice_site_density_mol_m3
        self.ratios = np.asarray([t.population.site_density_mol_m3 / self.nl for t in x.traps])
        self.energies = np.asarray([t.population.binding_energy_J_mol for t in x.traps])
        self.times = np.asarray(x.elapsed_time_s)
        self.accepted = self.rejected = self.attempts = self.newton_iterations = 0
        self.minimum_step = math.inf
        self.maximum_error_ratio = 0.0

    def parameters(self, time):
        x = self.x
        temperature = float(np.interp(time, self.times, x.uniform_temperature_K))
        diffusivity = float(np.interp(time, self.times, x.lattice_diffusivity_m2_s))
        capture, release = _trap_frequencies(x.traps, self.times, time, temperature, self.energies)
        boundaries = []
        for boundary in (x.left_boundary, x.right_boundary):
            boundaries.append(
                _boundary_target_and_velocity(boundary, self.times, time, diffusivity, self.dx / 2, self.nl)
            )
        return diffusivity, capture, release, boundaries

    def flux(self, lattice, time):
        diffusivity, _, _, boundaries = self.parameters(time)
        result = np.asarray(
            [
                0.0
                if boundaries[0] is None
                else self.nl * boundaries[0][1] * (boundaries[0][0] - lattice[0]),
                0.0
                if boundaries[1] is None
                else self.nl * boundaries[1][1] * (boundaries[1][0] - lattice[-1]),
            ]
        )
        if not np.all(np.isfinite(result)):
            raise _StepFailure("boundary flux is outside floating-point resolution")
        return result

    def step(self, lattice_old, traps_old, end_time, duration):
        diffusivity, capture, release, boundaries = self.parameters(end_time)
        cfl = diffusivity * duration / self.dx**2
        a, b = capture * duration, release * duration
        if not np.isfinite(cfl) or cfl > 1e12 or np.any(~np.isfinite(a)) or np.any(a > 1e100):
            raise _StepFailure("dimensionless step coefficients exceed the numerical range")
        diagonal = np.full(self.x.cell_count, 2.0)
        diagonal[0] = diagonal[-1] = 1.0
        boundary_diagonal = np.zeros(self.x.cell_count)
        if boundaries[0] is not None:
            boundary_diagonal[0] = duration * boundaries[0][1] / self.dx
        if boundaries[1] is not None:
            boundary_diagonal[-1] = duration * boundaries[1][1] / self.dx
        lattice = lattice_old.copy()

        def residual(candidate):
            trapped, derivative = _trap_update(candidate, traps_old, a, b)
            differences = np.diff(candidate)
            laplacian = np.zeros_like(candidate)
            laplacian[:-1] += differences
            laplacian[1:] -= differences
            value = candidate - lattice_old + self.ratios @ (trapped - traps_old) - cfl * laplacian
            if boundaries[0] is not None:
                value[0] -= boundary_diagonal[0] * (boundaries[0][0] - candidate[0])
            if boundaries[1] is not None:
                value[-1] -= boundary_diagonal[-1] * (boundaries[1][0] - candidate[-1])
            return value, trapped, derivative

        scale = max(
            float(np.max(np.abs(lattice_old))),
            float(np.max(self.ratios[:, None] * np.abs(traps_old), initial=0.0)),
            max((value[0] for value in boundaries if value is not None), default=0.0),
            np.finfo(float).tiny,
        )
        tolerance = 64 * np.finfo(float).eps * (1 + cfl) * scale
        for _ in range(40):
            value, trapped, derivative = residual(lattice)
            norm = float(np.max(np.abs(value)))
            if np.isfinite(norm) and norm <= tolerance:
                return lattice, trapped, self.flux(lattice, end_time) * duration
            self.newton_iterations += 1
            jacobian = np.zeros((3, len(lattice)))
            jacobian[1] = 1 + self.ratios @ derivative + cfl * diagonal + boundary_diagonal
            jacobian[0, 1:] = -cfl
            jacobian[2, :-1] = -cfl
            try:
                delta = self.solve_banded((1, 1), jacobian, -value, check_finite=True)
            except (ValueError, np.linalg.LinAlgError) as error:
                raise _StepFailure("nonlinear linearization could not be solved") from error
            positive, negative = delta > 0, delta < 0
            alpha = min(
                1.0,
                float(np.min((1 - lattice[positive]) / delta[positive], initial=1.0)),
                float(np.min(-lattice[negative] / delta[negative], initial=1.0)),
            )
            if not np.isfinite(alpha) or alpha <= 0:
                raise _StepFailure("bounded nonlinear update is not resolvable")
            for _ in range(24):
                trial = lattice + alpha * delta
                if np.all((trial >= 0) & (trial <= 1)):
                    trial_norm = float(np.max(np.abs(residual(trial)[0])))
                    if np.isfinite(trial_norm) and (trial_norm <= tolerance or trial_norm < norm):
                        lattice = trial
                        break
                alpha *= 0.5
            else:
                raise _StepFailure("nonlinear line search did not converge")
        raise _StepFailure("nonlinear iteration budget exhausted")

    def state_within_scope(self, lattice, trapped):
        return (
            np.all(np.isfinite(lattice))
            and np.all(np.isfinite(trapped))
            and np.all((lattice >= 0) & (lattice <= self.x.maximum_supported_lattice_occupancy))
            and np.all(trapped >= 0)
            and all(
                np.max(v) <= t.population.maximum_supported_occupancy
                for t, v in zip(self.x.traps, trapped, strict=True)
            )
        )

    def error(self, old, full, fine, full_exchange, fine_exchange):
        ratios = []
        for previous, coarse, refined in zip(old, full, fine, strict=True):
            scale = self.x.absolute_occupancy_tolerance + self.x.relative_tolerance * np.maximum(
                np.abs(previous), np.abs(refined)
            )
            ratios.append(float(np.max(np.abs(refined - coarse) / scale, initial=0.0)))
        coarse = full_exchange / (self.nl * self.x.thickness_m)
        refined = fine_exchange / (self.nl * self.x.thickness_m)
        inventory_fraction = float(np.mean(fine[0] + self.ratios @ fine[1]))
        scale = self.x.absolute_occupancy_tolerance + self.x.relative_tolerance * np.maximum(
            np.abs(refined), abs(inventory_fraction)
        )
        ratios.append(float(np.max(np.abs(coarse - refined) / scale)))
        return max(ratios)


def slab_kinetic(x: HydrogenSlab) -> Calculation:
    """Solve atom-mole conservation with adaptive, bounded backward-Euler steps."""
    reviews = (
        x.planar_geometry_reviewed,
        x.fixed_populations_and_uniform_temperature_reviewed,
        x.independent_single_occupancy_and_dilute_trap_regime_reviewed,
        x.negligible_stress_gradient_reviewed,
        _rate_assumptions_reviewed(x),
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Geometry, fixed-site kinetics, stress and the selected trap-rate assumptions require explicit review.",
            ),
        )
    dx = x.thickness_m / x.cell_count
    squared_dx = dx * dx
    areal_capacity = x.lattice_site_density_mol_m3 * x.thickness_m
    if squared_dx == 0 or not math.isfinite(squared_dx) or not 0 < areal_capacity < math.inf:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Geometry/site scales are outside floating-point resolution.",),
        )
    if x.store_profiles and x.cell_count * (1 + len(x.traps)) * len(x.elapsed_time_s) > 1_000_000:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Requested spatial output exceeds the explicit one-million-value limit.",),
        )
    solver = _SlabSolver(x)
    lattice = np.asarray(x.initial_lattice_hydrogen_atoms_mol_m3) / solver.nl
    trapped = np.asarray([t.initial_occupancy for t in x.traps]).reshape(len(x.traps), x.cell_count)
    boundary_values = [
        value / solver.nl
        for boundary in (x.left_boundary, x.right_boundary)
        for values in (
            boundary.lattice_hydrogen_atoms_mol_m3,
            boundary.equilibrium_lattice_hydrogen_atoms_mol_m3,
        )
        for value in (values or [])
    ]
    if (
        sum(solver.ratios) > x.maximum_supported_total_trap_to_lattice_site_ratio
        or not solver.state_within_scope(lattice, trapped)
        or max(boundary_values, default=0.0) > x.maximum_supported_lattice_occupancy
    ):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Initial/boundary occupancy or total trap-site ratio exceeds caller-reviewed support.",),
        )
    lattice_history, trap_history, inventories, exchanges, fluxes, residuals = [], [], [], [], [], []
    lattice_profiles, trap_profiles = [], []
    exchange = np.zeros(2)
    initial_inventory = solver.nl * x.thickness_m * float(np.mean(lattice + solver.ratios @ trapped))
    time = 0.0
    duration = (x.elapsed_time_s[1] - x.elapsed_time_s[0]) / 20
    failure = None

    def record_state():
        inventory = solver.nl * x.thickness_m * float(np.mean(lattice + solver.ratios @ trapped))
        if not math.isfinite(inventory):
            raise _StepFailure("inventory is outside floating-point resolution")
        inventories.append(inventory)
        exchanges.append(exchange.copy())
        fluxes.append(solver.flux(lattice, time))
        residuals.append(inventory - initial_inventory - float(np.sum(exchange)))
        lattice_history.append(float(np.mean(lattice) * solver.nl))
        trap_history.append(np.mean(trapped, axis=1) * solver.ratios * solver.nl)
        if x.store_profiles:
            lattice_profiles.append((lattice * solver.nl).tolist())
            trap_profiles.append(trapped.copy())

    try:
        record_state()
        diffusivity, capture, release, _ = solver.parameters(0.0)
        initial_frequency = max(
            4 * diffusivity / solver.dx**2,
            float(np.max(capture + release, initial=0.0)) * (1 + float(np.sum(solver.ratios))),
        )
        if not math.isfinite(initial_frequency) or initial_frequency <= 0:
            raise _StepFailure("initial transport/kinetic scales are outside floating-point resolution")
        duration = min(duration, 0.05 / initial_frequency)
        for target in x.elapsed_time_s[1:]:
            while time < target:
                solver.attempts += 1
                if solver.attempts > x.maximum_step_attempts:
                    raise _StepFailure("adaptive step-attempt budget exhausted")
                duration = min(duration, target - time, x.maximum_step_s or target - time)
                if duration <= 64 * np.finfo(float).eps * max(abs(time), abs(time + duration)):
                    raise _StepFailure("required time step is below time-coordinate resolution")
                try:
                    full_l, full_t, full_q = solver.step(lattice, trapped, time + duration, duration)
                    mid_l, mid_t, mid_q = solver.step(lattice, trapped, time + duration / 2, duration / 2)
                    fine_l, fine_t, fine_q = solver.step(mid_l, mid_t, time + duration, duration / 2)
                    error = solver.error(
                        (lattice, trapped), (full_l, full_t), (fine_l, fine_t), full_q, mid_q + fine_q
                    )
                except _StepFailure:
                    solver.rejected += 1
                    duration *= 0.25
                    continue
                if not math.isfinite(error):
                    raise _StepFailure("time-error estimate is non-finite")
                if error > 1:
                    solver.rejected += 1
                    duration *= max(0.1, 0.8 / math.sqrt(error))
                    continue
                if not solver.state_within_scope(mid_l, mid_t) or not solver.state_within_scope(
                    fine_l, fine_t
                ):
                    raise _StepFailure("accepted trajectory exceeds caller-reviewed occupancy support")
                lattice, trapped = fine_l, fine_t
                exchange += mid_q + fine_q
                if not np.all(np.isfinite(exchange)):
                    raise _StepFailure("cumulative boundary exchange is outside floating-point resolution")
                time = target if duration == target - time else time + duration
                solver.accepted += 1
                solver.minimum_step = min(solver.minimum_step, duration / 2)
                solver.maximum_error_ratio = max(solver.maximum_error_ratio, error)
                duration *= min(2.0, 0.8 / math.sqrt(max(error, 1e-12)))
            record_state()
    except _StepFailure as error:
        failure = str(error)
    diagnostics = dict(
        accepted_step_pairs=solver.accepted,
        rejected_step_pairs=solver.rejected,
        step_attempts=solver.attempts,
        nonlinear_iterations=solver.newton_iterations,
        minimum_accepted_substep_s=solver.minimum_step if math.isfinite(solver.minimum_step) else None,
        maximum_accepted_local_error_ratio=solver.maximum_error_ratio,
        time_error_control="backward_euler_step_doubling_on_occupancies_and_boundary_exchange; not_a_global_error_bound",
        spatial_error_control="caller_mesh_refinement_required",
    )
    if failure:
        return Calculation(
            status="out_of_scope",
            values=dict(completed_elapsed_time_s=time, solver=diagnostics),
            notes=(failure, "A partial trajectory is not returned as a completed assessment."),
        )
    scale = max(
        initial_inventory,
        float(np.max(np.abs(inventories))),
        float(np.sum(np.abs(exchange))),
        np.finfo(float).tiny,
    )
    mass_error = float(np.max(np.abs(residuals))) / scale
    if not math.isfinite(mass_error) or mass_error > x.maximum_relative_mass_balance_error:
        return Calculation(
            status="out_of_scope",
            values=dict(
                completed_elapsed_time_s=time, relative_mass_balance_error=mass_error, solver=diagnostics
            ),
            notes=("Mass residual exceeds the caller's numerical budget; refine/review the solve.",),
        )
    fluxes, exchanges, trap_history = np.asarray(fluxes), np.asarray(exchanges), np.asarray(trap_history)
    return Calculation(
        values=dict(
            elapsed_time_origin_id=x.elapsed_time_origin_id,
            elapsed_time_s=x.elapsed_time_s,
            cell_centers_m=((np.arange(x.cell_count) + 0.5) * solver.dx).tolist(),
            final_lattice_hydrogen_atoms_mol_m3=(lattice * solver.nl).tolist(),
            lattice_mean_hydrogen_atoms_mol_m3=lattice_history,
            lattice_profiles_hydrogen_atoms_mol_m3=lattice_profiles if x.store_profiles else None,
            traps=[
                dict(
                    trap_id=t.population.trap_id,
                    population_digest=canonical_digest(t.population.model_dump(mode="json")),
                    rate_model=t.rate_model,
                    rate_history_digest=canonical_digest(
                        {
                            "rate_model": t.rate_model,
                            "capture_frequency_per_s": t.capture_frequency_per_s,
                            "release_frequency_per_s": t.release_frequency_per_s,
                        }
                    ),
                    final_occupancy=trapped[i].tolist(),
                    final_hydrogen_atoms_mol_m3=(trapped[i] * t.population.site_density_mol_m3).tolist(),
                    mean_hydrogen_atoms_mol_m3=trap_history[:, i].tolist(),
                    occupancy_profiles=[v[i].tolist() for v in trap_profiles] if x.store_profiles else None,
                )
                for i, t in enumerate(x.traps)
            ],
            hydrogen_inventory_mol_m2=inventories,
            left_inward_flux_mol_m2_s=fluxes[:, 0].tolist(),
            right_inward_flux_mol_m2_s=fluxes[:, 1].tolist(),
            cumulative_left_exchange_mol_m2=exchanges[:, 0].tolist(),
            cumulative_right_exchange_mol_m2=exchanges[:, 1].tolist(),
            mass_balance_residual_mol_m2=residuals,
            relative_mass_balance_error=mass_error if math.isfinite(mass_error) else None,
            solver=diagnostics,
        ),
        notes=(
            "Every concentration/inventory counts mol of H atoms. Both boundary fluxes and cumulative exchanges are positive inward. Profiles are cell averages; no axial/cylindrical or stress-gradient term is present.",
            "Fixed independent single-occupancy traps exchange through capture*theta_L*(1-theta_T)-release*theta_T*(1-theta_L). Each trap either uses a reviewed release/capture=exp(-binding/(R*T)) ratio or separately reviewed capture and release histories. Only the ratio mode freezes a population when capture is zero.",
            "All supplied histories are piecewise linear on the elapsed-time knots; temperature is spatially uniform. Linear transfer and the reduced dissociative reaction both retain half-cell diffusion resistance. The latter uses J_abs*(1-theta_surface)-J_des*theta_surface with externally reviewed capacity histories; it is not a full adsorption mechanism or bulk-solubility law. Temporal local control does not bound global/spatial error. Detector response, current inversion, fracture and failure probability are separate providers.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_slab_kinetic",
            HydrogenSlab,
            slab_kinetic,
            {
                "elapsed_time_s": "s",
                "cell_centers_m": "m",
                "final_lattice_hydrogen_atoms_mol_m3": "mol/m^3",
                "lattice_mean_hydrogen_atoms_mol_m3": "mol/m^3",
                "lattice_profiles_hydrogen_atoms_mol_m3": "mol/m^3",
                "hydrogen_inventory_mol_m2": "mol/m^2",
                "left_inward_flux_mol_m2_s": "mol/(m^2*s)",
                "right_inward_flux_mol_m2_s": "mol/(m^2*s)",
                "cumulative_left_exchange_mol_m2": "mol/m^2",
                "cumulative_right_exchange_mol_m2": "mol/m^2",
                "mass_balance_residual_mol_m2": "mol/m^2",
                "relative_mass_balance_error": "1",
            },
            (
                "Planar Fickian lattice transport with fixed independent dilute trap populations, reviewed detailed-balance or independent-frequency kinetics, spatially uniform temperature and declared surface boundaries.",
            ),
            (
                "diaz_kinetic_transport",
                "hydrogen_slab_fvm_derivation",
                "hydrogen_reduced_surface_reaction_derivation",
                "scipy_banded",
            ),
        )
    ]
