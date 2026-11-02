"""External-pressure provider results bound to caller qualification evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

ResultKind = Literal["eigen_buckling_pressure", "nonlinear_limit_pressure"]
Partition = Literal["calibration", "holdout"]


class ExternalPressureGeometryMetric(Contract):
    metric_id: str = Field(min_length=1)
    value: Positive
    unit_token: str = Field(min_length=1)
    measurement_basis: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ExternalPressureImperfectionRecord(Contract):
    imperfection_field_id: str = Field(min_length=1)
    physical_surface_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    field_definition: str = Field(min_length=1)
    field_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    metric_definition_id: str = Field(min_length=1)
    metric_value: Nonnegative
    metric_unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid imperfection record requires a basis")
        return self


class ExternalPressureProviderResult(Contract):
    result_record_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    result_kind: ResultKind
    pressure_basis: str = Field(min_length=1)
    result_value: Positive
    result_unit_token: str = Field(min_length=1)
    mesh_id: str = Field(min_length=1)
    mesh_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_model_id: str = Field(min_length=1)
    material_model_id: str = Field(min_length=1)
    imperfection_model_id: str = Field(min_length=1)
    boundary_model_id: str = Field(min_length=1)
    load_model_id: str = Field(min_length=1)
    solver_id: str = Field(min_length=1)
    solver_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    convergence_or_solution_state: str = Field(min_length=1)
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("an invalid external-pressure result requires a basis")
        return self


class ExternalPressureQualificationEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    partition: Partition
    physical_benchmark_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    result_kind: ResultKind
    pressure_basis: str = Field(min_length=1)
    observed_value: Positive
    predicted_value: Positive
    unit_token: str = Field(min_length=1)
    expanded_observation_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    supports_declared_envelope: bool
    invalid_or_limiting_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if (
            not self.record_valid or not self.supports_declared_envelope
        ) and not self.invalid_or_limiting_basis:
            raise ValueError("invalid or limiting external-pressure qualification evidence needs a basis")
        return self


class ExternalPressureGeometrySupport(Contract):
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_value: Positive
    maximum_value: Positive

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.maximum_value < self.minimum_value:
            raise ValueError("external-pressure geometry support bounds must be ordered")
        return self


class ExternalPressureQualificationEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    shell_type_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    boundary_support_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    pressure_basis: str = Field(min_length=1)
    minimum_thickness_m: Positive
    maximum_thickness_m: Positive
    geometry_support: tuple[ExternalPressureGeometrySupport, ...] = Field(min_length=1)
    imperfection_metric_definition_id: str = Field(min_length=1)
    imperfection_metric_unit_token: str = Field(min_length=1)
    minimum_imperfection_metric_value: Nonnegative
    maximum_imperfection_metric_value: Nonnegative
    supported_result_kinds: tuple[ResultKind, ...] = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    solver_id: str = Field(min_length=1)
    solver_revision: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_evidence: tuple[ExternalPressureQualificationEvidence, ...] = Field(min_length=1)
    minimum_calibration_source_group_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_support(self):
        if self.maximum_thickness_m < self.minimum_thickness_m:
            raise ValueError("external-pressure thickness support must be ordered")
        if self.maximum_imperfection_metric_value < self.minimum_imperfection_metric_value:
            raise ValueError("external-pressure imperfection support must be ordered")
        geometry_ids = [row.metric_id for row in self.geometry_support]
        evidence_ids = [row.evidence_record_id for row in self.qualification_evidence]
        if len(set(geometry_ids)) != len(geometry_ids):
            raise ValueError("external-pressure geometry support identifiers must be unique")
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("external-pressure qualification evidence identifiers must be unique")
        if len(set(self.supported_result_kinds)) != len(self.supported_result_kinds):
            raise ValueError("external-pressure result kinds must be unique")
        return self


class ExternalPressureProviderEvidenceAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    shell_type_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    thickness_m: Positive
    geometry_metrics: tuple[ExternalPressureGeometryMetric, ...] = Field(min_length=1)
    boundary_support_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    pressure_basis: str = Field(min_length=1)
    imperfection: ExternalPressureImperfectionRecord
    provider_result: ExternalPressureProviderResult
    candidate_envelopes: tuple[ExternalPressureQualificationEnvelope, ...] = Field(min_length=1)
    component_material_geometry_and_thickness_reviewed: bool
    boundary_support_load_case_and_pressure_basis_reviewed: bool
    imperfection_field_metric_and_units_reviewed: bool
    mesh_and_model_identity_reviewed: bool
    solver_provider_revision_and_digests_reviewed: bool
    result_kind_units_and_solution_state_reviewed: bool
    calibration_holdout_partitions_reviewed: bool
    qualification_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_records(self):
        geometry_ids = [row.metric_id for row in self.geometry_metrics]
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(set(geometry_ids)) != len(geometry_ids):
            raise ValueError("external-pressure geometry metric identifiers must be unique")
        if len(set(envelope_ids)) != len(envelope_ids):
            raise ValueError("external-pressure envelope identifiers must be unique")
        return self


def _identity(value) -> tuple[str, ...]:
    return (
        value.shell_type_id,
        value.material_condition_id,
        value.boundary_support_id,
        value.load_case_id,
        value.pressure_basis,
    )


def external_pressure_provider_evidence(
    x: ExternalPressureProviderEvidenceAssessment,
) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "component_material_geometry_and_thickness_reviewed",
            "boundary_support_load_case_and_pressure_basis_reviewed",
            "imperfection_field_metric_and_units_reviewed",
            "mesh_and_model_identity_reviewed",
            "solver_provider_revision_and_digests_reviewed",
            "result_kind_units_and_solution_state_reviewed",
            "calibration_holdout_partitions_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    matches = [row for row in x.candidate_envelopes if _identity(row) == _identity(x)]
    if missing_reviews or not x.imperfection.record_valid or not x.provider_result.record_valid:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matches],
                "missing_reviews": missing_reviews,
                "imperfection_record_valid": x.imperfection.record_valid,
                "provider_result_record_valid": x.provider_result.record_valid,
            },
            notes=("Invalid or unreviewed imperfection and provider results are not qualified.",),
        )
    if not matches:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "identity_matching_envelope_ids": []},
            notes=("No caller-owned envelope has the exact shell, boundary, load and pressure basis.",),
        )

    envelope = matches[0]
    result = x.provider_result
    invalid_qualification_ids = [
        row.evidence_record_id
        for row in envelope.qualification_evidence
        if not row.record_valid or not row.supports_declared_envelope
    ]
    qualification_mismatch_ids = []
    for row in envelope.qualification_evidence:
        if (
            row.provider_id != envelope.provider_id
            or row.provider_revision != envelope.provider_revision
            or row.provider_configuration_digest != envelope.provider_configuration_digest
            or row.pressure_basis != envelope.pressure_basis
            or row.result_kind not in envelope.supported_result_kinds
            or row.unit_token != envelope.result_unit_token
        ):
            qualification_mismatch_ids.append(row.evidence_record_id)
    calibration_groups = {
        row.source_group_id for row in envelope.qualification_evidence if row.partition == "calibration"
    }
    holdout_groups = {
        row.source_group_id for row in envelope.qualification_evidence if row.partition == "holdout"
    }
    holdout_independence_groups = {
        row.independence_group_id for row in envelope.qualification_evidence if row.partition == "holdout"
    }
    partition_counts_sufficient = (
        len(calibration_groups) >= envelope.minimum_calibration_source_group_count
        and len(holdout_groups) >= envelope.minimum_holdout_source_group_count
        and len(holdout_independence_groups) >= envelope.minimum_holdout_independence_group_count
    )
    provider_identity_matches = (
        result.solver_id == envelope.solver_id
        and result.solver_revision == envelope.solver_revision
        and result.provider_id == envelope.provider_id
        and result.provider_revision == envelope.provider_revision
        and result.provider_configuration_digest == envelope.provider_configuration_digest
    )
    result_basis_and_unit_match = (
        result.pressure_basis == envelope.pressure_basis
        and result.result_unit_token == envelope.result_unit_token
    )
    if (
        invalid_qualification_ids
        or qualification_mismatch_ids
        or not partition_counts_sufficient
        or not provider_identity_matches
        or not result_basis_and_unit_match
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "qualification_envelope_id": envelope.envelope_id,
                "invalid_qualification_evidence_ids": invalid_qualification_ids,
                "qualification_evidence_identity_or_unit_mismatch_ids": qualification_mismatch_ids,
                "qualification_partition_counts_sufficient": partition_counts_sufficient,
                "provider_identity_matches": provider_identity_matches,
                "result_pressure_basis_and_unit_match": result_basis_and_unit_match,
            },
            notes=(
                "Provider lineage, exact units and independent qualification partitions must be complete.",
            ),
        )

    geometry_by_id = {row.metric_id: row for row in x.geometry_metrics}
    missing_geometry_ids = []
    geometry_unit_mismatch_ids = []
    outside_geometry_ids = []
    geometry_comparisons = []
    for support in envelope.geometry_support:
        row = geometry_by_id.get(support.metric_id)
        if row is None:
            missing_geometry_ids.append(support.metric_id)
            continue
        if row.unit_token != support.unit_token:
            geometry_unit_mismatch_ids.append(row.metric_id)
            within = None
        else:
            within = support.minimum_value <= row.value <= support.maximum_value
            if not within:
                outside_geometry_ids.append(row.metric_id)
        geometry_comparisons.append(
            {
                "metric_id": row.metric_id,
                "unit_matches": row.unit_token == support.unit_token,
                "within_support": within,
            }
        )
    imperfection_definition_matches = (
        x.imperfection.metric_definition_id == envelope.imperfection_metric_definition_id
    )
    imperfection_unit_matches = x.imperfection.metric_unit_token == envelope.imperfection_metric_unit_token
    if (
        missing_geometry_ids
        or geometry_unit_mismatch_ids
        or not imperfection_definition_matches
        or not imperfection_unit_matches
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "qualification_envelope_id": envelope.envelope_id,
                "missing_geometry_metric_ids": missing_geometry_ids,
                "geometry_unit_mismatch_ids": geometry_unit_mismatch_ids,
                "imperfection_metric_definition_matches": imperfection_definition_matches,
                "imperfection_metric_unit_matches": imperfection_unit_matches,
            },
            notes=(
                "Geometry and imperfection definitions require exact caller-declared units and identities.",
            ),
        )

    outside_reasons = []
    if not envelope.minimum_thickness_m <= x.thickness_m <= envelope.maximum_thickness_m:
        outside_reasons.append("thickness_m")
    if outside_geometry_ids:
        outside_reasons.append("geometry_support")
    if not (
        envelope.minimum_imperfection_metric_value
        <= x.imperfection.metric_value
        <= envelope.maximum_imperfection_metric_value
    ):
        outside_reasons.append("imperfection_metric_value")
    if result.result_kind not in envelope.supported_result_kinds:
        outside_reasons.append("result_kind")
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "component_id": x.component_id,
        "qualification_envelope_id": envelope.envelope_id,
        "provider_result_record_id": result.result_record_id,
        "result_kind": result.result_kind,
        "provider_reported_result_value": result.result_value,
        "provider_reported_result_unit_token": result.result_unit_token,
        "pressure_basis": result.pressure_basis,
        "mesh_id": result.mesh_id,
        "outside_support_reasons": outside_reasons,
        "geometry_comparisons": geometry_comparisons,
        "calibration_source_group_ids": sorted(calibration_groups),
        "holdout_source_group_ids": sorted(holdout_groups),
        "holdout_independence_group_ids": sorted(holdout_independence_groups),
    }
    notes = (
        "The provider value is preserved as evidence and is not converted to allowable pressure or safety factor.",
        "No code chart, collapse probability, acceptance, remaining life or model transferability is inferred.",
        "Eigen and nonlinear result kinds remain distinct and retain mesh, model, solver and digest lineage.",
    )
    if outside_reasons:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("external-pressure assessment asset and location must match run context")

    return [
        ModelSpec(
            "structural.external_pressure_provider_evidence",
            ExternalPressureProviderEvidenceAssessment,
            external_pressure_provider_evidence,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "component_id": "1",
                "qualification_envelope_id": "1",
                "provider_result_record_id": "1",
                "result_kind": "1",
                "provider_reported_result_value": "provider unit",
                "provider_reported_result_unit_token": "1",
                "pressure_basis": "1",
                "mesh_id": "1",
                "outside_support_reasons": "1",
                "geometry_comparisons": "mixed",
                "calibration_source_group_ids": "1",
                "holdout_source_group_ids": "1",
                "holdout_independence_group_ids": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Shell, material condition, boundary, load case and pressure basis match exactly.",
                "Geometry and imperfection metrics use exact caller definitions and units.",
                "Provider results remain evidence, not allowable pressure, acceptance or collapse probability.",
            ),
            ("reviewed_external_pressure_provider_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
