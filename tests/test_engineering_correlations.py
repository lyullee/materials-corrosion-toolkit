import pytest
from pydantic import ValidationError

from matintegrity.contracts import canonical_digest
from matintegrity.models.engineering_correlations import (
    CouplingPressure,
    FluxMoistureHydrogen,
    PipingDisplacementAllowance,
    ThreadConnectionPressure,
    WeldCoolingCorrelation,
    coupling_pressure,
    flux_moisture_hydrogen,
    piping_displacement_allowance,
    thread_connection_pressure,
    weld_cooling_correlation,
)


def bound(contract, payload):
    # Fill declared defaults via Pydantic's static field metadata before hashing.
    complete = {
        key: field.default
        for key, field in contract.model_fields.items()
        if key != "basis" and not field.is_required()
    }
    complete.update(payload)
    digest = canonical_digest(complete)
    return contract(
        **complete,
        basis={
            "source_id": "synthetic-parameters",
            "revision": "1",
            "license_id": "synthetic-example",
            "record_sha256": digest,
            "evidence": (
                {
                    "source_id": "synthetic-parameters",
                    "origin": "synthetic",
                    "citation": "Synthetic arithmetic verification only.",
                    "license_id": "synthetic-example",
                    "sha256": digest,
                },
            ),
            "applicability_and_units_reviewed": True,
            "computational_use_authorized": True,
        },
    )


@pytest.mark.parametrize(
    "variant,sustained,expected",
    [
        ("base", None, 90e6),
        ("with_sustained_stress", 20e6, 80e6),
    ],
)
def test_displacement_variants_preserve_declared_linear_stress_balance(variant, sustained, expected):
    request = bound(
        PipingDisplacementAllowance,
        {
            "variant": variant,
            "cold_allowable_Pa": 100e6,
            "hot_allowable_Pa": 80e6,
            "cycle_reduction_factor": 0.5,
            "cold_multiplier": 1.0,
            "hot_multiplier": 1.0,
            "sustained_stress_Pa": sustained,
        },
    )
    assert piping_displacement_allowance(request).values[
        "allowable_displacement_stress_range_Pa"
    ] == pytest.approx(expected)


def cooling(dimension, heat=1000.0):
    return bound(
        WeldCoolingCorrelation,
        {
            "heat_flow_dimension": dimension,
            "preheat_temperature_K": 300.0,
            "lower_temperature_K": 500.0,
            "upper_temperature_K": 800.0,
            "net_heat_input_J_m": heat,
            "plate_thickness_m": 0.01 if dimension == 2 else None,
            "shape_factor": 1.0,
            "coefficient_reference_temperature_K": 300.0,
            "coefficient_at_reference": 0.001 if dimension == 2 else 10.0,
            "coefficient_temperature_slope_per_K": 0.0,
            "coefficient_unit": "s*m^4*K^2/J^2" if dimension == 2 else "s*m*K/J",
            "minimum_valid_preheat_K": 290.0,
            "maximum_valid_preheat_K": 400.0,
        },
    )


@pytest.mark.parametrize("dimension,expected,multiplier", [(2, 210.0, 4.0), (3, 30.0, 2.0)])
def test_cooling_dimensions_have_distinct_energy_scaling(dimension, expected, multiplier):
    base = weld_cooling_correlation(cooling(dimension)).values["cooling_interval_s"]
    double = weld_cooling_correlation(cooling(dimension, 2000.0)).values["cooling_interval_s"]
    assert base == pytest.approx(expected)
    assert double == pytest.approx(multiplier * base)


def test_flux_volume_reference_and_mass_normalization_are_preserved():
    request = bound(
        FluxMoistureHydrogen,
        {
            "combined_water_mass_fraction": 0.02,
            "absorbed_water_mass_fraction": 0.01,
            "water_vapor_partial_pressure_Pa": 1000.0,
            "intercept_m3_H2_kg_deposit": 0.0,
            "combined_water_coefficient_m3_H2_kg_deposit": 0.01,
            "absorbed_water_coefficient_m3_H2_kg_deposit": 0.02,
            "vapor_coefficient_m3_H2_kg_deposit_Pa": 1e-8,
            "maximum_valid_combined_water_fraction": 0.1,
            "maximum_valid_absorbed_water_fraction": 0.1,
            "maximum_valid_vapor_pressure_Pa": 2000.0,
            "gas_volume_reference_temperature_K": 300.0,
            "gas_volume_reference_pressure_Pa": 100000.0,
        },
    )
    result = flux_moisture_hydrogen(request)
    assert result.values["hydrogen_volume_m3_H2_kg_deposit"] == pytest.approx(0.00041)
    assert result.values["hydrogen_volume_ml_H2_100g_deposit"] == pytest.approx(41.0)
    assert result.values["gas_volume_reference_temperature_K"] == 300.0


def test_coupling_and_thread_geometry_scale_without_changing_pressure():
    for scale in (1.0, 10.0):
        coupling = bound(
            CouplingPressure,
            {
                "outside_diameter_m": 0.2 * scale,
                "thread_root_diameter_m": 0.1 * scale,
                "yield_strength_Pa": 400e6,
                "declared_strength_factor": 0.8,
            },
        )
        thread = bound(
            ThreadConnectionPressure,
            {
                "outside_diameter_m": 0.2 * scale,
                "seal_pitch_diameter_m": 0.1 * scale,
                "elastic_modulus_Pa": 200e9,
                "diametral_taper_m_m": 0.1,
                "power_turn_count": 2.0,
                "thread_pitch_m_per_turn": 0.001 * scale,
            },
        )
        assert coupling_pressure(coupling).values["coupling_pressure_Pa"] == pytest.approx(160e6)
        assert thread_connection_pressure(thread).values[
            "connection_pressure_resistance_Pa"
        ] == pytest.approx(150e6)


def test_changed_record_or_wrong_coefficient_unit_is_rejected():
    request = cooling(2).model_dump(mode="python")
    request["net_heat_input_J_m"] = 2000.0
    with pytest.raises(ValidationError):
        WeldCoolingCorrelation(**request)
    request = cooling(2).model_dump(mode="python", exclude={"basis"})
    request["coefficient_unit"] = "s*m*K/J"
    with pytest.raises(ValidationError):
        bound(WeldCoolingCorrelation, request)


def test_new_correlation_specifications_are_in_public_registry():
    from matintegrity.contracts import RunContext
    from matintegrity.registry import default_registry

    registry = default_registry()
    result = registry.run(
        "welding.cooling_time_correlation",
        cooling(2).model_dump(mode="python"),
        RunContext(asset_id="synthetic", location_id="weld", time_basis="test"),
    )
    assert result.status == "computed"
    assert result.values["cooling_interval_s"] == pytest.approx(210.0)


@pytest.mark.parametrize("heat,coefficient,expected", [(1e200, 1e-300, 2.1e99), (1e-200, 1e300, 2.1e-101)])
def test_cooling_2d_retains_representable_result_after_extreme_intermediate(heat, coefficient, expected):
    payload = cooling(2).model_dump(mode="json", exclude={"basis"})
    payload.update(net_heat_input_J_m=heat, coefficient_at_reference=coefficient)
    result = weld_cooling_correlation(bound(WeldCoolingCorrelation, payload))
    assert result.status == "computed"
    assert result.values["cooling_interval_s"] == pytest.approx(expected)


@pytest.mark.parametrize("heat,coefficient", [(1e300, 1e300), (1e-300, 1e-300)])
def test_cooling_unrepresentable_final_result_is_withheld(heat, coefficient):
    payload = cooling(2).model_dump(mode="json", exclude={"basis"})
    payload.update(net_heat_input_J_m=heat, coefficient_at_reference=coefficient)
    result = weld_cooling_correlation(bound(WeldCoolingCorrelation, payload))
    assert result.status == "out_of_scope"
    assert "cooling_interval_s" not in result.values

