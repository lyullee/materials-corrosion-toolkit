"""Convert caller-reviewed crevice solid areal inventories to solid volume."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_solid_volume_inventory"
SOURCE_ID = "caller_crevice_solid_molar_volume_inventory"
MAX_CELLS = 5000
MAX_PHASES = 128


class CreviceSolidVolumeInventoryRequest(Contract):
    """A single exact state of cellwise phase inventory per reference area."""

    schema_version: Literal["matintegrity.crevice_solid_volume_inventory.v1"] = (
        "matintegrity.crevice_solid_volume_inventory.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    elapsed_time_s: float = Field(ge=0)
    phase_ids: tuple[str, ...] = Field(min_length=1, max_length=MAX_PHASES)
    cell_solid_inventory_mol_m2_by_phase: dict[str, tuple[float, ...]]
    solid_molar_volume_m3_mol_by_phase: dict[str, float]
    inventory_state_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    phase_inventory_basis_reviewed: bool
    molar_volume_state_and_units_reviewed: bool
    reference_area_and_cell_mapping_reviewed: bool
    no_morphology_or_aperture_inference_reviewed: bool

    @model_validator(mode="after")
    def validate_inventory(self):
        if len(set(self.phase_ids)) != len(self.phase_ids):
            raise ValueError("phase identifiers must be unique")
        if set(self.cell_solid_inventory_mol_m2_by_phase) != set(self.phase_ids):
            raise ValueError("one inventory row is required for each declared phase")
        if set(self.solid_molar_volume_m3_mol_by_phase) != set(self.phase_ids):
            raise ValueError("one molar volume is required for each declared phase")
        lengths = {len(row) for row in self.cell_solid_inventory_mol_m2_by_phase.values()}
        if len(lengths) != 1 or not lengths or next(iter(lengths)) < 1 or next(iter(lengths)) > MAX_CELLS:
            raise ValueError("phase inventories must share 1..5000 cell entries")
        for phase_id, inventory in self.cell_solid_inventory_mol_m2_by_phase.items():
            if any(not math.isfinite(value) or value < 0 for value in inventory):
                raise ValueError(f"solid inventory for {phase_id!r} must be finite and nonnegative")
            volume = self.solid_molar_volume_m3_mol_by_phase[phase_id]
            if not math.isfinite(volume) or volume <= 0:
                raise ValueError(f"molar volume for {phase_id!r} must be finite and positive")
        payload = {
            "physical_scope_id": self.physical_scope_id,
            "elapsed_time_s": self.elapsed_time_s,
            "phase_ids": self.phase_ids,
            "cell_solid_inventory_mol_m2_by_phase": self.cell_solid_inventory_mol_m2_by_phase,
            "solid_molar_volume_m3_mol_by_phase": self.solid_molar_volume_m3_mol_by_phase,
        }
        if canonical_digest(payload) != self.inventory_state_sha256:
            raise ValueError("solid inventory state digest mismatch")
        return self


def evaluate_crevice_solid_volume_inventory(
    request: CreviceSolidVolumeInventoryRequest,
) -> Calculation:
    """Calculate the volume-equivalent thickness implied by supplied solid amounts."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "elapsed_time_s": request.elapsed_time_s,
        "input_sha256": digest,
        "inventory_state_sha256": request.inventory_state_sha256,
        "phase_ids": list(request.phase_ids),
        "cell_count": len(next(iter(request.cell_solid_inventory_mol_m2_by_phase.values()))),
        "result_kind": "solid_volume_per_reference_area",
    }
    review_fields = (
        "phase_inventory_basis_reviewed",
        "molar_volume_state_and_units_reviewed",
        "reference_area_and_cell_mapping_reviewed",
        "no_morphology_or_aperture_inference_reviewed",
    )
    missing = [name for name in review_fields if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    cell_count = base["cell_count"]
    cell_volume_per_area = [0.0] * cell_count
    phase_volume_per_area: dict[str, list[float]] = {}
    for phase_id in request.phase_ids:
        molar_volume = request.solid_molar_volume_m3_mol_by_phase[phase_id]
        contributions = [amount * molar_volume for amount in request.cell_solid_inventory_mol_m2_by_phase[phase_id]]
        if any(not math.isfinite(value) for value in contributions):
            return Calculation(status="out_of_scope", values=base | {"reason": "phase volume exceeds finite support", "failed_phase_id": phase_id})
        phase_volume_per_area[phase_id] = contributions
        for index, value in enumerate(contributions):
            cell_volume_per_area[index] += value
            if not math.isfinite(cell_volume_per_area[index]):
                return Calculation(status="out_of_scope", values=base | {"reason": "summed solid volume exceeds finite support", "failed_cell_index": index})

    return Calculation(values=base | {
        "status": "computed",
        "cell_solid_volume_per_reference_area_m": cell_volume_per_area,
        "phase_solid_volume_per_reference_area_m": phase_volume_per_area,
        "total_solid_volume_per_reference_area_m": math.fsum(cell_volume_per_area),
        "interpretation_boundary": "This is the supplied phase inventory multiplied by caller-provided solid molar volume and summed by cell. It is a volume per reference area (dimensionally a length), not a deposit morphology or a slit-aperture change.",
        "not_inferred": ["solid distribution within a cell", "porosity", "adhesion", "precipitation kinetics", "wall coverage", "aperture closure", "transport feedback", "corrosion rate", "acceptance", "risk probability"],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSolidVolumeInventoryRequest,
        evaluator=evaluate_crevice_solid_volume_inventory,
        units={
            "elapsed_time_s": "s",
            "cell_solid_inventory_mol_m2_by_phase.*": "mol/m2",
            "solid_molar_volume_m3_mol_by_phase.*": "m3/mol",
            "cell_solid_volume_per_reference_area_m": "m3/m2",
            "phase_solid_volume_per_reference_area_m.*": "m3/m2",
            "total_solid_volume_per_reference_area_m": "m3/m2",
        },
        assumptions=(
            "Each phase inventory is nonnegative amount per caller-reviewed reference area for the same exact snapshot and spatial cell mapping.",
            "Each supplied molar volume applies to the stated solid phase and snapshot; product inventory times molar volume gives its compact-solid volume equivalent.",
            "Summation preserves cell identity; the output is volume per reference area and is not assigned to a wall or converted to aperture closure.",
            "Evidence is caller supplied and is not automatically qualified or independently validated by this adapter.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
