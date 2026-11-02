"""Compose explicit per-bolt influence into the existing unilateral contact request."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec
from .flange_contact_field import FlangeContactFieldRequest


MODEL_ID = "integration.multi_bolt_joint_to_flange_contact_request"
SOURCE_ID = "caller_multi_bolt_to_spatial_flange_contact_influence"
CONTACT_METHOD_SOURCE_ID = "caller_spatial_flange_contact_compliance"
UPSTREAM_MODEL_ID = "fabrication.gasket_multi_bolt_sector_equilibrium"


class MultiBoltFlangeContactInfluenceRequest(Contract):
    """Create a normal FlangeContactFieldRequest from a selected multi-bolt step."""

    schema_version: Literal["matintegrity.multi_bolt_flange_contact_influence.v1"] = (
        "matintegrity.multi_bolt_flange_contact_influence.v1"
    )
    assessment_id: str = Field(min_length=1)
    bolt_load_result: AssessmentResult
    bolt_load_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_step_id: str = Field(min_length=1)
    contact_template: FlangeContactFieldRequest
    bolt_ids: tuple[str, ...] = Field(min_length=1, max_length=256)
    bolt_to_node_closure_matrix_m_N: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=256)
    influence_provider_id: str = Field(min_length=1)
    influence_provider_revision: str = Field(min_length=1)
    influence_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    influence_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    influence_usage_license_id: str = Field(min_length=1)
    influence_evidence: tuple[Evidence, ...] = Field(min_length=1)
    bolt_step_scope_and_lineage_reviewed: bool
    bolt_order_to_operator_column_reviewed: bool
    free_closure_excludes_declared_bolt_set_reviewed: bool
    linear_operator_superposition_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_digests_and_operator(self):
        if self.bolt_load_result.model_id != UPSTREAM_MODEL_ID or self.bolt_load_result.status != "computed":
            raise ValueError("a computed multi-bolt sector equilibrium AssessmentResult is required")
        if canonical_digest(self.bolt_load_result.model_dump(mode="json")) != self.bolt_load_result_sha256:
            raise ValueError("bolt-load AssessmentResult digest does not match its declared SHA-256")
        values = self.bolt_load_result.values
        if values.get("joint_id") != self.contact_template.joint_id:
            raise ValueError("bolt-load result and flange contact request must identify the same joint")
        if values.get("physical_scope_id") != self.contact_template.physical_scope_id:
            raise ValueError("bolt-load result and flange contact request must identify the same physical scope")
        steps = values.get("steps")
        if not isinstance(steps, list):
            raise ValueError("bolt-load result must preserve its ordered load-step rows")
        selected = [row for row in steps if isinstance(row, dict) and row.get("step_id") == self.selected_step_id]
        if len(selected) != 1:
            raise ValueError("selected bolt-load step must occur exactly once")
        selected_bolts = selected[0].get("bolts")
        if not isinstance(selected_bolts, list):
            raise ValueError("selected step must contain per-bolt force rows")
        result_bolt_ids = [row.get("bolt_id") for row in selected_bolts if isinstance(row, dict)]
        if len(result_bolt_ids) != len(selected_bolts) or len(set(result_bolt_ids)) != len(result_bolt_ids):
            raise ValueError("selected step bolt rows must have unique explicit identities")
        if set(result_bolt_ids) != set(self.bolt_ids):
            raise ValueError("operator column bolt IDs must match the selected step bolt identities exactly")
        if len(set(self.bolt_ids)) != len(self.bolt_ids):
            raise ValueError("bolt IDs in the operator must be unique")
        node_count = len(self.contact_template.node_ids)
        if len(self.bolt_to_node_closure_matrix_m_N) != node_count:
            raise ValueError("one influence-matrix row is required per contact node")
        if any(len(row) != len(self.bolt_ids) for row in self.bolt_to_node_closure_matrix_m_N):
            raise ValueError("influence-matrix columns must align with bolt_ids")
        if any(not math.isfinite(value) for row in self.bolt_to_node_closure_matrix_m_N for value in row):
            raise ValueError("bolt-to-node influence coefficients must be finite")
        operator_record = {
            "provider_id": self.influence_provider_id,
            "provider_revision": self.influence_provider_revision,
            "configuration_sha256": self.influence_configuration_sha256,
            "node_ids": list(self.contact_template.node_ids),
            "bolt_ids": list(self.bolt_ids),
            "bolt_to_node_closure_matrix_m_N": [list(row) for row in self.bolt_to_node_closure_matrix_m_N],
        }
        if canonical_digest(operator_record) != self.influence_result_sha256:
            raise ValueError("influence result digest does not match provider/configuration/order/matrix content")
        if not any(
            evidence.source_id == self.influence_provider_id
            and evidence.sha256 == self.influence_result_sha256
            and evidence.license_id == self.influence_usage_license_id
            for evidence in self.influence_evidence
        ):
            raise ValueError("influence Evidence must pin the operator digest and declared use license")
        return self


class MultiBoltFlangeContactInfluenceOutput(Contract):
    schema_version: Literal["matintegrity.multi_bolt_flange_contact_influence_output.v1"] = (
        "matintegrity.multi_bolt_flange_contact_influence_output.v1"
    )
    model_id: Literal[MODEL_ID] = MODEL_ID
    assessment_id: str
    joint_id: str
    physical_scope_id: str
    selected_step_id: str
    selected_time_s: float
    bolt_load_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    influence_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contact_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contact_request: FlangeContactFieldRequest
    bolt_force_by_id_N: dict[str, float]
    bolt_closure_contribution_by_node_m: dict[str, float]
    total_free_closure_by_node_m: dict[str, float]
    use_license_id: str
    assumption: Literal["caller_linear_superposition_of_bolt_influence_and_nonbolt_free_closure"] = (
        "caller_linear_superposition_of_bolt_influence_and_nonbolt_free_closure"
    )


def adapt_multi_bolt_joint_to_flange_contact_request(
    request: MultiBoltFlangeContactInfluenceRequest,
) -> Calculation:
    """Compose bolt-induced closure and return input for the established contact solver."""
    digest = canonical_digest(request.model_dump(mode="json"))
    values_base = {
        "assessment_id": request.assessment_id,
        "joint_id": request.contact_template.joint_id,
        "physical_scope_id": request.contact_template.physical_scope_id,
        "selected_step_id": request.selected_step_id,
        "bolt_load_result_sha256": request.bolt_load_result_sha256,
        "influence_result_sha256": request.influence_result_sha256,
        "input_sha256": digest,
    }
    required_reviews = (
        request.bolt_step_scope_and_lineage_reviewed,
        request.bolt_order_to_operator_column_reviewed,
        request.free_closure_excludes_declared_bolt_set_reviewed,
        request.linear_operator_superposition_reviewed,
        request.computational_use_authorized,
        request.contact_template.flange_operator_basis_reviewed,
        request.contact_template.response_scope_and_coordinates_reviewed,
        request.contact_template.bolt_pressure_and_boundary_load_composition_reviewed,
        request.contact_template.gasket_linearization_and_support_reviewed,
        request.contact_template.compression_only_contact_model_reviewed,
        request.contact_template.computational_use_authorized,
    )
    if not all(required_reviews):
        return Calculation(
            status="needs_data",
            values=values_base | {"missing_review_count": sum(not value for value in required_reviews)},
            notes=("Bolt mapping, superposition, contact model, and computational-use reviews are required.",),
        )

    result_values = request.bolt_load_result.values
    steps = result_values.get("steps", [])
    selected = next(row for row in steps if row["step_id"] == request.selected_step_id)
    force_by_id = {
        row["bolt_id"]: row["tensile_force_N"]
        for row in selected["bolts"]
    }
    if any(not isinstance(force, (int, float)) or isinstance(force, bool) or not math.isfinite(force) or force < 0 for force in force_by_id.values()):
        return Calculation(
            status="out_of_scope",
            values=values_base,
            notes=("Selected bolt forces must be finite nonnegative tensile forces.",),
        )
    force_vector = [float(force_by_id[bolt_id]) for bolt_id in request.bolt_ids]
    node_ids = request.contact_template.node_ids
    bolt_closure = []
    total_closure = []
    try:
        for index, influence_row in enumerate(request.bolt_to_node_closure_matrix_m_N):
            displacement = math.fsum(coefficient * force for coefficient, force in zip(influence_row, force_vector, strict=True))
            combined = request.contact_template.free_closure_without_gasket_m[index] + displacement
            if not math.isfinite(displacement) or not math.isfinite(combined):
                raise OverflowError("bolt influence multiplication exceeded finite numeric support")
            bolt_closure.append(displacement)
            total_closure.append(combined)
    except (ArithmeticError, ValueError) as error:
        return Calculation(
            status="out_of_scope",
            values=values_base,
            notes=(f"Bolt-to-node closure mapping failed: {error}",),
        )

    contact_request = request.contact_template.model_copy(
        update={"free_closure_without_gasket_m": tuple(total_closure)}
    )
    contact_request_digest = canonical_digest(contact_request.model_dump(mode="json"))
    output = MultiBoltFlangeContactInfluenceOutput(
        assessment_id=request.assessment_id,
        joint_id=contact_request.joint_id,
        physical_scope_id=contact_request.physical_scope_id,
        selected_step_id=request.selected_step_id,
        selected_time_s=selected["time_s"],
        bolt_load_result_sha256=request.bolt_load_result_sha256,
        influence_result_sha256=request.influence_result_sha256,
        contact_request_sha256=contact_request_digest,
        contact_request=contact_request,
        bolt_force_by_id_N=force_by_id,
        bolt_closure_contribution_by_node_m=dict(zip(node_ids, bolt_closure, strict=True)),
        total_free_closure_by_node_m=dict(zip(node_ids, total_closure, strict=True)),
        use_license_id=request.influence_usage_license_id,
    )
    return Calculation(
        values=output.model_dump(mode="json"),
        notes=(
            "This adapter composes caller-supplied per-bolt displacement influence with the declared non-bolt free closure and emits a typed request for the existing unilateral flange contact solver.",
            "The flange compliance symmetry/positive-semidefinite support checks and gasket contact complementarity solve remain the responsibility of the downstream flange-contact API.",
            "No FE response is generated; no local stress, leakage, seal acceptance, or qualification is inferred.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            MultiBoltFlangeContactInfluenceRequest,
            adapt_multi_bolt_joint_to_flange_contact_request,
            {
                "selected_time_s": "s",
                "bolt_force_by_id_N": "N",
                "bolt_closure_contribution_by_node_m": "m",
                "total_free_closure_by_node_m": "m",
                "contact_request.free_closure_without_gasket_m": "m",
                "contact_request.flange_relative_compliance_matrix_m_N": "m/N",
            },
            (
                "Bolt force comes from a digest-pinned computed multi-bolt equilibrium AssessmentResult at one exact named knot.",
                "Bolt-to-node closure influence is a caller-supplied linear operator ordered by explicit bolt and flange contact-node identities.",
                "The base free-closure vector must exclude the exact bolt set represented by the influence matrix; the two contributions are superposed once.",
                "The output is a new typed FlangeContactFieldRequest. The downstream flange solver checks compliance support/symmetry/positive-semidefinite conditions and unilateral contact equilibrium.",
                "No FE response, local stress, leakage, seal acceptance, or qualification is provided.",
            ),
            (SOURCE_ID, CONTACT_METHOD_SOURCE_ID),
            qualification="user_model",
        )
    ]
