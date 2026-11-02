"""Area-exact summaries for rectilinear thickness maps with missing cells."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec


class RectilinearThicknessMap(Contract):
    """Cell-centred thickness values on explicit rectilinear cell edges.

    Matrix rows follow successive ``y_cell_edges_m`` intervals and columns follow
    successive ``x_cell_edges_m`` intervals. ``None`` is an unobserved cell.
    """

    x_cell_edges_m: list[float] = Field(min_length=2)
    y_cell_edges_m: list[float] = Field(min_length=2)
    cell_thickness_m: list[list[Nonnegative | None]] = Field(min_length=1)
    reference_thickness_m: Positive
    reporting_threshold_m: Nonnegative
    threshold_comparison: Literal["less_than", "less_than_or_equal"]
    connectivity: Literal["four_neighbour", "eight_neighbour"] = "four_neighbour"

    @model_validator(mode="after")
    def aligned_rectilinear_cells(self):
        if any(
            right <= left for left, right in zip(self.x_cell_edges_m, self.x_cell_edges_m[1:], strict=False)
        ):
            raise ValueError("x cell edges must be strictly increasing")
        if any(
            upper <= lower for lower, upper in zip(self.y_cell_edges_m, self.y_cell_edges_m[1:], strict=False)
        ):
            raise ValueError("y cell edges must be strictly increasing")
        expected_rows = len(self.y_cell_edges_m) - 1
        expected_columns = len(self.x_cell_edges_m) - 1
        if len(self.cell_thickness_m) != expected_rows or any(
            len(row) != expected_columns for row in self.cell_thickness_m
        ):
            raise ValueError(
                "thickness matrix must have one row per y interval and one column per x interval"
            )
        if not any(value is not None for row in self.cell_thickness_m for value in row):
            raise ValueError("at least one observed thickness cell is required")
        return self


def rectilinear_thickness_map(x: RectilinearThicknessMap) -> Calculation:
    """Summarize observed cells without interpolation or equal-area assumptions."""

    widths = [right - left for left, right in zip(x.x_cell_edges_m, x.x_cell_edges_m[1:], strict=False)]
    heights = [upper - lower for lower, upper in zip(x.y_cell_edges_m, x.y_cell_edges_m[1:], strict=False)]
    cell_areas = [[height * width for width in widths] for height in heights]

    observed_area = 0.0
    missing_area = 0.0
    thickness_area_sum = 0.0
    net_loss_volume = 0.0
    observed_thicknesses: list[float] = []
    threshold_cells: set[tuple[int, int]] = set()

    for row_index, row in enumerate(x.cell_thickness_m):
        for column_index, thickness in enumerate(row):
            area = cell_areas[row_index][column_index]
            if thickness is None:
                missing_area += area
                continue
            observed_area += area
            observed_thicknesses.append(thickness)
            thickness_area_sum += thickness * area
            net_loss_volume += (x.reference_thickness_m - thickness) * area
            is_below = (
                thickness < x.reporting_threshold_m
                if x.threshold_comparison == "less_than"
                else thickness <= x.reporting_threshold_m
            )
            if is_below:
                threshold_cells.add((row_index, column_index))

    component_areas: list[float] = []
    remaining = set(threshold_cells)
    while remaining:
        start = remaining.pop()
        stack = [start]
        component_area = 0.0
        while stack:
            row_index, column_index = stack.pop()
            component_area += cell_areas[row_index][column_index]
            neighbours = [
                (row_index - 1, column_index),
                (row_index + 1, column_index),
                (row_index, column_index - 1),
                (row_index, column_index + 1),
            ]
            if x.connectivity == "eight_neighbour":
                neighbours.extend(
                    (
                        (row_index - 1, column_index - 1),
                        (row_index - 1, column_index + 1),
                        (row_index + 1, column_index - 1),
                        (row_index + 1, column_index + 1),
                    )
                )
            for neighbour in neighbours:
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    stack.append(neighbour)
        component_areas.append(component_area)

    total_area = observed_area + missing_area
    return Calculation(
        values={
            "minimum_observed_thickness_m": min(observed_thicknesses),
            "maximum_observed_thickness_m": max(observed_thicknesses),
            "area_weighted_mean_observed_thickness_m": thickness_area_sum / observed_area,
            "total_map_area_m2": total_area,
            "observed_area_m2": observed_area,
            "missing_area_m2": missing_area,
            "observed_area_fraction": observed_area / total_area,
            "net_observed_loss_volume_m3": net_loss_volume,
            "threshold_cell_area_m2": sum(
                cell_areas[row_index][column_index] for row_index, column_index in threshold_cells
            ),
            "connected_threshold_component_areas_m2": sorted(component_areas, reverse=True),
            "connected_threshold_component_count": len(component_areas),
            "connectivity": (
                "four_neighbour_shared_edge"
                if x.connectivity == "four_neighbour"
                else "eight_neighbour_shared_edge_or_corner"
            ),
            "threshold_comparison": x.threshold_comparison,
            "interpolation_performed": False,
        },
        notes=(
            "Rows map to y intervals and columns map to x intervals; every statistic uses the corresponding edge-derived cell area.",
            "Missing cells are excluded from thickness and loss summaries, counted as missing area, and never interpolated or treated as sound.",
            "Net observed loss is signed reference-minus-observed thickness integrated only over observed cells; thickness above the reference contributes negative volume.",
            "Threshold components use the caller-selected four-neighbour shared-edge or eight-neighbour shared-edge-or-corner convention and are geometry summaries, not FFS acceptance or qualification results.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "geometry.rectilinear_thickness_map",
            RectilinearThicknessMap,
            rectilinear_thickness_map,
            {
                "minimum_observed_thickness_m": "m",
                "maximum_observed_thickness_m": "m",
                "area_weighted_mean_observed_thickness_m": "m",
                "total_map_area_m2": "m^2",
                "observed_area_m2": "m^2",
                "missing_area_m2": "m^2",
                "observed_area_fraction": "1",
                "net_observed_loss_volume_m3": "m^3",
                "threshold_cell_area_m2": "m^2",
                "connected_threshold_component_areas_m2": "m^2",
                "connected_threshold_component_count": "count",
                "connectivity": "1",
                "threshold_comparison": "1",
                "interpolation_performed": "1",
            },
            (
                "Cell edges define a rectilinear map in metres and matrix entries are cell-centred thicknesses in metres.",
                "Only observed cells contribute to thickness and signed net-loss summaries; no spatial interpolation is performed.",
                "Caller-selected four-neighbour or eight-neighbour threshold connectivity describes map geometry and supplies no acceptance, capacity, life or probability conclusion.",
            ),
            ("authored_rectilinear_thickness_map_cell_area_balance",),
        )
    ]
