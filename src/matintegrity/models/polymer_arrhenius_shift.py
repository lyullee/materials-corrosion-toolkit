"""Caller-owned Arrhenius temperature/time-shift calibration for one polymer state."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class PolymerShiftObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    polymer_formulation_id: str = Field(min_length=1)
    physical_state_id: str = Field(min_length=1)
    endpoint_definition_id: str = Field(min_length=1)
    temperature_K: Positive
    log_time_shift_factor: float | None = None
    log_basis: Literal["natural"] = "natural"
    weight: Positive | None = None
    record_status: Literal["valid", "missing", "invalid"]
    missing_or_invalid_basis: str | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_contract(self):
        if self.record_status == "valid":
            if self.log_time_shift_factor is None or self.weight is None or self.result_digest is None:
                raise ValueError("valid polymer shift records require value, weight and result digest")
            if self.missing_or_invalid_basis is not None:
                raise ValueError("valid polymer shift records cannot carry a missing basis")
        else:
            if (
                self.log_time_shift_factor is not None
                or self.weight is not None
                or self.result_digest is not None
            ):
                raise ValueError("missing or invalid shift records cannot carry fitted result fields")
            if not self.missing_or_invalid_basis:
                raise ValueError("missing or invalid polymer shift records require a basis")
        return self


class PolymerArrheniusShiftCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    polymer_formulation_id: str = Field(min_length=1)
    physical_state_id: str = Field(min_length=1)
    endpoint_definition_id: str = Field(min_length=1)
    reference_temperature_K: Positive
    observations: tuple[PolymerShiftObservation, ...] = Field(min_length=4)
    minimum_calibration_specimen_count: int = Field(ge=2)
    minimum_calibration_source_group_count: int = Field(ge=2)
    minimum_holdout_specimen_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    formulation_physical_state_and_endpoint_reviewed: bool
    absolute_temperature_reference_and_log_basis_reviewed: bool
    specimen_source_independence_and_partitions_reviewed: bool
    weights_missingness_and_validity_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    calibration_support_and_no_extrapolation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identity_and_partition_contract(self):
        identifiers = [row.observation_id for row in self.observations]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("polymer shift observation IDs must be unique")
        specimen_partitions = {}
        source_partitions = {}
        independence_partitions = {}
        for row in self.observations:
            for field in (
                "polymer_formulation_id",
                "physical_state_id",
                "endpoint_definition_id",
            ):
                if getattr(row, field) != getattr(self, field):
                    raise ValueError(f"all polymer shift records must share {field}")
            for mapping, key, label in (
                (specimen_partitions, row.physical_specimen_id, "physical specimen"),
                (source_partitions, row.source_group_id, "source group"),
                (independence_partitions, row.independence_group_id, "independence group"),
            ):
                prior = mapping.setdefault(key, row.partition)
                if prior != row.partition:
                    raise ValueError(f"{label} cannot cross calibration and holdout partitions")
        return self


def polymer_arrhenius_shift_calibration(x: PolymerArrheniusShiftCalibration) -> Calculation:
    review_fields = (
        "formulation_physical_state_and_endpoint_reviewed",
        "absolute_temperature_reference_and_log_basis_reviewed",
        "specimen_source_independence_and_partitions_reviewed",
        "weights_missingness_and_validity_reviewed",
        "provider_lineage_and_digests_reviewed",
        "calibration_support_and_no_extrapolation_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    calibration = [
        row for row in x.observations if row.partition == "calibration" and row.record_status == "valid"
    ]
    holdout = [row for row in x.observations if row.partition == "holdout" and row.record_status == "valid"]
    excluded = [row.observation_id for row in x.observations if row.record_status != "valid"]
    counts_ok = (
        len({row.physical_specimen_id for row in calibration}) >= x.minimum_calibration_specimen_count
        and len({row.source_group_id for row in calibration}) >= x.minimum_calibration_source_group_count
        and len({row.physical_specimen_id for row in holdout}) >= x.minimum_holdout_specimen_count
        and len({row.source_group_id for row in holdout}) >= x.minimum_holdout_source_group_count
    )
    if missing_reviews or not counts_ok:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "excluded_missing_or_invalid_observation_ids": excluded,
                "minimum_valid_partition_counts_satisfied": counts_ok,
            },
            notes=("Calibration is withheld until reviews and valid independent partitions are complete.",),
        )

    xs = [1.0 / row.temperature_K - 1.0 / x.reference_temperature_K for row in calibration]
    ys = [row.log_time_shift_factor for row in calibration]
    ws = [row.weight for row in calibration]
    sw = sum(ws)
    xm = sum(w * value for w, value in zip(ws, xs, strict=True)) / sw
    ym = sum(w * value for w, value in zip(ws, ys, strict=True)) / sw
    denominator = sum(w * (value - xm) ** 2 for w, value in zip(ws, xs, strict=True))
    if denominator <= 0:
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "reason": "zero reciprocal-temperature variance"},
            notes=("At least two distinct valid calibration temperatures are required.",),
        )
    slope = sum(w * (a - xm) * (b - ym) for w, a, b in zip(ws, xs, ys, strict=True)) / denominator
    intercept = ym - slope * xm
    if slope <= 0:
        return Calculation(
            status="out_of_scope",
            values={"calibration_id": x.calibration_id, "reciprocal_temperature_slope_K": slope},
            notes=("The supplied records do not identify the required positive Arrhenius slope.",),
        )
    minimum_temperature = min(row.temperature_K for row in calibration)
    maximum_temperature = max(row.temperature_K for row in calibration)
    outside = [
        row.observation_id
        for row in holdout
        if not minimum_temperature <= row.temperature_K <= maximum_temperature
    ]
    values = {
        "calibration_id": x.calibration_id,
        "reference_temperature_K": x.reference_temperature_K,
        "log_shift_at_reference_temperature": intercept,
        "reciprocal_temperature_slope_K": slope,
        "calibration_temperature_support_K": [minimum_temperature, maximum_temperature],
        "outside_support_holdout_observation_ids": outside,
        "excluded_missing_or_invalid_observation_ids": excluded,
        "calibration_observation_ids": [row.observation_id for row in calibration],
        "holdout_observation_ids": [row.observation_id for row in holdout],
    }
    notes = (
        "Only valid calibration rows identify the natural-log time-shift relation against reciprocal absolute temperature.",
        "Missing and invalid rows are preserved but excluded; holdout observations never update coefficients.",
        "The fit does not establish chemical compatibility, long-term life, acceptance or failure probability.",
    )
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    errors = [
        row.log_time_shift_factor
        - (intercept + slope * (1.0 / row.temperature_K - 1.0 / x.reference_temperature_K))
        for row in holdout
    ]
    hsw = sum(row.weight for row in holdout)
    values["holdout_log_shift_bias"] = (
        sum(row.weight * error for row, error in zip(holdout, errors, strict=True)) / hsw
    )
    values["holdout_log_shift_rmse"] = math.sqrt(
        sum(row.weight * error * error for row, error in zip(holdout, errors, strict=True)) / hsw
    )
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("polymer shift calibration asset and location must match the run context")

    return [
        ModelSpec(
            "materials.polymer_arrhenius_shift_calibration",
            PolymerArrheniusShiftCalibration,
            polymer_arrhenius_shift_calibration,
            {
                "calibration_id": "1",
                "reference_temperature_K": "K",
                "log_shift_at_reference_temperature": "1",
                "reciprocal_temperature_slope_K": "K",
                "calibration_temperature_support_K": "K",
                "outside_support_holdout_observation_ids": "1",
                "excluded_missing_or_invalid_observation_ids": "1",
                "calibration_observation_ids": "1",
                "holdout_observation_ids": "1",
                "holdout_log_shift_bias": "1",
                "holdout_log_shift_rmse": "1",
            },
            (
                "Weighted calibration is restricted to one polymer formulation, physical state and endpoint definition.",
                "Natural-log shift factor is linear in reciprocal absolute temperature relative to a declared reference.",
                "Calibration and holdout specimens, source groups and independence groups are disjoint.",
            ),
            ("weighted_polymer_arrhenius_time_shift_calibration",),
            context_validator=same_identity,
        )
    ]
