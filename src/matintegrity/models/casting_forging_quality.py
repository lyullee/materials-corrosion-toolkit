"""Casting and forging quality evidence without embedded acceptance rules."""

from __future__ import annotations

from collections import defaultdict

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class HeatTreatmentRecord(Contract):
    treatment_id: str = Field(min_length=1)
    treatment_type: str = Field(min_length=1)
    start_time_s: Nonnegative | None = None
    end_time_s: Positive | None = None
    minimum_recorded_temperature_K: Positive | None = None
    maximum_recorded_temperature_K: Positive | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_record(self):
        fields = (
            self.start_time_s,
            self.end_time_s,
            self.minimum_recorded_temperature_K,
            self.maximum_recorded_temperature_K,
        )
        if self.record_valid and any(value is None for value in fields):
            raise ValueError("a valid heat-treatment record requires time and temperature bounds")
        if self.record_valid and self.end_time_s <= self.start_time_s:
            raise ValueError("heat-treatment record must have positive duration")
        if self.record_valid and self.maximum_recorded_temperature_K < self.minimum_recorded_temperature_K:
            raise ValueError("heat-treatment temperature bounds must be ordered")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid heat-treatment record requires an invalid-record basis")
        return self


class QualityInspectionRegion(Contract):
    region_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    examination_method_id: str = Field(min_length=1)
    target_extent: Positive
    examined_extent: Nonnegative
    extent_unit: str = Field(min_length=1)
    record_valid: bool
    unexamined_basis: str | None = None
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_extent(self):
        if self.examined_extent > self.target_extent:
            raise ValueError("examined extent cannot exceed target extent")
        if self.examined_extent < self.target_extent and not self.unexamined_basis:
            raise ValueError("incomplete inspection coverage requires an unexamined basis")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid inspection region requires an invalid-record basis")
        return self


class QualityObservation(Contract):
    observation_id: str = Field(min_length=1)
    region_id: str = Field(min_length=1)
    reported_indication_type: str = Field(min_length=1)
    measurement_definition: str | None = None
    measured_value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit: str | None = None
    caller_limit_id: str | None = None
    caller_reported_disposition_id: str | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_measurement(self):
        measurement_fields = (self.measurement_definition, self.expanded_uncertainty, self.unit)
        if self.measured_value is None and any(value is not None for value in measurement_fields):
            raise ValueError("measurement metadata requires a measured value")
        if self.measured_value is not None and any(value is None for value in measurement_fields):
            raise ValueError("a measured value requires definition, expanded uncertainty and unit")
        if self.caller_limit_id is not None and self.measured_value is None:
            raise ValueError("a caller limit mapping requires a measured value")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid quality observation requires an invalid-record basis")
        return self


class CallerQualityLimit(Contract):
    limit_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    minimum_value: float | None = None
    maximum_value: float | None = None
    limit_basis: str = Field(min_length=1)
    caller_disposition_id_if_outside: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_limit(self):
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("a caller quality limit requires at least one bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("caller quality limit bounds must be ordered")
        return self


class CastingForgingQualityRecord(Contract):
    record_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    heat_id: str = Field(min_length=1)
    manufacturing_route_id: str = Field(min_length=1)
    manufacturing_route_description: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_treatments: list[HeatTreatmentRecord] = Field(default_factory=list)
    inspection_regions: list[QualityInspectionRegion] = Field(min_length=1)
    observations: list[QualityObservation] = Field(default_factory=list)
    caller_limits: list[CallerQualityLimit] = Field(default_factory=list)
    component_heat_and_route_reviewed: bool
    heat_treatment_history_reviewed: bool
    inspection_region_mapping_reviewed: bool
    examination_coverage_reviewed: bool
    indication_classification_reviewed: bool
    measurement_units_and_uncertainty_reviewed: bool
    caller_limit_mapping_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_identities(self):
        treatment_ids = [row.treatment_id for row in self.heat_treatments]
        region_ids = [row.region_id for row in self.inspection_regions]
        observation_ids = [row.observation_id for row in self.observations]
        limit_ids = [row.limit_id for row in self.caller_limits]
        for values, name in (
            (treatment_ids, "heat-treatment"),
            (region_ids, "inspection region"),
            (observation_ids, "quality observation"),
            (limit_ids, "caller quality limit"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{name} IDs must be unique")
        if {row.region_id for row in self.observations} - set(region_ids):
            raise ValueError("every quality observation must reference a declared inspection region")
        return self


def casting_forging_quality_record(x: CastingForgingQualityRecord) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "component_heat_and_route_reviewed",
            "heat_treatment_history_reviewed",
            "inspection_region_mapping_reviewed",
            "examination_coverage_reviewed",
            "indication_classification_reviewed",
            "measurement_units_and_uncertainty_reviewed",
            "caller_limit_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
    coverage_by_unit = defaultdict(lambda: {"target_extent": 0.0, "examined_extent": 0.0})
    for region in x.inspection_regions:
        coverage_by_unit[region.extent_unit]["target_extent"] += region.target_extent
        coverage_by_unit[region.extent_unit]["examined_extent"] += region.examined_extent
    coverage_rows = []
    for unit, totals in sorted(coverage_by_unit.items()):
        coverage_rows.append(
            {
                "extent_unit": unit,
                **totals,
                "unexamined_extent": totals["target_extent"] - totals["examined_extent"],
                "coverage_fraction": totals["examined_extent"] / totals["target_extent"],
            }
        )

    limits = {row.limit_id: row for row in x.caller_limits}
    missing_limit_mapping = []
    unknown_limit_mapping = []
    limit_definition_mismatch = []
    limit_unit_mismatch = []
    comparison_rows = []
    for observation in x.observations:
        if not observation.record_valid or observation.measured_value is None:
            continue
        if observation.caller_limit_id is None:
            missing_limit_mapping.append(observation.observation_id)
            continue
        limit = limits.get(observation.caller_limit_id)
        if limit is None:
            unknown_limit_mapping.append(observation.observation_id)
            continue
        if observation.measurement_definition != limit.metric_definition:
            limit_definition_mismatch.append(observation.observation_id)
            continue
        if observation.unit != limit.unit:
            limit_unit_mismatch.append(observation.observation_id)
            continue
        low = observation.measured_value - observation.expanded_uncertainty
        high = observation.measured_value + observation.expanded_uncertainty
        nominal_below = limit.minimum_value is not None and observation.measured_value < limit.minimum_value
        nominal_above = limit.maximum_value is not None and observation.measured_value > limit.maximum_value
        interval_below = limit.minimum_value is not None and low < limit.minimum_value
        interval_above = limit.maximum_value is not None and high > limit.maximum_value
        comparison_rows.append(
            {
                "observation_id": observation.observation_id,
                "limit_id": limit.limit_id,
                "reported_value": observation.measured_value,
                "expanded_uncertainty": observation.expanded_uncertainty,
                "uncertainty_interval_minimum": low,
                "uncertainty_interval_maximum": high,
                "unit": observation.unit,
                "nominal_below_declared_minimum": nominal_below,
                "nominal_above_declared_maximum": nominal_above,
                "uncertainty_interval_extends_below_declared_minimum": interval_below,
                "uncertainty_interval_extends_above_declared_maximum": interval_above,
                "caller_disposition_id_if_outside": limit.caller_disposition_id_if_outside,
            }
        )

    invalid_treatments = [row.treatment_id for row in x.heat_treatments if not row.record_valid]
    invalid_regions = [row.region_id for row in x.inspection_regions if not row.record_valid]
    invalid_observations = [row.observation_id for row in x.observations if not row.record_valid]
    incomplete = (
        missing_reviews
        or invalid_treatments
        or invalid_regions
        or invalid_observations
        or missing_limit_mapping
        or unknown_limit_mapping
        or limit_definition_mismatch
        or limit_unit_mismatch
    )
    return Calculation(
        status="needs_data" if incomplete else "computed",
        values={
            "record_id": x.record_id,
            "component_id": x.component_id,
            "heat_id": x.heat_id,
            "manufacturing_route_id": x.manufacturing_route_id,
            "material_condition_id": x.material_condition_id,
            "heat_treatment_record_count": len(x.heat_treatments),
            "invalid_heat_treatment_ids": invalid_treatments,
            "inspection_region_count": len(x.inspection_regions),
            "coverage_by_extent_unit": coverage_rows,
            "incomplete_coverage_region_ids": [
                row.region_id for row in x.inspection_regions if row.examined_extent < row.target_extent
            ],
            "invalid_inspection_region_ids": invalid_regions,
            "observation_count": len(x.observations),
            "invalid_observation_ids": invalid_observations,
            "reported_indication_types": sorted({row.reported_indication_type for row in x.observations}),
            "missing_limit_mapping_observation_ids": missing_limit_mapping,
            "unknown_limit_mapping_observation_ids": unknown_limit_mapping,
            "limit_definition_mismatch_observation_ids": limit_definition_mismatch,
            "limit_unit_mismatch_observation_ids": limit_unit_mismatch,
            "caller_limit_comparisons": comparison_rows,
            "caller_reported_disposition_ids": [
                row.caller_reported_disposition_id
                for row in x.observations
                if row.caller_reported_disposition_id is not None
            ],
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Inspection coverage, reported indication labels and measured quantities are evidence records, not defect classifications or acceptance decisions.",
            "Uncertainty intervals are caller-supplied measurement bounds; their overlap with a caller limit does not establish acceptability or criticality.",
            "No specification table, fracture calculation, damage rate, remaining life or failure probability is embedded.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("casting/forging quality asset and location must match the assessment context")

    return [
        ModelSpec(
            "materials.casting_forging_quality_record",
            CastingForgingQualityRecord,
            casting_forging_quality_record,
            {
                "heat_treatment_record_count": "count",
                "inspection_region_count": "count",
                "observation_count": "count",
            },
            (
                "Component, heat, manufacturing route, heat treatment, inspection coverage, observations and caller limits retain separate identities and evidence.",
                "Invalid records and missing or inconsistent caller-limit mappings prevent a complete evidence summary without inventing replacements.",
            ),
            ("casting_forging_quality_evidence_accounting",),
            context_validator=same_identity,
        )
    ]
