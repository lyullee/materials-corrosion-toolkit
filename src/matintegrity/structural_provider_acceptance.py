"""Tamper-evident receipt and caller acceptance of external structural results."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Evidence, Nonnegative, canonical_digest


class StructuralMeshReceipt(Contract):
    mesh_id: str = Field(min_length=1)
    mesh_revision: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    dimensionality: Literal["axisymmetric", "2d", "3d"]
    element_family_ids: tuple[str, ...] = Field(min_length=1)
    node_count: int = Field(ge=1)
    element_count: int = Field(ge=1)
    mesh_content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class StructuralResultFieldReceipt(Contract):
    field_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    result_location: Literal["node", "element", "integration_point", "face", "edge", "global"]
    averaging_basis: str = Field(min_length=1)
    quantity_id: str = Field(min_length=1)
    quantity_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    component_ids: tuple[str, ...] = Field(min_length=1)
    array_shape: tuple[int, ...] = Field(min_length=1)
    array_order: Literal["C", "F", "provider_native"]
    array_content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def valid_shape(self):
        if any(value < 1 for value in self.array_shape):
            raise ValueError("structural result field dimensions must be positive")
        if len(set(self.component_ids)) != len(self.component_ids):
            raise ValueError("structural result field components must be unique")
        return self


class StructuralDiagnosticEvidence(Contract):
    diagnostic_id: str = Field(min_length=1)
    category: Literal["equilibrium", "convergence", "uncertainty", "verification"]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    status: Literal["reported", "missing", "invalid"]
    value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    provider_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_and_value(self):
        if self.status == "reported":
            if self.value is None or self.expanded_uncertainty is None:
                raise ValueError("reported structural diagnostics require value and uncertainty")
        elif self.value is not None or self.expanded_uncertainty is not None:
            raise ValueError("missing or invalid structural diagnostics cannot carry numeric results")
        return self


class StructuralProviderResultReceipt(Contract):
    schema_version: Literal["matintegrity.structural_provider_receipt.v1"] = (
        "matintegrity.structural_provider_receipt.v1"
    )
    receipt_id: str = Field(min_length=1)
    analysis_kind: Literal["external_pressure", "nozzle_local_stress", "finite_element"]
    asset_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    mesh: StructuralMeshReceipt
    load_case_ids: tuple[str, ...] = Field(min_length=1)
    load_case_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_fields: tuple[StructuralResultFieldReceipt, ...] = Field(min_length=1)
    diagnostics: tuple[StructuralDiagnosticEvidence, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def links_and_digest(self, info: ValidationInfo):
        if len(set(self.load_case_ids)) != len(self.load_case_ids):
            raise ValueError("structural receipt load-case identifiers must be unique")
        field_ids = [row.field_id for row in self.result_fields]
        diagnostic_ids = [row.diagnostic_id for row in self.diagnostics]
        if len(set(field_ids)) != len(field_ids) or len(set(diagnostic_ids)) != len(diagnostic_ids):
            raise ValueError("structural receipt field and diagnostic identifiers must be unique")
        if {row.load_case_id for row in self.result_fields} - set(self.load_case_ids):
            raise ValueError("structural result fields must reference declared load cases")
        if any(row.coordinate_frame_id != self.mesh.coordinate_frame_id for row in self.result_fields):
            raise ValueError("structural result fields must use the declared mesh coordinate frame")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("structural provider receipt payload digest mismatch")
        return self


def structural_provider_result_receipt(**payload) -> StructuralProviderResultReceipt:
    unsigned = StructuralProviderResultReceipt.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return StructuralProviderResultReceipt.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )


class RequiredStructuralField(Contract):
    requirement_id: str = Field(min_length=1)
    field_id: str = Field(min_length=1)
    quantity_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    result_location: Literal["node", "element", "integration_point", "face", "edge", "global"]
    coordinate_frame_id: str = Field(min_length=1)


class StructuralDiagnosticCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    category: Literal["equilibrium", "convergence", "uncertainty", "verification"]
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_acceptable: float | None = None
    maximum_acceptable: float | None = None
    comparison: Literal["uncertainty_interval_against_bounds"] = "uncertainty_interval_against_bounds"
    basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_acceptable is None and self.maximum_acceptable is None:
            raise ValueError("diagnostic criterion requires at least one caller bound")
        if (
            self.minimum_acceptable is not None
            and self.maximum_acceptable is not None
            and self.minimum_acceptable > self.maximum_acceptable
        ):
            raise ValueError("diagnostic criterion bounds must be ordered")
        return self


class StructuralAcceptanceProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    supported_analysis_kinds: tuple[
        Literal["external_pressure", "nozzle_local_stress", "finite_element"], ...
    ] = Field(min_length=1)
    supported_model_ids: tuple[str, ...] = Field(min_length=1)
    supported_element_family_ids: tuple[str, ...] = Field(min_length=1)
    maximum_node_count: int = Field(ge=1)
    maximum_element_count: int = Field(ge=1)
    required_fields: tuple[RequiredStructuralField, ...] = Field(min_length=1)
    diagnostic_criteria: tuple[StructuralDiagnosticCriterion, ...] = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_requirements(self):
        for values, label in (
            ([row.requirement_id for row in self.required_fields], "field requirement"),
            ([row.criterion_id for row in self.diagnostic_criteria], "diagnostic criterion"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"structural acceptance {label} identifiers must be unique")
        return self

    @property
    def deterministic_digest(self):
        return canonical_digest(self.model_dump(mode="json"))


class StructuralAcceptanceFinding(Contract):
    finding_id: str
    state: Literal["within", "outside", "boundary_overlap", "missing", "invalid", "mismatch"]
    basis: str


class StructuralAcceptanceReport(Contract):
    receipt_id: str
    profile_id: str
    decision: Literal["accept", "reject", "review", "insufficient_evidence"]
    findings: tuple[StructuralAcceptanceFinding, ...]
    receipt_digest: str
    profile_digest: str
    report_digest: str
    qualification_claim: Literal[False] = False
    physical_validation_claim: Literal[False] = False

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def bound_digest(self):
        if canonical_digest(self.digest_payload()) != self.report_digest:
            raise ValueError("structural acceptance report digest mismatch")
        return self


def evaluate_structural_provider_receipt(
    receipt: StructuralProviderResultReceipt,
    profile: StructuralAcceptanceProfile,
) -> StructuralAcceptanceReport:
    findings: list[StructuralAcceptanceFinding] = []
    if receipt.analysis_kind not in profile.supported_analysis_kinds:
        findings.append(
            StructuralAcceptanceFinding(
                finding_id="analysis_kind",
                state="mismatch",
                basis="Analysis kind is outside the caller profile.",
            )
        )
    if receipt.model_id not in profile.supported_model_ids:
        findings.append(
            StructuralAcceptanceFinding(
                finding_id="model_id", state="mismatch", basis="Model identity is outside the caller profile."
            )
        )
    if set(receipt.mesh.element_family_ids) - set(profile.supported_element_family_ids):
        findings.append(
            StructuralAcceptanceFinding(
                finding_id="element_family_ids",
                state="mismatch",
                basis="Mesh element family is outside the caller profile.",
            )
        )
    if (
        receipt.mesh.node_count > profile.maximum_node_count
        or receipt.mesh.element_count > profile.maximum_element_count
    ):
        findings.append(
            StructuralAcceptanceFinding(
                finding_id="mesh_size", state="mismatch", basis="Mesh size is outside the caller profile."
            )
        )

    by_field = {row.field_id: row for row in receipt.result_fields}
    for requirement in profile.required_fields:
        field = by_field.get(requirement.field_id)
        if field is None:
            state, basis = "missing", "Required result field was not supplied."
        elif (
            field.quantity_id,
            field.unit_token,
            field.result_location,
            field.coordinate_frame_id,
        ) != (
            requirement.quantity_id,
            requirement.unit_token,
            requirement.result_location,
            requirement.coordinate_frame_id,
        ):
            state, basis = "mismatch", "Result field quantity, unit, location, or coordinate frame differs."
        else:
            state, basis = "within", "Required field metadata matches the caller profile."
        findings.append(
            StructuralAcceptanceFinding(finding_id=requirement.requirement_id, state=state, basis=basis)
        )

    diagnostics = {(row.category, row.metric_id): row for row in receipt.diagnostics}
    for criterion in profile.diagnostic_criteria:
        diagnostic = diagnostics.get((criterion.category, criterion.metric_id))
        if diagnostic is None or diagnostic.status == "missing":
            state, basis = "missing", "Required diagnostic evidence was not supplied."
        elif diagnostic.status == "invalid":
            state, basis = "invalid", "Provider marked the required diagnostic evidence invalid."
        elif diagnostic.unit_token != criterion.unit_token:
            state, basis = "mismatch", "Diagnostic unit differs from the caller criterion."
        else:
            lower = diagnostic.value - diagnostic.expanded_uncertainty
            upper = diagnostic.value + diagnostic.expanded_uncertainty
            inside = (criterion.minimum_acceptable is None or lower >= criterion.minimum_acceptable) and (
                criterion.maximum_acceptable is None or upper <= criterion.maximum_acceptable
            )
            outside = (criterion.minimum_acceptable is not None and upper < criterion.minimum_acceptable) or (
                criterion.maximum_acceptable is not None and lower > criterion.maximum_acceptable
            )
            state = "within" if inside else "outside" if outside else "boundary_overlap"
            basis = "Provider uncertainty interval compared with caller-owned diagnostic bounds."
        findings.append(
            StructuralAcceptanceFinding(finding_id=criterion.criterion_id, state=state, basis=basis)
        )

    states = {row.state for row in findings}
    if states & {"missing", "invalid", "mismatch"}:
        decision = "insufficient_evidence"
    elif "outside" in states:
        decision = "reject"
    elif "boundary_overlap" in states:
        decision = "review"
    else:
        decision = "accept"
    payload = {
        "receipt_id": receipt.receipt_id,
        "profile_id": profile.profile_id,
        "decision": decision,
        "findings": [row.model_dump(mode="json") for row in findings],
        "receipt_digest": receipt.payload_digest,
        "profile_digest": profile.deterministic_digest,
        "qualification_claim": False,
        "physical_validation_claim": False,
    }
    return StructuralAcceptanceReport.model_validate(
        {**payload, "findings": tuple(findings), "report_digest": canonical_digest(payload)}
    )
