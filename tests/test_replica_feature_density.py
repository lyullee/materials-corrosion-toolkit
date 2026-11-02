import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.replica_feature_density import (
    ReplicaFeatureDensityAssessment,
    replica_feature_density_summary,
    specifications,
)

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored geometry test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
DIGEST_E = "e" * 64
DIGEST_F = "f" * 64


def feature(identifier, x, y, digest, **updates):
    row = {
        "feature_id": identifier,
        "caller_feature_type": "reviewed-dark-feature",
        "centroid_x": x,
        "centroid_y": y,
        "bounding_box_min_x": x - 1,
        "bounding_box_min_y": y - 1,
        "bounding_box_max_x": x + 1,
        "bounding_box_max_y": y + 1,
        "segmented_area": 4.0,
        "expanded_centroid_uncertainty": 0.2,
        "expanded_area_uncertainty": 0.4,
        "uncertainty_coverage_factor": 2.0,
        "segmentation_feature_digest": digest,
        "overlaps_feature_ids": (),
        "touches_frame_edge": False,
        "include_in_summary": True,
        "edge_censoring_basis": None,
        "record_available": True,
        "record_valid": True,
        "missing_or_invalid_basis": None,
        "observer_review_id": "observer-review-1",
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return row


def payload(**updates):
    row = {
        "assessment_id": "replica-density-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "component_id": "component-1",
        "replica_campaign_id": "campaign-1",
        "physical_location_definition": "outer surface at caller datum A",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "service_exposure_id": "exposure-1",
        "service_clock_definition": "caller elapsed operating clock",
        "service_exposure_duration_s": 1000.0,
        "minimum_service_temperature_K": 500.0,
        "maximum_service_temperature_K": 600.0,
        "fields": (
            {
                "field_id": "field-1",
                "replica_id": "replica-1",
                "frame_id": "frame-1",
                "physical_source_group_id": "source-group-1",
                "independence_group_id": "independence-group-1",
                "calibration": {
                    "calibration_id": "scale-1",
                    "coordinate_unit": "px",
                    "frame_width": 100.0,
                    "frame_height": 100.0,
                    "pixel_size_x_m_per_px": 1e-6,
                    "pixel_size_y_m_per_px": 2e-6,
                    "expanded_pixel_size_x_uncertainty_m_per_px": 1e-8,
                    "expanded_pixel_size_y_uncertainty_m_per_px": 2e-8,
                    "uncertainty_coverage_factor": 2.0,
                    "calibration_provider_id": "cal-provider",
                    "calibration_provider_revision": "rev-1",
                    "calibration_record_digest": DIGEST_A,
                    "record_valid": True,
                    "invalid_or_missing_basis": None,
                    "evidence": (EVIDENCE,),
                },
                "segmentation_method_id": "method-1",
                "segmentation_provider_id": "seg-provider",
                "segmentation_provider_revision": "rev-2",
                "segmentation_configuration_digest": DIGEST_B,
                "segmentation_input_digest": DIGEST_C,
                "segmentation_result_digest": DIGEST_D,
                "observer_review_id": "observer-review-1",
                "observer_review_digest": DIGEST_E,
                "feature_inventory_complete": True,
                "field_record_valid": True,
                "invalid_or_missing_basis": None,
                "features": (
                    feature("f-1", 10.0, 10.0, DIGEST_A),
                    feature("f-2", 13.0, 14.0, DIGEST_F),
                ),
                "evidence": (EVIDENCE,),
            },
        ),
        "replica_location_material_and_service_exposure_reviewed": True,
        "frame_and_calibration_identity_reviewed": True,
        "si_scale_units_and_uncertainty_reviewed": True,
        "segmentation_provider_revision_and_digests_reviewed": True,
        "observer_review_and_feature_inventory_reviewed": True,
        "feature_ids_types_coordinates_and_geometry_reviewed": True,
        "duplicate_overlap_and_edge_censoring_reviewed": True,
        "physical_source_and_independence_groups_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    row.update(updates)
    return ReplicaFeatureDensityAssessment.model_validate(row)


def test_pixel_calibration_reduces_counts_area_and_spacing_to_si():
    result = replica_feature_density_summary(payload())
    assert result.status == "computed"
    summary = result.values["field_summaries"][0]
    assert summary["field_area_m2"] == pytest.approx(2e-8)
    assert summary["reviewed_feature_count"] == 2
    assert summary["feature_count_density_per_m2"] == pytest.approx(1e8)
    assert summary["total_segmented_feature_area_m2"] == pytest.approx(16e-12)
    assert summary["segmented_feature_area_fraction"] == pytest.approx(8e-4)
    assert summary["mean_nearest_neighbor_spacing_m"] == pytest.approx((3.0**2 + 8.0**2) ** 0.5 * 1e-6)


def test_reviewed_edge_feature_can_be_explicitly_excluded():
    data = payload().model_dump()
    edge = feature(
        "edge-1",
        1.0,
        1.0,
        DIGEST_B,
        bounding_box_min_x=0.0,
        bounding_box_min_y=0.0,
        touches_frame_edge=True,
        include_in_summary=False,
        edge_censoring_basis="reviewed frame-edge truncation; excluded from field summary",
    )
    data["fields"][0]["features"] = (*data["fields"][0]["features"], edge)
    result = replica_feature_density_summary(ReplicaFeatureDensityAssessment.model_validate(data))
    assert result.status == "computed"
    summary = result.values["field_summaries"][0]
    assert summary["reviewed_feature_count"] == 2
    assert summary["excluded_edge_feature_ids"] == ["edge-1"]


def test_overlap_incomplete_inventory_or_missing_review_needs_data():
    data = payload().model_dump()
    data["fields"][0]["features"][0]["overlaps_feature_ids"] = ("f-2",)
    data["fields"][0]["features"][1]["overlaps_feature_ids"] = ("f-1",)
    result = replica_feature_density_summary(ReplicaFeatureDensityAssessment.model_validate(data))
    assert result.status == "needs_data"
    assert result.values["overlapping_feature_ids"] == ["field-1:f-1", "field-1:f-2"]

    assert replica_feature_density_summary(
        payload(observer_review_and_feature_inventory_reviewed=False)
    ).status == ("needs_data")
    data = payload().model_dump()
    data["fields"][0]["feature_inventory_complete"] = False
    assert (
        replica_feature_density_summary(ReplicaFeatureDensityAssessment.model_validate(data)).status
        == "needs_data"
    )


def test_duplicate_features_and_unreviewed_edge_handling_are_rejected():
    data = payload().model_dump()
    data["fields"][0]["features"][1]["segmentation_feature_digest"] = DIGEST_A
    with pytest.raises(ValueError, match="duplicate replica segmentation feature digests"):
        ReplicaFeatureDensityAssessment.model_validate(data)

    data = payload().model_dump()
    data["fields"][0]["features"][0]["touches_frame_edge"] = True
    with pytest.raises(ValueError, match="edge-touching features require"):
        ReplicaFeatureDensityAssessment.model_validate(data)


def test_specification_identity_source_and_run_context_are_strict():
    spec = specifications()[0]
    assert spec.model_id == "inspection.replica_feature_density_summary"
    assert spec.input_type is ReplicaFeatureDensityAssessment
    assert spec.source_ids == ("authored_replica_feature_geometry_reduction",)
    context = RunContext(asset_id="asset-1", location_id="location-1", time_basis="service clock")
    spec.context_validator(payload(), context)
    with pytest.raises(ValueError, match="must match the run context"):
        spec.context_validator(
            payload(), RunContext(asset_id="other", location_id="location-1", time_basis="service clock")
        )
