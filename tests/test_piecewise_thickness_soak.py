import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    PiecewiseThicknessSoakDuration,
    ThicknessSoakBand,
    piecewise_thickness_soak_duration,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        component_id="part",
        procedure_id="authored",
        governing_thickness_m=0.08,
        minimum_supported_thickness_m=0.005,
        baseline_time_s=100.0,
        minimum_soak_time_s=0.0,
        thickness_bands=(
            ThicknessSoakBand(band_id="first", upper_thickness_m=0.04, slope_s_per_m=10000.0),
            ThicknessSoakBand(band_id="second", upper_thickness_m=0.2, slope_s_per_m=2000.0),
        ),
    )
    raw.update(updates)
    digest = canonical_digest(
        PiecewiseThicknessSoakDuration.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return PiecewiseThicknessSoakDuration(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            computational_use_authorized=True,
            applicability_and_units_reviewed=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="authored soak arithmetic",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize("thickness,expected", [(0.02, 300.0), (0.04, 500.0), (0.08, 580.0), (0.2, 820.0)])
def test_cumulative_band_integral_at_and_between_boundaries(thickness, expected):
    r = piecewise_thickness_soak_duration(request(governing_thickness_m=thickness))
    assert r.status == "computed"
    assert r.values["recipe_soak_time_s"] == pytest.approx(expected)
    assert sum(row["applied_thickness_m"] for row in r.values["band_contributions"]) == pytest.approx(
        thickness
    )


def test_minimum_time_and_exact_tie_retain_controlling_terms():
    assert piecewise_thickness_soak_duration(request(minimum_soak_time_s=600.0)).values[
        "controlling_terms"
    ] == ["minimum"]
    assert piecewise_thickness_soak_duration(request(minimum_soak_time_s=580.0)).values[
        "controlling_terms"
    ] == ["recipe", "minimum"]


@pytest.mark.parametrize("thickness", [0.001, 0.21])
def test_support_is_bounded(thickness):
    assert (
        piecewise_thickness_soak_duration(request(governing_thickness_m=thickness)).status == "out_of_scope"
    )


def test_reversed_band_bounds_are_rejected():
    with pytest.raises(ValueError, match="strictly increase"):
        request(thickness_bands=tuple(reversed(request().thickness_bands)))


@pytest.mark.parametrize("width,slope", [(1e308, 1e308), (1e-300, 1e-300)])
def test_unsupported_band_arithmetic_is_withheld(width, slope):
    x = request(
        governing_thickness_m=width,
        minimum_supported_thickness_m=0.0,
        thickness_bands=(ThicknessSoakBand(band_id="a", upper_thickness_m=width, slope_s_per_m=slope),),
    )
    assert piecewise_thickness_soak_duration(x).status == "out_of_scope"


def test_recipe_tampering_invalidates_identity():
    raw = request().model_dump()
    raw["baseline_time_s"] = 200.0
    with pytest.raises(ValueError, match="pin the complete"):
        PiecewiseThicknessSoakDuration.model_validate(raw)


def test_public_python_json_exchange():
    registry = default_registry()
    x = request()
    context = RunContext(asset_id="synthetic", location_id="part", time_basis="authored")
    a = registry.run("thermal.piecewise_thickness_soak_duration", x, context)
    b = registry.run_json("thermal.piecewise_thickness_soak_duration", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
