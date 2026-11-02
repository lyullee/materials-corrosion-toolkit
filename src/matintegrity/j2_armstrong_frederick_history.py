"""Small-strain J2 response with one nonlinear Armstrong-Frederick backstress."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .j2_prager_strain_history import J2PragerStrainHistory, _deviator, _elastic_predictor, _q_equivalent, _tensor_inner
from .registry import ModelSpec


MODEL_ID = "fatigue.j2_armstrong_frederick_strain_history"
SOURCE_ID = "caller_single_backstress_armstrong_frederick_parameters"
ALGORITHM_SOURCE_ID = "backward_euler_j2_armstrong_frederick_radial_return"


class J2ArmstrongFrederickStrainHistory(Contract):
    """A sampled strain path plus one caller-calibrated saturating backstress."""

    analysis_id: str = Field(min_length=1)
    base_path: J2PragerStrainHistory
    kinematic_modulus_Pa: float = Field(ge=0)
    dynamic_recovery_per_unit_equivalent_plastic_strain: float = Field(ge=0)
    parameter_source_id: str = SOURCE_ID
    parameter_record_id: str = Field(min_length=1)
    parameter_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameter_evidence_source_id: str = Field(min_length=1)
    parameter_evidence: Evidence
    parameters_and_model_reviewed: bool

    @model_validator(mode="after")
    def validate_parameters_and_base(self):
        if self.base_path.prager_kinematic_modulus_Pa != 0:
            raise ValueError("base_path Prager modulus must be zero; nonlinear AF hardening is supplied separately")
        if self.parameter_source_id != SOURCE_ID:
            raise ValueError("parameter_source_id must identify the caller Armstrong-Frederick calibration")
        if (
            self.parameter_evidence.source_id != self.parameter_evidence_source_id
            or self.parameter_evidence.sha256 != self.parameter_sha256
        ):
            raise ValueError("parameter Evidence must match the declared source ID and digest")
        if self.base_path.evidence.source_id != self.base_path.source_id:
            raise ValueError("base path Evidence must match its declared source ID")
        values = (
            self.kinematic_modulus_Pa,
            self.dynamic_recovery_per_unit_equivalent_plastic_strain,
        )
        if not all(math.isfinite(value) and value >= 0 for value in values):
            raise ValueError("Armstrong-Frederick parameters must be finite and nonnegative")
        return self


def _relative_deviator(stress: list[float], backstress: list[float]) -> list[float]:
    deviator, _ = _deviator(stress)
    return [deviator[i] - backstress[i] for i in range(6)]


def _alpha_update(
    old: list[float], direction: list[float], multiplier: float, modulus: float, recovery: float
) -> list[float]:
    denominator = 1.0 + recovery * multiplier
    return [(old[i] + modulus * multiplier * direction[i]) / denominator for i in range(6)]


def _yield_residual(
    multiplier: float,
    trial_stress: list[float],
    old_backstress: list[float],
    direction: list[float],
    shear_modulus: float,
    yield_stress: float,
    isotropic_modulus: float,
    accumulated_plastic_strain: float,
    kinematic_modulus: float,
    recovery: float,
) -> tuple[float, list[float], list[float]]:
    stress = [trial_stress[i] - 3.0 * shear_modulus * multiplier * direction[i] for i in range(6)]
    backstress = _alpha_update(old_backstress, direction, multiplier, kinematic_modulus, recovery)
    residual = _q_equivalent(_relative_deviator(stress, backstress)) - (
        yield_stress + isotropic_modulus * (accumulated_plastic_strain + multiplier)
    )
    return residual, stress, backstress


def _solve_plastic_multiplier(
    trial_stress: list[float],
    old_backstress: list[float],
    direction: list[float],
    shear_modulus: float,
    yield_stress: float,
    isotropic_modulus: float,
    accumulated: float,
    kinematic_modulus: float,
    recovery: float,
) -> tuple[float, list[float], list[float]] | None:
    f0, _, _ = _yield_residual(
        0.0, trial_stress, old_backstress, direction, shear_modulus, yield_stress,
        isotropic_modulus, accumulated, kinematic_modulus, recovery
    )
    if not math.isfinite(f0) or f0 <= 0:
        return None
    upper = max(f0 / max(3.0 * shear_modulus + isotropic_modulus, 1.0), 1e-16)
    bracketed = False
    for _ in range(100):
        f_upper, _, _ = _yield_residual(
            upper, trial_stress, old_backstress, direction, shear_modulus, yield_stress,
            isotropic_modulus, accumulated, kinematic_modulus, recovery
        )
        if not math.isfinite(f_upper):
            return None
        if f_upper <= 0.0:
            bracketed = True
            break
        upper *= 2.0
        if not math.isfinite(upper) or upper > 1e6:
            return None
    if not bracketed:
        return None
    lower = 0.0
    tolerance = 1e-12 * max(1.0, f0, yield_stress)
    for _ in range(120):
        middle = 0.5 * (lower + upper)
        f_middle, _, _ = _yield_residual(
            middle, trial_stress, old_backstress, direction, shear_modulus, yield_stress,
            isotropic_modulus, accumulated, kinematic_modulus, recovery
        )
        if not math.isfinite(f_middle):
            return None
        if abs(f_middle) <= tolerance or upper - lower <= 1e-14 * max(1.0, middle):
            _, stress, backstress = _yield_residual(
                middle, trial_stress, old_backstress, direction, shear_modulus, yield_stress,
                isotropic_modulus, accumulated, kinematic_modulus, recovery
            )
            return middle, stress, backstress
        if f_middle > 0:
            lower = middle
        else:
            upper = middle
    multiplier = 0.5 * (lower + upper)
    _, stress, backstress = _yield_residual(
        multiplier, trial_stress, old_backstress, direction, shear_modulus, yield_stress,
        isotropic_modulus, accumulated, kinematic_modulus, recovery
    )
    return multiplier, stress, backstress


def evaluate_j2_armstrong_frederick_history(request: J2ArmstrongFrederickStrainHistory) -> Calculation:
    """Integrate each caller strain increment with a backward-Euler radial return."""
    base_request = request.base_path
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": base_request.material_condition_id,
        "input_sha256": digest,
        "base_path_sha256": canonical_digest(base_request.model_dump(mode="json")),
        "parameter_source_id": request.parameter_source_id,
        "parameter_record_id": request.parameter_record_id,
        "parameter_sha256": request.parameter_sha256,
        "parameter_evidence_source_id": request.parameter_evidence_source_id,
        "sample_count": len(base_request.sample_ids),
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "strain_shear_convention": "tensor_shear_strain",
        "constitutive_model": "small_strain_rate_independent_J2_linear_isotropic_single_Armstrong_Frederick_backstress",
        "fatigue_damage_or_life": None,
    }
    if not all((
        request.parameters_and_model_reviewed,
        base_request.tensor_basis_and_order_reviewed,
        base_request.material_model_and_parameters_reviewed,
        base_request.initial_state_at_first_sample_reviewed,
        base_request.small_strain_quasistatic_applicability_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "tensor_material_initial_state_AF_parameter_and_applicability_reviews_required",
            "response_history": None,
        })

    E, nu = base_request.young_modulus_Pa, base_request.poisson_ratio
    shear = E / (2.0 * (1.0 + nu))
    bulk = E / (3.0 * (1.0 - 2.0 * nu))
    if not all(math.isfinite(value) and value > 0 for value in (shear, bulk)):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "elastic_moduli_outside_finite_numeric_support", "response_history": None,
        })

    stress = list(base_request.initial_stress_components_Pa)
    plastic_strain = list(base_request.initial_plastic_strain_components)
    backstress = list(base_request.initial_backstress_components_Pa)
    accumulated = base_request.initial_equivalent_plastic_strain
    initial_q = _q_equivalent(_relative_deviator(stress, backstress))
    initial_yield = base_request.initial_yield_stress_Pa + base_request.isotropic_hardening_modulus_Pa * accumulated
    initial_residual = initial_q - initial_yield
    if not math.isfinite(initial_residual) or initial_residual > 1e-10 * max(1.0, initial_q, initial_yield):
        return Calculation(status="needs_data", values=base | {
            "reason": "initial_stress_state_outside_declared_yield_surface",
            "initial_yield_residual_Pa": initial_residual if math.isfinite(initial_residual) else None,
            "response_history": None,
        })
    response = [{
        "sample_id": base_request.sample_ids[0],
        "stress_tensor_components_Pa": stress[:],
        "plastic_strain_tensor_components": plastic_strain[:],
        "backstress_tensor_components_Pa": backstress[:],
        "equivalent_plastic_strain": accumulated,
        "plastic_multiplier_increment": 0.0,
        "yield_function_residual_Pa": initial_residual,
    }]
    total_work = 0.0
    for index in range(1, len(base_request.sample_ids)):
        strain_increment = [
            base_request.strain_tensor_components[index][j] - base_request.strain_tensor_components[index - 1][j]
            for j in range(6)
        ]
        trial_stress = _elastic_predictor(stress, strain_increment, bulk, shear)
        relative = _relative_deviator(trial_stress, backstress)
        q_trial = _q_equivalent(relative)
        current_yield = base_request.initial_yield_stress_Pa + base_request.isotropic_hardening_modulus_Pa * accumulated
        trial_residual = q_trial - current_yield
        tolerance = 1e-12 * max(1.0, q_trial, current_yield)
        multiplier = 0.0
        if trial_residual > tolerance:
            if q_trial <= 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "plastic_predictor_has_no_resolvable_deviatoric_direction",
                    "failed_interval_sample_ids": [base_request.sample_ids[index - 1], base_request.sample_ids[index]],
                    "response_history": response,
                })
            direction = [value / q_trial for value in relative]
            solved = _solve_plastic_multiplier(
                trial_stress, backstress, direction, shear,
                base_request.initial_yield_stress_Pa,
                base_request.isotropic_hardening_modulus_Pa,
                accumulated, request.kinematic_modulus_Pa,
                request.dynamic_recovery_per_unit_equivalent_plastic_strain,
            )
            if solved is None:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "backward_euler_AF_return_map_could_not_bracket_finite_consistency_root",
                    "failed_interval_sample_ids": [base_request.sample_ids[index - 1], base_request.sample_ids[index]],
                    "response_history": response,
                })
            multiplier, stress, backstress = solved
            plastic_strain = [plastic_strain[j] + 1.5 * multiplier * direction[j] for j in range(6)]
            accumulated += multiplier
        else:
            stress = trial_stress
        residual = _q_equivalent(_relative_deviator(stress, backstress)) - (
            base_request.initial_yield_stress_Pa + base_request.isotropic_hardening_modulus_Pa * accumulated
        )
        segment_work = 0.5 * _tensor_inner(
            [response[-1]["stress_tensor_components_Pa"][j] + stress[j] for j in range(6)], strain_increment
        )
        state_values = [*stress, *plastic_strain, *backstress, accumulated, multiplier, residual, segment_work]
        if not all(math.isfinite(value) for value in state_values):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_inputs_produce_nonfinite_AF_state_update",
                "failed_interval_sample_ids": [base_request.sample_ids[index - 1], base_request.sample_ids[index]],
                "response_history": response,
            })
        total_work += segment_work
        response.append({
            "sample_id": base_request.sample_ids[index],
            "stress_tensor_components_Pa": stress[:],
            "plastic_strain_tensor_components": plastic_strain[:],
            "backstress_tensor_components_Pa": backstress[:],
            "equivalent_plastic_strain": accumulated,
            "plastic_multiplier_increment": multiplier,
            "yield_function_residual_Pa": residual,
        })
    if not math.isfinite(total_work):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "nonfinite_path_work_accumulation", "response_history": response,
        })
    return Calculation(values=base | {
        "status": "computed",
        "response_history": response,
        "final_equivalent_plastic_strain": accumulated,
        "signed_trapezoidal_stress_strain_work_density_J_m3": total_work,
        "hardening_parameters": {
            "initial_yield_stress_Pa": base_request.initial_yield_stress_Pa,
            "isotropic_modulus_Pa": base_request.isotropic_hardening_modulus_Pa,
            "kinematic_modulus_Pa": request.kinematic_modulus_Pa,
            "dynamic_recovery_per_unit_equivalent_plastic_strain": request.dynamic_recovery_per_unit_equivalent_plastic_strain,
        },
        "limitations": [
            "Small-strain, rate-independent, isothermal J2 model with linear isotropic hardening and one Armstrong-Frederick backstress.",
            "Each caller interval uses one backward-Euler radial return; no automatic substepping or multi-backstress Chaboche terms are used.",
            "The caller supplies total-strain knots and the initial stress, plastic strain, backstress and accumulated plastic strain state.",
            "The signed trapezoidal work is not identified as irreversible plastic dissipation; no fatigue damage, life or qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        J2ArmstrongFrederickStrainHistory,
        evaluate_j2_armstrong_frederick_history,
        {
            "response_history[].stress_tensor_components_Pa": "Pa",
            "response_history[].plastic_strain_tensor_components": "1",
            "response_history[].backstress_tensor_components_Pa": "Pa",
            "response_history[].equivalent_plastic_strain": "1",
            "response_history[].yield_function_residual_Pa": "Pa",
            "final_equivalent_plastic_strain": "1",
            "signed_trapezoidal_stress_strain_work_density_J_m3": "J/m^3",
        },
        (
            "Uses a small-strain associative J2 yield surface and one backward-Euler Armstrong-Frederick backstress update per caller strain interval.",
            "Cyclic parameters, initial state, tensor basis and small-strain quasistatic applicability are caller supplied and reviewed.",
            "No rate effects, automatic substepping, multiple backstress components, fatigue damage, life or qualification is provided.",
        ),
        (SOURCE_ID, ALGORITHM_SOURCE_ID),
        qualification="user_model",
    )]
