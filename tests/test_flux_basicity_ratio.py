import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredFluxBasicityRatio,
    declared_flux_basicity_ratio,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        flux_condition_id="authored-flux",
        index_definition_id="authored-ratio",
        input_mass_basis="mass_fraction",
        compound_assay={"compound-A": 0.25, "compound-B": 0.5},
        numerator_weights={"compound-A": 2.0},
        denominator_weights={"compound-B": 1.0},
    )
    raw.update(updates)
    digest = canonical_digest(raw)
    return DeclaredFluxBasicityRatio(
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
                    citation="Authored compound-ratio arithmetic.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "basis,scale", [("mass_fraction", 1.0), ("mass_percent", 100.0), ("mass_ppm", 1000000.0)]
)
def test_same_compound_mass_basis_scaling_preserves_ratio(basis, scale):
    result = declared_flux_basicity_ratio(
        request(
            input_mass_basis=basis, compound_assay={"compound-A": 0.25 * scale, "compound-B": 0.5 * scale}
        )
    )
    assert result.values["basicity_ratio"] == 1.0


def test_unknown_compound_is_not_zero():
    result = declared_flux_basicity_ratio(request(compound_assay={"compound-B": 0.5}))
    assert result.status == "needs_data"
    assert result.values["missing_compound_ids"] == ["compound-A"]


def test_measured_zero_denominator_is_undefined():
    assert (
        declared_flux_basicity_ratio(request(compound_assay={"compound-A": 0.25, "compound-B": 0.0})).status
        == "out_of_scope"
    )


def test_measured_zero_numerator_is_a_valid_zero_ratio():
    assert (
        declared_flux_basicity_ratio(request(compound_assay={"compound-A": 0.0, "compound-B": 0.5})).values[
            "basicity_ratio"
        ]
        == 0.0
    )


def test_weighted_sums_can_overflow_while_ratio_is_finite():
    result = declared_flux_basicity_ratio(
        request(
            input_mass_basis="mass_percent",
            compound_assay={"compound-A": 50.0, "compound-B": 50.0},
            numerator_weights={"compound-A": 1e308},
            denominator_weights={"compound-B": 1e308},
        )
    )
    assert result.status == "computed"
    assert result.values["basicity_ratio"] == 1.0
    assert result.values["weighted_numerator"] is None


def test_nonzero_ratio_underflow_is_not_reported_as_zero():
    result = declared_flux_basicity_ratio(
        request(
            compound_assay={"compound-A": 1e-300, "compound-B": 0.5}, numerator_weights={"compound-A": 1e-100}
        )
    )
    assert result.status == "out_of_scope"


def test_assay_mass_basis_and_positive_weight_side_are_validated():
    with pytest.raises(ValueError, match="mass basis"):
        request(compound_assay={"compound-A": 0.75, "compound-B": 0.5})
    with pytest.raises(ValueError, match="positive weight"):
        request(numerator_weights={"compound-A": 0.0})


def test_digest_pins_the_weight_definition():
    raw = request().model_dump()
    raw["numerator_weights"]["compound-A"] = 1.0
    with pytest.raises(ValueError, match="pin the complete"):
        DeclaredFluxBasicityRatio(**raw)


def test_python_json_registry_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    a = registry.run("welding.declared_flux_basicity_ratio", x.model_dump(), context)
    b = registry.run_json("welding.declared_flux_basicity_ratio", x.model_dump_json(), context)
    assert a.values == b.values
