"""Spatial gasket contact from an explicitly supplied flange compliance operator."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class FlangeContactFieldRequest(Contract):
    schema_version: Literal["matintegrity.flange_contact_field.v1"] = "matintegrity.flange_contact_field.v1"
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    response_provider_id: str = Field(min_length=1)
    response_provider_revision: str = Field(min_length=1)
    response_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_ids: tuple[str, ...] = Field(min_length=2, max_length=256)
    circumferential_coordinate_rad: tuple[float, ...] = Field(min_length=2, max_length=256)
    gasket_contact_area_m2: tuple[Positive, ...] = Field(min_length=2, max_length=256)
    gasket_compressive_stiffness_N_m: tuple[Positive, ...] = Field(min_length=2, max_length=256)
    free_closure_without_gasket_m: tuple[float, ...] = Field(min_length=2, max_length=256)
    flange_relative_compliance_matrix_m_N: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=256)
    matrix_symmetry_tolerance_m_N: Positive = Field(le=1e-6)
    compliance_psd_tolerance_m_N: Positive = Field(le=1e-6)
    active_set_maximum_iterations: int = Field(default=10000, ge=1, le=100000)
    active_set_work_budget: int = Field(default=50_000_000, ge=1, le=1_000_000_000)
    force_tolerance_N: Positive = Field(default=1e-6)
    gap_tolerance_m: Positive = Field(default=1e-12)
    complementarity_tolerance_N_m: Positive = Field(default=1e-9)
    flange_operator_basis_reviewed: bool
    response_scope_and_coordinates_reviewed: bool
    bolt_pressure_and_boundary_load_composition_reviewed: bool
    gasket_linearization_and_support_reviewed: bool
    compression_only_contact_model_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_operator(self):
        count = len(self.node_ids)
        if len(set(self.node_ids)) != count:
            raise ValueError("contact node IDs must be unique")
        aligned = (
            self.circumferential_coordinate_rad,
            self.gasket_contact_area_m2,
            self.gasket_compressive_stiffness_N_m,
            self.free_closure_without_gasket_m,
            self.flange_relative_compliance_matrix_m_N,
        )
        if any(len(rows) != count for rows in aligned):
            raise ValueError("all node arrays and the compliance matrix must align with node_ids")
        if any(len(row) != count for row in self.flange_relative_compliance_matrix_m_N):
            raise ValueError("flange compliance matrix must be square")
        for i in range(count):
            for j in range(count):
                left = self.flange_relative_compliance_matrix_m_N[i][j]
                right = self.flange_relative_compliance_matrix_m_N[j][i]
                if not math.isfinite(left) or abs(left - right) > self.matrix_symmetry_tolerance_m_N:
                    raise ValueError("caller flange compliance matrix must be finite and symmetric within declared tolerance")
        if any(not math.isfinite(value) for value in (*self.circumferential_coordinate_rad, *self.free_closure_without_gasket_m)):
            raise ValueError("coordinates and free-closure values must be finite")
        return self


class FlangeNonlinearContactFieldRequest(Contract):
    """Spatial field using a caller-supplied reversible gasket backbone per node."""

    schema_version: Literal["matintegrity.flange_nonlinear_contact_field.v1"] = "matintegrity.flange_nonlinear_contact_field.v1"
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    response_provider_id: str = Field(min_length=1)
    response_provider_revision: str = Field(min_length=1)
    response_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_ids: tuple[str, ...] = Field(min_length=2, max_length=128)
    circumferential_coordinate_rad: tuple[float, ...] = Field(min_length=2, max_length=128)
    gasket_contact_area_m2: tuple[Positive, ...] = Field(min_length=2, max_length=128)
    free_closure_without_gasket_m: tuple[float, ...] = Field(min_length=2, max_length=128)
    flange_relative_compliance_matrix_m_N: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=128)
    gasket_force_compression_curves: tuple[tuple[tuple[Nonnegative, Nonnegative], ...], ...] = Field(min_length=2, max_length=128)
    matrix_symmetry_tolerance_m_N: Positive = Field(le=1e-6)
    compliance_psd_tolerance_m_N: Positive = Field(le=1e-6)
    maximum_curve_points_per_node: int = Field(default=1000, ge=2, le=10000)
    maximum_nonlinear_iterations: int = Field(default=100, ge=1, le=10000)
    maximum_line_search_steps: int = Field(default=24, ge=1, le=100)
    residual_tolerance_N: Positive = Field(default=1e-5)
    displacement_tolerance_m: Positive = Field(default=1e-12)
    flange_operator_basis_reviewed: bool
    response_scope_and_coordinates_reviewed: bool
    bolt_pressure_and_boundary_load_composition_reviewed: bool
    gasket_curve_and_support_reviewed: bool
    compression_only_contact_model_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_curves_and_operator(self):
        count = len(self.node_ids)
        if len(set(self.node_ids)) != count:
            raise ValueError("contact node IDs must be unique")
        if any(len(rows) != count for rows in (
            self.circumferential_coordinate_rad,
            self.gasket_contact_area_m2,
            self.free_closure_without_gasket_m,
            self.flange_relative_compliance_matrix_m_N,
            self.gasket_force_compression_curves,
        )):
            raise ValueError("all node arrays and compliance rows must align with node_ids")
        if any(len(row) != count for row in self.flange_relative_compliance_matrix_m_N):
            raise ValueError("flange compliance matrix must be square")
        if any(not math.isfinite(v) for v in (*self.circumferential_coordinate_rad, *self.free_closure_without_gasket_m)):
            raise ValueError("coordinates and free-closure values must be finite")
        if any(not math.isfinite(area) for area in self.gasket_contact_area_m2):
            raise ValueError("gasket contact areas must be finite")
        for i in range(count):
            for j in range(count):
                a = self.flange_relative_compliance_matrix_m_N[i][j]
                b = self.flange_relative_compliance_matrix_m_N[j][i]
                if not math.isfinite(a) or abs(a - b) > self.matrix_symmetry_tolerance_m_N:
                    raise ValueError("caller flange compliance must be finite and symmetric")
            curve = self.gasket_force_compression_curves[i]
            if len(curve) < 2 or len(curve) > self.maximum_curve_points_per_node:
                raise ValueError("each gasket curve must have 2..maximum_curve_points_per_node points")
            if any(not math.isfinite(value) or value < 0 for point in curve for value in point):
                raise ValueError("gasket curve coordinates must be finite and nonnegative")
            if curve[0] != (0, 0):
                raise ValueError("each gasket curve must begin at zero compression and force")
            if any(b[0] <= a[0] or b[1] <= a[1] for a, b in zip(curve[:-1], curve[1:], strict=True)):
                raise ValueError("gasket compression and force must both increase strictly")
        return self


class FlangePronyBranch(Contract):
    branch_id: str = Field(min_length=1)
    modulus_Pa: Positive
    relaxation_time_s: Positive


class FlangeViscoelasticContactHistoryRequest(Contract):
    """Spatial linear-Prony gasket contact on a caller-supplied flange operator."""

    schema_version: Literal["matintegrity.flange_viscoelastic_contact_history.v1"] = "matintegrity.flange_viscoelastic_contact_history.v1"
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    response_provider_id: str = Field(min_length=1)
    response_provider_revision: str = Field(min_length=1)
    response_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_ids: tuple[str, ...] = Field(min_length=2, max_length=128)
    times_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=10000)
    circumferential_coordinate_rad: tuple[float, ...] = Field(min_length=2, max_length=128)
    gasket_contact_area_m2: tuple[Positive, ...] = Field(min_length=2, max_length=128)
    gasket_thickness_m: tuple[Positive, ...] = Field(min_length=2, max_length=128)
    equilibrium_modulus_Pa: tuple[Nonnegative, ...] = Field(min_length=2, max_length=128)
    prony_branches: tuple[tuple[FlangePronyBranch, ...], ...] = Field(min_length=2, max_length=128)
    initial_branch_stress_Pa: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=128)
    free_closure_without_gasket_m: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=10000)
    flange_relative_compliance_matrix_m_N: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=128)
    flange_compliance_history_result: dict | None = None
    flange_compliance_history_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    matrix_symmetry_tolerance_m_N: Positive = Field(le=1e-6)
    compliance_psd_tolerance_m_N: Positive = Field(le=1e-6)
    maximum_contact_iterations: int = Field(default=10000, ge=1, le=100000)
    maximum_contact_work_units: int = Field(default=50_000_000, ge=1, le=1_000_000_000)
    gap_tolerance_m: Positive = Field(default=1e-12)
    force_tolerance_N: Positive = Field(default=1e-6)
    flange_operator_basis_reviewed: bool
    response_scope_and_coordinates_reviewed: bool
    bolt_pressure_and_boundary_load_composition_reviewed: bool
    gasket_prony_calibration_and_support_reviewed: bool
    initial_branch_state_reviewed: bool
    zero_compression_branch_state_reviewed: bool
    compression_only_contact_model_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_history_and_material(self):
        n = len(self.node_ids)
        if len(set(self.node_ids)) != n:
            raise ValueError("contact node IDs must be unique")
        if any(len(values) != n for values in (
            self.circumferential_coordinate_rad, self.gasket_contact_area_m2,
            self.gasket_thickness_m, self.equilibrium_modulus_Pa, self.prony_branches,
            self.initial_branch_stress_Pa,
        )):
            raise ValueError("all spatial material and coordinate arrays must align with node_ids")
        if len(self.times_s) != len(self.free_closure_without_gasket_m):
            raise ValueError("free-closure rows must align with the time vector")
        if any(b <= a for a, b in zip(self.times_s[:-1], self.times_s[1:], strict=True)):
            raise ValueError("time knots must strictly increase")
        if any(len(row) != n or any(not math.isfinite(v) for v in row) for row in self.free_closure_without_gasket_m):
            raise ValueError("each finite free-closure row must align with node_ids")
        if len(self.flange_relative_compliance_matrix_m_N) != n or any(len(row) != n for row in self.flange_relative_compliance_matrix_m_N):
            raise ValueError("flange compliance matrix must be square and aligned")
        if (self.flange_compliance_history_result is None) != (self.flange_compliance_history_sha256 is None):
            raise ValueError("time-varying flange compliance requires both the pinned history result and its digest")
        if self.flange_compliance_history_result is not None:
            if canonical_digest(self.flange_compliance_history_result) != self.flange_compliance_history_sha256:
                raise ValueError("flange compliance history digest does not match the supplied result")
            history = self.flange_compliance_history_result
            values = history.get("values", history)
            operator_rows = values.get("operator_history") if isinstance(values, dict) else None
            if history.get("status") != "computed" or not isinstance(operator_rows, list) or len(operator_rows) != len(self.times_s):
                raise ValueError("a computed compliance history with one row per contact time is required")
            if values.get("contact_node_ids") != list(self.node_ids) or values.get("times_s") != list(self.times_s):
                raise ValueError("compliance-history contact node order and time knots must exactly match the gasket request")
            for index, row in enumerate(operator_rows):
                if not isinstance(row, dict):
                    raise ValueError("compliance-history rows must be objects")
                row_values = row.get("values")
                matrix = row_values.get("flange_relative_compliance_matrix_m_N") if isinstance(row_values, dict) else None
                if row.get("status") != "computed" or row.get("time_s") != self.times_s[index]:
                    raise ValueError("every compliance-history row must be computed at the matching time knot")
                if not isinstance(matrix, list) or len(matrix) != n or any(not isinstance(values, list) or len(values) != n for values in matrix):
                    raise ValueError("every compliance-history operator must be square and aligned with contact node order")
                if any(
                    isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                    for values in matrix for value in values
                ):
                    raise ValueError("compliance-history operators must contain finite numeric values")
                if any(
                    abs(matrix[i][j] - matrix[j][i]) > self.matrix_symmetry_tolerance_m_N
                    for i in range(n) for j in range(n)
                ):
                    raise ValueError("every compliance-history operator must be symmetric within the declared tolerance")
                if index == 0 and any(
                    not math.isclose(float(matrix[i][j]), self.flange_relative_compliance_matrix_m_N[i][j], rel_tol=1e-10, abs_tol=1e-15)
                    for i in range(n) for j in range(n)
                ):
                    raise ValueError("legacy compliance matrix must equal the first pinned history operator")
        if any(not math.isfinite(v) for v in (*self.circumferential_coordinate_rad, *self.equilibrium_modulus_Pa, *self.initial_branch_stress_Pa[0])):
            raise ValueError("coordinates, moduli and branch states must be finite")
        for i, branches in enumerate(self.prony_branches):
            if not branches or len({branch.branch_id for branch in branches}) != len(branches):
                raise ValueError("each node needs uniquely identified Prony branches")
            if len(self.initial_branch_stress_Pa[i]) != len(branches) or any(not math.isfinite(v) for v in self.initial_branch_stress_Pa[i]):
                raise ValueError("initial branch stresses must align with each node's branches")
        for i in range(n):
            for j in range(n):
                a, b = self.flange_relative_compliance_matrix_m_N[i][j], self.flange_relative_compliance_matrix_m_N[j][i]
                if not math.isfinite(a) or abs(a - b) > self.matrix_symmetry_tolerance_m_N:
                    raise ValueError("caller flange compliance must be finite and symmetric")
        return self


def flange_viscoelastic_contact_history(x: FlangeViscoelasticContactHistoryRequest) -> Calculation:
    """Advance exact linear-Prony branch states and solve unilateral contact at each knot."""
    digest = canonical_digest(x.model_dump(mode="json"))
    n, nt = len(x.node_ids), len(x.times_s)
    base = {
        "assessment_id": x.assessment_id, "joint_id": x.joint_id,
        "physical_scope_id": x.physical_scope_id, "response_provider_id": x.response_provider_id,
        "response_provider_revision": x.response_provider_revision,
        "response_configuration_digest": x.response_configuration_digest,
        "response_result_digest": x.response_result_digest, "input_digest": digest,
        "node_count": n, "time_knot_count": nt,
        "flange_compliance_history_sha256": x.flange_compliance_history_sha256,
    }
    reviews = {
        "flange_operator_basis_reviewed": x.flange_operator_basis_reviewed,
        "response_scope_and_coordinates_reviewed": x.response_scope_and_coordinates_reviewed,
        "bolt_pressure_and_boundary_load_composition_reviewed": x.bolt_pressure_and_boundary_load_composition_reviewed,
        "gasket_prony_calibration_and_support_reviewed": x.gasket_prony_calibration_and_support_reviewed,
        "initial_branch_state_reviewed": x.initial_branch_state_reviewed,
        "zero_compression_branch_state_reviewed": x.zero_compression_branch_state_reviewed,
        "compression_only_contact_model_reviewed": x.compression_only_contact_model_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    C_history = [np.asarray(x.flange_relative_compliance_matrix_m_N, dtype=float)] * nt
    compliance_source_history = [None] * nt
    if x.flange_compliance_history_result is not None:
        history_values = x.flange_compliance_history_result.get("values", x.flange_compliance_history_result)
        history_rows = history_values["operator_history"]
        C_history = [np.asarray(row["values"]["flange_relative_compliance_matrix_m_N"], dtype=float) for row in history_rows]
        compliance_source_history = [row["values"].get("stiffness_source_sha256") for row in history_rows]
    C_history = [0.5 * (matrix + matrix.T) for matrix in C_history]
    try:
        eigenvalues = [float(np.linalg.eigvalsh(0.5 * (C + C.T))[0]) for C in C_history]
        eigmin = min(eigenvalues)
        if any(value < -x.compliance_psd_tolerance_m_N for value in eigenvalues):
            return Calculation(status="out_of_scope", values=base | {"minimum_flange_compliance_eigenvalue_m_N": eigmin, "flange_compliance_minimum_eigenvalues_m_N": eigenvalues, "out_of_scope_reason": "flange_compliance_operator_not_positive_semidefinite"})
    except (np.linalg.LinAlgError, ValueError, FloatingPointError) as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "invalid_compliance_operator", "detail": str(error)})
    branch_state = [list(row) for row in x.initial_branch_stress_Pa]
    previous_compression = [0.0] * n
    fields = []
    work = 0
    for k, time_s in enumerate(x.times_s):
        C = C_history[k]
        rhs_closure = np.asarray(x.free_closure_without_gasket_m[k], dtype=float)
        if k == 0:
            dt = 0.0
            decays = [[1.0] * len(x.prony_branches[i]) for i in range(n)]
            # The initial knot is an instantaneous load from the reviewed
            # zero-compression reference state; each Maxwell spring is elastic
            # at that instant and its state is initialized below.
            ramps = [[1.0] * len(x.prony_branches[i]) for i in range(n)]
        else:
            dt = time_s - x.times_s[k - 1]
            decays, ramps = [], []
            for branches in x.prony_branches:
                drow, rrow = [], []
                for branch in branches:
                    ratio = dt / branch.relaxation_time_s
                    decay = math.exp(-ratio) if ratio < 745 else 0.0
                    drow.append(decay)
                    rrow.append(-math.expm1(-ratio) * branch.relaxation_time_s / dt)
                decays.append(drow); ramps.append(rrow)
        effective_modulus, intercept = [], []
        for i, branches in enumerate(x.prony_branches):
            e = x.equilibrium_modulus_Pa[i] + math.fsum(branch.modulus_Pa * ramps[i][j] for j, branch in enumerate(branches))
            b = math.fsum(branch_state[i][j] * decays[i][j] - branch.modulus_Pa * ramps[i][j] * previous_compression[i] / x.gasket_thickness_m[i] for j, branch in enumerate(branches))
            if not math.isfinite(e) or e <= 0 or not math.isfinite(b):
                return Calculation(status="out_of_scope", values=base | {"computed_prefix": fields, "first_unsupported_time_s": time_s, "out_of_scope_reason": "nonpositive_effective_modulus_or_nonfinite_branch_state"})
            effective_modulus.append(e); intercept.append(b)
        compliance = C.copy()
        target = rhs_closure.copy()
        for i in range(n):
            scale = x.gasket_thickness_m[i] / (x.gasket_contact_area_m2[i] * effective_modulus[i])
            compliance[i, i] += scale
            target[i] += x.gasket_thickness_m[i] * intercept[i] / effective_modulus[i]
        force = np.zeros(n, dtype=float)
        active = set(np.flatnonzero(target > x.gap_tolerance_m).tolist())
        converged = False
        iterations = 0
        for iterations in range(1, min(x.maximum_contact_iterations, x.maximum_contact_work_units // max(n, 1)) + 1):
            work += n * max(len(active), 1)
            if work > x.maximum_contact_work_units:
                break
            if active:
                ids = np.asarray(sorted(active), dtype=int)
                try:
                    force[:] = 0.0
                    force[ids] = np.linalg.solve(compliance[np.ix_(ids, ids)], target[ids])
                except np.linalg.LinAlgError:
                    break
                negative = [i for i in active if force[i] < -x.force_tolerance_N]
                if negative:
                    active.remove(min(negative, key=lambda i: force[i])); continue
                force[force < 0] = 0.0
            gap = compliance @ force - target
            inactive = sorted(set(range(n)) - active)
            violating = [i for i in inactive if gap[i] < -x.gap_tolerance_m]
            if violating:
                active.add(min(violating, key=lambda i: gap[i])); continue
            converged = True
            break
        if not converged:
            return Calculation(status="out_of_scope", values=base | {"computed_prefix": fields, "first_unsupported_time_s": time_s, "contact_work_units": work, "out_of_scope_reason": "contact_active_set_not_converged_or_work_budget_exceeded"}, notes=("A successful time prefix is retained; no aggregate history is claimed after a failed contact knot.",))
        compression = [0.0] * n
        rows = []
        max_active_force_residual = 0.0
        for i in range(n):
            compression[i] = x.gasket_thickness_m[i] * (force[i] / (x.gasket_contact_area_m2[i] * effective_modulus[i]) - intercept[i] / effective_modulus[i]) if force[i] > 0 else 0.0
            compression[i] = max(compression[i], 0.0)
            strain = compression[i] / x.gasket_thickness_m[i]
            for j, branch in enumerate(x.prony_branches[i]):
                branch_state[i][j] = branch_state[i][j] * decays[i][j] + branch.modulus_Pa * ramps[i][j] * (strain - previous_compression[i] / x.gasket_thickness_m[i])
            stress = x.equilibrium_modulus_Pa[i] * strain + math.fsum(branch_state[i])
            gap = float((C @ force)[i] - rhs_closure[i] + compression[i])
            if not all(math.isfinite(v) for v in (compression[i], stress, gap)) or gap < -x.gap_tolerance_m:
                return Calculation(status="out_of_scope", values=base | {"computed_prefix": fields, "first_unsupported_time_s": time_s, "out_of_scope_reason": "constitutive_or_complementarity_residual_failed"})
            if force[i] > 0:
                max_active_force_residual = max(max_active_force_residual, abs(force[i] - x.gasket_contact_area_m2[i] * stress))
            rows.append({"node_id": x.node_ids[i], "circumferential_coordinate_rad": x.circumferential_coordinate_rad[i], "contact_state": "closed" if force[i] > 0 else "open", "contact_force_N": float(force[i]), "mean_contact_pressure_Pa": float(force[i] / x.gasket_contact_area_m2[i]), "gasket_compression_m": compression[i], "gasket_strain": strain, "gasket_stress_Pa": stress, "contact_gap_m": max(gap, 0.0), "branch_stress_Pa": list(branch_state[i])})
        if max_active_force_residual > x.force_tolerance_N:
            return Calculation(status="out_of_scope", values=base | {"computed_prefix": fields, "first_unsupported_time_s": time_s, "maximum_active_force_residual_N": max_active_force_residual, "out_of_scope_reason": "active_contact_constitutive_force_residual_exceeded_tolerance"})
        fields.append({"time_s": time_s, "flange_compliance_stiffness_source_sha256": compliance_source_history[k], "minimum_flange_compliance_eigenvalue_m_N": eigenvalues[k], "contact_iteration_count": iterations, "maximum_active_force_residual_N": max_active_force_residual, "contact_force_sum_N": float(np.sum(force)), "response_field": rows})
        previous_compression = compression
    return Calculation(values=base | {"minimum_flange_compliance_eigenvalue_m_N": eigmin, "contact_work_units": work, "time_history": fields, "basis": "caller_supplied_linear_Prony_gasket_material_and_flange_operator_with_knotwise_unilateral_quasistatic_contact"}, notes=("The initial contact knot is treated as an instantaneous load from a reviewed zero-compression reference state. Each Maxwell branch uses the exact exponential update for the declared linear strain segment between adjacent knots.", "Contact is solved quasi-statically only at supplied knots; intermediate opening/closure times, flange response generation, leakage, local peak stress and acceptance are not inferred."))


def _curve_compression_and_inverse_tangent(curve: tuple[tuple[float, float], ...], force: float) -> tuple[float, float]:
    """Invert a strictly increasing piecewise-linear force/compression curve."""
    if force < 0 or force > curve[-1][1]:
        raise ValueError("gasket force is outside caller curve support")
    ys = [point[1] for point in curve]
    index = min(max(int(np.searchsorted(ys, force, side="right") - 1), 0), len(curve) - 2)
    x0, y0 = curve[index]
    x1, y1 = curve[index + 1]
    inverse_tangent = (x1 - x0) / (y1 - y0)
    return x0 + inverse_tangent * (force - y0), inverse_tangent


def _curve_force_at_compression(curve: tuple[tuple[float, float], ...], compression: float) -> float:
    if compression < 0 or compression > curve[-1][0]:
        raise ValueError("gasket compression is outside caller curve support")
    xs = [point[0] for point in curve]
    index = min(max(int(np.searchsorted(xs, compression, side="right") - 1), 0), len(curve) - 2)
    x0, y0 = curve[index]
    x1, y1 = curve[index + 1]
    return float(y0 + (y1 - y0) * (compression - x0) / (x1 - x0))


def flange_nonlinear_contact_field(x: FlangeNonlinearContactFieldRequest) -> Calculation:
    """Solve a spatial unilateral field with caller-reviewed nonlinear gasket curves.

    Uses ``u0 = C q + c(q)`` where each local compression-force backbone is
    reversible, strictly increasing and piecewise linear. Active nodes are
    solved by damped Newton steps inside declared curve support. The operator
    and loads are caller inputs; this does not produce an FE flange response.
    """
    digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id, "joint_id": x.joint_id,
        "physical_scope_id": x.physical_scope_id,
        "response_provider_id": x.response_provider_id,
        "response_provider_revision": x.response_provider_revision,
        "response_configuration_digest": x.response_configuration_digest,
        "response_result_digest": x.response_result_digest,
        "input_digest": digest, "node_count": len(x.node_ids),
    }
    reviews = {
        "flange_operator_basis_reviewed": x.flange_operator_basis_reviewed,
        "response_scope_and_coordinates_reviewed": x.response_scope_and_coordinates_reviewed,
        "bolt_pressure_and_boundary_load_composition_reviewed": x.bolt_pressure_and_boundary_load_composition_reviewed,
        "gasket_curve_and_support_reviewed": x.gasket_curve_and_support_reviewed,
        "compression_only_contact_model_reviewed": x.compression_only_contact_model_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    C = np.asarray(x.flange_relative_compliance_matrix_m_N, dtype=float)
    u0 = np.asarray(x.free_closure_without_gasket_m, dtype=float)
    try:
        eigmin = float(np.linalg.eigvalsh(0.5 * (C + C.T))[0])
        if eigmin < -x.compliance_psd_tolerance_m_N:
            return Calculation(status="out_of_scope", values=base | {
                "minimum_flange_compliance_eigenvalue_m_N": eigmin,
                "out_of_scope_reason": "flange_compliance_operator_not_positive_semidefinite",
            })
    except (np.linalg.LinAlgError, ValueError, FloatingPointError) as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "invalid_compliance_operator", "detail": str(error)})

    n = len(u0)
    q = np.zeros(n, dtype=float)
    active = set(np.flatnonzero(u0 > x.displacement_tolerance_m).tolist())
    iterations = 0
    total_line_search = 0
    converged = False
    reason = "nonlinear_contact_not_converged"
    try:
        for iterations in range(1, x.maximum_nonlinear_iterations + 1):
            if not active:
                converged = True
                break
            ids = np.asarray(sorted(active), dtype=int)
            residual = np.empty(len(ids), dtype=float)
            tangent = C[np.ix_(ids, ids)].copy()
            for local, i in enumerate(ids):
                compression, inverse_tangent = _curve_compression_and_inverse_tangent(
                    x.gasket_force_compression_curves[i], float(q[i])
                )
                residual[local] = float(C[i] @ q + compression - u0[i])
                tangent[local, local] += inverse_tangent
            norm = float(np.linalg.norm(residual, ord=np.inf))
            if norm <= x.displacement_tolerance_m:
                gap = C @ q - u0
                # Active nodes close through gasket compression; inactive nodes retain free gap.
                for i in active:
                    compression, _ = _curve_compression_and_inverse_tangent(
                        x.gasket_force_compression_curves[i], float(q[i])
                    )
                    gap[i] += compression
                if np.any(np.delete(gap, ids) < -x.displacement_tolerance_m):
                    inactive = sorted(set(range(n)) - active)
                    add = min(inactive, key=lambda j: gap[j])
                    active.add(add)
                    continue
                converged = True
                break
            delta = np.linalg.solve(tangent, -residual)
            old = q.copy()
            accepted = False
            alpha = 1.0
            for _ in range(x.maximum_line_search_steps):
                total_line_search += 1
                candidate = old[ids] + alpha * delta
                if np.any(candidate < 0) or any(
                    candidate[pos] > x.gasket_force_compression_curves[i][-1][1]
                    for pos, i in enumerate(ids)
                ):
                    alpha *= 0.5
                    continue
                candidate_q = np.zeros(n, dtype=float)
                candidate_q[ids] = candidate
                candidate_r = np.empty(len(ids), dtype=float)
                for local, i in enumerate(ids):
                    candidate_compression, _ = _curve_compression_and_inverse_tangent(
                        x.gasket_force_compression_curves[i], float(candidate_q[i])
                    )
                    candidate_r[local] = float(C[i] @ candidate_q + candidate_compression - u0[i])
                if float(np.linalg.norm(candidate_r, ord=np.inf)) < norm:
                    q = candidate_q
                    accepted = True
                    break
                alpha *= 0.5
            if not accepted:
                negative = [
                    (float(old[i] + delta[pos]), i)
                    for pos, i in enumerate(ids)
                    if old[i] + delta[pos] < 0
                ]
                if negative and len(active) > 1:
                    removed = min(negative)[1]
                    active.remove(removed)
                    q[removed] = 0.0
                    q[list(active)] = np.maximum(q[list(active)], 0.0)
                    continue
                reason = "nonlinear_contact_line_search_failed"
                break
    except (ValueError, ArithmeticError, FloatingPointError, np.linalg.LinAlgError) as error:
        reason = str(error) or reason

    # Re-evaluate complementarity and constitutive residual before returning.
    rows = []
    residual_force = 0.0
    min_gap = math.inf
    active_gap_residual = 0.0
    try:
        for i in range(n):
            compression = 0.0
            if q[i] > 0:
                compression, _ = _curve_compression_and_inverse_tangent(
                    x.gasket_force_compression_curves[i], float(q[i])
                )
                expected_force = _curve_force_at_compression(x.gasket_force_compression_curves[i], compression)
            else:
                expected_force = 0.0
            residual_force = max(residual_force, abs(float(q[i]) - expected_force))
            gap = float(C[i] @ q + compression - u0[i])
            min_gap = min(min_gap, gap)
            if i in active:
                active_gap_residual = max(active_gap_residual, abs(gap))
            rows.append({
                "node_id": x.node_ids[i],
                "circumferential_coordinate_rad": x.circumferential_coordinate_rad[i],
                "contact_state": "closed" if q[i] > 0 else "open",
                "contact_force_N": float(q[i]),
                "mean_contact_pressure_Pa": float(q[i] / x.gasket_contact_area_m2[i]),
                "gasket_compression_m": compression,
                "contact_gap_m": max(gap, 0.0),
                "free_closure_without_gasket_m": float(u0[i]),
            })
    except (ValueError, FloatingPointError) as error:
        reason = str(error)
        converged = False
    if (
        residual_force > x.residual_tolerance_N
        or min_gap < -x.displacement_tolerance_m
        or active_gap_residual > x.displacement_tolerance_m
    ):
        converged = False
    if not converged:
        return Calculation(status="out_of_scope", values=base | {
            "nonlinear_iterations": iterations,
            "line_search_steps": total_line_search,
            "maximum_force_residual_N": residual_force,
            "maximum_active_closure_residual_m": active_gap_residual,
            "minimum_gap_m": min_gap,
            "out_of_scope_reason": reason,
        }, notes=("No partial nonlinear contact field is returned when iteration, curve support or complementarity checks fail.",))
    return Calculation(values=base | {
        "nonlinear_iterations": iterations,
        "line_search_steps": total_line_search,
        "maximum_force_residual_N": residual_force,
        "maximum_active_closure_residual_m": active_gap_residual,
        "minimum_flange_compliance_eigenvalue_m_N": eigmin,
        "response_field": rows,
        "contact_force_sum_N": float(np.sum(q)),
        "contact_area_sum_m2": float(sum(x.gasket_contact_area_m2)),
        "contact_model": "caller_flange_compliance_plus_reversible_piecewise_linear_gasket_curves",
    }, notes=(
        "The nodal field is conditional on the exact caller flange operator, load composition and reversible gasket curves.",
        "Mean nodal pressure is force divided by caller area, not local FE stress, leakage, sealing performance or acceptance.",
    ))


def flange_contact_field(x: FlangeContactFieldRequest) -> Calculation:
    """Solve the nodal compression-only contact LCP within a caller operator support.

    Let ``u0`` be the caller-computed closure without gasket reaction, ``C`` the
    relative flange compliance matrix, and ``k`` the local linear gasket
    stiffnesses. The contact forces solve ``q >= 0``, ``g = (C+diag(1/k))q-u0
    >= 0`` and ``q*g = 0``. The compliance operator and load composition are
    inputs; this routine does not perform or approximate an FE flange solution.
    """
    digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "joint_id": x.joint_id,
        "physical_scope_id": x.physical_scope_id,
        "response_provider_id": x.response_provider_id,
        "response_provider_revision": x.response_provider_revision,
        "response_configuration_digest": x.response_configuration_digest,
        "response_result_digest": x.response_result_digest,
        "input_digest": digest,
        "node_count": len(x.node_ids),
    }
    reviews = {
        "flange_operator_basis_reviewed": x.flange_operator_basis_reviewed,
        "response_scope_and_coordinates_reviewed": x.response_scope_and_coordinates_reviewed,
        "bolt_pressure_and_boundary_load_composition_reviewed": x.bolt_pressure_and_boundary_load_composition_reviewed,
        "gasket_linearization_and_support_reviewed": x.gasket_linearization_and_support_reviewed,
        "compression_only_contact_model_reviewed": x.compression_only_contact_model_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing_reviews},
            notes=("A reviewed flange response operator, load composition, gasket stiffness support and unilateral contact assumption are required.",),
        )

    compliance = np.asarray(x.flange_relative_compliance_matrix_m_N, dtype=float)
    closure = np.asarray(x.free_closure_without_gasket_m, dtype=float)
    stiffness = np.asarray(x.gasket_compressive_stiffness_N_m, dtype=float)
    areas = np.asarray(x.gasket_contact_area_m2, dtype=float)
    if np.any(~np.isfinite(compliance)) or np.any(~np.isfinite(closure)):
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "nonfinite_flange_operator_or_closure"})
    try:
        symmetric_compliance = 0.5 * (compliance + compliance.T)
        eigenvalues = np.linalg.eigvalsh(symmetric_compliance)
        minimum_eigenvalue = float(eigenvalues[0])
        if minimum_eigenvalue < -x.compliance_psd_tolerance_m_N:
            return Calculation(
                status="out_of_scope",
                values=base | {
                    "minimum_flange_compliance_eigenvalue_m_N": minimum_eigenvalue,
                    "out_of_scope_reason": "flange_compliance_operator_not_positive_semidefinite",
                },
                notes=("The caller relative compliance matrix is not positive semidefinite within its declared numerical tolerance.",),
            )
        matrix = symmetric_compliance + np.diag(1.0 / stiffness)
        np.linalg.cholesky(matrix)
    except (np.linalg.LinAlgError, FloatingPointError, OverflowError, ValueError) as error:
        return Calculation(
            status="out_of_scope",
            values=base | {"out_of_scope_reason": "invalid_or_nonfinite_compliance_operator", "detail": str(error)},
        )

    active = set(np.flatnonzero(closure > x.gap_tolerance_m).tolist())
    force = np.zeros(len(closure), dtype=float)
    seen: set[tuple[int, ...]] = set()
    iterations = 0
    work_units = 0
    converged = False
    for iterations in range(1, x.active_set_maximum_iterations + 1):
        signature = tuple(sorted(active))
        if signature in seen:
            break
        seen.add(signature)
        force.fill(0.0)
        if active:
            indices = np.asarray(sorted(active), dtype=int)
            work_units += len(indices) ** 3
            if work_units > x.active_set_work_budget:
                return Calculation(
                    status="out_of_scope",
                    values=base | {
                        "active_set_iterations": iterations,
                        "active_set_work_units": work_units,
                        "out_of_scope_reason": "active_set_dense_solve_work_budget_exceeded",
                    },
                    notes=("The dense active-set solve exceeded the caller-declared cubic work budget; no partial contact field is returned.",),
                )
            try:
                force[indices] = np.linalg.solve(matrix[np.ix_(indices, indices)], closure[indices])
            except np.linalg.LinAlgError:
                break
            negative = indices[force[indices] < -x.force_tolerance_N]
            if len(negative):
                remove = int(negative[np.argmin(force[negative])])
                active.remove(remove)
                continue
            force[indices] = np.maximum(force[indices], 0.0)
        gap = matrix @ force - closure
        inactive = np.asarray(sorted(set(range(len(closure))) - active), dtype=int)
        penetrating = inactive[gap[inactive] < -x.gap_tolerance_m] if len(inactive) else np.asarray([], dtype=int)
        if len(penetrating):
            add = int(penetrating[np.argmin(gap[penetrating])])
            active.add(add)
            continue
        if active:
            active_indices = np.asarray(sorted(active), dtype=int)
            if float(np.max(np.abs(gap[active_indices]))) > x.gap_tolerance_m:
                break
        complementarity = float(np.max(np.abs(force * gap)))
        if complementarity > x.complementarity_tolerance_N_m:
            break
        converged = True
        break

    gap = matrix @ force - closure
    complementarity = float(np.max(np.abs(force * gap)))
    if not converged:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "active_set_iterations": iterations,
                "active_set_work_units": work_units,
                "active_contact_node_ids": [x.node_ids[i] for i in sorted(active)],
                "minimum_force_N": float(np.min(force)),
                "minimum_gap_m": float(np.min(gap)),
                "maximum_complementarity_residual_N_m": complementarity,
                "out_of_scope_reason": "unilateral_contact_active_set_not_converged",
            },
            notes=("No partial contact field is promoted when the active-set complementarity solve cycles or exhausts its caller budget.",),
        )

    rows = []
    for i, node_id in enumerate(x.node_ids):
        compression = force[i] / stiffness[i]
        pressure = force[i] / areas[i]
        rows.append({
            "node_id": node_id,
            "circumferential_coordinate_rad": x.circumferential_coordinate_rad[i],
            "contact_state": "closed" if force[i] > x.force_tolerance_N else "open",
            "contact_force_N": float(force[i]),
            "mean_contact_pressure_Pa": float(pressure),
            "linearized_gasket_compression_m": float(compression),
            "contact_gap_m": float(max(gap[i], 0.0)),
            "free_closure_without_gasket_m": float(closure[i]),
        })
    return Calculation(
        values=base | {
            "active_set_iterations": iterations,
            "active_set_work_units": work_units,
            "active_contact_node_ids": [x.node_ids[i] for i in sorted(active)],
            "minimum_flange_compliance_eigenvalue_m_N": minimum_eigenvalue,
            "maximum_complementarity_residual_N_m": complementarity,
            "response_field": rows,
            "contact_force_sum_N": float(np.sum(force)),
            "contact_area_sum_m2": float(np.sum(areas)),
            "contact_model": "caller_flange_compliance_plus_local_linear_gasket_springs",
        },
        notes=(
            "The nodal field is conditional on the exact caller flange compliance, load-composition and linearized gasket inputs; it is not an independent flange FE solution.",
            "Mean nodal pressure is force divided by caller contact area. It is not a local stress solution, leakage prediction, seal criterion, qualification result or acceptance decision.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "fabrication.flange_viscoelastic_contact_history",
            FlangeViscoelasticContactHistoryRequest,
            flange_viscoelastic_contact_history,
            {
                "time_history[].time_s": "s",
                "time_history[].contact_force_sum_N": "N",
                "time_history[].response_field[].circumferential_coordinate_rad": "rad",
                "time_history[].response_field[].contact_force_N": "N",
                "time_history[].response_field[].mean_contact_pressure_Pa": "Pa",
                "time_history[].response_field[].gasket_compression_m": "m",
                "time_history[].response_field[].gasket_stress_Pa": "Pa",
                "time_history[].response_field[].contact_gap_m": "m",
                "time_history[].response_field[].gasket_strain": "1",
                "time_history[].response_field[].branch_stress_Pa[]": "Pa",
                "minimum_flange_compliance_eigenvalue_m_N": "m/N",
                "contact_iteration_count": "1",
                "contact_work_units": "1",
                "node_count": "1",
                "time_knot_count": "1",
            },
            (
                "Caller-supplied linear generalized-Maxwell gasket branches evolve exactly over declared piecewise-linear compression segments and are coupled to a caller-supplied symmetric positive-semidefinite flange compliance operator, optionally supplied as a digest-bound operator at every declared time knot.",
                "Unilateral quasi-static contact is solved at declared time knots; the initial knot is an instantaneous load from the reviewed zero-compression branch state. No between-knot operator interpolation, transition time, FE response, leakage, peak stress or acceptance is inferred.",
            ),
            ("caller_spatial_linear_prony_flange_contact_history",),
            qualification="user_model",
        ),
        ModelSpec(
            "fabrication.flange_nonlinear_contact_field",
            FlangeNonlinearContactFieldRequest,
            flange_nonlinear_contact_field,
            {
                "response_field.circumferential_coordinate_rad": "rad",
                "response_field.contact_force_N": "N",
                "response_field.mean_contact_pressure_Pa": "Pa",
                "response_field.gasket_compression_m": "m",
                "response_field.contact_gap_m": "m",
                "response_field.free_closure_without_gasket_m": "m",
                "contact_force_sum_N": "N",
                "contact_area_sum_m2": "m2",
                "minimum_flange_compliance_eigenvalue_m_N": "m/N",
                "maximum_force_residual_N": "N",
                "maximum_active_closure_residual_m": "m",
                "nonlinear_iterations": "1",
                "line_search_steps": "1",
                "node_count": "1",
            },
            (
                "A caller-supplied symmetric positive-semidefinite flange operator is coupled to per-node reversible monotone piecewise-linear gasket force-compression curves.",
                "Compression-only contact is solved within the declared curve support; no curve extrapolation, FE flange generation, local stress, leakage or acceptance is inferred.",
            ),
            ("caller_spatial_nonlinear_flange_contact_compliance",),
            qualification="user_model",
        ),
        ModelSpec(
            "fabrication.flange_contact_field",
            FlangeContactFieldRequest,
            flange_contact_field,
            {
                "response_field.circumferential_coordinate_rad": "rad",
                "response_field.contact_force_N": "N",
                "response_field.mean_contact_pressure_Pa": "Pa",
                "response_field.linearized_gasket_compression_m": "m",
                "response_field.contact_gap_m": "m",
                "response_field.free_closure_without_gasket_m": "m",
                "contact_force_sum_N": "N",
                "contact_area_sum_m2": "m2",
                "minimum_flange_compliance_eigenvalue_m_N": "m/N",
                "maximum_complementarity_residual_N_m": "N m",
                "active_set_iterations": "1",
                "active_set_work_units": "1",
                "node_count": "1",
            },
            (
                "Caller-supplied symmetric positive-semidefinite relative flange compliance and per-node linear gasket springs define the spatial contact response.",
                "A deterministic active-set complementarity solve enforces nonnegative contact force and nonnegative gap; every load, coordinate and response operator requires explicit scope and computational-use review.",
                "No FE response, bolt/load distribution, geometry, nonlinear gasket law, local pressure stress, leakage, seal criterion or acceptance is inferred.",
            ),
            ("caller_spatial_flange_contact_compliance",),
            qualification="user_model",
        )
    ]
