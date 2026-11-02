"""Weighted log-response calibration for traceable reference-leak observations."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Partition = Literal["calibration", "holdout"]
ReportingStatus = Literal["detected", "below_detection", "censored", "missing", "invalid"]


class ReferenceLeakResponseObservation(Contract):
    observation_id: str = Field(min_length=1)
    partition: Partition
    physical_specimen_id: str = Field(min_length=1)
    reference_leak_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    instrument_configuration_id: str = Field(min_length=1)
    test_gas_id: str = Field(min_length=1)
    boundary_condition_id: str = Field(min_length=1)
    observation_clock_id: str = Field(min_length=1)
    reference_time_s: Nonnegative
    response_time_s: Nonnegative
    reporting_status: ReportingStatus
    reference_leak_rate_mol_s: Positive | None = None
    expanded_reference_leak_uncertainty_mol_s: Nonnegative | None = None
    response_value: Positive | None = None
    response_unit_token: str = Field(min_length=1)
    expanded_response_uncertainty: Nonnegative | None = None
    response_detection_limit: Positive | None = None
    sample_weight: Positive
    exclusion_or_status_basis: str | None = None
    reference_provider_id: str = Field(min_length=1)
    reference_provider_revision: str = Field(min_length=1)
    reference_provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    instrument_provider_id: str = Field(min_length=1)
    instrument_provider_revision: str = Field(min_length=1)
    instrument_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_specific_values(self):
        if self.reporting_status == "detected":
            if self.reference_leak_rate_mol_s is None or self.response_value is None:
                raise ValueError("detected reference-leak observations require leak rate and response")
            if (
                self.expanded_reference_leak_uncertainty_mol_s is None
                or self.expanded_response_uncertainty is None
            ):
                raise ValueError("detected reference-leak observations require both uncertainties")
        elif not self.exclusion_or_status_basis:
            raise ValueError("non-detect, missing or invalid observations require an explicit basis")
        if self.reporting_status in {"below_detection", "censored"} and self.response_detection_limit is None:
            raise ValueError("below-detection or censored observations require a reporting limit")
        if not self.record_valid and not self.exclusion_or_status_basis:
            raise ValueError("invalid reference-leak observations require a basis")
        return self


class ReferenceLeakResponseCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    observation_clock_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    instrument_id: str = Field(min_length=1)
    instrument_configuration_id: str = Field(min_length=1)
    test_gas_id: str = Field(min_length=1)
    boundary_condition_id: str = Field(min_length=1)
    leak_quantity_definition: Literal["molar_flow_rate"] = "molar_flow_rate"
    leak_rate_unit_token: Literal["mol/s"] = "mol/s"
    pressure_basis: str = Field(min_length=1)
    reference_temperature_basis: str = Field(min_length=1)
    response_definition: str = Field(min_length=1)
    response_unit_token: str = Field(min_length=1)
    log_reference_leak_rate_mol_s: Positive
    log_reference_response_value: Positive
    maximum_clock_alignment_error_s: Nonnegative
    observations: tuple[ReferenceLeakResponseObservation, ...] = Field(min_length=3)
    minimum_calibration_detected_count: int = Field(ge=2)
    minimum_holdout_detected_count: int = Field(ge=1)
    minimum_calibration_source_group_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    minimum_holdout_independence_group_count: int = Field(ge=1)
    instrument_configuration_gas_and_boundary_reviewed: bool
    clock_alignment_and_physical_scope_reviewed: bool
    si_leak_quantity_pressure_and_temperature_basis_reviewed: bool
    reference_traceability_and_uncertainty_reviewed: bool
    response_definition_units_and_uncertainty_reviewed: bool
    partition_and_group_independence_reviewed: bool
    censored_missing_and_invalid_status_reviewed: bool
    provider_and_result_digests_reviewed: bool

    @model_validator(mode="after")
    def aligned_identity_and_partitions(self):
        identifiers = [row.observation_id for row in self.observations]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("reference-leak observation identifiers must be unique")
        expected_identity = (
            self.instrument_id,
            self.instrument_configuration_id,
            self.test_gas_id,
            self.boundary_condition_id,
            self.observation_clock_id,
            self.response_unit_token,
        )
        for row in self.observations:
            identity = (
                row.instrument_id,
                row.instrument_configuration_id,
                row.test_gas_id,
                row.boundary_condition_id,
                row.observation_clock_id,
                row.response_unit_token,
            )
            if identity != expected_identity:
                raise ValueError("reference-leak observation identities and units must match calibration")
        for attribute, name in (
            ("physical_specimen_id", "physical specimen"),
            ("reference_leak_id", "reference leak"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            partitions_by_id: dict[str, set[str]] = {}
            for row in self.observations:
                partitions_by_id.setdefault(getattr(row, attribute), set()).add(row.partition)
            crossed = sorted(identifier for identifier, values in partitions_by_id.items() if len(values) > 1)
            if crossed:
                raise ValueError(f"{name} identifiers cannot cross calibration and holdout partitions")
        return self


def reference_leak_response_calibration(x: ReferenceLeakResponseCalibration) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "instrument_configuration_gas_and_boundary_reviewed",
            "clock_alignment_and_physical_scope_reviewed",
            "si_leak_quantity_pressure_and_temperature_basis_reviewed",
            "reference_traceability_and_uncertainty_reviewed",
            "response_definition_units_and_uncertainty_reviewed",
            "partition_and_group_independence_reviewed",
            "censored_missing_and_invalid_status_reviewed",
            "provider_and_result_digests_reviewed",
        )
        if not getattr(x, name)
    ]
    clock_misaligned_ids = [
        row.observation_id
        for row in x.observations
        if abs(row.reference_time_s - row.response_time_s) > x.maximum_clock_alignment_error_s
    ]
    invalid_record_ids = [row.observation_id for row in x.observations if not row.record_valid]
    included_calibration = [
        row
        for row in x.observations
        if row.partition == "calibration" and row.reporting_status == "detected" and row.record_valid
    ]
    included_holdout = [
        row
        for row in x.observations
        if row.partition == "holdout" and row.reporting_status == "detected" and row.record_valid
    ]
    excluded_records = [
        {
            "observation_id": row.observation_id,
            "partition": row.partition,
            "reporting_status": row.reporting_status,
            "exclusion_basis": row.exclusion_or_status_basis,
            "reference_leak_rate_mol_s": row.reference_leak_rate_mol_s,
            "response_detection_limit": row.response_detection_limit,
        }
        for row in x.observations
        if row.reporting_status != "detected" or not row.record_valid
    ]
    calibration_sources = {row.source_group_id for row in included_calibration}
    holdout_sources = {row.source_group_id for row in included_holdout}
    holdout_independence = {row.independence_group_id for row in included_holdout}
    minimum_counts_met = (
        len(included_calibration) >= x.minimum_calibration_detected_count
        and len(included_holdout) >= x.minimum_holdout_detected_count
        and len(calibration_sources) >= x.minimum_calibration_source_group_count
        and len(holdout_sources) >= x.minimum_holdout_source_group_count
        and len(holdout_independence) >= x.minimum_holdout_independence_group_count
    )
    if missing_reviews or clock_misaligned_ids or invalid_record_ids or not minimum_counts_met:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "clock_misaligned_observation_ids": clock_misaligned_ids,
                "invalid_observation_ids": invalid_record_ids,
                "minimum_counts_met": minimum_counts_met,
                "included_calibration_observation_ids": [row.observation_id for row in included_calibration],
                "included_holdout_observation_ids": [row.observation_id for row in included_holdout],
                "excluded_observations": excluded_records,
            },
            notes=("Only reviewed, valid, clock-aligned detected observations enter the regression.",),
        )

    weights = [row.sample_weight for row in included_calibration]
    log_leak = [
        math.log(row.reference_leak_rate_mol_s / x.log_reference_leak_rate_mol_s)
        for row in included_calibration
    ]
    log_response = [
        math.log(row.response_value / x.log_reference_response_value) for row in included_calibration
    ]
    weight_sum = math.fsum(weights)
    mean_x = math.fsum(weight * value for weight, value in zip(weights, log_leak, strict=True)) / weight_sum
    mean_y = (
        math.fsum(weight * value for weight, value in zip(weights, log_response, strict=True)) / weight_sum
    )
    weighted_x_variance_sum = math.fsum(
        weight * (value - mean_x) ** 2 for weight, value in zip(weights, log_leak, strict=True)
    )
    if weighted_x_variance_sum <= 0.0:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "included_calibration_observation_ids": [row.observation_id for row in included_calibration],
                "identifiable_log_leak_span": False,
                "calibration_leak_rate_minimum_mol_s": min(
                    row.reference_leak_rate_mol_s for row in included_calibration
                ),
                "calibration_leak_rate_maximum_mol_s": max(
                    row.reference_leak_rate_mol_s for row in included_calibration
                ),
            },
            notes=("At least two distinct positive calibration leak rates are required for log regression.",),
        )
    slope = (
        math.fsum(
            weight * (x_value - mean_x) * (y_value - mean_y)
            for weight, x_value, y_value in zip(weights, log_leak, log_response, strict=True)
        )
        / weighted_x_variance_sum
    )
    intercept = mean_y - slope * mean_x
    calibration_minimum = min(row.reference_leak_rate_mol_s for row in included_calibration)
    calibration_maximum = max(row.reference_leak_rate_mol_s for row in included_calibration)
    outside_holdout_ids = [
        row.observation_id
        for row in included_holdout
        if not calibration_minimum <= row.reference_leak_rate_mol_s <= calibration_maximum
    ]
    common_values = {
        "calibration_id": x.calibration_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "observation_clock_id": x.observation_clock_id,
        "log_response_intercept": intercept,
        "log_response_log_leak_slope": slope,
        "calibration_leak_rate_minimum_mol_s": calibration_minimum,
        "calibration_leak_rate_maximum_mol_s": calibration_maximum,
        "included_calibration_observation_ids": [row.observation_id for row in included_calibration],
        "included_holdout_observation_ids": [row.observation_id for row in included_holdout],
        "excluded_observations": excluded_records,
        "outside_calibration_support_holdout_ids": outside_holdout_ids,
        "calibration_source_group_ids": sorted(calibration_sources),
        "holdout_source_group_ids": sorted(holdout_sources),
        "holdout_independence_group_ids": sorted(holdout_independence),
    }
    notes = (
        "The fixed regression is log(instrument response) = intercept + slope*log(reference molar leak rate).",
        "Non-detect, censored, missing and invalid rows are preserved and are never replaced by zero or a detection limit.",
        "The fit calibrates reference response only; it does not invert unknown leaks, estimate detection probability, decide field acceptance or create FTA probabilities.",
    )
    if outside_holdout_ids:
        return Calculation(status="out_of_scope", values=common_values, notes=notes)
    residuals = [
        math.log(row.response_value / x.log_reference_response_value)
        - (intercept + slope * math.log(row.reference_leak_rate_mol_s / x.log_reference_leak_rate_mol_s))
        for row in included_holdout
    ]
    holdout_weights = [row.sample_weight for row in included_holdout]
    holdout_weight_sum = math.fsum(holdout_weights)
    bias = (
        math.fsum(weight * residual for weight, residual in zip(holdout_weights, residuals, strict=True))
        / holdout_weight_sum
    )
    rmse = math.sqrt(
        math.fsum(weight * residual**2 for weight, residual in zip(holdout_weights, residuals, strict=True))
        / holdout_weight_sum
    )
    common_values.update(
        {
            "holdout_log_response_bias": bias,
            "holdout_log_response_rmse": rmse,
            "holdout_residuals": [
                {"observation_id": row.observation_id, "log_response_residual": residual}
                for row, residual in zip(included_holdout, residuals, strict=True)
            ],
        }
    )
    return Calculation(values=common_values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("reference-leak calibration asset and location must match run context")
        if x.time_basis != context.time_basis:
            raise ValueError("reference-leak calibration time basis must match run context")

    return [
        ModelSpec(
            "inspection.reference_leak_response_calibration",
            ReferenceLeakResponseCalibration,
            reference_leak_response_calibration,
            {
                "calibration_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "observation_clock_id": "1",
                "log_response_intercept": "1",
                "log_response_log_leak_slope": "1",
                "calibration_leak_rate_minimum_mol_s": "mol/s",
                "calibration_leak_rate_maximum_mol_s": "mol/s",
                "included_calibration_observation_ids": "1",
                "included_holdout_observation_ids": "1",
                "excluded_observations": "mixed",
                "outside_calibration_support_holdout_ids": "1",
                "calibration_source_group_ids": "1",
                "holdout_source_group_ids": "1",
                "holdout_independence_group_ids": "1",
                "holdout_log_response_bias": "1",
                "holdout_log_response_rmse": "1",
                "holdout_residuals": "mixed",
            },
            (
                "Only valid detected rows with positive traceable molar leak rate and response enter the fit.",
                "Calibration and holdout specimens, reference leaks, source groups and independence groups are disjoint.",
                "Holdout leak rates are evaluated only inside calibration support; no unknown-leak inversion is performed.",
            ),
            ("authored_reference_leak_log_response_regression",),
            context_validator=same_identity,
        )
    ]
