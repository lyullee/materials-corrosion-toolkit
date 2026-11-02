"""Bounded handoff from a committed component-state BDF run to a new fixed segment."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_component_state_bdf import CreviceComponentStateBDFRequest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_component_state_segment_handoff"
SOURCE_ID = "caller_mapped_component_state_bdf_fixed_segment_handoff"
BDF_MODEL_ID = "integration.crevice_component_state_bdf"
MAX_WORK = 20_000_000


class HandoffPhaseGeometry(Contract):
    solid_species_id: str = Field(min_length=1)
    molar_volume_m3_mol: Positive
    occupies_gap: bool


class CreviceComponentStateSegmentHandoffRequest(Contract):
    """Exact source request/result pair plus caller-evidenced geometry basis."""

    schema_version: Literal["matintegrity.crevice_component_state_segment_handoff.v1"] = (
        "matintegrity.crevice_component_state_segment_handoff.v1"
    )
    assessment_id: str = Field(min_length=1)
    source_bdf_request: CreviceComponentStateBDFRequest
    source_bdf_result: Calculation
    source_bdf_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_bdf_result_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    target_segment_start_time_s: float = Field(ge=0)
    cell_ids: tuple[str, ...] = Field(min_length=2, max_length=300)
    cell_length_m: tuple[Positive, ...]
    transverse_width_m: tuple[Positive, ...]
    initial_aperture_m: tuple[Positive, ...]
    geometry_basis_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_source_id: str = Field(min_length=1)
    geometry_basis_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    phase_geometry: tuple[HandoffPhaseGeometry, ...] = Field(min_length=1, max_length=256)
    phase_geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    phase_geometry_source_id: str = Field(min_length=1)
    phase_geometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    uniform_within_cell_coverage_reviewed: bool
    geometry_and_phase_mapping_reviewed: bool
    maximum_work_operations: int = Field(default=2_000_000, ge=1, le=MAX_WORK)

    @model_validator(mode="after")
    def validate_bindings(self):
        n = len(self.cell_ids)
        if len(set(self.cell_ids)) != n:
            raise ValueError("cell IDs must be unique and retain exact source order")
        if any(len(v) != n for v in (self.cell_length_m, self.transverse_width_m,
                                     self.initial_aperture_m)):
            raise ValueError("geometry vectors must align exactly with cell_ids")
        phase_ids = tuple(p.solid_species_id for p in self.phase_geometry)
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("phase IDs must be unique and ordered")
        if not self.uniform_within_cell_coverage_reviewed or not self.geometry_and_phase_mapping_reviewed:
            raise ValueError("uniform coverage and geometry/phase mapping review are required")
        result_digest = canonical_digest(self.source_bdf_result.model_dump(mode="json"))
        if result_digest != self.source_bdf_result_sha256 or not any(
            ev.source_id == BDF_MODEL_ID and ev.sha256 == result_digest
            for ev in self.source_bdf_result_evidence
        ):
            raise ValueError("source BDF Evidence must pin the exact Calculation result digest")
        geometry_digest = canonical_digest({
            "cell_ids": list(self.cell_ids),
            "cell_length_m": list(self.cell_length_m),
            "transverse_width_m": list(self.transverse_width_m),
            "initial_aperture_m": list(self.initial_aperture_m),
        })
        if geometry_digest != self.geometry_basis_sha256 or not any(
            ev.source_id == self.geometry_source_id and ev.sha256 == geometry_digest
            for ev in self.geometry_basis_evidence
        ):
            raise ValueError("geometry Evidence must pin the exact geometry basis")
        phase_digest = canonical_digest([{
            "solid_species_id": p.solid_species_id,
            "molar_volume_m3_mol": float(p.molar_volume_m3_mol),
            "occupies_gap": p.occupies_gap,
        } for p in self.phase_geometry])
        if phase_digest != self.phase_geometry_sha256 or not any(
            ev.source_id == self.phase_geometry_source_id and ev.sha256 == phase_digest
            for ev in self.phase_geometry_evidence
        ):
            raise ValueError("phase Evidence must pin the exact ordered phase molar-volume/occupancy map")
        return self


def solve_crevice_component_state_segment_handoff(
    request: CreviceComponentStateSegmentHandoffRequest,
) -> Calculation:
    """Return next-segment candidate geometry and conserved total component inventory."""
    try:
        bdf_req = request.source_bdf_request
        calc = request.source_bdf_result
        values: dict[str, Any] = calc.values
        if bdf_req.assessment_id != request.assessment_id or values.get("assessment_id") != request.assessment_id:
            raise ValueError("assessment identity mismatch between handoff and BDF pair")
        if bdf_req.solid_equilibrium_mode != "instantaneous_solid_equilibrium":
            return Calculation(status="out_of_scope", notes=(
                "This handoff requires the component-state BDF solid-equilibrium mode.",
            ), values={"model_id": MODEL_ID, "assessment_id": request.assessment_id,
                       "committed": False, "qualification_claimed": False})
        expected_input_digest = canonical_digest(bdf_req.model_dump(mode="json"))
        expected_result_digest = canonical_digest(calc.model_dump(mode="json"))
        if expected_result_digest != request.source_bdf_result_sha256:
            raise ValueError("BDF result digest mismatch")
        if values.get("input_sha256") != expected_input_digest:
            raise ValueError("BDF result input_sha256 does not bind the exact supplied BDF request")
        if calc.status != "computed" or values.get("committed") is not True:
            raise ValueError("source BDF Calculation must be computed and committed")
        if values.get("all_component_ledgers_close") is not True:
            raise ValueError("source BDF component ledgers must all be closed")
        if values.get("component_state_basis") != "total_aqueous_plus_candidate_solid":
            raise ValueError("source BDF state must be total aqueous-plus-solid component inventory")
        times = values.get("time_s")
        cell_ids = values.get("cell_ids")
        if (not isinstance(times, list) or not times or tuple(times) != bdf_req.time_s
                or tuple(cell_ids or ()) != request.cell_ids):
            raise ValueError("source result must carry exact ordered cell IDs and time knots")
        if request.target_segment_start_time_s != float(times[-1]):
            raise ValueError("target segment start must exactly equal source final BDF time")
        if tuple(row.cell_id for row in bdf_req.cells) != request.cell_ids:
            raise ValueError("geometry cell order must exactly match the source BDF request")
        if bdf_req.faradaic_stage_coupling is not None:
            template = bdf_req.faradaic_stage_coupling.mixed_potential_template
            if (tuple(template.cell_ids) != request.cell_ids
                    or tuple(template.cell_lengths_m) != request.cell_length_m
                    or len(set(request.transverse_width_m)) != 1
                    or template.slit_width_m != request.transverse_width_m[0]
                    or tuple(template.cell_apertures_m) != request.initial_aperture_m):
                raise ValueError("caller source geometry must exactly match the BDF Faradaic template")
        if tuple(row.cell_id for row in bdf_req.solid_phase_sets_by_cell) != request.cell_ids:
            raise ValueError("phase set receipt cells must match the exact source cell order")
        phase_ids = tuple(p.solid_species_id for p in request.phase_geometry)
        for phase_set in bdf_req.solid_phase_sets_by_cell:
            if tuple(p.solid_species_id for p in phase_set.phase_candidates) != phase_ids:
                raise ValueError("caller phase map order must match every BDF phase-set order")

        phase_hist = values.get("solid_phase_inventory_mol_by_cell_phase_time")
        if not isinstance(phase_hist, dict) or tuple(phase_hist.keys()) != request.cell_ids:
            raise ValueError("solid phase histories must cover cells in the exact requested order")
        ncell, ntime, nphase = len(request.cell_ids), len(times), len(phase_ids)
        component_ledgers = values.get("component_ledgers")
        if not isinstance(component_ledgers, list) or not component_ledgers:
            raise ValueError("BDF component inventory ledgers are required")
        component_ids = tuple(row.get("component_id") for row in component_ledgers)
        if len(set(component_ids)) != len(component_ids):
            raise ValueError("component IDs in BDF ledgers must be unique")
        expected_component_ids = tuple(row.component_id for row in bdf_req.initial_component_inventory)
        if component_ids != expected_component_ids:
            raise ValueError("BDF result component order must match the exact source request")
        if ncell * (ntime * len(component_ids) + nphase) > request.maximum_work_operations:
            raise ValueError("handoff work exceeds maximum_work_operations")

        solid_volume = [0.0] * ncell
        phase_final: dict[str, list[float]] = {p: [] for p in phase_ids}
        for i, cell in enumerate(request.cell_ids):
            local = phase_hist[cell]
            if tuple(local.keys()) != phase_ids:
                raise ValueError("per-cell phase history must preserve exact caller phase order")
            for phase in request.phase_geometry:
                hist = local[phase.solid_species_id]
                if not isinstance(hist, list) or len(hist) != ntime:
                    raise ValueError("solid phase history must align with exact BDF knot count")
                series = [float(x) for x in hist]
                if any(not math.isfinite(x) or x < 0 for x in series):
                    raise ValueError("solid inventory values must be finite and nonnegative")
                if series[0] != 0.0:
                    raise ValueError("candidate solid phase initial inventory must be zero")
                phase_final[phase.solid_species_id].append(series[-1])
                if phase.occupies_gap:
                    solid_volume[i] += series[-1] * float(phase.molar_volume_m3_mol)

        initial_components: dict[str, list[float]] = {}
        final_components: dict[str, list[float]] = {}
        for ledger in component_ledgers:
            component = ledger["component_id"]
            hist = ledger.get("inventory_mol_by_time_and_cell")
            if not isinstance(hist, list) or len(hist) != ntime or any(
                not isinstance(row, list) or len(row) != ncell for row in hist
            ):
                raise ValueError("component ledger time/cell dimensions do not match BDF result")
            initial = [float(x) for x in hist[0]]
            final = [float(x) for x in hist[-1]]
            if any(not math.isfinite(x) or x < 0 for x in initial + final):
                raise ValueError("component inventories must be finite and nonnegative")
            declared_initial = next(
                row.inventory_mol_by_cell for row in bdf_req.initial_component_inventory
                if row.component_id == component
            )
            if initial != [float(value) for value in declared_initial]:
                raise ValueError("BDF result initial component inventories differ from the exact source request")
            initial_components[component] = initial
            final_components[component] = final

        next_aperture = []
        next_cross_section = []
        next_volume = []
        for i in range(ncell):
            width = float(request.transverse_width_m[i])
            length = float(request.cell_length_m[i])
            old_aperture = float(request.initial_aperture_m[i])
            new_aperture = old_aperture - solid_volume[i] / (width * length)
            if not math.isfinite(new_aperture) or new_aperture <= 0.0:
                raise ValueError("gap-occupying solid volume closes the remaining aperture")
            residual = width * length * (old_aperture - new_aperture) - solid_volume[i]
            if abs(residual) > max(1e-18, 1e-10 * max(solid_volume[i], 1e-30)):
                raise ValueError("solid-volume/aperture closure failed")
            next_aperture.append(new_aperture)
            next_cross_section.append(width * new_aperture)
            next_volume.append(width * new_aperture * length)

        # Linear interpolation of cross-section from cell centers to interfaces;
        # boundary faces use endpoint-cell values.
        face_areas = [next_cross_section[0]]
        for i in range(1, ncell):
            left_length = float(request.cell_length_m[i - 1])
            right_length = float(request.cell_length_m[i])
            weight_left = left_length / (left_length + right_length)
            face_areas.append(
                next_cross_section[i - 1]
                + weight_left * (next_cross_section[i] - next_cross_section[i - 1])
            )
        face_areas.append(next_cross_section[-1])
        return Calculation(status="computed", values={
            "model_id": MODEL_ID,
            "source_id": SOURCE_ID,
            "assessment_id": request.assessment_id,
            "source_bdf_model_id": values.get("model_id"),
            "source_bdf_input_sha256": expected_input_digest,
            "source_bdf_result_status": calc.status,
            "target_segment_start_time_s": request.target_segment_start_time_s,
            "cell_ids": list(request.cell_ids),
            "component_ids": list(component_ids),
            "source_initial_component_moles_mol_by_component_cell": initial_components,
            "next_initial_total_component_moles_mol_by_component_cell": final_components,
            "solid_phase_ids": list(phase_ids),
            "final_solid_moles_mol_by_phase_cell": phase_final,
            "gap_occupying_solid_volume_m3_by_cell": solid_volume,
            "next_cell_aperture_m": next_aperture,
            "next_cell_cross_section_m2": next_cross_section,
            "next_cell_solution_volume_m3": next_volume,
            "next_cell_solution_volume_L": [v * 1000.0 for v in next_volume],
            "next_face_area_m2_by_face": face_areas,
            "solid_volume_aperture_closure_residual_m3_by_cell": [
                float(request.transverse_width_m[i]) * float(request.cell_length_m[i])
                * (float(request.initial_aperture_m[i]) - next_aperture[i]) - solid_volume[i]
                for i in range(ncell)
            ],
            "preserves_source_final_component_moles_as_next_initial_state": True,
            "committed": True,
            "qualification_claimed": False,
            "limitations": [
                "Boundary handoff to a new fixed-geometry segment only; no source chemistry or BDF request mutation.",
                "No moving-boundary feedback within the source BDF stages or RHS.",
                "Caller-reviewed uniform within-cell coverage and binary gap-occupancy mapping are assumed.",
                "Interior face geometry is linearly interpolated between cell centers; boundary faces take the adjacent cell value.",
            ],
        })
    except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID,
            "source_id": SOURCE_ID,
            "assessment_id": request.assessment_id,
            "reason": str(error),
            "committed": False,
            "qualification_claimed": False,
        })


def specifications() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec(
            model_id=MODEL_ID,
            input_type=CreviceComponentStateSegmentHandoffRequest,
            evaluator=solve_crevice_component_state_segment_handoff,
            units={
                "target_segment_start_time_s": "s",
                "source_initial_component_moles_mol_by_component_cell.*[]": "mol",
                "next_initial_total_component_moles_mol_by_component_cell.*[]": "mol",
                "final_solid_moles_mol_by_phase_cell.*[]": "mol",
                "gap_occupying_solid_volume_m3_by_cell[]": "m3",
                "next_cell_aperture_m[]": "m",
                "next_cell_cross_section_m2[]": "m2",
                "next_cell_solution_volume_m3[]": "m3",
                "next_cell_solution_volume_L[]": "L",
                "next_face_area_m2_by_face[]": "m2",
                "solid_volume_aperture_closure_residual_m3_by_cell[]": "m3",
            },
            assumptions=(
                "The source BDF request and exact Calculation result are digest-pinned and the source is committed with closed total-component ledgers.",
                "Caller phase molar volumes and gap-occupancy mappings are fixed over this exact boundary and bound to Evidence.",
                "Solid coverage is represented by a caller-reviewed uniform within-cell volume that reduces the open aperture; total component moles are preserved as the next segment initial state.",
                "This is a segment-boundary handoff only; it does not update geometry inside the BDF RHS or solve moving-boundary dynamics.",
            ),
            source_ids=(SOURCE_ID, "finite_volume_conserved_component_inventory_bdf_state"),
            qualification="user_model",
        ),
    )
