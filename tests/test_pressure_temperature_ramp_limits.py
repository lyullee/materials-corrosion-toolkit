import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    PressureTemperatureRampLimits,
    pressure_temperature_ramp_limits,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        history_id="authored",
        component_id="vessel",
        metal_temperature_location_id="wall",
        pressure_location_id="internal",
        clock_basis="authored-elapsed",
        time_s=(100.0, 110.0, 130.0),
        metal_temperature_K=(300.0, 320.0, 300.0),
        pressure_Pa_abs=(1e5, 3e5, 1e5),
        maximum_heating_rate_K_s=2.0,
        maximum_cooling_rate_K_s=1.0,
        maximum_pressurizing_rate_Pa_s=20000.0,
        maximum_depressurizing_rate_Pa_s=10000.0,
        piecewise_linear_history_and_location_reviewed=True,
        rate_limit_applicability_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        PressureTemperatureRampLimits.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return PressureTemperatureRampLimits(
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
                    citation="authored ramp arithmetic",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_signed_rates_nonzero_clock_and_inclusive_limits():
    r = pressure_temperature_ramp_limits(request())
    assert r.status == "computed"
    rows = r.values["interval_results"]
    assert [row["temperature_rate_K_s"] for row in rows] == [2.0, -1.0]
    assert [row["pressure_rate_Pa_s"] for row in rows] == [20000.0, -10000.0]
    assert r.values["all_intervals_within_declared_rate_limits"] is True


@pytest.mark.parametrize(
    "field,value,index,key",
    [
        ("maximum_heating_rate_K_s", 1.9, 0, "heating"),
        ("maximum_cooling_rate_K_s", 0.9, 1, "cooling"),
        ("maximum_pressurizing_rate_Pa_s", 19000.0, 0, "pressurizing"),
        ("maximum_depressurizing_rate_Pa_s", 9000.0, 1, "depressurizing"),
    ],
)
def test_directional_limits_are_independent(field, value, index, key):
    r = pressure_temperature_ramp_limits(request(**{field: value}))
    assert r.status == "computed"
    assert r.values["exceeded_interval_indices"] == [index]
    assert r.values["interval_results"][index]["within_declared_rate_limits"][key] is False


def test_zero_limits_allow_only_steady_history():
    r = pressure_temperature_ramp_limits(
        request(
            metal_temperature_K=(300.0, 300.0, 300.0),
            pressure_Pa_abs=(1e5, 1e5, 1e5),
            maximum_heating_rate_K_s=0.0,
            maximum_cooling_rate_K_s=0.0,
            maximum_pressurizing_rate_Pa_s=0.0,
            maximum_depressurizing_rate_Pa_s=0.0,
        )
    )
    assert r.values["all_intervals_within_declared_rate_limits"] is True


def test_missing_piecewise_linear_review_withholds_rates():
    r = pressure_temperature_ramp_limits(request(piecewise_linear_history_and_location_reviewed=False))
    assert r.status == "needs_data"
    assert "interval_results" not in r.values


def test_unsupported_rate_range_is_withheld():
    r = pressure_temperature_ramp_limits(request(time_s=(0.0, 1e-308, 2e-308)))
    assert r.status == "out_of_scope"


def test_invalid_clock_and_alignment_are_rejected():
    with pytest.raises(ValueError, match="strictly increase"):
        request(time_s=(0.0, 1.0, 1.0))
    with pytest.raises(ValueError, match="align"):
        request(time_s=(0.0, 1.0))


def test_nonzero_change_underflow_is_not_a_zero_rate_pass():
    r = pressure_temperature_ramp_limits(
        request(
            time_s=(0.0, 5e307, 1e308),
            metal_temperature_K=(1e-300, 2e-300, 3e-300),
            maximum_heating_rate_K_s=0.0,
        )
    )
    assert r.status == "out_of_scope"
    assert "all_intervals_within_declared_rate_limits" not in r.values


def test_limits_and_clock_are_digest_bound():
    raw = request().model_dump()
    raw["maximum_heating_rate_K_s"] = 100.0
    with pytest.raises(ValueError, match="pin the complete"):
        PressureTemperatureRampLimits.model_validate(raw)


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="wall", time_basis="authored")
    a = registry.run("structural.pressure_temperature_ramp_limits", x, context)
    b = registry.run_json("structural.pressure_temperature_ramp_limits", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
