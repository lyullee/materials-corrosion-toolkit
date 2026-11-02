"""Forming process records compared with caller-owned qualification support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

FormingMode = Literal["cold", "hot"]
ThermalStage = Literal["forming", "post_forming_heat_treatment"]
EvidenceKind = Literal["inspection", "property_test"]


class FormingOperation(Contract):
    operation_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    finish_temperature_K: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("forming operation requires positive duration")
        if not self.minimum_temperature_K <= self.finish_temperature_K <= self.maximum_temperature_K:
            raise ValueError("finish temperature must lie inside the recorded operation range")
        return self


class InterOperationCoolingPoint(Contract):
    record_id: str = Field(min_length=1)
    time_s: Nonnegative
    temperature_K: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class FormingTreatmentWaiverBranch(Contract):
    branch_id: str = Field(min_length=1)
    minimum_last_finish_temperature_K: Positive
    finish_boundary_inclusive: bool
    maximum_final_area_reduction_fraction: Fraction
    basis: str = Field(min_length=1)


class FormingSequencePlan(Contract):
    plan_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    minimum_operation_count: int = Field(ge=1)
    maximum_operation_count: int = Field(ge=1)
    minimum_forming_temperature_K: Positive
    maximum_forming_temperature_K: Positive
    maximum_last_operation_temperature_K: Positive
    maximum_single_operation_duration_s: Positive
    maximum_total_operation_duration_s: Positive
    cooling_before_each_subsequent_operation_below_K: Positive | None = None
    waiver_branches: tuple[FormingTreatmentWaiverBranch, ...] = ()
    basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered(self):
        if self.maximum_operation_count < self.minimum_operation_count:
            raise ValueError("operation count support must be ordered")
        if self.maximum_forming_temperature_K < self.minimum_forming_temperature_K:
            raise ValueError("forming temperature support must be ordered")
        if self.maximum_last_operation_temperature_K < self.minimum_forming_temperature_K:
            raise ValueError("last operation support must include the minimum forming temperature")
        if len({b.branch_id for b in self.waiver_branches}) != len(self.waiver_branches):
            raise ValueError("waiver branch IDs must be unique")
        return self


class FormingProcessSequence(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    operations: tuple[FormingOperation, ...] = Field(min_length=1)
    cooling_points: tuple[InterOperationCoolingPoint, ...] = ()
    final_area_reduction_fraction: Fraction | None = None
    selected_plan: FormingSequencePlan
    operation_ranges_finish_temperatures_and_clock_reviewed: bool
    cooling_point_location_and_measurement_reviewed: bool
    final_area_change_and_selected_plan_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique(self):
        for rows, key in ((self.operations, "operation_id"), (self.cooling_points, "record_id")):
            if len({getattr(row, key) for row in rows}) != len(rows):
                raise ValueError("forming sequence record IDs must be unique")
        if any(
            b.start_time_s < a.end_time_s for a, b in zip(self.operations, self.operations[1:], strict=False)
        ):
            raise ValueError("forming operations must be ordered and cannot overlap")
        if any(
            b.time_s <= a.time_s for a, b in zip(self.cooling_points, self.cooling_points[1:], strict=False)
        ):
            raise ValueError("cooling points must have strictly increasing times")
        return self


def forming_process_sequence(x: FormingProcessSequence) -> Calculation:
    plan = x.selected_plan
    base = {
        "component_id": x.component_id,
        "clock_id": x.clock_id,
        "plan_id": plan.plan_id,
        "plan_digest": canonical_digest(plan.model_dump(mode="json")),
    }
    if (x.material_id, x.material_condition_id) != (plan.material_id, plan.material_condition_id):
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Selected plan material identity differs from the component.",),
        )
    if not (
        x.operation_ranges_finish_temperatures_and_clock_reviewed
        and x.cooling_point_location_and_measurement_reviewed
        and x.final_area_change_and_selected_plan_authority_reviewed
    ):
        return Calculation(status="needs_data", values=base)
    outside = []
    durations = [row.end_time_s - row.start_time_s for row in x.operations]
    if not plan.minimum_operation_count <= len(x.operations) <= plan.maximum_operation_count:
        outside.append("operation_count")
    if sum(durations) > plan.maximum_total_operation_duration_s:
        outside.append("total_operation_duration")
    for row, duration in zip(x.operations, durations, strict=True):
        if (
            row.minimum_temperature_K < plan.minimum_forming_temperature_K
            or row.maximum_temperature_K > plan.maximum_forming_temperature_K
            or duration > plan.maximum_single_operation_duration_s
        ):
            outside.append(row.operation_id)
    if x.operations[-1].maximum_temperature_K > plan.maximum_last_operation_temperature_K:
        outside.append("last_operation_maximum_temperature")
    cooling = []
    missing = []
    limit = plan.cooling_before_each_subsequent_operation_below_K
    if limit is not None:
        for left, right in zip(x.operations, x.operations[1:], strict=False):
            points = [p for p in x.cooling_points if left.end_time_s < p.time_s < right.start_time_s]
            witnesses = [p.record_id for p in points if p.temperature_K < limit]
            cooling.append(
                {
                    "preceding_operation_id": left.operation_id,
                    "following_operation_id": right.operation_id,
                    "witness_record_ids": witnesses,
                }
            )
            if not witnesses:
                missing.append(right.operation_id)
    eligible = []
    for branch in plan.waiver_branches:
        finish = x.operations[-1].finish_temperature_K
        temperature_ok = (
            finish >= branch.minimum_last_finish_temperature_K
            if branch.finish_boundary_inclusive
            else finish > branch.minimum_last_finish_temperature_K
        )
        if (
            temperature_ok
            and x.final_area_reduction_fraction is not None
            and x.final_area_reduction_fraction <= branch.maximum_final_area_reduction_fraction
        ):
            eligible.append(branch.branch_id)
    missing_area = bool(plan.waiver_branches) and x.final_area_reduction_fraction is None
    status = "out_of_scope" if outside else "needs_data" if missing or missing_area else "computed"
    return Calculation(
        status=status,
        values=base
        | {
            "outside_support_reasons": outside,
            "inter_operation_cooling": cooling,
            "cooling_witness_missing_before_operation_ids": missing,
            "final_area_reduction_missing": missing_area,
            "eligible_caller_waiver_branch_ids": eligible if status == "computed" else [],
            "declared_treatment_requirement": (
                "waiver_eligible_under_selected_plan"
                if eligible
                else "treatment_required_under_selected_plan"
            )
            if status == "computed"
            else "undetermined",
        },
        notes=(
            "Sequence and waiver conditions come only from the selected caller-owned plan; no standard limits are embedded.",
            "A cooling witness proves only a reviewed observation below the supplied threshold between operations, not continuous monitoring or a cooling-rate model.",
            "Waiver eligibility does not establish actual treatment omission authority, material properties or code acceptance.",
        ),
    )


class FormingMetricRecord(Contract):
    metric_record_id: str = Field(min_length=1)
    metric_definition_id: str = Field(min_length=1)
    direction_id: str = Field(min_length=1)
    value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    measurement_or_derivation_method_id: str = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid forming metric record requires a basis")
        return self


class FormingThermalInterval(Contract):
    interval_id: str = Field(min_length=1)
    stage: ThermalStage
    procedure_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("forming thermal intervals require positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("forming thermal temperature ranges must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid forming thermal interval requires a basis")
        return self


class FormingEvidenceRecord(Contract):
    evidence_record_id: str = Field(min_length=1)
    evidence_kind: EvidenceKind
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    physical_region_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    result_definition: str = Field(min_length=1)
    reported_value: float | None = None
    unit_token: str = Field(min_length=1)
    result_descriptor: str | None = None
    expanded_uncertainty: Nonnegative | None = None
    uncertainty_coverage_factor: Positive | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def result_is_complete(self):
        if self.reported_value is None and not self.result_descriptor:
            raise ValueError("forming evidence requires a numeric value or descriptor")
        if self.reported_value is not None and (
            self.expanded_uncertainty is None or self.uncertainty_coverage_factor is None
        ):
            raise ValueError("numeric forming evidence requires uncertainty and coverage")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid forming evidence record requires a basis")
        return self


class FormingMetricRequirement(Contract):
    metric_definition_id: str = Field(min_length=1)
    direction_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_value: float | None = None
    maximum_value: float | None = None
    requirement_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounded(self):
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("forming metric support requires at least one bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("forming metric support bounds must be ordered")
        return self


class FormingThermalSupport(Contract):
    stage: ThermalStage
    procedure_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    maximum_single_interval_s: Positive
    maximum_cumulative_duration_s: Positive

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("forming thermal support temperatures must be ordered")
        if self.maximum_cumulative_duration_s < self.maximum_single_interval_s:
            raise ValueError("forming cumulative thermal support cannot be below single interval support")
        return self


class FormingEvidenceRequirement(Contract):
    requirement_id: str = Field(min_length=1)
    evidence_kind: EvidenceKind
    method_id: str = Field(min_length=1)
    result_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_record_count: int = Field(ge=1)
    supported_result_descriptors: tuple[str, ...] = ()
    minimum_value: float | None = None
    maximum_value: float | None = None
    requirement_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_support(self):
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("forming evidence support bounds must be ordered")
        if (
            self.minimum_value is None
            and self.maximum_value is None
            and not self.supported_result_descriptors
        ):
            raise ValueError("forming evidence support requires bounds or descriptors")
        if len(set(self.supported_result_descriptors)) != len(self.supported_result_descriptors):
            raise ValueError("forming evidence descriptors must be unique")
        return self


class FormingQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    forming_mode: FormingMode
    forming_method_id: str = Field(min_length=1)
    minimum_thickness_m: Positive
    maximum_thickness_m: Positive
    supported_direction_ids: tuple[str, ...] = Field(min_length=1)
    metric_requirements: tuple[FormingMetricRequirement, ...] = Field(min_length=1)
    thermal_supports: tuple[FormingThermalSupport, ...] = Field(min_length=1)
    evidence_requirements: tuple[FormingEvidenceRequirement, ...] = Field(min_length=1)
    minimum_physical_specimen_count: int = Field(ge=1)
    minimum_source_group_count: int = Field(ge=1)
    minimum_independence_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_support(self):
        if self.maximum_thickness_m < self.minimum_thickness_m:
            raise ValueError("forming thickness support must be ordered")
        if len(set(self.supported_direction_ids)) != len(self.supported_direction_ids):
            raise ValueError("forming supported directions must be unique")
        metric_keys = [(row.metric_definition_id, row.direction_id) for row in self.metric_requirements]
        thermal_keys = [(row.stage, row.procedure_id) for row in self.thermal_supports]
        requirement_ids = [row.requirement_id for row in self.evidence_requirements]
        for values, name in (
            (metric_keys, "metric"),
            (thermal_keys, "thermal"),
            (requirement_ids, "evidence requirement"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"forming {name} support identifiers must be unique")
        return self


class FormingQualificationAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    product_form_id: str = Field(min_length=1)
    governing_thickness_m: Positive
    governing_direction_id: str = Field(min_length=1)
    forming_mode: FormingMode
    forming_method_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    forming_metrics: tuple[FormingMetricRecord, ...] = Field(min_length=1)
    thermal_history: tuple[FormingThermalInterval, ...] = Field(min_length=1)
    inspection_and_property_evidence: tuple[FormingEvidenceRecord, ...] = Field(min_length=1)
    candidate_envelopes: tuple[FormingQualificationEnvelope, ...] = Field(min_length=1)
    component_material_product_and_thickness_reviewed: bool
    forming_mode_method_and_direction_reviewed: bool
    deformation_metric_definitions_units_and_uncertainty_reviewed: bool
    temperature_time_history_reviewed: bool
    post_forming_heat_treatment_reviewed: bool
    inspection_property_and_partition_evidence_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_ordered_records(self):
        for identifiers, name in (
            ([row.metric_record_id for row in self.forming_metrics], "metric"),
            ([row.interval_id for row in self.thermal_history], "thermal interval"),
            ([row.evidence_record_id for row in self.inspection_and_property_evidence], "evidence"),
            ([row.envelope_id for row in self.candidate_envelopes], "envelope"),
        ):
            if len(set(identifiers)) != len(identifiers):
                raise ValueError(f"forming {name} identifiers must be unique")
        for first, second in zip(self.thermal_history, self.thermal_history[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("forming thermal intervals must be ordered and cannot overlap")
        keys = [(row.metric_definition_id, row.direction_id) for row in self.forming_metrics]
        if len(set(keys)) != len(keys):
            raise ValueError(
                "forming metrics require one record per definition and direction; aggregate replicates explicitly"
            )
        return self


def _identity(value) -> tuple[object, ...]:
    return (
        value.material_id,
        value.material_condition_id,
        value.product_form_id,
        value.forming_mode,
        value.forming_method_id,
    )


def forming_qualification(x: FormingQualificationAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "component_material_product_and_thickness_reviewed",
            "forming_mode_method_and_direction_reviewed",
            "deformation_metric_definitions_units_and_uncertainty_reviewed",
            "temperature_time_history_reviewed",
            "post_forming_heat_treatment_reviewed",
            "inspection_property_and_partition_evidence_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_metric_ids = [row.metric_record_id for row in x.forming_metrics if not row.record_valid]
    invalid_interval_ids = [row.interval_id for row in x.thermal_history if not row.record_valid]
    invalid_evidence_ids = [
        row.evidence_record_id for row in x.inspection_and_property_evidence if not row.record_valid
    ]
    matches = [row for row in x.candidate_envelopes if _identity(row) == _identity(x)]
    if missing_reviews or invalid_metric_ids or invalid_interval_ids or invalid_evidence_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
                "missing_reviews": missing_reviews,
                "invalid_metric_record_ids": invalid_metric_ids,
                "invalid_thermal_interval_ids": invalid_interval_ids,
                "invalid_evidence_record_ids": invalid_evidence_ids,
            },
            notes=("Invalid or unreviewed forming records are not treated as qualification evidence.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No caller-owned envelope has the exact material, product and forming identity.",),
        )

    if len(matches) != 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
            },
            notes=(
                "Select one caller-owned qualification envelope explicitly; matching identity does not resolve competing support definitions.",
            ),
        )
    envelope = matches[0]
    metric_by_key = {(row.metric_definition_id, row.direction_id): row for row in x.forming_metrics}
    missing_metric_keys = []
    metric_unit_mismatch_ids = []
    outside_metric_ids = []
    metric_comparisons = []
    for support in envelope.metric_requirements:
        key = (support.metric_definition_id, support.direction_id)
        row = metric_by_key.get(key)
        if row is None:
            missing_metric_keys.append(":".join(key))
            continue
        unit_matches = row.unit_token == support.unit_token
        if not unit_matches:
            metric_unit_mismatch_ids.append(row.metric_record_id)
            within = None
        else:
            within = not (
                support.minimum_value is not None
                and row.value < support.minimum_value
                or support.maximum_value is not None
                and row.value > support.maximum_value
            )
            if not within:
                outside_metric_ids.append(row.metric_record_id)
        metric_comparisons.append(
            {"metric_record_id": row.metric_record_id, "unit_matches": unit_matches, "within_support": within}
        )

    thermal_support = {(row.stage, row.procedure_id): row for row in envelope.thermal_supports}
    missing_thermal_support_ids = []
    outside_thermal_ids = []
    cumulative_duration: dict[tuple[str, str], float] = {}
    for row in x.thermal_history:
        key = (row.stage, row.procedure_id)
        support = thermal_support.get(key)
        if support is None:
            missing_thermal_support_ids.append(row.interval_id)
            continue
        duration = row.end_time_s - row.start_time_s
        cumulative_duration[key] = cumulative_duration.get(key, 0.0) + duration
        if (
            row.minimum_temperature_K < support.minimum_temperature_K
            or row.maximum_temperature_K > support.maximum_temperature_K
            or duration > support.maximum_single_interval_s
        ):
            outside_thermal_ids.append(row.interval_id)
    cumulative_outside_keys = [
        f"{key[0]}:{key[1]}"
        for key, duration in cumulative_duration.items()
        if duration > thermal_support[key].maximum_cumulative_duration_s
    ]
    required_thermal_keys = set(thermal_support)
    observed_thermal_keys = {(row.stage, row.procedure_id) for row in x.thermal_history}
    missing_required_thermal_keys = [
        f"{key[0]}:{key[1]}" for key in sorted(required_thermal_keys - observed_thermal_keys)
    ]

    records = x.inspection_and_property_evidence
    specimen_ids = sorted({row.physical_specimen_id for row in records})
    source_group_ids = sorted({row.source_group_id for row in records})
    independence_group_ids = sorted({row.independence_group_id for row in records})
    partitions_sufficient = (
        len(specimen_ids) >= envelope.minimum_physical_specimen_count
        and len(source_group_ids) >= envelope.minimum_source_group_count
        and len(independence_group_ids) >= envelope.minimum_independence_group_count
    )
    missing_evidence_requirement_ids = []
    evidence_unit_mismatch_ids = []
    outside_evidence_ids = []
    for requirement in envelope.evidence_requirements:
        candidates = [
            row
            for row in records
            if row.evidence_kind == requirement.evidence_kind
            and row.method_id == requirement.method_id
            and row.result_definition == requirement.result_definition
        ]
        if len(candidates) < requirement.minimum_record_count:
            missing_evidence_requirement_ids.append(requirement.requirement_id)
        for row in candidates:
            if row.unit_token != requirement.unit_token:
                evidence_unit_mismatch_ids.append(row.evidence_record_id)
                continue
            if row.reported_value is not None:
                within = not (
                    requirement.minimum_value is not None
                    and row.reported_value < requirement.minimum_value
                    or requirement.maximum_value is not None
                    and row.reported_value > requirement.maximum_value
                )
            else:
                within = row.result_descriptor in requirement.supported_result_descriptors
            if not within:
                outside_evidence_ids.append(row.evidence_record_id)

    if (
        missing_metric_keys
        or metric_unit_mismatch_ids
        or missing_thermal_support_ids
        or missing_required_thermal_keys
        or missing_evidence_requirement_ids
        or evidence_unit_mismatch_ids
        or not partitions_sufficient
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "qualification_envelope_id": envelope.envelope_id,
                "missing_metric_keys": missing_metric_keys,
                "metric_unit_mismatch_record_ids": metric_unit_mismatch_ids,
                "thermal_intervals_without_support_ids": missing_thermal_support_ids,
                "missing_required_thermal_support_keys": missing_required_thermal_keys,
                "missing_evidence_requirement_ids": missing_evidence_requirement_ids,
                "evidence_unit_mismatch_record_ids": evidence_unit_mismatch_ids,
                "evidence_partition_counts_sufficient": partitions_sufficient,
            },
            notes=("Exact metrics, thermal stages, evidence requirements and partitions must be complete.",),
        )

    outside_identity_reasons = []
    if not envelope.minimum_thickness_m <= x.governing_thickness_m <= envelope.maximum_thickness_m:
        outside_identity_reasons.append("governing_thickness_m")
    if x.governing_direction_id not in envelope.supported_direction_ids:
        outside_identity_reasons.append("governing_direction_id")
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "component_id": x.component_id,
        "qualification_envelope_id": envelope.envelope_id,
        "outside_identity_reasons": outside_identity_reasons,
        "outside_metric_record_ids": outside_metric_ids,
        "outside_thermal_interval_ids": outside_thermal_ids,
        "cumulative_thermal_duration_outside_support_keys": cumulative_outside_keys,
        "outside_evidence_record_ids": outside_evidence_ids,
        "metric_comparisons": metric_comparisons,
        "physical_specimen_ids": specimen_ids,
        "source_group_ids": source_group_ids,
        "independence_group_ids": independence_group_ids,
    }
    notes = (
        "The result compares reviewed production records only with a caller-owned qualification envelope.",
        "No proprietary forming limit, automatic strain reconstruction or property-degradation law is bundled.",
        "No acceptance, remaining life or failure probability is produced.",
    )
    if (
        outside_identity_reasons
        or outside_metric_ids
        or outside_thermal_ids
        or cumulative_outside_keys
        or outside_evidence_ids
    ):
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_qualification_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("forming assessment asset and location must match run context")

    return [
        ModelSpec(
            "fabrication.forming_process_sequence",
            FormingProcessSequence,
            forming_process_sequence,
            {
                "component_id": "1",
                "clock_id": "1",
                "plan_id": "1",
                "plan_digest": "1",
                "outside_support_reasons": "1",
                "inter_operation_cooling": "mixed",
                "cooling_witness_missing_before_operation_ids": "1",
                "final_area_reduction_missing": "1",
                "eligible_caller_waiver_branch_ids": "1",
                "declared_treatment_requirement": "1",
            },
            ("Explicit caller material-specific process plan, ordered operation records and shared clock.",),
            ("caller_forming_process_sequence_and_waiver_conditions",),
            context_validator=same_identity,
        ),
        ModelSpec(
            "fabrication.forming_qualification",
            FormingQualificationAssessment,
            forming_qualification,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "component_id": "1",
                "qualification_envelope_id": "1",
                "outside_identity_reasons": "1",
                "outside_metric_record_ids": "1",
                "outside_thermal_interval_ids": "1",
                "cumulative_thermal_duration_outside_support_keys": "1",
                "outside_evidence_record_ids": "1",
                "metric_comparisons": "mixed",
                "physical_specimen_ids": "1",
                "source_group_ids": "1",
                "independence_group_ids": "1",
                "declared_qualification_outcome": "1",
            },
            (
                "Material, condition, product form, forming mode and method match the envelope exactly.",
                "Metric definitions and units are caller-defined and no strain reconstruction is inferred.",
                "Qualification evidence does not establish code acceptance or long-term property retention.",
            ),
            ("reviewed_forming_qualification_envelope",),
            version="1.0.2",
            context_validator=same_identity,
        ),
    ]
