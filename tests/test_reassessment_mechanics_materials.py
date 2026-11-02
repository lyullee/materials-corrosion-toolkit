import math

import numpy as np
import pytest
from scipy.constants import Avogadro, elementary_charge

from matintegrity.models.materials import (
    DissolutionCharge,
    DuctilityComparison,
    TensilePoint,
    dissolution_charge,
    ductility_comparison,
    tensile_point,
)
from matintegrity.models.mechanics import (
    Cylinder,
    PlaneStress,
    StressIntensity,
    ThermalRestraint,
    lame_cylinder,
    plane_stress,
    stress_intensity,
    thermal_restraint,
)


@pytest.mark.parametrize("radius", [0.1, 0.15, 0.2])
def test_hydrostatic_lame_is_uniform_with_zero_deviatoric_stress(radius):
    result = lame_cylinder(
        Cylinder(
            inner_radius_m=0.1,
            outer_radius_m=0.2,
            internal_pressure_Pa=5e6,
            external_pressure_Pa=5e6,
            evaluation_radius_m=radius,
            closed_ends=True,
        )
    )
    assert [
        result.values[key] for key in ("hoop_stress_Pa", "radial_stress_Pa", "axial_stress_Pa")
    ] == pytest.approx([-5e6] * 3)
    assert result.values["von_mises_Pa"] == pytest.approx(0.0, abs=1e-8)


@pytest.mark.parametrize("sx,sy,shear", [(10.0, 0.0, 0.0), (0.0, 0.0, 10.0), (7.0, -3.0, 4.0)])
def test_plane_stress_against_independent_tensor_eigensolution(sx, sy, shear):
    matrix = np.array([[sx, shear, 0.0], [shear, sy, 0.0], [0.0, 0.0, 0.0]])
    in_plane = np.linalg.eigvalsh(matrix[:2, :2])
    deviator = matrix - np.eye(3) * np.trace(matrix) / 3
    result = plane_stress(PlaneStress(stress_x_Pa=sx, stress_y_Pa=sy, shear_xy_Pa=shear))
    assert result.values["principal_min_Pa"] == pytest.approx(in_plane[0])
    assert result.values["principal_max_Pa"] == pytest.approx(in_plane[1])
    assert result.values["von_mises_Pa"] == pytest.approx(math.sqrt(1.5 * np.sum(deviator * deviator)))


def test_thermal_restraint_free_boundary_and_heating_cooling_symmetry():
    x = ThermalRestraint(
        young_modulus_Pa=200e9,
        expansion_coefficient_per_K=1e-5,
        temperature_change_K=100.0,
        restraint_fraction=0.25,
    )
    hot = thermal_restraint(x)
    cold = thermal_restraint(x.model_copy(update={"temperature_change_K": -100.0}))
    free = thermal_restraint(x.model_copy(update={"restraint_fraction": 0.0}))
    assert hot.values["restrained_uniaxial_stress_Pa"] < 0
    assert cold.values["restrained_uniaxial_stress_Pa"] == -hot.values["restrained_uniaxial_stress_Pa"]
    assert free.values["restrained_uniaxial_stress_Pa"] == 0.0


def test_mode_i_length_scaling_and_zero_load_does_not_invent_critical_depth():
    x = StressIntensity(
        crack_depth_m=0.001, tensile_stress_Pa=100e6, geometry_factor=1.2, fracture_toughness_Pa_sqrt_m=50e6
    )
    base = stress_intensity(x)
    scaled = stress_intensity(x.model_copy(update={"crack_depth_m": 0.004}))
    assert scaled.values["stress_intensity_Pa_sqrt_m"] == pytest.approx(
        2 * base.values["stress_intensity_Pa_sqrt_m"]
    )
    at_critical = stress_intensity(x.model_copy(update={"crack_depth_m": base.values["critical_depth_m"]}))
    assert at_critical.values["toughness_margin_Pa_sqrt_m"] == pytest.approx(0.0, abs=1e-7)
    zero = stress_intensity(x.model_copy(update={"tensile_stress_Pa": 0.0}))
    assert zero.values["critical_depth_m"] is None


def test_tensile_force_equilibrium_and_necking_scope():
    x = TensilePoint(
        force_N=1000.0,
        initial_area_m2=1e-4,
        extension_m=0.01,
        gauge_length_m=0.1,
        uniform_deformation_declared=True,
    )
    values = tensile_point(x).values
    current_area = x.initial_area_m2 * x.gauge_length_m / (x.gauge_length_m + x.extension_m)
    assert values["true_stress_Pa"] * current_area == pytest.approx(x.force_N)
    assert math.exp(values["true_strain"]) == pytest.approx(1 + values["engineering_strain"])
    unreviewed = tensile_point(x.model_copy(update={"uniform_deformation_declared": False})).values
    assert "true_stress_Pa" not in unreviewed and "true_strain" not in unreviewed


def test_ductility_gain_is_signed_instead_of_clipped():
    result = ductility_comparison(
        DuctilityComparison(baseline_elongation_fraction=0.2, exposed_elongation_fraction=0.3)
    )
    assert result.values["ductility_retention_ratio"] == pytest.approx(1.5)
    assert result.values["relative_ductility_loss"] == pytest.approx(-0.5)


def test_charge_loss_against_si_charge_per_mole_and_volume_closure():
    charge_per_mole = elementary_charge * Avogadro
    x = DissolutionCharge(
        anodic_charge_C=charge_per_mole,
        equivalent_weight_kg_mol_electron=0.02,
        density_kg_m3=8000.0,
        current_efficiency=0.5,
    )
    result = dissolution_charge(x)
    assert result.values["dissolved_mass_kg"] == pytest.approx(0.01)
    assert result.values["dissolved_volume_m3"] * x.density_kg_m3 == pytest.approx(
        result.values["dissolved_mass_kg"]
    )
