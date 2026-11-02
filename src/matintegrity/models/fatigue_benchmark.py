"""Benchmark metrics and endpoint screens for caller-supplied fatigue observations."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Positive
from ..registry import ModelSpec


class CyclicResponseSeries(Contract):
    """One experiment's aligned observed and predicted cyclic descriptors."""

    experiment_id: str = Field(min_length=1)
    cycle: list[Positive] = Field(min_length=1)
    observed_mean: list[float] = Field(min_length=1)
    predicted_mean: list[float] = Field(min_length=1)
    observed_amplitude: list[float] = Field(min_length=1)
    predicted_amplitude: list[float] = Field(min_length=1)
    mean_normalizer: Positive
    amplitude_normalizer: Positive

    @model_validator(mode="after")
    def aligned_and_ordered(self):
        lengths = {
            len(self.cycle),
            len(self.observed_mean),
            len(self.predicted_mean),
            len(self.observed_amplitude),
            len(self.predicted_amplitude),
        }
        if len(lengths) != 1:
            raise ValueError("cycle and cyclic-response arrays must align")
        if any(right <= left for left, right in zip(self.cycle, self.cycle[1:], strict=False)):
            raise ValueError("cycle values must be strictly increasing in supplied order")
        if any(value < 0 for value in self.observed_amplitude + self.predicted_amplitude):
            raise ValueError("cyclic amplitudes must be nonnegative")
        return self


class CyclicResponseRelativeError(Contract):
    """Balanced mean/amplitude discrepancy across preselected experiments."""

    series: list[CyclicResponseSeries] = Field(min_length=1)
    mean_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    amplitude_weight: float = Field(default=0.4, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def unique_and_weighted(self):
        identities = [item.experiment_id for item in self.series]
        if len(identities) != len(set(identities)):
            raise ValueError("experiment identifiers must be unique")
        if not math.isclose(self.mean_weight + self.amplitude_weight, 1.0, abs_tol=1e-12):
            raise ValueError("mean and amplitude weights must sum to one")
        return self


def cyclic_response_relative_error(x: CyclicResponseRelativeError) -> Calculation:
    """Average normalized absolute errors without altering the supplied sampling grid."""
    experiment_rows = []
    for item in x.series:
        mean_terms = [
            abs(predicted - observed) / item.mean_normalizer
            for observed, predicted in zip(item.observed_mean, item.predicted_mean, strict=True)
        ]
        amplitude_terms = [
            abs(predicted - observed) / item.amplitude_normalizer
            for observed, predicted in zip(item.observed_amplitude, item.predicted_amplitude, strict=True)
        ]
        point_terms = [
            x.mean_weight * mean_term + x.amplitude_weight * amplitude_term
            for mean_term, amplitude_term in zip(mean_terms, amplitude_terms, strict=True)
        ]
        experiment_rows.append(
            {
                "experiment_id": item.experiment_id,
                "sample_count": len(item.cycle),
                "mean_absolute_relative_error": sum(mean_terms) / len(mean_terms),
                "amplitude_absolute_relative_error": sum(amplitude_terms) / len(amplitude_terms),
                "weighted_relative_error": sum(point_terms) / len(point_terms),
            }
        )
    score = sum(row["weighted_relative_error"] for row in experiment_rows) / len(experiment_rows)
    return Calculation(
        values={
            "experiment_count": len(experiment_rows),
            "mean_weight": x.mean_weight,
            "amplitude_weight": x.amplitude_weight,
            "aggregate_weighted_relative_error": score,
            "experiment_errors": experiment_rows,
        },
        notes=(
            "Each experiment contributes equally after averaging its own supplied cycle rows; dense traces do not receive extra experiment weight.",
            "Normalizers are explicit positive inputs. They are not inferred from a possibly zero first-cycle mean or from the prediction.",
            "This score compares supplied arrays only; it does not establish model validity, parameter identifiability, fatigue life or acceptance.",
        ),
    )


class FatigueLifeRmsle(Contract):
    """Positive observed and predicted lives for a predeclared comparison set."""

    case_id: list[str] = Field(min_length=1)
    observed_cycles: list[Positive] = Field(min_length=1)
    predicted_cycles: list[Positive] = Field(min_length=1)
    logarithm_base: Literal[10, "e"] = 10

    @model_validator(mode="after")
    def aligned_and_unique(self):
        if not len(self.case_id) == len(self.observed_cycles) == len(self.predicted_cycles):
            raise ValueError("case identifiers and fatigue-life arrays must align")
        if len(self.case_id) != len(set(self.case_id)):
            raise ValueError("fatigue-life case identifiers must be unique")
        return self


def fatigue_life_rmsle(x: FatigueLifeRmsle) -> Calculation:
    """Return the root mean square log-life residual and every signed residual."""
    log = math.log10 if x.logarithm_base == 10 else math.log
    residuals = [
        log(predicted) - log(observed)
        for observed, predicted in zip(x.observed_cycles, x.predicted_cycles, strict=True)
    ]
    return Calculation(
        values={
            "case_count": len(x.case_id),
            "logarithm_base": x.logarithm_base,
            "root_mean_square_log_error": math.sqrt(
                sum(residual * residual for residual in residuals) / len(residuals)
            ),
            "case_log_residuals": [
                {"case_id": case_id, "log_residual": residual}
                for case_id, residual in zip(x.case_id, residuals, strict=True)
            ],
        },
        notes=(
            "Only positive finite lives are accepted; censored tests and missing outcomes require a separate likelihood or survival-analysis contract.",
            "The metric is descriptive for the exact declared cases and does not prove calibration, transferability, uncertainty coverage or acceptance.",
        ),
    )


class DynamicModulusDropEndpoint(Contract):
    """First sampled or linearly bracketed crossing of a declared modulus-loss threshold."""

    test_id: str = Field(min_length=1)
    cycle: list[Positive] = Field(min_length=2)
    compressive_dynamic_modulus_Pa: list[Positive] = Field(min_length=2)
    reference_dynamic_modulus_Pa: Positive
    drop_fraction_threshold: float = Field(gt=0.0, lt=1.0)
    crossing_policy: Literal["first_observed_sample", "linear_between_samples"] = "first_observed_sample"
    observation_window_closed: bool

    @model_validator(mode="after")
    def aligned_and_ordered(self):
        if len(self.cycle) != len(self.compressive_dynamic_modulus_Pa):
            raise ValueError("cycle and dynamic-modulus arrays must align")
        if any(right <= left for left, right in zip(self.cycle, self.cycle[1:], strict=False)):
            raise ValueError("cycle values must be strictly increasing in supplied order")
        return self


def dynamic_modulus_drop_endpoint(x: DynamicModulusDropEndpoint) -> Calculation:
    """Locate a declared loss crossing while retaining right-censoring and policy meaning."""
    threshold = x.reference_dynamic_modulus_Pa * (1.0 - x.drop_fraction_threshold)
    crossing_index = next(
        (index for index, modulus in enumerate(x.compressive_dynamic_modulus_Pa) if modulus <= threshold),
        None,
    )
    endpoint_cycle = None
    endpoint_role = "not_reached_open_window"
    status: Literal["computed", "needs_data"] = "needs_data"
    bracket = None
    if crossing_index is not None:
        status = "computed"
        endpoint_role = "observed_threshold_crossing"
        endpoint_cycle = x.cycle[crossing_index]
        if x.crossing_policy == "linear_between_samples" and crossing_index > 0:
            left_cycle, right_cycle = x.cycle[crossing_index - 1 : crossing_index + 1]
            left_modulus, right_modulus = x.compressive_dynamic_modulus_Pa[
                crossing_index - 1 : crossing_index + 1
            ]
            if left_modulus > threshold and right_modulus < left_modulus:
                fraction = (threshold - left_modulus) / (right_modulus - left_modulus)
                endpoint_cycle = left_cycle + fraction * (right_cycle - left_cycle)
                bracket = [left_cycle, right_cycle]
    elif x.observation_window_closed:
        status = "computed"
        endpoint_role = "right_censored_no_crossing"

    return Calculation(
        status=status,
        values={
            "test_id": x.test_id,
            "reference_dynamic_modulus_Pa": x.reference_dynamic_modulus_Pa,
            "threshold_dynamic_modulus_Pa": threshold,
            "drop_fraction_threshold": x.drop_fraction_threshold,
            "crossing_policy": x.crossing_policy,
            "endpoint_cycle": endpoint_cycle,
            "crossing_bracket_cycles": bracket,
            "endpoint_role": endpoint_role,
            "last_observed_cycle": x.cycle[-1],
        },
        notes=(
            "The reference modulus and loss fraction are caller-declared; neither is estimated from the trace.",
            "Linear interpolation is used only when explicitly selected and only across the first descending threshold bracket; no smoothing or extrapolation is applied.",
            "A threshold crossing is a test endpoint under the declared convention, not a structural failure probability, design life or acceptance result.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "fatigue.cyclic_response_relative_error",
            CyclicResponseRelativeError,
            cyclic_response_relative_error,
            {
                "experiment_count": "1",
                "mean_weight": "1",
                "amplitude_weight": "1",
                "aggregate_weighted_relative_error": "1",
            },
            (
                "Caller-supplied observed/predicted mean and amplitude arrays share strict cycle alignment, explicit positive normalization and a predeclared experiment set.",
                "The default 0.6/0.4 balance is configurable and experiment-level averaging prevents unequal trace lengths from changing experiment weights.",
            ),
            ("fabest_lcf_rules_2026", "normalized_absolute_error"),
            qualification="engineering_screening",
        ),
        ModelSpec(
            "fatigue.life_rmsle",
            FatigueLifeRmsle,
            fatigue_life_rmsle,
            {"case_count": "1", "root_mean_square_log_error": "1"},
            (
                "Caller supplies one positive observed and predicted life for every unique predeclared case; censoring is outside this metric.",
            ),
            ("fabest_lcf_rules_2026", "root_mean_square_log_error"),
            qualification="engineering_screening",
        ),
        ModelSpec(
            "fatigue.dynamic_modulus_drop_endpoint",
            DynamicModulusDropEndpoint,
            dynamic_modulus_drop_endpoint,
            {
                "reference_dynamic_modulus_Pa": "Pa",
                "threshold_dynamic_modulus_Pa": "Pa",
                "drop_fraction_threshold": "1",
                "endpoint_cycle": "cycle",
                "last_observed_cycle": "cycle",
            },
            (
                "Caller supplies a strictly ordered compressive-branch dynamic-modulus history, explicit reference modulus, loss threshold and closed/open observation-window state.",
                "The default reports the first observed crossing; between-sample interpolation requires an explicit policy and a descending bracket.",
            ),
            ("fabest_lcf_rules_2026", "dynamic_modulus_endpoint"),
            qualification="engineering_screening",
        ),
    ]
