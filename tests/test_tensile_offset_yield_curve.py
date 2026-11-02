import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.tensile_offset_yield_curve import (
    TensileOffsetYieldCurveAssessment,
    specifications,
    tensile_offset_yield_curve,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def point(identifier, strain, stress, weight=1.0, **updates):
    value = {
        "point_id": identifier,
        "engineering_strain": strain,
        "engineering_stress_Pa": stress,
        "elastic_fit_weight": weight,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def curve(final_stress=600e6):
    return (
        point("p0", 0.0, 0.0),
        point("p1", 0.001, 200e6),
        point("p2", 0.002, 400e6),
        point("p3", 0.004, 500e6),
        point("p4", 0.006, 550e6),
        point("p5", 0.008, final_stress),
    )


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "specimen-location-1",
        "tensile_test_id": "test-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "independence_group_id": "independence-1",
        "material_condition_id": "condition-1",
        "specimen_geometry_id": "geometry-1",
        "extensometer_id": "extensometer-1",
        "gauge_length_m": 0.05,
        "instrument_provider_id": "instrument-provider",
        "instrument_provider_revision": "1",
        "instrument_configuration_digest": DIGEST_A,
        "extensometer_calibration_digest": DIGEST_B,
        "curve_data_digest": DIGEST_C,
        "result_provider_id": "result-provider",
        "result_provider_revision": "1",
        "result_configuration_digest": DIGEST_D,
        "engineering_strain_unit_token": "1",
        "engineering_stress_unit_token": "Pa",
        "curve_points": curve(),
        "elastic_fit_start_point_id": "p0",
        "elastic_fit_end_point_id": "p2",
        "analysis_start_point_id": "p0",
        "analysis_end_point_id": "p5",
        "offset_strain": 0.002,
        "crossing_zero_tolerance_Pa": 1e-6,
        "specimen_gauge_and_extensometer_identity_reviewed": True,
        "instrument_calibration_configuration_and_digests_reviewed": True,
        "engineering_units_and_raw_curve_reviewed": True,
        "monotonic_loading_branch_reviewed": True,
        "elastic_fit_window_and_weights_reviewed": True,
        "offset_and_linear_interpolation_reviewed": True,
        "pre_necking_analysis_window_reviewed": True,
        "crossing_uniqueness_reviewed": True,
        "optional_reference_comparison_reviewed": True,
    }
    value.update(updates)
    return TensileOffsetYieldCurveAssessment(**value)


def test_weighted_elastic_fit_and_unique_linear_crossing():
    result = tensile_offset_yield_curve(payload())
    assert result.status == "computed"
    assert result.values["fitted_elastic_modulus_Pa"] == pytest.approx(200e9)
    assert result.values["fitted_elastic_intercept_Pa"] == pytest.approx(0.0, abs=1e-5)
    assert result.values["offset_yield_stress_Pa"] == pytest.approx(514285714.2857143)
    assert result.values["intersection_engineering_strain"] == pytest.approx(0.004571428571428572)
    assert result.values["intersection_kind"] == "linear_segment_intersection"
    assert result.values["intersection_point_ids"] == ["p3", "p4"]


def test_multiple_or_missing_crossings_are_needs_data():
    multiple = tensile_offset_yield_curve(payload(curve_points=curve(final_stress=1500e6)))
    assert multiple.status == "needs_data"
    assert len(multiple.values["crossing_candidates"]) == 2

    no_crossing_curve = (
        point("p0", 0.0, 0.0),
        point("p1", 0.001, 200e6),
        point("p2", 0.002, 400e6),
        point("p3", 0.004, 900e6),
        point("p4", 0.006, 1300e6),
        point("p5", 0.008, 1700e6),
    )
    no_crossing = tensile_offset_yield_curve(payload(curve_points=no_crossing_curve))
    assert no_crossing.status == "needs_data"
    assert no_crossing.values["crossing_candidates"] == []


def test_independent_reference_comparison_is_diagnostic_only():
    reference = {
        "reference_record_id": "reference-1",
        "physical_specimen_id": "reference-specimen",
        "source_group_id": "reference-source",
        "independence_group_id": "reference-independence",
        "reference_method_id": "reference-method",
        "offset_strain": 0.002,
        "offset_yield_stress_Pa": 510e6,
        "expanded_uncertainty_Pa": 5e6,
        "uncertainty_coverage_factor": 2.0,
        "provider_id": "reference-provider",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    result = tensile_offset_yield_curve(payload(reference_comparison=reference))
    assert result.status == "computed"
    assert result.values["reference_comparison"]["signed_difference_Pa"] == pytest.approx(4285714.2857143)

    reference["physical_specimen_id"] = "specimen-1"
    with pytest.raises(ValueError, match="must be independent"):
        payload(reference_comparison=reference)


def test_raw_curve_window_and_review_contracts_are_strict():
    nonmonotonic = list(curve())
    nonmonotonic[3] = point("p3", 0.0015, 500e6)
    with pytest.raises(ValueError, match="strictly increasing"):
        payload(curve_points=tuple(nonmonotonic))

    with pytest.raises(ValueError, match="inside the reviewed analysis window"):
        payload(analysis_start_point_id="p1", elastic_fit_start_point_id="p0")

    assert (
        tensile_offset_yield_curve(payload(pre_necking_analysis_window_reviewed=False)).status == "needs_data"
    )


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.tensile_offset_yield_curve",
            payload(),
            RunContext(asset_id="other", location_id="specimen-location-1", time_basis="authored"),
        )
