"""Illustrate a review-gated linear thickness scenario from an empirical rate quantile."""

from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import CorrosionRateQuantileForecast
from matintegrity.registry import default_registry

INPUT = CorrosionRateQuantileForecast(
    sample={
        "observations": [
            {
                "observation_id": f"coupon-{index}-rate",
                "physical_specimen_id": f"coupon-{index}",
                "material_id": "user-alloy-01",
                "rate_m_s": rate,
                "condition_signature": {"temperature_K": 333.15, "chloride_mol_L": 0.05},
                "condition_group_id": "loop-test-condition-01",
                "source_group_id": "campaign-2026-01",
                "measurement_method": "weight_loss",
            }
            for index, rate in enumerate((2.1e-9, 2.8e-9, 3.4e-9), start=1)
        ],
        "quantile_probabilities": [0.1, 0.5, 0.9],
    },
    selected_quantile_level=0.5,
    current_thickness_m=0.012,
    required_thickness_m=0.009,
    horizon_s=31_536_000.0,
    material_state_compatibility_reviewed=True,
    condition_transferability_reviewed=True,
    linear_loss_model_reviewed=True,
    material_state_review_id="review-material-state-01",
    condition_transfer_review_id="review-condition-transfer-01",
    linear_loss_model_review_id="review-linear-loss-01",
)

if __name__ == "__main__":
    result = default_registry().run(
        "corrosion.rate_quantile_forecast",
        INPUT,
        RunContext(asset_id="pilot-loop", location_id="coupon-rack", time_basis="one-year scenario"),
    )
    print(result.model_dump_json(indent=2))
