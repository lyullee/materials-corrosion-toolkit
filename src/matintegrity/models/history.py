"""Process-pressure history to fatigue screening through a declared structural model."""

from __future__ import annotations

from pydantic import model_validator

from ..adapters import OperatingHistory
from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec


class PressureFatigue(Contract):
    history: OperatingHistory
    external_absolute_pressure_Pa: Positive
    mean_radius_m: Positive
    wall_thickness_m: Positive
    maximum_thickness_to_radius_ratio: Positive
    reference_stress_range_Pa: Positive
    reference_cycles: Positive
    basquin_exponent: Positive
    minimum_calibrated_stress_range_Pa: Positive
    maximum_calibrated_stress_range_Pa: Positive
    minimum_calibrated_temperature_K: Positive
    maximum_calibrated_temperature_K: Positive
    minimum_calibrated_stress_ratio: float
    maximum_calibrated_stress_ratio: float
    initial_damage: Nonnegative
    declared_damage_limit: Positive

    @model_validator(mode="after")
    def domain(self):
        for low, high in (
            (self.minimum_calibrated_stress_range_Pa, self.maximum_calibrated_stress_range_Pa),
            (self.minimum_calibrated_temperature_K, self.maximum_calibrated_temperature_K),
            (self.minimum_calibrated_stress_ratio, self.maximum_calibrated_stress_ratio),
        ):
            if high < low:
                raise ValueError("calibrated domains must be ordered")
        if self.maximum_calibrated_stress_ratio >= 1:
            raise ValueError("a nonzero tensile stress cycle requires stress ratio below one")
        return self


def pressure_fatigue(x: PressureFatigue) -> Calculation:
    import rainflow

    history = x.history
    reasons = []
    if not all(history.valid):
        reasons.append("Invalid history samples require segmentation; counting across gaps is disabled.")
    if x.wall_thickness_m / x.mean_radius_m > x.maximum_thickness_to_radius_ratio:
        reasons.append("The geometry exceeds the caller-declared membrane domain.")
    if min(history.pressure_absolute_Pa) < x.external_absolute_pressure_Pa:
        reasons.append("External-pressure loading needs a separate buckling and stress model.")
    if (
        min(history.temperature_K) < x.minimum_calibrated_temperature_K
        or max(history.temperature_K) > x.maximum_calibrated_temperature_K
    ):
        reasons.append("History temperature exceeds the supplied fatigue calibration domain.")
    if reasons:
        return Calculation(status="out_of_scope", values={}, notes=tuple(reasons))
    stress = [
        (p - x.external_absolute_pressure_Pa) * x.mean_radius_m / x.wall_thickness_m
        for p in history.pressure_absolute_Pa
    ]
    rows = []
    damage = x.initial_damage
    for value, mean, count, start, end in rainflow.extract_cycles(stress):
        if value <= 0:
            continue
        maximum = mean + value / 2
        ratio = (mean - value / 2) / maximum
        if (
            not x.minimum_calibrated_stress_range_Pa <= value <= x.maximum_calibrated_stress_range_Pa
            or not x.minimum_calibrated_stress_ratio <= ratio <= x.maximum_calibrated_stress_ratio
        ):
            return Calculation(
                status="out_of_scope",
                values={"rejected_stress_range_Pa": float(value), "rejected_stress_ratio": float(ratio)},
                notes=(
                    "A counted cycle exceeds the supplied stress-range or stress-ratio calibration domain; no endurance limit or mean-stress correction is invented.",
                ),
            )
        life = x.reference_cycles * (x.reference_stress_range_Pa / value) ** x.basquin_exponent
        damage += count / life
        rows.append(
            dict(
                stress_range_Pa=float(value),
                mean_stress_Pa=float(mean),
                stress_ratio=float(ratio),
                count=float(count),
                cycles_to_failure=life,
                start_time_s=history.time_s[start],
                end_time_s=history.time_s[end],
            )
        )
    return Calculation(
        values=dict(
            cycles=rows,
            counted_cycles=sum(row["count"] for row in rows),
            initial_damage=x.initial_damage,
            total_damage=damage,
            damage_increment=damage - x.initial_damage,
            damage_margin=x.declared_damage_limit - damage,
            history_source_digest=history.source_digest,
        ),
        notes=(
            "Closed thin-cylinder hoop stress, rainflow ranges and calibrated Basquin/Miner screening. Residual half cycles are retained. Axial, nozzle, residual, thermal and hydrogen effects require separate qualified models. Damage is not a failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.history.asset_id, x.history.location_id) != (context.asset_id, context.location_id):
            raise ValueError("operating-history asset and location must match the assessment context")

    return [
        ModelSpec(
            "workflow.pressure_fatigue",
            PressureFatigue,
            pressure_fatigue,
            {
                "counted_cycles": "cycle",
                "initial_damage": "1",
                "total_damage": "1",
                "damage_increment": "1",
                "damage_margin": "1",
            },
            (
                "Neutral operating history mapped through explicitly bounded membrane stress and user-calibrated fatigue parameters.",
            ),
            ("membrane_equilibrium", "rainflow_library", "basquin_relation", "miner_accumulation"),
            context_validator=same_identity,
        )
    ]
