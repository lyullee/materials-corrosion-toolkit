"""Iterate transient radial wet-CO2 electrochemistry against cylindrical recession."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_cylindrical_scale_geometry import (
    WetCo2CylindricalGeometryKnot,
    WetCo2CylindricalScaleGeometryHistory,
    evaluate_wet_co2_cylindrical_scale_geometry_history,
)
from .wet_co2_cylindrical_spatial_mixed_potential import (
    MODEL_ID as SPATIAL_MODEL_ID,
    WetCo2CylindricalSpatialMixedPotential,
    evaluate_wet_co2_cylindrical_spatial_mixed_potential,
)

MODEL_ID = "integration.wet_co2_cylindrical_geometry_coupled_history"
SOURCE_ID = "bounded_picard_replay_of_spatial_bv_transport_and_cylindrical_recession"


class WetCo2CylindricalGeometryCoupledHistory(Contract):
    """Exact-knot fixed-point coupling around the existing spatial BV solver.

    Scale phase inventories are caller-fixed inputs at each exact knot. Their chemistry
    or kinetics are not recalculated by this outer geometry iteration.
    """

    schema_version: Literal["matintegrity.wet_co2_cylindrical_geometry_coupled_history.v1"] = (
        "matintegrity.wet_co2_cylindrical_geometry_coupled_history.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    spatial_request: WetCo2CylindricalSpatialMixedPotential
    maximum_geometry_iterations: int = Field(default=20, ge=1, le=80)
    geometry_relaxation_factor: float = Field(default=0.5, gt=0.0, le=1.0)
    absolute_bore_radius_tolerance_m: Positive = Field(default=1e-9)
    relative_bore_radius_tolerance: float = Field(default=1e-7, gt=0.0, le=1e-2)
    absolute_wall_inventory_tolerance_mol_m: Positive = Field(default=1e-12)
    relative_wall_inventory_tolerance: float = Field(default=1e-8, gt=0.0, le=1e-2)
    maximum_iteration_work_units: int = Field(default=20_000_000, ge=1_000, le=200_000_000)
    scale_inventory_is_caller_fixed_at_each_knot_reviewed: bool
    exact_knot_radius_reconstruction_reviewed: bool
    spatial_bv_model_and_boundary_applicability_reviewed: bool
    element_to_alloy_release_mapping_reviewed: bool
    geometry_and_scale_axisymmetry_reviewed: bool
    no_inter_knot_or_qualification_claim_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_budget_and_baseline(self):
        request = self.spatial_request
        if request.geometry_trial_mode:
            raise ValueError("the nested spatial request must be a strict base request; this model owns trial mode")
        geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(request.geometry)
        if geometry.status != "computed":
            raise ValueError("the caller geometry must compute before requesting coupled-history iteration")
        if request.geometry.history[0].wall_recession_m != 0.0:
            raise ValueError("the exact time-zero wall recession must be zero for release accumulation")
        radial_cells = len(request.initial_species[0].cell_concentrations_mol_m3)
        species_knots = sum(len(knot.species_boundaries) for knot in request.knots)
        work = self.maximum_geometry_iterations * radial_cells * species_knots
        if work > self.maximum_iteration_work_units:
            raise ValueError("geometry-iteration work estimate exceeds the caller budget")
        return self


def _geometry_from_steel_radius(
    source: WetCo2CylindricalScaleGeometryHistory,
    steel_inner_radius_m_by_knot: tuple[float, ...],
    *,
    iteration: int,
) -> WetCo2CylindricalScaleGeometryHistory:
    if len(steel_inner_radius_m_by_knot) != len(source.history):
        raise ValueError("steel-radius path must match the exact geometry knot count")
    knots = []
    prior_recession = -math.inf
    for source_knot, steel_inner in zip(source.history, steel_inner_radius_m_by_knot, strict=True):
        recession = steel_inner - source.initial_inner_radius_m
        if not math.isfinite(recession) or recession < -1e-12 or recession < prior_recession - 1e-12:
            raise ValueError("trial steel-surface recession must be finite, nonnegative and nondecreasing")
        prior_recession = recession
        knots.append(source_knot.model_copy(update={"wall_recession_m": max(0.0, recession)}))
    knot_tuple = tuple(knots)
    history_digest = canonical_digest([row.model_dump(mode="json") for row in knot_tuple])
    derived_provider_id = f"{MODEL_ID}.trial_geometry"
    evidence = Evidence(
        source_id=derived_provider_id,
        origin="model_prediction",
        citation=(
            f"Computed trial geometry for {MODEL_ID}, iteration {iteration}; derived from "
            f"{source.history_provider_id}@{source.history_provider_revision}, "
            f"record sha256={source.history_record_sha256}; upstream usage terms remain attached."
        ),
        license_id=source.history_evidence.license_id,
        sha256=history_digest,
    )
    payload = source.model_dump(mode="python")
    payload.update({
        "history": knot_tuple,
        "history_record_sha256": history_digest,
        "history_provider_id": derived_provider_id,
        "history_provider_revision": "picard-trial-v1",
        "history_evidence": evidence,
    })
    return WetCo2CylindricalScaleGeometryHistory.model_validate(payload)


def _geometry_candidate(
    source: WetCo2CylindricalScaleGeometryHistory,
    requested_bore_radius_m: tuple[float, ...],
    *,
    iteration: int,
) -> tuple[WetCo2CylindricalScaleGeometryHistory, tuple[float, ...]]:
    steel_radii = []
    for knot, bore_radius in zip(source.history, requested_bore_radius_m, strict=True):
        phase_map = {row.phase_id: row.moles_per_axial_metre_mol_m for row in knot.phase_inventories}
        scale_volume = math.fsum(
            phase_map[phase.phase_id] * phase.molar_volume_m3_mol for phase in source.phases
        )
        steel_radius_sq = bore_radius * bore_radius + scale_volume / math.pi
        if not math.isfinite(steel_radius_sq) or steel_radius_sq <= 0.0:
            raise ValueError("requested bore radius and fixed scale inventory imply invalid steel radius")
        steel_radii.append(math.sqrt(steel_radius_sq))
    steel_tuple = tuple(steel_radii)
    candidate = _geometry_from_steel_radius(source, steel_tuple, iteration=iteration)
    geometry_result = evaluate_wet_co2_cylindrical_scale_geometry_history(candidate)
    if geometry_result.status != "computed":
        raise ValueError(f"candidate geometry is outside support: {geometry_result.values.get('reason')}")
    actual = tuple(float(row["bore_radius_m"]) for row in geometry_result.values["history"])
    for expected, got in zip(requested_bore_radius_m, actual, strict=True):
        if not math.isclose(expected, got, rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("derived trial steel surface does not reproduce the requested bore radius")
    return candidate, steel_tuple


def _residual_norms(
    values: dict,
    *,
    radius_abs_tol: float,
    radius_rel_tol: float,
    inventory_abs_tol: float,
    inventory_rel_tol: float,
) -> tuple[float, float, float, float]:
    input_radius = values["input_bore_radius_m_by_knot"]
    target_radius = values["target_bore_radius_m_by_knot"]
    radius_residual = max(abs(float(a) - float(b)) for a, b in zip(input_radius, target_radius, strict=True))
    radius_scale = max(1e-30, *(abs(float(x)) for x in (*input_radius, *target_radius)))
    radius_tol = radius_abs_tol + radius_rel_tol * radius_scale
    balance = values["wall_element_balance_residual_mol_m_by_element"]
    scales = values["wall_element_inventory_scale_mol_m"]
    balance_norm = 0.0
    balance_tol_max = 0.0
    if set(balance) != set(scales):
        raise ValueError("wall element balance and scale IDs differ")
    for element, rows in balance.items():
        scale_rows = scales[element]
        if len(rows) != len(input_radius) or len(scale_rows) != len(input_radius):
            raise ValueError("wall element residual and scale arrays must align with exact geometry knots")
        for residual, scale in zip(rows, scale_rows, strict=True):
            residual, scale = float(residual), abs(float(scale))
            if not math.isfinite(residual) or not math.isfinite(scale):
                raise ValueError("wall element residuals and scales must be finite")
            tolerance = inventory_abs_tol + inventory_rel_tol * scale
            balance_norm = max(balance_norm, abs(residual) / max(tolerance, 1e-300))
            balance_tol_max = max(balance_tol_max, tolerance)
    return radius_residual, radius_tol, balance_norm, balance_tol_max


def evaluate_wet_co2_cylindrical_geometry_coupled_history(
    request: WetCo2CylindricalGeometryCoupledHistory,
) -> Calculation:
    """Run bounded geometry/electrochemistry Picard trials and a final strict solve."""
    base_request = request.spatial_request
    source_geometry = base_request.geometry
    initial_geometry = evaluate_wet_co2_cylindrical_scale_geometry_history(source_geometry)
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "spatial_model_id": SPATIAL_MODEL_ID,
        "spatial_input_sha256": canonical_digest(base_request.model_dump(mode="json")),
        "asset_id": source_geometry.asset_id,
        "location_id": source_geometry.location_id,
        "time_basis_id": source_geometry.time_basis_id,
        "time_s": [float(row.time_s) for row in source_geometry.history],
        "iteration_method": "bounded_damped_picard_on_exact_knot_steel_surface_radius.v1",
        "scale_inventory_mode": "caller_fixed_at_each_exact_knot",
    }
    if initial_geometry.status != "computed":
        return Calculation(status=initial_geometry.status, values=base | {
            "reason": "caller_geometry_history_did_not_compute",
            "geometry_status": initial_geometry.status,
        })
    review_fields = {
        "scale_inventory_is_caller_fixed_at_each_knot_reviewed": request.scale_inventory_is_caller_fixed_at_each_knot_reviewed,
        "exact_knot_radius_reconstruction_reviewed": request.exact_knot_radius_reconstruction_reviewed,
        "spatial_bv_model_and_boundary_applicability_reviewed": request.spatial_bv_model_and_boundary_applicability_reviewed,
        "element_to_alloy_release_mapping_reviewed": request.element_to_alloy_release_mapping_reviewed,
        "geometry_and_scale_axisymmetry_reviewed": request.geometry_and_scale_axisymmetry_reviewed,
        "no_inter_knot_or_qualification_claim_reviewed": request.no_inter_knot_or_qualification_claim_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in review_fields.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "reason": "caller_review_gates_incomplete", "missing_reviews": missing,
        })

    radius_guess = tuple(float(row["bore_radius_m"]) for row in initial_geometry.values["history"])
    radius_path_history = []
    trial_result = None
    trial_request = None
    converged = False
    final_radius_norm = math.inf
    final_radius_tol = 0.0
    final_balance_norm = math.inf
    final_balance_tol = 0.0

    for iteration in range(request.maximum_geometry_iterations):
        try:
            trial_geometry, _steel_guess = _geometry_candidate(
                source_geometry, radius_guess, iteration=iteration,
            )
            geometry_sha = canonical_digest(trial_geometry.model_dump(mode="json"))
            fixed_point_digest = canonical_digest({
                "controller_model_id": MODEL_ID,
                "controller_input_sha256": canonical_digest(request.model_dump(mode="json")),
                "iteration": iteration,
                "bore_radius_m_by_knot": list(radius_guess),
                "geometry_sha256": geometry_sha,
            })
            trial_payload = base_request.model_dump(mode="python")
            trial_payload.update({
                "geometry": trial_geometry,
                "geometry_sha256": geometry_sha,
                "geometry_trial_mode": True,
                "fixed_point_input_sha256": fixed_point_digest,
                "trial_geometry_closure_exemption_reviewed": True,
                "inventory_absolute_tolerance_mol_m": request.absolute_wall_inventory_tolerance_mol_m,
                "inventory_relative_tolerance": request.relative_wall_inventory_tolerance,
            })
            trial_request = WetCo2CylindricalSpatialMixedPotential.model_validate(trial_payload)
            trial_result = evaluate_wet_co2_cylindrical_spatial_mixed_potential(trial_request)
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "geometry_trial_construction_or_evaluation_failed",
                "iteration_index": iteration,
                "detail": str(exc),
                "iteration_prefix": radius_path_history,
            })
        if trial_result.status != "computed":
            return Calculation(status=trial_result.status, values=base | {
                "reason": "spatial_electrochemical_trial_did_not_compute",
                "iteration_index": iteration,
                "trial_status": trial_result.status,
                "trial_values": trial_result.values,
                "iteration_prefix": radius_path_history,
            })
        values = trial_result.values
        if values.get("fixed_point_input_sha256") != fixed_point_digest:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "spatial_trial_digest_does_not_match_controller_iteration",
                "iteration_index": iteration,
                "iteration_prefix": radius_path_history,
            })
        try:
            final_radius_norm, final_radius_tol, final_balance_norm, final_balance_tol = _residual_norms(
                values,
                radius_abs_tol=request.absolute_bore_radius_tolerance_m,
                radius_rel_tol=request.relative_bore_radius_tolerance,
                inventory_abs_tol=request.absolute_wall_inventory_tolerance_mol_m,
                inventory_rel_tol=request.relative_wall_inventory_tolerance,
            )
            target_radius = tuple(float(row) for row in values["target_bore_radius_m_by_knot"])
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "trial_result_missing_or_invalid_fixed_point_ledgers",
                "iteration_index": iteration,
                "detail": str(exc),
                "iteration_prefix": radius_path_history,
            })
        result_digest = canonical_digest(trial_result.model_dump(mode="json"))
        radius_path_history.append({
            "iteration_index": iteration,
            "fixed_point_input_sha256": fixed_point_digest,
            "trial_request_sha256": canonical_digest(trial_request.model_dump(mode="json")),
            "trial_result_sha256": result_digest,
            "input_bore_radius_m_by_knot": list(radius_guess),
            "target_bore_radius_m_by_knot": list(target_radius),
            "fixed_point_residual_norm_m": final_radius_norm,
            "fixed_point_tolerance_m": final_radius_tol,
            "wall_element_balance_residual_norm_ratio": final_balance_norm,
            "wall_element_balance_tolerance_mol_m": final_balance_tol,
        })
        if final_radius_norm <= final_radius_tol and final_balance_norm <= 1.0:
            converged = True
            break
        if iteration + 1 >= request.maximum_geometry_iterations:
            break
        # Relax in steel-surface radius. For a fixed caller scale inventory this
        # coordinate preserves the geometry model's nondecreasing-recession rule.
        try:
            current_steel = tuple(float(row["steel_inner_radius_m"]) for row in values["history"])
            target_steel = []
            for knot, target in zip(source_geometry.history, target_radius, strict=True):
                phase_map = {row.phase_id: row.moles_per_axial_metre_mol_m for row in knot.phase_inventories}
                scale_volume = math.fsum(phase_map[p.phase_id] * p.molar_volume_m3_mol for p in source_geometry.phases)
                target_steel.append(math.sqrt(target * target + scale_volume / math.pi))
            steel_next = tuple(
                current_steel[i] + request.geometry_relaxation_factor * (target_steel[i] - current_steel[i])
                for i in range(len(target_steel))
            )
            bore_next = []
            for knot, steel in zip(source_geometry.history, steel_next, strict=True):
                phase_map = {row.phase_id: row.moles_per_axial_metre_mol_m for row in knot.phase_inventories}
                scale_volume = math.fsum(phase_map[p.phase_id] * p.molar_volume_m3_mol for p in source_geometry.phases)
                bore_sq = steel * steel - scale_volume / math.pi
                if not math.isfinite(bore_sq) or bore_sq <= 0.0:
                    raise ValueError("relaxed steel-radius path leaves positive-bore support")
                bore_next.append(math.sqrt(bore_sq))
            radius_guess = tuple(bore_next)
            # Validate monotone steel recession and the fixed outer-radius geometry now.
            _geometry_candidate(source_geometry, radius_guess, iteration=iteration + 1)
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "relaxed_geometry_iterate_failed_closed",
                "iteration_index": iteration,
                "detail": str(exc),
                "iteration_prefix": radius_path_history,
            })

    if not converged or trial_result is None or trial_request is None:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "geometry_electrochemistry_picard_iteration_did_not_converge",
            "converged": False,
            "iteration_count": len(radius_path_history),
            "final_radius_residual_norm_m": final_radius_norm,
            "final_radius_tolerance_m": final_radius_tol,
            "final_wall_balance_residual_norm_ratio": final_balance_norm,
            "iteration_history": radius_path_history,
            "qualification": "nonconverged geometry trials are diagnostics only",
        })

    # Re-evaluate once with the ordinary strict wall geometry/release gate. A
    # fixed-point trial is never promoted to a final result by residual reporting alone.
    strict_payload = trial_request.model_dump(mode="python")
    strict_payload.update({"geometry_trial_mode": False, "fixed_point_input_sha256": None,
                           "trial_geometry_closure_exemption_reviewed": False})
    strict_request = WetCo2CylindricalSpatialMixedPotential.model_validate(strict_payload)
    strict_result = evaluate_wet_co2_cylindrical_spatial_mixed_potential(strict_request)
    if strict_result.status != "computed":
        return Calculation(status=strict_result.status, values=base | {
            "reason": "converged_trial_failed_final_strict_geometry_recheck",
            "final_spatial_status": strict_result.status,
            "final_spatial_values": strict_result.values,
            "iteration_history": radius_path_history,
        })
    strict_values = strict_result.values
    try:
        strict_radius_norm, strict_radius_tol, strict_balance_ratio, strict_balance_tol = _residual_norms(
            strict_values,
            radius_abs_tol=request.absolute_bore_radius_tolerance_m,
            radius_rel_tol=request.relative_bore_radius_tolerance,
            inventory_abs_tol=request.absolute_wall_inventory_tolerance_mol_m,
            inventory_rel_tol=request.relative_wall_inventory_tolerance,
        )
    except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as exc:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "final_strict_result_fixed_point_ledgers_invalid",
            "detail": str(exc), "iteration_history": radius_path_history,
        })
    if strict_radius_norm > strict_radius_tol or strict_balance_ratio > 1.0:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "final_strict_result_exceeds_geometry_or_inventory_tolerance",
            "final_radius_residual_norm_m": strict_radius_norm,
            "final_radius_tolerance_m": strict_radius_tol,
            "final_wall_balance_residual_norm_ratio": strict_balance_ratio,
            "final_wall_balance_tolerance_mol_m": strict_balance_tol,
            "iteration_history": radius_path_history,
        })
    return Calculation(status="computed", values=base | {
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "converged": True,
        "iteration_count": len(radius_path_history),
        "iteration_history": radius_path_history,
        "final_radius_residual_norm_m": strict_radius_norm,
        "final_radius_tolerance_m": strict_radius_tol,
        "final_wall_balance_residual_norm_ratio": strict_balance_ratio,
        "final_wall_balance_tolerance_mol_m": strict_balance_tol,
        "final_spatial_request_sha256": canonical_digest(strict_request.model_dump(mode="json")),
        "final_spatial_result_sha256": canonical_digest(strict_result.model_dump(mode="json")),
        "final_spatial_result": strict_values,
        "final_geometry_history": strict_values["history"],
        "coupling_scope": "iterated_radial_species_transport_common_BV_potential_wall_release_and_cylindrical_geometry",
        "scale_scope": "caller_fixed_phase_inventory_history_is_used_in_each_geometry_trial",
        "qualification": "bounded user-calibrated screening model; not independently validated for design or life prediction",
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CylindricalGeometryCoupledHistory,
        evaluator=evaluate_wet_co2_cylindrical_geometry_coupled_history,
        units={
            "time_s[]": "s",
            "final_geometry_history[].bore_radius_m": "m",
            "final_spatial_result.history[].cell_concentration_mol_m3_by_species.*[]": "mol/m^3",
            "final_spatial_result.history[].mixed_potential_at_interval_end_V": "V",
            "final_spatial_result.interval_ledger[].reaction_extent_mol_m.*": "mol/m",
            "final_radius_residual_norm_m": "m",
            "final_wall_balance_tolerance_mol_m": "mol/m",
        },
        assumptions=(
            "Each outer iteration reruns the transient cylindrical finite-volume species balance and common BV mixed potential on a candidate exact-knot geometry path.",
            "Wall elemental release is accumulated from the declared aqueous reaction stoichiometry and alloy inventory; target radius follows annular mass-volume balance with caller density.",
            "Caller scale phase inventories are fixed at their declared exact knots during all iterations; scale chemistry, precipitation kinetics and morphology are not solved.",
            "Geometry and wall-element residuals must pass the declared fixed-point tolerances and a final ordinary strict spatial solve.",
            "No interpolation between caller knots, field extrapolation, independent experimental validation, or design-life qualification is provided.",
        ),
        source_ids=(
            SOURCE_ID,
            "independent_transient_cylindrical_finite_volume_electrochemical_inventory",
            "caller_calibrated_butler_volmer_reaction_set",
            "degradation.wet_co2_cylindrical_scale_geometry_history",
            "caller_wet_co2_scale_phase_molar_volume",
        ),
        qualification="user_model",
    ),)
