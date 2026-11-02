"""Activity-corrected reactive crevice transport on caller-pinned variable areas."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_activity_corrected_transport import CreviceActivityReactiveTransportRequest
from .registry import ModelSpec

MODEL_ID = "transport.crevice_variable_area_activity_corrected_reactive_nernst_planck_1d"
AREA_HISTORY_SOURCE_ID = "caller_crevice_variable_area_history"
METHOD_SOURCE_ID = "finite_volume_variable_volume_activity_nernst_planck_mass_action"
MAX_CELL_TIME_SPECIES_RECORDS = 2_000_000


class VariableAreaCreviceActivityReactiveTransportRequest(Contract):
    """Reactive transport plus exact-knot cell-volume and face-area records.

    Area arrays use time-major order: one cell-area row per output knot with one
    entry per axial cell; face-area rows have one additional entry. The nested
    activity request's scalar `cross_section_area_m2` is a reference value and
    must equal the arithmetic mean cell area at the first knot.
    """

    schema_version: Literal["matintegrity.crevice_variable_area_activity_transport.v1"] = (
        "matintegrity.crevice_variable_area_activity_transport.v1"
    )
    assessment_id: str = Field(min_length=1)
    transport_request: CreviceActivityReactiveTransportRequest
    geometry_id: str = Field(min_length=1)
    area_provider_id: str = Field(min_length=1)
    area_provider_revision: str = Field(min_length=1)
    area_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cell_cross_section_area_m2_by_knot: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=500)
    face_cross_section_area_m2_by_knot: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=500)
    area_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    area_history_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    absolute_volume_flow_continuity_tolerance_m3_s: Positive = 1e-14
    relative_volume_flow_continuity_tolerance: float = Field(default=1e-6, gt=0.0, le=0.01)
    positive_area_and_mesh_mapping_reviewed: bool
    temporal_area_interpolation_reviewed: bool
    moving_volume_inventory_and_dilution_reviewed: bool
    face_area_transport_mapping_reviewed: bool
    boundary_flux_area_basis_reviewed: bool
    volume_change_flow_consistency_reviewed: bool
    no_momentum_or_geometry_feedback_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_geometry_and_provenance(self):
        transport = self.transport_request
        nt = len(transport.output_time_s)
        nc = transport.cell_count
        cells = self.cell_cross_section_area_m2_by_knot
        faces = self.face_cross_section_area_m2_by_knot
        if len(cells) != nt or any(len(row) != nc for row in cells):
            raise ValueError("cell-area history must exactly match output knots × cell count")
        if len(faces) != nt or any(len(row) != nc + 1 for row in faces):
            raise ValueError("face-area history must exactly match output knots × (cell count + 1)")
        if nc * nt * len(transport.species) > MAX_CELL_TIME_SPECIES_RECORDS:
            raise ValueError("variable-area output record budget exceeded")
        reference = math.fsum(cells[0]) / nc
        if not math.isclose(transport.cross_section_area_m2, reference, rel_tol=1e-10,
                            abs_tol=1e-14 * max(reference, 1e-30)):
            raise ValueError("nested scalar cross-section must equal first-knot mean cell area as a reference")
        area_payload = {
            "geometry_id": self.geometry_id,
            "provider_id": self.area_provider_id,
            "provider_revision": self.area_provider_revision,
            "configuration_sha256": self.area_configuration_sha256,
            "time_s": list(transport.output_time_s),
            "cell_cross_section_area_m2_by_knot": [list(row) for row in cells],
            "face_cross_section_area_m2_by_knot": [list(row) for row in faces],
        }
        if canonical_digest(area_payload) != self.area_history_sha256:
            raise ValueError("area-history digest must bind provider, exact clock, cells and faces")
        if not any(row.source_id == AREA_HISTORY_SOURCE_ID and row.sha256 == self.area_history_sha256
                   and row.license_id for row in self.area_history_evidence):
            raise ValueError("licensed area-history Evidence must pin the complete variable geometry record")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights Evidence must identify a license or permitted-use basis")
        if not all((self.positive_area_and_mesh_mapping_reviewed,
                    self.temporal_area_interpolation_reviewed,
                    self.moving_volume_inventory_and_dilution_reviewed,
                    self.face_area_transport_mapping_reviewed,
                    self.boundary_flux_area_basis_reviewed,
                    self.volume_change_flow_consistency_reviewed,
                    self.no_momentum_or_geometry_feedback_claim_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all geometry, time interpolation, conservation, flow and use reviews are required")
        return self


def _stoichiometry(request: CreviceActivityReactiveTransportRequest):
    rows = request.species
    reactions = request.reactions
    index = {row.species_id: position for position, row in enumerate(rows)}
    matrix = np.zeros((len(rows), len(reactions)), dtype=float)
    forward = np.empty((len(reactions), len(request.output_time_s)), dtype=float)
    reverse = np.empty_like(forward)
    for j, reaction in enumerate(reactions):
        for term in reaction.reactants:
            matrix[index[term.species_id], j] -= term.coefficient
        for term in reaction.products:
            matrix[index[term.species_id], j] += term.coefficient
        forward[j] = reaction.forward_rate_constant_mol_m3_s_by_knot
        reverse[j] = reaction.reverse_rate_constant_mol_m3_s_by_knot
    return index, matrix, forward, reverse


def _volume_flow_continuity(request: VariableAreaCreviceActivityReactiveTransportRequest):
    """Find the exact maximum residual of quadratic face flow over linear-area/time intervals."""
    area = np.asarray(request.cell_cross_section_area_m2_by_knot, dtype=float)
    face_area = np.asarray(request.face_cross_section_area_m2_by_knot, dtype=float)
    velocity = np.asarray(request.transport_request.cell_face_axial_velocity_m_s_by_knot, dtype=float).T
    times = np.asarray(request.transport_request.output_time_s, dtype=float)
    dx = request.transport_request.length_m / request.transport_request.cell_count
    residuals: list[list[float]] = []
    scales: list[list[float]] = []
    for k, duration in enumerate(np.diff(times)):
        interval_residuals = []
        interval_scales = []
        dvolume_dt = (area[k + 1] - area[k]) * dx / duration
        for cell in range(request.transport_request.cell_count):
            # Qin-Qout is quadratic because both face area and velocity are linearly interpolated.
            al0, al1 = face_area[k, cell], face_area[k + 1, cell]
            ar0, ar1 = face_area[k, cell + 1], face_area[k + 1, cell + 1]
            ul0, ul1 = velocity[k, cell], velocity[k + 1, cell]
            ur0, ur1 = velocity[k, cell + 1], velocity[k + 1, cell + 1]
            p0 = al0 * ul0 - ar0 * ur0
            p1 = al0 * (ul1 - ul0) + (al1 - al0) * ul0 - ar0 * (ur1 - ur0) - (ar1 - ar0) * ur0
            p2 = (al1 - al0) * (ul1 - ul0) - (ar1 - ar0) * (ur1 - ur0)
            candidates = [0.0, 1.0]
            if p2 != 0.0:
                critical = -p1 / (2.0 * p2)
                if 0.0 < critical < 1.0:
                    candidates.append(critical)
            local_residual = max(abs(dvolume_dt[cell] - (p0 + p1 * f + p2 * f * f)) for f in candidates)
            local_flow = max(abs(p0 + p1 * f + p2 * f * f) for f in candidates)
            interval_residuals.append(float(local_residual))
            interval_scales.append(float(max(abs(dvolume_dt[cell]), local_flow)))
        residuals.append(interval_residuals)
        scales.append(interval_scales)
    return residuals, scales


def evaluate_variable_area_crevice_activity_transport(
    request: VariableAreaCreviceActivityReactiveTransportRequest,
) -> Calculation:
    """Integrate species moles in time-varying cell volumes with face-area fluxes."""
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values={"model_id": MODEL_ID, "reason": "scipy_runtime_unavailable"})

    transport = request.transport_request
    digest = canonical_digest(request.model_dump(mode="json"))
    times = np.asarray(transport.output_time_s, dtype=float)
    nt, nc, ns = len(times), transport.cell_count, len(transport.species)
    dx = transport.length_m / nc
    rows = transport.species
    z = np.asarray([row.charge_number for row in rows], dtype=float)
    diffusivity = np.asarray([row.diffusivity_m2_s for row in rows], dtype=float)
    initial = np.asarray([row.initial_cell_concentration_mol_m3 for row in rows], dtype=float)
    boundary = np.asarray([transport.mouth_boundary_concentration_mol_m3_by_species[row.species_id]
                           for row in rows], dtype=float)
    gamma_cells = np.transpose(
        np.asarray([row.activity_coefficient_by_time_and_cell for row in rows], dtype=float), (1, 0, 2)
    )  # time, species, cell
    gamma_mouth = np.transpose(
        np.asarray([row.mouth_activity_coefficient_by_time for row in rows], dtype=float), (1, 0)
    )  # time, species
    velocity_knots = np.asarray(transport.cell_face_axial_velocity_m_s_by_knot, dtype=float)
    cell_area = np.asarray(request.cell_cross_section_area_m2_by_knot, dtype=float)
    face_area = np.asarray(request.face_cross_section_area_m2_by_knot, dtype=float)
    continuity_residuals, continuity_scales = _volume_flow_continuity(request)
    continuity_allowed = [
        request.absolute_volume_flow_continuity_tolerance_m3_s
        + request.relative_volume_flow_continuity_tolerance * scale
        for interval in continuity_scales for scale in interval
    ]
    flat_residuals = [value for interval in continuity_residuals for value in interval]
    if any(value > allowed for value, allowed in zip(flat_residuals, continuity_allowed, strict=True)):
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "reason": "caller face volumetric flow is inconsistent with the supplied cell-volume change",
            "volume_flow_continuity_residual_m3_s_by_interval_and_cell": continuity_residuals,
            "volume_flow_continuity_allowed_residual_m3_s_by_interval_and_cell": [
                [request.absolute_volume_flow_continuity_tolerance_m3_s
                 + request.relative_volume_flow_continuity_tolerance * scale for scale in interval]
                for interval in continuity_scales
            ],
        })
    reactions = tuple(transport.reactions)
    nr = len(reactions)
    species_index, stoich, forward_knots, reverse_knots = _stoichiometry(transport)
    n_concentration = ns * nc
    n_aux = ns + (ns if nr else 0)  # integrated mouth transfer plus reaction source inventory
    y0 = np.concatenate((initial.reshape(-1), np.zeros(n_aux)))
    evaluations = 0
    max_current_residual = 0.0

    def interval_and_fraction(t: float, interval_hint: int):
        k = interval_hint
        duration = times[k + 1] - times[k]
        fraction = min(max((t - times[k]) / duration, 0.0), 1.0)
        return k, fraction, duration

    def interp(a: np.ndarray, k: int, fraction: float) -> np.ndarray:
        return a[k] + fraction * (a[k + 1] - a[k])

    def fields(t: float, interval_hint: int):
        k, f, duration = interval_and_fraction(t, interval_hint)
        mouth_c = interp(boundary.T, k, f)
        logg_cells = np.log(gamma_cells)
        logg_mouth = np.log(gamma_mouth)
        velocity = interp(velocity_knots.T, k, f)
        areas_c = interp(cell_area, k, f)
        areas_f = interp(face_area, k, f)
        darea_dt = (cell_area[k + 1] - cell_area[k]) / duration
        forward = reverse = np.empty((0,), dtype=float)
        if nr:
            forward = np.exp(np.log(forward_knots[:, k]) + f * (np.log(forward_knots[:, k + 1]) - np.log(forward_knots[:, k])))
            reverse = np.exp(np.log(reverse_knots[:, k]) + f * (np.log(reverse_knots[:, k + 1]) - np.log(reverse_knots[:, k])))
        return mouth_c, interp(logg_cells, k, f), interp(logg_mouth, k, f), velocity, areas_c, areas_f, darea_dt, forward, reverse

    def rhs(t: float, state: np.ndarray, interval_hint: int) -> np.ndarray:
        nonlocal evaluations, max_current_residual
        evaluations += 1
        if evaluations > transport.maximum_function_evaluations:
            raise RuntimeError("maximum_function_evaluations_exceeded")
        concentration = state[:n_concentration].reshape(ns, nc)
        nonnegative = np.maximum(concentration, 0.0)
        mouth_c, logg, mouth_logg, velocity, areas_c, areas_f, darea_dt, forward, reverse = fields(t, interval_hint)
        grad_c = np.zeros((ns, nc + 1), dtype=float)
        face_c = np.zeros_like(grad_c)
        grad_lng = np.zeros_like(grad_c)
        grad_c[:, 0] = (concentration[:, 0] - mouth_c) / (0.5 * dx)
        face_c[:, 0] = 0.5 * (nonnegative[:, 0] + mouth_c)
        grad_lng[:, 0] = (logg[:, 0] - mouth_logg) / (0.5 * dx)
        grad_c[:, 1:nc] = (concentration[:, 1:] - concentration[:, :-1]) / dx
        face_c[:, 1:nc] = 0.5 * (nonnegative[:, 1:] + nonnegative[:, :-1])
        grad_lng[:, 1:nc] = (logg[:, 1:] - logg[:, :-1]) / dx
        upwind = np.where(velocity[None, :] >= 0.0,
                          np.concatenate((np.broadcast_to(mouth_c[:, None], (ns, 1)), nonnegative), axis=1),
                          np.concatenate((nonnegative, np.zeros((ns, 1))), axis=1))
        denominator = np.sum((z[:, None] ** 2) * diffusivity[:, None] * face_c, axis=0)
        baseline = grad_c + face_c * grad_lng
        numerator = -np.sum(z[:, None] * diffusivity[:, None] * baseline, axis=0) + np.sum(
            z[:, None] * velocity[None, :] * upwind, axis=0
        )
        if np.any((denominator <= 0.0) & (np.abs(numerator) > 0.0)):
            raise RuntimeError("zero_ionic_mobility_cannot_close_face_current")
        dpsi = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0.0)
        flux_density = -diffusivity[:, None] * (baseline + z[:, None] * face_c * dpsi) + velocity[None, :] * upwind
        flux_density[:, -1] = 0.0
        max_current_residual = max(max_current_residual,
                                   float(np.max(np.abs(np.sum(z[:, None] * flux_density, axis=0)))))
        molar_face_rate = flux_density * areas_f[None, :]
        volume = areas_c * dx
        dcdt = -(molar_face_rate[:, 1:] - molar_face_rate[:, :-1]) / volume[None, :]
        dcdt -= concentration * (darea_dt / areas_c)[None, :]
        mouth_rate = molar_face_rate[:, 0]
        if nr:
            activity = np.exp(logg) * nonnegative / transport.concentration_standard_state_mol_m3
            rates = np.empty((nr, nc), dtype=float)
            for j, reaction in enumerate(reactions):
                fwd_product = np.ones(nc, dtype=float)
                rev_product = np.ones(nc, dtype=float)
                for term in reaction.reactants:
                    fwd_product *= activity[species_index[term.species_id]] ** term.coefficient
                for term in reaction.products:
                    rev_product *= activity[species_index[term.species_id]] ** term.coefficient
                rates[j] = forward[j] * fwd_product - reverse[j] * rev_product
            if not np.isfinite(rates).all():
                raise RuntimeError("nonfinite_activity_mass_action_rate")
            source = stoich @ rates
            dcdt += source
            reaction_rate = np.sum(source * volume[None, :], axis=1)
            return np.concatenate((dcdt.reshape(-1), mouth_rate, reaction_rate))
        return np.concatenate((dcdt.reshape(-1), mouth_rate))

    accepted_states = [y0.copy()]
    for k in range(nt - 1):
        try:
            solution = solve_ivp(
                lambda time_s, state, interval=k: rhs(time_s, state, interval),
                (float(times[k]), float(times[k + 1])), y0, method="BDF",
                t_eval=(float(times[k]), float(times[k + 1])),
                rtol=transport.relative_tolerance, atol=transport.absolute_tolerance_mol_m3,
                max_step=transport.maximum_step_s,
            )
        except (RuntimeError, FloatingPointError, ValueError, OverflowError) as error:
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "reason": str(error), "failed_interval_index": k,
                "committed_knot_count": len(accepted_states), "function_evaluations": evaluations,
                "accepted_state_prefix": [
                    {rows[i].species_id: [float(value) for value in state[i * nc:(i + 1) * nc]] for i in range(ns)}
                    for state in accepted_states
                ],
            })
        if not solution.success or solution.y.shape[1] != 2:
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "reason": "stiff_integrator_failed",
                "solver_message": solution.message, "failed_interval_index": k,
                "committed_knot_count": len(accepted_states), "function_evaluations": evaluations,
            })
        y0 = solution.y[:, -1].copy()
        accepted_states.append(y0)
    state_matrix = np.column_stack(accepted_states)
    concentration = state_matrix[:n_concentration].reshape(ns, nc, nt)
    if not np.isfinite(concentration).all() or float(np.min(concentration)) < -1e-7 * max(float(np.max(initial)), 1.0):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "nonphysical_negative_concentration_from_numerical_integration",
            "minimum_concentration_mol_m3": float(np.min(concentration)),
        })
    volumes = cell_area * dx
    inventory = np.empty((ns, nt), dtype=float)
    charge = np.empty((nt, nc), dtype=float)
    for k in range(nt):
        inventory[:, k] = np.sum(np.maximum(concentration[:, :, k], 0.0) * volumes[k][None, :], axis=1)
        charge[k] = np.einsum("s,sc->c", z, concentration[:, :, k])
    cumulative_mouth = state_matrix[n_concentration:n_concentration + ns]
    cumulative_reaction = state_matrix[n_concentration + ns:n_concentration + 2 * ns] if nr else np.zeros((ns, nt))
    residual = inventory - inventory[:, [0]] - cumulative_mouth - cumulative_reaction + cumulative_reaction[:, [0]]
    allowed = (transport.absolute_tolerance_mol_m3 * np.max(np.sum(volumes, axis=1))
               + transport.relative_tolerance * np.maximum(np.max(inventory, axis=1), 1e-30))
    if np.any(np.max(np.abs(residual), axis=1) > allowed):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "variable_volume_species_inventory_balance_tolerance_exceeded",
            "finite_volume_inventory_balance_residual_mol_by_species": {
                rows[i].species_id: [float(value) for value in residual[i]] for i in range(ns)
            },
        })
    charge_scale = max(float(np.max(np.einsum("s,sct->tc", np.abs(z), np.maximum(concentration, 0.0)))), 1e-30)
    max_charge = float(np.max(np.abs(charge)))
    if max_charge > 1e-7 * charge_scale:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "local_electroneutrality_residual_tolerance_exceeded",
            "peak_absolute_local_charge_residual_mol_eq_m3": max_charge,
        })
    states = []
    for k, time_s in enumerate(times):
        states.append({
            "time_s": float(time_s),
            "species_concentration_mol_m3_by_id": {
                rows[i].species_id: [float(value) for value in concentration[i, :, k]] for i in range(ns)
            },
            "species_inventory_mol_by_id": {rows[i].species_id: float(inventory[i, k]) for i in range(ns)},
            "cell_volume_m3_by_cell": [float(value) for value in volumes[k]],
            "local_charge_residual_mol_eq_m3_by_cell": [float(value) for value in charge[k]],
        })
    values = {
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": transport.asset_id,
        "physical_scope_id": transport.physical_scope_id,
        "clock_id": transport.clock_id,
        "provider_id": transport.provider_id,
        "provider_revision": transport.provider_revision,
        "input_sha256": digest,
        "transport_request_sha256": canonical_digest(transport.model_dump(mode="json")),
        "geometry_id": request.geometry_id,
        "area_provider_id": request.area_provider_id,
        "area_provider_revision": request.area_provider_revision,
        "area_configuration_sha256": request.area_configuration_sha256,
        "area_history_sha256": request.area_history_sha256,
        "volume_flow_continuity_residual_m3_s_by_interval_and_cell": continuity_residuals,
        "cell_cross_section_area_m2_by_knot": [list(row) for row in request.cell_cross_section_area_m2_by_knot],
        "face_cross_section_area_m2_by_knot": [list(row) for row in request.face_cross_section_area_m2_by_knot],
        "finite_volume_inventory_balance_residual_mol_by_species": {
            rows[i].species_id: [float(value) for value in residual[i]] for i in range(ns)
        },
        "integrated_mouth_transfer_mol_by_species": {
            rows[i].species_id: [float(value) for value in cumulative_mouth[i]] for i in range(ns)
        },
        "integrated_reaction_source_mol_by_species": {
            rows[i].species_id: [float(value) for value in cumulative_reaction[i]] for i in range(ns)
        },
        "peak_absolute_local_charge_residual_mol_eq_m3": max_charge,
        "peak_zero_current_residual_mol_eq_m2_s": max_current_residual,
        "minimum_accepted_concentration_mol_m3": float(np.min(concentration)),
        "function_evaluations": evaluations,
        "state_history": states,
        "area_interpolation": "piecewise_linear_between_exact_caller_knots",
        "cell_balance": "d(C*cell_area*dx)/dt = inward_face_area_flux - outward_face_area_flux + reaction_source*cell_volume",
        "interpretation": "caller_variable_area_finite_volume_activity_reactive_transport",
        "limitations": [
            "Cell-volume change contributes conservative concentration dilution/concentration through d(CV)/dt; fluid mechanics and wall-motion-induced velocity are not solved.",
            "Cell and face areas are caller histories, linearly interpolated between exact knots; no geometry feedback or area prediction is performed.",
            "Local electroneutrality and zero-current closure are retained from the scalar-area solver and assume one common ionic face area at each face.",
            "Activity fields, diffusivities, boundaries and reaction rates remain caller inputs; automatic speciation and phase selection are absent.",
            "Inventory/current/charge residuals are numerical diagnostics, not physical validation or qualification.",
        ],
    }
    return Calculation(values=values)


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=VariableAreaCreviceActivityReactiveTransportRequest,
        evaluator=evaluate_variable_area_crevice_activity_transport,
        units={
            "cell_cross_section_area_m2_by_knot[][]": "m^2",
            "face_cross_section_area_m2_by_knot[][]": "m^2",
            "state_history[].cell_volume_m3_by_cell[]": "m^3",
            "state_history[].species_concentration_mol_m3_by_id.*[]": "mol/m^3",
            "state_history[].species_inventory_mol_by_id.*": "mol",
            "integrated_mouth_transfer_mol_by_species.*[]": "mol",
            "integrated_reaction_source_mol_by_species.*[]": "mol",
            "finite_volume_inventory_balance_residual_mol_by_species.*[]": "mol",
        },
        assumptions=(
            "Concentration state is advanced through the conservative cell-mole balance using linearly interpolated caller cell volumes and face areas.",
            "One common face area multiplies all ionic species fluxes at a given face; zero-current closure is therefore imposed on flux density.",
            "The nested activity request supplies reaction, species and activity-coefficient schedules on the same exact knots.",
        ),
        source_ids=(AREA_HISTORY_SOURCE_ID, METHOD_SOURCE_ID, "caller_crevice_activity_corrected_transport_species",
                    "caller_crevice_activity_coefficient_cell_time_fields", "caller_crevice_activity_corrected_mouth_boundary_history",
                    "caller_activity_based_crevice_reaction_network", "scipy_integrate_bdf"),
    ),)
