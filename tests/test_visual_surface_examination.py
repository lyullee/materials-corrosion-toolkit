import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.inspection import VisualSurfaceExamination, visual_surface_summary
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "user-visual-record",
    "origin": "user_declared",
    "citation": "caller-controlled visual examination record",
}


def _inputs(**updates):
    values = {
        "examination_id": "visual-001",
        "procedure_id": "user-vt-procedure",
        "procedure_revision": "3",
        "examination_mode": "direct",
        "surface_condition": "clean dry metal surface",
        "surface_preparation": "caller-recorded cleaning",
        "illumination_basis": "caller-controlled illumination record",
        "resolution_check_basis": "caller-controlled resolution check",
        "areas": [
            {
                "area_id": "area-a",
                "physical_location_id": "weld-a",
                "target_area_m2": 2.0,
                "examined_area_m2": 1.5,
                "unexamined_basis": "insulated support footprint",
            },
            {
                "area_id": "area-b",
                "physical_location_id": "weld-b",
                "target_area_m2": 1.0,
                "examined_area_m2": 1.0,
            },
        ],
        "indications": [
            {
                "indication_id": "indication-1",
                "area_id": "area-a",
                "physical_location_id": "weld-a-clock-3",
                "indication_type": "linear surface feature",
                "location_description": "caller datum plus 0.2 m",
                "measured_length_m": 0.012,
                "measured_width_m": 0.001,
                "evidence": [EVIDENCE],
            },
            {
                "indication_id": "indication-2",
                "area_id": "area-b",
                "physical_location_id": "weld-b-clock-9",
                "indication_type": "rounded surface feature",
                "location_description": "caller datum plus 0.1 m",
                "evidence": [EVIDENCE],
            },
        ],
        "areas_mutually_exclusive_reviewed": True,
        "coverage_reviewed": True,
        "surface_condition_reviewed": True,
        "indication_mapping_reviewed": True,
        "negative_result_reviewed": False,
        "evidence": [EVIDENCE],
    }
    values.update(updates)
    return values


def test_visual_summary_preserves_coverage_and_reported_indications():
    result = visual_surface_summary(VisualSurfaceExamination.model_validate(_inputs()))
    assert result.status == "computed"
    assert result.values["coverage_fraction"] == pytest.approx(2.5 / 3.0)
    assert result.values["unexamined_area_m2"] == pytest.approx(0.5)
    assert result.values["incomplete_area_ids"] == ["area-a"]
    assert result.values["indication_count"] == 2
    assert result.values["indication_counts_by_reported_type"] == {
        "linear surface feature": 1,
        "rounded surface feature": 1,
    }
    assert result.values["maximum_reported_indication_length_m"] == pytest.approx(0.012)


def test_missing_review_is_needs_data_without_discarding_observations():
    result = visual_surface_summary(VisualSurfaceExamination.model_validate(_inputs(coverage_reviewed=False)))
    assert result.status == "needs_data"
    assert result.values["indication_count"] == 2
    assert result.values["missing_reviews"] == ["coverage_reviewed"]


def test_empty_indication_record_requires_reviewed_negative_statement():
    pending = visual_surface_summary(VisualSurfaceExamination.model_validate(_inputs(indications=[])))
    assert pending.status == "needs_data"
    completed = visual_surface_summary(
        VisualSurfaceExamination.model_validate(_inputs(indications=[], negative_result_reviewed=True))
    )
    assert completed.status == "computed"
    assert completed.values["indication_count"] == 0
    assert completed.values["maximum_reported_indication_length_m"] is None


@pytest.mark.parametrize(
    "updates",
    [
        {
            "areas": [
                {
                    "area_id": "area-a",
                    "physical_location_id": "weld-a",
                    "target_area_m2": 1.0,
                    "examined_area_m2": 1.1,
                }
            ]
        },
        {
            "areas": [
                {
                    "area_id": "area-a",
                    "physical_location_id": "weld-a",
                    "target_area_m2": 1.0,
                    "examined_area_m2": 0.5,
                }
            ]
        },
        {"areas": [_inputs()["areas"][0], _inputs()["areas"][0]]},
        {
            "indications": [
                {
                    **_inputs()["indications"][0],
                    "area_id": "unknown-area",
                }
            ]
        },
    ],
)
def test_visual_contract_rejects_area_and_mapping_errors(updates):
    with pytest.raises(ValidationError):
        VisualSurfaceExamination.model_validate(_inputs(**updates))


def test_registry_route_has_no_probability_or_acceptance_semantics():
    result = default_registry().run(
        "inspection.visual_surface_summary",
        _inputs(),
        RunContext(asset_id="asset-1", location_id="welds", time_basis="inspection campaign 1"),
    )
    assert result.status == "computed"
    assert result.source_ids == ("visual_surface_examination_definition",)
    assert result.probability_semantics == {}
    assert not any("accept" in key for key in result.values)


def test_evidence_contract_is_available_to_python_callers_without_json():
    examination = VisualSurfaceExamination.model_validate(_inputs())
    assert isinstance(examination.evidence[0], Evidence)
