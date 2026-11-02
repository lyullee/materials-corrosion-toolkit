"""Heat-exchanger geometry manifests with caller-owned provider support."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class TubeLayoutManifest(Contract):
    bundle_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_unit_token: str = Field(min_length=1)
    coordinate_component_order: tuple[str, str]
    tube_ordering_definition: str = Field(min_length=1)
    tube_count: int = Field(ge=1)
    layout_pattern_descriptor: str = Field(min_length=1)
    pitch_m: Positive
    tube_outer_diameter_m: Positive
    tube_wall_thickness_m: Positive
    tube_length_m: Positive
    coordinate_array_shape: tuple[int, int]
    coordinate_payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_layout(self):
        if self.tube_wall_thickness_m * 2 >= self.tube_outer_diameter_m:
            raise ValueError("tube wall thickness must leave positive inside diameter")
        if self.coordinate_array_shape != (self.tube_count, 2):
            raise ValueError("tube coordinate array shape must equal tube_count by two")
        if len(set(self.coordinate_component_order)) != 2:
            raise ValueError("tube coordinate component order must contain two unique components")
        return self


class TubesheetGeometryRecord(Contract):
    tubesheet_id: str = Field(min_length=1)
    axial_coordinate_m: float
    outer_diameter_m: Positive
    thickness_m: Positive
    tube_hole_count: int = Field(ge=1)
    material_condition_id: str = Field(min_length=1)
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_record_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid tubesheet record requires a basis")
        return self


class BaffleGeometryRecord(Contract):
    baffle_id: str = Field(min_length=1)
    axial_coordinate_m: float
    baffle_type_descriptor: str = Field(min_length=1)
    outer_diameter_m: Positive
    thickness_m: Positive
    cut_or_open_fraction: Nonnegative
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_fraction_and_basis(self):
        if self.cut_or_open_fraction > 1:
            raise ValueError("baffle cut or open fraction cannot exceed one")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid baffle record requires a basis")
        return self


class GeometryProviderEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    observed_value: float
    provider_value: float
    expanded_uncertainty: Nonnegative
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def invalid_evidence_basis(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid geometry-provider evidence requires a basis")
        return self


class GeometryMetricSupport(Contract):
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    maximum_absolute_difference: Nonnegative
    minimum_record_count: int = Field(ge=1)
    support_basis: str = Field(min_length=1)


class DeclaredHeatExchangerGeometryEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    shell_geometry_id: str = Field(min_length=1)
    shell_material_condition_id: str = Field(min_length=1)
    supported_layout_pattern_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_baffle_type_descriptors: tuple[str, ...] = Field(min_length=1)
    minimum_shell_inside_diameter_m: Positive
    maximum_shell_inside_diameter_m: Positive
    minimum_shell_length_m: Positive
    maximum_shell_length_m: Positive
    minimum_tube_count: int = Field(ge=1)
    maximum_tube_count: int = Field(ge=1)
    minimum_baffle_count: int = Field(ge=0)
    maximum_baffle_count: int = Field(ge=0)
    metric_support: tuple[GeometryMetricSupport, ...] = Field(min_length=1)
    minimum_source_group_count: int = Field(ge=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_shell_inside_diameter_m < self.minimum_shell_inside_diameter_m:
            raise ValueError("shell diameter support must be ordered")
        if self.maximum_shell_length_m < self.minimum_shell_length_m:
            raise ValueError("shell length support must be ordered")
        if self.maximum_tube_count < self.minimum_tube_count:
            raise ValueError("tube-count support must be ordered")
        if self.maximum_baffle_count < self.minimum_baffle_count:
            raise ValueError("baffle-count support must be ordered")
        ids = [row.metric_id for row in self.metric_support]
        if len(ids) != len(set(ids)):
            raise ValueError("geometry metric support IDs must be unique")
        return self


class HeatExchangerGeometryAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    exchanger_id: str = Field(min_length=1)
    shell_geometry_id: str = Field(min_length=1)
    shell_material_condition_id: str = Field(min_length=1)
    shell_inside_diameter_m: Positive
    shell_length_m: Positive
    tube_layout: TubeLayoutManifest
    tubesheets: tuple[TubesheetGeometryRecord, ...] = Field(min_length=1)
    baffles: tuple[BaffleGeometryRecord, ...]
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_evidence: tuple[GeometryProviderEvidence, ...] = Field(min_length=1)
    candidate_envelopes: tuple[DeclaredHeatExchangerGeometryEnvelope, ...] = Field(min_length=1)
    exchanger_shell_bundle_and_coordinate_frame_reviewed: bool
    tube_layout_shape_order_units_and_digest_reviewed: bool
    tubesheet_and_baffle_geometry_reviewed: bool
    material_condition_and_geometry_units_reviewed: bool
    provider_revision_configuration_input_and_result_reviewed: bool
    qualification_specimens_partitions_and_uncertainty_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_geometry(self):
        if self.tube_layout.bundle_id == "":
            raise ValueError("tube bundle identity is required")
        for rows, attribute, label in (
            (self.tubesheets, "tubesheet_id", "tubesheet"),
            (self.baffles, "baffle_id", "baffle"),
            (self.qualification_evidence, "evidence_record_id", "geometry evidence"),
            (self.candidate_envelopes, "envelope_id", "geometry envelope"),
        ):
            values = [getattr(row, attribute) for row in rows]
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        coordinates = [row.axial_coordinate_m for row in self.baffles]
        if coordinates != sorted(coordinates):
            raise ValueError("baffles must be supplied in axial order")
        return self


def heat_exchanger_geometry_evidence(x: HeatExchangerGeometryAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "exchanger_shell_bundle_and_coordinate_frame_reviewed",
            "tube_layout_shape_order_units_and_digest_reviewed",
            "tubesheet_and_baffle_geometry_reviewed",
            "material_condition_and_geometry_units_reviewed",
            "provider_revision_configuration_input_and_result_reviewed",
            "qualification_specimens_partitions_and_uncertainty_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_tubesheet_ids = [row.tubesheet_id for row in x.tubesheets if not row.record_valid]
    invalid_baffle_ids = [row.baffle_id for row in x.baffles if not row.record_valid]
    invalid_evidence_ids = [
        row.evidence_record_id for row in x.qualification_evidence if not row.record_valid
    ]
    matching = [
        envelope
        for envelope in x.candidate_envelopes
        if envelope.shell_geometry_id == x.shell_geometry_id
        and envelope.shell_material_condition_id == x.shell_material_condition_id
        and envelope.provider_id == x.provider_id
        and envelope.provider_version == x.provider_version
        and envelope.provider_state_digest == x.provider_state_digest
    ]
    if (
        missing_reviews
        or invalid_tubesheet_ids
        or invalid_baffle_ids
        or invalid_evidence_ids
        or len(matching) != 1
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in matching],
                "invalid_tubesheet_ids": invalid_tubesheet_ids,
                "invalid_baffle_ids": invalid_baffle_ids,
                "invalid_qualification_evidence_ids": invalid_evidence_ids,
                "missing_reviews": missing_reviews,
            },
            notes=("One exact provider envelope and complete valid reviewed geometry records are required.",),
        )

    envelope = matching[0]
    outside_reasons = []
    if x.tube_layout.layout_pattern_descriptor not in envelope.supported_layout_pattern_descriptors:
        outside_reasons.append("layout_pattern_descriptor")
    if any(row.baffle_type_descriptor not in envelope.supported_baffle_type_descriptors for row in x.baffles):
        outside_reasons.append("baffle_type_descriptor")
    if not (
        envelope.minimum_shell_inside_diameter_m
        <= x.shell_inside_diameter_m
        <= envelope.maximum_shell_inside_diameter_m
    ):
        outside_reasons.append("shell_inside_diameter")
    if not envelope.minimum_shell_length_m <= x.shell_length_m <= envelope.maximum_shell_length_m:
        outside_reasons.append("shell_length")
    if not envelope.minimum_tube_count <= x.tube_layout.tube_count <= envelope.maximum_tube_count:
        outside_reasons.append("tube_count")
    if not envelope.minimum_baffle_count <= len(x.baffles) <= envelope.maximum_baffle_count:
        outside_reasons.append("baffle_count")

    metric_counts = {}
    metric_comparisons = []
    unsupported_evidence_ids = []
    outside_evidence_ids = []
    support_by_metric = {row.metric_id: row for row in envelope.metric_support}
    for row in x.qualification_evidence:
        support = support_by_metric.get(row.metric_id)
        if support is None or row.unit_token != support.unit_token:
            unsupported_evidence_ids.append(row.evidence_record_id)
            continue
        difference = abs(row.provider_value - row.observed_value)
        within = difference <= support.maximum_absolute_difference
        metric_counts[row.metric_id] = metric_counts.get(row.metric_id, 0) + 1
        if not within:
            outside_evidence_ids.append(row.evidence_record_id)
        metric_comparisons.append(
            {
                "evidence_record_id": row.evidence_record_id,
                "metric_id": row.metric_id,
                "absolute_difference": difference,
                "within_declared_support": within,
            }
        )
    missing_metric_ids = [
        support.metric_id
        for support in envelope.metric_support
        if metric_counts.get(support.metric_id, 0) < support.minimum_record_count
    ]
    source_group_count = len({row.source_group_id for row in x.qualification_evidence})
    if (
        unsupported_evidence_ids
        or missing_metric_ids
        or source_group_count < envelope.minimum_source_group_count
    ):
        status = "needs_data"
        outcome = "evidence_incomplete"
    elif outside_reasons or outside_evidence_ids:
        status = "out_of_scope"
        outcome = "outside_declared_support"
    else:
        status = "computed"
        outcome = "within_support"
    return Calculation(
        status=status,
        values={
            "assessment_id": x.assessment_id,
            "exchanger_id": x.exchanger_id,
            "bundle_id": x.tube_layout.bundle_id,
            "selected_envelope_id": envelope.envelope_id,
            "declared_geometry_outcome": outcome,
            "tube_count": x.tube_layout.tube_count,
            "tubesheet_count": len(x.tubesheets),
            "baffle_count": len(x.baffles),
            "outside_geometry_support_reasons": outside_reasons,
            "metric_comparisons": metric_comparisons,
            "unsupported_qualification_evidence_ids": unsupported_evidence_ids,
            "missing_metric_ids": missing_metric_ids,
            "outside_support_evidence_ids": outside_evidence_ids,
            "qualification_source_group_count": source_group_count,
            "missing_reviews": [],
        },
        notes=(
            "Tube coordinates remain an external digest-bound payload; no coordinates are inferred from counts or pattern names.",
            "Geometry, provider and metric support are caller-owned and are not extrapolated.",
            "This exchange does not calculate flow, vibration, heat transfer, stress, structural capacity, acceptance, life, or probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("heat-exchanger geometry asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.heat_exchanger_geometry_evidence",
            HeatExchangerGeometryAssessment,
            heat_exchanger_geometry_evidence,
            {
                "assessment_id": "1",
                "exchanger_id": "1",
                "bundle_id": "1",
                "selected_envelope_id": "1",
                "declared_geometry_outcome": "1",
                "tube_count": "count",
                "tubesheet_count": "count",
                "baffle_count": "count",
                "outside_geometry_support_reasons": "1",
                "metric_comparisons": "mixed",
                "unsupported_qualification_evidence_ids": "1",
                "missing_metric_ids": "1",
                "outside_support_evidence_ids": "1",
                "qualification_source_group_count": "count",
                "missing_reviews": "1",
            },
            (
                "Exchanger, shell, bundle, coordinate frame, units, ordering and payload digests are caller reviewed.",
                "Tubesheet, baffle and tube geometry plus provider revision and support are caller-owned.",
                "Qualification evidence preserves physical specimens, source groups, partitions, methods and uncertainty.",
            ),
            ("reviewed_heat_exchanger_geometry_provider_envelope",),
            context_validator=same_identity,
        )
    ]
