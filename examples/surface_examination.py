"""Build penetrant and magnetic-particle records directly with Python objects."""

import math

from matintegrity.contracts import Evidence
from matintegrity.models.surface_examination import (
    LiquidPenetrantExamination,
    MagneticParticleExamination,
    MagnetizationPass,
    SurfaceExaminationArea,
    liquid_penetrant_summary,
    magnetic_particle_summary,
)

record = Evidence(
    source_id="user-surface-record",
    origin="user_declared",
    citation="replace with the controlled examination record",
)
area = SurfaceExaminationArea(
    area_id="area-a",
    physical_location_id="weld-a",
    target_area_m2=1.0,
    examined_area_m2=1.0,
)

penetrant = LiquidPenetrantExamination(
    examination_id="pt-001",
    procedure_id="user-pt-procedure",
    procedure_revision="1",
    penetrant_type="visible",
    removal_method="solvent_removable",
    cleaner_batch_id="cleaner-1",
    penetrant_batch_id="penetrant-1",
    remover_or_emulsifier_batch_id="remover-1",
    developer_batch_id="developer-1",
    surface_material_id="material-1",
    surface_condition="clean dry surface",
    precleaning_basis="replace with controlled record",
    drying_basis="replace with controlled record",
    examination_temperature_K=295.15,
    penetrant_dwell_s=600.0,
    excess_removal_basis="replace with controlled record",
    developer_application_basis="replace with controlled record",
    development_time_s=600.0,
    observation_lighting_basis="replace with controlled record",
    final_cleaning_basis="replace with controlled record",
    areas=[area],
    areas_mutually_exclusive_reviewed=True,
    material_and_consumables_compatibility_reviewed=True,
    process_sequence_reviewed=True,
    temperature_and_times_reviewed=True,
    surface_condition_reviewed=True,
    indication_mapping_reviewed=True,
    negative_result_reviewed=True,
    evidence=[record],
)

magnetic = MagneticParticleExamination(
    examination_id="mt-001",
    procedure_id="user-mt-procedure",
    procedure_revision="1",
    surface_material_id="ferromagnetic-material-1",
    surface_condition="clean dry surface",
    particle_medium="wet_fluorescent",
    particle_batch_id="particles-1",
    carrier_batch_id="carrier-1",
    observation_lighting_basis="replace with controlled record",
    minimum_direction_separation_rad=math.pi / 3,
    directional_coverage_requirement_basis="replace with approved user requirement",
    areas=[area],
    magnetization_passes=[
        MagnetizationPass(
            pass_id="pass-0",
            area_id="area-a",
            technique="yoke",
            current_mode="ac",
            field_direction_rad=0.0,
            field_adequacy_basis="replace with controlled field record",
            equipment_id="yoke-1",
        ),
        MagnetizationPass(
            pass_id="pass-90",
            area_id="area-a",
            technique="yoke",
            current_mode="ac",
            field_direction_rad=math.pi / 2,
            field_adequacy_basis="replace with controlled field record",
            equipment_id="yoke-1",
        ),
    ],
    areas_mutually_exclusive_reviewed=True,
    ferromagnetic_applicability_reviewed=True,
    equipment_and_media_reviewed=True,
    field_adequacy_reviewed=True,
    directional_requirement_reviewed=True,
    surface_condition_reviewed=True,
    indication_mapping_reviewed=True,
    negative_result_reviewed=True,
    evidence=[record],
)

print(liquid_penetrant_summary(penetrant).model_dump_json(indent=2))
print(magnetic_particle_summary(magnetic).model_dump_json(indent=2))
