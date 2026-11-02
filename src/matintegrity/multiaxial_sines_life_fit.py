"""Fit a caller-qualified log-log life relation to finite Sines descriptors."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .multiaxial_sines_mean_limit_screen import (
    MultiaxialSinesMeanLimitScreen,
    evaluate_multiaxial_sines_mean_limit_screen,
)
from .registry import ModelSpec


MODEL_ID = "fatigue.multiaxial_sines_life_fit"
OBSERVATION_SOURCE_ID = "caller_multiaxial_sines_life_calibration_tests"
FIT_SOURCE_ID = "finite_sines_parameter_loglog_ordinary_least_squares"
REFERENCE_PARAMETER_PA = 1.0e6


class SinesLifeCalibrationTest(Contract):
    """One uncensored failure test with a reviewed closed stress cycle."""

    test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    cycles_to_failure: Positive
    observation_evidence: Evidence
    screen: MultiaxialSinesMeanLimitScreen


class MultiaxialSinesLifeFit(Contract):
    """Fit a bounded Sines-parameter/life relation from same-condition tests."""

    campaign_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    tests: tuple[SinesLifeCalibrationTest, ...] = Field(min_length=3, max_length=10000)
    fit_source_id: str = FIT_SOURCE_ID
    independent_specimen_identity_reviewed: bool
    failure_endpoint_and_observation_rights_reviewed: bool
    loglog_power_law_form_and_fit_domain_reviewed: bool

    @model_validator(mode="after")
    def validate_campaign(self):
        if self.fit_source_id != FIT_SOURCE_ID:
            raise ValueError("fit_source_id must name the declared finite log-log OLS procedure")
        if len({row.test_id for row in self.tests}) != len(self.tests):
            raise ValueError("test_id values must be unique")
        if len({row.physical_specimen_id for row in self.tests}) != len(self.tests):
            raise ValueError("each calibration test must identify a distinct physical specimen")
        if len({row.source_record_id for row in self.tests}) != len(self.tests):
            raise ValueError("source_record_id values must be unique")
        for row in self.tests:
            if row.screen.calibration_material_condition_id != self.material_condition_id:
                raise ValueError("every Sines screen must match the campaign material condition")
            if row.observation_evidence.sha256 is None:
                raise ValueError("each test outcome must carry an immutable source digest")
            if row.observation_evidence.origin not in {"measured", "open_dataset"}:
                raise ValueError("life calibration outcomes must come from measured/open-dataset evidence")
        first = self.tests[0].screen
        invariant_fields = (
            "calibration_id",
            "calibration_source_id",
            "calibration_sha256",
            "calibration_material_condition_id",
            "deviatoric_coefficient",
            "mean_hydrostatic_coefficient",
            "caller_limit_Pa",
        )
        for row in self.tests[1:]:
            if any(getattr(row.screen, key) != getattr(first, key) for key in invariant_fields):
                raise ValueError("all tests must use exactly the same Sines coefficients, limit and calibration")
        return self


def evaluate_multiaxial_sines_life_fit(request: MultiaxialSinesLifeFit) -> Calculation:
    """Fit log(N)=intercept+slope*log(P/1 MPa) to caller failure observations."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "campaign_id": request.campaign_id,
        "material_condition_id": request.material_condition_id,
        "fit_source_id": request.fit_source_id,
        "input_sha256": input_digest,
        "reference_parameter_Pa": REFERENCE_PARAMETER_PA,
        "observation_count": len(request.tests),
    }
    if not all((
        request.independent_specimen_identity_reviewed,
        request.failure_endpoint_and_observation_rights_reviewed,
        request.loglog_power_law_form_and_fit_domain_reviewed,
    )):
        return Calculation(
            status="needs_data",
            values=base | {
                "reason": "specimen_endpoint_rights_and_loglog_fit_review_required",
                "fitted_log_cycles_intercept": None,
                "fitted_loglog_exponent": None,
                "parameter_support_Pa": None,
                "observations": [],
            },
        )

    observations = []
    for row in request.tests:
        screen = evaluate_multiaxial_sines_mean_limit_screen(row.screen)
        if screen["status"] != "computed":
            return Calculation(
                status=screen["status"],
                values=base | {
                    "reason": f"sines_screen_unavailable_for_test:{row.test_id}",
                    "fitted_log_cycles_intercept": None,
                    "fitted_loglog_exponent": None,
                    "parameter_support_Pa": None,
                    "observations": [{
                        "test_id": row.test_id,
                        "status": screen["status"],
                        "screen": screen,
                    }],
                },
            )
        parameter = screen["screening_parameter_Pa"]
        cycles = row.cycles_to_failure
        if not math.isfinite(parameter) or parameter <= 0.0 or not math.isfinite(cycles):
            return Calculation(
                status="out_of_scope",
                values=base | {
                    "reason": f"nonpositive_or_nonfinite_parameter_or_life:{row.test_id}",
                    "fitted_log_cycles_intercept": None,
                    "fitted_loglog_exponent": None,
                    "parameter_support_Pa": None,
                    "observations": [],
                },
            )
        observations.append({
            "test_id": row.test_id,
            "physical_specimen_id": row.physical_specimen_id,
            "source_group_id": row.source_group_id,
            "source_record_id": row.source_record_id,
            "observation_evidence_source_id": row.observation_evidence.source_id,
            "observation_evidence_sha256": row.observation_evidence.sha256,
            "screening_parameter_Pa": parameter,
            "observed_cycles_to_failure": cycles,
            "screen_input_sha256": screen["input_sha256"],
            "screen_output": screen,
        })

    parameters = [row["screening_parameter_Pa"] for row in observations]
    lives = [row["observed_cycles_to_failure"] for row in observations]
    if len({round(value, 12) for value in parameters}) < 3:
        return Calculation(
            status="needs_data",
            values=base | {
                "reason": "at_least_three_distinct_positive_sines_parameters_required",
                "fitted_log_cycles_intercept": None,
                "fitted_loglog_exponent": None,
                "parameter_support_Pa": [min(parameters), max(parameters)],
                "observations": observations,
            },
        )

    x_values = [math.log(value / REFERENCE_PARAMETER_PA) for value in parameters]
    y_values = [math.log(value) for value in lives]
    mean_x = math.fsum(x_values) / len(x_values)
    mean_y = math.fsum(y_values) / len(y_values)
    sxx_terms = [(value - mean_x) ** 2 for value in x_values]
    sxy_terms = [(x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values, strict=True)]
    sxx = math.fsum(sxx_terms)
    if not math.isfinite(sxx) or sxx <= 0.0:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "log_parameter_variance_unresolved",
                "fitted_log_cycles_intercept": None,
                "fitted_loglog_exponent": None,
                "parameter_support_Pa": [min(parameters), max(parameters)],
                "observations": observations,
            },
        )
    slope = math.fsum(sxy_terms) / sxx
    intercept = mean_y - slope * mean_x
    if not math.isfinite(slope) or not math.isfinite(intercept) or slope >= 0.0:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "fitted_life_must_decrease_with_increasing_sines_parameter",
                "fitted_log_cycles_intercept": intercept if math.isfinite(intercept) else None,
                "fitted_loglog_exponent": slope if math.isfinite(slope) else None,
                "parameter_support_Pa": [min(parameters), max(parameters)],
                "observations": observations,
            },
        )
    residuals = [y - (intercept + slope * x) for x, y in zip(x_values, y_values, strict=True)]
    total_sum_squares = math.fsum((value - mean_y) ** 2 for value in y_values)
    residual_sum_squares = math.fsum(value * value for value in residuals)
    if total_sum_squares <= 0.0 or not math.isfinite(residual_sum_squares):
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "life_observation_variance_unresolved",
                "fitted_log_cycles_intercept": None,
                "fitted_loglog_exponent": None,
                "parameter_support_Pa": [min(parameters), max(parameters)],
                "observations": observations,
            },
        )
    r_squared = 1.0 - residual_sum_squares / total_sum_squares
    predicted_lives = [math.exp(intercept + slope * x) for x in x_values]
    if not all(math.isfinite(value) for value in (*predicted_lives, r_squared)):
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "fit_outputs_nonfinite",
                "fitted_log_cycles_intercept": None,
                "fitted_loglog_exponent": None,
                "parameter_support_Pa": [min(parameters), max(parameters)],
                "observations": observations,
            },
        )
    for observation, prediction in zip(observations, predicted_lives, strict=True):
        observation["fitted_cycles_to_failure"] = prediction
        observation["log_life_residual"] = math.log(observation["observed_cycles_to_failure"] / prediction)
    return Calculation(
        status="computed",
        values=base | {
            "fitted_log_cycles_intercept_at_reference_parameter": intercept,
            "fitted_loglog_exponent": slope,
            "reference_parameter_Pa": REFERENCE_PARAMETER_PA,
            "parameter_support_Pa": [min(parameters), max(parameters)],
            "fit_r_squared_log_life": r_squared,
            "observations": observations,
            "fit_interpretation": "ordinary_least_squares_on_log_cycles_vs_log_parameter; calibration_descriptive_not_independent_validation",
        },
        notes=(
            "The fit uses only uncensored caller-declared failure lives with distinct reviewed physical specimens.",
            "The fitted relation is intended only within the observed parameter support and exact declared material condition.",
            "Fit residuals and R-squared describe the calibration sample; they are not independent validation or a prediction interval.",
            "No cycle counting, variable-amplitude accumulation, runout treatment, probability, acceptance or qualification is provided.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=MultiaxialSinesLifeFit,
        evaluator=evaluate_multiaxial_sines_life_fit,
        units={
            "fitted_log_cycles_intercept_at_reference_parameter": "1",
            "fitted_loglog_exponent": "1",
            "reference_parameter_Pa": "Pa",
            "parameter_support_Pa[]": "Pa",
            "fit_r_squared_log_life": "1",
            "observations[].screening_parameter_Pa": "Pa",
            "observations[].observed_cycles_to_failure": "cycle",
            "observations[].fitted_cycles_to_failure": "cycle",
        },
        assumptions=(
            "Fits a single log-log power relation by unweighted ordinary least squares to caller-declared uncensored failures.",
            "Each observation uses the same caller Sines coefficients and exact material condition with a distinct reviewed physical specimen.",
            "R-squared and residuals describe calibration only; independent validation, runout censoring and prediction intervals are not provided.",
        ),
        source_ids=(
            "caller_finite_sample_sines_mean_hydrostatic_limit_screen",
            OBSERVATION_SOURCE_ID,
            FIT_SOURCE_ID,
        ),
        qualification="user_model",
    )]
