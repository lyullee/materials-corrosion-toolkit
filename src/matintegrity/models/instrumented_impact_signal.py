"""Reviewed SI reduction of an instrumented impact force-displacement signal."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ImpactSignalPoint(Contract):
    sample_id: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    displacement_m: Nonnegative
    signed_force_N: float
    expanded_force_uncertainty_N: Nonnegative
    expanded_displacement_uncertainty_m: Nonnegative
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid impact signal points require a basis")
        return self


class ImpactInstrumentCalibration(Contract):
    calibration_record_id: str = Field(min_length=1)
    striker_id: str = Field(min_length=1)
    striker_configuration_id: str = Field(min_length=1)
    force_instrument_id: str = Field(min_length=1)
    displacement_instrument_id: str = Field(min_length=1)
    timebase_id: str = Field(min_length=1)
    force_calibration_id: str = Field(min_length=1)
    displacement_calibration_id: str = Field(min_length=1)
    force_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    displacement_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    timebase_calibration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    instrument_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    calibration_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid impact calibration records require a basis")
        return self


class MachineReportedImpactEnergy(Contract):
    comparison_record_id: str = Field(min_length=1)
    reported_energy_J: Nonnegative
    expanded_uncertainty_J: Nonnegative
    uncertainty_coverage_factor: Positive
    reporting_method_id: str = Field(min_length=1)
    independent_data_path_declared: bool
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity_has_basis(self):
        if not self.record_valid and not self.invalid_or_missing_basis:
            raise ValueError("invalid machine-energy comparison records require a basis")
        return self


class InstrumentedImpactSignalAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    impact_test_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_geometry_id: str = Field(min_length=1)
    notch_geometry_id: str = Field(min_length=1)
    notch_orientation_id: str = Field(min_length=1)
    specimen_orientation_id: str = Field(min_length=1)
    test_temperature_K: Positive
    signal_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    force_unit_token: Literal["N"] = "N"
    displacement_unit_token: Literal["m"] = "m"
    time_unit_token: Literal["s"] = "s"
    calibration: ImpactInstrumentCalibration
    signal_points: tuple[ImpactSignalPoint, ...] = Field(min_length=2)
    valid_window_start_sample_id: str = Field(min_length=1)
    valid_window_end_sample_id: str = Field(min_length=1)
    absorbed_energy_force_direction_multiplier: Literal[-1, 1]
    force_sign_convention: str = Field(min_length=1)
    peak_force_plateau_tolerance_N: Nonnegative
    negative_absorbed_energy_tolerance_J: Nonnegative
    machine_reported_energy: MachineReportedImpactEnergy | None = None
    specimen_notch_orientation_and_material_reviewed: bool
    test_temperature_striker_and_instrument_identity_reviewed: bool
    calibration_and_si_units_reviewed: bool
    source_digest_and_raw_signal_reviewed: bool
    monotonic_displacement_and_time_order_reviewed: bool
    valid_window_and_force_sign_reviewed: bool
    trapezoidal_integration_and_peak_definition_reviewed: bool
    machine_energy_comparison_independence_reviewed: bool

    @model_validator(mode="after")
    def ordered_signal_and_window(self):
        identifiers = [row.sample_id for row in self.signal_points]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("impact signal sample identifiers must be unique")
        times = [row.elapsed_time_s for row in self.signal_points]
        if any(second <= first for first, second in zip(times, times[1:], strict=False)):
            raise ValueError("impact signal elapsed time must be strictly increasing")
        displacements = [row.displacement_m for row in self.signal_points]
        if any(second < first for first, second in zip(displacements, displacements[1:], strict=False)):
            raise ValueError("impact signal displacement must be monotonic nondecreasing")
        index = {identifier: position for position, identifier in enumerate(identifiers)}
        if self.valid_window_start_sample_id not in index or self.valid_window_end_sample_id not in index:
            raise ValueError("impact valid-window samples must belong to the raw signal")
        if index[self.valid_window_end_sample_id] <= index[self.valid_window_start_sample_id]:
            raise ValueError("impact valid window requires at least two ordered samples")
        return self


def instrumented_impact_signal_summary(x: InstrumentedImpactSignalAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "specimen_notch_orientation_and_material_reviewed",
            "test_temperature_striker_and_instrument_identity_reviewed",
            "calibration_and_si_units_reviewed",
            "source_digest_and_raw_signal_reviewed",
            "monotonic_displacement_and_time_order_reviewed",
            "valid_window_and_force_sign_reviewed",
            "trapezoidal_integration_and_peak_definition_reviewed",
            "machine_energy_comparison_independence_reviewed",
        )
        if not getattr(x, name)
    ]
    point_index = {row.sample_id: index for index, row in enumerate(x.signal_points)}
    start = point_index[x.valid_window_start_sample_id]
    end = point_index[x.valid_window_end_sample_id]
    window = x.signal_points[start : end + 1]
    invalid_window_sample_ids = [row.sample_id for row in window if not row.record_valid]
    comparison_invalid = x.machine_reported_energy is not None and (
        not x.machine_reported_energy.record_valid
        or not x.machine_reported_energy.independent_data_path_declared
    )
    if missing_reviews or not x.calibration.record_valid or invalid_window_sample_ids or comparison_invalid:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "calibration_record_valid": x.calibration.record_valid,
                "invalid_window_sample_ids": invalid_window_sample_ids,
                "machine_energy_comparison_valid_and_independent": (
                    None if x.machine_reported_energy is None else not comparison_invalid
                ),
                "invalid_samples_outside_window_ids": [
                    row.sample_id
                    for index, row in enumerate(x.signal_points)
                    if not row.record_valid and not start <= index <= end
                ],
            },
            notes=("Reviewed calibration and valid signal records inside the declared window are required.",),
        )

    multiplier = x.absorbed_energy_force_direction_multiplier
    directed_forces = [multiplier * row.signed_force_N for row in window]
    interval_work = []
    absorbed_energy = 0.0
    for first, second, first_force, second_force in zip(
        window[:-1], window[1:], directed_forces[:-1], directed_forces[1:], strict=True
    ):
        displacement_increment = second.displacement_m - first.displacement_m
        work = 0.5 * (first_force + second_force) * displacement_increment
        absorbed_energy += work
        interval_work.append(
            {
                "start_sample_id": first.sample_id,
                "end_sample_id": second.sample_id,
                "displacement_increment_m": displacement_increment,
                "directed_trapezoidal_work_J": work,
            }
        )
    peak_force = max(directed_forces)
    peak_rows = [
        row
        for row, force in zip(window, directed_forces, strict=True)
        if peak_force - force <= x.peak_force_plateau_tolerance_N
    ]
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "impact_test_id": x.impact_test_id,
        "physical_specimen_id": x.physical_specimen_id,
        "valid_window_sample_ids": [row.sample_id for row in window],
        "valid_window_start_time_s": window[0].elapsed_time_s,
        "valid_window_end_time_s": window[-1].elapsed_time_s,
        "valid_window_start_displacement_m": window[0].displacement_m,
        "valid_window_end_displacement_m": window[-1].displacement_m,
        "force_direction_multiplier": multiplier,
        "trapezoidal_interval_work": interval_work,
        "absorbed_energy_J": absorbed_energy,
        "peak_directed_force_N": peak_force,
        "peak_plateau_sample_ids": [row.sample_id for row in peak_rows],
        "peak_first_time_s": peak_rows[0].elapsed_time_s,
        "peak_last_time_s": peak_rows[-1].elapsed_time_s,
        "peak_first_displacement_m": peak_rows[0].displacement_m,
        "peak_last_displacement_m": peak_rows[-1].displacement_m,
        "invalid_samples_outside_window_ids": [
            row.sample_id
            for index, row in enumerate(x.signal_points)
            if not row.record_valid and not start <= index <= end
        ],
    }
    notes = (
        "Absorbed energy is the signed trapezoidal integral of caller-reviewed directed force over measured displacement in the valid window.",
        "Peak plateaus preserve first/last sample, time and displacement rather than selecting an arbitrary point.",
        "No crack-initiation point, transition curve, toughness conversion, specification acceptance or failure probability is inferred.",
    )
    if absorbed_energy < -x.negative_absorbed_energy_tolerance_J:
        return Calculation(status="needs_data", values=values, notes=notes)
    comparison = x.machine_reported_energy
    if comparison is not None:
        difference = absorbed_energy - comparison.reported_energy_J
        values["machine_energy_comparison"] = {
            "comparison_record_id": comparison.comparison_record_id,
            "machine_reported_energy_J": comparison.reported_energy_J,
            "machine_expanded_uncertainty_J": comparison.expanded_uncertainty_J,
            "signed_difference_J": difference,
            "relative_difference": (
                None if comparison.reported_energy_J == 0.0 else difference / comparison.reported_energy_J
            ),
        }
    else:
        values["machine_energy_comparison"] = None
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("instrumented-impact assessment asset and location must match run context")

    return [
        ModelSpec(
            "inspection.instrumented_impact_signal_summary",
            InstrumentedImpactSignalAssessment,
            instrumented_impact_signal_summary,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "impact_test_id": "1",
                "physical_specimen_id": "1",
                "valid_window_sample_ids": "1",
                "valid_window_start_time_s": "s",
                "valid_window_end_time_s": "s",
                "valid_window_start_displacement_m": "m",
                "valid_window_end_displacement_m": "m",
                "force_direction_multiplier": "1",
                "trapezoidal_interval_work": "mixed",
                "absorbed_energy_J": "J",
                "peak_directed_force_N": "N",
                "peak_plateau_sample_ids": "1",
                "peak_first_time_s": "s",
                "peak_last_time_s": "s",
                "peak_first_displacement_m": "m",
                "peak_last_displacement_m": "m",
                "invalid_samples_outside_window_ids": "1",
                "machine_energy_comparison": "mixed",
            },
            (
                "The supplied signal is calibrated SI force, displacement and time with a reviewed sign convention and valid window.",
                "Displacement is monotonic nondecreasing and energy uses adjacent-sample trapezoidal integration without filtering.",
                "Signal reduction does not identify crack initiation or establish toughness, transition behavior or acceptance.",
            ),
            ("authored_trapezoidal_instrumented_impact_reduction",),
            context_validator=same_identity,
        )
    ]
