"""Finite-sampled-plane McDiarmid high-cycle fatigue strength screen."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fatigue.multiaxial_mcdiarmid_finite_plane_limit_screen"


class McDiarmidTensorState(Contract):
    time_s: float
    sigma_xx_Pa: float
    sigma_yy_Pa: float
    sigma_zz_Pa: float
    tau_xy_Pa: float
    tau_yz_Pa: float
    tau_zx_Pa: float


class McDiarmidCandidatePlane(Contract):
    plane_id: str = Field(min_length=1)
    normal_x: float
    normal_y: float
    normal_z: float


class McDiarmidCriticalPlaneLimitScreen(Contract):
    """Screen one repeated service tensor cycle against caller McDiarmid inputs."""

    schema_version: Literal["matintegrity.multiaxial_mcdiarmid_finite_plane_limit_screen.v1"] = (
        "matintegrity.multiaxial_mcdiarmid_finite_plane_limit_screen.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    crack_case: Literal["A", "B"]
    stress_history: tuple[McDiarmidTensorState, ...] = Field(min_length=2, max_length=100000)
    candidate_planes: tuple[McDiarmidCandidatePlane, ...] = Field(min_length=1, max_length=100000)
    reversed_torsion_fatigue_strength_Pa: Positive
    ultimate_tensile_strength_Pa: Positive
    material_provider_id: str = Field(min_length=1)
    material_provider_revision: str = Field(min_length=1)
    material_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    usage_license_id: str = Field(min_length=1)
    material_evidence: tuple[Evidence, ...] = Field(min_length=1)
    history_provider_id: str = Field(min_length=1)
    history_provider_revision: str = Field(min_length=1)
    history_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_usage_license_id: str = Field(min_length=1)
    history_evidence: tuple[Evidence, ...] = Field(min_length=1)
    repeated_cycle_and_tensor_convention_reviewed: bool
    material_condition_and_crack_case_reviewed: bool
    plane_set_and_surface_orientation_reviewed: bool
    calibration_records_and_computational_use_reviewed: bool

    @model_validator(mode="after")
    def validate_request(self):
        if any(not math.isfinite(value) for row in self.stress_history for value in (
            row.time_s, row.sigma_xx_Pa, row.sigma_yy_Pa, row.sigma_zz_Pa,
            row.tau_xy_Pa, row.tau_yz_Pa, row.tau_zx_Pa,
        )):
            raise ValueError("stress history values must be finite")
        times = [row.time_s for row in self.stress_history]
        if any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError("stress-history times must strictly increase")
        if len({row.plane_id for row in self.candidate_planes}) != len(self.candidate_planes):
            raise ValueError("candidate plane IDs must be unique")
        if any(
            not all(math.isfinite(value) for value in (row.normal_x, row.normal_y, row.normal_z))
            or not math.isfinite(math.hypot(row.normal_x, row.normal_y, row.normal_z))
            or math.hypot(row.normal_x, row.normal_y, row.normal_z) <= 1.0e-14
            for row in self.candidate_planes
        ):
            raise ValueError("candidate plane normals must be finite nonzero vectors")
        material_record = {
            "physical_scope_id": self.physical_scope_id,
            "material_condition_id": self.material_condition_id,
            "provider_id": self.material_provider_id,
            "provider_revision": self.material_provider_revision,
            "crack_case": self.crack_case,
            "reversed_torsion_fatigue_strength_Pa": self.reversed_torsion_fatigue_strength_Pa,
            "ultimate_tensile_strength_Pa": self.ultimate_tensile_strength_Pa,
        }
        if canonical_digest(material_record) != self.material_record_sha256:
            raise ValueError("material record digest does not bind the declared strengths and case")
        if not any(row.source_id == self.material_provider_id and row.sha256 == self.material_record_sha256
                   and row.license_id == self.usage_license_id for row in self.material_evidence):
            raise ValueError("material Evidence must pin the strengths, material condition and usage license")
        history_record = {
            "physical_scope_id": self.physical_scope_id,
            "provider_id": self.history_provider_id,
            "provider_revision": self.history_provider_revision,
            "stress_history": [row.model_dump(mode="json") for row in self.stress_history],
            "candidate_planes": [row.model_dump(mode="json") for row in self.candidate_planes],
        }
        if canonical_digest(history_record) != self.history_record_sha256:
            raise ValueError("history record digest does not bind stress samples and plane set")
        if not any(row.source_id == self.history_provider_id and row.sha256 == self.history_record_sha256
                   and row.license_id == self.history_usage_license_id for row in self.history_evidence):
            raise ValueError("history Evidence must pin stress samples, plane set and usage license")
        return self


def _tensor(row: McDiarmidTensorState) -> tuple[tuple[float, float, float], ...]:
    return (
        (row.sigma_xx_Pa, row.tau_xy_Pa, row.tau_zx_Pa),
        (row.tau_xy_Pa, row.sigma_yy_Pa, row.tau_yz_Pa),
        (row.tau_zx_Pa, row.tau_yz_Pa, row.sigma_zz_Pa),
    )


def evaluate_mcdiarmid_finite_plane_limit_screen(request: McDiarmidCriticalPlaneLimitScreen) -> Calculation:
    """Evaluate a finite plane set with shear-traction diameter and max normal stress."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "material_condition_id": request.material_condition_id,
        "input_sha256": digest,
        "model_id": MODEL_ID,
    }
    reviews = {
        "repeated_cycle_and_tensor_convention_reviewed": request.repeated_cycle_and_tensor_convention_reviewed,
        "material_condition_and_crack_case_reviewed": request.material_condition_and_crack_case_reviewed,
        "plane_set_and_surface_orientation_reviewed": request.plane_set_and_surface_orientation_reviewed,
        "calibration_records_and_computational_use_reviewed": request.calibration_records_and_computational_use_reviewed,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    states = [_tensor(row) for row in request.stress_history]
    plane_results = []
    for plane in request.candidate_planes:
        norm = math.hypot(plane.normal_x, plane.normal_y, plane.normal_z)
        n = (plane.normal_x / norm, plane.normal_y / norm, plane.normal_z / norm)
        shear_vectors = []
        normal_stresses = []
        try:
            for tensor in states:
                traction = tuple(math.fsum(tensor[i][j] * n[j] for j in range(3)) for i in range(3))
                normal = math.fsum(traction[i] * n[i] for i in range(3))
                shear_vectors.append(tuple(traction[i] - normal * n[i] for i in range(3)))
                normal_stresses.append(normal)
            max_range = 0.0
            for i, first in enumerate(shear_vectors):
                for second in shear_vectors[i + 1:]:
                    distance = math.hypot(*(second[k] - first[k] for k in range(3)))
                    max_range = max(max_range, distance)
            shear_amplitude = 0.5 * max_range
            maximum_normal = max(normal_stresses)
            torsion_strength = request.reversed_torsion_fatigue_strength_Pa
            criterion_index = shear_amplitude / torsion_strength + maximum_normal / (
                2.0 * request.ultimate_tensile_strength_Pa
            )
        except (ArithmeticError, OverflowError, ValueError):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "stress_tensor_projection_outside_finite_numeric_support",
                "completed_plane_count": len(plane_results),
                "failed_plane_id": plane.plane_id,
            })
        if not math.isfinite(criterion_index):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "criterion_value_outside_finite_numeric_support",
                "completed_plane_count": len(plane_results),
            })
        plane_results.append({
            "plane_id": plane.plane_id,
            "unit_normal": list(n),
            "maximum_shear_range_Pa": max_range,
            "shear_amplitude_Pa": shear_amplitude,
            "maximum_normal_stress_Pa": maximum_normal,
            "criterion_index": criterion_index,
            "screen_margin": 1.0 - criterion_index,
        })
    governing = max(plane_results, key=lambda row: row["criterion_index"])
    return Calculation(values=base | {
        "crack_case": request.crack_case,
        "plane_count": len(plane_results),
        "stress_sample_count": len(states),
        "plane_results": plane_results,
        "governing_plane_id": governing["plane_id"],
        "maximum_criterion_index": governing["criterion_index"],
        "screen_margin": governing["screen_margin"],
        "criterion_expression": "tau_amplitude/torsion_strength + sigma_normal_max/(2*ultimate_tensile_strength)",
        "interpretation": "finite_sampled_plane_high_cycle_strength_index_only",
    }, notes=(
        "The plane set and tensor-history sample resolution are caller supplied; the maximum is only over those samples and planes.",
        "Shear amplitude is implemented as one half the largest Euclidean distance between sampled in-plane shear-traction vectors.",
        "The criterion index is a high-cycle strength screen, not cycles to failure, cumulative damage, a probability or a code acceptance result.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        McDiarmidCriticalPlaneLimitScreen,
        evaluate_mcdiarmid_finite_plane_limit_screen,
        {
            "plane_results[].maximum_shear_range_Pa": "Pa",
            "plane_results[].shear_amplitude_Pa": "Pa",
            "plane_results[].maximum_normal_stress_Pa": "Pa",
            "plane_results[].criterion_index": "1",
            "plane_results[].screen_margin": "1",
            "maximum_criterion_index": "1",
            "screen_margin": "1",
        },
        (
            "Every plane is evaluated from the caller finite stress sample set, with its sampled shear-traction path and maximum normal stress.",
            "The caller selects McDiarmid crack case A or B and supplies matching reversed torsion fatigue strength and tensile strength.",
            "No plane-grid convergence, interpolation between stress samples, fatigue life or qualification is inferred.",
        ),
        (
            "mcdiarmid_shear_stress_critical_plane_1994",
            "caller_multiaxial_stress_tensor_history",
            "caller_mcdiarmid_case_torsion_and_tensile_strengths",
            "finite_sampled_shear_traction_diameter_and_normal_stress_screen",
        ),
        qualification="engineering_screening",
    )]
