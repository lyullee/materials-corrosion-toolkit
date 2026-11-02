"""Caller-profile audit of storage-preservation events and exposure evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

PreservationFactKind = Literal[
    "temperature",
    "relative_humidity",
    "dewpoint",
    "water_ingress",
    "desiccant",
    "inhibitor",
    "cover",
    "seal",
    "surface",
    "corrosion_observation",
]


class PreservationSystemIdentity(Contract):
    preservation_system_id: str = Field(min_length=1)
    preservation_method_id: str = Field(min_length=1)
    preservation_material_id: str = Field(min_length=1)
    preservation_material_batch_id: str = Field(min_length=1)
    application_procedure_id: str = Field(min_length=1)
    system_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class PreservationCampaignFact(Contract):
    fact_id: str = Field(min_length=1)
    fact_kind: PreservationFactKind
    quantity_id: str = Field(min_length=1)
    result_mode: Literal["quantitative", "qualitative"]
    status: Literal["reported", "missing", "invalid"]
    value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    qualitative_class: str | None = None
    qualitative_uncertainty_basis: str | None = None
    method_id: str = Field(min_length=1)
    fact_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_fact(self):
        if self.status != "reported":
            if not self.invalid_or_missing_basis:
                raise ValueError("missing or invalid preservation facts require a basis")
            if any(
                value is not None for value in (self.value, self.expanded_uncertainty, self.qualitative_class)
            ):
                raise ValueError("missing or invalid preservation facts cannot carry results")
            return self
        if self.result_mode == "quantitative":
            if self.value is None or self.expanded_uncertainty is None:
                raise ValueError("quantitative preservation facts require value and uncertainty")
            if self.qualitative_class is not None or self.qualitative_uncertainty_basis is not None:
                raise ValueError("quantitative preservation facts cannot carry a qualitative result")
        else:
            if not self.qualitative_class or not self.qualitative_uncertainty_basis:
                raise ValueError("qualitative preservation facts require class and uncertainty basis")
            if self.value is not None or self.expanded_uncertainty is not None or self.unit_token != "class":
                raise ValueError("qualitative preservation facts use only the exact class unit")
        return self


class StoragePreservationEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    event_kind: Literal["storage_start", "exposure", "inspection", "renewal", "storage_end"]
    start_time_s: Nonnegative
    end_time_s: Positive | None = None
    storage_location_id: str = Field(min_length=1)
    preservation_system_id: str = Field(min_length=1)
    facts: tuple[PreservationCampaignFact, ...] = ()
    caller_validity_status: Literal["valid", "invalid", "unknown"]
    caller_validity_basis: str = Field(min_length=1)
    event_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_group_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def event_shape(self):
        if self.event_kind == "exposure":
            if self.end_time_s is None or self.end_time_s <= self.start_time_s:
                raise ValueError("exposure events require a positive interval")
            if not self.facts:
                raise ValueError("exposure events require environment or preservation facts")
        elif self.end_time_s is not None:
            raise ValueError("instantaneous storage events cannot carry an end time")
        keys = [(row.fact_kind, row.quantity_id) for row in self.facts]
        if len(set(keys)) != len(keys):
            raise ValueError("preservation facts must be unique by kind and quantity within an event")
        return self


class PreservationFactCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    fact_kind: PreservationFactKind
    quantity_id: str = Field(min_length=1)
    result_mode: Literal["quantitative", "qualitative"]
    unit_token: str = Field(min_length=1)
    minimum_acceptable: float | None = None
    maximum_acceptable: float | None = None
    accepted_qualitative_classes: tuple[str, ...] = ()
    required_event_kinds: tuple[Literal["exposure", "inspection", "renewal"], ...] = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def criterion_mode(self):
        if self.result_mode == "quantitative":
            if self.minimum_acceptable is None and self.maximum_acceptable is None:
                raise ValueError("quantitative preservation criteria require caller bounds")
            if self.accepted_qualitative_classes:
                raise ValueError("quantitative preservation criteria cannot carry classes")
        else:
            if self.unit_token != "class" or not self.accepted_qualitative_classes:
                raise ValueError("qualitative preservation criteria require accepted classes")
            if self.minimum_acceptable is not None or self.maximum_acceptable is not None:
                raise ValueError("qualitative preservation criteria cannot carry numeric bounds")
        if (
            self.minimum_acceptable is not None
            and self.maximum_acceptable is not None
            and self.minimum_acceptable > self.maximum_acceptable
        ):
            raise ValueError("preservation criterion bounds must be ordered")
        return self


class StoragePreservationCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    storage_area_id: str = Field(min_length=1)
    storage_location_id: str = Field(min_length=1)
    supported_preservation_system_ids: tuple[str, ...] = Field(min_length=1)
    maximum_uncovered_duration_s: Nonnegative
    minimum_inspection_count: int = Field(ge=0)
    minimum_renewal_count: int = Field(ge=0)
    fact_criteria: tuple[PreservationFactCriterion, ...] = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    built_in_standard_cycle_used: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_criteria(self):
        ids = [row.criterion_id for row in self.fact_criteria]
        if len(set(ids)) != len(ids):
            raise ValueError("preservation criterion identifiers must be unique")
        return self


class StoragePreservationCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    item_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    storage_area_id: str = Field(min_length=1)
    storage_location_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    preservation_systems: tuple[PreservationSystemIdentity, ...] = Field(min_length=1)
    events: tuple[StoragePreservationEvent, ...] = Field(min_length=1)
    caller_profile: StoragePreservationCallerProfile
    item_material_area_and_storage_location_reviewed: bool
    preservation_methods_material_batches_and_procedures_reviewed: bool
    event_clock_order_and_interval_coverage_reviewed: bool
    environment_and_preservation_fact_units_uncertainties_reviewed: bool
    inspections_renewals_surface_and_corrosion_observations_reviewed: bool
    caller_validity_profile_missingness_and_digests_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("storage-preservation campaign horizon must have positive duration")
        for values, label in (
            ([row.preservation_system_id for row in self.preservation_systems], "system"),
            ([row.event_id for row in self.events], "event"),
            ([row.sequence_index for row in self.events], "event sequence"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"storage-preservation {label} identifiers must be unique")
        if [row.sequence_index for row in self.events] != sorted(row.sequence_index for row in self.events):
            raise ValueError("storage-preservation events must follow sequence order")
        if [row.start_time_s for row in self.events] != sorted(row.start_time_s for row in self.events):
            raise ValueError("storage-preservation event times must be nondecreasing")
        if any(row.storage_location_id != self.storage_location_id for row in self.events):
            raise ValueError("storage events must use the declared storage location")
        systems = {row.preservation_system_id for row in self.preservation_systems}
        if {row.preservation_system_id for row in self.events} - systems:
            raise ValueError("storage events must reference declared preservation systems")
        exposures = [row for row in self.events if row.event_kind == "exposure"]
        for left, right in zip(exposures, exposures[1:], strict=False):
            if right.start_time_s < left.end_time_s:
                raise ValueError("storage exposure events must be ordered and nonoverlapping")
        if any(
            row.start_time_s < self.horizon_start_s
            or (row.end_time_s or row.start_time_s) > self.horizon_end_s
            for row in self.events
        ):
            raise ValueError("storage events must remain inside the campaign horizon")
        return self


def storage_preservation_campaign(x: StoragePreservationCampaign) -> Calculation:
    profile = x.caller_profile
    missing_reviews = [
        name
        for name in (
            "item_material_area_and_storage_location_reviewed",
            "preservation_methods_material_batches_and_procedures_reviewed",
            "event_clock_order_and_interval_coverage_reviewed",
            "environment_and_preservation_fact_units_uncertainties_reviewed",
            "inspections_renewals_surface_and_corrosion_observations_reviewed",
            "caller_validity_profile_missingness_and_digests_reviewed",
        )
        if not getattr(x, name)
    ]
    identity_mismatches = [
        name
        for name in ("item_id", "material_id", "storage_area_id", "storage_location_id")
        if getattr(x, name) != getattr(profile, name)
    ]
    unsupported_system_ids = sorted(
        {row.preservation_system_id for row in x.events} - set(profile.supported_preservation_system_ids)
    )
    invalid_events = [row.event_id for row in x.events if row.caller_validity_status != "valid"]
    if missing_reviews or identity_mismatches or unsupported_system_ids or invalid_events:
        return _result(
            x,
            "insufficient_evidence",
            {
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatches,
                "unsupported_preservation_system_ids": unsupported_system_ids,
                "invalid_or_unknown_event_ids": invalid_events,
            },
        )

    exposure_events = [row for row in x.events if row.event_kind == "exposure"]
    represented = sum(row.end_time_s - row.start_time_s for row in exposure_events)
    uncovered = x.horizon_end_s - x.horizon_start_s - represented
    findings = [
        {
            "criterion_id": "interval_coverage",
            "event_id": "campaign",
            "outcome": "within" if uncovered <= profile.maximum_uncovered_duration_s else "outside",
            "value": uncovered,
            "unit": "s",
        }
    ]
    inspection_count = sum(row.event_kind == "inspection" for row in x.events)
    renewal_count = sum(row.event_kind == "renewal" for row in x.events)
    for name, value, minimum in (
        ("inspection_count", inspection_count, profile.minimum_inspection_count),
        ("renewal_count", renewal_count, profile.minimum_renewal_count),
    ):
        findings.append(
            {
                "criterion_id": name,
                "event_id": "campaign",
                "outcome": "within" if value >= minimum else "outside",
                "value": value,
                "unit": "count",
            }
        )

    missing_or_mismatch = []
    for event in x.events:
        facts = {(row.fact_kind, row.quantity_id): row for row in event.facts}
        for criterion in profile.fact_criteria:
            if event.event_kind not in criterion.required_event_kinds:
                continue
            fact = facts.get((criterion.fact_kind, criterion.quantity_id))
            if (
                fact is None
                or fact.status != "reported"
                or fact.result_mode != criterion.result_mode
                or fact.unit_token != criterion.unit_token
            ):
                missing_or_mismatch.append(f"{event.event_id}:{criterion.criterion_id}")
                continue
            if criterion.result_mode == "qualitative":
                outcome = (
                    "within"
                    if fact.qualitative_class in criterion.accepted_qualitative_classes
                    else "outside"
                )
                value, uncertainty = fact.qualitative_class, fact.qualitative_uncertainty_basis
            else:
                lower, upper = fact.value - fact.expanded_uncertainty, fact.value + fact.expanded_uncertainty
                within = (criterion.minimum_acceptable is None or lower >= criterion.minimum_acceptable) and (
                    criterion.maximum_acceptable is None or upper <= criterion.maximum_acceptable
                )
                outside = (
                    criterion.minimum_acceptable is not None and upper < criterion.minimum_acceptable
                ) or (criterion.maximum_acceptable is not None and lower > criterion.maximum_acceptable)
                outcome = "within" if within else "outside" if outside else "boundary_overlap"
                value, uncertainty = fact.value, fact.expanded_uncertainty
            findings.append(
                {
                    "criterion_id": criterion.criterion_id,
                    "event_id": event.event_id,
                    "fact_id": fact.fact_id,
                    "outcome": outcome,
                    "value": value,
                    "uncertainty_or_basis": uncertainty,
                    "unit": fact.unit_token,
                }
            )
    if missing_or_mismatch:
        return _result(
            x,
            "insufficient_evidence",
            {"missing_invalid_or_mismatch_facts": missing_or_mismatch, "criterion_findings": findings},
        )
    outcomes = {row["outcome"] for row in findings}
    outcome = "reject" if "outside" in outcomes else "review" if "boundary_overlap" in outcomes else "accept"
    return _result(
        x,
        outcome,
        {
            "criterion_findings": findings,
            "horizon_duration_s": x.horizon_end_s - x.horizon_start_s,
            "represented_exposure_duration_s": represented,
            "uncovered_duration_s": uncovered,
            "inspection_count": inspection_count,
            "renewal_count": renewal_count,
            "event_ids": [row.event_id for row in x.events],
            "source_group_ids": sorted({row.source_group_id for row in x.events}),
        },
    )


def _result(x, quality_outcome, additions):
    body = {
        "assessment_id": x.assessment_id,
        "campaign_id": x.campaign_id,
        "quality_outcome": quality_outcome,
        "caller_profile_id": x.caller_profile.profile_id,
        "corrosion_rate_inferred": False,
        "remaining_life_inferred": False,
        "built_in_standard_cycle_applied": False,
        "automatic_acceptance_claim": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        **additions,
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        status="needs_data" if quality_outcome == "insufficient_evidence" else "computed",
        values=body,
        notes=(
            "Storage events and preservation observations are evaluated only against caller-owned criteria.",
            "No corrosion rate, remaining life, bundled renewal cycle, standard limit or automatic acceptance is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("storage-preservation campaign asset and location must match run context")

    return [
        ModelSpec(
            "fabrication.storage_preservation",
            StoragePreservationCampaign,
            storage_preservation_campaign,
            {
                "assessment_id": "1",
                "campaign_id": "1",
                "quality_outcome": "1",
                "caller_profile_id": "1",
                "criterion_findings": "mixed",
                "horizon_duration_s": "s",
                "represented_exposure_duration_s": "s",
                "uncovered_duration_s": "s",
                "inspection_count": "count",
                "renewal_count": "count",
                "event_ids": "1",
                "source_group_ids": "1",
                "input_digest": "1",
                "report_digest": "1",
            },
            (
                "Item, material, area, storage location, preservation method, material batch and event identities are exact caller inputs.",
                "Ordered exposure, inspection and renewal records retain environmental, preservation, surface and corrosion observations.",
                "Campaign outcomes use caller criteria without rate, life, standard-cycle or automatic acceptance inference.",
            ),
            ("authored_storage_preservation_campaign_evidence_audit",),
            context_validator=same_identity,
        )
    ]
