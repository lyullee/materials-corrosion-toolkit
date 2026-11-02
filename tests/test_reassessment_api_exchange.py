import runpy
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

EXAMPLES = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/engineering_correlations.py"))


@pytest.fixture(scope="module")
def registry():
    return default_registry()


@pytest.mark.parametrize("model_id,inputs", EXAMPLES["sample_requests"]())
def test_public_python_and_json_exchange_preserves_values_units_and_input_identity(registry, model_id, inputs):
    context = RunContext(asset_id="synthetic-asset", location_id="joint-1", time_basis="test")
    python_result = registry.run(model_id, inputs, context)
    json_result = registry.run_json(model_id, inputs.model_dump_json(), context)
    assert python_result.status == json_result.status == "computed"
    assert python_result.values == json_result.values
    assert python_result.units == json_result.units
    assert python_result.input_digest == json_result.input_digest
    assert python_result.source_ids == json_result.source_ids
    assert python_result.context == context
