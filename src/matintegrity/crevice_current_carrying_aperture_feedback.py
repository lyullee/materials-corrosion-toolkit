"""Bounded geometry feedback around current-carrying crevice transport/Faradaic chemistry."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .crevice_current_carrying_np_faradaic import (
    CreviceCurrentCarryingNernstPlanckRequest,
    solve_crevice_current_carrying_np_faradaic,
)
from .crevice_spatial_chemistry_aperture_fixed_point import (
    APERTURE_SOURCE_ID,
    HYDRAULIC_SOURCE_ID,
    METHOD_SOURCE_ID as GEOMETRY_METHOD_SOURCE_ID,
    _bind_area_history,
    _replace_hydraulics,
)

MODEL_ID = "integration.crevice_current_carrying_aperture_feedback"
METHOD_SOURCE_ID = "bounded_picard_feedback_of_current_carrying_crevice_transport_geometry"
MAX_FEEDBACK_RECORDS = 2_000_000


class CreviceCurrentCarryingApertureFeedbackRequest(Contract):
    schema_version: Literal["matintegrity.crevice_current_carrying_aperture_feedback.v1"] = (
        "matintegrity.crevice_current_carrying_aperture_feedback.v1"
    )
    assessment_id: str = Field(min_length=1)
    current_carrying_request: CreviceCurrentCarryingNernstPlanckRequest
    transverse_width_m: Positive
    face_area_weight_by_face_and_cell: tuple[tuple[Nonnegative, ...], ...] = Field(min_length=3, max_length=301)
    deposit_volume_to_gap_change_factor_by_cell: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    solid_molar_volume_m3_mol_by_phase: dict[str, Positive] = Field(min_length=1, max_length=32)
    solid_molar_volume_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solid_molar_volume_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    aperture_mapping_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    aperture_mapping_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    hydraulic_velocity_sensitivity_m_s_per_m_by_knot_face_and_cell: tuple[
        tuple[tuple[float, ...], ...], ...
    ] = Field(min_length=2, max_length=500)
    hydraulic_sensitivity_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hydraulic_sensitivity_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    maximum_geometry_fixed_point_iterations: int = Field(default=30, ge=2, le=1000)
    maximum_total_transport_function_evaluations: int = Field(default=5_000_000, ge=100, le=20_000_000)
    maximum_total_mixed_potential_function_evaluations: int = Field(default=2_000_000, ge=100, le=20_000_000)
    aperture_absolute_tolerance_m: Positive = 1e-10
    aperture_relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    velocity_absolute_tolerance_m_s: Positive = 1e-12
    velocity_relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    relaxation_fraction: Positive = Field(default=0.5, le=1.0)
    solid_volume_to_gap_mapping_reviewed: bool
    hydraulic_sensitivity_mapping_reviewed: bool
    face_area_mapping_and_potential_mesh_reviewed: bool
    current_carrying_transport_geometry_feedback_scope_reviewed: bool
    caller_kinetics_and_flow_laws_only_reviewed: bool
    computation_budgets_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_feedback(self):
        coupling = self.current_carrying_request.faradaic_coupling
        variable = coupling.transport_chemistry.transport
        transport = variable.transport_request
        nc, nt = transport.cell_count, len(transport.output_time_s)
        if len(self.deposit_volume_to_gap_change_factor_by_cell) != nc:
            raise ValueError("deposit-volume aperture factors must align with transport cells")
        if len(self.face_area_weight_by_face_and_cell) != nc + 1 or any(
            len(row) != nc for row in self.face_area_weight_by_face_and_cell
        ):
            raise ValueError("face-area weights must map every face to every cell")
        if any(not math.isclose(math.fsum(row), 1.0, rel_tol=0.0, abs_tol=1e-12)
               for row in self.face_area_weight_by_face_and_cell):
            raise ValueError("each face-area interpolation row must sum to one")
        if any(self.face_area_weight_by_face_and_cell[0][cell] != (1.0 if cell == 0 else 0.0)
               for cell in range(nc)) or any(
            self.face_area_weight_by_face_and_cell[-1][cell] != (1.0 if cell == nc - 1 else 0.0)
            for cell in range(nc)
        ):
            raise ValueError("mouth and blind-tip face areas must map to their adjacent cells")
        phase_ids = {row.solid_species_id for row in
                     coupling.transport_chemistry.chemistry_by_knot[0].cells[0].solid_equilibrium_template.solid_phases}
        if set(self.solid_molar_volume_m3_mol_by_phase) != phase_ids:
            raise ValueError("molar-volume map must cover exactly the caller-declared solid phases")
        if canonical_digest(self.solid_molar_volume_m3_mol_by_phase) != self.solid_molar_volume_record_sha256:
            raise ValueError("molar-volume digest must bind its complete phase map")
        if not any(row.sha256 == self.solid_molar_volume_record_sha256 for row in self.solid_molar_volume_evidence):
            raise ValueError("molar-volume Evidence must pin the record digest")
        aperture_payload = {
            "transverse_width_m": self.transverse_width_m,
            "face_area_weight_by_face_and_cell": [list(row) for row in self.face_area_weight_by_face_and_cell],
            "deposit_volume_to_gap_change_factor_by_cell": list(self.deposit_volume_to_gap_change_factor_by_cell),
            "solid_molar_volume_record_sha256": self.solid_molar_volume_record_sha256,
        }
        aperture_digest = canonical_digest(aperture_payload)
        if aperture_digest != self.aperture_mapping_record_sha256 or not any(
            row.source_id == APERTURE_SOURCE_ID and row.sha256 == aperture_digest and row.license_id
            for row in self.aperture_mapping_evidence
        ):
            raise ValueError("licensed caller aperture Evidence must bind the complete mapping")
        tensor = self.hydraulic_velocity_sensitivity_m_s_per_m_by_knot_face_and_cell
        if len(tensor) != nt or any(len(knot) != nc + 1 for knot in tensor) or any(
            len(face) != nc for knot in tensor for face in knot
        ):
            raise ValueError("hydraulic sensitivity tensor must align with exact knots × faces × cells")
        if nt * (nc + 1) * nc > MAX_FEEDBACK_RECORDS:
            raise ValueError("hydraulic sensitivity tensor exceeds the finite record budget")
        hydraulic_digest = canonical_digest([[[float(v) for v in face] for face in knot] for knot in tensor])
        if hydraulic_digest != self.hydraulic_sensitivity_record_sha256 or any(
            value != 0.0 for knot in tensor for value in knot[-1]
        ):
            raise ValueError("hydraulic sensitivity digest must match and preserve blind-tip zero velocity")
        if not any(row.source_id == HYDRAULIC_SOURCE_ID and row.sha256 == hydraulic_digest and row.license_id
                   for row in self.hydraulic_sensitivity_evidence):
            raise ValueError("licensed caller hydraulic Evidence must pin the sensitivity tensor")
        if not all((self.solid_volume_to_gap_mapping_reviewed, self.hydraulic_sensitivity_mapping_reviewed,
                    self.face_area_mapping_and_potential_mesh_reviewed,
                    self.current_carrying_transport_geometry_feedback_scope_reviewed,
                    self.caller_kinetics_and_flow_laws_only_reviewed, self.computation_budgets_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all geometry, current, caller-law, budget and use reviews are required")
        return self


def _trial_request(request, aperture_history, initial_aperture, sensitivity, iteration, budget_transport, budget_mixed):
    current = request.current_carrying_request
    variable = current.faradaic_coupling.transport_chemistry.transport
    variable = _replace_hydraulics(variable, aperture_history, initial_aperture, sensitivity)
    variable, area_digest = _bind_area_history(variable, aperture_history, request)
    chemistry = current.faradaic_coupling.transport_chemistry.model_copy(update={"transport": variable})
    coupling = current.faradaic_coupling.model_copy(update={"transport_chemistry": chemistry})
    child = current.model_copy(update={
        "assessment_id": f"{request.assessment_id}:geometry_iteration:{iteration}",
        "faradaic_coupling": coupling,
        "maximum_total_transport_function_evaluations": budget_transport,
        "maximum_total_mixed_potential_function_evaluations": budget_mixed,
    })
    return child, area_digest, canonical_digest(child.model_dump(mode="json"))


def _target_aperture_history(request, result, initial_aperture, current_aperture):
    chemistry = request.current_carrying_request.faradaic_coupling.transport_chemistry
    transport = chemistry.transport.transport_request
    nc, nt = transport.cell_count, len(transport.output_time_s)
    dx, width = transport.length_m / nc, request.transverse_width_m
    phase_ids = tuple(request.solid_molar_volume_m3_mol_by_phase)
    initial_solids = [{phase.solid_species_id: phase.initial_solid_moles_per_solution_volume_mol_m3
                       for phase in cell.solid_equilibrium_template.solid_phases}
                      for cell in chemistry.chemistry_by_knot[0].cells]
    solids_by_knot = [initial_solids]
    for interval in result.values["accepted_intervals"]:
        solids_by_knot.append(interval["endpoint_solid_inventory_mol_m3_by_cell"])
    target = []
    for knot in range(nt):
        cells = []
        for cell in range(nc):
            reference_volume = initial_aperture[cell] * width * dx
            current_volume = current_aperture[knot][cell] * width * dx
            solid_volume_delta = math.fsum(
                (solids_by_knot[knot][cell][phase] * current_volume
                 - initial_solids[cell][phase] * reference_volume)
                * request.solid_molar_volume_m3_mol_by_phase[phase]
                for phase in phase_ids
            )
            area_plan = width * dx
            new_aperture = initial_aperture[cell] - (
                request.deposit_volume_to_gap_change_factor_by_cell[cell] * solid_volume_delta / area_plan
            )
            if not math.isfinite(new_aperture) or new_aperture <= 0.0:
                raise ArithmeticError(f"nonpositive aperture target at knot {knot}, cell {cell}")
            cells.append(new_aperture)
        target.append(cells)
    target[0] = list(initial_aperture)
    return target


def _velocity_history(request, apertures, initial_aperture):
    current = request.current_carrying_request
    variable = current.faradaic_coupling.transport_chemistry.transport
    transport = variable.transport_request
    base = np.asarray(transport.cell_face_axial_velocity_m_s_by_knot, dtype=float).T
    jac = np.asarray(request.hydraulic_velocity_sensitivity_m_s_per_m_by_knot_face_and_cell, dtype=float)
    delta = np.asarray(apertures) - np.asarray(initial_aperture)[None, :]
    return base + np.einsum("kfc,kc->kf", jac, delta)


def solve_crevice_current_carrying_aperture_feedback(
    request: CreviceCurrentCarryingApertureFeedbackRequest,
) -> Calculation:
    """Repeat the full transient current-carrying solver against solid-volume geometry feedback."""
    digest = canonical_digest(request.model_dump(mode="json"))
    coupling = request.current_carrying_request.faradaic_coupling
    variable = coupling.transport_chemistry.transport
    nc = variable.transport_request.cell_count
    initial_aperture = [float(area) / request.transverse_width_m
                        for area in variable.cell_cross_section_area_m2_by_knot[0]]
    aperture = [[float(area) / request.transverse_width_m for area in row]
                for row in variable.cell_cross_section_area_m2_by_knot]
    sensitivity = request.hydraulic_velocity_sensitivity_m_s_per_m_by_knot_face_and_cell
    prefix = []
    total_transport = total_mixed = 0
    last_trial = None

    def fail(reason, iteration=None, **extra):
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "reason": reason, "failed_iteration": iteration,
            "iteration_prefix": prefix, "accepted_interval_prefix": [], "committed": False,
            "transport_function_evaluations": total_transport,
            "mixed_potential_function_evaluations": total_mixed, **extra,
        })

    for iteration in range(1, request.maximum_geometry_fixed_point_iterations + 1):
        remaining_transport = request.maximum_total_transport_function_evaluations - total_transport
        remaining_mixed = request.maximum_total_mixed_potential_function_evaluations - total_mixed
        if remaining_transport < 100 or remaining_mixed < 100:
            return fail("aggregate_solver_budget_exhausted", iteration)
        try:
            trial, area_digest, trial_digest = _trial_request(
                request, aperture, initial_aperture, sensitivity, iteration,
                min(remaining_transport, request.current_carrying_request.maximum_total_transport_function_evaluations),
                min(remaining_mixed, request.current_carrying_request.maximum_total_mixed_potential_function_evaluations),
            )
            result = solve_crevice_current_carrying_np_faradaic(trial)
        except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError) as error:
            return fail(f"trial_build_or_evaluation_failed:{error}", iteration)
        if result.status != "computed":
            return fail("current_carrying_trial_failed", iteration,
                        failed_trial_result=result.model_dump(mode="json"))
        result_transport = int(result.values["transport_function_evaluations"])
        result_mixed = int(result.values["mixed_potential_function_evaluations"])
        total_transport += result_transport
        total_mixed += result_mixed
        try:
            target = _target_aperture_history(request, result, initial_aperture, aperture)
            velocity_target = _velocity_history(request, target, initial_aperture)
        except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError) as error:
            return fail(f"geometry_target_failed:{error}", iteration)
        aperture_residual = float(np.max(np.abs(np.asarray(target) - np.asarray(aperture))))
        aperture_scale = max(1e-30, float(np.max(np.abs(target))))
        aperture_allowed = request.aperture_absolute_tolerance_m + request.aperture_relative_tolerance * aperture_scale
        velocity_current = _velocity_history(request, aperture, initial_aperture)
        velocity_residual = float(np.max(np.abs(velocity_target - velocity_current)))
        velocity_scale = max(1e-30, float(np.max(np.abs(velocity_target))))
        velocity_allowed = request.velocity_absolute_tolerance_m_s + request.velocity_relative_tolerance * velocity_scale
        record = {
            "iteration": iteration,
            "trial_request_sha256": trial_digest,
            "trial_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "trial_geometry_area_history_sha256": area_digest,
            "aperture_residual_m": aperture_residual,
            "aperture_allowed_residual_m": aperture_allowed,
            "hydraulic_velocity_residual_m_s": velocity_residual,
            "hydraulic_velocity_allowed_residual_m_s": velocity_allowed,
            "trial_transport_evaluations": result_transport,
            "trial_mixed_potential_evaluations": result_mixed,
            "trial_committed_interval_count": result.values["committed_interval_count"],
            "committed": False,
        }
        prefix.append(record)
        last_trial = result
        if aperture_residual <= aperture_allowed and velocity_residual <= velocity_allowed:
            record["committed"] = True
            return Calculation(values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "method_source_id": METHOD_SOURCE_ID,
                "geometry_mapping_source_id": APERTURE_SOURCE_ID,
                "hydraulic_mapping_source_id": HYDRAULIC_SOURCE_ID,
                "inherited_current_carrying_result_sha256": canonical_digest(result.model_dump(mode="json")),
                "geometry_fixed_point_iteration_count": iteration,
                "aperture_history_m_by_knot_and_cell": aperture,
                "target_aperture_history_m_by_knot_and_cell": target,
                "cell_cross_section_area_m2_by_knot": [
                    [a * request.transverse_width_m for a in knot] for knot in aperture
                ],
                "face_velocity_m_s_by_knot_and_face": velocity_current.tolist(),
                "aperture_fixed_point_residual_m": aperture_residual,
                "hydraulic_fixed_point_residual_m_s": velocity_residual,
                "iteration_lineage": prefix,
                "current_carrying_result": result.model_dump(mode="json"),
                "transport_function_evaluations": total_transport,
                "mixed_potential_function_evaluations": total_mixed,
                "all_intervals_committed": result.values["all_requested_intervals_committed"],
                "qualification_claimed": False,
                "limitations": [
                    "Aperture and velocity responses are caller-supplied linearized sensitivities around the initial history; no universal deposition morphology or flow law is inferred.",
                    "Each geometry trial reruns the full transient current-carrying NP/Faradaic/exact-knot chemistry calculation. Geometry varies linearly between the exact caller knots during each trial interval.",
                    "No double-layer current, within-step phase equilibrium, dynamic hydraulic pressure solution or material qualification is included.",
                ],
            })
        factor = request.relaxation_fraction
        aperture = (np.asarray(aperture) + factor * (np.asarray(target) - np.asarray(aperture))).tolist()
        aperture[0] = list(initial_aperture)
        if np.any(~np.isfinite(aperture)) or np.any(np.asarray(aperture) <= 0.0):
            return fail("relaxed_aperture_history_is_nonphysical", iteration)

    return fail("aperture_and_hydraulic_fixed_point_not_converged_within_budget",
                request.maximum_geometry_fixed_point_iterations,
                last_trial_result=last_trial.model_dump(mode="json") if last_trial else None)


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCurrentCarryingApertureFeedbackRequest,
        evaluator=solve_crevice_current_carrying_aperture_feedback,
        units={
            "aperture_history_m_by_knot_and_cell[][]": "m",
            "cell_cross_section_area_m2_by_knot[][]": "m^2",
            "face_velocity_m_s_by_knot_and_face[][]": "m/s",
            "aperture_fixed_point_residual_m": "m",
            "hydraulic_fixed_point_residual_m_s": "m/s",
        },
        assumptions=(
            "Caller-specified solid molar volumes map endpoint aqueous/solid states to trial aperture histories.",
            "Caller-specified face-velocity sensitivity maps aperture departures from the initial history to hydraulic histories.",
            "Each fixed-point iteration reruns the complete current-carrying Nernst-Planck, mixed-potential, Faradaic and exact-knot chemistry path.",
            "Only a bounded converged geometry/hydraulic trial is returned; nonconvergence preserves iteration digest lineage and fails closed.",
            "Sensitivity updates are explicit caller linear maps, not general deposition morphology or hydraulic constitutive laws.",
        ),
        source_ids=(METHOD_SOURCE_ID, GEOMETRY_METHOD_SOURCE_ID, APERTURE_SOURCE_ID, HYDRAULIC_SOURCE_ID),
        qualification="user_model",
    ),)
