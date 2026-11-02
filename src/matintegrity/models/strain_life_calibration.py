"""Two-stage log-linear calibration of separated strain-life components."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class StrainLifeCalibrationObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    material_condition_id: str = Field(min_length=1)
    endpoint_status: Literal["failure", "runout", "censored"]
    cycles_value: Positive
    cycles_definition: str = Field(min_length=1)
    elastic_strain_amplitude: Positive | None = None
    plastic_strain_amplitude: Positive | None = None
    strain_unit_token: Literal["1"] = "1"
    weight: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def endpoint_contract(self):
        if self.endpoint_status == "failure":
            if self.elastic_strain_amplitude is None or self.plastic_strain_amplitude is None:
                raise ValueError("failure observations require separated elastic and plastic amplitudes")
        elif self.elastic_strain_amplitude is not None or self.plastic_strain_amplitude is not None:
            raise ValueError("runout and censored observations must not be represented as failure components")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid strain-life records require a basis")
        return self


class StrainLifeCoefficientCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    elastic_modulus: Positive
    stress_unit_token: str = Field(min_length=1)
    observations: tuple[StrainLifeCalibrationObservation, ...] = Field(min_length=6)
    minimum_calibration_failure_specimen_count: int = Field(ge=2)
    minimum_calibration_failure_source_group_count: int = Field(ge=2)
    minimum_holdout_failure_specimen_count: int = Field(ge=1)
    minimum_holdout_failure_source_group_count: int = Field(ge=1)
    stabilized_cycle_and_failure_endpoint_reviewed: bool
    elastic_plastic_component_definition_reviewed: bool
    cycles_reversals_and_units_reviewed: bool
    censoring_and_runout_status_reviewed: bool
    specimen_source_independence_and_partitions_reviewed: bool
    weights_validity_and_digests_reviewed: bool
    support_and_no_extrapolation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def partitions(self):
        ids = [row.observation_id for row in self.observations]
        if len(set(ids)) != len(ids):
            raise ValueError("strain-life observation IDs must be unique")
        maps = ({}, {}, {})
        for row in self.observations:
            if row.material_condition_id != self.material_condition_id:
                raise ValueError("all strain-life records must share material condition")
            for mapping, key, label in zip(
                maps,
                (row.physical_specimen_id, row.source_group_id, row.independence_group_id),
                ("physical specimen", "source group", "independence group"),
                strict=True,
            ):
                prior = mapping.setdefault(key, row.partition)
                if prior != row.partition:
                    raise ValueError(f"{label} cannot cross calibration and holdout")
        return self


def _fit(rows, attribute):
    xs = [math.log(2.0 * row.cycles_value) for row in rows]
    ys = [math.log(getattr(row, attribute)) for row in rows]
    ws = [row.weight for row in rows]
    sw = sum(ws)
    xm = sum(w * value for w, value in zip(ws, xs, strict=True)) / sw
    ym = sum(w * value for w, value in zip(ws, ys, strict=True)) / sw
    denominator = sum(w * (value - xm) ** 2 for w, value in zip(ws, xs, strict=True))
    if denominator <= 0:
        return None
    slope = sum(w * (a - xm) * (b - ym) for w, a, b in zip(ws, xs, ys, strict=True)) / denominator
    return ym - slope * xm, slope


def strain_life_coefficient_calibration(x: StrainLifeCoefficientCalibration) -> Calculation:
    reviews = (
        "stabilized_cycle_and_failure_endpoint_reviewed",
        "elastic_plastic_component_definition_reviewed",
        "cycles_reversals_and_units_reviewed",
        "censoring_and_runout_status_reviewed",
        "specimen_source_independence_and_partitions_reviewed",
        "weights_validity_and_digests_reviewed",
        "support_and_no_extrapolation_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    invalid = [row.observation_id for row in x.observations if not row.record_valid]
    calibration = [
        row for row in x.observations if row.partition == "calibration" and row.endpoint_status == "failure"
    ]
    holdout = [
        row for row in x.observations if row.partition == "holdout" and row.endpoint_status == "failure"
    ]
    counts_ok = (
        len({r.physical_specimen_id for r in calibration}) >= x.minimum_calibration_failure_specimen_count
        and len({r.source_group_id for r in calibration}) >= x.minimum_calibration_failure_source_group_count
        and len({r.physical_specimen_id for r in holdout}) >= x.minimum_holdout_failure_specimen_count
        and len({r.source_group_id for r in holdout}) >= x.minimum_holdout_failure_source_group_count
    )
    if missing_reviews or invalid or not counts_ok:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "invalid_observation_ids": invalid,
                "minimum_failure_partition_counts_satisfied": counts_ok,
            },
            notes=("Calibration is withheld until reviews and uncensored failure partitions are complete.",),
        )
    elastic_fit = _fit(calibration, "elastic_strain_amplitude")
    plastic_fit = _fit(calibration, "plastic_strain_amplitude")
    if elastic_fit is None or plastic_fit is None:
        return Calculation(
            status="needs_data",
            values={"calibration_id": x.calibration_id, "reason": "zero log-cycle variance"},
            notes=("Distinct calibration failure lives are required.",),
        )
    log_elastic, b = elastic_fit
    log_eps_f, c = plastic_fit
    if b >= 0 or c >= 0:
        return Calculation(
            status="out_of_scope",
            values={
                "calibration_id": x.calibration_id,
                "fatigue_strength_exponent": b,
                "fatigue_ductility_exponent": c,
            },
            notes=("The supplied data do not identify decreasing elastic and plastic components.",),
        )
    minimum_cycles = min(r.cycles_value for r in calibration)
    maximum_cycles = max(r.cycles_value for r in calibration)
    outside = [r.observation_id for r in holdout if not minimum_cycles <= r.cycles_value <= maximum_cycles]
    values = {
        "calibration_id": x.calibration_id,
        "fatigue_strength_coefficient": math.exp(log_elastic) * x.elastic_modulus,
        "elastic_coefficient_ratio": math.exp(log_elastic),
        "fatigue_strength_exponent": b,
        "fatigue_ductility_coefficient": math.exp(log_eps_f),
        "fatigue_ductility_exponent": c,
        "stress_unit_token": x.stress_unit_token,
        "calibration_cycle_support": [minimum_cycles, maximum_cycles],
        "outside_support_holdout_observation_ids": outside,
        "excluded_runout_or_censored_observation_ids": [
            r.observation_id for r in x.observations if r.endpoint_status != "failure"
        ],
    }
    notes = (
        "Elastic and plastic components are fitted in two independent weighted log-linear stages using calibration failures only.",
        "Runout and censored records are preserved but never substituted as failures or used in coefficient fitting.",
        "Holdout diagnostics do not update coefficients; no extrapolation, life acceptance or failure probability is produced.",
    )
    if outside:
        return Calculation(status="out_of_scope", values=values, notes=notes)

    def errors(attribute, intercept, slope):
        return [
            math.log(getattr(r, attribute)) - (intercept + slope * math.log(2 * r.cycles_value))
            for r in holdout
        ]

    for name, errs in (
        ("elastic", errors("elastic_strain_amplitude", log_elastic, b)),
        ("plastic", errors("plastic_strain_amplitude", log_eps_f, c)),
    ):
        sw = sum(r.weight for r in holdout)
        values[f"holdout_{name}_log_bias"] = (
            sum(r.weight * e for r, e in zip(holdout, errs, strict=True)) / sw
        )
        values[f"holdout_{name}_log_rmse"] = math.sqrt(
            sum(r.weight * e * e for r, e in zip(holdout, errs, strict=True)) / sw
        )
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("strain-life calibration asset and location must match the run context")

    return [
        ModelSpec(
            "materials.strain_life_coefficient_calibration",
            StrainLifeCoefficientCalibration,
            strain_life_coefficient_calibration,
            {
                "calibration_id": "1",
                "fatigue_strength_coefficient": "caller_stress_unit",
                "elastic_coefficient_ratio": "1",
                "fatigue_strength_exponent": "1",
                "fatigue_ductility_coefficient": "1",
                "fatigue_ductility_exponent": "1",
                "stress_unit_token": "1",
                "calibration_cycle_support": "cycle",
                "outside_support_holdout_observation_ids": "1",
                "excluded_runout_or_censored_observation_ids": "1",
                "holdout_elastic_log_bias": "1",
                "holdout_elastic_log_rmse": "1",
                "holdout_plastic_log_bias": "1",
                "holdout_plastic_log_rmse": "1",
            },
            (
                "Two-stage weighted log-linear CMB calibration requires separated elastic and plastic strain amplitudes.",
                "Only uncensored calibration failures identify coefficients; holdout failures are diagnostics only.",
                "Fitted coefficients are restricted to the calibration cycle support.",
            ),
            ("two_stage_weighted_coffin_manson_basquin_calibration",),
            context_validator=same_identity,
        )
    ]
