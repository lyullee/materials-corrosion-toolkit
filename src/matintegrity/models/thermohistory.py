"""Heat balances and recorded thermal histories with explicit boundary assumptions."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class CylindricalLayers(Contract):
    radii_m: list[Positive] = Field(min_length=2)
    conductivity_W_m_K: list[Positive] = Field(min_length=1)
    length_m: Positive
    inner_fluid_temperature_K: Positive
    ambient_temperature_K: Positive
    radiative_environment_temperature_K: Positive
    inner_convection_W_m2_K: Positive
    outer_convection_W_m2_K: Positive
    outer_emissivity: Fraction

    @model_validator(mode="after")
    def layers(self):
        if len(self.radii_m) != len(self.conductivity_W_m_K) + 1:
            raise ValueError("one more radius than material layers is required")
        if any(b <= a for a, b in zip(self.radii_m, self.radii_m[1:], strict=False)):
            raise ValueError("interface radii must strictly increase")
        return self


def cylindrical_layers(x: CylindricalLayers) -> Calculation:
    from scipy.optimize import brentq

    areas = [2 * math.pi * r * x.length_m for r in x.radii_m]
    resistances = [
        math.log1p((b - a) / a) / (2 * math.pi * x.length_m * k)
        for a, b, k in zip(x.radii_m, x.radii_m[1:], x.conductivity_W_m_K, strict=False)
    ]
    internal = 1 / (x.inner_convection_W_m2_K * areas[0]) + sum(resistances)
    sigma = 5.670374419e-8

    def external(surface):
        convection = x.outer_convection_W_m2_K * areas[-1] * (surface - x.ambient_temperature_K)
        radiation = (
            x.outer_emissivity
            * sigma
            * areas[-1]
            * (surface - x.radiative_environment_temperature_K)
            * (surface + x.radiative_environment_temperature_K)
            * (surface**2 + x.radiative_environment_temperature_K**2)
        )
        return convection + radiation

    bounds = [x.inner_fluid_temperature_K, x.ambient_temperature_K, x.radiative_environment_temperature_K]
    low, high = min(bounds), max(bounds)
    surface = (
        low
        if low == high
        else brentq(
            lambda t: (x.inner_fluid_temperature_K - t) / internal - external(t), low, high, xtol=1e-9
        )
    )
    heat = (x.inner_fluid_temperature_K - surface) / internal
    first = x.inner_fluid_temperature_K - heat / (x.inner_convection_W_m2_K * areas[0])
    temperatures = [first]
    for resistance in resistances:
        temperatures.append(temperatures[-1] - heat * resistance)
    return Calculation(
        values=dict(
            heat_rate_outward_W=heat,
            interface_temperatures_K=temperatures,
            conduction_resistances_K_W=resistances,
            outer_balance_residual_W=heat - external(surface),
        ),
        notes=(
            "Steady constant-conductivity radial layers; end effects, contact resistance, moisture and multidimensional bridges excluded.",
        ),
    )


class LumpedTemperature(Contract):
    initial_temperature_K: Positive
    ambient_temperature_K: Positive
    heat_capacity_J_K: Positive
    surface_area_m2: Positive
    convection_W_m2_K: Positive
    solid_conductivity_W_m_K: Positive
    characteristic_length_m: Positive
    maximum_declared_biot: Positive
    exposure_s: Nonnegative


def lumped_temperature(x: LumpedTemperature) -> Calculation:
    biot = x.convection_W_m2_K * x.characteristic_length_m / x.solid_conductivity_W_m_K
    tau = x.heat_capacity_J_K / (x.convection_W_m2_K * x.surface_area_m2)
    return Calculation(
        values=dict(
            biot_number=biot,
            time_constant_s=tau,
            temperature_K=x.ambient_temperature_K
            + (x.initial_temperature_K - x.ambient_temperature_K) * math.exp(-x.exposure_s / tau),
        ),
        status="computed" if biot <= x.maximum_declared_biot else "out_of_scope",
        notes=(
            "One uniform solid temperature, constant convection and heat capacity; radiation and phase change excluded.",
        ),
    )


class HeatTreatmentHistory(Contract):
    time_s: list[Nonnegative] = Field(min_length=2)
    sensor_temperature_K: list[list[Positive]] = Field(min_length=1)
    minimum_hold_temperature_K: Positive
    maximum_hold_temperature_K: Positive

    @model_validator(mode="after")
    def align(self):
        if self.maximum_hold_temperature_K < self.minimum_hold_temperature_K:
            raise ValueError("hold band is reversed")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("thermal-history clock must strictly increase")
        if any(len(row) != len(self.time_s) for row in self.sensor_temperature_K):
            raise ValueError("each sensor needs a complete common-clock temperature vector")
        return self


def _within_interval(start, end, low, high):
    if start == end:
        return (0.0, 1.0) if low <= start <= high else None
    a, b = sorted(((low - start) / (end - start), (high - start) / (end - start)))
    a, b = max(0.0, a), min(1.0, b)
    return (a, b) if b >= a else None


def heat_treatment_history(x: HeatTreatmentHistory) -> Calculation:
    intervals = []
    ramps = []
    spreads = []
    for i, (start, end) in enumerate(zip(x.time_s, x.time_s[1:], strict=False)):
        dt = end - start
        fractions = []
        for sensor in x.sensor_temperature_K:
            ramps.append((sensor[i + 1] - sensor[i]) / dt)
            fractions.append(
                _within_interval(
                    sensor[i], sensor[i + 1], x.minimum_hold_temperature_K, x.maximum_hold_temperature_K
                )
            )
        if all(f is not None for f in fractions):
            low = max(f[0] for f in fractions)
            high = min(f[1] for f in fractions)
            if high > low:
                # Reuse exact recorded endpoints. A fixed time tolerance can
                # erase a real out-of-band interval on a compressed clock.
                a = start if low == 0.0 else start + dt * low
                b = end if high == 1.0 else start + dt * high
                if intervals and intervals[-1][1] == a:
                    intervals[-1][1] = b
                else:
                    intervals.append([a, b])
    for i in range(len(x.time_s)):
        at_time = [sensor[i] for sensor in x.sensor_temperature_K]
        spreads.append(max(at_time) - min(at_time))
    return Calculation(
        values=dict(
            simultaneous_hold_intervals_s=intervals,
            total_simultaneous_hold_s=sum(b - a for a, b in intervals),
            longest_continuous_hold_s=max((b - a for a, b in intervals), default=0.0),
            maximum_heating_rate_K_s=max(0.0, max(ramps)),
            maximum_cooling_rate_K_s=max(0.0, -min(ramps)),
            maximum_sensor_spread_K=max(spreads),
        ),
        notes=(
            "Piecewise-linear interpolation only between recorded samples; gaps require upstream segmentation. Only exactly touching hold windows are joined. Hold compliance needs separate procedure-specific requirements.",
        ),
    )


class CoolingInterval(Contract):
    time_s: list[Nonnegative] = Field(min_length=2)
    temperature_K: list[Positive] = Field(min_length=2)
    upper_temperature_K: Positive
    lower_temperature_K: Positive
    cooling_branch_start_index: int = Field(default=0, ge=0)
    cooling_branch_end_index: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def monotonic_selected_branch(self):
        if (
            len(self.time_s) != len(self.temperature_K)
            or self.lower_temperature_K >= self.upper_temperature_K
        ):
            raise ValueError("aligned thermal history and ordered target temperatures required")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("time must strictly increase")
        end = len(self.time_s) - 1 if self.cooling_branch_end_index is None else self.cooling_branch_end_index
        if self.cooling_branch_start_index >= end or end >= len(self.time_s):
            raise ValueError("cooling branch indices must select at least two in-range samples")
        selected = self.temperature_K[self.cooling_branch_start_index : end + 1]
        if any(b > a for a, b in zip(selected, selected[1:], strict=False)):
            raise ValueError("the explicitly selected cooling branch must be nonincreasing")
        return self


COOLING_INTERVAL_RESULT_UNITS = {
    "upper_crossing_s": "s",
    "lower_crossing_s": "s",
    "cooling_interval_s": "s",
    "input_history_sha256": "1",
    "selected_branch_sha256": "1",
    "crossing_method": "1",
    "upper_crossing_available": "1",
    "lower_crossing_available": "1",
    "upper_crossing_bracket_sample_indices": "1",
    "lower_crossing_bracket_sample_indices": "1",
    "selected_cooling_branch_sample_indices_inclusive": "1",
    "maximum_selected_sample_spacing_s": "s",
}


def cooling_interval(x: CoolingInterval) -> Calculation:
    end = len(x.time_s) - 1 if x.cooling_branch_end_index is None else x.cooling_branch_end_index
    selected_history = {
        "time_s": x.time_s[x.cooling_branch_start_index : end + 1],
        "temperature_K": x.temperature_K[x.cooling_branch_start_index : end + 1],
    }
    provenance = {
        "input_history_sha256": canonical_digest({"time_s": x.time_s, "temperature_K": x.temperature_K}),
        "selected_branch_sha256": canonical_digest(selected_history),
        "crossing_method": "piecewise_linear_on_caller_selected_nonincreasing_branch",
    }

    def crossing(target):
        for i in range(x.cooling_branch_start_index, end):
            a, b = x.temperature_K[i], x.temperature_K[i + 1]
            if a >= target >= b:
                time = (
                    x.time_s[i]
                    if a == b
                    else x.time_s[i] + (a - target) / (a - b) * (x.time_s[i + 1] - x.time_s[i])
                )
                return time, (i, i + 1)
        return None

    upper, lower = crossing(x.upper_temperature_K), crossing(x.lower_temperature_K)
    if upper is None or lower is None:
        return Calculation(
            status="needs_data",
            values={
                **provenance,
                "upper_crossing_available": upper is not None,
                "lower_crossing_available": lower is not None,
                "selected_cooling_branch_sample_indices_inclusive": [x.cooling_branch_start_index, end],
            },
            notes=("Both target crossings must lie on the explicitly selected recorded cooling branch.",),
        )
    maximum_spacing = max(x.time_s[i + 1] - x.time_s[i] for i in range(x.cooling_branch_start_index, end))
    return Calculation(
        values=dict(
            **provenance,
            upper_crossing_s=upper[0],
            lower_crossing_s=lower[0],
            cooling_interval_s=lower[0] - upper[0],
            upper_crossing_bracket_sample_indices=list(upper[1]),
            lower_crossing_bracket_sample_indices=list(lower[1]),
            selected_cooling_branch_sample_indices_inclusive=[x.cooling_branch_start_index, end],
            maximum_selected_sample_spacing_s=maximum_spacing,
        ),
        notes=(
            "Crossings use piecewise-linear interpolation on the caller-selected nonincreasing branch.",
            "Sample spacing is reported as a diagnostic; interpolation accuracy and procedure suitability are not established.",
        ),
    )


class CoolingIntervalBranch(Contract):
    branch_id: str = Field(min_length=1)
    upper_temperature_K: Positive
    lower_temperature_K: Positive
    start_index: int = Field(default=0, ge=0)
    end_index: int | None = Field(default=None, ge=1)


class CoolingIntervalBatch(Contract):
    """Evaluate multiple caller-selected cooling branches on one preserved history."""

    time_s: list[Nonnegative] = Field(min_length=2)
    temperature_K: list[Positive] = Field(min_length=2)
    branches: tuple[CoolingIntervalBranch, ...] = Field(min_length=1)
    record_id: str | None = Field(default=None, min_length=1)
    sensor_id: str | None = Field(default=None, min_length=1)
    location_id: str | None = Field(default=None, min_length=1)
    provider_file_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def validate_branches(self):
        if len(self.time_s) != len(self.temperature_K):
            raise ValueError("batch time and temperature arrays must align")
        if (self.sensor_id is None) != (self.location_id is None):
            raise ValueError("sensor and measurement location identities must be supplied together")
        evidence_ids = [item.source_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("batch evidence source IDs must be unique")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("batch history times must strictly increase")
        ids = [branch.branch_id for branch in self.branches]
        if len(ids) != len(set(ids)):
            raise ValueError("cooling branch IDs must be unique")
        for branch in self.branches:
            CoolingInterval(
                time_s=self.time_s,
                temperature_K=self.temperature_K,
                upper_temperature_K=branch.upper_temperature_K,
                lower_temperature_K=branch.lower_temperature_K,
                cooling_branch_start_index=branch.start_index,
                cooling_branch_end_index=branch.end_index,
            )
        return self


def cooling_interval_batch(x: CoolingIntervalBatch) -> Calculation:
    history_digest = canonical_digest({"time_s": x.time_s, "temperature_K": x.temperature_K})
    rows = []
    for branch in x.branches:
        result = cooling_interval(
            CoolingInterval(
                time_s=x.time_s,
                temperature_K=x.temperature_K,
                upper_temperature_K=branch.upper_temperature_K,
                lower_temperature_K=branch.lower_temperature_K,
                cooling_branch_start_index=branch.start_index,
                cooling_branch_end_index=branch.end_index,
            )
        )
        rows.append(
            {
                "branch_id": branch.branch_id,
                "branch_input_sha256": canonical_digest(branch.model_dump(mode="json")),
                "status": result.status,
                "values": result.values,
                "units": dict(COOLING_INTERVAL_RESULT_UNITS),
                "notes": list(result.notes),
            }
        )
    statuses = {row["status"] for row in rows}
    if statuses == {"computed"}:
        status = "computed"
    elif "out_of_scope" in statuses:
        status = "out_of_scope"
    else:
        status = "needs_data"
    return Calculation(
        status=status,
        values={
            "input_sha256": canonical_digest(x.model_dump(mode="json")),
            "sample_arrays_sha256": history_digest,
            "record_id": x.record_id,
            "sensor_id": x.sensor_id,
            "location_id": x.location_id,
            "provider_file_sha256": x.provider_file_sha256,
            "evidence": [item.model_dump(mode="json") for item in x.evidence],
            "branch_count": len(rows),
            "branches": rows,
            "branch_result_units": dict(COOLING_INTERVAL_RESULT_UNITS),
        },
        notes=(
            "Each branch is evaluated independently on the same immutable caller-supplied time/temperature history.",
            "An incomplete crossing in any branch makes the batch status needs_data; all branch-level results remain available.",
        ),
    )


class CoolingIntervalSensorTrace(Contract):
    sensor_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    temperature_K: tuple[Positive, ...] = Field(min_length=2)


class CoolingIntervalSensorBranch(Contract):
    branch_id: str = Field(min_length=1)
    sensor_id: str = Field(min_length=1)
    upper_temperature_K: Positive
    lower_temperature_K: Positive
    start_index: int = Field(default=0, ge=0)
    end_index: int | None = Field(default=None, ge=1)


class CoolingIntervalSensorBatch(Contract):
    """Evaluate explicit sensor-local branches on a shared clock without cross-sensor interpolation."""

    time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    sensor_traces: tuple[CoolingIntervalSensorTrace, ...] = Field(min_length=1)
    branches: tuple[CoolingIntervalSensorBranch, ...] = Field(min_length=1)
    record_id: str | None = Field(default=None, min_length=1)
    provider_file_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def validate_sensor_branches(self):
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("shared sensor-history clock must strictly increase")
        sensor_ids = [trace.sensor_id for trace in self.sensor_traces]
        if len(sensor_ids) != len(set(sensor_ids)):
            raise ValueError("sensor trace IDs must be unique")
        sensors = {trace.sensor_id: trace for trace in self.sensor_traces}
        if any(len(trace.temperature_K) != len(self.time_s) for trace in self.sensor_traces):
            raise ValueError("every sensor trace must align exactly with the shared clock")
        branch_ids = [branch.branch_id for branch in self.branches]
        if len(branch_ids) != len(set(branch_ids)):
            raise ValueError("sensor cooling branch IDs must be unique")
        evidence_ids = [item.source_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("sensor batch evidence source IDs must be unique")
        for branch in self.branches:
            if branch.sensor_id not in sensors:
                raise ValueError(f"cooling branch references unknown sensor {branch.sensor_id}")
            CoolingInterval(
                time_s=list(self.time_s),
                temperature_K=list(sensors[branch.sensor_id].temperature_K),
                upper_temperature_K=branch.upper_temperature_K,
                lower_temperature_K=branch.lower_temperature_K,
                cooling_branch_start_index=branch.start_index,
                cooling_branch_end_index=branch.end_index,
            )
        return self


def cooling_interval_sensor_batch(x: CoolingIntervalSensorBatch) -> Calculation:
    traces = {trace.sensor_id: trace for trace in x.sensor_traces}
    history_digest = canonical_digest(
        {
            "time_s": x.time_s,
            "sensor_traces": [trace.model_dump(mode="json") for trace in x.sensor_traces],
        }
    )
    rows = []
    for branch in x.branches:
        trace = traces[branch.sensor_id]
        result = cooling_interval(
            CoolingInterval(
                time_s=list(x.time_s),
                temperature_K=list(trace.temperature_K),
                upper_temperature_K=branch.upper_temperature_K,
                lower_temperature_K=branch.lower_temperature_K,
                cooling_branch_start_index=branch.start_index,
                cooling_branch_end_index=branch.end_index,
            )
        )
        rows.append(
            {
                "branch_id": branch.branch_id,
                "sensor_id": trace.sensor_id,
                "location_id": trace.location_id,
                "branch_input_sha256": canonical_digest(branch.model_dump(mode="json")),
                "sensor_trace_sha256": canonical_digest(trace.model_dump(mode="json")),
                "status": result.status,
                "values": result.values,
                "units": dict(COOLING_INTERVAL_RESULT_UNITS),
                "notes": list(result.notes),
            }
        )
    statuses = {row["status"] for row in rows}
    status = (
        "computed"
        if statuses == {"computed"}
        else "out_of_scope"
        if "out_of_scope" in statuses
        else "needs_data"
    )
    return Calculation(
        status=status,
        values={
            "input_sha256": canonical_digest(x.model_dump(mode="json")),
            "sample_arrays_sha256": history_digest,
            "record_id": x.record_id,
            "provider_file_sha256": x.provider_file_sha256,
            "evidence": [item.model_dump(mode="json") for item in x.evidence],
            "sensor_count": len(x.sensor_traces),
            "branch_count": len(rows),
            "branches": rows,
            "branch_result_units": dict(COOLING_INTERVAL_RESULT_UNITS),
        },
        notes=(
            "Each declared branch uses only its named sensor trace on the shared clock; no cross-sensor temperature interpolation is performed.",
            "An incomplete branch remains visible and prevents a computed batch status.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "thermal.cylindrical_layers",
            CylindricalLayers,
            cylindrical_layers,
            {
                "heat_rate_outward_W": "W",
                "interface_temperatures_K": "K",
                "conduction_resistances_K_W": "K/W",
                "outer_balance_residual_W": "W",
            },
            ("Concentric cylindrical layers with two convection boundaries and optional outer radiation.",),
            ("inl_cylindrical_heat",),
        ),
        ModelSpec(
            "thermal.lumped_temperature",
            LumpedTemperature,
            lumped_temperature,
            {"biot_number": "1", "time_constant_s": "s", "temperature_K": "K"},
            ("Lumped thermal capacitance; caller specifies the maximum applicable Biot number.",),
            ("lumped_heat_balance",),
        ),
        ModelSpec(
            "welding.heat_treatment_history",
            HeatTreatmentHistory,
            heat_treatment_history,
            {
                "simultaneous_hold_intervals_s": "s",
                "total_simultaneous_hold_s": "s",
                "longest_continuous_hold_s": "s",
                "maximum_heating_rate_K_s": "K/s",
                "maximum_cooling_rate_K_s": "K/s",
                "maximum_sensor_spread_K": "K",
            },
            (
                "Complete sensor histories on one clock; all sensors must occupy the declared hold band simultaneously.",
            ),
            ("piecewise_linear_history",),
            version="1.0.1",
        ),
        ModelSpec(
            "welding.cooling_interval",
            CoolingInterval,
            cooling_interval,
            COOLING_INTERVAL_RESULT_UNITS,
            (
                "Caller-selected monotonic cooling branch and caller-supplied target temperatures; not a thermal-cycle prediction.",
                "Piecewise-linear crossings preserve sample brackets and report maximum selected time spacing; measurement and procedure validity remain caller responsibilities.",
            ),
            ("piecewise_linear_history",),
        ),
        ModelSpec(
            "welding.cooling_interval_batch",
            CoolingIntervalBatch,
            cooling_interval_batch,
            {
                "input_sha256": "1",
                "sample_arrays_sha256": "1",
                "branch_count": "1",
                "branches": "1",
                "branch_result_units": "1",
                "record_id": "1",
                "sensor_id": "1",
                "location_id": "1",
                "provider_file_sha256": "1",
                "evidence": "1",
            },
            (
                "Apply independently caller-selected monotonic cooling branches and threshold pairs to one common recorded history.",
                "Preserves branch-specific crossing status and provenance; does not infer branches, targets, sample quality or procedure qualification.",
            ),
            ("piecewise_linear_history",),
        ),
        ModelSpec(
            "welding.cooling_interval_sensor_batch",
            CoolingIntervalSensorBatch,
            cooling_interval_sensor_batch,
            {
                "input_sha256": "1",
                "sample_arrays_sha256": "1",
                "sensor_count": "1",
                "branch_count": "1",
                "branches": "1",
                "branch_result_units": "1",
                "record_id": "1",
                "provider_file_sha256": "1",
                "evidence": "1",
            },
            (
                "Apply sensor-local cooling branches to aligned traces sharing one explicit clock.",
                "Preserves sensor and location identity per branch and never interpolates between sensors.",
            ),
            ("piecewise_linear_history",),
        ),
    ]
