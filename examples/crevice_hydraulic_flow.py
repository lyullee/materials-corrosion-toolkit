"""Synthetic shape only: steady slit hydraulics feeding restricted transport."""

from matintegrity.crevice_geometry import (
    PlanarSlitApertureHistory,
    PlanarSlitHydraulicFlow,
    PlanarSlitHydraulicHistory,
    evaluate_planar_slit_hydraulic_flow,
    planar_slit_aperture_history,
)
from matintegrity.contracts import canonical_digest
from matintegrity import bind_planar_slit_hydraulic_history_series
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.restricted_transport import RestrictedTransportRequest


request = PlanarSlitHydraulicFlow(
    flow_id="synthetic-crevice-flow",
    geometry_source_sha256="a" * 64,
    cell_widths_m=(0.01, 0.01, 0.02),
    cell_aperture_m=(100e-6, 80e-6, 60e-6),
    transverse_width_m=0.01,
    fluid_property_source_sha256="c" * 64,
    pressure_drop_Pa=1000.0,
    dynamic_viscosity_Pa_s=1e-3,
    density_kg_m3=1000.0,
    geometry_and_boundary_pressures_reviewed=True,
    incompressible_newtonian_fluid_properties_reviewed=True,
    laminar_fully_developed_slit_assumption_reviewed=True,
)

result = evaluate_planar_slit_hydraulic_flow(request)
print(result)

aperture_history_request = PlanarSlitApertureHistory(
    geometry_id="synthetic-crevice-geometry-history",
    geometry_source_sha256="a" * 64,
    wall_loss_source_sha256="b" * 64,
    cell_widths_m=(0.01, 0.01, 0.02),
    initial_cell_aperture_m=(100e-6, 80e-6, 60e-6),
    transverse_width_m=0.01,
    reference_cross_section_m2=1e-6,
    reactive_broad_face_count=1,
    elapsed_time_s=(0.0, 10.0),
    cumulative_signed_cell_average_recession_m=(
        (0.0, 0.0, 0.0),
        (2e-6, 1e-6, 0.0),
    ),
    supported_minimum_aperture_m=20e-6,
    supported_maximum_aperture_m=200e-6,
    wall_recession_is_per_combined_reactive_area_reviewed=True,
    cell_center_to_face_mapping_reviewed=True,
    geometry_basis_reviewed=True,
)
aperture_history_result = planar_slit_aperture_history(aperture_history_request)
flow_history_request = PlanarSlitHydraulicHistory(
    flow_history_id="synthetic-crevice-flow-history",
    aperture_history_result=aperture_history_result,
    aperture_history_source_sha256=canonical_digest(aperture_history_result),
    pressure_history_source_sha256="d" * 64,
    pressure_drop_Pa=(1000.0, 1200.0),
    fluid_property_source_sha256="c" * 64,
    dynamic_viscosity_Pa_s=1e-3,
    density_kg_m3=1000.0,
    geometry_and_boundary_pressures_reviewed=True,
    incompressible_newtonian_fluid_properties_reviewed=True,
    laminar_fully_developed_slit_assumption_reviewed=True,
    pressure_history_and_geometry_time_alignment_reviewed=True,
)
registry = default_registry()
context = RunContext(
    asset_id="synthetic-asset",
    location_id="synthetic-crevice",
    time_basis="synthetic-elapsed-seconds",
)
flow_history_assessment = registry.run(
    "corrosion.planar_slit_hydraulic_history",
    flow_history_request,
    context,
)
print(flow_history_assessment.model_dump(mode="json"))

# Bind the first steady snapshot to a local 0–10 s fixed-geometry transport
# segment. No transport calculation is run by this adapter call.
transport_template = RestrictedTransportRequest(
    simulation_id="synthetic-transport-segment-0",
    species_ids=("Tracer",),
    length_m=0.04,
    cell_count=3,
    diffusivity_m2_s=(1e-9,),
    initial_concentration_mol_m3=((1.0, 1.0, 1.0),),
    mouth_concentration_mol_m3=(1.0,),
    output_times_s=(0.0, 10.0),
    reaction_provider_id="synthetic-no-reaction",
    reaction_configuration_sha256="e" * 64,
    geometry_diffusion_reaction_basis_reviewed=True,
    axial_advection_and_flow_continuity_reviewed=True,
)
bound_transport_requests = bind_planar_slit_hydraulic_history_series(
    (transport_template,),
    flow_history_assessment,
    canonical_digest(flow_history_assessment.model_dump(mode="json")),
)
print("transport requests bound to adjacent hydraulic snapshots:")
for bound_request in bound_transport_requests:
    print(bound_request.model_dump_json(indent=2))
