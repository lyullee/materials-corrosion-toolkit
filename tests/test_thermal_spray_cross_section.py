import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_spray_cross_section import (
    ThermalSprayCrossSectionSummary,
    specifications,
    thermal_spray_cross_section_summary,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def field(identifier, partition, specimen, source, thicknesses, pore_area_px2, edge=False):
    return {
        "field_id": identifier,
        "physical_specimen_id": specimen,
        "source_group_id": source,
        "independence_group_id": f"ind-{specimen}",
        "partition": partition,
        "physical_location_id": f"location-{identifier}",
        "layer_id": "layer-1",
        "substrate_condition_id": "substrate-1",
        "spray_batch_id": "batch-1",
        "process_condition_id": "process-1",
        "field_basis": "calibrated_image",
        "coordinate_frame_id": "frame-1",
        "frame_calibration_id": "frame-cal-1",
        "width_px": 100,
        "height_px": 100,
        "declared_field_area_m2": 1e-8,
        "thickness_traverses": (
            {
                "traverse_id": f"traverse-{identifier}",
                "points": tuple(
                    {
                        "point_id": f"{identifier}-point-{index}",
                        "x_coordinate": 10.0 + index * 20.0,
                        "y_coordinate": 50.0,
                        "coordinate_unit_token": "px",
                        "thickness_m": value,
                        "expanded_uncertainty_m": 2e-6,
                    }
                    for index, value in enumerate(thicknesses)
                ),
                "method_id": "thickness-method-1",
                "provider_id": "provider-1",
                "provider_revision": "1",
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "pores": (
            {
                "pore_id": f"pore-{identifier}",
                "area_value": pore_area_px2,
                "area_unit_token": "px^2",
                "coordinate_unit_token": "px",
                "minimum_x": 20.0,
                "maximum_x": 30.0,
                "minimum_y": 20.0,
                "maximum_y": 30.0,
                "touches_field_edge": edge,
                "segmentation_method_id": "caller-segmentation-1",
                "provider_id": "provider-1",
                "provider_revision": "1",
                "result_digest": DIGEST_C,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "field_method_id": "cross-section-method-1",
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_configuration_digest": DIGEST_A,
        "data_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def fields():
    return (
        field("cal-1", "calibration", "spec-cal-1", "source-cal-a", (100e-6, 110e-6, 105e-6), 100.0),
        field("cal-2", "calibration", "spec-cal-2", "source-cal-b", (102e-6, 108e-6, 106e-6), 120.0, True),
        field("hold-1", "holdout", "spec-hold-1", "source-hold", (101e-6, 109e-6, 104e-6), 110.0),
    )


def payload(**updates):
    value = {
        "summary_id": "summary-1",
        "asset_id": "asset-1",
        "location_id": "cross-section-scope-1",
        "physical_scope_id": "physical-scope-1",
        "coating_system_id": "coating-system-1",
        "layer_id": "layer-1",
        "substrate_condition_id": "substrate-1",
        "spray_batch_id": "batch-1",
        "process_condition_id": "process-1",
        "frame_calibrations": (
            {
                "calibration_id": "frame-cal-1",
                "coordinate_frame_id": "frame-1",
                "x_scale_m_per_px": 1e-6,
                "y_scale_m_per_px": 1e-6,
                "x_scale_expanded_uncertainty_m_per_px": 1e-8,
                "y_scale_expanded_uncertainty_m_per_px": 1e-8,
                "provider_id": "calibration-provider",
                "provider_revision": "1",
                "configuration_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "fields": fields(),
        "field_area_relative_tolerance": 1e-9,
        "specimen_location_layer_and_substrate_reviewed": True,
        "spray_batch_and_process_condition_reviewed": True,
        "frame_calibration_and_field_area_reviewed": True,
        "thickness_traverses_units_uncertainty_and_bounds_reviewed": True,
        "caller_segmentation_pore_area_edge_and_overlap_reviewed": True,
        "specimen_source_and_independence_partitions_reviewed": True,
        "method_provider_revision_and_digests_reviewed": True,
        "missing_invalid_and_support_policy_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ThermalSprayCrossSectionSummary(**value)


def test_calibrated_field_thickness_porosity_and_partition_summary_compute():
    result = thermal_spray_cross_section_summary(payload())
    assert result.status == "computed"
    first = result.values["field_rows"][0]
    assert first["mean_thickness_m"] == pytest.approx(105e-6)
    assert first["area_porosity_fraction"] == pytest.approx(0.01)
    calibration = result.values["partition_summaries"][0]
    assert calibration["field_count"] == 2
    assert calibration["field_mean_thickness_repeatability_m"] is not None
    assert result.values["field_rows"][1]["edge_pore_ids"] == ["pore-cal-2"]


def test_overlap_or_missing_review_needs_data():
    assert (
        thermal_spray_cross_section_summary(
            payload(caller_segmentation_pore_area_edge_and_overlap_reviewed=False)
        ).status
        == "needs_data"
    )
    rows = list(fields())
    pore = dict(rows[0]["pores"][0])
    pore["overlaps_pore_ids"] = ("other-pore",)
    rows[0] = {**rows[0], "pores": (pore,)}
    result = thermal_spray_cross_section_summary(payload(fields=tuple(rows)))
    assert result.status == "needs_data"
    assert "pore-cal-1" in result.values["overlapping_pore_ids"]


def test_out_of_bounds_geometry_needs_data():
    rows = list(fields())
    pore = dict(rows[0]["pores"][0])
    pore["maximum_x"] = 120.0
    rows[0] = {**rows[0], "pores": (pore,)}
    result = thermal_spray_cross_section_summary(payload(fields=tuple(rows)))
    assert result.status == "needs_data"
    assert result.values["out_of_bounds_geometry_ids"] == ["pore-cal-1"]


def test_partition_leakage_and_context_identity_are_enforced():
    rows = list(fields())
    rows[2] = {**rows[2], "source_group_id": "source-cal-a"}
    with pytest.raises(ValueError, match="source group"):
        payload(fields=tuple(rows))
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.thermal_spray_cross_section_summary",
            payload(),
            RunContext(asset_id="other", location_id="cross-section-scope-1", time_basis="authored"),
        )
