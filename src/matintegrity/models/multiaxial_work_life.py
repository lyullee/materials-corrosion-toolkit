"""Caller-calibrated work-based life for explicitly closed multiaxial tensor cycles."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class ClosedTensorCycle(Contract):
    cycle_id: str = Field(min_length=1)
    allocated_cycle_count: Positive = 1.0
    sample_ids: list[str] = Field(min_length=3, max_length=50000)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=50000)
    strain_tensor_components: list[list[float]] = Field(min_length=3, max_length=50000)
    sample_time_s: list[Nonnegative] | None = None
    stress_time_derivative_components_Pa_s: list[list[float]] | None = None
    strain_time_derivative_components_s_inv: list[list[float]] | None = None

    @model_validator(mode="after")
    def aligned_tensor_path(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("cycle sample IDs must be unique and preserve path order")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("stress, strain and sample-ID histories must align")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("stress tensors must use [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("strain tensors must use [xx, yy, zz, xy, yz, zx]")
        has_stress_derivatives = self.stress_time_derivative_components_Pa_s is not None
        has_strain_derivatives = self.strain_time_derivative_components_s_inv is not None
        if has_stress_derivatives != has_strain_derivatives:
            raise ValueError("cubic Hermite reconstruction requires both stress and strain derivative histories")
        if (has_stress_derivatives or has_strain_derivatives) and self.sample_time_s is None:
            raise ValueError("tensor derivative histories require an aligned time vector")
        if self.sample_time_s is not None:
            assert self.sample_time_s is not None
            if len(self.sample_time_s) != count or any(
                right <= left for left, right in zip(self.sample_time_s[:-1], self.sample_time_s[1:], strict=True)
            ):
                raise ValueError("time-resolved tensor samples must align and strictly increase")
        if has_stress_derivatives:
            assert self.stress_time_derivative_components_Pa_s is not None
            assert self.strain_time_derivative_components_s_inv is not None
            if len(self.stress_time_derivative_components_Pa_s) != count or len(self.strain_time_derivative_components_s_inv) != count:
                raise ValueError("cubic derivative histories must align with tensor samples")
            if any(len(row) != 6 for row in (*self.stress_time_derivative_components_Pa_s, *self.strain_time_derivative_components_s_inv)):
                raise ValueError("cubic derivative tensors must use [xx, yy, zz, xy, yz, zx]")
        finite_values = (
            self.allocated_cycle_count,
            *(value for row in self.stress_tensor_components_Pa for value in row),
            *(value for row in self.strain_tensor_components for value in row),
            *(self.sample_time_s or ()),
            *(
                value
                for history in (self.stress_time_derivative_components_Pa_s, self.strain_time_derivative_components_s_inv)
                if history is not None
                for row in history
                for value in row
            ),
        )
        if any(not math.isfinite(value) for value in finite_values):
            raise ValueError("tensor cycle samples, time coordinates, derivatives and repetitions must be finite")
        return self


class ClosedTensorWorkLife(Contract):
    schema_version: Literal["matintegrity.closed_tensor_work_life.v1"] = (
        "matintegrity.closed_tensor_work_life.v1"
    )
    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    cycles: tuple[ClosedTensorCycle, ...] = Field(min_length=1, max_length=10000)
    strain_shear_convention: Literal["tensor", "engineering"]
    time_reconstruction: Literal["piecewise_linear", "piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"] = "piecewise_linear"
    stress_history_source_id: str = Field(min_length=1)
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_history_source_id: str = Field(min_length=1)
    strain_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_id: str = Field(min_length=1)
    calibration_material_condition_id: str = Field(min_length=1)
    calibration_source_id: str = Field(min_length=1)
    calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dissipated_energy_density_J_m3: list[Positive] = Field(min_length=3, max_length=1000)
    cycles_to_failure: list[Positive] = Field(min_length=3, max_length=1000)
    maximum_closure_stress_error_Pa: Nonnegative
    maximum_closure_strain_error: Nonnegative
    tensor_basis_and_order_reviewed: bool = False
    stress_strain_conjugacy_reviewed: bool = False
    cycle_boundary_and_closure_reviewed: bool = False
    time_reconstruction_and_derivative_reviewed: bool = False
    periodic_spline_reviewed: bool = False
    material_calibration_applicability_reviewed: bool = False
    work_life_fit_and_miner_rule_reviewed: bool = False

    @model_validator(mode="after")
    def coherent_calibration_and_cycles(self):
        if len(self.dissipated_energy_density_J_m3) != len(self.cycles_to_failure):
            raise ValueError("work-life calibration vectors must have equal lengths")
        energy = self.dissipated_energy_density_J_m3
        life = self.cycles_to_failure
        if any(b <= a for a, b in zip(energy, energy[1:], strict=False)):
            raise ValueError("calibration energy densities must strictly increase")
        if any(b >= a for a, b in zip(life, life[1:], strict=False)):
            raise ValueError("calibrated cycles to failure must strictly decrease as energy increases")
        if self.material_condition_id != self.calibration_material_condition_id:
            raise ValueError("work-life calibration material condition must exactly match the cycle condition")
        cycle_ids = [row.cycle_id for row in self.cycles]
        if len(set(cycle_ids)) != len(cycle_ids):
            raise ValueError("cycle identifiers must be unique")
        contains_time_data = [cycle.sample_time_s is not None for cycle in self.cycles]
        if self.time_reconstruction == "piecewise_cubic_hermite":
            if not all(contains_time_data):
                raise ValueError("every cycle needs explicit time and derivative histories for cubic Hermite reconstruction")
        elif self.time_reconstruction == "piecewise_pchip":
            if not all(contains_time_data):
                raise ValueError("every PCHIP cycle needs an explicit time history")
            if any(cycle.stress_time_derivative_components_Pa_s is not None for cycle in self.cycles):
                raise ValueError("PCHIP derives its own knot slopes and cannot accept supplied derivatives")
        elif self.time_reconstruction == "piecewise_periodic_cubic_spline":
            if not all(contains_time_data):
                raise ValueError("every periodic spline cycle needs an explicit time history")
            if any(cycle.stress_time_derivative_components_Pa_s is not None for cycle in self.cycles):
                raise ValueError("periodic cubic spline derives its own slopes and cannot accept supplied derivatives")
            for cycle in self.cycles:
                if cycle.stress_tensor_components_Pa[0] != cycle.stress_tensor_components_Pa[-1] or cycle.strain_tensor_components[0] != cycle.strain_tensor_components[-1]:
                    raise ValueError("periodic cubic spline requires exactly matching first and last stress/strain samples")
        elif any(contains_time_data):
            raise ValueError("time histories require cubic-Hermite or PCHIP reconstruction")
        return self


def _hermite_coefficients(y0: float, y1: float, derivative0: float, derivative1: float, interval_s: float) -> tuple[float, float, float, float]:
    return (
        y0,
        interval_s * derivative0,
        -3.0 * y0 - 2.0 * interval_s * derivative0 + 3.0 * y1 - interval_s * derivative1,
        2.0 * y0 + interval_s * derivative0 - 2.0 * y1 + interval_s * derivative1,
    )


def _hermite_stress_strain_work(
    stress: tuple[float, float, float, float], strain: tuple[float, float, float, float]
) -> float:
    # Integrate sigma(s) * d(epsilon(s))/ds on normalized s in [0, 1].
    return math.fsum(
        stress[i] * (j + 1) * strain[j + 1] / (i + j + 1)
        for i in range(4)
        for j in range(3)
    )


def _pchip_slopes(times: list[float], values: list[float]) -> list[float]:
    """Fritsch-Butland monotone slopes for a shape-preserving cubic Hermite path."""
    n = len(times)
    h = [times[i + 1] - times[i] for i in range(n - 1)]
    delta = [(values[i + 1] - values[i]) / h[i] for i in range(n - 1)]
    if n == 2:
        return [delta[0], delta[0]]
    slopes = [0.0] * n
    for i in range(1, n - 1):
        left, right = delta[i - 1], delta[i]
        if left == 0.0 or right == 0.0 or math.copysign(1.0, left) != math.copysign(1.0, right):
            slopes[i] = 0.0
        else:
            w1 = 2.0 * h[i] + h[i - 1]
            w2 = h[i] + 2.0 * h[i - 1]
            slopes[i] = (w1 + w2) / (w1 / left + w2 / right)
    for index, adjacent in ((0, 0), (n - 1, n - 2)):
        if index == 0:
            estimate = ((2.0 * h[0] + h[1]) * delta[0] - h[0] * delta[1]) / (h[0] + h[1])
            near, following = delta[0], delta[1]
        else:
            estimate = ((2.0 * h[-1] + h[-2]) * delta[-1] - h[-1] * delta[-2]) / (h[-1] + h[-2])
            near, following = delta[-1], delta[-2]
        if estimate == 0.0 or near == 0.0 or math.copysign(1.0, estimate) != math.copysign(1.0, near):
            slopes[index] = 0.0
        elif math.copysign(1.0, near) != math.copysign(1.0, following) and abs(estimate) > 3.0 * abs(near):
            slopes[index] = 3.0 * near
        else:
            slopes[index] = estimate
    return slopes


def _hermite_coefficients_from_slopes(
    times: list[float], values: list[float], slopes: list[float], interval: int
) -> tuple[float, float, float, float]:
    dt = times[interval + 1] - times[interval]
    return _hermite_coefficients(values[interval], values[interval + 1], slopes[interval], slopes[interval + 1], dt)


def _pchip_coefficients(times: list[float], values: list[float], interval: int) -> tuple[float, float, float, float]:
    return _hermite_coefficients_from_slopes(times, values, _pchip_slopes(times, values), interval)


def _cycle_pchip_coefficients(cycle: ClosedTensorCycle):
    """Precompute the componentwise cubic segments once for repeated quadrature calls."""
    assert cycle.sample_time_s is not None
    times = cycle.sample_time_s
    stress_by_component = []
    strain_by_component = []
    for component in range(6):
        stress_values = [row[component] for row in cycle.stress_tensor_components_Pa]
        strain_values = [row[component] for row in cycle.strain_tensor_components]
        stress_by_component.append((stress_values, _pchip_slopes(times, stress_values)))
        strain_by_component.append((strain_values, _pchip_slopes(times, strain_values)))
    stress = tuple(
        tuple(_hermite_coefficients_from_slopes(times, values, slopes, interval) for values, slopes in stress_by_component)
        for interval in range(len(times) - 1)
    )
    strain = tuple(
        tuple(_hermite_coefficients_from_slopes(times, values, slopes, interval) for values, slopes in strain_by_component)
        for interval in range(len(times) - 1)
    )
    return stress, strain


def _cycle_periodic_spline_coefficients(cycle: ClosedTensorCycle):
    """Return periodic cubic coefficients in normalized interval coordinates.

    SciPy is imported only when this optional reconstruction is requested. The
    spline has no extrapolation path and requires an exactly closed input path.
    """
    try:
        from scipy.interpolate import CubicSpline
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("periodic cubic spline reconstruction requires SciPy") from exc
    assert cycle.sample_time_s is not None
    times = cycle.sample_time_s
    stress_values = [[row[k] for row in cycle.stress_tensor_components_Pa] for k in range(6)]
    strain_values = [[row[k] for row in cycle.strain_tensor_components] for k in range(6)]

    def convert(values):
        spline = CubicSpline(times, values, axis=1, bc_type="periodic", extrapolate=False)
        intervals = []
        for i, dt in enumerate(b - a for a, b in zip(times[:-1], times[1:], strict=True)):
            # SciPy stores descending powers of (t - t_i); work integration
            # uses ascending powers of s=(t-t_i)/dt.
            intervals.append(tuple((
                float(spline.c[3, i, k]),
                float(spline.c[2, i, k] * dt),
                float(spline.c[1, i, k] * dt * dt),
                float(spline.c[0, i, k] * dt * dt * dt),
            ) for k in range(6)))
        return tuple(intervals)

    return convert(stress_values), convert(strain_values)


def _tensor_loop_work(cycle: ClosedTensorCycle, convention: str, reconstruction: str) -> tuple[float, float, float]:
    shear_weight = 1.0 if convention == "engineering" else 2.0
    weights = (1.0, 1.0, 1.0, shear_weight, shear_weight, shear_weight)
    try:
        if reconstruction == "piecewise_linear":
            terms = [
                weights[k] * 0.5 * (stress_left[k] + stress_right[k]) * (strain_right[k] - strain_left[k])
                for stress_left, stress_right, strain_left, strain_right in zip(
                    cycle.stress_tensor_components_Pa[:-1], cycle.stress_tensor_components_Pa[1:],
                    cycle.strain_tensor_components[:-1], cycle.strain_tensor_components[1:], strict=True,
                ) for k in range(6)
            ]
        elif reconstruction == "piecewise_cubic_hermite":
            assert cycle.sample_time_s is not None
            assert cycle.stress_time_derivative_components_Pa_s is not None
            assert cycle.strain_time_derivative_components_s_inv is not None
            terms = []
            for index in range(len(cycle.sample_time_s) - 1):
                interval_s = cycle.sample_time_s[index + 1] - cycle.sample_time_s[index]
                for k in range(6):
                    stress = _hermite_coefficients(
                        cycle.stress_tensor_components_Pa[index][k], cycle.stress_tensor_components_Pa[index + 1][k],
                        cycle.stress_time_derivative_components_Pa_s[index][k], cycle.stress_time_derivative_components_Pa_s[index + 1][k], interval_s,
                    )
                    strain = _hermite_coefficients(
                        cycle.strain_tensor_components[index][k], cycle.strain_tensor_components[index + 1][k],
                        cycle.strain_time_derivative_components_s_inv[index][k], cycle.strain_time_derivative_components_s_inv[index + 1][k], interval_s,
                    )
                    terms.append(weights[k] * _hermite_stress_strain_work(stress, strain))
        elif reconstruction == "piecewise_periodic_cubic_spline":
            stress_intervals, strain_intervals = _cycle_periodic_spline_coefficients(cycle)
            terms = [
                weights[k] * _hermite_stress_strain_work(stress_intervals[i][k], strain_intervals[i][k])
                for i in range(len(stress_intervals)) for k in range(6)
            ]
        else:
            assert cycle.sample_time_s is not None
            times = cycle.sample_time_s
            terms = []
            for k in range(6):
                stress_values = [row[k] for row in cycle.stress_tensor_components_Pa]
                strain_values = [row[k] for row in cycle.strain_tensor_components]
                stress_slopes = _pchip_slopes(times, stress_values)
                strain_slopes = _pchip_slopes(times, strain_values)
                for index in range(len(times) - 1):
                    stress = _hermite_coefficients_from_slopes(times, stress_values, stress_slopes, index)
                    strain = _hermite_coefficients_from_slopes(times, strain_values, strain_slopes, index)
                    terms.append(weights[k] * _hermite_stress_strain_work(stress, strain))
        if any(not math.isfinite(term) for term in terms):
            signed_work = math.inf
        else:
            signed_work = math.fsum(terms)
    except (OverflowError, ValueError):
        signed_work = math.inf
    stress_closure = max(
        abs(a - b)
        for a, b in zip(
            cycle.stress_tensor_components_Pa[0], cycle.stress_tensor_components_Pa[-1], strict=True
        )
    )
    strain_closure = max(
        abs(a - b)
        for a, b in zip(cycle.strain_tensor_components[0], cycle.strain_tensor_components[-1], strict=True)
    )
    return signed_work, stress_closure, strain_closure


def _loglog_life(energy: float, knots: list[float], lives: list[float]) -> float | None:
    if energy < knots[0] or energy > knots[-1]:
        return None
    for index in range(len(knots) - 1):
        if energy <= knots[index + 1]:
            fraction = (math.log(energy) - math.log(knots[index])) / (
                math.log(knots[index + 1]) - math.log(knots[index])
            )
            return math.exp(
                math.log(lives[index]) + fraction * (math.log(lives[index + 1]) - math.log(lives[index]))
            )
    return lives[-1]


def closed_tensor_work_life(x: ClosedTensorWorkLife) -> Calculation:
    reviews = (
        x.tensor_basis_and_order_reviewed,
        x.stress_strain_conjugacy_reviewed,
        x.cycle_boundary_and_closure_reviewed,
        (x.time_reconstruction == "piecewise_linear" or x.time_reconstruction_and_derivative_reviewed),
        (x.time_reconstruction != "piecewise_periodic_cubic_spline" or x.periodic_spline_reviewed),
        x.material_calibration_applicability_reviewed,
        x.work_life_fit_and_miner_rule_reviewed,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={"analysis_id": x.analysis_id, "missing_review_count": sum(not item for item in reviews)},
            notes=("Tensor basis/order, conjugate stress-strain interpretation, closed-cycle boundary, calibration applicability and work-life/Miner assumptions require caller review.",),
        )
    rows = []
    damage_terms = []
    unresolved = []
    for cycle in x.cycles:
        try:
            signed_work, stress_closure, strain_closure = _tensor_loop_work(
                cycle, x.strain_shear_convention, x.time_reconstruction
            )
        except RuntimeError as error:
            return Calculation(
                status="needs_data",
                values={"analysis_id": x.analysis_id, "cycle_id": cycle.cycle_id},
                notes=(str(error),),
            )
        energy = abs(signed_work)
        if not all(math.isfinite(value) for value in (signed_work, stress_closure, strain_closure, energy)):
            unresolved.append({"cycle_id": cycle.cycle_id, "allocated_cycle_count": cycle.allocated_cycle_count, "reason": "nonfinite_tensor_work_or_closure_metric"})
            continue
        row = {
            "cycle_id": cycle.cycle_id,
            "allocated_cycle_count": cycle.allocated_cycle_count,
            "signed_closed_loop_work_density_J_m3": signed_work,
            "dissipated_energy_density_J_m3": energy,
            "work_orientation_sign": 1 if signed_work > 0 else (-1 if signed_work < 0 else 0),
            "maximum_stress_closure_error_Pa": stress_closure,
            "maximum_strain_closure_error": strain_closure,
        }
        if stress_closure > x.maximum_closure_stress_error_Pa or strain_closure > x.maximum_closure_strain_error:
            unresolved.append(row | {"reason": "cycle_endpoint_closure_exceeds_declared_tolerance"})
            continue
        if energy <= 0:
            unresolved.append(row | {"reason": "nonpositive_closed_loop_work_magnitude"})
            continue
        life = _loglog_life(energy, x.dissipated_energy_density_J_m3, x.cycles_to_failure)
        if life is None:
            unresolved.append(row | {"reason": "work_density_outside_calibration_support"})
            continue
        damage = cycle.allocated_cycle_count / life
        if not math.isfinite(damage):
            unresolved.append(row | {"cycles_to_failure": life, "reason": "nonfinite_miner_damage"})
            continue
        damage_terms.append(damage)
        rows.append(row | {"cycles_to_failure": life, "miner_damage": damage})
    common = {
        "analysis_id": x.analysis_id,
        "material_condition_id": x.material_condition_id,
        "location_id": x.location_id,
        "calibration_id": x.calibration_id,
        "calibration_sha256": x.calibration_sha256,
        "stress_history_sha256": x.stress_history_sha256,
        "strain_history_sha256": x.strain_history_sha256,
        "strain_shear_convention": x.strain_shear_convention,
        "time_reconstruction": x.time_reconstruction,
        "stress_strain_work_integration": "exact_piecewise_cubic_polynomial_product" if x.time_reconstruction != "piecewise_linear" else "trapezoidal_piecewise_linear",
        "work_life_interpolation": "piecewise_linear_in_log_energy_log_life_without_extrapolation",
        "input_digest": canonical_digest(x.model_dump(mode="json")),
    }
    if unresolved:
        return Calculation(
            status="out_of_scope",
            values=common | {"cycle_results": rows + unresolved, "unresolved_cycle_count": len(unresolved)},
            notes=("At least one cycle is open/nonpositive or outside the calibration support; total Miner damage is withheld.", "Path work from the supplied ordered history is a caller-calibrated work-life metric, not a universal nonproportional fatigue law."),
        )
    try:
        total_damage = math.fsum(damage_terms)
        cycle_count = math.fsum(cycle.allocated_cycle_count for cycle in x.cycles)
    except (OverflowError, ValueError):
        total_damage = cycle_count = math.inf
    if not math.isfinite(total_damage) or not math.isfinite(cycle_count):
        return Calculation(
            status="out_of_scope",
            values=common | {
                "cycle_results": rows,
                "unresolved_cycle_count": 0,
                "aggregate_issue": "nonfinite_total_miner_damage_or_cycle_count",
            },
            notes=("Every cycle was individually within the declared support, but a requested aggregate exceeds finite numeric range; no aggregate value is emitted.",),
        )
    return Calculation(
        values=common | {
            "cycle_results": rows,
            "total_miner_damage": total_damage,
            "cycle_count": cycle_count,
            "closure_checked_cycle_count": len(x.cycles),
        },
        notes=(
            "Tensor loop work follows the declared piecewise-linear, explicit-derivative cubic-Hermite or shape-preserving PCHIP reconstruction; cubic segment work is integrated exactly as a polynomial product. PCHIP derives componentwise knot slopes from the supplied time series and does not accept extrapolation. Tensor-shear inputs use a factor of two and engineering-shear inputs use a factor of one.",
            "Absolute closed-loop work magnitude is mapped through the caller calibration by log-log interpolation. Calibration applicability, path direction, cycle extraction and linear Miner accumulation remain explicit caller assumptions; no rainflow or standard acceptance rule is inferred.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "fatigue.closed_tensor_work_life",
            ClosedTensorWorkLife,
            closed_tensor_work_life,
            {
                "cycle_results[].signed_closed_loop_work_density_J_m3": "J/m^3",
                "cycle_results[].dissipated_energy_density_J_m3": "J/m^3",
                "cycle_results[].cycles_to_failure": "cycle",
                "cycle_results[].miner_damage": "1",
                "total_miner_damage": "1",
                "cycle_count": "cycle",
            },
            (
                "Caller-provided closed 3D stress-strain tensor cycles, explicit piecewise-linear, time-derivative-defined cubic-Hermite or shape-preserving PCHIP reconstruction, reviewed conjugacy and cycle boundaries, material-matched work-life calibration, bounded log-log interpolation and explicit linear Miner accumulation.",
                "The result is a caller-calibrated path-work metric; it is not a universal nonproportional fatigue law or code acceptance result.",
            ),
            ("closed_tensor_work_life_calibration",),
        )
    ]
