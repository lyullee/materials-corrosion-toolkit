"""Caller-criterion screen for FE solver diagnostics attached to flange receipts."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..structural_provider_acceptance import StructuralProviderResultReceipt
from ..registry import ModelSpec


class FlangeDiagnosticCriterion(Contract):
    """A caller-owned upper bound for one reported solver diagnostic."""

    criterion_id: str = Field(min_length=1)
    diagnostic_id: str = Field(min_length=1)
    category: Literal["equilibrium", "convergence", "uncertainty", "verification"]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    maximum_absolute_value_plus_uncertainty: float = Field(ge=0, allow_inf_nan=False)
    compatible_uncertainty_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ExternalFlangeDiagnosticScreenRequest(Contract):
    """Screen selected diagnostics on a digest-verified external FE receipt."""

    receipt: StructuralProviderResultReceipt
    criteria: tuple[FlangeDiagnosticCriterion, ...] = Field(min_length=1, max_length=100)
    receipt_diagnostics_applicability_reviewed: bool
    computational_use_authorized: bool


def screen_external_flange_diagnostics(request: ExternalFlangeDiagnosticScreenRequest) -> Calculation:
    """Compare provider-reported diagnostics to explicit caller limits.

    A diagnostic passes only when ``abs(value) + expanded_uncertainty`` is no
    greater than its caller threshold. The metric's physical meaning and the
    uncertainty's comparability are explicitly caller-reviewed. No threshold
    is supplied by this package.
    """
    receipt = request.receipt
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "model_id": "integration.external_flange_diagnostic_screen",
        "receipt_id": receipt.receipt_id,
        "receipt_sha256": receipt.payload_digest,
        "request_sha256": digest,
        "criterion_count": len(request.criteria),
        "physical_acceptance": False,
    }
    if not request.receipt_diagnostics_applicability_reviewed or not request.computational_use_authorized:
        missing = []
        if not request.receipt_diagnostics_applicability_reviewed:
            missing.append("receipt_diagnostics_applicability_reviewed")
        if not request.computational_use_authorized:
            missing.append("computational_use_authorized")
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "findings": []})
    if len({criterion.criterion_id for criterion in request.criteria}) != len(request.criteria):
        return Calculation(status="out_of_scope", values=base | {"reason": "criterion IDs must be unique", "findings": []})
    findings: list[dict[str, object]] = []
    unresolved: list[str] = []
    unsupported: list[str] = []
    failed: list[str] = []
    for criterion in request.criteria:
        if not criterion.compatible_uncertainty_reviewed:
            unresolved.append(criterion.criterion_id)
            findings.append({"criterion_id": criterion.criterion_id, "status": "needs_data",
                             "reason": "uncertainty-to-limit comparison was not reviewed"})
            continue
        matches = [row for row in receipt.diagnostics if row.diagnostic_id == criterion.diagnostic_id]
        if len(matches) != 1:
            unresolved.append(criterion.criterion_id)
            findings.append({"criterion_id": criterion.criterion_id, "status": "needs_data",
                             "reason": "diagnostic ID is absent or ambiguous"})
            continue
        diagnostic = matches[0]
        if (diagnostic.category != criterion.category or diagnostic.metric_id != criterion.metric_id
                or diagnostic.metric_definition != criterion.metric_definition
                or diagnostic.unit_token != criterion.unit_token):
            unsupported.append(criterion.criterion_id)
            findings.append({"criterion_id": criterion.criterion_id, "status": "out_of_scope",
                             "reason": "provider diagnostic meaning or unit differs from caller criterion"})
            continue
        if diagnostic.status != "reported" or diagnostic.value is None or diagnostic.expanded_uncertainty is None:
            unresolved.append(criterion.criterion_id)
            findings.append({"criterion_id": criterion.criterion_id, "status": "needs_data",
                             "provider_status": diagnostic.status})
            continue
        bounded = abs(diagnostic.value) + diagnostic.expanded_uncertainty
        status = "computed" if bounded <= criterion.maximum_absolute_value_plus_uncertainty else "out_of_scope"
        if status != "computed":
            failed.append(criterion.criterion_id)
        findings.append({"criterion_id": criterion.criterion_id, "diagnostic_id": diagnostic.diagnostic_id,
                         "provider_record_digest": diagnostic.provider_record_digest, "unit_token": diagnostic.unit_token,
                         "absolute_value_plus_expanded_uncertainty": bounded,
                         "caller_limit": criterion.maximum_absolute_value_plus_uncertainty,
                         "status": status})
    status = "out_of_scope" if unsupported or failed else "needs_data" if unresolved else "computed"
    return Calculation(status=status, values=base | {
        "findings": findings,
        "unresolved_criterion_ids": unresolved,
        "unsupported_criterion_ids": unsupported,
        "exceeding_criterion_ids": failed,
        "criterion_semantics": "caller-defined diagnostic screen; not solver qualification or physical acceptance",
    }, notes=("Only digest-bound diagnostics and caller-authored limits are compared; this screen does not validate the FE solution or certify a flange/gasket.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.external_flange_diagnostic_screen",
        input_type=ExternalFlangeDiagnosticScreenRequest,
        evaluator=screen_external_flange_diagnostics,
        units={"criteria[].maximum_absolute_value_plus_uncertainty": "caller-defined metric unit"},
        assumptions=("Criteria and uncertainty comparisons are caller-owned and evidence-backed.", "A passing diagnostic screen is not FE solver qualification, physical acceptance or seal qualification."),
        source_ids=("caller_external_flange_diagnostic_screen",),
        qualification="engineering_screening",
    )]
