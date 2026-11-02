"""Microbial sampling evidence without corrosion-causality inference."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class MicrobialSample(Contract):
    sample_id: str = Field(min_length=1)
    sampling_location_id: str = Field(min_length=1)
    sample_time_s: Nonnegative
    sample_matrix: str = Field(min_length=1)
    collection_method_id: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_record(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid microbial sample requires an invalid-record basis")
        return self


class MicrobialAssay(Contract):
    assay_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    result_qualifier: Literal["quantified", "below_detection", "not_reported"]
    reported_value: Nonnegative | None = None
    unit: str = Field(min_length=1)
    detection_limit: Positive
    caller_indicator_id: str | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_result(self):
        if self.record_valid and self.result_qualifier == "quantified" and self.reported_value is None:
            raise ValueError("a quantified assay requires a reported value")
        if self.result_qualifier == "below_detection" and self.reported_value is not None:
            raise ValueError("a below-detection assay must preserve censoring rather than report a value")
        if self.record_valid and self.result_qualifier == "not_reported":
            raise ValueError("a not-reported assay cannot be marked valid")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid microbial assay requires an invalid-record basis")
        return self


class WaterContextObservation(Contract):
    observation_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    parameter_id: str = Field(min_length=1)
    reported_value: float | None = None
    unit: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_result(self):
        if self.record_valid and self.reported_value is None:
            raise ValueError("a valid water-context observation requires a value")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid water-context observation requires an invalid-record basis")
        return self


class BiofilmDepositObservation(Contract):
    observation_id: str = Field(min_length=1)
    sample_id: str = Field(min_length=1)
    observation_method_id: str = Field(min_length=1)
    reported_description: str = Field(min_length=1)
    metric_id: str | None = None
    reported_value: Nonnegative | None = None
    unit: str | None = None
    record_valid: bool
    invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_metric(self):
        metric_fields = (self.metric_id, self.reported_value, self.unit)
        if any(value is not None for value in metric_fields) and any(
            value is None for value in metric_fields
        ):
            raise ValueError("biofilm/deposit metric ID, value and unit must be supplied together")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid biofilm/deposit observation requires an invalid-record basis")
        return self


class CallerMicrobialIndicator(Contract):
    indicator_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    minimum_value: Nonnegative | None = None
    maximum_value: Nonnegative | None = None
    definition_basis: str = Field(min_length=1)
    caller_disposition_id_if_outside: str = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_indicator(self):
        if self.minimum_value is None and self.maximum_value is None:
            raise ValueError("a caller microbial indicator requires at least one bound")
        if (
            self.minimum_value is not None
            and self.maximum_value is not None
            and self.maximum_value < self.minimum_value
        ):
            raise ValueError("caller microbial indicator bounds must be ordered")
        return self


class MicrobialCampaign(Contract):
    campaign_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    site_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    samples: list[MicrobialSample] = Field(min_length=1)
    assays: list[MicrobialAssay] = Field(default_factory=list)
    water_context: list[WaterContextObservation] = Field(default_factory=list)
    biofilm_deposit_observations: list[BiofilmDepositObservation] = Field(default_factory=list)
    caller_indicators: list[CallerMicrobialIndicator] = Field(default_factory=list)
    required_sampling_location_ids: list[str] = Field(default_factory=list)
    required_assay_target_ids: list[str] = Field(default_factory=list)
    required_water_context_parameter_ids: list[str] = Field(default_factory=list)
    biofilm_deposit_observation_required: bool = False
    campaign_site_and_clock_reviewed: bool
    sampling_plan_and_coverage_reviewed: bool
    sample_validity_reviewed: bool
    assay_method_units_and_detection_limits_reviewed: bool
    water_context_reviewed: bool
    biofilm_deposit_mapping_reviewed: bool
    caller_indicator_definitions_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_records(self):
        collections = (
            ([row.sample_id for row in self.samples], "sample"),
            ([row.assay_id for row in self.assays], "assay"),
            ([row.observation_id for row in self.water_context], "water-context observation"),
            (
                [row.observation_id for row in self.biofilm_deposit_observations],
                "biofilm/deposit observation",
            ),
            ([row.indicator_id for row in self.caller_indicators], "caller indicator"),
        )
        for values, name in collections:
            if len(set(values)) != len(values):
                raise ValueError(f"{name} IDs must be unique")
        sample_ids = {row.sample_id for row in self.samples}
        referenced = {
            row.sample_id
            for rows in (self.assays, self.water_context, self.biofilm_deposit_observations)
            for row in rows
        }
        if referenced - sample_ids:
            raise ValueError("assays and context observations must reference declared samples")
        for values, name in (
            (self.required_sampling_location_ids, "required sampling location"),
            (self.required_assay_target_ids, "required assay target"),
            (self.required_water_context_parameter_ids, "required water-context parameter"),
        ):
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError(f"{name} IDs must be unique and nonblank")
        return self


def microbial_campaign_summary(x: MicrobialCampaign) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "campaign_site_and_clock_reviewed",
            "sampling_plan_and_coverage_reviewed",
            "sample_validity_reviewed",
            "assay_method_units_and_detection_limits_reviewed",
            "water_context_reviewed",
            "biofilm_deposit_mapping_reviewed",
            "caller_indicator_definitions_reviewed",
        )
        if not getattr(x, name)
    ]
    valid_samples = [row for row in x.samples if row.record_valid]
    valid_sample_ids = {row.sample_id for row in valid_samples}
    observed_locations = {row.sampling_location_id for row in valid_samples}
    missing_locations = [
        location for location in x.required_sampling_location_ids if location not in observed_locations
    ]

    valid_assays = [row for row in x.assays if row.record_valid and row.sample_id in valid_sample_ids]
    assay_pairs = {(row.sample_id, row.target_id) for row in valid_assays}
    missing_assay_pairs = [
        {"sample_id": sample.sample_id, "target_id": target}
        for sample in valid_samples
        for target in x.required_assay_target_ids
        if (sample.sample_id, target) not in assay_pairs
    ]
    valid_context = [row for row in x.water_context if row.record_valid and row.sample_id in valid_sample_ids]
    context_pairs = {(row.sample_id, row.parameter_id) for row in valid_context}
    missing_context_pairs = [
        {"sample_id": sample.sample_id, "parameter_id": parameter}
        for sample in valid_samples
        for parameter in x.required_water_context_parameter_ids
        if (sample.sample_id, parameter) not in context_pairs
    ]
    valid_biofilm = [
        row
        for row in x.biofilm_deposit_observations
        if row.record_valid and row.sample_id in valid_sample_ids
    ]
    biofilm_sample_ids = {row.sample_id for row in valid_biofilm}
    missing_biofilm_samples = (
        [sample.sample_id for sample in valid_samples if sample.sample_id not in biofilm_sample_ids]
        if x.biofilm_deposit_observation_required
        else []
    )

    indicators = {row.indicator_id: row for row in x.caller_indicators}
    unmatched_assays = []
    target_method_mismatch = []
    unit_mismatch = []
    quantified_comparisons = []
    censored_rows = []
    for assay in valid_assays:
        if assay.caller_indicator_id is None:
            unmatched_assays.append(assay.assay_id)
            continue
        indicator = indicators.get(assay.caller_indicator_id)
        if indicator is None:
            unmatched_assays.append(assay.assay_id)
            continue
        if (assay.target_id, assay.method_id) != (indicator.target_id, indicator.method_id):
            target_method_mismatch.append(assay.assay_id)
            continue
        if assay.unit != indicator.unit:
            unit_mismatch.append(assay.assay_id)
            continue
        if assay.result_qualifier == "below_detection":
            censored_rows.append(
                {
                    "assay_id": assay.assay_id,
                    "sample_id": assay.sample_id,
                    "indicator_id": indicator.indicator_id,
                    "detection_limit": assay.detection_limit,
                    "unit": assay.unit,
                    "comparison_status": "censored_below_detection",
                }
            )
            continue
        below = indicator.minimum_value is not None and assay.reported_value < indicator.minimum_value
        above = indicator.maximum_value is not None and assay.reported_value > indicator.maximum_value
        quantified_comparisons.append(
            {
                "assay_id": assay.assay_id,
                "sample_id": assay.sample_id,
                "indicator_id": indicator.indicator_id,
                "reported_value": assay.reported_value,
                "unit": assay.unit,
                "below_declared_minimum": below,
                "above_declared_maximum": above,
                "caller_disposition_id_if_outside": indicator.caller_disposition_id_if_outside,
            }
        )

    invalid_samples = [row.sample_id for row in x.samples if not row.record_valid]
    invalid_assays = [row.assay_id for row in x.assays if not row.record_valid]
    invalid_context = [row.observation_id for row in x.water_context if not row.record_valid]
    invalid_biofilm = [row.observation_id for row in x.biofilm_deposit_observations if not row.record_valid]
    incomplete = (
        missing_reviews
        or invalid_samples
        or invalid_assays
        or invalid_context
        or invalid_biofilm
        or missing_locations
        or missing_assay_pairs
        or missing_context_pairs
        or missing_biofilm_samples
        or unmatched_assays
        or target_method_mismatch
        or unit_mismatch
    )
    return Calculation(
        status="needs_data" if incomplete else "computed",
        values={
            "campaign_id": x.campaign_id,
            "site_id": x.site_id,
            "clock_id": x.clock_id,
            "sample_count": len(x.samples),
            "valid_sample_count": len(valid_samples),
            "invalid_sample_ids": invalid_samples,
            "missing_required_sampling_location_ids": missing_locations,
            "assay_count": len(x.assays),
            "invalid_assay_ids": invalid_assays,
            "below_detection_assay_ids": [
                row.assay_id for row in valid_assays if row.result_qualifier == "below_detection"
            ],
            "missing_required_assay_pairs": missing_assay_pairs,
            "unmatched_indicator_assay_ids": unmatched_assays,
            "indicator_target_method_mismatch_assay_ids": target_method_mismatch,
            "indicator_unit_mismatch_assay_ids": unit_mismatch,
            "quantified_indicator_comparisons": quantified_comparisons,
            "censored_indicator_records": censored_rows,
            "water_context_observation_count": len(x.water_context),
            "invalid_water_context_observation_ids": invalid_context,
            "missing_required_water_context_pairs": missing_context_pairs,
            "biofilm_deposit_observation_count": len(x.biofilm_deposit_observations),
            "invalid_biofilm_deposit_observation_ids": invalid_biofilm,
            "missing_biofilm_deposit_sample_ids": missing_biofilm_samples,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Below-detection assays remain left-censored at their reported detection limits and are never replaced by zero or a fractional limit.",
            "Assay targets, methods and units remain distinct; caller indicators and dispositions are not bundled acceptance criteria.",
            "Microbial detection, water chemistry and biofilm/deposit observations do not establish corrosion causality, rate, remaining life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("microbial campaign asset and location must match the assessment context")

    return [
        ModelSpec(
            "degradation.microbial_campaign_summary",
            MicrobialCampaign,
            microbial_campaign_summary,
            {
                "sample_count": "count",
                "valid_sample_count": "count",
                "assay_count": "count",
                "water_context_observation_count": "count",
                "biofilm_deposit_observation_count": "count",
            },
            (
                "Campaign, site, clock, sample validity, assay identity, detection limits, water context and biofilm/deposit observations remain separate evidence fields.",
                "Caller indicators compare only matching target, method and unit; censored results and incomplete coverage remain explicit.",
            ),
            ("microbial_campaign_evidence_accounting",),
            context_validator=same_identity,
        )
    ]
