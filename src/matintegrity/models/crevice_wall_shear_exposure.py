"""Wall-shear descriptors composed from a pinned transient slit-flow result."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, canonical_digest
from ..registry import ModelSpec


class CreviceWallShearExposure(Contract):
    """Derive fully-developed wide-slit wall shear from an existing flow history.

    The source model solves a reduced lumped momentum balance. This API derives
    quasi-steady planar-slit wall shear from its exact interval flow trajectory;
    it adds no fluid or material law and does not predict erosion or corrosion.
    """

    schema_version: Literal["matintegrity.crevice_wall_shear_exposure.v1"] = (
        "matintegrity.crevice_wall_shear_exposure.v1"
    )
    assessment_id: str = Field(min_length=1)
    hydraulic_result: AssessmentResult
    hydraulic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_shear_relation_and_wide_slit_profile_reviewed: bool
    quasi_steady_wall_shear_on_lumped_flow_reviewed: bool
    shear_exposure_is_descriptor_only_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def pinned_hydraulic_source(self):
        result = self.hydraulic_result
        if result.model_id != "corrosion.planar_slit_transient_hydraulic_history" or result.status != "computed":
            raise ValueError("a computed planar-slit transient hydraulic result is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("hydraulic assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.hydraulic_result_sha256:
            raise ValueError("hydraulic result digest mismatch")
        inputs = result.inputs
        values = result.values
        if values.get("input_sha256") != canonical_digest(inputs):
            raise ValueError("hydraulic calculator input digest mismatch")
        times = inputs.get("time_s")
        intervals = values.get("interval_results")
        cell_ids = inputs.get("cell_ids")
        widths = inputs.get("cell_widths_m")
        if not isinstance(times, list) or len(times) < 2 or not isinstance(intervals, list):
            raise ValueError("hydraulic result lacks its ordered time and interval histories")
        if len(intervals) != len(times) - 1 or not isinstance(cell_ids, list) or len(cell_ids) != len(widths or []):
            raise ValueError("hydraulic result interval and cell histories are misaligned")
        if values.get("time_s") != times or values.get("cell_ids") != cell_ids:
            raise ValueError("hydraulic result clock or cell identities disagree with its input")
        for index, row in enumerate(intervals):
            if row.get("interval_index") != index or row.get("cell_aperture_m") != inputs["aperture_by_interval_m"][index]:
                raise ValueError("hydraulic interval identity or aperture differs from pinned input")
        # Confirm that the original source record identities have corresponding
        # digest-bearing Evidence before deriving another physical descriptor.
        evidence = inputs.get("evidence", [])
        for provider_key, record_key in (
            ("geometry_provider_id", "geometry_record_sha256"),
            ("pressure_provider_id", "pressure_record_sha256"),
            ("fluid_property_provider_id", "fluid_property_record_sha256"),
        ):
            if not any(
                item.get("source_id") == inputs.get(provider_key)
                and item.get("sha256") == inputs.get(record_key)
                for item in evidence if isinstance(item, dict)
            ):
                raise ValueError(f"hydraulic {provider_key} is not linked to source Evidence")
        return self


def crevice_wall_shear_exposure(request: CreviceWallShearExposure) -> Calculation:
    """Return signed and absolute wall-shear histories per slit cell.

    For each wide planar slit cell, tau_w(t)=6 mu Q(t)/(w h^2). The source
    trajectory is exponential within each constant-coefficient interval. Its
    absolute-flow integral is evaluated exactly, splitting at any recorded
    internal reversal root.
    """

    hydraulic = request.hydraulic_result
    source_values = hydraulic.values
    source_inputs = hydraulic.inputs
    result_digest = request.hydraulic_result_sha256
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": source_values.get("asset_id"),
        "location_id": source_values.get("location_id"),
        "physical_scope_id": source_values.get("physical_scope_id"),
        "hydraulic_model_id": hydraulic.model_id,
        "hydraulic_result_sha256": result_digest,
        "geometry_provider_id": source_inputs["geometry_provider_id"],
        "geometry_provider_revision": source_inputs["geometry_provider_revision"],
        "geometry_record_sha256": source_inputs["geometry_record_sha256"],
        "pressure_provider_id": source_inputs["pressure_provider_id"],
        "pressure_provider_revision": source_inputs["pressure_provider_revision"],
        "pressure_record_sha256": source_inputs["pressure_record_sha256"],
        "fluid_property_provider_id": source_inputs["fluid_property_provider_id"],
        "fluid_property_provider_revision": source_inputs["fluid_property_provider_revision"],
        "fluid_property_record_sha256": source_inputs["fluid_property_record_sha256"],
        "source_license_id": source_inputs["usage_license_id"],
    }
    reviews = {
        "wall_shear_relation_and_wide_slit_profile_reviewed": request.wall_shear_relation_and_wide_slit_profile_reviewed,
        "quasi_steady_wall_shear_on_lumped_flow_reviewed": request.quasi_steady_wall_shear_on_lumped_flow_reviewed,
        "shear_exposure_is_descriptor_only_reviewed": request.shear_exposure_is_descriptor_only_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    width = float(source_inputs["transverse_width_m"])
    viscosity = float(source_inputs["dynamic_viscosity_Pa_s"])
    times = source_inputs["time_s"]
    cell_ids = source_inputs["cell_ids"]
    cell_widths = source_inputs["cell_widths_m"]
    intervals = source_values["interval_results"]
    reversal_by_interval = {}
    for event in source_values.get("flow_reversal_events", []):
        reversal_by_interval.setdefault(event["interval_index"], []).append(event["time_s"])
    history = []
    cumulative_abs_shear_impulse = [0.0] * len(cell_ids)
    total_shear_evaluation_count = len(intervals) * len(cell_ids)
    if total_shear_evaluation_count > 2_000_000:
        return Calculation(status="out_of_scope", values=base | {"reason": "interval_by_cell_wall_shear_budget_exceeded"})

    try:
        for index, row in enumerate(intervals):
            start_s = float(times[index])
            end_s = float(times[index + 1])
            duration = end_s - start_s
            flow_start = float(row["start_volumetric_flow_m3_s"])
            flow_end = float(row["end_volumetric_flow_m3_s"])
            flow_integral = float(row["integrated_signed_volume_m3"])
            relaxation_rate = float(row["momentum_relaxation_rate_s_inv"])
            equilibrium_flow = float(row["equilibrium_volumetric_flow_m3_s"])
            absolute_volume = abs(flow_integral)
            reversal_times = reversal_by_interval.get(index, [])
            if len(reversal_times) > 1:
                raise ValueError("source interval reports more than one reversal for a first-order flow path")
            for reversal_s in reversal_times:
                elapsed_to_reversal = float(reversal_s) - start_s
                if not 0.0 < elapsed_to_reversal < duration:
                    raise ValueError("source reversal time is outside its hydraulic interval")
                amplitude = flow_start - equilibrium_flow
                before_reversal_volume = (
                    equilibrium_flow * elapsed_to_reversal
                    + amplitude * (-math.expm1(-relaxation_rate * elapsed_to_reversal)) / relaxation_rate
                )
                after_reversal_volume = flow_integral - before_reversal_volume
                absolute_volume = math.fsum((abs(before_reversal_volume), abs(after_reversal_volume)))
            cell_rows = []
            for cell_index, (cell_id, cell_length, aperture) in enumerate(zip(
                cell_ids, cell_widths, row["cell_aperture_m"], strict=True,
            )):
                shear_factor_Pa_s_m3 = 6.0 * viscosity / (width * float(aperture) ** 2)
                signed_impulse = shear_factor_Pa_s_m3 * flow_integral
                absolute_impulse = shear_factor_Pa_s_m3 * absolute_volume
                average_signed = signed_impulse / duration
                average_absolute = absolute_impulse / duration
                start_shear = shear_factor_Pa_s_m3 * flow_start
                end_shear = shear_factor_Pa_s_m3 * flow_end
                if not all(math.isfinite(value) for value in (
                    shear_factor_Pa_s_m3, signed_impulse, absolute_impulse,
                    average_signed, average_absolute, start_shear, end_shear,
                )):
                    raise ArithmeticError("wall-shear descriptor exceeded finite numeric support")
                cumulative_abs_shear_impulse[cell_index] = math.fsum((
                    cumulative_abs_shear_impulse[cell_index], absolute_impulse,
                ))
                cell_rows.append({
                    "cell_id": cell_id,
                    "cell_length_m": cell_length,
                    "aperture_m": aperture,
                    "start_signed_wall_shear_Pa": start_shear,
                    "end_signed_wall_shear_Pa": end_shear,
                    "time_average_signed_wall_shear_Pa": average_signed,
                    "time_average_absolute_wall_shear_Pa": average_absolute,
                    "signed_wall_shear_impulse_Pa_s": signed_impulse,
                    "absolute_wall_shear_impulse_Pa_s": absolute_impulse,
                    "cumulative_absolute_wall_shear_impulse_Pa_s": cumulative_abs_shear_impulse[cell_index],
                })
            history.append({
                "interval_index": index,
                "start_time_s": start_s,
                "end_time_s": end_s,
                "duration_s": duration,
                "start_volumetric_flow_m3_s": flow_start,
                "end_volumetric_flow_m3_s": flow_end,
                "integrated_signed_volume_m3": flow_integral,
                "integrated_absolute_volume_m3": absolute_volume,
                "internal_flow_reversal_times_s": reversal_times,
                "cells": cell_rows,
            })
    except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as error:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "completed_interval_count": len(history),
                "interval_history_prefix": history,
                "reason": str(error),
            },
            notes=("No complete wall-shear profile is reported when the source flow path cannot be integrated within its declared numerical support.",),
        )

    profile_digest = canonical_digest(history)
    return Calculation(
        values=base | {
            "time_s": list(times),
            "cell_ids": list(cell_ids),
            "dynamic_viscosity_Pa_s": viscosity,
            "transverse_width_m": width,
            "wall_shear_history": history,
            "wall_shear_history_sha256": profile_digest,
            "cumulative_absolute_wall_shear_impulse_by_cell_Pa_s": {
                cell_id: cumulative_abs_shear_impulse[index] for index, cell_id in enumerate(cell_ids)
            },
            "wall_shear_calculation": "fully_developed_wide_planar_slit_tau_w=6*mu*Q/(width*aperture^2); absolute exposure integrates the source exponential flow exactly and splits at its reported reversal event",
            "wall_shear_representation": "quasi_steady_profile_reconstructed_from_lumped_transient_flow",
            "missing_reviews": [],
        },
        notes=(
            "The calculation derives a local wall-shear descriptor for each cell from a digest-pinned reduced hydraulic history; signed and absolute time integrals are kept distinct.",
            "The profile assumes a fully developed wide slit and a quasi-steady parabolic velocity profile over the caller's lumped inertial flow trajectory. It does not infer turbulence, entrance effects, roughness, erosion, corrosion, damage, life or acceptance.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "corrosion.crevice_wall_shear_exposure",
        CreviceWallShearExposure,
        crevice_wall_shear_exposure,
        {
            "dynamic_viscosity_Pa_s": "Pa*s",
            "transverse_width_m": "m",
            "wall_shear_history[].start_time_s": "s",
            "wall_shear_history[].end_time_s": "s",
            "wall_shear_history[].integrated_signed_volume_m3": "m^3",
            "wall_shear_history[].integrated_absolute_volume_m3": "m^3",
            "wall_shear_history[].cells[].aperture_m": "m",
            "wall_shear_history[].cells[].start_signed_wall_shear_Pa": "Pa",
            "wall_shear_history[].cells[].end_signed_wall_shear_Pa": "Pa",
            "wall_shear_history[].cells[].time_average_absolute_wall_shear_Pa": "Pa",
            "wall_shear_history[].cells[].signed_wall_shear_impulse_Pa_s": "Pa*s",
            "wall_shear_history[].cells[].absolute_wall_shear_impulse_Pa_s": "Pa*s",
            "cumulative_absolute_wall_shear_impulse_by_cell_Pa_s": "Pa*s",
        },
        (
            "Derive wide-planar-slit wall shear per cell from a digest-pinned exact interval flow history; analytically integrate absolute shear exposure while honoring reported internal flow reversal.",
            "The wall velocity profile is quasi-steady and fully developed even though volumetric flow follows a lumped inertance model. This is a descriptor only; no erosion, corrosion or qualification law is included.",
        ),
        ("caller_crevice_laminar_wall_shear_exposure",),
        qualification="user_model",
    )]
