"""Integrate caller-measured gasket compression hysteresis loops."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fabrication.gasket_compression_hysteresis_energy"
MAX_TOTAL_SAMPLES = 2_000_000


class GasketCompressionLoop(Contract):
    loop_id: str = Field(min_length=1)
    sample_ids: tuple[str, ...] = Field(min_length=3, max_length=200000)
    time_s: tuple[Nonnegative, ...] = Field(min_length=3, max_length=200000)
    compression_displacement_m: tuple[Nonnegative, ...] = Field(min_length=3, max_length=200000)
    compressive_force_N: tuple[Nonnegative, ...] = Field(min_length=3, max_length=200000)
    repeat_count: StrictInt = Field(gt=0, le=2**53)

    @model_validator(mode="after")
    def aligned_ordered_loop(self):
        n = len(self.sample_ids)
        if len(set(self.sample_ids)) != n:
            raise ValueError("sample IDs must be unique within each measured loop")
        if len(self.time_s) != n or len(self.compression_displacement_m) != n or len(self.compressive_force_N) != n:
            raise ValueError("time, displacement, force and sample IDs must align")
        if any(right <= left for left, right in zip(self.time_s, self.time_s[1:])):
            raise ValueError("loop sample times must strictly increase")
        if any(not math.isfinite(value) for values in (
            self.time_s, self.compression_displacement_m, self.compressive_force_N
        ) for value in values):
            raise ValueError("measured loop values must be finite")
        return self


class GasketCompressionHysteresisEnergy(Contract):
    """Energy summary for caller-measured compression/unloading cycles."""

    schema_version: Literal["matintegrity.gasket_compression_hysteresis_energy.v1"] = (
        "matintegrity.gasket_compression_hysteresis_energy.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    temperature_K: Positive
    initial_gasket_thickness_m: Positive
    loaded_area_m2: Positive
    loops: tuple[GasketCompressionLoop, ...] = Field(min_length=1, max_length=10000)
    maximum_endpoint_displacement_error_m: Nonnegative
    maximum_endpoint_force_error_N: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    measurement_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    measured_displacement_is_gasket_compression_reviewed: bool
    force_area_temperature_and_sign_reviewed: bool
    loop_boundaries_and_repeat_counts_reviewed: bool
    representativeness_and_condition_transfer_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def bind_measurement_record(self):
        if len({row.loop_id for row in self.loops}) != len(self.loops):
            raise ValueError("loop IDs must be unique")
        if sum(len(row.sample_ids) for row in self.loops) > MAX_TOTAL_SAMPLES:
            raise ValueError("total measured samples exceed the contract budget")
        if sum(row.repeat_count for row in self.loops) > 2**53:
            raise ValueError("total repeated cycle count exceeds exact integer support")
        record = {
            "physical_scope_id": self.physical_scope_id,
            "material_condition_id": self.material_condition_id,
            "specimen_id": self.specimen_id,
            "temperature_K": self.temperature_K,
            "initial_gasket_thickness_m": self.initial_gasket_thickness_m,
            "loaded_area_m2": self.loaded_area_m2,
            "provider_id": self.provider_id,
            "provider_revision": self.provider_revision,
            "loops": [row.model_dump(mode="json") for row in self.loops],
        }
        if canonical_digest(record) != self.measurement_record_sha256:
            raise ValueError("measurement record digest does not bind specimen and loop samples")
        if not any(
            row.source_id == self.provider_id
            and row.sha256 == self.measurement_record_sha256
            and row.license_id == self.usage_license_id
            for row in self.evidence
        ):
            raise ValueError("measurement Evidence must pin the data and computational-use license")
        return self


def evaluate_gasket_compression_hysteresis_energy(request: GasketCompressionHysteresisEnergy) -> Calculation:
    """Integrate each measured loop by trapezoidal work under piecewise-linear force/displacement paths."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "material_condition_id": request.material_condition_id,
        "specimen_id": request.specimen_id,
        "temperature_K": request.temperature_K,
        "measurement_record_sha256": request.measurement_record_sha256,
        "input_sha256": digest,
        "model_id": MODEL_ID,
    }
    reviews = {
        "measured_displacement_is_gasket_compression_reviewed": request.measured_displacement_is_gasket_compression_reviewed,
        "force_area_temperature_and_sign_reviewed": request.force_area_temperature_and_sign_reviewed,
        "loop_boundaries_and_repeat_counts_reviewed": request.loop_boundaries_and_repeat_counts_reviewed,
        "representativeness_and_condition_transfer_reviewed": request.representativeness_and_condition_transfer_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    volume = request.loaded_area_m2 * request.initial_gasket_thickness_m
    if not math.isfinite(volume) or volume <= 0:
        return Calculation(status="out_of_scope", values=base | {"reason": "specimen_volume_outside_finite_support"})
    rows = []
    total_weighted_dissipation_J = 0.0
    total_weighted_dissipation_density = 0.0
    total_cycles = 0
    for loop in request.loops:
        displacement_error = abs(loop.compression_displacement_m[-1] - loop.compression_displacement_m[0])
        force_error = abs(loop.compressive_force_N[-1] - loop.compressive_force_N[0])
        if not math.isfinite(displacement_error) or not math.isfinite(force_error):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "loop_endpoint_closure_error_exceeded_finite_support",
                "loop_id": loop.loop_id,
                "completed_loop_count": len(rows),
            })
        if (displacement_error > request.maximum_endpoint_displacement_error_m
                or force_error > request.maximum_endpoint_force_error_N):
            return Calculation(status="needs_data", values=base | {
                "reason": "measured_loop_endpoint_closure_exceeds_caller_tolerance",
                "loop_id": loop.loop_id,
                "displacement_closure_error_m": displacement_error,
                "force_closure_error_N": force_error,
                "completed_loop_count": len(rows),
            })
        segment_work = []
        loading_work = []
        returned_work = []
        for index in range(len(loop.sample_ids) - 1):
            delta_displacement = loop.compression_displacement_m[index + 1] - loop.compression_displacement_m[index]
            average_force = 0.5 * (loop.compressive_force_N[index] + loop.compressive_force_N[index + 1])
            work = average_force * delta_displacement
            if not math.isfinite(work):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "measured_segment_work_exceeded_finite_support",
                    "loop_id": loop.loop_id,
                    "completed_loop_count": len(rows),
                })
            segment_work.append(work)
            loading_work.append(max(work, 0.0))
            returned_work.append(max(-work, 0.0))
        try:
            signed_loop_work_J = math.fsum(segment_work)
            dissipated_energy_J = abs(signed_loop_work_J)
            loading_work_J = math.fsum(loading_work)
            returned_work_J = math.fsum(returned_work)
            dissipated_density = dissipated_energy_J / volume
            loading_density = loading_work_J / volume
            returned_density = returned_work_J / volume
            loss_ratio = dissipated_energy_J / loading_work_J if loading_work_J > 0.0 else None
            recovery_ratio = returned_work_J / loading_work_J if loading_work_J > 0.0 else None
        except (ArithmeticError, OverflowError, ValueError):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "loop_energy_integration_exceeded_finite_support",
                "loop_id": loop.loop_id,
                "completed_loop_count": len(rows),
            })
        if not all(math.isfinite(value) for value in (
            dissipated_energy_J, loading_work_J, returned_work_J,
            dissipated_density, loading_density, returned_density,
        )) or any(value is not None and not math.isfinite(value) for value in (loss_ratio, recovery_ratio)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "loop_energy_summary_exceeded_finite_support",
                "loop_id": loop.loop_id,
                "completed_loop_count": len(rows),
            })
        rows.append({
            "loop_id": loop.loop_id,
            "repeat_count": loop.repeat_count,
            "sample_count": len(loop.sample_ids),
            "displacement_closure_error_m": displacement_error,
            "force_closure_error_N": force_error,
            "signed_loop_work_J": signed_loop_work_J,
            "dissipated_energy_J_per_cycle": dissipated_energy_J,
            "dissipated_energy_density_J_m3_per_cycle": dissipated_density,
            "positive_compression_work_J_per_cycle": loading_work_J,
            "positive_compression_work_density_J_m3_per_cycle": loading_density,
            "unloading_return_work_J_per_cycle": returned_work_J,
            "unloading_return_work_density_J_m3_per_cycle": returned_density,
            "hysteresis_loss_fraction_of_positive_work": loss_ratio,
            "unloading_return_fraction_of_positive_work": recovery_ratio,
            "repeated_dissipated_energy_J": dissipated_energy_J * loop.repeat_count,
            "repeated_dissipated_energy_density_J_m3": dissipated_density * loop.repeat_count,
        })
        total_weighted_dissipation_J += dissipated_energy_J * loop.repeat_count
        total_weighted_dissipation_density += dissipated_density * loop.repeat_count
        total_cycles += loop.repeat_count
    if not all(math.isfinite(value) for value in (total_weighted_dissipation_J, total_weighted_dissipation_density)):
        return Calculation(status="out_of_scope", values=base | {"reason": "campaign_energy_exceeded_finite_support"})
    return Calculation(values=base | {
        "loop_count": len(rows),
        "total_repeated_cycles": total_cycles,
        "initial_gasket_thickness_m": request.initial_gasket_thickness_m,
        "loaded_area_m2": request.loaded_area_m2,
        "specimen_volume_m3": volume,
        "cycle_results": rows,
        "total_repeated_dissipated_energy_J": total_weighted_dissipation_J,
        "total_repeated_dissipated_energy_density_J_m3": total_weighted_dissipation_density,
        "constitutive_law_fitted": False,
        "fatigue_damage_or_life_inferred": False,
    }, notes=(
        "Each measured cycle is integrated as a piecewise-linear force-displacement path; force times displacement work is normalized by the caller undeformed specimen volume for energy density.",
        "The absolute signed closed-loop work is reported as loop dissipation; the result does not identify whether the loop area is intrinsic dissipation, recoverable stored energy or another measurement effect.",
        "Repeated cycle counts apply the same measured-loop energy only as caller-declared bookkeeping; no progressive material evolution or gasket-joint leakage is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketCompressionHysteresisEnergy,
        evaluate_gasket_compression_hysteresis_energy,
        {
            "cycle_results[].signed_loop_work_J": "J",
            "cycle_results[].dissipated_energy_J_per_cycle": "J",
            "cycle_results[].dissipated_energy_density_J_m3_per_cycle": "J/m^3",
            "cycle_results[].positive_compression_work_J_per_cycle": "J",
            "cycle_results[].unloading_return_work_J_per_cycle": "J",
            "cycle_results[].hysteresis_loss_fraction_of_positive_work": "1",
            "total_repeated_dissipated_energy_J": "J",
            "total_repeated_dissipated_energy_density_J_m3": "J/m^3",
        },
        (
            "Every cycle is a caller-segmented ordered compression force-displacement loop with a reviewed repeated count and closed endpoints.",
            "The path between measurement points is reconstructed as piecewise linear and integrated by the trapezoidal work rule.",
            "Energy is normalized by caller initial thickness times loaded area; no constitutive law or damage criterion is inferred.",
        ),
        (
            "caller_gasket_compression_force_displacement_loops",
            "caller_gasket_specimen_area_thickness_and_condition",
            "piecewise_linear_force_displacement_loop_work_integral",
            "closed_loop_work_as_measured_hysteresis_energy_summary",
        ),
        qualification="user_model",
    )]
