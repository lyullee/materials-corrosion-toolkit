import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    BrinellSurfaceObservation,
    MatingBrinellHardnessDifference,
    mating_brinell_hardness_difference,
)
from matintegrity.registry import default_registry


def observation(name, value, uncertainty=5.0, **updates):
    raw = dict(
        surface_id=name,
        physical_scope_id="pair-scope",
        material_condition_id="authored",
        record_sha256="a" * 64,
        hardness_HBW=value,
        expanded_uncertainty_HBW=uncertainty,
        scale_id="HBW",
        method_revision_id="authored-method",
        test_force_N=100.0,
        indenter_diameter_m=0.005,
        dwell_time_s=10.0,
        test_temperature_K=293.15,
    )
    raw.update(updates)
    return BrinellSurfaceObservation(**raw)


def request(**updates):
    raw = dict(
        mating_pair_id="pair",
        first=observation("a", 200.0),
        second=observation("b", 220.0),
        comparison_direction="second_harder",
        minimum_declared_difference_HBW=10.0,
        pairing_test_conditions_and_interval_interpretation_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        MatingBrinellHardnessDifference.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return MatingBrinellHardnessDifference(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored interval subtraction.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "direction,state,low,high",
    [
        ("first_harder", "outside_declared_requirement", -30.0, -10.0),
        ("second_harder", "within_declared_requirement", 10.0, 30.0),
        ("either", "within_declared_requirement", 10.0, 30.0),
    ],
)
def test_signed_and_order_independent_intervals(direction, state, low, high):
    result = mating_brinell_hardness_difference(request(comparison_direction=direction))
    assert result.values["comparison_state"] == state
    assert result.values["signed_first_minus_second_HBW"] == -20.0
    assert result.values["comparison_interval_lower_HBW"] == low
    assert result.values["comparison_interval_upper_HBW"] == high


def test_uncertainty_overlap_is_not_a_boolean_pass():
    assert (
        mating_brinell_hardness_difference(request(minimum_declared_difference_HBW=20.0)).values[
            "comparison_state"
        ]
        == "uncertainty_overlap"
    )


def test_absolute_interval_crossing_zero_keeps_zero_lower_bound():
    result = mating_brinell_hardness_difference(
        request(
            first=observation("a", 220.0), comparison_direction="either", minimum_declared_difference_HBW=5.0
        )
    )
    assert result.values["comparison_interval_lower_HBW"] == 0.0
    assert result.values["comparison_interval_upper_HBW"] == 10.0
    assert result.values["comparison_state"] == "uncertainty_overlap"


def test_unreviewed_pairing_needs_data():
    assert (
        mating_brinell_hardness_difference(
            request(pairing_test_conditions_and_interval_interpretation_reviewed=False)
        ).status
        == "needs_data"
    )


@pytest.mark.parametrize(
    "updates",
    [
        {"test_force_N": 200.0},
        {"dwell_time_s": 20.0},
        {"method_revision_id": "different"},
        {"test_temperature_K": 300.0},
    ],
)
def test_different_test_conditions_are_not_silently_equated(updates):
    with pytest.raises(ValueError, match="conditions must match"):
        request(second=observation("b", 220.0, **updates))


def test_historical_hb_label_is_not_hbw_conversion():
    with pytest.raises(ValueError):
        observation("a", 200.0, scale_id="HB")


def test_unrepresentable_difference_interval_returns_status():
    result = mating_brinell_hardness_difference(
        request(first=observation("a", 1e308, 1e308), second=observation("b", 1e308, 1e308))
    )
    assert result.status == "out_of_scope"


def test_digest_pins_surface_and_comparison_inputs():
    raw = request().model_dump()
    raw["first"]["hardness_HBW"] = 210.0
    with pytest.raises(ValueError, match="pin the complete"):
        MatingBrinellHardnessDifference(**raw)


def test_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    a = registry.run("testing.mating_brinell_hardness_difference", x.model_dump(), context)
    b = registry.run_json("testing.mating_brinell_hardness_difference", x.model_dump_json(), context)
    assert a.values == b.values
