"""Exact-knot Lamé stress descriptors for caller-identified heat-exchanger tubes."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .assembly_calculations import TubeCondition
from .contracts import Calculation, Contract, Evidence, canonical_digest
from .models.mechanics import Cylinder, lame_cylinder
from .registry import ModelSpec

MODEL_ID = "integration.tube_bundle_lame_stress_history"
SOURCE_ID = "caller_reviewed_tube_bundle_pressure_stress_history"


class TubePressureKnot(Contract):
    """One exact pressure sample for one tube; pressure values are absolute Pa."""

    knot_id: str = Field(min_length=1, max_length=160)
    asset_id: str = Field(min_length=1, max_length=200)
    location_id: str = Field(min_length=1, max_length=200)
    exchanger_id: str = Field(min_length=1, max_length=200)
    bundle_id: str = Field(min_length=1, max_length=200)
    tube_id: str = Field(min_length=1, max_length=200)
    time_basis_id: str = Field(min_length=1, max_length=160)
    pressure_reference_basis_id: str = Field(min_length=1, max_length=200)
    time_s: float = Field(ge=0.0)
    internal_pressure_Pa: float = Field(ge=0.0)
    external_pressure_Pa: float = Field(ge=0.0)
    source_id: str = Field(min_length=1, max_length=160)
    source_record_id: str = Field(min_length=1, max_length=200)
    source_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def evidence_pins_record(self):
        if not any(
            item.source_id == self.source_id and item.sha256 == self.source_record_sha256
            for item in self.evidence
        ):
            raise ValueError("pressure-knot Evidence must pin its declared source record digest")
        return self


class TubePressureStressHistory(Contract):
    """One inspected tube's geometry and exact-knot pressure history."""

    tube_condition: TubeCondition
    asset_id: str = Field(min_length=1, max_length=200)
    location_id: str = Field(min_length=1, max_length=200)
    exchanger_id: str = Field(min_length=1, max_length=200)
    bundle_id: str = Field(min_length=1, max_length=200)
    material_condition_id: str = Field(min_length=1, max_length=200)
    closed_ends: bool
    geometry_source_id: str = Field(min_length=1, max_length=160)
    geometry_record_id: str = Field(min_length=1, max_length=200)
    geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    pressure_knots: tuple[TubePressureKnot, ...] = Field(min_length=1, max_length=100_000)
    plugged_tube_pressure_path_reviewed: bool = False

    @model_validator(mode="after")
    def tube_geometry_and_clock(self):
        if self.tube_condition.minimum_wall_m <= 0.0:
            raise ValueError("positive current minimum wall is required for Lamé stress evaluation")
        if not any(
            item.source_id == self.geometry_source_id and item.sha256 == self.geometry_record_sha256
            for item in self.geometry_evidence
        ):
            raise ValueError("geometry Evidence must pin its declared source record digest")
        knot_ids = [row.knot_id for row in self.pressure_knots]
        if len(knot_ids) != len(set(knot_ids)):
            raise ValueError("pressure knot identifiers must be unique within a tube history")
        times = [row.time_s for row in self.pressure_knots]
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("pressure knots must be in strictly increasing exact-time order")
        return self


class TubeBundleLameStressHistory(Contract):
    """Caller-reviewed scope and a set of tube-specific pressure-stress histories."""

    schema_version: Literal["matintegrity.tube_bundle_lame_stress_history.v1"] = (
        "matintegrity.tube_bundle_lame_stress_history.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    asset_id: str = Field(min_length=1, max_length=200)
    location_id: str = Field(min_length=1, max_length=200)
    exchanger_id: str = Field(min_length=1, max_length=200)
    bundle_id: str = Field(min_length=1, max_length=200)
    time_basis_id: str = Field(min_length=1, max_length=160)
    pressure_reference_basis_id: str = Field(min_length=1, max_length=200)
    tube_histories: tuple[TubePressureStressHistory, ...] = Field(min_length=1, max_length=100_000)
    tube_bundle_and_material_identity_reviewed: bool
    current_bore_and_minimum_wall_mapping_reviewed: bool
    wall_is_uniform_and_axisymmetric_reviewed: bool
    absolute_pressure_units_and_common_reference_reviewed: bool
    pressure_history_clock_and_record_lineage_reviewed: bool
    elastic_isotropic_axisymmetric_lame_applicability_reviewed: bool
    axial_end_condition_reviewed: bool
    no_acceptance_capacity_or_life_claim_reviewed: bool
    computational_use_authorized: bool
    maximum_work_units: int = Field(default=2_000_000, ge=1, le=20_000_000)

    @model_validator(mode="after")
    def unique_tube_histories(self):
        tube_ids = [row.tube_condition.tube_id for row in self.tube_histories]
        if len(tube_ids) != len(set(tube_ids)):
            raise ValueError("tube identifiers must be unique in one bundle assessment")
        for history in self.tube_histories:
            expected_scope = (self.asset_id, self.location_id, self.exchanger_id, self.bundle_id)
            actual_scope = (history.asset_id, history.location_id, history.exchanger_id, history.bundle_id)
            if actual_scope != expected_scope:
                raise ValueError("tube geometry history scope must match the bundle request")
            for knot in history.pressure_knots:
                knot_scope = (knot.asset_id, knot.location_id, knot.exchanger_id, knot.bundle_id)
                if knot_scope != expected_scope or knot.tube_id != history.tube_condition.tube_id:
                    raise ValueError("pressure-knot asset/bundle/tube identity must match its tube history")
                if knot.time_basis_id != self.time_basis_id:
                    raise ValueError("pressure-knot time basis must match the request")
                if knot.pressure_reference_basis_id != self.pressure_reference_basis_id:
                    raise ValueError("pressure-knot pressure reference must match the request")
        return self


def evaluate_tube_bundle_lame_stress_history(request: TubeBundleLameStressHistory) -> Calculation:
    """Evaluate inner- and outer-wall Lamé stresses at supplied knots, without interpolation."""
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": input_sha256,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "exchanger_id": request.exchanger_id,
        "bundle_id": request.bundle_id,
        "time_basis_id": request.time_basis_id,
        "pressure_reference_basis_id": request.pressure_reference_basis_id,
        "source_id": SOURCE_ID,
        "qualification_claimed": False,
        "acceptance_claimed": False,
    }
    required_reviews = (
        "tube_bundle_and_material_identity_reviewed",
        "current_bore_and_minimum_wall_mapping_reviewed",
        "wall_is_uniform_and_axisymmetric_reviewed",
        "absolute_pressure_units_and_common_reference_reviewed",
        "pressure_history_clock_and_record_lineage_reviewed",
        "elastic_isotropic_axisymmetric_lame_applicability_reviewed",
        "axial_end_condition_reviewed",
        "no_acceptance_capacity_or_life_claim_reviewed",
        "computational_use_authorized",
    )
    missing_reviews = [name for name in required_reviews if not getattr(request, name)]
    plugged_reviews = [
        history.tube_condition.tube_id
        for history in request.tube_histories
        if history.tube_condition.plugged and not history.plugged_tube_pressure_path_reviewed
    ]
    if missing_reviews or plugged_reviews:
        return Calculation(
            status="needs_data",
            values=base
            | {
                "missing_review_gates": missing_reviews,
                "plugged_tubes_without_pressure_path_review": plugged_reviews,
                "evaluated_tube_count": 0,
                "histories": [],
            },
            notes=("No stress calculation is committed until all scope and load-path reviews are declared.",),
        )

    work_units = sum(2 * len(history.pressure_knots) for history in request.tube_histories)
    if work_units > request.maximum_work_units:
        return Calculation(
            status="out_of_scope",
            values=base
            | {
                "reason": "declared_work_budget_exceeded",
                "required_work_units": work_units,
                "maximum_work_units": request.maximum_work_units,
                "evaluated_tube_count": 0,
                "histories": [],
            },
        )

    histories = []
    for history in request.tube_histories:
        condition = history.tube_condition
        inner_radius = condition.inner_diameter_m / 2.0
        outer_radius = inner_radius + condition.minimum_wall_m
        if not math.isfinite(outer_radius) or outer_radius <= inner_radius:
            return Calculation(
                status="out_of_scope",
                values=base
                | {
                    "reason": "tube_radii_outside_finite_numeric_support",
                    "failed_tube_id": condition.tube_id,
                    "evaluated_tube_count": len(histories),
                    "histories": histories,
                },
            )
        knot_results = []
        for knot in history.pressure_knots:
            surface_results = {}
            for surface, radius in (("inner_wall", inner_radius), ("outer_wall", outer_radius)):
                try:
                    cylinder = Cylinder(
                        inner_radius_m=inner_radius,
                        outer_radius_m=outer_radius,
                        internal_pressure_Pa=knot.internal_pressure_Pa,
                        external_pressure_Pa=knot.external_pressure_Pa,
                        evaluation_radius_m=radius,
                        closed_ends=history.closed_ends,
                    )
                    calculation = lame_cylinder(cylinder)
                    stresses = calculation.values
                    if any(not math.isfinite(float(value)) for value in stresses.values()):
                        raise ArithmeticError("Lamé result contains a nonfinite stress")
                except (ArithmeticError, OverflowError, ValueError) as error:
                    return Calculation(
                        status="out_of_scope",
                        values=base
                        | {
                            "reason": "lame_stress_numeric_or_geometry_failure",
                            "failure_detail": str(error),
                            "failed_tube_id": condition.tube_id,
                            "failed_knot_id": knot.knot_id,
                            "evaluated_tube_count": len(histories),
                            "histories": histories,
                        },
                    )
                surface_results[surface] = {"evaluation_radius_m": radius, **stresses}
            knot_results.append(
                {
                    "knot_id": knot.knot_id,
                    "time_s": knot.time_s,
                    "internal_pressure_Pa": knot.internal_pressure_Pa,
                    "external_pressure_Pa": knot.external_pressure_Pa,
                    "pressure_source_id": knot.source_id,
                    "pressure_source_record_id": knot.source_record_id,
                    "pressure_source_record_sha256": knot.source_record_sha256,
                    "surface_stresses": surface_results,
                }
            )
        tube_result = {
            "tube_id": condition.tube_id,
            "plugged": condition.plugged,
            "material_condition_id": history.material_condition_id,
            "inner_diameter_m": condition.inner_diameter_m,
            "current_minimum_wall_m": condition.minimum_wall_m,
            "reference_wall_m": condition.reference_wall_m,
            "tube_condition_sha256": canonical_digest(condition.model_dump(mode="json")),
            "inner_radius_m": inner_radius,
            "outer_radius_m": outer_radius,
            "closed_ends": history.closed_ends,
            "geometry_source_id": history.geometry_source_id,
            "geometry_record_id": history.geometry_record_id,
            "geometry_record_sha256": history.geometry_record_sha256,
            "geometry_evidence_source_ids": [item.source_id for item in history.geometry_evidence],
            "pressure_history_sha256": canonical_digest(
                [row.model_dump(mode="json") for row in history.pressure_knots]
            ),
            "knot_results": knot_results,
        }
        tube_result["result_sha256"] = canonical_digest(tube_result)
        histories.append(tube_result)

    return Calculation(
        status="computed",
        values=base
        | {
            "method": "exact-knot inner/outer wall Lamé stress evaluation",
            "interpolation_between_knots": False,
            "stress_output_only": True,
            "evaluated_tube_count": len(histories),
            "work_units": work_units,
            "histories": histories,
            "result_sha256": canonical_digest(histories),
        },
        notes=(
            "Uniform axisymmetric Lamé elasticity only; tubesheet/baffle restraint, ovality, local defects, thermal/residual stress, vibration, acceptance, capacity and life are not evaluated.",
            "Pressure is evaluated only at caller-supplied exact knots; no interpolation, extrapolation or missing-knot repair is performed.",
        ),
    )


def specifications() -> tuple[ModelSpec, ...]:
    return (
        ModelSpec(
            model_id=MODEL_ID,
            input_type=TubeBundleLameStressHistory,
            evaluator=evaluate_tube_bundle_lame_stress_history,
            units={
                "histories[].inner_radius_m": "m",
                "histories[].outer_radius_m": "m",
                "histories[].knot_results[].time_s": "s",
                "histories[].knot_results[].internal_pressure_Pa": "Pa",
                "histories[].knot_results[].external_pressure_Pa": "Pa",
                "histories[].knot_results[].surface_stresses.*.evaluation_radius_m": "m",
                "histories[].knot_results[].surface_stresses.*.hoop_stress_Pa": "Pa",
                "histories[].knot_results[].surface_stresses.*.radial_stress_Pa": "Pa",
                "histories[].knot_results[].surface_stresses.*.axial_stress_Pa": "Pa",
                "histories[].knot_results[].surface_stresses.*.von_mises_Pa": "Pa",
            },
            assumptions=(
                "Each tube is modeled as a homogeneous isotropic linear-elastic annular cylinder using the caller's current inner diameter and minimum wall.",
                "Internal and external absolute pressures are nonnegative, share one caller-reviewed Pa reference, and are evaluated only at exact supplied knots.",
                "The caller declares the axial end condition; plugged-tube pressure paths require a separate explicit review.",
                "Stress descriptors are not code acceptance, pressure capacity, remaining life, or qualification results.",
            ),
            source_ids=(SOURCE_ID, "cambridge_lame"),
            qualification="engineering_screening",
        ),
    )
