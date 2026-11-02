from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from matintegrity.contracts import canonical_digest
from matintegrity.gasket_correlated_uncertainty import (
    GasketLeakageCovariancePropagation,
    evaluate_gasket_leakage_covariance,
)


def _tuplify(value):
    if isinstance(value, list):
        return tuple(_tuplify(item) for item in value)
    if isinstance(value, dict):
        return {key: _tuplify(item) for key, item in value.items()}
    return value


def request_data(*, pressure=5.0, delta=10.0, covariance=None):
    calibration = {
        "differential_pressure_Pa": [0.0, 20.0],
        "rows": [
            {"contact_pressure_Pa": 0.0, "molar_leak_flux_by_delta_pressure_mol_s_m2": [1.0, 2.0]},
            {"contact_pressure_Pa": 10.0, "molar_leak_flux_by_delta_pressure_mol_s_m2": [0.5, 1.0]},
        ],
    }
    calibration_digest = canonical_digest(calibration)
    scenario_digest = "a" * 64
    covariance_digest = "b" * 64
    return _tuplify({
        "assessment_id": "synthetic-gasket-covariance",
        "asset_id": "synthetic-asset",
        "joint_id": "synthetic-joint",
        "physical_scope_id": "synthetic-scope",
        "time_s": 0.0,
        "node_ids": ["node-1"],
        "node_contact_pressure_Pa": [pressure],
        "common_differential_pressure_Pa": delta,
        "node_area_m2": [2.0],
        "calibration": calibration,
        "calibration_provider_id": "calibration-provider",
        "input_covariance": covariance or [[0.0] * 7 for _ in range(7)],
        "calibration_record_sha256": calibration_digest,
        "scenario_provider_id": "scenario-provider",
        "scenario_provider_revision": "1",
        "scenario_record_sha256": scenario_digest,
        "covariance_provider_id": "covariance-provider",
        "covariance_record_sha256": covariance_digest,
        "usage_license_id": "CC0-1.0",
        "evidence": [
            {"source_id": "scenario-provider", "origin": "synthetic", "citation": "synthetic scenario", "sha256": scenario_digest},
            {"source_id": "calibration-provider", "origin": "synthetic", "citation": "synthetic calibration", "sha256": calibration_digest},
            {"source_id": "covariance-provider", "origin": "synthetic", "citation": "synthetic covariance", "sha256": covariance_digest, "license_id": "CC0-1.0"},
        ],
        "calibration_scope_and_units_reviewed": True,
        "covariance_order_units_and_estimation_reviewed": True,
        "local_linearization_and_support_reviewed": True,
        "usage_rights_reviewed": True,
        "computational_use_authorized": True,
    })


@pytest.mark.parametrize("variance_index", range(7))
def test_diagonal_covariance_propagates_finite_variance(variance_index):
    matrix = [[0.0] * 7 for _ in range(7)]
    matrix[variance_index][variance_index] = 1.0e-8
    request = GasketLeakageCovariancePropagation.model_validate(request_data(covariance=matrix))
    result = evaluate_gasket_leakage_covariance(request)
    assert result.status == "computed", result.values.get("reason")
    assert math.isclose(result.values["nominal_molar_leak_rate_mol_s"], 2.25)
    assert len(result.values["jacobian"]) == 7
    expected = result.values["jacobian"][variance_index] ** 2 * 1.0e-8
    assert math.isclose(result.values["first_order_variance_mol2_s2"], expected, rel_tol=1e-12, abs_tol=1e-24)


@pytest.mark.parametrize("pressure,delta", [(0.0, 10.0), (10.0, 10.0), (5.0, 0.0), (5.0, 20.0), (10.0, 20.0)])
def test_calibration_knots_and_support_boundaries_fail_closed(pressure, delta):
    request = GasketLeakageCovariancePropagation.model_validate(request_data(pressure=pressure, delta=delta))
    result = evaluate_gasket_leakage_covariance(request)
    assert result.status == "out_of_scope"
    assert "knot or support boundary" in result.values["reason"]


def test_indefinite_covariance_is_rejected():
    matrix = [[0.0] * 7 for _ in range(7)]
    matrix[0][0] = matrix[1][1] = 1.0
    matrix[0][1] = matrix[1][0] = 2.0
    with pytest.raises(ValidationError, match="positive semidefinite"):
        GasketLeakageCovariancePropagation.model_validate(request_data(covariance=matrix))


def test_zero_variance_cannot_have_cross_covariance():
    matrix = [[0.0] * 7 for _ in range(7)]
    matrix[0][1] = matrix[1][0] = 1.0
    with pytest.raises(ValidationError, match="zero-variance"):
        GasketLeakageCovariancePropagation.model_validate(request_data(covariance=matrix))


def test_covariance_dimensions_are_bound_to_declared_order():
    with pytest.raises(ValidationError, match="dimensions"):
        GasketLeakageCovariancePropagation.model_validate(request_data(covariance=[[0.0]]))


def test_provider_digest_and_license_are_linked_to_evidence():
    data = request_data()
    data["covariance_provider_id"] = "unrelated-provider"
    with pytest.raises(ValidationError, match="covariance provider and digest"):
        GasketLeakageCovariancePropagation.model_validate(data)


def test_mixed_unit_covariance_uses_scale_normalized_psd_check():
    matrix = [[0.0] * 7 for _ in range(7)]
    diagonal = [1.0e18, 1.0e-10, 1.0e-12, 1.0e-20, 1.0e-20, 1.0e-20, 1.0e-20]
    for i, value in enumerate(diagonal):
        matrix[i][i] = value
    matrix[0][1] = matrix[1][0] = 0.25 * math.sqrt(diagonal[0] * diagonal[1])
    request = GasketLeakageCovariancePropagation.model_validate(request_data(covariance=matrix))
    result = evaluate_gasket_leakage_covariance(request)
    assert result.status == "computed", result.values.get("reason")
    assert result.values["first_order_variance_mol2_s2"] >= 0.0


def test_correlated_inputs_use_full_jacobian_covariance_product():
    matrix = [[0.0] * 7 for _ in range(7)]
    matrix[0][0] = 4.0
    matrix[1][1] = 9.0
    matrix[0][1] = matrix[1][0] = 3.0
    request = GasketLeakageCovariancePropagation.model_validate(request_data(covariance=matrix))
    result = evaluate_gasket_leakage_covariance(request)
    assert result.status == "computed", result.values.get("reason")
    jacobian = result.values["jacobian"]
    expected = sum(jacobian[i] * matrix[i][j] * jacobian[j] for i in range(7) for j in range(7))
    assert math.isclose(result.values["first_order_variance_mol2_s2"], expected, rel_tol=1e-12, abs_tol=1e-24)


def test_asymmetric_covariance_is_rejected():
    matrix = [[0.0] * 7 for _ in range(7)]
    matrix[0][0] = matrix[1][1] = 1.0
    matrix[0][1] = 0.1
    with pytest.raises(ValidationError, match="symmetric"):
        GasketLeakageCovariancePropagation.model_validate(request_data(covariance=matrix))


def test_negative_variance_is_rejected():
    matrix = [[0.0] * 7 for _ in range(7)]
    matrix[0][0] = -1.0
    with pytest.raises(ValidationError, match="variances must be nonnegative"):
        GasketLeakageCovariancePropagation.model_validate(request_data(covariance=matrix))
