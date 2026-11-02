"""Caller-declared elemental accounting for computed aqueous/solid histories."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from ..registry import ModelSpec


class ElementalComponent(Contract):
    """Explicit elemental formula for one already-computed species/phase ID."""

    component_id: str = Field(min_length=1)
    phase: Literal["aqueous_species", "solid_phase"]
    atom_counts: dict[str, int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_counts(self):
        if any(not key.strip() or isinstance(value, bool) or not isinstance(value, int) or value < 0
               for key, value in self.atom_counts.items()):
            raise ValueError("element symbols must be nonempty and atom counts nonnegative integers")
        if not any(self.atom_counts.values()):
            raise ValueError("each mapped species or phase must contain at least one declared atom")
        return self


class WetCO2PhaseHistoryHandoff(Contract):
    """Map a computed transport/phase output into element-resolved inventory receipts.

    Concentrations are read from the provider's output without recomputation. Cell
    solution volumes and formulas are caller-supplied and digest-bound. The handoff
    reports inventory differences; it does not infer reaction extents or kinetics.
    """

    campaign_id: str = Field(min_length=1)
    source_provider_id: str = Field(min_length=1)
    source_provider_revision: str = Field(min_length=1)
    source_assessment_result: AssessmentResult | None = None
    source_assessment_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    source_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_values: dict
    cell_solution_volume_m3: tuple[Positive, ...] = Field(min_length=1)
    components: tuple[ElementalComponent, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = ()
    formulas_and_cell_volume_basis_reviewed: bool
    provider_species_and_phase_id_mapping_reviewed: bool

    @model_validator(mode="after")
    def validate_mapping(self):
        ids = [(row.phase, row.component_id) for row in self.components]
        if len(ids) != len(set(ids)):
            raise ValueError("elemental component mappings must be unique by phase and component ID")
        if canonical_digest(self.source_values) != self.source_result_digest:
            raise ValueError("source result digest must match the supplied computed values payload")
        if not any(row.source_id == self.source_provider_id and row.sha256 == self.source_result_digest
                   for row in self.evidence):
            raise ValueError("source provider result digest must be linked to matching Evidence")
        if (self.source_assessment_result is None) != (self.source_assessment_result_sha256 is None):
            raise ValueError("upstream AssessmentResult and its digest must be supplied together")
        if self.source_assessment_result is not None:
            result = self.source_assessment_result
            expected_input = canonical_digest({
                "model_id": result.model_id,
                "model_version": result.model_version,
                "inputs": result.inputs,
                "context": result.context.model_dump(mode="json"),
            })
            if result.status != "computed" or result.input_digest != expected_input:
                raise ValueError("upstream AssessmentResult must be computed with a matching input/context digest")
            if canonical_digest(result.model_dump(mode="json")) != self.source_assessment_result_sha256:
                raise ValueError("upstream AssessmentResult digest mismatch")
            if canonical_digest(result.values) != self.source_result_digest or result.values != self.source_values:
                raise ValueError("upstream AssessmentResult values must exactly match the pinned source payload")
            if (result.context.asset_id, result.context.location_id, result.context.time_basis) != (
                self.asset_id, self.location_id, self.time_basis
            ):
                raise ValueError("upstream AssessmentResult context must match caller source identity")
        return self


def wet_co2_elemental_phase_handoff(x: WetCO2PhaseHistoryHandoff) -> Calculation:
    """Produce per-element aqueous, solid, and combined inventory histories."""
    input_digest = canonical_digest(x.model_dump(mode="json"))
    values = x.source_values
    base = {
        "campaign_id": x.campaign_id,
        "source_provider_id": x.source_provider_id,
        "source_provider_revision": x.source_provider_revision,
        "source_result_digest": x.source_result_digest,
        "source_assessment_result_sha256": x.source_assessment_result_sha256,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "time_basis": x.time_basis,
        "input_digest": input_digest,
        "component_mapping_sha256": canonical_digest([row.model_dump(mode="json") for row in x.components]),
        "cell_solution_volume_sha256": canonical_digest(x.cell_solution_volume_m3),
        "evidence_sha256": canonical_digest([row.model_dump(mode="json") for row in x.evidence]),
        "formulas_and_cell_volume_basis_reviewed": x.formulas_and_cell_volume_basis_reviewed,
        "provider_species_and_phase_id_mapping_reviewed": x.provider_species_and_phase_id_mapping_reviewed,
    }
    if not (x.formulas_and_cell_volume_basis_reviewed and x.provider_species_and_phase_id_mapping_reviewed):
        return Calculation(status="needs_data", values=base | {"reason": "mapping_or_basis_review_required"})
    if values.get("status") != "computed":
        return Calculation(status="out_of_scope", values=base | {"reason": "source_result_not_computed"})
    species_ids = values.get("species_ids")
    solid_ids = values.get("solid_species_ids")
    aqueous = values.get("concentration_after_phase_mol_m3")
    solids = values.get("solid_moles_per_solution_volume_mol_m3")
    times = values.get("elapsed_time_s")
    if (not isinstance(species_ids, list) or not isinstance(solid_ids, list)
            or not isinstance(aqueous, list) or not isinstance(solids, list)
            or not isinstance(times, list) or not species_ids or not aqueous or not times):
        return Calculation(status="out_of_scope", values=base | {"reason": "source_history_fields_missing"})
    if (not isinstance(aqueous[0], list) or not aqueous[0] or not isinstance(aqueous[0][0], list) or not aqueous[0][0]
            or len(x.cell_solution_volume_m3) != len(aqueous[0][0])
            or len(aqueous) != len(times) or len(solids) != len(times)):
        return Calculation(status="out_of_scope", values=base | {"reason": "source_history_dimensions_mismatch"})
    component_map = {(row.phase, row.component_id): row.atom_counts for row in x.components}
    if {key[1] for key in component_map if key[0] == "aqueous_species"} != set(species_ids):
        return Calculation(status="needs_data", values=base | {"reason": "aqueous_species_formula_mapping_incomplete"})
    if {key[1] for key in component_map if key[0] == "solid_phase"} != set(solid_ids):
        return Calculation(status="needs_data", values=base | {"reason": "solid_phase_formula_mapping_incomplete"})
    if (any(not isinstance(row, list) or len(row) != len(species_ids)
            or any(not isinstance(v, list) or len(v) != len(x.cell_solution_volume_m3) for v in row)
            for row in aqueous)):
        return Calculation(status="out_of_scope", values=base | {"reason": "aqueous_history_dimensions_mismatch"})
    if (any(not isinstance(row, list) or len(row) != len(x.cell_solution_volume_m3)
            or any(not isinstance(v, list) or len(v) != len(solid_ids) for v in row)
            for row in solids)):
        return Calculation(status="out_of_scope", values=base | {"reason": "solid_history_dimensions_mismatch"})
    if (any(isinstance(time, bool) or not isinstance(time, (int, float)) or not math.isfinite(time)
            for time in times) or times[0] != 0
            or any(right <= left for left, right in zip(times[:-1], times[1:]))):
        return Calculation(status="out_of_scope", values=base | {"reason": "invalid_source_clock"})
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
           for history in aqueous for species in history for value in species):
        return Calculation(status="out_of_scope", values=base | {"reason": "invalid_aqueous_concentration"})
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
           for history in solids for cell in history for value in cell):
        return Calculation(status="out_of_scope", values=base | {"reason": "invalid_solid_inventory"})
    elements = sorted({element for formula in component_map.values() for element in formula})
    result = {}
    for element in elements:
        aqueous_history, solid_history, total_history = [], [], []
        for k in range(len(times)):
            aqueous_terms = []
            for i, species_id in enumerate(species_ids):
                coefficient = component_map[("aqueous_species", species_id)].get(element, 0)
                for cell, volume in enumerate(x.cell_solution_volume_m3):
                    aqueous_terms.append(coefficient * float(aqueous[k][i][cell]) * volume)
            solid_terms = []
            for i, solid_id in enumerate(solid_ids):
                coefficient = component_map[("solid_phase", solid_id)].get(element, 0)
                for cell, volume in enumerate(x.cell_solution_volume_m3):
                    solid_terms.append(coefficient * float(solids[k][cell][i]) * volume)
            try:
                aq_total = math.fsum(aqueous_terms)
                solid_total = math.fsum(solid_terms)
            except OverflowError:
                return Calculation(status="out_of_scope", values=base | {"reason": "inventory_overflow"})
            if not math.isfinite(aq_total) or not math.isfinite(solid_total) or not math.isfinite(aq_total + solid_total):
                return Calculation(status="out_of_scope", values=base | {"reason": "inventory_overflow"})
            aqueous_history.append(aq_total)
            solid_history.append(solid_total)
            total_history.append(aq_total + solid_total)
        result[element] = {
            "aqueous_inventory_mol": aqueous_history,
            "solid_inventory_mol": solid_history,
            "combined_inventory_mol": total_history,
            "combined_change_from_initial_mol": [v - total_history[0] for v in total_history],
        }
    return Calculation(values=base | {
        "elapsed_time_s": times,
        "element_ids": elements,
        "element_inventory": result,
        "basis": "Caller-declared formula mappings and cell volumes applied to an already-computed phase/transport history; transport boundary fluxes and omitted pools are not inferred.",
    })


def _validate_context(x: WetCO2PhaseHistoryHandoff, context: RunContext) -> None:
    if (x.asset_id, x.location_id, x.time_basis) != (context.asset_id, context.location_id, context.time_basis):
        raise ValueError("handoff RunContext must match caller-declared asset, location and time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.wet_co2_elemental_phase_handoff",
        WetCO2PhaseHistoryHandoff,
        wet_co2_elemental_phase_handoff,
        {"elapsed_time_s[]": "s", "element_inventory[].aqueous_inventory_mol[]": "mol",
         "element_inventory[].solid_inventory_mol[]": "mol",
         "element_inventory[].combined_inventory_mol[]": "mol"},
        (
            "Only an already-computed source result payload with matching digest and exact species/phase formula mappings is consumed.",
            "Caller-provided cell solution volumes and formulas are required; boundary flux closure, omitted pools, reaction extents and kinetics are not inferred.",
        ),
        ("caller_declared_wet_co2_elemental_phase_history_handoff",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
