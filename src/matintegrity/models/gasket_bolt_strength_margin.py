"""Compare computed nominal bolt stress histories with caller-owned strength data."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictBool, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from ..registry import ModelSpec

MODEL_ID = "fabrication.gasket_bolt_nominal_strength_screen"
SOURCE_ID = "caller_bolt_proof_strength_temperature_curve"
METHOD_SOURCE_ID = "piecewise_linear_bolt_nominal_strength_margin"
UPSTREAM_MODEL_ID = "fabrication.gasket_multi_bolt_sector_equilibrium"


class BoltProofStrengthPoint(Contract):
    temperature_K: Positive
    nominal_proof_strength_Pa: Positive


class BoltMaterialStrengthBasis(Contract):
    """One bolt's caller-owned nominal tensile strength versus temperature."""

    bolt_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    curve_id: str = Field(min_length=1)
    source_id: str = SOURCE_ID
    curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    curve_points: tuple[BoltProofStrengthPoint, ...] = Field(min_length=2, max_length=1000)
    evidence: Evidence
    strength_definition_reviewed: StrictBool
    application_to_declared_bolt_reviewed: StrictBool

    @model_validator(mode="after")
    def validate_curve(self):
        if self.source_id != SOURCE_ID or self.evidence.source_id != self.source_id:
            raise ValueError("bolt strength Evidence must identify the caller-supplied proof-strength curve")
        if self.evidence.sha256 != self.curve_sha256:
            raise ValueError("Evidence digest must match the declared strength-curve digest")
        actual_digest = canonical_digest([row.model_dump(mode="json") for row in self.curve_points])
        if actual_digest != self.curve_sha256:
            raise ValueError("curve_sha256 must match the ordered finite curve points")
        temperatures = [row.temperature_K for row in self.curve_points]
        strengths = [row.nominal_proof_strength_Pa for row in self.curve_points]
        if not all(math.isfinite(value) and value > 0.0 for value in (*temperatures, *strengths)):
            raise ValueError("strength curve points must be finite and positive")
        if any(right <= left for left, right in zip(temperatures, temperatures[1:])):
            raise ValueError("curve temperatures must strictly increase")
        return self


class GasketBoltNominalStrengthScreen(Contract):
    """Evidence-bound exact-knot bolt stress to caller strength comparison."""

    schema_version: Literal["matintegrity.gasket_bolt_nominal_strength_screen.v1"] = (
        "matintegrity.gasket_bolt_nominal_strength_screen.v1"
    )
    assessment_id: str = Field(min_length=1)
    joint_assessment: AssessmentResult
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    temperature_history_K: tuple[Positive, ...] = Field(min_length=1, max_length=100_000)
    bolt_strength_bases: tuple[BoltMaterialStrengthBasis, ...] = Field(min_length=1, max_length=1024)
    temperature_interpolation_reviewed: StrictBool
    basis_identity_and_use_reviewed: StrictBool

    @model_validator(mode="after")
    def validate_alignment(self):
        if self.joint_assessment.model_id != UPSTREAM_MODEL_ID:
            raise ValueError("input result must come from the registered multi-bolt/sector equilibrium model")
        if self.joint_assessment.status != "computed":
            raise ValueError("only a computed joint equilibrium may supply bolt nominal stresses")
        upstream_context = self.joint_assessment.context
        if (upstream_context.asset_id, upstream_context.location_id, upstream_context.time_basis) != (
            self.asset_id, self.location_id, self.time_basis
        ):
            raise ValueError("downstream asset, location and time basis must match the upstream result context")
        if self.joint_assessment.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("physical scope must match the upstream joint input")
        steps = self.joint_assessment.values.get("steps")
        if not isinstance(steps, list) or len(steps) != len(self.temperature_history_K):
            raise ValueError("one caller temperature is required at each upstream computed joint step")
        digest_payload = {
            "model_id": self.joint_assessment.model_id,
            "model_version": self.joint_assessment.model_version,
            "inputs": self.joint_assessment.inputs,
            "context": self.joint_assessment.context.model_dump(mode="json"),
        }
        if canonical_digest(digest_payload) != self.joint_assessment.input_digest:
            raise ValueError("upstream joint input digest does not match its declared inputs and context")
        if len({item.bolt_id for item in self.bolt_strength_bases}) != len(self.bolt_strength_bases):
            raise ValueError("bolt strength bases must be unique by bolt ID")
        source_bolts = {
            row.get("bolt_id")
            for step in steps if isinstance(step, dict)
            for row in step.get("bolts", []) if isinstance(row, dict)
        }
        if source_bolts != {item.bolt_id for item in self.bolt_strength_bases}:
            raise ValueError("strength bases must cover exactly the upstream joint bolt population")
        input_bolts = self.joint_assessment.inputs.get("bolts", [])
        areas = {
            row.get("bolt_id"): row.get("tensile_stress_area_m2")
            for row in input_bolts if isinstance(row, dict)
        }
        if set(areas) != source_bolts or any(
            not isinstance(area, (int, float)) or isinstance(area, bool)
            or not math.isfinite(area) or area <= 0.0 for area in areas.values()
        ):
            raise ValueError("upstream inputs must identify each bolt's finite positive tensile stress area")
        if any(not math.isfinite(value) or value <= 0.0 for value in self.temperature_history_K):
            raise ValueError("temperatures must be finite and positive")
        if any(
            {row.get("bolt_id") for row in step.get("bolts", []) if isinstance(row, dict)} != source_bolts
            for step in steps if isinstance(step, dict)
        ):
            raise ValueError("every upstream joint knot must contain the complete bolt population")
        input_steps = self.joint_assessment.inputs.get("load_steps", [])
        if not isinstance(input_steps, list) or len(input_steps) != len(steps):
            raise ValueError("upstream joint result steps do not align with input load steps")
        for result_step, input_step in zip(steps, input_steps, strict=True):
            if result_step.get("step_id") != input_step.get("step_id") or result_step.get("time_s") != input_step.get("time_s"):
                raise ValueError("upstream result step identities must match exact input knots")
            force_by_id = {row["bolt_id"]: row.get("tensile_force_N") for row in result_step["bolts"]}
            for bolt_id, force in force_by_id.items():
                stress = next(row["nominal_tensile_stress_Pa"] for row in result_step["bolts"] if row["bolt_id"] == bolt_id)
                if not isinstance(force, (int, float)) or not isinstance(stress, (int, float)):
                    raise ValueError("upstream bolt force and nominal stress must be numeric")
                expected = force / areas[bolt_id]
                if not math.isfinite(expected) or not math.isclose(stress, expected, rel_tol=1e-10, abs_tol=1e-6):
                    raise ValueError("upstream nominal bolt stress does not match force divided by input tensile area")
        return self


def _validate_run_context(request: GasketBoltNominalStrengthScreen, context: RunContext) -> None:
    if (request.asset_id, request.location_id, request.time_basis) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("strength-screen RunContext must match the declared upstream asset/location/time basis")


def _interpolate_strength(basis: BoltMaterialStrengthBasis, temperature_K: float) -> float | None:
    points = basis.curve_points
    if temperature_K < points[0].temperature_K or temperature_K > points[-1].temperature_K:
        return None
    if temperature_K == points[0].temperature_K:
        return points[0].nominal_proof_strength_Pa
    if temperature_K == points[-1].temperature_K:
        return points[-1].nominal_proof_strength_Pa
    for left, right in zip(points, points[1:]):
        if left.temperature_K <= temperature_K <= right.temperature_K:
            fraction = (temperature_K - left.temperature_K) / (right.temperature_K - left.temperature_K)
            value = left.nominal_proof_strength_Pa + fraction * (
                right.nominal_proof_strength_Pa - left.nominal_proof_strength_Pa
            )
            return value if math.isfinite(value) and value > 0 else None
    return None


def evaluate_gasket_bolt_nominal_strength_screen(
    request: GasketBoltNominalStrengthScreen,
) -> Calculation:
    upstream = request.joint_assessment
    upstream_digest = canonical_digest(upstream.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis": request.time_basis,
        "physical_scope_id": request.physical_scope_id,
        "upstream_model_id": upstream.model_id,
        "upstream_result_sha256": upstream_digest,
        "upstream_input_sha256": upstream.input_digest,
        "upstream_joint_id": upstream.values.get("joint_id"),
        "temperature_history_K": list(request.temperature_history_K),
        "interpretation": "nominal axial bolt-stress to caller-supplied strength comparison only",
    }
    missing_reviews = sum(
        not (item.strength_definition_reviewed and item.application_to_declared_bolt_reviewed)
        for item in request.bolt_strength_bases
    )
    if not request.temperature_interpolation_reviewed or not request.basis_identity_and_use_reviewed or missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "missing_curve_review_count": missing_reviews,
            "reason": "temperature interpolation, bolt/material mapping, strength definition or use review is incomplete",
        })

    steps = upstream.values["steps"]
    basis_by_id = {item.bolt_id: item for item in request.bolt_strength_bases}
    history = []
    maximum_utilization = -math.inf
    minimum_margin = math.inf
    for step_index, (step, temperature) in enumerate(zip(steps, request.temperature_history_K, strict=True)):
        step_output = []
        for bolt in step["bolts"]:
            bolt_id = bolt["bolt_id"]
            strength = _interpolate_strength(basis_by_id[bolt_id], temperature)
            stress = bolt.get("nominal_tensile_stress_Pa")
            if strength is None:
                return Calculation(status="out_of_scope", values=base | {
                    "computed_prefix": history,
                    "failed_step_index": step_index,
                    "failed_bolt_id": bolt_id,
                    "reason": "caller proof-strength curve does not support this exact joint temperature",
                })
            if not isinstance(stress, (int, float)) or isinstance(stress, bool) or not math.isfinite(stress) or stress < 0:
                return Calculation(status="out_of_scope", values=base | {
                    "computed_prefix": history,
                    "failed_step_index": step_index,
                    "failed_bolt_id": bolt_id,
                    "reason": "upstream nominal bolt stress is absent or nonfinite",
                })
            margin = strength - float(stress)
            utilization = float(stress) / strength
            if not math.isfinite(margin) or not math.isfinite(utilization):
                return Calculation(status="out_of_scope", values=base | {
                    "computed_prefix": history,
                    "failed_step_index": step_index,
                    "failed_bolt_id": bolt_id,
                    "reason": "nominal strength comparison exceeded finite numeric support",
                })
            maximum_utilization = max(maximum_utilization, utilization)
            minimum_margin = min(minimum_margin, margin)
            step_output.append({
                "bolt_id": bolt_id,
                "material_condition_id": basis_by_id[bolt_id].material_condition_id,
                "nominal_tensile_stress_Pa": float(stress),
                "caller_nominal_proof_strength_Pa": strength,
                "nominal_strength_margin_Pa": margin,
                "nominal_strength_utilization": utilization,
                "exceeds_caller_strength_value": margin < 0.0,
                "strength_curve_id": basis_by_id[bolt_id].curve_id,
                "strength_curve_sha256": basis_by_id[bolt_id].curve_sha256,
            })
        history.append({
            "step_id": step["step_id"],
            "time_s": step["time_s"],
            "temperature_K": temperature,
            "bolt_checks": step_output,
        })
    return Calculation(status="computed", values=base | {
        "step_count": len(history),
        "maximum_nominal_strength_utilization": maximum_utilization,
        "minimum_nominal_strength_margin_Pa": minimum_margin,
        "strength_comparison_history": history,
        "limitations": [
            "The upstream stress is nominal axial bolt force divided by caller tensile area; thread-root, bending, torsional, bearing and local FE stresses are not supplied.",
            "Caller strength curves are interpolated linearly only within support and are not standard allowables unless the caller separately establishes that meaning and right to use them.",
            "Negative margin is a deterministic comparison with a caller value, not code acceptance, proof-load qualification, failure probability or safety decision.",
            "No preload scatter, fatigue, creep relaxation, corrosion, notch effect, bolt interaction or uncertainty propagation is added.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=GasketBoltNominalStrengthScreen,
        evaluator=evaluate_gasket_bolt_nominal_strength_screen,
        units={
            "temperature_history_K[]": "K",
            "maximum_nominal_strength_utilization": "1",
            "minimum_nominal_strength_margin_Pa": "Pa",
            "strength_comparison_history[].bolt_checks[].nominal_tensile_stress_Pa": "Pa",
            "strength_comparison_history[].bolt_checks[].caller_nominal_proof_strength_Pa": "Pa",
            "strength_comparison_history[].bolt_checks[].nominal_strength_margin_Pa": "Pa",
            "strength_comparison_history[].bolt_checks[].nominal_strength_utilization": "1",
        },
        assumptions=(
            "Consume a computed caller multi-bolt/sector equilibrium and compare its nominal axial bolt stresses with per-bolt caller strength curves at exact common knots.",
            "Proof-strength curves are linearly interpolated only inside their caller-declared temperature support.",
            "Output is descriptive nominal stress margin, not code acceptance or local stress qualification.",
        ),
        source_ids=(SOURCE_ID, METHOD_SOURCE_ID),
        qualification="engineering_screening",
        context_validator=_validate_run_context,
    )]
