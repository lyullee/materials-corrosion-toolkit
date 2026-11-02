import json
import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.forming_geometry_history import (
    FormingGeometryHistory,
    forming_geometry_history,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


@pytest.mark.parametrize("radius", [0.0, 1e-30])
def test_true_strain_handles_collapsed_and_nearly_collapsed_inner_surface(radius):
    raw = payload().model_dump(mode="json")
    raw["strain_convention"] = "true"
    raw["minimum_supported_radius_to_original_thickness"] = 0.0
    raw["records"][0].update(strain_convention="true", inside_radius_m=radius)
    result = forming_geometry_history(FormingGeometryHistory.model_validate_json(json.dumps(raw)))
    row = result.values["record_summaries"][0]
    if radius == 0.0:
        assert result.status == "out_of_scope"
        assert row["compressive_surface_strain"] is None
    else:
        assert result.status == "computed"
        assert row["compressive_surface_strain"] == pytest.approx(math.log(2 * radius / 0.009))
    json.dumps(result.values, allow_nan=False)


def payload(**updates):
    value = {
        "history_id": "forming-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "component_id": "component-1",
        "material_condition_id": "condition-1",
        "strain_convention": "engineering",
        "records": [
            {
                "record_id": "record-1",
                "physical_specimen_id": "specimen-1",
                "source_group_id": "source-1",
                "material_condition_id": "condition-1",
                "forming_mode": "cold",
                "forming_direction_id": "transverse",
                "geometry_convention": "mid_thickness_neutral_axis_circular_arc",
                "strain_convention": "engineering",
                "original_thickness_m": 0.01,
                "final_thickness_m": 0.009,
                "inside_radius_m": 0.02,
                "bend_angle_rad": 1.0,
                "thickness_standard_uncertainty_m": 0.0001,
                "radius_standard_uncertainty_m": 0.0002,
                "angle_standard_uncertainty_rad": 0.01,
                "record_status": "valid",
                "record_digest": D,
                "evidence": [E],
            }
        ],
        "minimum_supported_radius_to_original_thickness": 1.0,
        "maximum_supported_radius_to_original_thickness": 5.0,
        "maximum_supported_bend_angle_rad": 2.0,
        "caller_maximum_tensile_surface_strain": 0.25,
        "caller_maximum_thinning_measure": 0.2,
        "material_condition_mode_and_direction_reviewed": True,
        "original_final_thickness_and_geometry_reviewed": True,
        "geometry_and_strain_conventions_reviewed": True,
        "measurement_uncertainty_and_record_status_reviewed": True,
        "specimen_source_identity_and_digests_reviewed": True,
        "support_and_caller_threshold_authority_reviewed": True,
        "evidence": [E],
    }
    value.update(updates)
    return FormingGeometryHistory.model_validate_json(json.dumps(value))


def test_engineering_geometry_summary_and_signed_margins():
    result = forming_geometry_history(payload())
    assert result.status == "computed"
    row = result.values["record_summaries"][0]
    assert row["thinning_measure"] == pytest.approx(0.1)
    assert row["tensile_surface_strain"] == pytest.approx(0.009 / 0.049)
    assert row["thinning_measure_margin"] == pytest.approx(0.1)


def test_reviewed_geometry_outside_support_is_out_of_scope():
    base = payload()
    record = base.records[0].model_copy(update={"inside_radius_m": 0.1})
    assert forming_geometry_history(base.model_copy(update={"records": (record,)})).status == "out_of_scope"


def test_missing_review_or_all_missing_needs_data():
    assert (
        forming_geometry_history(payload(geometry_and_strain_conventions_reviewed=False)).status
        == "needs_data"
    )
    base = payload()
    missing = base.records[0].model_copy(
        update={
            "original_thickness_m": None,
            "final_thickness_m": None,
            "inside_radius_m": None,
            "bend_angle_rad": None,
            "thickness_standard_uncertainty_m": None,
            "radius_standard_uncertainty_m": None,
            "angle_standard_uncertainty_rad": None,
            "record_status": "missing",
            "missing_or_invalid_basis": "geometry unavailable",
        }
    )
    assert forming_geometry_history(base.model_copy(update={"records": (missing,)})).status == "needs_data"


def test_convention_and_context_are_strict():
    base = payload()
    true_record = base.records[0].model_copy(update={"strain_convention": "true"})
    with pytest.raises(ValueError, match="cannot be mixed"):
        FormingGeometryHistory(**base.model_dump(exclude={"records"}), records=(true_record,))
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.forming_geometry_history",
            base,
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
