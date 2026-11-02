"""Calibration of an Archard wear coefficient for one reviewed contact regime."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class ArchardCalibrationObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    material_condition_id: str = Field(min_length=1)
    counterface_material_condition_id: str = Field(min_length=1)
    contact_geometry_id: str = Field(min_length=1)
    lubrication_regime_id: str = Field(min_length=1)
    temperature_K: Positive
    normal_force_N: Positive
    sliding_distance_m: Positive
    hardness_Pa: Positive
    hardness_identity_id: str = Field(min_length=1)
    measured_wear_volume_m3: Positive | None = None
    expanded_uncertainty_wear_volume_m3: Positive | None = None
    uncertainty_coverage_factor: Positive | None = None
    weight: Positive | None = None
    record_status: Literal["valid", "missing", "invalid"]
    missing_or_invalid_basis: str | None = None
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def status_contract(self):
        result_fields = (
            self.measured_wear_volume_m3,
            self.expanded_uncertainty_wear_volume_m3,
            self.uncertainty_coverage_factor,
            self.weight,
        )
        if self.record_status == "valid":
            if any(value is None for value in result_fields):
                raise ValueError("valid wear observations require volume, uncertainty, coverage and weight")
            if self.missing_or_invalid_basis is not None:
                raise ValueError("valid wear observations cannot carry a missing basis")
        else:
            if any(value is not None for value in result_fields) or not self.missing_or_invalid_basis:
                raise ValueError("missing or invalid wear records require a basis and no result fields")
        return self


class ArchardWearCoefficientCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    counterface_material_condition_id: str = Field(min_length=1)
    contact_geometry_id: str = Field(min_length=1)
    lubrication_regime_id: str = Field(min_length=1)
    observations: tuple[ArchardCalibrationObservation, ...] = Field(min_length=4)
    minimum_calibration_specimen_count: int = Field(ge=2)
    minimum_calibration_source_group_count: int = Field(ge=2)
    minimum_holdout_specimen_count: int = Field(ge=1)
    minimum_holdout_source_group_count: int = Field(ge=1)
    material_contact_lubrication_and_temperature_regime_reviewed: bool
    si_units_load_distance_hardness_and_volume_reviewed: bool
    hardness_identity_and_measurement_basis_reviewed: bool
    specimen_source_groups_and_partitions_reviewed: bool
    uncertainty_weights_missingness_and_validity_reviewed: bool
    calibration_support_and_no_extrapolation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def identity_and_partitions(self):
        identifiers = [row.observation_id for row in self.observations]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("wear observation IDs must be unique")
        specimen_partitions = {}
        source_partitions = {}
        for row in self.observations:
            for field in (
                "material_condition_id",
                "counterface_material_condition_id",
                "contact_geometry_id",
                "lubrication_regime_id",
            ):
                if getattr(row, field) != getattr(self, field):
                    raise ValueError(f"all wear records must share {field}")
            for mapping, key, label in (
                (specimen_partitions, row.physical_specimen_id, "physical specimen"),
                (source_partitions, row.source_group_id, "source group"),
            ):
                prior = mapping.setdefault(key, row.partition)
                if prior != row.partition:
                    raise ValueError(f"{label} cannot cross calibration and holdout partitions")
        return self


def _coefficient(row: ArchardCalibrationObservation) -> float:
    return row.measured_wear_volume_m3 * row.hardness_Pa / (row.normal_force_N * row.sliding_distance_m)


def archard_wear_coefficient_calibration(x: ArchardWearCoefficientCalibration) -> Calculation:
    review_fields = (
        "material_contact_lubrication_and_temperature_regime_reviewed",
        "si_units_load_distance_hardness_and_volume_reviewed",
        "hardness_identity_and_measurement_basis_reviewed",
        "specimen_source_groups_and_partitions_reviewed",
        "uncertainty_weights_missingness_and_validity_reviewed",
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
            notes=("Wear-coefficient calibration is withheld until reviews and partitions are complete.",),
        )
    weights = [row.weight for row in calibration]
    log_coefficients = [math.log(_coefficient(row)) for row in calibration]
    weight_sum = sum(weights)
    log_coefficient = (
        sum(weight * value for weight, value in zip(weights, log_coefficients, strict=True)) / weight_sum
    )
    coefficient = math.exp(log_coefficient)
    support_fields = (
        "temperature_K",
        "normal_force_N",
        "sliding_distance_m",
        "hardness_Pa",
    )
    support = {
        field: [
            min(getattr(row, field) for row in calibration),
            max(getattr(row, field) for row in calibration),
        ]
        for field in support_fields
    }
    outside = [
        row.observation_id
        for row in holdout
        if any(not support[field][0] <= getattr(row, field) <= support[field][1] for field in support_fields)
    ]
    hardness_ids = sorted({row.hardness_identity_id for row in calibration})
    holdout_hardness_mismatch = [
        row.observation_id for row in holdout if row.hardness_identity_id not in hardness_ids
    ]
    if holdout_hardness_mismatch:
        outside.extend(identifier for identifier in holdout_hardness_mismatch if identifier not in outside)
    values = {
        "calibration_id": x.calibration_id,
        "dimensionless_wear_coefficient": coefficient,
        "calibration_support": support,
        "calibration_hardness_identity_ids": hardness_ids,
        "outside_support_holdout_observation_ids": outside,
        "excluded_missing_or_invalid_observation_ids": excluded,
        "calibration_observation_ids": [row.observation_id for row in calibration],
        "holdout_observation_ids": [row.observation_id for row in holdout],
    }
    notes = (
        "The coefficient is the caller-weighted geometric mean of Archard coefficients from valid calibration records.",
        "Holdout diagnostics are computed only inside calibration temperature, load, distance, hardness and hardness-identity support.",
        "No fretting-corrosion interaction, service life, acceptance or failure probability is produced.",
    )
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    errors = [math.log(_coefficient(row)) - log_coefficient for row in holdout]
    holdout_weight_sum = sum(row.weight for row in holdout)
    values["holdout_log_coefficient_bias"] = (
        sum(row.weight * error for row, error in zip(holdout, errors, strict=True)) / holdout_weight_sum
    )
    values["holdout_log_coefficient_rmse"] = math.sqrt(
        sum(row.weight * error * error for row, error in zip(holdout, errors, strict=True))
        / holdout_weight_sum
    )
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("wear calibration asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.archard_wear_coefficient_calibration",
            ArchardWearCoefficientCalibration,
            archard_wear_coefficient_calibration,
            {
                "calibration_id": "1",
                "dimensionless_wear_coefficient": "1",
                "calibration_support": "SI",
                "calibration_hardness_identity_ids": "1",
                "outside_support_holdout_observation_ids": "1",
                "excluded_missing_or_invalid_observation_ids": "1",
                "calibration_observation_ids": "1",
                "holdout_observation_ids": "1",
                "holdout_log_coefficient_bias": "1",
                "holdout_log_coefficient_rmse": "1",
            },
            (
                "Calibration is restricted to one material/counterface/contact/lubrication regime with SI force, distance, hardness and wear volume.",
                "The dimensionless coefficient follows V*H/(F*s) for each valid caller observation.",
                "Calibration and holdout physical specimens and source groups are disjoint.",
            ),
            ("weighted_archard_wear_coefficient_calibration",),
            context_validator=same_identity,
        )
    ]
