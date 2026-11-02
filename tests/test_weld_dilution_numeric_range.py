import math

import pytest

from matintegrity.models.quality import (
    WeldDilution,
    WeldDilutionUncertainty,
    weld_dilution,
    weld_dilution_with_uncertainty,
)


def request(uncertain=False, masses=(1e308, 1e308), compositions=(0.25, 0.75), **updates):
    rows = [
        dict(
            material_id=str(i), role=role, melted_mass_kg=mass, composition_mass_fraction={"Cr": composition}
        )
        for i, (role, mass, composition) in enumerate(
            zip(("base", "filler"), masses, compositions, strict=True)
        )
    ]
    raw = dict(constituents=rows, requested_elements=["Cr"])
    if uncertain:
        for row in rows:
            row.update(source_id="authored", record_sha256="a" * 64)
        raw.update(
            constituents=tuple(rows),
            requested_elements=("Cr",),
            melted_mass_and_roles_reviewed=True,
            composition_records_and_mass_basis_reviewed=True,
            covariance_basis_and_variable_order_reviewed=True,
        )
    raw.update(updates)
    return (WeldDilutionUncertainty if uncertain else WeldDilution)(**raw)


@pytest.mark.parametrize("uncertain", [False, True])
def test_large_total_mass_retains_finite_mixed_composition(uncertain):
    result = (weld_dilution_with_uncertainty if uncertain else weld_dilution)(request(uncertain))
    assert result.status == "computed"
    assert result.values["total_melted_mass_kg"] is None
    assert result.values["mixed_composition_mass_fraction"]["Cr"] == 0.5
    assert result.values["role_mass_fractions"]["base"] == 0.5


@pytest.mark.parametrize("uncertain", [False, True])
def test_uniform_mass_scaling_does_not_change_composition(uncertain):
    fn = weld_dilution_with_uncertainty if uncertain else weld_dilution
    assert fn(request(uncertain, masses=(1e-300, 3e-300))).values["mixed_composition_mass_fraction"][
        "Cr"
    ] == pytest.approx(0.625)


@pytest.mark.parametrize("uncertain", [False, True])
def test_missing_composition_is_not_zero(uncertain):
    result = (weld_dilution_with_uncertainty if uncertain else weld_dilution)(
        request(uncertain, compositions=(None, 0.75))
    )
    assert result.values["mixed_composition_mass_fraction"]["Cr"] is None
    assert result.values["constituents_missing_element_evidence"]["Cr"] == ["0"]


def test_covariance_propagation_uses_supported_weights_when_total_overflows():
    x = request(
        True,
        joint_composition_covariance=[[0.04, 0.0], [0.0, 0.16]],
        covariance_variable_order=("0:Cr", "1:Cr"),
        covariance_basis="authored joint assays",
        uncertainty_coverage_factor=2.0,
    )
    result = weld_dilution_with_uncertainty(x)
    assert result.status == "computed"
    assert result.values["propagated_covariance_mass_fraction_squared"][0][0] == pytest.approx(0.05)
    assert result.values["expanded_uncertainty_mass_fraction"]["Cr"] == pytest.approx(2 * math.sqrt(0.05))


@pytest.mark.parametrize("uncertain", [False, True])
def test_nonzero_role_or_constituent_underflow_is_not_silent(uncertain):
    result = (weld_dilution_with_uncertainty if uncertain else weld_dilution)(
        request(uncertain, masses=(1e-300, 1e300))
    )
    assert result.status == "out_of_scope"
