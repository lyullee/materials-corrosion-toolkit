"""Dissimilar-weld identity and caller-owned compatibility-review reconciliation."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

MaterialRole = Literal["base_a", "base_b", "filler_deposit", "buttering", "overlay"]
BoundarySide = Literal["base_a", "base_b"]
ReviewStatus = Literal[
    "reviewed_supported",
    "reviewed_limited",
    "reviewed_out_of_scope",
    "unresolved",
    "not_applicable",
]


class DissimilarWeldMaterialEvidence(Contract):
    material_subject_id: str = Field(min_length=1)
    material_role: MaterialRole
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    material_lot_id: str = Field(min_length=1)
    composition_provider_id: str = Field(min_length=1)
    composition_provider_revision: str = Field(min_length=1)
    composition_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    property_provider_id: str | None = None
    property_provider_revision: str | None = None
    property_result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_property_provider(self):
        fields = (
            self.property_provider_id,
            self.property_provider_revision,
            self.property_result_digest,
        )
        if any(value is not None for value in fields) and not all(value is not None for value in fields):
            raise ValueError("property provider ID, revision and digest must be supplied together")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid dissimilar-weld material evidence requires a basis")
        return self


class DissimilarWeldLayer(Contract):
    layer_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    layer_role: Literal["filler_deposit", "buttering", "overlay"]
    applied_side: Literal["base_a", "base_b", "joint"]
    material_subject_id: str = Field(min_length=1)
    welding_procedure_id: str = Field(min_length=1)
    welding_procedure_revision: str = Field(min_length=1)
    physical_region_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class FusionBoundaryRegion(Contract):
    boundary_region_id: str = Field(min_length=1)
    side: BoundarySide
    base_material_subject_id: str = Field(min_length=1)
    adjacent_layer_id: str = Field(min_length=1)
    joint_location_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    transition_zone_definition: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class DissimilarWeldThermalInterval(Contract):
    interval_id: str = Field(min_length=1)
    interval_kind: Literal["welding", "post_weld_heat_treatment", "service_thermal_exposure"]
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
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
            raise ValueError("dissimilar-weld thermal intervals require positive duration")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("dissimilar-weld thermal temperature ranges must be ordered")
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid dissimilar-weld thermal intervals require a basis")
        return self


class DissimilarWeldTransitionMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    boundary_region_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    measurement_kind: Literal[
        "dilution_metric",
        "transition_zone_dimension",
        "composition_metric",
        "property_metric",
    ]
    metric_definition: str = Field(min_length=1)
    value: float
    unit_token: str = Field(min_length=1)
    expanded_uncertainty: Nonnegative
    uncertainty_coverage_factor: Positive
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid dissimilar-weld transition measurements require a basis")
        return self


class DissimilarWeldCompatibilityReview(Contract):
    review_id: str = Field(min_length=1)
    review_subject_id: str = Field(min_length=1)
    review_subject_kind: Literal[
        "base_material_pair",
        "filler_or_deposit",
        "buttering_or_overlay",
        "fusion_boundary",
        "weld_procedure",
        "heat_treatment",
        "service_environment",
        "dilution_or_transition_zone",
        "user_defined",
    ]
    linked_identity_ids: tuple[str, ...] = Field(min_length=1)
    review_status: ReviewStatus
    review_basis: str = Field(min_length=1)
    limitation_or_unresolved_basis: str | None = None
    reviewer_or_provider_id: str = Field(min_length=1)
    reviewer_or_provider_revision: str = Field(min_length=1)
    review_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    review_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_basis(self):
        if (
            self.review_status
            in {
                "reviewed_limited",
                "reviewed_out_of_scope",
                "unresolved",
            }
            and not self.limitation_or_unresolved_basis
        ):
            raise ValueError("limited, out-of-scope or unresolved reviews require a basis")
        if len(set(self.linked_identity_ids)) != len(self.linked_identity_ids):
            raise ValueError("linked dissimilar-weld review identities must be unique")
        return self


class DissimilarWeldUnresolvedItem(Contract):
    unresolved_item_id: str = Field(min_length=1)
    review_subject_id: str = Field(min_length=1)
    unresolved_category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    required_evidence_or_decision: str = Field(min_length=1)
    owner_or_authority_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class DissimilarWeldApplicabilityEvidence(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    joint_location_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    service_environment_id: str = Field(min_length=1)
    service_environment_definition: str = Field(min_length=1)
    thermal_clock_id: str = Field(min_length=1)
    base_material_a_subject_id: str = Field(min_length=1)
    base_material_b_subject_id: str = Field(min_length=1)
    material_evidence: tuple[DissimilarWeldMaterialEvidence, ...] = Field(min_length=2)
    layers: tuple[DissimilarWeldLayer, ...] = Field(min_length=1)
    fusion_boundaries: tuple[FusionBoundaryRegion, ...] = Field(min_length=2)
    thermal_history: tuple[DissimilarWeldThermalInterval, ...] = Field(min_length=1)
    transition_measurements: tuple[DissimilarWeldTransitionMeasurement, ...] = ()
    required_review_subject_ids: tuple[str, ...] = Field(min_length=1)
    compatibility_reviews: tuple[DissimilarWeldCompatibilityReview, ...] = Field(min_length=1)
    unresolved_items: tuple[DissimilarWeldUnresolvedItem, ...] = ()
    joint_material_layer_and_boundary_identity_reviewed: bool
    location_coordinate_frame_and_region_mapping_reviewed: bool
    procedure_pwht_and_thermal_history_reviewed: bool
    service_environment_identity_reviewed: bool
    composition_property_provider_lineage_reviewed: bool
    transition_measurement_definitions_units_and_uncertainty_reviewed: bool
    compatibility_review_authority_and_scope_reviewed: bool
    unresolved_item_completeness_reviewed: bool

    @model_validator(mode="after")
    def linked_unique_records(self):
        for identifiers, name in (
            ([row.material_subject_id for row in self.material_evidence], "material subject"),
            ([row.layer_id for row in self.layers], "layer"),
            ([row.boundary_region_id for row in self.fusion_boundaries], "fusion boundary"),
            ([row.interval_id for row in self.thermal_history], "thermal interval"),
            ([row.measurement_id for row in self.transition_measurements], "measurement"),
            ([row.review_id for row in self.compatibility_reviews], "review"),
            ([row.review_subject_id for row in self.compatibility_reviews], "review subject"),
            ([row.unresolved_item_id for row in self.unresolved_items], "unresolved item"),
        ):
            if len(set(identifiers)) != len(identifiers):
                raise ValueError(f"dissimilar-weld {name} identifiers must be unique")
        if len(set(self.required_review_subject_ids)) != len(self.required_review_subject_ids):
            raise ValueError("required dissimilar-weld review subjects must be unique")
        materials = {row.material_subject_id: row for row in self.material_evidence}
        for required_subject, role in (
            (self.base_material_a_subject_id, "base_a"),
            (self.base_material_b_subject_id, "base_b"),
        ):
            if required_subject not in materials or materials[required_subject].material_role != role:
                raise ValueError("base-material subjects must map to their declared A/B roles")
        layer_ids = {row.layer_id for row in self.layers}
        positions = [row.sequence_position for row in self.layers]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("dissimilar-weld layers require consecutive sequence positions")
        if any(row.material_subject_id not in materials for row in self.layers):
            raise ValueError("every dissimilar-weld layer must reference material evidence")
        boundary_ids = {row.boundary_region_id for row in self.fusion_boundaries}
        if {row.side for row in self.fusion_boundaries} != {"base_a", "base_b"}:
            raise ValueError("fusion boundaries must include both base-material sides")
        for row in self.fusion_boundaries:
            expected_base = (
                self.base_material_a_subject_id if row.side == "base_a" else self.base_material_b_subject_id
            )
            if row.base_material_subject_id != expected_base or row.adjacent_layer_id not in layer_ids:
                raise ValueError("fusion-boundary side and adjacent-layer links must be exact")
            if (
                row.joint_location_id != self.joint_location_id
                or row.coordinate_frame_id != self.coordinate_frame_id
            ):
                raise ValueError("fusion boundaries must use the declared joint location and frame")
        for row in self.transition_measurements:
            if (
                row.boundary_region_id not in boundary_ids
                or row.coordinate_frame_id != self.coordinate_frame_id
            ):
                raise ValueError("transition measurements must map to a boundary in the declared frame")
        for first, second in zip(self.thermal_history, self.thermal_history[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("dissimilar-weld thermal intervals must be ordered and cannot overlap")
        known_review_subjects = {row.review_subject_id for row in self.compatibility_reviews}
        if {row.review_subject_id for row in self.unresolved_items} - known_review_subjects:
            raise ValueError("unresolved items must reference declared compatibility-review subjects")
        return self


def dissimilar_weld_applicability_evidence(
    x: DissimilarWeldApplicabilityEvidence,
) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "joint_material_layer_and_boundary_identity_reviewed",
            "location_coordinate_frame_and_region_mapping_reviewed",
            "procedure_pwht_and_thermal_history_reviewed",
            "service_environment_identity_reviewed",
            "composition_property_provider_lineage_reviewed",
            "transition_measurement_definitions_units_and_uncertainty_reviewed",
            "compatibility_review_authority_and_scope_reviewed",
            "unresolved_item_completeness_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_material_subject_ids = [
        row.material_subject_id for row in x.material_evidence if not row.record_valid
    ]
    invalid_thermal_interval_ids = [row.interval_id for row in x.thermal_history if not row.record_valid]
    invalid_measurement_ids = [
        row.measurement_id for row in x.transition_measurements if not row.record_valid
    ]
    review_by_subject = {row.review_subject_id: row for row in x.compatibility_reviews}
    missing_review_subject_ids = [
        subject_id for subject_id in x.required_review_subject_ids if subject_id not in review_by_subject
    ]
    unresolved_review_subject_ids = [
        row.review_subject_id for row in x.compatibility_reviews if row.review_status == "unresolved"
    ]
    out_of_scope_review_subject_ids = [
        row.review_subject_id
        for row in x.compatibility_reviews
        if row.review_status == "reviewed_out_of_scope"
    ]
    limited_review_subject_ids = [
        row.review_subject_id for row in x.compatibility_reviews if row.review_status == "reviewed_limited"
    ]
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "joint_id": x.joint_id,
        "joint_location_id": x.joint_location_id,
        "coordinate_frame_id": x.coordinate_frame_id,
        "service_environment_id": x.service_environment_id,
        "base_material_subject_ids": [
            x.base_material_a_subject_id,
            x.base_material_b_subject_id,
        ],
        "layer_sequence": [
            {
                "layer_id": row.layer_id,
                "layer_role": row.layer_role,
                "applied_side": row.applied_side,
                "material_subject_id": row.material_subject_id,
                "welding_procedure_id": row.welding_procedure_id,
                "welding_procedure_revision": row.welding_procedure_revision,
            }
            for row in x.layers
        ],
        "fusion_boundary_ids_by_side": {row.side: row.boundary_region_id for row in x.fusion_boundaries},
        "thermal_interval_ids": [row.interval_id for row in x.thermal_history],
        "transition_measurements": [
            {
                "measurement_id": row.measurement_id,
                "boundary_region_id": row.boundary_region_id,
                "measurement_kind": row.measurement_kind,
                "metric_definition": row.metric_definition,
                "value": row.value,
                "unit_token": row.unit_token,
                "expanded_uncertainty": row.expanded_uncertainty,
                "method_id": row.method_id,
                "provider_id": row.provider_id,
                "provider_revision": row.provider_revision,
                "provider_configuration_digest": row.provider_configuration_digest,
                "result_digest": row.result_digest,
            }
            for row in x.transition_measurements
        ],
        "missing_required_review_subject_ids": missing_review_subject_ids,
        "unresolved_review_subject_ids": unresolved_review_subject_ids,
        "limited_review_subject_ids": limited_review_subject_ids,
        "out_of_scope_review_subject_ids": out_of_scope_review_subject_ids,
        "unresolved_items": [row.model_dump(mode="json") for row in x.unresolved_items],
        "invalid_material_subject_ids": invalid_material_subject_ids,
        "invalid_thermal_interval_ids": invalid_thermal_interval_ids,
        "invalid_transition_measurement_ids": invalid_measurement_ids,
        "missing_reviews": missing_reviews,
    }
    notes = (
        "Compatibility review outcomes, limitations and unresolved items are caller-owned records; no alloy pairing or code rule is embedded.",
        "Dilution, transition-zone, composition and property measurements retain their reported definitions, units, uncertainty and provider digests.",
        "A computed reconciliation is not weld acceptance and does not predict cracking, property evolution, remaining life or failure probability.",
    )
    if (
        missing_reviews
        or invalid_material_subject_ids
        or invalid_thermal_interval_ids
        or invalid_measurement_ids
        or missing_review_subject_ids
        or unresolved_review_subject_ids
        or x.unresolved_items
    ):
        return Calculation(status="needs_data", values=values, notes=notes)
    if out_of_scope_review_subject_ids:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["review_record_reconciliation"] = "complete"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("dissimilar-weld assessment asset and location must match run context")

    return [
        ModelSpec(
            "welding.dissimilar_weld_applicability_evidence",
            DissimilarWeldApplicabilityEvidence,
            dissimilar_weld_applicability_evidence,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "joint_id": "1",
                "joint_location_id": "1",
                "coordinate_frame_id": "1",
                "service_environment_id": "1",
                "base_material_subject_ids": "1",
                "layer_sequence": "mixed",
                "fusion_boundary_ids_by_side": "1",
                "thermal_interval_ids": "1",
                "transition_measurements": "mixed",
                "missing_required_review_subject_ids": "1",
                "unresolved_review_subject_ids": "1",
                "limited_review_subject_ids": "1",
                "out_of_scope_review_subject_ids": "1",
                "unresolved_items": "mixed",
                "invalid_material_subject_ids": "1",
                "invalid_thermal_interval_ids": "1",
                "invalid_transition_measurement_ids": "1",
                "missing_reviews": "1",
                "review_record_reconciliation": "1",
            },
            (
                "Base A/B, deposited layers, fusion-boundary sides, procedures, thermal history and service environment retain exact identities.",
                "Compatibility outcomes and unresolved items are caller-reviewed records, not inferred alloy rules.",
                "A complete evidence reconciliation is not acceptance, life or failure-probability qualification.",
            ),
            ("authored_dissimilar_weld_review_reconciliation",),
            context_validator=same_identity,
        )
    ]
