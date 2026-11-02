"""Validate provider-neutral CFD histories for crevice transport callbacks."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from ..restricted_transport import RestrictedTransportRequest


class ExternalCreviceSolverHistory(Contract):
    """Normalized, geometry-bound pressure and face-velocity receipt from an external solver."""

    schema_version: Literal["matintegrity.external_crevice_solver_history.v1"] = (
        "matintegrity.external_crevice_solver_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_run_id: str = Field(min_length=1)
    time_basis_id: str = Field(min_length=1)
    provider_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    mesh_revision: str = Field(min_length=1)
    geometry_result: dict
    geometry_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    coordinate_system_id: str = Field(min_length=1)
    coordinate_origin: Literal["mouth"]
    positive_axial_direction: Literal["mouth_to_tip"]
    pressure_unit: Literal["Pa"]
    velocity_unit: Literal["m/s"]
    length_unit: Literal["m"]
    time_unit: Literal["s"]
    elapsed_time_s: tuple[float, ...] = Field(min_length=2, max_length=5000)
    face_positions_m: tuple[Nonnegative, ...] = Field(min_length=3, max_length=2001)
    cell_widths_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    cell_aperture_m: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=5000)
    face_pressure_Pa: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=5000)
    face_velocity_m_s: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=5000)
    time_interpolation: Literal["piecewise_linear"]
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    source_result_digest_reviewed: bool
    coordinate_and_unit_mapping_reviewed: bool
    face_order_and_velocity_sign_reviewed: bool
    mesh_to_geometry_mapping_reviewed: bool
    geometry_revision_and_time_alignment_reviewed: bool
    piecewise_linear_velocity_interpolation_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_receipt(self):
        if not any(row.source_id == self.provider_id and row.sha256 == self.provider_result_sha256
                   for row in self.evidence):
            raise ValueError("provider result digest must be linked to matching Evidence")
        if canonical_digest(self.geometry_result) != self.geometry_result_sha256:
            raise ValueError("geometry result digest mismatch")
        values = self.geometry_result.get("values", self.geometry_result)
        states = values.get("geometry_states") if isinstance(values, dict) else None
        if self.geometry_result.get("status", values.get("status") if isinstance(values, dict) else None) != "computed":
            raise ValueError("computed aperture history is required")
        if not isinstance(states, list) or len(states) != len(self.elapsed_time_s):
            raise ValueError("solver and geometry histories must have identical knot counts")
        widths = values.get("cell_widths_m")
        if widths != list(self.cell_widths_m) or len(self.face_positions_m) != len(self.cell_widths_m) + 1:
            raise ValueError("mesh cells and face coordinates must align with aperture geometry")
        if not math.isclose(math.fsum(self.cell_widths_m), self.face_positions_m[-1] - self.face_positions_m[0],
                            rel_tol=1e-10, abs_tol=1e-12):
            raise ValueError("face-coordinate span must equal total cell length")
        if not math.isclose(self.face_positions_m[0], 0.0, abs_tol=1e-12) or any(
            right <= left for left, right in zip(self.face_positions_m[:-1], self.face_positions_m[1:], strict=True)
        ):
            raise ValueError("face positions must increase from a zero mouth origin")
        if any(not math.isclose(right - left, width, rel_tol=1e-10, abs_tol=1e-12)
               for left, right, width in zip(
                   self.face_positions_m[:-1], self.face_positions_m[1:], self.cell_widths_m, strict=True
               )):
            raise ValueError("each mesh face interval must match its declared cell width in order")
        count = len(self.cell_widths_m)
        if len(self.cell_aperture_m) != len(self.elapsed_time_s) or any(len(row) != count for row in self.cell_aperture_m):
            raise ValueError("aperture history must align with solver time and cell dimensions")
        if any(len(row) != count + 1 for row in self.face_pressure_Pa + self.face_velocity_m_s):
            raise ValueError("pressure and velocity histories require one value per mesh face")
        if any(not math.isfinite(value) for row in self.face_pressure_Pa + self.face_velocity_m_s for value in row):
            raise ValueError("pressure and velocity values must be finite")
        if self.elapsed_time_s[0] != 0 or any(
            not math.isfinite(value) for value in self.elapsed_time_s
        ) or any(right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)):
            raise ValueError("solver time knots must be finite, zero-based, and strictly increasing")
        for index, state in enumerate(states):
            if (state.get("elapsed_time_s") != self.elapsed_time_s[index]
                    or state.get("cell_aperture_m") != list(self.cell_aperture_m[index])):
                raise ValueError("solver geometry samples must exactly match the pinned aperture state")
        gates = (
            self.source_result_digest_reviewed, self.coordinate_and_unit_mapping_reviewed,
            self.face_order_and_velocity_sign_reviewed, self.mesh_to_geometry_mapping_reviewed,
            self.geometry_revision_and_time_alignment_reviewed,
            self.piecewise_linear_velocity_interpolation_reviewed, self.computational_use_authorized,
        )
        if not all(gates):
            raise ValueError("all solver provenance, mapping, interpolation and use reviews are required")
        return self


class ExternalCreviceVelocityProvider:
    """Callable, no-extrapolation face-velocity history accepted by restricted transport."""

    def __init__(self, receipt: ExternalCreviceSolverHistory):
        self._times = np.asarray(receipt.elapsed_time_s, dtype=float)
        self._velocity = np.asarray(receipt.face_velocity_m_s, dtype=float)
        self.configuration_sha256 = canonical_digest({
            "provider_id": receipt.provider_id,
            "provider_revision": receipt.provider_revision,
            "provider_run_id": receipt.provider_run_id,
            "time_basis_id": receipt.time_basis_id,
            "provider_result_sha256": receipt.provider_result_sha256,
            "geometry_result_sha256": receipt.geometry_result_sha256,
            "mesh_revision": receipt.mesh_revision,
            "coordinate_system_id": receipt.coordinate_system_id,
            "elapsed_time_s": receipt.elapsed_time_s,
            "face_velocity_m_s": receipt.face_velocity_m_s,
            "interpolation": receipt.time_interpolation,
        })
        self.source_sha256 = receipt.provider_result_sha256
        self.provider_id = receipt.provider_id

    def __call__(self, time_s: float) -> np.ndarray:
        if not math.isfinite(time_s) or time_s < self._times[0] or time_s > self._times[-1]:
            raise ValueError("external velocity provider does not extrapolate beyond its receipt clock")
        return np.asarray([
            np.interp(time_s, self._times, self._velocity[:, face])
            for face in range(self._velocity.shape[1])
        ], dtype=float)


def bind_external_crevice_velocity(
    request: RestrictedTransportRequest,
    receipt: ExternalCreviceSolverHistory,
) -> tuple[RestrictedTransportRequest, ExternalCreviceVelocityProvider]:
    """Bind a reviewed CFD velocity history to a matching transport request.

    This adapter only checks mesh, spatial extent and clock coverage, then records
    provider lineage on a validated copy of the request.  Caller review gates in
    the request remain mandatory; the adapter does not approve flow continuity,
    transport physics, or reverse-flow boundary conditions.
    """
    if request.axial_advection_velocity_m_s is not None or request.axial_advection_provider_id is not None:
        raise ValueError("transport request already declares an axial-velocity source")
    widths = request.cell_widths_m or (request.length_m / request.cell_count,) * request.cell_count
    if request.cell_count != len(receipt.cell_widths_m):
        raise ValueError("transport cell count must match the CFD receipt mesh")
    if any(not math.isclose(float(a), float(b), rel_tol=1e-10, abs_tol=1e-12)
           for a, b in zip(widths, receipt.cell_widths_m, strict=True)):
        raise ValueError("transport cell widths must match the CFD receipt mesh in order")
    if not math.isclose(request.length_m, math.fsum(receipt.cell_widths_m), rel_tol=1e-10, abs_tol=1e-12):
        raise ValueError("transport length must match the CFD receipt axial extent")
    if request.output_times_s[0] < receipt.elapsed_time_s[0] or request.output_times_s[-1] > receipt.elapsed_time_s[-1]:
        raise ValueError("transport clock must lie within the CFD receipt clock; extrapolation is unavailable")
    provider = ExternalCreviceVelocityProvider(receipt)
    payload = request.model_dump(mode="python")
    payload.update({
        "axial_advection_provider_id": provider.provider_id,
        "axial_advection_configuration_sha256": provider.configuration_sha256,
        "axial_advection_source_result_sha256": provider.source_sha256,
    })
    bound_request = RestrictedTransportRequest.model_validate(payload)
    if not bound_request.time_varying_axial_advection_reviewed:
        raise ValueError("time-varying advection review must be explicitly recorded on the request")
    if not bound_request.axial_advection_and_flow_continuity_reviewed:
        raise ValueError("advection and flow-continuity review must be explicitly recorded on the request")
    return bound_request, provider


def external_crevice_solver_receipt(x: ExternalCreviceSolverHistory) -> Calculation:
    velocity = ExternalCreviceVelocityProvider(x)
    values = {
        "assessment_id": x.assessment_id,
        "status": "computed",
        "provider_id": x.provider_id,
        "provider_revision": x.provider_revision,
        "provider_run_id": x.provider_run_id,
        "provider_result_sha256": x.provider_result_sha256,
        "geometry_result_sha256": x.geometry_result_sha256,
        "mesh_revision": x.mesh_revision,
        "coordinate_system_id": x.coordinate_system_id,
        "elapsed_time_s": list(x.elapsed_time_s),
        "face_positions_m": list(x.face_positions_m),
        "cell_widths_m": list(x.cell_widths_m),
        "cell_aperture_m": [list(row) for row in x.cell_aperture_m],
        "face_pressure_Pa": [list(row) for row in x.face_pressure_Pa],
        "face_velocity_m_s": [list(row) for row in x.face_velocity_m_s],
        "velocity_provider_configuration_sha256": velocity.configuration_sha256,
        "interpolation": "piecewise_linear_no_extrapolation",
        "lineage_sha256": canonical_digest(x.model_dump(mode="json")),
        "transport_consumer_contract": "solve_restricted_transport(request, axial_advection_velocity=ExternalCreviceVelocityProvider(receipt))",
    }
    return Calculation(values=values, notes=(
        "Provider pressure and face velocity are retained in SI units and bound to exact geometry, mesh, clock and source digests.",
        "The velocity callback linearly interpolates only within the reviewed receipt clock; the consumer remains responsible for transport grid/species, boundaries, chemistry and mass-balance settings.",
        "This adapter does not execute an external solver or restricted-transport consumer and does not independently establish CFD accuracy.",
    ))


def _validate_context(x: ExternalCreviceSolverHistory, context: RunContext) -> None:
    if context.time_basis != x.time_basis_id:
        raise ValueError("RunContext time basis must match the provider receipt's declared clock identity")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.external_crevice_solver_receipt",
        ExternalCreviceSolverHistory,
        external_crevice_solver_receipt,
        {"elapsed_time_s": "s", "face_positions_m": "m", "cell_widths_m": "m",
         "cell_aperture_m": "m", "face_pressure_Pa": "Pa", "face_velocity_m_s": "m/s"},
        (
            "An external solver receipt must match the pinned aperture history, cell mesh, face ordering, SI units, axial sign and exact time knots.",
            "Only caller-reviewed piecewise-linear interpolation inside the receipt clock is exposed; no extrapolation or solver validation is performed.",
        ),
        ("external_crevice_solver_pressure_velocity_receipt",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
