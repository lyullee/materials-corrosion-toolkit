"""Convert crevice multiphase kinetic solid states into volume-per-area histories."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .crevice_solid_volume_inventory import (
    CreviceSolidVolumeInventoryRequest,
    evaluate_crevice_solid_volume_inventory,
)
from .multiphase_kinetic_transport import CompetingSolidKineticTransport
from .registry import ModelSpec

MODEL_ID = "integration.crevice_kinetic_solid_volume_history"
SOURCE_ID = "caller_crevice_kinetic_solid_inventory_to_solid_volume"
MAX_RECORDS = 2_000_000


class CreviceKineticSolidVolumeHistoryRequest(Contract):
    schema_version: Literal["matintegrity.crevice_kinetic_solid_volume_history.v1"] = (
        "matintegrity.crevice_kinetic_solid_volume_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    kinetic_campaign: CompetingSolidKineticTransport
    kinetic_campaign_result: dict
    kinetic_campaign_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    solid_molar_volume_m3_mol_by_phase: dict[str, float]
    molar_volume_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=256)
    kinetic_concentration_and_phase_mapping_reviewed: bool
    fixed_geometry_volume_basis_reviewed: bool
    molar_volume_current_solid_state_and_units_reviewed: bool
    no_morphology_or_aperture_inference_reviewed: bool

    @model_validator(mode="after")
    def validate_kinetic_source(self):
        campaign = self.kinetic_campaign
        transport = campaign.transport
        if transport.reference_cross_section_m2 is None:
            raise ValueError("an explicit kinetic-transport reference cross section is required")
        if any(value is not None for value in (
            transport.cell_cross_section_history_m2,
            transport.face_cross_section_history_m2,
            transport.wall_area_per_volume_history_m2_m3,
        )):
            raise ValueError("this adapter accepts only fixed geometry; moving geometry requires knot-specific cell volume support")
        phase_ids = tuple(row.solid_species_id for row in campaign.candidate_solid_phases)
        if set(self.solid_molar_volume_m3_mol_by_phase) != set(phase_ids):
            raise ValueError("one caller-reviewed molar volume is required for every and only kinetic solid phase")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0
            for value in self.solid_molar_volume_m3_mol_by_phase.values()
        ):
            raise ValueError("solid molar volumes must be finite and positive")
        if len(transport.output_times_s) * transport.cell_count * len(phase_ids) > MAX_RECORDS:
            raise ValueError("phase-by-knot-by-cell conversion exceeds the bounded record budget")
        if canonical_digest(self.kinetic_campaign_result) != self.kinetic_campaign_result_sha256:
            raise ValueError("kinetic transport result digest mismatch")
        result = self.kinetic_campaign_result
        if result.get("status") != "computed":
            raise ValueError("computed kinetic transport result is required")
        if result.get("input_sha256") != canonical_digest(campaign.model_dump(mode="json")):
            raise ValueError("kinetic transport result is not bound to the supplied typed campaign")
        if result.get("campaign_id") != campaign.campaign_id or result.get("physical_scope_id") != campaign.physical_scope_id:
            raise ValueError("kinetic result campaign or physical scope differs from its request")
        return self


def convert_crevice_kinetic_solid_volume_history(
    request: CreviceKineticSolidVolumeHistoryRequest,
) -> Calculation:
    """Convert each fixed-geometry phase concentration knot and reuse the volume ledger."""
    campaign = request.kinetic_campaign
    transport = campaign.transport
    source = request.kinetic_campaign_result
    widths = list(transport.cell_widths_m or (transport.length_m / transport.cell_count,) * transport.cell_count)
    if transport.cell_cross_section_m2 is None:
        area_ratio = [1.0] * transport.cell_count
    else:
        area_ratio = [area / transport.reference_cross_section_m2 for area in transport.cell_cross_section_m2]
    cell_volume_per_reference_area = [ratio * width for ratio, width in zip(area_ratio, widths, strict=True)]
    if any(not math.isfinite(value) or value <= 0 for value in cell_volume_per_reference_area):
        return Calculation(status="out_of_scope", values={
            "assessment_id": request.assessment_id,
            "kinetic_campaign_result_sha256": request.kinetic_campaign_result_sha256,
            "reason": "cell volume per reference area is not finite and positive",
            "completed_knot_count": 0,
            "solid_volume_history": [],
        })

    review_fields = (
        "kinetic_concentration_and_phase_mapping_reviewed",
        "fixed_geometry_volume_basis_reviewed",
        "molar_volume_current_solid_state_and_units_reviewed",
        "no_morphology_or_aperture_inference_reviewed",
    )
    missing = [name for name in review_fields if not getattr(request, name)]
    base = {
        "assessment_id": request.assessment_id,
        "campaign_id": campaign.campaign_id,
        "physical_scope_id": campaign.physical_scope_id,
        "kinetic_campaign_result_sha256": request.kinetic_campaign_result_sha256,
        "kinetic_campaign_input_sha256": source.get("input_sha256"),
        "reference_cross_section_m2": transport.reference_cross_section_m2,
        "cell_volume_per_reference_area_m": cell_volume_per_reference_area,
        "solid_phase_ids": [row.solid_species_id for row in campaign.candidate_solid_phases],
    }
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing, "completed_knot_count": 0, "solid_volume_history": [],
        })
    if not request.molar_volume_evidence:
        return Calculation(status="needs_data", values=base | {"reason": "molar-volume Evidence is required"})

    phase_ids = tuple(row.solid_species_id for row in campaign.candidate_solid_phases)
    times = source.get("elapsed_time_s")
    source_phase_ids = source.get("solid_phase_ids")
    solid_rows = source.get("solid_inventory_mol_m3_by_phase")
    if (
        times != list(transport.output_times_s)
        or source_phase_ids != list(phase_ids)
        or not isinstance(solid_rows, list)
        or len(solid_rows) != len(transport.output_times_s)
    ):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "kinetic phase history knots, phase order or transport clock do not match the typed campaign",
            "completed_knot_count": 0, "solid_volume_history": [],
        })
    if not source.get("inventory_balance_within_declared_tolerance", False):
        return Calculation(status="needs_data", values=base | {
            "reason": "upstream aqueous inventory closure did not satisfy its declared tolerance",
            "completed_knot_count": 0, "solid_volume_history": [],
        })

    evidence_source_id = f"derived-kinetic-result:{request.kinetic_campaign_result_sha256}"
    evidence = request.molar_volume_evidence + (Evidence(
        source_id=evidence_source_id,
        origin="model_prediction",
        citation=f"Computed crevice multiphase kinetic transport result {campaign.campaign_id}",
        sha256=request.kinetic_campaign_result_sha256,
    ),)
    history: list[dict] = []
    for knot_index, (time_s, solid_state) in enumerate(zip(times, solid_rows, strict=True)):
        if not isinstance(solid_state, dict) or set(solid_state) != set(phase_ids):
            return Calculation(status="out_of_scope", values=base | {
                "completed_knot_count": len(history), "solid_volume_history": history,
                "failed_knot_index": knot_index,
                "reason": "solid phase state is missing or has an unexpected identity set",
            })
        areal_inventory: dict[str, tuple[float, ...]] = {}
        invalid_phase: str | None = None
        for phase_id in phase_ids:
            concentrations = solid_state[phase_id]
            if not isinstance(concentrations, list) or len(concentrations) != transport.cell_count:
                invalid_phase = phase_id
                break
            amounts = []
            for concentration, volume_per_area in zip(concentrations, cell_volume_per_reference_area, strict=True):
                if (
                    isinstance(concentration, bool) or not isinstance(concentration, (int, float))
                    or not math.isfinite(concentration) or concentration < 0
                ):
                    invalid_phase = phase_id
                    break
                amount = float(concentration) * volume_per_area
                if not math.isfinite(amount):
                    invalid_phase = phase_id
                    break
                amounts.append(amount)
            if invalid_phase:
                break
            areal_inventory[phase_id] = tuple(amounts)
        if invalid_phase:
            return Calculation(status="out_of_scope", values=base | {
                "completed_knot_count": len(history), "solid_volume_history": history,
                "failed_knot_index": knot_index, "failed_solid_phase_id": invalid_phase,
                "reason": "kinetic phase concentration cannot be converted to finite nonnegative areal inventory",
            })
        digest_state = {
            "physical_scope_id": campaign.physical_scope_id,
            "elapsed_time_s": float(time_s),
            "phase_ids": phase_ids,
            "cell_solid_inventory_mol_m2_by_phase": areal_inventory,
            "solid_molar_volume_m3_mol_by_phase": request.solid_molar_volume_m3_mol_by_phase,
        }
        inventory_request = CreviceSolidVolumeInventoryRequest(
            assessment_id=f"{request.assessment_id}:knot:{knot_index}",
            physical_scope_id=campaign.physical_scope_id,
            elapsed_time_s=float(time_s),
            phase_ids=phase_ids,
            cell_solid_inventory_mol_m2_by_phase=areal_inventory,
            solid_molar_volume_m3_mol_by_phase=request.solid_molar_volume_m3_mol_by_phase,
            inventory_state_sha256=canonical_digest(digest_state),
            evidence=evidence,
            phase_inventory_basis_reviewed=True,
            molar_volume_state_and_units_reviewed=True,
            reference_area_and_cell_mapping_reviewed=True,
            no_morphology_or_aperture_inference_reviewed=True,
        )
        volume = evaluate_crevice_solid_volume_inventory(inventory_request)
        if volume.status != "computed":
            return Calculation(status=volume.status, values=base | {
                "completed_knot_count": len(history), "solid_volume_history": history,
                "failed_knot_index": knot_index,
                "reason": "solid-volume inventory conversion did not complete",
                "upstream_values": volume.values,
            })
        history.append({
            "knot_index": knot_index,
            "elapsed_time_s": float(time_s),
            "kinetic_solid_state_sha256": canonical_digest(solid_state),
            "cell_solid_inventory_mol_m2_by_phase": {key: list(value) for key, value in areal_inventory.items()},
            "solid_volume_result": volume.model_dump(mode="json"),
            "solid_volume_result_sha256": canonical_digest(volume.model_dump(mode="json")),
        })
    return Calculation(values=base | {
        "status": "computed",
        "completed_knot_count": len(history),
        "solid_volume_history": history,
        "volume_basis": "per fixed kinetic-transport reference cross section; each phase concentration is multiplied by the exact fixed cell liquid-volume-per-reference-area",
        "interpretation_boundary": "Solid inventory concentration is converted to per-area amount using the transport campaign's fixed geometry, then passed through the existing caller-molar-volume ledger. This does not change geometry, redistribute solids or infer deposit morphology.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceKineticSolidVolumeHistoryRequest,
        evaluator=convert_crevice_kinetic_solid_volume_history,
        units={
            "reference_cross_section_m2": "m2",
            "cell_volume_per_reference_area_m": "m3/m2",
            "solid_volume_history[].elapsed_time_s": "s",
            "solid_volume_history[].cell_solid_inventory_mol_m2_by_phase.*": "mol/m2",
            "solid_volume_history[].solid_volume_result.values.cell_solid_volume_per_reference_area_m": "m3/m2",
            "solid_volume_history[].solid_volume_result.values.total_solid_volume_per_reference_area_m": "m3/m2",
        },
        assumptions=(
            "Upstream solid_inventory_mol_m3_by_phase values are per solution volume and their exact species/phase order is bound to the typed kinetic campaign.",
            "Only fixed geometry is accepted; per-reference-area cell liquid volume is the fixed cell area/reference area ratio times cell length.",
            "Caller-provided solid molar volumes apply to each phase and snapshot; the existing solid-volume inventory evaluator performs the volume conversion.",
            "Only a computed upstream campaign with its aqueous inventory closure inside declared tolerance is consumed.",
            "No shape, porosity, adhesion, wall coverage, aperture closure, moving geometry, transport feedback or qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
