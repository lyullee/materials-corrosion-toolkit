"""Caller-profile campaign audit for test-water quality evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

HistoryKind = Literal["fill", "hold", "drain", "dry", "other"]
Analyte = Literal[
    "ph",
    "conductivity",
    "chloride",
    "halide",
    "oxygen",
    "solids",
    "microbiology",
    "inhibitor",
    "temperature",
]


class TestWaterCircuitIdentity(Contract):
    source_id: str = Field(min_length=1)
    water_batch_id: str = Field(min_length=1)
    source_type_descriptor: str = Field(min_length=1)
    tank_id: str = Field(min_length=1)
    circuit_id: str = Field(min_length=1)
    circuit_scope_definition: str = Field(min_length=1)
    contacted_material_ids: tuple[str, ...] = Field(min_length=1)
    contact_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_batch_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_materials(self):
        if len(set(self.contacted_material_ids)) != len(self.contacted_material_ids):
            raise ValueError("contacted material identities must be unique")
        return self


class TestWaterHistoryEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    event_kind: HistoryKind
    state_definition: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    water_batch_id: str | None = Field(default=None, min_length=1)
    event_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    event_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_event(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("test-water history events require positive duration")
        if self.event_kind in ("fill", "hold", "drain") and self.water_batch_id is None:
            raise ValueError("wet test-water history events require water batch identity")
        if self.event_kind == "dry" and self.water_batch_id is not None:
            raise ValueError("dry history events cannot claim a water batch")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid test-water history events require a basis")
        return self


class TestWaterAnalyticalResult(Contract):
    result_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    analyte: Analyte
    species_or_quantity_definition: str = Field(min_length=1)
    value: Nonnegative
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    uncertainty_basis: str = Field(min_length=1)
    analysis_method_id: str = Field(min_length=1)
    analysis_method_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid test-water analytical results require a basis")
        return self


class TestWaterSample(Contract):
    sample_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    sampling_time_s: Nonnegative
    sampling_location_id: str = Field(min_length=1)
    sampling_location_definition: str = Field(min_length=1)
    sampling_method_id: str = Field(min_length=1)
    laboratory_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    calibration_valid: bool
    invalid_calibration_basis: str | None = None
    calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    results: tuple[TestWaterAnalyticalResult, ...] = Field(min_length=1)
    sample_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_results_and_calibration(self):
        if not self.calibration_valid and not self.invalid_calibration_basis:
            raise ValueError("invalid sample calibration requires a basis")
        result_ids = [row.result_id for row in self.results]
        analytes = [row.analyte for row in self.results]
        if len(set(result_ids)) != len(result_ids) or len(set(analytes)) != len(analytes):
            raise ValueError("sample result identities and analytes must be unique")
        if any(row.sample_id != self.sample_id for row in self.results):
            raise ValueError("analytical results must reference their containing sample")
        return self


class TestWaterCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    analyte: Analyte
    species_or_quantity_definition: str = Field(min_length=1)
    aggregation: Literal["minimum", "maximum"]
    direction: Literal["minimum", "maximum"]
    accept_limit: Nonnegative
    reject_limit: Nonnegative
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_limits(self):
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum water-quality criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum water-quality criteria require accept <= reject")
        return self


class TestWaterCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    required_history_kinds: tuple[HistoryKind, ...] = Field(min_length=1)
    required_analytes: tuple[Analyte, ...] = Field(min_length=1)
    minimum_sample_count: int = Field(ge=1)
    minimum_independent_source_group_count: int = Field(ge=1)
    criteria: tuple[TestWaterCriterion, ...] = Field(min_length=1)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    chemical_species_conversion_used: Literal[False] = False
    corrosion_rate_inference_claimed: Literal[False] = False
    microbiological_risk_inference_claimed: Literal[False] = False
    built_in_code_or_standard_limits_used: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_profile(self):
        if len(set(self.required_history_kinds)) != len(self.required_history_kinds):
            raise ValueError("required test-water history kinds must be unique")
        if len(set(self.required_analytes)) != len(self.required_analytes):
            raise ValueError("required test-water analytes must be unique")
        ids = [row.criterion_id for row in self.criteria]
        analytes = [row.analyte for row in self.criteria]
        if len(set(ids)) != len(ids) or len(set(analytes)) != len(analytes):
            raise ValueError("test-water criteria must have unique identities and one row per analyte")
        if set(analytes) != set(self.required_analytes):
            raise ValueError("caller profile requires one criterion per required analyte")
        return self


class TestWaterQualityCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    circuit_identity: TestWaterCircuitIdentity
    history: tuple[TestWaterHistoryEvent, ...] = Field(min_length=1)
    samples: tuple[TestWaterSample, ...] = Field(min_length=1)
    caller_profile: TestWaterCallerProfile
    source_batch_tank_circuit_material_contact_identity_reviewed: bool
    ordered_fill_hold_drain_dry_history_reviewed: bool
    sampling_time_location_method_lab_and_calibration_reviewed: bool
    analyte_species_units_uncertainty_and_methods_reviewed: bool
    replicate_source_and_independence_claims_reviewed: bool
    provider_provenance_and_digests_reviewed: bool
    caller_profile_reviewed: bool
    invalid_and_missing_records_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        event_ids = [row.event_id for row in self.history]
        sequence = [row.sequence_index for row in self.history]
        sample_ids = [row.sample_id for row in self.samples]
        result_ids = [result.result_id for sample in self.samples for result in sample.results]
        raw_digests = [result.raw_data_digest for sample in self.samples for result in sample.results]
        result_digests = [result.result_record_digest for sample in self.samples for result in sample.results]
        for values, label in (
            (event_ids, "history event"),
            (sequence, "history sequence"),
            (sample_ids, "sample"),
            (result_ids, "analytical result"),
            (raw_digests, "raw-data digest"),
            (result_digests, "result-record digest"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"test-water campaign {label} identities must be unique")
        if tuple(sorted(self.history, key=lambda row: row.sequence_index)) != self.history:
            raise ValueError("test-water history must be supplied in sequence order")
        by_event = {row.event_id: row for row in self.history}
        for row in self.history:
            if row.water_batch_id is not None and row.water_batch_id != self.circuit_identity.water_batch_id:
                raise ValueError("wet history events must preserve campaign water batch identity")
        for sample in self.samples:
            event = by_event.get(sample.event_id)
            if event is None or not event.start_time_s <= sample.sampling_time_s <= event.end_time_s:
                raise ValueError("water samples must occur inside their declared history event")
            if event.event_kind == "dry":
                raise ValueError("water samples cannot be assigned to a dry event")
        return self


class TestWaterQualityCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.test_water_quality_campaign_report.v1"] = (
        "matintegrity.test_water_quality_campaign_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    campaign_outcome: Literal["accept", "review", "reject", "insufficient_evidence"]
    caller_profile_id: str = Field(min_length=1)
    analyte_metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_profile_only: Literal[True] = True
    chemical_species_converted: Literal[False] = False
    corrosion_rate_or_microbiological_risk_inferred: Literal[False] = False
    automatic_standard_acceptance: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("test-water campaign report digest does not match content")
        return self


def _bound_report(**payload: Any) -> TestWaterQualityCampaignReport:
    unsigned = TestWaterQualityCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return TestWaterQualityCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, row: TestWaterCriterion) -> str:
    if row.direction == "minimum":
        return "accept" if value >= row.accept_limit else "reject" if value <= row.reject_limit else "review"
    return "accept" if value <= row.accept_limit else "reject" if value >= row.reject_limit else "review"


def test_water_quality_campaign(x: TestWaterQualityCampaignAssessment) -> Calculation:
    review_fields = (
        "source_batch_tank_circuit_material_contact_identity_reviewed",
        "ordered_fill_hold_drain_dry_history_reviewed",
        "sampling_time_location_method_lab_and_calibration_reviewed",
        "analyte_species_units_uncertainty_and_methods_reviewed",
        "replicate_source_and_independence_claims_reviewed",
        "provider_provenance_and_digests_reviewed",
        "caller_profile_reviewed",
        "invalid_and_missing_records_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    results = [result for sample in x.samples for result in sample.results]
    invalid_events = [row.event_id for row in x.history if not row.record_valid]
    invalid_calibrations = [row.sample_id for row in x.samples if not row.calibration_valid]
    invalid_results = [row.result_id for row in results if not row.record_valid]
    profile = x.caller_profile
    missing_history = sorted(set(profile.required_history_kinds) - {row.event_kind for row in x.history})
    missing_analytes = sorted(set(profile.required_analytes) - {row.analyte for row in results})
    independent_groups = {(row.source_group_id, row.independence_group_id) for row in x.samples}
    count_gaps = {
        "sample_count": len(x.samples) < profile.minimum_sample_count,
        "independent_source_group_count": len(independent_groups)
        < profile.minimum_independent_source_group_count,
    }
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_history_event_ids": invalid_events,
        "invalid_sample_calibration_ids": invalid_calibrations,
        "invalid_result_ids": invalid_results,
        "missing_required_history_kinds": missing_history,
        "missing_required_analytes": missing_analytes,
        "campaign_count_gaps": count_gaps,
        "sample_ids": [row.sample_id for row in x.samples],
        "raw_data_digests": [row.raw_data_digest for row in results],
        "result_record_digests": [row.result_record_digest for row in results],
    }
    incomplete = (
        missing_reviews
        or invalid_events
        or invalid_calibrations
        or invalid_results
        or missing_history
        or missing_analytes
        or any(count_gaps.values())
    )
    if incomplete:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            analyte_metric_values={},
            criterion_findings=(),
            diagnostics=diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Complete reviewed history, samples, calibrations, and analytical results are required.",),
        )

    criteria = {row.analyte: row for row in profile.criteria}
    metric_values: dict[str, float] = {}
    identity_conflicts: list[str] = []
    for analyte, criterion in criteria.items():
        matching = [row for row in results if row.analyte == analyte]
        if {(row.species_or_quantity_definition, row.unit_token) for row in matching} != {
            (criterion.species_or_quantity_definition, criterion.unit_token)
        }:
            identity_conflicts.append(criterion.criterion_id)
            continue
        values = [row.value for row in matching]
        metric_values[analyte] = min(values) if criterion.aggregation == "minimum" else max(values)
    if identity_conflicts:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            analyte_metric_values=metric_values,
            criterion_findings=(),
            diagnostics={**diagnostics, "criterion_species_or_unit_conflict_ids": identity_conflicts},
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Caller criterion species definitions and units must match analytical results exactly.",),
        )

    findings = tuple(
        {
            "criterion_id": row.criterion_id,
            "analyte": row.analyte,
            "species_or_quantity_definition": row.species_or_quantity_definition,
            "aggregation": row.aggregation,
            "value": metric_values[row.analyte],
            "unit": row.unit_token,
            "direction": row.direction,
            "accept_limit": row.accept_limit,
            "reject_limit": row.reject_limit,
            "outcome": _criterion_outcome(metric_values[row.analyte], row),
            "criterion_basis": row.criterion_basis,
        }
        for row in profile.criteria
    )
    outcomes = {row["outcome"] for row in findings}
    campaign_outcome = "reject" if "reject" in outcomes else "review" if "review" in outcomes else "accept"
    report = _bound_report(
        assessment_id=x.assessment_id,
        campaign_id=x.campaign_id,
        campaign_outcome=campaign_outcome,
        caller_profile_id=profile.profile_id,
        analyte_metric_values=metric_values,
        criterion_findings=findings,
        diagnostics=diagnostics,
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Accept, review and reject reflect caller-authored analytical criteria only.",
            "Species definitions and units are compared exactly; no chemical conversion is performed.",
            "No corrosion rate, microbiological risk, standard acceptance, life, or failure probability is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("test-water campaign asset and location must match run context")

    return [
        ModelSpec(
            "inspection.test_water_quality",
            TestWaterQualityCampaignAssessment,
            test_water_quality_campaign,
            {
                "report_schema_version": "1",
                "assessment_id": "1",
                "campaign_id": "1",
                "campaign_outcome": "1",
                "caller_profile_id": "1",
                "analyte_metric_values": "exact caller units",
                "criterion_findings": "mixed",
                "diagnostics": "mixed",
                "input_digest": "1",
                "caller_profile_only": "1",
                "chemical_species_converted": "1",
                "corrosion_rate_or_microbiological_risk_inferred": "1",
                "automatic_standard_acceptance": "1",
                "report_digest": "1",
            },
            (
                "Source, batch, circuit, contact, history, sampling, laboratory and exact analytical identities are preserved.",
                "No species conversion, corrosion-rate/MIC-risk inference, standard limit, or automatic acceptance is produced.",
            ),
            ("authored_test_water_quality_campaign_audit",),
            context_validator=same_identity,
        )
    ]
