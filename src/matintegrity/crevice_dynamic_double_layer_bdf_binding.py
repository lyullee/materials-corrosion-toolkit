"""Bind a lumped dynamic Cdl/Faradaic result to conservative component BDF schedules."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .crevice_component_state_bdf import (
    CALLER_CAPACITIVE_CURRENT_SOURCE_ID,
    FARADAY_CONSTANT_C_MOL,
    CapacitiveCellCurrentSchedule,
    CreviceComponentStateBDFRequest,
    ElectrochemicalSourceExtentSchedule,
    ElectrochemicalSourceReaction,
    IonicFaceCurrentSchedule,
)
from .crevice_dynamic_double_layer_faradaic_history import (
    MODEL_ID as DYNAMIC_HISTORY_MODEL_ID,
    CreviceDynamicDoubleLayerFaradaicHistoryRequest,
    solve_crevice_dynamic_double_layer_faradaic_history,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_dynamic_double_layer_to_component_bdf_binding"
SOURCE_ID = "caller_reviewed_dynamic_double_layer_faradaic_result_to_component_bdf_operator_split"


class DynamicBranchReactionMap(Contract):
    branch_id: str = Field(min_length=1)
    electron_number: int = Field(ge=1, le=64)
    # Positive extent follows the caller reaction record; this sign maps its
    # Faradaic current to the dynamic solver's positive-into-electrode basis.
    current_sign_per_forward_extent: Literal[-1, 1]
    reaction: ElectrochemicalSourceReaction


class CreviceDynamicDoubleLayerBDFBindingRequest(Contract):
    schema_version: Literal["matintegrity.crevice_dynamic_double_layer_bdf_binding.v1"] = (
        "matintegrity.crevice_dynamic_double_layer_bdf_binding.v1"
    )
    assessment_id: str = Field(min_length=1)
    component_state_request: CreviceComponentStateBDFRequest
    dynamic_history_request: CreviceDynamicDoubleLayerFaradaicHistoryRequest
    dynamic_history_result: Calculation
    branch_reaction_maps: tuple[DynamicBranchReactionMap, ...] = Field(min_length=1, max_length=32)
    derived_schedule_license_id: str = Field(min_length=1)
    absolute_current_closure_tolerance_A: float = Field(gt=0.0)
    relative_current_closure_tolerance: float = Field(gt=0.0, le=1e-2)
    branch_electron_and_current_sign_reviewed: bool
    reaction_stoichiometry_and_reservoir_reviewed: bool
    aqueous_electrode_sign_mapping_reviewed: bool
    zero_external_ionic_current_boundary_reviewed: bool
    operator_split_and_no_stage_feedback_reviewed: bool
    derived_schedule_use_authorized: bool

    @model_validator(mode="after")
    def validate_alignment(self):
        bdf, history = self.component_state_request, self.dynamic_history_request
        if bdf.assessment_id != self.assessment_id or history.assessment_id != self.assessment_id:
            raise ValueError("assessment identity must match component and dynamic-history inputs")
        if tuple(bdf.time_s) != tuple(history.time_s) or tuple(
            cell.cell_id for cell in bdf.cells
        ) != tuple(history.cell_ids):
            raise ValueError("exact BDF time and cell order must match the dynamic-history request")
        if (bdf.electrochemical_sources or bdf.capacitive_current_schedule is not None
                or bdf.ionic_face_current_schedule is not None
                or bdf.capacitive_current_schedule_reviewed
                or bdf.ionic_face_current_schedule_reviewed):
            raise ValueError("the base BDF request must not already contain source or current schedules")
        if bdf.solid_equilibrium_mode != "aqueous_only" or bdf.moving_geometry_mode != "fixed_volume":
            raise ValueError("this endpoint adapter supports only aqueous-only fixed-volume component BDF")
        expected_branch_ids = {row.branch_id for row in history.faradaic_branches}
        mapped_ids = [row.branch_id for row in self.branch_reaction_maps]
        if len(set(mapped_ids)) != len(mapped_ids) or set(mapped_ids) != expected_branch_ids:
            raise ValueError("each dynamic Faradaic branch must have exactly one reaction/electron map")
        if not self.derived_schedule_license_id:
            raise ValueError("derived schedules require an explicit caller rights basis")
        if not all((self.branch_electron_and_current_sign_reviewed,
                    self.reaction_stoichiometry_and_reservoir_reviewed,
                    self.aqueous_electrode_sign_mapping_reviewed,
                    self.zero_external_ionic_current_boundary_reviewed,
                    self.operator_split_and_no_stage_feedback_reviewed,
                    self.derived_schedule_use_authorized)):
            raise ValueError("branch, stoichiometry, sign, boundary, split and use reviews are required")
        return self


def _derived_evidence(schedule_digest: str, request: CreviceDynamicDoubleLayerBDFBindingRequest,
                      citation: str) -> Evidence:
    return Evidence(
        source_id=MODEL_ID,
        origin="model_prediction",
        citation=citation,
        license_id=request.derived_schedule_license_id,
        sha256=schedule_digest,
    )


def bind_crevice_dynamic_double_layer_to_component_bdf(
    request: CreviceDynamicDoubleLayerBDFBindingRequest,
) -> Calculation:
    """Convert a committed dynamic history into digest-pinned BDF source schedules.

    Electrode stored-charge/current signs are reversed for the aqueous BDF
    balance. The adapter derives exact-knot Faradaic extents and reconstructs
    zero-boundary face currents from per-cell charge continuity. It never runs
    the BDF solver and does not feed BDF chemistry back into the polarization
    history.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    bdf, history, result = (
        request.component_state_request,
        request.dynamic_history_request,
        request.dynamic_history_result,
    )
    result_values = result.values
    history_digest = canonical_digest(history.model_dump(mode="json"))
    recomputed_result = solve_crevice_dynamic_double_layer_faradaic_history(history)
    if canonical_digest(recomputed_result.model_dump(mode="json")) != canonical_digest(result.model_dump(mode="json")):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "dynamic_history_result_recomputation_mismatch",
            "committed": False,
        })
    if (result.status != "computed" or result_values.get("model_id") != DYNAMIC_HISTORY_MODEL_ID
            or result_values.get("input_sha256") != history_digest or not result_values.get("committed")):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "dynamic_history_result_not_committed_or_digest_matched",
            "committed": False,
        })
    nt, nc = len(bdf.time_s), len(bdf.cells)
    branch_ids = [row.branch_id for row in history.faradaic_branches]
    mappings = {row.branch_id: row for row in request.branch_reaction_maps}
    branch_currents = result_values.get("faradaic_current_A_by_branch_knot_and_cell", [])
    cap_electrode = result_values.get("capacitive_current_A_by_knot_and_cell", [])
    if (len(branch_currents) != len(branch_ids) or any(
        len(branch_rows) != nt or any(len(row) != nc for row in branch_rows)
        for branch_rows in branch_currents
    ) or len(cap_electrode) != nt or any(len(row) != nc for row in cap_electrode)):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "dynamic_history_result_shape_mismatch", "committed": False,
        })

    extent_schedules = []
    source_charge_rate_by_knot_and_cell = [[0.0] * nc for _ in range(nt)]
    for branch_index, branch_id in enumerate(branch_ids):
        mapping = mappings[branch_id]
        reaction = mapping.reaction
        stoich = {term.species_id: term.coefficient for term in reaction.aqueous_species_stoichiometry}
        species_charge = {row.species_id: row.charge_number
                          for row in bdf.cells[0].aqueous_activity_request.system.species}
        if set(stoich) - set(species_charge):
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest,
                "reason": f"reaction_species_not_in_component_state:{branch_id}", "committed": False,
            })
        charge_per_extent = math.fsum(species_charge[sid] * coefficient for sid, coefficient in stoich.items())
        if not math.isclose(
            float(mapping.current_sign_per_forward_extent) * charge_per_extent,
            -float(mapping.electron_number), rel_tol=1e-10, abs_tol=1e-12,
        ):
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest,
                "reason": f"reaction_charge_does_not_match_branch_current:{branch_id}",
                "committed": False,
            })
        rates = []
        for knot in range(nt):
            row_rates = []
            for cell in range(nc):
                current = float(branch_currents[branch_index][knot][cell])
                rate = (float(mapping.current_sign_per_forward_extent) * current /
                        (mapping.electron_number * FARADAY_CONSTANT_C_MOL))
                if not math.isfinite(rate):
                    return Calculation(status="out_of_scope", values={
                        "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                        "input_sha256": digest, "reason": "nonfinite_faradic_extent_rate",
                        "branch_id": branch_id, "committed": False,
                    })
                row_rates.append(rate)
                source_charge_rate_by_knot_and_cell[knot][cell] += charge_per_extent * rate
            rates.append(tuple(row_rates))
        extent_schedules.append(ElectrochemicalSourceExtentSchedule(
            reaction=reaction, extent_rate_mol_s_by_knot_and_cell=tuple(rates),
        ))

    # Positive electrode current is positive into the electrode; BDF capacitive
    # source current is positive into aqueous solution.
    cap_aqueous = tuple(tuple(-float(value) for value in row) for row in cap_electrode)
    cap_record = {"time_s": list(bdf.time_s), "current_A_by_knot_and_cell": [list(row) for row in cap_aqueous]}
    cap_digest = canonical_digest(cap_record)
    cap_evidence = _derived_evidence(
        cap_digest, request,
        f"Derived aqueous capacitive-current schedule from committed dynamic history {history_digest}",
    )
    cap_schedule = CapacitiveCellCurrentSchedule(
        time_s=tuple(bdf.time_s), current_A_by_knot_and_cell=cap_aqueous,
        schedule_sha256=cap_digest, evidence=(cap_evidence,),
    )

    face_rows = []
    closure_rows = []
    max_boundary_residual = 0.0
    for knot in range(nt):
        face = [0.0]
        per_cell = []
        for cell in range(nc):
            cap_current = cap_aqueous[knot][cell]
            faradaic_charge_current = FARADAY_CONSTANT_C_MOL * source_charge_rate_by_knot_and_cell[knot][cell]
            delta = faradaic_charge_current + cap_current
            face.append(face[-1] + delta)
            per_cell.append({
                "cell_id": bdf.cells[cell].cell_id,
                "aqueous_faradaic_charge_current_A": faradaic_charge_current,
                "aqueous_capacitive_current_A": cap_current,
                "face_current_change_A": delta,
            })
        residual = face[-1]
        scale = max(max(abs(value) for value in face), 1e-30)
        allowed = float(request.absolute_current_closure_tolerance_A) + \
            float(request.relative_current_closure_tolerance) * scale
        max_boundary_residual = max(max_boundary_residual, abs(residual))
        closure_rows.append({
            "time_s": bdf.time_s[knot], "cells": per_cell,
            "reconstructed_left_to_right_face_current_A": face,
            "right_external_boundary_current_A": residual,
            "allowed_boundary_residual_A": allowed,
            "closed": abs(residual) <= allowed,
        })
        face_rows.append(tuple(face))
    if any(not row["closed"] for row in closure_rows):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "derived_schedules_do_not_close_zero_external_current_boundaries",
            "maximum_external_boundary_current_residual_A": max_boundary_residual,
            "current_continuity_reconstruction": closure_rows, "committed": False,
        })
    face_record = {
        "time_s": list(bdf.time_s),
        "current_A_by_knot_and_face": [list(row) for row in face_rows],
    }
    face_digest = canonical_digest(face_record)
    face_evidence = _derived_evidence(
        face_digest, request,
        f"Derived ionic face-current schedule from dynamic history {history_digest} and source maps",
    )
    face_schedule = IonicFaceCurrentSchedule(
        time_s=tuple(bdf.time_s), current_A_by_knot_and_face=tuple(face_rows), evidence=(face_evidence,),
    )
    try:
        payload = bdf.model_dump(mode="python")
        payload.update({
            "electrochemical_sources": tuple(extent_schedules),
            "electrochemical_source_stoichiometry_and_reservoir_reviewed": True,
            "capacitive_current_schedule": cap_schedule,
            "capacitive_current_schedule_reviewed": True,
            "ionic_face_current_schedule": face_schedule,
            "ionic_face_current_schedule_reviewed": True,
        })
        bound = CreviceComponentStateBDFRequest.model_validate(payload)
    except (TypeError, ValueError) as exc:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": f"derived_BDF_request_rejected:{exc}",
            "cap_schedule_sha256": cap_digest, "face_schedule_sha256": face_digest,
            "committed": False,
        })
    bound_digest = canonical_digest(bound.model_dump(mode="json"))
    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "dynamic_history_request_sha256": history_digest,
        "dynamic_history_result_sha256": canonical_digest(result.model_dump(mode="json")),
        "component_state_request": bound.model_dump(mode="json"),
        "component_state_request_sha256": bound_digest,
        "derived_capacitive_schedule_sha256": cap_digest,
        "derived_ionic_face_schedule_sha256": face_digest,
        "maximum_external_boundary_current_residual_A": max_boundary_residual,
        "current_continuity_reconstruction": closure_rows,
        "derived_faradaic_extent_rates_mol_s_by_branch_knot_and_cell": {
            branch_ids[i]: [list(row) for row in schedule.extent_rate_mol_s_by_knot_and_cell]
            for i, schedule in enumerate(extent_schedules)
        },
        "operator_split": True,
        "component_state_BDF_executed": False,
        "polarization_history_fed_back_from_BDF": False,
        "qualification_claimed": False,
    }, notes=(
        "The dynamic electrode history is solved first and bound as exact-knot Faradaic extent and aqueous capacitive-current schedules.",
        "The component-state BDF then consumes linearly reconstructed schedules; it does not feed its evolving chemistry back into the potential solve.",
        "Zero external ionic-current boundaries must close at every knot. Spatial electrolyte potential, moving geometry and qualification remain separate.",
    ))


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        MODEL_ID,
        CreviceDynamicDoubleLayerBDFBindingRequest,
        bind_crevice_dynamic_double_layer_to_component_bdf,
        {
            "derived_capacitive_schedule_sha256": "1",
            "derived_ionic_face_schedule_sha256": "1",
            "maximum_external_boundary_current_residual_A": "A",
            "derived_faradaic_extent_rates_mol_s_by_branch_knot_and_cell[][][]": "mol/s",
        },
        (
            "Caller maps every signed polarization branch to an evidenced aqueous reaction and electron number.",
            "Dynamic electrode currents are reversed to the aqueous BDF convention and derived exact-knot schedules must satisfy zero external ionic-current boundary closure.",
            "This is an operator-split schedule handoff, not a simultaneous potential/speciation/BDF solve.",
        ),
        (SOURCE_ID, DYNAMIC_HISTORY_MODEL_ID),
        qualification="user_model",
    ),)
