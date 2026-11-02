"""Blank-corrected known-volume pressure-rise analysis from reviewed raw traces."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

R_GAS = 8.31446261815324


class VacuumPressureRiseRun(Contract):
    run_id: str = Field(min_length=1)
    role: Literal["blank", "test"]
    source_group_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=3)
    absolute_pressure_Pa: tuple[Nonnegative, ...] = Field(min_length=3)
    pressure_standard_uncertainty_Pa: tuple[Positive, ...] = Field(min_length=3)
    temperature_K: tuple[Positive, ...] = Field(min_length=3)
    fit_window_start_s: Nonnegative
    fit_window_end_s: Positive
    apparatus_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    run_data_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_trace(self):
        lengths = {
            len(self.elapsed_time_s),
            len(self.absolute_pressure_Pa),
            len(self.pressure_standard_uncertainty_Pa),
            len(self.temperature_K),
        }
        if len(lengths) != 1:
            raise ValueError("vacuum trace arrays must align")
        if any(b <= a for a, b in zip(self.elapsed_time_s, self.elapsed_time_s[1:], strict=False)):
            raise ValueError("vacuum trace clock must be strictly increasing")
        if self.fit_window_end_s <= self.fit_window_start_s:
            raise ValueError("vacuum fit window must have positive duration")
        count = sum(self.fit_window_start_s <= t <= self.fit_window_end_s for t in self.elapsed_time_s)
        if count < 3:
            raise ValueError("vacuum fit window must contain at least three original points")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid vacuum runs require a basis")
        return self


class KnownVolumePressureRiseTest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    apparatus_id: str = Field(min_length=1)
    rigid_volume_m3: Positive
    pressure_basis: Literal["absolute"] = "absolute"
    runs: tuple[VacuumPressureRiseRun, ...] = Field(min_length=2, max_length=2)
    maximum_temperature_range_K: Nonnegative
    molar_conversion_requested: bool = False
    molar_conversion_state_reviewed: bool = False
    reference_temperature_K: Positive | None = None
    reference_net_throughput_Pa_m3_s: float | None = None
    reference_standard_uncertainty_Pa_m3_s: Positive | None = None
    reference_source_group_id: str | None = None
    reference_result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    apparatus_volume_and_isolation_reviewed: bool
    absolute_pressure_temperature_and_clock_reviewed: bool
    blank_test_independence_reviewed: bool
    fit_windows_weights_and_uncertainty_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    reference_comparison_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def run_and_reference_contract(self):
        if {row.role for row in self.runs} != {"blank", "test"}:
            raise ValueError("pressure-rise assessment requires exactly one blank and one test run")
        if len({row.run_id for row in self.runs}) != 2:
            raise ValueError("vacuum run IDs must be unique")
        if len({row.source_group_id for row in self.runs}) != 2:
            raise ValueError("blank and test runs require independent source groups")
        if len({row.clock_id for row in self.runs}) != 1:
            raise ValueError("blank and test runs must use one reviewed clock identity")
        reference_fields = (
            self.reference_net_throughput_Pa_m3_s,
            self.reference_standard_uncertainty_Pa_m3_s,
            self.reference_source_group_id,
            self.reference_result_digest,
        )
        if any(value is not None for value in reference_fields) and any(
            value is None for value in reference_fields
        ):
            raise ValueError("reference comparison fields must be supplied together")
        if self.molar_conversion_requested and self.reference_temperature_K is None:
            raise ValueError("molar conversion requires a reference absolute temperature")
        return self


def _fit(run: VacuumPressureRiseRun):
    rows = [
        (time, pressure, uncertainty, temperature)
        for time, pressure, uncertainty, temperature in zip(
            run.elapsed_time_s,
            run.absolute_pressure_Pa,
            run.pressure_standard_uncertainty_Pa,
            run.temperature_K,
            strict=True,
        )
        if run.fit_window_start_s <= time <= run.fit_window_end_s
    ]
    weights = [1.0 / uncertainty**2 for _, _, uncertainty, _ in rows]
    weight_sum = sum(weights)
    mean_time = sum(weight * row[0] for weight, row in zip(weights, rows, strict=True)) / weight_sum
    mean_pressure = sum(weight * row[1] for weight, row in zip(weights, rows, strict=True)) / weight_sum
    denominator = sum(weight * (row[0] - mean_time) ** 2 for weight, row in zip(weights, rows, strict=True))
    slope = (
        sum(
            weight * (row[0] - mean_time) * (row[1] - mean_pressure)
            for weight, row in zip(weights, rows, strict=True)
        )
        / denominator
    )
    return slope, math.sqrt(1.0 / denominator), [row[3] for row in rows], len(rows)


def known_volume_pressure_rise(x: KnownVolumePressureRiseTest) -> Calculation:
    reviews = (
        "apparatus_volume_and_isolation_reviewed",
        "absolute_pressure_temperature_and_clock_reviewed",
        "blank_test_independence_reviewed",
        "fit_windows_weights_and_uncertainty_reviewed",
        "provider_lineage_and_digests_reviewed",
        "reference_comparison_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    invalid_runs = [row.run_id for row in x.runs if not row.record_valid]
    if (
        missing_reviews
        or invalid_runs
        or (x.molar_conversion_requested and not x.molar_conversion_state_reviewed)
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "invalid_run_ids": invalid_runs,
                "molar_conversion_state_reviewed": x.molar_conversion_state_reviewed,
            },
            notes=("Pressure-rise calculation is withheld until records and state reviews are complete.",),
        )
    fitted = {row.role: (row, _fit(row)) for row in x.runs}
    temperature_ranges = {role: max(result[2]) - min(result[2]) for role, (_, result) in fitted.items()}
    if any(value > x.maximum_temperature_range_K for value in temperature_ranges.values()):
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": x.assessment_id, "fit_window_temperature_ranges_K": temperature_ranges},
            notes=("A fit window exceeds the caller-reviewed temperature range.",),
        )
    blank_slope, blank_sigma, _, blank_count = fitted["blank"][1]
    test_slope, test_sigma, _, test_count = fitted["test"][1]
    net = x.rigid_volume_m3 * (test_slope - blank_slope)
    net_sigma = x.rigid_volume_m3 * math.hypot(test_sigma, blank_sigma)
    values = {
        "assessment_id": x.assessment_id,
        "apparatus_id": x.apparatus_id,
        "blank_pressure_slope_Pa_s": blank_slope,
        "test_pressure_slope_Pa_s": test_slope,
        "blank_slope_standard_uncertainty_Pa_s": blank_sigma,
        "test_slope_standard_uncertainty_Pa_s": test_sigma,
        "net_gas_throughput_Pa_m3_s": net,
        "net_gas_throughput_standard_uncertainty_Pa_m3_s": net_sigma,
        "fit_point_counts": {"blank": blank_count, "test": test_count},
        "fit_window_temperature_ranges_K": temperature_ranges,
    }
    if x.molar_conversion_requested:
        values["net_molar_flow_mol_s"] = net / (R_GAS * x.reference_temperature_K)
        values["net_molar_flow_standard_uncertainty_mol_s"] = net_sigma / (R_GAS * x.reference_temperature_K)
    if x.reference_net_throughput_Pa_m3_s is not None:
        difference = net - x.reference_net_throughput_Pa_m3_s
        combined = math.hypot(net_sigma, x.reference_standard_uncertainty_Pa_m3_s)
        values["reference_comparison"] = {
            "difference_Pa_m3_s": difference,
            "combined_standard_uncertainty_Pa_m3_s": combined,
            "standardized_difference": difference / combined,
            "reference_source_group_id": x.reference_source_group_id,
            "reference_result_digest": x.reference_result_digest,
        }
    return Calculation(
        values=values,
        notes=(
            "Blank and test slopes are independently weighted fits to original points inside caller-reviewed windows; negative net throughput is retained.",
            "Pressure-rise throughput combines all gas loads and does not physically separate outgassing from a through-leak.",
            "No leak location, acceptance, failure probability or FTA event is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("vacuum pressure-rise asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.known_volume_pressure_rise",
            KnownVolumePressureRiseTest,
            known_volume_pressure_rise,
            {
                "assessment_id": "1",
                "apparatus_id": "1",
                "blank_pressure_slope_Pa_s": "Pa/s",
                "test_pressure_slope_Pa_s": "Pa/s",
                "blank_slope_standard_uncertainty_Pa_s": "Pa/s",
                "test_slope_standard_uncertainty_Pa_s": "Pa/s",
                "net_gas_throughput_Pa_m3_s": "Pa*m3/s",
                "net_gas_throughput_standard_uncertainty_Pa_m3_s": "Pa*m3/s",
                "fit_point_counts": "count",
                "fit_window_temperature_ranges_K": "K",
                "net_molar_flow_mol_s": "mol/s",
                "net_molar_flow_standard_uncertainty_mol_s": "mol/s",
                "reference_comparison": "mixed",
            },
            (
                "Rigid known volume, absolute pressure, one reviewed clock and independent blank/test source groups.",
                "Weighted linear fits use original monotonic trace points inside declared windows.",
                "Molar conversion is optional and requires an explicitly reviewed absolute temperature state.",
            ),
            ("weighted_blank_corrected_known_volume_pressure_rise",),
            context_validator=same_identity,
        )
    ]
