"""Translate a pinned electrochemical metal-loss ledger into a time-supported wall flux."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, canonical_digest
from .registry import ModelSpec

PROVIDER_ID = "matintegrity.electrochemical_metal_loss_wall_flux_schedule"
PROVIDER_REVISION = "1"
INTERFACE_ID = "integration.electrochemical_wall_flux_schedule"
SOURCE_ID = "caller_electrochemical_metal_loss_wall_flux_schedule"


class ElectrochemicalWallFluxScheduleRequest(Contract):
    """Caller-reviewed area-average anodic source schedule for restricted transport."""

    schema_version: Literal["matintegrity.electrochemical_wall_flux_schedule.v1"] = "matintegrity.electrochemical_wall_flux_schedule.v1"
    metal_loss_result: AssessmentResult
    metal_loss_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    species_ids: tuple[str, ...] = Field(min_length=1)
    cell_count: int = Field(ge=2, le=2000, strict=True)
    local_average_flux_mapping_reviewed: bool
    reaction_surface_area_is_comparable_across_selected_branches_reviewed: bool
    source_clock_origin_rebasing_reviewed: bool
    computational_use_authorized: bool
    local_only_authorized: bool

    @model_validator(mode="after")
    def source_is_complete(self):
        result = self.metal_loss_result
        if result.model_id != "integration.electrochemical_partial_current_metal_loss" or result.status != "computed":
            raise ValueError("a computed electrochemical partial-current metal-loss result is required")
        if canonical_digest(result.model_dump(mode="json")) != self.metal_loss_result_sha256:
            raise ValueError("complete metal-loss AssessmentResult digest mismatch")
        if not (self.local_average_flux_mapping_reviewed and
                self.reaction_surface_area_is_comparable_across_selected_branches_reviewed and
                self.source_clock_origin_rebasing_reviewed and self.computational_use_authorized and
                self.local_only_authorized):
            raise ValueError("explicit flux mapping, branch-area, clock and local computational reviews are required")
        if len(set(self.species_ids)) != len(self.species_ids) or any(not value.strip() for value in self.species_ids):
            raise ValueError("transport species IDs must be unique and non-empty")
        mapping = result.values.get("reaction_to_metal_mapping")
        intervals = result.values.get("interval_metal_loss")
        if not isinstance(mapping, list) or not mapping or not isinstance(intervals, list) or not intervals:
            raise ValueError("metal-loss result must include reaction mappings and interval history")
        reaction_rows = {row.get("reaction_id"): row for row in mapping if isinstance(row, dict)}
        if len(reaction_rows) != len(mapping) or None in reaction_rows:
            raise ValueError("reaction-to-metal mapping is invalid")
        if any(row.get("metal_species_id") not in self.species_ids for row in reaction_rows.values()):
            raise ValueError("all mapped dissolved metal species must exist in the transport species basis")
        times: list[float] = []
        expected_ids = tuple(reaction_rows)
        areas: list[float] = []
        for index, interval in enumerate(intervals):
            if not isinstance(interval, dict):
                raise ValueError("metal-loss intervals must be objects")
            start, end = interval.get("start_time_s"), interval.get("end_time_s")
            if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in (start, end))
                    or end <= start or not math.isfinite(float(end) - float(start))):
                raise ValueError("metal-loss interval times must be finite with positive duration")
            if index and start != times[-1]:
                raise ValueError("metal-loss intervals must be exactly contiguous")
            if not index:
                times.append(float(start))
            times.append(float(end))
            rows = interval.get("reaction_metal_loss")
            if (not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows)
                    or tuple(row.get("reaction_id") for row in rows) != expected_ids):
                raise ValueError("interval reaction rows must exactly match source mapping order")
            for row in rows:
                amount, area = row.get("anodic_metal_removal_mol"), row.get("exposed_area_m2")
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in (amount, area)) or amount < 0 or area <= 0:
                    raise ValueError("anodic metal amount and exposed area must be finite and physically nonnegative/positive")
                areas.append(float(area))
        if not math.isfinite(times[-1] - times[0]) or times[-1] <= times[0]:
            raise ValueError("rebased source schedule duration must be finite and positive")
        if times[0] != 0.0 and not self.source_clock_origin_rebasing_reviewed:
            raise ValueError("nonzero source origin requires explicit mapping to transport elapsed time zero")
        if areas and any(not math.isclose(a, areas[0], rel_tol=1e-10, abs_tol=0.0) for a in areas[1:]):
            raise ValueError("selected electrochemical branches must use one common exposed-area basis")
        return self


def build_electrochemical_wall_flux_schedule(
    request: ElectrochemicalWallFluxScheduleRequest,
) -> Callable[[float, np.ndarray, np.ndarray | None], np.ndarray]:
    """Build a global-area-average, piecewise-constant anodic metal source.

    Flux is derived from each upstream interval's anodic metal amount divided
    by its duration and pinned common exposure area. It is repeated over cells
    under the caller's explicit uniform local-flux mapping review. When used
    with moving geometry, the transport solver integrates this fixed flux
    density over its changing surface area; the result need not equal the
    upstream total ledger after the geometry changes.
    """
    result = request.metal_loss_result
    mappings = {row["reaction_id"]: row for row in result.values["reaction_to_metal_mapping"]}
    species_index = {name: i for i, name in enumerate(request.species_ids)}
    intervals = result.values["interval_metal_loss"]
    origin = float(intervals[0]["start_time_s"])
    times = [0.0, *(float(row["end_time_s"]) - origin for row in intervals)]
    fluxes: list[np.ndarray] = []
    for interval in intervals:
        duration = float(interval["end_time_s"]) - float(interval["start_time_s"])
        flux = np.zeros(len(request.species_ids), dtype=float)
        for row in interval["reaction_metal_loss"]:
            mapping = mappings[row["reaction_id"]]
            rate_density = float(row["anodic_metal_removal_mol"]) / duration / float(row["exposed_area_m2"])
            index = species_index[mapping["metal_species_id"]]
            flux[index] += rate_density
        if not np.isfinite(flux).all():
            raise ValueError("scheduled anodic wall flux exceeds finite numeric support")
        fluxes.append(flux)

    def callback(time_s: float, concentrations: np.ndarray, potential_V: np.ndarray | None) -> np.ndarray:
        if isinstance(time_s, bool) or not isinstance(time_s, (int, float, np.number)) or not math.isfinite(float(time_s)):
            raise ValueError("wall-flux callback time must be finite")
        t = float(time_s)
        if t < times[0] or t > times[-1]:
            raise ValueError("wall-flux callback time is outside the source schedule")
        state = np.asarray(concentrations, dtype=float)
        expected = (len(request.species_ids), request.cell_count)
        if state.shape != expected or not np.isfinite(state).all() or np.any(state < 0):
            raise ValueError("concentrations must match the configured finite nonnegative species-by-cell basis")
        if potential_V is not None:
            potential = np.asarray(potential_V, dtype=float)
            if potential.shape != (request.cell_count,) or not np.isfinite(potential).all():
                raise ValueError("potential vector must be finite and aligned with transport cells")
        interval_index = next((i for i, right in enumerate(times[1:]) if t < right), len(fluxes) - 1)
        return np.repeat(fluxes[interval_index][:, None], request.cell_count, axis=1)

    callback.provider_id = PROVIDER_ID
    callback.provider_revision = PROVIDER_REVISION
    callback.configuration_sha256 = canonical_digest(request.model_dump(mode="json"))
    callback.source_result_sha256 = request.metal_loss_result_sha256
    callback.species_ids = request.species_ids
    callback.interval_support_s = (times[0], times[-1])
    callback.flux_basis = "area_average_anodic_metal_mol_m2_s"
    callback.uniform_cell_mapping_reviewed = request.local_average_flux_mapping_reviewed
    callback.source_clock_origin_s = origin
    return callback


def _registered_evaluator(request: ElectrochemicalWallFluxScheduleRequest) -> Calculation:
    return Calculation(values={
        "model_id": INTERFACE_ID,
        "configuration_sha256": canonical_digest(request.model_dump(mode="json")),
        "source_result_sha256": request.metal_loss_result_sha256,
        "species_ids": list(request.species_ids),
        "cell_count": request.cell_count,
        "interval_support_s": [0.0, float(request.metal_loss_result.values["interval_metal_loss"][-1]["end_time_s"])-float(request.metal_loss_result.values["interval_metal_loss"][0]["start_time_s"])],
        "callback_builder_available": True,
        "callback_signature": "(elapsed_time_s, species_by_cell_concentration, optional_cell_potential) -> anodic_metal_wall_flux_mol_m2_s",
        "interpretation_limit": "caller-reviewed uniform local mapping of an upstream area-average anodic source; moving-boundary integration may differ from upstream ledger",
    }, notes=("The registry exposes the validated callback contract; Python callers create the callable with build_electrochemical_wall_flux_schedule.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=INTERFACE_ID,
        input_type=ElectrochemicalWallFluxScheduleRequest,
        evaluator=_registered_evaluator,
        units={"interval_support_s": "s", "wall_flux": "mol/m2/s"},
        assumptions=("The upstream metal-loss ledger is digest-pinned and only anodic metal removal is mapped.", "Uniform distribution over transport cells is a caller-reviewed approximation; changing surface geometry need not preserve the original total ledger."),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
