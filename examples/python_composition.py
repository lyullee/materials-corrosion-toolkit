"""Run from any directory after installing MatIntegrity."""

from matintegrity.composition import OutputBinding, WorkflowStep, run_workflow
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.units import SECONDS_PER_YEAR

registry = default_registry()
context = RunContext(
    asset_id="synthetic-pipe", location_id="synthetic-point", time_basis="synthetic elapsed seconds"
)
steps = [
    WorkflowStep(
        id="trend",
        model_id="corrosion.thickness_trend",
        inputs={
            "time_s": [0.0, SECONDS_PER_YEAR, 2 * SECONDS_PER_YEAR],
            "thickness_m": [0.0102, 0.0101, 0.01],
            "method": "theil_sen",
        },
    ),
    WorkflowStep(
        id="forecast",
        model_id="corrosion.uniform_forecast",
        inputs={"current_thickness_m": 0.01, "required_thickness_m": 0.006, "horizon_s": SECONDS_PER_YEAR},
        bindings={"rate_m_s": OutputBinding(step_id="trend", output_key="rate_m_s")},
    ),
]
if __name__ == "__main__":
    import json

    print(json.dumps(run_workflow(registry, steps, context), indent=2, ensure_ascii=False))
