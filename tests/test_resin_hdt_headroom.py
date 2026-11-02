import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import ResinHdtHeadroom, resin_hdt_headroom
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        material_condition_id="authored-resin",
        hdt_record_id="sample-record",
        test_method_id="authored-flexural-test",
        test_flexural_stress_Pa=1e6,
        heat_deflection_temperature_K=420.0,
        design_temperature_K=390.0,
        required_headroom_K=25.0,
    )
    raw.update(updates)
    digest = canonical_digest(raw)
    return ResinHdtHeadroom(
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
                    citation="Authored temperature difference.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "temperature,expected_headroom,expected_surplus,satisfied",
    [
        (390.0, 30.0, 5.0, True),
        (395.0, 25.0, 0.0, True),
        (400.0, 20.0, -5.0, False),
        (430.0, -10.0, -35.0, False),
    ],
)
def test_signed_headroom_and_inclusive_caller_criterion(
    temperature, expected_headroom, expected_surplus, satisfied
):
    result = resin_hdt_headroom(request(design_temperature_K=temperature))
    assert result.status == "computed"
    assert result.values["hdt_headroom_K"] == expected_headroom
    assert result.values["headroom_surplus_K"] == expected_surplus
    assert result.values["declared_headroom_satisfied"] is satisfied


def test_zero_required_difference_is_an_explicit_recipe():
    result = resin_hdt_headroom(request(design_temperature_K=420.0, required_headroom_K=0.0))
    assert result.values["declared_headroom_satisfied"] is True


def test_common_temperature_offset_preserves_difference():
    result = resin_hdt_headroom(request(heat_deflection_temperature_K=520.0, design_temperature_K=490.0))
    assert result.values["hdt_headroom_K"] == 30.0
    assert result.values["headroom_surplus_K"] == 5.0


def test_unrepresentable_surplus_is_not_a_passing_result():
    result = resin_hdt_headroom(
        request(heat_deflection_temperature_K=1.0, design_temperature_K=1.7e308, required_headroom_K=1.7e308)
    )
    assert result.status == "out_of_scope"
    assert "declared_headroom_satisfied" not in result.values


@pytest.mark.parametrize(
    "updates",
    [dict(test_flexural_stress_Pa=0.0), dict(required_headroom_K=-1.0), dict(design_temperature_K=0.0)],
)
def test_invalid_test_and_temperature_inputs(updates):
    with pytest.raises(ValueError):
        request(**updates)


def test_test_condition_change_breaks_digest():
    raw = request().model_dump()
    raw["test_flexural_stress_Pa"] = 2e6
    with pytest.raises(ValueError, match="pin the complete"):
        ResinHdtHeadroom.model_validate(raw)


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="bond", time_basis="instant")
    a = registry.run("materials.resin_hdt_headroom", x, context)
    b = registry.run_json("materials.resin_hdt_headroom", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
