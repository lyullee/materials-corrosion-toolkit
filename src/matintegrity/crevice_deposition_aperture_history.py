"""Map digest-bound solid-volume snapshots to a reviewed slit-gap history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_deposition_aperture_history"
SOURCE_ID = "caller_crevice_deposition_aperture_geometry_mapping"
MAX_CELLS = 2000
MAX_KNOTS = 5000


class CreviceDepositionVolumeKnot(Contract):
    elapsed_time_s: float = Field(ge=0)
    solid_volume_result: dict
    solid_volume_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_result_digest(self):
        if canonical_digest(self.solid_volume_result) != self.solid_volume_result_sha256:
            raise ValueError("solid-volume result digest mismatch")
        return self


class CreviceDepositionApertureHistoryRequest(Contract):
    """Convert exact solid-volume snapshots into explicit slit-gap measures."""

    schema_version: Literal["matintegrity.crevice_deposition_aperture_history.v1"] = (
        "matintegrity.crevice_deposition_aperture_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    initial_aperture_m: tuple[float, ...] = Field(min_length=1, max_length=MAX_CELLS)
    cell_length_m: tuple[float, ...] = Field(min_length=1, max_length=MAX_CELLS)
    transverse_width_m: float = Field(gt=0)
    reference_area_m2: float = Field(gt=0)
    deposition_side_count: Literal[1, 2]
    coverage_fraction_by_cell: tuple[float, ...] = Field(min_length=1, max_length=MAX_CELLS)
    knots: tuple[CreviceDepositionVolumeKnot, ...] = Field(min_length=1, max_length=MAX_KNOTS)
    initial_geometry_and_cell_mapping_reviewed: bool
    reference_area_conversion_reviewed: bool
    side_count_and_equal_side_partition_reviewed: bool
    uniform_coverage_within_each_cell_reviewed: bool
    solid_volume_result_lineage_reviewed: bool
    nonnegative_remaining_gap_as_scope_limit_reviewed: bool

    @model_validator(mode="after")
    def validate_geometry_clock(self):
        count = len(self.initial_aperture_m)
        if count != len(self.cell_length_m) or count != len(self.coverage_fraction_by_cell):
            raise ValueError("aperture, cell-length and coverage arrays must have the same cell count")
        if any(not math.isfinite(value) or value <= 0 for value in self.initial_aperture_m):
            raise ValueError("initial apertures must be finite and positive")
        if any(not math.isfinite(value) or value <= 0 for value in self.cell_length_m):
            raise ValueError("cell lengths must be finite and positive")
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in self.coverage_fraction_by_cell):
            raise ValueError("coverage fractions must lie in [0, 1]")
        if self.knots[0].elapsed_time_s != 0.0:
            raise ValueError("history must start at time zero")
        if any(right.elapsed_time_s <= left.elapsed_time_s for left, right in zip(self.knots[:-1], self.knots[1:])):
            raise ValueError("history times must be strictly increasing")
        return self


def _result_values(result: dict) -> dict | None:
    if result.get("status") != "computed":
        return None
    values = result.get("values")
    return values if isinstance(values, dict) else result


def evaluate_crevice_deposition_aperture_history(
    request: CreviceDepositionApertureHistoryRequest,
) -> Calculation:
    """Calculate coverage-weighted equivalent and covered-patch remaining gaps."""
    request_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "input_sha256": request_digest,
        "deposition_side_count": request.deposition_side_count,
        "reference_area_m2": request.reference_area_m2,
        "mapping": "equal solid-volume partition across the declared deposition sides and uniform over each covered cell fraction",
    }
    review_names = (
        "initial_geometry_and_cell_mapping_reviewed",
        "reference_area_conversion_reviewed",
        "side_count_and_equal_side_partition_reviewed",
        "uniform_coverage_within_each_cell_reviewed",
        "solid_volume_result_lineage_reviewed",
        "nonnegative_remaining_gap_as_scope_limit_reviewed",
    )
    missing = [name for name in review_names if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "committed_knot_count": 0, "knots": []})

    committed: list[dict] = []
    cell_count = len(request.initial_aperture_m)
    for knot_index, knot in enumerate(request.knots):
        values = _result_values(knot.solid_volume_result)
        if values is None:
            return Calculation(status="needs_data", values=base | {
                "committed_knot_count": len(committed), "knots": committed,
                "failed_knot_index": knot_index, "failure_reason": "upstream solid-volume result is not computed",
            })
        volumes = values.get("cell_solid_volume_per_reference_area_m")
        if (
            values.get("physical_scope_id") != request.physical_scope_id
            or values.get("elapsed_time_s") != knot.elapsed_time_s
            or not isinstance(volumes, list) or len(volumes) != cell_count
        ):
            return Calculation(status="out_of_scope", values=base | {
                "committed_knot_count": len(committed), "knots": committed,
                "failed_knot_index": knot_index,
                "failure_reason": "upstream result scope, exact time or cell count does not match the reviewed geometry",
            })

        mean_loss: list[float] = []
        covered_patch_loss: list[float | None] = []
        mean_gap: list[float] = []
        covered_gap: list[float | None] = []
        failed_cell: int | None = None
        for cell, solid_volume_per_reference_area in enumerate(volumes):
            if (
                isinstance(solid_volume_per_reference_area, bool)
                or not isinstance(solid_volume_per_reference_area, (int, float))
                or not math.isfinite(solid_volume_per_reference_area)
                or solid_volume_per_reference_area < 0
            ):
                failed_cell = cell
                break
            plan_area = request.transverse_width_m * request.cell_length_m[cell]
            solid_volume = float(solid_volume_per_reference_area) * request.reference_area_m2
            average_gap_loss = solid_volume / plan_area
            coverage = request.coverage_fraction_by_cell[cell]
            if coverage == 0.0:
                if solid_volume > 0.0:
                    failed_cell = cell
                    break
                local_gap_loss = None
                local_remaining_gap = None
            else:
                deposited_area = request.deposition_side_count * coverage * plan_area
                local_layer = solid_volume / deposited_area
                local_gap_loss = request.deposition_side_count * local_layer
                local_remaining_gap = request.initial_aperture_m[cell] - local_gap_loss
                if not math.isfinite(local_layer) or local_remaining_gap < 0.0:
                    failed_cell = cell
                    break
            average_remaining_gap = request.initial_aperture_m[cell] - average_gap_loss
            if not math.isfinite(average_gap_loss) or average_remaining_gap < 0.0:
                failed_cell = cell
                break
            mean_loss.append(average_gap_loss)
            covered_patch_loss.append(local_gap_loss)
            mean_gap.append(average_remaining_gap)
            covered_gap.append(local_remaining_gap)
        if failed_cell is not None:
            return Calculation(status="out_of_scope", values=base | {
                "committed_knot_count": len(committed), "knots": committed,
                "failed_knot_index": knot_index, "failed_cell_index": failed_cell,
                "failure_reason": "coverage/volume is incompatible or the implied remaining aperture is negative",
            })
        committed.append({
            "knot_index": knot_index,
            "elapsed_time_s": knot.elapsed_time_s,
            "solid_volume_result_sha256": knot.solid_volume_result_sha256,
            "equivalent_mean_aperture_loss_m_by_cell": mean_loss,
            "equivalent_mean_remaining_aperture_m_by_cell": mean_gap,
            "covered_patch_aperture_loss_m_by_cell": covered_patch_loss,
            "covered_patch_remaining_aperture_m_by_cell": covered_gap,
            "spatial_uniformity_inferred": False,
        })
    return Calculation(values=base | {
        "status": "computed",
        "committed_knot_count": len(committed),
        "knots": committed,
        "prefix_policy": "only complete exact knots are committed",
        "interpretation_boundary": "Mean gap is a volume-conserving cell average; covered-patch gap assumes the reviewed uniform coverage and equal partition over the declared faces. Neither is a resolved deposit morphology or a substitute for a moving-boundary transport solve.",
        "not_inferred": ["deposit morphology", "partial-cell spatial pattern", "porosity", "adhesion", "solid redistribution", "precipitation kinetics", "flow feedback", "corrosion rate", "acceptance", "risk probability"],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceDepositionApertureHistoryRequest,
        evaluator=evaluate_crevice_deposition_aperture_history,
        units={
            "knots[].elapsed_time_s": "s",
            "initial_aperture_m": "m",
            "cell_length_m": "m",
            "transverse_width_m": "m",
            "reference_area_m2": "m2",
            "coverage_fraction_by_cell": "1",
            "knots[].equivalent_mean_aperture_loss_m_by_cell": "m",
            "knots[].equivalent_mean_remaining_aperture_m_by_cell": "m",
            "knots[].covered_patch_aperture_loss_m_by_cell": "m",
            "knots[].covered_patch_remaining_aperture_m_by_cell": "m",
        },
        assumptions=(
            "Each exact-knot solid-volume result is per the declared reference area and matches the physical scope, time and cell ordering.",
            "Solid volume is distributed equally across the declared one or two deposition faces and uniformly over the caller-declared coverage within each cell.",
            "Equivalent mean gap loss is solid volume divided by the cell planform area; covered-patch local closure additionally depends on the reviewed coverage fraction and face count.",
            "Negative remaining aperture and positive deposition volume with zero coverage fail closed; no clipping or extrapolation occurs.",
            "The mapping is a geometric adapter only and does not resolve morphology, porosity, adhesion, kinetics or transport feedback.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
