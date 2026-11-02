"""Current-carrying variable-area Nernst–Planck transport coupled to mixed-potential Faradaic branches."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .registry import ModelSpec
from .crevice_faradaic_spatial_chemistry_coupling import (
    CreviceFaradaicSpatialChemistryRequest,
    _mixed_potential_at_knot,
    _rebind_evidence,
    _system_element_total,
)
from .crevice_spatial_chemistry_transport import _chemistry_at_knot, _subinterval_request
from .crevice_spatial_ohmic_mixed_potential import solve_crevice_spatial_ohmic_mixed_potential
from .crevice_variable_area_activity_transport import VariableAreaCreviceActivityReactiveTransportRequest
from .crevice_spatial_ohmic_mixed_potential import FARADAY_CONSTANT_C_MOL, GAS_CONSTANT_J_MOL_K
from .models.aqueous_activity_iteration import (
    AqueousBdotIteration,
    build_bdot_transport_activity_callback,
)

MODEL_ID = "integration.crevice_current_carrying_np_faradaic"
METHOD_SOURCE_ID = "finite_volume_current_carrying_activity_nernst_planck_with_faradaic_wall_balance"
CURRENT_CLOSURE_SOURCE_ID = "mixed_potential_face_current_to_ionic_nernst_planck_flux_closure"
FARADAIC_ENDPOINT_SOURCE_ID = "endpoint_trapezoid_faradaic_inventory_split"
FARADAIC_STAGE_SOURCE_ID = "endpoint_linear_branch_current_bdf_stage_inventory_source"
FARADAIC_STAGE_MIXED_POTENTIAL_SOURCE_ID = "bdf_stage_spatial_ohmic_mixed_potential_and_faradaic_source"
FARADAIC_STAGE_BDOT_ACTIVITY_SOURCE_ID = "caller_evidence_bound_bdot_activity_refresh_at_bdf_stages"


class CreviceCurrentCarryingNernstPlanckRequest(Contract):
    schema_version: Literal["matintegrity.crevice_current_carrying_np_faradaic.v1"] = (
        "matintegrity.crevice_current_carrying_np_faradaic.v1"
    )
    assessment_id: str = Field(min_length=1)
    faradaic_coupling: CreviceFaradaicSpatialChemistryRequest
    maximum_interval_fixed_point_iterations: int = Field(default=30, ge=2, le=1000)
    maximum_total_transport_function_evaluations: int = Field(default=5_000_000, ge=100, le=20_000_000)
    maximum_total_mixed_potential_function_evaluations: int = Field(default=2_000_000, ge=100, le=20_000_000)
    maximum_total_bdot_stage_activity_evaluations: int = Field(default=2_000_000, ge=100, le=20_000_000)
    absolute_face_current_closure_tolerance_A: Positive = 1e-8
    relative_face_current_closure_tolerance: Positive = Field(default=1e-7, le=1e-3)
    absolute_potential_fixed_point_tolerance_V: Positive = 1e-9
    relative_potential_fixed_point_tolerance: Positive = Field(default=1e-7, le=1e-3)
    absolute_branch_current_fixed_point_tolerance_A_m2: Positive = 1e-9
    relative_branch_current_fixed_point_tolerance: Positive = Field(default=1e-7, le=1e-3)
    relative_chemistry_fixed_point_tolerance: Positive = Field(default=1e-8, le=1e-3)
    absolute_charge_inventory_tolerance_mol_eq: Positive = 1e-10
    relative_charge_inventory_tolerance: Positive = Field(default=1e-8, le=1e-3)
    relaxation_fraction: Positive = Field(default=0.5, le=1.0)
    potential_gauge_cell_index: Literal[0] = 0
    mouth_electrical_boundary: Literal["insulated_zero_current"] = "insulated_zero_current"
    blind_tip_electrical_boundary: Literal["insulated_zero_current"] = "insulated_zero_current"
    np_current_matches_mixed_potential_sign_convention_reviewed: bool
    local_charge_storage_excluded_and_faradaic_source_closes_reviewed: bool
    potential_gauge_and_insulated_end_conditions_reviewed: bool
    face_area_current_density_and_mixed_potential_mesh_mapping_reviewed: bool
    computation_scope_and_solver_budgets_reviewed: bool
    computational_use_authorized: bool
    faradaic_source_integration_mode: Literal[
        "endpoint_trapezoid",
        "bdf_stage_linear_current",
        "bdf_stage_spatial_mixed_potential",
    ] = "endpoint_trapezoid"
    bdf_stage_linear_current_source_reviewed: bool = False
    bdf_stage_spatial_mixed_potential_reviewed: bool = False
    bdf_stage_bdot_activity_by_interval: tuple[AqueousBdotIteration, ...] | None = None
    bdf_stage_bdot_activity_reviewed: bool = False

    @model_validator(mode="after")
    def validate_electrical_mesh(self):
        coupling = self.faradaic_coupling
        transport = coupling.transport_chemistry.transport.transport_request
        mixed = coupling.mixed_potential_template
        if len(mixed.cell_ids) != transport.cell_count:
            raise ValueError("mixed-potential and Nernst–Planck cell counts must match")
        if mixed.cell_ids != tuple(cell.cell_id for cell in coupling.transport_chemistry.chemistry_by_knot[0].cells):
            raise ValueError("cell identity/order must match the knot chemistry path")
        if not all((self.np_current_matches_mixed_potential_sign_convention_reviewed,
                    self.local_charge_storage_excluded_and_faradaic_source_closes_reviewed,
                    self.potential_gauge_and_insulated_end_conditions_reviewed,
                    self.face_area_current_density_and_mixed_potential_mesh_mapping_reviewed,
                    self.computation_scope_and_solver_budgets_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all current, charge, gauge, mesh and applicability reviews are required")
        if (self.faradaic_source_integration_mode in (
                    "bdf_stage_linear_current", "bdf_stage_spatial_mixed_potential")
                and not self.bdf_stage_linear_current_source_reviewed):
            raise ValueError("BDF-stage Faradaic source integration requires explicit caller review")
        if (self.faradaic_source_integration_mode == "bdf_stage_spatial_mixed_potential"
                and not self.bdf_stage_spatial_mixed_potential_reviewed):
            raise ValueError("BDF-stage spatial mixed-potential solves require explicit caller review")
        if self.bdf_stage_bdot_activity_by_interval is not None:
            if self.faradaic_source_integration_mode != "bdf_stage_spatial_mixed_potential":
                raise ValueError("B-dot stage activity refresh is supported only with the spatial BDF-stage mixed-potential mode")
            if not self.bdf_stage_bdot_activity_reviewed:
                raise ValueError("B-dot stage activity refresh requires explicit caller review")
            if len(self.bdf_stage_bdot_activity_by_interval) != len(transport.output_time_s) - 1:
                raise ValueError("provide exactly one reviewed B-dot parameter request per transport interval")
            species_rows = transport.species
            species_ids = tuple(row.species_id for row in species_rows)
            charges = tuple(row.charge_number for row in species_rows)
            for interval, bdot in enumerate(self.bdf_stage_bdot_activity_by_interval):
                system_ids = tuple(row.species_id for row in bdot.system.species)
                system_charges = tuple(row.charge_number for row in bdot.system.species)
                if system_ids != species_ids or system_charges != charges:
                    raise ValueError("B-dot interval species identities, order and charges must exactly match transport")
                interval_temperatures = transport.temperature_K_by_knot[interval:interval + 2]
                if any(value != bdot.system.temperature_K or value != bdot.parameter_temperature_K
                       for value in interval_temperatures):
                    raise ValueError("B-dot stage parameters require constant interval temperature exactly matching both the reviewed system and parameter temperatures")
                # Validate the existing adapter's evidence and standard-state/applicability contract up front.
                build_bdot_transport_activity_callback(
                    bdot, transport_species_ids=species_ids, temperature_K=bdot.system.temperature_K
                )
        elif self.bdf_stage_bdot_activity_reviewed:
            raise ValueError("B-dot stage review cannot be enabled without interval parameter requests")
        return self


def _solve_spatial_mixed_potential_at_stage(
    base: CreviceFaradaicSpatialChemistryRequest,
    sub_variable: VariableAreaCreviceActivityReactiveTransportRequest,
    interval_index: int,
    fraction: float,
    concentration_mol_m3: np.ndarray,
    log_gamma: np.ndarray,
    maximum_solver_evaluations: int,
    *,
    solve_mixed_potential: bool = True,
):
    """Rebuild caller conductivity/Nernst inputs and solve the spatial BV balance at one BDF stage."""
    coupled = base.transport_chemistry
    transport = sub_variable.transport_request
    template = base.mixed_potential_template
    species_ids = [row.species_id for row in transport.species]
    species_index = {species_id: i for i, species_id in enumerate(species_ids)}
    if concentration_mol_m3.shape != (len(species_ids), transport.cell_count):
        raise ArithmeticError("BDF-stage concentration field does not align with declared species/cells")
    if log_gamma.shape != concentration_mol_m3.shape:
        raise ArithmeticError("BDF-stage activity coefficients do not align with concentration fields")
    if not np.isfinite(concentration_mol_m3).all() or np.any(concentration_mol_m3 <= 0.0):
        raise ArithmeticError("BDF-stage Nernst solve requires positive finite aqueous concentrations")
    full_transport = coupled.transport.transport_request
    if not 0 <= interval_index < len(full_transport.output_time_s) - 1:
        raise ArithmeticError("BDF-stage interval index is outside the exact hydraulic/chemistry clock")
    left_time = full_transport.output_time_s[interval_index]
    right_time = full_transport.output_time_s[interval_index + 1]
    stage_time = left_time + fraction * (right_time - left_time)
    left_temperature = transport.temperature_K_by_knot[0]
    right_temperature = transport.temperature_K_by_knot[1]
    temperature = left_temperature + fraction * (right_temperature - left_temperature)
    if not math.isfinite(temperature) or temperature <= 0.0:
        raise ArithmeticError("BDF-stage temperature is outside positive finite support")

    conductivity = np.asarray(
        [
            base.background_conductivity_S_m_by_knot_and_cell[interval_index][cell]
            + fraction
            * (
                base.background_conductivity_S_m_by_knot_and_cell[interval_index + 1][cell]
                - base.background_conductivity_S_m_by_knot_and_cell[interval_index][cell]
            )
            + math.fsum(
                (
                    base.molar_conductivity_S_m2_mol_by_species_knot_and_cell[species_id][interval_index][cell]
                    + fraction
                    * (
                        base.molar_conductivity_S_m2_mol_by_species_knot_and_cell[species_id][interval_index + 1][cell]
                        - base.molar_conductivity_S_m2_mol_by_species_knot_and_cell[species_id][interval_index][cell]
                    )
                )
                * concentration_mol_m3[species_index[species_id], cell]
                for species_id in species_ids
            )
            for cell in range(transport.cell_count)
        ],
        dtype=float,
    )
    if not np.isfinite(conductivity).all() or np.any(conductivity <= 0.0):
        raise ArithmeticError("stage-composition conductivity is nonpositive or nonfinite")

    nernst_by_id = {row.reaction_id: row for row in base.nernst_branch_maps}
    branches = []
    standard_state = transport.concentration_standard_state_mol_m3
    for branch in template.branches:
        mapping = nernst_by_id[branch.reaction_id]
        equilibrium_potential = []
        for cell in range(transport.cell_count):
            log_quotient = math.fsum(
                coefficient
                * (
                    log_gamma[species_index[species_id], cell]
                    + math.log(concentration_mol_m3[species_index[species_id], cell] / standard_state)
                )
                for species_id, coefficient in mapping.log_quotient_coefficient_by_species.items()
            )
            standard_potential = mapping.standard_potential_V_by_cell_and_knot[cell][interval_index]
            standard_potential += fraction * (
                mapping.standard_potential_V_by_cell_and_knot[cell][interval_index + 1] - standard_potential
            )
            equilibrium_potential.append(
                standard_potential
                - GAS_CONSTANT_J_MOL_K * temperature / (branch.electron_number * FARADAY_CONSTANT_C_MOL)
                * log_quotient
            )
        branches.append(
            branch.model_copy(
                update={
                    "equilibrium_potential_V_by_cell_and_time": tuple(
                        (float(value),) for value in equilibrium_potential
                    )
                }
            )
        )

    cell_area = np.asarray(sub_variable.cell_cross_section_area_m2_by_knot, dtype=float)
    areas = cell_area[0] + fraction * (cell_area[1] - cell_area[0])
    apertures = areas / template.slit_width_m
    if not np.isfinite(apertures).all() or np.any(apertures <= 0.0):
        raise ArithmeticError("BDF-stage slit geometry is nonpositive or nonfinite")
    geometry_payload = {
        "geometry_id": coupled.transport.geometry_id,
        "area_history_sha256": coupled.transport.area_history_sha256,
        "interval_index": interval_index,
        "stage_fraction": fraction,
        "time_s": stage_time,
        "cell_ids": list(template.cell_ids),
        "cell_lengths_m": list(template.cell_lengths_m),
        "cell_apertures_m": [float(value) for value in apertures],
        "slit_width_m": template.slit_width_m,
    }
    geometry_sha = canonical_digest(geometry_payload)
    conductivity_sha = canonical_digest(
        {
            "conductivity_record_sha256": base.conductivity_record_sha256,
            "interval_index": interval_index,
            "stage_fraction": fraction,
            "time_s": stage_time,
            "conductivity_S_m_by_cell": conductivity.tolist(),
        }
    )
    evidence = _rebind_evidence(
        template.evidence,
        template.geometry_provider_id,
        template.geometry_sha256,
        geometry_sha,
    )
    evidence = _rebind_evidence(
        evidence,
        template.conductivity_provider_id,
        template.conductivity_sha256,
        conductivity_sha,
    )
    stage_template = template.model_copy(
        update={
            "time_s": (stage_time,),
            "cell_apertures_m": tuple(float(value) for value in apertures),
            "temperature_K_by_time": (temperature,),
            "electrolyte_conductivity_S_m_by_cell_and_time": tuple((float(value),) for value in conductivity),
            "branches": tuple(branches),
            "geometry_sha256": geometry_sha,
            "conductivity_sha256": conductivity_sha,
            "evidence": evidence,
            "maximum_solver_evaluations": min(template.maximum_solver_evaluations, maximum_solver_evaluations),
        }
    )
    if not solve_mixed_potential:
        return None, stage_template
    stage_result = solve_crevice_spatial_ohmic_mixed_potential(stage_template)
    return stage_result, stage_template


def _integrate_current_carrying_interval(
    base: CreviceFaradaicSpatialChemistryRequest,
    sub_variable: VariableAreaCreviceActivityReactiveTransportRequest,
    left_mixed: Calculation,
    right_solution_potential_V: np.ndarray,
    right_face_current_A: np.ndarray,
    right_branch_current_A_m2: dict[str, np.ndarray],
    integrate_faradaic_at_stages: bool,
    solve_mixed_potential_at_stages: bool,
    stage_bdot_activity: AqueousBdotIteration | None,
    interval_index: int,
    evaluation_budget: int,
    mixed_potential_evaluation_budget: int,
    bdot_activity_evaluation_budget: int,
    current_abs_tol: float,
    current_rel_tol: float,
    charge_abs_tol: float,
    charge_rel_tol: float,
):
    """Integrate species moles and optionally stage-resolved wall extents using ionic face current."""
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return None, {"status": "needs_data", "reason": "scipy_runtime_unavailable",
                      "function_evaluations": 0, "mixed_potential_function_evaluations": 0}
    tr = sub_variable.transport_request
    times = np.asarray(tr.output_time_s, dtype=float)
    duration = float(times[1] - times[0])
    nc, ns = tr.cell_count, len(tr.species)
    dx = tr.length_m / nc
    rows = tr.species
    ids = [row.species_id for row in rows]
    index = {sid: i for i, sid in enumerate(ids)}
    z = np.asarray([row.charge_number for row in rows], dtype=float)
    diffusivity = np.asarray([row.diffusivity_m2_s for row in rows], dtype=float)
    initial = np.asarray([row.initial_cell_concentration_mol_m3 for row in rows], dtype=float)
    boundary = np.asarray([tr.mouth_boundary_concentration_mol_m3_by_species[row.species_id] for row in rows], dtype=float)
    log_gamma = np.log(np.asarray([row.activity_coefficient_by_time_and_cell for row in rows], dtype=float))
    mouth_log_gamma = np.log(np.asarray([row.mouth_activity_coefficient_by_time for row in rows], dtype=float))
    stage_activity_callback = None
    if stage_bdot_activity is not None:
        stage_activity_callback = build_bdot_transport_activity_callback(
            stage_bdot_activity,
            transport_species_ids=tuple(ids),
            temperature_K=float(stage_bdot_activity.system.temperature_K),
        )
    velocity_knots = np.asarray(tr.cell_face_axial_velocity_m_s_by_knot, dtype=float)
    cell_area = np.asarray(sub_variable.cell_cross_section_area_m2_by_knot, dtype=float)
    face_area = np.asarray(sub_variable.face_cross_section_area_m2_by_knot, dtype=float)
    left_state = left_mixed.values["state_history"][0]
    phi_left = np.asarray(left_state["solution_potential_V_by_cell_relative_to_cell_0"], dtype=float)
    current_left = np.asarray(left_state["electrolyte_face_current_A_by_cell_boundary"], dtype=float)
    phi_right = np.asarray(right_solution_potential_V, dtype=float)
    current_right = np.asarray(right_face_current_A, dtype=float)
    reactions = tuple(tr.reactions)
    nr = len(reactions)
    stoich = np.zeros((ns, nr), dtype=float)
    forward_knots = np.empty((nr, 2), dtype=float)
    reverse_knots = np.empty((nr, 2), dtype=float)
    for j, reaction in enumerate(reactions):
        for term in reaction.reactants:
            stoich[index[term.species_id], j] -= term.coefficient
        for term in reaction.products:
            stoich[index[term.species_id], j] += term.coefficient
        forward_knots[j] = reaction.forward_rate_constant_mol_m3_s_by_knot
        reverse_knots[j] = reaction.reverse_rate_constant_mol_m3_s_by_knot
    n_state = ns * nc
    faradaic_maps = tuple(base.faradaic_branch_maps)
    faradaic_ids = tuple(row.reaction_id for row in faradaic_maps)
    left_branches = {
        row["reaction_id"]: np.asarray(row["signed_current_density_A_m2_by_cell"], dtype=float)
        for row in left_state["reaction_branches"]
    }
    if set(left_branches) != set(faradaic_ids) or set(right_branch_current_A_m2) != set(faradaic_ids):
        return None, {"status": "needs_data", "reason": "faradaic_branch_current_identity_mismatch",
                      "function_evaluations": 0, "mixed_potential_function_evaluations": 0}
    right_branches = {key: np.asarray(value, dtype=float) for key, value in right_branch_current_A_m2.items()}
    if any(value.shape != (nc,) or not np.isfinite(value).all() for value in right_branches.values()):
        return None, {"status": "needs_data", "reason": "faradaic_branch_current_shape_or_finiteness_mismatch",
                      "function_evaluations": 0, "mixed_potential_function_evaluations": 0}
    extent_offset = n_state + 2 * ns
    # Diagnostics integrate mouth transfer, homogeneous source, and continuous branch extents.
    state0 = np.concatenate((initial.reshape(-1), np.zeros(2 * ns + len(faradaic_maps) * nc)))
    evaluations = 0
    stage_mixed_evaluations = 0
    stage_bdot_evaluations = 0
    maximum_face_current_residual_A = 0.0
    maximum_current_scale_A = 0.0
    maximum_charge_balance_residual_rate_mol_eq_s = 0.0

    def interpolate(a, fraction):
        return a[0] + fraction * (a[1] - a[0])

    def rhs(time_s, state):
        nonlocal evaluations, maximum_face_current_residual_A, maximum_current_scale_A
        nonlocal maximum_charge_balance_residual_rate_mol_eq_s, stage_mixed_evaluations
        nonlocal stage_bdot_evaluations
        evaluations += 1
        if evaluations > evaluation_budget:
            raise RuntimeError("current_carrying_transport_function_evaluation_budget_exceeded")
        fraction = min(max((time_s - times[0]) / duration, 0.0), 1.0)
        c = state[:n_state].reshape(ns, nc)
        mobile = np.maximum(c, 0.0)
        mouth_c = interpolate(boundary, fraction)
        lngamma = interpolate(log_gamma, fraction)
        mouth_lngamma = interpolate(mouth_log_gamma, fraction)
        if stage_activity_callback is not None:
            # One callback evaluation refreshes all cells and the mouth with the same
            # trial composition before NP fluxes, homogeneous rates and electrode Nernst.
            stage_bdot_evaluations += 1
            if stage_bdot_evaluations > bdot_activity_evaluation_budget:
                raise RuntimeError("stage_bdot_activity_evaluation_budget_exceeded")
            stage_gamma = stage_activity_callback(
                float(time_s), np.column_stack((mouth_c, mobile))
            )
            lngamma = np.log(stage_gamma[:, 1:])
            mouth_lngamma = np.log(stage_gamma[:, 0])
        velocity = interpolate(velocity_knots, fraction)
        areas_cell = interpolate(cell_area, fraction)
        areas_face = interpolate(face_area, fraction)
        darea_dt = (cell_area[1] - cell_area[0]) / duration
        stage_branch_current = None
        if solve_mixed_potential_at_stages:
            remaining_mixed = mixed_potential_evaluation_budget - stage_mixed_evaluations
            if remaining_mixed < 100:
                raise RuntimeError("stage_mixed_potential_function_evaluation_budget_exhausted")
            stage_mixed, stage_request = _solve_spatial_mixed_potential_at_stage(
                base,
                sub_variable,
                interval_index,
                fraction,
                c,
                lngamma,
                remaining_mixed,
            )
            stage_mixed_evaluations += int(stage_mixed.values.get("solver_function_evaluations", 0))
            if stage_mixed.status != "computed":
                raise RuntimeError(
                    "stage_spatial_mixed_potential_failed: "
                    + str(stage_mixed.values.get("reason", stage_mixed.status))
                )
            if stage_mixed_evaluations > mixed_potential_evaluation_budget:
                raise RuntimeError("stage_mixed_potential_function_evaluation_budget_exceeded")
            stage_state = stage_mixed.values["state_history"][0]
            phi = np.asarray(stage_state["solution_potential_V_by_cell_relative_to_cell_0"], dtype=float)
            target_current = np.asarray(stage_state["electrolyte_face_current_A_by_cell_boundary"], dtype=float)
            stage_branch_current = {
                row["reaction_id"]: np.asarray(row["signed_current_density_A_m2_by_cell"], dtype=float)
                for row in stage_state["reaction_branches"]
            }
            temperature = float(stage_request.temperature_K_by_time[0])
        else:
            phi = phi_left + fraction * (phi_right - phi_left)
            target_current = current_left + fraction * (current_right - current_left)
            temperature = float(tr.temperature_K_by_knot[0])
        thermal_factor = FARADAY_CONSTANT_C_MOL / (GAS_CONSTANT_J_MOL_K * temperature)

        grad_c = np.zeros((ns, nc + 1), dtype=float)
        face_c = np.zeros_like(grad_c)
        grad_lng = np.zeros_like(grad_c)
        grad_c[:, 0] = (c[:, 0] - mouth_c) / (0.5 * dx)
        face_c[:, 0] = 0.5 * (mobile[:, 0] + mouth_c)
        grad_lng[:, 0] = (lngamma[:, 0] - mouth_lngamma) / (0.5 * dx)
        grad_c[:, 1:nc] = (c[:, 1:] - c[:, :-1]) / dx
        face_c[:, 1:nc] = 0.5 * (mobile[:, 1:] + mobile[:, :-1])
        grad_lng[:, 1:nc] = (lngamma[:, 1:] - lngamma[:, :-1]) / dx
        upwind = np.where(velocity[None, :] >= 0.0,
                          np.concatenate((np.broadcast_to(mouth_c[:, None], (ns, 1)), mobile), axis=1),
                          np.concatenate((mobile, np.zeros((ns, 1))), axis=1))
        baseline = grad_c + face_c * grad_lng
        denominator = np.sum((z[:, None] ** 2) * diffusivity[:, None] * face_c, axis=0)
        non_migration_current = -np.sum(z[:, None] * diffusivity[:, None] * baseline, axis=0) \
            + np.sum(z[:, None] * velocity[None, :] * upwind, axis=0)
        flux_density = np.zeros((ns, nc + 1), dtype=float)
        # At the mouth, impose the declared electrically insulated boundary (I=0) by a local migration solve.
        if denominator[0] <= 0.0 and abs(non_migration_current[0]) > 0.0:
            raise RuntimeError("mouth_face_has_zero_ionic_mobility_but_nonzero_diffusive_current")
        dpsi_mouth = non_migration_current[0] / denominator[0] if denominator[0] > 0.0 else 0.0
        flux_density[:, 0] = -diffusivity * (baseline[:, 0] + z * face_c[:, 0] * dpsi_mouth) \
            + velocity[0] * upwind[:, 0]
        # Internal faces use the mixed-potential electrolyte voltage gradient, not a zero-current closure.
        for face in range(1, nc):
            if denominator[face] <= 0.0:
                if abs(target_current[face]) > current_abs_tol:
                    raise RuntimeError("internal_face_has_zero_ionic_mobility_but_nonzero_mixed_current")
                dpsi = 0.0
            else:
                dpsi = thermal_factor * (phi[face] - phi[face - 1]) / dx
            flux_density[:, face] = -diffusivity * (baseline[:, face] + z * face_c[:, face] * dpsi) \
                + velocity[face] * upwind[:, face]
        # The sealed end has no ionic or advective transfer.
        flux_density[:, -1] = 0.0
        actual_current = FARADAY_CONSTANT_C_MOL * np.sum(z[:, None] * flux_density, axis=0) * areas_face
        residual = actual_current - target_current
        allowed = current_abs_tol + current_rel_tol * np.maximum(np.abs(actual_current), np.abs(target_current))
        maximum_face_current_residual_A = max(maximum_face_current_residual_A,
                                               float(np.max(np.abs(residual[1:nc]))))
        maximum_current_scale_A = max(maximum_current_scale_A, float(np.max(np.abs(target_current[1:nc]))))
        if np.any(np.abs(residual[1:nc]) > 1000.0 * allowed[1:nc]):
            # Keep trial iterates alive for the outer fixed point, but reject gross constitutive incompatibility.
            raise RuntimeError("mixed_potential_current_and_Nernst_Planck_flux_are_incompatible")
        molar_face_rate = flux_density * areas_face[None, :]
        volume = areas_cell * dx
        dcdt = -(molar_face_rate[:, 1:] - molar_face_rate[:, :-1]) / volume[None, :]
        dcdt -= c * (darea_dt / areas_cell)[None, :]
        source = np.zeros((ns, nc), dtype=float)
        if nr:
            activity = np.exp(lngamma) * mobile / tr.concentration_standard_state_mol_m3
            rates = np.empty((nr, nc), dtype=float)
            for j, reaction in enumerate(reactions):
                fwd_product = np.ones(nc, dtype=float)
                rev_product = np.ones(nc, dtype=float)
                for term in reaction.reactants:
                    fwd_product *= activity[index[term.species_id]] ** term.coefficient
                for term in reaction.products:
                    rev_product *= activity[index[term.species_id]] ** term.coefficient
                kf = math.exp(math.log(forward_knots[j, 0]) + fraction *
                              (math.log(forward_knots[j, 1]) - math.log(forward_knots[j, 0])))
                kr = math.exp(math.log(reverse_knots[j, 0]) + fraction *
                              (math.log(reverse_knots[j, 1]) - math.log(reverse_knots[j, 0])))
                rates[j] = kf * fwd_product - kr * rev_product
            if not np.isfinite(rates).all():
                raise RuntimeError("nonfinite_activity_based_kinetic_rate")
            source = stoich @ rates
            dcdt += source
        faradaic_source_mol_s = np.zeros((ns, nc), dtype=float)
        extent_rate = np.zeros((len(faradaic_maps), nc), dtype=float)
        reactive_area_m2 = dx * base.mixed_potential_template.slit_width_m \
            * base.mixed_potential_template.reactive_face_count
        if integrate_faradaic_at_stages:
            for branch_index, branch_map in enumerate(faradaic_maps):
                if stage_branch_current is not None:
                    current_density = stage_branch_current[branch_map.reaction_id]
                else:
                    current_density = interpolate(
                        np.stack((left_branches[branch_map.reaction_id], right_branches[branch_map.reaction_id])),
                        fraction,
                    )
                extent_rate[branch_index] = (
                    current_density * reactive_area_m2
                    / (branch_map.electron_number * FARADAY_CONSTANT_C_MOL)
                )
                for species_id, coefficient in branch_map.aqueous_species_stoichiometry_per_extent.items():
                    faradaic_source_mol_s[index[species_id]] += coefficient * extent_rate[branch_index]
        dcdt += faradaic_source_mol_s / volume[None, :]
        mouth_rate = molar_face_rate[:, 0]
        source_inventory_rate = np.sum(source * volume[None, :], axis=1)
        # Dynamic local charge equation: inward ionic current + wall current equals outward ionic current.
        charge_rate = (target_current[:-1] - target_current[1:]) / FARADAY_CONSTANT_C_MOL
        maximum_charge_balance_residual_rate_mol_eq_s = max(
            maximum_charge_balance_residual_rate_mol_eq_s,
            float(np.max(np.abs(
                charge_rate + np.sum(z[:, None] * source, axis=0) * volume
                + np.sum(z[:, None] * faradaic_source_mol_s, axis=0)
            )))
        )
        return np.concatenate((dcdt.reshape(-1), mouth_rate, source_inventory_rate, extent_rate.reshape(-1)))

    try:
        cell_volume_atol = tr.absolute_tolerance_mol_m3 * np.mean(cell_area, axis=0) * dx
        total_volume_atol = tr.absolute_tolerance_mol_m3 * float(np.sum(np.mean(cell_area, axis=0) * dx))
        atol = np.concatenate((
            np.full(n_state, tr.absolute_tolerance_mol_m3),
            np.full(2 * ns, total_volume_atol),
            np.tile(cell_volume_atol, len(faradaic_maps)),
        ))
        solution = solve_ivp(
            rhs, (float(times[0]), float(times[1])), state0, method="BDF",
            t_eval=(float(times[0]), float(times[1])), rtol=tr.relative_tolerance,
            atol=atol, max_step=tr.maximum_step_s,
        )
    except (RuntimeError, FloatingPointError, ValueError, OverflowError) as error:
        return None, {
            "status": "needs_data", "reason": str(error), "function_evaluations": evaluations,
            "maximum_face_current_residual_A": maximum_face_current_residual_A,
            "maximum_face_current_scale_A": maximum_current_scale_A,
            "mixed_potential_function_evaluations": stage_mixed_evaluations,
            "bdot_stage_activity_evaluations": stage_bdot_evaluations,
        }
    if not solution.success or solution.y.shape[1] != 2:
        return None, {"status": "needs_data", "reason": "stiff_current_carrying_np_integrator_failed",
                      "solver_message": solution.message, "function_evaluations": evaluations,
                      "mixed_potential_function_evaluations": stage_mixed_evaluations}
    concentration = solution.y[:n_state].reshape(ns, nc, 2)
    scale = max(1.0, float(np.max(initial)))
    if not np.isfinite(concentration).all() or float(np.min(concentration)) < -1e-7 * scale:
        return None, {"status": "needs_data", "reason": "nonphysical_negative_concentration",
                      "minimum_concentration_mol_m3": float(np.min(concentration)),
                      "function_evaluations": evaluations,
                      "mixed_potential_function_evaluations": stage_mixed_evaluations}
    if maximum_face_current_residual_A > current_abs_tol + current_rel_tol * max(maximum_current_scale_A, 1e-30):
        return None, {"status": "needs_data", "reason": "NP_face_current_did_not_match_mixed_potential",
                      "maximum_face_current_residual_A": maximum_face_current_residual_A,
                      "maximum_face_current_scale_A": maximum_current_scale_A,
                      "function_evaluations": evaluations,
                      "mixed_potential_function_evaluations": stage_mixed_evaluations}
    charge_rate_limit = (charge_abs_tol / max(duration, 1e-30)
                         + charge_rel_tol
                         * max(maximum_current_scale_A / FARADAY_CONSTANT_C_MOL, 1e-30))
    if maximum_charge_balance_residual_rate_mol_eq_s > charge_rate_limit:
        return None, {"status": "needs_data", "reason": "local_ionic_current_wall_source_charge_closure_failed",
                      "maximum_local_charge_balance_residual_rate_mol_eq_s": maximum_charge_balance_residual_rate_mol_eq_s,
                      "allowed_charge_balance_residual_rate_mol_eq_s": charge_rate_limit,
                      "function_evaluations": evaluations,
                      "mixed_potential_function_evaluations": stage_mixed_evaluations}
    endpoint = {ids[i]: [float(value) for value in concentration[i, :, 1]] for i in range(ns)}
    integrated_mouth = solution.y[n_state:n_state + ns, -1]
    integrated_kinetic_source = solution.y[n_state + ns:n_state + 2 * ns, -1]
    integrated_extents = solution.y[extent_offset:, -1].reshape(len(faradaic_maps), nc)
    integrated_faradaic_source_cells = np.zeros((ns, nc), dtype=float)
    for branch_index, branch_map in enumerate(faradaic_maps):
        for species_id, coefficient in branch_map.aqueous_species_stoichiometry_per_extent.items():
            integrated_faradaic_source_cells[index[species_id]] += coefficient * integrated_extents[branch_index]
    integrated_faradaic_source = np.sum(integrated_faradaic_source_cells, axis=1)
    integrated_source = integrated_kinetic_source + integrated_faradaic_source
    volumes = np.asarray(sub_variable.cell_cross_section_area_m2_by_knot[-1]) * dx
    inventory_start = np.sum(np.maximum(concentration[:, :, 0], 0.0)
                             * (np.asarray(sub_variable.cell_cross_section_area_m2_by_knot[0]) * dx)[None, :], axis=1)
    inventory_end = np.sum(np.maximum(concentration[:, :, 1], 0.0) * volumes[None, :], axis=1)
    inventory_residual = inventory_end - inventory_start - integrated_mouth - integrated_source
    allowed_inventory = tr.absolute_tolerance_mol_m3 * float(np.sum(volumes)) \
        + tr.relative_tolerance * max(float(np.max(inventory_end)), 1e-30)
    if np.any(np.abs(inventory_residual) > allowed_inventory):
        return None, {"status": "needs_data", "reason": "current_carrying_species_inventory_balance_failed",
                      "inventory_residual_mol_by_species": {ids[i]: float(inventory_residual[i]) for i in range(ns)},
                      "allowed_inventory_residual_mol": allowed_inventory,
                      "function_evaluations": evaluations,
                      "mixed_potential_function_evaluations": stage_mixed_evaluations}
    return {
        "endpoint_concentration_mol_m3_by_species_and_cell": endpoint,
        "integrated_mouth_transfer_mol_by_species": {ids[i]: float(integrated_mouth[i]) for i in range(ns)},
        "integrated_kinetic_source_mol_by_species": {
            ids[i]: float(integrated_kinetic_source[i]) for i in range(ns)
        },
        "integrated_faradaic_aqueous_source_mol_by_species": {
            ids[i]: float(integrated_faradaic_source[i]) for i in range(ns)
        },
        "integrated_faradaic_aqueous_source_mol_by_species_and_cell": {
            ids[i]: [float(value) for value in integrated_faradaic_source_cells[i]] for i in range(ns)
        },
        "integrated_faradaic_extent_mol_by_branch_and_cell": {
            faradaic_ids[i]: [float(value) for value in integrated_extents[i]]
            for i in range(len(faradaic_maps))
        },
        "finite_volume_inventory_residual_mol_by_species": {ids[i]: float(inventory_residual[i]) for i in range(ns)},
        "maximum_face_current_residual_A": maximum_face_current_residual_A,
        "maximum_face_current_scale_A": maximum_current_scale_A,
        "maximum_local_charge_balance_residual_rate_mol_eq_s": maximum_charge_balance_residual_rate_mol_eq_s,
        "function_evaluations": evaluations,
        "mixed_potential_function_evaluations": stage_mixed_evaluations,
        "bdot_stage_activity_evaluations": stage_bdot_evaluations,
        "input_sha256": canonical_digest(sub_variable.model_dump(mode="json")),
    }, None


def solve_crevice_current_carrying_np_faradaic(
    request: CreviceCurrentCarryingNernstPlanckRequest,
) -> Calculation:
    """Couple variable-area ionic migration, caller BV branches and exact-knot chemistry.

    Mixed-potential face current is an ionic transport constraint; wall Faradaic current
    is a separate cell source. The two are linked only by the cell charge balance.
    """
    coupling = request.faradaic_coupling
    chemistry = coupling.transport_chemistry
    variable = chemistry.transport
    transport = variable.transport_request
    digest = canonical_digest(request.model_dump(mode="json"))
    species_rows = transport.species
    ids = [row.species_id for row in species_rows]
    nc, nt = transport.cell_count, len(transport.output_time_s)
    concentration = {row.species_id: list(row.initial_cell_concentration_mol_m3) for row in species_rows}
    solids = [{row.solid_species_id: row.initial_solid_moles_per_solution_volume_mol_m3
               for row in cell.solid_equilibrium_template.solid_phases}
              for cell in chemistry.chemistry_by_knot[0].cells]
    def fail(reason, *, knot=None, interval=None, iterations=(), **extra):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "reason": reason, "failed_knot_index": knot, "failed_interval_index": interval,
            "accepted_interval_prefix": accepted, "failed_iteration_prefix": list(iterations),
            "committed": False, **extra,
        })
    accepted = []
    try:
        chem_result, state = _chemistry_at_knot(chemistry, 0, concentration, solids)
        if state is None:
            return fail("initial_exact_knot_chemistry_failed", knot=0,
                        chemistry_result=chem_result.model_dump(mode="json"))
        concentration, solids, gamma = state["concentration"], state["solids"], state["gamma"]
        mixed_left, mixed_request, _ = _mixed_potential_at_knot(coupling, concentration, gamma, 0)
    except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError) as error:
        return fail(f"initial_state_failed:{error}", knot=0)
    if mixed_left.status != "computed":
        return fail("initial_mixed_potential_failed", knot=0,
                    mixed_result=mixed_left.model_dump(mode="json"))
    total_transport_evaluations = 0
    total_mixed_evaluations = int(mixed_left.values.get("solver_function_evaluations", 0))
    total_bdot_stage_activity_evaluations = 0
    mixed_lineage = [{"knot_index": 0,
        "input_sha256": canonical_digest(mixed_request.model_dump(mode="json")),
        "result_sha256": canonical_digest(mixed_left.model_dump(mode="json"))}]
    branch_maps = {row.reaction_id: row for row in coupling.faradaic_branch_maps}
    branch_templates = {row.reaction_id: row for row in coupling.mixed_potential_template.branches}
    element_initial = _system_element_total(state, coupling, 0)
    cumulative_external = {e: 0.0 for e in element_initial}
    cumulative_mouth_and_kinetic = {e: 0.0 for e in element_initial}
    species_by_id = {row.species_id: row for row in species_rows}

    def mixed_arrays(result):
        hist = result.values["state_history"][0]
        currents = {row["reaction_id"]: np.asarray(row["signed_current_density_A_m2_by_cell"], dtype=float)
                    for row in hist["reaction_branches"]}
        return (np.asarray(hist["solution_potential_V_by_cell_relative_to_cell_0"], dtype=float),
                np.asarray(hist["electrolyte_face_current_A_by_cell_boundary"], dtype=float), currents)

    phi_left, face_left, branch_current_left = mixed_arrays(mixed_left)
    ionic_face_current_knot_history = [face_left.tolist()]
    branch_current_density_knot_history = {
        key: [value.tolist()] for key, value in branch_current_left.items()
    }
    for interval in range(nt - 1):
        dt = transport.output_time_s[interval + 1] - transport.output_time_s[interval]
        interval_prefix = []
        try:
            sub_variable, _ = _subinterval_request(chemistry, interval, concentration, gamma)
            # Endpoint guesses start from the preceding exact-knot electrical state.
            phi_guess, face_guess = phi_left.copy(), face_left.copy()
            branch_guess = {key: value.copy() for key, value in branch_current_left.items()}
            converged = None
            for iteration in range(1, request.maximum_interval_fixed_point_iterations + 1):
                transport_result, transport_error = _integrate_current_carrying_interval(
                    coupling, sub_variable, mixed_left, phi_guess, face_guess, branch_guess,
                    request.faradaic_source_integration_mode != "endpoint_trapezoid",
                    request.faradaic_source_integration_mode == "bdf_stage_spatial_mixed_potential",
                    (request.bdf_stage_bdot_activity_by_interval[interval]
                     if request.bdf_stage_bdot_activity_by_interval is not None else None),
                    interval,
                    request.maximum_total_transport_function_evaluations - total_transport_evaluations,
                    request.maximum_total_mixed_potential_function_evaluations - total_mixed_evaluations,
                    request.maximum_total_bdot_stage_activity_evaluations - total_bdot_stage_activity_evaluations,
                    request.absolute_face_current_closure_tolerance_A,
                    request.relative_face_current_closure_tolerance,
                    request.absolute_charge_inventory_tolerance_mol_eq,
                    request.relative_charge_inventory_tolerance,
                )
                if transport_error:
                    total_bdot_stage_activity_evaluations += int(
                        transport_error.get("bdot_stage_activity_evaluations", 0)
                    )
                    return fail("current_carrying_transport_failed", interval=interval,
                                iterations=interval_prefix, transport_diagnostics=transport_error)
                total_bdot_stage_activity_evaluations += int(
                    transport_result.get("bdot_stage_activity_evaluations", 0)
                )
                if total_bdot_stage_activity_evaluations > request.maximum_total_bdot_stage_activity_evaluations:
                    return fail("stage_bdot_activity_evaluation_budget_exceeded", interval=interval,
                                iterations=interval_prefix)
                stage_integrated = request.faradaic_source_integration_mode != "endpoint_trapezoid"
                if stage_integrated:
                    # Branch-current endpoint guesses are integrated as cellwise wall
                    # sources inside the BDF interval, not as a separate endpoint kick.
                    extents = {
                        key: np.asarray(values, dtype=float)
                        for key, values in transport_result[
                            "integrated_faradaic_extent_mol_by_branch_and_cell"
                        ].items()
                    }
                    faradaic_source_moles = {
                        sid: np.asarray(values, dtype=float)
                        for sid, values in transport_result[
                            "integrated_faradaic_aqueous_source_mol_by_species_and_cell"
                        ].items()
                    }
                else:
                    # Backward-compatible endpoint trapezoid path for existing requests.
                    end_area = np.asarray(variable.cell_cross_section_area_m2_by_knot[interval + 1], dtype=float)
                    volume = end_area * transport.length_m / nc
                    extents, faradaic_source_moles = {}, {sid: np.zeros(nc, dtype=float) for sid in ids}
                    reactive_area = (transport.length_m / nc * coupling.mixed_potential_template.slit_width_m
                                     * coupling.mixed_potential_template.reactive_face_count)
                    for branch_id, fmap in branch_maps.items():
                        if branch_id not in branch_guess:
                            return fail("branch_identity_mismatch", interval=interval, iterations=interval_prefix)
                        jbar = 0.5 * (branch_current_left[branch_id] + branch_guess[branch_id])
                        extent = jbar * reactive_area * dt / (fmap.electron_number * FARADAY_CONSTANT_C_MOL)
                        extents[branch_id] = extent
                        for sid, coefficient in fmap.aqueous_species_stoichiometry_per_extent.items():
                            faradaic_source_moles[sid] += coefficient * extent
                    transport_result["integrated_faradaic_extent_mol_by_branch_and_cell"] = {
                        key: [float(value) for value in values] for key, values in extents.items()
                    }
                reservoir = {e: 0.0 for e in element_initial}
                for branch_id, fmap in branch_maps.items():
                    if branch_id not in branch_guess or branch_id not in extents:
                        return fail("branch_identity_mismatch", interval=interval, iterations=interval_prefix)
                    for element, coefficient in fmap.external_reservoir_element_stoichiometry_per_extent.items():
                        reservoir[element] += coefficient * float(np.sum(extents[branch_id]))
                    # This core uses extent = signed current/(nF); sign must exactly close charge.
                    charge_per_extent = math.fsum(species_by_id[sid].charge_number * value
                        for sid, value in fmap.aqueous_species_stoichiometry_per_extent.items())
                    if not math.isclose(charge_per_extent, fmap.electron_number, rel_tol=1e-10, abs_tol=1e-10):
                        return fail("signed_Faradaic_charge_convention_not_compatible_with_extent", interval=interval,
                                    iterations=interval_prefix, branch_id=branch_id,
                                    charge_per_extent=charge_per_extent, electron_number=fmap.electron_number)
                endpoint_concentration = {
                    sid: np.asarray(values, dtype=float)
                    for sid, values in transport_result[
                        "endpoint_concentration_mol_m3_by_species_and_cell"
                    ].items()
                }
                if not stage_integrated:
                    for sid in ids:
                        endpoint_concentration[sid] = (
                            endpoint_concentration[sid] + faradaic_source_moles[sid] / volume
                        )
                if any(not math.isfinite(c) or c <= 0.0 for vals in endpoint_concentration.values() for c in vals):
                    return fail("stage-integrated Faradaic source produced nonpositive aqueous concentration", interval=interval,
                                iterations=interval_prefix)
                endpoint_chem, endpoint_state = _chemistry_at_knot(
                    chemistry, interval + 1, endpoint_concentration, solids
                )
                if endpoint_state is None:
                    return fail("endpoint_chemistry_failed", interval=interval, iterations=interval_prefix,
                                chemistry_result=endpoint_chem.model_dump(mode="json"))
                endpoint_mixed, endpoint_mixed_request, _ = _mixed_potential_at_knot(
                    coupling, endpoint_state["concentration"], endpoint_state["gamma"], interval + 1)
                if endpoint_mixed.status != "computed":
                    return fail("endpoint_mixed_potential_failed", interval=interval, iterations=interval_prefix,
                                mixed_result=endpoint_mixed.model_dump(mode="json"))
                phi_new, face_new, branches_new = mixed_arrays(endpoint_mixed)
                current_resid = max((float(np.max(np.abs(branches_new[k] - branch_guess[k])))
                                     for k in branches_new), default=0.0)
                current_scale = max(1e-30, *(float(np.max(np.abs(v))) for v in branches_new.values()))
                current_allowed = request.absolute_branch_current_fixed_point_tolerance_A_m2 \
                    + request.relative_branch_current_fixed_point_tolerance * current_scale
                phi_resid = float(np.max(np.abs(phi_new - phi_guess)))
                phi_scale = max(1e-30, float(np.max(np.abs(phi_new))))
                phi_allowed = request.absolute_potential_fixed_point_tolerance_V \
                    + request.relative_potential_fixed_point_tolerance * phi_scale
                face_resid = float(np.max(np.abs(face_new - face_guess)))
                face_scale = max(1e-30, float(np.max(np.abs(face_new))))
                face_allowed = request.absolute_face_current_closure_tolerance_A \
                    + request.relative_face_current_closure_tolerance * face_scale
                interval_prefix.append({"iteration": iteration,
                    "transport_input_sha256": transport_result["input_sha256"],
                    "transport_function_evaluations": transport_result["function_evaluations"],
                    "bdot_stage_activity_evaluations": transport_result.get("bdot_stage_activity_evaluations", 0),
                    "np_face_current_residual_A": transport_result["maximum_face_current_residual_A"],
                    "potential_residual_V": phi_resid, "branch_current_density_residual_A_m2": current_resid,
                    "face_current_residual_A": face_resid,
                    "chemistry_result_sha256": canonical_digest(endpoint_chem.model_dump(mode="json")),
                    "mixed_result_sha256": canonical_digest(endpoint_mixed.model_dump(mode="json"))})
                total_transport_evaluations += transport_result["function_evaluations"]
                total_mixed_evaluations += int(transport_result.get("mixed_potential_function_evaluations", 0))
                total_mixed_evaluations += int(endpoint_mixed.values.get("solver_function_evaluations", 0))
                if total_transport_evaluations > request.maximum_total_transport_function_evaluations:
                    return fail("transport_function_evaluation_budget_exceeded", interval=interval, iterations=interval_prefix)
                if total_mixed_evaluations > request.maximum_total_mixed_potential_function_evaluations:
                    return fail("mixed_potential_function_evaluation_budget_exceeded", interval=interval, iterations=interval_prefix)
                chem_resid = 0.0
                if converged is not None:
                    old = converged["state"]
                    vals = [abs(endpoint_state["concentration"][sid][i] - old["concentration"][sid][i])
                            for sid in ids for i in range(nc)]
                    scale = max(1e-30, *(abs(v) for sid in ids for v in endpoint_state["concentration"][sid]))
                    chem_resid = max(vals, default=0.0) / scale
                if (current_resid <= current_allowed and phi_resid <= phi_allowed
                        and face_resid <= face_allowed and chem_resid <= request.relative_chemistry_fixed_point_tolerance
                        and transport_result["maximum_face_current_residual_A"] <= face_allowed):
                    converged = {"transport": transport_result, "chemistry": endpoint_chem,
                        "state": endpoint_state, "mixed": endpoint_mixed, "mixed_request": endpoint_mixed_request,
                        "extent": extents, "reservoir": reservoir,
                        "faradaic_source_moles": faradaic_source_moles}
                    break
                # Keep latest endpoint as convergence comparator; relax electrical guesses only.
                converged = {"state": endpoint_state}
                fraction = request.relaxation_fraction
                phi_guess += fraction * (phi_new - phi_guess)
                face_guess += fraction * (face_new - face_guess)
                branch_guess = {k: branch_guess[k] + fraction * (branches_new[k] - branch_guess[k]) for k in branches_new}
            if converged is None or "transport" not in converged:
                return fail("endpoint_current_chemistry_fixed_point_did_not_converge", interval=interval,
                            iterations=interval_prefix)
        except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError, RuntimeError) as error:
            return fail(f"interval_failed:{error}", interval=interval, iterations=interval_prefix)

        state_end = converged["state"]
        total_elements = _system_element_total(state_end, coupling, interval + 1)
        mouth = converged["transport"]["integrated_mouth_transfer_mol_by_species"]
        kinetic = converged["transport"]["integrated_kinetic_source_mol_by_species"]
        faradaic_source = converged["faradaic_source_moles"]
        for element in cumulative_mouth_and_kinetic:
            cumulative_mouth_and_kinetic[element] += math.fsum(
                species_by_id[sid].elemental_composition.get(element, 0)
                * (mouth[sid] + kinetic[sid] + float(np.sum(faradaic_source[sid]))) for sid in ids)
            cumulative_external[element] += converged["reservoir"].get(element, 0.0)
        residual_elements = {e: total_elements[e] - element_initial[e] - cumulative_mouth_and_kinetic[e] - cumulative_external[e]
                             for e in element_initial}
        scale = max(1e-30, *(abs(v) for v in total_elements.values()), *(abs(v) for v in element_initial.values()))
        allowed = coupling.absolute_inventory_balance_tolerance_mol + coupling.relative_inventory_balance_tolerance * scale
        if any(abs(v) > allowed for v in residual_elements.values()):
            return fail("aqueous_solid_reservoir_element_ledger_failed", interval=interval,
                        iterations=interval_prefix, element_residual_mol_by_element=residual_elements,
                        allowed_element_residual_mol=allowed)
        result = converged["mixed"]
        _, face_current_right, branch_current_right = mixed_arrays(result)
        ionic_face_current_knot_history.append(face_current_right.tolist())
        if set(branch_current_right) != set(branch_current_density_knot_history):
            return fail("branch_identity_changed_between_exact_knots", interval=interval,
                        iterations=interval_prefix)
        for branch_id, branch_values in branch_current_right.items():
            branch_current_density_knot_history[branch_id].append(branch_values.tolist())
        mixed_lineage.append({"knot_index": interval + 1,
            "input_sha256": canonical_digest(converged["mixed_request"].model_dump(mode="json")),
            "result_sha256": canonical_digest(result.model_dump(mode="json"))})
        accepted.append({"interval_index": interval, "start_time_s": transport.output_time_s[interval],
            "end_time_s": transport.output_time_s[interval + 1], "iterations": interval_prefix,
            "ionic_face_current_A_by_boundary": result.values["state_history"][0]["electrolyte_face_current_A_by_cell_boundary"],
            "wall_faradaic_current_A_by_cell": result.values["state_history"][0]["net_electrode_current_A_by_cell"],
            "faradaic_extent_mol_by_branch_and_cell": {k: v.tolist() for k, v in converged["extent"].items()},
            "faradaic_aqueous_source_mol_by_species": {
                sid: faradaic_source[sid].tolist() for sid in ids
            },
            "endpoint_aqueous_concentration_mol_m3_by_species_and_cell": state_end["concentration"],
            "endpoint_solid_inventory_mol_m3_by_cell": state_end["solids"],
            "element_inventory_closure_residual_mol_by_element": residual_elements,
            "transport_diagnostics": converged["transport"],
            "chemistry_result_sha256": canonical_digest(converged["chemistry"].model_dump(mode="json")),
            "mixed_potential_result_sha256": canonical_digest(result.model_dump(mode="json")), "committed": True})
        concentration, solids, gamma = state_end["concentration"], state_end["solids"], state_end["gamma"]
        mixed_left = result
        phi_left, face_left, branch_current_left = mixed_arrays(result)

    return Calculation(values={"model_id": MODEL_ID, "assessment_id": request.assessment_id,
        "input_sha256": digest, "transport_input_sha256": canonical_digest(chemistry.model_dump(mode="json")),
        "mixed_potential_template_sha256": canonical_digest(coupling.mixed_potential_template.model_dump(mode="json")),
        "faradaic_source_integration_mode": request.faradaic_source_integration_mode,
        "faradaic_source_method_source_id": (
            FARADAIC_STAGE_MIXED_POTENTIAL_SOURCE_ID
            if request.faradaic_source_integration_mode == "bdf_stage_spatial_mixed_potential"
            else FARADAIC_STAGE_SOURCE_ID
            if request.faradaic_source_integration_mode == "bdf_stage_linear_current"
            else FARADAIC_ENDPOINT_SOURCE_ID
        ),
        "stage_activity_model_source_id": (
            FARADAIC_STAGE_BDOT_ACTIVITY_SOURCE_ID
            if request.bdf_stage_bdot_activity_by_interval is not None else None
        ),
        "stage_activity_parameter_request_sha256_by_interval": (
            [canonical_digest(item.model_dump(mode="json"))
             for item in request.bdf_stage_bdot_activity_by_interval]
            if request.bdf_stage_bdot_activity_by_interval is not None else []
        ),
        "ionic_face_current_and_wall_source_are_distinct_ledgers": True,
        "exact_knot_ionic_face_current_A_by_boundary": ionic_face_current_knot_history,
        "exact_knot_branch_current_density_A_m2_by_branch_and_cell": branch_current_density_knot_history,
        "exact_knot_current_time_s": list(transport.output_time_s),
        "potential_gauge": "cell_0=0 V at exact knots; endpoint interpolation or opt-in stage spatial re-solve within interval",
        "electrical_end_conditions": {"mouth": "insulated_zero_current", "blind_tip": "insulated_zero_current"},
        "committed_interval_count": len(accepted), "accepted_intervals": accepted,
        "mixed_potential_lineage": mixed_lineage,
        "transport_function_evaluations": total_transport_evaluations,
        "mixed_potential_function_evaluations": total_mixed_evaluations,
        "bdot_stage_activity_evaluations": total_bdot_stage_activity_evaluations,
        "all_requested_intervals_committed": True, "qualification_claimed": False,
        "limitations": ["Caller conductivity mapping and Nernst-Planck ionic mobility are independently declared; every interior face must satisfy current closure or the interval fails.",
            "The legacy endpoint_trapezoid mode applies the Faradaic source after interval transport. The opt-in bdf_stage_linear_current mode integrates endpoint-linearly interpolated branch currents and their species source/extents inside BDF stages.",
            "In bdf_stage_linear_current mode the mixed-potential solve remains endpoint-coupled and is not rerun at every BDF stage.",
            "The opt-in bdf_stage_spatial_mixed_potential mode re-solves the quasi-steady spatial ohmic/Butler-Volmer balance using BDF-stage concentrations and caller Nernst/conductivity/geometry records, then integrates its branch sources/extents. It omits double-layer charging and does not create an independent calibrated kinetic law.",
            "No double-layer storage, fully implicit coupling of the mixed-potential algebraic solve to the BDF Newton Jacobian, or automatic phase discovery is included.",
            "Aqueous chemistry/solid phases are caller-declared exact-knot equilibria; no automatic reaction or phase discovery.",
            "Optional B-dot stage activity refresh uses caller-evidence-bound coefficients at each BDF trial composition for NP fluxes, homogeneous activity-based rates and stage Nernst/BV; it is a coefficient evaluation only, not mass-action speciation or phase equilibrium. It requires constant interval temperature and has its own RHS-evaluation budget.",
            "When B-dot stage refresh is enabled, exact-knot equilibrium and endpoint mixed-potential coupling remain on the existing Davies-based chemistry path; the B-dot/Davies split is explicit and requires caller review.",
            "Computational screening only; no qualification claim."]})


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCurrentCarryingNernstPlanckRequest,
        evaluator=solve_crevice_current_carrying_np_faradaic,
        units={
            "accepted_intervals[].start_time_s": "s",
            "accepted_intervals[].end_time_s": "s",
            "accepted_intervals[].ionic_face_current_A_by_boundary[]": "A",
            "accepted_intervals[].wall_faradaic_current_A_by_cell[]": "A",
            "exact_knot_current_time_s[]": "s",
            "exact_knot_ionic_face_current_A_by_boundary[][]": "A",
            "exact_knot_branch_current_density_A_m2_by_branch_and_cell.*[][]": "A/m^2",
            "accepted_intervals[].faradaic_extent_mol_by_branch_and_cell.*[]": "mol",
            "accepted_intervals[].faradaic_aqueous_source_mol_by_species.*[]": "mol",
            "accepted_intervals[].endpoint_aqueous_concentration_mol_m3_by_species_and_cell.*[]": "mol/m^3",
            "accepted_intervals[].endpoint_solid_inventory_mol_m3_by_cell.*": "mol/m^3_solution",
        },
        assumptions=(
            "Cell 0 is the potential gauge at each exact knot; mouth and blind tip have zero ionic current.",
            "The caller mixed-potential face current is coupled to Nernst-Planck migration and must match the constitutive ionic flux.",
            "The legacy mode uses endpoint trapezoid splitting; opt-in bdf_stage_linear_current uses endpoint-linear branch-current interpolation and integrates cellwise sources/extents inside BDF stages. Signed charge stoichiometry must satisfy sum(z nu)=+n.",
            "Potential and equilibrium chemistry are solved at exact knots in legacy and linear-current modes. The opt-in spatial mixed-potential stage mode re-solves the quasi-steady ohmic/Butler-Volmer balance within each BDF RHS evaluation using fixed caller reaction topology and trial concentrations; that algebraic solve is not part of the BDF Newton Jacobian, and double-layer storage and phase discovery are not modeled.",
            "Optional B-dot stage activity refresh is caller-evidence-bound and coefficient-only; it is evaluated once per BDF RHS from mouth-plus-cell trial concentrations and feeds NP activity gradients, homogeneous activity-based kinetic rates, and stage Nernst/BV. It does not solve speciation or phase equilibrium; exact-knot/end-point chemistry remains on its existing activity model path.",
            "The caller provides all chemistry, kinetics, conductivity, geometry, reservoir and applicability inputs; no automatic discovery or qualification is included.",
        ),
        source_ids=(METHOD_SOURCE_ID, CURRENT_CLOSURE_SOURCE_ID, "scipy_integrate_bdf",
                    FARADAIC_ENDPOINT_SOURCE_ID, FARADAIC_STAGE_SOURCE_ID,
                    FARADAIC_STAGE_MIXED_POTENTIAL_SOURCE_ID,
                    FARADAIC_STAGE_BDOT_ACTIVITY_SOURCE_ID,
                    "finite_volume_current_carrying_activity_nernst_planck_with_faradaic_wall_balance",
                    "mixed_potential_face_current_to_ionic_nernst_planck_flux_closure"),
        qualification="user_model",
    ),)
