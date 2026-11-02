"""Bind electrochemical metal loss to an explicitly mapped slit geometry."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Fraction, Positive, RunContext, canonical_digest
from ..crevice_geometry import PlanarSlitApertureHistory, planar_slit_aperture_history
from ..registry import ModelSpec


class ReactionCellVolumeAllocation(Contract):
    """Per-knot spatial allocation of one reaction's cumulative metal-transfer volume."""

    reaction_id: str = Field(min_length=1)
    cumulative_cell_volume_fraction: tuple[tuple[Fraction, ...], ...] = Field(min_length=2, max_length=5000)


class ElectrochemicalCreviceGeometryHistory(Contract):
    """Conserve mapped electrochemical metal volume while updating slit cells.

    The caller supplies the reaction- and knot-specific spatial distribution.
    This adapter does not infer local current density from a global branch.
    """

    schema_version: Literal["matintegrity.electrochemical_crevice_geometry_history.v1"] = (
        "matintegrity.electrochemical_crevice_geometry_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    metal_loss_result: AssessmentResult
    metal_loss_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_id: str = Field(min_length=1)
    geometry_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_cell_ids: tuple[str, ...] = Field(default=(), max_length=2000)
    cell_widths_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    initial_cell_aperture_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    transverse_width_m: Positive
    reference_cross_section_m2: Positive
    reactive_broad_face_count: Literal[1, 2]
    cell_volume_allocations: tuple[ReactionCellVolumeAllocation, ...] = Field(default=(), max_length=32)
    supported_minimum_aperture_m: Positive
    supported_maximum_aperture_m: Positive
    reaction_surface_to_slit_face_mapping_reviewed: bool
    cell_volume_allocation_basis_reviewed: bool
    reaction_volume_conservation_reviewed: bool
    wall_recession_is_per_combined_reactive_area_reviewed: bool
    opposing_face_recession_is_equal_reviewed: bool
    cell_center_to_face_mapping_reviewed: bool
    geometry_basis_reviewed: bool
    computational_use_authorized: bool
    source_clock_origin_rebasing_reviewed: bool = False

    @model_validator(mode="after")
    def validate_metal_history_and_spatial_mapping(self):
        result = self.metal_loss_result
        if result.model_id not in {
            "integration.electrochemical_partial_current_metal_loss",
            "integration.crevice_current_carrying_extent_to_metal_loss",
        } or result.status != "computed":
            raise ValueError("a computed digest-pinned electrochemical metal-loss result is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("metal-loss input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.metal_loss_result_sha256:
            raise ValueError("complete metal-loss result digest mismatch")
        if result.values.get("material_condition_id") != result.inputs.get("material_condition_id"):
            raise ValueError("metal-loss material condition does not match the pinned input")
        if len(self.cell_widths_m) != len(self.initial_cell_aperture_m):
            raise ValueError("initial aperture and cell-width vectors must align")
        if self.supported_maximum_aperture_m <= self.supported_minimum_aperture_m:
            raise ValueError("aperture support bounds must be strictly ordered")
        if not self.computational_use_authorized:
            raise ValueError("computational use must be explicitly authorized")
        if not (self.reaction_surface_to_slit_face_mapping_reviewed and self.cell_volume_allocation_basis_reviewed
                and self.reaction_volume_conservation_reviewed):
            raise ValueError("reaction-to-face mapping, cell allocation and volume conservation reviews are required")
        if self.reactive_broad_face_count == 2 and not self.opposing_face_recession_is_equal_reviewed:
            raise ValueError("two-face geometry requires an explicit equal-face recession review")
        if not (self.wall_recession_is_per_combined_reactive_area_reviewed
                and self.cell_center_to_face_mapping_reviewed and self.geometry_basis_reviewed):
            raise ValueError("combined-area, cell-to-face and geometry basis reviews are required")
        if not math.isfinite(math.fsum(self.cell_widths_m)):
            raise ValueError("total slit length must be finite")
        if any(
            value < self.supported_minimum_aperture_m or value > self.supported_maximum_aperture_m
            for value in self.initial_cell_aperture_m
        ):
            raise ValueError("initial cell apertures must lie inside declared support")
        intervals = result.values.get("interval_metal_loss")
        mappings = result.values.get("reaction_to_metal_mapping")
        if not isinstance(intervals, list) or not intervals or not isinstance(mappings, list):
            raise ValueError("metal-loss result lacks interval history or reaction mapping lineage")
        reaction_ids = [row.get("reaction_id") for row in mappings if isinstance(row, dict)]
        if len(reaction_ids) != len(mappings) or len(reaction_ids) != len(set(reaction_ids)):
            raise ValueError("upstream reaction mappings are invalid or duplicated")
        direct_cell_ledger = result.model_id == "integration.crevice_current_carrying_extent_to_metal_loss"
        allocations = {row.reaction_id: row for row in self.cell_volume_allocations}
        if len(allocations) != len(self.cell_volume_allocations):
            raise ValueError("cell volume allocation reaction IDs must be unique")
        cellwise_intervals = None
        cell_ids = None
        if direct_cell_ledger:
            if allocations:
                raise ValueError("direct cell-resolved Faradaic metal volumes must not be remapped by caller fractions")
            cell_ids = result.values.get("cell_ids")
            if (not isinstance(cell_ids, list) or len(cell_ids) != len(self.cell_widths_m)
                    or len(set(cell_ids)) != len(cell_ids)):
                raise ValueError("direct cell-resolved metal ledger must match the geometry cell count and order")
            if tuple(self.geometry_cell_ids) != tuple(cell_ids):
                raise ValueError("geometry_cell_ids must exactly match the current-carrying source cell order")
            cellwise_intervals = result.values.get("cellwise_interval_metal_loss")
            if not isinstance(cellwise_intervals, list) or len(cellwise_intervals) != len(intervals):
                raise ValueError("direct cell-resolved metal ledger must match every source interval")
        elif set(allocations) != set(reaction_ids):
            raise ValueError("legacy metal-loss results require caller allocations for every selected reaction")
        if not direct_cell_ledger and self.geometry_cell_ids and (
            len(self.geometry_cell_ids) != len(self.cell_widths_m)
            or len(set(self.geometry_cell_ids)) != len(self.geometry_cell_ids)
        ):
            raise ValueError("optional geometry cell IDs must be unique and align with geometry cell widths")
        times = []
        for index, interval in enumerate(intervals):
            if not isinstance(interval, dict):
                raise ValueError("metal-loss intervals must be objects")
            start, end = interval.get("start_time_s"), interval.get("end_time_s")
            if (
                isinstance(start, bool) or not isinstance(start, (int, float)) or not math.isfinite(start)
                or isinstance(end, bool) or not isinstance(end, (int, float)) or not math.isfinite(end)
                or end <= start
            ):
                raise ValueError("metal-loss interval times must be finite and strictly increasing")
            if index and start != times[-1]:
                raise ValueError("metal-loss intervals must form a contiguous geometry clock")
            if not index:
                times.append(start)
            times.append(end)
            rows = interval.get("reaction_metal_loss")
            if not isinstance(rows, list) or tuple(row.get("reaction_id") for row in rows) != tuple(reaction_ids):
                raise ValueError("reaction metal-loss rows must preserve upstream mapping order")
            for row in rows:
                if not isinstance(row.get("cumulative"), dict):
                    raise ValueError("each reaction interval must retain a cumulative metal ledger")
                cumulative = row["cumulative"].get("signed_mass_loss_kg")
                if isinstance(cumulative, bool) or not isinstance(cumulative, (int, float)) or not math.isfinite(cumulative):
                    raise ValueError("cumulative signed reaction mass must be finite")
            if direct_cell_ledger:
                cell_interval = cellwise_intervals[index]
                if (not isinstance(cell_interval, dict)
                        or cell_interval.get("interval_index") != index
                        or cell_interval.get("start_time_s") != start
                        or cell_interval.get("end_time_s") != end):
                    raise ValueError("direct cellwise metal interval clocks must match the mass ledger")
                branches = cell_interval.get("branches")
                if not isinstance(branches, list) or tuple(row.get("reaction_id") for row in branches) != tuple(reaction_ids):
                    raise ValueError("direct cellwise metal branches must preserve reaction mapping order")
                mass_by_reaction = {
                    row["reaction_id"]: row["cumulative"]["signed_mass_loss_kg"] for row in rows
                }
                density_by_reaction = {row["reaction_id"]: row.get("density_kg_m3") for row in mappings}
                for branch in branches:
                    cells = branch.get("cells")
                    if not isinstance(cells, list) or tuple(row.get("cell_id") for row in cells) != tuple(cell_ids):
                        raise ValueError("direct cellwise metal rows must match the exact source cell identity/order")
                    volume_values = [row.get("cumulative_metal_volume_m3") for row in cells]
                    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0.0
                           for v in volume_values):
                        raise ValueError("direct cellwise cumulative metal volumes must be finite and nonnegative")
                    density = density_by_reaction[branch["reaction_id"]]
                    if (isinstance(density, bool) or not isinstance(density, (int, float))
                            or not math.isfinite(density) or density <= 0.0):
                        raise ValueError("direct cellwise metal mapping requires a positive density")
                    cell_volume = math.fsum(volume_values)
                    mass_volume = mass_by_reaction[branch["reaction_id"]] / density
                    if not math.isclose(cell_volume, mass_volume, rel_tol=1e-10, abs_tol=1e-18):
                        raise ValueError("direct cellwise volume does not close to cumulative metal mass/density")
        if times[0] != 0.0 and not self.source_clock_origin_rebasing_reviewed:
            raise ValueError("nonzero source time origin requires explicit rebasing review against the initial geometry")
        if not direct_cell_ledger:
            for reaction_id, allocation in allocations.items():
                rows = allocation.cumulative_cell_volume_fraction
                if len(rows) != len(times) or any(len(row) != len(self.cell_widths_m) for row in rows):
                    raise ValueError("each reaction allocation must align with every time knot and geometry cell")
                if any(not math.isclose(math.fsum(row), 1.0, rel_tol=1e-10, abs_tol=1e-12) for row in rows):
                    raise ValueError(f"cell volume fractions for {reaction_id} must sum to one at every knot")
        return self


def electrochemical_crevice_geometry_history(x: ElectrochemicalCreviceGeometryHistory) -> Calculation:
    result = x.metal_loss_result
    intervals = result.values["interval_metal_loss"]
    mappings = {row["reaction_id"]: row for row in result.values["reaction_to_metal_mapping"]}
    allocations = {row.reaction_id: row.cumulative_cell_volume_fraction for row in x.cell_volume_allocations}
    direct_cell_ledger = result.model_id == "integration.crevice_current_carrying_extent_to_metal_loss"
    source_times = [intervals[0]["start_time_s"], *(row["end_time_s"] for row in intervals)]
    source_time_origin_s = source_times[0]
    elapsed_times = [time_s - source_time_origin_s for time_s in source_times]
    face_count = x.reactive_broad_face_count
    cell_areas = [face_count * x.transverse_width_m * width for width in x.cell_widths_m]
    area_ratios = [area / x.reference_cross_section_m2 for area in cell_areas]
    cumulative_by_time = [
        {reaction_id: {"signed_mass_loss_kg": 0.0} for reaction_id in mappings}
    ]
    for interval in intervals:
        cumulative_by_time.append({
            row["reaction_id"]: row["cumulative"]
            for row in interval["reaction_metal_loss"]
        })
    if direct_cell_ledger:
        direct_cell_volume_by_time = [
            {reaction_id: [0.0] * len(x.cell_widths_m) for reaction_id in mappings}
        ]
        for cell_interval in result.values["cellwise_interval_metal_loss"]:
            direct_cell_volume_by_time.append({
                branch["reaction_id"]: [float(cell["cumulative_metal_volume_m3"]) for cell in branch["cells"]]
                for branch in cell_interval["branches"]
            })
        allocations = {}
        for reaction_id, mapping in mappings.items():
            rows = []
            for knot_index, volumes in enumerate(direct_cell_volume_by_time):
                values = volumes[reaction_id]
                total_volume = math.fsum(values)
                expected_volume = (
                    cumulative_by_time[knot_index][reaction_id]["signed_mass_loss_kg"]
                    / mapping["density_kg_m3"]
                )
                if not math.isclose(total_volume, expected_volume, rel_tol=1e-10, abs_tol=1e-18):
                    return Calculation(status="out_of_scope", values={
                        "assessment_id": x.assessment_id,
                        "failed_time_index": knot_index,
                        "failed_time_s": source_times[knot_index],
                        "failure_reason": "direct_cellwise_volume_does_not_close_to_metal_mass",
                        "reaction_id": reaction_id,
                        "cell_volume_m3": total_volume,
                        "mass_density_volume_m3": expected_volume,
                    })
                if total_volume > 0.0:
                    rows.append([value / total_volume for value in values])
                else:
                    # Zero total loss makes the allocation immaterial; use a deterministic bookkeeping row.
                    rows.append([1.0] + [0.0] * (len(values) - 1))
            allocations[reaction_id] = rows
    cellwise_history = []
    reaction_volume_balance = []
    for time_index, time_s in enumerate(elapsed_times):
        total_cell_volume = [0.0] * len(cell_areas)
        reaction_volumes = {}
        for reaction_id, mapping in mappings.items():
            cumulative = cumulative_by_time[time_index][reaction_id]
            signed_mass = cumulative["signed_mass_loss_kg"]
            density = mapping["density_kg_m3"]
            total_volume = signed_mass / density
            reaction_volumes[reaction_id] = total_volume
            for cell_index, fraction in enumerate(allocations[reaction_id][time_index]):
                total_cell_volume[cell_index] += total_volume * fraction
        if not all(math.isfinite(value) for value in total_cell_volume):
            return Calculation(status="out_of_scope", values={
                "assessment_id": x.assessment_id,
                "failed_time_index": time_index,
                "failed_time_s": time_s,
                "failure_reason": "cellwise_metal_volume_exceeded_finite_numeric_support",
            })
        upstream_total_volume = math.fsum(reaction_volumes.values())
        allocated_total_volume = math.fsum(total_cell_volume)
        closure_residual = allocated_total_volume - upstream_total_volume
        if not math.isfinite(closure_residual) or not math.isclose(
            allocated_total_volume, upstream_total_volume, rel_tol=1e-10, abs_tol=1e-18
        ):
            return Calculation(status="out_of_scope", values={
                "assessment_id": x.assessment_id,
                "failed_time_index": time_index,
                "failed_time_s": time_s,
                "failure_reason": "reaction_volume_allocation_did_not_conserve_upstream_ledger",
                "upstream_signed_total_volume_m3": upstream_total_volume,
                "allocated_signed_total_volume_m3": allocated_total_volume,
                "closure_residual_m3": closure_residual,
            })
        reaction_volume_balance.append({
            "elapsed_time_s": time_s,
            "by_reaction_m3": reaction_volumes,
            "upstream_signed_total_m3": upstream_total_volume,
            "allocated_signed_total_m3": allocated_total_volume,
            "closure_residual_m3": closure_residual,
        })
        cells = [
            {
                "cell_index": index,
                "signed_local_cell_average_recession_m": total_cell_volume[index] / cell_areas[index],
                "reactive_wall_area_over_reference_area": area_ratios[index],
            }
            for index in range(len(cell_areas))
        ]
        cellwise_history.append({"elapsed_time_s": time_s, "cells": cells})
    wall_result = {
        "status": "computed",
        "model_id": result.model_id,
        "values": {
            "wall_metal_loss": {
                "reference_cross_section_m2": x.reference_cross_section_m2,
                "reactive_wall_area_over_reference_area": math.fsum(area_ratios),
                "cellwise_history": cellwise_history,
            },
            "selection_sha256": canonical_digest({
                "metal_loss_result_sha256": x.metal_loss_result_sha256,
                "geometry_cell_ids": list(x.geometry_cell_ids),
                "cell_volume_allocations": [row.model_dump(mode="json") for row in x.cell_volume_allocations],
                "direct_cellwise_source_ledger_sha256": (
                    canonical_digest(result.values["cellwise_interval_metal_loss"])
                    if direct_cell_ledger else None
                ),
            }),
        },
    }
    geometry_request = PlanarSlitApertureHistory(
        geometry_id=x.geometry_id,
        geometry_source_sha256=x.geometry_source_sha256,
        wall_loss_source_sha256=canonical_digest(wall_result),
        cell_widths_m=x.cell_widths_m,
        initial_cell_aperture_m=x.initial_cell_aperture_m,
        transverse_width_m=x.transverse_width_m,
        reference_cross_section_m2=x.reference_cross_section_m2,
        reactive_broad_face_count=face_count,
        wall_loss_result=wall_result,
        supported_minimum_aperture_m=x.supported_minimum_aperture_m,
        supported_maximum_aperture_m=x.supported_maximum_aperture_m,
        wall_recession_is_per_combined_reactive_area_reviewed=x.wall_recession_is_per_combined_reactive_area_reviewed,
        opposing_face_recession_is_equal_reviewed=x.opposing_face_recession_is_equal_reviewed,
        cell_center_to_face_mapping_reviewed=x.cell_center_to_face_mapping_reviewed,
        geometry_basis_reviewed=x.geometry_basis_reviewed,
    )
    geometry = planar_slit_aperture_history(geometry_request)
    values = dict(geometry) | {
        "assessment_id": x.assessment_id,
        "material_condition_id": result.values["material_condition_id"],
        "metal_loss_result_sha256": x.metal_loss_result_sha256,
        "source_time_origin_s": source_time_origin_s,
        "source_clock_origin_rebasing_reviewed": x.source_clock_origin_rebasing_reviewed,
        "source_to_elapsed_time_s": [
            {"source_time_s": source_time, "elapsed_time_s": elapsed}
            for source_time, elapsed in zip(source_times, elapsed_times, strict=True)
        ],
        "cell_volume_allocation_sha256": wall_result["values"]["selection_sha256"],
        "metal_loss_allocation_policy": (
            "upstream_digest_pinned_cellwise_metal_volumes"
            if direct_cell_ledger else "caller_supplied_reaction_specific_cumulative_cell_volume_fractions"
        ),
        "cellwise_signed_metal_volume_m3": [
            {"elapsed_time_s": row["elapsed_time_s"], "volume_m3": [
                cell["signed_local_cell_average_recession_m"] * cell_areas[index]
                for index, cell in enumerate(row["cells"])
            ]}
            for row in cellwise_history
        ],
        "reaction_volume_balance_m3": reaction_volume_balance,
    }
    return Calculation(status=geometry["status"], values=values, notes=(
        "Reaction-specific cumulative signed metal-transfer volume is allocated to cells only by caller-supplied fractions that sum to one at every knot; the signed volume closure residual is reported.",
        "The first source time is the initial geometry reference and is mapped to elapsed time zero. A nonzero source origin is accepted only with an explicit caller review and the source-to-elapsed mapping is retained.",
        "Cellwise recession is the signed net volume divided by the caller-declared combined reactive wall area. The existing sequential aperture remap is reused; no local electrochemical current or within-interval moving boundary is inferred.",
    ))


def _validate_context(x: ElectrochemicalCreviceGeometryHistory, context: RunContext) -> None:
    upstream = x.metal_loss_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        upstream.asset_id,
        upstream.location_id,
        upstream.time_basis,
    ):
        raise ValueError("geometry-history context must match upstream metal-loss asset, location and time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.electrochemical_metal_loss_to_crevice_geometry",
        ElectrochemicalCreviceGeometryHistory,
        electrochemical_crevice_geometry_history,
        {
            "geometry_states[].elapsed_time_s": "s",
            "source_time_origin_s": "s",
            "source_to_elapsed_time_s[].source_time_s": "s",
            "source_to_elapsed_time_s[].elapsed_time_s": "s",
            "geometry_states[].cell_aperture_m": "m",
            "geometry_states[].axial_cross_section_m2": "m2",
            "geometry_states[].cell_volume_m3": "m3",
            "cellwise_signed_metal_volume_m3[].volume_m3": "m3",
        },
        (
            "Only a computed digest-pinned electrochemical metal-loss result with every selected reaction explicitly allocated is accepted.",
            "Legacy metal-loss results require caller-supplied per-reaction volume fractions at every exact knot; the current-carrying extent bridge instead uses its digest-pinned per-cell volume ledger directly.",
            "The first supplied source time is mapped to elapsed geometry time zero; a nonzero origin requires explicit caller review and is retained in result lineage.",
            "Reaction-to-face, allocation, combined-area, cell-center mapping, geometry and computational-use reviews are mandatory; two-face use also requires equal-face recession review.",
            "The existing planar-slit remap computes sequential geometry only inside caller aperture support. This is not local current prediction or a fully coupled moving-boundary solver.",
        ),
        ("electrochemical_metal_loss_to_crevice_geometry",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
