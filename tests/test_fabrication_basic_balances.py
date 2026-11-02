import pytest
from pydantic import ValidationError

from matintegrity.models.fabrication import (
    BendStrain,
    BoltPreload,
    CoatingCoverage,
    ConductionLayers,
    MeasuredPipeOvality,
    bend_strain,
    bolt_preload,
    coating_coverage,
    conduction_layers,
    measured_pipe_ovality,
)


def test_bending_fiber_strain_is_invariant_under_uniform_geometry_scaling():
    for scale in (1.0, 1000.0):
        result = bend_strain(BendStrain(outside_diameter_m=0.1 * scale,
                                      centerline_bend_radius_m=0.5 * scale))
        assert result.values["outer_fiber_strain"] == pytest.approx(0.1)


def test_bolt_preload_closes_torque_and_tensile_force_balance():
    result = bolt_preload(BoltPreload(torque_N_m=100.0, nominal_diameter_m=0.02,
                                    nut_factor=0.2, tensile_area_m2=1e-4))
    assert result.values["preload_N"] == pytest.approx(25_000.0)
    assert result.values["preload_N"] * 0.2 * 0.02 == pytest.approx(100.0)
    assert result.values["nominal_tensile_stress_Pa"] * 1e-4 == pytest.approx(25_000.0)


def test_required_wet_coating_preserves_deposited_solid_volume():
    result = coating_coverage(CoatingCoverage(area_m2=10.0, dry_thickness_m=1e-4,
                                            volume_solids_fraction=0.5, transfer_efficiency=0.8))
    assert result.values["required_wet_volume_m3"] == pytest.approx(0.0025)
    assert result.values["required_wet_volume_m3"] * 0.5 * 0.8 == pytest.approx(0.001)
    assert result.values["dry_volume_m3"] == pytest.approx(0.001)


def test_series_thermal_resistance_is_unchanged_by_splitting_a_layer():
    for thickness, conductivity in (([0.1, 0.2], [1.0, 2.0]), ([0.1, 0.1, 0.1], [1.0, 2.0, 2.0])):
        result = conduction_layers(ConductionLayers(thickness_m=thickness, conductivity_W_m_K=conductivity,
                                                    area_m2=2.0, temperature_difference_K=-20.0))
        assert result.values["thermal_resistance_K_W"] == pytest.approx(0.1)
        assert result.values["heat_rate_W"] == pytest.approx(-200.0)


@pytest.mark.parametrize("basis,nominal,expected", [("nominal", 0.105, 0.02 / 0.105),
                                                   ("mean_measured", None, 0.2)])
def test_ovality_preserves_declared_denominator(basis, nominal, expected):
    result = measured_pipe_ovality(MeasuredPipeOvality(maximum_diameter_m=0.11, minimum_diameter_m=0.09,
                                                     reference_basis=basis, nominal_diameter_m=nominal))
    assert result.values["ovality_fraction"] == pytest.approx(expected)
    assert result.values["ovality_percent"] == pytest.approx(100.0 * expected)


@pytest.mark.parametrize("maximum,minimum,nominal", [(0.09, 0.11, 0.1), (0.11, 0.09, None)])
def test_reversed_measurements_or_missing_reference_are_rejected(maximum, minimum, nominal):
    with pytest.raises(ValidationError):
        MeasuredPipeOvality(maximum_diameter_m=maximum, minimum_diameter_m=minimum,
                           reference_basis="nominal", nominal_diameter_m=nominal)
