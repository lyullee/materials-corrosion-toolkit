"""Caller-mapped annular contact grid connectivity screen for radial open paths."""

from __future__ import annotations

import heapq
import math
from collections import deque
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fabrication.gasket_radial_open_path_screen"
MAX_GRID_CELLS = 250_000
TWO_PI = 2.0 * math.pi


class GasketPolarContactMap(Contract):
    radial_cell_edges_m: tuple[Nonnegative, ...] = Field(min_length=2, max_length=1001)
    angular_sector_edges_rad: tuple[float, ...] = Field(min_length=2, max_length=1001)
    mean_contact_pressure_by_cell_Pa: tuple[tuple[Nonnegative, ...], ...] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def aligned_annular_grid(self):
        radial_count = len(self.radial_cell_edges_m) - 1
        angular_count = len(self.angular_sector_edges_rad) - 1
        if radial_count != len(self.mean_contact_pressure_by_cell_Pa):
            raise ValueError("pressure rows must align with radial cells")
        if any(len(row) != angular_count for row in self.mean_contact_pressure_by_cell_Pa):
            raise ValueError("each radial pressure row must align with angular sectors")
        if radial_count * angular_count > MAX_GRID_CELLS:
            raise ValueError("annular contact grid exceeds the supported cell budget")
        if any(right <= left for left, right in zip(self.radial_cell_edges_m, self.radial_cell_edges_m[1:])):
            raise ValueError("radial cell edges must strictly increase")
        if any(right <= left for left, right in zip(self.angular_sector_edges_rad, self.angular_sector_edges_rad[1:])):
            raise ValueError("angular sector edges must strictly increase")
        if any(not math.isfinite(value) for value in self.angular_sector_edges_rad):
            raise ValueError("angular sector edges must be finite")
        if any(not math.isfinite(value) for value in self.radial_cell_edges_m):
            raise ValueError("radial cell edges must be finite")
        if any(not math.isfinite(value) for row in self.mean_contact_pressure_by_cell_Pa for value in row):
            raise ValueError("cell contact pressures must be finite")
        span = self.angular_sector_edges_rad[-1] - self.angular_sector_edges_rad[0]
        if not math.isclose(span, TWO_PI, rel_tol=1.0e-10, abs_tol=1.0e-10):
            raise ValueError("angular sector edges must span exactly one full ring")
        return self


class GasketRadialOpenPathScreen(Contract):
    """Map a caller pressure field to connected low-contact radial paths."""

    schema_version: Literal["matintegrity.gasket_radial_open_path_screen.v1"] = (
        "matintegrity.gasket_radial_open_path_screen.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    contact_map: GasketPolarContactMap
    map_provider_id: str = Field(min_length=1)
    map_provider_revision: str = Field(min_length=1)
    map_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    map_usage_license_id: str = Field(min_length=1)
    map_evidence: tuple[Evidence, ...] = Field(min_length=1)
    minimum_closing_contact_pressure_Pa: Positive
    criterion_provider_id: str = Field(min_length=1)
    criterion_provider_revision: str = Field(min_length=1)
    criterion_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    criterion_usage_license_id: str = Field(min_length=1)
    criterion_evidence: tuple[Evidence, ...] = Field(min_length=1)
    grid_to_annular_seal_and_flow_direction_reviewed: bool
    pressure_definition_and_threshold_reviewed: bool
    mesh_resolution_and_four_neighbor_connectivity_reviewed: bool
    scope_and_time_alignment_reviewed: bool
    evidence_rights_and_computational_use_reviewed: bool

    @model_validator(mode="after")
    def bind_data_and_criterion(self):
        map_record = {
            "provider_id": self.map_provider_id,
            "provider_revision": self.map_provider_revision,
            "physical_scope_id": self.physical_scope_id,
            "contact_map": self.contact_map.model_dump(mode="json"),
        }
        if canonical_digest(map_record) != self.map_record_sha256:
            raise ValueError("pressure-map digest does not bind the annular grid")
        if not any(item.source_id == self.map_provider_id and item.sha256 == self.map_record_sha256
                   and item.license_id == self.map_usage_license_id for item in self.map_evidence):
            raise ValueError("map Evidence must pin pressure data and its usage license")
        criterion_record = {
            "provider_id": self.criterion_provider_id,
            "provider_revision": self.criterion_provider_revision,
            "physical_scope_id": self.physical_scope_id,
            "map_record_sha256": self.map_record_sha256,
            "minimum_closing_contact_pressure_Pa": self.minimum_closing_contact_pressure_Pa,
            "open_cell_rule": "cell_mean_contact_pressure_below_threshold",
            "connectivity": "radial_and_periodic_angular_four_neighbor",
        }
        if canonical_digest(criterion_record) != self.criterion_record_sha256:
            raise ValueError("criterion digest does not bind the threshold, grid and connectivity rule")
        if not any(item.source_id == self.criterion_provider_id and item.sha256 == self.criterion_record_sha256
                   and item.license_id == self.criterion_usage_license_id for item in self.criterion_evidence):
            raise ValueError("threshold Evidence must pin criterion and its usage license")
        return self


def _cell_areas(grid: GasketPolarContactMap) -> list[list[float]]:
    areas: list[list[float]] = []
    for i, (r0, r1) in enumerate(zip(grid.radial_cell_edges_m, grid.radial_cell_edges_m[1:])):
        row = []
        radial_factor = 0.5 * (r1 * r1 - r0 * r0)
        for a0, a1 in zip(grid.angular_sector_edges_rad, grid.angular_sector_edges_rad[1:]):
            area = radial_factor * (a1 - a0)
            if not math.isfinite(area) or area <= 0.0:
                raise OverflowError("annular cell area is outside finite positive support")
            row.append(area)
        areas.append(row)
    return areas


def _neighbors(i: int, j: int, nr: int, na: int):
    if i > 0:
        yield i - 1, j
    if i + 1 < nr:
        yield i + 1, j
    yield i, (j - 1) % na
    yield i, (j + 1) % na


def _open_components(mask: list[list[bool]], areas: list[list[float]]) -> tuple[int, float, list[dict]]:
    nr, na = len(mask), len(mask[0])
    visited = [[False] * na for _ in range(nr)]
    component_count = 0
    open_area_terms = []
    spanning_components = []
    for i in range(nr):
        for j in range(na):
            if not mask[i][j] or visited[i][j]:
                continue
            queue = deque([(i, j)])
            visited[i][j] = True
            cell_count = 0
            radial_min = radial_max = i
            angular_min = angular_max = j
            area_terms = []
            touches_inner = False
            touches_outer = False
            while queue:
                ci, cj = queue.popleft()
                cell_count += 1
                radial_min = min(radial_min, ci)
                radial_max = max(radial_max, ci)
                angular_min = min(angular_min, cj)
                angular_max = max(angular_max, cj)
                area_terms.append(areas[ci][cj])
                touches_inner |= ci == 0
                touches_outer |= ci == nr - 1
                for ni, nj in _neighbors(ci, cj, nr, na):
                    if mask[ni][nj] and not visited[ni][nj]:
                        visited[ni][nj] = True
                        queue.append((ni, nj))
            component_area = math.fsum(area_terms)
            component_count += 1
            open_area_terms.append(component_area)
            if touches_inner and touches_outer:
                spanning_components.append({
                    "component_index": component_count - 1,
                    "cell_count": cell_count,
                    "open_area_m2": component_area,
                    "radial_index_min_max": [radial_min, radial_max],
                    "angular_index_min_max": [angular_min, angular_max],
                })
    return component_count, math.fsum(open_area_terms), spanning_components


def _minimum_bottleneck_path(pressure: tuple[tuple[float, ...], ...]) -> tuple[float, list[list[int]]]:
    nr, na = len(pressure), len(pressure[0])
    best = [[math.inf] * na for _ in range(nr)]
    previous: list[list[tuple[int, int] | None]] = [[None] * na for _ in range(nr)]
    heap = []
    for j in range(na):
        value = pressure[0][j]
        best[0][j] = value
        heapq.heappush(heap, (value, 0, j))
    target = None
    while heap:
        value, i, j = heapq.heappop(heap)
        if value != best[i][j]:
            continue
        if i == nr - 1:
            target = (i, j)
            break
        for ni, nj in _neighbors(i, j, nr, na):
            candidate = max(value, pressure[ni][nj])
            if candidate < best[ni][nj]:
                best[ni][nj] = candidate
                previous[ni][nj] = (i, j)
                heapq.heappush(heap, (candidate, ni, nj))
    if target is None:
        raise RuntimeError("annular grid has no radial route")
    path = []
    current: tuple[int, int] | None = target
    while current is not None:
        path.append([current[0], current[1]])
        current = previous[current[0]][current[1]]
    path.reverse()
    return best[target[0]][target[1]], path


def evaluate_gasket_radial_open_path_screen(request: GasketRadialOpenPathScreen) -> Calculation:
    """Find thresholded radial open components and minimum contact-pressure bottleneck route."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "map_record_sha256": request.map_record_sha256,
        "criterion_record_sha256": request.criterion_record_sha256,
        "input_sha256": digest,
        "model_id": MODEL_ID,
    }
    reviews = {
        "grid_to_annular_seal_and_flow_direction_reviewed": request.grid_to_annular_seal_and_flow_direction_reviewed,
        "pressure_definition_and_threshold_reviewed": request.pressure_definition_and_threshold_reviewed,
        "mesh_resolution_and_four_neighbor_connectivity_reviewed": request.mesh_resolution_and_four_neighbor_connectivity_reviewed,
        "scope_and_time_alignment_reviewed": request.scope_and_time_alignment_reviewed,
        "evidence_rights_and_computational_use_reviewed": request.evidence_rights_and_computational_use_reviewed,
    }
    missing = [name for name, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    try:
        areas = _cell_areas(request.contact_map)
        component_count, open_area, spanning = _open_components(
            [[p < request.minimum_closing_contact_pressure_Pa for p in row]
             for row in request.contact_map.mean_contact_pressure_by_cell_Pa],
            areas,
        )
        bottleneck, path = _minimum_bottleneck_path(request.contact_map.mean_contact_pressure_by_cell_Pa)
    except (ArithmeticError, OverflowError, RuntimeError, ValueError):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "annular_geometry_or_path_search_exceeded_finite_support",
        })
    try:
        total_area = math.fsum(value for row in areas for value in row)
        total_pressure_area = math.fsum(
            pressure * area
            for pressure_row, area_row in zip(request.contact_map.mean_contact_pressure_by_cell_Pa, areas)
            for pressure, area in zip(pressure_row, area_row)
        )
        mean_pressure = total_pressure_area / total_area
    except (ArithmeticError, OverflowError, ValueError):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "area_weighted_pressure_summary_exceeded_finite_support",
        })
    if not all(math.isfinite(value) for value in (total_area, open_area, total_pressure_area, mean_pressure)):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "area_weighted_pressure_summary_exceeded_finite_support",
        })
    return Calculation(values=base | {
        "radial_cell_count": len(areas),
        "angular_sector_count": len(areas[0]),
        "total_contact_area_m2": total_area,
        "area_weighted_mean_contact_pressure_Pa": mean_pressure,
        "open_area_below_threshold_m2": open_area,
        "open_area_fraction": open_area / total_area,
        "open_component_count": component_count,
        "radial_spanning_open_path_count": len(spanning),
        "spanning_open_components": spanning,
        "minimum_bottleneck_contact_pressure_Pa": bottleneck,
        "spanning_open_path_exists_at_threshold": bottleneck < request.minimum_closing_contact_pressure_Pa,
        "minimum_bottleneck_path_cell_count": len(path),
        "minimum_bottleneck_path_preview_radial_angular_cells": path[:10] + (path[-10:] if len(path) > 10 else []),
        "minimum_bottleneck_path_sha256": canonical_digest(path),
        "connectivity_rule": "four_neighbor_radial_and_periodic_angular",
        "open_cell_rule": "mean_cell_contact_pressure_below_caller_threshold",
        "interpretation": "geometric_radial_open_path_screen_only",
        "limitations": [
            "The polar grid and cellwise mean contact pressures are caller-supplied; subcell contact gaps, roughness and local aperture are unresolved.",
            "Four-neighbor connectivity without diagonal shortcuts is a discrete topology convention and can change with mesh resolution.",
            "A connected low-pressure path does not calculate fluid flow, leak rate, seal acceptance or qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketRadialOpenPathScreen,
        evaluate_gasket_radial_open_path_screen,
        {
            "total_contact_area_m2": "m^2",
            "area_weighted_mean_contact_pressure_Pa": "Pa",
            "open_area_below_threshold_m2": "m^2",
            "open_area_fraction": "1",
            "minimum_bottleneck_contact_pressure_Pa": "Pa",
        },
        (
            "The supplied cell pressure map is interpreted on an annulus partitioned by radial and full-ring angular edges.",
            "Cells below a caller threshold are open; four-neighbor connectivity wraps around the angular coordinate.",
            "The minimum bottleneck is the minimum, over radial cell paths, of the highest cell pressure on that path.",
        ),
        (
            "caller_gasket_annular_contact_pressure_map",
            "caller_radial_seal_threshold_and_mesh_connectivity",
            "annular_cell_area_and_four_neighbor_radial_path_graph",
            "gasket_contact_open_path_topology_screen",
        ),
        qualification="user_model",
    )]
