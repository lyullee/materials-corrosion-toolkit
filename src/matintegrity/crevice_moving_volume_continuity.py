"""Conservative interval continuity for caller-evidenced changing slit volume."""
from __future__ import annotations

import math

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_moving_volume_liquid_continuity"
SOURCE_ID = "caller_evidenced_slit_volume_and_boundary_flow_continuity"


class CreviceMovingVolumeContinuityRequest(Contract):
    """Reconstruct interval-mean face flow from cell-volume change and boundaries.

    Positive flow points from the left reservoir toward the right reservoir.
    This is a kinematic volume-continuity operator; pressure, momentum, species
    transport and deposition kinetics are not solved here.
    """

    schema_version: str = "matintegrity.crevice_moving_volume_continuity.v1"
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    cell_ids: tuple[str, ...] = Field(min_length=1, max_length=300)
    cell_lengths_m: tuple[Positive, ...] = Field(min_length=1, max_length=300)
    transverse_width_m: Positive
    aperture_m_by_knot_and_cell: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=500)
    left_boundary_flow_m3_s_by_knot: tuple[float, ...] = Field(min_length=2, max_length=500)
    right_boundary_flow_m3_s_by_knot: tuple[float, ...] = Field(min_length=2, max_length=500)
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_flow_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=2, max_length=256)
    geometry_boundary_and_sign_convention_reviewed: bool
    incompressible_liquid_and_fixed_mesh_reviewed: bool
    computational_use_authorized: bool
    absolute_flow_closure_tolerance_m3_s: Positive = 1e-15
    relative_flow_closure_tolerance: Positive = Field(default=1e-9, le=1e-3)

    @model_validator(mode="after")
    def validate_histories(self):
        if self.schema_version != "matintegrity.crevice_moving_volume_continuity.v1":
            raise ValueError("unsupported moving-volume continuity schema")
        if any(not math.isfinite(t) for t in self.time_s) or any(
            b <= a for a, b in zip(self.time_s, self.time_s[1:])
        ):
            raise ValueError("continuity clock must be finite and strictly increasing")
        nc, nt = len(self.cell_ids), len(self.time_s)
        if len(set(self.cell_ids)) != nc or len(self.cell_lengths_m) != nc:
            raise ValueError("cell IDs must be unique and match the ordered cell lengths")
        if len(self.aperture_m_by_knot_and_cell) != nt or any(
            len(row) != nc for row in self.aperture_m_by_knot_and_cell
        ):
            raise ValueError("aperture history must provide every ordered cell at every exact knot")
        if len(self.left_boundary_flow_m3_s_by_knot) != nt or len(self.right_boundary_flow_m3_s_by_knot) != nt:
            raise ValueError("both boundary-flow histories must match all exact knots")
        if any(not math.isfinite(q) for q in (*self.left_boundary_flow_m3_s_by_knot,
                                               *self.right_boundary_flow_m3_s_by_knot)):
            raise ValueError("boundary flows must be finite")
        geometry_payload = {
            "assessment_id": self.assessment_id,
            "physical_scope_id": self.physical_scope_id,
            "time_s": list(self.time_s),
            "cell_ids": list(self.cell_ids),
            "cell_lengths_m": [float(x) for x in self.cell_lengths_m],
            "transverse_width_m": float(self.transverse_width_m),
            "aperture_m_by_knot_and_cell": [[float(x) for x in row]
                                              for row in self.aperture_m_by_knot_and_cell],
        }
        boundary_payload = {
            "physical_scope_id": self.physical_scope_id,
            "time_s": list(self.time_s),
            "left_boundary_flow_m3_s_by_knot": list(self.left_boundary_flow_m3_s_by_knot),
            "right_boundary_flow_m3_s_by_knot": list(self.right_boundary_flow_m3_s_by_knot),
        }
        if canonical_digest(geometry_payload) != self.geometry_sha256:
            raise ValueError("geometry digest must bind the exact cell dimensions and aperture history")
        if canonical_digest(boundary_payload) != self.boundary_flow_sha256:
            raise ValueError("boundary-flow digest must bind both ordered boundary histories")
        if (not any(row.sha256 == self.geometry_sha256 and row.license_id for row in self.evidence)
                or not any(row.sha256 == self.boundary_flow_sha256 and row.license_id
                           for row in self.evidence)):
            raise ValueError("licensed Evidence must pin geometry and boundary-flow digests")
        if not all((self.geometry_boundary_and_sign_convention_reviewed,
                    self.incompressible_liquid_and_fixed_mesh_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("geometry, boundary/sign, liquid assumptions and use must be reviewed")
        return self


def evaluate_crevice_moving_volume_continuity(
    request: CreviceMovingVolumeContinuityRequest,
) -> Calculation:
    """Return interval-mean internal flows and a cellwise volume ledger."""
    digest = canonical_digest(request.model_dump(mode="json"))
    times = np.asarray(request.time_s, dtype=float)
    aperture = np.asarray(request.aperture_m_by_knot_and_cell, dtype=float)
    length = np.asarray(request.cell_lengths_m, dtype=float)
    cell_volume = aperture * (length * float(request.transverse_width_m))[None, :]
    dt = np.diff(times)
    volume_rate = np.diff(cell_volume, axis=0) / dt[:, None]
    q_left = 0.5 * (np.asarray(request.left_boundary_flow_m3_s_by_knot[:-1])
                    + np.asarray(request.left_boundary_flow_m3_s_by_knot[1:]))
    q_right_declared = 0.5 * (np.asarray(request.right_boundary_flow_m3_s_by_knot[:-1])
                              + np.asarray(request.right_boundary_flow_m3_s_by_knot[1:]))
    face_flow = np.zeros((len(dt), len(request.cell_ids) + 1), dtype=float)
    face_flow[:, 0] = q_left
    # dV_i/dt = Q_i - Q_(i+1), with positive face flow directed left-to-right.
    for cell in range(len(request.cell_ids)):
        face_flow[:, cell + 1] = face_flow[:, cell] - volume_rate[:, cell]
    residual = face_flow[:, :-1] - face_flow[:, 1:] - volume_rate
    boundary_residual = face_flow[:, -1] - q_right_declared
    allowed = (float(request.absolute_flow_closure_tolerance_m3_s)
               + float(request.relative_flow_closure_tolerance)
               * np.maximum(np.maximum(np.abs(face_flow[:, -1]), np.abs(q_right_declared)),
                            np.max(np.abs(face_flow), axis=1)))
    committed = bool(np.isfinite(face_flow).all() and np.all(np.abs(residual) <= allowed[:, None])
                     and np.all(np.abs(boundary_residual) <= allowed))
    values = {
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "input_sha256": digest,
        "geometry_sha256": request.geometry_sha256,
        "boundary_flow_sha256": request.boundary_flow_sha256,
        "interval_start_time_s": times[:-1].tolist(),
        "interval_end_time_s": times[1:].tolist(),
        "cell_volume_m3_by_knot_and_cell": cell_volume.tolist(),
        "cell_volume_rate_m3_s_by_interval_and_cell": volume_rate.tolist(),
        "face_flow_m3_s_by_interval_and_face": face_flow.tolist(),
        "cell_continuity_residual_m3_s_by_interval_and_cell": residual.tolist(),
        "right_boundary_flow_residual_m3_s_by_interval": boundary_residual.tolist(),
        "maximum_absolute_cell_residual_m3_s": float(np.max(np.abs(residual))),
        "maximum_absolute_boundary_residual_m3_s": float(np.max(np.abs(boundary_residual))),
        "committed": committed,
        "qualification_claimed": False,
        "limitations": [
            "Interval-mean continuity only; no transient pressure-momentum equation or constitutive flow law is solved.",
            "The mesh is fixed and liquid is treated as incompressible; topology change and liquid compressibility are excluded.",
            "Boundary flows and aperture histories are caller inputs; deposit kinetics and species inventories are not inferred.",
        ],
    }
    return Calculation(status="computed" if committed else "needs_data", values=values)


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceMovingVolumeContinuityRequest,
        evaluator=evaluate_crevice_moving_volume_continuity,
        units={
            "time_s": "s",
            "cell_volume_m3_by_knot_and_cell[][]": "m^3",
            "cell_volume_rate_m3_s_by_interval_and_cell[][]": "m^3/s",
            "face_flow_m3_s_by_interval_and_face[][]": "m^3/s",
            "cell_continuity_residual_m3_s_by_interval_and_cell[][]": "m^3/s",
        },
        assumptions=(
            "Linear aperture change between exact knots implies constant interval-mean volume rate.",
            "Positive face flow is left-to-right and each cell obeys dV/dt = Q_left - Q_right.",
            "This operator supplies a conservative kinematic schedule only; it does not solve pressure-driven momentum or reactive transport.",
        ),
        source_ids=(SOURCE_ID,),
        version="0.1.0",
        qualification="user_model",
    ),)
