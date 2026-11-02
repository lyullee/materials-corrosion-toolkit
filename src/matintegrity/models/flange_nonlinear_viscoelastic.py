"""Spatial unilateral contact with caller-calibrated nonlinear Maxwell gasket branches."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..gasket_relaxation import (
    NonlinearGasketViscoelasticMaterial,
    _advance_nonlinear_branch,
    _backbone_stress,
)
from ..registry import ModelSpec


class FlangeNonlinearViscoelasticContactHistory(Contract):
    schema_version: Literal["matintegrity.flange_nonlinear_viscoelastic_contact_history.v1"] = "matintegrity.flange_nonlinear_viscoelastic_contact_history.v1"
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    response_provider_id: str = Field(min_length=1)
    response_provider_revision: str = Field(min_length=1)
    response_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    material: NonlinearGasketViscoelasticMaterial
    node_ids: tuple[str, ...] = Field(min_length=2, max_length=64)
    times_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=10000)
    circumferential_coordinate_rad: tuple[float, ...] = Field(min_length=2, max_length=64)
    gasket_contact_area_m2: tuple[Positive, ...] = Field(min_length=2, max_length=64)
    gasket_thickness_m: tuple[Positive, ...] = Field(min_length=2, max_length=64)
    initial_branch_stress_by_node_Pa: tuple[tuple[float, ...], ...] | None = None
    free_closure_without_gasket_m: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=10000)
    flange_relative_compliance_matrix_m_N: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=64)
    flange_relative_compliance_history_m_N: tuple[tuple[tuple[float, ...], ...], ...] | None = None
    compliance_history_interpolation_reviewed: bool = False
    maximum_compressive_strain: Positive
    matrix_symmetry_tolerance_m_N: Positive = Field(le=1e-6)
    compliance_psd_tolerance_m_N: Positive = Field(le=1e-6)
    maximum_contact_iterations: int = Field(default=10000, ge=1, le=100000)
    maximum_newton_iterations_per_active_set: int = Field(default=100, ge=1, le=1000)
    maximum_contact_work_units: int = Field(default=50_000_000, ge=1, le=1_000_000_000)
    maximum_contact_transition_step_s: Positive | None = None
    additional_contact_sampling_times_s: tuple[Nonnegative, ...] = Field(default=(), max_length=9998)
    contact_transition_time_sampling_reviewed: bool = False
    contact_transition_time_tolerance_s: Positive | None = None
    single_contact_transition_per_refined_interval_reviewed: bool = False
    maximum_transition_refinement_solves: int = Field(default=100, ge=1, le=10000)
    maximum_transition_refinement_work_units: int = Field(default=50_000_000, ge=1, le=1_000_000_000)
    gap_tolerance_m: Positive = Field(default=1e-12)
    force_tolerance_N: Positive = Field(default=1e-5)
    flange_operator_basis_reviewed: bool
    response_scope_and_coordinates_reviewed: bool
    bolt_pressure_and_boundary_load_composition_reviewed: bool
    material_curve_condition_and_support_reviewed: bool
    initial_branch_states_reviewed: bool
    zero_compression_branch_state_reviewed: bool
    nonlinear_history_integration_reviewed: bool
    unilateral_contact_model_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_geometry_history_and_material(self):
        n = len(self.node_ids)
        if len(set(self.node_ids)) != n:
            raise ValueError("contact node IDs must be unique")
        if any(len(values) != n for values in (
            self.circumferential_coordinate_rad, self.gasket_contact_area_m2,
            self.gasket_thickness_m,
            self.flange_relative_compliance_matrix_m_N,
        )):
            raise ValueError("all spatial arrays must align with node_ids")
        if len(self.times_s) != len(self.free_closure_without_gasket_m):
            raise ValueError("free-closure history rows must align with time knots")
        if any(right <= left for left, right in zip(self.times_s[:-1], self.times_s[1:], strict=True)):
            raise ValueError("time knots must strictly increase")
        if self.maximum_contact_transition_step_s is not None:
            if not self.contact_transition_time_sampling_reviewed:
                raise ValueError("refined contact-time sampling requires an explicit interpolation review")
            required_steps = 0
            for left, right in zip(self.times_s[:-1], self.times_s[1:], strict=True):
                ratio = (right - left) / self.maximum_contact_transition_step_s
                if not math.isfinite(ratio) or ratio > 9999:
                    raise ValueError("refined contact-time grid exceeds the 10000-knot limit")
                required_steps += max(1, math.ceil(ratio))
                if required_steps + 1 > 10000:
                    raise ValueError("refined contact-time grid exceeds the 10000-knot limit")
        if self.additional_contact_sampling_times_s:
            if self.maximum_contact_transition_step_s is None:
                raise ValueError("additional contact sampling requires reviewed transition-time sampling")
            extra = self.additional_contact_sampling_times_s
            if any(right <= left for left, right in zip(extra[:-1], extra[1:])):
                raise ValueError("additional contact times must strictly increase")
            if any(not self.times_s[0] < time < self.times_s[-1] for time in extra):
                raise ValueError("additional contact times must lie inside the source history")
        if self.contact_transition_time_tolerance_s is not None:
            if self.maximum_contact_transition_step_s is None:
                raise ValueError("transition-time bisection requires a maximum sampled time step")
            if not self.single_contact_transition_per_refined_interval_reviewed:
                raise ValueError("transition-time bisection requires review that each refined interval contains at most one transition per node")
        if any(len(row) != n for row in self.free_closure_without_gasket_m):
            raise ValueError("each free-closure row must align with node IDs")
        if any(not math.isfinite(v) for v in (*self.circumferential_coordinate_rad, *(v for row in self.free_closure_without_gasket_m for v in row))):
            raise ValueError("coordinates and free-closure histories must be finite")
        branch_count = len(self.material.branches)
        if self.initial_branch_stress_by_node_Pa is not None:
            if len(self.initial_branch_stress_by_node_Pa) != n or any(
                len(row) != branch_count or any(not math.isfinite(v) for v in row)
                for row in self.initial_branch_stress_by_node_Pa
            ):
                raise ValueError("each node's initial branch stress must align with the material branch list")
        if self.maximum_compressive_strain > self.material.equilibrium_stress_strain_backbone[-1].compressive_strain:
            raise ValueError("requested strain exceeds the equilibrium backbone support")
        if any(self.maximum_compressive_strain > branch.stress_strain_backbone[-1].compressive_strain for branch in self.material.branches):
            raise ValueError("requested strain exceeds a Maxwell branch backbone support")
        if len(self.flange_relative_compliance_matrix_m_N) != n or any(len(row) != n for row in self.flange_relative_compliance_matrix_m_N):
            raise ValueError("flange compliance matrix must be square and aligned")
        for i in range(n):
            for j in range(n):
                left = self.flange_relative_compliance_matrix_m_N[i][j]
                right = self.flange_relative_compliance_matrix_m_N[j][i]
                if not math.isfinite(left) or abs(left - right) > self.matrix_symmetry_tolerance_m_N:
                    raise ValueError("caller flange compliance must be finite and symmetric")
        if self.flange_relative_compliance_history_m_N is not None:
            if not self.compliance_history_interpolation_reviewed:
                raise ValueError("time-varying flange compliance requires an explicit history/interpolation review")
            if len(self.flange_relative_compliance_history_m_N) != len(self.times_s):
                raise ValueError("flange compliance history must align with every time knot")
            for matrix in self.flange_relative_compliance_history_m_N:
                if len(matrix) != n or any(len(row) != n for row in matrix):
                    raise ValueError("each compliance-history matrix must be square and node-aligned")
                for i in range(n):
                    for j in range(n):
                        left, right = matrix[i][j], matrix[j][i]
                        if not math.isfinite(left) or abs(left - right) > self.matrix_symmetry_tolerance_m_N:
                            raise ValueError("every flange compliance history matrix must be finite and symmetric")
        elif self.compliance_history_interpolation_reviewed:
            raise ValueError("compliance-history review cannot be declared without a compliance history")
        return self


def flange_nonlinear_viscoelastic_contact_history(x: FlangeNonlinearViscoelasticContactHistory) -> Calculation:
    """Solve nodal contact at explicit time knots with nonlinear Maxwell history."""
    if x.maximum_contact_transition_step_s is not None:
        refined_times = [float(x.times_s[0])]
        for start, end in zip(x.times_s[:-1], x.times_s[1:], strict=True):
            ratio = (end - start) / x.maximum_contact_transition_step_s
            if not math.isfinite(ratio) or ratio > 9999:
                raise ValueError("refined contact-time grid exceeds the 10000-knot limit")
            substeps = max(1, math.ceil(ratio))
            refined_times.extend(
                float(start + (end - start) * index / substeps)
                for index in range(1, substeps)
            )
            refined_times.append(float(end))
        refined_times = sorted(set(refined_times).union(x.additional_contact_sampling_times_s))
        if len(refined_times) > 10000:
            raise ValueError("combined contact-time grid exceeds the 10000-knot limit")
        source_closure = np.asarray(x.free_closure_without_gasket_m, dtype=float)
        interpolated_closure = np.column_stack([
            np.interp(refined_times, x.times_s, source_closure[:, node])
            for node in range(len(x.node_ids))
        ])
        refined_closure = tuple(
            tuple(float(value) for value in row) for row in interpolated_closure
        )
        refined_compliance = None
        if x.flange_relative_compliance_history_m_N is not None:
            source_compliance = np.asarray(x.flange_relative_compliance_history_m_N, dtype=float)
            interpolated_compliance = np.empty((len(refined_times), len(x.node_ids), len(x.node_ids)))
            for i in range(len(x.node_ids)):
                for j in range(len(x.node_ids)):
                    interpolated_compliance[:, i, j] = np.interp(
                        refined_times, x.times_s, source_compliance[:, i, j]
                    )
            refined_compliance = tuple(
                tuple(tuple(float(value) for value in row) for row in matrix)
                for matrix in interpolated_compliance
            )
        original_digest = canonical_digest(x.model_dump(mode="json"))
        refined_request = FlangeNonlinearViscoelasticContactHistory.model_validate(
            x.model_dump(mode="python") | {
                "times_s": tuple(refined_times),
                "free_closure_without_gasket_m": refined_closure,
                "flange_relative_compliance_history_m_N": refined_compliance,
                "maximum_contact_transition_step_s": None,
                "additional_contact_sampling_times_s": (),
                "contact_transition_time_tolerance_s": None,
            }
        )
        refined = flange_nonlinear_viscoelastic_contact_history(refined_request)
        values = dict(refined.values)
        values["additional_contact_sampling_times_s"] = list(x.additional_contact_sampling_times_s)
        values["planned_evaluation_time_knots_s"] = refined_times
        values["planned_evaluation_time_knots_sha256"] = canonical_digest(refined_times)
        values["source_time_knots_preserved_exactly"] = all(time in refined_times for time in x.times_s)
        history = values.get("time_history", values.get("computed_prefix", []))
        transition_history = history
        transitions = []
        for left, right in zip(history[:-1], history[1:], strict=True):
            left_states = {row["node_id"]: row["contact_state"] for row in left["response_field"]}
            right_states = {row["node_id"]: row["contact_state"] for row in right["response_field"]}
            left_rows = {row["node_id"]: row for row in left["response_field"]}
            right_rows = {row["node_id"]: row for row in right["response_field"]}
            for node_id in x.node_ids:
                if left_states.get(node_id) != right_states.get(node_id):
                    transitions.append({
                        "node_id": node_id,
                        "from_state": left_states[node_id],
                        "to_state": right_states[node_id],
                        "lower_time_s": left["time_s"],
                        "upper_time_s": right["time_s"],
                        "bracket_width_s": right["time_s"] - left["time_s"],
                        "lower_flange_compliance_operator_sha256": left.get("flange_compliance_operator_sha256"),
                        "upper_flange_compliance_operator_sha256": right.get("flange_compliance_operator_sha256"),
                        "sampled_bracket_endpoint_results": [
                            {
                                "time_s": endpoint["time_s"],
                                "contact_state": row["contact_state"],
                                "contact_force_N": row["contact_force_N"],
                                "mean_contact_pressure_Pa": row["mean_contact_pressure_Pa"],
                                "gasket_compression_m": row["gasket_compression_m"],
                                "gasket_strain": row["gasket_strain"],
                                "gasket_constitutive_stress_Pa": row["gasket_constitutive_stress_Pa"],
                                "contact_gap_m": row["contact_gap_m"],
                                "flange_compliance_operator_sha256": endpoint.get("flange_compliance_operator_sha256"),
                            }
                            for endpoint, row in ((left, left_rows[node_id]), (right, right_rows[node_id]))
                        ],
                        "refinement_observations": [],
                    })
        refinement_solves = 0
        refinement_work_units = 0
        refinement_midpoints = []
        refinement_request_digests = []
        if x.contact_transition_time_tolerance_s is not None and transitions and refined.status == "computed":
            refined_input = refined_request.model_dump(mode="python")
            base_times = list(refined_request.times_s)
            base_closure = np.asarray(refined_request.free_closure_without_gasket_m, dtype=float)
            closure_at = lambda time_s, node: float(np.interp(time_s, base_times, base_closure[:, node]))
            base_compliance = refined_request.flange_relative_compliance_history_m_N
            compliance_array = None if base_compliance is None else np.asarray(base_compliance, dtype=float)
            node_lookup = {node_id: index for index, node_id in enumerate(x.node_ids)}
            for transition in transitions:
                solves_before_transition = refinement_solves
                low = float(transition["lower_time_s"])
                high = float(transition["upper_time_s"])
                low_state = transition["from_state"]
                node_index = node_lookup[transition["node_id"]]
                while high - low > x.contact_transition_time_tolerance_s:
                    if refinement_solves >= x.maximum_transition_refinement_solves:
                        return Calculation(
                            status="out_of_scope",
                            values=values | {
                                "input_digest": original_digest,
                                "transition_refinement_complete": False,
                                "sampled_contact_transition_brackets": transitions,
                                "transition_refinement_solves": refinement_solves,
                                "transition_refinement_work_units": refinement_work_units,
                                "transition_refinement_midpoint_times_s": refinement_midpoints,
                                "transition_refinement_request_sha256": refinement_request_digests,
                                "out_of_scope_reason": "contact_transition_refinement_solve_budget_exceeded",
                            },
                            notes=refined.notes + ("The sampled contact transition was not promoted to a tolerance-bounded bracket because the refinement-solve budget was exhausted.",),
                        )
                    middle = low + 0.5 * (high - low)
                    if not low < middle < high:
                        return Calculation(
                            status="out_of_scope",
                            values=values | {
                                "input_digest": original_digest,
                                "transition_refinement_complete": False,
                                "sampled_contact_transition_brackets": transitions,
                                "transition_refinement_solves": refinement_solves,
                                "transition_refinement_work_units": refinement_work_units,
                                "transition_refinement_midpoint_times_s": refinement_midpoints,
                                "transition_refinement_request_sha256": refinement_request_digests,
                                "out_of_scope_reason": "contact_transition_midpoint_below_time_resolution",
                            },
                            notes=refined.notes + ("No representable floating-point time lies strictly inside the remaining contact transition bracket.",),
                        )
                    if len(base_times) >= 10000:
                        return Calculation(
                            status="out_of_scope",
                            values=values | {
                                "input_digest": original_digest,
                                "transition_refinement_complete": False,
                                "sampled_contact_transition_brackets": transitions,
                                "transition_refinement_solves": refinement_solves,
                                "transition_refinement_work_units": refinement_work_units,
                                "transition_refinement_midpoint_times_s": refinement_midpoints,
                                "transition_refinement_request_sha256": refinement_request_digests,
                                "out_of_scope_reason": "contact_transition_refinement_knot_budget_exceeded",
                            },
                            notes=refined.notes + ("The refined time path is at its 10,000-knot limit and cannot accept another bisection point.",),
                        )
                    insertion = int(np.searchsorted(base_times, middle))
                    trial_times = base_times[:insertion] + [middle] + base_times[insertion:]
                    midpoint_closure = tuple(closure_at(middle, node) for node in range(len(x.node_ids)))
                    trial_closure = (
                        refined_request.free_closure_without_gasket_m[:insertion]
                        + (midpoint_closure,)
                        + refined_request.free_closure_without_gasket_m[insertion:]
                    )
                    trial_compliance = None
                    if base_compliance is not None:
                        midpoint_compliance = tuple(
                            tuple(float(np.interp(middle, base_times, compliance_array[:, i, j]))
                                  for j in range(len(x.node_ids)))
                            for i in range(len(x.node_ids))
                        )
                        trial_compliance = base_compliance[:insertion] + (midpoint_compliance,) + base_compliance[insertion:]
                    trial_request = FlangeNonlinearViscoelasticContactHistory.model_validate(
                        refined_input | {
                            "times_s": tuple(trial_times),
                            "free_closure_without_gasket_m": trial_closure,
                            "flange_relative_compliance_history_m_N": trial_compliance,
                            "maximum_contact_transition_step_s": None,
                            "contact_transition_time_tolerance_s": None,
                        }
                    )
                    trial = flange_nonlinear_viscoelastic_contact_history(trial_request)
                    refinement_solves += 1
                    refinement_midpoints.append(middle)
                    refinement_request_digests.append(canonical_digest(trial_request.model_dump(mode="json")))
                    trial_work = trial.values.get("contact_work_units", 0)
                    if isinstance(trial_work, bool) or not isinstance(trial_work, int) or trial_work < 0:
                        return Calculation(
                            status="out_of_scope",
                            values=values | {
                                "input_digest": original_digest,
                                "transition_refinement_complete": False,
                                "sampled_contact_transition_brackets": transitions,
                                "transition_refinement_solves": refinement_solves,
                                "transition_refinement_work_units": refinement_work_units,
                                "transition_refinement_midpoint_times_s": refinement_midpoints,
                                "transition_refinement_request_sha256": refinement_request_digests,
                                "out_of_scope_reason": "contact_transition_refinement_replay_failed",
                            },
                            notes=refined.notes + ("A replayed constitutive/contact path failed during transition-time refinement; the event bracket is not reported as refined.",),
                        )
                    refinement_work_units += trial_work
                    if trial.status != "computed":
                        return Calculation(
                            status="out_of_scope",
                            values=values | {
                                "input_digest": original_digest,
                                "transition_refinement_complete": False,
                                "sampled_contact_transition_brackets": transitions,
                                "transition_refinement_solves": refinement_solves,
                                "transition_refinement_work_units": refinement_work_units,
                                "transition_refinement_midpoint_times_s": refinement_midpoints,
                                "transition_refinement_request_sha256": refinement_request_digests,
                                "out_of_scope_reason": "contact_transition_refinement_replay_failed",
                            },
                            notes=refined.notes + ("A replayed constitutive/contact path failed during transition-time refinement; the event bracket is not reported as refined.",),
                        )
                    transition_history = trial.values.get("time_history", trial.values.get("computed_prefix", []))
                    if refinement_work_units > x.maximum_transition_refinement_work_units:
                        return Calculation(
                            status="out_of_scope",
                            values=values | {
                                "input_digest": original_digest,
                                "transition_refinement_complete": False,
                                "sampled_contact_transition_brackets": transitions,
                                "transition_refinement_solves": refinement_solves,
                                "transition_refinement_work_units": refinement_work_units,
                                "transition_refinement_midpoint_times_s": refinement_midpoints,
                                "transition_refinement_request_sha256": refinement_request_digests,
                                "out_of_scope_reason": "contact_transition_refinement_work_budget_exceeded",
                            },
                            notes=refined.notes + ("The sampled contact transition was not promoted to a tolerance-bounded bracket because the aggregate replay work-unit budget was exhausted.",),
                        )
                    midpoint_row = next(
                        (row for row in trial.values.get("time_history", []) if row["time_s"] == middle),
                        None,
                    )
                    if midpoint_row is None:
                        return Calculation(
                            status="out_of_scope",
                            values=values | {
                                "input_digest": original_digest,
                                "transition_refinement_complete": False,
                                "sampled_contact_transition_brackets": transitions,
                                "transition_refinement_solves": refinement_solves,
                                "transition_refinement_work_units": refinement_work_units,
                                "transition_refinement_midpoint_times_s": refinement_midpoints,
                                "transition_refinement_request_sha256": refinement_request_digests,
                                "out_of_scope_reason": "contact_transition_midpoint_state_missing",
                            },
                            notes=refined.notes + ("The replay did not return a contact state at the requested bisection midpoint.",),
                        )
                    midpoint_response = midpoint_row["response_field"][node_index]
                    transition["refinement_observations"].append({
                        "time_s": middle,
                        "contact_state": midpoint_response["contact_state"],
                        "contact_force_N": midpoint_response["contact_force_N"],
                        "mean_contact_pressure_Pa": midpoint_response["mean_contact_pressure_Pa"],
                        "gasket_compression_m": midpoint_response["gasket_compression_m"],
                        "gasket_strain": midpoint_response["gasket_strain"],
                        "gasket_constitutive_stress_Pa": midpoint_response["gasket_constitutive_stress_Pa"],
                        "contact_gap_m": midpoint_response["contact_gap_m"],
                        "flange_compliance_operator_sha256": midpoint_row.get("flange_compliance_operator_sha256"),
                        "replay_request_sha256": refinement_request_digests[-1],
                    })
                    midpoint_state = midpoint_response["contact_state"]
                    if midpoint_state == low_state:
                        low = middle
                    else:
                        high = middle
                transition["lower_time_s"] = low
                transition["upper_time_s"] = high
                transition["bracket_width_s"] = high - low
                bracket_observations = {
                    row["time_s"]: row
                    for row in (
                        *transition["sampled_bracket_endpoint_results"],
                        *transition["refinement_observations"],
                    )
                }
                if low in bracket_observations and high in bracket_observations:
                    transition["sampled_bracket_endpoint_results"] = [
                        bracket_observations[low], bracket_observations[high]
                    ]
                    transition["lower_flange_compliance_operator_sha256"] = bracket_observations[low].get(
                        "flange_compliance_operator_sha256"
                    )
                    transition["upper_flange_compliance_operator_sha256"] = bracket_observations[high].get(
                        "flange_compliance_operator_sha256"
                    )
                endpoint_rows = {row["time_s"]: row for row in transition_history}
                if low in endpoint_rows and high in endpoint_rows:
                    transition["lower_flange_compliance_operator_sha256"] = endpoint_rows[low].get(
                        "flange_compliance_operator_sha256"
                    )
                    transition["upper_flange_compliance_operator_sha256"] = endpoint_rows[high].get(
                        "flange_compliance_operator_sha256"
                    )
                transition["refinement_method"] = (
                    "replayed_path_state_bisection"
                    if refinement_solves > solves_before_transition
                    else "sampled_bracket_within_requested_tolerance"
                )
                transition["requested_time_tolerance_s"] = x.contact_transition_time_tolerance_s
        values.update({
            "input_digest": original_digest,
            "transition_refinement_complete": refined.status == "computed",
            "expanded_evaluation_input_digest": values.get("input_digest"),
            "requested_time_knots_s": list(x.times_s),
            "evaluation_time_knots_s": [row["time_s"] for row in history],
            "contact_transition_time_sampling_reviewed": x.contact_transition_time_sampling_reviewed,
            "maximum_contact_transition_step_s": x.maximum_contact_transition_step_s,
            "contact_transition_time_tolerance_s": x.contact_transition_time_tolerance_s,
            "transition_refinement_solves": refinement_solves,
            "transition_refinement_work_units": refinement_work_units,
            "transition_refinement_midpoint_times_s": refinement_midpoints,
            "transition_refinement_request_sha256": refinement_request_digests,
            "sampled_contact_transition_brackets": transitions,
            "maximum_observed_transition_bracket_width_s": max(
                (row["bracket_width_s"] for row in transitions), default=0.0
            ),
        })
        return Calculation(
            status=refined.status,
            values=values,
            notes=refined.notes + (
                "Contact state is sampled at caller-reviewed interpolated knots; optional replayed-path bisection narrows observed transition brackets to the declared tolerance but does not establish an exact event time or detect unobserved transitions.",
            ),
        )

    material = x.material
    n = len(x.node_ids)
    digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id, "joint_id": x.joint_id,
        "physical_scope_id": x.physical_scope_id,
        "response_provider_id": x.response_provider_id,
        "response_provider_revision": x.response_provider_revision,
        "response_configuration_digest": x.response_configuration_digest,
        "response_result_digest": x.response_result_digest,
        "material_condition_id": material.material_condition_id,
        "material_physical_specimen_id": material.physical_specimen_id,
        "material_source_group_id": material.source_group_id,
        "material_provider_id": material.provider_id,
        "material_provider_revision": material.provider_revision,
        "material_temperature_K": material.temperature_K,
        "material_source_sha256": material.source_sha256,
        "material_condition_sha256": material.condition_sha256,
        "branch_ids": [branch.branch_id for branch in material.branches],
        "time_varying_flange_compliance": x.flange_relative_compliance_history_m_N is not None,
        "compliance_history_interpolation_reviewed": x.compliance_history_interpolation_reviewed,
        "compliance_operators_symmetrized_within_declared_tolerance": True,
        "input_digest": digest, "node_count": n, "time_knot_count": len(x.times_s),
    }
    reviews = {
        "flange_operator_basis_reviewed": x.flange_operator_basis_reviewed,
        "response_scope_and_coordinates_reviewed": x.response_scope_and_coordinates_reviewed,
        "bolt_pressure_and_boundary_load_composition_reviewed": x.bolt_pressure_and_boundary_load_composition_reviewed,
        "material_curve_condition_and_support_reviewed": x.material_curve_condition_and_support_reviewed,
        "initial_branch_states_reviewed": x.initial_branch_states_reviewed,
        "zero_compression_branch_state_reviewed": x.zero_compression_branch_state_reviewed,
        "nonlinear_history_integration_reviewed": x.nonlinear_history_integration_reviewed,
        "unilateral_contact_model_reviewed": x.unilateral_contact_model_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
        "material_nonlinear_branch_calibration_reviewed": material.nonlinear_branch_calibration_reviewed,
        "material_initial_branch_state_reviewed": material.initial_branch_state_reviewed,
        "material_computational_use_authorized": material.computational_use_authorized,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})

    C_history = (
        np.asarray(x.flange_relative_compliance_history_m_N, dtype=float)
        if x.flange_relative_compliance_history_m_N is not None
        else None
    )
    if C_history is not None:
        C_history = 0.5 * (C_history + np.swapaxes(C_history, 1, 2))
    C = (
        C_history[0]
        if C_history is not None
        else np.asarray(x.flange_relative_compliance_matrix_m_N, dtype=float)
    )
    if C_history is None:
        C = 0.5 * (C + C.T)
    try:
        eigmin = float(np.linalg.eigvalsh(0.5 * (C + C.T))[0])
    except (np.linalg.LinAlgError, ValueError, FloatingPointError) as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "invalid_flange_compliance_operator", "detail": str(error)})
    if eigmin < -x.compliance_psd_tolerance_m_N:
        return Calculation(status="out_of_scope", values=base | {"minimum_flange_compliance_eigenvalue_m_N": eigmin, "out_of_scope_reason": "flange_compliance_operator_not_positive_semidefinite"})

    branches = material.branches
    initial_states = x.initial_branch_stress_by_node_Pa or tuple(material.initial_branch_stress_Pa for _ in range(n))
    branch_state = [list(initial_states[i]) for i in range(n)]
    previous_strain = [0.0] * n
    history = []
    work = 0

    def local_state(node: int, strain: float, knot: int):
        nonlocal work
        work += 1
        if work > x.maximum_contact_work_units:
            raise ArithmeticError("nonlinear_spatial_contact_work_budget_exceeded")
        if strain < 0 or strain > x.maximum_compressive_strain:
            raise ValueError("strain is outside the caller-declared nonlinear gasket support")
        if knot == 0:
            states = [
                branch_state[node][j] + _backbone_stress(branch.stress_strain_backbone, strain)
                for j, branch in enumerate(branches)
            ]
        else:
            dt = x.times_s[knot] - x.times_s[knot - 1]
            states = [
                _advance_nonlinear_branch(branch, branch_state[node][j], previous_strain[node], strain, dt)
                for j, branch in enumerate(branches)
            ]
        stress = _backbone_stress(material.equilibrium_stress_strain_backbone, strain) + math.fsum(states)
        if not math.isfinite(stress) or any(not math.isfinite(state) for state in states):
            raise ValueError("nonlinear gasket stress or branch state is nonfinite")
        return stress, states

    for knot, time_s in enumerate(x.times_s):
        knot_eigmin = eigmin
        if C_history is not None:
            C = C_history[knot]
            try:
                knot_eigmin = float(np.linalg.eigvalsh(0.5 * (C + C.T))[0])
            except (np.linalg.LinAlgError, ValueError, FloatingPointError) as error:
                return Calculation(status="out_of_scope", values=base | {"computed_prefix": history, "first_unsupported_time_s": time_s, "out_of_scope_reason": "invalid_flange_compliance_history_operator", "detail": str(error)})
            if knot_eigmin < -x.compliance_psd_tolerance_m_N:
                return Calculation(status="out_of_scope", values=base | {"computed_prefix": history, "first_unsupported_time_s": time_s, "minimum_flange_compliance_eigenvalue_m_N": knot_eigmin, "out_of_scope_reason": "flange_compliance_history_operator_not_positive_semidefinite"})
            eigmin = min(eigmin, knot_eigmin)
        compliance_operator_digest = canonical_digest(C.tolist())
        closure = np.asarray(x.free_closure_without_gasket_m[knot], dtype=float)
        active = set(np.flatnonzero(closure > x.gap_tolerance_m).tolist())
        strain = np.zeros(n, dtype=float)
        force = np.zeros(n, dtype=float)
        converged = False
        active_iteration = 0
        total_newton = 0
        reason = "nonlinear_spatial_contact_not_converged"

        def set_positive_seed(node: int) -> bool:
            # Find a positive-traction starting point within the declared support.
            for fraction in np.linspace(0.0, 1.0, 65)[1:]:
                candidate = x.maximum_compressive_strain * float(fraction)
                stress_value, _ = local_state(node, candidate, knot)
                if stress_value > 0:
                    strain[node] = candidate
                    return True
            return False

        try:
            for active_iteration in range(1, x.maximum_contact_iterations + 1):
                for i in range(n):
                    force[i] = 0.0
                if active:
                    for node in sorted(active):
                        if strain[node] <= 0 and not set_positive_seed(node):
                            reason = "no_positive_gasket_traction_inside_declared_strain_support"
                            raise ArithmeticError(reason)
                    newton_converged = False
                    removed_active = False
                    for _ in range(x.maximum_newton_iterations_per_active_set):
                        total_newton += 1
                        ids = np.asarray(sorted(active), dtype=int)
                        stresses_and_states = {i: local_state(i, float(strain[i]), knot) for i in ids}
                        for i in ids:
                            force[i] = x.gasket_contact_area_m2[i] * stresses_and_states[i][0]
                        if np.any(force[ids] <= 0):
                            negative_node = int(ids[int(np.argmin(force[ids]))])
                            active.remove(negative_node)
                            strain[negative_node] = 0.0
                            removed_active = True
                            break
                        residual = (C @ force + np.asarray(x.gasket_thickness_m) * strain - closure)[ids]
                        norm = float(np.linalg.norm(residual, ord=np.inf))
                        if norm <= x.gap_tolerance_m:
                            newton_converged = True
                            break
                        tangent = np.zeros(len(ids), dtype=float)
                        for position, node_raw in enumerate(ids):
                            node = int(node_raw)
                            h = max(1e-8, 1e-5 * max(float(strain[node]), 1e-3))
                            if strain[node] + h <= x.maximum_compressive_strain:
                                perturbed, _ = local_state(node, float(strain[node] + h), knot)
                                tangent[position] = x.gasket_contact_area_m2[node] * (perturbed - stresses_and_states[node][0]) / h
                            elif strain[node] - h >= 0:
                                perturbed, _ = local_state(node, float(strain[node] - h), knot)
                                tangent[position] = x.gasket_contact_area_m2[node] * (stresses_and_states[node][0] - perturbed) / h
                        if np.any(~np.isfinite(tangent)) or np.any(tangent <= 0):
                            reason = "nonpositive_or_nonfinite_local_nonlinear_gasket_tangent"
                            break
                        jacobian = C[np.ix_(ids, ids)] @ np.diag(tangent) + np.diag(np.asarray(x.gasket_thickness_m)[ids])
                        delta = np.linalg.solve(jacobian, -residual)
                        accepted = False
                        alpha = 1.0
                        for _line in range(24):
                            candidate_strain = strain[ids] + alpha * delta
                            if np.any(candidate_strain < 0) or np.any(candidate_strain > x.maximum_compressive_strain):
                                alpha *= 0.5
                                continue
                            candidate_force = np.zeros(n, dtype=float)
                            for position, node_raw in enumerate(ids):
                                node = int(node_raw)
                                stress_value, _ = local_state(node, float(candidate_strain[position]), knot)
                                candidate_force[node] = x.gasket_contact_area_m2[node] * stress_value
                            if np.any(candidate_force[ids] <= 0):
                                alpha *= 0.5
                                continue
                            # Set only active-node compression before evaluating closure residual.
                            active_strain = np.zeros(n, dtype=float)
                            active_strain[ids] = candidate_strain
                            candidate_residual = (C @ candidate_force + np.asarray(x.gasket_thickness_m) * active_strain - closure)[ids]
                            if float(np.linalg.norm(candidate_residual, ord=np.inf)) < norm:
                                strain[ids] = candidate_strain
                                force[:] = candidate_force
                                accepted = True
                                break
                            alpha *= 0.5
                        if not accepted:
                            reason = "nonlinear_spatial_contact_line_search_failed"
                            break
                    if removed_active:
                        continue
                    if reason != "nonlinear_spatial_contact_not_converged" and not newton_converged:
                        break
                    if not newton_converged:
                        reason = "nonlinear_spatial_contact_newton_iteration_limit"
                        break
                gap = C @ force + np.asarray(x.gasket_thickness_m) * strain - closure
                violating = sorted((node for node in range(n) if node not in active and gap[node] < -x.gap_tolerance_m), key=lambda node: gap[node])
                if violating:
                    node = violating[0]
                    if not set_positive_seed(node):
                        reason = "no_positive_gasket_traction_inside_declared_strain_support"
                        break
                    active.add(node)
                    continue
                if np.any(force < -x.force_tolerance_N) or np.min(gap) < -x.gap_tolerance_m:
                    reason = "nonlinear_spatial_contact_complementarity_failed"
                    break
                converged = True
                break
        except (ArithmeticError, FloatingPointError, OverflowError, ValueError, np.linalg.LinAlgError) as error:
            reason = str(error) or reason

        if not converged:
            return Calculation(status="out_of_scope", values=base | {
                "computed_prefix": history,
                "first_unsupported_time_s": time_s,
                "contact_active_set_iterations": active_iteration if "active_iteration" in locals() else 0,
                "newton_iterations": total_newton,
                "contact_work_units": work,
                "out_of_scope_reason": reason,
            }, notes=("No partial field is emitted for a failed knot. Constitutive, tangent and unilateral-contact support must all be satisfied.",))

        node_rows = []
        next_branch_state = []
        max_force_residual = 0.0
        for node in range(n):
            stress, states = local_state(node, float(strain[node]), knot)
            if node in active:
                max_force_residual = max(max_force_residual, abs(force[node] - x.gasket_contact_area_m2[node] * stress))
            next_branch_state.append(states)
            node_rows.append({
                "node_id": x.node_ids[node],
                "circumferential_coordinate_rad": x.circumferential_coordinate_rad[node],
                "contact_state": "closed" if force[node] > 0 else "open",
                "contact_force_N": float(force[node]),
                "mean_contact_pressure_Pa": float(force[node] / x.gasket_contact_area_m2[node]),
                "gasket_compression_m": float(strain[node] * x.gasket_thickness_m[node]),
                "gasket_strain": float(strain[node]),
                "gasket_constitutive_stress_Pa": stress,
                "contact_gap_m": float(max(gap[node], 0.0)),
                "branch_stress_Pa": states,
            })
        if max_force_residual > x.force_tolerance_N:
            return Calculation(status="out_of_scope", values=base | {
                "computed_prefix": history, "first_unsupported_time_s": time_s,
                "maximum_active_force_residual_N": max_force_residual,
                "out_of_scope_reason": "active_contact_force_residual_exceeded_tolerance",
            })
        history.append({
            "time_s": time_s,
            "flange_compliance_operator_sha256": compliance_operator_digest,
            "minimum_flange_compliance_eigenvalue_m_N": knot_eigmin,
            "contact_active_set_iterations": active_iteration,
            "newton_iterations": total_newton,
            "maximum_active_force_residual_N": max_force_residual,
            "contact_force_sum_N": float(np.sum(force)),
            "response_field": node_rows,
        })
        previous_strain = strain.tolist()
        branch_state = next_branch_state

    return Calculation(values=base | {
        "minimum_flange_compliance_eigenvalue_m_N": eigmin,
        "contact_work_units": work,
        "time_history": history,
        "flange_compliance_history_used": C_history is not None,
        "compliance_history_interpolation_reviewed": x.compliance_history_interpolation_reviewed,
        "compliance_operators_symmetrized_within_declared_tolerance": True,
        "basis": "caller_nonlinear_generalized_maxwell_gasket_and_time_varying_flange_compliance_with_knotwise_unilateral_contact" if C_history is not None else "caller_nonlinear_generalized_maxwell_gasket_and_flange_compliance_with_knotwise_unilateral_contact",
    }, notes=(
        "Each branch uses its caller monotone backbone with exact exponential updates split at backbone knots over linearly interpolated strain intervals.",
        "Contact is solved only at supplied time knots. Optional replayed-path bisection bounds observed transitions under an explicit single-transition-per-refined-interval review; it does not produce exact event timing. This is not a generated flange FE response; local peak stress, leakage, seal performance and acceptance are not inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.flange_nonlinear_viscoelastic_contact_history",
        FlangeNonlinearViscoelasticContactHistory,
        flange_nonlinear_viscoelastic_contact_history,
        {
            "time_history[].time_s": "s",
            "requested_time_knots_s[]": "s",
            "evaluation_time_knots_s[]": "s",
            "maximum_contact_transition_step_s": "s",
            "contact_transition_time_tolerance_s": "s",
            "maximum_observed_transition_bracket_width_s": "s",
            "sampled_contact_transition_brackets[].lower_time_s": "s",
            "sampled_contact_transition_brackets[].upper_time_s": "s",
            "sampled_contact_transition_brackets[].bracket_width_s": "s",
            "sampled_contact_transition_brackets[].requested_time_tolerance_s": "s",
            "sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].time_s": "s",
            "sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].contact_force_N": "N",
            "sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].mean_contact_pressure_Pa": "Pa",
            "sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].gasket_compression_m": "m",
            "sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].gasket_strain": "1",
            "sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].gasket_constitutive_stress_Pa": "Pa",
            "sampled_contact_transition_brackets[].sampled_bracket_endpoint_results[].contact_gap_m": "m",
            "sampled_contact_transition_brackets[].refinement_observations[].time_s": "s",
            "sampled_contact_transition_brackets[].refinement_observations[].contact_force_N": "N",
            "sampled_contact_transition_brackets[].refinement_observations[].mean_contact_pressure_Pa": "Pa",
            "sampled_contact_transition_brackets[].refinement_observations[].gasket_compression_m": "m",
            "sampled_contact_transition_brackets[].refinement_observations[].gasket_strain": "1",
            "sampled_contact_transition_brackets[].refinement_observations[].gasket_constitutive_stress_Pa": "Pa",
            "sampled_contact_transition_brackets[].refinement_observations[].contact_gap_m": "m",
            "transition_refinement_complete": "1",
            "transition_refinement_solves": "1",
            "transition_refinement_work_units": "1",
            "transition_refinement_midpoint_times_s[]": "s",
            "time_history[].contact_force_sum_N": "N",
            "time_history[].maximum_active_force_residual_N": "N",
            "time_history[].response_field[].circumferential_coordinate_rad": "rad",
            "time_history[].response_field[].contact_force_N": "N",
            "time_history[].response_field[].mean_contact_pressure_Pa": "Pa",
            "time_history[].response_field[].gasket_compression_m": "m",
            "time_history[].response_field[].gasket_strain": "1",
            "time_history[].response_field[].gasket_constitutive_stress_Pa": "Pa",
            "time_history[].response_field[].contact_gap_m": "m",
            "time_history[].response_field[].branch_stress_Pa[]": "Pa",
            "minimum_flange_compliance_eigenvalue_m_N": "m/N",
            "time_history[].minimum_flange_compliance_eigenvalue_m_N": "m/N",
            "contact_work_units": "1",
            "contact_active_set_iterations": "1",
            "newton_iterations": "1",
            "node_count": "1",
            "time_knot_count": "1",
        },
        (
            "Caller nonlinear Maxwell branch backbones and equilibrium gasket backbone are coupled to caller-supplied positive-semidefinite flange compliance. An optional time-varying matrix history is linearly interpolated only after explicit caller review and each evaluation matrix is checked for positive semidefiniteness.",
            "Optional replayed-path bisection narrows observed contact-state transition brackets only with caller-reviewed sampling and a single-transition-per-bracket assumption; it does not establish exact event timing. Each bracket preserves both sampled endpoint states and response quantities; each refinement replay also records its sampled midpoint response, applied compliance-operator digest, and replay-input digest. These records expose the bounded search history but do not establish an exact event root or detect unobserved transitions. No extrapolation, constitutive fitting/transfer, flange FE generation, leakage or seal acceptance is inferred.",
        ),
        ("caller_nonlinear_maxwell_spatial_gasket_contact",),
        qualification="user_model",
    )]
