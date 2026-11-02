"""Synthetic pressure-driven slit-flow example with prescribed aperture closure."""
from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.crevice_moving_volume_hydraulic_history import (
    CreviceMovingVolumeHydraulicHistoryRequest,
    evaluate_crevice_moving_volume_hydraulic_history,
)

assessment_id = "synthetic-moving-hydraulic-demo"
physical_scope_id = "synthetic-two-cell-slit"
time_s = (0.0, 10.0)
cell_ids = ("cell-1", "cell-2")
lengths_m = (0.1, 0.1)
widths_m = (0.05, 0.05)
aperture = ((1.0e-3, 1.0e-3), (0.95e-3, 0.95e-3))
pressure_drop = (100.0,)
geometry_record = {
    "assessment_id": assessment_id,
    "physical_scope_id": physical_scope_id,
    "time_s": list(time_s),
    "cell_ids": list(cell_ids),
    "cell_lengths_m": list(lengths_m),
    "cell_widths_m": list(widths_m),
    "aperture_m_by_knot_and_cell": [list(row) for row in aperture],
}
pressure_record = {
    "physical_scope_id": physical_scope_id,
    "time_s": list(time_s),
    "pressure_drop_Pa_by_interval": list(pressure_drop),
}
geometry_sha = canonical_digest(geometry_record)
pressure_sha = canonical_digest(pressure_record)
request = CreviceMovingVolumeHydraulicHistoryRequest(
    assessment_id=assessment_id,
    physical_scope_id=physical_scope_id,
    time_s=time_s,
    cell_ids=cell_ids,
    cell_lengths_m=lengths_m,
    cell_widths_m=widths_m,
    aperture_m_by_knot_and_cell=aperture,
    pressure_drop_Pa_by_interval=pressure_drop,
    initial_left_boundary_flow_m3_s=0.0,
    density_kg_m3=998.0,
    dynamic_viscosity_Pa_s=1.0e-3,
    geometry_sha256=geometry_sha,
    pressure_sha256=pressure_sha,
    evidence=(
        Evidence(source_id="synthetic_geometry", origin="synthetic", citation="Synthetic example geometry.", license_id="synthetic-example", sha256=geometry_sha),
        Evidence(source_id="synthetic_pressure", origin="synthetic", citation="Synthetic example pressure forcing.", license_id="synthetic-example", sha256=pressure_sha),
    ),
    geometry_and_volume_history_reviewed=True,
    pressure_reference_and_sign_reviewed=True,
    incompressible_newtonian_fluid_reviewed=True,
    wide_laminar_slit_resistance_and_inertance_reviewed=True,
    computational_use_authorized=True,
)
result = evaluate_crevice_moving_volume_hydraulic_history(request)
print(result.model_dump_json(indent=2))
