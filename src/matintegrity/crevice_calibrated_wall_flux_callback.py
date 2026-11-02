"""Build a digest-bound Robin wall-flux callback from calibrated rate and slit geometry histories."""

from __future__ import annotations

import bisect
import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_calibrated_wall_flux_callback"
SOURCE_ID = "caller_crevice_calibrated_wall_flux_boundary"
MAX_KNOTS = 5000
MAX_CELLS = 2000


class CreviceCalibratedWallFluxRequest(Contract):
    schema_version: Literal["matintegrity.crevice_calibrated_wall_flux_callback.v1"] = (
        "matintegrity.crevice_calibrated_wall_flux_callback.v1"
    )
    callback_id: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    calibrated_wall_rate_history_result: dict
    calibrated_wall_rate_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_history: dict
    geometry_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_equilibrium_concentration_mol_m3_by_knot_by_cell: tuple[tuple[float, ...], ...] = Field(
        min_length=2, max_length=MAX_KNOTS
    )
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=256)
    temperature_clock_and_geometry_alignment_reviewed: bool
    single_species_restricted_transport_mapping_reviewed: bool
    linear_inter_knot_rate_and_surface_state_path_reviewed: bool
    robin_flux_sign_and_surface_concentration_reviewed: bool
    calibrated_condition_and_geometry_applicability_reviewed: bool

    @model_validator(mode="after")
    def validate_source_histories(self):
        if canonical_digest(self.calibrated_wall_rate_history_result) != self.calibrated_wall_rate_history_result_sha256:
            raise ValueError("calibrated wall-rate history digest mismatch")
        if canonical_digest(self.geometry_history) != self.geometry_history_sha256:
            raise ValueError("geometry history digest mismatch")
        rates_result = self.calibrated_wall_rate_history_result
        rate_values = rates_result.get("values", rates_result)
        states = self.geometry_history.get("geometry_states")
        rate_knots = rate_values.get("wall_rate_knots")
        if rates_result.get("status") != "computed" or self.geometry_history.get("status") != "computed":
            raise ValueError("computed wall-rate and geometry histories are required")
        if (
            rate_values.get("species_id") != self.species_id
            or rate_values.get("condition_id") != self.condition_id
            or rate_values.get("geometry_id") != self.geometry_id
        ):
            raise ValueError("wall-rate history species or condition identity mismatch")
        if self.geometry_history.get("geometry_id") != self.geometry_id:
            raise ValueError("geometry history identity mismatch")
        if not isinstance(states, list) or not isinstance(rate_knots, list) or len(states) != len(rate_knots):
            raise ValueError("rate and geometry histories must have the same exact knot count")
        count = self.geometry_history.get("cell_count")
        if isinstance(count, bool) or not isinstance(count, int) or not 2 <= count <= MAX_CELLS:
            raise ValueError("geometry history must contain 2..2000 cells")
        if len(self.wall_equilibrium_concentration_mol_m3_by_knot_by_cell) != len(states):
            raise ValueError("surface concentration profile must align with each exact knot")
        for index, (state, rate, surface_profile) in enumerate(zip(
            states, rate_knots, self.wall_equilibrium_concentration_mol_m3_by_knot_by_cell, strict=True
        )):
            geometry = state.get("restricted_transport_geometry")
            areas = geometry.get("wall_area_per_volume_m2_m3") if isinstance(geometry, dict) else None
            if (
                state.get("elapsed_time_s") != rate.get("elapsed_time_s")
                or not isinstance(areas, list) or len(areas) != count
                or len(surface_profile) != count
                or any(not math.isfinite(value) or value <= 0 for value in areas)
                or any(not math.isfinite(value) or value < 0 for value in surface_profile)
                or isinstance(rate.get("wall_transfer_velocity_m_s"), bool)
                or not isinstance(rate.get("wall_transfer_velocity_m_s"), (int, float))
                or not math.isfinite(rate["wall_transfer_velocity_m_s"])
                or rate["wall_transfer_velocity_m_s"] <= 0
            ):
                raise ValueError(f"geometry/rate/surface state is misaligned or invalid at knot {index}")
        if states[0].get("elapsed_time_s") != 0.0 or any(
            right.get("elapsed_time_s") <= left.get("elapsed_time_s")
            for left, right in zip(states[:-1], states[1:])
        ):
            raise ValueError("callback histories must start at zero and increase strictly")
        return self


class CreviceCalibratedWallFluxCallback:
    """Callable one-species inward wall flux for restricted transport solvers."""

    provider_id = "matintegrity.crevice_calibrated_wall_flux_callback"
    provider_revision = "1.0"
    interpolation_method = "piecewise_linear_exact_knot_bounded"

    def __init__(self, request: CreviceCalibratedWallFluxRequest):
        self.request = request
        self.source_request_sha256 = canonical_digest(request.model_dump(mode="json"))
        self.configuration_sha256 = canonical_digest({
            "provider_id": self.provider_id,
            "provider_revision": self.provider_revision,
            "request_sha256": self.source_request_sha256,
        })
        rate_values = request.calibrated_wall_rate_history_result.get("values", request.calibrated_wall_rate_history_result)
        self.times_s = tuple(float(row["elapsed_time_s"]) for row in rate_values["wall_rate_knots"])
        self.rate_m_s = tuple(float(row["wall_transfer_velocity_m_s"]) for row in rate_values["wall_rate_knots"])
        self.surface_concentration = np.asarray(
            request.wall_equilibrium_concentration_mol_m3_by_knot_by_cell, dtype=float
        )
        self.cell_count = request.geometry_history["cell_count"]
        self.species_ids = (request.species_id,)
        self.condition_id = request.condition_id
        self.geometry_id = request.geometry_id
        self.evidence = tuple(row.model_dump(mode="json") for row in request.evidence)

    def __call__(self, elapsed_time_s: float, concentrations: np.ndarray, potential_V: np.ndarray | None = None) -> np.ndarray:
        time_s = float(elapsed_time_s)
        if not math.isfinite(time_s) or time_s < self.times_s[0] or time_s > self.times_s[-1]:
            raise ValueError("callback time is outside the reviewed history support")
        state = np.asarray(concentrations, dtype=float)
        if state.shape != (1, self.cell_count) or not np.isfinite(state).all():
            raise ValueError("wall callback expects one finite species concentration per geometry cell")
        right = bisect.bisect_left(self.times_s, time_s)
        if right < len(self.times_s) and self.times_s[right] == time_s:
            k_value = self.rate_m_s[right]
            surface = self.surface_concentration[right]
        else:
            left = right - 1
            fraction = (time_s - self.times_s[left]) / (self.times_s[right] - self.times_s[left])
            k_value = self.rate_m_s[left] + fraction * (self.rate_m_s[right] - self.rate_m_s[left])
            surface = self.surface_concentration[left] + fraction * (
                self.surface_concentration[right] - self.surface_concentration[left]
            )
        inward_flux = k_value * (surface - state[0])
        if not np.isfinite(inward_flux).all():
            raise ValueError("computed wall flux exceeds finite numeric support")
        return inward_flux.reshape((1, self.cell_count))


def build_crevice_calibrated_wall_flux_callback(
    request: CreviceCalibratedWallFluxRequest,
) -> CreviceCalibratedWallFluxCallback:
    """Return the callable; pass it as ``wall_surface_flux`` to restricted transport."""
    if _missing_reviews(request):
        raise ValueError(f"wall-flux callback requires explicit reviews: {_missing_reviews(request)}")
    return CreviceCalibratedWallFluxCallback(request)


def _missing_reviews(request: CreviceCalibratedWallFluxRequest) -> list[str]:
    return [name for name in (
        "temperature_clock_and_geometry_alignment_reviewed",
        "single_species_restricted_transport_mapping_reviewed",
        "linear_inter_knot_rate_and_surface_state_path_reviewed",
        "robin_flux_sign_and_surface_concentration_reviewed",
        "calibrated_condition_and_geometry_applicability_reviewed",
    ) if not getattr(request, name)]


def evaluate_crevice_calibrated_wall_flux_callback(
    request: CreviceCalibratedWallFluxRequest,
) -> Calculation:
    """Return a serializable manifest for the callback configuration."""
    missing = _missing_reviews(request)
    if missing:
        return Calculation(status="needs_data", values={
            "callback_id": request.callback_id,
            "missing_reviews": missing,
            "calibrated_wall_rate_history_result_sha256": request.calibrated_wall_rate_history_result_sha256,
            "geometry_history_sha256": request.geometry_history_sha256,
        })
    callback = build_crevice_calibrated_wall_flux_callback(request)
    rate_values = request.calibrated_wall_rate_history_result.get("values", request.calibrated_wall_rate_history_result)
    return Calculation(values={
        "status": "computed",
        "callback_id": request.callback_id,
        "provider_id": callback.provider_id,
        "provider_revision": callback.provider_revision,
        "configuration_sha256": callback.configuration_sha256,
        "source_request_sha256": callback.source_request_sha256,
        "calibrated_wall_rate_history_result_sha256": request.calibrated_wall_rate_history_result_sha256,
        "geometry_history_sha256": request.geometry_history_sha256,
        "species_ids": [request.species_id],
        "condition_id": request.condition_id,
        "geometry_id": request.geometry_id,
        "elapsed_time_s": callback.times_s,
        "wall_transfer_velocity_m_s": callback.rate_m_s,
        "wall_flux_sign_convention": "inward positive; J = k_w * (C_surface_equilibrium - C_bulk)",
        "interpolation_method": callback.interpolation_method,
        "concentration_support_mol_m3": [
            [float(value) for value in row]
            for row in request.wall_equilibrium_concentration_mol_m3_by_knot_by_cell
        ],
        "Evidence": list(callback.evidence),
        "model_boundary": "Builds a time-interpolated Robin wall boundary callback for one species on the digest-pinned geometry grid; it does not run transport.",
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCalibratedWallFluxRequest,
        evaluator=evaluate_crevice_calibrated_wall_flux_callback,
        units={
            "elapsed_time_s[]": "s",
            "wall_transfer_velocity_m_s[]": "m/s",
            "concentration_support_mol_m3[][]": "mol/m3",
            "wall_flux_sign_convention": "mol/(m2 s)",
        },
        assumptions=(
            "A calibrated effective wall-transfer velocity and a caller-supplied equilibrium surface concentration define inward flux J=k_w(C_surface-C_bulk).",
            "Rate, surface concentration and geometry histories share exact ordered knots and cell identity; interpolation is linear only between the supplied knots and no time extrapolation is allowed.",
            "The callback supports one species and returns one inward molar flux per cell; the transport solver applies its wall-area-per-volume geometry exactly once.",
            "The caller's equilibrium surface concentration and application condition must be physically reviewed; no surface chemistry is solved here.",
            "The callback is intended for the existing restricted-transport/crevice campaign wall boundary and does not run or alter a transport calculation.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
