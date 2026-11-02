"""Wire the synthetic closed-tensor work-life fixture to periodic cubic splines.

This example is illustrative only. Its synthetic numbers are not material data
and the example is intentionally not run as part of implementation work.
"""

import json
from pathlib import Path

from matintegrity.models.multiaxial_work_life import ClosedTensorWorkLife, closed_tensor_work_life


root = Path(__file__).resolve().parents[1]
inputs = json.loads((root / "examples/model_inputs.json").read_text(encoding="utf-8"))
request_data = inputs["models"]["fatigue.closed_tensor_work_life"]
request_data["time_reconstruction"] = "piecewise_periodic_cubic_spline"
request_data["periodic_spline_reviewed"] = True
request_data["time_reconstruction_and_derivative_reviewed"] = True
for cycle in request_data["cycles"]:
    cycle.pop("stress_time_derivative_components_Pa_s", None)
    cycle.pop("strain_time_derivative_components_s_inv", None)

request = ClosedTensorWorkLife.model_validate(request_data)
result = closed_tensor_work_life(request)
print(result.model_dump(mode="json"))
