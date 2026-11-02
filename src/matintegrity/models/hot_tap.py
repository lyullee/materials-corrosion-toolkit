"""Hot-tap applicability against caller-owned provider qualification evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class HotTapProviderResult(Contract):
    result_id: str = Field(min_length=1)
    result_kind: Literal["thermal_or_burn_through_screen", "hydrogen_cracking_screen"]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid hot-tap provider result requires a basis")
        return self


class HotTapProviderMetricSupport(Contract):
    result_kind: Literal["thermal_or_burn_through_screen", "hydrogen_cracking_screen"]
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_supported_value: float
    maximum_supported_value: float
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    support_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_supported_value < self.minimum_supported_value:
            raise ValueError("hot-tap provider metric support bounds must be ordered")
        return self


class HotTapQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["qualification", "holdout", "application"]
    supported_metric_ids: tuple[str, ...] = Field(min_length=1)
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    expanded_uncertainty: Nonnegative
    uncertainty_unit_token: str = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_evidence(self):
        if len(self.supported_metric_ids) != len(set(self.supported_metric_ids)):
            raise ValueError("supported hot-tap metric identifiers must be unique")
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting hot-tap qualification evidence requires a basis")
        return self


class HotTapQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    host_pipe_id: str = Field(min_length=1)
    host_material_condition_id: str = Field(min_length=1)
    pressure_basis: str = Field(min_length=1)
    minimum_operating_pressure_Pa: Nonnegative
    maximum_operating_pressure_Pa: Nonnegative
    minimum_operating_temperature_K: Positive
    maximum_operating_temperature_K: Positive
    minimum_wall_thickness_m: Positive
    maximum_wall_thickness_m: Positive
    supported_flow_heat_extraction_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_branch_geometry_ids: tuple[str, ...] = Field(min_length=1)
    supported_joint_geometry_ids: tuple[str, ...] = Field(min_length=1)
    supported_welding_process_ids: tuple[str, ...] = Field(min_length=1)
    supported_consumable_condition_ids: tuple[str, ...] = Field(min_length=1)
    supported_hydrogen_control_descriptors: tuple[str, ...] = Field(min_length=1)
    provider_metric_support: tuple[HotTapProviderMetricSupport, ...] = Field(min_length=2)
    qualification_evidence: tuple[HotTapQualificationEvidence, ...] = Field(min_length=1)
    minimum_qualification_source_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        for minimum, maximum, label in (
            (self.minimum_operating_pressure_Pa, self.maximum_operating_pressure_Pa, "pressure"),
            (self.minimum_operating_temperature_K, self.maximum_operating_temperature_K, "temperature"),
            (self.minimum_wall_thickness_m, self.maximum_wall_thickness_m, "wall thickness"),
        ):
            if maximum < minimum:
                raise ValueError(f"hot-tap {label} support bounds must be ordered")
        for values, label in (
            (self.supported_flow_heat_extraction_descriptors, "flow descriptors"),
            (self.supported_branch_geometry_ids, "branch geometry identifiers"),
            (self.supported_joint_geometry_ids, "joint geometry identifiers"),
            (self.supported_welding_process_ids, "welding process identifiers"),
            (self.supported_consumable_condition_ids, "consumable identifiers"),
            (self.supported_hydrogen_control_descriptors, "hydrogen-control descriptors"),
            ([row.metric_id for row in self.provider_metric_support], "provider metric identifiers"),
            ([row.evidence_record_id for row in self.qualification_evidence], "evidence identifiers"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"hot-tap {label} must be unique")
        supported_kinds = {row.result_kind for row in self.provider_metric_support}
        required_kinds = {"thermal_or_burn_through_screen", "hydrogen_cracking_screen"}
        if supported_kinds != required_kinds:
            raise ValueError("hot-tap support requires thermal/burn-through and hydrogen-cracking metrics")
        return self


class HotTapApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    host_pipe_id: str = Field(min_length=1)
    host_material_condition_id: str = Field(min_length=1)
    pressure_basis: str = Field(min_length=1)
    operating_pressure_Pa: Nonnegative
    operating_temperature_K: Positive
    wall_thickness_m: Positive
    flow_heat_extraction_descriptor: str = Field(min_length=1)
    branch_geometry_id: str = Field(min_length=1)
    joint_geometry_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    consumable_condition_id: str = Field(min_length=1)
    hydrogen_control_descriptor: str = Field(min_length=1)
    provider_results: tuple[HotTapProviderResult, ...] = Field(min_length=2)
    candidate_envelopes: tuple[HotTapQualificationEnvelope, ...] = Field(min_length=1)
    host_pipe_material_and_condition_reviewed: bool
    operating_pressure_basis_and_temperature_reviewed: bool
    wall_thickness_and_geometry_reviewed: bool
    flow_and_heat_extraction_reviewed: bool
    welding_process_consumable_and_hydrogen_control_reviewed: bool
    provider_results_units_and_support_reviewed: bool
    qualification_specimens_and_source_groups_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_results_and_envelopes(self):
        result_ids = [row.result_id for row in self.provider_results]
        metric_ids = [row.metric_id for row in self.provider_results]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(result_ids) != len(set(result_ids)):
            raise ValueError("hot-tap provider result identifiers must be unique")
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError("hot-tap provider metric identifiers must be unique")
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("hot-tap envelope identifiers must be unique")
        kinds = {row.result_kind for row in self.provider_results}
        required = {"thermal_or_burn_through_screen", "hydrogen_cracking_screen"}
        if kinds != required:
            raise ValueError("hot-tap assessment requires both provider result kinds")
        return self


def _identity(x: HotTapApplicability) -> tuple[str, ...]:
    return x.host_pipe_id, x.host_material_condition_id, x.pressure_basis


def _envelope_identity(x: HotTapQualificationEnvelope) -> tuple[str, ...]:
    return x.host_pipe_id, x.host_material_condition_id, x.pressure_basis


def hot_tap_applicability(x: HotTapApplicability) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "host_pipe_material_and_condition_reviewed",
            "operating_pressure_basis_and_temperature_reviewed",
            "wall_thickness_and_geometry_reviewed",
            "flow_and_heat_extraction_reviewed",
            "welding_process_consumable_and_hydrogen_control_reviewed",
            "provider_results_units_and_support_reviewed",
            "qualification_specimens_and_source_groups_reviewed",
            "provider_lineage_and_digests_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_result_ids = [row.result_id for row in x.provider_results if not row.record_valid]
    matches = [row for row in x.candidate_envelopes if _envelope_identity(row) == _identity(x)]
    if missing_reviews or invalid_result_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_provider_result_ids": invalid_result_ids,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
            },
            notes=("Reviewed host, operating and provider-result records are required.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": [],
                "invalid_provider_result_ids": [],
                "identity_matching_envelope_ids": [],
            },
            notes=("No caller envelope has the exact host-pipe, material and pressure-basis identity.",),
        )

    envelope = matches[0]
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    support = {row.metric_id: row for row in envelope.provider_metric_support}
    results = {row.metric_id: row for row in x.provider_results}
    missing_metric_ids = sorted(set(support) - set(results))
    extra_metric_ids = sorted(set(results) - set(support))
    unit_or_provider_mismatch_ids = []
    metric_comparisons = []
    outside_metric_ids = []
    for metric_id in sorted(set(support) & set(results)):
        row = results[metric_id]
        limit = support[metric_id]
        matches_support = (
            row.result_kind == limit.result_kind
            and row.unit_token == limit.unit_token
            and row.provider_id == limit.provider_id
            and row.provider_revision == limit.provider_revision
            and row.provider_state_digest == limit.provider_state_digest
        )
        within = None
        if not matches_support:
            unit_or_provider_mismatch_ids.append(metric_id)
        else:
            within = limit.minimum_supported_value <= row.reported_value <= limit.maximum_supported_value
            if not within:
                outside_metric_ids.append(metric_id)
        metric_comparisons.append(
            {
                "metric_id": metric_id,
                "result_kind": row.result_kind,
                "reported_value": row.reported_value,
                "unit_token": row.unit_token,
                "within_declared_support": within,
            }
        )
    if invalid_evidence_ids or missing_metric_ids or extra_metric_ids or unit_or_provider_mismatch_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "envelope_id": envelope.envelope_id,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "missing_metric_ids": missing_metric_ids,
                "extra_metric_ids": extra_metric_ids,
                "unit_or_provider_mismatch_ids": unit_or_provider_mismatch_ids,
                "metric_comparisons": metric_comparisons,
            },
            notes=("Exact provider identities, state digests, metric identities and units are required.",),
        )

    qualification_rows = [row for row in envelope.qualification_evidence if row.partition == "qualification"]
    source_group_count = len({row.source_group_id for row in qualification_rows})
    evidence_supported_metrics = {
        metric_id for row in qualification_rows for metric_id in row.supported_metric_ids
    }
    unsupported_evidence_metric_ids = sorted(set(support) - evidence_supported_metrics)
    outside_support_reasons = []
    if (
        not envelope.minimum_operating_pressure_Pa
        <= x.operating_pressure_Pa
        <= envelope.maximum_operating_pressure_Pa
    ):
        outside_support_reasons.append("operating_pressure")
    if (
        not envelope.minimum_operating_temperature_K
        <= x.operating_temperature_K
        <= envelope.maximum_operating_temperature_K
    ):
        outside_support_reasons.append("operating_temperature")
    if not envelope.minimum_wall_thickness_m <= x.wall_thickness_m <= envelope.maximum_wall_thickness_m:
        outside_support_reasons.append("wall_thickness")
    for value, supported, label in (
        (
            x.flow_heat_extraction_descriptor,
            envelope.supported_flow_heat_extraction_descriptors,
            "flow_heat_extraction_descriptor",
        ),
        (x.branch_geometry_id, envelope.supported_branch_geometry_ids, "branch_geometry_id"),
        (x.joint_geometry_id, envelope.supported_joint_geometry_ids, "joint_geometry_id"),
        (x.welding_process_id, envelope.supported_welding_process_ids, "welding_process_id"),
        (x.consumable_condition_id, envelope.supported_consumable_condition_ids, "consumable_condition_id"),
        (
            x.hydrogen_control_descriptor,
            envelope.supported_hydrogen_control_descriptors,
            "hydrogen_control_descriptor",
        ),
    ):
        if value not in supported:
            outside_support_reasons.append(label)
    if source_group_count < envelope.minimum_qualification_source_group_count:
        outside_support_reasons.append("qualification_source_group_count")
    if unsupported_evidence_metric_ids:
        outside_support_reasons.append("qualification_metric_coverage")
    if outside_metric_ids:
        outside_support_reasons.append("provider_metric_range")

    return Calculation(
        status="out_of_scope" if outside_support_reasons else "computed",
        values={
            "assessment_id": x.assessment_id,
            "physical_scope_id": x.physical_scope_id,
            "envelope_id": envelope.envelope_id,
            "metric_comparisons": metric_comparisons,
            "outside_metric_ids": outside_metric_ids,
            "qualification_source_group_count": source_group_count,
            "unsupported_evidence_metric_ids": unsupported_evidence_metric_ids,
            "outside_support_reasons": outside_support_reasons,
            "declared_applicability_outcome": (
                "outside_support" if outside_support_reasons else "within_support"
            ),
        },
        notes=(
            "The result compares caller-supplied provider results with a caller-owned qualification envelope.",
            "No proprietary chart, acceptance, burn-through or cracking probability, capacity or life is calculated.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("hot-tap assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.hot_tap_applicability",
            HotTapApplicability,
            hot_tap_applicability,
            {
                "assessment_id": "1",
                "physical_scope_id": "1",
                "envelope_id": "1",
                "metric_comparisons": "mixed",
                "outside_metric_ids": "1",
                "qualification_source_group_count": "1",
                "unsupported_evidence_metric_ids": "1",
                "outside_support_reasons": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Host pipe, material condition and operating pressure basis are exact caller-reviewed identities.",
                "Thermal/burn-through and hydrogen-cracking values are external provider results, not internal calculations.",
                "Qualification evidence preserves physical specimens, source groups, uncertainty and provider digests.",
            ),
            ("reviewed_hot_tap_provider_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
