import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import (
    CorrosionRateQuantileForecast,
    CorrosionRateSampleSummary,
    corrosion_rate_quantile_forecast,
    corrosion_rate_sample_summary,
)
from matintegrity.registry import default_registry


def _row(specimen, rate):
    return {
        "observation_id": f"rate-{specimen}",
        "physical_specimen_id": specimen,
        "material_id": "alloy-A",
        "rate_m_s": rate,
        "condition_signature": {"temperature_K": 323.15, "chloride_mol_L": 0.1},
        "condition_group_id": "water-chemistry-A",
        "source_group_id": "study-1",
        "measurement_method": "weight_loss",
    }


def test_empirical_quantiles_preserve_specimen_lineage_and_custom_probabilities():
    data = CorrosionRateSampleSummary(
        observations=[_row("coupon-1", 1e-9), _row("coupon-2", 2e-9), _row("coupon-3", 9e-9)],
        quantile_probabilities=[0.1, 0.5, 0.9],
    )
    result = corrosion_rate_sample_summary(data)
    assert result.values["specimen_count"] == 3
    assert result.values["physical_specimen_ids"] == ["coupon-1", "coupon-2", "coupon-3"]
    assert result.values["quantile_probabilities"] == [0.1, 0.5, 0.9]
    assert result.values["quantile_rates_m_s"] == pytest.approx([1.2e-9, 2e-9, 7.6e-9])
    assert "not confidence or prediction intervals" in result.notes[1]


def test_mean_measurement_uncertainty_uses_declared_cross_specimen_covariance_separately():
    first = _row("coupon-1", 1e-9)
    second = _row("coupon-2", 3e-9)
    first["rate_standard_uncertainty_m_s"] = 1e-10
    first["rate_uncertainty_basis"] = "synthetic standard uncertainty"
    second["rate_standard_uncertainty_m_s"] = 2e-10
    second["rate_uncertainty_basis"] = "synthetic standard uncertainty"
    summary = CorrosionRateSampleSummary(
        observations=[first, second],
        measurement_error_covariance_m_s2=[[1e-20, 1e-20], [1e-20, 4e-20]],
    )
    result = corrosion_rate_sample_summary(summary)
    assert result.values["arithmetic_mean_rate_m_s"] == pytest.approx(2e-9)
    assert result.values["between_specimen_sample_standard_deviation_m_s"] == pytest.approx(2**0.5 * 1e-9)
    assert result.values["measurement_standard_uncertainty_of_mean_m_s"] == pytest.approx((1.75e-20) ** 0.5)
    assert result.values["quantile_rates_m_s"] == pytest.approx([1.5e-9, 2e-9, 2.5e-9])
    assert result.values["measurement_error_covariance_sha256"]


def test_mean_uncertainty_requires_complete_and_psd_cross_specimen_covariance():
    first = _row("coupon-1", 1e-9)
    second = _row("coupon-2", 2e-9)
    first["rate_standard_uncertainty_m_s"] = 1e-10
    first["rate_uncertainty_basis"] = "synthetic"
    second["rate_standard_uncertainty_m_s"] = 2e-10
    second["rate_uncertainty_basis"] = "synthetic"
    with pytest.raises(ValidationError, match="positive semidefinite"):
        CorrosionRateSampleSummary(
            observations=[first, second],
            measurement_error_covariance_m_s2=[[1e-20, 3e-20], [3e-20, 4e-20]],
        )
    with pytest.raises(ValidationError, match="every observation"):
        CorrosionRateSampleSummary(
            observations=[_row("coupon-1", 1e-9), _row("coupon-2", 2e-9)],
            measurement_error_covariance_m_s2=[[1e-20, 0.0], [0.0, 4e-20]],
        )


def test_summary_rejects_duplicate_specimens_and_mixed_conditions():
    with pytest.raises(ValidationError, match="one rate summary per physical specimen"):
        duplicate_specimen = _row("coupon-1", 2e-9)
        duplicate_specimen["observation_id"] = "rate-coupon-1-repeat"
        CorrosionRateSampleSummary(observations=[_row("coupon-1", 1e-9), duplicate_specimen])
    changed = _row("coupon-2", 2e-9)
    changed["condition_signature"] = {"temperature_K": 333.15}
    with pytest.raises(ValidationError, match="same condition_signature"):
        CorrosionRateSampleSummary(observations=[_row("coupon-1", 1e-9), changed])


def test_summary_requires_reviewable_identifiers_and_ordered_quantiles():
    blank_id = _row("coupon-1", 1e-9)
    blank_id["source_group_id"] = "  "
    with pytest.raises(ValidationError, match="cannot be blank"):
        CorrosionRateSampleSummary(observations=[blank_id])
    with pytest.raises(ValidationError, match="strictly increasing"):
        CorrosionRateSampleSummary(observations=[_row("coupon-1", 1e-9)], quantile_probabilities=[0.5, 0.5])
    with pytest.raises(ValidationError):
        CorrosionRateSampleSummary(observations=[_row("coupon-1", 1e-9)], quantile_probabilities=[1.01])


def test_registered_rate_sample_summary_api():
    result = default_registry().run(
        "corrosion.rate_sample_summary",
        CorrosionRateSampleSummary(observations=[_row("coupon-1", 1e-9)]),
        RunContext(asset_id="test-asset", location_id="coupon-set", time_basis="exposure interval"),
    )
    assert result.values["minimum_rate_m_s"] == 1e-9


def test_rate_quantile_forecast_uses_selected_sample_quantile_and_preserves_lineage():
    sample = CorrosionRateSampleSummary(
        observations=[_row("coupon-1", 1e-9), _row("coupon-2", 2e-9), _row("coupon-3", 9e-9)],
        quantile_probabilities=[0.1, 0.5, 0.9],
    )
    forecast = CorrosionRateQuantileForecast(
        sample=sample,
        selected_quantile_level=0.5,
        current_thickness_m=0.01,
        required_thickness_m=0.008,
        horizon_s=5e5,
        material_state_compatibility_reviewed=True,
        condition_transferability_reviewed=True,
        linear_loss_model_reviewed=True,
        material_state_review_id="review-material-state-01",
        condition_transfer_review_id="review-transfer-01",
        linear_loss_model_review_id="review-linear-loss-01",
    )
    result = corrosion_rate_quantile_forecast(forecast)
    assert result.values["selected_sample_rate_m_s"] == pytest.approx(2e-9)
    assert result.values["predicted_thickness_m"] == pytest.approx(0.01 - 2e-9 * 5e5)
    assert result.values["rate_sample_physical_specimen_ids"] == ["coupon-1", "coupon-2", "coupon-3"]
    assert "not a confidence level" in result.notes[-1]


def test_rate_quantile_forecast_preserves_mean_error_summary_without_propagating_it():
    first = _row("coupon-1", 1e-9)
    second = _row("coupon-2", 2e-9)
    first["rate_standard_uncertainty_m_s"] = 1e-10
    first["rate_uncertainty_basis"] = "synthetic independent measurement error"
    second["rate_standard_uncertainty_m_s"] = 2e-10
    second["rate_uncertainty_basis"] = "synthetic independent measurement error"
    sample = CorrosionRateSampleSummary(
        observations=[first, second],
        measurement_error_covariance_m_s2=[[1e-20, 0.0], [0.0, 4e-20]],
    )
    forecast = CorrosionRateQuantileForecast(
        sample=sample,
        selected_quantile_level=0.5,
        current_thickness_m=0.01,
        required_thickness_m=0.008,
        horizon_s=1e6,
        material_state_compatibility_reviewed=True,
        condition_transferability_reviewed=True,
        linear_loss_model_reviewed=True,
        material_state_review_id="review-material",
        condition_transfer_review_id="review-transfer",
        linear_loss_model_review_id="review-linear-rate",
    )
    result = corrosion_rate_quantile_forecast(forecast)
    assert result.values["selected_sample_rate_m_s"] == pytest.approx(1.5e-9)
    assert result.values["rate_sample_uncertainty_of_mean_m_s"] == pytest.approx((1.25e-20) ** 0.5)
    assert result.values["rate_sample_standard_uncertainties_m_s"] == pytest.approx([1e-10, 2e-10])
    assert "not propagated into this deterministic forecast" in result.notes[-2]


def test_rate_quantile_forecast_requires_exact_quantile_and_all_review_gates():
    sample = CorrosionRateSampleSummary(observations=[_row("coupon-1", 1e-9)])
    payload = {
        "sample": sample,
        "selected_quantile_level": 0.8,
        "current_thickness_m": 0.01,
        "required_thickness_m": 0.008,
        "horizon_s": 1000.0,
        "material_state_compatibility_reviewed": True,
        "condition_transferability_reviewed": True,
        "linear_loss_model_reviewed": True,
        "material_state_review_id": "review-material-state-01",
        "condition_transfer_review_id": "review-transfer-01",
        "linear_loss_model_review_id": "review-linear-loss-01",
    }
    with pytest.raises(ValidationError, match="exactly match"):
        CorrosionRateQuantileForecast(**payload)
    payload["selected_quantile_level"] = 0.5
    payload["condition_transferability_reviewed"] = False
    with pytest.raises(ValidationError, match="reviews are required"):
        CorrosionRateQuantileForecast(**payload)
    payload["condition_transferability_reviewed"] = True
    payload["linear_loss_model_review_id"] = "  "
    with pytest.raises(ValidationError, match="traceable review identifier"):
        CorrosionRateQuantileForecast(**payload)
