"""Top-level caller criteria for certificate document coverage."""

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence
from ..registry import ModelSpec
from .certificate_reconciliation import MaterialCertificateReconciliation, certificate_reconciliation


class CertificateCoverageRecord(Contract):
    record_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    traceability_id: str = Field(min_length=1)
    category: Literal["chemistry", "mechanical", "heat_treatment", "nde", "traceability"]
    status: Literal["pass", "fail", "review", "missing"]
    caller_criterion_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CertificateCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    purchase_requirement_set_id: str = Field(min_length=1)
    expected_product_id: str | None = Field(default=None, min_length=1)
    expected_traceability_id: str | None = Field(default=None, min_length=1)
    product_and_traceability_binding_reviewed: bool = False
    lower_level: MaterialCertificateReconciliation
    coverage: tuple[CertificateCoverageRecord, ...] = Field(min_length=1)
    required_categories: tuple[
        Literal["chemistry", "mechanical", "heat_treatment", "nde", "traceability"], ...
    ] = Field(min_length=1)
    caller_criteria_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked(self):
        record_ids = [row.record_id for row in self.coverage]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("certificate coverage record IDs must be unique")
        if len(self.required_categories) != len(set(self.required_categories)):
            raise ValueError("required certificate coverage categories must be unique")
        if (self.asset_id, self.location_id) != (self.lower_level.asset_id, self.lower_level.location_id):
            raise ValueError("certificate campaign and lower-level identity must match")
        if any(r.heat_id != self.lower_level.heat_id for r in self.coverage):
            raise ValueError("coverage heat identity must match")
        if (self.expected_product_id is None) != (self.expected_traceability_id is None):
            raise ValueError("expected product and traceability identifiers must be supplied together")
        if self.expected_product_id is not None and any(
            (row.product_id, row.traceability_id) != (self.expected_product_id, self.expected_traceability_id)
            for row in self.coverage
        ):
            raise ValueError("coverage product and traceability identifiers must match the declared target")
        return self


def certificate_campaign(x: CertificateCampaign) -> Calculation:
    lower = certificate_reconciliation(x.lower_level)
    identity_bound = (
        x.expected_product_id is not None
        and x.expected_traceability_id is not None
        and x.product_and_traceability_binding_reviewed
    )
    states = {c: [] for c in x.required_categories}
    for r in x.coverage:
        if r.category in states:
            states[r.category].append(r.status)
    findings = {
        c: (
            "missing"
            if not v or "missing" in v
            else "fail"
            if "fail" in v
            else "review"
            if "review" in v
            else "pass"
        )
        for c, v in states.items()
    }
    disposition = (
        "insufficient_evidence"
        if not identity_bound
        or not x.caller_criteria_reviewed
        or lower.status == "needs_data"
        or "missing" in findings.values()
        else "reject"
        if "fail" in findings.values() or lower.values.get("declared_requirement_outcome") == "not_satisfied"
        else "review"
        if "review" in findings.values() or lower.values.get("declared_requirement_outcome") == "unknown"
        else "pass"
    )
    return Calculation(
        status="needs_data" if not identity_bound else "computed",
        values={
            "assessment_id": x.assessment_id,
            "expected_product_id": x.expected_product_id,
            "expected_traceability_id": x.expected_traceability_id,
            "product_and_traceability_identity_bound": identity_bound,
            "disposition": disposition,
            "category_findings": findings,
            "lower_level": lower.model_dump(mode="json"),
        },
        notes=(
            "Caller criteria only; no built-in specification, alias equivalence, material approval or statistical inference.",
        ),
    )


def specifications() -> list[ModelSpec]:
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("certificate campaign asset and location must match run context")

    return [
        ModelSpec(
            "materials.certificate_reconciliation",
            CertificateCampaign,
            certificate_campaign,
            {
                "disposition": "1",
                "category_findings": "1",
                "lower_level": "mixed",
                "expected_product_id": "1",
                "expected_traceability_id": "1",
                "product_and_traceability_identity_bound": "1",
            },
            (
                "Certificate campaign coverage composed over lower-level reconciliation with exact reviewed target product and traceability binding.",
            ),
            ("authored_certificate_campaign_coverage_reconciliation",),
            version="1.1.0",
            context_validator=same_identity,
        )
    ]
