import runpy
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parent
CASES = (
    ("test_wps_qualification.py", "welding.wps_qualification_envelope"),
    ("test_welding_production_test.py", "welding.production_weld_test_evidence"),
    ("test_production_weld_test_campaign.py", "welding.production_weld_test_campaign_evidence"),
    ("test_temper_bead.py", "welding.temper_bead_qualification"),
    ("test_welding_consumable.py", "welding.consumable_compatibility"),
)


@pytest.fixture(scope="module")
def registry():
    return default_registry()


@pytest.mark.parametrize("filename,model_id", CASES)
def test_welding_evidence_python_json_preserves_scope_and_findings(registry, filename, model_id):
    inputs = registry.input_type(model_id).model_validate(runpy.run_path(str(ROOT / filename))["payload"]())
    context = RunContext(
        asset_id=getattr(inputs, "asset_id", "synthetic"),
        location_id=getattr(inputs, "location_id", "synthetic"),
        time_basis="test",
    )
    direct = registry.run(model_id, inputs, context)
    serialized = registry.run_json(model_id, inputs.model_dump_json(), context)
    assert direct.status == serialized.status == "computed"
    assert direct.model_dump() == serialized.model_dump()
