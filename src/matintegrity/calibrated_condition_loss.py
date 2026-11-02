"""Explicit calibrated empirical condition-to-loss law and ordered history composition.

The caller supplies every coefficient, feature scale, unit and support bound.
No microbial count or pressure descriptor determines a rate without that law.
"""

import math
from typing import Literal

from pydantic import Field, model_validator

from .calibrated_damage_history import (
    CalibratedDamageHistory,
    CalibratedDamageInterval,
    integrate_calibrated_damage,
)
from .contracts import Contract, Nonnegative, Positive, canonical_digest


class LossRateFeature(Contract):
    feature_id: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    reference_value: float
    normalization_scale: Positive
    minimum_valid_value: float
    maximum_valid_value: float
    log_rate_coefficient: float

    @model_validator(mode="after")
    def support(self):
        if not self.minimum_valid_value <= self.reference_value <= self.maximum_valid_value:
            raise ValueError("feature reference must lie in its declared support")
        if self.maximum_valid_value <= self.minimum_valid_value:
            raise ValueError("feature support must be a nonempty interval")
        return self


class LogRateInteraction(Contract):
    first_feature_id: str = Field(min_length=1)
    second_feature_id: str = Field(min_length=1)
    coefficient: float


class CalibratedConditionLossLaw(Contract):
    law_id: str = Field(min_length=1)
    mechanism: Literal["microbial", "cavitation"]
    material_condition_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_loss_rate_m_s: Positive
    features: tuple[LossRateFeature, ...] = Field(min_length=1)
    interactions: tuple[LogRateInteraction, ...] = ()
    calibration_and_feature_interpretation_reviewed: bool
    calibration_computational_use_authorized: bool

    @model_validator(mode="after")
    def feature_identity(self):
        ids = [row.feature_id for row in self.features]
        if len(set(ids)) != len(ids):
            raise ValueError("loss-law feature IDs must be unique")
        pairs = []
        for row in self.interactions:
            if row.first_feature_id not in ids or row.second_feature_id not in ids:
                raise ValueError("interaction refers to an unknown feature")
            pair = tuple(sorted((row.first_feature_id, row.second_feature_id)))
            if pair in pairs:
                raise ValueError("duplicate symmetric interaction term")
            pairs.append(pair)
        return self


class LossCondition(Contract):
    condition_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    feature_values: dict[str, float]
    feature_units: dict[str, str]
    condition_and_measurement_basis_reviewed: bool


class ConditionLossRateAssessment(Contract):
    law: CalibratedConditionLossLaw
    condition: LossCondition


def evaluate_condition_loss_rate(request: ConditionLossRateAssessment) -> dict:
    law, condition = request.law, request.condition
    base = dict(
        status="needs_data",
        law_id=law.law_id,
        condition_id=condition.condition_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        calibration_sha256=law.calibration_sha256,
        condition_source_sha256=condition.source_sha256,
        loss_rate_m_s=None,
        log_loss_rate_m_s=None,
        prediction_origin="model_prediction",
    )
    expected = {row.feature_id for row in law.features}
    if set(condition.feature_values) != expected or set(condition.feature_units) != expected:
        raise ValueError("condition must supply the exact feature and unit set")
    if any(condition.feature_units[row.feature_id] != row.unit for row in law.features):
        raise ValueError("feature unit tokens must match the calibration; no implicit conversion")
    if not (
        law.calibration_and_feature_interpretation_reviewed
        and law.calibration_computational_use_authorized
        and condition.condition_and_measurement_basis_reviewed
    ):
        return base
    outside = [
        row.feature_id
        for row in law.features
        if not row.minimum_valid_value <= condition.feature_values[row.feature_id] <= row.maximum_valid_value
    ]
    if outside:
        return base | dict(status="out_of_scope", unsupported_feature_ids=outside)
    normalized = {
        row.feature_id: (condition.feature_values[row.feature_id] - row.reference_value)
        / row.normalization_scale
        for row in law.features
    }
    terms = [row.log_rate_coefficient * normalized[row.feature_id] for row in law.features]
    terms.extend(
        row.coefficient * normalized[row.first_feature_id] * normalized[row.second_feature_id]
        for row in law.interactions
    )
    if not all(math.isfinite(value) for value in terms):
        return base | dict(status="out_of_scope", reason="Nonfinite calibrated response terms")
    try:
        log_rate = math.log(law.reference_loss_rate_m_s) + math.fsum(terms)
        rate = math.exp(log_rate)
    except (OverflowError, ValueError):
        return base | dict(status="out_of_scope", reason="Calibrated response exceeds numeric range")
    if not math.isfinite(rate) or rate == 0:
        return base | dict(
            status="out_of_scope",
            reason="Rate overflow or underflow; not replaced by zero",
            log_loss_rate_m_s=log_rate if math.isfinite(log_rate) else None,
        )
    return base | dict(
        status="computed",
        loss_rate_m_s=rate,
        log_loss_rate_m_s=log_rate,
        normalized_features=normalized,
        basis="Caller-calibrated log-rate response inside explicit feature support. No universal microbial/cavitation law, physical validation, lifetime or failure probability is inferred.",
    )


class ConditionLossInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_s: Nonnegative
    end_s: Positive
    condition: LossCondition

    @model_validator(mode="after")
    def duration(self):
        if self.end_s <= self.start_s:
            raise ValueError("condition interval must have positive duration")
        return self


class ConditionLossHistory(Contract):
    history_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    law: CalibratedConditionLossLaw
    intervals: tuple[ConditionLossInterval, ...] = Field(min_length=1)
    piecewise_constant_conditions_and_rate_integration_reviewed: bool

    @model_validator(mode="after")
    def chronology(self):
        if len({row.interval_id for row in self.intervals}) != len(self.intervals):
            raise ValueError("condition interval IDs must be unique")
        if any(
            left.end_s != right.start_s
            for left, right in zip(self.intervals[:-1], self.intervals[1:], strict=True)
        ):
            raise ValueError("condition intervals must be ordered and contiguous")
        return self


def evaluate_condition_loss_history(request: ConditionLossHistory) -> dict:
    base = dict(
        history_id=request.history_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        rate_results=[],
        integrated_loss=None,
    )
    if not request.piecewise_constant_conditions_and_rate_integration_reviewed:
        return base
    rates = [
        evaluate_condition_loss_rate(ConditionLossRateAssessment(law=request.law, condition=row.condition))
        for row in request.intervals
    ]
    base["rate_results"] = rates
    if any(row["status"] != "computed" for row in rates):
        return base | dict(
            status="out_of_scope" if any(row["status"] == "out_of_scope" for row in rates) else "needs_data",
            reason="Every condition must have a supported calibrated rate; no interval was dropped",
        )
    law = request.law
    history = CalibratedDamageHistory(
        history_id=request.history_id,
        mechanism=law.mechanism,
        material_condition_id=law.material_condition_id,
        physical_location_id=request.physical_location_id,
        calibrated_rate_and_mechanism_reviewed=True,
        intervals=tuple(
            CalibratedDamageInterval(
                interval_id=interval.interval_id,
                start_s=interval.start_s,
                end_s=interval.end_s,
                loss_rate_m_s=rate["loss_rate_m_s"],
                provider_id=law.provider_id,
                provider_revision=law.provider_revision,
                calibration_sha256=law.calibration_sha256,
                condition_sha256=canonical_digest(interval.condition.model_dump(mode="json")),
                condition_within_calibration_support_reviewed=True,
            )
            for interval, rate in zip(request.intervals, rates, strict=True)
        ),
    )
    integrated = integrate_calibrated_damage(history)
    return base | dict(
        status=integrated["status"],
        integrated_loss=integrated,
        basis="Complete piecewise-constant calibrated condition history; failed intervals withhold the total. No cross-mechanism rate addition, structural capacity, life qualification or failure probability.",
    )
