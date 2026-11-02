"""Sequential operator-split transport over a caller-pinned slit geometry history."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any, Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Positive, canonical_digest
from .crevice_geometry_aware_chemistry import (
    CreviceGeometryAwareAqueousChemistryProvider,
    GeometryAwareChemistryEvaluationError,
)
from .crevice_geometry_aware_solid_deposition import (
    CreviceGeometryAwareSolidDepositionProvider,
    GeometryAwareSolidExtentEvaluationError,
)
from .crevice_geometry import (
    PlanarSlitEndpointVelocityPath,
    PlanarSlitGeometry,
    PlanarSlitHydraulicFlow,
    evaluate_planar_slit_hydraulic_flow,
    planar_slit_transport_geometry,
)
from .restricted_transport import RestrictedTransportRequest, solve_restricted_transport


class CreviceGeometryTransportCampaign(Contract):
    campaign_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    geometry_history: dict[str, Any]
    geometry_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    base_transport_request: RestrictedTransportRequest
    exact_geometry_transport_clock_reviewed: bool
    operator_split_and_fixed_within_interval_reviewed: bool
    cell_inventory_remap_on_aperture_change_reviewed: bool
    callback_global_time_mapping_reviewed: bool
    maximum_segment_count: int = Field(default=1000, ge=1, le=5000)

    @model_validator(mode="after")
    def geometry_history_identity(self):
        if canonical_digest(self.geometry_history) != self.geometry_history_sha256:
            raise ValueError("geometry-history digest does not match the pinned result")
        if self.geometry_history.get("geometry_id") != self.geometry_id:
            raise ValueError("geometry-history identity differs from the requested geometry")
        if self.geometry_history.get("status") != "computed":
            raise ValueError("a computed planar-slit geometry history is required")
        states = self.geometry_history.get("geometry_states")
        if not isinstance(states, list) or len(states) < 2 or len(states) > self.maximum_segment_count + 1:
            raise ValueError("geometry history must contain a bounded sequence of at least two states")
        times = [row.get("elapsed_time_s") if isinstance(row, dict) else None for row in states]
        if (
            any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in times)
            or times[0] != 0.0
            or any(right <= left for left, right in zip(times[:-1], times[1:], strict=True))
        ):
            raise ValueError("geometry-history clock must start at zero and increase strictly")
        clock = self.base_transport_request.output_times_s
        if times[-1] != clock[-1] or any(time not in clock for time in times):
            raise ValueError("every geometry knot, including the end time, must appear exactly on the transport output clock")
        if self.base_transport_request.reference_cross_section_m2 is None or self.base_transport_request.reference_cross_section_m2 != self.geometry_history.get("reference_cross_section_m2"):
            raise ValueError("transport and geometry reference cross sections differ")
        if self.base_transport_request.cell_count != self.geometry_history.get("cell_count"):
            raise ValueError("transport and geometry cell counts differ")
        widths = np.asarray(self.geometry_history.get("cell_widths_m"), dtype=float)
        if (
            widths.shape != (self.base_transport_request.cell_count,)
            or not np.isfinite(widths).all()
            or np.any(widths <= 0)
            or not math.isclose(float(np.sum(widths)), self.base_transport_request.length_m, rel_tol=1e-12)
        ):
            raise ValueError("geometry cell widths must match the transport length and grid")
        for state in states:
            geometry = state.get("restricted_transport_geometry")
            if not isinstance(geometry, dict):
                raise ValueError("each geometry knot needs a restricted-transport mapping")
            cell_area = np.asarray(geometry.get("cell_cross_section_m2"), dtype=float)
            face_area = np.asarray(geometry.get("face_cross_section_m2"), dtype=float)
            wall_area_density = np.asarray(geometry.get("wall_area_per_volume_m2_m3"), dtype=float)
            if (
                cell_area.shape != (self.base_transport_request.cell_count,)
                or face_area.shape != (self.base_transport_request.cell_count + 1,)
                or wall_area_density.shape != (self.base_transport_request.cell_count,)
                or not np.isfinite(cell_area).all()
                or not np.isfinite(face_area).all()
                or not np.isfinite(wall_area_density).all()
                or np.any(cell_area <= 0)
                or np.any(face_area <= 0)
                or np.any(wall_area_density <= 0)
                or geometry.get("reference_cross_section_m2") != self.base_transport_request.reference_cross_section_m2
                or tuple(geometry.get("cell_widths_m", ())) != tuple(self.geometry_history["cell_widths_m"])
            ):
                raise ValueError("geometry knot contains invalid or misaligned transport areas")
        if not self.base_transport_request.variable_area_one_dimensional_reduction_reviewed:
            raise ValueError("variable-area transport reduction must be reviewed")
        return self


def _shift_callback(callback, global_start_s: float):
    if callback is None:
        return None

    def shifted(local_time_s, *args):
        return callback(float(local_time_s) + global_start_s, *args)

    for attribute in (
        "provider_id",
        "provider_revision",
        "configuration_sha256",
        "network_id",
        "species_ids",
        "activity_provider_id",
        "activity_provider_revision",
        "activity_provider_configuration_sha256",
        "source_request_sha256",
        "source_sha256",
        "reaction_ids",
        "rate_units",
        "normalized_activity_table_sha256",
        "activity_table_source_record_lineage_sha256",
        "activity_table_evidence_sha256",
        "interpolation_method",
    ):
        if hasattr(callback, attribute):
            setattr(shifted, attribute, getattr(callback, attribute))
    shifted.global_time_offset_s = float(global_start_s)
    return shifted


def _callback_lineage(callbacks: dict[str, Callable | None], global_start_s: float) -> dict[str, Any]:
    """Describe callbacks and their local-to-global time mapping per segment."""
    lineage = {}
    attributes = (
        "provider_id",
        "provider_revision",
        "configuration_sha256",
        "network_id",
        "species_ids",
        "activity_provider_id",
        "activity_provider_revision",
        "activity_provider_configuration_sha256",
        "source_request_sha256",
        "source_sha256",
        "reaction_ids",
        "rate_units",
        "normalized_activity_table_sha256",
        "activity_table_source_record_lineage_sha256",
        "activity_table_evidence_sha256",
        "interpolation_method",
    )
    for role, callback in callbacks.items():
        if callback is None:
            continue
        identity = {
            name: list(value) if isinstance((value := getattr(callback, name, None)), tuple) else value
            for name in attributes
            if getattr(callback, name, None) is not None
        }
        identity["global_time_offset_s"] = float(global_start_s)
        identity["callback_identity_sha256"] = canonical_digest(identity)
        lineage[role] = identity
    return lineage


def solve_crevice_geometry_transport_campaign(
    campaign: CreviceGeometryTransportCampaign,
    *,
    reaction: Callable[[float, np.ndarray], np.ndarray] | None = None,
    tip_surface_flux: Callable[[float, np.ndarray, float | None], np.ndarray] | None = None,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
    geometry_aware_chemistry_provider: CreviceGeometryAwareAqueousChemistryProvider | None = None,
    geometry_aware_solid_deposition_provider: CreviceGeometryAwareSolidDepositionProvider | None = None,
) -> dict[str, Any]:
    """Solve fixed-geometry transport segments and remap cell inventory at knots.

    The aperture history is an independent, digest-pinned input. Each interval
    uses its left-knot geometry; at the right knot, concentrations are rescaled
    by old/new cell volume to preserve each cell's species inventory. Callback
    times are translated from interval-local solver time to campaign time.
    No wall recession is inferred from the transport solution.
    """
    req = campaign.base_transport_request
    result_digest = canonical_digest(campaign.model_dump(mode="json"))
    base = {
        "campaign_id": campaign.campaign_id,
        "geometry_id": campaign.geometry_id,
        "geometry_history_sha256": campaign.geometry_history_sha256,
        "campaign_input_sha256": result_digest,
        "simulation_id": req.simulation_id,
    }
    reviews = {
        "exact_geometry_transport_clock_reviewed": campaign.exact_geometry_transport_clock_reviewed,
        "operator_split_and_fixed_within_interval_reviewed": campaign.operator_split_and_fixed_within_interval_reviewed,
        "cell_inventory_remap_on_aperture_change_reviewed": campaign.cell_inventory_remap_on_aperture_change_reviewed,
        "callback_global_time_mapping_reviewed": campaign.callback_global_time_mapping_reviewed,
    }
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return base | {"status": "needs_data", "missing_reviews": missing}
    if req.axial_advection_provider_id is not None and req.axial_advection_velocity_m_s is None and axial_advection_velocity is None:
        return base | {"status": "needs_data", "reason": "The declared advection callback is unavailable"}
    if req.wall_surface_provider_id is not None and wall_surface_flux is None:
        return base | {"status": "needs_data", "reason": "The declared wall-surface callback is unavailable"}
    if req.tip_surface_provider_id is not None and tip_surface_flux is None:
        return base | {"status": "needs_data", "reason": "The declared tip-surface callback is unavailable"}
    if req.activity_provider_id is not None and activity_coefficients is None:
        return base | {"status": "needs_data", "reason": "The declared activity callback is unavailable"}

    states = campaign.geometry_history["geometry_states"]
    initial_geometry = states[0]["restricted_transport_geometry"]
    initial_area = np.asarray(initial_geometry.get("cell_cross_section_m2"), dtype=float)
    initial_face_area = np.asarray(initial_geometry.get("face_cross_section_m2"), dtype=float)
    declared_area = np.asarray(req.cell_cross_section_m2 or (), dtype=float)
    declared_face_area = np.asarray(req.face_cross_section_m2 or (), dtype=float)
    if (
        initial_area.shape != (req.cell_count,)
        or declared_area.shape != initial_area.shape
        or not np.allclose(initial_area, declared_area, rtol=1e-10, atol=0.0)
        or initial_face_area.shape != (req.cell_count + 1,)
        or declared_face_area.shape != initial_face_area.shape
        or not np.allclose(initial_face_area, declared_face_area, rtol=1e-10, atol=0.0)
    ):
        return base | {"status": "out_of_scope", "reason": "Initial transport geometry does not match the first pinned aperture state"}

    segment_results = []
    remaps = []
    callbacks = {
        "reaction": reaction,
        "tip_surface_flux": tip_surface_flux,
        "wall_surface_flux": wall_surface_flux,
        "activity_coefficients": activity_coefficients,
        "axial_advection_velocity": axial_advection_velocity,
    }

    def failed_segment(index: int, reason: str, *, status: str = "out_of_scope", result=None):
        attempted_start_s = float(states[index].get("elapsed_time_s", 0.0)) if index < len(states) else 0.0
        failure = base | {
            "status": status,
            "failed_segment_index": index,
            "failure_reason": reason,
            "computed_segment_count": len(segment_results),
            "computed_prefix": segment_results,
            "failed_segment_callback_lineage": _callback_lineage(callbacks, attempted_start_s),
        }
        if result is not None:
            failure["failed_segment_result"] = result
        return failure

    current_concentration = np.asarray(req.initial_concentration_mol_m3, dtype=float)
    previous_area = initial_area
    clock = req.output_times_s
    state_count = len(states)
    for index in range(state_count - 1):
        left_state, right_state = states[index], states[index + 1]
        start_s = float(left_state["elapsed_time_s"])
        end_s = float(right_state["elapsed_time_s"])
        geometry = left_state["restricted_transport_geometry"]
        segment_global_times = [time for time in clock if start_s <= time <= end_s]
        if not segment_global_times or segment_global_times[0] != start_s or segment_global_times[-1] != end_s:
            return failed_segment(index, "geometry segment boundaries are not present on the transport output clock")
        local_times = tuple(float(time - start_s) for time in segment_global_times)
        if len(local_times) < 2 or local_times[0] != 0.0:
            return failed_segment(index, "each geometry segment requires at least two transport output times")

        updates: dict[str, Any] = {
            "simulation_id": f"{req.simulation_id}:geometry-segment-{index:04d}",
            "output_times_s": local_times,
            "initial_concentration_mol_m3": tuple(tuple(float(value) for value in row) for row in current_concentration),
            "cell_count": geometry["cell_count"],
            "length_m": geometry["length_m"],
            "cell_widths_m": tuple(geometry["cell_widths_m"]),
            "cell_cross_section_m2": tuple(geometry["cell_cross_section_m2"]),
            "face_cross_section_m2": tuple(geometry["face_cross_section_m2"]),
            "reference_cross_section_m2": geometry["reference_cross_section_m2"],
            "wall_area_per_volume_m2_m3": tuple(geometry["wall_area_per_volume_m2_m3"])
            if req.wall_area_per_volume_m2_m3 is not None else None,
        }
        if req.mouth_concentration_history_mol_m3 is not None:
            history_by_time = dict(zip(clock, req.mouth_concentration_history_mol_m3, strict=True))
            mouth_rows = tuple(tuple(float(v) for v in history_by_time[time]) for time in segment_global_times)
            updates["mouth_concentration_mol_m3"] = mouth_rows[0]
            updates["mouth_concentration_history_mol_m3"] = mouth_rows
        segment_request = RestrictedTransportRequest.model_validate(req.model_dump(mode="python") | updates)
        segment = solve_restricted_transport(
            segment_request,
            reaction=_shift_callback(reaction, start_s),
            tip_surface_flux=_shift_callback(tip_surface_flux, start_s),
            wall_surface_flux=_shift_callback(wall_surface_flux, start_s),
            activity_coefficients=_shift_callback(activity_coefficients, start_s),
            axial_advection_velocity=_shift_callback(axial_advection_velocity, start_s),
        )
        if segment.get("status") != "computed":
            return failed_segment(
                index,
                "restricted transport segment did not compute",
                status=segment.get("status", "out_of_scope"),
                result=segment,
            )
        fields = np.asarray(segment["concentration_mol_m3"], dtype=float)
        if fields.shape != (len(local_times), len(req.species_ids), req.cell_count):
            return failed_segment(index, "transport solver returned an unexpected concentration field shape", result=segment)
        segment_results.append({
            "segment_index": index,
            "global_start_time_s": start_s,
            "global_end_time_s": end_s,
            "geometry_state_sha256": canonical_digest(left_state),
            "transport_input_sha256": canonical_digest(segment_request.model_dump(mode="json")),
            "callback_lineage": _callback_lineage(callbacks, start_s),
            "result": segment,
        })

        current_concentration = fields[-1]
        next_area = np.asarray(right_state["restricted_transport_geometry"].get("cell_cross_section_m2"), dtype=float)
        if next_area.shape != (req.cell_count,) or not np.isfinite(next_area).all() or np.any(next_area <= 0):
            return failed_segment(index, "next geometry has invalid cell areas")
        widths = np.asarray(geometry["cell_widths_m"], dtype=float)
        before = current_concentration * previous_area[None, :] * widths[None, :]
        remapped = before / (next_area[None, :] * widths[None, :])
        after = remapped * next_area[None, :] * widths[None, :]
        conservation_error = float(np.max(np.abs(after - before)))
        if not np.isfinite(remapped).all() or np.any(remapped < 0) or not math.isfinite(conservation_error):
            return failed_segment(index, "cell concentration inventory remap exceeded finite support")
        remaps.append({
            "elapsed_time_s": end_s,
            "from_geometry_state_sha256": canonical_digest(left_state),
            "to_geometry_state_sha256": canonical_digest(right_state),
            "pre_remap_cell_concentration_mol_m3": current_concentration.tolist(),
            "post_remap_cell_concentration_mol_m3": remapped.tolist(),
            "maximum_cell_inventory_change_mol": conservation_error,
            "basis": "instantaneous_cellwise_concentration_rescale_to_preserve_inventory_when_cell_volume_changes",
        })
        current_concentration = remapped
        previous_area = next_area

    ledger_keys = (
        "cumulative_mouth_inward_mol_m2",
        "cumulative_tip_inward_mol_m2",
        "cumulative_homogeneous_source_mol_m2",
        "cumulative_wall_inward_mol_m2",
    )
    totals = {key: np.zeros(len(req.species_ids), dtype=float) for key in ledger_keys}
    wall_by_cell_total = np.zeros((len(req.species_ids), req.cell_count), dtype=float)
    absolute_ledger_scale = np.zeros(len(req.species_ids), dtype=float)
    for segment_row in segment_results:
        output = segment_row["result"]
        for key in ledger_keys:
            final_ledger = np.asarray(output[key][-1], dtype=float)
            totals[key] += final_ledger
            absolute_ledger_scale += np.abs(final_ledger)
        wall_by_cell_total += np.asarray(output["cumulative_wall_inward_by_cell_mol_m2"][-1], dtype=float)
    initial_inventory = np.asarray(segment_results[0]["result"]["inventory_per_unit_area_mol_m2"][0], dtype=float)
    final_inventory = np.asarray(segment_results[-1]["result"]["inventory_per_unit_area_mol_m2"][-1], dtype=float)
    total_signed_sources = sum(totals.values(), np.zeros(len(req.species_ids), dtype=float))
    global_residual = final_inventory - initial_inventory - total_signed_sources
    global_scale = np.maximum(np.abs(final_inventory), np.abs(initial_inventory) + absolute_ledger_scale)
    global_limit = req.inventory_absolute_tolerance_mol_m2 + req.inventory_relative_tolerance * global_scale
    if not (
        np.isfinite(global_residual).all()
        and np.isfinite(global_limit).all()
        and all(np.isfinite(values).all() for values in totals.values())
        and np.isfinite(wall_by_cell_total).all()
    ):
        return base | {
            "status": "out_of_scope",
            "computed_segment_count": len(segment_results),
            "computed_prefix": segment_results,
            "reason": "campaign-wide inventory ledger exceeded finite numeric support",
        }
    if np.any(np.abs(global_residual) > global_limit):
        return base | {
            "status": "out_of_scope",
            "computed_segment_count": len(segment_results),
            "computed_prefix": segment_results,
            "global_species_inventory_balance_residual_mol_m2": global_residual.tolist(),
            "global_species_inventory_balance_limit_mol_m2": global_limit.tolist(),
            "reason": "campaign-wide inventory balance exceeded the declared tolerance",
        }

    return base | {
        "status": "computed",
        "segment_count": len(segment_results),
        "species_ids": list(req.species_ids),
        "segment_results": segment_results,
        "geometry_boundary_inventory_remaps": remaps,
        "final_cell_concentration_mol_m3": current_concentration.tolist(),
        "initial_inventory_per_unit_area_mol_m2": initial_inventory.tolist(),
        "final_inventory_per_unit_area_mol_m2": final_inventory.tolist(),
        "cumulative_transport_ledgers_mol_m2": {key: value.tolist() for key, value in totals.items()},
        "cumulative_wall_inward_by_cell_mol_m2": wall_by_cell_total.tolist(),
        "global_species_inventory_balance_residual_mol_m2": global_residual.tolist(),
        "global_species_inventory_balance_limit_mol_m2": global_limit.tolist(),
        "global_inventory_balance_within_declared_tolerance": True,
        "geometry_history_coupling": "caller_pinned_operator_split; fixed_geometry_within_each_segment",
        "notes": [
            "The recession/aperture history is an independent pinned input; transport output does not feed back into wall loss or update geometry.",
            "Each segment holds its left-knot geometry fixed. Geometry changes use a cellwise instantaneous concentration remap to preserve cell inventory; fast chemistry or unresolved within-step transients are not modeled.",
            "All external callbacks receive global campaign time after interval-local time translation. Geometry knots must coincide exactly with the declared transport output clock.",
        ],
    }


class CreviceTransportRecessionFeedback(Contract):
    """Reviewed material and geometry mapping for sequential transport-derived recession."""

    metal_species_id: str = Field(min_length=1)
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    one_metal_atom_per_species_mole_reviewed: bool
    all_selected_wall_flux_is_metal_dissolution_or_redeposition_reviewed: bool
    both_slit_faces_share_equal_recession_reviewed: bool = False
    supported_minimum_aperture_m: Positive
    supported_maximum_aperture_m: Positive
    aperture_feedback_mapping_reviewed: bool
    maximum_geometry_update_step_s: Positive | None = None
    geometry_update_step_sampling_reviewed: bool = False
    maximum_internal_segments: int = Field(default=1000, ge=1, le=10000)
    maximum_relative_aperture_change_per_segment: Positive | None = Field(default=None, le=1.0)
    adaptive_aperture_update_reviewed: bool = False
    callback_re_evaluation_deterministic_reviewed: bool = False
    maximum_adaptive_aperture_refinements: int = Field(default=100, ge=0, le=10000)
    within_segment_geometry_feedback_enabled: bool = False
    within_segment_geometry_feedback_reviewed: bool = False
    within_segment_feedback_convergence_reviewed: bool = False
    within_segment_hydraulic_feedback_enabled: bool = False
    within_segment_hydraulic_velocity_path_reviewed: bool = False
    maximum_within_segment_feedback_iterations: int = Field(default=8, ge=2, le=50)
    within_segment_relative_aperture_tolerance: Positive = Field(default=1e-5, le=0.1)
    within_segment_feedback_relaxation: Positive = Field(default=0.5, le=1.0)
    steady_hydraulic_recalculation_enabled: bool = False
    pressure_drop_history_Pa: tuple[float, ...] | None = Field(default=None, min_length=2, max_length=10000)
    pressure_history_interpolation: Literal["exact_requested_knots", "piecewise_linear"] = "exact_requested_knots"
    pressure_interpolation_reviewed: bool = False
    pressure_history_source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    fluid_property_source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    dynamic_viscosity_Pa_s: Positive | None = None
    density_kg_m3: Positive | None = None
    minimum_width_to_aperture_ratio: Positive = Field(default=20.0, ge=20.0, le=1000.0)
    maximum_reviewed_reynolds_number: Positive = Field(default=1000.0, le=1000.0)
    steady_hydraulics_and_pressure_alignment_reviewed: bool = False
    incompressible_newtonian_fluid_properties_reviewed: bool = False
    laminar_fully_developed_slit_assumption_reviewed: bool = False

    @model_validator(mode="after")
    def ordered_aperture_support(self):
        if self.supported_maximum_aperture_m <= self.supported_minimum_aperture_m:
            raise ValueError("supported aperture limits must be strictly ordered")
        if self.maximum_geometry_update_step_s is not None and not self.geometry_update_step_sampling_reviewed:
            raise ValueError("substepped geometry feedback requires explicit time-sampling review")
        if self.maximum_relative_aperture_change_per_segment is not None:
            if not self.adaptive_aperture_update_reviewed:
                raise ValueError("adaptive aperture refinement requires an explicit update-policy review")
            if not self.callback_re_evaluation_deterministic_reviewed:
                raise ValueError("adaptive aperture refinement requires reviewed deterministic callback reevaluation")
            if self.maximum_adaptive_aperture_refinements < 1:
                raise ValueError("adaptive aperture refinement requires a positive refinement budget")
        elif self.adaptive_aperture_update_reviewed or self.callback_re_evaluation_deterministic_reviewed:
            raise ValueError("adaptive aperture reviews require a declared relative aperture-change limit")
        if self.within_segment_geometry_feedback_enabled:
            if not (self.within_segment_geometry_feedback_reviewed and self.within_segment_feedback_convergence_reviewed):
                raise ValueError("within-segment geometry feedback requires separate mapping and convergence reviews")
            if self.maximum_geometry_update_step_s is None or self.maximum_relative_aperture_change_per_segment is None:
                raise ValueError("within-segment feedback requires time-step and relative aperture-change limits")
            if not self.callback_re_evaluation_deterministic_reviewed:
                raise ValueError("within-segment fixed-point iteration requires deterministic callback review")
            if self.maximum_within_segment_feedback_iterations < 2:
                raise ValueError("within-segment feedback needs at least two fixed-point iterations")
        elif (
            self.within_segment_geometry_feedback_reviewed
            or self.within_segment_feedback_convergence_reviewed
            or self.maximum_within_segment_feedback_iterations != 8
            or self.within_segment_relative_aperture_tolerance != 1e-5
            or self.within_segment_feedback_relaxation != 0.5
        ):
            raise ValueError("within-segment feedback controls require the feature to be enabled")
        if self.within_segment_hydraulic_feedback_enabled:
            if not self.within_segment_geometry_feedback_enabled:
                raise ValueError("within-segment hydraulic feedback requires within-segment geometry feedback")
            if not self.steady_hydraulic_recalculation_enabled:
                raise ValueError("within-segment hydraulic feedback requires steady slit hydraulics")
            if (self.pressure_history_interpolation != "piecewise_linear"
                    or not self.pressure_interpolation_reviewed):
                raise ValueError("within-segment hydraulic feedback requires reviewed piecewise-linear pressure support")
            if not self.within_segment_hydraulic_velocity_path_reviewed:
                raise ValueError("within-segment hydraulic feedback requires review of the endpoint-velocity interpolation model")
        elif self.within_segment_hydraulic_velocity_path_reviewed:
            raise ValueError("within-segment hydraulic velocity-path review requires the feature to be enabled")
        hydraulic_values = (
            self.pressure_drop_history_Pa,
            self.pressure_history_source_sha256,
            self.fluid_property_source_sha256,
            self.dynamic_viscosity_Pa_s,
            self.density_kg_m3,
        )
        if self.steady_hydraulic_recalculation_enabled:
            if any(value is None for value in hydraulic_values):
                raise ValueError("steady hydraulic recalculation requires pressure history, source digests and fluid properties")
            if not all((
                self.steady_hydraulics_and_pressure_alignment_reviewed,
                self.incompressible_newtonian_fluid_properties_reviewed,
                self.laminar_fully_developed_slit_assumption_reviewed,
            )):
                raise ValueError("steady hydraulic recalculation requires explicit model and time-alignment reviews")
            if self.pressure_history_interpolation == "piecewise_linear" and not self.pressure_interpolation_reviewed:
                raise ValueError("piecewise-linear pressure interpolation requires an explicit review")
            if self.pressure_history_interpolation == "exact_requested_knots" and self.pressure_interpolation_reviewed:
                raise ValueError("pressure interpolation review must match the selected interpolation policy")
        elif any(value is not None for value in hydraulic_values) or self.pressure_history_interpolation != "exact_requested_knots" or self.pressure_interpolation_reviewed or any((
            self.steady_hydraulics_and_pressure_alignment_reviewed,
            self.incompressible_newtonian_fluid_properties_reviewed,
            self.laminar_fully_developed_slit_assumption_reviewed,
        )):
            raise ValueError("hydraulic inputs and reviews require steady hydraulic recalculation to be enabled")
        return self


def solve_crevice_transport_recession_feedback(
    *,
    campaign_id: str,
    geometry: PlanarSlitGeometry,
    base_transport_request: RestrictedTransportRequest,
    feedback: CreviceTransportRecessionFeedback,
    geometry_aware_chemistry_provider: CreviceGeometryAwareAqueousChemistryProvider | None = None,
    geometry_aware_solid_deposition_provider: CreviceGeometryAwareSolidDepositionProvider | None = None,
    output_times_s: tuple[float, ...],
    exact_time_geometry_remap_reviewed: bool,
    fixed_geometry_within_interval_reviewed: bool,
    cell_inventory_remap_reviewed: bool,
    callback_global_time_mapping_reviewed: bool,
    reaction: Callable[[float, np.ndarray], np.ndarray],
    tip_surface_flux: Callable[[float, np.ndarray, float | None], np.ndarray] | None = None,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
) -> dict[str, Any]:
    """Sequentially feed each segment's integrated metal wall flux into the next slit aperture.

    By default, geometry is fixed within each transport segment. The optional
    within-segment fixed-point mode repeatedly solves transport on a guessed
    linear aperture path, derives a new path from its integrated metal wall
    flux, and commits only after the endpoint aperture converges. By default,
    the mode is restricted to diffusion/reaction transport without axial-flow
    feedback. A separate opt-in mode can couple it to caller-reviewed steady
    slit-flow endpoint solutions through a linear face-velocity path; this does
    not model transient momentum or simultaneous chemistry/flow.

    When ``geometry_aware_chemistry_provider`` is supplied, each inner fixed-
    point trial binds its declared balanced aqueous reaction extents to that
    trial's linear aperture path. It is mutually exclusive with ``reaction``
    and does not evolve solid phases or chemistry parameters.
    """
    if not isinstance(campaign_id, str) or not campaign_id.strip():
        raise ValueError("campaign_id must be a non-empty string")
    if any(isinstance(value, bool) for value in output_times_s):
        return {"campaign_id": campaign_id, "status": "needs_data", "reason": "Boolean values are not valid times"}
    try:
        times = tuple(float(value) for value in output_times_s)
    except (TypeError, ValueError, OverflowError):
        return {"campaign_id": campaign_id, "status": "needs_data", "reason": "Finite numeric output times are required"}
    req = base_transport_request
    if geometry_aware_chemistry_provider is not None and not isinstance(
        geometry_aware_chemistry_provider, CreviceGeometryAwareAqueousChemistryProvider
    ):
        return {"campaign_id": campaign_id, "status": "needs_data", "reason": "typed geometry-aware aqueous chemistry provider is required"}
    if geometry_aware_solid_deposition_provider is not None and not isinstance(
        geometry_aware_solid_deposition_provider, CreviceGeometryAwareSolidDepositionProvider
    ):
        return {"campaign_id": campaign_id, "status": "needs_data", "reason": "typed geometry-aware solid-deposition provider is required"}
    geometry_result = planar_slit_transport_geometry(geometry)
    aperture_refinements = []
    within_segment_feedback_history = []
    hydraulic_history = []
    payload = {
        "campaign_id": campaign_id,
        "geometry_input_sha256": geometry_result.get("input_sha256"),
        "transport_input_sha256": canonical_digest(req.model_dump(mode="json")),
        "feedback_input_sha256": canonical_digest(feedback.model_dump(mode="json")),
        "requested_output_times_s": list(req.output_times_s),
        "maximum_geometry_update_step_s": feedback.maximum_geometry_update_step_s,
        "maximum_internal_segments": feedback.maximum_internal_segments,
        "maximum_relative_aperture_change_per_segment": feedback.maximum_relative_aperture_change_per_segment,
        "maximum_adaptive_aperture_refinements": feedback.maximum_adaptive_aperture_refinements,
        "adaptive_aperture_refinements": aperture_refinements,
        "within_segment_geometry_feedback_enabled": feedback.within_segment_geometry_feedback_enabled,
        "within_segment_hydraulic_feedback_enabled": feedback.within_segment_hydraulic_feedback_enabled,
        "within_segment_hydraulic_velocity_path_reviewed": feedback.within_segment_hydraulic_velocity_path_reviewed,
        "maximum_within_segment_feedback_iterations": feedback.maximum_within_segment_feedback_iterations,
        "within_segment_relative_aperture_tolerance": feedback.within_segment_relative_aperture_tolerance,
        "within_segment_feedback_relaxation": feedback.within_segment_feedback_relaxation,
        "within_segment_feedback_history": within_segment_feedback_history,
        "steady_hydraulic_recalculation_enabled": feedback.steady_hydraulic_recalculation_enabled,
        "pressure_history_interpolation": feedback.pressure_history_interpolation,
        "pressure_interpolation_reviewed": feedback.pressure_interpolation_reviewed,
        "pressure_history_source_sha256": feedback.pressure_history_source_sha256,
        "fluid_property_source_sha256": feedback.fluid_property_source_sha256,
        "steady_hydraulic_history": hydraulic_history,
    }
    if geometry_aware_chemistry_provider is not None:
        provider_contract = geometry_aware_chemistry_provider.contract
        payload["geometry_aware_chemistry_provider"] = {
            "provider_id": provider_contract.provider_id,
            "provider_revision": provider_contract.provider_revision,
            "source_sha256": provider_contract.source_sha256,
            "configuration_sha256": provider_contract.configuration_sha256,
            "contract_sha256": canonical_digest(provider_contract.model_dump(mode="json")),
            "species_ids": [row.species_id for row in provider_contract.species],
            "reaction_ids": [row.reaction_id for row in provider_contract.reactions],
            "rate_basis": provider_contract.rate_basis,
        }
    if geometry_aware_solid_deposition_provider is not None:
        solid_contract = geometry_aware_solid_deposition_provider.contract
        payload["geometry_aware_solid_deposition_provider"] = {
            "provider_id": solid_contract.provider_id,
            "provider_revision": solid_contract.provider_revision,
            "provider_source_sha256": solid_contract.provider_source_sha256,
            "configuration_sha256": solid_contract.configuration_sha256,
            "contract_sha256": canonical_digest(solid_contract.model_dump(mode="json")),
            "aqueous_species_ids": list(geometry_aware_solid_deposition_provider.species_ids),
            "solid_phase_ids": list(geometry_aware_solid_deposition_provider.solid_phase_ids),
            "reaction_ids": list(geometry_aware_solid_deposition_provider.reaction_ids),
            "extent_basis": "net endpoint reaction extent in mol/m3 solution, operator-split at interval end",
        }
    if (
        reaction is None
        and geometry_aware_chemistry_provider is None
        and geometry_aware_solid_deposition_provider is not None
    ):
        def zero_homogeneous_reaction(_time_s, concentrations):
            return np.zeros_like(concentrations)

        zero_homogeneous_reaction.provider_id = "matintegrity.no_continuous_aqueous_reaction"
        zero_homogeneous_reaction.provider_revision = "1"
        zero_homogeneous_reaction.configuration_sha256 = canonical_digest({"source": "explicit_endpoint_solid_extent_only"})
        zero_homogeneous_reaction.reaction_ids = ()
        reaction = zero_homogeneous_reaction
    reviews = {
        "callback_global_time_mapping_reviewed": callback_global_time_mapping_reviewed,
        "one_metal_atom_per_species_mole_reviewed": feedback.one_metal_atom_per_species_mole_reviewed,
        "all_selected_wall_flux_is_metal_dissolution_or_redeposition_reviewed": feedback.all_selected_wall_flux_is_metal_dissolution_or_redeposition_reviewed,
        "aperture_feedback_mapping_reviewed": feedback.aperture_feedback_mapping_reviewed,
    }
    if feedback.within_segment_geometry_feedback_enabled:
        reviews.update({
            "within_segment_geometry_feedback_reviewed": feedback.within_segment_geometry_feedback_reviewed,
            "within_segment_feedback_convergence_reviewed": feedback.within_segment_feedback_convergence_reviewed,
        })
    else:
        reviews.update({
            "exact_time_geometry_remap_reviewed": exact_time_geometry_remap_reviewed,
            "fixed_geometry_within_interval_reviewed": fixed_geometry_within_interval_reviewed,
            "cell_inventory_remap_reviewed": cell_inventory_remap_reviewed,
        })
    if geometry_aware_chemistry_provider is not None:
        contract = geometry_aware_chemistry_provider.contract
        if not feedback.within_segment_geometry_feedback_enabled:
            return payload | {"status": "needs_data", "reason": "geometry-aware chemistry requires within-segment geometry fixed-point feedback"}
        if tuple(req.species_ids) != geometry_aware_chemistry_provider.species_ids:
            return payload | {"status": "out_of_scope", "reason": "provider species order does not match restricted transport order"}
        if times[0] < contract.valid_time_start_s or times[-1] > contract.valid_time_end_s:
            return payload | {"status": "out_of_scope", "reason": "campaign clock is outside chemistry provider support"}
        if geometry_aware_chemistry_provider.source_sha256 != contract.source_sha256:
            return payload | {"status": "out_of_scope", "reason": "geometry-aware chemistry provider source identity changed"}
        if reaction is not None:
            return payload | {"status": "needs_data", "reason": "supply either geometry-aware chemistry provider or legacy reaction callback, not both"}
    elif reaction is None:
        return payload | {"status": "needs_data", "reason": "a reaction callback or typed geometry-aware chemistry provider is required"}
    if geometry_aware_solid_deposition_provider is not None:
        solid_contract = geometry_aware_solid_deposition_provider.contract
        solid_cells = len(solid_contract.coverage_fraction_by_cell)
        if not feedback.within_segment_geometry_feedback_enabled:
            return payload | {"status": "needs_data", "reason": "solid deposition geometry feedback requires within-segment geometry fixed-point mode"}
        if tuple(req.species_ids) != geometry_aware_solid_deposition_provider.species_ids:
            return payload | {"status": "out_of_scope", "reason": "solid extent aqueous species order does not match transport"}
        if solid_cells != req.cell_count or not all(len(phase.initial_inventory_mol_m2_by_cell) == req.cell_count for phase in solid_contract.solid_phases):
            return payload | {"status": "out_of_scope", "reason": "solid inventory/coverage cell count does not match transport"}
        if solid_contract.reference_area_m2 != req.reference_cross_section_m2:
            return payload | {"status": "out_of_scope", "reason": "solid extent basis reference area does not match transport"}
        if solid_contract.deposition_side_count != geometry.reactive_broad_face_count:
            return payload | {"status": "out_of_scope", "reason": "solid deposition face count does not match slit geometry"}
        if tuple(solid_contract.coverage_fraction_by_cell) and len(solid_contract.coverage_fraction_by_cell) != len(geometry.cell_widths_m):
            return payload | {"status": "out_of_scope", "reason": "solid deposition coverage grid does not match slit geometry"}
        if times[0] < solid_contract.valid_time_start_s or times[-1] > solid_contract.valid_time_end_s:
            return payload | {"status": "out_of_scope", "reason": "campaign clock is outside solid extent provider support"}
        if geometry.aperture_m < solid_contract.minimum_aperture_m or geometry.aperture_m > solid_contract.maximum_aperture_m:
            return payload | {"status": "out_of_scope", "reason": "initial slit aperture is outside solid provider support"}
        if geometry_aware_chemistry_provider is not None:
            overlapping = set(geometry_aware_chemistry_provider.reaction_ids) & set(geometry_aware_solid_deposition_provider.reaction_ids)
            if overlapping:
                return payload | {"status": "out_of_scope", "reason": "aqueous and solid provider reaction IDs overlap; duplicate reaction extents are not accepted", "overlapping_reaction_ids": sorted(overlapping)}
        elif reaction is not None and getattr(reaction, "reaction_ids", None) is None:
            return payload | {"status": "needs_data", "reason": "a legacy reaction callback needs declared reaction_ids before it can be combined with solid extents"}
        elif reaction is not None:
            overlapping = set(getattr(reaction, "reaction_ids")) & set(geometry_aware_solid_deposition_provider.reaction_ids)
            if overlapping:
                return payload | {"status": "out_of_scope", "reason": "legacy and solid provider reaction IDs overlap", "overlapping_reaction_ids": sorted(overlapping)}
    if geometry_result.get("status") != "computed":
        return payload | {"status": geometry_result.get("status", "needs_data"), "reason": "Reviewed planar slit geometry is required"}
    if not all(reviews.values()):
        return payload | {"status": "needs_data", "missing_reviews": [key for key, value in reviews.items() if not value]}
    if (len(times) < 2 or not all(math.isfinite(value) for value in times) or times[0] != 0
        or any(right <= left for left, right in zip(times[:-1], times[1:], strict=True))):
        return payload | {"status": "needs_data", "reason": "Output times must start at zero and increase strictly"}
    if tuple(req.output_times_s) != times:
        return payload | {"status": "out_of_scope", "reason": "Feedback clock must exactly match the transport request clock"}
    if feedback.within_segment_geometry_feedback_enabled:
        if wall_surface_flux is None or req.wall_surface_provider_id is None:
            return payload | {"status": "needs_data", "reason": "Within-segment geometry feedback requires the declared metal wall-flux callback"}
        if (
            (feedback.steady_hydraulic_recalculation_enabled
             and not feedback.within_segment_hydraulic_feedback_enabled)
            or req.axial_advection_velocity_m_s is not None
            or req.axial_advection_provider_id is not None
            or axial_advection_velocity is not None
        ):
            return payload | {
                "status": "out_of_scope",
                "reason": "Within-segment geometry feedback allows only the reviewed steady-hydraulic endpoint-path mode; arbitrary caller advection providers are unsupported",
            }
        if any((
            req.cell_cross_section_history_m2 is not None,
            req.face_cross_section_history_m2 is not None,
            req.wall_area_per_volume_history_m2_m3 is not None,
        )):
            return payload | {"status": "out_of_scope", "reason": "Within-segment feedback constructs its own geometry histories"}
    requested_times = times
    if feedback.steady_hydraulic_recalculation_enabled:
        if req.axial_advection_velocity_m_s is not None or req.axial_advection_provider_id is not None or axial_advection_velocity is not None:
            return payload | {
                "status": "out_of_scope",
                "reason": "Steady hydraulic feedback supplies the advection field; caller-supplied velocity providers must be omitted",
            }
        if not req.axial_advection_and_flow_continuity_reviewed:
            return payload | {"status": "needs_data", "reason": "Restricted-transport flow continuity review is required for hydraulic feedback"}
        pressure_history = feedback.pressure_drop_history_Pa or ()
        if len(pressure_history) != len(requested_times):
            return payload | {"status": "out_of_scope", "reason": "Pressure samples must exactly match requested output times"}
        if (
            feedback.maximum_geometry_update_step_s is not None
            or feedback.maximum_relative_aperture_change_per_segment is not None
        ) and feedback.pressure_history_interpolation != "piecewise_linear":
            return payload | {
                "status": "needs_data",
                "reason": "Internal geometry updates require an explicitly selected piecewise-linear pressure history",
            }
        pressure_by_time = dict(zip(requested_times, pressure_history, strict=True))
        pressure_index_by_time = {time_s: index for index, time_s in enumerate(requested_times)}

        def pressure_sample_at(time_s: float):
            exact = pressure_by_time.get(time_s)
            if exact is not None:
                source_index = pressure_index_by_time[time_s]
                return exact, {
                    "interpolation_policy": "exact_requested_knots",
                    "source_start_time_s": time_s,
                    "source_end_time_s": time_s,
                    "source_start_index": source_index,
                    "source_end_index": source_index,
                    "interpolation_fraction": 0.0,
                }
            if feedback.pressure_history_interpolation != "piecewise_linear" or not feedback.pressure_interpolation_reviewed:
                return None, None
            for source_index, (left_time, right_time) in enumerate(zip(requested_times[:-1], requested_times[1:], strict=True)):
                if left_time < time_s < right_time:
                    fraction = (time_s - left_time) / (right_time - left_time)
                    left_pressure = float(pressure_history[source_index])
                    right_pressure = float(pressure_history[source_index + 1])
                    interpolated = left_pressure + fraction * (right_pressure - left_pressure)
                    if not math.isfinite(interpolated):
                        return None, None
                    return interpolated, {
                        "interpolation_policy": "piecewise_linear",
                        "source_start_time_s": left_time,
                        "source_end_time_s": right_time,
                        "source_start_index": source_index,
                        "source_end_index": source_index + 1,
                        "interpolation_fraction": fraction,
                    }
            return None, None

        hydraulic_static_lineage = {
            "pressure_history_source_sha256": feedback.pressure_history_source_sha256,
            "fluid_property_source_sha256": feedback.fluid_property_source_sha256,
            "dynamic_viscosity_Pa_s": feedback.dynamic_viscosity_Pa_s,
            "density_kg_m3": feedback.density_kg_m3,
            "steady_hydraulics_and_pressure_alignment_reviewed": feedback.steady_hydraulics_and_pressure_alignment_reviewed,
            "pressure_history_interpolation": feedback.pressure_history_interpolation,
            "pressure_interpolation_reviewed": feedback.pressure_interpolation_reviewed,
            "incompressible_newtonian_fluid_properties_reviewed": feedback.incompressible_newtonian_fluid_properties_reviewed,
            "laminar_fully_developed_slit_assumption_reviewed": feedback.laminar_fully_developed_slit_assumption_reviewed,
        }
    else:
        pressure_by_time = {}
        pressure_sample_at = lambda time_s: (None, None)
        hydraulic_static_lineage = {}
    maximum_step = feedback.maximum_geometry_update_step_s
    if maximum_step is not None:
        internal_times = [requested_times[0]]
        segment_count = 0
        for start_s, end_s in zip(requested_times[:-1], requested_times[1:], strict=True):
            ratio = (end_s - start_s) / maximum_step
            if not math.isfinite(ratio) or ratio > feedback.maximum_internal_segments:
                return payload | {
                    "status": "out_of_scope",
                    "reason": "Requested geometry update spacing exceeds the internal segment budget",
                    "maximum_internal_segments": feedback.maximum_internal_segments,
                }
            substeps = max(1, math.ceil(ratio))
            segment_count += substeps
            if segment_count > feedback.maximum_internal_segments:
                return payload | {
                    "status": "out_of_scope",
                    "reason": "Requested geometry update spacing exceeds the internal segment budget",
                    "maximum_internal_segments": feedback.maximum_internal_segments,
                }
            internal_times.extend(
                float(end_s if index == substeps else start_s + (end_s - start_s) * index / substeps)
                for index in range(1, substeps + 1)
            )
        times = tuple(internal_times)
        if len(req.species_ids) * req.cell_count * segment_count > 5_000_000:
            return payload | {
                "status": "out_of_scope",
                "reason": "Internal geometry-update transport record budget exceeded",
                "internal_segment_count": segment_count,
            }
        if geometry_aware_solid_deposition_provider is not None:
            extent_work = (
                2 * len(geometry_aware_solid_deposition_provider.reaction_ids)
                * req.cell_count * feedback.maximum_within_segment_feedback_iterations * segment_count
            )
            if extent_work > 10_000_000:
                return payload | {
                    "status": "out_of_scope",
                    "reason": "Solid endpoint extent reevaluation exceeds its bounded campaign work budget",
                    "estimated_extent_values": extent_work,
                    "maximum_extent_values": 10_000_000,
                }
    ncell = geometry_result["cell_count"]
    if (req.cell_count != ncell or req.cell_widths_m is None
        or tuple(req.cell_widths_m) != tuple(geometry.cell_widths_m)):
        return payload | {"status": "out_of_scope", "reason": "Slit and transport cell grids differ"}
    if (req.reference_cross_section_m2 is None or req.cell_cross_section_m2 is None
        or req.face_cross_section_m2 is None or req.wall_area_per_volume_m2_m3 is None):
        return payload | {"status": "needs_data", "reason": "Explicit variable-area geometry fields are required for feedback"}
    if not math.isclose(
        req.reference_cross_section_m2, geometry_result["axial_cross_section_m2"], rel_tol=1e-12
    ):
        return payload | {"status": "out_of_scope", "reason": "Transport reference area must match the initial slit cross section"}
    if feedback.metal_species_id not in req.species_ids:
        return payload | {"status": "out_of_scope", "reason": "Selected metal species is absent from transport"}
    if geometry.reactive_broad_face_count not in (1, 2):
        return payload | {"status": "out_of_scope", "reason": "At least one selected broad face is required for recession feedback"}
    if geometry.reactive_broad_face_count == 2 and not feedback.both_slit_faces_share_equal_recession_reviewed:
        return payload | {"status": "needs_data", "reason": "Equal recession on two opposing faces requires review"}
    if not (feedback.supported_minimum_aperture_m <= geometry.aperture_m <= feedback.supported_maximum_aperture_m):
        return payload | {"status": "out_of_scope", "reason": "Initial aperture is outside declared provider support"}
    if not req.variable_area_one_dimensional_reduction_reviewed:
        return payload | {"status": "needs_data", "reason": "Variable-area transport reduction requires review"}
    if req.axial_advection_provider_id and req.axial_advection_velocity_m_s is None and axial_advection_velocity is None:
        return payload | {"status": "needs_data", "reason": "Declared advection callback is unavailable"}
    if req.wall_surface_provider_id and wall_surface_flux is None:
        return payload | {"status": "needs_data", "reason": "Declared wall-flux callback is unavailable"}
    if req.tip_surface_provider_id and tip_surface_flux is None:
        return payload | {"status": "needs_data", "reason": "Declared tip-flux callback is unavailable"}
    if req.activity_provider_id and activity_coefficients is None:
        return payload | {"status": "needs_data", "reason": "Declared activity callback is unavailable"}

    species_index = req.species_ids.index(feedback.metal_species_id)
    area = geometry_result["axial_cross_section_m2"]
    expected_area = geometry.aperture_m * geometry.transverse_width_m
    if (not math.isclose(area, expected_area, rel_tol=1e-12)
        or not np.allclose(req.cell_cross_section_m2, expected_area, rtol=1e-10, atol=0.0)
        or not np.allclose(req.face_cross_section_m2, expected_area, rtol=1e-10, atol=0.0)
        or not np.allclose(req.wall_area_per_volume_m2_m3,
                           geometry.reactive_broad_face_count / geometry.aperture_m,
                           rtol=1e-10, atol=0.0)):
        return payload | {"status": "out_of_scope", "reason": "Initial cell cross section does not match slit geometry"}
    if req.wall_surface_provider_id is not None and not req.wall_surface_flux_basis_reviewed:
        return payload | {"status": "needs_data", "reason": "Wall-surface flux basis requires review"}
    aperture = [geometry.aperture_m] * ncell
    concentration = np.asarray(req.initial_concentration_mol_m3, dtype=float)
    segments = []
    remaps = []
    cumulative_recession = np.zeros(ncell, dtype=float)
    solid_inventory_initial_by_phase = (
        {
            phase.phase_id: np.asarray(phase.initial_inventory_mol_m2_by_cell, dtype=float)
            for phase in geometry_aware_solid_deposition_provider.contract.solid_phases
        }
        if geometry_aware_solid_deposition_provider is not None else {}
    )
    solid_inventory_by_phase = {
        phase_id: values.copy() for phase_id, values in solid_inventory_initial_by_phase.items()
    }
    solid_inventory_history = ([{
        "elapsed_time_s": float(times[0]),
        "solid_inventory_mol_m2_by_phase_cell": {
            phase_id: values.tolist() for phase_id, values in solid_inventory_by_phase.items()
        },
    }] if solid_inventory_by_phase else [])
    initial_inventory = np.sum(
        concentration * np.asarray(geometry.cell_widths_m, dtype=float)[None, :], axis=1
    )
    total_ledgers = {key: np.zeros(len(req.species_ids), dtype=float) for key in (
        "cumulative_mouth_inward_mol_m2", "cumulative_tip_inward_mol_m2",
        "cumulative_homogeneous_source_mol_m2", "cumulative_wall_inward_mol_m2",
    )}
    requested_snapshots = [{
        "elapsed_time_s": requested_times[0],
        "cell_aperture_m": list(aperture),
        "cell_concentration_mol_m3": concentration.tolist(),
        "cumulative_signed_cell_average_recession_m": cumulative_recession.tolist(),
        "solid_inventory_mol_m2_by_phase_cell": {
            phase_id: values.tolist() for phase_id, values in solid_inventory_by_phase.items()
        },
        "cumulative_transport_ledgers_mol_m2": {
            key: value.tolist() for key, value in total_ledgers.items()
        },
    }]

    def shifted(callback, start):
        return _shift_callback(callback, start)

    current_hydraulic_result = None
    if feedback.steady_hydraulic_recalculation_enabled:
        initial_pressure = pressure_by_time.get(requested_times[0])
        initial_hydraulic_request = PlanarSlitHydraulicFlow(
            flow_id=f"{campaign_id}:steady-hydraulics:initial",
            geometry_source_sha256=canonical_digest({
                "campaign_id": campaign_id,
                "elapsed_time_s": requested_times[0],
                "aperture_m": aperture,
                "pressure_history_source_sha256": feedback.pressure_history_source_sha256,
            }),
            cell_widths_m=geometry.cell_widths_m,
            cell_aperture_m=tuple(aperture),
            transverse_width_m=geometry.transverse_width_m,
            fluid_property_source_sha256=feedback.fluid_property_source_sha256,
            pressure_drop_Pa=initial_pressure,
            dynamic_viscosity_Pa_s=feedback.dynamic_viscosity_Pa_s,
            density_kg_m3=feedback.density_kg_m3,
            minimum_width_to_aperture_ratio=feedback.minimum_width_to_aperture_ratio,
            maximum_reviewed_reynolds_number=feedback.maximum_reviewed_reynolds_number,
            geometry_and_boundary_pressures_reviewed=True,
            incompressible_newtonian_fluid_properties_reviewed=True,
            laminar_fully_developed_slit_assumption_reviewed=True,
        )
        current_hydraulic_result = evaluate_planar_slit_hydraulic_flow(initial_hydraulic_request)
        if current_hydraulic_result.get("status") != "computed":
            return payload | {
                "status": current_hydraulic_result.get("status", "out_of_scope"),
                "uncommitted_hydraulic_result": current_hydraulic_result,
                "reason": "Initial steady slit flow could not be calculated",
            }
        hydraulic_history.append({
            "state_index": 0,
            "elapsed_time_s": requested_times[0],
            "pressure_drop_Pa": initial_pressure,
            "aperture_m": list(aperture),
            "flow_input_sha256": canonical_digest(initial_hydraulic_request.model_dump(mode="json")),
            "flow_result_sha256": canonical_digest(current_hydraulic_result),
            **hydraulic_static_lineage,
            "result": current_hydraulic_result,
        })

    pending_segments = list(zip(times[:-1], times[1:], strict=True))
    accepted_internal_times = [times[0]]
    index = 0
    while index < len(pending_segments):
        start, end = pending_segments[index]
        cross_sections = [value * geometry.transverse_width_m for value in aperture]
        faces = [cross_sections[0]]
        for i in range(1, ncell):
            left_half = geometry.cell_widths_m[i - 1] / 2
            right_half = geometry.cell_widths_m[i] / 2
            faces.append((cross_sections[i - 1] * right_half + cross_sections[i] * left_half) / (left_half + right_half))
        faces.append(cross_sections[-1])
        wall_density = [geometry.reactive_broad_face_count / value for value in aperture]
        updates = {
            "simulation_id": f"{req.simulation_id}:feedback-{index:04d}",
            "output_times_s": (0.0, float(end - start)),
            "initial_concentration_mol_m3": tuple(tuple(float(v) for v in row) for row in concentration),
            "cell_cross_section_m2": tuple(cross_sections),
            "face_cross_section_m2": tuple(faces),
            "wall_area_per_volume_m2_m3": tuple(wall_density),
        }
        if current_hydraulic_result is not None:
            flow_contract = current_hydraulic_result["transport_coupling_contract"]
            updates.update({
                "axial_advection_velocity_m_s": tuple(current_hydraulic_result["transport_face_velocity_m_s"]),
                "axial_advection_provider_id": flow_contract["provider_id"],
                "axial_advection_configuration_sha256": flow_contract["configuration_sha256"],
                "time_varying_axial_advection_reviewed": False,
            })
        if req.mouth_concentration_history_mol_m3 is not None:
            mouth_history = np.asarray(req.mouth_concentration_history_mol_m3, dtype=float)
            interpolated_mouth = tuple(
                tuple(
                    float(np.interp(sample_time, requested_times, mouth_history[:, species]))
                    for species in range(mouth_history.shape[1])
                )
                for sample_time in (start, end)
            )
            updates["mouth_concentration_mol_m3"] = interpolated_mouth[0]
            updates["mouth_concentration_history_mol_m3"] = interpolated_mouth
        area_ratios = np.asarray([
            geometry.reactive_broad_face_count * geometry.transverse_width_m * width / area
            for width in geometry.cell_widths_m
        ])
        fixed_point_records = []
        fixed_point_hydraulic_path = None
        accepted_solid_deposition_result = None
        if feedback.within_segment_geometry_feedback_enabled:
            start_aperture = np.asarray(aperture, dtype=float)
            guessed_end_aperture = start_aperture.copy()
            segment_req = None
            segment = None
            converged = False
            accepted_solid_deposition_result = None
            for feedback_iteration in range(feedback.maximum_within_segment_feedback_iterations):
                guessed_cross_sections = guessed_end_aperture * geometry.transverse_width_m
                guessed_faces = [float(guessed_cross_sections[0])]
                for cell_index in range(1, ncell):
                    left_half = geometry.cell_widths_m[cell_index - 1] / 2
                    right_half = geometry.cell_widths_m[cell_index] / 2
                    guessed_faces.append(float(
                        (guessed_cross_sections[cell_index - 1] * right_half
                         + guessed_cross_sections[cell_index] * left_half)
                        / (left_half + right_half)
                    ))
                guessed_faces.append(float(guessed_cross_sections[-1]))
                local_callback = None
                hydraulic_path_records = None
                if feedback.within_segment_hydraulic_feedback_enabled:
                    if current_hydraulic_result is None:
                        return payload | {
                            "status": "needs_data",
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "reason": "Within-segment hydraulic feedback has no accepted start-state flow result",
                        }
                    end_pressure, end_pressure_lineage = pressure_sample_at(end)
                    if end_pressure is None:
                        return payload | {
                            "status": "out_of_scope",
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "reason": "Within-segment hydraulic trial endpoint has no supported pressure sample",
                        }
                    end_hydraulic_request = PlanarSlitHydraulicFlow(
                        flow_id=f"{campaign_id}:steady-hydraulics:{index:05d}:fixed-point-{feedback_iteration:03d}",
                        geometry_source_sha256=canonical_digest({
                            "campaign_id": campaign_id,
                            "segment_start_s": start,
                            "segment_end_s": end,
                            "guessed_end_aperture_m": guessed_end_aperture.tolist(),
                            "pressure_drop_Pa": end_pressure,
                            "pressure_history_source_sha256": feedback.pressure_history_source_sha256,
                            "feedback_iteration": feedback_iteration,
                        }),
                        cell_widths_m=geometry.cell_widths_m,
                        cell_aperture_m=tuple(float(value) for value in guessed_end_aperture),
                        transverse_width_m=geometry.transverse_width_m,
                        fluid_property_source_sha256=feedback.fluid_property_source_sha256,
                        pressure_drop_Pa=end_pressure,
                        dynamic_viscosity_Pa_s=feedback.dynamic_viscosity_Pa_s,
                        density_kg_m3=feedback.density_kg_m3,
                        minimum_width_to_aperture_ratio=feedback.minimum_width_to_aperture_ratio,
                        maximum_reviewed_reynolds_number=feedback.maximum_reviewed_reynolds_number,
                        geometry_and_boundary_pressures_reviewed=True,
                        incompressible_newtonian_fluid_properties_reviewed=True,
                        laminar_fully_developed_slit_assumption_reviewed=True,
                    )
                    end_hydraulic_result = evaluate_planar_slit_hydraulic_flow(end_hydraulic_request)
                    if end_hydraulic_result.get("status") != "computed":
                        return payload | {
                            "status": end_hydraulic_result.get("status", "out_of_scope"),
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "uncommitted_hydraulic_result": end_hydraulic_result,
                            "within_segment_feedback_iterations": fixed_point_records,
                            "reason": "Steady slit hydraulics could not be evaluated at the guessed end aperture",
                        }
                    start_velocity = np.asarray(
                        current_hydraulic_result["transport_face_velocity_m_s"], dtype=float
                    )
                    end_velocity = np.asarray(
                        end_hydraulic_result["transport_face_velocity_m_s"], dtype=float
                    )
                    if (start_velocity.shape != (ncell + 1,) or end_velocity.shape != (ncell + 1,)
                            or not np.isfinite(start_velocity).all() or not np.isfinite(end_velocity).all()):
                        return payload | {
                            "status": "out_of_scope",
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "reason": "Endpoint hydraulic velocities are missing or misaligned",
                        }
                    if (np.any(start_velocity < 0.0) or np.any(end_velocity < 0.0)) and not (
                            req.axial_flow_reversal_and_tip_boundary_reviewed
                            and req.tip_advection_inflow_mol_m3 is not None):
                        return payload | {
                            "status": "needs_data",
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "reason": "Endpoint hydraulic flow reversal requires reviewed distal inflow concentrations",
                        }
                    start_flow_digest = canonical_digest(current_hydraulic_result)
                    end_flow_digest = canonical_digest(end_hydraulic_result)
                    velocity_path = PlanarSlitEndpointVelocityPath(
                        path_id=f"{campaign_id}:velocity-path:{index:05d}:iteration-{feedback_iteration:03d}",
                        global_start_time_s=start,
                        global_end_time_s=end,
                        start_face_velocity_m_s=tuple(float(value) for value in start_velocity),
                        end_face_velocity_m_s=tuple(float(value) for value in end_velocity),
                        start_hydraulic_result_sha256=start_flow_digest,
                        end_hydraulic_input_sha256=canonical_digest(end_hydraulic_request.model_dump(mode="json")),
                        end_hydraulic_result_sha256=end_flow_digest,
                        end_pressure_drop_Pa=end_pressure,
                        pressure_history_source_sha256=feedback.pressure_history_source_sha256,
                        fluid_property_source_sha256=feedback.fluid_property_source_sha256,
                        end_pressure_interpolation_lineage=end_pressure_lineage,
                        endpoint_velocity_interpolation_reviewed=feedback.within_segment_hydraulic_velocity_path_reviewed,
                    )
                    local_callback = velocity_path
                    hydraulic_provider_id = velocity_path.provider_id
                    hydraulic_configuration_digest = velocity_path.configuration_sha256
                    path_source_digest = velocity_path.source_sha256
                    hydraulic_path_records = {
                        **velocity_path.model_dump(mode="json"),
                        "provider_id": hydraulic_provider_id,
                        "configuration_sha256": hydraulic_configuration_digest,
                        "source_sha256": path_source_digest,
                        "start_time_s": velocity_path.global_start_time_s,
                        "end_time_s": velocity_path.global_end_time_s,
                        "interpolation_policy": "piecewise_linear_between_endpoint_steady_face_velocities",
                        "velocity_path_reviewed": feedback.within_segment_hydraulic_velocity_path_reviewed,
                    }
                    fixed_point_hydraulic_path = hydraulic_path_records
                local_updates = dict(updates) | {
                    "cell_cross_section_history_m2": (
                        tuple(float(value) for value in cross_sections),
                        tuple(float(value) for value in guessed_cross_sections),
                    ),
                    "face_cross_section_history_m2": (
                        tuple(float(value) for value in faces),
                        tuple(guessed_faces),
                    ),
                    "wall_area_per_volume_history_m2_m3": (
                        tuple(float(value) for value in wall_density),
                        tuple(float(geometry.reactive_broad_face_count / value) for value in guessed_end_aperture),
                    ),
                    "moving_geometry_interpolation_reviewed": True,
                    "moving_geometry_inventory_dilution_reviewed": True,
                    "moving_geometry_provider_id": "matintegrity.crevice_transport_recession_feedback",
                    "moving_geometry_configuration_sha256": canonical_digest({
                        "campaign_id": campaign_id,
                        "segment_start_s": start,
                        "segment_end_s": end,
                        "feedback_iteration": feedback_iteration,
                        "guessed_end_aperture_m": guessed_end_aperture.tolist(),
                    }),
                    "moving_geometry_time_basis_id": f"{campaign_id}:segment-{index:05d}:local_elapsed_s",
                }
                if hydraulic_path_records is not None:
                    local_updates.update({
                        "axial_advection_velocity_m_s": None,
                        "axial_advection_provider_id": hydraulic_path_records["provider_id"],
                        "axial_advection_configuration_sha256": hydraulic_path_records["configuration_sha256"],
                        "axial_advection_source_result_sha256": hydraulic_path_records["source_sha256"],
                        "time_varying_axial_advection_reviewed": True,
                    })
                try:
                    segment_req = RestrictedTransportRequest.model_validate(
                        req.model_dump(mode="python") | local_updates
                    )
                except (TypeError, ValueError) as error:
                    return payload | {
                        "status": "needs_data",
                        "failed_segment_index": index,
                        "computed_prefix": segments,
                        "reason": "Within-segment geometry history failed its transport contract",
                        "contract_error": str(error),
                    }
                trial_reaction = reaction
                if geometry_aware_chemistry_provider is not None:
                    try:
                        trial_reaction = geometry_aware_chemistry_provider.bind_linear_aperture_path(
                            start, end, start_aperture, guessed_end_aperture
                        )
                    except GeometryAwareChemistryEvaluationError as error:
                        return payload | {
                            "status": "out_of_scope",
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "within_segment_feedback_iterations": fixed_point_records,
                            "geometry_aware_chemistry_failure": error.as_dict(),
                            "reason": "geometry-aware chemistry provider rejected the guessed aperture path",
                        }
                trial_reaction_provider_id = getattr(trial_reaction, "provider_id", None)
                trial_reaction_configuration = getattr(trial_reaction, "configuration_sha256", None)
                if trial_reaction_provider_id is not None and trial_reaction_configuration is not None:
                    try:
                        segment_req = RestrictedTransportRequest.model_validate(
                            segment_req.model_dump(mode="python") | {
                                "reaction_provider_id": trial_reaction_provider_id,
                                "reaction_configuration_sha256": trial_reaction_configuration,
                            }
                        )
                    except (TypeError, ValueError) as error:
                        return payload | {
                            "status": "needs_data",
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "within_segment_feedback_iterations": fixed_point_records,
                            "reason": "geometry-aware reaction identity could not be bound to the transport contract",
                            "contract_error": str(error),
                        }
                try:
                    segment = solve_restricted_transport(
                        segment_req,
                        reaction=shifted(trial_reaction, start),
                        tip_surface_flux=shifted(tip_surface_flux, start),
                        wall_surface_flux=shifted(wall_surface_flux, start),
                        activity_coefficients=shifted(activity_coefficients, start),
                        axial_advection_velocity=local_callback,
                    )
                except GeometryAwareChemistryEvaluationError as error:
                    return payload | {
                        "status": "out_of_scope",
                        "failed_segment_index": index,
                        "computed_prefix": segments,
                        "within_segment_feedback_iterations": fixed_point_records,
                        "geometry_aware_chemistry_failure": error.as_dict(),
                        "reason": "geometry-aware chemistry callback failed; current segment remains uncommitted",
                    }
                if segment.get("status") != "computed":
                    return payload | {
                        "status": segment.get("status", "out_of_scope"),
                        "failed_segment_index": index,
                        "computed_prefix": segments,
                        "failed_segment_result": segment,
                    }
                try:
                    trial_wall_ledger = np.asarray(
                        segment.get("cumulative_wall_inward_by_cell_mol_m2"), dtype=float
                    )
                except (TypeError, ValueError):
                    trial_wall_ledger = np.empty((0,))
                if trial_wall_ledger.shape != (2, len(req.species_ids), ncell) or not np.isfinite(trial_wall_ledger).all():
                    return payload | {
                        "status": "needs_data",
                        "failed_segment_index": index,
                        "computed_prefix": segments,
                        "reason": "Within-segment fixed-point iteration requires a finite cellwise wall-metal ledger",
                    }
                trial_metal_by_cell = trial_wall_ledger[-1, species_index]
                trial_increment = (
                    trial_metal_by_cell * feedback.metal_molar_mass_kg_mol
                    / feedback.metal_density_kg_m3 / np.asarray(area_ratios)
                )
                trial_solid_deposition_result = None
                if geometry_aware_solid_deposition_provider is not None:
                    try:
                        endpoint_fields = np.asarray(segment.get("concentration_mol_m3"), dtype=float)
                        if endpoint_fields.shape != (2, len(req.species_ids), ncell) or not np.isfinite(endpoint_fields).all():
                            raise ValueError("trial transport endpoint concentration history is invalid")
                        guessed_volume_per_area = (
                            guessed_end_aperture * geometry.transverse_width_m
                            / float(req.reference_cross_section_m2)
                            * np.asarray(geometry.cell_widths_m, dtype=float)
                        )
                        trial_solid_deposition_result = geometry_aware_solid_deposition_provider.evaluate_endpoint(
                            start_time_s=start,
                            end_time_s=end,
                            transport_endpoint_concentration_mol_m3=endpoint_fields[-1],
                            start_aperture_m=start_aperture,
                            guessed_end_aperture_m=guessed_end_aperture,
                            current_solid_inventory_mol_m2_by_phase=solid_inventory_by_phase,
                            cell_volume_per_reference_area_m=guessed_volume_per_area,
                            cell_width_m=np.asarray(geometry.cell_widths_m, dtype=float),
                            transverse_width_m=geometry.transverse_width_m,
                            metal_recession_increment_m_by_cell=trial_increment,
                        )
                    except Exception as error:
                        failure = error.as_dict() if isinstance(error, GeometryAwareSolidExtentEvaluationError) else {
                            "provider_id": geometry_aware_solid_deposition_provider.provider_id,
                            "elapsed_time_s": end,
                            "failure_type": type(error).__name__,
                            "reason": "trial transport state could not be mapped to the solid extent contract",
                        }
                        return payload | {
                            "status": "out_of_scope",
                            "failed_segment_index": index,
                            "computed_prefix": segments,
                            "within_segment_feedback_iterations": fixed_point_records,
                            "geometry_aware_solid_extent_failure": failure,
                            "reason": "solid extent provider failed or exceeded inventory/geometry support; trial remains uncommitted",
                        }
                predicted_end_aperture = np.asarray(
                    trial_solid_deposition_result["predicted_end_aperture_m_by_cell"]
                    if trial_solid_deposition_result is not None
                    else start_aperture + geometry.reactive_broad_face_count * trial_increment,
                    dtype=float,
                )
                if (not np.isfinite(predicted_end_aperture).all()
                        or np.any(predicted_end_aperture < feedback.supported_minimum_aperture_m)
                        or np.any(predicted_end_aperture > feedback.supported_maximum_aperture_m)):
                    return payload | {
                        "status": "out_of_scope",
                        "failed_segment_index": index,
                        "computed_prefix": segments,
                        "uncommitted_predicted_end_aperture_m": predicted_end_aperture.tolist(),
                        "within_segment_feedback_iterations": fixed_point_records,
                        "reason": "Within-segment feedback aperture left declared provider support",
                    }
                residual = np.abs(predicted_end_aperture - guessed_end_aperture) / np.maximum(
                    np.maximum(np.abs(predicted_end_aperture), np.abs(guessed_end_aperture)),
                    feedback.supported_minimum_aperture_m,
                )
                relative_residual = float(np.max(residual))
                iteration_record = {
                    "iteration": feedback_iteration,
                    "guessed_end_aperture_m": guessed_end_aperture.tolist(),
                    "predicted_end_aperture_m": predicted_end_aperture.tolist(),
                    "maximum_relative_aperture_residual": relative_residual,
                    "transport_input_sha256": canonical_digest(segment_req.model_dump(mode="json")),
                    "transport_result_sha256": canonical_digest(segment),
                    "within_segment_hydraulic_path": hydraulic_path_records,
                    "solid_deposition_endpoint_sha256": (
                        trial_solid_deposition_result["endpoint_evaluation_sha256"]
                        if trial_solid_deposition_result is not None else None
                    ),
                    "solid_volume_change_m3_m2_by_cell": (
                        trial_solid_deposition_result["solid_volume_change_m3_m2_by_cell"]
                        if trial_solid_deposition_result is not None else None
                    ),
                    "relaxation_factor": feedback.within_segment_feedback_relaxation,
                    "segment_committed": False,
                }
                fixed_point_records.append(iteration_record)
                within_segment_feedback_history.append({
                    "segment_index": index,
                    "global_start_time_s": start,
                    "global_end_time_s": end,
                    **iteration_record,
                })
                if relative_residual <= feedback.within_segment_relative_aperture_tolerance:
                    next_aperture = predicted_end_aperture
                    accepted_solid_deposition_result = trial_solid_deposition_result
                    converged = True
                    break
                guessed_end_aperture = guessed_end_aperture + feedback.within_segment_feedback_relaxation * (
                    predicted_end_aperture - guessed_end_aperture
                )
            if not converged:
                return payload | {
                    "status": "out_of_scope",
                    "failed_segment_index": index,
                    "computed_prefix": segments,
                    "within_segment_feedback_iterations": fixed_point_records,
                    "out_of_scope_reason": "within-segment aperture fixed-point iteration did not converge within its declared budget",
                }
        else:
            segment_req = RestrictedTransportRequest.model_validate(req.model_dump(mode="python") | updates)
            segment = solve_restricted_transport(
                segment_req,
                reaction=shifted(reaction, start),
                tip_surface_flux=shifted(tip_surface_flux, start),
                wall_surface_flux=shifted(wall_surface_flux, start),
                activity_coefficients=shifted(activity_coefficients, start),
                axial_advection_velocity=shifted(axial_advection_velocity, start),
            )
        if segment.get("status") != "computed":
            return payload | {"status": segment.get("status", "out_of_scope"), "failed_segment_index": index,
                              "computed_prefix": segments, "failed_segment_result": segment}
        wall_rows = segment.get("cumulative_wall_inward_by_cell_mol_m2")
        try:
            wall_ledger = np.asarray(wall_rows, dtype=float)
        except (TypeError, ValueError):
            wall_ledger = np.empty((0,))
        if wall_ledger.shape != (2, len(req.species_ids), ncell) or not np.isfinite(wall_ledger).all():
            return payload | {"status": "needs_data", "failed_segment_index": index,
                              "computed_prefix": segments, "reason": "Cellwise signed wall-metal ledger is missing"}
        metal_by_cell = wall_ledger[-1, species_index]
        # Transport ledger is mol/reference axial area. Divide each cell amount by
        # its physical reactive-wall/reference-area ratio to obtain mean recession.
        increment = metal_by_cell * feedback.metal_molar_mass_kg_mol / feedback.metal_density_kg_m3 / area_ratios
        # Positive signed recession denotes metal removal and therefore opens
        # the slit; negative recession denotes deposition and narrows it.
        next_aperture = np.asarray(aperture) + geometry.reactive_broad_face_count * increment
        if feedback.within_segment_geometry_feedback_enabled:
            if geometry_aware_solid_deposition_provider is not None:
                if accepted_solid_deposition_result is None:
                    return payload | {
                        "status": "needs_data",
                        "failed_segment_index": index,
                        "computed_prefix": segments,
                        "reason": "converged solid extent result is unavailable for geometry commitment",
                    }
                next_aperture = next_aperture - np.asarray(
                    accepted_solid_deposition_result["equivalent_mean_aperture_loss_m_by_cell"],
                    dtype=float,
                )
            fixed_point_error = np.max(np.abs(next_aperture - guessed_end_aperture) / np.maximum(
                np.maximum(np.abs(next_aperture), np.abs(guessed_end_aperture)),
                feedback.supported_minimum_aperture_m,
            ))
            if fixed_point_error > feedback.within_segment_relative_aperture_tolerance:
                return payload | {
                    "status": "out_of_scope",
                    "failed_segment_index": index,
                    "computed_prefix": segments,
                    "within_segment_feedback_iterations": fixed_point_records,
                    "out_of_scope_reason": "committed transport segment does not match the converged aperture iterate",
                }
        if not np.isfinite(next_aperture).all():
            return payload | {"status": "out_of_scope", "failed_segment_index": index,
                              "computed_prefix": segments, "reason": "Feedback aperture exceeded finite numeric support"}
        relative_aperture_change = np.abs(next_aperture - np.asarray(aperture)) / np.asarray(aperture)
        maximum_relative_aperture_change = float(np.max(relative_aperture_change))
        aperture_change_limit = feedback.maximum_relative_aperture_change_per_segment
        if aperture_change_limit is not None and maximum_relative_aperture_change > aperture_change_limit:
            if len(aperture_refinements) >= feedback.maximum_adaptive_aperture_refinements:
                return payload | {
                    "status": "out_of_scope",
                    "failed_segment_index": index,
                    "computed_prefix": segments,
                    "adaptive_aperture_refinements": aperture_refinements,
                    "out_of_scope_reason": "adaptive aperture refinement budget exceeded before the segment could be committed",
                }
            middle = start + 0.5 * (end - start)
            if not start < middle < end:
                return payload | {
                    "status": "out_of_scope",
                    "failed_segment_index": index,
                    "computed_prefix": segments,
                    "adaptive_aperture_refinements": aperture_refinements,
                    "out_of_scope_reason": "time interval cannot be bisected at floating-point resolution",
                }
            if (len(pending_segments) + 1 > feedback.maximum_internal_segments
                or len(req.species_ids) * req.cell_count * (len(pending_segments) + 1) > 5_000_000
                or (
                    geometry_aware_solid_deposition_provider is not None
                    and 2 * len(geometry_aware_solid_deposition_provider.reaction_ids)
                    * req.cell_count * feedback.maximum_within_segment_feedback_iterations
                    * (len(pending_segments) + 1) > 10_000_000
                )):
                return payload | {
                    "status": "out_of_scope",
                    "failed_segment_index": index,
                    "computed_prefix": segments,
                    "adaptive_aperture_refinements": aperture_refinements,
                    "out_of_scope_reason": "adaptive aperture refinement exceeds the internal segment or transport-record budget",
                }
            aperture_refinements.append({
                "rejected_trial_index": len(aperture_refinements),
                "global_start_time_s": start,
                "global_end_time_s": end,
                "maximum_relative_aperture_change": maximum_relative_aperture_change,
                "caller_limit": aperture_change_limit,
                "proposed_split_time_s": middle,
                "transport_result_sha256": canonical_digest(segment),
                "uncommitted_aperture_m": list(aperture),
                "trial_next_aperture_m": next_aperture.tolist(),
                "within_segment_feedback_iterations": fixed_point_records,
            })
            pending_segments[index:index + 1] = [(start, middle), (middle, end)]
            continue
        if (np.any(next_aperture < feedback.supported_minimum_aperture_m)
            or np.any(next_aperture > feedback.supported_maximum_aperture_m)):
            return payload | {"status": "out_of_scope", "failed_segment_index": index,
                              "computed_prefix": segments, "reason": "Feedback aperture left declared provider support"}
        pending_hydraulic_result = None
        pending_hydraulic_record = None
        if feedback.steady_hydraulic_recalculation_enabled:
            pressure_drop, pressure_interpolation_lineage = pressure_sample_at(end)
            if pressure_drop is None:
                return payload | {
                    "status": "out_of_scope", "failed_segment_index": index,
                    "computed_prefix": segments,
                    "reason": "Accepted segment endpoint has no supported pressure sample or interpolation bracket",
                }
            hydraulic_request = PlanarSlitHydraulicFlow(
                flow_id=f"{campaign_id}:steady-hydraulics:{index:05d}",
                geometry_source_sha256=canonical_digest({
                    "campaign_id": campaign_id,
                    "segment_start_s": start,
                    "segment_end_s": end,
                    "aperture_m": aperture,
                    "pressure_history_source_sha256": feedback.pressure_history_source_sha256,
                }),
                cell_widths_m=geometry.cell_widths_m,
                cell_aperture_m=tuple(float(value) for value in next_aperture),
                transverse_width_m=geometry.transverse_width_m,
                fluid_property_source_sha256=feedback.fluid_property_source_sha256,
                pressure_drop_Pa=pressure_drop,
                dynamic_viscosity_Pa_s=feedback.dynamic_viscosity_Pa_s,
                density_kg_m3=feedback.density_kg_m3,
                minimum_width_to_aperture_ratio=feedback.minimum_width_to_aperture_ratio,
                maximum_reviewed_reynolds_number=feedback.maximum_reviewed_reynolds_number,
                geometry_and_boundary_pressures_reviewed=True,
                incompressible_newtonian_fluid_properties_reviewed=True,
                laminar_fully_developed_slit_assumption_reviewed=True,
            )
            hydraulic_result = evaluate_planar_slit_hydraulic_flow(hydraulic_request)
            if hydraulic_result.get("status") != "computed":
                return payload | {
                    "status": hydraulic_result.get("status", "out_of_scope"),
                    "failed_segment_index": index,
                    "computed_prefix": segments,
                    "uncommitted_hydraulic_result": hydraulic_result,
                    "reason": "Steady slit flow could not be recalculated for the updated aperture",
                }
            pending_hydraulic_record = {
                "state_index": index + 1,
                "elapsed_time_s": end,
                "pressure_drop_Pa": pressure_drop,
                "pressure_interpolation_lineage": pressure_interpolation_lineage,
                "aperture_m": list(next_aperture),
                "flow_input_sha256": canonical_digest(hydraulic_request.model_dump(mode="json")),
                "flow_result_sha256": canonical_digest(hydraulic_result),
                **hydraulic_static_lineage,
                "result": hydraulic_result,
                "basis": "Steady flow is recalculated at this accepted geometry/pressure knot and supplies the static face-velocity field to the next fixed-geometry transport segment.",
            }
            pending_hydraulic_result = hydraulic_result
        segment_record = {"segment_index": index, "global_start_time_s": start, "global_end_time_s": end,
                          "aperture_m": list(aperture), "transport_input_sha256": canonical_digest(segment_req.model_dump(mode="json")),
                          "result": segment, "metal_wall_inward_mol_m2_by_cell": metal_by_cell.tolist(),
                          "signed_recession_increment_m_by_cell": increment.tolist(),
                          "solid_deposition_endpoint": accepted_solid_deposition_result,
                          "maximum_relative_aperture_change": maximum_relative_aperture_change,
                          "within_segment_feedback_iterations": fixed_point_records,
                          "within_segment_hydraulic_path": fixed_point_hydraulic_path,
                          "next_aperture_m": next_aperture.tolist()}
        widths = np.asarray(geometry.cell_widths_m, dtype=float)
        before = concentration * np.asarray(cross_sections)[None, :] * widths[None, :]
        try:
            concentration_history = np.asarray(segment["concentration_mol_m3"], dtype=float)
        except (KeyError, TypeError, ValueError):
            return payload | {"status": "needs_data", "failed_segment_index": index,
                              "computed_prefix": segments, "computed_uncommitted_segment": segment_record,
                              "reason": "Transport concentration field is missing"}
        if (concentration_history.shape != (2, len(req.species_ids), ncell)
            or not np.isfinite(concentration_history).all() or np.any(concentration_history < 0)):
            return payload | {"status": "out_of_scope", "failed_segment_index": index,
                              "computed_prefix": segments, "computed_uncommitted_segment": segment_record,
                              "reason": "Transport concentration field is nonfinite, negative or misaligned"}
        after_concentration = concentration_history[-1]
        if feedback.within_segment_geometry_feedback_enabled:
            # The moving-volume ODE already advances concentration at the
            # converged end geometry; a second boundary remap would double count
            # expansion/recession.
            reaction_endpoint_concentration = after_concentration.copy()
            chemistry_inventory_source_mol_m2_by_species_cell = None
            if accepted_solid_deposition_result is not None:
                aqueous_delta = np.asarray(
                    accepted_solid_deposition_result["aqueous_concentration_delta_mol_m3_by_species_cell"],
                    dtype=float,
                )
                reaction_endpoint_concentration = after_concentration + aqueous_delta
                chemistry_inventory_source_mol_m2_by_species_cell = np.asarray(
                    accepted_solid_deposition_result["aqueous_reaction_source_mol_m2_by_species_cell"],
                    dtype=float,
                )
            guessed_cell_area = guessed_end_aperture * geometry.transverse_width_m
            target_cell_area = np.asarray(next_aperture, dtype=float) * geometry.transverse_width_m
            remapped = reaction_endpoint_concentration * guessed_cell_area[None, :] / target_cell_area[None, :]
            pre_remap_inventory = reaction_endpoint_concentration * guessed_cell_area[None, :] * widths[None, :]
            post_remap_inventory = remapped * target_cell_area[None, :] * widths[None, :]
            remap_error = float(np.max(np.abs(post_remap_inventory - pre_remap_inventory)))
            remap_limit = (req.inventory_absolute_tolerance_mol_m2
                           + req.inventory_relative_tolerance * float(np.max(np.abs(before)) / area)) * area
            remap_record = {
                "elapsed_time_s": end,
                "remap_applied": bool(accepted_solid_deposition_result is not None),
                "geometry_feedback_integrated_within_segment": True,
                "maximum_cell_inventory_change_mol": remap_error,
                "pre_remap_concentration_mol_m3": after_concentration.tolist(),
                "post_endpoint_chemistry_concentration_mol_m3": reaction_endpoint_concentration.tolist(),
                "post_remap_concentration_mol_m3": remapped.tolist(),
                "aqueous_reaction_source_mol_m2_by_species_cell": (
                    chemistry_inventory_source_mol_m2_by_species_cell.tolist()
                    if chemistry_inventory_source_mol_m2_by_species_cell is not None else None
                ),
            }
        else:
            remapped = after_concentration * np.asarray(cross_sections)[None, :] / np.asarray(next_aperture * geometry.transverse_width_m)[None, :]
            remap_error = float(np.max(np.abs(
                remapped * np.asarray(next_aperture * geometry.transverse_width_m)[None, :] * widths[None, :]
                - before
            )))
            remap_limit = (req.inventory_absolute_tolerance_mol_m2
                           + req.inventory_relative_tolerance * float(np.max(np.abs(before)) / area)) * area
            remap_record = {
                "elapsed_time_s": end,
                "remap_applied": True,
                "maximum_cell_inventory_change_mol": remap_error,
                "pre_remap_concentration_mol_m3": after_concentration.tolist(),
                "post_remap_concentration_mol_m3": remapped.tolist(),
            }
        after = remapped * np.asarray(next_aperture * geometry.transverse_width_m)[None, :] * widths[None, :]
        if (not np.isfinite(remapped).all() or np.any(remapped < 0) or not math.isfinite(remap_error)
            or not math.isfinite(remap_limit) or (
                not feedback.within_segment_geometry_feedback_enabled and remap_error > remap_limit
            )):
            return payload | {"status": "out_of_scope", "failed_segment_index": index,
                              "computed_prefix": segments, "computed_uncommitted_segment": segment_record,
                              "reason": "Cell inventory remap exceeded finite or declared tolerance"}
        segments.append(segment_record)
        if feedback.within_segment_geometry_feedback_enabled:
            for record in within_segment_feedback_history:
                if (record["segment_index"] == index
                        and record["global_start_time_s"] == start
                        and record["global_end_time_s"] == end):
                    record["segment_committed"] = True
        if pending_hydraulic_record is not None:
            hydraulic_history.append(pending_hydraulic_record)
            current_hydraulic_result = pending_hydraulic_result
        for key in total_ledgers:
            total_ledgers[key] += np.asarray(segment[key][-1], dtype=float)
        if accepted_solid_deposition_result is not None:
            source_by_species = np.asarray(
                accepted_solid_deposition_result["aqueous_reaction_source_mol_m2_by_species_cell"],
                dtype=float,
            )
            total_ledgers["cumulative_homogeneous_source_mol_m2"] += np.sum(source_by_species, axis=1)
            for phase_index, phase_id in enumerate(geometry_aware_solid_deposition_provider.solid_phase_ids):
                solid_inventory_by_phase[phase_id] = np.asarray(
                    accepted_solid_deposition_result["solid_inventory_end_mol_m2_by_phase_cell"][phase_index],
                    dtype=float,
                )
            solid_inventory_history.append({
                "elapsed_time_s": float(end),
                "endpoint_evaluation_sha256": accepted_solid_deposition_result["endpoint_evaluation_sha256"],
                "solid_inventory_mol_m2_by_phase_cell": {
                    phase_id: values.tolist() for phase_id, values in solid_inventory_by_phase.items()
                },
                "balance_residual_mol_m2_by_phase_cell": (
                    np.asarray(accepted_solid_deposition_result["solid_inventory_end_mol_m2_by_phase_cell"], dtype=float)
                    - np.asarray(accepted_solid_deposition_result["solid_inventory_start_mol_m2_by_phase_cell"], dtype=float)
                    - np.asarray(accepted_solid_deposition_result["solid_inventory_change_mol_m2_by_phase_cell"], dtype=float)
                ).tolist(),
            })
        remaps.append(remap_record)
        concentration = remapped
        cumulative_recession += increment
        aperture = next_aperture.tolist()
        accepted_internal_times.append(end)
        if end in requested_times:
            requested_snapshots.append({
                "elapsed_time_s": end,
                "cell_aperture_m": list(aperture),
                "cell_concentration_mol_m3": concentration.tolist(),
                "cumulative_signed_cell_average_recession_m": cumulative_recession.tolist(),
                "solid_inventory_mol_m2_by_phase_cell": {
                    phase_id: values.tolist() for phase_id, values in solid_inventory_by_phase.items()
                },
                "cumulative_transport_ledgers_mol_m2": {
                    key: value.tolist() for key, value in total_ledgers.items()
                },
            })
        index += 1

    final_area_per_reference = np.asarray(aperture, dtype=float) * geometry.transverse_width_m / area
    widths = np.asarray(geometry.cell_widths_m, dtype=float)
    final_inventory = np.sum(concentration * final_area_per_reference[None, :] * widths[None, :], axis=1)
    cumulative_sources = sum(total_ledgers.values(), np.zeros(len(req.species_ids), dtype=float))
    residual = final_inventory - initial_inventory - cumulative_sources
    ledger_scale = sum((np.abs(values) for values in total_ledgers.values()), np.zeros(len(req.species_ids)))
    balance_scale = np.maximum(np.abs(final_inventory), np.abs(initial_inventory) + ledger_scale)
    balance_limit = req.inventory_absolute_tolerance_mol_m2 + req.inventory_relative_tolerance * balance_scale
    if (not np.isfinite(residual).all() or not np.isfinite(balance_limit).all()
        or np.any(np.abs(residual) > balance_limit)):
        return payload | {
            "status": "out_of_scope", "computed_segment_count": len(segments),
            "computed_prefix": segments,
            "global_species_inventory_balance_residual_mol_m2": residual.tolist(),
            "global_species_inventory_balance_limit_mol_m2": balance_limit.tolist(),
            "reason": "Campaign-wide species inventory balance exceeded declared tolerance",
        }
    solid_closure = {}
    if geometry_aware_solid_deposition_provider is not None:
        phase_ids = geometry_aware_solid_deposition_provider.solid_phase_ids
        initial_solid = np.asarray([solid_inventory_initial_by_phase[key] for key in phase_ids], dtype=float)
        final_solid = np.asarray([solid_inventory_by_phase[key] for key in phase_ids], dtype=float)
        cumulative_solid_change = np.zeros_like(initial_solid)
        for segment_row in segments:
            endpoint = segment_row.get("solid_deposition_endpoint")
            if endpoint is not None:
                cumulative_solid_change += np.asarray(
                    endpoint["solid_inventory_change_mol_m2_by_phase_cell"], dtype=float
                )
        solid_residual = final_solid - initial_solid - cumulative_solid_change
        solid_scale = np.maximum(np.abs(final_solid), np.abs(initial_solid) + np.abs(cumulative_solid_change))
        solid_limit = req.inventory_absolute_tolerance_mol_m2 + req.inventory_relative_tolerance * solid_scale
        if (
            not np.isfinite(solid_residual).all() or not np.isfinite(solid_limit).all()
            or np.any(np.abs(solid_residual) > solid_limit)
        ):
            return payload | {
                "status": "out_of_scope",
                "computed_segment_count": len(segments),
                "computed_prefix": segments,
                "solid_inventory_balance_residual_mol_m2_by_phase_cell": solid_residual.tolist(),
                "solid_inventory_balance_limit_mol_m2_by_phase_cell": solid_limit.tolist(),
                "reason": "Campaign-wide solid-phase inventory balance exceeded the declared transport inventory tolerance",
            }
        solid_closure = {
            "solid_phase_ids": list(phase_ids),
            "initial_solid_inventory_mol_m2_by_phase_cell": initial_solid.tolist(),
            "final_solid_inventory_mol_m2_by_phase_cell": final_solid.tolist(),
            "cumulative_solid_inventory_change_mol_m2_by_phase_cell": cumulative_solid_change.tolist(),
            "solid_inventory_balance_residual_mol_m2_by_phase_cell": solid_residual.tolist(),
            "solid_inventory_balance_limit_mol_m2_by_phase_cell": solid_limit.tolist(),
            "solid_inventory_balance_within_declared_tolerance": True,
            "solid_inventory_history": solid_inventory_history,
        }
    return payload | {
        "status": "computed", "species_ids": list(req.species_ids), "metal_species_id": feedback.metal_species_id,
        "segment_count": len(segments), "segment_results": segments,
        "internal_time_s": accepted_internal_times,
        "internal_segment_count": len(segments),
        "maximum_geometry_update_step_s": maximum_step,
        "maximum_relative_aperture_change_per_segment": feedback.maximum_relative_aperture_change_per_segment,
        "adaptive_aperture_refinement_count": len(aperture_refinements),
        "adaptive_aperture_refinements": aperture_refinements,
        "steady_hydraulic_history": hydraulic_history,
        "requested_output_snapshots": requested_snapshots,
        "geometry_boundary_inventory_remaps": remaps,
        "final_cell_aperture_m": aperture,
        "cumulative_signed_cell_average_recession_m": cumulative_recession.tolist(),
        "cumulative_transport_ledgers_mol_m2": {key: value.tolist() for key, value in total_ledgers.items()},
        "initial_inventory_per_reference_area_mol_m2": initial_inventory.tolist(),
        "final_inventory_per_reference_area_mol_m2": final_inventory.tolist(),
        "global_species_inventory_balance_residual_mol_m2": residual.tolist(),
        "global_species_inventory_balance_limit_mol_m2": balance_limit.tolist(),
        **solid_closure,
        "coupling_basis": (
            "segmentwise_geometry_fixed_point_with_caller_endpoint_solid_extents; each trial re-evaluates balanced aqueous-to-solid extents on the guessed end-state geometry, applies an inventory-limited endpoint split and maps net phase volume to mean aperture change before convergence; transport, endpoint reactions and recession are still operator-split"
            if geometry_aware_solid_deposition_provider is not None
            else
            "segmentwise_geometry_fixed_point_with_caller_geometry_aware_aqueous_reaction_provider; provider net extents are reevaluated against each guessed linear aperture path, with per-reaction element/charge balance and transport species-inventory closure; phase change, deposition mechanics and fully simultaneous chemistry/flow are excluded"
            if geometry_aware_chemistry_provider is not None
            else
            "segmentwise_fixed_point_transport_recession_feedback_with_steady_hydraulic_endpoint_path; caller-approved linear aperture and face-velocity paths between endpoint steady slit solutions are iterated against transport-integrated metal wall flux and committed only after endpoint residual convergence; transient momentum and fully simultaneous flow/chemistry are excluded"
            if feedback.within_segment_geometry_feedback_enabled and feedback.within_segment_hydraulic_feedback_enabled
            else "segmentwise_fixed_point_transport_recession_feedback; caller-approved linear aperture path is iterated against transport-integrated metal wall flux and committed only after endpoint residual convergence; axial flow is excluded"
            if feedback.within_segment_geometry_feedback_enabled
            else "sequential_operator_split; transport-integrated selected metal wall flux updates slit aperture after each internal geometry-update segment; geometry is fixed within each internal segment"
        ),
        "geometry_update_policy": {
            "requested_output_times_s": list(requested_times),
            "maximum_geometry_update_step_s": maximum_step,
            "maximum_internal_segments": feedback.maximum_internal_segments,
            "maximum_relative_aperture_change_per_segment": feedback.maximum_relative_aperture_change_per_segment,
            "maximum_adaptive_aperture_refinements": feedback.maximum_adaptive_aperture_refinements,
            "adaptive_aperture_update_reviewed": feedback.adaptive_aperture_update_reviewed,
            "callback_re_evaluation_deterministic_reviewed": feedback.callback_re_evaluation_deterministic_reviewed,
            "within_segment_geometry_feedback_enabled": feedback.within_segment_geometry_feedback_enabled,
            "within_segment_geometry_feedback_reviewed": feedback.within_segment_geometry_feedback_reviewed,
            "within_segment_feedback_convergence_reviewed": feedback.within_segment_feedback_convergence_reviewed,
            "within_segment_hydraulic_feedback_enabled": feedback.within_segment_hydraulic_feedback_enabled,
            "within_segment_hydraulic_velocity_path_reviewed": feedback.within_segment_hydraulic_velocity_path_reviewed,
            "maximum_within_segment_feedback_iterations": feedback.maximum_within_segment_feedback_iterations,
            "within_segment_relative_aperture_tolerance": feedback.within_segment_relative_aperture_tolerance,
            "within_segment_feedback_relaxation": feedback.within_segment_feedback_relaxation,
            "mouth_history_interpolation": "piecewise_linear_between_requested_output_times",
            "within_internal_segment_geometry": (
                "reviewed_linear_aperture_path_with_bounded_endpoint_fixed_point"
                if feedback.within_segment_geometry_feedback_enabled
                else "fixed_at_segment_start"
            ),
        },
        "limitations": [
                        ("Within-segment feedback uses linear aperture and endpoint steady-velocity paths with bounded iterations; it does not solve transient momentum or fully simultaneous flow/chemistry." if feedback.within_segment_hydraulic_feedback_enabled else "Within-segment feedback uses a linear aperture path and a bounded endpoint fixed-point iteration; axial flow is excluded."),
                        ("The geometry-aware aqueous callback evaluates caller net reaction extents from each fixed-point aperture guess. Only aqueous species reactions declared in the balanced stoichiometric contract are supported; phase selection, solid deposition/dissolution inventory, activity feedback and independently qualified kinetics are not calculated." if geometry_aware_chemistry_provider is not None else "Reaction and activity callbacks remain caller-provided and are not recomputed from guessed geometry unless the geometry-aware provider option is used."),
                        ("The solid extent provider applies caller-declared endpoint extents after each transport interval. Solid molar volumes, initial inventories, coverage and reaction extents are input evidence; no Ksp, kinetics, phase selection, within-interval solid evolution or deposit morphology is inferred." if geometry_aware_solid_deposition_provider is not None else "No solid phase extent or deposition-induced aperture change is evaluated."),
                        "Evolving surface chemistry, deposit mechanics and independently qualified metal-flux laws remain external.",
                        "Selected species identity and conversion to signed metal recession are caller-reviewed assumptions; this result is not corrosion qualification, remaining life, or acceptance."],
        **({
            "geometry_aware_chemistry_closure": {
                "provider_contract_sha256": canonical_digest(
                    geometry_aware_chemistry_provider.contract.model_dump(mode="json")
                ),
                "provider_source_sha256": geometry_aware_chemistry_provider.source_sha256,
                "reaction_stoichiometry_element_charge_balanced": True,
                "aqueous_species_inventory_balance_within_declared_tolerance": True,
                "solid_phase_inventory_closed": False,
                "closure_basis": "Each instantaneous aqueous source is formed from element/charge-balanced net reaction extents; the existing transport ledger closes each aqueous species inventory over accepted segments.",
            }
        } if geometry_aware_chemistry_provider is not None else {}),
    }
