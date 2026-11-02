import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import FaradayLoss, faraday_loss
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        current_density_A_m2=1.0,
        molar_mass_kg_mol=0.055845,
        electrons_per_atom=2.0,
        density_kg_m3=7800.0,
        current_efficiency=1.0,
        duration_s=86400.0,
    )
    return FaradayLoss(**(raw | updates))


def test_standard_declared_dissolution_relation():
    result = faraday_loss(request())
    rate = 0.055845 / (2.0 * 96485.33212331001 * 7800.0)
    assert result.status == "computed"
    assert result.values["rate_m_s"] == pytest.approx(rate, rel=1e-14)
    assert result.values["penetration_m"] == pytest.approx(rate * 86400.0, rel=1e-14)


def test_large_intermediate_products_preserve_finite_ratio():
    result = faraday_loss(
        request(
            current_density_A_m2=1e100,
            molar_mass_kg_mol=1e308,
            electrons_per_atom=1e308,
            density_kg_m3=1e308,
            duration_s=1e200,
        )
    )
    assert result.status == "computed"
    assert result.values["rate_m_s"] == pytest.approx(1e-208 / 96485.33212331001, rel=1e-14, abs=0.0)


@pytest.mark.parametrize("changes", [{"current_density_A_m2": 0.0}, {"current_efficiency": 0.0}])
def test_declared_zero_is_exact_even_when_other_products_would_overflow(changes):
    result = faraday_loss(
        request(molar_mass_kg_mol=1e308, electrons_per_atom=1e308, density_kg_m3=1e308, **changes)
    )
    assert result.status == "computed"
    assert result.values == {"rate_m_s": 0.0, "penetration_m": 0.0}


@pytest.mark.parametrize(
    "changes",
    [
        {"current_density_A_m2": 1e-300, "molar_mass_kg_mol": 1e-300},
        {"current_density_A_m2": 1e300, "molar_mass_kg_mol": 1e300},
        {"current_density_A_m2": 1e300, "duration_s": 1e300},
    ],
)
def test_unrepresentable_required_output_is_not_zero_or_partial(changes):
    result = faraday_loss(request(**changes))
    assert result.status == "out_of_scope"
    assert "rate_m_s" not in result.values
    assert "penetration_m" not in result.values


def test_registry_python_json_exchange():
    x = request()
    registry = default_registry()
    model = "corrosion.faraday"
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )
