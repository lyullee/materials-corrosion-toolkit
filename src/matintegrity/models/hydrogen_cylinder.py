"""Conservative axisymmetric transport in a finite cylinder with kinetic hydrogen traps."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .hydrogen_kinetics import (
    HydrogenKineticTrap,
    LatticeBoundary,
    _boundary_target_and_velocity,
    _rate_assumptions_reviewed,
    _StepFailure,
    _trap_frequencies,
    _trap_update,
)


class HydrogenFiniteCylinder(Contract):
    material_condition_id: str = Field(min_length=1)
    reference_lattice_id: str = Field(min_length=1)
    elapsed_time_origin_id: str = Field(min_length=1)
    radius_m: Positive
    length_m: Positive
    radial_cell_count: int = Field(ge=2, le=128)
    axial_cell_count: int = Field(ge=2, le=256)
    lattice_site_density_mol_m3: Positive
    initial_lattice_hydrogen_atoms_mol_m3: list[Nonnegative]
    elapsed_time_s: list[Nonnegative] = Field(min_length=2, max_length=4096)
    uniform_temperature_K: list[Positive]
    lattice_diffusivity_m2_s: list[Positive]
    curved_surface_boundary: LatticeBoundary
    lower_end_boundary: LatticeBoundary
    upper_end_boundary: LatticeBoundary
    traps: list[HydrogenKineticTrap] = Field(default_factory=list, max_length=16)
    maximum_supported_lattice_occupancy: float = Field(gt=0, le=1)
    maximum_supported_total_trap_to_lattice_site_ratio: float = Field(gt=0, lt=1)
    finite_axisymmetric_geometry_reviewed: bool = False
    azimuthally_uniform_state_reviewed: bool = False
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
        cells = self.radial_cell_count * self.axial_cell_count
        if cells > 16384:
            raise ValueError("axisymmetric grid exceeds the explicit 16,384-cell limit")
        if self.elapsed_time_s[0] != 0 or any(
            b <= a for a, b in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("elapsed times must start at zero and strictly increase")
        if len(self.initial_lattice_hydrogen_atoms_mol_m3) != cells:
            raise ValueError("initial lattice profile must have radial-major, axial-minor cell values")
        if len(self.uniform_temperature_K) != count or len(self.lattice_diffusivity_m2_s) != count:
            raise ValueError("temperature and diffusivity must match all time knots")
        boundaries = (
            self.curved_surface_boundary,
            self.lower_end_boundary,
            self.upper_end_boundary,
        )
        if len({boundary.boundary_id for boundary in boundaries}) != 3:
            raise ValueError("the three surface boundary identities must differ")
        for boundary in boundaries:
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
            if len(trap.capture_frequency_per_s) != count or len(trap.initial_occupancy) != cells:
                raise ValueError("capture history or initial trap profile has the wrong length")
            if trap.release_frequency_per_s is not None and len(trap.release_frequency_per_s) != count:
                raise ValueError("release history must match all time knots")
        if len(set(ids)) != len(ids):
            raise ValueError("trap IDs must be unique")
        return self


class _CylinderSolver:
    def __init__(self, x):
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import spsolve

        self.csr_matrix = csr_matrix
        self.spsolve = spsolve
        self.x = x
        self.nr = x.radial_cell_count
        self.nz = x.axial_cell_count
        self.cells = self.nr * self.nz
        self.dr = x.radius_m / self.nr
        self.dz = x.length_m / self.nz
        self.nl = x.lattice_site_density_mol_m3
        self.ratios = np.asarray([t.population.site_density_mol_m3 / self.nl for t in x.traps])
        self.energies = np.asarray([t.population.binding_energy_J_mol for t in x.traps])
        self.times = np.asarray(x.elapsed_time_s)
        radial_edges = np.arange(self.nr + 1) * self.dr
        annular_areas = math.pi * np.diff(radial_edges**2)
        self.volumes = np.repeat(annular_areas * self.dz, self.nz)
        self.total_volume = float(np.sum(self.volumes))
        self.neighbors = []
        self.boundary_geometry = [[], [], []]
        for ir in range(self.nr):
            for iz in range(self.nz):
                cell = ir * self.nz + iz
                if ir + 1 < self.nr:
                    other = (ir + 1) * self.nz + iz
                    self.neighbors.append(
                        (cell, other, 2 * math.pi * radial_edges[ir + 1] * self.dz / self.dr)
                    )
                else:
                    self.boundary_geometry[0].append(
                        (cell, 2 * math.pi * x.radius_m * self.dz / (self.dr / 2))
                    )
                end_area = annular_areas[ir]
                if iz == 0:
                    self.boundary_geometry[1].append((cell, end_area / (self.dz / 2)))
                if iz + 1 < self.nz:
                    self.neighbors.append((cell, cell + 1, end_area / self.dz))
                else:
                    self.boundary_geometry[2].append((cell, end_area / (self.dz / 2)))
        self.accepted = self.rejected = self.attempts = self.newton_iterations = 0
        self.minimum_step = math.inf
        self.maximum_error_ratio = 0.0

    def parameters(self, time):
        temperature = float(np.interp(time, self.times, self.x.uniform_temperature_K))
        diffusivity = float(np.interp(time, self.times, self.x.lattice_diffusivity_m2_s))
        capture, release = _trap_frequencies(self.x.traps, self.times, time, temperature, self.energies)
        boundaries = []
        distances = (self.dr / 2, self.dz / 2, self.dz / 2)
        for boundary, distance in zip(
            (
                self.x.curved_surface_boundary,
                self.x.lower_end_boundary,
                self.x.upper_end_boundary,
            ),
            distances,
            strict=True,
        ):
            parameters = _boundary_target_and_velocity(
                boundary, self.times, time, diffusivity, distance, self.nl
            )
            if parameters is None:
                boundaries.append(None)
                continue
            target, effective_velocity = parameters
            boundaries.append((target, effective_velocity * distance / diffusivity))
        return diffusivity, capture, release, boundaries

    def flux(self, lattice, time):
        diffusivity, _, _, boundaries = self.parameters(time)
        result = np.zeros(3)
        for surface, boundary in enumerate(boundaries):
            if boundary is not None:
                result[surface] = (
                    diffusivity
                    * self.nl
                    * sum(
                        geometry * boundary[1] * (boundary[0] - lattice[cell])
                        for cell, geometry in self.boundary_geometry[surface]
                    )
                )
        if not np.all(np.isfinite(result)):
            raise _StepFailure("boundary flow is outside floating-point resolution")
        return result

    def _transport(self, lattice, boundaries):
        flow = np.zeros(self.cells)
        diagonal_geometry = np.zeros(self.cells)
        rows, columns, off_diagonal_geometry = [], [], []
        for first, second, geometry in self.neighbors:
            amount = geometry * (lattice[second] - lattice[first])
            flow[first] += amount
            flow[second] -= amount
            diagonal_geometry[first] += geometry
            diagonal_geometry[second] += geometry
            rows.extend((first, second))
            columns.extend((second, first))
            off_diagonal_geometry.extend((geometry, geometry))
        for surface, boundary in enumerate(boundaries):
            if boundary is None:
                continue
            for cell, geometry in self.boundary_geometry[surface]:
                effective_geometry = geometry * boundary[1]
                flow[cell] += effective_geometry * (boundary[0] - lattice[cell])
                diagonal_geometry[cell] += effective_geometry
        return flow, diagonal_geometry, rows, columns, off_diagonal_geometry

    def step(self, lattice_old, traps_old, end_time, duration):
        diffusivity, capture, release, boundaries = self.parameters(end_time)
        a, b = capture * duration, release * duration
        if np.any(~np.isfinite(a)) or np.any(a > 1e100):
            raise _StepFailure("dimensionless kinetic coefficients exceed the numerical range")
        lattice = lattice_old.copy()

        def residual(candidate):
            trapped, derivative = _trap_update(candidate, traps_old, a, b)
            flow, diagonal, rows, columns, off_diagonal = self._transport(candidate, boundaries)
            value = (
                candidate
                - lattice_old
                + self.ratios @ (trapped - traps_old)
                - duration * diffusivity * flow / self.volumes
            )
            return value, trapped, derivative, diagonal, rows, columns, off_diagonal

        scale = max(
            float(np.max(np.abs(lattice_old))),
            float(np.max(self.ratios[:, None] * np.abs(traps_old), initial=0.0)),
            max((value[0] for value in boundaries if value is not None), default=0.0),
            np.finfo(float).tiny,
        )
        for _ in range(40):
            value, trapped, derivative, diagonal, rows, columns, off_diagonal = residual(lattice)
            norm = float(np.max(np.abs(value)))
            coefficient_scale = float(np.max(duration * diffusivity * diagonal / self.volumes))
            tolerance = 64 * np.finfo(float).eps * (1 + coefficient_scale) * scale
            if np.isfinite(norm) and norm <= tolerance:
                return lattice, trapped, self.flux(lattice, end_time) * duration
            self.newton_iterations += 1
            main = 1 + self.ratios @ derivative + duration * diffusivity * diagonal / self.volumes
            matrix_rows = list(range(self.cells)) + rows
            matrix_columns = list(range(self.cells)) + columns
            matrix_values = main.tolist() + [
                -duration * diffusivity * geometry / self.volumes[row]
                for row, geometry in zip(rows, off_diagonal, strict=True)
            ]
            matrix = self.csr_matrix(
                (matrix_values, (matrix_rows, matrix_columns)), shape=(self.cells, self.cells)
            )
            try:
                delta = self.spsolve(matrix, -value)
            except Exception as error:
                raise _StepFailure("sparse nonlinear linearization could not be solved") from error
            if not np.all(np.isfinite(delta)):
                raise _StepFailure("sparse nonlinear update is non-finite")
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
                np.max(values) <= trap.population.maximum_supported_occupancy
                for trap, values in zip(self.x.traps, trapped, strict=True)
            )
        )

    def inventory(self, lattice, trapped):
        density = lattice + self.ratios @ trapped
        return self.nl * float(np.dot(self.volumes, density))

    def weighted_mean(self, values):
        return float(np.dot(self.volumes, values) / self.total_volume)

    def error(self, old, full, fine, full_exchange, fine_exchange):
        ratios = []
        for previous, coarse, refined in zip(old, full, fine, strict=True):
            scale = self.x.absolute_occupancy_tolerance + self.x.relative_tolerance * np.maximum(
                np.abs(previous), np.abs(refined)
            )
            ratios.append(float(np.max(np.abs(refined - coarse) / scale, initial=0.0)))
        coarse = full_exchange / (self.nl * self.total_volume)
        refined = fine_exchange / (self.nl * self.total_volume)
        inventory_fraction = self.inventory(fine[0], fine[1]) / (self.nl * self.total_volume)
        scale = self.x.absolute_occupancy_tolerance + self.x.relative_tolerance * np.maximum(
            np.abs(refined), abs(inventory_fraction)
        )
        ratios.append(float(np.max(np.abs(coarse - refined) / scale)))
        return max(ratios)


def finite_cylinder_kinetic(x: HydrogenFiniteCylinder) -> Calculation:
    """Solve axisymmetric radial-axial atom-mole conservation in a finite cylinder."""
    reviews = (
        x.finite_axisymmetric_geometry_reviewed,
        x.azimuthally_uniform_state_reviewed,
        x.fixed_populations_and_uniform_temperature_reviewed,
        x.independent_single_occupancy_and_dilute_trap_regime_reviewed,
        x.negligible_stress_gradient_reviewed,
        _rate_assumptions_reviewed(x),
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Finite-cylinder geometry, symmetry, kinetics and stress assumptions require review.",),
        )
    solver = _CylinderSolver(x)
    if (
        solver.dr * solver.dr == 0
        or solver.dz * solver.dz == 0
        or not math.isfinite(solver.total_volume)
        or not 0 < solver.nl * solver.total_volume < math.inf
    ):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Geometry/site scales are outside floating-point resolution.",),
        )
    cells = solver.cells
    if x.store_profiles and cells * (1 + len(x.traps)) * len(x.elapsed_time_s) > 1_000_000:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Requested spatial output exceeds the explicit one-million-value limit.",),
        )
    lattice = np.asarray(x.initial_lattice_hydrogen_atoms_mol_m3) / solver.nl
    trapped = np.asarray([trap.initial_occupancy for trap in x.traps]).reshape(len(x.traps), cells)
    boundaries = (x.curved_surface_boundary, x.lower_end_boundary, x.upper_end_boundary)
    boundary_values = [
        value / solver.nl
        for boundary in boundaries
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
            notes=("Initial/boundary occupancy or total trap-site ratio exceeds reviewed support.",),
        )
    lattice_history, trap_history, inventories, exchanges, flows, residuals = [], [], [], [], [], []
    lattice_profiles, trap_profiles = [], []
    exchange = np.zeros(3)
    initial_inventory = solver.inventory(lattice, trapped)
    time = 0.0
    duration = (x.elapsed_time_s[1] - x.elapsed_time_s[0]) / 20
    failure = None

    def record_state():
        inventory = solver.inventory(lattice, trapped)
        if not math.isfinite(inventory):
            raise _StepFailure("inventory is outside floating-point resolution")
        inventories.append(inventory)
        exchanges.append(exchange.copy())
        flows.append(solver.flux(lattice, time))
        residuals.append(inventory - initial_inventory - float(np.sum(exchange)))
        lattice_history.append(solver.weighted_mean(lattice) * solver.nl)
        trap_history.append(
            [
                solver.weighted_mean(trapped[index]) * trap.population.site_density_mol_m3
                for index, trap in enumerate(x.traps)
            ]
        )
        if x.store_profiles:
            lattice_profiles.append((lattice * solver.nl).tolist())
            trap_profiles.append(trapped.copy())

    try:
        record_state()
        diffusivity, capture, release, boundary_values_now = solver.parameters(0.0)
        _, diagonal, *_ = solver._transport(lattice, boundary_values_now)
        initial_frequency = max(
            float(np.max(diffusivity * diagonal / solver.volumes)),
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
                        (lattice, trapped),
                        (full_l, full_t),
                        (fine_l, fine_t),
                        full_q,
                        mid_q + fine_q,
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
                    raise _StepFailure("accepted trajectory exceeds reviewed occupancy support")
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
        spatial_error_control="caller_radial_and_axial_mesh_refinement_required",
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
                completed_elapsed_time_s=time,
                relative_mass_balance_error=mass_error,
                solver=diagnostics,
            ),
            notes=("Mass residual exceeds the caller's numerical budget; refine/review the solve.",),
        )
    flows_array = np.asarray(flows)
    exchanges_array = np.asarray(exchanges)
    trap_history_array = np.asarray(trap_history)
    radial_centers = ((np.arange(x.radial_cell_count) + 0.5) * solver.dr).tolist()
    axial_centers = ((np.arange(x.axial_cell_count) + 0.5) * solver.dz).tolist()
    surface_names = ("curved_surface", "lower_end", "upper_end")
    return Calculation(
        values=dict(
            elapsed_time_origin_id=x.elapsed_time_origin_id,
            elapsed_time_s=x.elapsed_time_s,
            radial_cell_centers_m=radial_centers,
            axial_cell_centers_m=axial_centers,
            profile_layout="radial_major_axial_minor_cell_averages",
            cylinder_volume_m3=solver.total_volume,
            final_lattice_hydrogen_atoms_mol_m3=(lattice * solver.nl).tolist(),
            lattice_volume_mean_hydrogen_atoms_mol_m3=lattice_history,
            lattice_profiles_hydrogen_atoms_mol_m3=lattice_profiles if x.store_profiles else None,
            traps=[
                dict(
                    trap_id=trap.population.trap_id,
                    population_digest=canonical_digest(trap.population.model_dump(mode="json")),
                    rate_model=trap.rate_model,
                    rate_history_digest=canonical_digest(
                        {
                            "rate_model": trap.rate_model,
                            "capture_frequency_per_s": trap.capture_frequency_per_s,
                            "release_frequency_per_s": trap.release_frequency_per_s,
                        }
                    ),
                    final_occupancy=trapped[index].tolist(),
                    final_hydrogen_atoms_mol_m3=(
                        trapped[index] * trap.population.site_density_mol_m3
                    ).tolist(),
                    volume_mean_hydrogen_atoms_mol_m3=trap_history_array[:, index].tolist(),
                    occupancy_profiles=(
                        [profile[index].tolist() for profile in trap_profiles] if x.store_profiles else None
                    ),
                )
                for index, trap in enumerate(x.traps)
            ],
            hydrogen_inventory_mol=inventories,
            inward_surface_flow_mol_s={
                name: flows_array[:, index].tolist() for index, name in enumerate(surface_names)
            },
            cumulative_surface_exchange_mol={
                name: exchanges_array[:, index].tolist() for index, name in enumerate(surface_names)
            },
            mass_balance_residual_mol=residuals,
            relative_mass_balance_error=mass_error,
            solver=diagnostics,
        ),
        notes=(
            "Every concentration and inventory counts mol of H atoms. Surface flows/exchanges are positive inward. The axis is a symmetry surface; the curved wall and two ends retain separate identities.",
            "The state is azimuthally uniform and cell averaged on a finite radial-axial volume grid. Linear transfer and the reduced dissociative reaction retain half-cell diffusion resistance. The latter consumes externally reviewed absorption/desorption capacity histories and is not a full adsorption mechanism, bulk-solubility law or specimen-specific calibration. This is not a one-dimensional infinite-cylinder approximation.",
            "Fixed independent traps use either the reviewed binding-energy rate ratio or separately reviewed capture and release histories, matching the planar model. Temporal local control does not bound radial/axial spatial error; mesh refinement remains required.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "transport.hydrogen_finite_cylinder_kinetic",
            HydrogenFiniteCylinder,
            finite_cylinder_kinetic,
            {
                "elapsed_time_s": "s",
                "radial_cell_centers_m": "m",
                "axial_cell_centers_m": "m",
                "cylinder_volume_m3": "m^3",
                "final_lattice_hydrogen_atoms_mol_m3": "mol/m^3",
                "lattice_volume_mean_hydrogen_atoms_mol_m3": "mol/m^3",
                "lattice_profiles_hydrogen_atoms_mol_m3": "mol/m^3",
                "hydrogen_inventory_mol": "mol",
                "inward_surface_flow_mol_s": "mol/s",
                "cumulative_surface_exchange_mol": "mol",
                "mass_balance_residual_mol": "mol",
                "relative_mass_balance_error": "1",
            },
            (
                "Finite axisymmetric radial-axial Fickian transport with separately declared curved/end boundaries, fixed independent dilute traps, reviewed detailed-balance or independent-frequency kinetics and spatially uniform temperature.",
            ),
            (
                "diaz_kinetic_transport",
                "hydrogen_finite_cylinder_fvm_derivation",
                "hydrogen_reduced_surface_reaction_derivation",
                "scipy_sparse",
            ),
        )
    ]
