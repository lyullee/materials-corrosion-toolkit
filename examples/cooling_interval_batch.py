"""Evaluate two caller-selected cooling branches from one synthetic record."""

from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.thermohistory import CoolingIntervalBatch, CoolingIntervalBranch
from matintegrity.registry import default_registry


def build_request() -> CoolingIntervalBatch:
    return CoolingIntervalBatch(
        time_s=(0.0, 1.0, 2.0, 3.0, 4.0, 5.0),
        temperature_K=(500.0, 450.0, 300.0, 500.0, 450.0, 300.0),
        branches=(
            CoolingIntervalBranch(
                branch_id="cycle-1-cooling",
                upper_temperature_K=400.0,
                lower_temperature_K=350.0,
                start_index=0,
                end_index=2,
            ),
            CoolingIntervalBranch(
                branch_id="cycle-2-cooling",
                upper_temperature_K=400.0,
                lower_temperature_K=350.0,
                start_index=3,
                end_index=5,
            ),
        ),
        record_id="synthetic-multipass-thermal-history",
        sensor_id="synthetic-thermocouple-1",
        location_id="synthetic-weld-point-1",
        evidence=(Evidence(
            source_id="synthetic_example_data",
            origin="synthetic",
            citation="Synthetic values constructed in this example; not measured data.",
        ),),
    )


if __name__ == "__main__":
    assessment = default_registry().run(
        "welding.cooling_interval_batch",
        build_request(),
        RunContext(asset_id="synthetic-demo", location_id="thermal-history", time_basis="elapsed_seconds"),
    )
    print(assessment.model_dump_json(indent=2))
