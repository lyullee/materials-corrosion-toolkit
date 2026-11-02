"""Finite-element mesh/result metadata exchange with caller-owned qualification support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative
from ..registry import ModelSpec


class FEMeshDescriptor(Contract):
    mesh_id: str = Field(min_length=1)
    mesh_revision: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    dimensionality: Literal["1d", "2d", "axisymmetric", "3d"]
    element_family_ids: tuple[str, ...] = Field(min_length=1)
    node_count: int = Field(ge=1)
    element_count: int = Field(ge=1)
    region_ids: tuple[str, ...] = Field(min_length=1)
    node_identity_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    element_identity_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    connectivity_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_identifiers(self):
        for values, label in ((self.element_family_ids, "element family"), (self.region_ids, "region")):
            if len(set(values)) != len(values):
                raise ValueError(f"finite-element {label} IDs must be unique")
        return self


class FEMaterialAssignment(Contract):
    assignment_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    property_provider_id: str = Field(min_length=1)
    property_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    assignment_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class FELoadBoundaryCase(Contract):
    case_id: str = Field(min_length=1)
    load_definition_id: str = Field(min_length=1)
    boundary_definition_id: str = Field(min_length=1)
    load_basis: str = Field(min_length=1)
    load_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class FEResultFieldDescriptor(Contract):
    field_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    time_s: Nonnegative | None = None
    frequency_Hz: Nonnegative | None = None
    region_id: str = Field(min_length=1)
    result_location: Literal["node", "element", "integration_point", "face", "edge"]
    averaging_basis: str = Field(min_length=1)
    quantity_kind: Literal["scalar", "vector", "tensor"]
    quantity_id: str = Field(min_length=1)
    quantity_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    component_ids: tuple[str, ...] = Field(min_length=1)
    array_shape: tuple[int, ...] = Field(min_length=1)
    array_order: Literal["C", "F", "provider_native"]
    identity_axis_basis: str = Field(min_length=1)
    array_content_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def strict_field_metadata(self):
        if (self.time_s is None) == (self.frequency_Hz is None):
            raise ValueError("finite-element fields require exactly one time or frequency coordinate")
        if any(size < 1 for size in self.array_shape):
            raise ValueError("finite-element result array dimensions must be positive")
        if len(set(self.component_ids)) != len(self.component_ids):
            raise ValueError("finite-element result component IDs must be unique")
        expected = {"scalar": 1, "vector": 2, "tensor": 3}[self.quantity_kind]
        if len(self.component_ids) < expected:
            raise ValueError("finite-element result components do not support the declared quantity kind")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid finite-element result fields require a basis")
        return self


class FEVerificationRecord(Contract):
    verification_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout", "application"]
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    verification_kind: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    metric_value: Nonnegative
    metric_unit_token: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid finite-element verification records require a basis")
        return self


class FEResultExchangeEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    supported_dimensionalities: tuple[Literal["1d", "2d", "axisymmetric", "3d"], ...]
    supported_element_family_ids: tuple[str, ...] = Field(min_length=1)
    supported_result_locations: tuple[
        Literal["node", "element", "integration_point", "face", "edge"], ...
    ] = Field(min_length=1)
    supported_quantity_ids: tuple[str, ...] = Field(min_length=1)
    supported_unit_tokens: tuple[str, ...] = Field(min_length=1)
    maximum_node_count: int = Field(ge=1)
    maximum_element_count: int = Field(ge=1)
    required_partitions: tuple[Literal["calibration", "holdout", "application"], ...] = Field(min_length=1)
    solver_id: str = Field(min_length=1)
    solver_revision: str = Field(min_length=1)
    solver_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_support(self):
        for values, label in (
            (self.supported_dimensionalities, "dimensionality"),
            (self.supported_element_family_ids, "element family"),
            (self.supported_result_locations, "result location"),
            (self.supported_quantity_ids, "quantity"),
            (self.supported_unit_tokens, "unit"),
            (self.required_partitions, "partition"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"finite-element supported {label} values must be unique")
        return self


class FiniteElementResultExchange(Contract):
    exchange_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    mesh: FEMeshDescriptor
    material_assignments: tuple[FEMaterialAssignment, ...] = Field(min_length=1)
    load_boundary_cases: tuple[FELoadBoundaryCase, ...] = Field(min_length=1)
    result_fields: tuple[FEResultFieldDescriptor, ...] = Field(min_length=1)
    solver_id: str = Field(min_length=1)
    solver_revision: str = Field(min_length=1)
    solver_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    solver_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    solver_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    convergence_definition: str = Field(min_length=1)
    convergence_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    convergence_record_reviewed: bool
    verification_records: tuple[FEVerificationRecord, ...] = Field(min_length=1)
    qualification_envelope: FEResultExchangeEnvelope
    model_mesh_and_coordinate_frame_reviewed: bool
    material_assignments_reviewed: bool
    load_and_boundary_cases_reviewed: bool
    step_time_frequency_and_result_location_reviewed: bool
    quantity_components_units_shape_and_order_reviewed: bool
    solver_revision_configuration_and_digests_reviewed: bool
    verification_partitions_and_source_groups_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identities_and_links(self):
        for rows, attr, label in (
            (self.material_assignments, "assignment_id", "material assignment"),
            (self.load_boundary_cases, "case_id", "load/boundary case"),
            (self.result_fields, "field_id", "result field"),
            (self.verification_records, "verification_id", "verification record"),
        ):
            identifiers = [getattr(row, attr) for row in rows]
            if len(set(identifiers)) != len(identifiers):
                raise ValueError(f"finite-element {label} IDs must be unique")
        regions = set(self.mesh.region_ids)
        if {row.region_id for row in self.material_assignments} - regions:
            raise ValueError("material assignments must reference declared mesh regions")
        if {row.region_id for row in self.result_fields} - regions:
            raise ValueError("result fields must reference declared mesh regions")
        cases = {row.case_id for row in self.load_boundary_cases}
        if {row.case_id for row in self.result_fields} - cases:
            raise ValueError("result fields must reference declared load/boundary cases")
        partition_groups = {}
        for record in self.verification_records:
            prior = partition_groups.setdefault(record.source_group_id, record.partition)
            if prior != record.partition:
                raise ValueError("verification source groups cannot cross partitions")
        return self


def finite_element_result_exchange(x: FiniteElementResultExchange) -> Calculation:
    envelope = x.qualification_envelope
    reviews = (
        "model_mesh_and_coordinate_frame_reviewed",
        "material_assignments_reviewed",
        "load_and_boundary_cases_reviewed",
        "step_time_frequency_and_result_location_reviewed",
        "quantity_components_units_shape_and_order_reviewed",
        "solver_revision_configuration_and_digests_reviewed",
        "verification_partitions_and_source_groups_reviewed",
        "qualification_envelope_authority_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    solver_mismatch_fields = [
        name
        for name in ("solver_id", "solver_revision", "solver_configuration_digest")
        if getattr(x, name) != getattr(envelope, name)
    ]
    invalid_field_ids = [row.field_id for row in x.result_fields if not row.record_valid]
    invalid_verification_ids = [row.verification_id for row in x.verification_records if not row.record_valid]
    represented_partitions = {row.partition for row in x.verification_records if row.record_valid}
    missing_partitions = [
        partition for partition in envelope.required_partitions if partition not in represented_partitions
    ]
    if (
        any(
            (
                missing_reviews,
                solver_mismatch_fields,
                invalid_field_ids,
                invalid_verification_ids,
                missing_partitions,
            )
        )
        or not x.convergence_record_reviewed
    ):
        return Calculation(
            status="needs_data",
            values={
                "exchange_id": x.exchange_id,
                "missing_reviews": missing_reviews,
                "solver_mismatch_fields": solver_mismatch_fields,
                "invalid_result_field_ids": invalid_field_ids,
                "invalid_verification_record_ids": invalid_verification_ids,
                "missing_verification_partitions": missing_partitions,
                "convergence_record_reviewed": x.convergence_record_reviewed,
            },
            notes=("Exchange is withheld until solver, convergence and verification lineage is complete.",),
        )

    mesh_reasons = []
    if x.mesh.dimensionality not in envelope.supported_dimensionalities:
        mesh_reasons.append("dimensionality")
    if set(x.mesh.element_family_ids) - set(envelope.supported_element_family_ids):
        mesh_reasons.append("element_family_ids")
    if x.mesh.node_count > envelope.maximum_node_count:
        mesh_reasons.append("node_count")
    if x.mesh.element_count > envelope.maximum_element_count:
        mesh_reasons.append("element_count")
    field_comparisons = []
    outside_field_ids = []
    for field in x.result_fields:
        reasons = []
        if field.result_location not in envelope.supported_result_locations:
            reasons.append("result_location")
        if field.quantity_id not in envelope.supported_quantity_ids:
            reasons.append("quantity_id")
        if field.unit_token not in envelope.supported_unit_tokens:
            reasons.append("unit_token")
        if reasons:
            outside_field_ids.append(field.field_id)
        field_comparisons.append(
            {
                "field_id": field.field_id,
                "outside_support_reasons": reasons,
                "within_declared_exchange_support": not reasons,
            }
        )
    values = {
        "exchange_id": x.exchange_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "analysis_id": x.analysis_id,
        "model_id": x.model_id,
        "mesh_id": x.mesh.mesh_id,
        "qualification_envelope_id": envelope.envelope_id,
        "mesh_outside_support_reasons": mesh_reasons,
        "field_comparisons": field_comparisons,
        "outside_support_field_ids": outside_field_ids,
        "verification_partition_counts": {
            partition: sum(row.partition == partition for row in x.verification_records)
            for partition in envelope.required_partitions
        },
        "physical_specimen_ids": sorted({row.physical_specimen_id for row in x.verification_records}),
        "source_group_ids": sorted({row.source_group_id for row in x.verification_records}),
    }
    notes = (
        "Only mesh, field and solver metadata plus immutable content digests are exchanged; large result arrays are not embedded.",
        "Schema and caller-envelope compliance do not qualify a mesh, solver, interpolation, convergence or physical model.",
        "No acceptance, remaining life or failure probability is produced.",
    )
    if mesh_reasons or outside_field_ids:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_exchange_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("finite-element exchange asset and location must match the run context")

    return [
        ModelSpec(
            "structural.finite_element_result_exchange",
            FiniteElementResultExchange,
            finite_element_result_exchange,
            {
                "exchange_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "analysis_id": "1",
                "model_id": "1",
                "mesh_id": "1",
                "qualification_envelope_id": "1",
                "mesh_outside_support_reasons": "1",
                "field_comparisons": "mixed",
                "outside_support_field_ids": "1",
                "verification_partition_counts": "count",
                "physical_specimen_ids": "1",
                "source_group_ids": "1",
                "declared_exchange_outcome": "1",
            },
            (
                "Mesh and result identities, coordinate frame, ordering, quantity definitions and content digests are caller-reviewed metadata.",
                "Solver revision, configuration, input and result digests bind the exchange without embedding solver output arrays.",
                "Qualification support and verification partitions do not establish mesh convergence, solver validity or code acceptance.",
            ),
            ("reviewed_finite_element_result_exchange_envelope",),
            context_validator=same_identity,
        )
    ]
