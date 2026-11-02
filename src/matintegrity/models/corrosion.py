"""Mass conservation, electrochemistry and observation-based degradation."""

from __future__ import annotations

import math
from fractions import Fraction as Rational
from typing import Literal

import numpy as np
from pydantic import Field, field_validator, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from ..units import SECONDS_PER_YEAR
from ..wet_co2_data import WetCo2SimulationGridRow


class CouponLoss(Contract):
    mass_loss_kg: Nonnegative
    exposed_area_m2: Positive
    density_kg_m3: Positive
    duration_s: Positive


def _coupon_exact_nominal(mass, area, density, duration):
    penetration = Rational(mass) / (Rational(area) * Rational(density))
    rate = penetration / Rational(duration)
    return penetration, rate, rate * 1000 * Rational(SECONDS_PER_YEAR)


def _finite_rational_result(value):
    result = float(value)
    if not math.isfinite(result) or (value and result == 0):
        raise ArithmeticError("result exceeds nonzero finite numeric support")
    return result


def _coupon_sqrt(value):
    if value == 0:
        return 0.0
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    half_exponent = exponent // 2
    normalized = value / Rational(2) ** (2 * half_exponent)
    result = math.ldexp(math.sqrt(float(normalized)), half_exponent)
    if not math.isfinite(result) or result == 0:
        raise ArithmeticError("coupon standard uncertainty exceeds numeric support")
    return result


def coupon_loss(x: CouponLoss) -> Calculation:
    try:
        penetration, rate, annual = _coupon_exact_nominal(
            x.mass_loss_kg, x.exposed_area_m2, x.density_kg_m3, x.duration_s
        )
        values = dict(
            mean_penetration_m=_finite_rational_result(penetration),
            rate_m_s=_finite_rational_result(rate),
            rate_mm_year=_finite_rational_result(annual),
        )
    except ArithmeticError:
        return Calculation(
            status="out_of_scope", values={"reason": "coupon result exceeds finite arithmetic support"}
        )
    return Calculation(values=values)


class CouponLossWithUncertainty(Contract):
    """Caller-reviewed mass-loss result with a full input covariance matrix."""

    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    condition_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    measurement_method: str = Field(min_length=1)
    mass_loss_kg: Nonnegative
    exposed_area_m2: Positive
    density_kg_m3: Positive
    duration_s: Positive
    covariance_matrix: list[list[float]] = Field(min_length=4, max_length=4)
    covariance_basis: str = Field(min_length=1)
    condition_signature: dict[str, str | float | int | bool]
    measurement_reviewed: bool
    measurement_review_id: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_covariance_and_review(self):
        identifiers = (
            self.observation_id,
            self.physical_specimen_id,
            self.material_id,
            self.condition_group_id,
            self.source_group_id,
            self.measurement_method,
            self.covariance_basis,
        )
        if any(not value.strip() for value in identifiers):
            raise ValueError("measurement identity and covariance basis fields cannot be blank")
        if not self.condition_signature or any(not key.strip() for key in self.condition_signature):
            raise ValueError("a non-empty flat condition signature is required")
        if any(type(value) not in {str, int, float, bool} for value in self.condition_signature.values()):
            raise ValueError("condition signature values must be flat JSON scalars")
        matrix = np.asarray(self.covariance_matrix, dtype=float)
        if matrix.shape != (4, 4) or not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-18):
            raise ValueError("covariance_matrix must be symmetric 4x4")
        diagonal = np.diag(matrix)
        if np.any(diagonal < 0.0):
            raise ValueError("covariance_matrix diagonal variances cannot be negative")
        standard_deviations = np.sqrt(diagonal)
        scales = np.outer(standard_deviations, standard_deviations)
        correlation = np.zeros_like(matrix)
        nonzero_scale = scales > 0.0
        correlation[nonzero_scale] = matrix[nonzero_scale] / scales[nonzero_scale]
        covariance_scale = max(float(np.max(np.abs(matrix))), 1e-30)
        if np.any(np.abs(matrix[~nonzero_scale]) > covariance_scale * 1e-12):
            raise ValueError("zero-variance covariance rows must have zero covariances")
        if float(np.min(np.linalg.eigvalsh(correlation))) < -1e-10:
            raise ValueError("covariance_matrix must be positive semidefinite")
        if self.measurement_reviewed and (
            self.measurement_review_id is None or not self.measurement_review_id.strip()
        ):
            raise ValueError("reviewed measurement requires a traceable measurement_review_id")
        return self


def coupon_loss_with_uncertainty(x: CouponLossWithUncertainty) -> Calculation:
    """Propagate caller-declared joint input uncertainty through uniform mass loss."""

    if not x.measurement_reviewed:
        return Calculation(
            status="needs_data",
            values={"observation_id": x.observation_id, "reason": "measurement_review_required"},
            notes=(
                "Review corrected mass loss, exposed area, material density, duration and covariance before use.",
            ),
        )

    mass, area, density, duration = map(
        Rational, (x.mass_loss_kg, x.exposed_area_m2, x.density_kg_m3, x.duration_s)
    )
    penetration_exact, rate_exact, annual_exact = _coupon_exact_nominal(mass, area, density, duration)
    gradient = (
        1 / (area * density * duration),
        -rate_exact / area,
        -rate_exact / density,
        -rate_exact / duration,
    )
    penetration_gradient = (
        1 / (area * density),
        -penetration_exact / area,
        -penetration_exact / density,
        Rational(0),
    )
    covariance = tuple(tuple(Rational(value) for value in row) for row in x.covariance_matrix)

    def variance(g):
        value = sum((g[i] * covariance[i][j] * g[j] for i in range(4) for j in range(4)), Rational(0))
        scale = max(max(abs(value) for row in covariance for value in row), Rational(1e-30))
        tolerance = scale * sum((value * value for value in g), Rational(0)) * Rational(1e-12)
        if value < -tolerance:
            raise ValueError("propagated variance is materially negative")
        return max(Rational(0), value)

    try:
        penetration = _finite_rational_result(penetration_exact)
        rate = _finite_rational_result(rate_exact)
        annual = _finite_rational_result(annual_exact)
        rate_standard_uncertainty = _coupon_sqrt(variance(gradient))
        penetration_standard_uncertainty = _coupon_sqrt(variance(penetration_gradient))
        relative_uncertainty = (
            _finite_rational_result(Rational(rate_standard_uncertainty) / rate_exact) if rate_exact else None
        )
    except ArithmeticError:
        return Calculation(
            status="out_of_scope",
            values={
                "observation_id": x.observation_id,
                "reason": "coupon result or uncertainty exceeds finite arithmetic support",
            },
        )
    input_payload = x.model_dump(mode="json")
    return Calculation(
        values={
            "observation_id": x.observation_id,
            "physical_specimen_id": x.physical_specimen_id,
            "material_id": x.material_id,
            "condition_group_id": x.condition_group_id,
            "source_group_id": x.source_group_id,
            "measurement_method": x.measurement_method,
            "condition_signature": x.condition_signature,
            "condition_signature_sha256": canonical_digest(x.condition_signature),
            "mean_penetration_m": penetration,
            "rate_m_s": rate,
            "rate_mm_year": annual,
            "rate_standard_uncertainty_m_s": rate_standard_uncertainty,
            "rate_relative_standard_uncertainty": relative_uncertainty,
            "penetration_standard_uncertainty_m": penetration_standard_uncertainty,
            "covariance_basis": x.covariance_basis,
            "covariance_variable_order": ["mass_loss_kg", "exposed_area_m2", "density_kg_m3", "duration_s"],
            "measurement_review_id": x.measurement_review_id,
            "input_record_sha256": canonical_digest(input_payload),
            "evidence_ids": [item.source_id for item in x.evidence],
            "uncertainty_method": "first_order_delta_method_with_caller_joint_covariance",
        },
        notes=(
            "Mass loss is assumed corrected by the caller for blanks, cleaning effects and non-corrosion changes; the module does not apply a standard-specific correction.",
            "Standard uncertainty is a first-order propagation using the supplied covariance matrix; it is not a confidence or prediction interval.",
            "Uniform average penetration does not describe localized attack, corrosion mechanism, remaining life, acceptance or failure probability.",
        ),
    )


class FaradayLoss(Contract):
    current_density_A_m2: Nonnegative
    molar_mass_kg_mol: Positive
    electrons_per_atom: Positive
    density_kg_m3: Positive
    current_efficiency: float = Field(ge=0, le=1)
    duration_s: Positive


def faraday_loss(x: FaradayLoss) -> Calculation:
    try:
        exact_rate = (
            Rational(x.current_efficiency)
            * Rational(x.current_density_A_m2)
            * Rational(x.molar_mass_kg_mol)
            / (Rational(x.electrons_per_atom) * Rational(96485.33212331001) * Rational(x.density_kg_m3))
        )
        values = dict(
            rate_m_s=_finite_rational_result(exact_rate),
            penetration_m=_finite_rational_result(exact_rate * Rational(x.duration_s)),
        )
    except ArithmeticError:
        return Calculation(
            status="out_of_scope", values={"reason": "Faraday result exceeds finite arithmetic support"}
        )
    return Calculation(
        values=values,
        notes=(
            "Caller-declared dissolution current, efficiency, valence and density; no net-current separation or mechanism inference.",
            "Zero declared current or efficiency produces exact zero; missing efficiency is not assigned zero.",
        ),
    )


class ThicknessTrend(Contract):
    time_s: list[Nonnegative] = Field(min_length=3)
    thickness_m: list[Positive] = Field(min_length=3)
    method: Literal["ols", "theil_sen"] = "theil_sen"

    @model_validator(mode="after")
    def align(self):
        if len(self.time_s) != len(self.thickness_m) or np.any(np.diff(self.time_s) <= 0):
            raise ValueError("aligned observations with strictly increasing times required")
        return self


def thickness_trend(x: ThicknessTrend) -> Calculation:
    time = (np.asarray(x.time_s) - x.time_s[0]) / SECONDS_PER_YEAR
    thickness = np.asarray(x.thickness_m) * 1000
    if x.method == "theil_sen":
        from scipy.stats import theilslopes

        fit = theilslopes(thickness, time, method="joint")
        slope, intercept = float(fit.slope), float(fit.intercept)
        interval = [
            -float(fit.high_slope) / 1000 / SECONDS_PER_YEAR,
            -float(fit.low_slope) / 1000 / SECONDS_PER_YEAR,
        ]
    else:
        slope, intercept = (float(v) for v in np.polyfit(time, thickness, 1))
        interval = None
    residual = thickness - (intercept + slope * time)
    notes = (
        ("Trend is not distinguishable from thickness increase; check measurement and repair history.",)
        if slope >= 0
        else ()
    )
    return Calculation(
        values=dict(
            rate_m_s=-slope / 1000 / SECONDS_PER_YEAR,
            thickness_at_first_time_m=intercept / 1000,
            residual_rmse_m=float(np.sqrt(np.mean(residual**2))) / 1000,
            rate_interval_m_s=interval,
        ),
        notes=notes,
    )


class UniformForecast(Contract):
    current_thickness_m: Positive
    required_thickness_m: Positive
    rate_m_s: Nonnegative
    horizon_s: Nonnegative


def uniform_forecast(x: UniformForecast) -> Calculation:
    margin = x.current_thickness_m - x.required_thickness_m
    if margin <= 0:
        life, interpretation = 0.0, "required thickness reached or exceeded"
    elif x.rate_m_s == 0:
        life, interpretation = None, "no finite crossing under the declared zero-growth model"
    else:
        life, interpretation = margin / x.rate_m_s, "linear extrapolation under fixed conditions"
    remaining = x.current_thickness_m - x.rate_m_s * x.horizon_s
    exhausted = remaining <= 0
    return Calculation(
        status="out_of_scope" if exhausted else "computed",
        values=dict(
            thickness_margin_m=margin,
            predicted_thickness_m=None if exhausted else remaining,
            forecast_margin_m=None if exhausted else remaining - x.required_thickness_m,
            time_to_required_s=life,
        ),
        notes=(interpretation, "Loss of positive wall thickness invalidates continued linear evolution."),
    )


class PowerLawPenetration(Contract):
    coefficient_m: Nonnegative
    exponent: Positive
    exposure_s: Nonnegative
    reference_time_s: Positive


def power_law(x: PowerLawPenetration) -> Calculation:
    return Calculation(
        values={"penetration_m": x.coefficient_m * (x.exposure_s / x.reference_time_s) ** x.exponent}
    )


class ArrheniusRate(Contract):
    reference_rate: Nonnegative
    reference_temperature_K: Positive
    temperature_K: Positive
    activation_energy_J_mol: Nonnegative


class MaterialCorrosionRateContrast(Contract):
    """Compare two reported uniform-loss rates under one caller-declared condition group."""

    comparison_id: str = Field(min_length=1)
    numerator_material_id: str = Field(min_length=1)
    reference_material_id: str = Field(min_length=1)
    numerator_rate_m_s: Nonnegative
    reference_rate_m_s: Nonnegative
    condition_signature: dict[str, str | float | int | bool]
    condition_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    measurement_method: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_contrast(self):
        if self.numerator_material_id == self.reference_material_id:
            raise ValueError("numerator and reference material identities must differ")
        if not self.condition_signature:
            raise ValueError("condition_signature must contain reviewed comparison conditions")
        if any(not key.strip() for key in self.condition_signature):
            raise ValueError("condition_signature keys must be non-empty")
        return self

    @field_validator("condition_signature")
    @classmethod
    def validate_condition_signature(cls, value):
        if not value:
            return value
        if any(type(item) not in {str, int, float, bool} for item in value.values()):
            raise ValueError("condition_signature values must be flat JSON scalar values")
        return value


def material_corrosion_rate_contrast(x: MaterialCorrosionRateContrast) -> Calculation:
    ratio = x.numerator_rate_m_s / x.reference_rate_m_s if x.reference_rate_m_s > 0 else None
    log_ratio = math.log(ratio) if ratio is not None and ratio > 0 else None
    return Calculation(
        values={
            "comparison_id": x.comparison_id,
            "numerator_material_id": x.numerator_material_id,
            "reference_material_id": x.reference_material_id,
            "condition_group_id": x.condition_group_id,
            "source_group_id": x.source_group_id,
            "condition_signature": x.condition_signature,
            "condition_signature_sha256": canonical_digest(x.condition_signature),
            "measurement_method": x.measurement_method,
            "numerator_rate_m_s": x.numerator_rate_m_s,
            "reference_rate_m_s": x.reference_rate_m_s,
            "rate_difference_m_s": x.numerator_rate_m_s - x.reference_rate_m_s,
            "rate_ratio": ratio,
            "log_rate_ratio": log_ratio,
        },
        notes=(
            "Descriptive contrast of caller-supplied uniform-loss rates under a declared shared condition group.",
            "A zero reference rate makes the ratio undefined; a zero numerator makes the logarithmic ratio undefined.",
            "The ratio is not a material ranking, causal weld effect, transferable multiplier, acceptance result, life estimate, or probability.",
        ),
    )


class CorrosionRateObservation(Contract):
    """One rate summary per explicitly identified physical specimen."""

    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    rate_m_s: Nonnegative
    condition_signature: dict[str, str | float | int | bool]
    condition_group_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    measurement_method: str = Field(min_length=1)
    rate_standard_uncertainty_m_s: Nonnegative | None = None
    rate_uncertainty_basis: str | None = None
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def validate_uncertainty_lineage(self):
        if (self.rate_standard_uncertainty_m_s is None) != (self.rate_uncertainty_basis is None):
            raise ValueError("rate uncertainty and its basis must either both be present or both be absent")
        if self.rate_uncertainty_basis is not None and not self.rate_uncertainty_basis.strip():
            raise ValueError("rate uncertainty basis cannot be blank")
        return self

    @field_validator(
        "observation_id",
        "physical_specimen_id",
        "material_id",
        "condition_group_id",
        "source_group_id",
        "measurement_method",
    )
    @classmethod
    def validate_identifiers(cls, value):
        if not value.strip():
            raise ValueError("identifiers and measurement method cannot be blank")
        return value

    @field_validator("condition_signature")
    @classmethod
    def validate_conditions(cls, value):
        if not value or any(not key.strip() for key in value):
            raise ValueError("condition_signature must contain non-empty field names")
        if any(type(item) not in {str, int, float, bool} for item in value.values()):
            raise ValueError("condition_signature values must be flat JSON scalars")
        if any(isinstance(item, str) and not item.strip() for item in value.values()):
            raise ValueError("condition_signature text values cannot be blank")
        return value


def coupon_loss_input_to_rate_observation(x: CouponLossWithUncertainty) -> CorrosionRateObservation:
    """Convert one reviewed coupon calculation into a typed rate sample while retaining uncertainty lineage."""

    calculation = coupon_loss_with_uncertainty(x)
    if calculation.status != "computed":
        raise ValueError("only a reviewed coupon measurement can become a corrosion-rate observation")
    return CorrosionRateObservation(
        observation_id=x.observation_id,
        physical_specimen_id=x.physical_specimen_id,
        material_id=x.material_id,
        rate_m_s=calculation.values["rate_m_s"],
        condition_signature=x.condition_signature,
        condition_group_id=x.condition_group_id,
        source_group_id=x.source_group_id,
        measurement_method=x.measurement_method,
        rate_standard_uncertainty_m_s=calculation.values["rate_standard_uncertainty_m_s"],
        rate_uncertainty_basis=x.covariance_basis,
        evidence=x.evidence,
    )


class CorrosionRateSampleSummary(Contract):
    """Descriptive quantiles for unique specimens in one declared study condition."""

    observations: list[CorrosionRateObservation] = Field(min_length=1)
    quantile_probabilities: list[Fraction] = Field(default_factory=lambda: [0.25, 0.5, 0.75], min_length=1)
    measurement_error_covariance_m_s2: list[list[float]] | None = None

    @model_validator(mode="after")
    def validate_sample(self):
        rows = self.observations
        if len({row.observation_id for row in rows}) != len(rows):
            raise ValueError("observation IDs must be unique")
        if len({row.physical_specimen_id for row in rows}) != len(rows):
            raise ValueError("provide at most one rate summary per physical specimen")
        for field in (
            "material_id",
            "condition_signature",
            "condition_group_id",
            "source_group_id",
            "measurement_method",
        ):
            if any(getattr(row, field) != getattr(rows[0], field) for row in rows[1:]):
                raise ValueError(f"all observations must share the same {field}")
        if any(
            a >= b for a, b in zip(self.quantile_probabilities, self.quantile_probabilities[1:], strict=False)
        ):
            raise ValueError("quantile probabilities must be strictly increasing")
        if self.measurement_error_covariance_m_s2 is not None:
            covariance = np.asarray(self.measurement_error_covariance_m_s2, dtype=float)
            if covariance.shape != (len(rows), len(rows)):
                raise ValueError(
                    "measurement-error covariance must be square and aligned to observation order"
                )
            scale = max(float(np.max(np.abs(covariance))), 1e-300)
            if not np.allclose(covariance, covariance.T, rtol=1e-10, atol=scale * 1e-12):
                raise ValueError("measurement-error covariance must be symmetric")
            uncertainties = [row.rate_standard_uncertainty_m_s for row in rows]
            if any(value is None for value in uncertainties):
                raise ValueError("every observation needs a standard uncertainty when covariance is supplied")
            expected_variances = np.square(np.asarray(uncertainties, dtype=float))
            if not np.allclose(np.diag(covariance), expected_variances, rtol=1e-8, atol=1e-300):
                raise ValueError(
                    "measurement-error covariance diagonal must match rowwise standard uncertainties"
                )
            diagonal = np.diag(covariance)
            if np.any(diagonal < 0.0):
                raise ValueError("measurement-error covariance variances cannot be negative")
            standard_deviations = np.sqrt(diagonal)
            scales = np.outer(standard_deviations, standard_deviations)
            correlation = np.zeros_like(covariance)
            nonzero = scales > 0.0
            correlation[nonzero] = covariance[nonzero] / scales[nonzero]
            if np.any(np.abs(covariance[~nonzero]) > scale * 1e-12):
                raise ValueError("zero-variance observations must have zero cross-covariance")
            if float(np.min(np.linalg.eigvalsh(correlation))) < -1e-10:
                raise ValueError("measurement-error covariance must be positive semidefinite")
        return self


def corrosion_rate_sample_summary(x: CorrosionRateSampleSummary) -> Calculation:
    rates = np.asarray([row.rate_m_s for row in x.observations], dtype=float)
    quantiles = np.quantile(rates, x.quantile_probabilities, method="linear")
    mean_rate = float(np.mean(rates))
    between_specimen_sd = float(np.std(rates, ddof=1)) if len(rates) > 1 else None
    measurement_mean_uncertainty = None
    measurement_covariance_digest = None
    if x.measurement_error_covariance_m_s2 is not None:
        measurement_covariance = np.asarray(x.measurement_error_covariance_m_s2, dtype=float)
        n = len(rates)
        measurement_mean_uncertainty = math.sqrt(max(0.0, float(np.sum(measurement_covariance)) / (n * n)))
        measurement_covariance_digest = canonical_digest(x.measurement_error_covariance_m_s2)
    return Calculation(
        values={
            "material_id": x.observations[0].material_id,
            "condition_signature": x.observations[0].condition_signature,
            "condition_signature_sha256": canonical_digest(x.observations[0].condition_signature),
            "condition_group_id": x.observations[0].condition_group_id,
            "source_group_id": x.observations[0].source_group_id,
            "measurement_method": x.observations[0].measurement_method,
            "arithmetic_mean_rate_m_s": mean_rate,
            "between_specimen_sample_standard_deviation_m_s": between_specimen_sd,
            "measurement_standard_uncertainty_of_mean_m_s": measurement_mean_uncertainty,
            "measurement_error_covariance_sha256": measurement_covariance_digest,
            "physical_specimen_ids": [row.physical_specimen_id for row in x.observations],
            "observation_ids": [row.observation_id for row in x.observations],
            "rate_standard_uncertainties_m_s": [row.rate_standard_uncertainty_m_s for row in x.observations],
            "rate_uncertainty_bases": [row.rate_uncertainty_basis for row in x.observations],
            "evidence_source_ids_by_observation": [
                [item.source_id for item in row.evidence] for row in x.observations
            ],
            "specimen_count": len(rates),
            "minimum_rate_m_s": float(np.min(rates)),
            "maximum_rate_m_s": float(np.max(rates)),
            "quantile_probabilities": x.quantile_probabilities,
            "quantile_rates_m_s": [float(value) for value in quantiles],
            "quantile_method": "numpy_linear",
        },
        notes=(
            "Descriptive empirical quantiles of caller-supplied one-per-specimen rate summaries under one condition and source group.",
            "Quantiles are not confidence or prediction intervals; sample independence, measurement uncertainty, transferability, acceptance and life are not established.",
            "Rowwise measurement standard uncertainties and evidence are preserved separately; measurement uncertainty is not blended into empirical sample quantiles.",
        ),
    )


class CorrosionRateQuantileForecast(Contract):
    """A deterministic linear wall-loss scenario using one selected empirical rate quantile."""

    sample: CorrosionRateSampleSummary
    selected_quantile_level: Fraction
    current_thickness_m: Positive
    required_thickness_m: Positive
    horizon_s: Nonnegative
    material_state_compatibility_reviewed: bool
    material_state_review_id: str = Field(min_length=1)
    condition_transferability_reviewed: bool
    condition_transfer_review_id: str = Field(min_length=1)
    linear_loss_model_reviewed: bool
    linear_loss_model_review_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_scenario(self):
        if self.selected_quantile_level not in self.sample.quantile_probabilities:
            raise ValueError("selected_quantile_level must exactly match one supplied summary quantile")
        if not all(
            (
                self.material_state_compatibility_reviewed,
                self.condition_transferability_reviewed,
                self.linear_loss_model_reviewed,
            )
        ):
            raise ValueError("material, condition-transfer and linear-loss reviews are required")
        if any(
            not identifier.strip()
            for identifier in (
                self.material_state_review_id,
                self.condition_transfer_review_id,
                self.linear_loss_model_review_id,
            )
        ):
            raise ValueError("each review must have a non-blank traceable review identifier")
        return self


def corrosion_rate_quantile_forecast(x: CorrosionRateQuantileForecast) -> Calculation:
    summary = corrosion_rate_sample_summary(x.sample)
    index = x.sample.quantile_probabilities.index(x.selected_quantile_level)
    selected_rate = summary.values["quantile_rates_m_s"][index]
    forecast = uniform_forecast(
        UniformForecast(
            current_thickness_m=x.current_thickness_m,
            required_thickness_m=x.required_thickness_m,
            rate_m_s=selected_rate,
            horizon_s=x.horizon_s,
        )
    )
    return Calculation(
        status=forecast.status,
        values={
            **forecast.values,
            "selected_sample_quantile_level": x.selected_quantile_level,
            "selected_sample_rate_m_s": selected_rate,
            "rate_sample_specimen_count": summary.values["specimen_count"],
            "rate_sample_quantile_method": summary.values["quantile_method"],
            "rate_sample_material_id": summary.values["material_id"],
            "rate_sample_condition_group_id": summary.values["condition_group_id"],
            "rate_sample_source_group_id": summary.values["source_group_id"],
            "rate_sample_condition_signature_sha256": summary.values["condition_signature_sha256"],
            "rate_sample_physical_specimen_ids": summary.values["physical_specimen_ids"],
            "rate_sample_observation_ids": summary.values["observation_ids"],
            "rate_sample_standard_uncertainties_m_s": summary.values["rate_standard_uncertainties_m_s"],
            "rate_sample_uncertainty_bases": summary.values["rate_uncertainty_bases"],
            "rate_sample_arithmetic_mean_m_s": summary.values["arithmetic_mean_rate_m_s"],
            "rate_sample_between_specimen_sd_m_s": summary.values[
                "between_specimen_sample_standard_deviation_m_s"
            ],
            "rate_sample_uncertainty_of_mean_m_s": summary.values[
                "measurement_standard_uncertainty_of_mean_m_s"
            ],
            "rate_sample_measurement_error_covariance_sha256": summary.values[
                "measurement_error_covariance_sha256"
            ],
            "rate_sample_evidence_source_ids_by_observation": summary.values[
                "evidence_source_ids_by_observation"
            ],
            "material_state_review_id": x.material_state_review_id,
            "condition_transfer_review_id": x.condition_transfer_review_id,
            "linear_loss_model_review_id": x.linear_loss_model_review_id,
        },
        notes=forecast.notes
        + (
            "This deterministic scenario uses one selected empirical sample quantile as a fixed future rate after caller review of material state, condition transfer and linear-loss applicability.",
            "Coupon measurement standard uncertainties, when supplied, are retained separately and are not propagated into this deterministic forecast.",
            "The quantile level is not a confidence level, failure probability or FTA basic-event probability; this scenario supplies none of those quantities.",
        ),
    )


class CorrosionRateJointScenario(Contract):
    """Caller-weighted rate scenarios for propagating sample variation to wall loss."""

    sample: CorrosionRateSampleSummary
    current_thickness_m: Positive
    required_thickness_m: Positive
    horizon_s: Nonnegative
    material_state_compatibility_reviewed: bool
    material_state_review_id: str = Field(min_length=1)
    condition_transferability_reviewed: bool
    condition_transfer_review_id: str = Field(min_length=1)
    linear_loss_model_reviewed: bool
    linear_loss_model_review_id: str = Field(min_length=1)
    scenario_rate_m_s: list[Nonnegative] = Field(min_length=1)
    scenario_weights: list[Fraction] = Field(min_length=1)
    scenario_ids: list[str] = Field(min_length=1)
    scenario_set_id: str = Field(min_length=1)
    scenario_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    weight_meaning: Literal["caller_declared_scenario_weight"]

    @model_validator(mode="after")
    def validate_scenarios(self):
        count = len(self.scenario_rate_m_s)
        if not (len(self.scenario_weights) == len(self.scenario_ids) == count):
            raise ValueError("scenario rates, weights and IDs must have equal lengths")
        if len(set(self.scenario_ids)) != count or any(not item.strip() for item in self.scenario_ids):
            raise ValueError("scenario IDs must be unique and non-blank")
        if abs(sum(self.scenario_weights) - 1.0) > 1e-10:
            raise ValueError("scenario weights must sum to one")
        if not self.scenario_set_id.strip():
            raise ValueError("scenario_set_id cannot be blank")
        if not all(
            (
                self.material_state_compatibility_reviewed,
                self.condition_transferability_reviewed,
                self.linear_loss_model_reviewed,
            )
        ):
            raise ValueError("material, condition-transfer and linear-loss reviews are required")
        if any(
            not item.strip()
            for item in (
                self.material_state_review_id,
                self.condition_transfer_review_id,
                self.linear_loss_model_review_id,
            )
        ):
            raise ValueError("each review must have a non-blank traceable review identifier")
        return self


def corrosion_rate_joint_scenario(x: CorrosionRateJointScenario) -> Calculation:
    """Push caller-weighted sample rates through fixed linear wall-loss scenarios."""

    rates = np.asarray(x.scenario_rate_m_s, dtype=float)
    weights = np.asarray(x.scenario_weights, dtype=float)
    remaining = x.current_thickness_m - rates * x.horizon_s
    exhausted = remaining < 0.0
    safe_remaining = np.maximum(remaining, 0.0)
    threshold_crossed = remaining <= x.required_thickness_m
    crossing_time = np.full(rates.shape, np.inf)
    positive_loss = rates > 0.0
    crossing_time[positive_loss] = (x.current_thickness_m - x.required_thickness_m) / rates[positive_loss]
    crossing_time[(~positive_loss) & (x.current_thickness_m <= x.required_thickness_m)] = 0.0
    crossing_time = np.maximum(crossing_time, 0.0)
    weighted_mean_rate = float(weights @ rates)
    weighted_remaining = float(weights @ safe_remaining)
    result = {
        "scenario_set_id": x.scenario_set_id,
        "scenario_source_digest": x.scenario_source_digest,
        "scenario_ids": list(x.scenario_ids),
        "scenario_rates_m_s": x.scenario_rate_m_s,
        "scenario_weights": x.scenario_weights,
        "scenario_weight_meaning": x.weight_meaning,
        "scenario_rate_mean_m_s": weighted_mean_rate,
        "scenario_remaining_thickness_m": safe_remaining.tolist(),
        "scenario_threshold_crossed_by_horizon": threshold_crossed.tolist(),
        "scenario_wall_exhausted_by_horizon": exhausted.tolist(),
        "weighted_remaining_thickness_m": weighted_remaining,
        "weighted_threshold_crossing_mass": float(weights @ threshold_crossed.astype(float)),
        "weighted_wall_exhaustion_mass": float(weights @ exhausted.astype(float)),
        "crossing_time_to_required_s_by_scenario": [
            float(value) if math.isfinite(float(value)) else None for value in crossing_time
        ],
        "material_id": x.sample.observations[0].material_id,
        "condition_group_id": x.sample.observations[0].condition_group_id,
        "source_group_id": x.sample.observations[0].source_group_id,
        "sample_condition_signature_sha256": canonical_digest(x.sample.observations[0].condition_signature),
        "sample_physical_specimen_ids": [row.physical_specimen_id for row in x.sample.observations],
        "sample_observation_ids": [row.observation_id for row in x.sample.observations],
        "material_state_review_id": x.material_state_review_id,
        "condition_transfer_review_id": x.condition_transfer_review_id,
        "linear_loss_model_review_id": x.linear_loss_model_review_id,
    }
    return Calculation(
        status="out_of_scope" if np.any(exhausted) else "computed",
        values=result,
        notes=(
            "Caller-supplied scenario rates and normalized weights are propagated through a fixed linear wall-loss calculation.",
            "Threshold-crossing and wall-exhaustion masses inherit the caller's scenario-weight meaning; they are not automatically probabilities, confidence bounds or FTA event probabilities.",
            "Scenario weights, dependence, material-state compatibility, condition transfer and fixed-rate applicability require external review.",
        ),
    )


class SimulationRateWallLossScenario(Contract):
    """Propagate attributed model-output rows to a caller-defined asset scenario."""

    rows: list[WetCo2SimulationGridRow] = Field(min_length=1, max_length=243)
    current_thickness_m: Positive
    required_thickness_m: Positive
    horizon_s: Nonnegative
    material_state_compatibility_reviewed: bool
    material_state_review_id: str = Field(min_length=1)
    condition_transferability_reviewed: bool
    condition_transfer_review_id: str = Field(min_length=1)
    linear_loss_model_reviewed: bool
    linear_loss_model_review_id: str = Field(min_length=1)
    scenario_weights: list[Fraction] = Field(min_length=1)
    weight_meaning: Literal["caller_declared_scenario_weight"]
    scenario_set_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_simulation_scenario(self):
        if len(self.rows) != len(self.scenario_weights):
            raise ValueError("one caller-supplied weight is required for each simulation row")
        if abs(sum(self.scenario_weights) - 1.0) > 1e-10:
            raise ValueError("scenario weights must sum to one")
        if len({row.provider_row for row in self.rows}) != len(self.rows):
            raise ValueError("simulation scenario provider rows must be unique")
        for field in ("dataset_id", "dataset_doi", "source_group_id", "source_archive_sha256"):
            if len({getattr(row, field) for row in self.rows}) != 1:
                raise ValueError(f"simulation scenario rows must share {field}")
        if not self.scenario_set_id.strip():
            raise ValueError("scenario_set_id cannot be blank")
        if not all(
            (
                self.material_state_compatibility_reviewed,
                self.condition_transferability_reviewed,
                self.linear_loss_model_reviewed,
            )
        ):
            raise ValueError("material, condition-transfer and linear-loss reviews are required")
        if any(
            not value.strip()
            for value in (
                self.material_state_review_id,
                self.condition_transfer_review_id,
                self.linear_loss_model_review_id,
            )
        ):
            raise ValueError("each review must have a non-blank traceable review identifier")
        return self


def simulation_rate_wall_loss_scenario(x: SimulationRateWallLossScenario) -> Calculation:
    """Apply provider model rates to reviewed constant-rate wall-loss scenarios."""

    rows = x.rows
    rates = np.asarray([row.corrosion_rate_m_s for row in rows], dtype=float)
    weights = np.asarray(x.scenario_weights, dtype=float)
    remaining = x.current_thickness_m - rates * x.horizon_s
    exhausted = remaining < 0.0
    safe_remaining = np.maximum(remaining, 0.0)
    threshold_crossed = remaining <= x.required_thickness_m
    crossing_time = np.full(rates.shape, np.inf)
    positive_loss = rates > 0.0
    crossing_time[positive_loss] = (x.current_thickness_m - x.required_thickness_m) / rates[positive_loss]
    crossing_time[(~positive_loss) & (x.current_thickness_m <= x.required_thickness_m)] = 0.0
    crossing_time = np.maximum(crossing_time, 0.0)
    result = {
        "scenario_set_id": x.scenario_set_id,
        "scenario_ids": [f"{row.dataset_id}:row:{row.provider_row}" for row in rows],
        "scenario_rates_m_s": rates.tolist(),
        "scenario_weights": x.scenario_weights,
        "scenario_weight_meaning": x.weight_meaning,
        "scenario_rate_weighted_mean_m_s": float(weights @ rates),
        "scenario_remaining_thickness_m": safe_remaining.tolist(),
        "scenario_threshold_crossed_by_horizon": threshold_crossed.tolist(),
        "scenario_wall_exhausted_by_horizon": exhausted.tolist(),
        "weighted_remaining_thickness_m": float(weights @ safe_remaining),
        "weighted_threshold_crossing_mass": float(weights @ threshold_crossed.astype(float)),
        "weighted_wall_exhaustion_mass": float(weights @ exhausted.astype(float)),
        "crossing_time_to_required_s_by_scenario": [
            float(value) if math.isfinite(float(value)) else None for value in crossing_time
        ],
        "source_dataset_id": rows[0].dataset_id,
        "source_dataset_doi": rows[0].dataset_doi,
        "source_license_id": "CC-BY-4.0",
        "source_group_id": rows[0].source_group_id,
        "source_archive_sha256": rows[0].source_archive_sha256,
        "source_provider_rows": [row.provider_row for row in rows],
        "source_evidence_by_row": [
            [evidence.model_dump(mode="json") for evidence in row.evidence] for row in rows
        ],
        "source_data_type": "simulated_model_output",
        "physical_observation_inferred": False,
        "physical_calibration_inferred": False,
        "failure_probability_inferred": False,
        "material_state_review_id": x.material_state_review_id,
        "condition_transfer_review_id": x.condition_transfer_review_id,
        "linear_loss_model_review_id": x.linear_loss_model_review_id,
    }
    return Calculation(
        status="out_of_scope" if np.any(exhausted) else "computed",
        values=result,
        notes=(
            "Provider-generated simulated corrosion rates are applied to caller-specified thickness and horizon under a fixed-rate linear-loss assumption.",
            "This is a model-output scenario projection, not an empirical specimen forecast or calibrated physical corrosion prediction.",
            "Weighted masses retain caller-declared scenario-weight meaning and are not probabilities, confidence bounds or FTA event probabilities.",
        ),
    )


class CorrosionRateProjectionRow(Contract):
    """A non-empirical corrosion-rate scenario row with portable source lineage."""

    schema_version: Literal["matintegrity.corrosion_rate_projection_row.v1"] = (
        "matintegrity.corrosion_rate_projection_row.v1"
    )
    scenario_id: str = Field(min_length=1)
    source_dataset_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    source_archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_role: Literal["simulated_model_output", "caller_assumed_scenario"]
    rate_m_s: Nonnegative
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    physical_specimen_id: None = None
    independent_physical_observation: Literal[False] = False
    empirical_calibration_ready: Literal[False] = False

    @model_validator(mode="after")
    def evidence_matches_source(self):
        matching = [
            item
            for item in self.evidence
            if item.source_id == self.source_dataset_id and item.sha256 == self.source_archive_sha256
        ]
        if not matching:
            raise ValueError("projection row requires evidence matching its dataset and archive digest")
        if self.source_role == "simulated_model_output" and not any(
            item.origin in {"open_dataset", "model_prediction"} for item in matching
        ):
            raise ValueError("simulated output needs open-dataset or model-prediction source evidence")
        if self.source_role == "caller_assumed_scenario" and not any(
            item.origin in {"user_declared", "synthetic"} for item in matching
        ):
            raise ValueError("assumed scenario needs user-declared or synthetic source evidence")
        return self


class CorrosionRateModelOutputWallLossScenario(Contract):
    """Portable model-output rate scenarios projected through reviewed linear wall loss."""

    rows: list[CorrosionRateProjectionRow] = Field(min_length=1, max_length=100_000)
    current_thickness_m: Positive
    required_thickness_m: Positive
    horizon_s: Nonnegative
    material_state_compatibility_reviewed: bool
    material_state_review_id: str = Field(min_length=1)
    condition_transferability_reviewed: bool
    condition_transfer_review_id: str = Field(min_length=1)
    linear_loss_model_reviewed: bool
    linear_loss_model_review_id: str = Field(min_length=1)
    scenario_weights: list[Fraction] = Field(min_length=1)
    weight_meaning: Literal["caller_declared_scenario_weight"]
    scenario_set_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_projection_scenario(self):
        if len(self.rows) != len(self.scenario_weights):
            raise ValueError("one caller-supplied weight is required for each projection row")
        if abs(sum(self.scenario_weights) - 1.0) > 1e-10:
            raise ValueError("scenario weights must sum to one")
        for field in ("scenario_id", "source_record_id"):
            if len({getattr(row, field) for row in self.rows}) != len(self.rows):
                raise ValueError(f"projection {field} values must be unique")
        for field in ("source_dataset_id", "source_group_id", "source_archive_sha256", "source_role"):
            if len({getattr(row, field) for row in self.rows}) != 1:
                raise ValueError(f"projection rows must share {field}")
        if not self.scenario_set_id.strip():
            raise ValueError("scenario_set_id cannot be blank")
        if not all(
            (
                self.material_state_compatibility_reviewed,
                self.condition_transferability_reviewed,
                self.linear_loss_model_reviewed,
            )
        ):
            raise ValueError("material, condition-transfer and linear-loss reviews are required")
        if any(
            not value.strip()
            for value in (
                self.material_state_review_id,
                self.condition_transfer_review_id,
                self.linear_loss_model_review_id,
            )
        ):
            raise ValueError("each review must have a non-blank traceable review identifier")
        return self


def wet_co2_simulation_row_to_projection_row(
    row: WetCo2SimulationGridRow,
) -> CorrosionRateProjectionRow:
    """Adapt one typed wet-CO2 provider output into the generic non-empirical scenario contract."""

    return CorrosionRateProjectionRow(
        scenario_id=f"{row.dataset_id}:row:{row.provider_row}",
        source_dataset_id=row.dataset_id,
        source_group_id=row.source_group_id,
        source_record_id=f"provider-row:{row.provider_row}",
        source_archive_sha256=row.source_archive_sha256,
        source_role="simulated_model_output",
        rate_m_s=row.corrosion_rate_m_s,
        evidence=row.evidence,
    )


def corrosion_rate_model_output_wall_loss_scenario(
    x: CorrosionRateModelOutputWallLossScenario,
) -> Calculation:
    """Project portable, non-empirical rate rows to a caller-defined wall-loss horizon."""

    rates = np.asarray([row.rate_m_s for row in x.rows], dtype=float)
    weights = np.asarray(x.scenario_weights, dtype=float)
    remaining = x.current_thickness_m - rates * x.horizon_s
    exhausted = remaining < 0.0
    safe_remaining = np.maximum(remaining, 0.0)
    threshold_crossed = remaining <= x.required_thickness_m
    crossing_time = np.full(rates.shape, np.inf)
    positive_loss = rates > 0.0
    crossing_time[positive_loss] = (x.current_thickness_m - x.required_thickness_m) / rates[positive_loss]
    crossing_time[(~positive_loss) & (x.current_thickness_m <= x.required_thickness_m)] = 0.0
    crossing_time = np.maximum(crossing_time, 0.0)
    rows = x.rows
    values = {
        "scenario_set_id": x.scenario_set_id,
        "scenario_ids": [row.scenario_id for row in rows],
        "scenario_rates_m_s": rates.tolist(),
        "scenario_weights": x.scenario_weights,
        "scenario_weight_meaning": x.weight_meaning,
        "scenario_rate_weighted_mean_m_s": float(weights @ rates),
        "scenario_remaining_thickness_m": safe_remaining.tolist(),
        "scenario_threshold_crossed_by_horizon": threshold_crossed.tolist(),
        "scenario_wall_exhausted_by_horizon": exhausted.tolist(),
        "weighted_remaining_thickness_m": float(weights @ safe_remaining),
        "weighted_threshold_crossing_mass": float(weights @ threshold_crossed.astype(float)),
        "weighted_wall_exhaustion_mass": float(weights @ exhausted.astype(float)),
        "crossing_time_to_required_s_by_scenario": [
            float(value) if math.isfinite(float(value)) else None for value in crossing_time
        ],
        "source_dataset_id": rows[0].source_dataset_id,
        "source_group_id": rows[0].source_group_id,
        "source_archive_sha256": rows[0].source_archive_sha256,
        "source_role": rows[0].source_role,
        "source_record_ids": [row.source_record_id for row in rows],
        "source_evidence_by_row": [
            [evidence.model_dump(mode="json") for evidence in row.evidence] for row in rows
        ],
        "physical_observation_inferred": False,
        "physical_calibration_inferred": False,
        "failure_probability_inferred": False,
        "material_state_review_id": x.material_state_review_id,
        "condition_transfer_review_id": x.condition_transfer_review_id,
        "linear_loss_model_review_id": x.linear_loss_model_review_id,
    }
    return Calculation(
        status="out_of_scope" if np.any(exhausted) else "computed",
        values=values,
        notes=(
            "Caller-weighted simulated or assumed corrosion-rate rows are propagated through fixed linear wall loss.",
            "This exchange contract accepts non-empirical scenarios; measured physical specimens belong in the observation and sample-summary contracts.",
            "Weighted threshold and exhaustion masses retain caller-declared weight meaning and are not probabilities, confidence bounds or FTA event probabilities.",
        ),
    )


def corrosion_model_output_to_first_passage_inputs(
    x: CorrosionRateModelOutputWallLossScenario,
    *,
    forecast_id: str,
    asset_id: str,
    location_id: str,
    physical_scope_id: str,
    physical_location_id: str,
    time_basis: str,
    assessment_time_s: float,
    conditioning: str,
    event_id: str,
    event_definition: str,
    distribution_definition_id: str,
    sample_design_id: str,
    candidate_horizon_end_s: list[float],
    current_thickness_at_assessment_review_id: str,
    samples_conditioned_on_survival_to_assessment: bool,
    constant_nonnegative_loss_model_reviewed: bool,
    joint_sample_distribution_reviewed: bool,
    required_thickness_basis_reviewed: bool,
    candidate_horizons_reviewed: bool,
    review_reference_ids: dict[str, str],
):
    """Adapt scenario rows to a separate, explicitly reviewed first-passage probability model."""

    from .reliability import (
        LinearThicknessFirstPassageSample,
        SampledLinearThicknessFirstPassage,
    )

    if len(x.rows) < 2:
        raise ValueError("first-passage adaptation requires at least two joint scenario rows")
    if not current_thickness_at_assessment_review_id.strip():
        raise ValueError("current thickness at assessment needs a traceable review identifier")
    gates = {
        "samples_conditioned_on_survival_to_assessment": samples_conditioned_on_survival_to_assessment,
        "constant_nonnegative_loss_model_reviewed": constant_nonnegative_loss_model_reviewed,
        "joint_sample_distribution_reviewed": joint_sample_distribution_reviewed,
        "required_thickness_basis_reviewed": required_thickness_basis_reviewed,
        "candidate_horizons_reviewed": candidate_horizons_reviewed,
    }
    missing_refs = [
        name for name, reviewed in gates.items() if reviewed and not review_reference_ids.get(name)
    ]
    if missing_refs:
        raise ValueError(f"reviewed first-passage gates need review reference IDs: {missing_refs}")
    if any(not value.strip() for value in review_reference_ids.values()):
        raise ValueError("review reference IDs must be non-blank")
    references = {
        **review_reference_ids,
        "current_thickness_at_assessment": current_thickness_at_assessment_review_id,
    }
    lineage = {
        "scenario_set_id": x.scenario_set_id,
        "scenario_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "source_dataset_id": x.rows[0].source_dataset_id,
        "source_group_id": x.rows[0].source_group_id,
        "source_archive_sha256": x.rows[0].source_archive_sha256,
        "source_role": x.rows[0].source_role,
        "source_record_ids": [row.source_record_id for row in x.rows],
        "source_evidence_by_row": [
            [evidence.model_dump(mode="json") for evidence in row.evidence] for row in x.rows
        ],
    }
    joint_source_digest = canonical_digest(
        {
            "scenario_input_sha256": lineage["scenario_input_sha256"],
            "assessment_time_s": assessment_time_s,
            "conditioning": conditioning,
            "event_id": event_id,
            "review_reference_ids": references,
        }
    )
    return SampledLinearThicknessFirstPassage(
        forecast_id=forecast_id,
        asset_id=asset_id,
        location_id=location_id,
        physical_scope_id=physical_scope_id,
        physical_location_id=physical_location_id,
        time_basis=time_basis,
        assessment_time_s=assessment_time_s,
        conditioning=conditioning,
        event_id=event_id,
        event_definition=event_definition,
        required_thickness_m=x.required_thickness_m,
        distribution_definition_id=distribution_definition_id,
        sample_design_id=sample_design_id,
        joint_sample_source_sha256=joint_source_digest,
        source_lineage=lineage,
        review_reference_ids=references,
        samples=[
            LinearThicknessFirstPassageSample(
                sample_id=row.scenario_id,
                remaining_thickness_at_assessment_m=x.current_thickness_m,
                nonnegative_loss_rate_m_s=row.rate_m_s,
                normalized_weight=weight,
            )
            for row, weight in zip(x.rows, x.scenario_weights, strict=True)
        ],
        candidate_horizon_end_s=candidate_horizon_end_s,
        samples_conditioned_on_survival_to_assessment=samples_conditioned_on_survival_to_assessment,
        constant_nonnegative_loss_model_reviewed=constant_nonnegative_loss_model_reviewed,
        joint_sample_distribution_reviewed=joint_sample_distribution_reviewed,
        required_thickness_basis_reviewed=required_thickness_basis_reviewed,
        candidate_horizons_reviewed=candidate_horizons_reviewed,
    )


def arrhenius(x: ArrheniusRate) -> Calculation:
    factor = math.exp(
        -x.activation_energy_J_mol / 8.31446261815324 * (1 / x.temperature_K - 1 / x.reference_temperature_K)
    )
    return Calculation(values=dict(rate=x.reference_rate * factor, temperature_factor=factor))


def specifications():
    return [
        ModelSpec(
            "corrosion.coupon_loss",
            CouponLoss,
            coupon_loss,
            {"mean_penetration_m": "m", "rate_m_s": "m/s", "rate_mm_year": "mm/year"},
            ("Uniform average loss over the declared exposed area; cleaning loss is corrected upstream.",),
            ("mass_conservation",),
            version="0.1.1",
        ),
        ModelSpec(
            "corrosion.coupon_loss_with_uncertainty",
            CouponLossWithUncertainty,
            coupon_loss_with_uncertainty,
            {
                "mean_penetration_m": "m",
                "rate_m_s": "m/s",
                "rate_mm_year": "mm/year",
                "rate_standard_uncertainty_m_s": "m/s",
                "rate_relative_standard_uncertainty": "1",
                "penetration_standard_uncertainty_m": "m",
            },
            (
                "Caller supplies corrected mass loss, geometry, material density, exposure duration and joint input covariance.",
                "First-order uncertainty propagation assumes the supplied covariance is applicable; localized attack and life are outside scope.",
            ),
            ("mass_conservation",),
            version="0.1.1",
        ),
        ModelSpec(
            "corrosion.faraday",
            FaradayLoss,
            faraday_loss,
            {"rate_m_s": "m/s", "penetration_m": "m"},
            ("Declared dissolution valence and current efficiency; no automatic pit geometry inference.",),
            ("faraday_electrolysis",),
            version="0.1.1",
        ),
        ModelSpec(
            "corrosion.thickness_trend",
            ThicknessTrend,
            thickness_trend,
            {
                "rate_m_s": "m/s",
                "thickness_at_first_time_m": "m",
                "residual_rmse_m": "m",
                "rate_interval_m_s": "m/s",
            },
            ("Same measurement location and unchanged repair/operating regime; residuals are not POD.",),
            ("scipy_theilslopes",),
        ),
        ModelSpec(
            "corrosion.uniform_forecast",
            UniformForecast,
            uniform_forecast,
            {
                "thickness_margin_m": "m",
                "predicted_thickness_m": "m",
                "forecast_margin_m": "m",
                "time_to_required_s": "s",
            },
            (
                "Constant nonnegative growth; required thickness supplied by a separately qualified assessment.",
            ),
            ("linear_degradation",),
        ),
        ModelSpec(
            "corrosion.power_law",
            PowerLawPenetration,
            power_law,
            {"penetration_m": "m"},
            ("Empirical coefficients apply only to their calibration domain and chosen reference time.",),
            ("empirical_power_law",),
        ),
        ModelSpec(
            "kinetics.arrhenius",
            ArrheniusRate,
            arrhenius,
            {"temperature_factor": "1", "rate": "same as reference_rate"},
            (
                "Single thermally activated mechanism; parameters and applicable temperature range are user supplied.",
            ),
            ("arrhenius_kinetics",),
        ),
        ModelSpec(
            "corrosion.material_rate_contrast",
            MaterialCorrosionRateContrast,
            material_corrosion_rate_contrast,
            {
                "numerator_rate_m_s": "m/s",
                "reference_rate_m_s": "m/s",
                "rate_difference_m_s": "m/s",
                "rate_ratio": "1",
                "log_rate_ratio": "1",
            },
            (
                "Input rates and condition groups are supplied by the caller; matched methodology and exposure conditions require source review.",
                "A ratio describes only the supplied comparison and does not transfer to another material, process, or environment.",
            ),
            ("material_corrosion_rate_contrast",),
        ),
        ModelSpec(
            "corrosion.rate_sample_summary",
            CorrosionRateSampleSummary,
            corrosion_rate_sample_summary,
            {
                "arithmetic_mean_rate_m_s": "m/s",
                "between_specimen_sample_standard_deviation_m_s": "m/s",
                "measurement_standard_uncertainty_of_mean_m_s": "m/s",
                "minimum_rate_m_s": "m/s",
                "maximum_rate_m_s": "m/s",
                "quantile_rates_m_s": "m/s",
                "rate_standard_uncertainties_m_s": "m/s",
                "specimen_count": "1",
            },
            (
                "One caller-reviewed rate summary per unique physical specimen, all from one material, condition, method and source group.",
                "Between-specimen sample standard deviation and caller-propagated uncertainty of the equal-weight mean are distinct and reported separately.",
                "Empirical quantiles describe the supplied sample only and are not uncertainty bounds or life forecasts.",
            ),
            ("numpy_quantile_linear",),
        ),
        ModelSpec(
            "corrosion.rate_quantile_forecast",
            CorrosionRateQuantileForecast,
            corrosion_rate_quantile_forecast,
            {
                "thickness_margin_m": "m",
                "predicted_thickness_m": "m",
                "forecast_margin_m": "m",
                "time_to_required_s": "s",
                "selected_sample_rate_m_s": "m/s",
                "rate_sample_standard_uncertainties_m_s": "m/s",
                "rate_sample_arithmetic_mean_m_s": "m/s",
                "rate_sample_between_specimen_sd_m_s": "m/s",
                "rate_sample_uncertainty_of_mean_m_s": "m/s",
                "selected_sample_quantile_level": "1",
                "rate_sample_specimen_count": "1",
            },
            (
                "Uses exactly one selected empirical quantile from one-per-specimen caller rate summaries after explicit material, transfer and fixed linear-loss applicability review.",
                "Deterministic scenario only; rowwise measurement uncertainties are retained but not propagated. Selected sample quantile is not a confidence level, failure probability, acceptance result or general corrosion-life model.",
            ),
            ("numpy_quantile_linear", "linear_degradation"),
        ),
        ModelSpec(
            "corrosion.rate_joint_scenario",
            CorrosionRateJointScenario,
            corrosion_rate_joint_scenario,
            {
                "scenario_rate_mean_m_s": "m/s",
                "scenario_remaining_thickness_m": "m",
                "weighted_remaining_thickness_m": "m",
                "weighted_threshold_crossing_mass": "1",
                "weighted_wall_exhaustion_mass": "1",
                "crossing_time_to_required_s_by_scenario": "s",
            },
            (
                "Each rate and weight is a caller-supplied complete scenario; one-per-specimen sample lineage is preserved separately.",
                "Weights retain caller-declared scenario meaning and are not promoted to probability semantics without an explicit reliability model.",
                "Material, environment transfer and constant linear-loss reviews are required; wall exhaustion is reported out of scope.",
            ),
            ("linear_degradation", "caller_weighted_scenario_pushforward"),
        ),
        ModelSpec(
            "corrosion.simulation_rate_wall_loss_scenario",
            SimulationRateWallLossScenario,
            simulation_rate_wall_loss_scenario,
            {
                "scenario_rates_m_s": "m/s",
                "scenario_remaining_thickness_m": "m",
                "weighted_remaining_thickness_m": "m",
                "weighted_threshold_crossing_mass": "1",
                "weighted_wall_exhaustion_mass": "1",
                "crossing_time_to_required_s_by_scenario": "s",
            },
            (
                "Uses attributed simulated-model-output rows as scenario inputs while keeping them distinct from physical specimen observations.",
                "Requires explicit caller weights and material, condition-transfer and linear-loss review identifiers.",
                "Output is not empirical calibration, failure probability, confidence bound or FTA event probability.",
            ),
            ("linear_degradation", "caller_weighted_scenario_pushforward"),
        ),
        ModelSpec(
            "corrosion.model_output_rate_wall_loss_scenario",
            CorrosionRateModelOutputWallLossScenario,
            corrosion_rate_model_output_wall_loss_scenario,
            {
                "scenario_rates_m_s": "m/s",
                "scenario_remaining_thickness_m": "m",
                "weighted_remaining_thickness_m": "m",
                "weighted_threshold_crossing_mass": "1",
                "weighted_wall_exhaustion_mass": "1",
                "crossing_time_to_required_s_by_scenario": "s",
            },
            (
                "Accepts portable simulated or caller-assumed scenario rows with matching source evidence, digest and common source group.",
                "Rows with physical specimen identities or measured-observation roles belong in the empirical observation contracts, not this scenario API.",
                "Requires explicit caller weights and material, condition-transfer and linear-loss review identifiers; weights are not probabilities or FTA events.",
            ),
            ("linear_degradation", "caller_weighted_scenario_pushforward"),
        ),
    ]
