"""Bounded fixed-point control and spatial-BV adapter for cylindrical wet-CO2 geometry."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_cylindrical_geometry_fixed_point_controller"
SOURCE_ID = "bounded_relaxed_fixed_point_controller_for_caller_cylindrical_solver"


class WetCo2GeometryFixedPointRequest(Contract):
    """Input contract for iterating a caller's radius-to-radius solver mapping.

    The callback is a runtime dependency, deliberately not serialized in this request.
    It must calculate chemistry/transport/electrochemistry for the supplied radius path
    and return the corresponding wall-loss target path plus independent balance residuals.
    """

    schema_version: Literal["matintegrity.wet_co2_geometry_fixed_point.v1"] = (
        "matintegrity.wet_co2_geometry_fixed_point.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    asset_id: str = Field(min_length=1, max_length=160)
    location_id: str = Field(min_length=1, max_length=160)
    time_basis_id: str = Field(min_length=1, max_length=160)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=2000)
    initial_bore_radius_m_by_knot: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    outer_radius_m: Positive
    solver_model_id: str = Field(min_length=1, max_length=160)
    solver_contract_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solver_contract_evidence: Evidence
    maximum_iterations: int = Field(default=30, ge=1, le=200)
    relaxation_factor: float = Field(default=0.5, gt=0.0, le=1.0)
    absolute_radius_tolerance_m: Positive = 1e-9
    relative_radius_tolerance: float = Field(default=1e-7, gt=0.0, le=1e-2)
    absolute_inventory_balance_tolerance_mol_m: Positive = 1e-10
    relative_inventory_balance_tolerance: float = Field(default=1e-8, gt=0.0, le=1e-2)
    corrosion_bore_radius_increase_only_reviewed: bool
    solver_mapping_and_iteration_semantics_reviewed: bool
    inventory_residual_definition_reviewed: bool
    no_between_knot_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_grid_and_provenance(self):
        if len(self.time_s) != len(self.initial_bore_radius_m_by_knot):
            raise ValueError("time and initial radius arrays must have identical lengths")
        if self.time_s[0] != 0.0 or any(b <= a for a, b in zip(self.time_s, self.time_s[1:])):
            raise ValueError("fixed-point knots must start at zero and increase strictly")
        if any(not math.isfinite(t) or t < 0.0 for t in self.time_s):
            raise ValueError("all exact knot times must be finite and nonnegative")
        if any(radius >= self.outer_radius_m for radius in self.initial_bore_radius_m_by_knot):
            raise ValueError("every initial bore radius must remain below the fixed outer radius")
        if any(b < a - self.absolute_radius_tolerance_m for a, b in zip(
            self.initial_bore_radius_m_by_knot, self.initial_bore_radius_m_by_knot[1:]
        )):
            raise ValueError("the seed bore-radius history must be nondecreasing for corrosion-only coupling")
        if self.solver_contract_evidence.source_id != self.solver_model_id:
            raise ValueError("solver Evidence must identify the declared caller solver")
        if self.solver_contract_evidence.sha256 != self.solver_contract_sha256:
            raise ValueError("solver Evidence digest must match the pinned solver contract")
        if not self.solver_contract_evidence.license_id:
            raise ValueError("solver contract usage license must be explicit")
        return self


def _call_digest(request: WetCo2GeometryFixedPointRequest, radii: tuple[float, ...]) -> str:
    return canonical_digest({
        "model_id": MODEL_ID,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis_id": request.time_basis_id,
        "time_s": list(request.time_s),
        "input_bore_radius_m_by_knot": list(radii),
        "solver_model_id": request.solver_model_id,
        "solver_contract_sha256": request.solver_contract_sha256,
    })


def evaluate_wet_co2_geometry_fixed_point(
    request: WetCo2GeometryFixedPointRequest,
    *,
    candidate_solver: Callable[..., Calculation],
) -> Calculation:
    """Iterate a caller solver's radius mapping until geometry and loss are consistent.

    The controller verifies exact knot identity, fixed-point residuals and the caller
    solver's element-inventory residual ledger. It does not implement or qualify the
    chemistry, transport, electrochemical kinetics, or constitutive response itself.
    """
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis_id": request.time_basis_id,
        "solver_model_id": request.solver_model_id,
        "solver_contract_sha256": request.solver_contract_sha256,
        "iteration_method": "caller_mapping_relaxed_fixed_point.v1",
        "time_s": list(request.time_s),
    }
    reviews = {
        "corrosion_bore_radius_increase_only_reviewed": request.corrosion_bore_radius_increase_only_reviewed,
        "solver_mapping_and_iteration_semantics_reviewed": request.solver_mapping_and_iteration_semantics_reviewed,
        "inventory_residual_definition_reviewed": request.inventory_residual_definition_reviewed,
        "no_between_knot_claim_reviewed": request.no_between_knot_claim_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"reason": "caller_review_gates_incomplete", "missing_reviews": missing})
    if not callable(candidate_solver):
        return Calculation(status="needs_data", values=base | {"reason": "declared_candidate_solver_is_not_callable"})

    radii = tuple(float(value) for value in request.initial_bore_radius_m_by_knot)
    iteration_history: list[dict[str, Any]] = []
    previous_result: Calculation | None = None
    for index in range(request.maximum_iterations):
        call_digest = _call_digest(request, radii)
        try:
            result = candidate_solver(request, radii, index, previous_result, call_digest)
        except Exception as exc:  # callback is an external integration boundary
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_raised_exception",
                "iteration_index": index,
                "detail": f"{type(exc).__name__}: {exc}",
                "iteration_history": iteration_history,
            })
        if not isinstance(result, Calculation):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_did_not_return_calculation_contract",
                "iteration_index": index,
                "iteration_history": iteration_history,
            })
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "reason": "caller_solver_did_not_compute_candidate",
                "iteration_index": index,
                "caller_solver_status": result.status,
                "caller_solver_result_sha256": canonical_digest(result.model_dump(mode="json")),
                "iteration_history": iteration_history,
            })
        values = result.values
        if values.get("model_id") != request.solver_model_id:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_model_identity_mismatch", "iteration_index": index,
                "iteration_history": iteration_history,
            })
        if values.get("fixed_point_input_sha256") != call_digest:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_input_radius_digest_mismatch", "iteration_index": index,
                "expected_fixed_point_input_sha256": call_digest,
                "caller_fixed_point_input_sha256": values.get("fixed_point_input_sha256"),
                "iteration_history": iteration_history,
            })
        if tuple(values.get("time_s", ())) != request.time_s:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_time_grid_mismatch", "iteration_index": index,
                "iteration_history": iteration_history,
            })
        target_raw = values.get("target_bore_radius_m_by_knot")
        if not isinstance(target_raw, (list, tuple)) or len(target_raw) != len(radii):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_target_radius_history_missing_or_misaligned",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        try:
            target = tuple(float(value) for value in target_raw)
        except (TypeError, ValueError, OverflowError):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_target_radius_non_numeric",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        if any(not math.isfinite(value) or value <= 0.0 or value >= request.outer_radius_m for value in target):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_target_radius_outside_geometry_bounds",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        if any(target[i] < radii[i] - request.absolute_radius_tolerance_m
               for i in range(len(target))):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "target_radius_decreases_from_current_corrosion_iterate",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        if any(target[i + 1] < target[i] - request.absolute_radius_tolerance_m
               for i in range(len(target) - 1)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "target_bore_radius_history_is_not_monotone_in_corrosion_direction",
                "iteration_index": index, "iteration_history": iteration_history,
            })

        residual = tuple(target[i] - radii[i] for i in range(len(target)))
        residual_norm = max(abs(value) for value in residual)
        radius_scale = max(max(abs(value) for value in radii), max(abs(value) for value in target), 1e-30)
        radius_tolerance = request.absolute_radius_tolerance_m + request.relative_radius_tolerance * radius_scale
        balance = values.get("wall_element_balance_residual_mol_m_by_element")
        if not isinstance(balance, dict) or not balance:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_element_inventory_balance_ledger_missing",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        if any(not isinstance(rows, (list, tuple)) or len(rows) != len(radii)
               for rows in balance.values()):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_element_inventory_balance_grid_mismatch",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        try:
            balance_norm = max(abs(float(value)) for rows in balance.values() for value in rows)
        except (TypeError, ValueError):
            balance_norm = math.inf
        if not math.isfinite(balance_norm):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_element_inventory_residual_nonfinite",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        scale_raw = values.get("wall_element_inventory_scale_mol_m", [1.0])
        try:
            if isinstance(scale_raw, dict):
                if set(scale_raw) != set(balance):
                    raise ValueError("inventory scale element IDs must match the residual ledger")
                if any(not isinstance(rows, (list, tuple)) or len(rows) != len(radii)
                       for rows in scale_raw.values()):
                    raise ValueError("inventory scale arrays must match the exact knot grid")
                scale_values = [float(value) for rows in scale_raw.values() for value in rows]
            elif isinstance(scale_raw, (list, tuple)):
                scale_values = [float(value) for value in scale_raw]
            else:
                raise ValueError("inventory scale must be an ordered list or element mapping")
        except (TypeError, ValueError):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_element_inventory_scale_invalid",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        if not scale_values or any(not math.isfinite(value) or value < 0.0 for value in scale_values):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "caller_solver_element_inventory_scale_invalid",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        balance_scale = max(1e-30, max(scale_values))
        balance_tolerance = request.absolute_inventory_balance_tolerance_mol_m + request.relative_inventory_balance_tolerance * balance_scale
        result_digest = canonical_digest(result.model_dump(mode="json"))
        row = {
            "iteration_index": index,
            "fixed_point_input_sha256": call_digest,
            "caller_solver_result_sha256": result_digest,
            "input_radius_m_by_knot": list(radii),
            "target_radius_m_by_knot": list(target),
            "fixed_point_residual_m_by_knot": list(residual),
            "fixed_point_residual_norm_m": residual_norm,
            "fixed_point_tolerance_m": radius_tolerance,
            "wall_element_balance_residual_mol_m_by_element": balance,
            "wall_element_balance_residual_norm_mol_m": balance_norm,
            "wall_element_balance_tolerance_mol_m": balance_tolerance,
        }
        iteration_history.append(row)
        if residual_norm <= radius_tolerance and balance_norm <= balance_tolerance:
            return Calculation(status="computed", values=base | {
                "input_sha256": canonical_digest(request.model_dump(mode="json")),
                "converged": True,
                "iteration_count": index + 1,
                "converged_bore_radius_m_by_knot": list(target),
                "fixed_point_residual_norm_m": residual_norm,
                "wall_element_balance_residual_norm_mol_m": balance_norm,
                "caller_solver_result_sha256": result_digest,
                "caller_solver_values": values,
                "iteration_history": iteration_history,
                "coupling_scope": "converged_caller_solver_fixed_point_controller_only",
                "qualification": "no corrosion chemistry, constitutive response, or field fitness is supplied by this controller",
            })
        if index + 1 == request.maximum_iterations:
            break
        candidate = tuple(radii[i] + request.relaxation_factor * residual[i] for i in range(len(radii)))
        if any(not math.isfinite(value) or value <= 0.0 or value >= request.outer_radius_m for value in candidate):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "relaxed_iterate_left_cylindrical_wall_domain",
                "iteration_index": index, "iteration_history": iteration_history,
            })
        radii = candidate
        previous_result = result

    return Calculation(status="out_of_scope", values=base | {
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "converged": False,
        "reason": "fixed_point_iteration_limit_reached",
        "iteration_count": len(iteration_history),
        "iteration_history": iteration_history,
        "qualification": "nonconverged iterates are diagnostic only and must not be used as a computed geometry history",
    })


def make_spatial_wet_co2_candidate_solver(spatial_request_template):
    """Bind the spatial BV calculator as a fixed-point candidate solver.

    The template supplies all reviewed transport, chemistry, kinetics, material,
    scale-phase, and source inputs. For each iteration, this adapter reconstructs
    the annular geometry from the controller's current bore-radius path while
    keeping the template's exact scale inventories, then runs the real spatial
    evaluator in its explicit trial mode. It does not fit or invent inputs.
    """
    from . import wet_co2_cylindrical_spatial_mixed_potential as spatial
    from .wet_co2_cylindrical_scale_geometry import WetCo2CylindricalScaleGeometryHistory

    if not isinstance(spatial_request_template, spatial.WetCo2CylindricalSpatialMixedPotential):
        raise TypeError("spatial_request_template must be WetCo2CylindricalSpatialMixedPotential")

    template = spatial_request_template
    template_times = tuple(float(row.time_s) for row in template.knots)
    original_geometry = template.geometry
    original_history_sha256 = original_geometry.history_record_sha256
    def candidate_solver(controller_request, radii, iteration_index, previous_result, call_digest):
        del iteration_index, previous_result
        if (controller_request.solver_model_id != spatial.MODEL_ID
                or controller_request.solver_contract_sha256 != candidate_solver.configuration_sha256
                or controller_request.asset_id != original_geometry.asset_id
                or controller_request.location_id != original_geometry.location_id
                or controller_request.time_basis_id != original_geometry.time_basis_id
                or controller_request.outer_radius_m != original_geometry.outer_radius_m
                or tuple(controller_request.time_s) != template_times
                or len(radii) != len(original_geometry.history)):
            return Calculation(status="out_of_scope", values={
                "model_id": spatial.MODEL_ID,
                "reason": "controller_and_spatial_template_identity_or_exact_grid_mismatch",
            })
        if not math.isclose(float(radii[0]), float(template.geometry.initial_inner_radius_m),
                            rel_tol=1e-10, abs_tol=1e-12):
            # The original radius may already include the template's scale volume.
            initial_scale = math.fsum(
                row.moles_per_axial_metre_mol_m
                * next(phase.molar_volume_m3_mol for phase in original_geometry.phases
                       if phase.phase_id == row.phase_id)
                for row in original_geometry.history[0].phase_inventories
            )
            initial_bore = math.sqrt(max(
                original_geometry.initial_inner_radius_m ** 2 - initial_scale / math.pi, 0.0
            ))
            if not math.isclose(float(radii[0]), initial_bore, rel_tol=1e-10, abs_tol=1e-12):
                return Calculation(status="out_of_scope", values={
                    "model_id": spatial.MODEL_ID,
                    "reason": "controller_initial_radius_does_not_match_template_scale_geometry",
                    "template_initial_bore_radius_m": initial_bore,
                })

        geometry_payload = original_geometry.model_dump(mode="json")
        phase_molar_volumes = {row.phase_id: row.molar_volume_m3_mol for row in original_geometry.phases}
        rebuilt_history = []
        for index, (knot, radius) in enumerate(zip(original_geometry.history, radii, strict=True)):
            if knot.time_s != controller_request.time_s[index]:
                return Calculation(status="out_of_scope", values={
                    "model_id": spatial.MODEL_ID,
                    "reason": "geometry_template_knot_time_mismatch",
                    "failed_knot_index": index,
                })
            scale_area_per_length = math.fsum(
                row.moles_per_axial_metre_mol_m * phase_molar_volumes[row.phase_id]
                for row in knot.phase_inventories
            )
            radius_sq = float(radius) * float(radius)
            steel_inner_sq = radius_sq + scale_area_per_length / math.pi
            if (not math.isfinite(steel_inner_sq) or steel_inner_sq <= 0.0
                    or not math.isfinite(float(radius)) or float(radius) <= 0.0
                    or float(radius) >= original_geometry.outer_radius_m):
                return Calculation(status="out_of_scope", values={
                    "model_id": spatial.MODEL_ID,
                    "reason": "candidate_radius_or_scale_inventory_outside_cylindrical_support",
                    "failed_knot_index": index,
                })
            recession = math.sqrt(steel_inner_sq) - original_geometry.initial_inner_radius_m
            if recession < -1e-12 * max(original_geometry.initial_inner_radius_m, 1.0):
                return Calculation(status="out_of_scope", values={
                    "model_id": spatial.MODEL_ID,
                    "reason": "candidate_radius_implies_negative_wall_recession",
                    "failed_knot_index": index,
                })
            row = knot.model_dump(mode="json")
            row["wall_recession_m"] = max(0.0, recession)
            rebuilt_history.append(row)

        geometry_payload["history"] = rebuilt_history
        derived_history_sha256 = canonical_digest(rebuilt_history)
        geometry_payload["history_record_sha256"] = derived_history_sha256
        geometry_payload["history_provider_id"] = MODEL_ID
        geometry_payload["history_provider_revision"] = controller_request.solver_contract_sha256
        original_license = original_geometry.history_evidence[0].license_id
        geometry_payload["history_evidence"] = [{
            "source_id": MODEL_ID,
            "origin": "model_prediction",
            "citation": (
                "Geometry history derived for one bounded fixed-point candidate; "
                f"controller input SHA-256 {call_digest}; adapter configuration SHA-256 "
                f"{candidate_solver.configuration_sha256}; source history SHA-256 {original_history_sha256}"
            ),
            "license_id": original_license,
            "sha256": derived_history_sha256,
        }]
        rebuilt_geometry = WetCo2CylindricalScaleGeometryHistory.model_validate(geometry_payload)
        spatial_payload = template.model_dump(mode="json")
        spatial_payload.update({
            "geometry": rebuilt_geometry.model_dump(mode="json"),
            "geometry_sha256": canonical_digest(rebuilt_geometry.model_dump(mode="json")),
            "geometry_trial_mode": True,
            "fixed_point_input_sha256": call_digest,
            "trial_geometry_closure_exemption_reviewed": True,
        })
        calculation = spatial.evaluate_wet_co2_cylindrical_spatial_mixed_potential(
            spatial.WetCo2CylindricalSpatialMixedPotential.model_validate(spatial_payload)
        )
        if calculation.status == "computed":
            values = calculation.values | {
                "candidate_geometry_source_history_sha256": original_history_sha256,
                "candidate_geometry_derived_history_sha256": derived_history_sha256,
                "fixed_point_iteration_geometry_rebuilt": True,
            }
            return Calculation(status="computed", values=values, notes=calculation.notes)
        return calculation

    candidate_solver.configuration_sha256 = canonical_digest({
        "adapter_id": "make_spatial_wet_co2_candidate_solver.v1",
        "solver_model_id": spatial.MODEL_ID,
        "spatial_template_sha256": canonical_digest(template.model_dump(mode="json")),
    })
    candidate_solver.solver_model_id = spatial.MODEL_ID
    return candidate_solver


def specifications() -> tuple[ModelSpec, ...]:
    from . import wet_co2_cylindrical_spatial_mixed_potential as spatial

    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2GeometryFixedPointRequest,
        evaluator=evaluate_wet_co2_geometry_fixed_point,
        units={
            "time_s[]": "s",
            "converged_bore_radius_m_by_knot[]": "m",
            "fixed_point_residual_norm_m": "m",
            "wall_element_balance_residual_norm_mol_m": "mol/m",
        },
        assumptions=(
            "A caller-owned runtime solver or bundled spatial-BV adapter must recompute declared physics for each supplied exact-knot radius path.",
            "The controller checks target radii and wall-element inventory residuals; its spatial adapter derives them from the bounded BV calculation.",
            "Damped Picard iteration is bounded by caller-selected iteration and tolerance limits; no convergence is claimed unless both geometry and inventory gates pass.",
            "The model is a coupling controller and does not supply chemistry, transport, electrochemical kinetics, empirical parameters, or corrosion qualification.",
        ),
        source_ids=(
            SOURCE_ID,
            "caller_selected_geometry_dependent_wet_co2_solver",
            spatial.SOURCE_ID,
            spatial.KINETICS_SOURCE_ID,
            spatial.GEOMETRY_SOURCE_ID,
        ),
        runtime_dependency_names=("candidate_solver",),
        qualification="user_model",
    ),)
