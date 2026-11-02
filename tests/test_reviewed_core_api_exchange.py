import runpy
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

EXAMPLES = runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/reviewed_core_calculations.py"))


@pytest.fixture(scope="module")
def registry():
    return default_registry()


@pytest.mark.parametrize("model_id,inputs", EXAMPLES["sample_requests"]())
def test_core_python_json_preserves_values_units_identity_and_metadata(registry, model_id, inputs):
    context = RunContext(asset_id="synthetic", location_id="specimen", time_basis="test")
    direct = registry.run(model_id, inputs, context)
    serialized = registry.run_json(model_id, inputs.model_dump_json(), context)
    assert direct.status == serialized.status == "computed"
    assert direct.model_dump() == serialized.model_dump()
    assert direct.source_ids and direct.context == context
