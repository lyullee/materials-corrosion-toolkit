"""Bounded fixed point between caller geometry/hydraulics and spatial crevice chemistry transport."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .crevice_spatial_chemistry_transport import (
    CreviceSpatialChemistryTransportRequest,
    solve_crevice_spatial_chemistry_transport,
)

MODEL_ID = "integration.crevice_spatial_chemistry_aperture_fixed_point"
APERTURE_SOURCE_ID = "caller_solid_volume_to_aperture_response"
HYDRAULIC_SOURCE_ID = "caller_aperture_to_hydraulic_velocity_response"
METHOD_SOURCE_ID = "bounded_geometry_hydraulic_chemistry_picard_iteration"
MAX_FEEDBACK_RECORDS = 2_000_000


class CreviceSpatialChemistryApertureFixedPointRequest(Contract):
    schema_version: Literal["matintegrity.crevice_spatial_chemistry_aperture_fixed_point.v1"] = (
        "matintegrity.crevice_spatial_chemistry_aperture_fixed_point.v1"
    )
    assessment_id: str = Field(min_length=1)
    chemistry_transport_request: CreviceSpatialChemistryTransportRequest
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
    maximum_fixed_point_iterations: int = Field(default=30, ge=2, le=1000)
    maximum_total_transport_function_evaluations: int = Field(default=5_000_000, ge=100, le=20_000_000)
    aperture_absolute_tolerance_m: Positive = 1e-10
    aperture_relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    velocity_absolute_tolerance_m_s: Positive = 1e-12
    velocity_relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    relaxation_fraction: Positive = Field(default=0.5, le=1.0)
    solid_volume_to_gap_mapping_reviewed: bool
    hydraulic_sensitivity_mapping_reviewed: bool
    fixed_aperture_anchor_and_face_area_interpolation_reviewed: bool
    geometry_hydraulic_chemistry_fixed_point_scope_reviewed: bool
    no_unprovided_kinetics_or_hydraulic_law_inferred_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_feedback_mapping(self):
        coupled = self.chemistry_transport_request
        variable = coupled.transport
        transport = variable.transport_request
        nc, nt = transport.cell_count, len(transport.output_time_s)
        if len(self.deposit_volume_to_gap_change_factor_by_cell) != nc:
            raise ValueError("deposit-volume response factors must align with transport cells")
        if len(self.face_area_weight_by_face_and_cell) != nc + 1 or any(len(row) != nc for row in self.face_area_weight_by_face_and_cell):
            raise ValueError("face-area weights must map every face to every cell")
        if any(not math.isclose(math.fsum(row), 1.0, rel_tol=0.0, abs_tol=1e-12)
               for row in self.face_area_weight_by_face_and_cell):
            raise ValueError("each caller face-area interpolation row must sum to one")
        if any(self.face_area_weight_by_face_and_cell[0][j] != (1.0 if j == 0 else 0.0) for j in range(nc)):
            raise ValueError("mouth face area must map to the first cell aperture")
        if any(self.face_area_weight_by_face_and_cell[-1][j] != (1.0 if j == nc - 1 else 0.0) for j in range(nc)):
            raise ValueError("blind-tip face area must map to the last cell aperture")
        if set(self.solid_molar_volume_m3_mol_by_phase) != {
            phase.solid_species_id for phase in coupled.chemistry_by_knot[0].cells[0].solid_equilibrium_template.solid_phases
        }:
            raise ValueError("molar-volume mapping must cover the exact caller solid-phase set")
        if canonical_digest(self.solid_molar_volume_m3_mol_by_phase) != self.solid_molar_volume_record_sha256:
            raise ValueError("solid molar-volume digest must bind the complete mapping")
        if not any(row.sha256 == self.solid_molar_volume_record_sha256 for row in self.solid_molar_volume_evidence):
            raise ValueError("solid molar-volume Evidence must pin its record digest")
        aperture_mapping_payload = {
            "transverse_width_m": self.transverse_width_m,
            "face_area_weight_by_face_and_cell": [list(row) for row in self.face_area_weight_by_face_and_cell],
            "deposit_volume_to_gap_change_factor_by_cell": list(self.deposit_volume_to_gap_change_factor_by_cell),
            "solid_molar_volume_record_sha256": self.solid_molar_volume_record_sha256,
        }
        aperture_mapping_digest = canonical_digest(aperture_mapping_payload)
        if aperture_mapping_digest != self.aperture_mapping_record_sha256:
            raise ValueError("aperture mapping digest must bind width, face mapping, gap factors and solid-volume record")
        if not any(row.source_id == APERTURE_SOURCE_ID and row.sha256 == aperture_mapping_digest and row.license_id
                   for row in self.aperture_mapping_evidence):
            raise ValueError("licensed caller Evidence must pin the aperture response mapping")
        hydraulic = self.hydraulic_velocity_sensitivity_m_s_per_m_by_knot_face_and_cell
        if len(hydraulic) != nt or any(len(knot) != nc + 1 for knot in hydraulic) \
                or any(len(face) != nc for knot in hydraulic for face in knot):
            raise ValueError("hydraulic sensitivity tensor must align with knots × faces × cells")
        if nt * (nc + 1) * nc > MAX_FEEDBACK_RECORDS:
            raise ValueError("hydraulic sensitivity tensor exceeds the declared record budget")
        hydraulic_digest = canonical_digest([[[float(v) for v in face] for face in knot] for knot in hydraulic])
        if hydraulic_digest != self.hydraulic_sensitivity_record_sha256:
            raise ValueError("hydraulic sensitivity digest must bind exact ordered coefficients")
        if any(value != 0.0 for knot in hydraulic for value in knot[-1]):
            raise ValueError("caller hydraulic response must preserve exactly zero blind-tip velocity")
        if not any(row.source_id == HYDRAULIC_SOURCE_ID and row.sha256 == hydraulic_digest and row.license_id
                   for row in self.hydraulic_sensitivity_evidence):
            raise ValueError("licensed caller hydraulic Evidence must pin its coefficient digest")
        if not all((self.solid_volume_to_gap_mapping_reviewed,
                    self.hydraulic_sensitivity_mapping_reviewed,
                    self.fixed_aperture_anchor_and_face_area_interpolation_reviewed,
                    self.geometry_hydraulic_chemistry_fixed_point_scope_reviewed,
                    self.no_unprovided_kinetics_or_hydraulic_law_inferred_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all caller geometry/hydraulic law and use reviews are required")
        return self


def _bind_area_history(template, apertures, request):
    width = request.transverse_width_m
    cell_areas = tuple(tuple(float(a) * width for a in knot) for knot in apertures)
    face_areas = tuple(tuple(
        width * math.fsum(request.face_area_weight_by_face_and_cell[face][cell] * apertures[knot][cell]
                          for cell in range(len(apertures[knot])))
        for face in range(len(apertures[knot]) + 1)
    ) for knot in range(len(apertures)))
    transport = template.transport_request
    area_payload = {
        "geometry_id": template.geometry_id,
        "provider_id": template.area_provider_id,
        "provider_revision": template.area_provider_revision,
        "configuration_sha256": template.area_configuration_sha256,
        "time_s": list(transport.output_time_s),
        "cell_cross_section_area_m2_by_knot": [list(row) for row in cell_areas],
        "face_cross_section_area_m2_by_knot": [list(row) for row in face_areas],
    }
    area_sha = canonical_digest(area_payload)
    evidence = []
    pinned = False
    for row in template.area_history_evidence:
        if row.source_id == "caller_crevice_variable_area_history" and row.sha256 == template.area_history_sha256:
            evidence.append(row.model_copy(update={
                "sha256": area_sha,
                "origin": "user_declared",
                "citation": row.citation + "; trial geometry derived by the caller-reviewed feedback mapping",
            }))
            pinned = True
        else:
            evidence.append(row)
    if not pinned:
        raise ValueError("trial area history cannot be rebound without its licensed source Evidence")
    return template.model_copy(update={
        "cell_cross_section_area_m2_by_knot": cell_areas,
        "face_cross_section_area_m2_by_knot": face_areas,
        "area_history_sha256": area_sha,
        "area_history_evidence": tuple(evidence),
        "transport_request": transport.model_copy(update={
            "cross_section_area_m2": math.fsum(cell_areas[0]) / len(cell_areas[0]),
        }),
    }), area_sha


def _replace_hydraulics(template, aperture_trial, aperture_initial, sensitivity):
    transport = template.transport_request
    baseline = np.asarray(transport.cell_face_axial_velocity_m_s_by_knot, dtype=float).T
    delta = np.asarray(aperture_trial, dtype=float) - np.asarray(aperture_initial, dtype=float)
    jacobian = np.asarray(sensitivity, dtype=float)
    velocity = baseline + np.einsum("kfc,kc->kf", jacobian, delta)
    if np.any(~np.isfinite(velocity)):
        raise ArithmeticError("caller hydraulic response produced nonfinite face velocity")
    if np.any(np.abs(velocity[-1]) > 0.0):
        raise ValueError("caller hydraulic response violates the sealed blind-tip zero-velocity condition")
    return template.model_copy(update={
        "transport_request": transport.model_copy(update={
            "cell_face_axial_velocity_m_s_by_knot": tuple(tuple(float(v) for v in face) for face in velocity.T),
        }),
    })


def _aperture_target(request, result, aperture_initial, aperture_trial):
    coupled = request.chemistry_transport_request
    transport = coupled.transport.transport_request
    dx = transport.length_m / transport.cell_count
    history = result.values["state_history"]
    nc, nt = transport.cell_count, len(transport.output_time_s)
    initial_solid = history[0]["solid_inventory_mol_m3_by_cell"]
    target = []
    for knot in range(nt):
        trial_knot = []
        trial_solid = history[knot]["solid_inventory_mol_m3_by_cell"]
        for cell in range(nc):
            plan_area = request.transverse_width_m * dx
            reference_volume = aperture_initial[cell] * request.transverse_width_m * dx
            current_volume = aperture_trial[knot][cell] * request.transverse_width_m * dx
            deposit_volume_change = math.fsum(
                (trial_solid[cell][phase_id] * current_volume
                 - initial_solid[cell][phase_id] * reference_volume)
                * request.solid_molar_volume_m3_mol_by_phase[phase_id]
                for phase_id in request.solid_molar_volume_m3_mol_by_phase
            )
            factor = request.deposit_volume_to_gap_change_factor_by_cell[cell]
            target_aperture = aperture_initial[cell] - factor * deposit_volume_change / plan_area
            if not math.isfinite(target_aperture) or target_aperture <= 0.0:
                raise ArithmeticError(f"nonpositive aperture target at knot {knot}, cell {cell}")
            trial_knot.append(target_aperture)
        target.append(trial_knot)
    # The first-knot geometry is the declared seed and is not overwritten by an initial-state inventory offset.
    target[0] = list(aperture_initial)
    return target


def solve_crevice_spatial_chemistry_aperture_fixed_point(
    request: CreviceSpatialChemistryApertureFixedPointRequest,
) -> Calculation:
    """Iterate geometry/hydraulic histories around the existing spatial chemistry transport calculation."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base_coupled = request.chemistry_transport_request
    variable = base_coupled.transport
    transport = variable.transport_request
    nc, nt = transport.cell_count, len(transport.output_time_s)
    aperture_initial = [area / request.transverse_width_m
                        for area in variable.cell_cross_section_area_m2_by_knot[0]]
    aperture = [[area / request.transverse_width_m for area in row]
                for row in variable.cell_cross_section_area_m2_by_knot]
    sensitivity = request.hydraulic_velocity_sensitivity_m_s_per_m_by_knot_face_and_cell
    prefix = []
    total_evaluations = 0
    converged = False
    last_result = None
    for iteration in range(1, request.maximum_fixed_point_iterations + 1):
        try:
            trial_variable = _replace_hydraulics(variable, aperture, aperture_initial, sensitivity)
            trial_variable, trial_geometry_sha = _bind_area_history(trial_variable, aperture, request)
            trial_coupled = base_coupled.model_copy(update={"transport": trial_variable})
            trial_digest = canonical_digest(trial_coupled.model_dump(mode="json"))
            result = solve_crevice_spatial_chemistry_transport(trial_coupled)
        except (ArithmeticError, ValueError, KeyError, TypeError) as error:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "failed_iteration": iteration,
                "reason": str(error), "accepted_trial_prefix": prefix,
                "accepted_trial_prefix_sha256": canonical_digest(prefix),
                "committed": False,
            })
        if result.status != "computed":
            return Calculation(status=result.status, values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "failed_iteration": iteration,
                "failed_trial_geometry_sha256": trial_geometry_sha,
                "failed_trial_transport_chemistry_input_sha256": trial_digest,
                "failed_trial_result": result.model_dump(mode="json"),
                "accepted_trial_prefix": prefix,
                "accepted_trial_prefix_sha256": canonical_digest(prefix),
                "committed": False,
            })
        total_evaluations += int(result.values["total_transport_function_evaluations"])
        target_aperture = _aperture_target(request, result, aperture_initial, aperture)
        target_velocity = np.asarray(transport.cell_face_axial_velocity_m_s_by_knot, dtype=float).T \
            + np.einsum("kfc,kc->kf", np.asarray(sensitivity, dtype=float),
                        np.asarray(target_aperture, dtype=float) - np.asarray(aperture_initial, dtype=float))
        current_velocity = np.asarray(trial_variable.transport_request.cell_face_axial_velocity_m_s_by_knot, dtype=float).T
        aperture_residual = max(abs(target_aperture[k][i] - aperture[k][i])
                                for k in range(nt) for i in range(nc))
        aperture_scale = max(1e-30, *(abs(v) for row in target_aperture for v in row))
        velocity_residual = float(np.max(np.abs(target_velocity - current_velocity)))
        velocity_scale = max(1e-30, float(np.max(np.abs(target_velocity))))
        aperture_allowed = request.aperture_absolute_tolerance_m + request.aperture_relative_tolerance * aperture_scale
        velocity_allowed = request.velocity_absolute_tolerance_m_s + request.velocity_relative_tolerance * velocity_scale
        record = {
            "iteration": iteration,
            "trial_geometry_sha256": trial_geometry_sha,
            "trial_transport_chemistry_input_sha256": trial_digest,
            "trial_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "target_aperture_m_by_knot_and_cell": target_aperture,
            "current_aperture_m_by_knot_and_cell": aperture,
            "maximum_absolute_aperture_residual_m": aperture_residual,
            "allowed_aperture_residual_m": aperture_allowed,
            "maximum_absolute_hydraulic_velocity_residual_m_s": velocity_residual,
            "allowed_hydraulic_velocity_residual_m_s": velocity_allowed,
            "transport_function_evaluations_cumulative": total_evaluations,
            "transport_chemistry_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "element_inventory_closure_history_sha256": canonical_digest(result.values["element_inventory_closure_history"]),
            "converged": False,
        }
        if total_evaluations > request.maximum_total_transport_function_evaluations:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "failed_iteration": iteration,
                "reason": "outer fixed-point transport evaluation budget exceeded",
                "accepted_trial_prefix": prefix + [record],
                "committed": False,
            })
        prefix.append(record)
        if aperture_residual <= aperture_allowed and velocity_residual <= velocity_allowed:
            record["converged"] = True
            converged = True
            last_result = result
            aperture = target_aperture
            break
        fraction = request.relaxation_fraction
        aperture = [[aperture[k][i] + fraction * (target_aperture[k][i] - aperture[k][i])
                     for i in range(nc)] for k in range(nt)]
    if not converged or last_result is None:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "termination_reason": "aperture and hydraulic residuals did not both converge within the declared budget",
            "iteration_count": len(prefix), "iteration_lineage": prefix,
            "accepted_trial_prefix_sha256": canonical_digest(prefix),
            "committed": False,
        })
    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "geometry_mode": "caller_volume_to_gap_mapping_with_bounded_hydraulic_sensitivity",
        "converged_aperture_m_by_knot_and_cell": aperture,
        "converged_face_velocity_m_s_by_knot_and_face": target_velocity.tolist(),
        "fixed_point_iteration_count": len(prefix),
        "iteration_lineage": prefix,
        "accepted_trial_prefix_sha256": canonical_digest(prefix),
        "coupled_transport_chemistry_result": last_result.model_dump(mode="json"),
        "element_inventory_closure_history": last_result.values["element_inventory_closure_history"],
        "transport_face_flux_history": last_result.values["transport_face_flux_history"],
        "total_transport_function_evaluations": total_evaluations,
        "aperture_and_hydraulic_residuals_converged": True,
        "all_kinetics_and_hydraulic_response_caller_owned": True,
        "automatic_kinetics_or_flow_law": False,
        "phase_discovery": False,
        "committed": True,
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSpatialChemistryApertureFixedPointRequest,
        evaluator=solve_crevice_spatial_chemistry_aperture_fixed_point,
        units={
            "converged_aperture_m_by_knot_and_cell[][]": "m",
            "converged_face_velocity_m_s_by_knot_and_face[][]": "m/s",
            "aperture_residual_m_by_knot_and_cell[][]": "m",
            "hydraulic_velocity_residual_m_s_by_knot_and_face[][]": "m/s",
        },
        assumptions=(
            "Each outer trial reruns the registered spatial chemistry-transport operator-split calculation on its exact knot history.",
            "Aperture response is derived only from caller-mapped finite solid volume and a caller-reviewed solid-volume-to-gap coefficient.",
            "Hydraulic feedback is a bounded caller-supplied aperture sensitivity tensor; no pressure-flow law is inferred.",
            "Both aperture and face-velocity residuals must satisfy caller tolerances before committing a result; failure retains the accepted trial prefix.",
            "Aqueous activity/speciation is held over each transport interval and recalculated at the endpoint knot; no monolithic chemistry-transport integration is claimed.",
        ),
        source_ids=(APERTURE_SOURCE_ID, HYDRAULIC_SOURCE_ID, METHOD_SOURCE_ID),
        qualification="user_model",
    ),)
