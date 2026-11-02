"""Synthetic wiring example for the caller-owned multiaxial damage-rate API.

The constant callback is only an API demonstration. It is not a fatigue law,
material calibration, benchmark or validation case.
"""

from matintegrity.models.multiaxial_work_life import ClosedTensorCycle
from matintegrity.contracts import Evidence
from matintegrity.multiaxial_damage_provider import (
    CallerMultiaxialDamageRequest,
    MultiaxialFatigueLawProfile,
    bind_caller_multiaxial_material_law,
    evaluate_caller_multiaxial_damage,
)


def synthetic_constant_rate(time_s, stress6, strain6, stress_rate6, strain_rate6, context):
    """Return a fixed synthetic rate solely to demonstrate the provider contract."""
    _ = (time_s, stress6, strain6, stress_rate6, strain_rate6, context)
    return 1e-3


synthetic_constant_rate.provider_id = "example.synthetic_constant_damage_rate"
synthetic_constant_rate.revision = "example-v1"
synthetic_constant_rate.configuration_sha256 = "c" * 64


def build_request() -> CallerMultiaxialDamageRequest:
    cycle = ClosedTensorCycle(
        cycle_id="synthetic-cycle-001",
        allocated_cycle_count=1.0,
        sample_ids=["sample-0", "sample-1", "sample-2"],
        sample_time_s=[0.0, 0.5, 1.0],
        stress_tensor_components_Pa=[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [10e6, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
        strain_tensor_components=[
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1e-3, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
    )


def bind_synthetic_profile(request):
    evidence = Evidence(
        source_id=synthetic_constant_rate.provider_id,
        origin="synthetic",
        citation="Synthetic calibration metadata fixture for API wiring only.",
        sha256=request.calibration_sha256,
        license_id="synthetic-no-external-data",
    )
    rights_evidence = Evidence(
        source_id="synthetic-example-rights-record",
        origin="synthetic",
        citation="Synthetic rights record; no third-party data or law is included.",
        license_id="synthetic-no-external-data",
    )
    profile = MultiaxialFatigueLawProfile(
        law_id="synthetic-constant-rate-demo",
        law_revision="example-v1",
        provider_id=synthetic_constant_rate.provider_id,
        provider_revision=synthetic_constant_rate.revision,
        provider_configuration_sha256=synthetic_constant_rate.configuration_sha256,
        calibration_id=request.calibration_id,
        calibration_sha256=request.calibration_sha256,
        material_condition_id=request.material_condition_id,
        stress_measure_id="Cauchy-stress-tensor-components",
        stress_unit="Pa",
        stress_component_order=("xx", "yy", "zz", "xy", "yz", "zx"),
        strain_measure_id="infinitesimal-strain-tensor-components",
        strain_unit="dimensionless",
        strain_shear_convention=request.strain_shear_convention,
        stress_component_minimum_Pa=(-1e8,) * 6,
        stress_component_maximum_Pa=(1e8,) * 6,
        strain_component_minimum=(-0.02,) * 6,
        strain_component_maximum=(0.02,) * 6,
        minimum_cycle_duration_s=0.1,
        maximum_cycle_duration_s=10.0,
        minimum_cycle_count=1,
        maximum_cycle_count=100,
        minimum_allocated_repetitions=1.0,
        maximum_allocated_repetitions=1e6,
        supported_time_reconstructions=(
            "piecewise_linear", "piecewise_cubic_hermite", "piecewise_pchip", "piecewise_periodic_cubic_spline"
        ),
        evidence=(evidence,),
        usage_license_id="synthetic-no-external-data",
        usage_rights_evidence=(rights_evidence,),
        tensor_order_and_measurement_definition_reviewed=True,
        calibration_support_and_transfer_reviewed=True,
        material_condition_match_reviewed=True,
        cycle_population_scope_reviewed=True,
        usage_rights_reviewed=True,
        computational_use_authorized=True,
    )
    return bind_caller_multiaxial_material_law(request, synthetic_constant_rate, profile)
    return CallerMultiaxialDamageRequest(
        analysis_id="synthetic-api-wiring-only",
        material_condition_id="synthetic-unqualified-condition",
        location_id="synthetic-location",
        cycles=(cycle,),
        strain_shear_convention="engineering",
        time_reconstruction="piecewise_linear",
        stress_history_source_id="synthetic-stress-history",
        stress_history_sha256="a" * 64,
        strain_history_source_id="synthetic-strain-history",
        strain_history_sha256="b" * 64,
        damage_provider_id=synthetic_constant_rate.provider_id,
        damage_provider_revision=synthetic_constant_rate.revision,
        damage_provider_configuration_sha256=synthetic_constant_rate.configuration_sha256,
        calibration_id="synthetic-rate-contract-only",
        calibration_sha256="d" * 64,
        maximum_closure_stress_error_Pa=0.0,
        maximum_closure_strain_error=0.0,
        quadrature_absolute_tolerance_damage=1e-12,
        quadrature_relative_tolerance=1e-9,
        initial_subinterval_count=1,
        maximum_subinterval_count=16,
        maximum_provider_evaluations=10000,
        quadrature_order=4,
        tensor_basis_and_order_reviewed=True,
        stress_strain_conjugacy_reviewed=True,
        cycle_extraction_and_closure_reviewed=True,
        time_reconstruction_reviewed=True,
        provider_material_applicability_reviewed=True,
        provider_usage_rights_reviewed=True,
        memoryless_deterministic_rate_reviewed=True,
    )


if __name__ == "__main__":
    base_request = build_request()
    print(evaluate_caller_multiaxial_damage(base_request, bind_synthetic_profile(base_request)))
    pchip_request = CallerMultiaxialDamageRequest.model_validate(
        build_request().model_dump(mode="python")
        | {
            "time_reconstruction": "piecewise_pchip",
            # Loose synthetic limits make the endpoint-slope discontinuity visible in output.
            "maximum_closure_stress_rate_error_Pa_s": 1e8,
            "maximum_closure_strain_rate_error_s_inv": 1.0,
        }
    )
    print(evaluate_caller_multiaxial_damage(pchip_request, bind_synthetic_profile(pchip_request)))
    periodic_spline_request = CallerMultiaxialDamageRequest.model_validate(
        build_request().model_dump(mode="python")
        | {
            "time_reconstruction": "piecewise_periodic_cubic_spline",
            "periodic_spline_reviewed": True,
            "maximum_closure_stress_rate_error_Pa_s": 1e-3,
            "maximum_closure_strain_rate_error_s_inv": 1e-12,
        }
    )
    print(evaluate_caller_multiaxial_damage(periodic_spline_request, bind_synthetic_profile(periodic_spline_request)))
