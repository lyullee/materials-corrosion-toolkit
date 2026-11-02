"""Create and summarize a visual-examination record directly with Python objects."""

from matintegrity.contracts import Evidence
from matintegrity.models.inspection import (
    VisualExaminationArea,
    VisualSurfaceExamination,
    VisualSurfaceIndication,
    visual_surface_summary,
)

record = Evidence(
    source_id="user-visual-record",
    origin="user_declared",
    citation="replace with the controlled examination record",
)
request = VisualSurfaceExamination(
    examination_id="visual-001",
    procedure_id="user-visual-procedure",
    procedure_revision="1",
    examination_mode="direct",
    surface_condition="clean dry metal surface",
    surface_preparation="replace with the recorded preparation",
    illumination_basis="replace with the controlled illumination record",
    resolution_check_basis="replace with the controlled resolution check",
    areas=[
        VisualExaminationArea(
            area_id="area-a",
            physical_location_id="weld-a",
            target_area_m2=1.0,
            examined_area_m2=0.8,
            unexamined_basis="support footprint",
        )
    ],
    indications=[
        VisualSurfaceIndication(
            indication_id="feature-1",
            area_id="area-a",
            physical_location_id="weld-a-clock-3",
            indication_type="linear surface feature",
            location_description="user datum plus 0.2 m",
            measured_length_m=0.01,
            evidence=[record],
        )
    ],
    areas_mutually_exclusive_reviewed=True,
    coverage_reviewed=True,
    surface_condition_reviewed=True,
    indication_mapping_reviewed=True,
    evidence=[record],
)

print(visual_surface_summary(request).model_dump_json(indent=2))
