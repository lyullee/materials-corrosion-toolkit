"""Qualified metadata exchange for externally evaluated pitting FFS results."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class PitGeometryRecord(Contract):
    pit_field_id: str = Field(min_length=1)
    cluster_id: str = Field(min_length=1)
    geometry_definition_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    length_value: Positive
    width_value: Positive
    depth_value: Positive
    geometry_unit_token: str = Field(min_length=1)
    geometry_content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    inspection_method_id: str = Field(min_length=1)
    sizing_uncertainty_value: Nonnegative | None = None
    sizing_uncertainty_unit_token: str | None = None
    pod_evidence_id: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def uncertainty_pair(self):
        if (self.sizing_uncertainty_value is None) != (self.sizing_uncertainty_unit_token is None):
            raise ValueError("pit sizing uncertainty value and unit must be supplied together")
        return self


class PittingFFSQualificationRecord(Contract):
    record_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid pitting FFS qualification records require a basis")
        return self


class PittingFFSProviderEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    component_type_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    pressure_basis: Literal["internal_minus_external", "external_minus_internal"]
    wall_thickness_unit_token: str = Field(min_length=1)
    geometry_unit_token: str = Field(min_length=1)
    supported_geometry_definition_ids: tuple[str, ...] = Field(min_length=1)
    supported_inspection_method_ids: tuple[str, ...] = Field(min_length=1)
    supported_load_case_ids: tuple[str, ...] = Field(min_length=1)
    result_metric_id: str = Field(min_length=1)
    result_metric_definition: str = Field(min_length=1)
    result_unit_token: str = Field(min_length=1)
    provider_model_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_records: tuple[PittingFFSQualificationRecord, ...] = Field(min_length=2)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def qualification_partitions(self):
        for values in (
            self.supported_geometry_definition_ids,
            self.supported_inspection_method_ids,
            self.supported_load_case_ids,
        ):
            if len(set(values)) != len(values):
                raise ValueError("pitting FFS support identifiers must be unique")
        if {row.partition for row in self.qualification_records if row.record_valid} != {
            "calibration",
            "holdout",
        }:
            raise ValueError("pitting FFS qualification requires calibration and holdout records")
        groups = {}
        for row in self.qualification_records:
            prior = groups.setdefault(row.source_group_id, row.partition)
            if prior != row.partition:
                raise ValueError("pitting FFS source groups cannot cross partitions")
        return self


class PittingFFSProviderEvidence(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    component_type_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    wall_thickness_value: Positive
    wall_thickness_unit_token: str = Field(min_length=1)
    pressure_basis: Literal["internal_minus_external", "external_minus_internal"]
    load_case_id: str = Field(min_length=1)
    pit_geometries: tuple[PitGeometryRecord, ...] = Field(min_length=1)
    provider_model_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_metric_id: str = Field(min_length=1)
    result_metric_definition: str = Field(min_length=1)
    result_value: float
    result_unit_token: str = Field(min_length=1)
    qualification_envelope: PittingFFSProviderEnvelope
    component_material_location_and_frame_reviewed: bool
    wall_thickness_pressure_and_load_basis_reviewed: bool
    pit_geometry_definition_units_and_clusters_reviewed: bool
    inspection_uncertainty_and_pod_evidence_reviewed: bool
    provider_model_revision_and_digests_reviewed: bool
    result_metric_definition_and_unit_reviewed: bool
    qualification_partitions_and_source_groups_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_pits(self):
        ids = [row.pit_field_id for row in self.pit_geometries]
        if len(set(ids)) != len(ids):
            raise ValueError("pit-field IDs must be unique")
        return self


def pitting_ffs_provider_evidence(x: PittingFFSProviderEvidence) -> Calculation:
    e = x.qualification_envelope
    reviews = (
        "component_material_location_and_frame_reviewed",
        "wall_thickness_pressure_and_load_basis_reviewed",
        "pit_geometry_definition_units_and_clusters_reviewed",
        "inspection_uncertainty_and_pod_evidence_reviewed",
        "provider_model_revision_and_digests_reviewed",
        "result_metric_definition_and_unit_reviewed",
        "qualification_partitions_and_source_groups_reviewed",
        "qualification_envelope_authority_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    exact_fields = (
        "component_type_id",
        "material_condition_id",
        "coordinate_frame_id",
        "pressure_basis",
        "wall_thickness_unit_token",
        "provider_model_id",
        "provider_revision",
        "provider_configuration_digest",
        "result_metric_id",
        "result_metric_definition",
        "result_unit_token",
    )
    mismatches = [name for name in exact_fields if getattr(x, name) != getattr(e, name)]
    invalid_qualification_ids = [row.record_id for row in e.qualification_records if not row.record_valid]
    if missing_reviews or mismatches or invalid_qualification_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_or_definition_mismatch_fields": mismatches,
                "invalid_qualification_record_ids": invalid_qualification_ids,
            },
            notes=(
                "Provider evidence is withheld until identity, definition and qualification lineage are complete.",
            ),
        )
    comparisons = []
    outside = []
    for pit in x.pit_geometries:
        reasons = []
        if pit.coordinate_frame_id != e.coordinate_frame_id:
            reasons.append("coordinate_frame_id")
        if pit.geometry_unit_token != e.geometry_unit_token:
            reasons.append("geometry_unit_token")
        if pit.geometry_definition_id not in e.supported_geometry_definition_ids:
            reasons.append("geometry_definition_id")
        if pit.inspection_method_id not in e.supported_inspection_method_ids:
            reasons.append("inspection_method_id")
        if reasons:
            outside.append(pit.pit_field_id)
        comparisons.append(
            {
                "pit_field_id": pit.pit_field_id,
                "cluster_id": pit.cluster_id,
                "outside_support_reasons": reasons,
                "within_declared_provider_support": not reasons,
            }
        )
    load_supported = x.load_case_id in e.supported_load_case_ids
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "component_id": x.component_id,
        "selected_envelope_id": e.envelope_id,
        "pit_geometry_comparisons": comparisons,
        "outside_support_pit_field_ids": outside,
        "load_case_within_support": load_supported,
        "provider_result": {
            "metric_id": x.result_metric_id,
            "metric_definition": x.result_metric_definition,
            "value": x.result_value,
            "unit_token": x.result_unit_token,
            "result_digest": x.provider_result_digest,
        },
        "qualification_partition_counts": {
            p: sum(r.partition == p for r in e.qualification_records) for p in ("calibration", "holdout")
        },
    }
    notes = (
        "The external result is preserved without reproducing proprietary FFS equations, tables or provider code.",
        "Pit clusters, interaction and missing geometry are never reconstructed or inferred.",
        "No capacity, acceptance, remaining life or failure probability is produced.",
    )
    if outside or not load_supported:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_provider_evidence_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("pitting FFS assessment asset and location must match the run context")

    return [
        ModelSpec(
            "structural.pitting_ffs_provider_evidence",
            PittingFFSProviderEvidence,
            pitting_ffs_provider_evidence,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "component_id": "1",
                "selected_envelope_id": "1",
                "pit_geometry_comparisons": "mixed",
                "outside_support_pit_field_ids": "1",
                "load_case_within_support": "1",
                "provider_result": "mixed",
                "qualification_partition_counts": "count",
                "declared_provider_evidence_outcome": "1",
            },
            (
                "Component, material, coordinate frame, pressure and load bases are caller-reviewed exact identities.",
                "Geometry, inspection and result metrics retain their original definitions, units, uncertainty and content digests.",
                "The model exchanges a qualified provider result without implementing FFS equations or acceptance limits.",
            ),
            ("reviewed_pitting_ffs_provider_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
