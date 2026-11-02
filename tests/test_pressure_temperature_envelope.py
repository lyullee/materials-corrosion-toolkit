import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

MODEL_ID = "structural.pressure_temperature_envelope"
CONTEXT = RunContext(
    asset_id="synthetic-vessel",
    location_id="synthetic-pressure-boundary",
    time_basis="authored operating points",
)


def inputs():
    return {
        "envelope_id": "authored-affine-envelope",
        "applicability_basis": "synthetic pressure limit for arithmetic verification only",
        "source_sha256": "1" * 64,
        "knots": [
            {"temperature_K": 250.0, "allowable_pressure_Pa": 12.0e6},
            {"temperature_K": 300.0, "allowable_pressure_Pa": 10.0e6},
            {"temperature_K": 400.0, "allowable_pressure_Pa": 8.0e6},
        ],
        "operating_points": [
            {"point_id": "cold-boundary", "temperature_K": 250.0, "pressure_Pa": 11.0e6},
            {"point_id": "interior-limit", "temperature_K": 350.0, "pressure_Pa": 9.0e6},
            {"point_id": "hot-exceedance", "temperature_K": 400.0, "pressure_Pa": 8.4e6},
        ],
        "interpolation": "piecewise_linear",
        "applicability_reviewed": True,
        "operating_points_reviewed": True,
    }


def test_piecewise_linear_envelope_matches_authored_affine_segments():
    result = default_registry().run(MODEL_ID, inputs(), CONTEXT)

    assert result.status == "computed"
    assert result.values["allowable_pressures_Pa"] == pytest.approx([12.0e6, 9.0e6, 8.0e6])
    assert result.values["pressure_margins_Pa"] == pytest.approx([1.0e6, 0.0, -0.4e6])
    assert result.values["utilization_ratios"] == pytest.approx([11 / 12, 1.0, 1.05])
    assert result.values["within_supplied_envelope"] == [True, True, False]
    assert result.values["all_within_supplied_envelope"] is False
    assert result.values["minimum_margin_point_id"] == "hot-exceedance"
    assert result.values["maximum_utilization_point_id"] == "hot-exceedance"


def test_operating_point_outside_support_is_not_extrapolated():
    payload = inputs()
    payload["operating_points"] = [
        {"point_id": "below-support", "temperature_K": 249.0, "pressure_Pa": 1.0e6},
        {"point_id": "inside", "temperature_K": 300.0, "pressure_Pa": 1.0e6},
    ]
    result = default_registry().run(MODEL_ID, payload, CONTEXT)

    assert result.status == "out_of_scope"
    assert result.values["outside_support_point_ids"] == ["below-support"]
    assert "allowable_pressures_Pa" not in result.values


@pytest.mark.parametrize("review_field", ["applicability_reviewed", "operating_points_reviewed"])
def test_unreviewed_identity_or_applicability_stops_computation(review_field):
    payload = inputs()
    payload[review_field] = False
    result = default_registry().run(MODEL_ID, payload, CONTEXT)

    assert result.status == "needs_data"
    assert result.values == {}


def test_nonincreasing_knots_and_duplicate_point_ids_are_rejected():
    payload = inputs()
    payload["knots"][1]["temperature_K"] = 250.0
    with pytest.raises(ValidationError, match="strictly increasing"):
        default_registry().run(MODEL_ID, payload, CONTEXT)

    payload = inputs()
    payload["operating_points"][1]["point_id"] = "cold-boundary"
    with pytest.raises(ValidationError, match="identifiers must be unique"):
        default_registry().run(MODEL_ID, payload, CONTEXT)


def test_nonpositive_allowable_and_unknown_interpolation_are_rejected():
    payload = inputs()
    payload["knots"][0]["allowable_pressure_Pa"] = 0.0
    with pytest.raises(ValidationError):
        default_registry().run(MODEL_ID, payload, CONTEXT)

    payload = inputs()
    payload["interpolation"] = "cubic"
    with pytest.raises(ValidationError):
        default_registry().run(MODEL_ID, payload, CONTEXT)


def test_extreme_pressure_contrast_retains_positive_hot_endpoint():
    payload = inputs()
    payload["knots"] = [dict(temperature_K=250., allowable_pressure_Pa=1e300),
                        dict(temperature_K=400., allowable_pressure_Pa=1e-100)]
    payload["operating_points"] = [dict(point_id="hot", temperature_K=400., pressure_Pa=1e-100)]
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.status == "computed"
    assert result.values["allowable_pressures_Pa"] == [1e-100]
    assert result.values["utilization_ratios"] == [1.]


def test_unrepresentable_utilization_withholds_entire_batch():
    payload = inputs()
    payload["knots"] = [dict(temperature_K=250., allowable_pressure_Pa=1e-300),
                        dict(temperature_K=400., allowable_pressure_Pa=1e-300)]
    payload["operating_points"] = [dict(point_id="extreme", temperature_K=300., pressure_Pa=1e300)]
    result = default_registry().run(MODEL_ID, payload, CONTEXT)
    assert result.status == "out_of_scope"
    assert "allowable_pressures_Pa" not in result.values
