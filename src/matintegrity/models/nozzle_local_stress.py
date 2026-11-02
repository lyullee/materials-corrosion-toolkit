"""Nozzle local-stress provider evidence against caller-owned support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative
from ..registry import ModelSpec


class NozzleGeometryQuantity(Contract):
    quantity_id: str = Field(min_length=1)
    value: float
    unit_token: str = Field(min_length=1)
    basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class NozzleLoadComponent(Contract):
    component_id: str = Field(min_length=1)
    component_kind: Literal["force", "moment", "pressure", "temperature", "user_defined"]
    value: float
    unit_token: str = Field(min_length=1)
    sign_and_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class NozzleProviderStressResult(Contract):
    result_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    mesh_id: str = Field(min_length=1)
    result_location_id: str = Field(min_length=1)
    spatial_averaging_basis: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    representation_kind: Literal[
        "stress_tensor_component",
        "linearized_membrane",
        "linearized_bending",
        "user_defined_metric",
    ]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    reported_value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_result(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid nozzle stress result requires a basis")
        return self


class NozzleQuantitySupport(Contract):
    quantity_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_supported_value: float
    maximum_supported_value: float

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_supported_value < self.minimum_supported_value:
            raise ValueError("nozzle quantity support bounds must be ordered")
        return self


class NozzleResultSupport(Contract):
    representation_kind: Literal[
        "stress_tensor_component",
        "linearized_membrane",
        "linearized_bending",
        "user_defined_metric",
    ]
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_supported_value: float
    maximum_supported_value: float
    maximum_supported_expanded_uncertainty: Nonnegative
    supported_result_location_ids: tuple[str, ...] = Field(min_length=1)
    supported_spatial_averaging_bases: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_supported_value < self.minimum_supported_value:
            raise ValueError("nozzle result support bounds must be ordered")
        if len(self.supported_result_location_ids) != len(set(self.supported_result_location_ids)):
            raise ValueError("supported nozzle result locations must be unique")
        if len(self.supported_spatial_averaging_bases) != len(set(self.supported_spatial_averaging_bases)):
            raise ValueError("supported nozzle averaging bases must be unique")
        return self


class NozzleQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    supported_metric_ids: tuple[str, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_evidence(self):
        if len(self.supported_metric_ids) != len(set(self.supported_metric_ids)):
            raise ValueError("nozzle qualification metric identifiers must be unique")
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting nozzle qualification evidence requires a basis")
        return self


class NozzleLocalStressEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    vessel_geometry_id: str = Field(min_length=1)
    nozzle_geometry_id: str = Field(min_length=1)
    opening_geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    supported_mesh_ids: tuple[str, ...] = Field(min_length=1)
    geometry_support: tuple[NozzleQuantitySupport, ...] = Field(min_length=1)
    load_support: tuple[NozzleQuantitySupport, ...] = Field(min_length=1)
    result_support: tuple[NozzleResultSupport, ...] = Field(min_length=1)
    qualification_evidence: tuple[NozzleQualificationEvidence, ...] = Field(min_length=2)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_independent_support(self):
        for values, label in (
            (self.supported_mesh_ids, "mesh identifiers"),
            ([row.quantity_id for row in self.geometry_support], "geometry quantities"),
            ([row.quantity_id for row in self.load_support], "load quantities"),
            ([row.metric_id for row in self.result_support], "result metrics"),
            ([row.evidence_record_id for row in self.qualification_evidence], "evidence identifiers"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"nozzle {label} must be unique")
        partitions = {row.partition for row in self.qualification_evidence}
        if partitions != {"calibration", "holdout"}:
            raise ValueError("nozzle qualification requires calibration and holdout evidence")
        calibration_groups = {
            row.source_group_id for row in self.qualification_evidence if row.partition == "calibration"
        }
        holdout_groups = {
            row.source_group_id for row in self.qualification_evidence if row.partition == "holdout"
        }
        if calibration_groups & holdout_groups:
            raise ValueError("nozzle calibration and holdout source groups must be disjoint")
        return self


class NozzleLocalStressProviderEvidence(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    vessel_geometry_id: str = Field(min_length=1)
    nozzle_geometry_id: str = Field(min_length=1)
    opening_geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    geometry_quantities: tuple[NozzleGeometryQuantity, ...] = Field(min_length=1)
    load_components: tuple[NozzleLoadComponent, ...] = Field(min_length=1)
    provider_results: tuple[NozzleProviderStressResult, ...] = Field(min_length=1)
    candidate_envelopes: tuple[NozzleLocalStressEnvelope, ...] = Field(min_length=1)
    vessel_nozzle_opening_geometry_and_units_reviewed: bool
    material_condition_reviewed: bool
    coordinate_frame_and_load_basis_reviewed: bool
    mesh_location_and_averaging_reviewed: bool
    stress_representation_metrics_units_and_uncertainty_reviewed: bool
    provider_revision_configuration_and_digests_reviewed: bool
    calibration_holdout_and_source_groups_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_linked_records(self):
        for values, label in (
            ([row.quantity_id for row in self.geometry_quantities], "geometry quantities"),
            ([row.component_id for row in self.load_components], "load components"),
            ([row.result_id for row in self.provider_results], "result identifiers"),
            ([row.metric_id for row in self.provider_results], "result metric identifiers"),
            ([row.envelope_id for row in self.candidate_envelopes], "envelope identifiers"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"nozzle {label} must be unique")
        if any(row.load_case_id != self.load_case_id for row in self.provider_results):
            raise ValueError("nozzle provider results must reference the assessed load case")
        return self


def _identity(x: NozzleLocalStressProviderEvidence) -> tuple[str, ...]:
    return (
        x.vessel_geometry_id,
        x.nozzle_geometry_id,
        x.opening_geometry_id,
        x.material_condition_id,
        x.coordinate_frame_id,
    )


def _envelope_identity(x: NozzleLocalStressEnvelope) -> tuple[str, ...]:
    return (
        x.vessel_geometry_id,
        x.nozzle_geometry_id,
        x.opening_geometry_id,
        x.material_condition_id,
        x.coordinate_frame_id,
    )


def nozzle_local_stress_provider_evidence(x: NozzleLocalStressProviderEvidence) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "vessel_nozzle_opening_geometry_and_units_reviewed",
            "material_condition_reviewed",
            "coordinate_frame_and_load_basis_reviewed",
            "mesh_location_and_averaging_reviewed",
            "stress_representation_metrics_units_and_uncertainty_reviewed",
            "provider_revision_configuration_and_digests_reviewed",
            "calibration_holdout_and_source_groups_reviewed",
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
                "invalid_result_ids": invalid_result_ids,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
            },
            notes=("Reviewed geometry, load and provider-result records are required.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No caller envelope has the exact geometry, material and coordinate-frame identity.",),
        )

    envelope = matches[0]
    invalid_evidence_ids = [
        row.evidence_record_id
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    provider_mismatch_ids = [
        row.result_id
        for row in x.provider_results
        if row.provider_id != envelope.provider_id
        or row.provider_revision != envelope.provider_revision
        or row.provider_configuration_digest != envelope.provider_configuration_digest
    ]

    def compare_quantities(records, supports, id_attr):
        by_id = {getattr(row, id_attr): row for row in records}
        support_by_id = {row.quantity_id: row for row in supports}
        missing = sorted(set(support_by_id) - set(by_id))
        extra = sorted(set(by_id) - set(support_by_id))
        unit_mismatch = []
        outside = []
        for identifier in sorted(set(by_id) & set(support_by_id)):
            record, support = by_id[identifier], support_by_id[identifier]
            if record.unit_token != support.unit_token:
                unit_mismatch.append(identifier)
            elif not support.minimum_supported_value <= record.value <= support.maximum_supported_value:
                outside.append(identifier)
        return missing, extra, unit_mismatch, outside

    geometry_missing, geometry_extra, geometry_unit_mismatch, geometry_outside = compare_quantities(
        x.geometry_quantities, envelope.geometry_support, "quantity_id"
    )
    load_missing, load_extra, load_unit_mismatch, load_outside = compare_quantities(
        x.load_components, envelope.load_support, "component_id"
    )
    result_support = {row.metric_id: row for row in envelope.result_support}
    results = {row.metric_id: row for row in x.provider_results}
    result_missing = sorted(set(result_support) - set(results))
    result_extra = sorted(set(results) - set(result_support))
    unsupported_result_ids = []
    outside_result_ids = []
    result_comparisons = []
    for metric_id in sorted(set(result_support) & set(results)):
        row, support = results[metric_id], result_support[metric_id]
        compatible = (
            row.representation_kind == support.representation_kind
            and row.unit_token == support.unit_token
            and row.mesh_id in envelope.supported_mesh_ids
            and row.result_location_id in support.supported_result_location_ids
            and row.spatial_averaging_basis in support.supported_spatial_averaging_bases
        )
        within = None
        if not compatible:
            unsupported_result_ids.append(row.result_id)
        else:
            within = (
                support.minimum_supported_value <= row.reported_value <= support.maximum_supported_value
                and row.expanded_uncertainty <= support.maximum_supported_expanded_uncertainty
            )
            if not within:
                outside_result_ids.append(row.result_id)
        result_comparisons.append(
            {
                "result_id": row.result_id,
                "metric_id": metric_id,
                "representation_kind": row.representation_kind,
                "reported_value": row.reported_value,
                "unit_token": row.unit_token,
                "within_declared_support": within,
            }
        )
    needs_data = any(
        (
            invalid_evidence_ids,
            provider_mismatch_ids,
            geometry_missing,
            geometry_extra,
            geometry_unit_mismatch,
            load_missing,
            load_extra,
            load_unit_mismatch,
            result_missing,
            result_extra,
            unsupported_result_ids,
        )
    )
    if needs_data:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "envelope_id": envelope.envelope_id,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "provider_mismatch_result_ids": provider_mismatch_ids,
                "geometry_missing_ids": geometry_missing,
                "geometry_extra_ids": geometry_extra,
                "geometry_unit_mismatch_ids": geometry_unit_mismatch,
                "load_missing_ids": load_missing,
                "load_extra_ids": load_extra,
                "load_unit_mismatch_ids": load_unit_mismatch,
                "result_missing_metric_ids": result_missing,
                "result_extra_metric_ids": result_extra,
                "unsupported_result_ids": unsupported_result_ids,
                "result_comparisons": result_comparisons,
            },
            notes=("Exact provider, geometry, load, mesh, representation and unit support is required.",),
        )
    qualification_metric_ids = {
        metric_id for row in envelope.qualification_evidence for metric_id in row.supported_metric_ids
    }
    uncovered_metric_ids = sorted(set(result_support) - qualification_metric_ids)
    outside_support_reasons = []
    if geometry_outside:
        outside_support_reasons.append("geometry_range")
    if load_outside:
        outside_support_reasons.append("load_range")
    if outside_result_ids:
        outside_support_reasons.append("result_range_or_uncertainty")
    if uncovered_metric_ids:
        outside_support_reasons.append("qualification_metric_coverage")
    return Calculation(
        status="out_of_scope" if outside_support_reasons else "computed",
        values={
            "assessment_id": x.assessment_id,
            "load_case_id": x.load_case_id,
            "envelope_id": envelope.envelope_id,
            "geometry_outside_support_ids": geometry_outside,
            "load_outside_support_ids": load_outside,
            "result_comparisons": result_comparisons,
            "outside_result_ids": outside_result_ids,
            "uncovered_metric_ids": uncovered_metric_ids,
            "outside_support_reasons": outside_support_reasons,
            "declared_applicability_outcome": (
                "outside_support" if outside_support_reasons else "within_support"
            ),
        },
        notes=(
            "The result is a support comparison for replaceable caller/provider stress evidence.",
            "No proprietary stress index, acceptance, fatigue, life or probability is calculated.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("nozzle local-stress assessment asset and location must match the run context")

    return [
        ModelSpec(
            "structural.nozzle_local_stress_provider_evidence",
            NozzleLocalStressProviderEvidence,
            nozzle_local_stress_provider_evidence,
            {
                "assessment_id": "1",
                "load_case_id": "1",
                "envelope_id": "1",
                "geometry_outside_support_ids": "1",
                "load_outside_support_ids": "1",
                "result_comparisons": "mixed",
                "outside_result_ids": "1",
                "uncovered_metric_ids": "1",
                "outside_support_reasons": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Geometry, load component and stress metric units are exact caller/provider tokens.",
                "Coordinate frame, mesh, result location and spatial averaging basis are not inferred.",
                "Calibration and holdout evidence retain disjoint physical source groups.",
            ),
            ("reviewed_nozzle_local_stress_provider_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
