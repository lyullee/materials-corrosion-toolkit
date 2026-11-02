import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.corrosion import (
    CorrosionRateSampleSummary,
    CouponLoss,
    CouponLossWithUncertainty,
    corrosion_rate_sample_summary,
    coupon_loss,
    coupon_loss_input_to_rate_observation,
    coupon_loss_with_uncertainty,
)
from matintegrity.registry import default_registry


def _input(**overrides):
    payload = dict(
        observation_id="coupon-observation-1",
        physical_specimen_id="coupon-1",
        material_id="carbon-steel-grade-x",
        condition_group_id="water-ambient-1",
        source_group_id="study-1",
        measurement_method="corrected-gravimetric-loss",
        mass_loss_kg=0.001,
        exposed_area_m2=0.01,
        density_kg_m3=7800.0,
        duration_s=86400.0,
        covariance_matrix=[
            [1e-10, 0.0, 0.0, 0.0],
            [0.0, 1e-8, 0.0, 0.0],
            [0.0, 0.0, 100.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
        covariance_basis="independent standard uncertainties, stated in native input units",
        condition_signature={"temperature_K": 298.15, "chloride_mol_L": 0.01},
        measurement_reviewed=True,
        measurement_review_id="review-2026-01",
        evidence=(Evidence(source_id="study-1", origin="measured", citation="caller-provided citation"),),
    )
    payload.update(overrides)
    return CouponLossWithUncertainty(**payload)


@pytest.mark.parametrize(
    "mass,area,density,duration,penetration,rate",
    [
        (1e300, 1e200, 1e200, 1e100, 1e-100, 1e-200),
        (1e-300, 1e-200, 1e-200, 1e100, 1e100, 1.0),
    ],
)
def test_coupon_products_do_not_overflow_or_underflow_before_final_ratio(
    mass, area, density, duration, penetration, rate
):
    raw = dict(mass_loss_kg=mass, exposed_area_m2=area, density_kg_m3=density, duration_s=duration)
    result = coupon_loss(CouponLoss(**raw))
    assert result.status == "computed"
    assert result.values["mean_penetration_m"] == pytest.approx(penetration, rel=1e-14, abs=0.0)
    assert result.values["rate_m_s"] == pytest.approx(rate, rel=1e-14, abs=0.0)
    uncertain = coupon_loss_with_uncertainty(_input(**raw, covariance_matrix=[[0.0] * 4 for _ in range(4)]))
    assert uncertain.status == "computed"
    assert uncertain.values["rate_m_s"] == result.values["rate_m_s"]
    assert uncertain.values["rate_standard_uncertainty_m_s"] == 0.0


def test_variance_underflow_does_not_erase_representable_standard_uncertainty():
    covariance = [[0.0] * 4 for _ in range(4)]
    covariance[0][0] = 1.0
    result = coupon_loss_with_uncertainty(
        _input(
            mass_loss_kg=1.0,
            exposed_area_m2=1e100,
            density_kg_m3=1e100,
            duration_s=1.0,
            covariance_matrix=covariance,
        )
    )
    assert result.status == "computed"
    assert result.values["rate_standard_uncertainty_m_s"] == pytest.approx(1e-200, rel=1e-14, abs=0.0)


def test_zero_loss_with_large_but_representable_standard_uncertainty():
    covariance = [[0.0] * 4 for _ in range(4)]
    covariance[0][0] = 1e-300
    result = coupon_loss_with_uncertainty(
        _input(
            mass_loss_kg=0.0,
            exposed_area_m2=1e-200,
            density_kg_m3=1e-200,
            duration_s=1.0,
            covariance_matrix=covariance,
        )
    )
    assert result.status == "computed"
    assert result.values["rate_standard_uncertainty_m_s"] == pytest.approx(1e250, rel=1e-14, abs=0.0)
    assert result.values["rate_relative_standard_uncertainty"] is None


def test_nonzero_unrepresentable_mean_loss_is_not_reported_as_zero():
    result = coupon_loss(
        CouponLoss(mass_loss_kg=1e-300, exposed_area_m2=1e100, density_kg_m3=1e100, duration_s=1.0)
    )
    assert result.status == "out_of_scope"
    assert "rate_m_s" not in result.values


@pytest.mark.parametrize("with_uncertainty", [False, True])
def test_repaired_coupon_registry_python_json_exchange(with_uncertainty):
    x = (
        _input()
        if with_uncertainty
        else CouponLoss(mass_loss_kg=0.001, exposed_area_m2=0.01, density_kg_m3=7800.0, duration_s=86400.0)
    )
    model = "corrosion.coupon_loss_with_uncertainty" if with_uncertainty else "corrosion.coupon_loss"
    registry = default_registry()
    context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x.model_dump(), context).values
        == registry.run_json(model, x.model_dump_json(), context).values
    )


def test_coupon_rate_uses_full_covariance_and_retains_specimen_lineage():
    result = coupon_loss_with_uncertainty(_input())
    expected_rate = 0.001 / (0.01 * 7800.0 * 86400.0)
    assert result.values["rate_m_s"] == pytest.approx(expected_rate)
    assert result.values["rate_standard_uncertainty_m_s"] > 0.0
    assert result.values["physical_specimen_id"] == "coupon-1"
    assert result.values["source_group_id"] == "study-1"
    assert result.values["uncertainty_method"] == "first_order_delta_method_with_caller_joint_covariance"


def test_exposure_time_uncertainty_changes_rate_but_not_measured_penetration():
    covariance = [[0.0] * 4 for _ in range(4)]
    covariance[3][3] = 1.0
    result = coupon_loss_with_uncertainty(_input(covariance_matrix=covariance))
    assert result.values["rate_standard_uncertainty_m_s"] > 0.0
    assert result.values["penetration_standard_uncertainty_m"] == 0.0


def test_coupon_rate_requires_review_and_positive_semidefinite_covariance():
    assert coupon_loss_with_uncertainty(_input(measurement_reviewed=False)).status == "needs_data"
    with pytest.raises(ValidationError, match="positive semidefinite"):
        _input(
            covariance_matrix=[
                [1.0, 2.0, 0.0, 0.0],
                [2.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )


def test_reviewed_coupon_measurement_requires_review_identifier():
    with pytest.raises(ValidationError, match="measurement_review_id"):
        _input(measurement_review_id=None)


def test_coupon_adapter_preserves_uncertainty_and_source_through_rate_summary():
    first = coupon_loss_input_to_rate_observation(
        _input(observation_id="coupon-observation-1", physical_specimen_id="coupon-1")
    )
    second = coupon_loss_input_to_rate_observation(
        _input(
            observation_id="coupon-observation-2",
            physical_specimen_id="coupon-2",
            mass_loss_kg=0.002,
        )
    )
    summary = corrosion_rate_sample_summary(CorrosionRateSampleSummary(observations=[first, second]))
    assert summary.values["rate_standard_uncertainties_m_s"] == pytest.approx(
        [first.rate_standard_uncertainty_m_s, second.rate_standard_uncertainty_m_s]
    )
    assert summary.values["evidence_source_ids_by_observation"] == [["study-1"], ["study-1"]]
    assert summary.values["quantile_rates_m_s"][1] == pytest.approx((first.rate_m_s + second.rate_m_s) / 2)
