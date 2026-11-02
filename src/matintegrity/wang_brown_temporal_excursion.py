"""Finite-sample temporal association of shear cycles and normal strain excursion."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec


class WangBrownTemporalExcursion(Contract):
    """Attach normal strain excursion on each caller-counted shear-cycle interval."""

    analysis_id: str = Field(min_length=1)
    projected_rainflow_result: dict
    projected_rainflow_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    plane_id: str = Field(min_length=1)
    shear_projection: str = Field(
        pattern=r"^(engineering_shear_strain_directional_component|engineering_shear_strain_vector_magnitude)$"
    )
    normal_strain_sample_ids: list[str] = Field(min_length=3, max_length=100000)
    normal_strain_values: list[float] = Field(min_length=3, max_length=100000)
    normal_strain_source_id: str = Field(min_length=1)
    normal_strain_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    normal_strain_evidence: Evidence
    same_ordered_sample_clock_reviewed: bool

    @model_validator(mode="after")
    def source_and_alignment(self):
        if len(self.normal_strain_sample_ids) != len(self.normal_strain_values):
            raise ValueError("normal-strain sample IDs and values must have equal length")
        if len(set(self.normal_strain_sample_ids)) != len(self.normal_strain_sample_ids):
            raise ValueError("normal-strain sample IDs must be unique")
        if any(not math.isfinite(value) for value in self.normal_strain_values):
            raise ValueError("normal-strain samples must be finite")
        if (
            self.normal_strain_evidence.source_id != self.normal_strain_source_id
            or self.normal_strain_evidence.sha256 != self.normal_strain_source_sha256
        ):
            raise ValueError("normal-strain Evidence must match its declared source and digest")
        if canonical_digest(self.projected_rainflow_result) != self.projected_rainflow_result_sha256:
            raise ValueError("projected rainflow result digest differs from the pinned digest")
        return self


def evaluate_wang_brown_temporal_excursion(request: WangBrownTemporalExcursion) -> Calculation:
    """Return sampled normal-strain excursion per already-counted shear cycle.

    This is a bounded temporal association adapter. It does not perform rainflow
    counting, reconstruct a continuous path, or calculate fatigue damage/life.
    """
    result = request.projected_rainflow_result
    base = {
        "analysis_id": request.analysis_id,
        "projected_rainflow_result_sha256": request.projected_rainflow_result_sha256,
        "normal_strain_source_id": request.normal_strain_source_id,
        "normal_strain_source_sha256": request.normal_strain_source_sha256,
        "plane_id": request.plane_id,
        "shear_projection": request.shear_projection,
        "normal_strain_unit": "1",
        "association_method": "normal-strain sampled range over inclusive shear-cycle start/end index interval",
        "fatigue_damage_or_life": None,
    }
    if not request.same_ordered_sample_clock_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "same_ordered_sample_clock_review_required", "cycles": None,
        })
    if result.get("status") != "computed" or not isinstance(result.get("values"), dict):
        return Calculation(status="needs_data", values=base | {
            "reason": "computed_projected_rainflow_result_required", "cycles": None,
        })
    values = result["values"]
    if values.get("sample_count") != len(request.normal_strain_values):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "sample_count_mismatch", "cycles": None,
        })
    planes = values.get("projection_cycle_results")
    plane = next((row for row in planes or () if isinstance(row, dict) and row.get("plane_id") == request.plane_id), None)
    if plane is None or not isinstance(plane.get("projections"), dict):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "requested_plane_missing", "cycles": None,
        })
    projection = plane["projections"].get(request.shear_projection)
    if not isinstance(projection, dict) or not isinstance(projection.get("cycles"), list):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "requested_shear_cycle_list_missing", "cycles": None,
        })
    expected_interpretation = (
        "signed_engineering_shear_component_along_supplied_in_plane_direction"
        if request.shear_projection == "engineering_shear_strain_directional_component"
        else "nonnegative_engineering_shear_vector_magnitude_direction_lost"
    )
    if projection.get("projection_interpretation") != expected_interpretation:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "shear_projection_interpretation_mismatch", "cycles": None,
        })
    output = []
    for index, cycle in enumerate(projection["cycles"]):
        if not isinstance(cycle, dict):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "malformed_shear_cycle", "cycle_index": index, "cycles": None,
            })
        start, end, count = cycle.get("start_index"), cycle.get("end_index"), cycle.get("count")
        if (
            isinstance(start, bool) or not isinstance(start, int)
            or isinstance(end, bool) or not isinstance(end, int)
            or start < 0 or end < start or end >= len(request.normal_strain_values)
            or isinstance(count, bool) or not isinstance(count, (int, float))
            or not math.isfinite(float(count)) or count <= 0
        ):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "invalid_cycle_bounds_or_count", "cycle_index": index, "cycles": None,
            })
        segment = request.normal_strain_values[start:end + 1]
        minimum, maximum = min(segment), max(segment)
        excursion = maximum - minimum
        if not math.isfinite(excursion):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "nonfinite_excursion", "cycle_index": index, "cycles": None,
            })
        output.append({
            "cycle_index": index,
            "start_index": start,
            "end_index": end,
            "start_sample_id": request.normal_strain_sample_ids[start],
            "end_sample_id": request.normal_strain_sample_ids[end],
            "cycle_count": float(count),
            "normal_strain_minimum": minimum,
            "normal_strain_maximum": maximum,
            "normal_strain_excursion": excursion,
            "normal_strain_minimum_sample_id": request.normal_strain_sample_ids[start + segment.index(minimum)],
            "normal_strain_maximum_sample_id": request.normal_strain_sample_ids[start + segment.index(maximum)],
        })
    return Calculation(values=base | {
        "status": "computed",
        "sample_count": len(request.normal_strain_values),
        "paired_cycle_count": len(output),
        "cycle_count_equivalents": math.fsum(row["cycle_count"] for row in output),
        "cycles": output,
        "limitations": [
            "The caller supplies the counted shear cycles and attests that both channels share the same ordered clock.",
            "Excursions use only the finite samples inside each inclusive cycle-index interval; no between-sample extrema are inferred.",
            "This returns a kinematic descriptor only; it is not a damage parameter, life estimate, acceptance decision or qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.wang_brown_temporal_normal_excursion",
        WangBrownTemporalExcursion,
        evaluate_wang_brown_temporal_excursion,
        {
            "cycles.normal_strain_minimum": "1",
            "cycles.normal_strain_maximum": "1",
            "cycles.normal_strain_excursion": "1",
            "cycle_count_equivalents": "cycle",
        },
        (
            "The shear cycle sequence is caller-counted; normal-strain samples are associated by the cycle's inclusive sample-index interval.",
            "Caller review must establish identical sample order and clock across source channels.",
            "Finite sampled ranges do not reconstruct continuous extrema or imply fatigue damage, life or qualification.",
        ),
        ("wang_brown_1993_normal_strain_excursion_on_maximum_shear_reversal",),
        qualification="user_model",
    )]
