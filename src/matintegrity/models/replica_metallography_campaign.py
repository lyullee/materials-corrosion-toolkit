"""Caller-profile audit of replica-metallography campaign observations."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

ObservationKind = Literal[
    "grain",
    "cavity",
    "phase",
    "precipitate",
    "decarburization",
    "user_defined",
]


class ReplicaServiceInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    environment_descriptor_id: str = Field(min_length=1)
    service_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("replica service intervals require positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("replica service temperature bounds must be ordered")
        return self


class ReplicaAcquisitionConfiguration(Contract):
    surface_preparation_id: str = Field(min_length=1)
    surface_preparation_definition: str = Field(min_length=1)
    replication_medium_id: str = Field(min_length=1)
    replication_medium_lot_id: str = Field(min_length=1)
    magnification: Positive
    magnification_unit_token: Literal["1"] = "1"
    instrument_id: str = Field(min_length=1)
    instrument_revision: str = Field(min_length=1)
    instrument_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_id: str = Field(min_length=1)
    calibration_revision: str = Field(min_length=1)
    calibration_status: Literal["valid", "invalid", "missing"]
    calibration_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def calibration_basis(self):
        if self.calibration_status != "valid" and not self.invalid_or_missing_basis:
            raise ValueError("invalid or missing replica calibration requires a basis")
        return self


class ReplicaCampaignObservation(Contract):
    observation_id: str = Field(min_length=1)
    observation_kind: ObservationKind
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    result_mode: Literal["quantitative", "qualitative"]
    status: Literal["reported", "missing", "invalid"]
    value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    qualitative_class: str | None = None
    qualitative_uncertainty_basis: str | None = None
    observer_id: str = Field(min_length=1)
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def mode_and_status(self):
        if self.status != "reported":
            if not self.invalid_or_missing_basis:
                raise ValueError("missing or invalid replica observations require a basis")
            if any(
                value is not None for value in (self.value, self.expanded_uncertainty, self.qualitative_class)
            ):
                raise ValueError("missing or invalid replica observations cannot carry results")
            return self
        if self.result_mode == "quantitative":
            if self.value is None or self.expanded_uncertainty is None:
                raise ValueError("quantitative replica observations require value and uncertainty")
            if self.qualitative_class is not None or self.qualitative_uncertainty_basis is not None:
                raise ValueError("quantitative replica observations cannot carry a qualitative class")
        else:
            if not self.qualitative_class or not self.qualitative_uncertainty_basis:
                raise ValueError("qualitative replica observations require class and uncertainty basis")
            if self.value is not None or self.expanded_uncertainty is not None or self.unit_token != "class":
                raise ValueError("qualitative replica observations use only the exact class unit")
        return self


class ReplicaCampaignField(Contract):
    field_id: str = Field(min_length=1)
    replica_id: str = Field(min_length=1)
    replica_site_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    configuration: ReplicaAcquisitionConfiguration
    image_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    field_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observations: tuple[ReplicaCampaignObservation, ...] = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    caller_validity_status: Literal["valid", "invalid", "unknown"]
    caller_validity_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_observations(self):
        ids = [row.observation_id for row in self.observations]
        keys = [(row.observation_kind, row.metric_id) for row in self.observations]
        if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
            raise ValueError("replica field observations require unique identifiers and metrics")
        return self


class ReplicaObservationCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    observation_kind: ObservationKind
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    result_mode: Literal["quantitative", "qualitative"]
    unit_token: str = Field(min_length=1)
    minimum_acceptable: float | None = None
    maximum_acceptable: float | None = None
    accepted_qualitative_classes: tuple[str, ...] = ()
    criterion_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def criterion_mode(self):
        if self.result_mode == "quantitative":
            if self.minimum_acceptable is None and self.maximum_acceptable is None:
                raise ValueError("quantitative replica criteria require at least one caller bound")
            if self.accepted_qualitative_classes:
                raise ValueError("quantitative replica criteria cannot carry qualitative classes")
            if (
                self.minimum_acceptable is not None
                and self.maximum_acceptable is not None
                and self.minimum_acceptable > self.maximum_acceptable
            ):
                raise ValueError("quantitative replica criterion bounds must be ordered")
        else:
            if self.unit_token != "class" or not self.accepted_qualitative_classes:
                raise ValueError("qualitative replica criteria require accepted classes and class unit")
            if self.minimum_acceptable is not None or self.maximum_acceptable is not None:
                raise ValueError("qualitative replica criteria cannot carry numeric bounds")
        return self


class ReplicaCampaignCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    supported_replica_site_ids: tuple[str, ...] = Field(min_length=1)
    supported_environment_descriptor_ids: tuple[str, ...] = Field(min_length=1)
    required_surface_preparation_id: str = Field(min_length=1)
    required_replication_medium_id: str = Field(min_length=1)
    required_magnification: Positive
    magnification_tolerance: Nonnegative
    required_instrument_id: str = Field(min_length=1)
    required_calibration_id: str = Field(min_length=1)
    criteria: tuple[ReplicaObservationCriterion, ...] = Field(min_length=1)
    minimum_valid_field_count: int = Field(ge=1)
    minimum_independence_group_count: int = Field(ge=1)
    caller_validity_policy_id: str = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    built_in_grade_table_used: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_criteria(self):
        keys = [(row.observation_kind, row.metric_id) for row in self.criteria]
        if len(set(keys)) != len(keys):
            raise ValueError("replica campaign criteria must be unique by observation metric")
        return self


class ReplicaMetallographyCampaign(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    service_history: tuple[ReplicaServiceInterval, ...] = Field(min_length=1)
    fields: tuple[ReplicaCampaignField, ...] = Field(min_length=1)
    caller_profile: ReplicaCampaignCallerProfile
    component_location_material_heat_and_service_history_reviewed: bool
    surface_preparation_medium_magnification_and_instrument_reviewed: bool
    calibration_image_and_record_digests_reviewed: bool
    observation_definitions_units_classes_and_uncertainties_reviewed: bool
    replicate_source_and_independence_groups_reviewed: bool
    caller_validity_flags_profile_and_missingness_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        for values, label in (
            ([row.interval_id for row in self.service_history], "service interval"),
            ([row.field_id for row in self.fields], "field"),
            ([row.sequence_index for row in self.fields], "field sequence"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"replica campaign {label} identifiers must be unique")
        for left, right in zip(self.service_history, self.service_history[1:], strict=False):
            if right.start_time_s < left.end_time_s:
                raise ValueError("replica service intervals must be ordered and nonoverlapping")
        return self


def replica_metallography_campaign(x: ReplicaMetallographyCampaign) -> Calculation:
    profile = x.caller_profile
    missing_reviews = [
        name
        for name in (
            "component_location_material_heat_and_service_history_reviewed",
            "surface_preparation_medium_magnification_and_instrument_reviewed",
            "calibration_image_and_record_digests_reviewed",
            "observation_definitions_units_classes_and_uncertainties_reviewed",
            "replicate_source_and_independence_groups_reviewed",
            "caller_validity_flags_profile_and_missingness_reviewed",
        )
        if not getattr(x, name)
    ]
    identity_mismatches = [
        name
        for name in ("component_id", "material_id", "material_condition_id", "heat_id")
        if getattr(x, name) != getattr(profile, name)
    ]
    unsupported_service_intervals = [
        row.interval_id
        for row in x.service_history
        if row.environment_descriptor_id not in profile.supported_environment_descriptor_ids
    ]
    invalid_fields, configuration_mismatches = [], []
    for field in x.fields:
        if field.caller_validity_status != "valid" or field.configuration.calibration_status != "valid":
            invalid_fields.append(field.field_id)
        configuration = field.configuration
        if (
            field.replica_site_id not in profile.supported_replica_site_ids
            or configuration.surface_preparation_id != profile.required_surface_preparation_id
            or configuration.replication_medium_id != profile.required_replication_medium_id
            or abs(configuration.magnification - profile.required_magnification)
            > profile.magnification_tolerance
            or configuration.instrument_id != profile.required_instrument_id
            or configuration.calibration_id != profile.required_calibration_id
        ):
            configuration_mismatches.append(field.field_id)
    if (
        missing_reviews
        or identity_mismatches
        or unsupported_service_intervals
        or invalid_fields
        or configuration_mismatches
    ):
        return _result(
            x,
            "insufficient_evidence",
            {
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatches,
                "unsupported_service_interval_ids": unsupported_service_intervals,
                "invalid_field_ids": invalid_fields,
                "configuration_mismatch_field_ids": configuration_mismatches,
            },
        )
    groups = {row.independence_group_id for row in x.fields}
    if (
        len(x.fields) < profile.minimum_valid_field_count
        or len(groups) < profile.minimum_independence_group_count
    ):
        return _result(
            x,
            "insufficient_evidence",
            {"valid_field_count": len(x.fields), "independence_group_count": len(groups)},
        )

    criteria = {(row.observation_kind, row.metric_id): row for row in profile.criteria}
    findings, missing_or_mismatch = [], []
    for field in x.fields:
        observations = {(row.observation_kind, row.metric_id): row for row in field.observations}
        for key, criterion in criteria.items():
            observation = observations.get(key)
            if (
                observation is None
                or observation.status != "reported"
                or observation.metric_definition != criterion.metric_definition
                or observation.result_mode != criterion.result_mode
                or observation.unit_token != criterion.unit_token
            ):
                missing_or_mismatch.append(f"{field.field_id}:{criterion.criterion_id}")
                continue
            if criterion.result_mode == "qualitative":
                outcome = (
                    "within"
                    if observation.qualitative_class in criterion.accepted_qualitative_classes
                    else "outside"
                )
                value = observation.qualitative_class
                uncertainty = observation.qualitative_uncertainty_basis
            else:
                lower = observation.value - observation.expanded_uncertainty
                upper = observation.value + observation.expanded_uncertainty
                within = (criterion.minimum_acceptable is None or lower >= criterion.minimum_acceptable) and (
                    criterion.maximum_acceptable is None or upper <= criterion.maximum_acceptable
                )
                outside = (
                    criterion.minimum_acceptable is not None and upper < criterion.minimum_acceptable
                ) or (criterion.maximum_acceptable is not None and lower > criterion.maximum_acceptable)
                outcome = "within" if within else "outside" if outside else "boundary_overlap"
                value, uncertainty = observation.value, observation.expanded_uncertainty
            findings.append(
                {
                    "field_id": field.field_id,
                    "observation_id": observation.observation_id,
                    "criterion_id": criterion.criterion_id,
                    "observation_kind": observation.observation_kind,
                    "metric_id": observation.metric_id,
                    "value_or_class": value,
                    "uncertainty_or_basis": uncertainty,
                    "unit": observation.unit_token,
                    "outcome": outcome,
                }
            )
    if missing_or_mismatch:
        return _result(
            x,
            "insufficient_evidence",
            {"missing_invalid_or_mismatch_observations": missing_or_mismatch, "criterion_findings": findings},
        )
    outcomes = {row["outcome"] for row in findings}
    outcome = "reject" if "outside" in outcomes else "review" if "boundary_overlap" in outcomes else "accept"
    return _result(
        x,
        outcome,
        {
            "criterion_findings": findings,
            "field_ids": [row.field_id for row in x.fields],
            "replica_ids": [row.replica_id for row in x.fields],
            "source_group_ids": sorted({row.source_group_id for row in x.fields}),
            "independence_group_ids": sorted(groups),
            "service_history_digest": canonical_digest(
                [row.model_dump(mode="json") for row in x.service_history]
            ),
        },
    )


def _result(x, quality_outcome, additions):
    body = {
        "assessment_id": x.assessment_id,
        "campaign_id": x.campaign_id,
        "quality_outcome": quality_outcome,
        "caller_profile_id": x.caller_profile.profile_id,
        "image_automatic_analysis_performed": False,
        "built_in_grade_table_applied": False,
        "creep_life_inferred": False,
        "standard_acceptance_claim": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        **additions,
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        status="needs_data" if quality_outcome == "insufficient_evidence" else "computed",
        values=body,
        notes=(
            "Reported microstructure observations are preserved without image analysis or relabelling.",
            "No grade table, creep-life mapping, bundled acceptance rule or physical qualification claim is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("replica campaign asset and location must match run context")

    return [
        ModelSpec(
            "inspection.replica_metallography_campaign",
            ReplicaMetallographyCampaign,
            replica_metallography_campaign,
            {
                "assessment_id": "1",
                "campaign_id": "1",
                "quality_outcome": "1",
                "caller_profile_id": "1",
                "criterion_findings": "mixed",
                "field_ids": "1",
                "replica_ids": "1",
                "source_group_ids": "1",
                "independence_group_ids": "1",
                "service_history_digest": "1",
                "input_digest": "1",
                "report_digest": "1",
            },
            (
                "Component, location, material, heat and ordered service history are exact caller inputs.",
                "Preparation, replication medium, magnification, instrument, calibration, images and reported observations retain provenance.",
                "Campaign outcomes use caller criteria without image analysis, grade tables, life inference or standard acceptance.",
            ),
            ("authored_replica_metallography_campaign_evidence_audit",),
            context_validator=same_identity,
        )
    ]
