"""Evaluate caller-provided gasket preload-retention observations within their support."""

from __future__ import annotations

import math
from bisect import bisect_right
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Fraction, Nonnegative, Positive, canonical_digest
from .gasket_contact import BoltForceChangePoint


class GasketRelaxationCurve(Contract):
    """Reviewed normalized force-retention curve for one identified condition."""

    curve_id: str = Field(min_length=1)
    gasket_material_condition_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    retained_preload_fraction: tuple[Fraction, ...] = Field(min_length=2)
    test_and_normalization_basis_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def ordered_curve(self):
        if len(self.elapsed_time_s) != len(self.retained_preload_fraction):
            raise ValueError("relaxation time and retained-force arrays must align")
        if self.elapsed_time_s[0] != 0 or self.retained_preload_fraction[0] != 1:
            raise ValueError("curve must begin at zero elapsed time and unit normalized preload")
        if any(right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)):
            raise ValueError("relaxation time knots must be strictly increasing")
        if any(right > left for left, right in zip(self.retained_preload_fraction[:-1], self.retained_preload_fraction[1:], strict=True)):
            raise ValueError("retained preload fractions must be nonincreasing")
        return self


class GasketRelaxationRequest(Contract):
    request_id: str = Field(min_length=1)
    initial_preload_N: Positive
    curve: GasketRelaxationCurve
    evaluation_time_s: tuple[Nonnegative, ...] = Field(min_length=1)
    preload_and_curve_transfer_reviewed: bool

    @model_validator(mode="after")
    def ordered_times(self):
        if any(right < left for left, right in zip(self.evaluation_time_s[:-1], self.evaluation_time_s[1:], strict=True)):
            raise ValueError("evaluation times must be ordered; duplicate times are allowed")
        return self


def evaluate_gasket_relaxation(request: GasketRelaxationRequest) -> dict:
    """Interpolate measured/provider retention and multiply by the supplied initial preload.

    No material law is fitted, no extrapolation is made, and recovery between test
    knots is represented only by the caller's piecewise-linear curve.
    """
    curve = request.curve
    base = dict(
        request_id=request.request_id,
        curve_id=curve.curve_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        curve_sha256=canonical_digest(curve.model_dump(mode="json")),
        status="needs_data",
        force_history_N=None,
    )
    if not (
        request.preload_and_curve_transfer_reviewed
        and curve.test_and_normalization_basis_reviewed
        and curve.computational_use_authorized
    ):
        return base
    lower, upper = curve.elapsed_time_s[0], curve.elapsed_time_s[-1]
    outside = [
        time for time in request.evaluation_time_s if not lower <= time <= upper
    ]
    if outside:
        return base | dict(status="out_of_scope", unsupported_evaluation_time_s=outside)

    times = curve.elapsed_time_s
    fractions = curve.retained_preload_fraction
    rows = []
    for time in request.evaluation_time_s:
        index = min(max(bisect_right(times, time) - 1, 0), len(times) - 2)
        span = times[index + 1] - times[index]
        weight = (time - times[index]) / span
        retained = fractions[index] + weight * (fractions[index + 1] - fractions[index])
        force = request.initial_preload_N * retained
        if not math.isfinite(force):
            return base | dict(status="out_of_scope", reason="Force calculation exceeded finite numeric range")
        rows.append(dict(elapsed_time_s=time, retained_preload_fraction=retained, residual_preload_N=force))
    return base | dict(
        status="computed",
        force_history_N=rows,
        support_time_s=[lower, upper],
        specimen_id=curve.physical_specimen_id,
        source_group_id=curve.source_group_id,
        condition_sha256=curve.condition_sha256,
        source_sha256=curve.source_sha256,
        provider_id=curve.provider_id,
        provider_revision=curve.provider_revision,
        basis="Piecewise-linear interpolation of an authorized caller retention curve at fixed declared condition; no fit, time extrapolation, unload/reload hysteresis, leakage, joint equilibrium or acceptance is inferred.",
    )


class GasketPronyBranch(Contract):
    branch_id: str = Field(min_length=1)
    modulus_Pa: Positive
    relaxation_time_s: Positive


class GasketViscoelasticMaterial(Contract):
    material_condition_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    temperature_K: Positive
    equilibrium_modulus_Pa: Nonnegative
    prony_branches: tuple[GasketPronyBranch, ...] = Field(min_length=1)
    initial_branch_stress_Pa: tuple[float, ...]
    initial_branch_state_reviewed: bool
    calibration_basis_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_unique_branches(self):
        ids = [branch.branch_id for branch in self.prony_branches]
        if len(set(ids)) != len(ids) or len(self.initial_branch_stress_Pa) != len(ids):
            raise ValueError("Prony branch identities and initial internal stresses must align uniquely")
        return self


class GasketViscoelasticHistoryRequest(Contract):
    request_id: str = Field(min_length=1)
    material: GasketViscoelasticMaterial
    compression_area_m2: Positive
    compression_area_basis_reviewed: bool
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    compressive_strain: tuple[Nonnegative, ...] = Field(min_length=2)
    piecewise_linear_strain_history_reviewed: bool

    @model_validator(mode="after")
    def aligned_ordered_history(self):
        if len(self.elapsed_time_s) != len(self.compressive_strain):
            raise ValueError("time and compression-strain histories must align")
        if self.elapsed_time_s[0] != 0 or any(
            right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("history must begin at zero and have strictly increasing time")
        return self


def evaluate_gasket_viscoelastic_history(request: GasketViscoelasticHistoryRequest) -> dict:
    """Integrate a caller-calibrated generalized Maxwell model over a piecewise-linear strain path."""
    material = request.material
    digest = canonical_digest(request.model_dump(mode="json"))
    base = dict(
        request_id=request.request_id,
        status="needs_data",
        input_sha256=digest,
        response_history=None,
    )
    if not (
        request.compression_area_basis_reviewed
        and request.piecewise_linear_strain_history_reviewed
        and material.calibration_basis_reviewed
        and material.initial_branch_state_reviewed
        and material.computational_use_authorized
    ):
        return base
    branch_stress = list(material.initial_branch_stress_Pa)
    histories = []
    for index, (time, strain) in enumerate(zip(request.elapsed_time_s, request.compressive_strain, strict=True)):
        if index:
            dt = time - request.elapsed_time_s[index - 1]
            strain_rate = (strain - request.compressive_strain[index - 1]) / dt
            for branch_index, branch in enumerate(material.prony_branches):
                decay = math.exp(-dt / branch.relaxation_time_s)
                ramp_factor = -math.expm1(-dt / branch.relaxation_time_s)
                branch_stress[branch_index] = (
                    branch_stress[branch_index] * decay
                    + branch.modulus_Pa * strain_rate * branch.relaxation_time_s * ramp_factor
                )
        stress = material.equilibrium_modulus_Pa * strain + math.fsum(branch_stress)
        force = stress * request.compression_area_m2
        if not math.isfinite(stress) or not math.isfinite(force):
            return base | dict(status="out_of_scope", reason="Viscoelastic response exceeded finite numeric range")
        if stress < 0:
            return base | dict(
                status="out_of_scope",
                reason="The linear viscoelastic response predicts tensile gasket stress; contact-loss mechanics are not represented.",
                first_unsupported_time_s=time,
            )
        histories.append(
            dict(
                elapsed_time_s=time,
                compressive_strain=strain,
                equilibrium_stress_Pa=material.equilibrium_modulus_Pa * strain,
                branch_stress_Pa=list(branch_stress),
                total_compressive_stress_Pa=stress,
                compressive_force_N=force,
            )
        )
    return base | dict(
        status="computed",
        response_history=histories,
        branch_ids=[branch.branch_id for branch in material.prony_branches],
        material_condition_id=material.material_condition_id,
        physical_specimen_id=material.physical_specimen_id,
        source_group_id=material.source_group_id,
        source_sha256=material.source_sha256,
        condition_sha256=material.condition_sha256,
        provider_id=material.provider_id,
        provider_revision=material.provider_revision,
        temperature_K=material.temperature_K,
        strain_path_interpretation="piecewise_linear_between_declared_knots",
        basis="Caller-authorized generalized Maxwell Prony response with exact branch-state update for piecewise-linear compressive strain over each interval. No parameter fit, condition transfer, tensile contact, flange flexibility, leakage or acceptance is inferred.",
    )


class GasketViscoelasticJointHistoryRequest(Contract):
    """Coupled quasi-static bolt equilibrium and caller-calibrated Prony gasket history."""

    request_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    material: GasketViscoelasticMaterial
    compression_area_m2: Positive
    gasket_compression_height_m: Positive
    bolt_stiffness_N_m: Positive
    initial_compressive_strain: Nonnegative
    maximum_compressive_strain: Positive
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    external_separating_force_N: tuple[Nonnegative, ...] = Field(min_length=2)
    bolt_free_length_change_m: tuple[float, ...] = Field(min_length=2)
    joint_geometry_and_force_balance_reviewed: bool
    piecewise_linear_internal_strain_update_reviewed: bool
    coupled_history_model_applicability_reviewed: bool

    @model_validator(mode="after")
    def aligned_joint_history(self):
        count = len(self.elapsed_time_s)
        if len(self.external_separating_force_N) != count or len(self.bolt_free_length_change_m) != count:
            raise ValueError("time, separating-force and bolt free-length histories must align")
        if self.elapsed_time_s[0] != 0 or any(
            right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("joint history must begin at zero and have strictly increasing time")
        if self.bolt_free_length_change_m[0] != 0:
            raise ValueError("bolt free-length history must use zero change at the initial reference time")
        if self.initial_compressive_strain > self.maximum_compressive_strain:
            raise ValueError("initial strain exceeds declared compression support")
        if self.maximum_compressive_strain <= 0:
            raise ValueError("maximum compression strain must be positive")
        return self


def _finite_sum(values):
    try:
        result = math.fsum(values)
    except (OverflowError, ValueError):
        return None
    return result if math.isfinite(result) else None


def evaluate_gasket_viscoelastic_joint_history(request: GasketViscoelasticJointHistoryRequest) -> dict:
    """Solve each time-knot equilibrium exactly for the linear Prony-plus-bolt model.

    Between consecutive knots, each Maxwell branch receives the closed-form update
    for a linear strain segment. The unknown endpoint compression strain follows
    from the affine force balance, so no iterative nonlinear constitutive solve is
    implied by this caller-calibrated linear model.
    """
    material = request.material
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "request_id": request.request_id,
        "joint_id": request.joint_id,
        "status": "needs_data",
        "input_sha256": digest,
        "material_condition_id": material.material_condition_id,
        "material_source_sha256": material.source_sha256,
        "material_condition_sha256": material.condition_sha256,
        "provider_id": material.provider_id,
        "provider_revision": material.provider_revision,
        "temperature_K": material.temperature_K,
    }
    if not (
        request.joint_geometry_and_force_balance_reviewed
        and request.piecewise_linear_internal_strain_update_reviewed
        and request.coupled_history_model_applicability_reviewed
        and material.calibration_basis_reviewed
        and material.initial_branch_state_reviewed
        and material.computational_use_authorized
    ):
        return base | {"missing_review_count": sum(not flag for flag in (
            request.joint_geometry_and_force_balance_reviewed,
            request.piecewise_linear_internal_strain_update_reviewed,
            request.coupled_history_model_applicability_reviewed,
            material.calibration_basis_reviewed,
            material.initial_branch_state_reviewed,
            material.computational_use_authorized,
        ))}

    numeric_inputs = [
        request.compression_area_m2,
        request.gasket_compression_height_m,
        request.bolt_stiffness_N_m,
        request.initial_compressive_strain,
        request.maximum_compressive_strain,
        material.temperature_K,
        material.equilibrium_modulus_Pa,
        *request.elapsed_time_s,
        *request.external_separating_force_N,
        *request.bolt_free_length_change_m,
        *material.initial_branch_stress_Pa,
        *(value for branch in material.prony_branches for value in (branch.modulus_Pa, branch.relaxation_time_s)),
    ]
    if any(not math.isfinite(value) for value in numeric_inputs):
        return base | {"status": "out_of_scope", "reason": "Nonfinite input in joint or Prony history"}
    area = request.compression_area_m2
    height = request.gasket_compression_height_m
    initial_strain = request.initial_compressive_strain
    maximum_strain = request.maximum_compressive_strain
    branches = material.prony_branches
    branch_stress = list(material.initial_branch_stress_Pa)
    initial_branch_sum = _finite_sum(branch_stress)
    if initial_branch_sum is None:
        return base | {"status": "out_of_scope", "reason": "Initial branch stress sum exceeded finite numeric range"}
    initial_gasket_stress = material.equilibrium_modulus_Pa * initial_strain + initial_branch_sum
    initial_gasket_force = area * initial_gasket_stress
    if not math.isfinite(initial_gasket_force) or initial_gasket_stress < 0:
        return base | {"status": "out_of_scope", "reason": "Initial Prony state yields nonfinite or tensile gasket response"}
    initial_bolt_force = initial_gasket_force + request.external_separating_force_N[0]
    if not math.isfinite(initial_bolt_force) or initial_bolt_force < 0:
        return base | {"status": "out_of_scope", "reason": "Initial bolt preload is nonfinite or negative"}

    rows = [{
        "elapsed_time_s": request.elapsed_time_s[0],
        "compressive_strain": initial_strain,
        "compressive_displacement_m": initial_strain * height,
        "branch_stress_Pa": list(branch_stress),
        "gasket_stress_Pa": initial_gasket_stress,
        "gasket_force_N": initial_gasket_force,
        "bolt_force_N": initial_bolt_force,
        "external_separating_force_N": request.external_separating_force_N[0],
        "bolt_free_length_change_m": 0.0,
        "bolt_extension_change_m": 0.0,
        "force_balance_residual_N": 0.0,
    }]
    previous_strain = initial_strain
    for index in range(1, len(request.elapsed_time_s)):
        time = request.elapsed_time_s[index]
        dt = time - request.elapsed_time_s[index - 1]
        decays = []
        ramp_coefficients = []
        for branch in branches:
            ratio = dt / branch.relaxation_time_s
            decay = math.exp(-ratio) if math.isfinite(ratio) else 0.0
            ramp_fraction = -math.expm1(-ratio) if math.isfinite(ratio) else 1.0
            coefficient = branch.modulus_Pa * (branch.relaxation_time_s / dt) * ramp_fraction
            decays.append(decay)
            ramp_coefficients.append(coefficient)
        if any(not math.isfinite(value) for value in ramp_coefficients):
            return base | {"status": "out_of_scope", "reason": "Prony interval coefficient exceeded finite numeric range", "first_unsupported_time_s": time, "computed_prefix": rows}

        relaxed_branch_state = [
            branch_stress[i] * decays[i] - ramp_coefficients[i] * previous_strain
            for i in range(len(branches))
        ]
        ramp_sum = _finite_sum(ramp_coefficients)
        relaxed_branch_sum = _finite_sum(relaxed_branch_state)
        if ramp_sum is None or relaxed_branch_sum is None:
            return base | {"status": "out_of_scope", "reason": "Prony branch state exceeded finite numeric range", "first_unsupported_time_s": time, "computed_prefix": rows}
        free_change = request.bolt_free_length_change_m[index]
        external_force = request.external_separating_force_N[index]
        residual_at_zero = (
            initial_bolt_force
            + request.bolt_stiffness_N_m * (initial_strain * height - free_change)
            - area * relaxed_branch_sum
            - external_force
        )
        tangent = request.bolt_stiffness_N_m * height + area * (
            material.equilibrium_modulus_Pa + ramp_sum
        )
        if not math.isfinite(residual_at_zero) or not math.isfinite(tangent) or tangent <= 0:
            return base | {"status": "out_of_scope", "reason": "Joint equilibrium exceeded finite numeric range", "first_unsupported_time_s": time, "computed_prefix": rows}
        strain = residual_at_zero / tangent
        if not 0 < strain <= maximum_strain:
            reason = "Contact loss requires a unilateral separation model" if strain <= 0 else "Required compression exceeds declared strain support"
            return base | {"status": "out_of_scope", "reason": reason, "first_unsupported_time_s": time, "required_compressive_strain": strain, "computed_prefix": rows}

        branch_stress = [
            branch_stress[i] * decays[i] + ramp_coefficients[i] * (strain - previous_strain)
            for i in range(len(branches))
        ]
        branch_sum = _finite_sum(branch_stress)
        if branch_sum is None:
            return base | {"status": "out_of_scope", "reason": "Updated branch stress exceeded finite numeric range", "first_unsupported_time_s": time, "computed_prefix": rows}
        gasket_stress = material.equilibrium_modulus_Pa * strain + branch_sum
        gasket_force = area * gasket_stress
        bolt_extension = (initial_strain - strain) * height - free_change
        bolt_force = initial_bolt_force + request.bolt_stiffness_N_m * bolt_extension
        residual = bolt_force - gasket_force - external_force
        if not all(math.isfinite(value) for value in (strain * height, gasket_stress, gasket_force, bolt_extension, bolt_force, residual)):
            return base | {"status": "out_of_scope", "reason": "Viscoelastic joint state exceeded finite numeric range", "first_unsupported_time_s": time, "computed_prefix": rows}
        if gasket_stress < 0 or bolt_force < 0:
            return base | {"status": "out_of_scope", "reason": "Tensile gasket stress or negative bolt force is outside the compression-contact model", "first_unsupported_time_s": time, "computed_prefix": rows}
        rows.append({
            "elapsed_time_s": time,
            "compressive_strain": strain,
            "compressive_displacement_m": strain * height,
            "branch_stress_Pa": list(branch_stress),
            "gasket_stress_Pa": gasket_stress,
            "gasket_force_N": gasket_force,
            "bolt_force_N": bolt_force,
            "external_separating_force_N": external_force,
            "bolt_free_length_change_m": free_change,
            "bolt_extension_change_m": bolt_extension,
            "force_balance_residual_N": residual,
        })
        previous_strain = strain

    return base | {
        "status": "computed",
        "initial_bolt_preload_N": initial_bolt_force,
        "response_history": rows,
        "strain_interpretation": "piecewise_linear_between_solved_time_knots",
        "basis": "Coupled single-degree-of-freedom equilibrium of a linear elastic bolt and caller-authorized generalized-Maxwell gasket. Branch stress is updated for piecewise-linear strain between knots, and each endpoint equilibrium is solved in closed form. Contact opening, flange flexibility, leakage, coefficient fitting/transfer and acceptance are not modeled.",
    }


class GasketBackbonePoint(Contract):
    compressive_strain: Nonnegative
    stress_Pa: Nonnegative


class NonlinearGasketMaxwellBranch(Contract):
    branch_id: str = Field(min_length=1)
    relaxation_time_s: Positive
    stress_strain_backbone: tuple[GasketBackbonePoint, ...] = Field(min_length=2, max_length=10000)

    @model_validator(mode="after")
    def curve_support(self):
        points = self.stress_strain_backbone
        if points[0].compressive_strain != 0 or points[0].stress_Pa != 0:
            raise ValueError("Maxwell branch backbone must begin at zero strain and stress")
        if any(
            right.compressive_strain <= left.compressive_strain
            or right.stress_Pa < left.stress_Pa
            for left, right in zip(points[:-1], points[1:], strict=True)
        ):
            raise ValueError("branch backbone strain must increase and stress must not decrease")
        return self


class NonlinearGasketViscoelasticMaterial(Contract):
    material_condition_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    temperature_K: Positive
    equilibrium_stress_strain_backbone: tuple[GasketBackbonePoint, ...] = Field(min_length=2, max_length=10000)
    branches: tuple[NonlinearGasketMaxwellBranch, ...] = Field(min_length=1, max_length=100)
    initial_branch_stress_Pa: tuple[float, ...]
    nonlinear_branch_calibration_reviewed: bool
    initial_branch_state_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_backbones(self):
        equilibrium = self.equilibrium_stress_strain_backbone
        if equilibrium[0].compressive_strain != 0 or equilibrium[0].stress_Pa != 0:
            raise ValueError("equilibrium backbone must begin at zero strain and stress")
        if any(
            right.compressive_strain <= left.compressive_strain or right.stress_Pa < left.stress_Pa
            for left, right in zip(equilibrium[:-1], equilibrium[1:], strict=True)
        ):
            raise ValueError("equilibrium backbone strain must increase and stress must not decrease")
        branch_ids = [branch.branch_id for branch in self.branches]
        if len(branch_ids) != len(set(branch_ids)) or len(self.initial_branch_stress_Pa) != len(branch_ids):
            raise ValueError("branch IDs and initial internal stresses must align uniquely")
        maximum_strain = equilibrium[-1].compressive_strain
        for branch in self.branches:
            if branch.stress_strain_backbone[-1].compressive_strain < maximum_strain:
                raise ValueError("all Maxwell branch curves must cover the equilibrium backbone support")
        return self


class NonlinearGasketViscoelasticJointHistoryRequest(Contract):
    request_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    material: NonlinearGasketViscoelasticMaterial
    compression_area_m2: Positive
    gasket_compression_height_m: Positive
    bolt_force_change_curve: tuple[BoltForceChangePoint, ...] = Field(min_length=3, max_length=10000)
    bolt_curve_id: str = Field(min_length=1)
    bolt_curve_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_compressive_strain: Nonnegative
    maximum_compressive_strain: Positive
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=100000)
    external_separating_force_N: tuple[Nonnegative, ...] = Field(min_length=2, max_length=100000)
    bolt_free_length_change_m: tuple[float, ...] = Field(min_length=2, max_length=100000)
    joint_geometry_and_force_balance_reviewed: bool
    piecewise_linear_internal_strain_update_reviewed: bool
    coupled_history_model_applicability_reviewed: bool
    bolt_curve_and_support_reviewed: bool

    @model_validator(mode="after")
    def coherent_support(self):
        count = len(self.elapsed_time_s)
        if len(self.external_separating_force_N) != count or len(self.bolt_free_length_change_m) != count:
            raise ValueError("time, separating-force and bolt free-length histories must align")
        if self.elapsed_time_s[0] != 0 or any(
            right <= left for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
        ):
            raise ValueError("joint history must begin at zero and have strictly increasing times")
        if self.bolt_free_length_change_m[0] != 0:
            raise ValueError("bolt free-length history must start at zero change")
        if self.initial_compressive_strain > self.maximum_compressive_strain:
            raise ValueError("initial strain exceeds requested support")
        if self.maximum_compressive_strain > self.material.equilibrium_stress_strain_backbone[-1].compressive_strain:
            raise ValueError("requested strain exceeds equilibrium backbone support")
        bolt = self.bolt_force_change_curve
        if not any(row.extension_change_m == 0 and row.force_change_N == 0 for row in bolt):
            raise ValueError("bolt force-change curve must include the origin")
        for left, right in zip(bolt[:-1], bolt[1:], strict=True):
            if right.extension_change_m <= left.extension_change_m or right.force_change_N <= left.force_change_N:
                raise ValueError("bolt extension and force-change must increase strictly")
        return self


def _backbone_stress(points: tuple[GasketBackbonePoint, ...], strain: float) -> float:
    strains = [point.compressive_strain for point in points]
    if strain < strains[0] or strain > strains[-1]:
        raise ValueError("strain is outside caller backbone support")
    index = min(max(bisect_right(strains, strain) - 1, 0), len(points) - 2)
    left, right = points[index], points[index + 1]
    fraction = (strain - left.compressive_strain) / (right.compressive_strain - left.compressive_strain)
    return left.stress_Pa + fraction * (right.stress_Pa - left.stress_Pa)


def _advance_nonlinear_branch(branch: NonlinearGasketMaxwellBranch, state: float, start: float, end: float, dt: float) -> float:
    points = branch.stress_strain_backbone
    direction = 1 if end > start else -1
    interior = [
        point.compressive_strain for point in points
        if min(start, end) < point.compressive_strain < max(start, end)
    ]
    interior.sort(reverse=direction < 0)
    path = [start, *interior, end]
    total_strain_change = abs(end - start)
    for left_strain, right_strain in zip(path[:-1], path[1:], strict=True):
        interval = dt if total_strain_change == 0 else dt * abs(right_strain - left_strain) / total_strain_change
        ratio = interval / branch.relaxation_time_s
        decay = math.exp(-ratio) if math.isfinite(ratio) else 0.0
        ramp = -math.expm1(-ratio) if math.isfinite(ratio) else 1.0
        delta_backbone_stress = _backbone_stress(points, right_strain) - _backbone_stress(points, left_strain)
        if total_strain_change == 0:
            state *= decay
        else:
            state = state * decay + (delta_backbone_stress / interval) * branch.relaxation_time_s * ramp
        if not math.isfinite(state):
            raise ValueError("nonlinear Maxwell branch state exceeded finite numeric range")
    return state


def evaluate_nonlinear_gasket_viscoelastic_joint_history(
    request: NonlinearGasketViscoelasticJointHistoryRequest,
) -> dict:
    """Solve closed-contact bolt/gasket equilibrium with piecewise-linear nonlinear Maxwell branches."""
    material = request.material
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "request_id": request.request_id,
        "joint_id": request.joint_id,
        "status": "needs_data",
        "input_sha256": digest,
        "material_condition_id": material.material_condition_id,
        "material_source_sha256": material.source_sha256,
        "material_condition_sha256": material.condition_sha256,
        "bolt_curve_id": request.bolt_curve_id,
        "bolt_curve_source_sha256": request.bolt_curve_source_sha256,
    }
    reviews = (
        request.joint_geometry_and_force_balance_reviewed,
        request.piecewise_linear_internal_strain_update_reviewed,
        request.coupled_history_model_applicability_reviewed,
        request.bolt_curve_and_support_reviewed,
        material.nonlinear_branch_calibration_reviewed,
        material.initial_branch_state_reviewed,
        material.computational_use_authorized,
    )
    if not all(reviews):
        return base | {"missing_review_count": sum(not flag for flag in reviews)}

    area = request.compression_area_m2
    height = request.gasket_compression_height_m
    max_strain = request.maximum_compressive_strain
    initial_strain = request.initial_compressive_strain
    if not all(math.isfinite(value) for value in (
        area, height, max_strain, initial_strain, material.temperature_K,
        *request.elapsed_time_s, *request.external_separating_force_N,
        *request.bolt_free_length_change_m, *material.initial_branch_stress_Pa,
    )):
        return base | {"status": "out_of_scope", "reason": "nonfinite_joint_or_material_input"}

    def bolt_delta(extension: float) -> float:
        points = request.bolt_force_change_curve
        low, high = points[0].extension_change_m, points[-1].extension_change_m
        if extension < low or extension > high:
            raise ValueError("required bolt extension is outside caller curve support")
        coordinates = [point.extension_change_m for point in points]
        index = min(max(bisect_right(coordinates, extension) - 1, 0), len(points) - 2)
        left, right = points[index], points[index + 1]
        weight = (extension - left.extension_change_m) / (right.extension_change_m - left.extension_change_m)
        return left.force_change_N + weight * (right.force_change_N - left.force_change_N)

    branch_state = list(material.initial_branch_stress_Pa)
    if any(not math.isfinite(value) for value in branch_state):
        return base | {"status": "out_of_scope", "reason": "nonfinite_initial_branch_state"}
    try:
        initial_stress = _backbone_stress(material.equilibrium_stress_strain_backbone, initial_strain) + math.fsum(branch_state)
        initial_gasket_force = area * initial_stress
        initial_bolt_force = initial_gasket_force + request.external_separating_force_N[0]
        if not all(math.isfinite(value) for value in (initial_stress, initial_gasket_force, initial_bolt_force)) or initial_stress < 0:
            return base | {"status": "out_of_scope", "reason": "invalid_initial_gasket_force_state"}
        rows = [{
            "elapsed_time_s": request.elapsed_time_s[0],
            "compressive_strain": initial_strain,
            "compressive_displacement_m": initial_strain * height,
            "equilibrium_backbone_stress_Pa": _backbone_stress(material.equilibrium_stress_strain_backbone, initial_strain),
            "branch_stress_Pa": list(branch_state),
            "gasket_stress_Pa": initial_stress,
            "gasket_force_N": initial_gasket_force,
            "bolt_force_N": initial_bolt_force,
            "external_separating_force_N": request.external_separating_force_N[0],
            "bolt_free_length_change_m": 0.0,
            "bolt_extension_change_m": 0.0,
            "force_balance_residual_N": 0.0,
        }]
        previous_strain = initial_strain
        for index in range(1, len(request.elapsed_time_s)):
            time = request.elapsed_time_s[index]
            dt = time - request.elapsed_time_s[index - 1]
            free_change = request.bolt_free_length_change_m[index]
            external_force = request.external_separating_force_N[index]

            def candidate_state(strain: float):
                updated = [
                    _advance_nonlinear_branch(branch, branch_state[branch_index], previous_strain, strain, dt)
                    for branch_index, branch in enumerate(material.branches)
                ]
                equilibrium_stress = _backbone_stress(material.equilibrium_stress_strain_backbone, strain)
                gasket_stress = equilibrium_stress + math.fsum(updated)
                extension = (initial_strain - strain) * height - free_change
                bolt_force = initial_bolt_force + bolt_delta(extension)
                gasket_force = area * gasket_stress
                residual = bolt_force - gasket_force - external_force
                if not all(math.isfinite(value) for value in (*updated, equilibrium_stress, gasket_stress, extension, bolt_force, gasket_force, residual)):
                    raise ValueError("joint state exceeded finite numeric range")
                return residual, updated, equilibrium_stress, gasket_stress, extension, bolt_force, gasket_force

            bolt_min_extension = request.bolt_force_change_curve[0].extension_change_m
            bolt_max_extension = request.bolt_force_change_curve[-1].extension_change_m
            lower_strain = max(
                0.0,
                initial_strain - (bolt_max_extension + free_change) / height,
            )
            upper_strain = min(
                max_strain,
                initial_strain - (bolt_min_extension + free_change) / height,
            )
            if upper_strain < lower_strain:
                return base | {"status": "out_of_scope", "reason": "bolt_and_gasket_strain_supports_do_not_overlap", "first_unsupported_time_s": time, "computed_prefix": rows}
            low_state, high_state = candidate_state(lower_strain), candidate_state(upper_strain)
            if low_state[0] <= 0:
                reason = (
                    "contact_opening_requires_unilateral_history_model"
                    if lower_strain == 0.0
                    else "equilibrium_requires_compression_outside_bolt_curve_support"
                )
                return base | {"status": "out_of_scope", "reason": reason, "first_unsupported_time_s": time, "computed_prefix": rows}
            if high_state[0] >= 0:
                reason = (
                    "required_compression_exceeds_declared_curve_support"
                    if upper_strain == max_strain
                    else "equilibrium_requires_compression_outside_bolt_curve_support"
                )
                return base | {"status": "out_of_scope", "reason": reason, "first_unsupported_time_s": time, "computed_prefix": rows}
            low, high = lower_strain, upper_strain
            for _ in range(100):
                middle = (low + high) / 2.0
                middle_state = candidate_state(middle)
                if middle_state[0] > 0:
                    low = middle
                else:
                    high = middle
                if high - low <= max(1e-14, 1e-12 * max_strain):
                    break
            strain = (low + high) / 2.0
            residual, branch_state, equilibrium_stress, gasket_stress, extension, bolt_force, gasket_force = candidate_state(strain)
            if gasket_stress < 0 or bolt_force < 0:
                return base | {"status": "out_of_scope", "reason": "tensile_gasket_stress_or_negative_bolt_force", "first_unsupported_time_s": time, "computed_prefix": rows}
            rows.append({
                "elapsed_time_s": time,
                "compressive_strain": strain,
                "compressive_displacement_m": strain * height,
                "equilibrium_backbone_stress_Pa": equilibrium_stress,
                "branch_stress_Pa": list(branch_state),
                "gasket_stress_Pa": gasket_stress,
                "gasket_force_N": gasket_force,
                "bolt_force_N": bolt_force,
                "external_separating_force_N": external_force,
                "bolt_free_length_change_m": free_change,
                "bolt_extension_change_m": extension,
                "force_balance_residual_N": residual,
            })
            previous_strain = strain
    except (ArithmeticError, OverflowError, ValueError) as error:
        return base | {"status": "out_of_scope", "reason": str(error), "computed_prefix": rows if "rows" in locals() else []}

    return base | {
        "status": "computed",
        "initial_bolt_preload_N": initial_bolt_force,
        "response_history": rows,
        "branch_ids": [branch.branch_id for branch in material.branches],
        "temperature_K": material.temperature_K,
        "strain_path_interpretation": "piecewise_linear_between_equilibrium_knots_with_branch_backbone_breakpoint_splitting",
        "basis": "Caller-authorized nonlinear generalized-Maxwell gasket branches with monotone piecewise-linear stress-strain backbones, exact exponential branch updates over split linear-strain segments, caller nonlinear bolt force-extension curve, and quasi-static single-degree-of-freedom equilibrium at declared knots. Contact opening, curve extrapolation, flange fields, leakage, parameter fitting/transfer and acceptance are not modeled.",
    }


class UnilateralNonlinearGasketJointHistoryRequest(NonlinearGasketViscoelasticJointHistoryRequest):
    """Request for a knotwise unilateral gasket-contact history."""

    schema_version: Literal["matintegrity.unilateral_nonlinear_gasket_prony_joint_history.v1"] = (
        "matintegrity.unilateral_nonlinear_gasket_prony_joint_history.v1"
    )
    initial_compressive_strain: Positive
    unilateral_contact_transition_reviewed: bool
    zero_compression_branch_state_reviewed: bool
    between_knot_transition_interpretation_reviewed: bool


def evaluate_unilateral_nonlinear_gasket_joint_history(
    request: UnilateralNonlinearGasketJointHistoryRequest,
) -> dict:
    """Add compression-only contact to the nonlinear single-degree-of-freedom joint.

    The gasket carries no force at zero compression. While separated, the bolt
    follows the supplied force-extension curve against the external separating
    force. Contact may close at a declared time knot when that separated state
    would require compression or when a compressive equilibrium becomes
    available. This is a knotwise model; transition times between knots are not
    reconstructed.
    """
    material = request.material
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "request_id": request.request_id,
        "joint_id": request.joint_id,
        "status": "needs_data",
        "input_sha256": digest,
        "material_condition_id": material.material_condition_id,
        "material_source_sha256": material.source_sha256,
        "material_condition_sha256": material.condition_sha256,
        "bolt_curve_id": request.bolt_curve_id,
        "bolt_curve_source_sha256": request.bolt_curve_source_sha256,
    }
    reviews = (
        request.joint_geometry_and_force_balance_reviewed,
        request.piecewise_linear_internal_strain_update_reviewed,
        request.coupled_history_model_applicability_reviewed,
        request.bolt_curve_and_support_reviewed,
        material.nonlinear_branch_calibration_reviewed,
        material.initial_branch_state_reviewed,
        material.computational_use_authorized,
        request.unilateral_contact_transition_reviewed,
        request.zero_compression_branch_state_reviewed,
        request.between_knot_transition_interpretation_reviewed,
    )
    if not all(reviews):
        return base | {"missing_review_count": sum(not flag for flag in reviews)}

    area = request.compression_area_m2
    height = request.gasket_compression_height_m
    max_strain = request.maximum_compressive_strain
    initial_strain = request.initial_compressive_strain
    if not all(math.isfinite(value) for value in (
        area, height, max_strain, initial_strain, material.temperature_K,
        *request.elapsed_time_s, *request.external_separating_force_N,
        *request.bolt_free_length_change_m, *material.initial_branch_stress_Pa,
    )):
        return base | {"status": "out_of_scope", "reason": "nonfinite_joint_or_material_input"}

    def bolt_delta(extension: float) -> float:
        points = request.bolt_force_change_curve
        coordinates = [point.extension_change_m for point in points]
        if extension < coordinates[0] or extension > coordinates[-1]:
            raise ValueError("required bolt extension is outside caller curve support")
        index = min(max(bisect_right(coordinates, extension) - 1, 0), len(points) - 2)
        left, right = points[index], points[index + 1]
        fraction = (extension - left.extension_change_m) / (right.extension_change_m - left.extension_change_m)
        return left.force_change_N + fraction * (right.force_change_N - left.force_change_N)

    def bolt_force(strain: float, free_change: float, initial_force: float) -> tuple[float, float]:
        extension = (initial_strain - strain) * height - free_change
        return initial_force + bolt_delta(extension), extension

    def extension_for_force_change(force_change: float) -> float:
        points = request.bolt_force_change_curve
        if not points[0].force_change_N <= force_change <= points[-1].force_change_N:
            raise ValueError("separated bolt equilibrium is outside caller curve support")
        forces = [point.force_change_N for point in points]
        index = min(max(bisect_right(forces, force_change) - 1, 0), len(points) - 2)
        left, right = points[index], points[index + 1]
        fraction = (force_change - left.force_change_N) / (right.force_change_N - left.force_change_N)
        return left.extension_change_m + fraction * (right.extension_change_m - left.extension_change_m)

    branch_state = list(material.initial_branch_stress_Pa)
    if any(not math.isfinite(value) for value in branch_state):
        return base | {"status": "out_of_scope", "reason": "nonfinite_initial_branch_state"}
    try:
        initial_equilibrium = _backbone_stress(material.equilibrium_stress_strain_backbone, initial_strain)
        initial_stress = initial_equilibrium + math.fsum(branch_state)
        initial_gasket_force = area * initial_stress
        initial_bolt_force = initial_gasket_force + request.external_separating_force_N[0]
        if not all(math.isfinite(v) for v in (initial_stress, initial_gasket_force, initial_bolt_force)):
            return base | {"status": "out_of_scope", "reason": "invalid_initial_joint_state"}
        if initial_stress < 0:
            return base | {"status": "out_of_scope", "reason": "initial_zero_compression_branch_state_requires_explicit_constitutive_state"}

        rows = [{
            "elapsed_time_s": request.elapsed_time_s[0],
            "contact_state": "closed",
            "contact_transition": "initial_condition",
            "compressive_strain": initial_strain,
            "compressive_displacement_m": initial_strain * height,
            "equilibrium_backbone_stress_Pa": initial_equilibrium,
            "branch_stress_Pa": list(branch_state),
            "gasket_stress_Pa": initial_stress,
            "gasket_force_N": initial_gasket_force,
            "bolt_force_N": initial_bolt_force,
            "external_separating_force_N": request.external_separating_force_N[0],
            "bolt_free_length_change_m": 0.0,
            "bolt_extension_change_m": 0.0,
            "force_balance_residual_N": 0.0,
        }]
        previous_strain = initial_strain
        contact_state = "closed"
        transition_count = 0
        for index in range(1, len(request.elapsed_time_s)):
            time = request.elapsed_time_s[index]
            dt = time - request.elapsed_time_s[index - 1]
            free_change = request.bolt_free_length_change_m[index]
            external_force = request.external_separating_force_N[index]

            def candidate(strain: float, advance_branches: bool = True):
                updated = (
                    [
                        _advance_nonlinear_branch(branch, branch_state[j], previous_strain, strain, dt)
                        for j, branch in enumerate(material.branches)
                    ]
                    if advance_branches
                    else list(branch_state)
                )
                eq_stress = _backbone_stress(material.equilibrium_stress_strain_backbone, strain)
                gasket_stress = eq_stress + math.fsum(updated)
                bolt, extension = bolt_force(strain, free_change, initial_bolt_force)
                force = area * gasket_stress
                residual = bolt - force - external_force
                if not all(math.isfinite(v) for v in (*updated, eq_stress, gasket_stress, bolt, extension, force, residual)):
                    raise ValueError("joint state exceeded finite numeric range")
                return residual, updated, eq_stress, gasket_stress, extension, bolt, force

            bolt_min = request.bolt_force_change_curve[0].extension_change_m
            bolt_max = request.bolt_force_change_curve[-1].extension_change_m
            lower = max(0.0, initial_strain - (bolt_max + free_change) / height)
            upper = min(max_strain, initial_strain - (bolt_min + free_change) / height)
            if upper < lower:
                return base | {"status": "out_of_scope", "reason": "bolt_and_gasket_strain_supports_do_not_overlap", "first_unsupported_time_s": time, "computed_prefix": rows}
            low_state, high_state = candidate(lower), candidate(upper)
            transition = "none"

            if contact_state == "closed" and low_state[0] <= 0:
                contact_state = "separated"
                transition = "opened_at_time_knot"
                transition_count += 1

            if contact_state == "separated":
                # With no gasket traction, solve the bolt-only equilibrium. The
                # gasket remains open only if that state retains a nonnegative gap.
                separated_extension = extension_for_force_change(external_force - initial_bolt_force)
                opening_gap = separated_extension + free_change - initial_strain * height
                if opening_gap >= 0:
                    strain = 0.0
                    eq_stress = gasket_stress = gasket_force = 0.0
                    extension = separated_extension
                    bolt = external_force
                    residual = 0.0
                    transition = transition if transition != "none" else "remained_open"
                    previous_strain = 0.0
                    rows.append({
                        "elapsed_time_s": time, "contact_state": "separated", "contact_transition": transition,
                        "compressive_strain": 0.0, "compressive_displacement_m": 0.0,
                        "equilibrium_backbone_stress_Pa": 0.0, "branch_stress_Pa": list(branch_state),
                        "gasket_stress_Pa": 0.0, "gasket_force_N": 0.0, "bolt_force_N": bolt,
                        "external_separating_force_N": external_force, "bolt_free_length_change_m": free_change,
                        "bolt_extension_change_m": extension, "force_balance_residual_N": residual,
                    })
                    continue
                # The bolt-only state would penetrate the gasket reference plane:
                # return to the compression-contact force balance.
                if high_state[0] > 0:
                    reason = "required_compression_exceeds_declared_curve_support" if upper == max_strain else "equilibrium_outside_bolt_curve_support"
                    return base | {"status": "out_of_scope", "reason": reason, "first_unsupported_time_s": time, "computed_prefix": rows}
                lo, hi = max(0.0, lower), upper
                for _ in range(100):
                    mid = (lo + hi) / 2.0
                    if candidate(mid, advance_branches=False)[0] > 0:
                        lo = mid
                    else:
                        hi = mid
                    if hi - lo <= max(1e-14, 1e-12 * max_strain):
                        break
                strain = (lo + hi) / 2.0
                transition = "reclosed_at_time_knot"
                contact_state = "closed"
                transition_count += 1
                residual, branch_state, eq_stress, gasket_stress, extension, bolt, gasket_force = candidate(
                    strain, advance_branches=False
                )
            else:
                if high_state[0] >= 0:
                    return base | {"status": "out_of_scope", "reason": "required_compression_exceeds_declared_curve_support" if upper == max_strain else "equilibrium_outside_bolt_curve_support", "first_unsupported_time_s": time, "computed_prefix": rows}
                lo, hi = lower, upper
                for _ in range(100):
                    mid = (lo + hi) / 2.0
                    if candidate(mid)[0] > 0:
                        lo = mid
                    else:
                        hi = mid
                    if hi - lo <= max(1e-14, 1e-12 * max_strain):
                        break
                strain = (lo + hi) / 2.0
                residual, branch_state, eq_stress, gasket_stress, extension, bolt, gasket_force = candidate(
                    strain, advance_branches=True
                )
            if gasket_stress < -1e-8 or bolt < -1e-8:
                return base | {"status": "out_of_scope", "reason": "negative_contact_or_bolt_force", "first_unsupported_time_s": time, "computed_prefix": rows}
            previous_strain = strain
            rows.append({
                "elapsed_time_s": time, "contact_state": "closed", "contact_transition": transition,
                "compressive_strain": strain, "compressive_displacement_m": strain * height,
                "equilibrium_backbone_stress_Pa": eq_stress, "branch_stress_Pa": list(branch_state),
                "gasket_stress_Pa": gasket_stress, "gasket_force_N": gasket_force,
                "bolt_force_N": bolt, "external_separating_force_N": external_force,
                "bolt_free_length_change_m": free_change, "bolt_extension_change_m": extension,
                "force_balance_residual_N": residual,
            })
        return base | {
            "status": "computed", "initial_bolt_preload_N": initial_bolt_force,
            "response_history": rows, "branch_ids": [branch.branch_id for branch in material.branches],
                "contact_transition_count": transition_count,
            "temperature_K": material.temperature_K,
            "transition_interpretation": "knotwise_complementarity_no_between_knot_transition_time",
            "basis": "Caller-authorized nonlinear generalized-Maxwell gasket history with unilateral zero-tension contact, knotwise open/reclose transitions, a supplied nonlinear bolt curve and quasi-static single-degree-of-freedom equilibrium. Transitions are only located at declared time knots; flange fields, leakage, curve transfer and acceptance are not represented.",
        }
    except (ArithmeticError, OverflowError, ValueError) as error:
        return base | {"status": "out_of_scope", "reason": str(error), "computed_prefix": rows if "rows" in locals() else []}
