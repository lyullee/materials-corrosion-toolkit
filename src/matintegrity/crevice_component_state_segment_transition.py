"""Operator-split geometry transition between Crevice component BDF segments.

Conserved component moles are carried cellwise across an exact segment boundary;
caller-supplied target geometry is bound by digest and evidence. This is not an
intrastep moving-boundary solver.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_component_state_bdf import ComponentInventoryByCell, CreviceComponentStateBDFRequest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_component_state_segment_transition"
SOURCE_ID = "caller_mapped_committed_component_bdf_segment_transition"
BDF_MODEL_ID = "integration.crevice_component_state_bdf"


class CreviceSegmentGeometry(Contract):
    cell_ids: tuple[str, ...] = Field(min_length=2, max_length=300)
    cell_length_m: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    transverse_width_m: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    aperture_m: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    solution_volume_L: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    interior_face_area_m2: tuple[Positive, ...] = Field(min_length=1, max_length=299)
    center_distance_m: tuple[Positive, ...] = Field(min_length=1, max_length=299)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_geometry(self):
        n = len(self.cell_ids)
        if len(set(self.cell_ids)) != n or any(len(x) != n for x in (
            self.cell_length_m, self.transverse_width_m, self.aperture_m, self.solution_volume_L,
        )):
            raise ValueError("geometry cell arrays must have one unique, ordered row per cell")
        if len(self.interior_face_area_m2) != n - 1 or len(self.center_distance_m) != n - 1:
            raise ValueError("one face area and center distance are required per interior face")
        for i, (length, width, aperture, volume_l) in enumerate(zip(
            self.cell_length_m, self.transverse_width_m, self.aperture_m, self.solution_volume_L, strict=True,
        )):
            expected = float(length) * float(width) * float(aperture) * 1000.0
            if not math.isclose(float(volume_l), expected, rel_tol=1e-9, abs_tol=1e-12):
                raise ValueError(f"cell volume must equal length*width*aperture at cell {i}")
        payload = {
            "cell_ids": list(self.cell_ids),
            "cell_length_m": [float(x) for x in self.cell_length_m],
            "transverse_width_m": [float(x) for x in self.transverse_width_m],
            "aperture_m": [float(x) for x in self.aperture_m],
            "solution_volume_L": [float(x) for x in self.solution_volume_L],
            "interior_face_area_m2": [float(x) for x in self.interior_face_area_m2],
            "center_distance_m": [float(x) for x in self.center_distance_m],
        }
        if canonical_digest(payload) != self.sha256 or not any(
            e.source_id == self.source_id and e.sha256 == self.sha256 for e in self.evidence
        ):
            raise ValueError("geometry Evidence must identify and pin the complete geometry digest")
        return self


class CreviceComponentStateSegmentTransitionRequest(Contract):
    schema_version: Literal["matintegrity.crevice_component_state_segment_transition.v1"] = (
        "matintegrity.crevice_component_state_segment_transition.v1"
    )
    assessment_id: str = Field(min_length=1)
    source_request: CreviceComponentStateBDFRequest
    source_result: Calculation
    source_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_result_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    next_request_template: CreviceComponentStateBDFRequest
    next_geometry: CreviceSegmentGeometry
    boundary_time_s: float = Field(ge=0)
    committed_result_reviewed: bool
    component_basis_continuity_reviewed: bool
    geometry_transition_reviewed: bool
    maximum_work_operations: int = Field(default=500_000, ge=1, le=2_000_000)

    @model_validator(mode="after")
    def validate_transition(self):
        src, calc, nxt = self.source_request, self.source_result, self.next_request_template
        if src.assessment_id != self.assessment_id or nxt.assessment_id != self.assessment_id:
            raise ValueError("source, transition and target BDF requests must share assessment identity")
        digest = canonical_digest(calc.model_dump(mode="json"))
        if digest != self.source_result_sha256 or not any(
            e.source_id == BDF_MODEL_ID and e.sha256 == digest for e in self.source_result_evidence
        ):
            raise ValueError("Evidence must pin the full source Calculation digest")
        if (calc.status != "computed" or calc.values.get("model_id") != BDF_MODEL_ID
                or calc.values.get("input_sha256") != canonical_digest(src.model_dump(mode="json"))
                or calc.values.get("committed") is not True
                or calc.values.get("all_component_ledgers_close") is not True):
            raise ValueError("source BDF result must be computed, committed, input-bound and ledger-closed")
        times = calc.values.get("time_s")
        ids = tuple(c.cell_id for c in src.cells)
        if not isinstance(times, list) or tuple(times) != src.time_s or tuple(calc.values.get("cell_ids", ())) != ids:
            raise ValueError("source result must report its exact time and cell ordering")
        if float(times[-1]) != self.boundary_time_s or nxt.time_s[0] != self.boundary_time_s:
            raise ValueError("next segment must start at the exact source final time")
        geom = self.next_geometry
        if ids != geom.cell_ids or tuple(c.cell_id for c in nxt.cells) != geom.cell_ids:
            raise ValueError("cell identities/order must remain invariant at this segment boundary")
        if tuple(float(c.solution_volume_L) for c in nxt.cells) != tuple(float(v) for v in geom.solution_volume_L):
            raise ValueError("target request volumes must match the digest-bound geometry")
        if nxt.interior_face_area_m2 != geom.interior_face_area_m2 or nxt.center_distance_m_by_interior_face != geom.center_distance_m:
            raise ValueError("target face geometry must match the digest-bound geometry")
        source_basis = tuple(c.model_dump(mode="json") for c in src.cells[0].conserved_components)
        target_basis = tuple(c.model_dump(mode="json") for c in nxt.cells[0].conserved_components)
        if source_basis != target_basis:
            raise ValueError("conserved-component basis must remain exactly the same across segments")
        source_species = tuple((s.species_id, s.charge_number) for s in src.cells[0].aqueous_activity_request.system.species)
        target_species = tuple((s.species_id, s.charge_number) for s in nxt.cells[0].aqueous_activity_request.system.species)
        if source_species != target_species:
            raise ValueError("species identity/order/charge basis must remain fixed across this remap")
        if not (self.committed_result_reviewed and self.component_basis_continuity_reviewed
                and self.geometry_transition_reviewed):
            raise ValueError("source, component-basis and geometry transition reviews are required")
        if len(ids) * len(src.initial_component_inventory) > self.maximum_work_operations:
            raise ValueError("segment transition exceeds its declared work limit")
        return self


def transition_crevice_component_state_segment(request: CreviceComponentStateSegmentTransitionRequest) -> Calculation:
    """Construct a next-segment BDF request carrying source final component moles cellwise."""
    try:
        ledgers = request.source_result.values.get("component_ledgers")
        if not isinstance(ledgers, list):
            raise ValueError("source component ledgers are missing")
        ids = tuple(x.component_id for x in request.source_request.initial_component_inventory)
        by_id = {row.get("component_id"): row for row in ledgers if isinstance(row, dict)}
        if tuple(by_id) != ids:
            raise ValueError("source ledger component IDs/order must exactly match source request")
        inventory: list[ComponentInventoryByCell] = []
        transfer: dict[str, list[float]] = {}
        ntime = len(request.source_request.time_s)
        ncell = len(request.next_geometry.cell_ids)
        for component_id in ids:
            history = by_id[component_id].get("inventory_mol_by_time_and_cell")
            if not isinstance(history, list) or len(history) != ntime or not isinstance(history[-1], list) or len(history[-1]) != ncell:
                raise ValueError(f"invalid source inventory history for {component_id}")
            final = tuple(float(x) for x in history[-1])
            if any(not math.isfinite(x) or x < 0 for x in final):
                raise ValueError(f"invalid final component inventory for {component_id}")
            inventory.append(ComponentInventoryByCell(component_id=component_id, inventory_mol_by_cell=final))
            initial = next(x.inventory_mol_by_cell for x in request.source_request.initial_component_inventory if x.component_id == component_id)
            transfer[component_id] = [float(b) - float(a) for a, b in zip(initial, final, strict=True)]
        next_data = request.next_request_template.model_dump(mode="json")
        next_data["initial_component_inventory"] = [x.model_dump(mode="json") for x in inventory]
        next_request = CreviceComponentStateBDFRequest.model_validate(next_data)
        source_volumes = [float(x.solution_volume_L) for x in request.source_request.cells]
        target_volumes = [float(x.solution_volume_L) for x in next_request.cells]
        return Calculation(status="computed", values={
            "model_id": MODEL_ID,
            "source_id": SOURCE_ID,
            "assessment_id": request.assessment_id,
            "source_request_sha256": canonical_digest(request.source_request.model_dump(mode="json")),
            "source_result_sha256": request.source_result_sha256,
            "target_geometry_sha256": request.next_geometry.sha256,
            "next_request_sha256": canonical_digest(next_request.model_dump(mode="json")),
            "boundary_time_s": request.boundary_time_s,
            "cell_ids": list(request.next_geometry.cell_ids),
            "component_ids": list(ids),
            "source_segment_component_inventory_change_mol_by_component_cell": transfer,
            "next_initial_component_inventory": [x.model_dump(mode="json") for x in inventory],
            "source_cell_volume_L": source_volumes,
            "target_cell_volume_L": target_volumes,
            "cell_volume_change_L": [b-a for a, b in zip(source_volumes, target_volumes, strict=True)],
            "target_aperture_m": [float(x) for x in request.next_geometry.aperture_m],
            "next_segment_bdf_request": next_request.model_dump(mode="json"),
            "next_segment_request_ready": True,
            "component_moles_preserved_exactly_at_boundary": True,
            "transition_mode": "operator_split_fixed_geometry_segments",
            "committed": False,
            "qualification_claimed": False,
            "limitations": [
                "Geometry is caller/provider supplied; no aperture is inferred from deposition or metal loss.",
                "The next BDF request must be solved separately; geometry changes only at an exact segment boundary.",
                "No moving-boundary feedback inside a BDF interval/RHS, cross-cell remap, cell split/merge, or monolithic transport-chemistry-flow coupling is performed.",
            ],
        })
    except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "source_id": SOURCE_ID, "assessment_id": request.assessment_id,
            "reason": str(error), "committed": False, "qualification_claimed": False,
        })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceComponentStateSegmentTransitionRequest,
        evaluator=transition_crevice_component_state_segment,
        units={
            "boundary_time_s": "s", "next_geometry.aperture_m[]": "m",
            "next_geometry.solution_volume_L[]": "L", "next_geometry.interior_face_area_m2[]": "m^2",
            "next_geometry.center_distance_m[]": "m",
            "next_initial_component_inventory[].inventory_mol_by_cell[]": "mol",
            "source_segment_component_inventory_change_mol_by_component_cell.*[]": "mol",
            "cell_volume_change_L[]": "L",
        },
        assumptions=(
            "Source BDF result is full-digest-bound, committed and component-ledger closed.",
            "Caller supplies digest/Evidence-bound next geometry and retains cell identity/order.",
            "Final conserved component moles transfer cellwise as the next segment initial state without concentration remapping.",
            "This is an operator-split segment transition, not an intrastep moving-boundary or monolithic solver.",
        ),
        source_ids=(SOURCE_ID, "finite_volume_conserved_component_inventory_bdf_state"),
        version="1.0.0", qualification="user_model",
    ),)
