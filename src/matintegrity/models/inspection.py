"""Inspection observations, detection likelihood and explicit test loading."""

from __future__ import annotations

import math
from fractions import Fraction as Rational
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import (
    Calculation,
    Contract,
    Evidence,
    Fraction,
    Nonnegative,
    Positive,
    RunContext,
    canonical_digest,
)
from ..registry import ModelSpec


class UltrasonicThickness(Contract):
    round_trip_time_s: Positive
    sound_speed_m_s: Positive
    time_zero_offset_s: Nonnegative
    incidence_angle_rad: float = Field(ge=0, lt=math.pi / 2)


def ultrasonic_thickness(x: UltrasonicThickness) -> Calculation:
    corrected = x.round_trip_time_s - x.time_zero_offset_s
    if corrected <= 0:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Time-zero correction consumes the measured round trip.",),
        )
    return Calculation(
        values={"thickness_m": 0.5 * corrected * x.sound_speed_m_s * math.cos(x.incidence_angle_rad)}
    )


class PulseEchoCalibrationObservation(Contract):
    """One reference-block observation, with an immutable fit/holdout assignment."""

    observation_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    reference_thickness_m: Positive
    round_trip_time_s: Positive
    reference_thickness_standard_uncertainty_m: Positive | None = None
    round_trip_time_standard_uncertainty_s: Positive | None = None


class PulseEchoSoundSpeedFit(Contract):
    """Fit one sound speed while holding timing zero and path angle fixed and reviewed."""

    calibration_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    probe_id: str = Field(min_length=1)
    wave_mode: Literal["longitudinal"] = "longitudinal"
    temperature_K: Positive
    time_zero_offset_s: Nonnegative
    incidence_angle_rad: float = Field(ge=0, lt=math.pi / 2)
    reference_dimension_method: str = Field(min_length=1)
    fit_method: Literal["ordinary_through_origin", "iterative_effective_variance"] = "ordinary_through_origin"
    relative_convergence_tolerance: Positive = 1e-12
    maximum_iterations: int = Field(default=100, ge=1)
    observations: list[PulseEchoCalibrationObservation] = Field(min_length=4)
    timing_and_path_reviewed: bool
    reference_dimensions_reviewed: bool
    holdout_partition_predeclared: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def reviewed_partition(self):
        if not (
            self.timing_and_path_reviewed
            and self.reference_dimensions_reviewed
            and self.holdout_partition_predeclared
        ):
            raise ValueError("timing, reference dimensions and predeclared holdout must be reviewed")
        ids = [row.observation_id for row in self.observations]
        if len(set(ids)) != len(ids):
            raise ValueError("pulse-echo observation IDs must be unique")
        calibration = [row for row in self.observations if row.partition == "calibration"]
        holdout = [row for row in self.observations if row.partition == "holdout"]
        if len(calibration) < 3 or not holdout:
            raise ValueError("at least three calibration and one holdout observations are required")
        for identity in ("physical_location_id", "source_group_id"):
            fit_ids = {getattr(row, identity) for row in calibration}
            holdout_ids = {getattr(row, identity) for row in holdout}
            if fit_ids & holdout_ids:
                raise ValueError(f"{identity} cannot cross calibration and holdout partitions")
        if any(row.round_trip_time_s <= self.time_zero_offset_s for row in self.observations):
            raise ValueError("time-zero correction must leave a positive round-trip time")
        uncertainty_pairs = [
            (
                row.reference_thickness_standard_uncertainty_m,
                row.round_trip_time_standard_uncertainty_s,
            )
            for row in self.observations
        ]
        if any((a is None) != (b is None) for a, b in uncertainty_pairs):
            raise ValueError("thickness and round-trip-time uncertainties must be supplied together")
        if self.fit_method == "iterative_effective_variance" and any(a is None for a, _ in uncertainty_pairs):
            raise ValueError("effective-variance fitting requires uncertainties for every observation")
        return self


def pulse_echo_sound_speed_fit(x: PulseEchoSoundSpeedFit) -> Calculation:
    calibration = [row for row in x.observations if row.partition == "calibration"]
    holdout = [row for row in x.observations if row.partition == "holdout"]
    cosine = math.cos(x.incidence_angle_rad)

    def path_coordinate(row: PulseEchoCalibrationObservation) -> float:
        return 0.5 * (row.round_trip_time_s - x.time_zero_offset_s) * cosine

    fit_x = np.asarray([path_coordinate(row) for row in calibration])
    fit_y = np.asarray([row.reference_thickness_m for row in calibration])
    denominator = float(np.dot(fit_x, fit_x))
    sound_speed = float(np.dot(fit_x, fit_y) / denominator)
    iterations = 1
    converged = True
    weights = None
    if x.fit_method == "iterative_effective_variance":
        fit_sigma_y = np.asarray(
            [row.reference_thickness_standard_uncertainty_m for row in calibration], dtype=float
        )
        fit_sigma_x = (
            0.5
            * cosine
            * np.asarray([row.round_trip_time_standard_uncertainty_s for row in calibration], dtype=float)
        )
        converged = False
        for iteration_index in range(1, x.maximum_iterations + 1):
            iterations = iteration_index
            weights = 1.0 / (fit_sigma_y**2 + sound_speed**2 * fit_sigma_x**2)
            weighted_denominator = float(np.dot(weights, fit_x**2))
            updated = float(np.dot(weights, fit_x * fit_y) / weighted_denominator)
            relative_change = abs(updated - sound_speed) / max(abs(updated), abs(sound_speed))
            sound_speed = updated
            if relative_change <= x.relative_convergence_tolerance:
                converged = True
                break
        if not converged:
            return Calculation(
                status="needs_data",
                values={"iterations": iterations, "fit_method": x.fit_method},
                notes=("Effective-variance sound-speed fit did not converge within the declared limit.",),
            )
    residual = fit_y - sound_speed * fit_x
    residual_sum_squares = float(np.dot(residual, residual))
    residual_standard_deviation = math.sqrt(residual_sum_squares / (len(calibration) - 1))
    if weights is None:
        sound_speed_standard_error = residual_standard_deviation / math.sqrt(denominator)
        reduced_chi_square = None
        residual_scaled_standard_error = sound_speed_standard_error
    else:
        weighted_denominator = float(np.dot(weights, fit_x**2))
        sound_speed_standard_error = math.sqrt(1.0 / weighted_denominator)
        reduced_chi_square = float(np.dot(weights, residual**2) / (len(calibration) - 1))
        residual_scaled_standard_error = sound_speed_standard_error * math.sqrt(max(1.0, reduced_chi_square))
    holdout_x = np.asarray([path_coordinate(row) for row in holdout])
    holdout_y = np.asarray([row.reference_thickness_m for row in holdout])
    holdout_residual = holdout_y - sound_speed * holdout_x
    holdout_standardized_residual = None
    if x.fit_method == "iterative_effective_variance":
        holdout_sigma_y = np.asarray(
            [row.reference_thickness_standard_uncertainty_m for row in holdout], dtype=float
        )
        holdout_sigma_x = (
            0.5
            * cosine
            * np.asarray([row.round_trip_time_standard_uncertainty_s for row in holdout], dtype=float)
        )
        holdout_standardized_residual = holdout_residual / np.sqrt(
            holdout_sigma_y**2 + sound_speed**2 * holdout_sigma_x**2
        )
    calibration_fragment = {
        "calibration_id": x.calibration_id,
        "material_id": x.material_id,
        "applicable_sample_ids": [],
        "applicable_probe_ids": [x.probe_id],
        "wave_mode": x.wave_mode,
        "sound_speed_m_s": sound_speed,
        "sound_speed_temperature_K": x.temperature_K,
        "time_zero_offset_s": x.time_zero_offset_s,
        "incidence_angle_rad": x.incidence_angle_rad,
        "calibration_basis": (
            f"through-origin reference-block fit using {len(calibration)} calibration observations; "
            "sample applicability must be assigned by the caller"
        ),
        "evidence": x.evidence[0].model_dump(mode="json"),
        "calibration_reviewed": False,
    }
    return Calculation(
        values={
            "calibration_id": x.calibration_id,
            "material_id": x.material_id,
            "probe_id": x.probe_id,
            "temperature_K": x.temperature_K,
            "sound_speed_m_s": sound_speed,
            "sound_speed_standard_error_m_s": sound_speed_standard_error,
            "sound_speed_residual_scaled_standard_error_m_s": residual_scaled_standard_error,
            "fit_method": x.fit_method,
            "iterations": iterations,
            "converged": converged,
            "calibration_reduced_chi_square": reduced_chi_square,
            "calibration_observation_count": len(calibration),
            "holdout_observation_count": len(holdout),
            "calibration_rmse_m": float(np.sqrt(np.mean(residual**2))),
            "calibration_maximum_absolute_residual_m": float(np.max(np.abs(residual))),
            "holdout_rmse_m": float(np.sqrt(np.mean(holdout_residual**2))),
            "holdout_maximum_absolute_residual_m": float(np.max(np.abs(holdout_residual))),
            "holdout_standardized_residual_rmse": None
            if holdout_standardized_residual is None
            else float(np.sqrt(np.mean(holdout_standardized_residual**2))),
            "calibration_reference_thickness_range_m": [float(np.min(fit_y)), float(np.max(fit_y))],
            "holdout_reference_thickness_range_m": [
                float(np.min(holdout_y)),
                float(np.max(holdout_y)),
            ],
            "calibration_fragment": calibration_fragment,
        },
        notes=(
            "Only calibration rows determine sound speed; holdout rows are evaluated after fitting.",
            "The ordinary-fit standard error is residual-conditional; neither method covers shared time-zero, angle, probe, temperature, coupling or model-form uncertainty.",
            "Effective-variance weights propagate declared independent pointwise thickness and time uncertainties; shared systematic components remain excluded.",
            "The returned fragment is deliberately unreviewed and has no sample scope; a caller must review and complete it before thickness conversion.",
        ),
    )


class DetectionCurve(Contract):
    flaw_size_m: Nonnegative
    midpoint_size_m: Positive
    log_size_scale: Positive


def detection_curve(x: DetectionCurve) -> Calculation:
    if x.flaw_size_m == 0:
        probability = 0.0
    else:
        z = math.log(x.flaw_size_m / x.midpoint_size_m) / x.log_size_scale
        probability = 1 / (1 + math.exp(-z)) if z >= 0 else math.exp(z) / (1 + math.exp(z))
    return Calculation(values={"probability_of_detection": probability})


class NoIndicationUpdate(Contract):
    prior_weights: list[Nonnegative] = Field(min_length=1)
    probabilities_of_detection: list[Fraction] = Field(min_length=1)
    coverage_fraction: Fraction

    @model_validator(mode="after")
    def align(self):
        if len(self.prior_weights) != len(self.probabilities_of_detection) or sum(self.prior_weights) <= 0:
            raise ValueError("aligned POD bins and a positive total prior weight required")
        return self


def no_indication_update(x: NoIndicationUpdate) -> Calculation:
    total = sum(x.prior_weights)
    unscaled = [
        w / total * (1 - x.coverage_fraction * pod)
        for w, pod in zip(x.prior_weights, x.probabilities_of_detection, strict=True)
    ]
    likelihood = sum(unscaled)
    if likelihood <= 0:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Observation has zero probability under the supplied model.",),
        )
    return Calculation(
        values=dict(
            posterior_weights=[w / likelihood for w in unscaled], probability_of_no_indication=likelihood
        )
    )


class PressureTest(Contract):
    design_pressure_Pa: Positive
    declared_test_factor: Positive
    allowable_at_test_Pa: Positive
    allowable_at_design_Pa: Positive
    fluid_density_kg_m3: Nonnegative
    elevation_below_gauge_m: Nonnegative


class PipeMembraneTestPressure(Contract):
    """Declared fraction of yield applied to an outside-diameter membrane basis."""

    outside_diameter_m: Positive
    wall_thickness_m: Positive
    yield_strength_Pa: Positive
    declared_yield_fraction: float = Field(gt=0, le=1)
    factor_basis: str = Field(min_length=1)
    geometry_material_and_factor_applicability_reviewed: bool

    @model_validator(mode="after")
    def validate_pipe_section(self):
        if 2.0 * self.wall_thickness_m >= self.outside_diameter_m:
            raise ValueError("pipe section must retain a positive bore")
        return self


def pipe_membrane_test_pressure(x: PipeMembraneTestPressure) -> Calculation:
    if not x.geometry_material_and_factor_applicability_reviewed:
        return Calculation(status="needs_data", values={"reason": "pipe_and_factor_applicability_unreviewed"})
    try:
        exact_stress = Rational(x.declared_yield_fraction) * Rational(x.yield_strength_Pa)
        exact_pressure = 2 * exact_stress * Rational(x.wall_thickness_m) / Rational(x.outside_diameter_m)
        stress, pressure = float(exact_stress), float(exact_pressure)
        if stress == 0 or pressure == 0:
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Membrane test pressure or stress exceeds numeric support.",),
        )
    return Calculation(
        values={
            "membrane_test_pressure_difference_Pa": pressure,
            "declared_membrane_stress_Pa": stress,
            "factor_basis": x.factor_basis,
            "diameter_basis": "outside_diameter",
        }
    )


def pressure_test(x: PressureTest) -> Calculation:
    try:
        exact_reference = (
            Rational(x.design_pressure_Pa)
            * Rational(x.declared_test_factor)
            * Rational(x.allowable_at_test_Pa)
            / Rational(x.allowable_at_design_Pa)
        )
        exact_local = exact_reference + Rational(x.fluid_density_kg_m3) * Rational(9.80665) * Rational(
            x.elevation_below_gauge_m
        )
        reference, local = float(exact_reference), float(exact_local)
        if reference == 0:
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Reference or local test pressure exceeds numeric support.",),
        )
    return Calculation(
        values=dict(
            reference_test_pressure_Pa=reference,
            local_test_pressure_Pa=local,
        )
    )


class VisualExaminationArea(Contract):
    area_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    target_area_m2: Positive
    examined_area_m2: Nonnegative
    unexamined_basis: str | None = None

    @model_validator(mode="after")
    def valid_coverage(self):
        if self.examined_area_m2 > self.target_area_m2:
            raise ValueError("examined visual area cannot exceed its target area")
        if self.examined_area_m2 < self.target_area_m2 and not self.unexamined_basis:
            raise ValueError("incomplete visual coverage requires an unexamined basis")
        return self


class VisualSurfaceIndication(Contract):
    indication_id: str = Field(min_length=1)
    area_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    indication_type: str = Field(min_length=1)
    location_description: str = Field(min_length=1)
    measured_length_m: Nonnegative | None = None
    measured_width_m: Nonnegative | None = None
    evidence: list[Evidence] = Field(min_length=1)


class VisualSurfaceExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    examination_mode: Literal["direct", "remote"]
    surface_condition: str = Field(min_length=1)
    surface_preparation: str = Field(min_length=1)
    illumination_basis: str = Field(min_length=1)
    resolution_check_basis: str = Field(min_length=1)
    areas: list[VisualExaminationArea] = Field(min_length=1)
    indications: list[VisualSurfaceIndication] = Field(default_factory=list)
    areas_mutually_exclusive_reviewed: bool
    coverage_reviewed: bool
    surface_condition_reviewed: bool
    indication_mapping_reviewed: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def identities(self):
        area_ids = [area.area_id for area in self.areas]
        if len(set(area_ids)) != len(area_ids):
            raise ValueError("visual examination area IDs must be unique")
        indication_ids = [item.indication_id for item in self.indications]
        if len(set(indication_ids)) != len(indication_ids):
            raise ValueError("visual indication IDs must be unique")
        unknown = {item.area_id for item in self.indications} - set(area_ids)
        if unknown:
            raise ValueError("every visual indication must reference a declared examination area")
        return self


def visual_surface_summary(x: VisualSurfaceExamination) -> Calculation:
    target = sum(area.target_area_m2 for area in x.areas)
    examined = sum(area.examined_area_m2 for area in x.areas)
    missing_reviews = []
    for field in (
        "areas_mutually_exclusive_reviewed",
        "coverage_reviewed",
        "surface_condition_reviewed",
        "indication_mapping_reviewed",
    ):
        if not getattr(x, field):
            missing_reviews.append(field)
    if not x.indications and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")
    counts = {}
    for indication in x.indications:
        counts[indication.indication_type] = counts.get(indication.indication_type, 0) + 1
    lengths = [
        indication.measured_length_m
        for indication in x.indications
        if indication.measured_length_m is not None
    ]
    widths = [
        indication.measured_width_m for indication in x.indications if indication.measured_width_m is not None
    ]
    return Calculation(
        status="needs_data" if missing_reviews else "computed",
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "examination_mode": x.examination_mode,
            "target_area_m2": target,
            "examined_area_m2": examined,
            "unexamined_area_m2": target - examined,
            "coverage_fraction": examined / target,
            "area_count": len(x.areas),
            "incomplete_area_ids": [
                area.area_id for area in x.areas if area.examined_area_m2 < area.target_area_m2
            ],
            "indication_count": len(x.indications),
            "indication_counts_by_reported_type": counts,
            "indication_ids": [item.indication_id for item in x.indications],
            "measured_length_count": len(lengths),
            "maximum_reported_indication_length_m": max(lengths, default=None),
            "measured_width_count": len(widths),
            "maximum_reported_indication_width_m": max(widths, default=None),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Reported indication types and dimensions are observations under the declared procedure, not flaw classifications or acceptance decisions.",
            "Coverage and a negative record do not establish probability of detection or absence of flaws.",
            "No code acceptance criteria, severity ranking, repair disposition, remaining life or failure probability is inferred.",
        ),
    )


class GasInventoryEnergy(Contract):
    initial_absolute_pressure_Pa: Positive
    final_absolute_pressure_Pa: Positive
    initial_volume_m3: Positive
    heat_capacity_ratio: float = Field(gt=1)


class ReferenceEnergyMass(Contract):
    """Normalize declared energy by a caller-owned reference specific energy."""

    energy_J: Nonnegative
    reference_specific_energy_J_kg: Positive
    reference_id: str = Field(min_length=1)
    energy_basis: str = Field(min_length=1)


def reference_energy_mass(x: ReferenceEnergyMass) -> Calculation:
    return Calculation(
        values={
            "reference_equivalent_mass_kg": x.energy_J / x.reference_specific_energy_J_kg,
            "reference_id": x.reference_id,
            "energy_basis": x.energy_basis,
        },
        notes=(
            "Energy normalization only; blast efficiency, overpressure and exclusion distance are not inferred.",
        ),
    )


def gas_expansion_energy(x: GasInventoryEnergy) -> Calculation:
    if x.final_absolute_pressure_Pa > x.initial_absolute_pressure_Pa:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Expansion requires final pressure no greater than initial pressure.",),
        )
    gamma = x.heat_capacity_ratio
    if x.final_absolute_pressure_Pa == x.initial_absolute_pressure_Pa:
        return Calculation(values=dict(ideal_expansion_work_J=0.0, final_volume_m3=x.initial_volume_m3))
    ratio_delta = (
        x.initial_absolute_pressure_Pa - x.final_absolute_pressure_Pa
    ) / x.final_absolute_pressure_Pa
    log_ratio = (
        math.log1p(ratio_delta)
        if math.isfinite(ratio_delta)
        else math.log(x.initial_absolute_pressure_Pa) - math.log(x.final_absolute_pressure_Pa)
    )
    try:
        volume_log_factor = log_ratio / gamma
        if volume_log_factor < 700:
            final_volume = float(Rational(x.initial_volume_m3) * Rational(math.exp(volume_log_factor)))
        else:
            final_volume = math.exp(math.log(x.initial_volume_m3) + volume_log_factor)
        release_factor = -math.expm1(-((gamma - 1) / gamma) * log_ratio)
        work = float(
            Rational(x.initial_absolute_pressure_Pa)
            * Rational(x.initial_volume_m3)
            * Rational(release_factor)
            / Rational(gamma - 1)
        )
        if final_volume == 0 or work == 0:
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Ideal expansion work or final volume exceeds numeric support.",),
        )
    return Calculation(values=dict(ideal_expansion_work_J=work, final_volume_m3=final_volume))


class GuidedWavePairFeatures(Contract):
    """Descriptive features for one aligned baseline/current guided-wave channel pair."""

    specimen_id: str = Field(min_length=1)
    baseline_acquisition_id: str = Field(min_length=1)
    observation_acquisition_id: str = Field(min_length=1)
    frequency_Hz: Positive
    wave_mode: Literal["torsional", "flexural"]
    baseline_distance_m: list[float] = Field(min_length=2)
    baseline_voltage_V: list[float] = Field(min_length=2)
    observation_distance_m: list[float] = Field(min_length=2)
    observation_voltage_V: list[float] = Field(min_length=2)
    window_start_m: float
    window_end_m: float
    distance_match_tolerance_m: Nonnegative = 0.0
    duplicate_distance_policy: Literal["preserve_samples", "mean_aligned_duplicates", "reject"] = (
        "preserve_samples"
    )

    @model_validator(mode="after")
    def aligned_pair(self):
        if self.baseline_acquisition_id == self.observation_acquisition_id:
            raise ValueError("baseline and observation acquisition IDs must differ")
        vectors = (
            self.baseline_distance_m,
            self.baseline_voltage_V,
            self.observation_distance_m,
            self.observation_voltage_V,
        )
        if len({len(vector) for vector in vectors}) != 1:
            raise ValueError("guided-wave distance and voltage vectors must have equal length")
        if self.window_end_m <= self.window_start_m:
            raise ValueError("guided-wave feature window must have positive length")
        for distances in (self.baseline_distance_m, self.observation_distance_m):
            if any(b < a for a, b in zip(distances, distances[1:], strict=False)):
                raise ValueError("guided-wave distance axes must retain nondecreasing provider order")
        mismatch = max(
            abs(a - b) for a, b in zip(self.baseline_distance_m, self.observation_distance_m, strict=True)
        )
        if mismatch > self.distance_match_tolerance_m:
            raise ValueError("guided-wave distance grids are not aligned within the declared tolerance")
        baseline_repeats = [
            right == left
            for left, right in zip(self.baseline_distance_m, self.baseline_distance_m[1:], strict=False)
        ]
        observation_repeats = [
            right == left
            for left, right in zip(self.observation_distance_m, self.observation_distance_m[1:], strict=False)
        ]
        if baseline_repeats != observation_repeats:
            raise ValueError("guided-wave repeated-distance positions must align between acquisitions")
        return self


class GuidedWaveReferenceEnsemble(Contract):
    """Descriptive comparison with an explicitly selected acquisition ensemble."""

    specimen_id: str = Field(min_length=1)
    baseline_acquisition_ids: list[str] = Field(min_length=3)
    observation_acquisition_id: str = Field(min_length=1)
    baseline_source_group_id: str = Field(min_length=1)
    observation_source_group_id: str = Field(min_length=1)
    baseline_selection_basis: str = Field(min_length=1)
    frequency_Hz: Positive
    wave_mode: Literal["torsional", "flexural"]
    distance_m: list[float] = Field(min_length=2)
    baseline_voltage_V: list[list[float]] = Field(min_length=3)
    observation_distance_m: list[float] = Field(min_length=2)
    observation_voltage_V: list[float] = Field(min_length=2)
    window_start_m: float
    window_end_m: float
    distance_match_tolerance_m: Nonnegative = 0.0
    duplicate_distance_policy: Literal["preserve_samples", "mean_aligned_duplicates", "reject"] = (
        "preserve_samples"
    )
    reference_statistic: Literal["mean", "median"] = "median"

    @model_validator(mode="after")
    def aligned_ensemble(self):
        if len(set(self.baseline_acquisition_ids)) != len(self.baseline_acquisition_ids):
            raise ValueError("guided-wave baseline acquisition IDs must be unique")
        if self.observation_acquisition_id in self.baseline_acquisition_ids:
            raise ValueError("guided-wave observation cannot also be a baseline acquisition")
        if len(self.baseline_voltage_V) != len(self.baseline_acquisition_ids):
            raise ValueError("one guided-wave voltage vector is required per baseline acquisition")
        if self.window_end_m <= self.window_start_m:
            raise ValueError("guided-wave ensemble window must have positive length")
        sample_count = len(self.distance_m)
        if (
            len(self.observation_distance_m) != sample_count
            or len(self.observation_voltage_V) != sample_count
        ):
            raise ValueError("guided-wave observation vectors must align with the reference distance axis")
        if any(len(values) != sample_count for values in self.baseline_voltage_V):
            raise ValueError("guided-wave baseline vectors must align with the reference distance axis")
        for distances in (self.distance_m, self.observation_distance_m):
            if any(right < left for left, right in zip(distances, distances[1:], strict=False)):
                raise ValueError(
                    "guided-wave ensemble distance axes must retain nondecreasing provider order"
                )
        mismatch = max(
            abs(reference - observed)
            for reference, observed in zip(self.distance_m, self.observation_distance_m, strict=True)
        )
        if mismatch > self.distance_match_tolerance_m:
            raise ValueError("guided-wave ensemble distance grids exceed the declared tolerance")
        reference_repeats = [
            right == left for left, right in zip(self.distance_m, self.distance_m[1:], strict=False)
        ]
        observation_repeats = [
            right == left
            for left, right in zip(self.observation_distance_m, self.observation_distance_m[1:], strict=False)
        ]
        if reference_repeats != observation_repeats:
            raise ValueError("guided-wave ensemble repeated-distance positions must align")
        return self


def _mean_duplicate_groups(distance, baseline, observation):
    grouped_distance = []
    grouped_baseline = []
    grouped_observation = []
    start = 0
    while start < len(distance):
        stop = start + 1
        while stop < len(distance) and distance[stop] == distance[start]:
            stop += 1
        grouped_distance.append(distance[start])
        grouped_baseline.append(float(np.mean(baseline[start:stop])))
        grouped_observation.append(float(np.mean(observation[start:stop])))
        start = stop
    return np.asarray(grouped_distance), np.asarray(grouped_baseline), np.asarray(grouped_observation)


def _mean_duplicate_ensemble(distance, baselines, observation):
    grouped_distance = []
    grouped_baselines = []
    grouped_observation = []
    start = 0
    while start < len(distance):
        stop = start + 1
        while stop < len(distance) and distance[stop] == distance[start]:
            stop += 1
        grouped_distance.append(distance[start])
        grouped_baselines.append(np.mean(baselines[:, start:stop], axis=1))
        grouped_observation.append(float(np.mean(observation[start:stop])))
        start = stop
    return (
        np.asarray(grouped_distance),
        np.asarray(grouped_baselines).T,
        np.asarray(grouped_observation),
    )


def guided_wave_pair_features(x: GuidedWavePairFeatures) -> Calculation:
    baseline_distance = np.asarray(x.baseline_distance_m)
    observation_distance = np.asarray(x.observation_distance_m)
    baseline = np.asarray(x.baseline_voltage_V)
    observation = np.asarray(x.observation_voltage_V)
    selected = (baseline_distance >= x.window_start_m) & (baseline_distance <= x.window_end_m)
    if np.count_nonzero(selected) < 2:
        return Calculation(
            status="needs_data",
            values={"selected_samples": int(np.count_nonzero(selected))},
            notes=("At least two aligned samples are required inside the declared spatial window.",),
        )
    distance = baseline_distance[selected]
    baseline = baseline[selected]
    observation = observation[selected]
    observed_selected_distance = observation_distance[selected]
    repeated = int(np.count_nonzero(np.diff(distance) == 0))
    if repeated and x.duplicate_distance_policy == "reject":
        return Calculation(
            status="out_of_scope",
            values={"selected_samples": len(distance), "repeated_distance_intervals": repeated},
            notes=("The selected window contains repeated provider distance samples.",),
        )
    raw_samples = len(distance)
    if x.duplicate_distance_policy == "mean_aligned_duplicates":
        distance, baseline, observation = _mean_duplicate_groups(distance, baseline, observation)
    residual = observation - baseline
    baseline_rms = float(np.sqrt(np.mean(baseline**2)))
    observation_rms = float(np.sqrt(np.mean(observation**2)))
    residual_rms = float(np.sqrt(np.mean(residual**2)))
    baseline_centered = baseline - np.mean(baseline)
    observation_centered = observation - np.mean(observation)
    correlation_denominator = float(
        np.sqrt(
            np.dot(baseline_centered, baseline_centered) * np.dot(observation_centered, observation_centered)
        )
    )
    correlation = (
        None
        if correlation_denominator == 0
        else float(np.dot(baseline_centered, observation_centered) / correlation_denominator)
    )
    baseline_energy = float(np.dot(baseline, baseline))
    return Calculation(
        values={
            "specimen_id": x.specimen_id,
            "baseline_acquisition_id": x.baseline_acquisition_id,
            "observation_acquisition_id": x.observation_acquisition_id,
            "frequency_Hz": x.frequency_Hz,
            "wave_mode": x.wave_mode,
            "window_start_m": x.window_start_m,
            "window_end_m": x.window_end_m,
            "maximum_distance_grid_mismatch_m": float(
                np.max(np.abs(baseline_distance - observation_distance))
            ),
            "raw_selected_samples": raw_samples,
            "effective_selected_samples": len(distance),
            "repeated_distance_intervals": repeated,
            "duplicate_distance_policy": x.duplicate_distance_policy,
            "effective_distance_start_m": float(distance[0]),
            "effective_distance_end_m": float(distance[-1]),
            "baseline_rms_V": baseline_rms,
            "observation_rms_V": observation_rms,
            "residual_rms_V": residual_rms,
            "normalized_residual_rms": None if baseline_rms == 0 else residual_rms / baseline_rms,
            "voltage_energy_ratio": None
            if baseline_energy == 0
            else float(np.dot(observation, observation) / baseline_energy),
            "correlation_coefficient": correlation,
            "peak_absolute_difference_V": float(np.max(np.abs(residual))),
            "signed_mean_difference_V": float(np.mean(residual)),
            "observation_selected_distance_start_m": float(observed_selected_distance[0]),
            "observation_selected_distance_end_m": float(observed_selected_distance[-1]),
        },
        notes=(
            "These are paired waveform descriptors, not remaining thickness, defect dimensions, POD, acceptance, life or failure probability.",
            "A single baseline comparison can confound environmental, coupling, acquisition and damage effects.",
        ),
    )


class InspectionForecastPoint(Contract):
    """One reviewed candidate time on a cumulative first-crossing probability curve."""

    forecast_point_id: str = Field(min_length=1)
    horizon_end_s: Positive
    cumulative_probability_given_survival: Fraction
    cumulative_probability_upper_bound: Fraction | None = None

    @model_validator(mode="after")
    def ordered_probability_bound(self):
        if (
            self.cumulative_probability_upper_bound is not None
            and self.cumulative_probability_upper_bound < self.cumulative_probability_given_survival
        ):
            raise ValueError("probability upper bound cannot be below the point estimate")
        return self


class ThresholdInspectionSchedule(Contract):
    """Select one reviewed candidate without interpolating or optimizing consequences."""

    schema_version: Literal["matintegrity.threshold_inspection_schedule.v1"] = (
        "matintegrity.threshold_inspection_schedule.v1"
    )
    schedule_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    assessment_time_s: Nonnegative
    conditioning: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    forecast_model_id: str = Field(min_length=1)
    forecast_model_revision: str = Field(min_length=1)
    forecast_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    forecast_points: list[InspectionForecastPoint] = Field(min_length=2)
    probability_basis: Literal["estimate", "upper_bound"]
    maximum_probability_before_inspection: float = Field(gt=0.0, lt=1.0)
    minimum_notice_s: Nonnegative = 0.0
    maximum_deferral_s: Positive
    forecast_identity_reviewed: bool
    event_scope_and_conditioning_reviewed: bool
    cumulative_probability_curve_reviewed: bool
    scheduling_criterion_user_approved: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_forecast(self):
        if self.maximum_deferral_s <= self.minimum_notice_s:
            raise ValueError("maximum deferral must exceed the minimum notice time")
        ids = [point.forecast_point_id for point in self.forecast_points]
        if len(set(ids)) != len(ids):
            raise ValueError("inspection forecast point IDs must be unique")
        times = [point.horizon_end_s for point in self.forecast_points]
        if any(time <= self.assessment_time_s for time in times):
            raise ValueError("every forecast horizon must end after the assessment time")
        if any(right <= left for left, right in zip(times, times[1:], strict=False)):
            raise ValueError("inspection forecast horizons must strictly increase")
        estimates = [point.cumulative_probability_given_survival for point in self.forecast_points]
        if any(right < left for left, right in zip(estimates, estimates[1:], strict=False)):
            raise ValueError("cumulative probability estimates must be nondecreasing")
        bounds = [point.cumulative_probability_upper_bound for point in self.forecast_points]
        if self.probability_basis == "upper_bound" and any(value is None for value in bounds):
            raise ValueError("upper-bound scheduling requires a bound at every forecast point")
        supplied_bounds = [value for value in bounds if value is not None]
        if any(right < left for left, right in zip(supplied_bounds, supplied_bounds[1:], strict=False)):
            raise ValueError("supplied cumulative probability upper bounds must be nondecreasing")
        return self


def threshold_inspection_schedule(x: ThresholdInspectionSchedule) -> Calculation:
    gates = {
        "forecast_identity_reviewed": x.forecast_identity_reviewed,
        "event_scope_and_conditioning_reviewed": x.event_scope_and_conditioning_reviewed,
        "cumulative_probability_curve_reviewed": x.cumulative_probability_curve_reviewed,
        "scheduling_criterion_user_approved": x.scheduling_criterion_user_approved,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    window_start = x.assessment_time_s + x.minimum_notice_s
    window_end = x.assessment_time_s + x.maximum_deferral_s
    common = {
        "schedule_id": x.schedule_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "event_id": x.event_id,
        "assessment_time_s": x.assessment_time_s,
        "conditioning": x.conditioning,
        "forecast_model_id": x.forecast_model_id,
        "forecast_model_revision": x.forecast_model_revision,
        "forecast_input_sha256": x.forecast_input_sha256,
        "probability_basis": x.probability_basis,
        "maximum_probability_before_inspection": x.maximum_probability_before_inspection,
        "candidate_window_start_s": window_start,
        "candidate_window_end_s": window_end,
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "schedule_state": "review_required"},
            notes=(
                "All forecast, event-scope, probability-curve and scheduling-criterion reviews are required.",
            ),
        )
    eligible = [point for point in x.forecast_points if window_start <= point.horizon_end_s <= window_end]
    if not eligible:
        return Calculation(
            status="needs_data",
            values={**common, "schedule_state": "no_candidate_in_allowed_window"},
            notes=("No reviewed forecast point lies inside the notice and maximum-deferral window.",),
        )

    def decision_probability(point: InspectionForecastPoint) -> float:
        if x.probability_basis == "estimate":
            return point.cumulative_probability_given_survival
        assert point.cumulative_probability_upper_bound is not None
        return point.cumulative_probability_upper_bound

    compliant = [
        point for point in eligible if decision_probability(point) <= x.maximum_probability_before_inspection
    ]
    if not compliant:
        first = eligible[0]
        return Calculation(
            status="needs_data",
            values={
                **common,
                "schedule_state": "criterion_exceeded_before_earliest_candidate",
                "earliest_candidate_time_s": first.horizon_end_s,
                "earliest_candidate_probability": decision_probability(first),
            },
            notes=(
                "The declared probability criterion is already exceeded at the earliest eligible reviewed candidate; an earlier forecast point or an immediate user decision is required.",
            ),
        )
    selected = compliant[-1]
    selected_index = eligible.index(selected)
    later = eligible[selected_index + 1 :]
    next_noncompliant = next(
        (point for point in later if decision_probability(point) > x.maximum_probability_before_inspection),
        None,
    )
    if next_noncompliant is not None:
        state = "criterion_limited"
    elif x.forecast_points[-1].horizon_end_s <= window_end:
        state = "forecast_boundary_limited"
    else:
        state = "maximum_deferral_limited"
    return Calculation(
        values={
            **common,
            "schedule_state": state,
            "eligible_candidate_count": len(eligible),
            "selected_forecast_point_id": selected.forecast_point_id,
            "selected_inspection_time_s": selected.horizon_end_s,
            "selected_time_from_assessment_s": selected.horizon_end_s - x.assessment_time_s,
            "selected_probability_given_survival": decision_probability(selected),
            "selected_probability_estimate": selected.cumulative_probability_given_survival,
            "selected_probability_upper_bound": selected.cumulative_probability_upper_bound,
            "probability_margin_to_criterion": (
                x.maximum_probability_before_inspection - decision_probability(selected)
            ),
            "next_noncompliant_candidate_time_s": (
                None if next_noncompliant is None else next_noncompliant.horizon_end_s
            ),
            "next_noncompliant_candidate_probability": (
                None if next_noncompliant is None else decision_probability(next_noncompliant)
            ),
            "forecast_support_end_s": x.forecast_points[-1].horizon_end_s,
            "continuous_time_interpolation_performed": False,
            "consequence_optimization_performed": False,
        },
        notes=(
            "The selected time is the latest supplied candidate in the allowed window satisfying the user-approved probability criterion on the declared estimate or upper-bound basis.",
            "No probability interpolation, consequence optimization, inspection effectiveness, intervention benefit or regulatory acceptance is inferred.",
        ),
    )


def _threshold_schedule_context(x: ThresholdInspectionSchedule, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("inspection schedule asset and location must match the run context")


class RiskCostComponent(Contract):
    """One reviewed additive cost in the comparison's declared common cost basis."""

    component_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    amount: Nonnegative
    basis: str = Field(min_length=1)


class InspectionActionRiskCandidate(Contract):
    """One complete action alternative and its externally evaluated residual event probability."""

    action_id: str = Field(min_length=1)
    action_label: str = Field(min_length=1)
    candidate_kind: Literal["baseline", "intervention"]
    action_definition: str = Field(min_length=1)
    action_effect_model_id: str = Field(min_length=1)
    action_effect_model_revision: str = Field(min_length=1)
    action_effect_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    action_effect_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    risk_model_structure_id: str = Field(min_length=1)
    event_probability_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    common_cause_group_ids: list[str] = Field(default_factory=list)
    residual_failure_probability_estimate: Fraction
    residual_failure_probability_upper_bound: Fraction | None = None
    action_cost_components: list[RiskCostComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def ordered_probability_bound(self):
        upper = self.residual_failure_probability_upper_bound
        if upper is not None and upper < self.residual_failure_probability_estimate:
            raise ValueError("residual probability upper bound cannot be below its estimate")
        component_ids = [component.component_id for component in self.action_cost_components]
        if len(set(component_ids)) != len(component_ids):
            raise ValueError("action cost component IDs must be unique within each candidate")
        if len(set(self.common_cause_group_ids)) != len(self.common_cause_group_ids):
            raise ValueError("common-cause group IDs must be unique within each candidate")
        return self


class InspectionActionExpectedLossComparison(Contract):
    """Compare complete reviewed actions over one event, scope, horizon and cost basis."""

    schema_version: Literal["matintegrity.inspection_action_expected_loss.v1"] = (
        "matintegrity.inspection_action_expected_loss.v1"
    )
    comparison_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    probability_basis: Literal["estimate", "upper_bound"]
    cost_basis_id: str = Field(min_length=1)
    currency_or_normalized_unit: str = Field(min_length=1)
    failure_consequence_components: list[RiskCostComponent] = Field(min_length=1)
    candidates: list[InspectionActionRiskCandidate] = Field(min_length=2)
    cost_tie_absolute_tolerance: Nonnegative = 0.0
    action_definitions_reviewed: bool
    residual_probabilities_reviewed: bool
    costs_and_consequences_reviewed: bool
    decision_criterion_user_approved: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_comparison(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("comparison horizon must have positive duration")
        action_ids = [candidate.action_id for candidate in self.candidates]
        if len(set(action_ids)) != len(action_ids):
            raise ValueError("inspection action IDs must be unique")
        baselines = [candidate for candidate in self.candidates if candidate.candidate_kind == "baseline"]
        if len(baselines) != 1:
            raise ValueError("exactly one baseline candidate is required")
        if any(component.amount != 0.0 for component in baselines[0].action_cost_components):
            raise ValueError("baseline action cost components must be zero")
        consequence_ids = [component.component_id for component in self.failure_consequence_components]
        if len(set(consequence_ids)) != len(consequence_ids):
            raise ValueError("failure consequence component IDs must be unique")
        if self.probability_basis == "upper_bound" and any(
            candidate.residual_failure_probability_upper_bound is None for candidate in self.candidates
        ):
            raise ValueError("upper-bound comparison requires a bound for every candidate")
        return self


def inspection_action_expected_loss(x: InspectionActionExpectedLossComparison) -> Calculation:
    gates = {
        "action_definitions_reviewed": x.action_definitions_reviewed,
        "residual_probabilities_reviewed": x.residual_probabilities_reviewed,
        "costs_and_consequences_reviewed": x.costs_and_consequences_reviewed,
        "decision_criterion_user_approved": x.decision_criterion_user_approved,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "comparison_id": x.comparison_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "event_id": x.event_id,
        "horizon_start_s": x.horizon_start_s,
        "horizon_end_s": x.horizon_end_s,
        "conditioning": x.conditioning,
        "probability_basis": x.probability_basis,
        "cost_basis_id": x.cost_basis_id,
        "currency_or_normalized_unit": x.currency_or_normalized_unit,
        "comparison_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "comparison_state": "review_required"},
            notes=(
                "Action definitions, residual probabilities, all cost inputs and the decision criterion must be reviewed before comparison.",
            ),
        )

    consequence_cost = sum(component.amount for component in x.failure_consequence_components)

    def probability(candidate: InspectionActionRiskCandidate) -> float:
        if x.probability_basis == "estimate":
            return candidate.residual_failure_probability_estimate
        assert candidate.residual_failure_probability_upper_bound is not None
        return candidate.residual_failure_probability_upper_bound

    provisional = []
    for candidate in x.candidates:
        direct_cost = sum(component.amount for component in candidate.action_cost_components)
        probability_used = probability(candidate)
        failure_loss = probability_used * consequence_cost
        provisional.append(
            {
                "action_id": candidate.action_id,
                "action_label": candidate.action_label,
                "candidate_kind": candidate.candidate_kind,
                "action_definition": candidate.action_definition,
                "action_effect_model_id": candidate.action_effect_model_id,
                "action_effect_model_revision": candidate.action_effect_model_revision,
                "action_effect_input_sha256": candidate.action_effect_input_sha256,
                "action_effect_configuration_sha256": candidate.action_effect_configuration_sha256,
                "risk_model_structure_id": candidate.risk_model_structure_id,
                "event_probability_result_sha256": candidate.event_probability_result_sha256,
                "common_cause_group_ids": candidate.common_cause_group_ids,
                "residual_failure_probability_used": probability_used,
                "residual_failure_probability_estimate": candidate.residual_failure_probability_estimate,
                "residual_failure_probability_upper_bound": (
                    candidate.residual_failure_probability_upper_bound
                ),
                "direct_action_cost": direct_cost,
                "expected_failure_loss": failure_loss,
                "total_expected_loss": direct_cost + failure_loss,
                "action_cost_components": [
                    component.model_dump(mode="json") for component in candidate.action_cost_components
                ],
            }
        )
    baseline = next(row for row in provisional if row["candidate_kind"] == "baseline")
    baseline_failure_loss = baseline["expected_failure_loss"]
    baseline_total = baseline["total_expected_loss"]
    rows = []
    for row in provisional:
        rows.append(
            {
                **row,
                "expected_failure_loss_reduction_vs_baseline": (
                    baseline_failure_loss - row["expected_failure_loss"]
                ),
                "incremental_total_loss_vs_baseline": row["total_expected_loss"] - baseline_total,
                "net_expected_benefit_vs_baseline": baseline_total - row["total_expected_loss"],
            }
        )
    minimum = min(row["total_expected_loss"] for row in rows)
    tied = [
        row["action_id"]
        for row in rows
        if abs(row["total_expected_loss"] - minimum) <= x.cost_tie_absolute_tolerance
    ]
    values = {
        **common,
        "failure_consequence_cost": consequence_cost,
        "failure_consequence_components": [
            component.model_dump(mode="json") for component in x.failure_consequence_components
        ],
        "baseline_action_id": baseline["action_id"],
        "baseline_total_expected_loss": baseline_total,
        "candidate_results": rows,
        "minimum_total_expected_loss": minimum,
        "cost_tie_absolute_tolerance": x.cost_tie_absolute_tolerance,
        "tied_minimum_action_ids": tied,
        "selected_action_id": tied[0] if len(tied) == 1 else None,
        "comparison_state": "unique_minimum" if len(tied) == 1 else "minimum_tie",
        "probability_or_action_effect_inferred": False,
        "regulatory_acceptance_inferred": False,
    }
    if len(tied) != 1:
        return Calculation(
            status="needs_data",
            values=values,
            notes=(
                "Two or more actions are tied within the caller-declared absolute cost tolerance; no arbitrary action is selected.",
                "The arithmetic comparison is not a regulatory acceptance decision or a validation of any supplied action-effect model.",
            ),
        )
    return Calculation(
        values=values,
        notes=(
            "The selected action has the lowest supplied expected loss on the declared probability and cost basis.",
            "The comparison does not infer action effectiveness, event probabilities, cost inputs, risk tolerance or regulatory acceptance.",
        ),
    )


def _inspection_action_expected_loss_context(
    x: InspectionActionExpectedLossComparison, context: RunContext
) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("inspection action comparison asset and location must match the run context")


class InspectionDispositionOutcomeBranch(Contract):
    """One mutually exclusive inspection outcome and its reviewed downstream disposition."""

    outcome_id: str = Field(min_length=1)
    outcome_label: str = Field(min_length=1)
    probability_given_inspection: Fraction
    disposition_id: str = Field(min_length=1)
    disposition_label: str = Field(min_length=1)
    disposition_definition: str = Field(min_length=1)
    disposition_effect_model_id: str = Field(min_length=1)
    disposition_effect_model_revision: str = Field(min_length=1)
    disposition_effect_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    disposition_effect_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    disposition_event_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    residual_failure_probability_given_outcome_and_disposition: Fraction
    disposition_cost_components: list[RiskCostComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_cost_components(self):
        component_ids = [component.component_id for component in self.disposition_cost_components]
        if len(set(component_ids)) != len(component_ids):
            raise ValueError("disposition cost component IDs must be unique within each outcome")
        return self


class InspectionDispositionDecisionTree(Contract):
    """Reduce a complete reviewed one-inspection outcome tree to expected cost and residual risk."""

    schema_version: Literal["matintegrity.inspection_disposition_tree.v1"] = (
        "matintegrity.inspection_disposition_tree.v1"
    )
    tree_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    inspection_action_id: str = Field(min_length=1)
    inspection_action_label: str = Field(min_length=1)
    inspection_action_definition: str = Field(min_length=1)
    inspection_outcome_model_id: str = Field(min_length=1)
    inspection_outcome_model_revision: str = Field(min_length=1)
    inspection_outcome_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    inspection_outcome_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    risk_model_structure_id: str = Field(min_length=1)
    common_cause_group_ids: list[str] = Field(default_factory=list)
    cost_basis_id: str = Field(min_length=1)
    currency_or_normalized_unit: str = Field(min_length=1)
    inspection_cost_components: list[RiskCostComponent] = Field(default_factory=list)
    outcome_branches: list[InspectionDispositionOutcomeBranch] = Field(min_length=2)
    maximum_outcome_probability_sum_error: Positive = 1e-12
    outcome_partition_reviewed: bool
    outcome_probabilities_reviewed: bool
    disposition_definitions_reviewed: bool
    disposition_effects_reviewed: bool
    costs_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_tree(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("disposition-tree horizon must have positive duration")
        outcome_ids = [branch.outcome_id for branch in self.outcome_branches]
        if len(set(outcome_ids)) != len(outcome_ids):
            raise ValueError("inspection outcome IDs must be unique")
        inspection_cost_ids = [component.component_id for component in self.inspection_cost_components]
        if len(set(inspection_cost_ids)) != len(inspection_cost_ids):
            raise ValueError("inspection cost component IDs must be unique")
        if len(set(self.common_cause_group_ids)) != len(self.common_cause_group_ids):
            raise ValueError("common-cause group IDs must be unique")
        probability_sum = sum(branch.probability_given_inspection for branch in self.outcome_branches)
        if abs(probability_sum - 1.0) > self.maximum_outcome_probability_sum_error:
            raise ValueError("inspection outcome probabilities must sum to one within tolerance")
        return self


def inspection_disposition_tree(x: InspectionDispositionDecisionTree) -> Calculation:
    gates = {
        "outcome_partition_reviewed": x.outcome_partition_reviewed,
        "outcome_probabilities_reviewed": x.outcome_probabilities_reviewed,
        "disposition_definitions_reviewed": x.disposition_definitions_reviewed,
        "disposition_effects_reviewed": x.disposition_effects_reviewed,
        "costs_reviewed": x.costs_reviewed,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "tree_id": x.tree_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "event_id": x.event_id,
        "horizon_start_s": x.horizon_start_s,
        "horizon_end_s": x.horizon_end_s,
        "conditioning": x.conditioning,
        "inspection_action_id": x.inspection_action_id,
        "cost_basis_id": x.cost_basis_id,
        "currency_or_normalized_unit": x.currency_or_normalized_unit,
        "tree_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "tree_state": "review_required"},
            notes=("Every outcome, probability, disposition, effect and cost review is required.",),
        )
    inspection_cost = sum(component.amount for component in x.inspection_cost_components)
    branch_results = []
    expected_disposition_cost = 0.0
    residual_probability = 0.0
    for branch in x.outcome_branches:
        disposition_cost = sum(component.amount for component in branch.disposition_cost_components)
        cost_contribution = branch.probability_given_inspection * disposition_cost
        probability_contribution = (
            branch.probability_given_inspection
            * branch.residual_failure_probability_given_outcome_and_disposition
        )
        expected_disposition_cost += cost_contribution
        residual_probability += probability_contribution
        branch_results.append(
            {
                "outcome_id": branch.outcome_id,
                "outcome_label": branch.outcome_label,
                "probability_given_inspection": branch.probability_given_inspection,
                "disposition_id": branch.disposition_id,
                "disposition_label": branch.disposition_label,
                "disposition_definition": branch.disposition_definition,
                "disposition_effect_model_id": branch.disposition_effect_model_id,
                "disposition_effect_model_revision": branch.disposition_effect_model_revision,
                "disposition_effect_configuration_sha256": (branch.disposition_effect_configuration_sha256),
                "disposition_effect_input_sha256": branch.disposition_effect_input_sha256,
                "disposition_event_result_sha256": branch.disposition_event_result_sha256,
                "residual_failure_probability_given_outcome_and_disposition": (
                    branch.residual_failure_probability_given_outcome_and_disposition
                ),
                "disposition_cost": disposition_cost,
                "expected_disposition_cost_contribution": cost_contribution,
                "residual_failure_probability_contribution": probability_contribution,
                "disposition_cost_components": [
                    component.model_dump(mode="json") for component in branch.disposition_cost_components
                ],
            }
        )
    return Calculation(
        values={
            **common,
            "tree_state": "computed",
            "outcome_probability_sum": sum(
                branch.probability_given_inspection for branch in x.outcome_branches
            ),
            "inspection_cost": inspection_cost,
            "expected_disposition_cost": expected_disposition_cost,
            "expected_total_action_cost": inspection_cost + expected_disposition_cost,
            "residual_failure_probability_estimate": residual_probability,
            "branch_results": branch_results,
            "risk_model_structure_id": x.risk_model_structure_id,
            "common_cause_group_ids": x.common_cause_group_ids,
            "upper_bound_computed": False,
            "pod_or_false_call_inferred": False,
        },
        notes=(
            "Outcome probabilities and conditional disposition effects are supplied reviewed inputs; the result is their finite expectation.",
            "No POD, false-call rate, outcome probability, disposition rule, confidence bound or regulatory acceptance is inferred.",
        ),
    )


def _inspection_disposition_tree_context(x: InspectionDispositionDecisionTree, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("inspection disposition tree asset and location must match the run context")


class PolicyStageCostComponent(Contract):
    component_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    amount_at_stage_time: Nonnegative
    present_value_factor: Nonnegative
    basis: str = Field(min_length=1)


class InspectionPolicyStage(Contract):
    stage_id: str = Field(min_length=1)
    stage_time_s: Nonnegative
    observed_state_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    action_definition: str = Field(min_length=1)
    action_model_id: str = Field(min_length=1)
    action_model_revision: str = Field(min_length=1)
    action_model_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    action_model_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cost_components: list[PolicyStageCostComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_cost_ids(self):
        ids = [component.component_id for component in self.cost_components]
        if len(set(ids)) != len(ids):
            raise ValueError("policy-stage cost component IDs must be unique")
        return self


class InspectionPolicyPath(Contract):
    path_id: str = Field(min_length=1)
    path_probability_given_start_survival: Fraction
    path_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stages: list[InspectionPolicyStage] = Field(default_factory=list)
    first_failure_occurred: bool
    first_failure_time_s: Nonnegative | None = None
    failure_consequence_present_value_factor: Nonnegative | None = None

    @model_validator(mode="after")
    def aligned_path(self):
        stage_ids = [stage.stage_id for stage in self.stages]
        if len(set(stage_ids)) != len(stage_ids):
            raise ValueError("policy stage IDs must be unique within each path")
        stage_times = [stage.stage_time_s for stage in self.stages]
        if any(right <= left for left, right in zip(stage_times, stage_times[1:], strict=False)):
            raise ValueError("policy stage times must strictly increase within each path")
        failure_values_present = (
            self.first_failure_time_s is not None
            and self.failure_consequence_present_value_factor is not None
        )
        if self.first_failure_occurred != failure_values_present:
            raise ValueError(
                "first-failure time and consequence present-value factor are required exactly for failure paths"
            )
        return self


class FinitePolicyState(Contract):
    state_id: str = Field(min_length=1)
    state_definition: str = Field(min_length=1)
    is_failure_state: bool


class PolicyObservationLabel(Contract):
    observation_id: str = Field(min_length=1)
    observation_definition: str = Field(min_length=1)


class PolicyCalibrationAction(Contract):
    action_id: str = Field(min_length=1)
    action_definition: str = Field(min_length=1)


class PolicyObservationCalibrationRecord(Contract):
    """One reviewed physical-state/inspection-label pair with a fixed data partition."""

    record_id: str = Field(min_length=1)
    sequence_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    observation_time_s: Nonnegative
    true_state_id: str = Field(min_length=1)
    observed_label_id: str = Field(min_length=1)
    weight: Positive = 1.0


class PolicyTransitionCalibrationRecord(Contract):
    """One reviewed state transition under an explicitly recorded action."""

    record_id: str = Field(min_length=1)
    sequence_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    interval_start_s: Nonnegative
    interval_end_s: Positive
    from_state_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    to_state_id: str = Field(min_length=1)
    weight: Positive = 1.0

    @model_validator(mode="after")
    def ordered_interval(self):
        if self.interval_end_s <= self.interval_start_s:
            raise ValueError("transition interval must have positive duration")
        return self


class FinitePolicyProbabilityCalibration(Contract):
    """Estimate finite policy tables from reviewed labels and an isolated holdout."""

    schema_version: Literal["matintegrity.finite_policy_probability_calibration.v1"] = (
        "matintegrity.finite_policy_probability_calibration.v1"
    )
    calibration_id: str = Field(min_length=1)
    states: list[FinitePolicyState] = Field(min_length=2)
    observation_labels: list[PolicyObservationLabel] = Field(min_length=2)
    actions: list[PolicyCalibrationAction] = Field(min_length=1)
    observation_records: list[PolicyObservationCalibrationRecord] = Field(min_length=2)
    transition_records: list[PolicyTransitionCalibrationRecord] = Field(min_length=2)
    symmetric_pseudocount: Nonnegative = 0.0
    state_definitions_reviewed: bool
    physical_state_truth_reviewed: bool
    observation_labels_reviewed: bool
    action_assignments_reviewed: bool
    calibration_holdout_partition_reviewed: bool
    smoothing_basis_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_calibration(self):
        state_ids = [row.state_id for row in self.states]
        observation_ids = [row.observation_id for row in self.observation_labels]
        action_ids = [row.action_id for row in self.actions]
        if len(set(state_ids)) != len(state_ids):
            raise ValueError("policy calibration state IDs must be unique")
        if len(set(observation_ids)) != len(observation_ids):
            raise ValueError("policy calibration observation IDs must be unique")
        if len(set(action_ids)) != len(action_ids):
            raise ValueError("policy calibration action IDs must be unique")
        nonfailure_ids = {row.state_id for row in self.states if not row.is_failure_state}
        if not nonfailure_ids or not ({*state_ids} - nonfailure_ids):
            raise ValueError("policy calibration requires failure and nonfailure states")
        observation_record_ids = [row.record_id for row in self.observation_records]
        transition_record_ids = [row.record_id for row in self.transition_records]
        if len(set(observation_record_ids)) != len(observation_record_ids):
            raise ValueError("policy observation calibration record IDs must be unique")
        if len(set(transition_record_ids)) != len(transition_record_ids):
            raise ValueError("policy transition calibration record IDs must be unique")
        if set(observation_record_ids) & set(transition_record_ids):
            raise ValueError("observation and transition record IDs must not overlap")
        if any(row.true_state_id not in nonfailure_ids for row in self.observation_records):
            raise ValueError("observation truth must reference a nonfailure policy state")
        if any(row.observed_label_id not in observation_ids for row in self.observation_records):
            raise ValueError("observation record references an unknown observation label")
        if any(
            row.from_state_id not in nonfailure_ids or row.to_state_id not in state_ids
            for row in self.transition_records
        ):
            raise ValueError("transition record references an unknown state or starts from failure")
        if any(row.action_id not in action_ids for row in self.transition_records):
            raise ValueError("transition record references an unknown action")
        all_records = [*self.observation_records, *self.transition_records]
        for identity in ("sequence_id", "source_group_id"):
            calibration_ids = {
                getattr(row, identity) for row in all_records if row.partition == "calibration"
            }
            holdout_ids = {getattr(row, identity) for row in all_records if row.partition == "holdout"}
            if calibration_ids & holdout_ids:
                raise ValueError(f"{identity} cannot cross calibration and holdout partitions")
        for records, label in (
            (self.observation_records, "observation"),
            (self.transition_records, "transition"),
        ):
            if not any(row.partition == "calibration" for row in records) or not any(
                row.partition == "holdout" for row in records
            ):
                raise ValueError(f"{label} records require calibration and holdout partitions")
        return self


def finite_policy_probability_calibration(x: FinitePolicyProbabilityCalibration) -> Calculation:
    gates = {
        "state_definitions_reviewed": x.state_definitions_reviewed,
        "physical_state_truth_reviewed": x.physical_state_truth_reviewed,
        "observation_labels_reviewed": x.observation_labels_reviewed,
        "action_assignments_reviewed": x.action_assignments_reviewed,
        "calibration_holdout_partition_reviewed": x.calibration_holdout_partition_reviewed,
        "smoothing_basis_reviewed": x.smoothing_basis_reviewed,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "calibration_id": x.calibration_id,
        "calibration_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "symmetric_pseudocount": x.symmetric_pseudocount,
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "calibration_state": "review_required"},
            notes=("Every label, truth, action, partition and smoothing review is required.",),
        )

    nonfailure_ids = [row.state_id for row in x.states if not row.is_failure_state]
    state_ids = [row.state_id for row in x.states]
    observation_ids = [row.observation_id for row in x.observation_labels]
    action_ids = [row.action_id for row in x.actions]

    def weighted_count(records, predicate) -> float:
        return sum(row.weight for row in records if predicate(row))

    observation_fit = [row for row in x.observation_records if row.partition == "calibration"]
    observation_holdout = [row for row in x.observation_records if row.partition == "holdout"]
    transition_fit = [row for row in x.transition_records if row.partition == "calibration"]
    transition_holdout = [row for row in x.transition_records if row.partition == "holdout"]
    unsupported_observation_states = []
    observation_table = []
    for state_id in nonfailure_ids:
        denominator = weighted_count(
            observation_fit, lambda row, state_id=state_id: row.true_state_id == state_id
        )
        denominator += x.symmetric_pseudocount * len(observation_ids)
        if denominator == 0:
            unsupported_observation_states.append(state_id)
            continue
        for observation_id in observation_ids:
            numerator = (
                weighted_count(
                    observation_fit,
                    lambda row, state_id=state_id, observation_id=observation_id: (
                        row.true_state_id == state_id and row.observed_label_id == observation_id
                    ),
                )
                + x.symmetric_pseudocount
            )
            observation_table.append(
                {
                    "state_id": state_id,
                    "observation_id": observation_id,
                    "probability_given_state": numerator / denominator,
                    "weighted_calibration_count": numerator - x.symmetric_pseudocount,
                }
            )

    unsupported_transition_pairs = []
    transition_table = []
    for state_id in nonfailure_ids:
        for action_id in action_ids:
            denominator = weighted_count(
                transition_fit,
                lambda row, state_id=state_id, action_id=action_id: (
                    row.from_state_id == state_id and row.action_id == action_id
                ),
            )
            denominator += x.symmetric_pseudocount * len(state_ids)
            if denominator == 0:
                unsupported_transition_pairs.append({"from_state_id": state_id, "action_id": action_id})
                continue
            for to_state_id in state_ids:
                numerator = (
                    weighted_count(
                        transition_fit,
                        lambda row, state_id=state_id, action_id=action_id, to_state_id=to_state_id: (
                            row.from_state_id == state_id
                            and row.action_id == action_id
                            and row.to_state_id == to_state_id
                        ),
                    )
                    + x.symmetric_pseudocount
                )
                transition_table.append(
                    {
                        "from_state_id": state_id,
                        "action_id": action_id,
                        "to_state_id": to_state_id,
                        "probability_given_state_and_action": numerator / denominator,
                        "weighted_calibration_count": numerator - x.symmetric_pseudocount,
                    }
                )

    if unsupported_observation_states or unsupported_transition_pairs:
        return Calculation(
            status="needs_data",
            values={
                **common,
                "calibration_state": "unsupported_conditioning_rows",
                "unsupported_observation_state_ids": unsupported_observation_states,
                "unsupported_transition_state_action_pairs": unsupported_transition_pairs,
            },
            notes=(
                "At least one conditioning row has no calibration support and no positive caller-approved pseudocount.",
            ),
        )

    observation_probability = {
        (row["state_id"], row["observation_id"]): row["probability_given_state"] for row in observation_table
    }
    transition_probability = {
        (row["from_state_id"], row["action_id"], row["to_state_id"]): row[
            "probability_given_state_and_action"
        ]
        for row in transition_table
    }

    def holdout_metrics(records, probability_for_row, outcome_ids):
        total_weight = sum(row.weight for row in records)
        zero_probability = []
        log_sum = 0.0
        brier_sum = 0.0
        for row in records:
            probability = probability_for_row(row)
            if probability == 0:
                zero_probability.append(row.record_id)
            else:
                log_sum -= row.weight * math.log(probability)
            brier_sum += row.weight * sum(
                (probability_for_row(row, outcome_id) - float(outcome_id == outcome_ids(row))) ** 2
                for outcome_id in (
                    observation_ids if isinstance(row, PolicyObservationCalibrationRecord) else state_ids
                )
            )
        return {
            "record_count": len(records),
            "total_weight": total_weight,
            "mean_negative_log_likelihood": None if zero_probability else log_sum / total_weight,
            "multiclass_brier_score": brier_sum / total_weight,
            "zero_probability_record_ids": zero_probability,
        }

    def observation_probability_for(row, outcome_id=None):
        label = row.observed_label_id if outcome_id is None else outcome_id
        return observation_probability[(row.true_state_id, label)]

    def transition_probability_for(row, outcome_id=None):
        state = row.to_state_id if outcome_id is None else outcome_id
        return transition_probability[(row.from_state_id, row.action_id, state)]

    observation_metrics = holdout_metrics(
        observation_holdout,
        observation_probability_for,
        lambda row: row.observed_label_id,
    )
    transition_metrics = holdout_metrics(
        transition_holdout,
        transition_probability_for,
        lambda row: row.to_state_id,
    )
    all_records = [*x.observation_records, *x.transition_records]
    return Calculation(
        values={
            **common,
            "calibration_state": "computed",
            "observation_probabilities": observation_table,
            "transition_probabilities": transition_table,
            "observation_holdout_metrics": observation_metrics,
            "transition_holdout_metrics": transition_metrics,
            "calibration_sequence_count": len(
                {row.sequence_id for row in all_records if row.partition == "calibration"}
            ),
            "holdout_sequence_count": len(
                {row.sequence_id for row in all_records if row.partition == "holdout"}
            ),
            "calibration_source_group_count": len(
                {row.source_group_id for row in all_records if row.partition == "calibration"}
            ),
            "holdout_source_group_count": len(
                {row.source_group_id for row in all_records if row.partition == "holdout"}
            ),
            "confidence_intervals_computed": False,
            "record_independence_inferred": False,
        },
        notes=(
            "Probabilities are weighted empirical frequencies with only the declared symmetric pseudocount; no record independence or confidence interval is inferred.",
            "A null holdout log loss means at least one observed holdout outcome received exactly zero probability; values are not clipped.",
        ),
    )


class InitialPolicyStateProbability(Contract):
    state_id: str = Field(min_length=1)
    probability_given_start_survival: Fraction


class FinitePolicyObservationProbability(Contract):
    state_id: str = Field(min_length=1)
    observation_id: str = Field(min_length=1)
    probability_given_state: Fraction


class FinitePolicyDecisionRule(Contract):
    observation_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)


class FinitePolicyAction(Contract):
    action_id: str = Field(min_length=1)
    action_definition: str = Field(min_length=1)
    action_model_id: str = Field(min_length=1)
    action_model_revision: str = Field(min_length=1)
    action_model_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    action_model_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cost_components: list[PolicyStageCostComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_cost_ids(self):
        ids = [row.component_id for row in self.cost_components]
        if len(set(ids)) != len(ids):
            raise ValueError("finite-policy action cost component IDs must be unique")
        return self


class FinitePolicyTransitionProbability(Contract):
    from_state_id: str = Field(min_length=1)
    action_id: str = Field(min_length=1)
    to_state_id: str = Field(min_length=1)
    probability_given_state_and_action: Fraction
    failure_consequence_present_value_factor: Nonnegative | None = None


class FinitePolicyDecisionEpoch(Contract):
    stage_id: str = Field(min_length=1)
    stage_time_s: Nonnegative
    observation_probabilities: list[FinitePolicyObservationProbability] = Field(min_length=1)
    decision_rules: list[FinitePolicyDecisionRule] = Field(min_length=1)
    actions: list[FinitePolicyAction] = Field(min_length=1)
    transition_probabilities: list[FinitePolicyTransitionProbability] = Field(min_length=1)


class FiniteInspectionPolicyPathGeneration(Contract):
    """Expand reviewed finite state, observation, decision and transition tables exactly."""

    schema_version: Literal["matintegrity.finite_inspection_policy_path_generation.v1"] = (
        "matintegrity.finite_inspection_policy_path_generation.v1"
    )
    generation_id: str = Field(min_length=1)
    generator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    policy_id: str = Field(min_length=1)
    policy_revision: str = Field(min_length=1)
    policy_definition: str = Field(min_length=1)
    policy_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    cost_basis_id: str = Field(min_length=1)
    currency_or_normalized_unit: str = Field(min_length=1)
    discount_basis_id: str = Field(min_length=1)
    states: list[FinitePolicyState] = Field(min_length=2)
    initial_state_probabilities: list[InitialPolicyStateProbability] = Field(min_length=1)
    decision_epochs: list[FinitePolicyDecisionEpoch] = Field(min_length=1)
    maximum_probability_sum_error: Positive = 1e-12
    maximum_generated_paths: int = Field(ge=1)
    state_space_reviewed: bool
    initial_distribution_reviewed: bool
    observation_models_reviewed: bool
    decision_rules_reviewed: bool
    transition_models_reviewed: bool
    action_costs_and_discount_factors_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_generator(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("finite-policy generation horizon must have positive duration")
        state_ids = [state.state_id for state in self.states]
        if len(set(state_ids)) != len(state_ids):
            raise ValueError("finite-policy state IDs must be unique")
        state_by_id = {state.state_id: state for state in self.states}
        nonfailure_ids = {state.state_id for state in self.states if not state.is_failure_state}
        failure_ids = {state.state_id for state in self.states if state.is_failure_state}
        if not nonfailure_ids or not failure_ids:
            raise ValueError("finite-policy state space requires failure and nonfailure states")
        initial_ids = [row.state_id for row in self.initial_state_probabilities]
        if len(set(initial_ids)) != len(initial_ids):
            raise ValueError("initial policy state IDs must be unique")
        if set(initial_ids) != nonfailure_ids:
            raise ValueError("initial policy distribution must cover every nonfailure state exactly")
        if (
            abs(sum(row.probability_given_start_survival for row in self.initial_state_probabilities) - 1.0)
            > self.maximum_probability_sum_error
        ):
            raise ValueError("initial policy state probabilities must sum to one")
        epoch_ids = [epoch.stage_id for epoch in self.decision_epochs]
        if len(set(epoch_ids)) != len(epoch_ids):
            raise ValueError("finite-policy decision epoch IDs must be unique")
        epoch_times = [epoch.stage_time_s for epoch in self.decision_epochs]
        if any(time <= self.horizon_start_s or time > self.horizon_end_s for time in epoch_times):
            raise ValueError("every finite-policy epoch must lie after start and within the horizon")
        if any(right <= left for left, right in zip(epoch_times, epoch_times[1:], strict=False)):
            raise ValueError("finite-policy decision epoch times must strictly increase")
        for epoch in self.decision_epochs:
            observation_keys = [(row.state_id, row.observation_id) for row in epoch.observation_probabilities]
            if len(set(observation_keys)) != len(observation_keys):
                raise ValueError("finite-policy observation rows must be unique")
            if {row.state_id for row in epoch.observation_probabilities} != nonfailure_ids:
                raise ValueError("each epoch observation model must cover every nonfailure state")
            if any(row.state_id not in state_by_id for row in epoch.observation_probabilities):
                raise ValueError("finite-policy observation state is unknown")
            for state_id in nonfailure_ids:
                probability_sum = sum(
                    row.probability_given_state
                    for row in epoch.observation_probabilities
                    if row.state_id == state_id
                )
                if abs(probability_sum - 1.0) > self.maximum_probability_sum_error:
                    raise ValueError("finite-policy observation probabilities must sum to one")
            observation_ids = {row.observation_id for row in epoch.observation_probabilities}
            decision_ids = [row.observation_id for row in epoch.decision_rules]
            if len(set(decision_ids)) != len(decision_ids) or set(decision_ids) != observation_ids:
                raise ValueError("finite-policy decision rules must cover every observation exactly")
            action_ids = [row.action_id for row in epoch.actions]
            if len(set(action_ids)) != len(action_ids):
                raise ValueError("finite-policy action IDs must be unique within each epoch")
            if set(action_ids) != {row.action_id for row in epoch.decision_rules}:
                raise ValueError("finite-policy actions must cover the decision-rule action set exactly")
            decision_by_observation = {row.observation_id: row.action_id for row in epoch.decision_rules}
            reachable_pairs = {
                (row.state_id, decision_by_observation[row.observation_id])
                for row in epoch.observation_probabilities
                if row.probability_given_state > 0
            }
            transition_keys = [
                (row.from_state_id, row.action_id, row.to_state_id) for row in epoch.transition_probabilities
            ]
            if len(set(transition_keys)) != len(transition_keys):
                raise ValueError("finite-policy transition rows must be unique")
            transition_pairs = {(row.from_state_id, row.action_id) for row in epoch.transition_probabilities}
            if transition_pairs != reachable_pairs:
                raise ValueError("finite-policy transitions must cover every reachable state-action pair")
            for row in epoch.transition_probabilities:
                if row.from_state_id not in nonfailure_ids or row.to_state_id not in state_by_id:
                    raise ValueError("finite-policy transition state is unknown or starts from failure")
                is_failure = state_by_id[row.to_state_id].is_failure_state
                if is_failure != (row.failure_consequence_present_value_factor is not None):
                    raise ValueError(
                        "failure consequence factor is required exactly on transitions to failure"
                    )
            for state_action in reachable_pairs:
                probability_sum = sum(
                    row.probability_given_state_and_action
                    for row in epoch.transition_probabilities
                    if (row.from_state_id, row.action_id) == state_action
                )
                if abs(probability_sum - 1.0) > self.maximum_probability_sum_error:
                    raise ValueError("finite-policy transition probabilities must sum to one")
        return self


def finite_inspection_policy_path_generation(
    x: FiniteInspectionPolicyPathGeneration,
) -> Calculation:
    gates = {
        "state_space_reviewed": x.state_space_reviewed,
        "initial_distribution_reviewed": x.initial_distribution_reviewed,
        "observation_models_reviewed": x.observation_models_reviewed,
        "decision_rules_reviewed": x.decision_rules_reviewed,
        "transition_models_reviewed": x.transition_models_reviewed,
        "action_costs_and_discount_factors_reviewed": (x.action_costs_and_discount_factors_reviewed),
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "generation_id": x.generation_id,
        "policy_id": x.policy_id,
        "policy_revision": x.policy_revision,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "event_id": x.event_id,
        "horizon_start_s": x.horizon_start_s,
        "horizon_end_s": x.horizon_end_s,
        "conditioning": x.conditioning,
        "cost_basis_id": x.cost_basis_id,
        "currency_or_normalized_unit": x.currency_or_normalized_unit,
        "discount_basis_id": x.discount_basis_id,
        "generation_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "path_generation_state": "review_required"},
            notes=(
                "Every state, distribution, observation, decision, transition and cost review is required.",
            ),
        )
    state_by_id = {state.state_id: state for state in x.states}
    traces = [
        {
            "probability": row.probability_given_start_survival,
            "state_id": row.state_id,
            "stages": [],
            "trace_tokens": [f"initial:{row.state_id}"],
            "first_failure_time_s": None,
            "failure_factor": None,
        }
        for row in x.initial_state_probabilities
        if row.probability_given_start_survival > 0
    ]
    for epoch in x.decision_epochs:
        observations_by_state: dict[str, list[FinitePolicyObservationProbability]] = {}
        for row in epoch.observation_probabilities:
            observations_by_state.setdefault(row.state_id, []).append(row)
        decision_by_observation = {row.observation_id: row.action_id for row in epoch.decision_rules}
        action_by_id = {row.action_id: row for row in epoch.actions}
        transitions_by_pair: dict[tuple[str, str], list[FinitePolicyTransitionProbability]] = {}
        for row in epoch.transition_probabilities:
            transitions_by_pair.setdefault((row.from_state_id, row.action_id), []).append(row)
        expanded = []
        for trace in traces:
            if trace["first_failure_time_s"] is not None:
                expanded.append(trace)
                continue
            state_id = trace["state_id"]
            for observation in observations_by_state[state_id]:
                if observation.probability_given_state == 0:
                    continue
                action_id = decision_by_observation[observation.observation_id]
                action = action_by_id[action_id]
                for transition in transitions_by_pair[(state_id, action_id)]:
                    if transition.probability_given_state_and_action == 0:
                        continue
                    probability = (
                        trace["probability"]
                        * observation.probability_given_state
                        * transition.probability_given_state_and_action
                    )
                    next_is_failure = state_by_id[transition.to_state_id].is_failure_state
                    expanded.append(
                        {
                            "probability": probability,
                            "state_id": transition.to_state_id,
                            "stages": [
                                *trace["stages"],
                                {
                                    "stage_id": epoch.stage_id,
                                    "stage_time_s": epoch.stage_time_s,
                                    "observed_state_id": observation.observation_id,
                                    "action_id": action.action_id,
                                    "action_definition": action.action_definition,
                                    "action_model_id": action.action_model_id,
                                    "action_model_revision": action.action_model_revision,
                                    "action_model_configuration_sha256": (
                                        action.action_model_configuration_sha256
                                    ),
                                    "action_model_input_sha256": action.action_model_input_sha256,
                                    "cost_components": [
                                        row.model_dump(mode="json") for row in action.cost_components
                                    ],
                                },
                            ],
                            "trace_tokens": [
                                *trace["trace_tokens"],
                                (
                                    f"{epoch.stage_id}:{state_id}:{observation.observation_id}:"
                                    f"{action_id}:{transition.to_state_id}"
                                ),
                            ],
                            "first_failure_time_s": (epoch.stage_time_s if next_is_failure else None),
                            "failure_factor": (
                                transition.failure_consequence_present_value_factor
                                if next_is_failure
                                else None
                            ),
                        }
                    )
        traces = expanded
        if len(traces) > x.maximum_generated_paths:
            return Calculation(
                status="out_of_scope",
                values={
                    **common,
                    "path_generation_state": "path_limit_exceeded",
                    "decision_epoch_id": epoch.stage_id,
                    "generated_paths_at_stop": len(traces),
                    "maximum_generated_paths": x.maximum_generated_paths,
                },
                notes=(
                    "The exact positive-probability path expansion exceeded the declared resource limit.",
                ),
            )
    paths = []
    generation_digest = common["generation_input_sha256"]
    for index, trace in enumerate(traces):
        path = InspectionPolicyPath.model_validate(
            {
                "path_id": f"generated-path-{index:06d}",
                "path_probability_given_start_survival": trace["probability"],
                "path_source_sha256": canonical_digest(
                    {"generation_input_sha256": generation_digest, "trace": trace["trace_tokens"]}
                ),
                "stages": trace["stages"],
                "first_failure_occurred": trace["first_failure_time_s"] is not None,
                "first_failure_time_s": trace["first_failure_time_s"],
                "failure_consequence_present_value_factor": trace["failure_factor"],
            }
        )
        paths.append(path.model_dump(mode="json"))
    probability_sum = sum(path["path_probability_given_start_survival"] for path in paths)
    if abs(probability_sum - 1.0) > x.maximum_probability_sum_error:
        raise RuntimeError("generated finite-policy path probabilities do not preserve total mass")
    return Calculation(
        values={
            **common,
            "path_generation_state": "computed",
            "generated_path_count": len(paths),
            "path_probability_sum": probability_sum,
            "path_manifest_sha256": canonical_digest(paths),
            "paths": paths,
            "zero_probability_branches_omitted": True,
            "observation_transition_or_policy_inferred": False,
            "policy_optimization_performed": False,
        },
        notes=(
            "Every positive-probability path is an exact product of caller-reviewed initial, observation and transition table entries under the supplied decision rule.",
            "Zero-probability branches are omitted; no probabilities, states, actions, costs, bounds or policy choices are inferred.",
        ),
    )


def _finite_inspection_policy_path_generation_context(
    x: FiniteInspectionPolicyPathGeneration, context: RunContext
) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("finite-policy path generation asset and location must match the run context")


class MultiPeriodInspectionPolicyEvaluation(Contract):
    """Evaluate one externally generated complete finite policy-path ensemble."""

    schema_version: Literal["matintegrity.multi_period_inspection_policy.v1"] = (
        "matintegrity.multi_period_inspection_policy.v1"
    )
    evaluation_id: str = Field(min_length=1)
    policy_id: str = Field(min_length=1)
    policy_revision: str = Field(min_length=1)
    policy_definition: str = Field(min_length=1)
    policy_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    path_generator_id: str = Field(min_length=1)
    path_generator_revision: str = Field(min_length=1)
    path_generator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    path_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    event_definition: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    cost_basis_id: str = Field(min_length=1)
    currency_or_normalized_unit: str = Field(min_length=1)
    discount_basis_id: str = Field(min_length=1)
    failure_consequence_components: list[RiskCostComponent] = Field(min_length=1)
    paths: list[InspectionPolicyPath] = Field(min_length=1)
    maximum_path_probability_sum_error: Positive = 1e-12
    complete_path_manifest_reviewed: bool
    path_probabilities_reviewed: bool
    policy_actions_reviewed: bool
    first_failure_events_reviewed: bool
    costs_and_discount_factors_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_policy(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("policy horizon must have positive duration")
        path_ids = [path.path_id for path in self.paths]
        if len(set(path_ids)) != len(path_ids):
            raise ValueError("policy path IDs must be unique")
        consequence_ids = [component.component_id for component in self.failure_consequence_components]
        if len(set(consequence_ids)) != len(consequence_ids):
            raise ValueError("failure consequence component IDs must be unique")
        probability_sum = sum(path.path_probability_given_start_survival for path in self.paths)
        if abs(probability_sum - 1.0) > self.maximum_path_probability_sum_error:
            raise ValueError("policy path probabilities must sum to one within tolerance")
        for path in self.paths:
            if any(
                stage.stage_time_s < self.horizon_start_s or stage.stage_time_s > self.horizon_end_s
                for stage in path.stages
            ):
                raise ValueError("every policy stage time must lie inside the policy horizon")
            if path.first_failure_time_s is not None and not (
                self.horizon_start_s < path.first_failure_time_s <= self.horizon_end_s
            ):
                raise ValueError("every first-failure time must lie after start and within the horizon")
            if path.first_failure_time_s is not None and any(
                stage.stage_time_s > path.first_failure_time_s for stage in path.stages
            ):
                raise ValueError("a policy path cannot contain stages after its first failure")
        return self


def multi_period_inspection_policy(x: MultiPeriodInspectionPolicyEvaluation) -> Calculation:
    gates = {
        "complete_path_manifest_reviewed": x.complete_path_manifest_reviewed,
        "path_probabilities_reviewed": x.path_probabilities_reviewed,
        "policy_actions_reviewed": x.policy_actions_reviewed,
        "first_failure_events_reviewed": x.first_failure_events_reviewed,
        "costs_and_discount_factors_reviewed": x.costs_and_discount_factors_reviewed,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "evaluation_id": x.evaluation_id,
        "policy_id": x.policy_id,
        "policy_revision": x.policy_revision,
        "path_manifest_sha256": x.path_manifest_sha256,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "event_id": x.event_id,
        "horizon_start_s": x.horizon_start_s,
        "horizon_end_s": x.horizon_end_s,
        "conditioning": x.conditioning,
        "cost_basis_id": x.cost_basis_id,
        "currency_or_normalized_unit": x.currency_or_normalized_unit,
        "discount_basis_id": x.discount_basis_id,
        "evaluation_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "policy_evaluation_state": "review_required"},
            notes=("Every path, probability, action, failure event, cost and discount review is required.",),
        )
    consequence_cost = sum(component.amount for component in x.failure_consequence_components)
    expected_action_cost = 0.0
    expected_failure_consequence = 0.0
    first_failure_probability = 0.0
    path_results = []
    for path in x.paths:
        discounted_action_cost = sum(
            component.amount_at_stage_time * component.present_value_factor
            for stage in path.stages
            for component in stage.cost_components
        )
        discounted_failure_consequence = 0.0
        if path.first_failure_occurred:
            assert path.failure_consequence_present_value_factor is not None
            discounted_failure_consequence = consequence_cost * path.failure_consequence_present_value_factor
            first_failure_probability += path.path_probability_given_start_survival
        action_contribution = path.path_probability_given_start_survival * discounted_action_cost
        failure_contribution = path.path_probability_given_start_survival * discounted_failure_consequence
        expected_action_cost += action_contribution
        expected_failure_consequence += failure_contribution
        path_results.append(
            {
                "path_id": path.path_id,
                "path_probability_given_start_survival": (path.path_probability_given_start_survival),
                "path_source_sha256": path.path_source_sha256,
                "first_failure_occurred": path.first_failure_occurred,
                "first_failure_time_s": path.first_failure_time_s,
                "failure_consequence_present_value_factor": (path.failure_consequence_present_value_factor),
                "discounted_action_cost_if_path": discounted_action_cost,
                "discounted_failure_consequence_if_path": discounted_failure_consequence,
                "expected_action_cost_contribution": action_contribution,
                "expected_failure_consequence_contribution": failure_contribution,
                "stage_count": len(path.stages),
                "stage_ids": [stage.stage_id for stage in path.stages],
            }
        )
    return Calculation(
        values={
            **common,
            "policy_evaluation_state": "computed",
            "path_probability_sum": sum(path.path_probability_given_start_survival for path in x.paths),
            "conditional_first_failure_probability": first_failure_probability,
            "failure_consequence_cost_at_undiscounted_basis": consequence_cost,
            "expected_discounted_action_cost": expected_action_cost,
            "expected_discounted_failure_consequence": expected_failure_consequence,
            "expected_discounted_total_loss": (expected_action_cost + expected_failure_consequence),
            "path_results": path_results,
            "path_probabilities_or_policy_inferred": False,
            "policy_optimization_performed": False,
            "upper_bound_computed": False,
        },
        notes=(
            "This is a finite expectation over the complete caller-supplied policy-path manifest, not a policy search or optimization.",
            "Path probabilities, failure events, costs and present-value factors are preserved inputs; no transition, discount, upper bound or acceptance rule is inferred.",
        ),
    )


def _multi_period_inspection_policy_context(
    x: MultiPeriodInspectionPolicyEvaluation, context: RunContext
) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("multi-period inspection policy asset and location must match the run context")


class PolicyResourceUsage(Contract):
    resource_id: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    expected_usage: Nonnegative
    upper_bound_usage: Nonnegative | None = None

    @model_validator(mode="after")
    def ordered_bound(self):
        if self.upper_bound_usage is not None and self.upper_bound_usage < self.expected_usage:
            raise ValueError("policy resource upper bound cannot be below expected usage")
        return self


class MultiPeriodInspectionPolicyCandidate(Contract):
    policy_id: str = Field(min_length=1)
    policy_revision: str = Field(min_length=1)
    policy_definition: str = Field(min_length=1)
    policy_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluation_model_id: str = Field(min_length=1)
    evaluation_model_revision: str = Field(min_length=1)
    evaluation_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluation_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluation_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    cost_basis_id: str = Field(min_length=1)
    currency_or_normalized_unit: str = Field(min_length=1)
    discount_basis_id: str = Field(min_length=1)
    conditional_first_failure_probability: Fraction
    conditional_first_failure_probability_upper_bound: Fraction | None = None
    expected_discounted_action_cost: Nonnegative
    expected_discounted_failure_consequence: Nonnegative
    expected_discounted_total_loss: Nonnegative
    resource_usage: list[PolicyResourceUsage] = Field(default_factory=list)

    @model_validator(mode="after")
    def aligned_candidate(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("policy-comparison candidate horizon must have positive duration")
        if (
            self.conditional_first_failure_probability_upper_bound is not None
            and self.conditional_first_failure_probability_upper_bound
            < self.conditional_first_failure_probability
        ):
            raise ValueError("policy probability upper bound cannot be below its estimate")
        expected_total = self.expected_discounted_action_cost + self.expected_discounted_failure_consequence
        if not math.isclose(
            self.expected_discounted_total_loss,
            expected_total,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("policy expected total loss must equal action and failure components")
        resource_ids = [row.resource_id for row in self.resource_usage]
        if len(set(resource_ids)) != len(resource_ids):
            raise ValueError("policy resource IDs must be unique within each candidate")
        return self


class PolicyResourceConstraint(Contract):
    resource_id: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    comparison_basis: Literal["expected", "upper_bound"]
    maximum_usage: Nonnegative
    criterion_basis: str = Field(min_length=1)


class MultiPeriodInspectionPolicyComparison(Contract):
    """Compare complete external policy evaluations under reviewed hard constraints."""

    schema_version: Literal["matintegrity.multi_period_inspection_policy_comparison.v1"] = (
        "matintegrity.multi_period_inspection_policy_comparison.v1"
    )
    comparison_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    conditioning: str = Field(min_length=1)
    event_probability_meaning: Literal["conditional_first_failure_in_period"]
    cost_basis_id: str = Field(min_length=1)
    currency_or_normalized_unit: str = Field(min_length=1)
    discount_basis_id: str = Field(min_length=1)
    probability_basis: Literal["estimate", "upper_bound"]
    maximum_conditional_first_failure_probability: Fraction
    resource_constraints: list[PolicyResourceConstraint] = Field(default_factory=list)
    candidates: list[MultiPeriodInspectionPolicyCandidate] = Field(min_length=2)
    cost_tie_absolute_tolerance: Nonnegative = 0.0
    complete_policy_set_reviewed: bool
    policy_evaluations_reviewed: bool
    probability_criterion_user_approved: bool
    resource_constraints_user_approved: bool
    cost_comparison_user_approved: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_comparison(self):
        if self.horizon_end_s <= self.horizon_start_s:
            raise ValueError("policy-comparison horizon must have positive duration")
        policy_ids = [candidate.policy_id for candidate in self.candidates]
        if len(set(policy_ids)) != len(policy_ids):
            raise ValueError("policy comparison candidate IDs must be unique")
        constraint_ids = [constraint.resource_id for constraint in self.resource_constraints]
        if len(set(constraint_ids)) != len(constraint_ids):
            raise ValueError("policy resource constraint IDs must be unique")
        common_fields = (
            "asset_id",
            "location_id",
            "physical_scope_id",
            "event_id",
            "horizon_start_s",
            "horizon_end_s",
            "conditioning",
            "event_probability_meaning",
            "cost_basis_id",
            "currency_or_normalized_unit",
            "discount_basis_id",
        )
        for candidate in self.candidates:
            mismatched = [
                field for field in common_fields if getattr(candidate, field) != getattr(self, field)
            ]
            if mismatched:
                raise ValueError(
                    f"policy candidates must share the comparison context; policy={candidate.policy_id}, fields={mismatched}"
                )
            if (
                self.probability_basis == "upper_bound"
                and candidate.conditional_first_failure_probability_upper_bound is None
            ):
                raise ValueError("upper-bound policy comparison requires a bound for every candidate")
            usage_by_id = {row.resource_id: row for row in candidate.resource_usage}
            if set(usage_by_id) != set(constraint_ids):
                raise ValueError("every policy candidate must cover the exact resource constraint set")
            for constraint in self.resource_constraints:
                usage = usage_by_id[constraint.resource_id]
                if usage.unit != constraint.unit:
                    raise ValueError("policy resource units must match their constraints")
                if constraint.comparison_basis == "upper_bound" and usage.upper_bound_usage is None:
                    raise ValueError("upper-bound resource constraints require a bound for every candidate")
        return self


def multi_period_inspection_policy_comparison(
    x: MultiPeriodInspectionPolicyComparison,
) -> Calculation:
    gates = {
        "complete_policy_set_reviewed": x.complete_policy_set_reviewed,
        "policy_evaluations_reviewed": x.policy_evaluations_reviewed,
        "probability_criterion_user_approved": x.probability_criterion_user_approved,
        "resource_constraints_user_approved": x.resource_constraints_user_approved,
        "cost_comparison_user_approved": x.cost_comparison_user_approved,
    }
    missing_gates = [name for name, reviewed in gates.items() if not reviewed]
    common = {
        "comparison_id": x.comparison_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "event_id": x.event_id,
        "horizon_start_s": x.horizon_start_s,
        "horizon_end_s": x.horizon_end_s,
        "conditioning": x.conditioning,
        "probability_basis": x.probability_basis,
        "maximum_conditional_first_failure_probability": (x.maximum_conditional_first_failure_probability),
        "cost_basis_id": x.cost_basis_id,
        "currency_or_normalized_unit": x.currency_or_normalized_unit,
        "discount_basis_id": x.discount_basis_id,
        "comparison_input_sha256": canonical_digest(x.model_dump(mode="json")),
        "missing_review_gates": missing_gates,
    }
    if missing_gates:
        return Calculation(
            status="needs_data",
            values={**common, "comparison_state": "review_required"},
            notes=("Every policy-set, evaluation, probability, resource and cost review is required.",),
        )
    rows = []
    for candidate in x.candidates:
        probability = (
            candidate.conditional_first_failure_probability
            if x.probability_basis == "estimate"
            else candidate.conditional_first_failure_probability_upper_bound
        )
        assert probability is not None
        violated = []
        if probability > x.maximum_conditional_first_failure_probability:
            violated.append("conditional_first_failure_probability")
        usage_by_id = {row.resource_id: row for row in candidate.resource_usage}
        resource_results = []
        for constraint in x.resource_constraints:
            usage = usage_by_id[constraint.resource_id]
            used = (
                usage.expected_usage if constraint.comparison_basis == "expected" else usage.upper_bound_usage
            )
            assert used is not None
            compliant = used <= constraint.maximum_usage
            if not compliant:
                violated.append(f"resource:{constraint.resource_id}")
            resource_results.append(
                {
                    "resource_id": constraint.resource_id,
                    "unit": constraint.unit,
                    "comparison_basis": constraint.comparison_basis,
                    "usage_for_comparison": used,
                    "maximum_usage": constraint.maximum_usage,
                    "compliant": compliant,
                }
            )
        rows.append(
            {
                "policy_id": candidate.policy_id,
                "policy_revision": candidate.policy_revision,
                "evaluation_model_id": candidate.evaluation_model_id,
                "evaluation_model_revision": candidate.evaluation_model_revision,
                "evaluation_input_sha256": candidate.evaluation_input_sha256,
                "evaluation_result_sha256": candidate.evaluation_result_sha256,
                "conditional_first_failure_probability_for_comparison": probability,
                "expected_discounted_total_loss": candidate.expected_discounted_total_loss,
                "resource_results": resource_results,
                "violated_constraints": violated,
                "constraint_compliant": not violated,
            }
        )
    feasible = [row for row in rows if row["constraint_compliant"]]
    values = {**common, "candidate_results": rows, "feasible_policy_count": len(feasible)}
    if not feasible:
        return Calculation(
            status="out_of_scope",
            values={
                **values,
                "comparison_state": "no_constraint_compliant_policy",
                "selected_policy_id": None,
            },
            notes=(
                "No supplied policy satisfies every caller-approved hard constraint; no constraint is relaxed.",
                "This result does not prove infeasibility outside the complete caller-declared candidate set.",
            ),
        )
    minimum = min(row["expected_discounted_total_loss"] for row in feasible)
    tied = [
        row["policy_id"]
        for row in feasible
        if abs(row["expected_discounted_total_loss"] - minimum) <= x.cost_tie_absolute_tolerance
    ]
    selection = {
        **values,
        "minimum_constraint_compliant_expected_loss": minimum,
        "tied_minimum_policy_ids": tied,
        "selected_policy_id": tied[0] if len(tied) == 1 else None,
        "comparison_state": "unique_minimum" if len(tied) == 1 else "minimum_tie",
        "policy_search_or_generation_performed": False,
        "global_optimality_claimed": False,
        "constraints_inferred": False,
    }
    if len(tied) != 1:
        return Calculation(
            status="needs_data",
            values=selection,
            notes=("Constraint-compliant policies are tied within the declared cost tolerance.",),
        )
    return Calculation(
        values=selection,
        notes=(
            "The selected policy has the least expected loss among the supplied constraint-compliant candidates only.",
            "No policy, transition, probability, resource use, constraint, cost or global optimum is inferred.",
        ),
    )


def _multi_period_inspection_policy_comparison_context(
    x: MultiPeriodInspectionPolicyComparison, context: RunContext
) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("multi-period policy comparison asset and location must match the run context")


def guided_wave_reference_ensemble(x: GuidedWaveReferenceEnsemble) -> Calculation:
    distance = np.asarray(x.distance_m)
    observation_distance = np.asarray(x.observation_distance_m)
    baselines = np.asarray(x.baseline_voltage_V)
    observation = np.asarray(x.observation_voltage_V)
    selected = (distance >= x.window_start_m) & (distance <= x.window_end_m)
    selected_samples = int(np.count_nonzero(selected))
    if selected_samples < 2:
        return Calculation(
            status="needs_data",
            values={"selected_samples": selected_samples},
            notes=("At least two aligned samples are required inside the declared spatial window.",),
        )
    distance = distance[selected]
    baselines = baselines[:, selected]
    observation = observation[selected]
    observed_selected_distance = observation_distance[selected]
    repeated = int(np.count_nonzero(np.diff(distance) == 0))
    if repeated and x.duplicate_distance_policy == "reject":
        return Calculation(
            status="out_of_scope",
            values={"selected_samples": selected_samples, "repeated_distance_intervals": repeated},
            notes=("The selected ensemble window contains repeated provider distance samples.",),
        )
    raw_samples = len(distance)
    if x.duplicate_distance_policy == "mean_aligned_duplicates":
        distance, baselines, observation = _mean_duplicate_ensemble(distance, baselines, observation)
    statistic = np.mean if x.reference_statistic == "mean" else np.median
    reference = statistic(baselines, axis=0)
    observation_residual = observation - reference
    leave_one_out_rms = []
    for index in range(len(baselines)):
        leave_one_out_reference = statistic(np.delete(baselines, index, axis=0), axis=0)
        leave_one_out_rms.append(float(np.sqrt(np.mean((baselines[index] - leave_one_out_reference) ** 2))))
    reference_rms = float(np.sqrt(np.mean(reference**2)))
    observation_rms = float(np.sqrt(np.mean(observation**2)))
    observation_residual_rms = float(np.sqrt(np.mean(observation_residual**2)))
    baseline_spread_rms = float(np.sqrt(np.mean((baselines - reference) ** 2)))
    loo_median = float(np.median(leave_one_out_rms))
    loo_maximum = float(np.max(leave_one_out_rms))
    loo_q95 = float(np.quantile(leave_one_out_rms, 0.95, method="linear"))
    reference_centered = reference - np.mean(reference)
    observation_centered = observation - np.mean(observation)
    denominator = float(
        np.sqrt(
            np.dot(reference_centered, reference_centered)
            * np.dot(observation_centered, observation_centered)
        )
    )
    return Calculation(
        values={
            "specimen_id": x.specimen_id,
            "baseline_acquisition_ids": x.baseline_acquisition_ids,
            "observation_acquisition_id": x.observation_acquisition_id,
            "baseline_source_group_id": x.baseline_source_group_id,
            "observation_source_group_id": x.observation_source_group_id,
            "baseline_selection_basis": x.baseline_selection_basis,
            "frequency_Hz": x.frequency_Hz,
            "wave_mode": x.wave_mode,
            "window_start_m": x.window_start_m,
            "window_end_m": x.window_end_m,
            "reference_statistic": x.reference_statistic,
            "baseline_acquisition_count": len(baselines),
            "raw_selected_samples": raw_samples,
            "effective_selected_samples": len(distance),
            "repeated_distance_intervals": repeated,
            "duplicate_distance_policy": x.duplicate_distance_policy,
            "effective_distance_start_m": float(distance[0]),
            "effective_distance_end_m": float(distance[-1]),
            "observation_selected_distance_start_m": float(observed_selected_distance[0]),
            "observation_selected_distance_end_m": float(observed_selected_distance[-1]),
            "maximum_distance_grid_mismatch_m": float(
                np.max(np.abs(np.asarray(x.distance_m) - observation_distance))
            ),
            "reference_rms_V": reference_rms,
            "observation_rms_V": observation_rms,
            "observation_residual_rms_V": observation_residual_rms,
            "normalized_observation_residual_rms": None
            if reference_rms == 0
            else observation_residual_rms / reference_rms,
            "baseline_spread_rms_V": baseline_spread_rms,
            "observation_to_baseline_spread_ratio": None
            if baseline_spread_rms == 0
            else observation_residual_rms / baseline_spread_rms,
            "leave_one_out_residual_rms_V": leave_one_out_rms,
            "leave_one_out_residual_median_V": loo_median,
            "leave_one_out_residual_q95_V": loo_q95,
            "leave_one_out_residual_maximum_V": loo_maximum,
            "observation_to_leave_one_out_median_ratio": None
            if loo_median == 0
            else observation_residual_rms / loo_median,
            "observation_to_leave_one_out_maximum_ratio": None
            if loo_maximum == 0
            else observation_residual_rms / loo_maximum,
            "reference_observation_correlation": None
            if denominator == 0
            else float(np.dot(reference_centered, observation_centered) / denominator),
            "peak_absolute_difference_V": float(np.max(np.abs(observation_residual))),
            "signed_mean_difference_V": float(np.mean(observation_residual)),
        },
        notes=(
            "The reference ensemble describes selected acquisition variability; it is not an anomaly probability, POD curve or acceptance threshold.",
            "Repeated measurements from one specimen do not establish independent-specimen validation or separate acquisition conditions from damage.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.ultrasonic_thickness",
            UltrasonicThickness,
            ultrasonic_thickness,
            {"thickness_m": "m"},
            (
                "Single homogeneous sound path and declared refracted angle; coating and mode conversion excluded.",
            ),
            ("ultrasonic_time_of_flight",),
        ),
        ModelSpec(
            "inspection.pulse_echo_sound_speed_fit",
            PulseEchoSoundSpeedFit,
            pulse_echo_sound_speed_fit,
            {
                "temperature_K": "K",
                "sound_speed_m_s": "m/s",
                "sound_speed_standard_error_m_s": "m/s",
                "sound_speed_residual_scaled_standard_error_m_s": "m/s",
                "calibration_rmse_m": "m",
                "calibration_maximum_absolute_residual_m": "m",
                "holdout_rmse_m": "m",
                "holdout_maximum_absolute_residual_m": "m",
                "holdout_standardized_residual_rmse": "1",
                "calibration_reference_thickness_range_m": "m",
                "holdout_reference_thickness_range_m": "m",
            },
            (
                "Fixed reviewed time zero and incidence angle; through-origin least squares on independently measured reference thicknesses; conditional uncertainty excludes errors in predictors and fixed inputs.",
            ),
            ("pulse_echo_sound_speed_fit_derivation",),
        ),
        ModelSpec(
            "inspection.logistic_pod",
            DetectionCurve,
            detection_curve,
            {"probability_of_detection": "1"},
            ("User-calibrated log-size logistic curve; false calls and confidence bounds are separate.",),
            ("nde_pod",),
            probability_semantics={"probability_of_detection": "detection_given_flaw_and_procedure"},
        ),
        ModelSpec(
            "inspection.no_indication_update",
            NoIndicationUpdate,
            no_indication_update,
            {"posterior_weights": "1", "probability_of_no_indication": "1"},
            (
                "POD conditional on each prior bin; random independent coverage and no false indication mechanism.",
            ),
            ("bayes_rule",),
        ),
        ModelSpec(
            "inspection.threshold_inspection_schedule",
            ThresholdInspectionSchedule,
            threshold_inspection_schedule,
            {
                "assessment_time_s": "s",
                "maximum_probability_before_inspection": "1",
                "candidate_window_start_s": "s",
                "candidate_window_end_s": "s",
                "earliest_candidate_time_s": "s",
                "earliest_candidate_probability": "1",
                "selected_inspection_time_s": "s",
                "selected_time_from_assessment_s": "s",
                "selected_probability_given_survival": "1",
                "selected_probability_estimate": "1",
                "selected_probability_upper_bound": "1",
                "probability_margin_to_criterion": "1",
                "next_noncompliant_candidate_time_s": "s",
                "next_noncompliant_candidate_probability": "1",
                "forecast_support_end_s": "s",
            },
            (
                "Caller-reviewed cumulative first-crossing probabilities on strictly ordered candidate times; select the latest supplied candidate within notice and deferral limits that satisfies a user-approved probability criterion without interpolation or consequence optimization.",
            ),
            ("threshold_inspection_schedule_definition",),
            context_validator=_threshold_schedule_context,
            probability_semantics={
                "earliest_candidate_probability": "conditional_first_failure_in_period",
                "selected_probability_given_survival": "conditional_first_failure_in_period",
                "selected_probability_estimate": "conditional_first_failure_in_period",
                "selected_probability_upper_bound": "conditional_first_failure_in_period",
                "next_noncompliant_candidate_probability": "conditional_first_failure_in_period",
            },
        ),
        ModelSpec(
            "inspection.action_expected_loss",
            InspectionActionExpectedLossComparison,
            inspection_action_expected_loss,
            {
                "horizon_start_s": "s",
                "horizon_end_s": "s",
                "failure_consequence_cost": "declared_cost_unit",
                "baseline_total_expected_loss": "declared_cost_unit",
                "minimum_total_expected_loss": "declared_cost_unit",
                "cost_tie_absolute_tolerance": "declared_cost_unit",
            },
            (
                "One event, physical scope, horizon, survival conditioning and cost basis; every complete action retains an externally evaluated residual first-failure probability and reviewed additive costs; expectation is probability times conditional consequence plus action cost.",
            ),
            ("inspection_action_expected_loss_definition",),
            context_validator=_inspection_action_expected_loss_context,
        ),
        ModelSpec(
            "inspection.disposition_decision_tree",
            InspectionDispositionDecisionTree,
            inspection_disposition_tree,
            {
                "horizon_start_s": "s",
                "horizon_end_s": "s",
                "outcome_probability_sum": "1",
                "inspection_cost": "declared_cost_unit",
                "expected_disposition_cost": "declared_cost_unit",
                "expected_total_action_cost": "declared_cost_unit",
                "residual_failure_probability_estimate": "1",
            },
            (
                "One reviewed exhaustive mutually exclusive inspection-outcome partition over one event context; each branch supplies its probability, complete disposition, conditional residual first-failure probability and costs; finite expectations only.",
            ),
            ("inspection_disposition_tree_definition",),
            context_validator=_inspection_disposition_tree_context,
            probability_semantics={
                "residual_failure_probability_estimate": "conditional_first_failure_in_period"
            },
        ),
        ModelSpec(
            "inspection.finite_policy_probability_calibration",
            FinitePolicyProbabilityCalibration,
            finite_policy_probability_calibration,
            {
                "probability_given_state": "1",
                "probability_given_state_and_action": "1",
                "mean_negative_log_likelihood": "1",
                "multiclass_brier_score": "1",
            },
            (
                "Reviewed finite physical-state truth, inspection labels and action-conditioned longitudinal transitions with immutable, sequence- and source-group-disjoint calibration/holdout partitions; weighted empirical frequencies and an explicit symmetric pseudocount only.",
            ),
            ("finite_policy_probability_calibration_definition",),
        ),
        ModelSpec(
            "inspection.finite_policy_path_generation",
            FiniteInspectionPolicyPathGeneration,
            finite_inspection_policy_path_generation,
            {
                "horizon_start_s": "s",
                "horizon_end_s": "s",
                "stage_time_s": "s",
                "path_probability_sum": "1",
            },
            (
                "Reviewed finite state, initial, observation, fixed decision-rule and transition tables over ordered epochs; enumerate every positive-probability path exactly within a caller-declared path-count limit.",
            ),
            ("finite_inspection_policy_path_generation_definition",),
            context_validator=_finite_inspection_policy_path_generation_context,
        ),
        ModelSpec(
            "inspection.multi_period_policy_evaluation",
            MultiPeriodInspectionPolicyEvaluation,
            multi_period_inspection_policy,
            {
                "horizon_start_s": "s",
                "horizon_end_s": "s",
                "path_probability_sum": "1",
                "conditional_first_failure_probability": "1",
                "failure_consequence_cost_at_undiscounted_basis": "declared_cost_unit",
                "expected_discounted_action_cost": "declared_cost_unit",
                "expected_discounted_failure_consequence": "declared_cost_unit",
                "expected_discounted_total_loss": "declared_cost_unit",
            },
            (
                "One complete caller-reviewed finite policy-path ensemble over a common event, scope, horizon, start-survival condition, cost and discount basis; evaluate path-probability-weighted discounted action and first-failure consequence costs without policy search.",
            ),
            ("multi_period_inspection_policy_definition",),
            context_validator=_multi_period_inspection_policy_context,
            probability_semantics={
                "conditional_first_failure_probability": "conditional_first_failure_in_period"
            },
        ),
        ModelSpec(
            "inspection.multi_period_policy_comparison",
            MultiPeriodInspectionPolicyComparison,
            multi_period_inspection_policy_comparison,
            {
                "horizon_start_s": "s",
                "horizon_end_s": "s",
                "maximum_conditional_first_failure_probability": "1",
                "conditional_first_failure_probability_for_comparison": "1",
                "expected_discounted_total_loss": "declared_cost_unit",
                "minimum_constraint_compliant_expected_loss": "declared_cost_unit",
                "cost_tie_absolute_tolerance": "declared_cost_unit",
            },
            (
                "At least two complete externally evaluated policies over one common event, scope, horizon, start-survival condition, cost and discount basis; apply caller-approved hard probability and resource constraints before finite expected-loss comparison.",
            ),
            ("multi_period_inspection_policy_comparison_definition",),
            context_validator=_multi_period_inspection_policy_comparison_context,
            probability_semantics={
                "maximum_conditional_first_failure_probability": ("conditional_first_failure_in_period"),
                "conditional_first_failure_probability_for_comparison": (
                    "conditional_first_failure_in_period"
                ),
            },
        ),
        ModelSpec(
            "inspection.pressure_test_load",
            PressureTest,
            pressure_test,
            {"reference_test_pressure_Pa": "Pa", "local_test_pressure_Pa": "Pa"},
            ("User-selected factor and allowables; no automatic standard eligibility or test approval.",),
            ("declared_pressure_test",),
        ),
        ModelSpec(
            "inspection.pipe_membrane_test_pressure",
            PipeMembraneTestPressure,
            pipe_membrane_test_pressure,
            {"membrane_test_pressure_difference_Pa": "Pa", "declared_membrane_stress_Pa": "Pa"},
            (
                "Caller provides the applicable material yield strength, factor and its review basis.",
                "Outside-diameter membrane arithmetic only; grade factors, rounding, thread/coupling resistance, standard eligibility and test approval are not inferred.",
            ),
            ("declared_yield_fraction_pipe_membrane_equilibrium",),
        ),
        ModelSpec(
            "inspection.visual_surface_summary",
            VisualSurfaceExamination,
            visual_surface_summary,
            {
                "target_area_m2": "m^2",
                "examined_area_m2": "m^2",
                "unexamined_area_m2": "m^2",
                "coverage_fraction": "1",
                "maximum_reported_indication_length_m": "m",
                "maximum_reported_indication_width_m": "m",
            },
            (
                "Caller-defined mutually exclusive target areas, reviewed coverage and surface condition, traceable procedure and indication mapping; no acceptance or detection inference.",
            ),
            ("visual_surface_examination_definition",),
        ),
        ModelSpec(
            "inspection.gas_expansion_energy",
            GasInventoryEnergy,
            gas_expansion_energy,
            {"ideal_expansion_work_J": "J", "final_volume_m3": "m^3"},
            (
                "Ideal reversible adiabatic gas expansion; not a blast model or exclusion-distance determination.",
            ),
            ("ideal_gas_first_law",),
        ),
        ModelSpec(
            "inspection.reference_energy_mass",
            ReferenceEnergyMass,
            reference_energy_mass,
            {"reference_equivalent_mass_kg": "kg"},
            (
                "Caller supplies the reference identity, specific energy in J/kg and the physical basis of input energy.",
                "No built-in explosive energy, blast efficiency, overpressure or safety-distance model is applied.",
            ),
            ("energy_divided_by_declared_reference_specific_energy",),
        ),
        ModelSpec(
            "inspection.guided_wave_pair_features",
            GuidedWavePairFeatures,
            guided_wave_pair_features,
            {
                "frequency_Hz": "Hz",
                "window_start_m": "m",
                "window_end_m": "m",
                "maximum_distance_grid_mismatch_m": "m",
                "baseline_rms_V": "V",
                "observation_rms_V": "V",
                "residual_rms_V": "V",
                "normalized_residual_rms": "1",
                "voltage_energy_ratio": "1",
                "correlation_coefficient": "1",
                "peak_absolute_difference_V": "V",
                "signed_mean_difference_V": "V",
            },
            (
                "One physical specimen, aligned provider distance grids and one declared spatial window; paired descriptors do not separate environmental change from damage.",
            ),
            ("guided_wave_pair_feature_definition",),
        ),
        ModelSpec(
            "inspection.guided_wave_reference_ensemble",
            GuidedWaveReferenceEnsemble,
            guided_wave_reference_ensemble,
            {
                "frequency_Hz": "Hz",
                "window_start_m": "m",
                "window_end_m": "m",
                "maximum_distance_grid_mismatch_m": "m",
                "reference_rms_V": "V",
                "observation_rms_V": "V",
                "observation_residual_rms_V": "V",
                "normalized_observation_residual_rms": "1",
                "baseline_spread_rms_V": "V",
                "observation_to_baseline_spread_ratio": "1",
                "leave_one_out_residual_rms_V": "V",
                "leave_one_out_residual_median_V": "V",
                "leave_one_out_residual_q95_V": "V",
                "leave_one_out_residual_maximum_V": "V",
                "observation_to_leave_one_out_median_ratio": "1",
                "observation_to_leave_one_out_maximum_ratio": "1",
                "reference_observation_correlation": "1",
                "peak_absolute_difference_V": "V",
                "signed_mean_difference_V": "V",
            },
            (
                "At least three explicitly selected same-specimen baseline acquisitions, one aligned observation and one spatial window; ensemble descriptors are not detection calibration or acceptance.",
            ),
            ("guided_wave_reference_ensemble_definition",),
        ),
    ]
