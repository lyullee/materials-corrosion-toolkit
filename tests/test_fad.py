import json

import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.fad import (
    FailureAssessment,
    FailureAssessmentCurve,
    FailureAssessmentPoint,
    assess_failure_diagram,
)
from matintegrity.registry import default_registry

EVIDENCE = Evidence(
    source_id="licensed-user-curve",
    origin="user_declared",
    citation="Synthetic curve for software verification",
    license_id="user-entitlement",
)


def curve(**changes):
    values = dict(
        curve_id="synthetic-boundary",
        assessment_basis_id="user-method-revision-a",
        load_ratio=(0.0, 0.5, 1.0, 1.25),
        allowable_toughness_ratio=(1.0, 0.9, 0.6, 0.0),
        validity_description="Synthetic verification boundary only",
        evidence=(EVIDENCE,),
    )
    values.update(changes)
    return FailureAssessmentCurve(**values)


def point(point_id="p1", k=40e6, toughness=80e6, stress=200e6, strength=400e6, **changes):
    values = dict(
        point_id=point_id,
        load_case_id="lc-1",
        location_id="weld-toe",
        material_condition_id="condition-a",
        geometry_solution_id="geometry-solution-a",
        reference_stress_solution_id="reference-stress-a",
        toughness_source_id="toughness-a",
        effective_stress_intensity_Pa_sqrt_m=k,
        fracture_resistance_Pa_sqrt_m=toughness,
        reference_stress_Pa=stress,
        normalizing_strength_Pa=strength,
    )
    values.update(changes)
    return FailureAssessmentPoint(**values)


def request(points=None, **changes):
    values = dict(
        material_condition_id="condition-a",
        curve=curve(),
        points=tuple(points or [point()]),
        linear_elastic_k_solution_reviewed=True,
        reference_stress_solution_reviewed=True,
        toughness_applicability_reviewed=True,
        load_combination_reviewed=True,
        curve_applicability_reviewed=True,
    )
    values.update(changes)
    return FailureAssessment(**values)


def test_inside_and_outside_points_preserve_identities():
    result = assess_failure_diagram(
        request(
            [
                point(),
                point("p2", k=76e6, stress=200e6, location_id="weld-root"),
            ]
        )
    )
    assert result.status == "computed"
    assert result.values["declared_boundary_outcome"] == "not_satisfied"
    assert result.values["points"][0]["toughness_ratio_Kr"] == pytest.approx(0.5)
    assert result.values["points"][0]["allowable_toughness_ratio"] == pytest.approx(0.9)
    assert result.values["points"][1]["point_outcome"] == "outside_declared_boundary"
    assert result.values["points"][1]["location_id"] == "weld-root"


def test_point_on_boundary_is_satisfied():
    result = assess_failure_diagram(request([point(k=72e6)]))
    assert result.values["points"][0]["vertical_toughness_ratio_margin"] == pytest.approx(0)
    assert result.values["declared_boundary_outcome"] == "satisfied"


def test_curve_is_linearly_interpolated():
    result = assess_failure_diagram(request([point(stress=300e6)]))
    assert result.values["points"][0]["load_ratio_Lr"] == pytest.approx(0.75)
    assert result.values["points"][0]["allowable_toughness_ratio"] == pytest.approx(0.75)


def test_curve_support_is_not_extrapolated_or_clipped():
    result = assess_failure_diagram(request([point(stress=600e6)]))
    assert result.status == "out_of_scope"
    assert result.values["declared_boundary_outcome"] == "unknown"
    assert result.values["points"][0]["load_ratio_Lr"] == pytest.approx(1.5)
    assert result.values["points"][0]["allowable_toughness_ratio"] is None


@pytest.mark.parametrize(
    "review",
    [
        "linear_elastic_k_solution_reviewed",
        "reference_stress_solution_reviewed",
        "toughness_applicability_reviewed",
        "load_combination_reviewed",
        "curve_applicability_reviewed",
    ],
)
def test_unreviewed_inputs_stop(review):
    result = assess_failure_diagram(request(**{review: False}))
    assert result.status == "needs_data"
    assert result.values == {}


def test_material_condition_mismatch_stops():
    result = assess_failure_diagram(request([point(material_condition_id="condition-b")]))
    assert result.status == "needs_data"


@pytest.mark.parametrize(
    "changes",
    [
        {"load_ratio": (0.1, 1.0)},
        {"load_ratio": (0.0, 0.5, 0.5)},
        {"allowable_toughness_ratio": (1.0, 0.8)},
        {"allowable_toughness_ratio": (1.0, 0.8, 0.9, 0.0)},
    ],
)
def test_invalid_curve_contracts_are_rejected(changes):
    with pytest.raises(ValidationError):
        curve(**changes)


def test_curve_requires_declared_permission():
    evidence = EVIDENCE.model_copy(update={"license_id": None})
    with pytest.raises(ValidationError, match="license"):
        curve(evidence=(evidence,))


def test_duplicate_point_identity_is_rejected():
    with pytest.raises(ValidationError, match="unique"):
        request([point(), point()])


def test_registry_strict_json_round_trip_and_no_probability_meaning():
    registry = default_registry()
    model_id = "structural.failure_assessment_points"
    payload = request().model_dump_json()
    context = RunContext(asset_id="asset", location_id="crack", time_basis="static synthetic case")
    result = registry.run_json(model_id, payload, context)
    assert result.status == "computed"
    assert result.probability_semantics == {}
    assert registry.describe(model_id)["output_units"]["points.toughness_ratio_Kr"] == "1"
    json.dumps(result.model_dump(mode="json"), allow_nan=False)


def test_curve_digest_changes_with_provider_boundary():
    first = assess_failure_diagram(request()).values["curve_digest"]
    second = assess_failure_diagram(request(curve=curve(curve_id="different"))).values["curve_digest"]
    assert first != second
