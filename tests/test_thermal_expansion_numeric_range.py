import math

import pytest

from matintegrity.thermal_expansion import TangentExpansionTable, integrate_tangent_expansion


def table(xs, ys):
    return TangentExpansionTable(
        table_id="authored",
        material_condition_id="synthetic",
        direction_id="x",
        temperature_K=xs,
        tangent_alpha_1_K=ys,
        evidence=(
            dict(
                source_id="authored",
                origin="synthetic",
                citation="Authored arithmetic case.",
                license_id="authored-test",
                sha256="a" * 64,
            ),
        ),
        coefficient_definition="d_log_length_d_temperature",
        applicability_reviewed=True,
    )


def test_constant_coefficient_and_reverse_path():
    x = table((200.0, 400.0), (1e-5, 1e-5))
    forward = integrate_tangent_expansion(x, 200.0, 400.0)
    reverse = integrate_tangent_expansion(x, 400.0, 200.0)
    assert forward.logarithmic_length_change == pytest.approx(0.002)
    assert reverse.logarithmic_length_change == pytest.approx(-0.002)
    assert forward.engineering_length_change == pytest.approx(math.expm1(0.002))


def test_large_opposite_coefficients_cancel_without_overflow():
    # Use an exactly antisymmetric linear segment instead of summing huge float endpoints.
    x = table((1.0, 5.0), (1e308, -1e308))
    result = integrate_tangent_expansion(x, 1.0, 5.0)
    assert result.status == "computed"
    assert result.logarithmic_length_change == 0


@pytest.mark.parametrize("ys", [(1e308, 1e308), (-1e308, -1e308)])
def test_unrepresentable_integral_returns_status(ys):
    result = integrate_tangent_expansion(table((1.0, 10.0), ys), 1.0, 10.0)
    assert result.status == "out_of_scope"
    assert result.engineering_length_change is None


def test_tiny_interval_avoids_intermediate_coefficient_sum_overflow():
    start, end = 1e-308, 2e-308
    result = integrate_tangent_expansion(table((start, end), (1e308, 1e308)), start, end)
    assert result.status == "computed"
    assert result.logarithmic_length_change == pytest.approx(1.0)


def test_unrepresentable_contraction_does_not_report_zero_final_length():
    result = integrate_tangent_expansion(table((1.0, 2.0), (-1000.0, -1000.0)), 1.0, 2.0)
    assert result.status == "out_of_scope"


def test_nonzero_integral_underflow_is_not_silent_zero():
    result = integrate_tangent_expansion(table((1e-300, 2e-300), (1e-100, 1e-100)), 1e-300, 2e-300)
    assert result.status == "out_of_scope"
