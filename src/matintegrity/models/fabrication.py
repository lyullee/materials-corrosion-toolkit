"""Basic welding, fastening, coating and heat-transfer calculations."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class ArcEnergy(Contract):
    voltage_V: Positive
    current_A: Positive
    travel_speed_m_s: Positive
    efficiency: float = Field(gt=0, le=1)


class MeasuredWeldEnergy(Contract):
    """Measured source energy over a declared deposited weld length."""

    source_energy_J: Nonnegative
    weld_length_m: Positive
    efficiency: float = Field(gt=0, le=1)


def measured_weld_energy(x: MeasuredWeldEnergy) -> Calculation:
    gross = x.source_energy_J / x.weld_length_m
    return Calculation(
        values={
            "source_energy_per_length_J_m": gross,
            "net_heat_input_J_m": x.efficiency * gross,
        }
    )


class WeldPowerTravel(Contract):
    """Constant measured source power and weld travel speed in SI units."""

    source_power_W: Nonnegative
    travel_speed_m_s: Positive
    efficiency: float = Field(gt=0, le=1)


def weld_power_travel(x: WeldPowerTravel) -> Calculation:
    gross = x.source_power_W / x.travel_speed_m_s
    return Calculation(
        values={
            "source_energy_per_length_J_m": gross,
            "net_heat_input_J_m": x.efficiency * gross,
        }
    )


class RosenthalPointSource3D(Contract):
    """Caller-defined steady moving point-source temperature field for a half-space."""

    absorbed_power_W: Positive
    travel_speed_m_s: Positive
    thermal_conductivity_W_m_K: Positive
    density_kg_m3: Positive
    specific_heat_J_kg_K: Positive
    initial_temperature_K: Positive
    source_relative_x_m: tuple[float, ...] = Field(min_length=1)
    transverse_y_m: tuple[float, ...] = Field(min_length=1)
    depth_z_m: tuple[Nonnegative, ...] = Field(min_length=1)
    time_s: tuple[Nonnegative, ...] | None = None
    threshold_temperatures_K: tuple[Positive, ...] = ()
    semi_infinite_half_space_reviewed: bool
    constant_properties_reviewed: bool
    phase_change_and_latent_heat_neglected_reviewed: bool
    convection_radiation_and_pool_flow_neglected_reviewed: bool
    point_source_and_steady_moving_frame_reviewed: bool

    @model_validator(mode="after")
    def aligned_points(self):
        if len({len(self.source_relative_x_m), len(self.transverse_y_m), len(self.depth_z_m)}) != 1:
            raise ValueError("temperature query coordinate arrays must have equal lengths")
        if self.time_s is not None:
            if len(self.time_s) != len(self.source_relative_x_m):
                raise ValueError("time samples must align with the moving-frame coordinate arrays")
            if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
                raise ValueError("thermal-history sample times must strictly increase")
        elif self.threshold_temperatures_K:
            raise ValueError("threshold crossings require an explicit aligned time vector")
        if len(set(self.threshold_temperatures_K)) != len(self.threshold_temperatures_K):
            raise ValueError("threshold temperatures must be unique")
        if any(
            math.hypot(x, y, z) == 0
            for x, y, z in zip(self.source_relative_x_m, self.transverse_y_m, self.depth_z_m, strict=True)
        ):
            raise ValueError("the ideal point-source singularity cannot be evaluated at the source location")
        return self


def rosenthal_point_source_3d(x: RosenthalPointSource3D) -> Calculation:
    review_fields = (
        "semi_infinite_half_space_reviewed",
        "constant_properties_reviewed",
        "phase_change_and_latent_heat_neglected_reviewed",
        "convection_radiation_and_pool_flow_neglected_reviewed",
        "point_source_and_steady_moving_frame_reviewed",
    )
    missing = [name for name in review_fields if not getattr(x, name)]
    if missing:
        return Calculation(status="needs_data", values={"missing_applicability_reviews": missing})
    alpha = x.thermal_conductivity_W_m_K / (x.density_kg_m3 * x.specific_heat_J_kg_K)
    temperatures = []
    for xi, yi, zi in zip(x.source_relative_x_m, x.transverse_y_m, x.depth_z_m, strict=True):
        radius = math.sqrt(xi * xi + yi * yi + zi * zi)
        exponent = -x.travel_speed_m_s * (xi + radius) / (2.0 * alpha)
        rise = (
            x.absorbed_power_W / (2.0 * math.pi * x.thermal_conductivity_W_m_K * radius) * math.exp(exponent)
        )
        temperature = x.initial_temperature_K + rise
        if not math.isfinite(temperature):
            return Calculation(
                status="out_of_scope", values={"reason": "temperature exceeds finite numeric support"}
            )
        temperatures.append(temperature)
    crossings = []
    if x.time_s is not None:
        for threshold in x.threshold_temperatures_K:
            found = []
            for index, (left, right) in enumerate(zip(temperatures, temperatures[1:], strict=False)):
                if left == right:
                    continue
                if (left - threshold) * (right - threshold) <= 0:
                    fraction = (threshold - left) / (right - left)
                    time = x.time_s[index] + fraction * (x.time_s[index + 1] - x.time_s[index])
                    direction = "heating" if right > left else "cooling"
                    if not found or not math.isclose(time, found[-1]["time_s"], rel_tol=0.0, abs_tol=1e-12):
                        found.append({"time_s": time, "direction": direction, "bracket_index": index})
            crossings.append({"threshold_temperature_K": threshold, "crossings": found})
    return Calculation(
        values={
            "thermal_diffusivity_m2_s": alpha,
            "temperature_K": temperatures,
            "temperature_rise_K": [value - x.initial_temperature_K for value in temperatures],
            "time_s": list(x.time_s) if x.time_s is not None else None,
            "threshold_crossings": crossings,
            "query_count": len(temperatures),
            "basis": "steady_rosenthal_moving_point_source_three_dimensional_half_space",
        },
        notes=(
            "This idealized steady field excludes finite travel starts, finite boundaries, variable properties, phase change, surface losses, and weld-pool flow.",
            "Optional threshold times use linear interpolation between caller-sampled moving-frame evaluations; they are not qualified cooling-time, hardness, microstructure, residual-stress, or weld-acceptance predictions.",
        ),
    )


class RosenthalCoolingIntervalLink(Contract):
    """Compose a fixed-point moving-source history with a caller-selected cooling branch."""

    thermal_history: RosenthalPointSource3D
    upper_temperature_K: Positive
    lower_temperature_K: Positive
    cooling_branch_start_index: int = Field(default=0, ge=0)
    cooling_branch_end_index: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def fixed_point_history_and_branch(self):
        history = self.thermal_history
        if self.lower_temperature_K >= self.upper_temperature_K:
            raise ValueError("lower threshold must be below upper threshold")
        if history.time_s is None or len(history.time_s) < 2:
            raise ValueError("a time-resolved Rosenthal history is required")
        if any(y != history.transverse_y_m[0] for y in history.transverse_y_m) or any(
            z != history.depth_z_m[0] for z in history.depth_z_m
        ):
            raise ValueError("a fixed-point history must keep transverse position and depth constant")
        x0, t0 = history.source_relative_x_m[0], history.time_s[0]
        for coordinate, time in zip(history.source_relative_x_m, history.time_s, strict=True):
            expected = x0 - history.travel_speed_m_s * (time - t0)
            if not math.isclose(coordinate, expected, rel_tol=1e-9, abs_tol=1e-12):
                raise ValueError(
                    "moving-frame coordinates must follow one fixed point and the declared travel speed"
                )
        end = (
            len(history.time_s) - 1
            if self.cooling_branch_end_index is None
            else self.cooling_branch_end_index
        )
        if self.cooling_branch_start_index >= end or end >= len(history.time_s):
            raise ValueError("cooling branch indices must select at least two in-range history samples")
        return self


def evaluate_rosenthal_cooling_interval(x: RosenthalCoolingIntervalLink) -> Calculation:
    """Evaluate one sampled Rosenthal history, then calculate an interval on its selected cooling branch."""
    history = rosenthal_point_source_3d(x.thermal_history)
    thermal_digest = canonical_digest(x.thermal_history.model_dump(mode="json"))
    if history.status != "computed":
        return Calculation(
            status=history.status,
            values={
                "thermal_history_sha256": thermal_digest,
                "rosenthal_request_sha256": thermal_digest,
                "thermal_history_status": history.status,
                "thermal_history_values": history.values,
            },
            notes=history.notes,
        )
    from .thermohistory import CoolingInterval, cooling_interval

    interval_request = CoolingInterval(
        time_s=list(x.thermal_history.time_s),
        temperature_K=history.values["temperature_K"],
        upper_temperature_K=x.upper_temperature_K,
        lower_temperature_K=x.lower_temperature_K,
        cooling_branch_start_index=x.cooling_branch_start_index,
        cooling_branch_end_index=x.cooling_branch_end_index,
    )
    interval = cooling_interval(interval_request)
    return Calculation(
        status=interval.status,
        values={
            "thermal_history_sha256": thermal_digest,
            "rosenthal_request_sha256": thermal_digest,
            "cooling_interval_request_sha256": canonical_digest(interval_request.model_dump(mode="json")),
            "thermal_history_status": history.status,
            "thermal_history_time_s": list(x.thermal_history.time_s),
            "thermal_history_temperature_K": history.values["temperature_K"],
            **interval.values,
        },
        notes=(
            "Thermal history is evaluated from a steady moving-source field at caller-provided fixed-point coordinates.",
            "Cooling interval uses piecewise-linear interpolation on the caller-selected branch; finite weld starts and procedure qualification are excluded.",
        )
        + interval.notes,
    )


def arc_energy(x: ArcEnergy) -> Calculation:
    gross = x.voltage_V * x.current_A / x.travel_speed_m_s
    return Calculation(values=dict(arc_energy_J_m=gross, net_heat_input_J_m=x.efficiency * gross))


class WaveformEnergy(Contract):
    time_s: list[Nonnegative] = Field(min_length=2)
    voltage_V: list[float] = Field(min_length=2)
    current_A: list[float] = Field(min_length=2)
    travel_distance_m: Positive
    efficiency: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def align(self):
        if len({len(self.time_s), len(self.voltage_V), len(self.current_A)}) != 1:
            raise ValueError("waveform vectors must align")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("waveform clock must increase")
        if any(u * i < 0 for u, i in zip(self.voltage_V, self.current_A, strict=True)):
            raise ValueError("voltage/current sign convention must produce nonnegative arc power")
        return self


def waveform_energy(x: WaveformEnergy) -> Calculation:
    import numpy as np

    energy = float(np.trapezoid(np.asarray(x.voltage_V) * np.asarray(x.current_A), x.time_s))
    return Calculation(
        values=dict(arc_energy_J=energy, net_heat_input_J_m=x.efficiency * energy / x.travel_distance_m)
    )


class SteelChemistry(Contract):
    C: Nonnegative
    Mn: Nonnegative
    Cr: Nonnegative
    Mo: Nonnegative
    V: Nonnegative
    Ni: Nonnegative
    Cu: Nonnegative
    Si: Nonnegative
    B: Nonnegative

    @model_validator(mode="after")
    def percent(self):
        if sum(self.model_dump().values()) > 100:
            raise ValueError("chemistry is in mass percent and cannot exceed 100")
        return self


def carbon_equivalents(x: SteelChemistry) -> Calculation:
    return Calculation(
        values=dict(
            CE_IIW=x.C + x.Mn / 6 + (x.Cr + x.Mo + x.V) / 5 + (x.Ni + x.Cu) / 15,
            Pcm=x.C + x.Si / 30 + (x.Mn + x.Cu + x.Cr) / 20 + x.Ni / 60 + x.Mo / 15 + x.V / 10 + 5 * x.B,
        )
    )


class BoltPreload(Contract):
    torque_N_m: Nonnegative
    nominal_diameter_m: Positive
    nut_factor: Positive
    tensile_area_m2: Positive


def bolt_preload(x: BoltPreload) -> Calculation:
    force = x.torque_N_m / (x.nut_factor * x.nominal_diameter_m)
    return Calculation(values=dict(preload_N=force, nominal_tensile_stress_Pa=force / x.tensile_area_m2))


class BendStrain(Contract):
    outside_diameter_m: Positive
    centerline_bend_radius_m: Positive


class MeasuredPipeOvality(Contract):
    maximum_diameter_m: Positive
    minimum_diameter_m: Positive
    reference_basis: Literal["nominal", "mean_measured"]
    nominal_diameter_m: Positive | None = None

    @model_validator(mode="after")
    def validate_diameter_basis(self):
        if self.maximum_diameter_m < self.minimum_diameter_m:
            raise ValueError("maximum measured diameter must not be below minimum")
        if (self.reference_basis == "nominal") != (self.nominal_diameter_m is not None):
            raise ValueError("only nominal-basis ovality requires an explicit nominal diameter")
        return self


def measured_pipe_ovality(x: MeasuredPipeOvality) -> Calculation:
    reference = (
        x.nominal_diameter_m
        if x.reference_basis == "nominal"
        else (x.maximum_diameter_m + x.minimum_diameter_m) / 2.0
    )
    difference = x.maximum_diameter_m - x.minimum_diameter_m
    ratio = difference / reference
    return Calculation(
        values={
            "diameter_range_m": difference,
            "reference_diameter_m": reference,
            "ovality_fraction": ratio,
            "ovality_percent": ratio * 100.0,
            "reference_basis": x.reference_basis,
        },
        notes=("Measured geometry descriptor only; tolerance acceptance uses a separate caller rule.",),
    )


def bend_strain(x: BendStrain) -> Calculation:
    if x.centerline_bend_radius_m <= x.outside_diameter_m / 2:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Bend radius is incompatible with this kinematic estimate.",),
        )
    return Calculation(values={"outer_fiber_strain": x.outside_diameter_m / (2 * x.centerline_bend_radius_m)})


class CoatingCoverage(Contract):
    area_m2: Positive
    dry_thickness_m: Positive
    volume_solids_fraction: float = Field(gt=0, le=1)
    transfer_efficiency: float = Field(gt=0, le=1)


def coating_coverage(x: CoatingCoverage) -> Calculation:
    dry_volume = x.area_m2 * x.dry_thickness_m
    wet_thickness = x.dry_thickness_m / x.volume_solids_fraction
    wet_volume = dry_volume / x.volume_solids_fraction / x.transfer_efficiency
    if not all(math.isfinite(value) and value > 0.0 for value in (dry_volume, wet_thickness, wet_volume)):
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("Coating volume or thickness exceeds positive finite numeric support.",),
        )
    return Calculation(
        values=dict(
            dry_volume_m3=dry_volume,
            wet_thickness_m=wet_thickness,
            required_wet_volume_m3=wet_volume,
        )
    )


class ConductionLayers(Contract):
    thickness_m: list[Positive] = Field(min_length=1)
    conductivity_W_m_K: list[Positive] = Field(min_length=1)
    area_m2: Positive
    temperature_difference_K: float

    @model_validator(mode="after")
    def align(self):
        if len(self.thickness_m) != len(self.conductivity_W_m_K):
            raise ValueError("one conductivity per layer required")
        return self


def conduction_layers(x: ConductionLayers) -> Calculation:
    resistance = sum(t / k / x.area_m2 for t, k in zip(x.thickness_m, x.conductivity_W_m_K, strict=True))
    return Calculation(
        values=dict(thermal_resistance_K_W=resistance, heat_rate_W=x.temperature_difference_K / resistance)
    )


class WinterizationInventory(Contract):
    case_id: str = Field(min_length=1)
    fluid_id: str = Field(min_length=1)
    pressure_Pa_abs: Positive
    inventory_mass_kg: Positive
    initial_bulk_temperature_K: Positive
    minimum_allowable_temperature_K: Positive
    time_s: list[Nonnegative] = Field(min_length=2)
    interval_ambient_temperature_K: list[Positive] = Field(min_length=1)
    interval_heat_loss_conductance_W_K: list[Nonnegative] = Field(min_length=1)
    interval_heat_tracing_power_W: list[Nonnegative] = Field(min_length=1)
    interval_effective_isobaric_heat_capacity_J_kg_K: list[Positive] = Field(min_length=1)
    property_evaluation_temperature_K: list[Positive] = Field(min_length=1)
    property_phase: list[str] = Field(min_length=1)
    property_provider_id: str = Field(min_length=1)
    property_provider_version: str = Field(min_length=1)
    property_history_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    inventory_and_mixing_reviewed: bool
    conductance_history_reviewed: bool
    heat_tracing_history_reviewed: bool
    property_states_reviewed: bool
    minimum_temperature_reviewed: bool

    @model_validator(mode="after")
    def align_and_bound(self):
        interval_count = len(self.time_s) - 1
        interval_vectors = (
            self.interval_ambient_temperature_K,
            self.interval_heat_loss_conductance_W_K,
            self.interval_heat_tracing_power_W,
            self.interval_effective_isobaric_heat_capacity_J_kg_K,
            self.property_evaluation_temperature_K,
            self.property_phase,
        )
        if any(len(values) != interval_count for values in interval_vectors):
            raise ValueError("one ambient, conductance, heat input and property state per interval required")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("winterization clock must increase")
        if any(not phase.strip() for phase in self.property_phase):
            raise ValueError("each property state requires a phase label")
        return self


def winterization_inventory(x: WinterizationInventory) -> Calculation:
    reviews = (
        x.inventory_and_mixing_reviewed,
        x.conductance_history_reviewed,
        x.heat_tracing_history_reviewed,
        x.property_states_reviewed,
        x.minimum_temperature_reviewed,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={"case_id": x.case_id, "fluid_id": x.fluid_id},
            notes=("Inventory, heat-transfer, property-state and temperature-limit reviews are required.",),
        )

    temperatures = [x.initial_bulk_temperature_K]
    interval_environment_heat_J = []
    interval_trace_heat_J = []
    first_crossing_s = (
        x.time_s[0] if x.initial_bulk_temperature_K <= x.minimum_allowable_temperature_K else None
    )
    cumulative_environment_heat = 0.0
    cumulative_trace_heat = 0.0
    minimum_temperature = x.initial_bulk_temperature_K
    for index, (start, end) in enumerate(zip(x.time_s, x.time_s[1:], strict=False)):
        duration = end - start
        temperature = temperatures[-1]
        ambient = x.interval_ambient_temperature_K[index]
        conductance = x.interval_heat_loss_conductance_W_K[index]
        trace_power = x.interval_heat_tracing_power_W[index]
        heat_capacity = x.interval_effective_isobaric_heat_capacity_J_kg_K[index]
        thermal_capacity = x.inventory_mass_kg * heat_capacity
        if not math.isfinite(thermal_capacity) or thermal_capacity <= 0:
            return Calculation(
                status="out_of_scope",
                values={},
                notes=("Inventory thermal capacity exceeds positive finite numeric support.",),
            )
        if conductance > 0:
            equilibrium = ambient + trace_power / conductance
            exponent = conductance / thermal_capacity * duration
            if not math.isfinite(equilibrium) or not math.isfinite(exponent):
                return Calculation(
                    status="out_of_scope",
                    values={},
                    notes=("Interval equilibrium or decay scale exceeds finite numeric support.",),
                )
            # The increment form retains small changes without subtracting two
            # nearly equal exponential terms.
            next_temperature = temperature + (equilibrium - temperature) * (-math.expm1(-exponent))
        else:
            equilibrium = None
            next_temperature = temperature + trace_power * duration / thermal_capacity

        if (
            first_crossing_s is None
            and temperature > x.minimum_allowable_temperature_K
            and next_temperature <= x.minimum_allowable_temperature_K
            and conductance > 0
        ):
            ratio = (x.minimum_allowable_temperature_K - equilibrium) / (temperature - equilibrium)
            if 0 < ratio <= 1:
                first_crossing_s = start - thermal_capacity / conductance * math.log(ratio)

        trace_heat = trace_power * duration
        stored_heat_change = thermal_capacity * (next_temperature - temperature)
        environment_heat = trace_heat - stored_heat_change
        cumulative_trace_heat += trace_heat
        cumulative_environment_heat += environment_heat
        if (
            not all(
                math.isfinite(value)
                for value in (
                    next_temperature,
                    trace_heat,
                    stored_heat_change,
                    environment_heat,
                    cumulative_trace_heat,
                    cumulative_environment_heat,
                )
            )
            or next_temperature <= 0
        ):
            return Calculation(
                status="out_of_scope",
                values={},
                notes=("Interval temperature or energy exceeds finite numeric support.",),
            )
        interval_trace_heat_J.append(trace_heat)
        interval_environment_heat_J.append(environment_heat)
        temperatures.append(next_temperature)
        minimum_temperature = min(minimum_temperature, next_temperature)

    return Calculation(
        values={
            "case_id": x.case_id,
            "fluid_id": x.fluid_id,
            "bulk_temperature_K": temperatures,
            "temperature_margin_K": [
                temperature - x.minimum_allowable_temperature_K for temperature in temperatures
            ],
            "minimum_bulk_temperature_K": minimum_temperature,
            "minimum_temperature_margin_K": minimum_temperature - x.minimum_allowable_temperature_K,
            "first_minimum_temperature_crossing_s": first_crossing_s,
            "interval_heat_tracing_energy_J": interval_trace_heat_J,
            "interval_environment_heat_loss_J": interval_environment_heat_J,
            "cumulative_heat_tracing_energy_J": cumulative_trace_heat,
            "cumulative_environment_heat_loss_J": cumulative_environment_heat,
        },
        notes=(
            "Negative environment heat loss denotes net heat gain from the environment.",
            "A threshold crossing is a screening result, not a prediction of solid formation or acceptance.",
            "An initially sub-limit inventory is flagged at the initial clock; heating does not erase that excursion.",
        ),
    )


class PittingResistanceIndex(Contract):
    chromium_mass_percent: float = Field(ge=0, le=100)
    molybdenum_mass_percent: float = Field(ge=0, le=100)
    nitrogen_mass_percent: float = Field(ge=0, le=100)
    molybdenum_coefficient: Positive
    nitrogen_coefficient: Positive

    @model_validator(mode="after")
    def composition(self):
        if self.chromium_mass_percent + self.molybdenum_mass_percent + self.nitrogen_mass_percent > 100:
            raise ValueError("declared elemental mass percentages cannot exceed 100")
        return self


def pitting_index(x: PittingResistanceIndex) -> Calculation:
    return Calculation(
        values={
            "composition_index": x.chromium_mass_percent
            + x.molybdenum_coefficient * x.molybdenum_mass_percent
            + x.nitrogen_coefficient * x.nitrogen_mass_percent
        }
    )


def specifications():
    return [
        ModelSpec(
            "welding.rosenthal_3d_point_source_temperature",
            RosenthalPointSource3D,
            rosenthal_point_source_3d,
            {
                "thermal_diffusivity_m2_s": "m^2/s",
                "temperature_K": "K",
                "temperature_rise_K": "K",
                "query_count": "1",
            },
            (
                "Steady three-dimensional moving point source in a semi-infinite homogeneous solid with constant properties.",
                "Neglects phase change, latent heat, convection, radiation, finite boundaries and weld-pool flow; not a cooling-time or acceptance model.",
            ),
            ("rosenthal_welding_heat_source",),
        ),
        ModelSpec(
            "welding.rosenthal_cooling_interval",
            RosenthalCoolingIntervalLink,
            evaluate_rosenthal_cooling_interval,
            {
                "thermal_history_sha256": "1",
                "rosenthal_request_sha256": "1",
                "cooling_interval_request_sha256": "1",
                "input_history_sha256": "1",
                "thermal_history_time_s": "s",
                "thermal_history_temperature_K": "K",
                "upper_crossing_s": "s",
                "lower_crossing_s": "s",
                "cooling_interval_s": "s",
                "maximum_selected_sample_spacing_s": "s",
                "upper_crossing_available": "1",
                "lower_crossing_available": "1",
                "upper_crossing_bracket_sample_indices": "1",
                "lower_crossing_bracket_sample_indices": "1",
                "selected_cooling_branch_sample_indices_inclusive": "1",
                "selected_branch_sha256": "1",
            },
            (
                "Compose a fixed-point sampled Rosenthal moving-source history with caller-selected cooling-branch interval extraction.",
                "The quasi-steady semi-infinite constant-property history is not a qualified thermal-cycle or t8/5 prediction.",
            ),
            ("rosenthal_welding_heat_source", "piecewise_linear_history"),
        ),
        ModelSpec(
            "welding.arc_energy",
            ArcEnergy,
            arc_energy,
            {"arc_energy_J_m": "J/m", "net_heat_input_J_m": "J/m"},
            ("Constant arc voltage/current; thermal efficiency is explicit and procedure-specific.",),
            ("twi_arc_measurement",),
        ),
        ModelSpec(
            "welding.measured_energy_per_length",
            MeasuredWeldEnergy,
            measured_weld_energy,
            {"source_energy_per_length_J_m": "J/m", "net_heat_input_J_m": "J/m"},
            (
                "Measured source energy and deposited length cover the same observation interval.",
                "Caller efficiency distinguishes source energy from absorbed weld heat; no procedure acceptance is inferred.",
            ),
            ("declared_energy_or_power_per_weld_length",),
        ),
        ModelSpec(
            "welding.power_travel_energy",
            WeldPowerTravel,
            weld_power_travel,
            {"source_energy_per_length_J_m": "J/m", "net_heat_input_J_m": "J/m"},
            (
                "Source power and travel speed are constant over the declared weld interval.",
                "Caller efficiency is process-specific; the result does not predict thermal history or weld quality.",
            ),
            ("declared_energy_or_power_per_weld_length",),
        ),
        ModelSpec(
            "welding.waveform_energy",
            WaveformEnergy,
            waveform_energy,
            {"arc_energy_J": "J", "net_heat_input_J_m": "J/m"},
            ("Time-aligned sampled arc voltage/current; resolution must resolve the actual waveform.",),
            ("twi_arc_measurement",),
        ),
        ModelSpec(
            "welding.carbon_equivalents",
            SteelChemistry,
            carbon_equivalents,
            {"CE_IIW": "mass percent", "Pcm": "mass percent"},
            ("All elements are mass percent; indices do not prescribe preheat or demonstrate weldability.",),
            ("twi_carbon_equivalent",),
        ),
        ModelSpec(
            "fabrication.bolt_preload",
            BoltPreload,
            bolt_preload,
            {"preload_N": "N", "nominal_tensile_stress_Pa": "Pa"},
            (
                "Approximate torque-factor relation; friction scatter and joint stiffness require separate treatment.",
            ),
            ("bolt_torque_equilibrium",),
        ),
        ModelSpec(
            "fabrication.bend_strain",
            BendStrain,
            bend_strain,
            {"outer_fiber_strain": "1"},
            (
                "Kinematic bending estimate; ovalization, thinning and plastic-neutral-axis movement excluded.",
            ),
            ("beam_kinematics",),
        ),
        ModelSpec(
            "fabrication.measured_pipe_ovality",
            MeasuredPipeOvality,
            measured_pipe_ovality,
            {
                "diameter_range_m": "m",
                "reference_diameter_m": "m",
                "ovality_fraction": "1",
                "ovality_percent": "%",
            },
            (
                "Caller selects nominal or measured-mean reference diameter; no tolerance or sampling rule is inferred.",
            ),
            ("declared_reference_normalized_diameter_range",),
        ),
        ModelSpec(
            "protection.coating_coverage",
            CoatingCoverage,
            coating_coverage,
            {"dry_volume_m3": "m^3", "wet_thickness_m": "m", "required_wet_volume_m3": "m^3"},
            ("Uniform deposited film; solids fraction and transfer losses are declared.",),
            ("volume_conservation",),
            version="1.0.1",
        ),
        ModelSpec(
            "thermal.planar_layers",
            ConductionLayers,
            conduction_layers,
            {"thermal_resistance_K_W": "K/W", "heat_rate_W": "W"},
            ("Steady planar one-dimensional conduction with constant per-layer conductivity.",),
            ("fourier_conduction",),
        ),
        ModelSpec(
            "fabrication.winterization_inventory",
            WinterizationInventory,
            winterization_inventory,
            {
                "case_id": "1",
                "fluid_id": "1",
                "bulk_temperature_K": "K",
                "temperature_margin_K": "K",
                "minimum_bulk_temperature_K": "K",
                "minimum_temperature_margin_K": "K",
                "first_minimum_temperature_crossing_s": "s",
                "interval_heat_tracing_energy_J": "J",
                "interval_environment_heat_loss_J": "J",
                "cumulative_heat_tracing_energy_J": "J",
                "cumulative_environment_heat_loss_J": "J",
            },
            (
                "Each interval uses constant ambient temperature, conductance, trace power and effective isobaric heat capacity.",
                "The inventory is spatially uniform and well mixed at constant absolute pressure with no phase change, flow or reaction.",
                "The minimum allowable temperature is caller-reviewed; this model does not infer a freezing point or code acceptance.",
            ),
            ("lumped_heat_balance", "coolprop_high_level"),
            version="1.1.0",
        ),
        ModelSpec(
            "materials.pitting_composition_index",
            PittingResistanceIndex,
            pitting_index,
            {"composition_index": "index"},
            (
                "User-declared composition coefficients; index is not a corrosion rate or material acceptance rule.",
            ),
            ("declared_composition_index",),
        ),
    ]
