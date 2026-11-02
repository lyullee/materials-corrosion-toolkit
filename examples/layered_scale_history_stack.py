"""Compose synthetic single-phase scale histories into a layered transport request."""

import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.scale_layer_stack_transport import LayeredScaleHistoryStackTransport


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    examples = json.loads((root / "examples" / "model_inputs.json").read_text(encoding="utf-8"))
    scale_template = examples["models"]["chemistry.caller_surface_scale_kinetics"]
    transport = examples["models"]["chemistry.layered_scale_diffusion_limit"]
    transport["physical_scope_id"] = "synthetic-surface-coupon"
    transport["solution_condition_id"] = "synthetic-aqueous-condition"
    transport["scale_phase_id"] = "synthetic-multiphase-stack"
    context = RunContext(
        asset_id="synthetic-scale-asset",
        location_id="synthetic-surface-location",
        time_basis="elapsed-time-s",
    )
    registry = default_registry()
    histories = []
    for index, layer in enumerate(transport["layers"], start=1):
        profile = dict(scale_template)
        profile["physical_scope_id"] = transport["physical_scope_id"]
        profile["solution_condition_id"] = transport["solution_condition_id"]
        profile["scale_phase_id"] = f"synthetic-phase-{index}"
        profile["assessment_id"] = f"synthetic-scale-history-{index}"
        result = registry.run("chemistry.caller_surface_scale_kinetics", profile, context)
        histories.append({"layer_id": layer["layer_id"], "scale_history_result": result.model_dump(mode="json")})

    request = LayeredScaleHistoryStackTransport.model_validate({
        "transport_request": transport,
        "selected_time_s": 3600.0,
        "layer_bindings": histories,
        "layer_order_and_phase_mapping_reviewed": True,
        "common_scope_and_time_reviewed": True,
        "computational_use_authorized": True,
    })
    result = registry.run("chemistry.layered_scale_history_stack_transport", request, context)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
