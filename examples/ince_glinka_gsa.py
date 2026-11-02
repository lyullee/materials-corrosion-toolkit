"""Synthetic single-cycle example for the caller-input GSA calculator."""

from hashlib import sha256

from matintegrity.contracts import Evidence
from matintegrity.models.fatigue import CriticalPlaneCandidate
from matintegrity.models.ince_glinka_gsa import (
    InceGlinkaGSACalculation,
    ince_glinka_gsa_parameter,
)


fixture_hash = sha256(b"project-authored synthetic GSA fixture v1").hexdigest()
request = InceGlinkaGSACalculation(
    assessment_id="synthetic-gsa-example",
    physical_scope_id="synthetic-coupon",
    material_condition_id="synthetic-condition",
    location_id="synthetic-location",
    source_provider_id="synthetic-gsa-inputs",
    source_provider_revision="example-v1",
    configuration_sha256=fixture_hash,
    sample_ids=("cycle-start", "positive-peak", "negative-peak", "cycle-end"),
    stress_tensor_components_Pa=(
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 50e6, 0.0, 0.0, 100e6],
        [0.0, 0.0, 30e6, 0.0, 0.0, -100e6],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ),
    elastic_strain_tensor_components=(
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 2.5e-4, 0.0, 0.0, 5e-4],
        [0.0, 0.0, 1.5e-4, 0.0, 0.0, -5e-4],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ),
    plastic_strain_tensor_components=(
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1e-5, 0.0, 0.0, 1e-4],
        [0.0, 0.0, -1e-5, 0.0, 0.0, -1e-4],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ),
    candidate_planes=(CriticalPlaneCandidate(
        plane_id="xy-plane-x-shear",
        normal=[0.0, 0.0, 1.0],
        in_plane_direction=[1.0, 0.0, 0.0],
    ),),
    shear_fatigue_strength_coefficient_Pa=300e6,
    axial_fatigue_strength_coefficient_Pa=800e6,
    maximum_stress_closure_error_Pa=1.0,
    maximum_elastic_strain_closure_error=1e-12,
    maximum_plastic_strain_closure_error=1e-12,
    representative_cycle_and_tensor_convention_reviewed=True,
    elastic_plastic_decomposition_reviewed=True,
    plane_grid_support_reviewed=True,
    material_parameter_basis_and_units_reviewed=True,
    source_use_rights_reviewed=True,
    computational_use_authorized=True,
    evidence=(Evidence(
        source_id="synthetic-gsa-inputs",
        origin="synthetic",
        citation="Project-authored synthetic example only; not experimental evidence",
        sha256=fixture_hash,
    ),),
)

result = ince_glinka_gsa_parameter(request)

if __name__ == "__main__":
    print(result.model_dump(mode="json"))
