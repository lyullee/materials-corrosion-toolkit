"""Finite-sample rotation descriptor for the maximum principal stress axis."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec


class PrincipalStressAxisRotation(Contract):
    """Summarize sign-invariant changes in the largest-principal-stress axis."""

    analysis_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    sample_ids: list[str] = Field(min_length=3, max_length=10000)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=10000)
    minimum_relative_principal_gap: float = Field(gt=0, le=1)
    tensor_basis_and_component_order_reviewed: bool
    closed_cycle_and_sample_order_reviewed: bool

    @model_validator(mode="after")
    def validate_history(self):
        if len(self.sample_ids) != len(self.stress_tensor_components_Pa):
            raise ValueError("sample IDs and tensor samples must align")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample IDs must be unique in caller path order")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor must use six symmetric components")
        if self.stress_tensor_components_Pa[0] != self.stress_tensor_components_Pa[-1]:
            raise ValueError("the finite history must include an exactly closed stress endpoint")
        if not all(math.isfinite(value) for row in self.stress_tensor_components_Pa for value in row):
            raise ValueError("stress tensor components must be finite")
        if self.evidence.source_id != self.source_id or self.evidence.sha256 != self.source_sha256:
            raise ValueError("Evidence must match the declared source ID and digest")
        return self


def _symmetric_eigensystem(tensor: list[float]) -> tuple[list[float], list[list[float]]]:
    """Small deterministic Jacobi solver; vectors are stored as matrix columns."""
    magnitude = max(abs(value) for value in tensor)
    if magnitude == 0.0:
        return [0.0, 0.0, 0.0], [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    # Eigenvectors and relative eigenvalue gaps are scale invariant. Normalizing
    # first avoids overflow in Jacobi rotations for large, finite stress inputs.
    xx, yy, zz, xy, yz, zx = (value / magnitude for value in tensor)
    a = [[xx, xy, zx], [xy, yy, yz], [zx, yz, zz]]
    v = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    for _ in range(32):
        p, q = max(((0, 1), (0, 2), (1, 2)), key=lambda pair: abs(a[pair[0]][pair[1]]))
        apq = a[p][q]
        scale = max(abs(a[0][0]), abs(a[1][1]), abs(a[2][2]), 1.0)
        if abs(apq) <= 1e-15 * scale:
            break
        tau = (a[q][q] - a[p][p]) / (2.0 * apq)
        sign = 1.0 if tau >= 0.0 else -1.0
        t = sign / (abs(tau) + math.sqrt(1.0 + tau * tau))
        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c
        app, aqq = a[p][p], a[q][q]
        a[p][p] = app - t * apq
        a[q][q] = aqq + t * apq
        a[p][q] = a[q][p] = 0.0
        for k in range(3):
            if k not in (p, q):
                akp, akq = a[k][p], a[k][q]
                a[k][p] = a[p][k] = c * akp - s * akq
                a[k][q] = a[q][k] = s * akp + c * akq
            vkp, vkq = v[k][p], v[k][q]
            v[k][p] = c * vkp - s * vkq
            v[k][q] = s * vkp + c * vkq
    pairs = sorted(((a[i][i], [v[row][i] for row in range(3)]) for i in range(3)), reverse=True, key=lambda row: row[0])
    return [row[0] for row in pairs], [row[1] for row in pairs]


def evaluate_principal_stress_axis_rotation(request: PrincipalStressAxisRotation) -> Calculation:
    """Return sampled projective-axis angular travel; not a fatigue law."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "source_id": request.source_id,
        "source_sha256": request.source_sha256,
        "input_sha256": digest,
        "sample_count": len(request.sample_ids),
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "eigenvector_convention": "largest algebraic principal stress; axis sign treated as equivalent",
        "fatigue_damage_or_life": None,
    }
    if not request.tensor_basis_and_component_order_reviewed or not request.closed_cycle_and_sample_order_reviewed:
        return Calculation(status="needs_data", values=base | {
            "reason": "tensor_basis_closed_cycle_and_sample_order_reviews_required",
            "total_axis_rotation_rad": None,
            "maximum_adjacent_rotation_rad": None,
        })
    axes = []
    gaps = []
    for index, tensor in enumerate(request.stress_tensor_components_Pa):
        eigenvalues, eigenvectors = _symmetric_eigensystem(tensor)
        gap = eigenvalues[0] - eigenvalues[1]
        scale = max(abs(value) for value in eigenvalues)
        relative_gap = gap / scale if scale > 0.0 else 0.0
        if not math.isfinite(relative_gap) or relative_gap <= request.minimum_relative_principal_gap:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "maximum_principal_axis_not_resolved_by_declared_gap_threshold",
                "sample_id": request.sample_ids[index],
                "relative_principal_gap": relative_gap if math.isfinite(relative_gap) else None,
                "minimum_relative_principal_gap": request.minimum_relative_principal_gap,
                "total_axis_rotation_rad": None,
                "maximum_adjacent_rotation_rad": None,
            })
        axes.append(eigenvectors[0])
        gaps.append(relative_gap)
    increments = []
    for left, right in zip(axes[:-1], axes[1:], strict=True):
        cosine = abs(math.fsum(a * b for a, b in zip(left, right, strict=True)))
        increments.append(math.acos(max(-1.0, min(1.0, cosine))))
    try:
        total = math.fsum(increments)
    except (OverflowError, ValueError):
        total = math.inf
    if not math.isfinite(total):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "nonfinite_axis_rotation_accumulation",
            "total_axis_rotation_rad": None,
            "maximum_adjacent_rotation_rad": None,
        })
    maximum_index = max(range(len(increments)), key=increments.__getitem__)
    return Calculation(values=base | {
        "status": "computed",
        "total_axis_rotation_rad": total,
        "total_axis_rotation_deg": math.degrees(total),
        "maximum_adjacent_rotation_rad": increments[maximum_index],
        "maximum_rotation_sample_pair": [request.sample_ids[maximum_index], request.sample_ids[maximum_index + 1]],
        "minimum_observed_relative_top_eigenvalue_gap": min(gaps),
        "minimum_relative_principal_gap": request.minimum_relative_principal_gap,
        "angular_distance": "acos(abs(dot(u_i, u_(i+1)))); principal axes are unoriented lines",
        "limitations": [
            "Only adjacent supplied samples are compared; no path between samples is reconstructed.",
            "The maximum principal axis is undefined or unstable near a repeated top eigenvalue; such records are rejected by the caller threshold.",
            "Accumulated sampled axis rotation is a kinematic descriptor, not a nonproportional damage factor, fatigue life or qualification result.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.multiaxial_principal_stress_axis_rotation",
        PrincipalStressAxisRotation,
        evaluate_principal_stress_axis_rotation,
        {
            "total_axis_rotation_rad": "rad",
            "total_axis_rotation_deg": "degree",
            "maximum_adjacent_rotation_rad": "rad",
            "minimum_observed_relative_top_eigenvalue_gap": "1",
        },
        (
            "The six supplied components form symmetric stress tensors in [xx, yy, zz, xy, yz, zx] order.",
            "The largest algebraic principal axis is tracked as an unoriented line and requires a caller-selected eigenvalue-gap threshold.",
            "Only ordered finite samples are summarized; no interpolation or fatigue-damage/life model is implied.",
        ),
        ("caller_finite_sample_principal_stress_axis_rotation_descriptor_nonproportional_loading",),
        qualification="user_model",
    )]
