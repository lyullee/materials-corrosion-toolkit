"""Reduce a caller-provided linear structural stiffness operator to gasket contact DOFs."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Positive, canonical_digest
from ..registry import ModelSpec


class FlangeComplianceReductionRequest(Contract):
    reduction_id: str = Field(min_length=1)
    upstream_solver_id: str = Field(min_length=1)
    upstream_solver_revision: str = Field(min_length=1)
    stiffness_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stiffness_matrix_N_m: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=128)
    fixed_incremental_dof_indices: tuple[int, ...] = ()
    contact_node_ids: tuple[str, ...] = Field(min_length=2, max_length=64)
    contact_normal_dof_indices: tuple[int, ...] = Field(min_length=2, max_length=64)
    contact_closure_signs: tuple[Literal[-1, 1], ...] = Field(min_length=2, max_length=64)
    symmetry_relative_tolerance: float = Field(default=1e-10, gt=0, le=1e-5)
    minimum_positive_stiffness_eigenvalue_N_m: Positive = 1e-12
    maximum_free_operator_condition_number: Positive = Field(default=1e12, ge=1, le=1e14)
    stiffness_units_and_scaling_reviewed: bool
    fixed_supports_and_boundary_dofs_reviewed: bool
    contact_normal_dof_mapping_reviewed: bool
    incremental_linear_elastic_applicability_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_reduction_indices(self):
        dof_count = len(self.stiffness_matrix_N_m)
        if any(len(row) != dof_count for row in self.stiffness_matrix_N_m):
            raise ValueError("structural stiffness matrix must be square")
        contact_count = len(self.contact_node_ids)
        if len(set(self.contact_node_ids)) != contact_count:
            raise ValueError("contact node IDs must be unique and ordered")
        if len(self.contact_normal_dof_indices) != contact_count or len(self.contact_closure_signs) != contact_count:
            raise ValueError("one contact DOF and closure sign are required for each contact node")
        if len(set(self.contact_normal_dof_indices)) != contact_count:
            raise ValueError("each contact node must map to a unique structural DOF")
        if len(set(self.fixed_incremental_dof_indices)) != len(self.fixed_incremental_dof_indices):
            raise ValueError("fixed incremental DOF indices must be unique")
        all_indices = self.fixed_incremental_dof_indices + self.contact_normal_dof_indices
        if any(index < 0 or index >= dof_count for index in all_indices):
            raise ValueError("fixed and contact DOF indices must lie in the global stiffness matrix")
        if set(self.fixed_incremental_dof_indices) & set(self.contact_normal_dof_indices):
            raise ValueError("contact response DOFs cannot be fixed supports")
        if len(self.contact_node_ids) > dof_count - len(set(self.fixed_incremental_dof_indices)):
            raise ValueError("fewer free structural DOFs than requested contact nodes")
        return self


def reduce_flange_contact_compliance(request: FlangeComplianceReductionRequest) -> Calculation:
    """Solve selected translational responses for signed unit contact loads.

    The input is an upstream, consistently scaled incremental stiffness matrix whose
    retained DOFs all use translation/displacement and force units N/m. Rotational or
    mixed-unit coordinates must be condensed by the supplying solver before this API.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "reduction_id": request.reduction_id,
        "upstream_solver_id": request.upstream_solver_id,
        "upstream_solver_revision": request.upstream_solver_revision,
        "stiffness_source_sha256": request.stiffness_source_sha256,
        "input_sha256": digest,
        "contact_node_ids": list(request.contact_node_ids),
    }
    reviews = {
        "stiffness_units_and_scaling_reviewed": request.stiffness_units_and_scaling_reviewed,
        "fixed_supports_and_boundary_dofs_reviewed": request.fixed_supports_and_boundary_dofs_reviewed,
        "contact_normal_dof_mapping_reviewed": request.contact_normal_dof_mapping_reviewed,
        "incremental_linear_elastic_applicability_reviewed": request.incremental_linear_elastic_applicability_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    stiffness = np.asarray(request.stiffness_matrix_N_m, dtype=float)
    matrix_scale = float(np.linalg.norm(stiffness, ord=np.inf))
    if not np.isfinite(stiffness).all() or not math.isfinite(matrix_scale) or matrix_scale <= 0:
        return Calculation(status="out_of_scope", values=base | {"reason": "stiffness_matrix_nonfinite_or_zero"})
    symmetry_error = float(np.max(np.abs(stiffness - stiffness.T)))
    if symmetry_error > request.symmetry_relative_tolerance * matrix_scale:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "stiffness_matrix_not_symmetric_within_reviewed_tolerance",
            "maximum_symmetry_error_N_m": symmetry_error,
        })
    stiffness = 0.5 * (stiffness + stiffness.T)
    fixed = set(request.fixed_incremental_dof_indices)
    free_indices = [index for index in range(stiffness.shape[0]) if index not in fixed]
    position = {global_index: local_index for local_index, global_index in enumerate(free_indices)}
    contact_positions = np.asarray([position[index] for index in request.contact_normal_dof_indices], dtype=int)
    reduced_stiffness = stiffness[np.ix_(free_indices, free_indices)]
    try:
        eigenvalues = np.linalg.eigvalsh(reduced_stiffness)
        minimum_eigenvalue = float(eigenvalues[0])
        condition_number = float(np.linalg.cond(reduced_stiffness))
        if (
            not np.isfinite(eigenvalues).all()
            or not math.isfinite(condition_number)
            or minimum_eigenvalue < request.minimum_positive_stiffness_eigenvalue_N_m
            or condition_number > request.maximum_free_operator_condition_number
        ):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "free_incremental_stiffness_not_sufficiently_positive_or_conditioned",
                "minimum_free_stiffness_eigenvalue_N_m": minimum_eigenvalue,
                "free_stiffness_condition_number": condition_number,
            })
        rhs = np.zeros((len(free_indices), len(contact_positions)), dtype=float)
        signs = np.asarray(request.contact_closure_signs, dtype=float)
        rhs[contact_positions, np.arange(len(contact_positions))] = signs
        displacement = np.linalg.solve(reduced_stiffness, rhs)
        compliance = signs[:, None] * displacement[contact_positions, :]
        if not np.isfinite(compliance).all():
            return Calculation(status="out_of_scope", values=base | {"reason": "contact_compliance_nonfinite"})
        compliance_asymmetry = float(np.max(np.abs(compliance - compliance.T)))
        compliance = 0.5 * (compliance + compliance.T)
        compliance_eigenvalues = np.linalg.eigvalsh(compliance)
    except np.linalg.LinAlgError as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "free_incremental_stiffness_solve_failed",
            "detail": str(error),
        })
    compliance_scale = max(float(np.linalg.norm(compliance, ord=np.inf)), np.finfo(float).tiny)
    if (
        not np.isfinite(compliance_eigenvalues).all()
        or float(compliance_eigenvalues[0]) < -request.symmetry_relative_tolerance * compliance_scale
        or compliance_asymmetry > request.symmetry_relative_tolerance * compliance_scale
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "reduced_contact_compliance_failed_symmetry_or_positive_semidefinite_check",
            "minimum_contact_compliance_eigenvalue_m_N": float(compliance_eigenvalues[0]),
            "maximum_contact_compliance_asymmetry_m_N": compliance_asymmetry,
        })
    matrix = compliance.tolist()
    return Calculation(status="computed", values=base | {
        "flange_relative_compliance_matrix_m_N": matrix,
        "downstream_contact_operator": {
            "node_ids": list(request.contact_node_ids),
            "flange_relative_compliance_matrix_m_N": matrix,
        },
        "free_structural_dof_count": len(free_indices),
        "contact_node_count": len(contact_positions),
        "minimum_free_stiffness_eigenvalue_N_m": minimum_eigenvalue,
        "free_stiffness_condition_number": condition_number,
        "minimum_contact_compliance_eigenvalue_m_N": float(compliance_eigenvalues[0]),
        "maximum_contact_compliance_asymmetry_m_N": compliance_asymmetry,
        "basis": "Selected signed translation DOFs reduced from an upstream constrained, linear incremental stiffness matrix; intended to populate spatial gasket contact operator inputs.",
        "scope": "No FE mesh assembly, material law generation, baseline thermal/pressure displacement, nonlinear contact, local stress, leakage, seal criterion or acceptance is computed.",
    })


class FlangeComplianceReductionHistoryRequest(Contract):
    history_id: str = Field(min_length=1)
    upstream_solver_id: str = Field(min_length=1)
    upstream_solver_revision: str = Field(min_length=1)
    times_s: tuple[float, ...] = Field(min_length=2, max_length=1000)
    stiffness_source_sha256: tuple[str, ...] = Field(min_length=2, max_length=1000)
    stiffness_matrices_N_m: tuple[tuple[tuple[float, ...], ...], ...] = Field(min_length=2, max_length=1000)
    fixed_incremental_dof_indices: tuple[int, ...] = ()
    contact_node_ids: tuple[str, ...] = Field(min_length=2, max_length=64)
    contact_normal_dof_indices: tuple[int, ...] = Field(min_length=2, max_length=64)
    contact_closure_signs: tuple[Literal[-1, 1], ...] = Field(min_length=2, max_length=64)
    symmetry_relative_tolerance: float = Field(default=1e-10, gt=0, le=1e-5)
    minimum_positive_stiffness_eigenvalue_N_m: Positive = 1e-12
    maximum_free_operator_condition_number: Positive = Field(default=1e12, ge=1, le=1e14)
    stiffness_units_and_scaling_reviewed: bool
    fixed_supports_and_boundary_dofs_reviewed: bool
    contact_normal_dof_mapping_reviewed: bool
    incremental_linear_elastic_applicability_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_operator_history(self):
        count = len(self.times_s)
        if len(self.stiffness_matrices_N_m) != count or len(self.stiffness_source_sha256) != count:
            raise ValueError("time, stiffness matrix, and source digest rows must align")
        if self.times_s[0] != 0 or any(not math.isfinite(value) for value in self.times_s) or any(
            right <= left for left, right in zip(self.times_s[:-1], self.times_s[1:], strict=True)
        ):
            raise ValueError("operator history requires a finite zero-based increasing time vector")
        size = len(self.stiffness_matrices_N_m[0])
        if size < 2 or size > 128 or count * size * size > 1_000_000:
            raise ValueError("stiffness history exceeds the bounded matrix/time budget")
        if any(len(matrix) != size or any(len(row) != size for row in matrix) for matrix in self.stiffness_matrices_N_m):
            raise ValueError("every stiffness matrix must have the same square dimension")
        if any(len(value) != 64 or any(char not in "0123456789abcdef" for char in value) for value in self.stiffness_source_sha256):
            raise ValueError("each stiffness history source requires a lowercase SHA-256 digest")
        contact_count = len(self.contact_node_ids)
        if len(set(self.contact_node_ids)) != contact_count:
            raise ValueError("contact node IDs must be unique and ordered")
        if len(self.contact_normal_dof_indices) != contact_count or len(self.contact_closure_signs) != contact_count:
            raise ValueError("one contact DOF and closure sign are required for each contact node")
        if len(set(self.contact_normal_dof_indices)) != contact_count:
            raise ValueError("each contact node must map to a unique structural DOF")
        if len(set(self.fixed_incremental_dof_indices)) != len(self.fixed_incremental_dof_indices):
            raise ValueError("fixed incremental DOF indices must be unique")
        indices = self.fixed_incremental_dof_indices + self.contact_normal_dof_indices
        if any(index < 0 or index >= size for index in indices):
            raise ValueError("fixed and contact DOF indices must lie in every stiffness matrix")
        if set(self.fixed_incremental_dof_indices) & set(self.contact_normal_dof_indices):
            raise ValueError("contact response DOFs cannot be fixed supports")
        if len(self.contact_node_ids) > size - len(set(self.fixed_incremental_dof_indices)):
            raise ValueError("fewer free structural DOFs than requested contact nodes")
        return self


def reduce_flange_contact_compliance_history(request: FlangeComplianceReductionHistoryRequest) -> Calculation:
    """Reduce each caller-supplied tangent stiffness matrix on one aligned time grid."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "history_id": request.history_id,
        "upstream_solver_id": request.upstream_solver_id,
        "upstream_solver_revision": request.upstream_solver_revision,
        "input_sha256": digest,
        "times_s": list(request.times_s),
        "contact_node_ids": list(request.contact_node_ids),
        "stiffness_source_sha256": list(request.stiffness_source_sha256),
    }
    reviews = {
        "stiffness_units_and_scaling_reviewed": request.stiffness_units_and_scaling_reviewed,
        "fixed_supports_and_boundary_dofs_reviewed": request.fixed_supports_and_boundary_dofs_reviewed,
        "contact_normal_dof_mapping_reviewed": request.contact_normal_dof_mapping_reviewed,
        "incremental_linear_elastic_applicability_reviewed": request.incremental_linear_elastic_applicability_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    rows = []
    for index, (time_s, matrix, source_sha256) in enumerate(zip(
        request.times_s, request.stiffness_matrices_N_m, request.stiffness_source_sha256, strict=True
    )):
        reduced = reduce_flange_contact_compliance(FlangeComplianceReductionRequest(
            reduction_id=f"{request.history_id}:{index}",
            upstream_solver_id=request.upstream_solver_id,
            upstream_solver_revision=request.upstream_solver_revision,
            stiffness_source_sha256=source_sha256,
            stiffness_matrix_N_m=matrix,
            fixed_incremental_dof_indices=request.fixed_incremental_dof_indices,
            contact_node_ids=request.contact_node_ids,
            contact_normal_dof_indices=request.contact_normal_dof_indices,
            contact_closure_signs=request.contact_closure_signs,
            symmetry_relative_tolerance=request.symmetry_relative_tolerance,
            minimum_positive_stiffness_eigenvalue_N_m=request.minimum_positive_stiffness_eigenvalue_N_m,
            maximum_free_operator_condition_number=request.maximum_free_operator_condition_number,
            stiffness_units_and_scaling_reviewed=True,
            fixed_supports_and_boundary_dofs_reviewed=True,
            contact_normal_dof_mapping_reviewed=True,
            incremental_linear_elastic_applicability_reviewed=True,
            computational_use_authorized=True,
        ))
        reduced_row = reduced.model_dump(mode="json")
        rows.append({"time_s": time_s, **reduced_row})
    statuses = [row["status"] for row in rows]
    status = (
        "computed" if all(item == "computed" for item in statuses)
        else "needs_data" if any(item == "needs_data" for item in statuses)
        else "out_of_scope"
    )
    return Calculation(status=status, values=base | {
        "operator_history": rows,
        "downstream_usage": "Pass each row values.flange_relative_compliance_matrix_m_N and node order to the matching spatial gasket contact request.",
        "basis": "Independent linear incremental stiffness reductions at caller-declared times; rows do not define interpolation, contact-transition timing, or a nonlinear structural solution.",
    })


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "fabrication.flange_contact_compliance_reduction",
            FlangeComplianceReductionRequest,
            reduce_flange_contact_compliance,
            {
                "flange_relative_compliance_matrix_m_N": "m/N",
                "minimum_free_stiffness_eigenvalue_N_m": "N/m",
                "free_stiffness_condition_number": "1",
            },
            (
                "Condense an explicitly supplied constrained incremental translational stiffness operator to selected signed gasket-contact DOFs.",
                "This accepts external solver matrices; it does not assemble an FE model, infer loads/material data, solve nonlinear gasket contact, or qualify sealing/leakage/acceptance.",
            ),
            ("caller_linear_flange_contact_compliance_reduction",),
            qualification="user_model",
        ),
        ModelSpec(
            "fabrication.flange_contact_compliance_reduction_history",
            FlangeComplianceReductionHistoryRequest,
            reduce_flange_contact_compliance_history,
            {
                "times_s": "s",
                "operator_history[].values.flange_relative_compliance_matrix_m_N": "m/N",
            },
            (
                "Reduce one caller-supplied constrained linear incremental stiffness matrix per aligned geometry/time knot using a fixed node/DOF mapping.",
                "No matrix interpolation, FE response generation, nonlinear contact, leakage, seal qualification or between-knot transition is inferred.",
            ),
            ("caller_linear_flange_contact_compliance_history",),
            qualification="user_model",
        ),
    ]
