"""Bind caller elastic-joint clamp snapshots to the existing spatial contact solver."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Nonnegative, canonical_digest
from .gasket_joint_load_history import (
    ElasticJointLoadHistoryRequest,
    evaluate_elastic_joint_load_history,
)
from .models.flange_contact_field import FlangeContactFieldRequest, flange_contact_field
from .registry import ModelSpec


class ElasticJointToFlangeContactHistory(Contract):
    """Apply a caller-provided linear closure-per-clamp-force map at exact snapshots."""

    schema_version: Literal["matintegrity.elastic_joint_to_flange_contact_history.v1"] = (
        "matintegrity.elastic_joint_to_flange_contact_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    joint_load_history: ElasticJointLoadHistoryRequest
    contact_template: FlangeContactFieldRequest
    reference_clamp_force_N: Nonnegative
    nodal_free_closure_change_m_per_N: tuple[float, ...] = Field(min_length=2, max_length=256)
    clamp_to_nodal_closure_mapping_reviewed: bool
    transfer_scope_and_reference_state_reviewed: bool
    linear_incremental_response_and_fixed_other_loads_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_transfer(self):
        if self.contact_template.joint_id != self.joint_id:
            raise ValueError("contact template joint ID must match the adapter joint ID")
        if len(self.nodal_free_closure_change_m_per_N) != len(self.contact_template.node_ids):
            raise ValueError("nodal transfer vector must align with the contact template node order")
        if any(not math.isfinite(value) for value in self.nodal_free_closure_change_m_per_N):
            raise ValueError("nodal clamp-to-closure transfer values must be finite")
        return self


def evaluate_elastic_joint_to_flange_contact_history(
    request: ElasticJointToFlangeContactHistory,
) -> Calculation:
    """Run the existing load and contact solvers at aligned exact input knots."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "joint_id": request.joint_id,
        "physical_scope_id": request.contact_template.physical_scope_id,
        "load_history_id": request.joint_load_history.history_id,
        "load_history_input_sha256": canonical_digest(request.joint_load_history.model_dump(mode="json")),
        "contact_template_sha256": canonical_digest(request.contact_template.model_dump(mode="json")),
        "transfer_vector_sha256": canonical_digest(list(request.nodal_free_closure_change_m_per_N)),
        "input_sha256": input_digest,
        "time_policy": "exact_caller_snapshots_only_no_interpolation",
        "automatic_flange_response_or_material_law": False,
    }
    reviews = {
        "clamp_to_nodal_closure_mapping_reviewed": request.clamp_to_nodal_closure_mapping_reviewed,
        "transfer_scope_and_reference_state_reviewed": request.transfer_scope_and_reference_state_reviewed,
        "linear_incremental_response_and_fixed_other_loads_reviewed": request.linear_incremental_response_and_fixed_other_loads_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "completed_contact_knot_count": 0,
            "contact_history": [],
        })

    load_result = evaluate_elastic_joint_load_history(request.joint_load_history)
    if load_result.status != "computed":
        return Calculation(status=load_result.status, values=base | {
            "load_history_result_sha256": canonical_digest(load_result.model_dump(mode="json")),
            "load_history_result": load_result.model_dump(mode="json"),
            "completed_contact_knot_count": 0,
            "contact_history": [],
            "contact_solver_started": False,
        }, notes=("Spatial contact is withheld unless the complete upstream clamp-load history computes.",))
    load_rows = load_result.values.get("joint_load_history")
    if not isinstance(load_rows, list) or len(load_rows) != len(request.joint_load_history.knots):
        return Calculation(status="out_of_scope", values=base | {
            "load_history_result_sha256": canonical_digest(load_result.model_dump(mode="json")),
            "reason": "computed_joint_load_history_does_not_align_with_requested_knots",
            "contact_history": [],
        })

    contact_rows = []
    for index, (load_knot, load_row) in enumerate(zip(request.joint_load_history.knots, load_rows, strict=True)):
        if load_row.get("time_s") != load_knot.time_s or load_row.get("knot_index") != load_knot.knot_index:
            return Calculation(status="out_of_scope", values=base | {
                "load_history_result_sha256": canonical_digest(load_result.model_dump(mode="json")),
                "completed_contact_knot_count": len(contact_rows),
                "contact_history": contact_rows,
                "failed_knot_index": index,
                "reason": "load_history_result_knot_identity_does_not_match_request",
            })
        clamp_force = load_row.get("clamp_force_N")
        if isinstance(clamp_force, bool) or not isinstance(clamp_force, (float, int)) or not math.isfinite(clamp_force):
            return Calculation(status="out_of_scope", values=base | {
                "load_history_result_sha256": canonical_digest(load_result.model_dump(mode="json")),
                "completed_contact_knot_count": len(contact_rows),
                "contact_history": contact_rows,
                "failed_knot_index": index,
                "failed_time_s": load_knot.time_s,
                "reason": "clamp_force_is_not_finite_at_requested_knot",
            })
        delta_force = float(clamp_force) - request.reference_clamp_force_N
        closure = tuple(
            baseline + transfer * delta_force
            for baseline, transfer in zip(
                request.contact_template.free_closure_without_gasket_m,
                request.nodal_free_closure_change_m_per_N,
                strict=True,
            )
        )
        if any(not math.isfinite(value) for value in closure):
            return Calculation(status="out_of_scope", values=base | {
                "load_history_result_sha256": canonical_digest(load_result.model_dump(mode="json")),
                "completed_contact_knot_count": len(contact_rows),
                "contact_history": contact_rows,
                "failed_knot_index": index,
                "failed_time_s": load_knot.time_s,
                "reason": "transferred_free_closure_exceeds_finite_support",
            })
        payload = request.contact_template.model_dump(mode="python") | {
            "assessment_id": f"{request.contact_template.assessment_id}:knot:{index}",
            "free_closure_without_gasket_m": closure,
        }
        contact_request = FlangeContactFieldRequest.model_validate(payload)
        contact_result = flange_contact_field(contact_request)
        row = {
            "knot_index": index,
            "time_s": load_knot.time_s,
            "load_knot_input_sha256": canonical_digest(load_knot.model_dump(mode="json")),
            "load_knot_result_sha256": canonical_digest(load_row),
            "clamp_force_N": float(clamp_force),
            "delta_from_reference_clamp_force_N": delta_force,
            "transferred_free_closure_without_gasket_m": list(closure),
            "contact_request_sha256": canonical_digest(contact_request.model_dump(mode="json")),
            "contact_result_sha256": canonical_digest(contact_result.model_dump(mode="json")),
            "contact_result": contact_result.model_dump(mode="json"),
            "status": contact_result.status,
        }
        if contact_result.status != "computed":
            return Calculation(status=contact_result.status, values=base | {
                "load_history_result_sha256": canonical_digest(load_result.model_dump(mode="json")),
                "completed_contact_knot_count": len(contact_rows),
                "contact_history": contact_rows + [row],
                "failed_knot_index": index,
                "failed_time_s": load_knot.time_s,
                "contact_solver_started": True,
                "prefix_policy": "only successfully computed exact contact knots are committed",
            })
        contact_rows.append(row)

    return Calculation(values=base | {
        "load_history_result_sha256": canonical_digest(load_result.model_dump(mode="json")),
        "load_history_result": load_result.model_dump(mode="json"),
        "completed_contact_knot_count": len(contact_rows),
        "contact_history": contact_rows,
        "transfer_equation": "free_closure_i(t)=template_free_closure_i+transfer_m_per_N_i*(clamp_force(t)-reference_clamp_force)",
        "contact_path_interpolation": "not_performed",
        "seal_acceptance_or_leakage_inferred": False,
        "material_law_inferred": False,
    }, notes=(
        "Each exact clamp-force snapshot is transformed only by the caller-supplied nodal closure-per-force vector and evaluated with the existing unilateral flange contact solver.",
        "The transfer vector is an explicit caller model; no FE response, contact-load partition, gasket constitutive law or time interpolation is generated by this adapter.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.elastic_joint_to_flange_contact_history",
        input_type=ElasticJointToFlangeContactHistory,
        evaluator=evaluate_elastic_joint_to_flange_contact_history,
        units={
            "joint_load_history.knots[].time_s": "s",
            "joint_load_history_result.values.joint_load_history[].clamp_force_N": "N",
            "reference_clamp_force_N": "N",
            "nodal_free_closure_change_m_per_N[]": "m/N",
            "contact_history[].transferred_free_closure_without_gasket_m[]": "m",
            "contact_history[].contact_result.values.response_field[].mean_contact_pressure_Pa": "Pa",
            "contact_history[].contact_result.values.response_field[].contact_force_N": "N",
        },
        assumptions=(
            "At each exact caller load snapshot, apply only the supplied linear nodal closure-per-clamp-force mapping around its declared reference clamp force, then reuse the existing flange contact field solver.",
            "The caller mapping and fixed other-load baseline require review. No material law, FE compliance response, gasket law or response between snapshots is inferred.",
            "Contact pressure outputs are solver results only and do not establish gasket leak rate, sealing acceptance, qualification or probability.",
        ),
        source_ids=("caller_elastic_joint_to_flange_contact_history_transfer",),
        qualification="user_model",
    )]
