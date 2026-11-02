"""Run the synthetic closed-tensor work-life fixture with shape-preserving PCHIP."""

import json
from pathlib import Path

from matintegrity.models.multiaxial_work_life import ClosedTensorWorkLife, closed_tensor_work_life


root = Path(__file__).resolve().parents[1]
inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
request_data = inputs["models"]["fatigue.closed_tensor_work_life"]
request_data["time_reconstruction"] = "piecewise_pchip"
for cycle in request_data["cycles"]:
    cycle.pop("stress_time_derivative_components_Pa_s", None)
    cycle.pop("strain_time_derivative_components_s_inv", None)

request = ClosedTensorWorkLife.model_validate(request_data)
result = closed_tensor_work_life(request)
print(result.model_dump(mode="json"))
