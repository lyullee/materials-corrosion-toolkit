import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredLogSlopeRuptureFactor,
    TemperatureTrendStrengthScaling,
    declared_log_slope_rupture_factor,
    temperature_trend_strength_scaling,
)
from matintegrity.registry import default_registry


def bind(cls, raw):
    digest = canonical_digest(raw)
    return cls(
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
                    citation="Authored strength arithmetic.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def factor(**updates):
    raw = dict(
        material_condition_id="condition",
        slope_definition_id="log-time-per-log-stress",
        negative_log_time_per_log_stress_slope=-2.0,
        logarithm_base=4.0,
        upper_factor_cap=1.0,
    )
    raw.update(updates)
    return bind(DeclaredLogSlopeRuptureFactor, raw)


def strength(**updates):
    raw = dict(
        material_condition_id="condition",
        property_definition_id="declared-tensile-property",
        trend_basis_id="authored-trend",
        reference_temperature_K=300.0,
        evaluation_temperature_K=600.0,
        reference_strength_Pa=500e6,
        trend_strength_at_reference_Pa=800e6,
        trend_strength_at_evaluation_Pa=400e6,
    )
    raw.update(updates)
    return bind(TemperatureTrendStrengthScaling, raw)


def test_known_log_slope_factor():
    values = declared_log_slope_rupture_factor(factor()).values
    assert values["uncapped_factor"] == 0.5
    assert values["capped_factor"] == 0.5
    assert values["controlling_terms"] == ["log_slope"]


def test_caller_cap_controls():
    values = declared_log_slope_rupture_factor(factor(upper_factor_cap=0.25)).values
    assert values["capped_factor"] == 0.25
    assert values["controlling_terms"] == ["upper_cap"]


def test_numeric_tie_retains_both_terms():
    values = declared_log_slope_rupture_factor(factor(upper_factor_cap=0.5)).values
    assert values["controlling_terms"] == ["log_slope", "upper_cap"]


def test_explicit_log_base_changes_recipe():
    assert declared_log_slope_rupture_factor(factor(logarithm_base=16.0)).values["capped_factor"] == 0.25


def test_underflowing_positive_factor_is_not_zero_or_cap():
    result = declared_log_slope_rupture_factor(factor(negative_log_time_per_log_stress_slope=-5e-324))
    assert result.status == "out_of_scope"
    assert "capped_factor" not in result.values


@pytest.mark.parametrize(
    "updates",
    [
        dict(negative_log_time_per_log_stress_slope=0.0),
        dict(negative_log_time_per_log_stress_slope=1.0),
        dict(logarithm_base=1.0),
        dict(upper_factor_cap=0.0),
    ],
)
def test_invalid_factor_recipe(updates):
    with pytest.raises(ValueError):
        factor(**updates)


def test_temperature_trend_ratio_scales_supplied_reference():
    values = temperature_trend_strength_scaling(strength()).values
    assert values["trend_ratio"] == 0.5
    assert values["scaled_reference_strength_Pa"] == 250e6


def test_coincident_temperature_same_trend_preserves_reference():
    values = temperature_trend_strength_scaling(
        strength(evaluation_temperature_K=300.0, trend_strength_at_evaluation_Pa=800e6)
    ).values
    assert values["scaled_reference_strength_Pa"] == 500e6


def test_coincident_temperature_conflicting_trend_is_rejected():
    with pytest.raises(ValueError):
        strength(evaluation_temperature_K=300.0)


@pytest.mark.parametrize(
    "reference,trend,trend_reference,expected",
    [
        (1e-300, 1e300, 1e-300, 1e300),
        (1e300, 1e-300, 1e300, 1e-300),
    ],
)
def test_unrepresentable_intermediate_ratio_does_not_erase_scaled_strength(
    reference, trend, trend_reference, expected
):
    result = temperature_trend_strength_scaling(
        strength(
            reference_strength_Pa=reference,
            trend_strength_at_evaluation_Pa=trend,
            trend_strength_at_reference_Pa=trend_reference,
        )
    )
    assert result.status == "computed"
    assert result.values["trend_ratio"] is None
    assert result.values["trend_ratio_representable"] is False
    assert result.values["scaled_reference_strength_Pa"] == pytest.approx(expected, rel=1e-12, abs=0.0)


@pytest.mark.parametrize(
    "reference,trend,trend_reference",
    [
        (1e308, 1e308, 1e-300),
        (1e-300, 1e-300, 1e300),
    ],
)
def test_unrepresentable_scaled_strength_is_withheld(reference, trend, trend_reference):
    result = temperature_trend_strength_scaling(
        strength(
            reference_strength_Pa=reference,
            trend_strength_at_evaluation_Pa=trend,
            trend_strength_at_reference_Pa=trend_reference,
        )
    )
    assert result.status == "out_of_scope"


@pytest.mark.parametrize(
    "builder,cls,field,value",
    [
        (factor, DeclaredLogSlopeRuptureFactor, "logarithm_base", 2.0),
        (strength, TemperatureTrendStrengthScaling, "reference_strength_Pa", 1.0),
    ],
)
def test_changed_parameter_breaks_digest(builder, cls, field, value):
    raw = builder().model_dump()
    raw[field] = value
    with pytest.raises(ValueError, match="pin the complete"):
        cls.model_validate(raw)


@pytest.mark.parametrize(
    "builder,identifier",
    [
        (factor, "creep.declared_log_slope_rupture_factor"),
        (strength, "materials.temperature_trend_strength_scaling"),
    ],
)
def test_public_python_json_exchange(builder, identifier):
    x = builder()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="test", time_basis="instant")
    a = registry.run(identifier, x, context)
    b = registry.run_json(identifier, x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
