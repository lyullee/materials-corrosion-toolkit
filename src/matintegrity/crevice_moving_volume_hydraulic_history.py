"""Pressure-driven reduced hydraulic history with prescribed moving slit volume."""
from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "corrosion.crevice_moving_volume_hydraulic_history"
SOURCE_ID = "caller_evidenced_pressure_driven_moving_slit_volume_history"


class CreviceMovingVolumeHydraulicHistoryRequest(Contract):
    """Integrate one pressure-driven series slit with prescribed aperture history.

    Cell aperture is linearly interpolated on each exact interval. Incompressible
    continuity determines the flow difference across each cell; total pressure
    drop drives the remaining common inlet-flow degree of freedom through a
    reduced series resistance/inertance balance.
    """

    schema_version: str = "matintegrity.crevice_moving_volume_hydraulic_history.v1"
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=5000)
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=1000)
    cell_lengths_m: tuple[Positive, ...] = Field(min_length=1, max_length=1000)
    cell_widths_m: tuple[Positive, ...] = Field(min_length=1, max_length=1000)
    aperture_m_by_knot_and_cell: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=5000)
    pressure_drop_Pa_by_interval: tuple[float, ...] = Field(min_length=1, max_length=4999)
    initial_left_boundary_flow_m3_s: float
    density_kg_m3: Positive
    dynamic_viscosity_Pa_s: Positive
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pressure_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=2, max_length=256)
    absolute_tolerance_flow_m3_s: Positive = 1e-12
    relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    absolute_pressure_closure_tolerance_Pa: Positive = 1e-9
    relative_pressure_closure_tolerance: Positive = Field(default=1e-9, le=1e-3)
    maximum_step_s: Positive = 1e6
    maximum_righthand_evaluations: int = Field(default=1_000_000, ge=1, le=20_000_000)
    maximum_output_cell_intervals: int = Field(default=2_000_000, ge=1, le=20_000_000)
    minimum_width_to_aperture_ratio: Positive = Field(default=20.0, ge=20.0, le=1000.0)
    maximum_reviewed_reynolds_number: Positive = Field(default=1000.0, ge=1.0, le=1000.0)
    geometry_and_volume_history_reviewed: bool
    pressure_reference_and_sign_reviewed: bool
    incompressible_newtonian_fluid_reviewed: bool
    wide_laminar_slit_resistance_and_inertance_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_moving_hydraulic_request(self):
        if self.schema_version != "matintegrity.crevice_moving_volume_hydraulic_history.v1":
            raise ValueError("unsupported moving-volume hydraulic schema")
        if any(not math.isfinite(t) for t in self.time_s) or any(
            b <= a for a, b in zip(self.time_s, self.time_s[1:])
        ):
            raise ValueError("hydraulic time knots must be finite and strictly increasing")
        nc, nt = len(self.cell_ids), len(self.time_s)
        if len(set(self.cell_ids)) != nc or len(self.cell_lengths_m) != nc or len(self.cell_widths_m) != nc:
            raise ValueError("cell IDs, lengths and widths must have identical unique ordered layout")
        if len(self.aperture_m_by_knot_and_cell) != nt or any(
            len(row) != nc for row in self.aperture_m_by_knot_and_cell
        ):
            raise ValueError("aperture history must match every exact time knot and ordered cell")
        if (nt - 1) * nc > self.maximum_output_cell_intervals:
            raise ValueError("interval-by-cell outputs exceed the caller work/output limit")
        if len(self.pressure_drop_Pa_by_interval) != nt - 1 or any(
            not math.isfinite(dp) for dp in self.pressure_drop_Pa_by_interval
        ):
            raise ValueError("one finite signed pressure drop is required per exact interval")
        if not math.isfinite(self.initial_left_boundary_flow_m3_s):
            raise ValueError("initial flow must be finite")
        geometry_payload = {
            "assessment_id": self.assessment_id,
            "physical_scope_id": self.physical_scope_id,
            "time_s": list(self.time_s),
            "cell_ids": list(self.cell_ids),
            "cell_lengths_m": [float(v) for v in self.cell_lengths_m],
            "cell_widths_m": [float(v) for v in self.cell_widths_m],
            "aperture_m_by_knot_and_cell": [[float(v) for v in row]
                                              for row in self.aperture_m_by_knot_and_cell],
        }
        pressure_payload = {
            "physical_scope_id": self.physical_scope_id,
            "time_s": list(self.time_s),
            "pressure_drop_Pa_by_interval": list(self.pressure_drop_Pa_by_interval),
        }
        if canonical_digest(geometry_payload) != self.geometry_sha256:
            raise ValueError("geometry digest must pin the ordered moving aperture mesh")
        if canonical_digest(pressure_payload) != self.pressure_sha256:
            raise ValueError("pressure digest must pin the ordered interval pressure forcing")
        if (not any(e.sha256 == self.geometry_sha256 and e.license_id for e in self.evidence)
                or not any(e.sha256 == self.pressure_sha256 and e.license_id for e in self.evidence)):
            raise ValueError("licensed Evidence must pin both geometry and pressure records")
        if not all((self.geometry_and_volume_history_reviewed,
                    self.pressure_reference_and_sign_reviewed,
                    self.incompressible_newtonian_fluid_reviewed,
                    self.wide_laminar_slit_resistance_and_inertance_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("geometry, pressure, fluid, slit-law and use reviews are required")
        return self


def evaluate_crevice_moving_volume_hydraulic_history(
    request: CreviceMovingVolumeHydraulicHistoryRequest,
) -> Calculation:
    """Integrate inlet flow and derive conservative interval-mean face flows."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {"model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "physical_scope_id": request.physical_scope_id, "input_sha256": digest,
            "geometry_sha256": request.geometry_sha256, "pressure_sha256": request.pressure_sha256}
    try:
        from scipy.integrate import solve_ivp
        times = np.asarray(request.time_s, dtype=float)
        aperture = np.asarray(request.aperture_m_by_knot_and_cell, dtype=float)
        lengths = np.asarray(request.cell_lengths_m, dtype=float)
        widths = np.asarray(request.cell_widths_m, dtype=float)
        volume = aperture * (lengths * widths)[None, :]
        if not np.isfinite(volume).all() or np.any(volume <= 0.0):
            raise ArithmeticError("liquid cell volume exceeded finite positive support")
        volume_rate = np.diff(volume, axis=0) / np.diff(times)[:, None]
        flow = float(request.initial_left_boundary_flow_m3_s)
        cumulative_volume = 0.0
        face_mean_history: list[list[float]] = []
        continuity_residual_history: list[list[float]] = []
        boundary_volume_residual_history: list[float] = []
        inlet_knot_history = [flow]
        interval_records = []
        rhs_evaluations = 0
        maximum_reynolds = 0.0
        maximum_aspect_ratio = math.inf
        rho, mu = float(request.density_kg_m3), float(request.dynamic_viscosity_Pa_s)
        aspect_by_knot = widths[None, :] / aperture
        if float(np.min(aspect_by_knot)) < float(request.minimum_width_to_aperture_ratio):
            raise ArithmeticError("moving slit aperture history is outside the caller-reviewed wide-slit support")
        maximum_aspect_ratio = float(np.min(aspect_by_knot))
        for interval, (start, end, pressure) in enumerate(zip(
            times[:-1], times[1:], request.pressure_drop_Pa_by_interval, strict=True,
        )):
            duration = float(end - start)
            h0, h1 = aperture[interval], aperture[interval + 1]
            vdot = volume_rate[interval]
            offsets = np.cumsum(np.concatenate(([0.0], vdot[:-1]))) + 0.5 * vdot

            def coefficients(t_rel: float):
                fraction = min(1.0, max(0.0, t_rel / duration))
                gap = h0 + fraction * (h1 - h0)
                resistance = 12.0 * mu * lengths / (widths * gap**3)
                inertance = rho * lengths / (widths * gap)
                return gap, resistance, inertance

            def rhs(t_rel, state):
                nonlocal rhs_evaluations, maximum_reynolds
                rhs_evaluations += 1
                if rhs_evaluations > request.maximum_righthand_evaluations:
                    raise RuntimeError("moving_hydraulic_rhs_evaluation_budget_exceeded")
                gap, resistance, inertance = coefficients(float(t_rel))
                trial_cell_flow = float(state[0]) - offsets
                stage_reynolds = 2.0 * rho * np.abs(trial_cell_flow) / (widths * mu)
                maximum_reynolds = max(maximum_reynolds, float(np.max(stage_reynolds)))
                if maximum_reynolds > float(request.maximum_reviewed_reynolds_number):
                    raise ArithmeticError("moving slit exceeded the caller-reviewed Reynolds support")
                if np.any(widths / gap < float(request.minimum_width_to_aperture_ratio)):
                    raise ArithmeticError("moving slit left the caller-reviewed wide-slit support")
                total_inertance = float(np.sum(inertance))
                if not math.isfinite(total_inertance) or total_inertance <= 0.0:
                    raise ArithmeticError("moving slit inertance exceeded finite positive support")
                dflow = (float(pressure) - float(np.sum(resistance)) * state[0]
                         + float(np.dot(resistance, offsets))) / total_inertance
                if not math.isfinite(dflow):
                    raise ArithmeticError("moving slit flow derivative exceeded finite support")
                return (dflow, state[0])

            solution = solve_ivp(
                rhs, (0.0, duration), (flow, 0.0), method="BDF",
                t_eval=(0.5 * duration, duration), rtol=float(request.relative_tolerance),
                atol=(float(request.absolute_tolerance_flow_m3_s),
                      float(request.absolute_tolerance_flow_m3_s) * duration),
                max_step=float(request.maximum_step_s),
            )
            if not solution.success or solution.y.shape != (2, 2):
                raise RuntimeError(f"moving_hydraulic_bdf_failed:{solution.message}")
            flow_mid = float(solution.y[0, 0])
            flow_end = float(solution.y[0, 1])
            integrated_inlet_volume = float(solution.y[1, 1])
            mean_inlet_flow = integrated_inlet_volume / duration
            face_flows = mean_inlet_flow - np.concatenate(([0.0], np.cumsum(vdot)))
            gaps_mid, resistance_mid, inertance_mid = coefficients(0.5 * duration)
            q_cell = mean_inlet_flow - offsets
            dflow_mid = (float(pressure) - float(np.sum(resistance_mid)) * flow_mid
                         + float(np.dot(resistance_mid, offsets))) / float(np.sum(inertance_mid))
            q_cell_mid = flow_mid - offsets
            cell_dp = inertance_mid * dflow_mid + resistance_mid * q_cell_mid
            aspect = widths / gaps_mid
            reynolds = 2.0 * rho * np.abs(q_cell) / (widths * mu)
            maximum_aspect_ratio = min(maximum_aspect_ratio, float(np.min(aspect)))
            maximum_reynolds = max(maximum_reynolds, float(np.max(reynolds)))
            if np.any(aspect < float(request.minimum_width_to_aperture_ratio)):
                raise ArithmeticError("moving slit left the caller-reviewed wide-slit support")
            if maximum_reynolds > float(request.maximum_reviewed_reynolds_number):
                raise ArithmeticError("moving slit exceeded the caller-reviewed Reynolds support")
            if not (np.isfinite(face_flows).all() and np.isfinite(cell_dp).all()
                    and math.isfinite(flow_end) and math.isfinite(mean_inlet_flow)):
                raise ArithmeticError("moving hydraulic result exceeded finite numeric support")
            pressure_residual = float(np.sum(cell_dp) - pressure)
            allowed_pressure = (float(request.absolute_pressure_closure_tolerance_Pa)
                                + float(request.relative_pressure_closure_tolerance)
                                * abs(float(pressure)))
            if abs(pressure_residual) > allowed_pressure:
                raise ArithmeticError("distributed cell pressure drops do not close total pressure")
            continuity_residual = face_flows[:-1] - face_flows[1:] - vdot
            allowed_continuity = float(request.absolute_tolerance_flow_m3_s) + \
                float(request.relative_tolerance) * np.maximum.reduce((
                    np.abs(face_flows[:-1]), np.abs(face_flows[1:]), np.abs(vdot),
                ))
            if np.any(np.abs(continuity_residual) > allowed_continuity):
                raise ArithmeticError("moving-volume cell flow continuity exceeds the declared tolerance")
            volume_change = float(np.sum(volume[interval + 1] - volume[interval]))
            boundary_volume_residual = (
                (mean_inlet_flow - float(face_flows[-1])) * duration - volume_change
            )
            allowed_boundary_volume = (
                float(request.absolute_tolerance_flow_m3_s) * duration
                + float(request.relative_tolerance)
                * max(abs(volume_change), abs((mean_inlet_flow - float(face_flows[-1])) * duration))
            )
            if abs(boundary_volume_residual) > allowed_boundary_volume:
                raise ArithmeticError("moving-volume inlet/outlet displacement balance exceeds the declared tolerance")
            face_mean_history.append(face_flows.tolist())
            continuity_residual_history.append(continuity_residual.tolist())
            boundary_volume_residual_history.append(boundary_volume_residual)
            interval_records.append({
                "interval_index": interval,
                "start_time_s": float(start), "end_time_s": float(end),
                "input_pressure_drop_Pa": float(pressure),
                "interval_mean_cell_aperture_m": gaps_mid.tolist(),
                "cell_volume_rate_m3_s": vdot.tolist(),
                "interval_mean_face_flow_m3_s": face_flows.tolist(),
                "cell_continuity_residual_m3_s": continuity_residual.tolist(),
                "integrated_boundary_volume_change_residual_m3": boundary_volume_residual,
                "interval_mean_cell_flow_m3_s": q_cell.tolist(),
                "cell_pressure_drop_Pa": cell_dp.tolist(),
                "pressure_closure_residual_Pa": pressure_residual,
                "left_boundary_flow_start_m3_s": flow,
                "left_boundary_flow_end_m3_s": flow_end,
                "left_boundary_mean_flow_m3_s": mean_inlet_flow,
                "right_boundary_mean_flow_m3_s": float(face_flows[-1]),
                "integrated_left_boundary_volume_m3": integrated_inlet_volume,
            })
            flow = flow_end
            cumulative_volume += integrated_inlet_volume
            if not math.isfinite(cumulative_volume):
                raise ArithmeticError("integrated inlet volume exceeded finite numeric support")
            inlet_knot_history.append(flow)
        return Calculation(values=base | {
            "time_s": list(request.time_s),
            "left_boundary_flow_m3_s_by_knot": inlet_knot_history,
            "interval_results": interval_records,
            "interval_mean_face_flow_m3_s_by_interval": face_mean_history,
            "cell_continuity_residual_m3_s_by_interval_and_cell": continuity_residual_history,
            "maximum_absolute_cell_continuity_residual_m3_s": max(
                (abs(value) for row in continuity_residual_history for value in row), default=0.0
            ),
            "integrated_boundary_volume_change_residual_m3_by_interval": boundary_volume_residual_history,
            "maximum_absolute_boundary_volume_change_residual_m3": max(
                (abs(value) for value in boundary_volume_residual_history), default=0.0
            ),
            "integrated_left_boundary_volume_m3": cumulative_volume,
            "rhs_evaluations": rhs_evaluations,
            "minimum_width_to_aperture_ratio_observed": maximum_aspect_ratio,
            "maximum_reynolds_number_observed": maximum_reynolds,
            "committed": True,
            "qualification_claimed": False,
            "limitations": [
                "Pressure and aperture are piecewise constant/linear by declared interval; no stage-resolved solid morphology is inferred.",
                "The model is a one-dimensional reduced series momentum balance, not transient Navier-Stokes or compressible flow.",
                "Face-flow differences satisfy prescribed incompressible cell-volume continuity; aqueous species, chemistry and corrosion remain uncoupled.",
            ],
        })
    except (ArithmeticError, OverflowError, RuntimeError, ValueError, ZeroDivisionError) as error:
        return Calculation(status="needs_data", values=base | {
            "reason": str(error), "committed": False, "qualification_claimed": False,
        })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceMovingVolumeHydraulicHistoryRequest,
        evaluator=evaluate_crevice_moving_volume_hydraulic_history,
        units={
            "time_s": "s", "pressure_drop_Pa_by_interval[]": "Pa",
            "left_boundary_flow_m3_s_by_knot[]": "m^3/s",
            "interval_mean_face_flow_m3_s_by_interval[][]": "m^3/s",
            "cell_continuity_residual_m3_s_by_interval_and_cell[][]": "m^3/s",
            "maximum_absolute_cell_continuity_residual_m3_s": "m^3/s",
            "integrated_boundary_volume_change_residual_m3_by_interval[]": "m^3",
            "maximum_absolute_boundary_volume_change_residual_m3": "m^3",
            "cell_pressure_drop_Pa_by_interval_and_cell[][]": "Pa",
            "cell_volume_rate_m3_s_by_interval_and_cell[][]": "m^3/s",
        },
        assumptions=(
            "Aperture varies linearly within each caller interval, so liquid volume rate is interval constant.",
            "One common pressure forcing drives the series momentum balance; continuity determines downstream face-flow offsets from cell volume rates.",
            "The reduced slit resistance/inertance law is only used inside declared wide-slit, laminar and fluid-property support.",
        ),
        source_ids=(SOURCE_ID,), version="0.1.0", qualification="user_model",
    ),)
