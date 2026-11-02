"""Axial parallel-sector bolted-joint equilibrium from caller-owned properties."""

from __future__ import annotations

import math
from bisect import bisect_right
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


MODEL_ID = "fabrication.gasket_multi_bolt_sector_equilibrium"
SOURCE_ID = "caller_multi_bolt_parallel_sector_joint_equilibrium"


class GasketForceCompressionPoint(Contract):
    """Caller-measured compression-force point for one gasket sector."""

    compression_m: Nonnegative
    compressive_force_N: Nonnegative


class GasketJointBolt(Contract):
    bolt_id: str = Field(min_length=1)
    initial_preload_N: Positive
    axial_stiffness_N_m: Positive
    tensile_stress_area_m2: Positive
    evidence_source_ids: tuple[str, ...] = Field(min_length=1)


class GasketJointSector(Contract):
    sector_id: str = Field(min_length=1)
    contact_area_m2: Positive
    initial_compression_m: Positive
    force_compression_curve: tuple[GasketForceCompressionPoint, ...] = Field(min_length=2, max_length=1000)
    evidence_source_ids: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def increasing_supported_curve(self):
        curve = self.force_compression_curve
        if curve[0].compression_m != 0 or curve[0].compressive_force_N != 0:
            raise ValueError("each sector curve must start at zero compression and zero force")
        if any(
            right.compression_m <= left.compression_m
            or right.compressive_force_N <= left.compressive_force_N
            for left, right in zip(curve[:-1], curve[1:], strict=True)
        ):
            raise ValueError("gasket compression and force coordinates must increase strictly")
        if self.initial_compression_m > curve[-1].compression_m:
            raise ValueError("initial gasket compression exceeds the supplied curve support")
        if not all(math.isfinite(p.compression_m) and math.isfinite(p.compressive_force_N) for p in curve):
            raise ValueError("gasket curve coordinates must be finite")
        return self


class GasketJointLoadStep(Contract):
    step_id: str = Field(min_length=1)
    time_s: Nonnegative
    external_separating_force_N: float
    bolt_free_length_change_m: tuple[float, ...]
    gasket_free_thickness_change_m: tuple[float, ...]


class GasketMultiBoltSectorEquilibrium(Contract):
    """Quasi-static common-opening equilibrium for parallel bolt/gasket sectors."""

    schema_version: Literal["matintegrity.gasket_multi_bolt_sector_equilibrium.v1"] = (
        "matintegrity.gasket_multi_bolt_sector_equilibrium.v1"
    )
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    bolts: tuple[GasketJointBolt, ...] = Field(min_length=2, max_length=256)
    gasket_sectors: tuple[GasketJointSector, ...] = Field(min_length=1, max_length=256)
    load_steps: tuple[GasketJointLoadStep, ...] = Field(min_length=1, max_length=10000)
    minimum_opening_m: float
    maximum_opening_m: Positive
    initial_force_balance_tolerance_N: Positive
    force_balance_tolerance_N: Positive
    opening_tolerance_m: Positive
    maximum_bisection_iterations: int = Field(default=160, ge=1, le=1000)
    common_axial_opening_assumption_reviewed: bool
    per_bolt_preload_stiffness_area_basis_reviewed: bool
    sector_force_curve_support_reviewed: bool
    tension_only_bolts_and_compression_only_gasket_reviewed: bool
    load_step_interpolation_and_quasistatic_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_parallel_joint(self):
        if not math.isfinite(self.minimum_opening_m) or self.minimum_opening_m >= 0:
            raise ValueError("minimum opening must be finite and below the assembled zero-opening state")
        if len({row.bolt_id for row in self.bolts}) != len(self.bolts):
            raise ValueError("bolt identifiers must be unique")
        if len({row.sector_id for row in self.gasket_sectors}) != len(self.gasket_sectors):
            raise ValueError("gasket sector identifiers must be unique")
        if len({row.step_id for row in self.load_steps}) != len(self.load_steps):
            raise ValueError("load-step identifiers must be unique")
        if any(not math.isfinite(row.external_separating_force_N) for row in self.load_steps):
            raise ValueError("external separating forces must be finite")
        bolt_count, sector_count = len(self.bolts), len(self.gasket_sectors)
        for step in self.load_steps:
            if len(step.bolt_free_length_change_m) != bolt_count:
                raise ValueError("each load step needs one free-length change per ordered bolt")
            if len(step.gasket_free_thickness_change_m) != sector_count:
                raise ValueError("each load step needs one free-thickness change per ordered gasket sector")
            if not all(math.isfinite(v) for v in (*step.bolt_free_length_change_m, *step.gasket_free_thickness_change_m)):
                raise ValueError("free-length and free-thickness changes must be finite")
        if self.load_steps[0].time_s != 0 or self.load_steps[0].external_separating_force_N != 0:
            raise ValueError("the first step must be the zero-time, zero-external-load assembled reference")
        if any(self.load_steps[0].bolt_free_length_change_m) or any(
            self.load_steps[0].gasket_free_thickness_change_m
        ):
            raise ValueError("the first reference step must have zero free thermal/material changes")
        if any(right.time_s <= left.time_s for left, right in zip(self.load_steps[:-1], self.load_steps[1:], strict=True)):
            raise ValueError("load-step times must strictly increase")
        if self.maximum_opening_m <= 0 or self.minimum_opening_m >= self.maximum_opening_m:
            raise ValueError("opening bounds must straddle the assembled zero-opening state")
        evidence_ids = {row.source_id for row in self.evidence}
        required_ids = {
            *[source_id for bolt in self.bolts for source_id in bolt.evidence_source_ids],
            *[source_id for sector in self.gasket_sectors for source_id in sector.evidence_source_ids],
        }
        if not required_ids <= evidence_ids:
            raise ValueError("every preload, stiffness, area and gasket curve source must appear in request Evidence")
        return self


def _interpolate_curve(curve: tuple[GasketForceCompressionPoint, ...], compression_m: float) -> tuple[float, float]:
    """Return piecewise-linear force and tangent stiffness without extrapolation."""
    if compression_m <= 0:
        return 0.0, 0.0
    if compression_m > curve[-1].compression_m:
        raise ValueError("required gasket compression exceeds caller curve support")
    xs = [point.compression_m for point in curve]
    index = min(max(bisect_right(xs, compression_m) - 1, 0), len(curve) - 2)
    left, right = curve[index], curve[index + 1]
    slope = (right.compressive_force_N - left.compressive_force_N) / (right.compression_m - left.compression_m)
    force = left.compressive_force_N + slope * (compression_m - left.compression_m)
    return force, slope


def evaluate_gasket_multi_bolt_sector_equilibrium(
    request: GasketMultiBoltSectorEquilibrium,
) -> Calculation:
    """Solve each ordered load step's scalar axial equilibrium by bounded bisection.

    Positive opening increases tension in a bolt and releases gasket compression.
    Caller free bolt expansion subtracts from bolt extension; free gasket swelling
    adds to gasket compression. The gasket curve is piecewise linear as supplied.
    """
    input_digest = canonical_digest(request.model_dump(mode="json"))
    if not all((
        request.common_axial_opening_assumption_reviewed,
        request.per_bolt_preload_stiffness_area_basis_reviewed,
        request.sector_force_curve_support_reviewed,
        request.tension_only_bolts_and_compression_only_gasket_reviewed,
        request.load_step_interpolation_and_quasistatic_reviewed,
        request.computational_use_authorized,
    )):
        return Calculation(
            status="needs_data",
            values={"assessment_id": request.assessment_id, "input_sha256": input_digest},
            notes=("All model-basis and computational-use reviews are required.",),
        )

    initial_gasket_forces = []
    try:
        for sector in request.gasket_sectors:
            force, _ = _interpolate_curve(sector.force_compression_curve, sector.initial_compression_m)
            initial_gasket_forces.append(force)
    except ValueError as error:
        return Calculation(
            status="out_of_scope",
            values={"assessment_id": request.assessment_id, "input_sha256": input_digest},
            notes=(str(error),),
        )
    initial_bolt_force = math.fsum(row.initial_preload_N for row in request.bolts)
    initial_gasket_force = math.fsum(initial_gasket_forces)
    initial_residual = initial_bolt_force - initial_gasket_force
    if abs(initial_residual) > request.initial_force_balance_tolerance_N:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": request.assessment_id,
                "input_sha256": input_digest,
                "initial_bolt_force_sum_N": initial_bolt_force,
                "initial_gasket_force_sum_N": initial_gasket_force,
                "initial_force_balance_residual_N": initial_residual,
            },
            notes=("Initial per-bolt preload and sector gasket reactions do not close within the caller tolerance.",),
        )

    step_results: list[dict] = []
    for step in request.load_steps:
        # At the lower opening bound, every bolt and every gasket curve must remain supported.
        lower = request.minimum_opening_m
        for bolt, free_change in zip(request.bolts, step.bolt_free_length_change_m, strict=True):
            lower = max(lower, free_change - bolt.initial_preload_N / bolt.axial_stiffness_N_m)
        for sector, free_change in zip(request.gasket_sectors, step.gasket_free_thickness_change_m, strict=True):
            lower = max(
                lower,
                sector.initial_compression_m + free_change - sector.force_compression_curve[-1].compression_m,
            )
        upper = request.maximum_opening_m
        if lower > upper:
            return Calculation(
                status="out_of_scope",
                values={"assessment_id": request.assessment_id, "input_sha256": input_digest, "failed_step_id": step.step_id},
                notes=("Caller opening bounds and component curve supports do not overlap.",),
            )

        def state(opening_m: float):
            bolt_rows = []
            for bolt, free_change in zip(request.bolts, step.bolt_free_length_change_m, strict=True):
                extension = opening_m - free_change
                force = max(0.0, bolt.initial_preload_N + bolt.axial_stiffness_N_m * extension)
                stress = force / bolt.tensile_stress_area_m2
                if not math.isfinite(force) or not math.isfinite(stress):
                    raise OverflowError("bolt force or nominal stress is outside finite floating-point support")
                bolt_rows.append({
                    "bolt_id": bolt.bolt_id,
                    "extension_m": extension,
                    "tensile_force_N": force,
                    "nominal_tensile_stress_Pa": stress,
                    "tension_active": force > 0.0,
                })
            sector_rows = []
            for sector, free_change in zip(request.gasket_sectors, step.gasket_free_thickness_change_m, strict=True):
                compression = sector.initial_compression_m + free_change - opening_m
                force, tangent = _interpolate_curve(sector.force_compression_curve, compression)
                pressure = force / sector.contact_area_m2
                if not math.isfinite(pressure) or not math.isfinite(tangent):
                    raise OverflowError("sector pressure or tangent is outside finite floating-point support")
                sector_rows.append({
                    "sector_id": sector.sector_id,
                    "compression_m": max(0.0, compression),
                    "gap_m": max(0.0, -compression),
                    "compressive_force_N": force,
                    "mean_contact_pressure_Pa": pressure,
                    "tangent_stiffness_N_m": tangent,
                    "contact_active": compression > 0.0,
                })
            bolt_sum = math.fsum(row["tensile_force_N"] for row in bolt_rows)
            gasket_sum = math.fsum(row["compressive_force_N"] for row in sector_rows)
            residual = bolt_sum - gasket_sum - step.external_separating_force_N
            tangent = math.fsum(
                bolt.axial_stiffness_N_m
                for bolt, row in zip(request.bolts, bolt_rows, strict=True)
                if row["tension_active"]
            ) + math.fsum(row["tangent_stiffness_N_m"] for row in sector_rows)
            if not all(math.isfinite(value) for value in (bolt_sum, gasket_sum, residual, tangent)):
                raise OverflowError("equilibrium residual or tangent is outside finite floating-point support")
            return residual, bolt_rows, sector_rows, bolt_sum, gasket_sum, tangent

        try:
            low = state(lower)
            high = state(upper)
        except ValueError as error:
            return Calculation(
                status="out_of_scope",
                values={"assessment_id": request.assessment_id, "input_sha256": input_digest, "failed_step_id": step.step_id},
                notes=(str(error),),
            )
        if low[0] > request.force_balance_tolerance_N or high[0] < -request.force_balance_tolerance_N:
            return Calculation(
                status="out_of_scope",
                values={
                    "assessment_id": request.assessment_id,
                    "input_sha256": input_digest,
                    "failed_step_id": step.step_id,
                    "lower_bound_residual_N": low[0],
                    "upper_bound_residual_N": high[0],
                    "opening_support_m": [lower, upper],
                },
                notes=("No force-balance root is bracketed by caller opening bounds and supplied component curves.",),
            )
        lo, hi = lower, upper
        try:
            for _ in range(request.maximum_bisection_iterations):
                mid = lo + 0.5 * (hi - lo)
                current = state(mid)
                if abs(current[0]) <= request.force_balance_tolerance_N or hi - lo <= request.opening_tolerance_m:
                    break
                if current[0] < 0:
                    lo = mid
                else:
                    hi = mid
            opening = mid
            current = state(opening)
        except (ArithmeticError, ValueError) as error:
            return Calculation(
                status="out_of_scope",
                values={"assessment_id": request.assessment_id, "input_sha256": input_digest, "failed_step_id": step.step_id},
                notes=(f"Finite equilibrium calculation failed: {error}",),
            )
        if current[5] <= 0 or abs(current[0]) > request.force_balance_tolerance_N:
            return Calculation(
                status="out_of_scope",
                values={"assessment_id": request.assessment_id, "input_sha256": input_digest, "failed_step_id": step.step_id},
                notes=("The bounded equilibrium is not unique or did not meet force tolerance within the iteration limit.",),
            )
        residual, bolt_rows, sector_rows, bolt_sum, gasket_sum, tangent = current
        step_results.append({
            "step_id": step.step_id,
            "time_s": step.time_s,
            "opening_m": opening,
            "bolt_tensile_force_sum_N": bolt_sum,
            "gasket_compressive_force_sum_N": gasket_sum,
            "external_separating_force_N": step.external_separating_force_N,
            "force_balance_residual_N": residual,
            "equilibrium_tangent_N_m": tangent,
            "bolts": bolt_rows,
            "gasket_sectors": sector_rows,
        })

    return Calculation(
        values={
            "assessment_id": request.assessment_id,
            "joint_id": request.joint_id,
            "physical_scope_id": request.physical_scope_id,
            "input_sha256": input_digest,
            "initial_force_balance_residual_N": initial_residual,
            "step_count": len(step_results),
            "steps": step_results,
            "interpretation": "caller-calibrated quasi-static parallel axial sectors; no flange interaction, leakage, seal acceptance, or qualification",
        },
        notes=(
            "Piecewise-linear gasket force curves and linear tensile-only bolts were solved at each supplied knot by bounded bisection.",
            "Load histories between knots, flange bending/coupling, gasket shear, viscoelastic memory, local stresses beyond nominal bolt tension, leakage, and acceptance are not inferred.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            GasketMultiBoltSectorEquilibrium,
            evaluate_gasket_multi_bolt_sector_equilibrium,
            {
                "time_s": "s",
                "opening_m": "m",
                "bolt_tensile_force_sum_N": "N",
                "gasket_compressive_force_sum_N": "N",
                "force_balance_residual_N": "N",
                "nominal_tensile_stress_Pa": "Pa",
                "mean_contact_pressure_Pa": "Pa",
            },
            (
                "Each bolt is an independent caller-specified linear axial spring that carries tension only; each gasket sector carries compression only.",
                "All bolts and sectors share one axial opening; cross-sector flange bending and spatial interaction are excluded.",
                "Gasket force-compression curves are linearly interpolated only inside their supplied support and never extrapolated.",
                "Each load step is an independent quasi-static equilibrium relative to the declared zero-time assembly preload; no relaxation or path memory is included.",
                "Bolt stress is nominal axial force divided by caller-supplied tensile area and is not a thread-root/local stress or allowable comparison.",
            ),
            (SOURCE_ID,),
        )
    ]
