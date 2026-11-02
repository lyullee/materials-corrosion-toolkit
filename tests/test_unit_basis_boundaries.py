import pytest

from matintegrity.units import absolute_pressure, convert


def test_pressure_addition_overflow_is_rejected():
    with pytest.raises(ValueError, match="positive and finite"):
        absolute_pressure(1e308, "Pa", basis="gauge", ambient_pa=1e308)


def test_boolean_ambient_is_not_a_pressure_measurement():
    with pytest.raises(ValueError, match="declared ambient"):
        absolute_pressure(1.0, "Pa", basis="gauge", ambient_pa=True)


def test_negative_gauge_and_explicit_ambient_preserve_physical_absolute_pressure():
    assert absolute_pressure(-20000.0, "Pa", basis="gauge", ambient_pa=100000.0) == 80000.0


def test_absolute_and_interval_temperature_use_different_units():
    assert convert(50.0, "degF", "degC") == pytest.approx(10.0)
    assert convert(50.0, "delta_degF", "delta_degC") == pytest.approx(250.0 / 9.0)
