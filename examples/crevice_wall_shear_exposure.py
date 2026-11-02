"""Synthetic composition of a slit-flow result and wall-shear descriptor."""

from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.models.crevice_wall_shear_exposure import CreviceWallShearExposure
from matintegrity.registry import default_registry

geometry_evidence = Evidence(
    source_id="synthetic-crevice-geometry",
    origin="synthetic",
    citation="Synthetic geometry wiring only; no experimental geometry is claimed.",
    sha256="1" * 64,
)
pressure_evidence = Evidence(
    source_id="synthetic-pressure-history",
    origin="synthetic",
    citation="Synthetic pressure wiring only; no operating data is claimed.",
    sha256="2" * 64,
)
fluid_evidence = Evidence(
    source_id="synthetic-fluid-properties",
    origin="synthetic",
    citation="Synthetic fluid-property wiring only; no recommended property is claimed.",
    sha256="3" * 64,
)
rights_evidence = Evidence(
    source_id="synthetic-input-rights",
    origin="user_declared",
    citation="Illustration assumes the caller has rights to compute with their input values.",
    license_id="caller_authorized_synthetic_example",
)
context = RunContext(
    asset_id="synthetic-loop",
    location_id="synthetic-crevice",
    time_basis="elapsed_seconds",
    evidence=(geometry_evidence, pressure_evidence, fluid_evidence, rights_evidence),
)

hydraulic_inputs = {
    "assessment_id": "synthetic-slit-flow",
    "asset_id": "synthetic-loop",
    "location_id": "synthetic-crevice",
    "physical_scope_id": "synthetic-scope",
    "time_basis": "elapsed_seconds",
    "time_s": (0.0, 30.0, 60.0),
    "cell_ids": ("inlet", "middle", "tip"),
    "cell_widths_m": (0.004, 0.004, 0.004),
    "aperture_by_interval_m": ((2e-5, 1.5e-5, 1e-5), (2e-5, 1.5e-5, 1e-5)),
    "transverse_width_m": 0.01,
    "pressure_drop_by_interval_Pa": (120.0, -30.0),
    "initial_volumetric_flow_m3_s": 0.0,
    "density_kg_m3": 998.0,
    "dynamic_viscosity_Pa_s": 1.0e-3,
    "geometry_provider_id": "synthetic-crevice-geometry",
    "geometry_provider_revision": "1",
    "geometry_record_sha256": "1" * 64,
    "pressure_provider_id": "synthetic-pressure-history",
    "pressure_provider_revision": "1",
    "pressure_record_sha256": "2" * 64,
    "fluid_property_provider_id": "synthetic-fluid-properties",
    "fluid_property_provider_revision": "1",
    "fluid_property_record_sha256": "3" * 64,
    "evidence": (geometry_evidence, pressure_evidence, fluid_evidence),
    "usage_rights_evidence": (rights_evidence,),
    "usage_license_id": "caller_authorized_synthetic_example",
    "geometry_clock_and_grid_reviewed": True,
    "pressure_reference_sign_and_clock_reviewed": True,
    "incompressible_newtonian_property_support_reviewed": True,
    "wide_slit_aspect_ratio_reviewed": True,
    "laminar_fully_developed_resistance_reviewed": True,
    "unsteady_lumped_inertance_applicability_reviewed": True,
    "signed_flow_reversal_reviewed": True,
    "usage_rights_reviewed": True,
    "computational_use_authorized": True,
}
registry = default_registry()
hydraulic_result = registry.run(
    "corrosion.planar_slit_transient_hydraulic_history", hydraulic_inputs, context,
)
wall_shear_input = CreviceWallShearExposure(
    assessment_id="synthetic-wall-shear-exposure",
    hydraulic_result=hydraulic_result,
    hydraulic_result_sha256=canonical_digest(hydraulic_result.model_dump(mode="json")),
    wall_shear_relation_and_wide_slit_profile_reviewed=True,
    quasi_steady_wall_shear_on_lumped_flow_reviewed=True,
    shear_exposure_is_descriptor_only_reviewed=True,
    computational_use_authorized=True,
)
wall_shear_result = registry.run(
    "corrosion.crevice_wall_shear_exposure", wall_shear_input, context,
)
print(wall_shear_result.model_dump_json(indent=2))
