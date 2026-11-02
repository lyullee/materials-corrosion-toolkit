"""Small-strain J2 elastoplastic stress update for a sampled 3D strain path."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec


class J2PragerStrainHistory(Contract):
    """Rate-independent J2 response with linear isotropic and Prager hardening."""

    analysis_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: Evidence
    sample_ids: list[str] = Field(min_length=2, max_length=10000)
    strain_tensor_components: list[list[float]] = Field(min_length=2, max_length=10000)
    initial_stress_components_Pa: list[float] = Field(min_length=6, max_length=6)
    initial_plastic_strain_components: list[float] = Field(min_length=6, max_length=6)
    initial_backstress_components_Pa: list[float] = Field(min_length=6, max_length=6)
    initial_equivalent_plastic_strain: float = Field(ge=0)
    young_modulus_Pa: Positive
    poisson_ratio: float = Field(gt=-1, lt=0.5)
    initial_yield_stress_Pa: Positive
    isotropic_hardening_modulus_Pa: float = Field(ge=0)
    prager_kinematic_modulus_Pa: float = Field(ge=0)
    tensor_basis_and_order_reviewed: bool
    material_model_and_parameters_reviewed: bool
    initial_state_at_first_sample_reviewed: bool
    small_strain_quasistatic_applicability_reviewed: bool

    @model_validator(mode="after")
    def validate_input_alignment_and_lineage(self):
        if len(self.sample_ids) != len(self.strain_tensor_components):
            raise ValueError("sample IDs and total-strain tensors must align")
        if len(set(self.sample_ids)) != len(self.sample_ids):
            raise ValueError("sample IDs must be unique and preserve caller path order")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("strain tensors need six [xx, yy, zz, xy, yz, zx] components")
        all_values = (
            *(value for row in self.strain_tensor_components for value in row),
            *self.initial_stress_components_Pa,
            *self.initial_plastic_strain_components,
            *self.initial_backstress_components_Pa,
            self.initial_equivalent_plastic_strain,
            self.young_modulus_Pa,
            self.poisson_ratio,
            self.initial_yield_stress_Pa,
            self.isotropic_hardening_modulus_Pa,
            self.prager_kinematic_modulus_Pa,
        )
        if not all(math.isfinite(value) for value in all_values):
            raise ValueError("all input tensors and material parameters must be finite")
        for label, tensor in (
            ("initial plastic strain", self.initial_plastic_strain_components),
            ("initial backstress", self.initial_backstress_components_Pa),
        ):
            trace = tensor[0] + tensor[1] + tensor[2]
            scale = max(1.0, *(abs(value) for value in tensor))
            if abs(trace) > 1e-10 * scale:
                raise ValueError(f"{label} must be deviatoric")
        if self.evidence.source_id != self.source_id or self.evidence.sha256 != self.source_sha256:
            raise ValueError("material Evidence must match the declared source and digest")
        return self


def _deviator(tensor: list[float]) -> tuple[list[float], float]:
    mean = (tensor[0] + tensor[1] + tensor[2]) / 3.0
    return [tensor[0] - mean, tensor[1] - mean, tensor[2] - mean, tensor[3], tensor[4], tensor[5]], mean


def _tensor_inner(left: list[float], right: list[float]) -> float:
    return math.fsum(left[i] * right[i] for i in range(3)) + 2.0 * math.fsum(left[i] * right[i] for i in range(3, 6))


def _q_equivalent(deviatoric: list[float]) -> float:
    return math.sqrt(max(0.0, 1.5 * _tensor_inner(deviatoric, deviatoric)))


def _elastic_predictor(
    previous_stress: list[float], strain_increment: list[float], bulk_modulus: float, shear_modulus: float
) -> list[float]:
    delta_dev, delta_mean = _deviator(strain_increment)
    return [
        previous_stress[index] + 2.0 * shear_modulus * delta_dev[index] + (3.0 * bulk_modulus * delta_mean if index < 3 else 0.0)
        for index in range(6)
    ]


def evaluate_j2_prager_strain_history(request: J2PragerStrainHistory) -> Calculation:
    """Integrate one caller-ordered strain path by an incremental radial return."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "analysis_id": request.analysis_id,
        "material_condition_id": request.material_condition_id,
        "source_id": request.source_id,
        "source_sha256": request.source_sha256,
        "input_sha256": digest,
        "sample_count": len(request.sample_ids),
        "tensor_component_order": ["xx", "yy", "zz", "xy", "yz", "zx"],
        "strain_shear_convention": "tensor_shear_strain",
        "constitutive_model": "small_strain_associative_J2_linear_isotropic_plus_Prager_kinematic_hardening",
        "fatigue_damage_or_life": None,
    }
    if not all((
        request.tensor_basis_and_order_reviewed,
        request.material_model_and_parameters_reviewed,
        request.initial_state_at_first_sample_reviewed,
        request.small_strain_quasistatic_applicability_reviewed,
    )):
        return Calculation(status="needs_data", values=base | {
            "reason": "tensor_basis_material_initial_state_and_applicability_reviews_required",
            "response_history": None,
        })

    E, nu = request.young_modulus_Pa, request.poisson_ratio
    shear = E / (2.0 * (1.0 + nu))
    bulk = E / (3.0 * (1.0 - 2.0 * nu))
    if not all(math.isfinite(value) and value > 0 for value in (shear, bulk)):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "elastic_moduli_outside_finite_numeric_support", "response_history": None,
        })

    stress = list(request.initial_stress_components_Pa)
    plastic_strain = list(request.initial_plastic_strain_components)
    backstress = list(request.initial_backstress_components_Pa)
    accumulated = request.initial_equivalent_plastic_strain
    initial_dev, _ = _deviator(stress)
    initial_relative = [initial_dev[i] - backstress[i] for i in range(6)]
    initial_residual = _q_equivalent(initial_relative) - (
        request.initial_yield_stress_Pa + request.isotropic_hardening_modulus_Pa * accumulated
    )
    initial_scale = max(1.0, request.initial_yield_stress_Pa, _q_equivalent(initial_relative))
    if not math.isfinite(initial_residual) or initial_residual > 1e-10 * initial_scale:
        return Calculation(status="needs_data", values=base | {
            "reason": "initial_stress_state_outside_declared_yield_surface",
            "initial_yield_residual_Pa": initial_residual if math.isfinite(initial_residual) else None,
            "response_history": None,
        })

    response = [{
        "sample_id": request.sample_ids[0],
        "stress_tensor_components_Pa": stress[:],
        "plastic_strain_tensor_components": plastic_strain[:],
        "backstress_tensor_components_Pa": backstress[:],
        "equivalent_plastic_strain": accumulated,
        "plastic_multiplier_increment": 0.0,
        "von_mises_equivalent_stress_Pa": _q_equivalent(initial_dev),
        "yield_equivalent_stress_Pa": _q_equivalent(initial_relative),
        "yield_function_residual_Pa": initial_residual,
    }]
    total_work = 0.0
    for index in range(1, len(request.sample_ids)):
        previous_strain = request.strain_tensor_components[index - 1]
        current_strain = request.strain_tensor_components[index]
        strain_increment = [current_strain[j] - previous_strain[j] for j in range(6)]
        trial_stress = _elastic_predictor(stress, strain_increment, bulk, shear)
        trial_dev, _ = _deviator(trial_stress)
        relative = [trial_dev[j] - backstress[j] for j in range(6)]
        q_trial = _q_equivalent(relative)
        current_yield = request.initial_yield_stress_Pa + request.isotropic_hardening_modulus_Pa * accumulated
        yield_trial = q_trial - current_yield
        tolerance = 1e-12 * max(1.0, q_trial, current_yield)
        multiplier = 0.0
        if yield_trial > tolerance:
            denominator = 3.0 * shear + request.isotropic_hardening_modulus_Pa + request.prager_kinematic_modulus_Pa
            multiplier = yield_trial / denominator
            direction = [value / q_trial for value in relative]
            stress = [trial_stress[j] - 3.0 * shear * multiplier * direction[j] for j in range(6)]
            backstress = [backstress[j] + request.prager_kinematic_modulus_Pa * multiplier * direction[j] for j in range(6)]
            plastic_strain = [plastic_strain[j] + 1.5 * multiplier * direction[j] for j in range(6)]
            accumulated += multiplier
        else:
            stress = trial_stress
        stress_dev, _ = _deviator(stress)
        corrected_relative = [stress_dev[j] - backstress[j] for j in range(6)]
        q_corrected = _q_equivalent(corrected_relative)
        q_stress = _q_equivalent(stress_dev)
        residual = q_corrected - (request.initial_yield_stress_Pa + request.isotropic_hardening_modulus_Pa * accumulated)
        segment_work = 0.5 * _tensor_inner(
            [response[-1]["stress_tensor_components_Pa"][j] + stress[j] for j in range(6)],
            strain_increment,
        )
        intermediates = [*stress, *plastic_strain, *backstress, accumulated, multiplier, residual, segment_work, q_stress, q_corrected]
        if not all(math.isfinite(value) for value in intermediates):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_inputs_produce_nonfinite_constitutive_update",
                "failed_interval_sample_ids": [request.sample_ids[index - 1], request.sample_ids[index]],
                "response_history": response,
            })
        total_work += segment_work
        response.append({
            "sample_id": request.sample_ids[index],
            "stress_tensor_components_Pa": stress[:],
            "plastic_strain_tensor_components": plastic_strain[:],
            "backstress_tensor_components_Pa": backstress[:],
            "equivalent_plastic_strain": accumulated,
            "plastic_multiplier_increment": multiplier,
            "von_mises_equivalent_stress_Pa": q_stress,
            "yield_equivalent_stress_Pa": q_corrected,
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
        "hardening_parameters_Pa": {
            "initial_yield_stress": request.initial_yield_stress_Pa,
            "isotropic_modulus": request.isotropic_hardening_modulus_Pa,
            "Prager_kinematic_modulus": request.prager_kinematic_modulus_Pa,
        },
        "limitations": [
            "Small-strain, rate-independent, isothermal associative J2 model with linear isotropic and Prager kinematic hardening only.",
            "The caller supplies the initial state and ordered total-strain knots; each interval uses one backward-Euler radial return without adaptive substepping.",
            "No nonproportional additional hardening, cyclic softening, damage, crack initiation, rainflow, fatigue life or material qualification is modeled.",
            "The signed work is trapezoidal over knot stresses and increments; it is not identified as irreversible plastic dissipation.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fatigue.j2_prager_strain_history",
        J2PragerStrainHistory,
        evaluate_j2_prager_strain_history,
        {
            "response_history[].stress_tensor_components_Pa": "Pa",
            "response_history[].plastic_strain_tensor_components": "1",
            "response_history[].backstress_tensor_components_Pa": "Pa",
            "response_history[].equivalent_plastic_strain": "1",
            "response_history[].von_mises_equivalent_stress_Pa": "Pa",
            "response_history[].yield_equivalent_stress_Pa": "Pa",
            "response_history[].yield_function_residual_Pa": "Pa",
            "signed_trapezoidal_stress_strain_work_density_J_m3": "J/m^3",
        },
        (
            "Six-component tensors use [xx, yy, zz, xy, yz, zx] order with tensor shear strain coordinates.",
            "Material parameters and the state at the first sample are caller supplied and require matching material applicability review.",
            "The constitutive response is not a fatigue damage, life, acceptance or qualification model.",
        ),
        ("small_strain_j2_associative_return_mapping_with_linear_prager_kinematic_and_isotropic_hardening",),
        qualification="user_model",
    )]
