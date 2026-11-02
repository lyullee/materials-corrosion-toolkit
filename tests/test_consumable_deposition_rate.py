import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.engineering_correlations import (
    DeclaredConsumableDepositionRate,
    declared_consumable_deposition_rate,
)
from matintegrity.registry import default_registry


def request(**updates):
    raw = dict(
        process_id="authored-continuous-feed",
        consumable_condition_id="authored-material",
        material_cross_section_area_m2=0.002,
        material_density_kg_m3=1000.0,
        arc_on_feed_speed_m_s=0.5,
        captured_feed_mass_fraction=0.75,
        arc_on_time_fraction=0.25,
        feed_volume_basis="continuous_uniform_material_cross_section",
        cross_section_density_capture_and_time_basis_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(raw)
    return DeclaredConsumableDepositionRate(
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
                    citation="Authored mass-flux balance.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_feed_capture_and_clock_rates_are_distinct():
    result = declared_consumable_deposition_rate(request())
    assert result.values["arc_on_feed_mass_rate_kg_s"] == pytest.approx(1.0)
    assert result.values["arc_on_deposited_feed_mass_rate_kg_s"] == pytest.approx(0.75)
    assert result.values["clock_average_deposited_feed_mass_rate_kg_s"] == pytest.approx(0.1875)


@pytest.mark.parametrize(
    "updates,key",
    [
        ({"arc_on_feed_speed_m_s": 0.0}, "arc_on_feed_mass_rate_kg_s"),
        ({"captured_feed_mass_fraction": 0.0}, "arc_on_deposited_feed_mass_rate_kg_s"),
        ({"arc_on_time_fraction": 0.0}, "clock_average_deposited_feed_mass_rate_kg_s"),
    ],
)
def test_explicit_zero_modes_remain_zero(updates, key):
    assert declared_consumable_deposition_rate(request(**updates)).values[key] == 0.0


def test_intermediate_product_overflow_can_cancel_with_speed():
    result = declared_consumable_deposition_rate(
        request(
            material_cross_section_area_m2=1e200, material_density_kg_m3=1e200, arc_on_feed_speed_m_s=1e-200
        )
    )
    assert result.status == "computed"
    assert result.values["arc_on_feed_mass_rate_kg_s"] == pytest.approx(1e200)


@pytest.mark.parametrize(
    "updates",
    [
        {"material_cross_section_area_m2": 1e308, "material_density_kg_m3": 1e308},
        {"material_cross_section_area_m2": 1e-300, "material_density_kg_m3": 1e-300},
    ],
)
def test_unrepresentable_rates_return_scope_status(updates):
    assert declared_consumable_deposition_rate(request(**updates)).status == "out_of_scope"


def test_unknown_capture_or_time_basis_is_not_filled():
    assert (
        declared_consumable_deposition_rate(
            request(cross_section_density_capture_and_time_basis_reviewed=False)
        ).status
        == "needs_data"
    )


def test_digest_prevents_silent_capture_change():
    raw = request().model_dump()
    raw["captured_feed_mass_fraction"] = 0.5
    with pytest.raises(ValueError, match="pin the complete"):
        DeclaredConsumableDepositionRate(**raw)


def test_python_json_registry_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="a", location_id="l", time_basis="synthetic")
    a = registry.run("welding.declared_consumable_deposition_rate", x.model_dump(), context)
    b = registry.run_json("welding.declared_consumable_deposition_rate", x.model_dump_json(), context)
    assert a.values == b.values
