"""Faradaic cellwise metal-loss mapping for a pinned spatial crevice current history."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec


MODEL_ID = "integration.crevice_spatial_ohmic_partial_current_metal_loss"
UPSTREAM_MODEL_ID = "integration.crevice_spatial_ohmic_mixed_potential"
SOURCE_ID = "caller_crevice_spatial_dissolution_branch_mapping"
METHOD_SOURCE_ID = "piecewise_linear_positive_spatial_current_faraday_recession"
FARADAY_CONSTANT_C_MOL = 96485.33212


class CreviceSpatialDissolutionBranchMapping(Contract):
    """Caller-reviewed interpretation of one spatial reaction-current branch."""

    reaction_id: str = Field(min_length=1)
    metal_species_id: str = Field(min_length=1)
    electron_count: int = Field(gt=0, le=64)
    metal_moles_per_reaction_extent: Positive
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    current_efficiency: float = Field(gt=0, le=1)
    reactive_area_m2_by_cell: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    mapping_record_id: str = Field(min_length=1)
    mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=32)
    anodic_positive_sign_reviewed: bool
    branch_is_metal_dissolution_reviewed: bool
    area_mapping_and_uniform_cell_recession_reviewed: bool


class CreviceSpatialMetalLossRequest(Contract):
    """Map selected spatial anodic branches to conditional cellwise Faradaic loss."""

    assessment_id: str = Field(min_length=1)
    upstream_result: AssessmentResult
    upstream_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mappings: tuple[CreviceSpatialDissolutionBranchMapping, ...] = Field(min_length=1, max_length=64)
    piecewise_linear_current_between_knots_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_upstream_and_mappings(self):
        result = self.upstream_result
        if result.model_id != UPSTREAM_MODEL_ID or result.status != "computed":
            raise ValueError("a computed spatial ohmic mixed-potential result is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("upstream assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.upstream_result_sha256:
            raise ValueError("upstream result digest mismatch")
        values = result.values
        cell_ids = values.get("cell_ids")
        history = values.get("state_history")
        if not isinstance(cell_ids, list) or len(cell_ids) < 2 or len(set(cell_ids)) != len(cell_ids):
            raise ValueError("upstream result must provide unique ordered cell IDs")
        if not isinstance(history, list) or len(history) < 2:
            raise ValueError("upstream result requires at least two computed time knots")
        reaction_ids: tuple[str, ...] | None = None
        times: list[float] = []
        for index, knot in enumerate(history):
            if not isinstance(knot, dict):
                raise ValueError("upstream time knots must be objects")
            time_s = knot.get("time_s")
            if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s):
                raise ValueError("each upstream knot needs a finite time")
            times.append(float(time_s))
            branches = knot.get("reaction_branches")
            if not isinstance(branches, list) or not branches:
                raise ValueError("each knot must contain spatial reaction branches")
            ids = tuple(row.get("reaction_id") for row in branches if isinstance(row, dict))
            if len(ids) != len(branches) or any(not isinstance(item, str) or not item.strip() for item in ids):
                raise ValueError("each branch must have a valid reaction identity")
            if len(ids) != len(set(ids)):
                raise ValueError("reaction IDs must be unique at each knot")
            if reaction_ids is None:
                reaction_ids = ids
            elif ids != reaction_ids:
                raise ValueError("branch identities and ordering must remain fixed across knots")
            for row in branches:
                density = row.get("signed_current_density_A_m2_by_cell")
                if (not isinstance(density, list) or len(density) != len(cell_ids)
                        or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                               for v in density)):
                    raise ValueError("each branch current-density vector must align with cells and be finite")
            if len(knot.get("solution_potential_V_by_cell_relative_to_cell_0", [])) != len(cell_ids):
                raise ValueError("upstream potential vectors must align with the declared cell order")
            if index and times[-1] <= times[-2]:
                raise ValueError("upstream times must strictly increase")
        mapping_ids = [row.reaction_id for row in self.mappings]
        if len(mapping_ids) != len(set(mapping_ids)):
            raise ValueError("selected dissolution mappings must have unique reaction IDs")
        if not set(mapping_ids).issubset(set(reaction_ids or ())):
            raise ValueError("every mapped reaction must exist in the upstream result")
        for mapping in self.mappings:
            if len(mapping.reactive_area_m2_by_cell) != len(cell_ids):
                raise ValueError("each branch area vector must match the upstream cell order")
            if not any(
                item.source_id == SOURCE_ID and item.sha256 == mapping.mapping_sha256
                for item in mapping.evidence
            ):
                raise ValueError("branch mapping Evidence must match its source ID and declared digest")
        return self


def _positive_linear_charge_density(start: float, end: float, duration: float) -> float:
    """Exact integral of the positive part of a linearly reconstructed current density."""
    if start >= 0.0 and end >= 0.0:
        return duration * (start + end) / 2.0
    if start <= 0.0 and end <= 0.0:
        return 0.0
    if start > 0.0:
        fraction = start / (start - end)
        return duration * start * fraction / 2.0
    fraction = end / (end - start)
    return duration * end * fraction / 2.0


def evaluate_crevice_spatial_metal_loss(request: CreviceSpatialMetalLossRequest) -> Calculation:
    """Integrate selected positive anodic currents per cell and apply explicit Faraday mapping."""
    upstream = request.upstream_result
    values = upstream.values
    history = values["state_history"]
    cell_ids = values["cell_ids"]
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": values.get("asset_id"),
        "location_id": values.get("location_id"),
        "physical_scope_id": values.get("physical_scope_id"),
        "clock_id": values.get("clock_id"),
        "upstream_model_id": upstream.model_id,
        "upstream_result_sha256": request.upstream_result_sha256,
        "upstream_input_sha256": upstream.input_digest,
        "cell_ids": cell_ids,
        "input_sha256": input_digest,
        "integration_method": "exact_positive_part_of_piecewise_linear_current_density_per_cell",
        "faraday_constant_C_mol": FARADAY_CONSTANT_C_MOL,
    }
    missing = []
    if not request.piecewise_linear_current_between_knots_reviewed:
        missing.append("piecewise_linear_current_between_knots_reviewed")
    if not request.computational_use_authorized:
        missing.append("computational_use_authorized")
    for mapping in request.mappings:
        if not mapping.anodic_positive_sign_reviewed:
            missing.append(f"{mapping.reaction_id}:anodic_positive_sign_reviewed")
        if not mapping.branch_is_metal_dissolution_reviewed:
            missing.append(f"{mapping.reaction_id}:branch_is_metal_dissolution_reviewed")
        if not mapping.area_mapping_and_uniform_cell_recession_reviewed:
            missing.append(f"{mapping.reaction_id}:area_mapping_and_uniform_cell_recession_reviewed")
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    mapping_by_id = {mapping.reaction_id: mapping for mapping in request.mappings}
    selected_history = []
    cumulative_by_branch: dict[str, list[float]] = {
        key: [0.0] * len(cell_ids) for key in mapping_by_id
    }
    cumulative_knots: list[dict[str, list[float]]] = [
        {key: [0.0] * len(cell_ids) for key in mapping_by_id}
    ]
    cumulative_interval_rows = []
    for left, right in zip(history[:-1], history[1:], strict=True):
        duration = float(right["time_s"] - left["time_s"])
        interval_rows = []
        for reaction_id, mapping in mapping_by_id.items():
            left_density = {
                row["reaction_id"]: row["signed_current_density_A_m2_by_cell"]
                for row in left["reaction_branches"]
            }[reaction_id]
            right_density = {
                row["reaction_id"]: row["signed_current_density_A_m2_by_cell"]
                for row in right["reaction_branches"]
            }[reaction_id]
            cell_rows = []
            for cell_index, cell_id in enumerate(cell_ids):
                anodic_charge_density = _positive_linear_charge_density(
                    float(left_density[cell_index]), float(right_density[cell_index]), duration
                )
                charge = anodic_charge_density * mapping.reactive_area_m2_by_cell[cell_index]
                extent = charge * mapping.current_efficiency / (mapping.electron_count * FARADAY_CONSTANT_C_MOL)
                metal_moles = extent * mapping.metal_moles_per_reaction_extent
                mass = metal_moles * mapping.metal_molar_mass_kg_mol
                recession = mass / (mapping.metal_density_kg_m3 * mapping.reactive_area_m2_by_cell[cell_index])
                cumulative_by_branch[reaction_id][cell_index] += recession
                cell_rows.append({
                    "cell_id": cell_id,
                    "start_signed_current_density_A_m2": float(left_density[cell_index]),
                    "end_signed_current_density_A_m2": float(right_density[cell_index]),
                    "gross_anodic_charge_C": charge,
                    "reaction_extent_mol": extent,
                    "metal_dissolved_mol": metal_moles,
                    "mass_loss_kg": mass,
                    "uniform_cell_area_recession_m": recession,
                    "cumulative_uniform_cell_area_recession_m": cumulative_by_branch[reaction_id][cell_index],
                })
            interval_rows.append({"reaction_id": reaction_id, "metal_species_id": mapping.metal_species_id,
                                  "cells": cell_rows})
        cumulative_interval_rows.append({
            "start_time_s": float(left["time_s"]), "end_time_s": float(right["time_s"]),
            "duration_s": duration, "mapped_reaction_branches": interval_rows,
        })
        cumulative_knots.append({key: list(vector) for key, vector in cumulative_by_branch.items()})

    for knot_index, knot in enumerate(history):
        by_branch = []
        for reaction_id, mapping in mapping_by_id.items():
            branch = next(row for row in knot["reaction_branches"] if row["reaction_id"] == reaction_id)
            by_branch.append({
                "reaction_id": reaction_id,
                "signed_current_density_A_m2_by_cell": branch["signed_current_density_A_m2_by_cell"],
                "cumulative_gross_anodic_uniform_recession_m_by_cell": cumulative_knots[knot_index][reaction_id],
                "cell_areas_m2": list(mapping.reactive_area_m2_by_cell),
            })
        selected_history.append({"time_s": float(knot["time_s"]), "branches": by_branch})
    return Calculation(status="computed", values=base | {
        "selected_reaction_count": len(mapping_by_id),
        "state_history": selected_history,
        "interval_ledger": cumulative_interval_rows,
        "branch_totals": [
            {
                "reaction_id": reaction_id,
                "metal_species_id": mapping_by_id[reaction_id].metal_species_id,
                "gross_anodic_charge_C": math.fsum(
                    cell["gross_anodic_charge_C"]
                    for interval in cumulative_interval_rows
                    for branch in interval["mapped_reaction_branches"] if branch["reaction_id"] == reaction_id
                    for cell in branch["cells"]
                ),
                "total_metal_dissolved_mol": math.fsum(
                    cell["metal_dissolved_mol"]
                    for interval in cumulative_interval_rows
                    for branch in interval["mapped_reaction_branches"] if branch["reaction_id"] == reaction_id
                    for cell in branch["cells"]
                ),
                "cumulative_uniform_cell_area_recession_m_by_cell": cumulative_by_branch[reaction_id],
            }
            for reaction_id in mapping_by_id
        ],
        "interpretation": "conditional_gross_anodic_Faradaic_equivalent_per_fixed_cell_area",
        "limitations": [
            "Only selected caller-reviewed anodic-positive branches are mapped; cathodic current is excluded and redeposition is not inferred.",
            "Electron count, metal stoichiometry, efficiency, molar mass, density and per-cell reactive area are caller supplied.",
            "Upstream knots are quasi-steady snapshots. The declared piecewise-linear current reconstruction is an integration convention, not within-interval electrochemical dynamics.",
            "Uniform recession per fixed cell area is a mapped average and does not resolve pits, undercutting, roughness, corrosion rate qualification, life, probability or acceptance.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSpatialMetalLossRequest,
        evaluator=evaluate_crevice_spatial_metal_loss,
        units={
            "state_history[].time_s": "s",
            "state_history[].branches[].signed_current_density_A_m2_by_cell[]": "A/m^2",
            "interval_ledger[].mapped_reaction_branches[].cells[].gross_anodic_charge_C": "C",
            "branch_totals[].total_metal_dissolved_mol": "mol",
            "interval_ledger[].mapped_reaction_branches[].cells[].mass_loss_kg": "kg",
            "branch_totals[].cumulative_uniform_cell_area_recession_m_by_cell[]": "m",
        },
        assumptions=(
            "A computed spatial ohmic mixed-potential history is the sole current source and is pinned by its complete AssessmentResult digest.",
            "Only explicitly selected anodic-positive dissolution branches are integrated; the caller owns branch chemistry and Faraday mapping.",
            "Per-cell reactive areas are fixed and caller reviewed; local recession is uniform over each mapped cell area.",
        ),
        source_ids=(SOURCE_ID, METHOD_SOURCE_ID, "electrochemical_partial_current_to_metal_loss"),
    )]
