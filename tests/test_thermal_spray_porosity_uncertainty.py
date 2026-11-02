import math

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.thermal_spray_porosity_uncertainty import (
    ThermalSprayPorosityUncertainty,
    specifications,
    thermal_spray_porosity_uncertainty,
)
from matintegrity.registry import ModelRegistry

SHA = "a" * 64


def evidence(label="porosity"):
    return {
        "source_id": label,
        "origin": "measured",
        "citation": f"caller evidence {label}",
        "sha256": SHA,
    }


def calibration(maximum_field_area_px2=20_000.0):
    return {
        "calibration_id": "pixel-cal-1",
        "coordinate_frame_id": "frame-1",
        "pixel_area_scale_m2_per_px2": 1e-12,
        "pixel_area_scale_standard_uncertainty_m2_per_px2": 1e-14,
        "minimum_supported_field_area_px2": 5_000.0,
        "maximum_supported_field_area_px2": maximum_field_area_px2,
        "maximum_supported_single_pore_area_px2": 500.0,
        "provider_id": "calibration-lab",
        "provider_revision": "1",
        "configuration_digest": SHA,
        "result_digest": SHA,
        "record_valid": True,
        "evidence": (evidence("pixel-calibration"),),
    }


def pore(pore_id, area_px2):
    return {
        "pore_id": pore_id,
        "segmented_area_px2": area_px2,
        "segmented_area_standard_uncertainty_px2": 2.0,
        "area_unit_token": "px^2",
        "touches_field_edge": False,
        "segmentation_method_id": "caller-segment-v1",
        "provider_id": "caller-segmentation",
        "provider_revision": "1",
        "input_digest": SHA,
        "result_digest": SHA,
        "record_valid": True,
        "evidence": (evidence(f"pore-{pore_id}"),),
    }


def reference(reference_id, fraction):
    return {
        "reference_id": reference_id,
        "porosity_area_fraction": fraction,
        "porosity_standard_uncertainty_fraction": 0.0005,
        "minimum_supported_field_area_m2": 5e-9,
        "maximum_supported_field_area_m2": 2e-8,
        "method_id": "independent-reference-v1",
        "provider_id": "reference-lab",
        "provider_revision": "2",
        "source_lineage_id": "reference-series-2026",
        "source_digest": SHA,
        "result_digest": SHA,
        "record_valid": True,
        "evidence": (evidence(f"reference-{reference_id}"),),
    }


def field(field_id, partition, group, area_px2, reference_fraction=None):
    suffix = field_id[-1]
    return {
        "field_id": field_id,
        "replicate_group_id": group,
        "physical_specimen_id": f"specimen-{partition}-{suffix}",
        "source_group_id": f"source-{partition}-{suffix}",
        "independence_group_id": f"independent-{partition}-{suffix}",
        "spatial_group_id": f"spatial-{partition}-{suffix}",
        "partition": partition,
        "physical_location_id": f"location-{partition}-{suffix}",
        "coordinate_frame_id": "frame-1",
        "width_px": 100,
        "height_px": 100,
        "pixel_area_calibration_id": "pixel-cal-1",
        "layer_id": "topcoat",
        "substrate_condition_id": "prepared-steel",
        "spray_batch_id": "batch-1",
        "process_condition_id": "process-1",
        "pores": (pore(f"pore-{field_id}", area_px2),),
        "reference": (
            reference(f"ref-{field_id}", reference_fraction) if reference_fraction is not None else None
        ),
        "field_provider_id": "microscopy-lab",
        "field_provider_revision": "3",
        "field_data_digest": SHA,
        "evidence": (evidence(f"field-{field_id}"),),
    }


def fields():
    return (
        field("cal-field-1", "calibration", "cal-group", 100.0),
        field("cal-field-2", "calibration", "cal-group", 110.0),
        field("hold-field-1", "holdout", "hold-group", 120.0, 0.011),
        field("hold-field-2", "holdout", "hold-group", 130.0, 0.012),
    )


def payload(**changes):
    data = {
        "assessment_id": "porosity-assessment-1",
        "asset_id": "asset-1",
        "location_id": "coating-location-1",
        "physical_scope_id": "scope-1",
        "coating_system_id": "coating-1",
        "layer_id": "topcoat",
        "substrate_condition_id": "prepared-steel",
        "spray_batch_id": "batch-1",
        "process_condition_id": "process-1",
        "calibrations": (calibration(),),
        "fields": fields(),
        "minimum_replicates_per_group": 2,
        "expanded_uncertainty_coverage_factor": 2.0,
        "specimen_field_layer_and_process_identity_reviewed": True,
        "pixel_area_calibration_units_uncertainty_and_support_reviewed": True,
        "caller_segmentation_area_uncertainty_edge_status_and_digests_reviewed": True,
        "replicate_and_spatial_group_independence_reviewed": True,
        "specimen_source_independence_spatial_and_partition_groups_reviewed": True,
        "holdout_reference_lineage_digest_uncertainty_and_support_reviewed": True,
        "uncertainty_propagation_and_coverage_factor_reviewed": True,
        "missing_invalid_and_out_of_support_policy_reviewed": True,
        "evidence": (evidence("assessment"),),
    }
    data.update(changes)
    return ThermalSprayPorosityUncertainty.model_validate(data)


def test_computes_field_replicate_and_holdout_uncertainty_summaries():
    result = thermal_spray_porosity_uncertainty(payload())
    assert result.status == "computed"
    assert result.values["field_rows"][0]["porosity_area_fraction"] == pytest.approx(0.01)
    assert result.values["field_rows"][0]["segmented_pore_area_m2"] == pytest.approx(1e-10)
    calibration_group = result.values["replicate_group_rows"][0]
    assert calibration_group["mean_porosity_area_fraction"] == pytest.approx(0.0105)
    assert calibration_group["combined_standard_uncertainty_fraction"] > 0
    assert result.values["holdout_diagnostics"]["mean_error_fraction"] == pytest.approx(0.001)
    assert result.values["holdout_diagnostics"]["root_mean_squared_error_fraction"] == pytest.approx(0.001)
    assert math.isfinite(result.values["holdout_diagnostics"]["mean_absolute_standardized_error"])


def test_missing_review_and_insufficient_replicates_need_data():
    result = thermal_spray_porosity_uncertainty(
        payload(
            minimum_replicates_per_group=3,
            uncertainty_propagation_and_coverage_factor_reviewed=False,
        )
    )
    assert result.status == "needs_data"
    assert "uncertainty_propagation_and_coverage_factor_reviewed" in result.values["missing_reviews"]
    assert result.values["insufficient_replicate_groups"] == [
        "calibration:cal-group",
        "holdout:hold-group",
    ]


def test_calibration_or_reference_support_is_not_extrapolated():
    result = thermal_spray_porosity_uncertainty(
        payload(calibrations=(calibration(maximum_field_area_px2=9_000.0),))
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_pixel_area_calibration_support_ids"] == [
        "cal-field-1",
        "cal-field-2",
        "hold-field-1",
        "hold-field-2",
    ]


def test_partition_leakage_and_context_identity_are_enforced():
    rows = list(fields())
    rows[2] = {**rows[2], "source_group_id": rows[0]["source_group_id"]}
    with pytest.raises(ValueError, match="source group"):
        payload(fields=tuple(rows))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.thermal_spray_porosity_uncertainty",
            payload(),
            RunContext(asset_id="other", location_id="coating-location-1", time_basis="authored"),
        )
