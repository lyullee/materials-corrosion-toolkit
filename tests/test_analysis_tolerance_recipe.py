import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    ChemicalToleranceBranch,
    DeclaredAnalysisToleranceRecipe,
    declared_analysis_tolerance_recipe,
)
from matintegrity.registry import default_registry


def request(value=0.25, **updates):
    raw = dict(
        element_id="X",
        product_specification_id="authored",
        analysis_kind="product_analysis",
        boundary_role="maximum",
        original_specified_limit_mass_fraction=value,
        service_tolerance_application_authorized=True,
        branches=(
            ChemicalToleranceBranch(
                branch_id="a",
                original_limit_lower=0.0,
                original_limit_upper=0.5,
                lower_inclusive=True,
                upper_inclusive=True,
                multiplier=0.125,
                offset_mass_fraction=0.03125,
            ),
            ChemicalToleranceBranch(
                branch_id="b",
                original_limit_lower=0.5,
                original_limit_upper=1.0,
                lower_inclusive=False,
                upper_inclusive=True,
                multiplier=0.0,
                offset_mass_fraction=0.125,
            ),
        ),
    )
    raw.update(updates)
    digest = canonical_digest(
        DeclaredAnalysisToleranceRecipe.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return DeclaredAnalysisToleranceRecipe(
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
                    citation="Authored affine branch cases.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "value,branch,tolerance", [(0.25, "a", 0.0625), (0.5, "a", 0.09375), (0.75, "b", 0.125)]
)
def test_explicit_original_boundary_and_inclusion(value, branch, tolerance):
    result = declared_analysis_tolerance_recipe(request(value))
    assert result.status == "computed"
    assert result.values["selected_branch_id"] == branch
    assert result.values["permitted_variation_mass_fraction"] == tolerance


@pytest.mark.parametrize("kind", ["gap", "overlap"])
def test_branch_gap_or_overlap_withholds_tolerance(kind):
    x = request()
    branches = (
        (x.branches[1],)
        if kind == "gap"
        else (x.branches[0], x.branches[0].model_copy(update={"branch_id": "duplicate-range"}))
    )
    assert declared_analysis_tolerance_recipe(request(branches=branches)).status == "out_of_scope"


def test_service_authority_is_required():
    assert (
        declared_analysis_tolerance_recipe(request(service_tolerance_application_authorized=False)).status
        == "needs_data"
    )


def test_lower_boundary_uses_its_own_original_value():
    result = declared_analysis_tolerance_recipe(request(0.125, boundary_role="minimum"))
    assert result.values["permitted_variation_mass_fraction"] == 0.046875


@pytest.mark.parametrize("offset", [-1.0, 2.0])
def test_invalid_calculated_tolerance_is_not_clipped(offset):
    x = request()
    branch = x.branches[0].model_copy(update={"offset_mass_fraction": offset})
    assert declared_analysis_tolerance_recipe(request(branches=(branch,))).status == "out_of_scope"


def test_python_json_exchange():
    x = request()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    registry = default_registry()
    a = registry.run("materials.declared_analysis_tolerance_recipe", x.model_dump(), context)
    b = registry.run_json("materials.declared_analysis_tolerance_recipe", x.model_dump_json(), context)
    assert a.values == b.values
