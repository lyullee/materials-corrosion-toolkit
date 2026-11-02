"""Piecewise-constant inertance/resistance history for wide planar slit flow."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec


class PlanarSlitTransientHydraulicHistory(Contract):
    """Exact interval solution of a caller-reviewed lumped slit momentum balance."""

    schema_version: Literal["matintegrity.planar_slit_transient_hydraulic_history.v1"] = (
        "matintegrity.planar_slit_transient_hydraulic_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_state_id: str | None = None
    time_basis: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=100001)
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=2000)
    cell_widths_m: tuple[Positive, ...] = Field(min_length=1, max_length=2000)
    aperture_by_interval_m: tuple[tuple[Positive, ...], ...] = Field(min_length=1, max_length=100000)
    transverse_width_m: Positive
    pressure_drop_by_interval_Pa: tuple[float, ...] = Field(min_length=1, max_length=100000)
    initial_volumetric_flow_m3_s: float
    density_kg_m3: Positive
    dynamic_viscosity_Pa_s: Positive
    resistance_correction_multiplier: Positive = 1.0
    inertance_correction_multiplier: Positive = 1.0
    hydraulic_parameter_fit_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    hydraulic_parameter_fit_evidence: Evidence | None = None
    hydraulic_parameter_fit_applicability_reviewed: bool = False
    minimum_width_to_aperture_ratio: Positive = Field(default=20.0, ge=20.0, le=1000.0)
    maximum_reviewed_reynolds_number: Positive = Field(default=1000.0, ge=1.0, le=1000.0)
    geometry_provider_id: str = Field(min_length=1)
    geometry_provider_revision: str = Field(min_length=1)
    geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pressure_provider_id: str = Field(min_length=1)
    pressure_provider_revision: str = Field(min_length=1)
    pressure_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fluid_property_provider_id: str = Field(min_length=1)
    fluid_property_provider_revision: str = Field(min_length=1)
    fluid_property_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    geometry_clock_and_grid_reviewed: bool
    pressure_reference_sign_and_clock_reviewed: bool
    incompressible_newtonian_property_support_reviewed: bool
    wide_slit_aspect_ratio_reviewed: bool
    laminar_fully_developed_resistance_reviewed: bool
    unsteady_lumped_inertance_applicability_reviewed: bool
    signed_flow_reversal_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_piecewise_history(self):
        if any(not math.isfinite(value) for value in self.time_s):
            raise ValueError("time knots must be finite")
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("time knots must increase strictly")
        interval_count = len(self.time_s) - 1
        if interval_count * len(self.cell_widths_m) > 2_000_000:
            raise ValueError("interval-by-cell evaluation budget exceeded")
        if len(self.cell_ids) != len(self.cell_widths_m) or len(set(self.cell_ids)) != len(self.cell_ids):
            raise ValueError("ordered cell IDs must be unique and align one-to-one with cell widths")
        if len(self.aperture_by_interval_m) != interval_count or len(self.pressure_drop_by_interval_Pa) != interval_count:
            raise ValueError("pressure and aperture histories must provide one value per interval")
        if any(len(row) != len(self.cell_widths_m) for row in self.aperture_by_interval_m):
            raise ValueError("each interval must provide one positive aperture for every ordered cell")
        if any(not math.isfinite(value) for value in self.pressure_drop_by_interval_Pa):
            raise ValueError("pressure drops must be finite signed values")
        if not math.isfinite(self.initial_volumetric_flow_m3_s):
            raise ValueError("initial signed volumetric flow must be finite")
        fit_fields = (self.hydraulic_parameter_fit_result_sha256, self.hydraulic_parameter_fit_evidence,
                      self.hydraulic_parameter_fit_applicability_reviewed)
        if self.hydraulic_parameter_fit_result_sha256 is None:
            if self.resistance_correction_multiplier != 1.0 or self.inertance_correction_multiplier != 1.0 or any(value is not None and value is not False for value in fit_fields):
                raise ValueError("non-default hydraulic corrections require a digest-bound fit result and review")
        else:
            evidence = self.hydraulic_parameter_fit_evidence
            if (evidence is None or evidence.sha256 != self.hydraulic_parameter_fit_result_sha256
                    or evidence.source_id != "calibration.crevice_slit_hydraulic_law_parameters"
                    or not self.hydraulic_parameter_fit_applicability_reviewed):
                raise ValueError("hydraulic fit multipliers require matching fit-result Evidence and transfer review")
        if not any(row.source_id == self.geometry_provider_id and row.sha256 == self.geometry_record_sha256 for row in self.evidence):
            raise ValueError("geometry provider and record digest must be linked to matching Evidence")
        if not any(row.source_id == self.pressure_provider_id and row.sha256 == self.pressure_record_sha256 for row in self.evidence):
            raise ValueError("pressure provider and record digest must be linked to matching Evidence")
        if not any(
            row.source_id == self.fluid_property_provider_id and row.sha256 == self.fluid_property_record_sha256
            for row in self.evidence
        ):
            raise ValueError("fluid-property provider and record digest must be linked to matching Evidence")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify the declared license or permission basis")
        return self


def evaluate_planar_slit_transient_hydraulic_history(
    request: PlanarSlitTransientHydraulicHistory,
) -> Calculation:
    """Integrate I dQ/dt + R Q = Δp exactly for each constant-input interval.

    For series slit cells, ``R = Σ 12 μ L/(w h³)`` and
    ``I = Σ ρ L/(w h)``. The relation is a reduced lumped model with
    quasi-steady laminar resistance, not an unsteady Navier–Stokes solution.
    """
    request_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "time_basis": request.time_basis,
        "input_sha256": request_sha,
        "geometry_provider_id": request.geometry_provider_id,
        "geometry_provider_revision": request.geometry_provider_revision,
        "geometry_record_sha256": request.geometry_record_sha256,
        "pressure_provider_id": request.pressure_provider_id,
        "pressure_provider_revision": request.pressure_provider_revision,
        "pressure_record_sha256": request.pressure_record_sha256,
        "fluid_property_provider_id": request.fluid_property_provider_id,
        "fluid_property_provider_revision": request.fluid_property_provider_revision,
        "fluid_property_record_sha256": request.fluid_property_record_sha256,
        "resistance_correction_multiplier": request.resistance_correction_multiplier,
        "inertance_correction_multiplier": request.inertance_correction_multiplier,
        "hydraulic_parameter_fit_result_sha256": request.hydraulic_parameter_fit_result_sha256,
        "usage_license_id": request.usage_license_id,
        "momentum_model": "piecewise_constant_lumped_inertance_plus_quasisteady_laminar_slit_resistance",
    }
    reviews = {
        "geometry_clock_and_grid_reviewed": request.geometry_clock_and_grid_reviewed,
        "pressure_reference_sign_and_clock_reviewed": request.pressure_reference_sign_and_clock_reviewed,
        "incompressible_newtonian_property_support_reviewed": request.incompressible_newtonian_property_support_reviewed,
        "wide_slit_aspect_ratio_reviewed": request.wide_slit_aspect_ratio_reviewed,
        "laminar_fully_developed_resistance_reviewed": request.laminar_fully_developed_resistance_reviewed,
        "unsteady_lumped_inertance_applicability_reviewed": request.unsteady_lumped_inertance_applicability_reviewed,
        "signed_flow_reversal_reviewed": request.signed_flow_reversal_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, passed in reviews.items() if not passed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    flow = float(request.initial_volumetric_flow_m3_s)
    flow_history = [flow]
    cumulative_volume = 0.0
    cumulative_volume_history = [cumulative_volume]
    intervals = []
    reversals = []
    try:
        for index, (start, end, apertures, delta_p) in enumerate(zip(
            request.time_s[:-1], request.time_s[1:], request.aperture_by_interval_m,
            request.pressure_drop_by_interval_Pa, strict=True,
        )):
            duration = end - start
            width = float(request.transverse_width_m)
            gaps = tuple(float(value) for value in apertures)
            lengths = tuple(float(value) for value in request.cell_widths_m)
            aspect_ratios = tuple(width / gap for gap in gaps)
            if any(not math.isfinite(value) or value < request.minimum_width_to_aperture_ratio for value in aspect_ratios):
                raise ValueError("a cell is outside the reviewed wide-slit aspect-ratio support")

            resistance_terms = tuple(
                12.0 * request.dynamic_viscosity_Pa_s * length / (width * gap**3)
                for length, gap in zip(lengths, gaps, strict=True)
            )
            inertance_terms = tuple(
                request.density_kg_m3 * length / (width * gap)
                for length, gap in zip(lengths, gaps, strict=True)
            )
            resistance = math.fsum(resistance_terms) * request.resistance_correction_multiplier
            inertance = math.fsum(inertance_terms) * request.inertance_correction_multiplier
            if not math.isfinite(resistance) or resistance <= 0.0 or not math.isfinite(inertance) or inertance <= 0.0:
                raise ArithmeticError("slit resistance or inertance exceeded finite positive support")

            rate = resistance / inertance
            equilibrium_flow = float(delta_p) / resistance
            exponent = rate * duration
            if not math.isfinite(rate) or rate <= 0.0 or not math.isfinite(equilibrium_flow):
                raise ArithmeticError("momentum decay rate or equilibrium flow exceeded finite support")
            if exponent > 745.0:
                decay = 0.0
                integral_kernel = 1.0 / rate
            else:
                decay = math.exp(-exponent)
                integral_kernel = -math.expm1(-exponent) / rate
            flow_end = equilibrium_flow + (flow - equilibrium_flow) * decay
            integrated_flow = equilibrium_flow * duration + (flow - equilibrium_flow) * integral_kernel
            next_cumulative_volume = math.fsum((cumulative_volume, integrated_flow))
            if not all(math.isfinite(value) for value in (flow_end, integrated_flow, next_cumulative_volume)):
                raise ArithmeticError("flow state or integrated volume exceeded finite numeric support")

            flow_scale = max(abs(flow), abs(flow_end))
            maximum_reynolds = 2.0 * request.density_kg_m3 * flow_scale / (width * request.dynamic_viscosity_Pa_s)
            if not math.isfinite(maximum_reynolds) or maximum_reynolds > request.maximum_reviewed_reynolds_number:
                raise ValueError("laminar Reynolds support exceeded during the interval")

            if flow * flow_end < 0.0:
                ratio = -equilibrium_flow / (flow - equilibrium_flow)
                if ratio <= 0.0 or ratio >= 1.0:
                    raise ArithmeticError("flow-reversal root is outside a valid logarithmic domain")
                reversal_time = -math.log(ratio) / rate
                if 0.0 < reversal_time < duration:
                    reversals.append({"interval_index": index, "time_s": start + reversal_time})

            cell_velocities_end = [flow_end / (width * gap) for gap in gaps]
            intervals.append({
                "interval_index": index,
                "start_time_s": start,
                "end_time_s": end,
                "pressure_drop_Pa": delta_p,
                "cell_aperture_m": list(gaps),
                "series_resistance_Pa_s_m3": resistance,
                "series_inertance_Pa_s2_m3": inertance,
                "momentum_relaxation_rate_s_inv": rate,
                "momentum_relaxation_time_s": 1.0 / rate,
                "equilibrium_volumetric_flow_m3_s": equilibrium_flow,
                "start_volumetric_flow_m3_s": flow,
                "end_volumetric_flow_m3_s": flow_end,
                "mean_volumetric_flow_m3_s": integrated_flow / duration,
                "integrated_signed_volume_m3": integrated_flow,
                "cumulative_signed_volume_m3_at_end": next_cumulative_volume,
                "end_cell_velocity_m_s": cell_velocities_end,
                "maximum_reynolds_number": maximum_reynolds,
                "minimum_width_to_aperture_ratio": min(aspect_ratios),
            })
            flow = flow_end
            flow_history.append(flow)
            cumulative_volume = next_cumulative_volume
            cumulative_volume_history.append(cumulative_volume)
    except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "completed_interval_count": len(intervals),
            "time_prefix_s": list(request.time_s[: len(intervals) + 1]),
            "volumetric_flow_prefix_m3_s": flow_history,
            "cumulative_signed_volume_prefix_m3": cumulative_volume_history,
            "interval_results": intervals,
            "flow_reversal_events": reversals,
            "failed_interval_index": len(intervals),
            "reason": str(error),
        })

    return Calculation(values=base | {
        "time_s": list(request.time_s),
        "cell_ids": list(request.cell_ids),
        "volumetric_flow_history_m3_s": flow_history,
        "cumulative_signed_volume_history_m3": cumulative_volume_history,
        "interval_results": intervals,
        "flow_reversal_events": reversals,
        "cell_count": len(request.cell_widths_m),
        "geometry_is_exogenous_piecewise_constant": True,
        "pressure_is_exogenous_piecewise_constant": True,
        "interval_solution": "exact_for_each_constant_coefficient_lumped_first_order_momentum_interval",
        "time_support_semantics": "closed_declared_output_window; no extrapolation beyond supplied knots",
        "reduced_model_scope": "uniform_signed_flow_through_series_wide_slit_cells_with_quasisteady_resistance",
    }, notes=(
        "The model solves I dQ/dt + R Q = pressure_drop on each half-open interval, carrying volumetric flow continuously across caller-declared input jumps.",
        "Resistance is the fully developed parallel-plate laminar relation and inertance is a one-dimensional lumped fluid-column approximation; this is not transient Navier–Stokes or compressible flow.",
        "Pressure, aperture, density and viscosity are caller inputs. No aperture evolution, transport, chemistry, corrosion rate, seal acceptance or qualification is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "corrosion.planar_slit_transient_hydraulic_history",
        PlanarSlitTransientHydraulicHistory,
        evaluate_planar_slit_transient_hydraulic_history,
        {
            "volumetric_flow_history_m3_s[]": "m^3/s",
            "interval_results[].integrated_signed_volume_m3": "m^3",
            "interval_results[].end_cell_velocity_m_s[]": "m/s",
            "interval_results[].series_resistance_Pa_s_m3": "Pa*s/m^3",
            "interval_results[].series_inertance_Pa_s2_m3": "Pa*s^2/m^3",
            "interval_results[].maximum_reynolds_number": "1",
            "flow_reversal_events[].time_s": "s",
        },
        (
            "Exact interval propagation for the caller-reviewed reduced balance I dQ/dt + R Q = pressure_drop with piecewise-constant pressure and aperture.",
            "Uses a quasi-steady fully developed laminar slit resistance and lumped incompressible fluid inertance; it is not a Navier–Stokes, compressible, roughness, entrance, or moving-boundary solver.",
        ),
        ("caller_lumped_slit_inertance_resistance",),
        qualification="user_model",
    )]
