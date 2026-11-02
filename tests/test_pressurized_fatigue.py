import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@pytest.fixture
def context():
    return RunContext(
        asset_id="synthetic-annulus",
        location_id="declared-reference-section",
        time_basis="static load-state verification",
    )


def run(context, **overrides):
    inputs = {
        "reference_section_id": "net-annulus",
        "load_case_id": "synthetic-axial-torsion-pressure",
        "inner_radius_m": 0.006,
        "outer_radius_m": 0.008,
        "pressure_evaluation_radius_m": 0.006,
        "external_axial_force_mean_N": 0.0,
        "external_axial_force_amplitude_N": 10_000.0,
        "torque_mean_N_m": 0.0,
        "torque_amplitude_N_m": 100.0,
        "axial_torsion_phase_rad": math.pi / 2,
        "internal_pressure_Pa": 60e6,
        "external_pressure_Pa": 0.0,
        "closed_ends": True,
    }
    result = default_registry().run("fatigue.pressurized_annulus_load_state", inputs | overrides, context)
    assert result.status == "computed"
    return result


def test_annular_reference_section_matches_diameter_form(context):
    values = run(context).values
    outer_diameter = 0.016
    inner_diameter = 0.012
    expected_area = math.pi * (outer_diameter**2 - inner_diameter**2) / 4
    expected_polar = math.pi * (outer_diameter**4 - inner_diameter**4) / 32
    assert values["reference_area_m2"] == pytest.approx(expected_area)
    assert values["polar_second_moment_m4"] == pytest.approx(expected_polar)
    assert values["external_axial_amplitude_Pa"] == pytest.approx(10_000 / expected_area)
    assert values["torsional_shear_amplitude_Pa"] == pytest.approx(
        100 * (outer_diameter / 2) / expected_polar
    )
    assert values["axial_torsion_phase_rad"] == pytest.approx(math.pi / 2)


def test_pressure_boundaries_and_closed_end_axial_component(context):
    inner = run(context).values
    outer = run(context, pressure_evaluation_radius_m=0.008).values
    expected_axial = 60e6 * 0.006**2 / (0.008**2 - 0.006**2)
    assert inner["pressure_radial_mean_Pa"] == pytest.approx(-60e6)
    assert outer["pressure_radial_mean_Pa"] == pytest.approx(0.0, abs=1e-8)
    assert inner["pressure_axial_mean_Pa"] == pytest.approx(expected_axial)
    assert inner["combined_axial_mean_Pa"] == pytest.approx(expected_axial)

    open_end = run(context, closed_ends=False).values
    assert open_end["pressure_axial_mean_Pa"] == 0.0
    assert open_end["combined_axial_mean_Pa"] == 0.0


def test_external_means_and_amplitudes_remain_separate(context):
    values = run(
        context,
        external_axial_force_mean_N=-2_000.0,
        external_axial_force_amplitude_N=5_000.0,
        torque_mean_N_m=-12.0,
        torque_amplitude_N_m=25.0,
    ).values
    area = values["reference_area_m2"]
    polar = values["polar_second_moment_m4"]
    assert values["external_axial_minimum_Pa"] == pytest.approx(-2_000 / area - 5_000 / area)
    assert values["external_axial_maximum_Pa"] == pytest.approx(-2_000 / area + 5_000 / area)
    assert values["torsional_shear_minimum_Pa"] == pytest.approx((-12 - 25) * 0.008 / polar)
    assert values["torsional_shear_maximum_Pa"] == pytest.approx((-12 + 25) * 0.008 / polar)


@pytest.mark.parametrize(
    "overrides",
    [
        {"inner_radius_m": 0.008},
        {"pressure_evaluation_radius_m": 0.005},
        {"pressure_evaluation_radius_m": 0.009},
        {"axial_torsion_phase_rad": -0.1},
        {"axial_torsion_phase_rad": 2 * math.pi + 0.1},
    ],
)
def test_invalid_geometry_or_phase_is_rejected(context, overrides):
    with pytest.raises(ValidationError):
        run(context, **overrides)


def test_model_does_not_report_fatigue_strength_or_life(context):
    result = run(context)
    assert not any("life" in key or "strength" in key for key in result.values)
    assert "fabest_hcf_protocol_v2_1_2" in result.source_ids
