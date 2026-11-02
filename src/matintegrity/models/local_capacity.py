"""Nodal axial area scan with reviewed, replaceable reference and bulging providers."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class ReferenceCapacity(Contract):
    geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    reference_pressure_difference_Pa: Positive
    capacity_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def licensed_basis(self):
        if any(not item.license_id for item in self.evidence):
            raise ValueError("reference capacity needs a declared source license or entitlement")
        return self


class BulgingFactorTable(Contract):
    geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    window_length_m: list[Nonnegative] = Field(min_length=2)
    factor: list[float] = Field(min_length=2)
    validity_description: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def table(self):
        if len(self.window_length_m) != len(self.factor) or np.any(np.diff(self.window_length_m) <= 0):
            raise ValueError("aligned strictly increasing bulging length knots are required")
        if any(value < 1 for value in self.factor) or np.any(np.diff(self.factor) < 0):
            raise ValueError("this provider requires finite nondecreasing factors at least one")
        if any(not item.license_id for item in self.evidence):
            raise ValueError("bulging table needs a declared source license or entitlement")
        return self


class ProfileCapacity(Contract):
    geometry_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    reference_wall_thickness_m: Positive
    axial_position_m: list[float] = Field(min_length=2, max_length=500)
    measured_remaining_thickness_m: list[Nonnegative] = Field(min_length=2, max_length=500)
    reference_capacity: ReferenceCapacity
    bulging_table: BulgingFactorTable
    maximum_supported_depth_fraction: float = Field(ge=0, lt=1)
    full_axial_extent_confirmed: bool
    blunt_metal_loss_confirmed: bool
    internal_pressure_dominant_confirmed: bool
    provider_applicability_reviewed: bool

    @model_validator(mode="after")
    def align(self):
        if len(self.axial_position_m) != len(self.measured_remaining_thickness_m):
            raise ValueError("one measured wall thickness per axial position is required")
        if np.any(np.diff(self.axial_position_m) <= 0):
            raise ValueError("strictly increasing axial positions are required")
        return self


def profile_capacity(x: ProfileCapacity) -> Calculation:
    if not all(
        (
            x.full_axial_extent_confirmed,
            x.blunt_metal_loss_confirmed,
            x.internal_pressure_dominant_confirmed,
            x.provider_applicability_reviewed,
        )
    ):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "Confirm complete axial extent, blunt loss, internal-pressure dominance and both providers' applicability before a capacity scan.",
            ),
        )
    for provider in (x.reference_capacity, x.bulging_table):
        if (provider.geometry_id, provider.material_condition_id) != (x.geometry_id, x.material_condition_id):
            return Calculation(
                status="needs_data",
                values={},
                notes=("Reference capacity, bulging table and profile identities must match exactly.",),
            )
    position = np.asarray(x.axial_position_m)
    thickness = np.asarray(x.measured_remaining_thickness_m)
    if np.any(thickness <= 0):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=(
                "A measured zero ligament requires a separate leakage/perforation assessment; no zero burst capacity is inferred.",
            ),
        )
    if np.any(thickness > x.reference_wall_thickness_m):
        return Calculation(
            status="needs_data",
            values={},
            notes=(
                "A measurement exceeds the declared reference wall; resolve baseline and sizing uncertainty instead of clipping apparent negative loss.",
            ),
        )
    relative_loss = 1 - thickness / x.reference_wall_thickness_m
    if relative_loss.max() > x.maximum_supported_depth_fraction:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("A measured depth exceeds the caller's supported relative-depth bound.",),
        )
    spacing = np.diff(position)
    full_length = float(position[-1] - position[0])
    if not math.isfinite(full_length):
        return Calculation(
            status="out_of_scope", values={}, notes=("Axial span exceeds the finite numerical range.",)
        )
    if (
        spacing.min() < x.bulging_table.window_length_m[0]
        or full_length > x.bulging_table.window_length_m[-1]
    ):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=(
                "All nodal window lengths must lie inside the declared bulging table; no window is skipped or extrapolated.",
            ),
        )
    segment_loss = 0.5 * (relative_loss[:-1] + relative_loss[1:]) * spacing
    critical = None
    windows = 0
    for start in range(len(position) - 1):
        length = position[start + 1 :] - position[start]
        # Start-local sums avoid subtracting two large cumulative areas for a tiny window.
        integrated_relative_loss = np.cumsum(segment_loss[start:])
        area_fraction = integrated_relative_loss / length
        factors = np.interp(length, x.bulging_table.window_length_m, x.bulging_table.factor)
        remaining = 1 - area_fraction
        reduction = remaining / ((factors - 1 + remaining) / factors)
        if not np.isfinite(reduction).all() or np.any(reduction <= 0) or np.any(reduction > 1 + 1e-12):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=(
                    "Numerical scan did not preserve a finite physical reduction; no window is silently discarded.",
                ),
            )
        index = int(np.argmin(reduction))
        end = start + index + 1
        candidate = dict(
            start_index=start,
            end_index=end,
            start_position_m=float(position[start]),
            end_position_m=float(position[end]),
            length_m=float(length[index]),
            loss_area_fraction=float(area_fraction[index]),
            bulging_factor=float(factors[index]),
            capacity_reduction_factor=float(reduction[index]),
            projected_loss_area_m2=float(integrated_relative_loss[index] * x.reference_wall_thickness_m),
        )
        if not math.isfinite(candidate["projected_loss_area_m2"]):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=("Projected loss area exceeds the finite numerical range.",),
            )
        windows += len(length)
        if critical is None or candidate["capacity_reduction_factor"] < critical["capacity_reduction_factor"]:
            critical = candidate
    pressure = x.reference_capacity.reference_pressure_difference_Pa * critical["capacity_reduction_factor"]
    return Calculation(
        values=dict(
            pressure_basis="internal_minus_external",
            critical_window=critical,
            scanned_nodal_windows=windows,
            capacity_reduction_factor=critical["capacity_reduction_factor"],
            declared_model_pressure_difference_capacity_Pa=pressure,
            minimum_measured_thickness_m=float(thickness.min()),
            maximum_measured_depth_fraction=float(relative_loss.max()),
            reference_capacity_digest=canonical_digest(x.reference_capacity.model_dump(mode="json")),
            bulging_table_digest=canonical_digest(x.bulging_table.model_dump(mode="json")),
        ),
        notes=(
            "For each pair of supplied axial nodes, piecewise-linear depth is integrated and alpha=A/(reference wall times window length). The declared reduction is (1-alpha)/(1-alpha/M), with a caller-supplied pressure reference and bulging table.",
            "Only nodal endpoint windows are scanned. Continuous endpoint optima, unmeasured pits, circumferential extent, sizing/detection uncertainty and local discontinuities need separate treatment and spatial convergence checks.",
            "Pressure capacity is an internal-minus-external pressure difference, not absolute internal pressure. This is a parameterized static blunt-loss component, not a complete standard assessment, MAWP, safety factor, rupture/leak classification or event probability. No regulatory coefficient, acceptance table, flow-stress rule or prescribed factor is bundled.",
        ),
    )


class ProfileCapacityCorrosionScenario(Contract):
    """Apply a caller-specified uniform loss scenario to a reviewed axial thickness profile."""

    scenario_id: str = Field(min_length=1)
    profile: ProfileCapacity
    uniform_loss_rate_m_s: Nonnegative
    forecast_horizon_s: Nonnegative


def profile_capacity_corrosion_scenario(x: ProfileCapacityCorrosionScenario) -> Calculation:
    """Re-evaluate the same profile capacity provider after uniform wall-loss projection."""
    baseline = profile_capacity(x.profile)
    common = {
        "scenario_id": x.scenario_id,
        "baseline_status": baseline.status,
        "forecast_status": "not_evaluated",
        "baseline_pressure_difference_capacity_Pa": baseline.values.get(
            "declared_model_pressure_difference_capacity_Pa"
        ),
        "forecast_pressure_difference_capacity_Pa": None,
        "capacity_change_Pa": None,
        "capacity_loss_fraction_of_baseline": None,
        "uniform_metal_loss_m": None,
        "forecast_minimum_thickness_m": None,
        "baseline_capacity_reduction_factor": baseline.values.get("capacity_reduction_factor"),
        "forecast_capacity_reduction_factor": None,
        "forecast_critical_window_start_m": None,
        "forecast_critical_window_end_m": None,
    }
    if baseline.status != "computed":
        return Calculation(
            status=baseline.status,
            values=common,
            notes=baseline.notes
            + (
                "The corrosion scenario was not evaluated because the baseline profile has no computed capacity.",
            ),
        )

    uniform_loss = x.uniform_loss_rate_m_s * x.forecast_horizon_s
    if not math.isfinite(uniform_loss):
        return Calculation(
            status="out_of_scope",
            values=common | {"forecast_status": "out_of_scope"},
            notes=("The declared rate-horizon product exceeds the finite numerical range.",),
        )
    forecast_thickness = [value - uniform_loss for value in x.profile.measured_remaining_thickness_m]
    minimum_thickness = min(forecast_thickness)
    if minimum_thickness <= 0:
        return Calculation(
            status="out_of_scope",
            values=common
            | {
                "forecast_status": "out_of_scope",
                "uniform_metal_loss_m": uniform_loss,
                "forecast_minimum_thickness_m": minimum_thickness,
            },
            notes=(
                "The uniform scenario reaches or crosses zero ligament at at least one supplied location; no pressure capacity is inferred beyond that point.",
            ),
        )

    forecast_profile = x.profile.model_copy(
        update={"measured_remaining_thickness_m": tuple(forecast_thickness)}
    )
    forecast = profile_capacity(forecast_profile)
    values = common | {
        "forecast_status": forecast.status,
        "uniform_metal_loss_m": uniform_loss,
        "forecast_minimum_thickness_m": minimum_thickness,
        "forecast_capacity_reduction_factor": forecast.values.get("capacity_reduction_factor"),
        "forecast_critical_window_start_m": forecast.values.get("critical_window", {}).get(
            "start_position_m"
        ),
        "forecast_critical_window_end_m": forecast.values.get("critical_window", {}).get("end_position_m"),
    }
    if forecast.status != "computed":
        return Calculation(
            status=forecast.status,
            values=values,
            notes=forecast.notes
            + ("The projected profile did not meet its caller-declared capacity-provider scope.",),
        )

    baseline_capacity = baseline.values["declared_model_pressure_difference_capacity_Pa"]
    forecast_capacity = forecast.values["declared_model_pressure_difference_capacity_Pa"]
    return Calculation(
        values=values
        | {
            "forecast_pressure_difference_capacity_Pa": forecast_capacity,
            "capacity_change_Pa": baseline_capacity - forecast_capacity,
            "capacity_loss_fraction_of_baseline": 1 - forecast_capacity / baseline_capacity,
        },
        notes=(
            "The same caller-supplied profile-capacity and bulging providers are applied before and after a uniform thickness decrement.",
            "The rate, horizon and uniform spatial loss assumption are caller inputs. This is a conditional deterministic scenario, not a corrosion-rate fit, complete fitness-for-service assessment, acceptance decision, remaining-life prediction or failure probability.",
        ),
    )


class ProfileCapacityRateFieldScenario(Contract):
    """Project a caller-supplied axial and time-varying corrosion-rate field."""

    scenario_id: str = Field(min_length=1)
    profile: ProfileCapacity
    time_s: list[Nonnegative] = Field(min_length=2, max_length=1000)
    corrosion_rate_m_s: list[list[Nonnegative]] = Field(min_length=2, max_length=500)
    forecast_horizon_s: Positive

    @model_validator(mode="after")
    def align_field(self):
        if self.time_s[0] != 0 or np.any(np.diff(self.time_s) <= 0):
            raise ValueError("rate-field times must start at zero and increase strictly")
        if self.forecast_horizon_s > self.time_s[-1]:
            raise ValueError("forecast horizon cannot extend beyond supplied rate-field support")
        if len(self.corrosion_rate_m_s) != len(self.profile.axial_position_m):
            raise ValueError("one rate-field row is required for each profile axial node")
        if any(len(row) != len(self.time_s) for row in self.corrosion_rate_m_s):
            raise ValueError("each axial rate-field row must align with the supplied time knots")
        return self


def profile_capacity_rate_field_scenario(x: ProfileCapacityRateFieldScenario) -> Calculation:
    """Integrate supplied linearly interpolated rates, then reuse the profile-capacity provider."""
    baseline = profile_capacity(x.profile)
    common = {
        "scenario_id": x.scenario_id,
        "baseline_status": baseline.status,
        "forecast_status": "not_evaluated",
        "baseline_pressure_difference_capacity_Pa": baseline.values.get(
            "declared_model_pressure_difference_capacity_Pa"
        ),
        "forecast_pressure_difference_capacity_Pa": None,
        "capacity_change_Pa": None,
        "capacity_loss_fraction_of_baseline": None,
        "integrated_metal_loss_by_node_m": None,
        "forecast_minimum_thickness_m": None,
        "forecast_capacity_reduction_factor": None,
    }
    if baseline.status != "computed":
        return Calculation(
            status=baseline.status,
            values=common,
            notes=baseline.notes
            + ("The rate-field scenario was not evaluated because baseline capacity was not computed.",),
        )

    times = np.asarray(x.time_s, dtype=float)
    rates = np.asarray(x.corrosion_rate_m_s, dtype=float)
    horizon = x.forecast_horizon_s
    selected = times < horizon
    integration_times = np.r_[times[selected], horizon]
    horizon_rates = np.asarray([np.interp(horizon, times, row) for row in rates], dtype=float)
    integration_rates = np.column_stack((rates[:, selected], horizon_rates))
    losses = np.trapezoid(integration_rates, x=integration_times, axis=1)
    if not np.isfinite(losses).all():
        return Calculation(
            status="out_of_scope",
            values=common | {"forecast_status": "out_of_scope"},
            notes=("Integrated rate-field loss exceeds the finite numerical range.",),
        )

    forecast_thickness = np.asarray(x.profile.measured_remaining_thickness_m) - losses
    minimum_thickness = float(forecast_thickness.min())
    projected_values = common | {
        "integrated_metal_loss_by_node_m": losses.tolist(),
        "forecast_minimum_thickness_m": minimum_thickness,
    }
    if minimum_thickness <= 0:
        return Calculation(
            status="out_of_scope",
            values=projected_values | {"forecast_status": "out_of_scope"},
            notes=(
                "The supplied rate field reaches or crosses zero ligament at a profile node; no forecast pressure capacity is inferred.",
            ),
        )

    forecast_profile = x.profile.model_copy(
        update={"measured_remaining_thickness_m": tuple(forecast_thickness.tolist())}
    )
    forecast = profile_capacity(forecast_profile)
    result_values = projected_values | {
        "forecast_status": forecast.status,
        "forecast_capacity_reduction_factor": forecast.values.get("capacity_reduction_factor"),
    }
    if forecast.status != "computed":
        return Calculation(
            status=forecast.status,
            values=result_values,
            notes=forecast.notes + ("The projected profile exceeded the declared capacity-provider scope.",),
        )

    baseline_capacity = baseline.values["declared_model_pressure_difference_capacity_Pa"]
    forecast_capacity = forecast.values["declared_model_pressure_difference_capacity_Pa"]
    return Calculation(
        values=result_values
        | {
            "forecast_pressure_difference_capacity_Pa": forecast_capacity,
            "capacity_change_Pa": baseline_capacity - forecast_capacity,
            "capacity_loss_fraction_of_baseline": 1 - forecast_capacity / baseline_capacity,
        },
        notes=(
            "Rate values at supplied axial nodes and time knots are connected by piecewise-linear interpolation and integrated by the trapezoidal rule, including an interpolated horizon endpoint.",
            "Rates are caller-supplied and are not fitted, spatially interpolated, extrapolated, probabilistic or mechanistically predicted. The result is a deterministic conditional scenario, not remaining life, acceptance or failure probability.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "structural.profile_capacity_rate_field_scenario",
            ProfileCapacityRateFieldScenario,
            profile_capacity_rate_field_scenario,
            {
                "baseline_pressure_difference_capacity_Pa": "Pa",
                "forecast_pressure_difference_capacity_Pa": "Pa",
                "capacity_change_Pa": "Pa",
                "capacity_loss_fraction_of_baseline": "1",
                "integrated_metal_loss_by_node_m": "m",
                "forecast_minimum_thickness_m": "m",
                "forecast_capacity_reduction_factor": "1",
                "baseline_status": "1",
                "forecast_status": "1",
                "scenario_id": "1",
            },
            (
                "A caller-provided axial-by-time rate field is integrated nodewise and passed to the same reviewed profile-capacity provider.",
                "No rate inference, spatial interpolation or temporal extrapolation is performed; provider and zero-ligament limits remain explicit.",
            ),
            ("linear_degradation", "piecewise_linear_history", "piecewise_linear_loss_geometry"),
        ),
        ModelSpec(
            "structural.profile_capacity_corrosion_scenario",
            ProfileCapacityCorrosionScenario,
            profile_capacity_corrosion_scenario,
            {
                "baseline_pressure_difference_capacity_Pa": "Pa",
                "forecast_pressure_difference_capacity_Pa": "Pa",
                "capacity_change_Pa": "Pa",
                "capacity_loss_fraction_of_baseline": "1",
                "uniform_metal_loss_m": "m",
                "forecast_minimum_thickness_m": "m",
                "baseline_capacity_reduction_factor": "1",
                "forecast_capacity_reduction_factor": "1",
                "forecast_critical_window_start_m": "m",
                "forecast_critical_window_end_m": "m",
                "baseline_status": "1",
                "forecast_status": "1",
                "scenario_id": "1",
            },
            (
                "The supplied axial remaining-thickness profile is re-evaluated after a caller-declared spatially uniform constant loss rate over a fixed horizon.",
                "Both states use the exact same reviewed reference-pressure and bulging providers; zero-ligament, provider-boundary and baseline failures remain explicit and no acceptance or probability is inferred.",
            ),
            ("linear_degradation", "bsee_area_reduction", "piecewise_linear_loss_geometry"),
        ),
        ModelSpec(
            "structural.profile_capacity",
            ProfileCapacity,
            profile_capacity,
            {
                "declared_model_pressure_difference_capacity_Pa": "Pa",
                "minimum_measured_thickness_m": "m",
                "capacity_reduction_factor": "1",
                "critical_window.projected_loss_area_m2": "m^2",
                "critical_window.length_m": "m",
            },
            (
                "Nodal axial blunt-loss area scan with exact caller-matched reference pressure and bounded nondecreasing bulging table; no automatic engineering qualification.",
            ),
            ("bsee_area_reduction", "piecewise_linear_loss_geometry"),
        ),
    ]
