"""Test-water observations compared with a caller-controlled material envelope."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class TestWaterSample(Contract):
    sample_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    sample_time_s: Nonnegative
    temperature_K: Positive
    pH: float = Field(ge=0, le=14)
    conductivity_S_m: Nonnegative
    chloride_kg_m3: Nonnegative
    measurement_method_id: str = Field(min_length=1)
    record_valid: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class TestWaterEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pH: float = Field(ge=0, le=14)
    maximum_pH: float = Field(ge=0, le=14)
    minimum_conductivity_S_m: Nonnegative
    maximum_conductivity_S_m: Nonnegative
    minimum_chloride_kg_m3: Nonnegative
    maximum_chloride_kg_m3: Nonnegative
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_bounds(self):
        for lower, upper, name in (
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_pH, self.maximum_pH, "pH"),
            (self.minimum_conductivity_S_m, self.maximum_conductivity_S_m, "conductivity"),
            (self.minimum_chloride_kg_m3, self.maximum_chloride_kg_m3, "chloride"),
        ):
            if upper < lower:
                raise ValueError(f"{name} envelope bounds must be ordered")
        return self


class TestWaterQualityRecord(Contract):
    record_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    test_start_time_s: Nonnegative
    test_end_time_s: Positive
    required_location_ids: tuple[str, ...] = Field(min_length=1)
    maximum_sampling_gap_s: Positive
    samples: tuple[TestWaterSample, ...] = Field(min_length=1)
    envelope: TestWaterEnvelope
    sampling_plan_reviewed: bool
    sample_identity_and_location_reviewed: bool
    clock_and_units_reviewed: bool
    measurement_methods_reviewed: bool
    material_envelope_reviewed: bool
    record_completeness_reviewed: bool

    @model_validator(mode="after")
    def identities_and_clock(self):
        if self.test_end_time_s <= self.test_start_time_s:
            raise ValueError("test interval must have positive duration")
        if len(self.required_location_ids) != len(set(self.required_location_ids)):
            raise ValueError("required water-sampling locations must be unique")
        if any(not identifier.strip() for identifier in self.required_location_ids):
            raise ValueError("sampling location identifiers cannot be blank")
        sample_ids = [sample.sample_id for sample in self.samples]
        if len(sample_ids) != len(set(sample_ids)):
            raise ValueError("water sample identifiers must be unique")
        if any(
            sample.sample_time_s < self.test_start_time_s or sample.sample_time_s > self.test_end_time_s
            for sample in self.samples
        ):
            raise ValueError("water sample time must lie inside the declared test interval")
        if self.envelope.material_condition_id != self.material_condition_id:
            raise ValueError("water-quality envelope must identify the tested material condition")
        return self


def test_water_quality(x: TestWaterQualityRecord) -> Calculation:
    missing_reviews = [
        name
        for name, value in (
            ("sampling_plan", x.sampling_plan_reviewed),
            ("sample_identity_and_location", x.sample_identity_and_location_reviewed),
            ("clock_and_units", x.clock_and_units_reviewed),
            ("measurement_methods", x.measurement_methods_reviewed),
            ("material_envelope", x.material_envelope_reviewed),
            ("record_completeness", x.record_completeness_reviewed),
        )
        if not value
    ]
    invalid_sample_ids = [sample.sample_id for sample in x.samples if not sample.record_valid]
    observed_locations = {sample.location_id for sample in x.samples}
    missing_locations = [
        location for location in x.required_location_ids if location not in observed_locations
    ]

    coverage_rows = []
    insufficient_locations = []
    for location in x.required_location_ids:
        times = sorted(sample.sample_time_s for sample in x.samples if sample.location_id == location)
        if not times:
            continue
        boundaries = [x.test_start_time_s, *times, x.test_end_time_s]
        maximum_gap = max(second - first for first, second in zip(boundaries, boundaries[1:], strict=False))
        sufficient = maximum_gap <= x.maximum_sampling_gap_s
        if not sufficient:
            insufficient_locations.append(location)
        coverage_rows.append(
            {
                "location_id": location,
                "sample_count": len(times),
                "maximum_sampling_gap_s": maximum_gap,
                "coverage_sufficient": sufficient,
            }
        )

    if missing_reviews or invalid_sample_ids or missing_locations or insufficient_locations:
        return Calculation(
            status="needs_data",
            values={
                "record_id": x.record_id,
                "missing_reviews": missing_reviews,
                "invalid_sample_ids": invalid_sample_ids,
                "missing_location_ids": missing_locations,
                "insufficient_coverage_location_ids": insufficient_locations,
                "coverage": coverage_rows,
            },
            notes=(
                "Water-quality comparison is withheld until sample validity, coverage and review gates are complete.",
            ),
        )

    comparisons = []
    violating_sample_ids = []
    for sample in x.samples:
        violations = []
        if not x.envelope.minimum_temperature_K <= sample.temperature_K <= x.envelope.maximum_temperature_K:
            violations.append("temperature")
        if not x.envelope.minimum_pH <= sample.pH <= x.envelope.maximum_pH:
            violations.append("pH")
        if not (
            x.envelope.minimum_conductivity_S_m
            <= sample.conductivity_S_m
            <= x.envelope.maximum_conductivity_S_m
        ):
            violations.append("conductivity")
        if not (
            x.envelope.minimum_chloride_kg_m3 <= sample.chloride_kg_m3 <= x.envelope.maximum_chloride_kg_m3
        ):
            violations.append("chloride")
        if violations:
            violating_sample_ids.append(sample.sample_id)
        comparisons.append(
            {
                "sample_id": sample.sample_id,
                "location_id": sample.location_id,
                "sample_time_s": sample.sample_time_s,
                "violations": violations,
                "within_declared_envelope": not violations,
            }
        )

    return Calculation(
        values={
            "record_id": x.record_id,
            "coverage": coverage_rows,
            "sample_comparisons": comparisons,
            "violating_sample_ids": violating_sample_ids,
            "observed_temperature_range_K": [
                min(sample.temperature_K for sample in x.samples),
                max(sample.temperature_K for sample in x.samples),
            ],
            "observed_pH_range": [
                min(sample.pH for sample in x.samples),
                max(sample.pH for sample in x.samples),
            ],
            "observed_conductivity_range_S_m": [
                min(sample.conductivity_S_m for sample in x.samples),
                max(sample.conductivity_S_m for sample in x.samples),
            ],
            "observed_chloride_range_kg_m3": [
                min(sample.chloride_kg_m3 for sample in x.samples),
                max(sample.chloride_kg_m3 for sample in x.samples),
            ],
            "declared_envelope_outcome": "within" if not violating_sample_ids else "outside",
        },
        notes=(
            "The outcome is a comparison with a caller-owned envelope and is not a test or material acceptance decision.",
            "No corrosion rate, microbial activity, deposit chemistry, local concentration or future condition is inferred.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.test_water_quality_summary",
            TestWaterQualityRecord,
            test_water_quality,
            {
                "record_id": "1",
                "coverage": "1",
                "sample_comparisons": "1",
                "violating_sample_ids": "1",
                "observed_temperature_range_K": "K",
                "observed_pH_range": "1",
                "observed_conductivity_range_S_m": "S/m",
                "observed_chloride_range_kg_m3": "kg/m^3",
                "declared_envelope_outcome": "1",
            },
            (
                "Samples retain explicit location, time, method and evidence identities on one reviewed test clock.",
                "Coverage and property limits are caller-owned inputs; no regulatory or material limit is embedded.",
                "Observed sample properties are not interpolated between sampling events.",
            ),
            ("declared_test_water_envelope",),
        )
    ]
