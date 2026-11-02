"""Caller-criteria evidence assessment for overlay and cladding campaigns."""

from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "welding.overlay_cladding_evidence_campaign"


class OverlayDepositionPass(Contract):
    pass_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    layer_id: str = Field(min_length=1)
    layer_sequence_position: int = Field(ge=1)
    substrate_or_parent_id: str = Field(min_length=1)
    filler_lot_id: str = Field(min_length=1)
    process_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    heat_input_j_m: Nonnegative | None = None
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class OverlayMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    layer_id: str = Field(min_length=1)
    pass_id: str | None = None
    replicate_group_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    metric_kind: Literal[
        "dilution",
        "composition",
        "layer_thickness",
        "ferrite",
        "bond",
        "continuity",
        "nde",
        "user_defined",
    ]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    status: Literal["available", "missing", "invalid"]
    value: float | None = None
    standard_uncertainty: Nonnegative | None = None
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_status(self):
        if self.status == "available":
            if self.value is None or self.standard_uncertainty is None or self.result_digest is None:
                raise ValueError("available overlay measurements require value, uncertainty and digest")
        elif (
            self.value is not None
            or self.standard_uncertainty is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid overlay measurements require a basis and no value")
        return self


class OverlayHeatInterval(Contract):
    interval_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    interval_kind: Literal["deposition", "interpass", "post_weld_heat_treatment", "service_exposure"]
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_time_s <= self.start_time_s or self.maximum_temperature_k < self.minimum_temperature_k:
            raise ValueError("overlay heat intervals require ordered time and temperature")
        return self


class CallerOverlayCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    metric_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    aggregation: Literal["individual", "replicate_mean", "replicate_minimum", "replicate_maximum"]
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    minimum_replicates: int = Field(ge=1)
    missing_disposition: Literal["review", "insufficient_evidence"]
    description: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("overlay criteria require at least one caller bound")
        if (
            self.minimum_inclusive is not None
            and self.maximum_inclusive is not None
            and self.maximum_inclusive < self.minimum_inclusive
        ):
            raise ValueError("overlay criterion bounds must be ordered")
        return self


class CallerOverlayProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_substrate_ids: tuple[str, ...] = Field(min_length=1)
    permitted_filler_lot_ids: tuple[str, ...] = Field(min_length=1)
    permitted_process_ids: tuple[str, ...] = Field(min_length=1)
    criteria: tuple[CallerOverlayCriterion, ...] = Field(min_length=1)
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_criteria(self):
        ids = [row.criterion_id for row in self.criteria]
        if len(ids) != len(set(ids)):
            raise ValueError("overlay criterion IDs must be unique")
        return self


class OverlayCladdingCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    substrate_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    passes: tuple[OverlayDepositionPass, ...] = Field(min_length=1)
    measurements: tuple[OverlayMeasurement, ...] = Field(min_length=1)
    heat_history: tuple[OverlayHeatInterval, ...] = Field(min_length=1)
    profile: CallerOverlayProfile
    substrate_filler_process_layer_and_pass_identity_reviewed: bool
    dilution_composition_thickness_ferrite_bond_continuity_and_nde_reviewed: bool
    measurement_units_uncertainty_methods_and_provenance_reviewed: bool
    heat_history_time_temperature_and_sequence_reviewed: bool
    caller_profile_authority_and_criteria_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_sequences(self):
        pass_ids = [row.pass_id for row in self.passes]
        if len(pass_ids) != len(set(pass_ids)) or [row.sequence_position for row in self.passes] != list(
            range(1, len(self.passes) + 1)
        ):
            raise ValueError("overlay passes require unique IDs and consecutive sequence")
        layer_positions: dict[str, int] = {}
        for row in self.passes:
            if (
                row.layer_id in layer_positions
                and layer_positions[row.layer_id] != row.layer_sequence_position
            ):
                raise ValueError("one overlay layer must retain one sequence position")
            layer_positions[row.layer_id] = row.layer_sequence_position
        if sorted(set(layer_positions.values())) != list(range(1, len(set(layer_positions.values())) + 1)):
            raise ValueError("overlay layers require consecutive sequence positions")
        measurement_ids = [row.measurement_id for row in self.measurements]
        if len(measurement_ids) != len(set(measurement_ids)):
            raise ValueError("overlay measurement IDs must be unique")
        if any(
            row.layer_id not in layer_positions or (row.pass_id is not None and row.pass_id not in pass_ids)
            for row in self.measurements
        ):
            raise ValueError("overlay measurements must reference declared layers and passes")
        if [row.sequence_position for row in self.heat_history] != list(range(1, len(self.heat_history) + 1)):
            raise ValueError("overlay heat history requires consecutive sequence")
        for first, second in zip(self.heat_history, self.heat_history[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("overlay heat intervals cannot overlap")
        return self


class OverlayFinding(Contract):
    criterion_id: str
    target_id: str
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str


class OverlayCladdingCampaignResult(Contract):
    schema_version: Literal["matintegrity.overlay_cladding_campaign.v1"] = (
        "matintegrity.overlay_cladding_campaign.v1"
    )
    model_id: Literal["welding.overlay_cladding_evidence_campaign"] = MODEL_ID
    assessment_id: str
    campaign_id: str
    profile_id: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[OverlayFinding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    automatic_material_compatibility_or_qualification_claim: Literal[False] = False
    corrosion_life_or_standard_acceptance_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("overlay campaign result digest does not match its content")
        return self


def assess_overlay_cladding(x: OverlayCladdingCampaign) -> OverlayCladdingCampaignResult:
    p = x.profile
    reviews, insufficient, findings = [], [], []
    for reviewed, reason in (
        (p.profile_reviewed, "caller profile was not reviewed"),
        (
            x.substrate_filler_process_layer_and_pass_identity_reviewed,
            "substrate, filler, process, layer or pass identity was not reviewed",
        ),
        (
            x.dilution_composition_thickness_ferrite_bond_continuity_and_nde_reviewed,
            "overlay measurement scope was not reviewed",
        ),
        (
            x.measurement_units_uncertainty_methods_and_provenance_reviewed,
            "measurement units, uncertainty, methods or provenance were not reviewed",
        ),
        (x.heat_history_time_temperature_and_sequence_reviewed, "heat history was not reviewed"),
        (x.caller_profile_authority_and_criteria_reviewed, "caller criteria authority was not reviewed"),
    ):
        if not reviewed:
            insufficient.append(reason)
    if x.substrate_id not in p.permitted_substrate_ids:
        reviews.append("substrate identity is outside caller profile")
    if any(
        row.filler_lot_id not in p.permitted_filler_lot_ids or row.process_id not in p.permitted_process_ids
        for row in x.passes
    ):
        reviews.append("one or more filler/process identities are outside caller profile")
    for criterion in p.criteria:
        rows = [
            row
            for row in x.measurements
            if row.metric_kind == criterion.metric_kind
            and row.metric_id == criterion.metric_id
            and row.unit_token == criterion.unit_token
        ]
        groups: dict[str, list[OverlayMeasurement]] = {}
        for row in rows:
            groups.setdefault(row.replicate_group_id, []).append(row)
        if not groups:
            outcome = criterion.missing_disposition
            (reviews if outcome == "review" else insufficient).append(
                f"{criterion.criterion_id} lacks exact metric/unit evidence"
            )
            continue
        for group_id, group in sorted(groups.items()):
            available = [row for row in group if row.status == "available"]
            if len(available) < criterion.minimum_replicates:
                outcome = criterion.missing_disposition
                (reviews if outcome == "review" else insufficient).append(
                    f"{criterion.criterion_id}:{group_id} lacks valid replicates"
                )
                findings.append(
                    OverlayFinding(
                        criterion_id=criterion.criterion_id,
                        target_id=group_id,
                        outcome=outcome,
                        observed_value=None,
                        unit_token=criterion.unit_token,
                        basis="caller minimum replicate count not met",
                    )
                )
                continue
            values = [row.value for row in available]
            if criterion.aggregation == "individual":
                selected = [(row.measurement_id, row.value, row.standard_uncertainty) for row in available]
            else:
                value = {
                    "replicate_mean": fmean(values),
                    "replicate_minimum": min(values),
                    "replicate_maximum": max(values),
                }[criterion.aggregation]
                repeatability = pstdev(values) / math.sqrt(len(values)) if len(values) > 1 else 0.0
                measurement_u = math.sqrt(sum(row.standard_uncertainty**2 for row in available)) / len(
                    available
                )
                selected = [(group_id, value, math.sqrt(repeatability**2 + measurement_u**2))]
            for target, value, uncertainty in selected:
                span = (
                    criterion.uncertainty_coverage_factor * uncertainty
                    if criterion.uncertainty_policy == "interval_must_fit"
                    else 0.0
                )
                low, high = value - span, value + span
                within = (criterion.minimum_inclusive is None or low >= criterion.minimum_inclusive) and (
                    criterion.maximum_inclusive is None or high <= criterion.maximum_inclusive
                )
                findings.append(
                    OverlayFinding(
                        criterion_id=criterion.criterion_id,
                        target_id=target,
                        outcome="pass" if within else "fail",
                        observed_value=value,
                        unit_token=criterion.unit_token,
                        evaluated_lower=low,
                        evaluated_upper=high,
                        basis=f"caller {criterion.aggregation} criterion with {criterion.uncertainty_policy}",
                    )
                )
    if insufficient:
        disposition: Disposition = "insufficient_evidence"
    elif any(row.outcome == "fail" for row in findings):
        disposition = "reject"
    elif reviews or any(row.outcome == "review" for row in findings):
        disposition = "review"
    else:
        disposition = "accept"
    values = dict(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        profile_id=p.profile_id,
        disposition=disposition,
        input_digest=canonical_digest(x.model_dump(mode="json")),
        findings=tuple(findings),
        review_reasons=tuple(dict.fromkeys(reviews)),
        insufficient_evidence_reasons=tuple(dict.fromkeys(insufficient)),
        notes=(
            "Only caller criteria are applied to traceable overlay evidence; no material compatibility or standard allowable is inferred.",
            "Pass/layer sequence, dilution, composition, thickness, ferrite, bond, continuity, NDE and heat-history records remain caller/provider evidence.",
            "No qualification, corrosion life or failure probability is claimed.",
        ),
    )
    unsigned = OverlayCladdingCampaignResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return OverlayCladdingCampaignResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )
