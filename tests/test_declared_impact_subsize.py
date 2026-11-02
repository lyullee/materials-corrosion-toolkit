import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredImpactSubsizeRequirements,
    ImpactWidthTemperatureReduction,
    declared_impact_subsize_requirements,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        method_id="authored-requirement",
        material_condition_id="authored-state",
        specimen_geometry_definition_id="authored-width-normal",
        specimen_width_m=0.006,
        reference_specimen_width_m=0.012,
        reference_required_mean_energy_J=40.0,
        reference_required_individual_energy_J=30.0,
        reference_test_temperature_K=250.0,
        width_temperature_reduction_table=(
            ImpactWidthTemperatureReduction(specimen_width_m=0.003, temperature_reduction_K=24.0),
            ImpactWidthTemperatureReduction(specimen_width_m=0.009, temperature_reduction_K=6.0),
            ImpactWidthTemperatureReduction(specimen_width_m=0.012, temperature_reduction_K=0.0),
        ),
        linear_width_energy_requirement_scaling_reviewed=True,
        temperature_table_interpolation_and_applicability_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        DeclaredImpactSubsizeRequirements.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return DeclaredImpactSubsizeRequirements(
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
                    citation="authored test requirements",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_linear_requirement_scaling_and_bounded_temperature_interpolation():
    r = declared_impact_subsize_requirements(request())
    assert r.status == "computed"
    assert r.values["required_mean_energy_J"] == 20.0
    assert r.values["required_individual_energy_J"] == 15.0
    assert r.values["required_test_temperature_K"] == pytest.approx(235.0)
    assert r.values["interpolation_width_bracket_m"] == [0.003, 0.009]


@pytest.mark.parametrize("width,reduction", [(0.003, 24.0), (0.009, 6.0), (0.012, 0.0)])
def test_exact_table_knots(width, reduction):
    r = declared_impact_subsize_requirements(request(specimen_width_m=width))
    assert r.values["temperature_reduction_K"] == reduction
    assert r.values["interpolation_width_bracket_m"] == [width, width]


def test_table_extrapolation_is_withheld():
    assert declared_impact_subsize_requirements(request(specimen_width_m=0.002)).status == "out_of_scope"


def test_missing_linear_scaling_review_withholds_requirements():
    r = declared_impact_subsize_requirements(request(linear_width_energy_requirement_scaling_reviewed=False))
    assert r.status == "needs_data"
    assert "required_mean_energy_J" not in r.values


def test_invalid_absolute_temperature_is_withheld():
    assert (
        declared_impact_subsize_requirements(request(reference_test_temperature_K=10.0)).status
        == "out_of_scope"
    )


def test_table_and_reference_width_are_checked():
    with pytest.raises(ValueError, match="reference width"):
        request(specimen_width_m=0.02)
    with pytest.raises(ValueError, match="strictly increase"):
        request(
            width_temperature_reduction_table=tuple(reversed(request().width_temperature_reduction_table))
        )


def test_requirement_tampering_invalidates_digest():
    raw = request().model_dump()
    raw["reference_required_mean_energy_J"] = 80.0
    with pytest.raises(ValueError, match="pin the complete"):
        DeclaredImpactSubsizeRequirements.model_validate(raw)


def test_public_python_json_exchange():
    registry = default_registry()
    x = request()
    context = RunContext(asset_id="synthetic", location_id="impact", time_basis="authored")
    a = registry.run("inspection.declared_impact_subsize_requirements", x, context)
    b = registry.run_json("inspection.declared_impact_subsize_requirements", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
