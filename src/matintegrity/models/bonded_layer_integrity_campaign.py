"""Caller-profile campaign audit for bonded-layer integrity evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

ProcessKind = Literal[
    "surface_preparation",
    "layer_application",
    "bonding",
    "cure",
    "heat_treatment",
    "cooling",
    "other",
]
ObservationCategory = Literal[
    "thickness",
    "adhesion",
    "shear",
    "peel",
    "porosity",
    "disbond",
    "continuity",
    "nde",
]
CampaignMetric = Literal[
    "assembly_count",
    "sample_count",
    "replicate_group_count",
    "independent_source_group_count",
    "valid_observation_fraction",
]


class BondedAssemblyGeometry(Contract):
    geometry_id: str = Field(min_length=1)
    substrate_thickness: Positive
    layer_nominal_thickness: Positive
    bonded_area: Positive
    thickness_unit_token: str = Field(min_length=1)
    area_unit_token: str = Field(min_length=1)
    geometry_uncertainty: Nonnegative
    coordinate_frame_id: str = Field(min_length=1)
    geometry_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class BondProcessEvent(Contract):
    event_id: str = Field(min_length=1)
    sequence_index: int = Field(ge=0)
    process_kind: ProcessKind
    process_step_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_recorded_temperature_K: Positive
    maximum_recorded_temperature_K: Positive
    expanded_temperature_uncertainty_K: Nonnegative
    applied_pressure: Nonnegative | None = None
    pressure_unit_token: str | None = Field(default=None, min_length=1)
    expanded_pressure_uncertainty: Nonnegative | None = None
    process_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    process_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_event(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("bond-process events require positive duration")
        if self.maximum_recorded_temperature_K < self.minimum_recorded_temperature_K:
            raise ValueError("bond-process temperature bounds must be ordered")
        pressure_fields = (
            self.applied_pressure,
            self.pressure_unit_token,
            self.expanded_pressure_uncertainty,
        )
        if any(value is not None for value in pressure_fields) and any(
            value is None for value in pressure_fields
        ):
            raise ValueError("bond-process pressure requires value, unit, and uncertainty")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid bond-process events require a basis")
        return self


class BondedAssemblyEvidence(Contract):
    assembly_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    substrate_id: str = Field(min_length=1)
    substrate_material_id: str = Field(min_length=1)
    substrate_material_lot_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    layer_id: str = Field(min_length=1)
    layer_material_id: str = Field(min_length=1)
    layer_material_lot_id: str = Field(min_length=1)
    layer_condition_id: str = Field(min_length=1)
    interface_id: str = Field(min_length=1)
    interface_definition: str = Field(min_length=1)
    bond_process_id: str = Field(min_length=1)
    bond_process_revision: str = Field(min_length=1)
    bond_process_provider_id: str = Field(min_length=1)
    bond_process_route_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry: BondedAssemblyGeometry
    process_events: tuple[BondProcessEvent, ...] = Field(min_length=1)
    assembly_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_process(self):
        ids = [row.event_id for row in self.process_events]
        sequence = [row.sequence_index for row in self.process_events]
        if len(set(ids)) != len(ids) or len(set(sequence)) != len(sequence):
            raise ValueError("bond-process event identities and sequence indices must be unique")
        if tuple(sorted(self.process_events, key=lambda row: row.sequence_index)) != self.process_events:
            raise ValueError("bond-process events must be supplied in sequence order")
        return self


class BondedLayerSample(Contract):
    sample_id: str = Field(min_length=1)
    assembly_id: str = Field(min_length=1)
    interface_id: str = Field(min_length=1)
    sampling_plan_id: str = Field(min_length=1)
    physical_location_definition: str = Field(min_length=1)
    orientation_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    replicate_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    sampling_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class BondedLayerObservation(Contract):
    observation_id: str = Field(min_length=1)
    assembly_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    interface_id: str = Field(min_length=1)
    observation_category: ObservationCategory
    test_or_examination_method_id: str = Field(min_length=1)
    method_revision: str = Field(min_length=1)
    metric_id: str | None = Field(default=None, min_length=1)
    metric_definition: str | None = Field(default=None, min_length=1)
    value: float | None = None
    unit_token: str | None = Field(default=None, min_length=1)
    expanded_uncertainty: Nonnegative | None = None
    uncertainty_basis: str | None = Field(default=None, min_length=1)
    reported_finding: str = Field(min_length=1)
    caller_reported_failure_descriptor: str | None = Field(default=None, min_length=1)
    caller_disposition_id: str | None = Field(default=None, min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    raw_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    observation_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_observation(self):
        quantitative = (
            self.metric_id,
            self.metric_definition,
            self.value,
            self.unit_token,
            self.expanded_uncertainty,
            self.uncertainty_basis,
        )
        if any(value is not None for value in quantitative) and any(value is None for value in quantitative):
            raise ValueError("quantitative bonded-layer observations require complete metric evidence")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid bonded-layer observations require a basis")
        return self


class BondedLayerCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    criterion_source: Literal["campaign", "observation"]
    campaign_metric: CampaignMetric | None = None
    observation_category: ObservationCategory | None = None
    observation_metric_id: str | None = Field(default=None, min_length=1)
    aggregation: Literal["minimum", "maximum"]
    direction: Literal["minimum", "maximum"]
    accept_limit: float
    reject_limit: float
    unit_token: str = Field(min_length=1)
    criterion_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_criterion(self):
        if self.criterion_source == "campaign":
            if (
                self.campaign_metric is None
                or self.observation_category is not None
                or self.observation_metric_id is not None
            ):
                raise ValueError("campaign criteria require only a campaign metric")
        elif (
            self.campaign_metric is not None
            or self.observation_category is None
            or self.observation_metric_id is None
        ):
            raise ValueError("observation criteria require category and metric identity")
        if self.direction == "minimum" and self.reject_limit > self.accept_limit:
            raise ValueError("minimum bonded-layer criteria require reject <= accept")
        if self.direction == "maximum" and self.reject_limit < self.accept_limit:
            raise ValueError("maximum bonded-layer criteria require accept <= reject")
        return self


class BondedLayerCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    required_process_kinds: tuple[ProcessKind, ...] = Field(min_length=1)
    required_observation_categories: tuple[ObservationCategory, ...] = Field(min_length=1)
    criteria: tuple[BondedLayerCriterion, ...] = Field(min_length=1)
    profile_provider_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    profile_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_acceptance_authority: str = Field(min_length=1)
    built_in_code_or_specification_limits_used: Literal[False] = False
    automatic_cohesive_or_adhesive_mechanism_claimed: Literal[False] = False
    service_life_claimed: Literal[False] = False
    physical_qualification_claimed: Literal[False] = False
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_profile(self):
        if len(set(self.required_process_kinds)) != len(self.required_process_kinds):
            raise ValueError("required bond-process kinds must be unique")
        if len(set(self.required_observation_categories)) != len(self.required_observation_categories):
            raise ValueError("required bonded-layer observation categories must be unique")
        ids = [row.criterion_id for row in self.criteria]
        keys = [
            (row.criterion_source, row.campaign_metric, row.observation_category, row.observation_metric_id)
            for row in self.criteria
        ]
        if len(set(ids)) != len(ids) or len(set(keys)) != len(keys):
            raise ValueError("bonded-layer criteria must have unique identities and metric sources")
        return self


class BondedLayerIntegrityCampaignAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    assemblies: tuple[BondedAssemblyEvidence, ...] = Field(min_length=1)
    samples: tuple[BondedLayerSample, ...] = Field(min_length=1)
    observations: tuple[BondedLayerObservation, ...] = Field(min_length=1)
    caller_profile: BondedLayerCallerProfile
    substrate_layer_lot_interface_and_geometry_reviewed: bool
    bond_process_provider_route_and_order_reviewed: bool
    process_time_temperature_pressure_and_digests_reviewed: bool
    sampling_location_orientation_and_groups_reviewed: bool
    observation_method_units_uncertainty_and_findings_reviewed: bool
    replicate_source_and_independence_claims_reviewed: bool
    provider_provenance_and_digests_reviewed: bool
    caller_profile_reviewed: bool
    invalid_and_missing_records_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_campaign(self):
        identities = {
            "assembly": [row.assembly_id for row in self.assemblies],
            "product": [row.product_id for row in self.assemblies],
            "interface": [row.interface_id for row in self.assemblies],
            "sample": [row.sample_id for row in self.samples],
            "observation": [row.observation_id for row in self.observations],
            "raw-data digest": [row.raw_data_digest for row in self.observations],
            "observation digest": [row.observation_record_digest for row in self.observations],
        }
        for label, values in identities.items():
            if len(set(values)) != len(values):
                raise ValueError(f"bonded-layer campaign {label} identities must be unique")
        assembly_by_id = {row.assembly_id: row for row in self.assemblies}
        sample_by_id = {row.sample_id: row for row in self.samples}
        for sample in self.samples:
            assembly = assembly_by_id.get(sample.assembly_id)
            if assembly is None or sample.interface_id != assembly.interface_id:
                raise ValueError("samples must match their declared assembly and interface")
        for row in self.observations:
            sample = sample_by_id.get(row.sample_id)
            if sample is None or (row.assembly_id, row.interface_id) != (
                sample.assembly_id,
                sample.interface_id,
            ):
                raise ValueError("observations must match their declared sample, assembly, and interface")
        return self


class BondedLayerIntegrityCampaignReport(Contract):
    report_schema_version: Literal["matintegrity.bonded_layer_integrity_campaign_report.v1"] = (
        "matintegrity.bonded_layer_integrity_campaign_report.v1"
    )
    assessment_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    campaign_outcome: Literal["accept", "review", "reject", "insufficient_evidence"]
    caller_profile_id: str = Field(min_length=1)
    metric_values: dict[str, float]
    criterion_findings: tuple[dict[str, Any], ...]
    diagnostics: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    caller_profile_only: Literal[True] = True
    automatic_failure_mechanism: Literal[False] = False
    service_life_or_specification_acceptance: Literal[False] = False
    physical_qualification: Literal[False] = False
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def digest_is_bound(self, info: ValidationInfo):
        if not (
            isinstance(info.context, dict) and info.context.get("allow_unbound_digest")
        ) and self.report_digest != canonical_digest(self.digest_payload()):
            raise ValueError("bonded-layer campaign report digest does not match content")
        return self


def _bound_report(**payload: Any) -> BondedLayerIntegrityCampaignReport:
    unsigned = BondedLayerIntegrityCampaignReport.model_validate(
        {**payload, "report_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return BondedLayerIntegrityCampaignReport.model_validate(
        {**payload, "report_digest": canonical_digest(unsigned.digest_payload())}
    )


def _criterion_outcome(value: float, row: BondedLayerCriterion) -> str:
    if row.direction == "minimum":
        return "accept" if value >= row.accept_limit else "reject" if value <= row.reject_limit else "review"
    return "accept" if value <= row.accept_limit else "reject" if value >= row.reject_limit else "review"


def bonded_layer_integrity_campaign(x: BondedLayerIntegrityCampaignAssessment) -> Calculation:
    review_fields = (
        "substrate_layer_lot_interface_and_geometry_reviewed",
        "bond_process_provider_route_and_order_reviewed",
        "process_time_temperature_pressure_and_digests_reviewed",
        "sampling_location_orientation_and_groups_reviewed",
        "observation_method_units_uncertainty_and_findings_reviewed",
        "replicate_source_and_independence_claims_reviewed",
        "provider_provenance_and_digests_reviewed",
        "caller_profile_reviewed",
        "invalid_and_missing_records_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    invalid_events = [
        row.event_id for assembly in x.assemblies for row in assembly.process_events if not row.record_valid
    ]
    invalid_observations = [row.observation_id for row in x.observations if not row.record_valid]
    profile = x.caller_profile
    represented_processes = {row.process_kind for assembly in x.assemblies for row in assembly.process_events}
    missing_processes = sorted(set(profile.required_process_kinds) - represented_processes)
    missing_categories = sorted(
        set(profile.required_observation_categories) - {row.observation_category for row in x.observations}
    )
    input_digest = canonical_digest(x.model_dump(mode="json"))
    diagnostics: dict[str, Any] = {
        "missing_reviews": missing_reviews,
        "invalid_process_event_ids": invalid_events,
        "invalid_observation_ids": invalid_observations,
        "missing_required_process_kinds": missing_processes,
        "missing_required_observation_categories": missing_categories,
        "assembly_ids": [row.assembly_id for row in x.assemblies],
        "interface_ids": [row.interface_id for row in x.assemblies],
        "sample_ids": [row.sample_id for row in x.samples],
        "caller_reported_failure_descriptors": [
            row.caller_reported_failure_descriptor
            for row in x.observations
            if row.caller_reported_failure_descriptor is not None
        ],
        "raw_data_digests": [row.raw_data_digest for row in x.observations],
        "observation_record_digests": [row.observation_record_digest for row in x.observations],
    }
    if missing_reviews or invalid_events or invalid_observations or missing_processes or missing_categories:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values={},
            criterion_findings=(),
            diagnostics=diagnostics,
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Complete reviewed bonded-layer campaign evidence is required.",),
        )

    campaign_values = {
        "assembly_count": float(len(x.assemblies)),
        "sample_count": float(len(x.samples)),
        "replicate_group_count": float(len({row.replicate_group_id for row in x.samples})),
        "independent_source_group_count": float(
            len({(row.source_group_id, row.independence_group_id) for row in x.samples})
        ),
        "valid_observation_fraction": sum(row.record_valid for row in x.observations) / len(x.observations),
    }
    campaign_units = {key: "1" if key == "valid_observation_fraction" else "count" for key in campaign_values}
    metric_values: dict[str, float] = {}
    metric_units: dict[str, str] = {}
    missing_criteria: list[str] = []
    unit_conflicts: list[str] = []
    for criterion in profile.criteria:
        if criterion.criterion_source == "campaign":
            key = f"campaign:{criterion.campaign_metric}"
            value = campaign_values[criterion.campaign_metric]
            unit = campaign_units[criterion.campaign_metric]
        else:
            key = f"observation:{criterion.observation_category}:{criterion.observation_metric_id}"
            matching = [
                row
                for row in x.observations
                if row.observation_category == criterion.observation_category
                and row.metric_id == criterion.observation_metric_id
            ]
            if not matching:
                missing_criteria.append(criterion.criterion_id)
                continue
            units = {row.unit_token for row in matching}
            if units != {criterion.unit_token}:
                unit_conflicts.append(criterion.criterion_id)
                continue
            values = [row.value for row in matching]
            value = min(values) if criterion.aggregation == "minimum" else max(values)
            unit = criterion.unit_token
        if unit != criterion.unit_token:
            unit_conflicts.append(criterion.criterion_id)
            continue
        metric_values[key] = value
        metric_units[key] = unit
    if missing_criteria or unit_conflicts:
        report = _bound_report(
            assessment_id=x.assessment_id,
            campaign_id=x.campaign_id,
            campaign_outcome="insufficient_evidence",
            caller_profile_id=profile.profile_id,
            metric_values=metric_values,
            criterion_findings=(),
            diagnostics={
                **diagnostics,
                "missing_criterion_evidence_ids": missing_criteria,
                "criterion_unit_conflict_ids": unit_conflicts,
            },
            input_digest=input_digest,
        )
        return Calculation(
            status="needs_data",
            values=report.model_dump(),
            notes=("Every caller criterion requires matching exact-unit evidence.",),
        )

    def criterion_key(row: BondedLayerCriterion) -> str:
        if row.criterion_source == "campaign":
            return f"campaign:{row.campaign_metric}"
        return f"observation:{row.observation_category}:{row.observation_metric_id}"

    findings = tuple(
        {
            "criterion_id": row.criterion_id,
            "metric_key": criterion_key(row),
            "aggregation": row.aggregation,
            "value": metric_values[criterion_key(row)],
            "unit": metric_units[criterion_key(row)],
            "direction": row.direction,
            "accept_limit": row.accept_limit,
            "reject_limit": row.reject_limit,
            "outcome": _criterion_outcome(metric_values[criterion_key(row)], row),
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
        metric_values=metric_values,
        criterion_findings=findings,
        diagnostics=diagnostics,
        input_digest=input_digest,
    )
    return Calculation(
        status="computed",
        values=report.model_dump(),
        notes=(
            "Accept, review and reject reflect caller-authored campaign criteria only.",
            "Caller failure descriptors are preserved but are not reclassified as cohesive or adhesive mechanisms.",
            "No specification limit, qualification, service life, defect criticality, or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("bonded-layer campaign asset and location must match run context")

    return [
        ModelSpec(
            "materials.bonded_layer_integrity",
            BondedLayerIntegrityCampaignAssessment,
            bonded_layer_integrity_campaign,
            {
                "report_schema_version": "1",
                "assessment_id": "1",
                "campaign_id": "1",
                "campaign_outcome": "1",
                "caller_profile_id": "1",
                "metric_values": "mixed",
                "criterion_findings": "mixed",
                "diagnostics": "mixed",
                "input_digest": "1",
                "caller_profile_only": "1",
                "automatic_failure_mechanism": "1",
                "service_life_or_specification_acceptance": "1",
                "physical_qualification": "1",
                "report_digest": "1",
            },
            (
                "Substrate, layer, lots, interface, geometry, process history, samples and observations remain caller evidence.",
                "No automatic mechanism classification, specification acceptance, service life, or qualification is produced.",
            ),
            ("authored_bonded_layer_integrity_campaign_audit",),
            context_validator=same_identity,
        )
    ]
