"""Integrate multispecies wall-transfer callbacks over changing crevice area."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, canonical_digest
from .crevice_multispecies_wall_flux_callback import (
    CreviceMultispeciesWallFluxRequest,
    build_crevice_multispecies_wall_flux_callback,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_wall_flux_inventory_history"
SOURCE_ID = "caller_crevice_wall_flux_to_species_inventory_history"
MAX_PROFILE_VALUES = 2_000_000


class CreviceWallFluxInventoryHistoryRequest(Contract):
    schema_version: Literal["matintegrity.crevice_wall_flux_inventory_history.v1"] = (
        "matintegrity.crevice_wall_flux_inventory_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    wall_flux_callback: CreviceMultispeciesWallFluxRequest
    bulk_concentration_mol_m3_by_knot_species_cell: tuple[tuple[tuple[float, ...], ...], ...] = Field(
        min_length=2, max_length=5000
    )
    bulk_concentration_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    exact_clock_species_cell_order_reviewed: bool
    piecewise_linear_bulk_concentration_path_reviewed: bool
    wall_area_from_geometry_density_and_liquid_volume_reviewed: bool
    callback_flux_sign_convention_reviewed: bool
    transfer_amount_is_not_reaction_extent_reviewed: bool

    @model_validator(mode="after")
    def validate_profiles(self):
        callback = self.wall_flux_callback
        if self.bulk_concentration_history_sha256 != canonical_digest(
            self.bulk_concentration_mol_m3_by_knot_species_cell
        ):
            raise ValueError("bulk concentration profile digest mismatch")
        states = callback.geometry_history["geometry_states"]
        species_count = len(callback.transport_species_order)
        cell_count = callback.geometry_history["cell_count"]
        if len(states) != len(self.bulk_concentration_mol_m3_by_knot_species_cell):
            raise ValueError("bulk concentration profiles must match every geometry knot")
        if len(states) * species_count * cell_count > MAX_PROFILE_VALUES:
            raise ValueError("species-by-knot-by-cell profile exceeds the bounded record budget")
        for knot_index, profiles in enumerate(self.bulk_concentration_mol_m3_by_knot_species_cell):
            if len(profiles) != species_count or any(len(profile) != cell_count for profile in profiles):
                raise ValueError(f"bulk profile dimensions do not match species and cells at knot {knot_index}")
            if any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0
                for profile in profiles for value in profile
            ):
                raise ValueError(f"bulk concentrations must be finite and nonnegative at knot {knot_index}")
        return self


def evaluate_crevice_wall_flux_inventory_history(
    request: CreviceWallFluxInventoryHistoryRequest,
) -> Calculation:
    """Integrate species wall flux times geometry-derived wall area per cell."""
    callback_request = request.wall_flux_callback
    callback = build_crevice_multispecies_wall_flux_callback(callback_request)
    times = callback.times_s
    species_ids = callback.species_ids
    cell_count = callback.cell_count
    geometry_states = callback_request.geometry_history["geometry_states"]
    widths = callback_request.geometry_history.get("cell_widths_m")
    if not isinstance(widths, list) or len(widths) != cell_count or any(
        isinstance(value, bool) or not isinstance(value, (int, float))
        or not math.isfinite(value) or value <= 0 for value in widths
    ):
        return Calculation(status="out_of_scope", values={
            "assessment_id": request.assessment_id,
            "reason": "geometry history must provide one finite positive axial cell width per cell",
        })
    request_sha = canonical_digest(request.model_dump(mode="json"))
    callback_sha = canonical_digest(callback_request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "input_sha256": request_sha,
        "callback_request_sha256": callback_sha,
        "geometry_history_sha256": callback_request.geometry_history_sha256,
        "bulk_concentration_history_sha256": request.bulk_concentration_history_sha256,
        "transport_species_order": list(species_ids),
        "elapsed_time_s": list(times),
        "flux_sign_convention": "inward positive; integrated amount is positive into the crevice liquid",
    }
    reviews = (
        "exact_clock_species_cell_order_reviewed",
        "piecewise_linear_bulk_concentration_path_reviewed",
        "wall_area_from_geometry_density_and_liquid_volume_reviewed",
        "callback_flux_sign_convention_reviewed",
        "transfer_amount_is_not_reaction_extent_reviewed",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    bulk = np.asarray(request.bulk_concentration_mol_m3_by_knot_species_cell, dtype=float)
    intervals: list[dict] = []
    quadrature = (
        (-math.sqrt(3.0 / 5.0), 5.0 / 9.0),
        (0.0, 8.0 / 9.0),
        (math.sqrt(3.0 / 5.0), 5.0 / 9.0),
    )
    try:
        for index, (left_time, right_time) in enumerate(zip(times[:-1], times[1:], strict=True)):
            duration = right_time - left_time
            if not math.isfinite(duration) or duration <= 0:
                raise ValueError("geometry/callback clock must be strictly increasing")
            left_state = geometry_states[index].get("restricted_transport_geometry")
            right_state = geometry_states[index + 1].get("restricted_transport_geometry")
            left_density = left_state.get("wall_area_per_volume_m2_m3") if isinstance(left_state, dict) else None
            right_density = right_state.get("wall_area_per_volume_m2_m3") if isinstance(right_state, dict) else None
            left_area = left_state.get("cell_cross_section_m2") if isinstance(left_state, dict) else None
            right_area = right_state.get("cell_cross_section_m2") if isinstance(right_state, dict) else None
            geometry_vectors = (left_density, right_density, left_area, right_area)
            if any(not isinstance(row, list) or len(row) != cell_count for row in geometry_vectors):
                raise ValueError(f"geometry area/density vector is incomplete at interval {index}")
            if any(
                isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value <= 0
                for row in geometry_vectors for value in row
            ):
                raise ValueError(f"geometry area/density values must be finite and positive at interval {index}")

            amount = np.zeros((len(species_ids), cell_count), dtype=float)
            for node, weight in quadrature:
                fraction = (node + 1.0) / 2.0
                time_s = left_time + fraction * duration
                concentrations = bulk[index] + fraction * (bulk[index + 1] - bulk[index])
                flux = callback(time_s, concentrations)
                density = np.asarray(left_density) + fraction * (np.asarray(right_density) - np.asarray(left_density))
                cross_section = np.asarray(left_area) + fraction * (np.asarray(right_area) - np.asarray(left_area))
                wall_area = density * cross_section * np.asarray(widths, dtype=float)
                contribution = (duration / 2.0) * weight * flux * wall_area[None, :]
                if not np.isfinite(contribution).all():
                    raise ArithmeticError("integrated wall-transfer amount exceeds finite numerical support")
                amount += contribution
            intervals.append({
                "interval_index": index,
                "start_time_s": left_time,
                "end_time_s": right_time,
                "net_wall_transfer_mol_by_species_cell": {
                    species_id: amount[species_index].tolist()
                    for species_index, species_id in enumerate(species_ids)
                },
                "net_wall_transfer_mol_by_species": {
                    species_id: float(math.fsum(amount[species_index].tolist()))
                    for species_index, species_id in enumerate(species_ids)
                },
                "integration_method": "three-point Gauss-Legendre; exact through polynomial degree five for the declared linear k, surface concentration, bulk concentration, wall-area density, and slit cross-section paths",
            })
    except (ArithmeticError, ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "completed_interval_count": len(intervals),
            "intervals": intervals,
            "failed_interval_index": len(intervals),
            "reason": f"wall-flux inventory integration failed: {type(error).__name__}",
        })

    total_by_species = {
        species_id: float(math.fsum(
            row["net_wall_transfer_mol_by_species"][species_id] for row in intervals
        ))
        for species_id in species_ids
    }
    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(intervals),
        "intervals": intervals,
        "net_wall_transfer_mol_by_species": total_by_species,
        "integration_method": "three-point Gauss-Legendre per exact geometry interval",
        "interpretation_boundary": "This is net species transfer through the declared wall boundary. It is not a surface reaction extent, metal loss, solid precipitation amount, or independently validated wall law.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceWallFluxInventoryHistoryRequest,
        evaluator=evaluate_crevice_wall_flux_inventory_history,
        units={
            "elapsed_time_s[]": "s",
            "bulk_concentration_mol_m3_by_knot_species_cell": "mol/m3",
            "net_wall_transfer_mol_by_species_cell.*": "mol",
            "net_wall_transfer_mol_by_species.*": "mol",
        },
        assumptions=(
            "The callback rate, wall surface concentration, bulk concentration, wall-area density and slit cross section are reconstructed linearly within each exact shared time interval.",
            "Cell wall area is computed as wall area per liquid volume times cross-sectional liquid area times axial cell width.",
            "Three-point Gauss-Legendre integrates the resulting polynomial transfer rate exactly under the declared linear inputs; no such exactness applies to nonlinear paths.",
            "Positive integrated amount denotes transfer into the crevice liquid according to the callback's inward-positive convention.",
            "The amount is a species boundary transfer ledger only; it does not imply stoichiometric reaction, metal loss or phase formation.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
