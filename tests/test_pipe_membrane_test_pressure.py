import pytest
from pydantic import ValidationError

from matintegrity.models.inspection import PipeMembraneTestPressure, pipe_membrane_test_pressure


def payload(**changes):
    return {
        "outside_diameter_m": 0.2, "wall_thickness_m": 0.01,
        "yield_strength_Pa": 400e6, "declared_yield_fraction": 0.8,
        "factor_basis": "synthetic user factor, not a grade rule",
        "geometry_material_and_factor_applicability_reviewed": True,
    } | changes


def test_pressure_closes_declared_outside_diameter_membrane_force_balance():
    result = pipe_membrane_test_pressure(PipeMembraneTestPressure(**payload()))
    assert result.status == "computed"
    assert result.values["membrane_test_pressure_difference_Pa"] == pytest.approx(32e6)
    # Force per axial metre: pressure*outside diameter equals two tensile wall forces.
    assert result.values["membrane_test_pressure_difference_Pa"] * 0.2 == pytest.approx(2 * 320e6 * 0.01)
    assert result.values["diameter_basis"] == "outside_diameter"


def test_unreviewed_factor_never_returns_a_test_pressure():
    result = pipe_membrane_test_pressure(PipeMembraneTestPressure(**payload(
        geometry_material_and_factor_applicability_reviewed=False,
    )))
    assert result.status == "needs_data"
    assert "membrane_test_pressure_difference_Pa" not in result.values


@pytest.mark.parametrize("changes", [
    {"wall_thickness_m": 0.1}, {"declared_yield_fraction": 1.01},
    {"outside_diameter_m": 0.0},
])
def test_invalid_geometry_or_fraction_is_rejected(changes):
    with pytest.raises(ValidationError):
        PipeMembraneTestPressure(**payload(**changes))
