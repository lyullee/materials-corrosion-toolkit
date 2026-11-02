"""Weighted pre-necking monotonic Hollomon plastic-curve calibration."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class MonotonicStressStrainPoint(Contract):
    point_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    material_condition_id: str = Field(min_length=1)
    quantity_convention: Literal["engineering", "true"]
    stress_value: Positive
    stress_unit_token: str = Field(min_length=1)
    total_strain: Positive
    strain_unit_token: Literal["1"] = "1"
    elastic_modulus: Positive
    elastic_modulus_unit_token: str = Field(min_length=1)
    stress_standard_uncertainty: Nonnegative
    weight: Positive
    pre_necking_window_id: str = Field(min_length=1)
    pre_necking_reviewed: bool
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid monotonic stress-strain points require a basis")
        return self


class MonotonicHollomonCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    quantity_convention: Literal["engineering", "true"]
    points: tuple[MonotonicStressStrainPoint, ...] = Field(min_length=4)
    minimum_calibration_specimen_count: int = Field(ge=2)
    minimum_calibration_source_group_count: int = Field(ge=2)
    minimum_holdout_specimen_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    monotonic_loading_and_quantity_convention_reviewed: bool
    stress_strain_units_sign_and_elastic_subtraction_reviewed: bool
    pre_necking_windows_reviewed: bool
    specimen_source_independence_and_partitions_reviewed: bool
    uncertainty_weights_validity_and_digests_reviewed: bool
    calibration_support_and_no_extrapolation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identity_and_partitions(self):
        identifiers = [row.point_id for row in self.points]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("monotonic stress-strain point IDs must be unique")
        specimen_partitions = {}
        source_partitions = {}
        independence_partitions = {}
        for row in self.points:
            if row.material_condition_id != self.material_condition_id:
                raise ValueError("all monotonic points must share material condition")
            if row.quantity_convention != self.quantity_convention:
                raise ValueError("engineering and true quantities cannot be mixed")
            if row.stress_unit_token != row.elastic_modulus_unit_token:
                raise ValueError("stress and elastic modulus must use the same unit token")
            for mapping, key, label in (
                (specimen_partitions, row.physical_specimen_id, "physical specimen"),
                (source_partitions, row.source_group_id, "source group"),
                (independence_partitions, row.independence_group_id, "independence group"),
            ):
                prior = mapping.setdefault(key, row.partition)
                if prior != row.partition:
                    raise ValueError(f"{label} cannot cross calibration and holdout partitions")
        return self


def monotonic_hollomon_calibration(x: MonotonicHollomonCalibration) -> Calculation:
    review_fields = (
        "monotonic_loading_and_quantity_convention_reviewed",
        "stress_strain_units_sign_and_elastic_subtraction_reviewed",
        "pre_necking_windows_reviewed",
        "specimen_source_independence_and_partitions_reviewed",
        "uncertainty_weights_validity_and_digests_reviewed",
        "calibration_support_and_no_extrapolation_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    invalid_ids = [row.point_id for row in x.points if not row.record_valid]
    unreviewed_necking_ids = [row.point_id for row in x.points if not row.pre_necking_reviewed]
    stress_units = {row.stress_unit_token for row in x.points}
    plastic_strain = {
        row.point_id: row.total_strain - row.stress_value / row.elastic_modulus for row in x.points
    }
    nonpositive_ids = [identifier for identifier, value in plastic_strain.items() if value <= 0]
    calibration = [row for row in x.points if row.partition == "calibration"]
    holdout = [row for row in x.points if row.partition == "holdout"]
    counts_ok = (
        len({row.physical_specimen_id for row in calibration}) >= x.minimum_calibration_specimen_count
        and len({row.source_group_id for row in calibration}) >= x.minimum_calibration_source_group_count
        and len({row.physical_specimen_id for row in holdout}) >= x.minimum_holdout_specimen_count
        and len({row.source_group_id for row in holdout}) >= x.minimum_holdout_source_group_count
    )
    if (
        missing_reviews
        or invalid_ids
        or unreviewed_necking_ids
        or len(stress_units) != 1
        or nonpositive_ids
        or not counts_ok
    ):
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "invalid_point_ids": invalid_ids,
                "unreviewed_pre_necking_point_ids": unreviewed_necking_ids,
                "stress_unit_tokens": sorted(stress_units),
                "nonpositive_plastic_strain_point_ids": nonpositive_ids,
                "minimum_partition_counts_satisfied": counts_ok,
            },
            notes=(
                "Calibration is withheld until definitions, pre-necking scope and partitions are complete.",
            ),
        )
    xs = [math.log(plastic_strain[row.point_id]) for row in calibration]
    ys = [math.log(row.stress_value) for row in calibration]
    ws = [row.weight for row in calibration]
    weight_sum = sum(ws)
    mean_x = sum(w * value for w, value in zip(ws, xs, strict=True)) / weight_sum
    mean_y = sum(w * value for w, value in zip(ws, ys, strict=True)) / weight_sum
    denominator = sum(w * (value - mean_x) ** 2 for w, value in zip(ws, xs, strict=True))
    if denominator <= 0:
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "reason": "zero log-plastic-strain variance"},
            notes=("Distinct calibration plastic strains are required.",),
        )
    exponent = sum(w * (a - mean_x) * (b - mean_y) for w, a, b in zip(ws, xs, ys, strict=True)) / denominator
    log_strength = mean_y - exponent * mean_x
    if exponent <= 0:
        return Calculation(
            status="out_of_scope",
            values={"calibration_id": x.calibration_id, "strain_hardening_exponent": exponent},
            notes=("The supplied pre-necking points do not identify a positive hardening exponent.",),
        )
    minimum_strain = min(plastic_strain[row.point_id] for row in calibration)
    maximum_strain = max(plastic_strain[row.point_id] for row in calibration)
    outside = [
        row.point_id
        for row in holdout
        if not minimum_strain <= plastic_strain[row.point_id] <= maximum_strain
    ]
    values = {
        "calibration_id": x.calibration_id,
        "strength_coefficient": math.exp(log_strength),
        "strain_hardening_exponent": exponent,
        "stress_unit_token": next(iter(stress_units)),
        "quantity_convention": x.quantity_convention,
        "calibration_plastic_strain_support": [minimum_strain, maximum_strain],
        "outside_support_holdout_point_ids": outside,
        "calibration_point_ids": [row.point_id for row in calibration],
        "holdout_point_ids": [row.point_id for row in holdout],
    }
    notes = (
        "The model fits the declared engineering or true monotonic pre-necking quantities without converting between conventions.",
        "Plastic strain is total strain minus stress divided by the record elastic modulus; calibration alone identifies the Hollomon coefficients.",
        "No post-necking extrapolation, cyclic behavior, code acceptance, life or failure probability is produced.",
    )
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    errors = [
        math.log(row.stress_value) - (log_strength + exponent * math.log(plastic_strain[row.point_id]))
        for row in holdout
    ]
    hws = [row.weight for row in holdout]
    hsum = sum(hws)
    values["holdout_log_stress_bias"] = sum(w * e for w, e in zip(hws, errors, strict=True)) / hsum
    values["holdout_log_stress_rmse"] = math.sqrt(
        sum(w * e * e for w, e in zip(hws, errors, strict=True)) / hsum
    )
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError(
                "monotonic plastic-curve calibration asset and location must match the run context"
            )

    return [
        ModelSpec(
            "materials.monotonic_hollomon_calibration",
            MonotonicHollomonCalibration,
            monotonic_hollomon_calibration,
            {
                "calibration_id": "1",
                "strength_coefficient": "caller_stress_unit",
                "strain_hardening_exponent": "1",
                "stress_unit_token": "1",
                "quantity_convention": "1",
                "calibration_plastic_strain_support": "1",
                "outside_support_holdout_point_ids": "1",
                "calibration_point_ids": "1",
                "holdout_point_ids": "1",
                "holdout_log_stress_bias": "1",
                "holdout_log_stress_rmse": "1",
            },
            (
                "Weighted log-space Hollomon fit to caller-reviewed monotonic pre-necking stress and elastic-subtracted plastic strain.",
                "Engineering or true quantity convention is preserved without implicit conversion.",
                "Calibration and holdout specimen, source and independence groups are disjoint.",
            ),
            ("weighted_pre_necking_monotonic_hollomon_calibration",),
            context_validator=same_identity,
        )
    ]
