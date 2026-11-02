"""Summarize one reviewed uniform-loss rate per physical coupon."""

from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import CorrosionRateSampleSummary
from matintegrity.registry import default_registry

INPUT = CorrosionRateSampleSummary(
    observations=[
        {
            "observation_id": "coupon-A-rate",
            "physical_specimen_id": "coupon-A",
            "material_id": "user-alloy-01",
            "rate_m_s": 2.1e-9,
            "condition_signature": {"temperature_K": 333.15, "chloride_mol_L": 0.05},
            "condition_group_id": "loop-test-condition-01",
            "source_group_id": "campaign-2026-01",
            "measurement_method": "weight_loss",
        },
        {
            "observation_id": "coupon-B-rate",
            "physical_specimen_id": "coupon-B",
            "material_id": "user-alloy-01",
            "rate_m_s": 2.8e-9,
            "condition_signature": {"temperature_K": 333.15, "chloride_mol_L": 0.05},
            "condition_group_id": "loop-test-condition-01",
            "source_group_id": "campaign-2026-01",
            "measurement_method": "weight_loss",
        },
    ],
    quantile_probabilities=[0.1, 0.5, 0.9],
)

if __name__ == "__main__":
    print(
        default_registry()
        .run(
            "corrosion.rate_sample_summary",
            INPUT,
            RunContext(asset_id="pilot-loop", location_id="coupon-rack", time_basis="168 h exposure"),
        )
        .model_dump_json(indent=2)
    )
