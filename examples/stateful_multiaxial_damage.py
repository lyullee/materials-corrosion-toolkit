"""Synthetic stateful multiaxial damage-provider integration example."""

from matintegrity.models.multiaxial_work_life import ClosedTensorCycle
from matintegrity.multiaxial_damage_provider import (
    CallerStatefulMultiaxialDamageRequest,
    evaluate_caller_stateful_multiaxial_damage,
)


request = CallerStatefulMultiaxialDamageRequest(
    analysis_id="synthetic-stateful-fatigue",
    material_condition_id="synthetic-condition",
    location_id="synthetic-point",
    cycles=(
        ClosedTensorCycle(
            cycle_id="cycle-A",
            allocated_cycle_count=2.0,
            sample_ids=["a0", "a1", "a2"],
            sample_time_s=[0.0, 0.5, 1.0],
            stress_tensor_components_Pa=[[0.0] * 6, [1.0e6, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0] * 6],
            strain_tensor_components=[[0.0] * 6, [1.0e-4, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0] * 6],
        ),
        ClosedTensorCycle(
            cycle_id="cycle-B",
            allocated_cycle_count=1.0,
            sample_ids=["b0", "b1", "b2"],
            sample_time_s=[0.0, 0.5, 1.0],
            stress_tensor_components_Pa=[[0.0] * 6, [1.5e6, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0] * 6],
            strain_tensor_components=[[0.0] * 6, [1.5e-4, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0] * 6],
        ),
    ),
    state_variable_ids=("synthetic_memory",),
    initial_state=(0.0,),
    minimum_state=(0.0,),
    maximum_state=(10.0,),
    strain_shear_convention="engineering",
    time_reconstruction="piecewise_linear",
    stress_history_source_id="synthetic-stress",
    stress_history_sha256="1" * 64,
    strain_history_source_id="synthetic-strain",
    strain_history_sha256="2" * 64,
    damage_provider_id="synthetic-state-law",
    damage_provider_revision="1",
    damage_provider_configuration_sha256="3" * 64,
    calibration_id="synthetic-calibration",
    calibration_sha256="4" * 64,
    maximum_time_step_s=0.05,
    maximum_closure_stress_error_Pa=0.0,
    maximum_closure_strain_error=0.0,
    tensor_basis_and_order_reviewed=True,
    stress_strain_conjugacy_reviewed=True,
    cycle_extraction_and_sequence_order_reviewed=True,
    time_reconstruction_reviewed=True,
    state_initialization_and_bounds_reviewed=True,
    provider_material_applicability_reviewed=True,
    provider_usage_rights_reviewed=True,
    stateful_rate_and_evolution_law_reviewed=True,
)


def synthetic_provider(time_s, stress, strain, dstress, dstrain, state, context):
    """Illustrative state and damage law; not a calibrated fatigue model."""
    strain_amplitude = abs(strain[0])
    return {
        "state_derivative_per_s": (strain_amplitude * 0.1,),
        "damage_rate_per_s": strain_amplitude * (1.0 + state[0]) * 1e-3,
    }


synthetic_provider.provider_id = "synthetic-state-law"
synthetic_provider.revision = "1"
synthetic_provider.configuration_sha256 = "3" * 64

result = evaluate_caller_stateful_multiaxial_damage(request, synthetic_provider)
print({"fixed_step_result": result})

adaptive_request = CallerStatefulMultiaxialDamageRequest.model_validate(
    request.model_dump(mode="python")
    | {
        "integration_method": "adaptive_step_doubling_rk4",
        "minimum_time_step_s": 1e-5,
        "state_absolute_tolerance": 1e-10,
        "state_relative_tolerance": 1e-6,
        "damage_absolute_tolerance": 1e-12,
        "damage_relative_tolerance": 1e-5,
        "maximum_rejected_steps_per_interval": 20,
        "adaptive_integration_controls_reviewed": True,
        "provider_repeat_evaluation_is_deterministic_reviewed": True,
        "periodic_state_absolute_tolerance": 1e-8,
        "periodic_state_relative_tolerance": 1e-5,
        "periodic_state_convergence_reviewed": True,
    }
)
adaptive_result = evaluate_caller_stateful_multiaxial_damage(adaptive_request, synthetic_provider)
print({"adaptive_step_doubling_result": adaptive_result})

pchip_request = CallerStatefulMultiaxialDamageRequest.model_validate(
    request.model_dump(mode="python")
    | {
        "time_reconstruction": "piecewise_pchip",
        # Loose synthetic limits expose the derived start/end rate mismatch.
        "maximum_closure_stress_rate_error_Pa_s": 1e8,
        "maximum_closure_strain_rate_error_s_inv": 1.0,
    }
)
print({"pchip_path_result": evaluate_caller_stateful_multiaxial_damage(pchip_request, synthetic_provider)})

periodic_spline_request = CallerStatefulMultiaxialDamageRequest.model_validate(
    request.model_dump(mode="python")
    | {
        "time_reconstruction": "piecewise_periodic_cubic_spline",
        "periodic_spline_reviewed": True,
        "maximum_closure_stress_rate_error_Pa_s": 1e-3,
        "maximum_closure_strain_rate_error_s_inv": 1e-12,
    }
)
print({"periodic_spline_path_result": evaluate_caller_stateful_multiaxial_damage(periodic_spline_request, synthetic_provider)})
