"""Compose independent calibrated wall-transfer laws into a multispecies transport callback."""

from __future__ import annotations

import bisect
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_multispecies_wall_flux_callback"
SOURCE_ID = "caller_crevice_multispecies_calibrated_wall_flux_boundary"
MAX_KNOTS = 5000
MAX_CELLS = 2000
MAX_SPECIES = 100
MAX_PROFILE_VALUES = 2_000_000


class CreviceSpeciesWallRateHistory(Contract):
    species_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    rate_history_result: dict
    rate_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_equilibrium_concentration_mol_m3_by_knot_by_cell: tuple[tuple[float, ...], ...] = Field(
        min_length=2, max_length=MAX_KNOTS
    )
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def valid_history(self):
        if canonical_digest(self.rate_history_result) != self.rate_history_result_sha256:
            raise ValueError("species wall-rate history digest mismatch")
        result = self.rate_history_result
        values = result.get("values", result)
        knots = values.get("wall_rate_knots")
        if result.get("status") != "computed" or values.get("species_id") != self.species_id or values.get("condition_id") != self.condition_id:
            raise ValueError("computed rate history species/condition identity mismatch")
        if not isinstance(knots, list) or len(knots) != len(self.wall_equilibrium_concentration_mol_m3_by_knot_by_cell):
            raise ValueError("surface concentration and rate histories require equal knot counts")
        for index, (rate, profile) in enumerate(zip(knots, self.wall_equilibrium_concentration_mol_m3_by_knot_by_cell, strict=True)):
            velocity = rate.get("wall_transfer_velocity_m_s") if isinstance(rate, dict) else None
            if (
                isinstance(velocity, bool) or not isinstance(velocity, (int, float))
                or not math.isfinite(velocity) or velocity < 0
                or any(not math.isfinite(value) or value < 0 for value in profile)
            ):
                raise ValueError(f"wall velocity or surface concentration is invalid at knot {index}")
        return self


class CreviceMultispeciesWallFluxRequest(Contract):
    schema_version: Literal["matintegrity.crevice_multispecies_wall_flux_callback.v1"] = (
        "matintegrity.crevice_multispecies_wall_flux_callback.v1"
    )
    callback_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    geometry_history: dict
    geometry_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transport_species_order: tuple[str, ...] = Field(min_length=1, max_length=MAX_SPECIES)
    species_histories: tuple[CreviceSpeciesWallRateHistory, ...] = Field(min_length=1, max_length=MAX_SPECIES)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=256)
    exact_shared_clock_and_cell_mapping_reviewed: bool
    independent_species_wall_laws_reviewed: bool
    linear_inter_knot_reconstruction_reviewed: bool
    wall_flux_sign_and_surface_state_reviewed: bool
    transport_species_order_reviewed: bool

    @model_validator(mode="after")
    def validate_grid(self):
        if canonical_digest(self.geometry_history) != self.geometry_history_sha256:
            raise ValueError("geometry history digest mismatch")
        if self.geometry_history.get("status") != "computed" or self.geometry_history.get("geometry_id") != self.geometry_id:
            raise ValueError("computed geometry history identity mismatch")
        states = self.geometry_history.get("geometry_states")
        cell_count = self.geometry_history.get("cell_count")
        if not isinstance(states, list) or not 2 <= len(states) <= MAX_KNOTS:
            raise ValueError("geometry history requires 2..5000 exact knots")
        if isinstance(cell_count, bool) or not isinstance(cell_count, int) or not 2 <= cell_count <= MAX_CELLS:
            raise ValueError("geometry history requires 2..2000 cells")
        identifiers = tuple(row.species_id for row in self.species_histories)
        if len(set(identifiers)) != len(identifiers) or identifiers != self.transport_species_order:
            raise ValueError("species histories must exactly follow the declared transport species order")
        if not self.evidence or len({row.source_id for row in self.evidence}) != len(self.evidence):
            raise ValueError("callback evidence must be nonempty and have unique source IDs")
        if len(states) * cell_count * len(identifiers) > MAX_PROFILE_VALUES:
            raise ValueError("species-by-knot-by-cell profile exceeds the bounded record budget")
        if any(len(item.wall_equilibrium_concentration_mol_m3_by_knot_by_cell) != len(states) for item in self.species_histories):
            raise ValueError("all species rate histories must align to every geometry knot")
        if any(
            len(profile) != cell_count
            for item in self.species_histories
            for profile in item.wall_equilibrium_concentration_mol_m3_by_knot_by_cell
        ):
            raise ValueError("every surface concentration profile needs one value per geometry cell")
        geometry_times = [state.get("elapsed_time_s") for state in states]
        if (
            geometry_times[0] != 0.0
            or any(not isinstance(time, (int, float)) or not math.isfinite(time) for time in geometry_times)
            or any(right <= left for left, right in zip(geometry_times[:-1], geometry_times[1:]))
        ):
            raise ValueError("geometry time knots must start at zero and increase strictly")
        for species in self.species_histories:
            values = species.rate_history_result.get("values", species.rate_history_result)
            if (
                values.get("geometry_id") != self.geometry_id
                or not isinstance(values.get("wall_rate_knots"), list)
                or len(values["wall_rate_knots"]) != len(states)
            ):
                raise ValueError(f"rate history geometry identity mismatch for {species.species_id!r}")
            rate_knots = values["wall_rate_knots"]
            for index, (state, rate) in enumerate(zip(states, rate_knots, strict=True)):
                geometry = state.get("restricted_transport_geometry")
                wall_density = geometry.get("wall_area_per_volume_m2_m3") if isinstance(geometry, dict) else None
                if (
                    not isinstance(rate, dict)
                    or state.get("elapsed_time_s") != rate.get("elapsed_time_s")
                    or not isinstance(wall_density, list) or len(wall_density) != cell_count
                    or any(not math.isfinite(value) or value <= 0 for value in wall_density)
                ):
                    raise ValueError(f"rate/geometry time knot mismatch for {species.species_id!r} at {index}")
        return self


class CreviceMultispeciesWallFluxCallback:
    provider_id = "matintegrity.crevice_multispecies_wall_flux_callback"
    provider_revision = "1.0"
    interpolation_method = "piecewise_linear_exact_knot_bounded"

    def __init__(self, request: CreviceMultispeciesWallFluxRequest):
        self.request = request
        self.species_ids = request.transport_species_order
        self.cell_count = request.geometry_history["cell_count"]
        first = request.species_histories[0].rate_history_result.get("values", request.species_histories[0].rate_history_result)
        self.times_s = tuple(float(row["elapsed_time_s"]) for row in first["wall_rate_knots"])
        self.rate_by_species = np.asarray([
            [float(row["wall_transfer_velocity_m_s"]) for row in item.rate_history_result.get("values", item.rate_history_result)["wall_rate_knots"]]
            for item in request.species_histories
        ], dtype=float)
        self.surface_by_species_knot_cell = np.asarray([
            item.wall_equilibrium_concentration_mol_m3_by_knot_by_cell for item in request.species_histories
        ], dtype=float)
        self.source_request_sha256 = canonical_digest(request.model_dump(mode="json"))
        self.configuration_sha256 = canonical_digest({
            "provider_id": self.provider_id,
            "provider_revision": self.provider_revision,
            "source_request_sha256": self.source_request_sha256,
        })
        self.geometry_id = request.geometry_id

    def __call__(self, elapsed_time_s: float, concentrations: np.ndarray, potential_V: np.ndarray | None = None) -> np.ndarray:
        time_s = float(elapsed_time_s)
        if not math.isfinite(time_s) or time_s < self.times_s[0] or time_s > self.times_s[-1]:
            raise ValueError("callback time is outside the reviewed history support")
        state = np.asarray(concentrations, dtype=float)
        if state.shape != (len(self.species_ids), self.cell_count) or not np.isfinite(state).all():
            raise ValueError("wall callback concentration shape must match exact species and cell order")
        right = bisect.bisect_left(self.times_s, time_s)
        if right < len(self.times_s) and self.times_s[right] == time_s:
            rates = self.rate_by_species[:, right]
            surface = self.surface_by_species_knot_cell[:, right, :]
        else:
            left = right - 1
            fraction = (time_s - self.times_s[left]) / (self.times_s[right] - self.times_s[left])
            rates = self.rate_by_species[:, left] + fraction * (self.rate_by_species[:, right] - self.rate_by_species[:, left])
            surface = self.surface_by_species_knot_cell[:, left, :] + fraction * (
                self.surface_by_species_knot_cell[:, right, :] - self.surface_by_species_knot_cell[:, left, :]
            )
        inward = rates[:, None] * (surface - state)
        if not np.isfinite(inward).all():
            raise ValueError("computed multispecies wall flux exceeds finite support")
        return inward


def _missing_reviews(request: CreviceMultispeciesWallFluxRequest) -> list[str]:
    return [name for name in (
        "exact_shared_clock_and_cell_mapping_reviewed",
        "independent_species_wall_laws_reviewed",
        "linear_inter_knot_reconstruction_reviewed",
        "wall_flux_sign_and_surface_state_reviewed",
        "transport_species_order_reviewed",
    ) if not getattr(request, name)]


def build_crevice_multispecies_wall_flux_callback(
    request: CreviceMultispeciesWallFluxRequest,
) -> CreviceMultispeciesWallFluxCallback:
    missing = _missing_reviews(request)
    if missing:
        raise ValueError(f"multispecies wall-flux callback requires explicit reviews: {missing}")
    return CreviceMultispeciesWallFluxCallback(request)


def evaluate_crevice_multispecies_wall_flux_callback(
    request: CreviceMultispeciesWallFluxRequest,
) -> Calculation:
    missing = _missing_reviews(request)
    if missing:
        return Calculation(status="needs_data", values={"callback_id": request.callback_id, "missing_reviews": missing})
    callback = build_crevice_multispecies_wall_flux_callback(request)
    return Calculation(values={
        "status": "computed",
        "callback_id": request.callback_id,
        "provider_id": callback.provider_id,
        "provider_revision": callback.provider_revision,
        "configuration_sha256": callback.configuration_sha256,
        "source_request_sha256": callback.source_request_sha256,
        "geometry_history_sha256": request.geometry_history_sha256,
        "transport_species_order": list(callback.species_ids),
        "elapsed_time_s": list(callback.times_s),
        "rate_history_result_sha256_by_species": {
            item.species_id: item.rate_history_result_sha256 for item in request.species_histories
        },
        "wall_flux_sign_convention": "inward positive; each independent species J_i = k_i(T) * (C_surface_i - C_bulk_i)",
        "interpolation_method": callback.interpolation_method,
        "species_reaction_coupling": False,
        "model_boundary": "Builds a transport-order multispecies wall boundary callback; it does not solve coupled surface reaction or transport.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceMultispeciesWallFluxRequest,
        evaluator=evaluate_crevice_multispecies_wall_flux_callback,
        units={
            "elapsed_time_s[]": "s",
            "species_histories[].wall_rate_history_result.values.wall_rate_knots[].wall_transfer_velocity_m_s": "m/s",
            "species_histories[].wall_equilibrium_concentration_mol_m3_by_knot_by_cell": "mol/m3",
            "wall_flux_sign_convention": "mol/(m2 s)",
        },
        assumptions=(
            "Each transported species has one digest-pinned calibrated wall-transfer history and an explicit equilibrium surface-concentration profile on the same geometry knots.",
            "Each species obeys an independent linear wall law; this callback does not represent stoichiometrically coupled surface reactions or competition for shared sites.",
            "Species order exactly matches the transport request, and each wall rate/profile is linearly interpolated only between common exact knots without extrapolation.",
            "The transport solver applies its geometry wall-area density once after receiving the surface flux matrix.",
            "The caller reviews surface-state concentration meaning, calibration applicability and each independent wall-law assumption.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
