"""Residual-stress evidence mapped to caller-owned provider support envelopes."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ResidualStressProviderQualification(Contract):
    qualification_id: str = Field(min_length=1)
    calibration_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_observation_count: int = Field(ge=1)
    holdout_observation_count: int = Field(ge=1)
    holdout_metric_definition: str = Field(min_length=1)
    holdout_metric_value: Nonnegative
    holdout_metric_unit: str = Field(min_length=1)
    maximum_supported_holdout_metric: Positive
    maximum_supported_holdout_metric_unit: str = Field(min_length=1)
    calibration_and_holdout_independent: bool
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def matching_holdout_metric_units(self):
        if self.holdout_metric_unit != self.maximum_supported_holdout_metric_unit:
            raise ValueError("holdout metric value and maximum must use the same unit")
        return self


class DeclaredResidualStressSupport(Contract):
    support_id: str = Field(min_length=1)
    method_kind: Literal["measured", "modelled"]
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    component_definition: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_frame_definition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    coordinate_names: tuple[str, ...] = Field(min_length=1)
    minimum_coordinates_m: tuple[float, ...] = Field(min_length=1)
    maximum_coordinates_m: tuple[float, ...] = Field(min_length=1)
    minimum_supported_stress_Pa: float
    maximum_supported_stress_Pa: float
    maximum_supported_expanded_uncertainty_Pa: Nonnegative
    applicability_basis: str = Field(min_length=1)
    qualification: ResidualStressProviderQualification
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        dimension = len(self.coordinate_names)
        if len(set(self.coordinate_names)) != dimension:
            raise ValueError("residual-stress coordinate names must be unique")
        if len(self.minimum_coordinates_m) != dimension or len(self.maximum_coordinates_m) != dimension:
            raise ValueError("residual-stress coordinate bounds must match the declared dimension")
        if any(
            high < low
            for low, high in zip(self.minimum_coordinates_m, self.maximum_coordinates_m, strict=True)
        ):
            raise ValueError("residual-stress coordinate bounds must be ordered")
        if self.maximum_supported_stress_Pa < self.minimum_supported_stress_Pa:
            raise ValueError("residual-stress support bounds must be ordered")
        return self


class ResidualStressEvidenceRecord(Contract):
    record_id: str = Field(min_length=1)
    method_kind: Literal["measured", "modelled"]
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    partition: Literal["calibration", "holdout", "application"]
    source_group_id: str = Field(min_length=1)
    component_definition: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_frame_definition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    coordinate_names: tuple[str, ...] = Field(min_length=1)
    coordinates_m: tuple[float, ...] = Field(min_length=1)
    stress_Pa: float
    expanded_uncertainty_Pa: Nonnegative
    coverage_factor: Positive
    uncertainty_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_coordinate_axes(self):
        if len(self.coordinate_names) != len(self.coordinates_m):
            raise ValueError("residual-stress coordinate names and values must have equal dimensions")
        if len(self.coordinate_names) != len(set(self.coordinate_names)):
            raise ValueError("residual-stress record coordinate names must be unique")
        return self


class ResidualStressEvidenceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    weld_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    records: tuple[ResidualStressEvidenceRecord, ...] = Field(min_length=1)
    candidate_supports: tuple[DeclaredResidualStressSupport, ...] = Field(min_length=1)
    weld_and_material_identity_reviewed: bool
    coordinate_frames_and_components_reviewed: bool
    units_and_uncertainty_reviewed: bool
    provider_identity_and_state_reviewed: bool
    record_digests_reviewed: bool
    calibration_and_holdout_reviewed: bool
    support_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_and_partitioned_records(self):
        for values, name in (
            ([row.record_id for row in self.records], "residual-stress record"),
            ([row.support_id for row in self.candidate_supports], "residual-stress support"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} identifiers must be unique")
        partition_groups: dict[str, set[str]] = {}
        for row in self.records:
            partition_groups.setdefault(row.partition, set()).add(row.source_group_id)
        partitions = ("calibration", "holdout", "application")
        for index, left in enumerate(partitions):
            for right in partitions[index + 1 :]:
                if partition_groups.get(left, set()) & partition_groups.get(right, set()):
                    raise ValueError("source groups must be disjoint across data partitions")
        return self


def _support_identity(row):
    return (
        row.method_kind,
        row.provider_id,
        row.provider_version,
        row.provider_state_digest,
        row.component_definition,
        row.coordinate_frame_id,
    )


def _provider_identity(row):
    return (
        row.method_kind,
        row.provider_id,
        row.provider_version,
        row.provider_state_digest,
    )


def residual_stress_evidence(x: ResidualStressEvidenceAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "weld_and_material_identity_reviewed",
            "coordinate_frames_and_components_reviewed",
            "units_and_uncertainty_reviewed",
            "provider_identity_and_state_reviewed",
            "record_digests_reviewed",
            "calibration_and_holdout_reviewed",
            "support_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    support_by_identity = {_support_identity(row): [] for row in x.candidate_supports}
    support_by_provider = {}
    for support in x.candidate_supports:
        support_by_identity[_support_identity(support)].append(support)
        support_by_provider.setdefault(_provider_identity(support), []).append(support)

    comparison_rows = []
    unmatched_record_ids = []
    record_match_issue_reasons = {}
    ambiguous_record_ids = []
    invalid_qualification_support_ids = []
    for support in x.candidate_supports:
        qualification = support.qualification
        if (
            not qualification.calibration_and_holdout_independent
            or qualification.holdout_metric_value > qualification.maximum_supported_holdout_metric
        ):
            invalid_qualification_support_ids.append(support.support_id)

    for record in x.records:
        candidates = support_by_identity.get(_support_identity(record), [])
        if not candidates:
            unmatched_record_ids.append(record.record_id)
            provider_candidates = support_by_provider.get(_provider_identity(record), [])
            same_frame_candidates = [
                support
                for support in provider_candidates
                if support.coordinate_frame_id == record.coordinate_frame_id
            ]
            if same_frame_candidates and all(
                support.component_definition != record.component_definition
                for support in same_frame_candidates
            ):
                record_match_issue_reasons[record.record_id] = "component_definition_mismatch"
            elif provider_candidates and not same_frame_candidates:
                record_match_issue_reasons[record.record_id] = "coordinate_frame_id_mismatch"
            else:
                record_match_issue_reasons[record.record_id] = "no_exact_provider_support_match"
            continue
        if len(candidates) != 1:
            ambiguous_record_ids.append(record.record_id)
            record_match_issue_reasons[record.record_id] = "ambiguous_provider_support_match"
            continue
        support = candidates[0]
        if len(record.coordinates_m) != len(support.coordinate_names):
            coordinate_dimension_matches = False
            coordinates_within_support = False
            coordinate_values_within_bounds = False
        else:
            coordinate_dimension_matches = True
            coordinate_values_within_bounds = all(
                low <= value <= high
                for value, low, high in zip(
                    record.coordinates_m,
                    support.minimum_coordinates_m,
                    support.maximum_coordinates_m,
                    strict=True,
                )
            )
        coordinate_axes_match = record.coordinate_names == support.coordinate_names
        coordinate_frame_definition_matches = (
            record.coordinate_frame_definition_sha256 == support.coordinate_frame_definition_sha256
        )
        coordinates_within_support = (
            coordinate_axes_match and coordinate_frame_definition_matches and coordinate_values_within_bounds
        )
        stress_within_support = (
            support.minimum_supported_stress_Pa <= record.stress_Pa <= support.maximum_supported_stress_Pa
        )
        uncertainty_interval_minimum = record.stress_Pa - record.expanded_uncertainty_Pa
        uncertainty_interval_maximum = record.stress_Pa + record.expanded_uncertainty_Pa
        uncertainty_interval_within_stress_support = (
            support.minimum_supported_stress_Pa <= uncertainty_interval_minimum
            and uncertainty_interval_maximum <= support.maximum_supported_stress_Pa
        )
        uncertainty_within_support = (
            record.expanded_uncertainty_Pa <= support.maximum_supported_expanded_uncertainty_Pa
        )
        qualification_supported = support.support_id not in invalid_qualification_support_ids
        support_exclusion_reasons = []
        if not coordinate_dimension_matches:
            support_exclusion_reasons.append("coordinate_dimension_mismatch")
        if not coordinate_frame_definition_matches:
            support_exclusion_reasons.append("coordinate_frame_definition_mismatch")
        if not coordinate_axes_match:
            if set(record.coordinate_names) == set(support.coordinate_names):
                support_exclusion_reasons.append("coordinate_axis_order_mismatch")
            else:
                support_exclusion_reasons.append("coordinate_axis_definition_mismatch")
        if (
            coordinate_dimension_matches
            and coordinate_axes_match
            and coordinate_frame_definition_matches
            and not coordinate_values_within_bounds
        ):
            support_exclusion_reasons.append("coordinates_outside_declared_support")
        if not stress_within_support:
            support_exclusion_reasons.append("stress_outside_declared_support")
        if not uncertainty_interval_within_stress_support:
            support_exclusion_reasons.append("uncertainty_interval_outside_stress_support")
        if not uncertainty_within_support:
            support_exclusion_reasons.append("expanded_uncertainty_outside_declared_support")
        if not qualification_supported:
            support_exclusion_reasons.append("provider_qualification_not_supported")
        comparison_rows.append(
            {
                "record_id": record.record_id,
                "partition": record.partition,
                "source_group_id": record.source_group_id,
                "method_kind": record.method_kind,
                "provider_id": record.provider_id,
                "provider_version": record.provider_version,
                "provider_state_digest": record.provider_state_digest,
                "record_digest": record.record_digest,
                "record_evidence": [item.model_dump(mode="json") for item in record.evidence],
                "support_id": support.support_id,
                "support_evidence": [item.model_dump(mode="json") for item in support.evidence],
                "qualification_id": support.qualification.qualification_id,
                "calibration_dataset_digest": support.qualification.calibration_dataset_digest,
                "holdout_dataset_digest": support.qualification.holdout_dataset_digest,
                "component_definition": record.component_definition,
                "coordinate_frame_id": record.coordinate_frame_id,
                "record_coordinate_frame_definition_sha256": record.coordinate_frame_definition_sha256,
                "support_coordinate_frame_definition_sha256": support.coordinate_frame_definition_sha256,
                "record_coordinate_names": list(record.coordinate_names),
                "support_coordinate_names": list(support.coordinate_names),
                "coordinates_m": list(record.coordinates_m),
                "coordinate_dimension_matches": coordinate_dimension_matches,
                "coordinate_frame_definition_matches": coordinate_frame_definition_matches,
                "coordinate_axes_match_in_order": coordinate_axes_match,
                "coordinates_within_declared_support": coordinates_within_support,
                "stress_Pa": record.stress_Pa,
                "expanded_uncertainty_Pa": record.expanded_uncertainty_Pa,
                "uncertainty_interval_minimum_Pa": uncertainty_interval_minimum,
                "uncertainty_interval_maximum_Pa": uncertainty_interval_maximum,
                "uncertainty_interval_within_declared_stress_support": (
                    uncertainty_interval_within_stress_support
                ),
                "stress_within_declared_provider_support": stress_within_support,
                "uncertainty_within_declared_provider_support": uncertainty_within_support,
                "provider_qualification_supported": qualification_supported,
                "support_exclusion_reasons": support_exclusion_reasons,
                "record_within_declared_support": (
                    coordinate_dimension_matches
                    and coordinates_within_support
                    and stress_within_support
                    and uncertainty_interval_within_stress_support
                    and uncertainty_within_support
                    and qualification_supported
                ),
            }
        )

    incomplete = (
        missing_reviews or unmatched_record_ids or ambiguous_record_ids or invalid_qualification_support_ids
    )
    application_rows = [row for row in comparison_rows if row["partition"] == "application"]
    application_records = [row for row in x.records if row.partition == "application"]
    unmatched_application_record_ids = [
        record_id
        for record_id in unmatched_record_ids
        if record_id in {row.record_id for row in application_records}
    ]
    ambiguous_application_record_ids = [
        record_id
        for record_id in ambiguous_record_ids
        if record_id in {row.record_id for row in application_records}
    ]
    unsupported_record_ids = [
        row["record_id"] for row in comparison_rows if not row["record_within_declared_support"]
    ]
    unsupported_application_id_set = (
        {row["record_id"] for row in application_rows if not row["record_within_declared_support"]}
        | set(unmatched_application_record_ids)
        | set(ambiguous_application_record_ids)
    )
    unsupported_application_record_ids = [
        row.record_id for row in application_records if row.record_id in unsupported_application_id_set
    ]
    partition_record_ids = {
        partition: [row.record_id for row in x.records if row.partition == partition]
        for partition in ("calibration", "holdout", "application")
    }
    record_source_lineage = [
        {
            "record_id": row.record_id,
            "partition": row.partition,
            "source_group_id": row.source_group_id,
            "method_kind": row.method_kind,
            "provider_id": row.provider_id,
            "provider_version": row.provider_version,
            "provider_state_digest": row.provider_state_digest,
            "record_digest": row.record_digest,
            "component_definition": row.component_definition,
            "coordinate_frame_id": row.coordinate_frame_id,
            "coordinate_frame_definition_sha256": row.coordinate_frame_definition_sha256,
            "coordinate_names": list(row.coordinate_names),
            "coordinates_m": list(row.coordinates_m),
            "evidence": [item.model_dump(mode="json") for item in row.evidence],
        }
        for row in x.records
    ]
    provider_support_lineage = [
        {
            "support_id": row.support_id,
            "method_kind": row.method_kind,
            "provider_id": row.provider_id,
            "provider_version": row.provider_version,
            "provider_state_digest": row.provider_state_digest,
            "component_definition": row.component_definition,
            "coordinate_frame_id": row.coordinate_frame_id,
            "coordinate_frame_definition_sha256": row.coordinate_frame_definition_sha256,
            "coordinate_names": list(row.coordinate_names),
            "minimum_coordinates_m": list(row.minimum_coordinates_m),
            "maximum_coordinates_m": list(row.maximum_coordinates_m),
            "minimum_supported_stress_Pa": row.minimum_supported_stress_Pa,
            "maximum_supported_stress_Pa": row.maximum_supported_stress_Pa,
            "maximum_supported_expanded_uncertainty_Pa": row.maximum_supported_expanded_uncertainty_Pa,
            "qualification": row.qualification.model_dump(mode="json"),
            "evidence": [item.model_dump(mode="json") for item in row.evidence],
        }
        for row in x.candidate_supports
    ]
    return Calculation(
        status="needs_data" if incomplete else "computed",
        values={
            "assessment_id": x.assessment_id,
            "weld_id": x.weld_id,
            "material_condition_id": x.material_condition_id,
            "record_count": len(x.records),
            "partition_counts": {
                partition: sum(row.partition == partition for row in x.records)
                for partition in ("calibration", "holdout", "application")
            },
            "partition_record_ids": partition_record_ids,
            "record_source_lineage": record_source_lineage,
            "provider_support_lineage": provider_support_lineage,
            "record_comparisons": comparison_rows,
            "unsupported_record_ids": unsupported_record_ids,
            "application_record_count": len(application_records),
            "application_compared_record_count": len(application_rows),
            "application_records_within_declared_support_count": sum(
                bool(row["record_within_declared_support"]) for row in application_rows
            ),
            "all_application_records_within_declared_support": bool(application_records)
            and len(application_rows) == len(application_records)
            and all(bool(row["record_within_declared_support"]) for row in application_rows),
            "unsupported_application_record_ids": unsupported_application_record_ids,
            "unmatched_application_record_ids": unmatched_application_record_ids,
            "ambiguous_application_record_ids": ambiguous_application_record_ids,
            "unmatched_record_ids": unmatched_record_ids,
            "record_match_issue_reasons": record_match_issue_reasons,
            "ambiguous_record_ids": ambiguous_record_ids,
            "invalid_qualification_support_ids": sorted(set(invalid_qualification_support_ids)),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Stress components, coordinate frames, provider support and validation limits are caller-owned and must retain their evidence lineage.",
            "Comparison rows preserve source-group, record/provider digests and record/support evidence for downstream traceability.",
            "Uncertainty bounds and support comparisons do not establish weld acceptance, fracture resistance, damage rate, remaining life or failure probability.",
            "No residual-stress redistribution, crack-driving-force calculation or standards acceptance table is embedded.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("residual-stress assessment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.residual_stress_evidence",
            ResidualStressEvidenceAssessment,
            residual_stress_evidence,
            {
                "assessment_id": "1",
                "weld_id": "1",
                "material_condition_id": "1",
                "record_count": "1",
                "partition_counts": "1",
                "partition_record_ids": "mixed",
                "record_source_lineage": "mixed",
                "provider_support_lineage": "mixed",
                "record_comparisons": "mixed",
                "application_record_count": "1",
                "application_compared_record_count": "1",
                "application_records_within_declared_support_count": "1",
                "all_application_records_within_declared_support": "1",
                "unsupported_application_record_ids": "1",
                "unmatched_application_record_ids": "1",
                "ambiguous_application_record_ids": "1",
                "record_match_issue_reasons": "mixed",
                "unmatched_record_ids": "1",
                "ambiguous_record_ids": "1",
                "invalid_qualification_support_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Each residual-stress value retains its declared tensor-component meaning and coordinate frame.",
                "The full declared expanded-uncertainty interval must remain inside provider stress support.",
                "Calibration, holdout and application source groups must be mutually disjoint.",
                "Provider identity, version, state digest and caller-owned support are exact-match evidence contracts.",
                "Calibration and holdout source groups are independent when the provider qualification declares them independent.",
            ),
            ("reviewed_residual_stress_evidence_record",),
            context_validator=same_identity,
        )
    ]
