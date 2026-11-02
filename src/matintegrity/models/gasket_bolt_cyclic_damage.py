"""Caller-calibrated fatigue screening for bolt stress histories in gasket joints."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec


MODEL_ID = "fabrication.gasket_bolt_cyclic_damage"
SOURCE_ID = "caller_gasket_bolt_sn_calibration"
UPSTREAM_MODEL_ID = "fabrication.gasket_multi_bolt_sector_equilibrium"


class BoltFatigueCurve(Contract):
    bolt_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    reference_stress_range_Pa: Positive
    reference_cycles: Positive
    basquin_exponent: Positive
    ultimate_tensile_strength_Pa: Positive
    calibration_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class GasketBoltCyclicDamage(Contract):
    """Rainflow plus caller-supplied Basquin/Goodman screening for one bolt-joint history."""

    schema_version: Literal["matintegrity.gasket_bolt_cyclic_damage.v1"] = "matintegrity.gasket_bolt_cyclic_damage.v1"
    assessment_id: str = Field(min_length=1)
    bolt_history_result: AssessmentResult
    bolt_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curves: tuple[BoltFatigueCurve, ...] = Field(min_length=1, max_length=256)
    declared_damage_limit: Positive
    time_history_interpretation: Literal["ordered_repeated_service_record"]
    load_history_scope_reviewed: bool
    bolt_identity_and_stress_area_reviewed: bool
    material_condition_and_temperature_applicability_reviewed: bool
    calibration_lineage_license_and_computational_use_reviewed: bool
    cycle_counting_and_record_boundary_reviewed: bool

    @model_validator(mode="after")
    def verify_history_and_curves(self):
        result = self.bolt_history_result
        if result.model_id != UPSTREAM_MODEL_ID or result.status != "computed":
            raise ValueError("a computed multi-bolt gasket-joint history is required")
        if canonical_digest(result.model_dump(mode="json")) != self.bolt_history_result_sha256:
            raise ValueError("bolt history result digest does not match")
        steps = result.values.get("steps")
        if not isinstance(steps, list) or len(steps) < 3:
            raise ValueError("at least three ordered load steps are required for cycle counting")
        times = [row.get("time_s") for row in steps if isinstance(row, dict)]
        if len(times) != len(steps) or any(not isinstance(t, (int, float)) or isinstance(t, bool) or not math.isfinite(t) for t in times):
            raise ValueError("history knots must have finite numeric times")
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("history time knots must be strictly increasing")
        bolt_ids: set[str] | None = None
        for step in steps:
            rows = step.get("bolts")
            if not isinstance(rows, list):
                raise ValueError("each load step must contain per-bolt rows")
            ids = {row.get("bolt_id") for row in rows if isinstance(row, dict)}
            if len(ids) != len(rows) or bolt_ids is not None and ids != bolt_ids:
                raise ValueError("each step must contain the same unique bolt IDs")
            bolt_ids = ids
            if any(
                not isinstance(row.get("nominal_tensile_stress_Pa"), (int, float))
                or isinstance(row.get("nominal_tensile_stress_Pa"), bool)
                or not math.isfinite(row["nominal_tensile_stress_Pa"])
                or row["nominal_tensile_stress_Pa"] < 0
                for row in rows
            ):
                raise ValueError("upstream nominal bolt stresses must be finite and nonnegative")
        curves_by_id = {curve.bolt_id: curve for curve in self.curves}
        if len(curves_by_id) != len(self.curves) or set(curves_by_id) != (bolt_ids or set()):
            raise ValueError("provide exactly one fatigue calibration per history bolt")
        for curve in self.curves:
            record = {
                "bolt_id": curve.bolt_id,
                "material_condition_id": curve.material_condition_id,
                "provider_id": curve.provider_id,
                "provider_revision": curve.provider_revision,
                "reference_stress_range_Pa": curve.reference_stress_range_Pa,
                "reference_cycles": curve.reference_cycles,
                "basquin_exponent": curve.basquin_exponent,
                "ultimate_tensile_strength_Pa": curve.ultimate_tensile_strength_Pa,
                "history_result_sha256": self.bolt_history_result_sha256,
            }
            if canonical_digest(record) != curve.calibration_record_sha256:
                raise ValueError("fatigue calibration digest does not match its parameters and history")
            if not any(
                item.source_id == curve.provider_id
                and item.sha256 == curve.calibration_record_sha256
                and item.license_id == curve.usage_license_id
                for item in curve.evidence
            ):
                raise ValueError("curve Evidence must pin calibration data and declared license")
        return self


def evaluate_gasket_bolt_cyclic_damage(request: GasketBoltCyclicDamage) -> Calculation:
    """Count stress cycles and calculate caller-calibrated linear cumulative damage."""
    try:
        import rainflow
    except ImportError:
        return Calculation(
            status="needs_data",
            values={"model_id": MODEL_ID, "reason": "optional_rainflow_runtime_unavailable"},
            notes=("Install the optional science dependency group to enable rainflow cycle extraction.",),
        )

    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "joint_id": request.bolt_history_result.values.get("joint_id"),
        "physical_scope_id": request.bolt_history_result.values.get("physical_scope_id"),
        "bolt_history_result_sha256": request.bolt_history_result_sha256,
        "input_sha256": digest,
    }
    reviews = (
        request.load_history_scope_reviewed,
        request.bolt_identity_and_stress_area_reviewed,
        request.material_condition_and_temperature_applicability_reviewed,
        request.calibration_lineage_license_and_computational_use_reviewed,
        request.cycle_counting_and_record_boundary_reviewed,
    )
    if not all(reviews):
        return Calculation(status="needs_data", values=base | {"missing_review_count": sum(not item for item in reviews)})

    steps = request.bolt_history_result.values["steps"]
    bolt_rows = [step["bolts"] for step in steps]
    results = []
    for curve in request.curves:
        signal = [next(row["nominal_tensile_stress_Pa"] for row in rows if row["bolt_id"] == curve.bolt_id) for rows in bolt_rows]
        cycles = []
        damage = 0.0
        for stress_range, mean_stress, count, start, end in rainflow.extract_cycles(signal):
            alternating = float(stress_range) / 2.0
            tensile_mean = max(float(mean_stress), 0.0)
            if tensile_mean >= curve.ultimate_tensile_strength_Pa:
                return Calculation(
                    status="out_of_scope",
                    values=base | {"bolt_id": curve.bolt_id},
                    notes=("Rainflow cycle mean reaches the caller-supplied ultimate strength; Goodman correction is undefined.",),
                )
            denominator = 1.0 - tensile_mean / curve.ultimate_tensile_strength_Pa
            equivalent_amplitude = alternating / denominator
            equivalent_range = 2.0 * equivalent_amplitude
            if equivalent_range == 0.0:
                life = math.inf
                increment = 0.0
            else:
                try:
                    life = curve.reference_cycles * (
                        curve.reference_stress_range_Pa / equivalent_range
                    ) ** curve.basquin_exponent
                    increment = float(count) / life if life > 0.0 and math.isfinite(life) else 0.0
                except (OverflowError, ZeroDivisionError):
                    return Calculation(
                        status="out_of_scope",
                        values=base | {"bolt_id": curve.bolt_id},
                        notes=("Basquin life calculation exceeded finite numeric support.",),
                    )
                if life <= 0.0:
                    return Calculation(
                        status="out_of_scope",
                        values=base | {"bolt_id": curve.bolt_id},
                        notes=("Basquin life is not positive and finite.",),
                    )
            if not math.isfinite(increment) or increment < 0:
                return Calculation(status="out_of_scope", values=base | {"bolt_id": curve.bolt_id}, notes=("Damage increment is outside finite numeric support.",))
            damage += increment
            cycles.append({
                "stress_range_Pa": float(stress_range),
                "mean_stress_Pa": float(mean_stress),
                "goodman_equivalent_range_Pa": equivalent_range,
                "cycle_count": float(count),
                "start_index": int(start),
                "end_index": int(end),
                "cycles_to_failure": life if math.isfinite(life) else None,
                "miner_damage_increment": increment,
            })
        if not math.isfinite(damage):
            return Calculation(status="out_of_scope", values=base | {"bolt_id": curve.bolt_id}, notes=("Accumulated damage is not finite.",))
        results.append({
            "bolt_id": curve.bolt_id,
            "material_condition_id": curve.material_condition_id,
            "fatigue_calibration_sha256": curve.calibration_record_sha256,
            "cycles": cycles,
            "counted_cycles": math.fsum(row["cycle_count"] for row in cycles),
            "linear_miner_damage": damage,
            "declared_damage_limit": request.declared_damage_limit,
            "damage_margin": request.declared_damage_limit - damage,
            "fraction_of_declared_damage_limit": damage / request.declared_damage_limit,
        })
    return Calculation(
        values=base | {
            "bolt_results": results,
            "maximum_bolt_damage": max(row["linear_miner_damage"] for row in results),
            "governing_bolt_id": max(results, key=lambda row: row["linear_miner_damage"])["bolt_id"],
            "interpretation": "caller_calibrated_nominal_bolt_stress_cycle_screening",
        },
        notes=(
            "The ordered record is treated as the repeated service history exactly as supplied; boundary and repetition count are caller-defined.",
            "Rainflow ranges use linear Goodman correction for tensile cycle mean and caller-supplied Basquin calibration with linear Miner accumulation.",
            "No bolt notch/local stress, preload scatter, relaxation beyond upstream history, corrosion/fretting, interaction rule, service-life extrapolation, failure probability or code acceptance is inferred.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketBoltCyclicDamage,
        evaluate_gasket_bolt_cyclic_damage,
        {
            "bolt_results[].cycles[].stress_range_Pa": "Pa",
            "bolt_results[].cycles[].goodman_equivalent_range_Pa": "Pa",
            "bolt_results[].cycles[].cycles_to_failure": "cycle",
            "bolt_results[].cycles[].miner_damage_increment": "1",
            "bolt_results[].linear_miner_damage": "1",
            "bolt_results[].damage_margin": "1",
            "maximum_bolt_damage": "1",
        },
        (
            "Nominal tensile stress histories are read from one digest-pinned computed gasket multi-bolt equilibrium result.",
            "Cycle lives use caller-provided material-condition-specific Basquin parameters and tensile ultimate strength; all curve records require Evidence and an explicit usage license.",
            "Rainflow cycle counting, linear Goodman mean correction and Miner accumulation are screening assumptions; no universal fatigue acceptance is asserted.",
        ),
        (SOURCE_ID, "rainflow_library", "caller_basquin_goodman_miner"),
        qualification="engineering_screening",
        runtime_dependency_names=("rainflow",),
    )]
