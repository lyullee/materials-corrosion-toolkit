"""Physical identities and changes of scale, independent of fitted material truth."""

import copy
import json
import math
from functools import lru_cache
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
BASELINES = json.loads(
    (ROOT / "tests/data/core_physics_valid_input_baselines.json").read_text(encoding="utf8")
)["model_inputs"]
EXAMPLES = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf8"))["models"]


@lru_cache(maxsize=1)
def registry():
    return default_registry()


def run(model, **changes):
    payload = copy.deepcopy(BASELINES.get(model, EXAMPLES.get(model, {})))
    payload.update(changes)
    result = registry().run_json(
        model,
        json.dumps(payload),
        RunContext(asset_id="authored", location_id="authored", time_basis="physical identity check"),
    )
    assert result.status == "computed", result.values
    return result.values


@pytest.mark.parametrize("current_factor,time_factor", [(0.0, 2.0), (0.25, 4.0), (2.0, 0.5), (10.0, 0.1)])
def test_group02_faraday_equal_charge_equal_penetration(current_factor, time_factor):
    p = BASELINES["corrosion.faraday"]
    reference = run("corrosion.faraday")
    actual = run(
        "corrosion.faraday",
        current_density_A_m2=p["current_density_A_m2"] * current_factor,
        duration_s=p["duration_s"] * time_factor,
    )
    # Integral of current per area, not elapsed time alone, determines removed volume.
    key = "penetration_m"
    assert actual[key] == pytest.approx(reference[key] * current_factor * time_factor, rel=1e-13, abs=1e-25)


@pytest.mark.parametrize("factor", [0.1, 0.5, 2.0, 10.0])
def test_group03_polarization_resistance_is_inverse_current(factor):
    a = run("corrosion.stern_geary")
    b = run("corrosion.stern_geary", area_normalized_resistance_ohm_m2=factor)
    assert b["corrosion_current_density_A_m2"] * factor == pytest.approx(a["corrosion_current_density_A_m2"])


@pytest.mark.parametrize("offset", [0.0, 1e5, 1e7])
def test_group26_common_pressure_offset_is_hydrostatic_for_closed_ends(offset):
    args = dict(
        inner_radius_m=0.05,
        outer_radius_m=0.06,
        evaluation_radius_m=0.055,
        internal_pressure_Pa=2e6,
        external_pressure_Pa=1e5,
        closed_ends=True,
    )
    a = run("mechanics.lame_cylinder", **args)
    b = run(
        "mechanics.lame_cylinder",
        **(
            args
            | dict(
                internal_pressure_Pa=args["internal_pressure_Pa"] + offset,
                external_pressure_Pa=args["external_pressure_Pa"] + offset,
            )
        ),
    )
    for quantity in ("hoop_stress_Pa", "radial_stress_Pa", "axial_stress_Pa"):
        assert b[quantity] == pytest.approx(a[quantity] - offset)
    assert b["von_mises_Pa"] == pytest.approx(a["von_mises_Pa"])


@pytest.mark.parametrize("angle", [0.0, 0.17, math.pi / 4, math.pi / 2, 2.1])
def test_group27_plane_rotation_preserves_principal_stresses_and_von_mises(angle):
    sx, sy, shear = 120e6, -30e6, 40e6
    c, s = math.cos(angle), math.sin(angle)
    a = run("mechanics.plane_stress", stress_x_Pa=sx, stress_y_Pa=sy, shear_xy_Pa=shear)
    b = run(
        "mechanics.plane_stress",
        stress_x_Pa=c * c * sx + s * s * sy + 2 * c * s * shear,
        stress_y_Pa=s * s * sx + c * c * sy - 2 * c * s * shear,
        shear_xy_Pa=c * s * (sy - sx) + (c * c - s * s) * shear,
    )
    assert b == pytest.approx(a)


@pytest.mark.parametrize("thickness_ratio", [0.0001, 0.001, 0.01, 0.05])
def test_group26_thin_shell_approaches_lame_as_thickness_vanishes(thickness_ratio):
    radius, pressure = 0.05, 1e6
    thickness = radius * thickness_ratio
    exact = run(
        "mechanics.lame_cylinder",
        inner_radius_m=radius - thickness / 2,
        outer_radius_m=radius + thickness / 2,
        evaluation_radius_m=radius,
        internal_pressure_Pa=pressure,
        external_pressure_Pa=0.0,
        closed_ends=True,
    )
    thin = run(
        "mechanics.thin_cylinder",
        pressure_difference_Pa=pressure,
        mean_radius_m=radius,
        wall_thickness_m=thickness,
        allowable_hoop_stress_Pa=1e9,
    )
    assert exact["hoop_stress_Pa"] == pytest.approx(thin["hoop_stress_Pa"], rel=thickness_ratio)


@pytest.mark.parametrize("temperature_change", [-100.0, 0.0, 100.0])
@pytest.mark.parametrize("restraint", [0.0, 1.0])
def test_group28_free_expansion_and_restrained_stress_sign(temperature_change, restraint):
    v = run(
        "mechanics.thermal_restraint", temperature_change_K=temperature_change, restraint_fraction=restraint
    )
    assert v["free_thermal_strain"] == pytest.approx(1.2e-5 * temperature_change)
    assert v["restrained_uniaxial_stress_Pa"] == pytest.approx(
        -restraint * 200e9 * 1.2e-5 * temperature_change
    )


@pytest.mark.parametrize("ratio", [0.5, 1.0, 2.0, 4.0])
def test_group40_basquin_load_scaling_against_declared_power_law(ratio):
    v = run(
        "fatigue.basquin",
        stress_range_Pa=ratio * 100e6,
        reference_range_Pa=100e6,
        reference_cycles=1e6,
        exponent=4.0,
    )
    assert v["cycles_to_failure"] == pytest.approx(1e6 / ratio**4)


@pytest.mark.parametrize("mean", [0.0, 100e6, 300e6])
def test_group40_goodman_tensile_mean_stress_increases_equivalent_amplitude(mean):
    v = run(
        "fatigue.goodman",
        alternating_stress_Pa=100e6,
        mean_stress_Pa=mean,
        ultimate_tensile_strength_Pa=600e6,
    )
    expected = 100e6 * 600e6 / (600e6 - mean)
    assert v["equivalent_fully_reversed_amplitude_Pa"] == pytest.approx(expected)
    assert v["equivalent_fully_reversed_amplitude_Pa"] >= 100e6


@pytest.mark.parametrize(
    "counts,lives",
    [
        ([10.0, 20.0], [100.0, 200.0]),
        ([20.0, 10.0], [200.0, 100.0]),
        ([5.0, 5.0, 20.0], [100.0, 100.0, 200.0]),
    ],
)
def test_group42_miner_permutation_and_block_partition_invariance(counts, lives):
    assert run("fatigue.miner", cycle_counts=counts, cycles_to_failure=lives, declared_damage_limit=1.0)[
        "damage"
    ] == pytest.approx(0.2)


@pytest.mark.parametrize("factor", [0.5, 2.0, 4.0])
def test_group37_norton_stress_scaling_and_elapsed_strain(factor):
    v = run("creep.norton", stress_Pa=1e8 * factor)
    assert v["steady_creep_strain_rate_per_s"] == pytest.approx(1e-10 * factor**5)
    assert v["steady_creep_strain"] == pytest.approx(1e-5 * factor**5)


@pytest.mark.parametrize("factor", [0.5, 2.0, 10.0])
def test_group55_archard_normal_work_and_hardness_scaling(factor):
    a = run("degradation.archard_wear")
    b = run("degradation.archard_wear", normal_force_N=1000.0 * factor, hardness_Pa=2e9 * factor)
    assert b["wear_volume_m3"] == pytest.approx(a["wear_volume_m3"])
    assert b["mean_wear_depth_m"] == pytest.approx(a["mean_wear_depth_m"])


@pytest.mark.parametrize("initial,surface", [(0.0, 2.0), (2.0, 0.0), (1.0, 1.0)])
def test_group20_diffusion_inventory_is_integral_of_signed_surface_flux(initial, surface):
    d, t = 1e-10, 100.0
    v = run(
        "transport.semi_infinite_diffusion",
        diffusivity_m2_s=d,
        exposure_s=t,
        depth_m=[0.0, 1.0],
        initial_concentration_mol_m3=initial,
        surface_concentration_mol_m3=surface,
    )
    assert v["integrated_excess_mol_m2"] == pytest.approx(
        2 * (surface - initial) * math.sqrt(d * t / math.pi), abs=1e-18
    )
    assert 2 * t * v["surface_flux_mol_m2_s"] == pytest.approx(v["integrated_excess_mol_m2"], abs=1e-18)
    assert v["concentration_mol_m3"] == pytest.approx([surface, initial])


@pytest.mark.parametrize("temperature", [280.0, 300.0, 330.0])
def test_group57_arrhenius_forward_backward_reciprocity(temperature):
    forward = run(
        "kinetics.arrhenius",
        reference_rate=1.0,
        reference_temperature_K=300.0,
        temperature_K=temperature,
        activation_energy_J_mol=50000.0,
    )
    backward = run(
        "kinetics.arrhenius",
        reference_rate=1.0,
        reference_temperature_K=temperature,
        temperature_K=300.0,
        activation_energy_J_mol=50000.0,
    )
    assert forward["rate"] * backward["rate"] == pytest.approx(1.0)


@pytest.mark.parametrize("volumetric_axis_strain", [-0.001, 0.0, 0.001])
def test_group46_j2_hydrostatic_loading_never_creates_deviatoric_plastic_flow(volumetric_axis_strain):
    payload = BASELINES["fatigue.j2_prager_strain_history"]
    v = run(
        "fatigue.j2_prager_strain_history",
        strain_tensor_components=[[0.0] * 6, [volumetric_axis_strain] * 3 + [0.0] * 3],
    )
    row = v["response_history"][-1]
    bulk = payload["young_modulus_Pa"] / (3 * (1 - 2 * payload["poisson_ratio"]))
    assert row["stress_tensor_components_Pa"] == pytest.approx(
        [3 * bulk * volumetric_axis_strain] * 3 + [0.0] * 3
    )
    assert row["plastic_strain_tensor_components"] == pytest.approx([0.0] * 6, abs=1e-14)
    assert row["equivalent_plastic_strain"] == pytest.approx(0.0, abs=1e-14)
    assert row["von_mises_equivalent_stress_Pa"] == pytest.approx(0.0, abs=1e-6)


@pytest.mark.parametrize("temperature", [280.0, 300.0, 373.15])
def test_group52_saturation_clapeyron_identity(temperature):
    # Separate pressure derivative and enthalpy/volume paths in the EOS.
    # Thermodynamic self-consistency, not an independent experiment.
    cp = pytest.importorskip("CoolProp.CoolProp")
    dt = 0.01
    derivative = (
        cp.PropsSI("P", "T", temperature + dt, "Q", 0, "Water")
        - cp.PropsSI("P", "T", temperature - dt, "Q", 0, "Water")
    ) / (2 * dt)
    latent = cp.PropsSI("Hmass", "T", temperature, "Q", 1, "Water") - cp.PropsSI(
        "Hmass", "T", temperature, "Q", 0, "Water"
    )
    volume_difference = 1 / cp.PropsSI("Dmass", "T", temperature, "Q", 1, "Water") - 1 / cp.PropsSI(
        "Dmass", "T", temperature, "Q", 0, "Water"
    )
    assert derivative == pytest.approx(latent / (temperature * volume_difference), rel=2e-6)
