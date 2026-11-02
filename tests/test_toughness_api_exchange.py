import json
import runpy
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
CASES = (
    (None, None, "materials.impact_transition"),
    ("test_impact_metric_crossings.py", "payload", "inspection.impact_metric_crossings"),
    ("test_instrumented_impact_signal.py", "payload", "inspection.instrumented_impact_signal_summary"),
    ("test_impact_testing_campaign.py", "payload", "inspection.impact_testing_campaign"),
    ("test_fracture_toughness_testing.py", "payload", "inspection.fracture_toughness_testing"),
    ("test_fracture_toughness_evidence.py", "payload", "inspection.fracture_toughness_test_evidence"),
)


@pytest.fixture(scope="module")
def registry():
    return default_registry()


@pytest.mark.parametrize("filename,factory,model_id", CASES)
def test_toughness_python_json_exchange_preserves_endpoints_and_scope(registry, filename, factory, model_id):
    raw = (
        json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][model_id]
        if filename is None
        else runpy.run_path(str(ROOT / "tests" / filename))[factory]()
    )
    inputs = registry.input_type(model_id).model_validate(raw)
    context = RunContext(
        asset_id=getattr(inputs, "asset_id", "synthetic"),
        location_id=getattr(inputs, "location_id", "synthetic"),
        time_basis="test",
    )
    direct = registry.run(model_id, inputs, context)
    serialized = registry.run_json(model_id, inputs.model_dump_json(), context)
    assert direct.status == serialized.status == "computed"
    assert direct.model_dump() == serialized.model_dump()
