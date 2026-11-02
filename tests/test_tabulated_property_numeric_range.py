import numpy as np
import pytest

from matintegrity.data import TabulatedProperty


def curve(x, y, method="linear"):
    return TabulatedProperty(
        property_id="authored",
        x=x,
        y=y,
        x_unit="authored_x",
        y_unit="authored_y",
        source_id="authored",
        interpolation=method,
    )


def test_opposite_large_ordinates_interpolate_without_overflow():
    table = curve([100, 300], [-1e308, 1e308])
    assert table.at(200) == 0
    assert table.at(150) == -5e307


def test_large_coordinate_span_does_not_overflow_order_or_weight():
    table = curve([-1e308, 1e308], [1, 3])
    assert table.at(0) == 2


def test_exact_nodes_and_numpy_scalar_are_preserved():
    table = curve([100, 300], [1e-320, 2e-320])
    assert table.at(np.float32(100)) == 1e-320
    assert table.at(300) == 2e-320


def test_nonzero_cancellation_below_float_support_is_withheld():
    table = curve([100, 300], [1e-323, -5e-324])
    with pytest.raises(ArithmeticError, match="not representable"):
        table.at(200)


def test_pchip_existing_shape_and_no_extrapolation():
    table = curve([100, 200, 300], [1, 2, 4], "pchip")
    assert 1 < table.at(150) < 2
    with pytest.raises(ValueError, match="extrapolation"):
        table.at(301)
