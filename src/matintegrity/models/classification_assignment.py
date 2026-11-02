"""Exact caller classification records, distinct from material equivalence."""

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec
from ..specification_aliases import SpecificationDesignation
from .engineering_correlations import SOURCE_ID, CorrelationRequest
from .wps_qualification import ProductionEssentialVariableRecord


class ClassificationContext(Contract):
    code_namespace: str = Field(min_length=1)
    code_edition: str = Field(min_length=1)
    classification_scheme_id: str = Field(min_length=1)
    process_id: str = Field(min_length=1)
    subject_kind: Literal["base_material", "filler_material", "consumable", "weld_deposit"]
    qualification_purpose_id: str = Field(min_length=1)


class ClassificationQuery(Contract):
    query_id: str = Field(min_length=1)
    physical_item_id: str = Field(min_length=1)
    designation: SpecificationDesignation
    context: ClassificationContext


class DeclaredClassificationRecord(Contract):
    record_id: str = Field(min_length=1)
    designation: SpecificationDesignation
    context: ClassificationContext
    assignment_status: Literal["assigned", "unassigned", "unknown"]
    assignment_token: str | None = None
    unknown_basis: str | None = None
    assignment_basis: str = Field(min_length=1)
    authority_id: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    source_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    authority_and_assignment_reviewed: bool
    assignment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def state_and_digest(self):
        if self.assignment_status == "assigned":
            if (
                self.assignment_token is None
                or not self.assignment_token.strip()
                or self.unknown_basis is not None
            ):
                raise ValueError("assigned classifications need an exact nonblank token and no unknown basis")
        elif self.assignment_token is not None:
            raise ValueError("unassigned or unknown classifications cannot carry a token")
        if self.assignment_status == "unknown":
            if not self.unknown_basis or not self.unknown_basis.strip():
                raise ValueError("unknown assignment records require an explicit basis")
        elif self.unknown_basis is not None:
            raise ValueError("only unknown assignment records can carry an unknown basis")
        digest = canonical_digest(self.model_dump(mode="json", exclude={"assignment_sha256", "evidence"}))
        if digest != self.assignment_sha256 or not any(
            e.sha256 == digest and e.license_id for e in self.evidence
        ):
            raise ValueError("licensed assignment evidence must pin the exact identity, scope and state")
        return self


class DeclaredClassificationAssignment(CorrelationRequest):
    lookup_id: str = Field(min_length=1)
    queries: tuple[ClassificationQuery, ...] = Field(min_length=1, max_length=10000)
    records: tuple[DeclaredClassificationRecord, ...] = Field(max_length=20000)
    item_designations_and_conditions_reviewed: bool
    classification_authority_and_scope_reviewed: bool

    @model_validator(mode="after")
    def unique_requests_and_records(self):
        for ids in (tuple(q.query_id for q in self.queries), tuple(r.record_id for r in self.records)):
            if len(set(ids)) != len(ids) or any(not key.strip() for key in ids):
                raise ValueError("classification query and record identities must be unique and nonblank")
        identities = {}
        for query in self.queries:
            key = (query.physical_item_id, canonical_digest(query.context.model_dump(mode="json")))
            designation = canonical_digest(query.designation.model_dump(mode="json"))
            if key in identities and identities[key] != designation:
                raise ValueError(
                    "one physical item cannot have conflicting designations in the same classification context"
                )
            identities[key] = designation
        return self


def _assignment_key(item):
    return canonical_digest(
        dict(
            designation=item.designation.model_dump(mode="json"), context=item.context.model_dump(mode="json")
        )
    )


def declared_classification_assignment(x: DeclaredClassificationAssignment) -> Calculation:
    index = {}
    for record in x.records:
        index.setdefault(_assignment_key(record), []).append(record)
    reviewed = x.item_designations_and_conditions_reviewed and x.classification_authority_and_scope_reviewed
    findings = []
    for query in x.queries:
        matches = index.get(_assignment_key(query), [])
        state, token, selected = "unknown", None, None
        basis = "No exact designation and classification context matched."
        if not reviewed:
            basis = "Item identity and classification authority/scope reviews are incomplete."
        elif len(matches) > 1:
            state, basis = (
                "ambiguous",
                "Multiple exact records matched; no authority or revision priority was inferred.",
            )
        elif matches:
            record = matches[0]
            if not record.authority_and_assignment_reviewed:
                basis = "The matching assignment authority and state are unreviewed."
            else:
                state, token, selected = record.assignment_status, record.assignment_token, record.record_id
                basis = record.unknown_basis if state == "unknown" else record.assignment_basis
        findings.append(
            dict(
                query_id=query.query_id,
                physical_item_id=query.physical_item_id,
                designation=query.designation.model_dump(mode="json"),
                context=query.context.model_dump(mode="json"),
                assignment_status=state,
                assignment_token=token,
                selected_record_id=selected,
                candidate_record_ids=sorted(record.record_id for record in matches),
                basis=basis,
                candidate_assignment_sha256={
                    record.record_id: record.assignment_sha256 for record in matches
                },
                selected_evidence=None
                if selected is None
                else dict(
                    authority_id=matches[0].authority_id,
                    revision=matches[0].revision,
                    assignment_sha256=matches[0].assignment_sha256,
                    source_record_sha256=matches[0].source_record_sha256,
                ),
                status="computed" if state in {"assigned", "unassigned"} else "needs_data",
            )
        )
    return Calculation(
        status="needs_data" if any(row["status"] == "needs_data" for row in findings) else "computed",
        values=dict(
            lookup_id=x.lookup_id,
            assignment_findings=findings,
            qualification_decision="not_evaluated",
            material_equivalence_established=False,
            record_sha256=x.basis.record_sha256,
        ),
        notes=(
            "Exact caller records only. Tokens are identifiers, never ordered numbers or material property values.",
            "Explicitly unassigned differs from unknown. No cross-edition, process, purpose, product-form or condition mapping, material substitution or qualification coverage is inferred.",
        ),
    )


class ClassificationWPSBinding(Contract):
    query_id: str = Field(min_length=1)
    physical_item_id: str = Field(min_length=1)
    designation: SpecificationDesignation
    context: ClassificationContext
    selected_record_id: str = Field(min_length=1)
    assignment_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    lookup_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    production_variable: ProductionEssentialVariableRecord
    binding_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def pinned_binding(self):
        if (
            self.production_variable.variable_kind != "categorical"
            or not self.production_variable.record_valid
            or self.production_variable.unit_token != "1"
        ):
            raise ValueError("classification bindings require a valid dimensionless categorical variable")
        if self.binding_sha256 != canonical_digest(self.model_dump(mode="json", exclude={"binding_sha256"})):
            raise ValueError(
                "classification-to-WPS binding digest does not match its physical item and variable"
            )
        return self


def classification_to_wps_variable(
    x: DeclaredClassificationAssignment, query_id: str, *, variable_id: str, production_record_id: str
) -> ClassificationWPSBinding:
    """Bind one resolved token to an existing categorical WPS variable contract."""
    result = declared_classification_assignment(x)
    finding = next((row for row in result.values["assignment_findings"] if row["query_id"] == query_id), None)
    if finding is None or finding["assignment_status"] != "assigned":
        raise ValueError("WPS binding requires one reviewed, unambiguous assigned classification query")
    selected = next(record for record in x.records if record.record_id == finding["selected_record_id"])
    variable = ProductionEssentialVariableRecord(
        record_id=production_record_id,
        variable_id=variable_id,
        variable_kind="categorical",
        unit_token="1",
        categorical_value_token=finding["assignment_token"],
        record_valid=True,
        evidence=(*selected.evidence, *x.basis.evidence),
    )
    query = next(query for query in x.queries if query.query_id == query_id)
    payload = dict(
        query_id=query_id,
        physical_item_id=query.physical_item_id,
        designation=query.designation,
        context=query.context,
        selected_record_id=selected.record_id,
        assignment_sha256=selected.assignment_sha256,
        lookup_input_sha256=x.basis.record_sha256,
        production_variable=variable,
    )
    digest = canonical_digest(
        ClassificationWPSBinding.model_construct(**payload).model_dump(
            mode="json", exclude={"binding_sha256"}
        )
    )
    return ClassificationWPSBinding(**payload, binding_sha256=digest)


def specifications():
    return [
        ModelSpec(
            "materials.declared_classification_assignment",
            DeclaredClassificationAssignment,
            declared_classification_assignment,
            {"assignment_findings": "structured_record"},
            (
                "Caller classification records bind material designation, edition, product, condition, process, subject and qualification purpose.",
            ),
            (SOURCE_ID,),
            qualification="user_model",
        )
    ]
