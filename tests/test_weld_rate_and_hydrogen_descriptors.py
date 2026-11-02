import math

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredHydrogenSusceptibilityIndex,
    ThicknessScaledRateLimit,
    declared_hydrogen_susceptibility_index,
    thickness_scaled_rate_limit,
)
from matintegrity.registry import default_registry


def bind(cls, raw):
    digest = canonical_digest(cls.model_construct(**raw).model_dump(mode="json", exclude={"basis"}))
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
                    citation="authored descriptor arithmetic",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def rate(**updates):
    raw = dict(
        component_id="part",
        procedure_id="authored",
        rate_direction="heating",
        governing_thickness_m=0.04,
        minimum_supported_thickness_m=0.001,
        maximum_supported_thickness_m=1.0,
        reference_thickness_m=0.04,
        reference_rate_K_s=0.5,
        ceiling_rate_K_s=1.0,
        metal_temperature_K=600.0,
        activation_temperature_K=500.0,
        activation_comparison="greater_than",
    )
    return bind(ThicknessScaledRateLimit, raw | updates)


def hydrogen(**updates):
    raw = dict(
        material_condition_id="steel",
        composition_index_definition_id="authored-index",
        composition_index_mass_percent=0.2,
        hydrogen_definition_id="authored-volume-concentration",
        hydrogen_input_kind="measured_quantity",
        hydrogen_unit_token="authored-volume/mass",
        hydrogen_value=10.0,
        hydrogen_reference_value=1.0,
        composition_coefficient=2.0,
        logarithmic_coefficient=3.0,
        constant_offset=-1.0,
    )
    return bind(DeclaredHydrogenSusceptibilityIndex, raw | updates)


@pytest.mark.parametrize("thickness,expected", [(0.01, 1.0), (0.02, 1.0), (0.08, 0.25)])
def test_inverse_thickness_and_ceiling(thickness, expected):
    r = thickness_scaled_rate_limit(rate(governing_thickness_m=thickness))
    assert r.status == "computed"
    assert r.values["maximum_rate_K_s"] == expected
    if thickness == 0.02:
        assert r.values["controlling_terms"] == ["thickness_scaled", "ceiling"]


@pytest.mark.parametrize(
    "temperature,comparison,active",
    [(499.0, "greater_than", False), (500.0, "greater_than", False), (500.0, "greater_or_equal", True)],
)
def test_activation_does_not_grant_permission_when_inactive(temperature, comparison, active):
    r = thickness_scaled_rate_limit(rate(metal_temperature_K=temperature, activation_comparison=comparison))
    assert r.values["rule_active"] is active
    if not active:
        assert r.values["maximum_rate_K_s"] is None


def test_thickness_support_and_zero_limit():
    assert thickness_scaled_rate_limit(rate(governing_thickness_m=2.0)).status == "out_of_scope"
    assert thickness_scaled_rate_limit(rate(ceiling_rate_K_s=0.0)).values["maximum_rate_K_s"] == 0.0


def test_unused_unrepresentable_inverse_candidate_retains_finite_ceiling():
    r = thickness_scaled_rate_limit(
        rate(
            governing_thickness_m=1e-300,
            minimum_supported_thickness_m=1e-300,
            reference_thickness_m=1e300,
            reference_rate_K_s=1e300,
        )
    )
    assert r.values["maximum_rate_K_s"] == 1.0
    assert r.values["uncapped_rate_K_s"] is None
    assert r.values["uncapped_rate_representable"] is False


def test_positive_limit_underflow_does_not_become_zero():
    r = thickness_scaled_rate_limit(rate(reference_rate_K_s=1e-300, reference_thickness_m=1e-300))
    assert r.status == "out_of_scope"


def test_composition_plus_log_ratio_preserves_signed_descriptor():
    r = declared_hydrogen_susceptibility_index(hydrogen())
    assert r.status == "computed"
    assert r.values["index_value"] == pytest.approx(2.4)
    assert declared_hydrogen_susceptibility_index(hydrogen(constant_offset=-10.0)).values["index_value"] < 0.0


def test_near_unity_ratio_retains_small_nonzero_log():
    h = math.nextafter(1e300, math.inf)
    r = declared_hydrogen_susceptibility_index(hydrogen(hydrogen_value=h, hydrogen_reference_value=1e300))
    expected = math.log1p((h - 1e300) / 1e300) / math.log(10.0)
    assert r.values["log10_hydrogen_ratio"] == expected > 0.0


@pytest.mark.parametrize("h,reference,expected", [(1e300, 1e-300, 600.0), (1e-300, 1e300, -600.0)])
def test_extreme_ratio_does_not_overflow_or_underflow(h, reference, expected):
    r = declared_hydrogen_susceptibility_index(hydrogen(hydrogen_value=h, hydrogen_reference_value=reference))
    assert r.status == "computed"
    assert r.values["log10_hydrogen_ratio"] == expected


def test_category_is_dimensionless_and_zero_hydrogen_is_invalid():
    with pytest.raises(ValueError, match="dimensionless"):
        hydrogen(hydrogen_input_kind="declared_category_value")
    with pytest.raises(ValueError):
        hydrogen(hydrogen_value=0.0)
    r = declared_hydrogen_susceptibility_index(
        hydrogen(hydrogen_input_kind="declared_category_value", hydrogen_unit_token="1")
    )
    assert r.values["hydrogen_input_kind"] == "declared_category_value"


def test_nonfinite_descriptor_is_withheld():
    assert (
        declared_hydrogen_susceptibility_index(
            hydrogen(logarithmic_coefficient=1e308, hydrogen_value=1e300)
        ).status
        == "out_of_scope"
    )


@pytest.mark.parametrize(
    "builder,cls,field,value",
    [
        (rate, ThicknessScaledRateLimit, "ceiling_rate_K_s", 2.0),
        (hydrogen, DeclaredHydrogenSusceptibilityIndex, "hydrogen_reference_value", 2.0),
    ],
)
def test_parameter_changes_break_digest(builder, cls, field, value):
    raw = builder().model_dump()
    raw[field] = value
    with pytest.raises(ValueError, match="pin the complete"):
        cls.model_validate(raw)


@pytest.mark.parametrize(
    "builder,identifier",
    [
        (rate, "thermal.thickness_scaled_rate_limit"),
        (hydrogen, "welding.declared_hydrogen_susceptibility_index"),
    ],
)
def test_public_python_json_exchange(builder, identifier):
    x = builder()
    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="part", time_basis="authored")
    a = registry.run(identifier, x, context)
    b = registry.run_json(identifier, x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
