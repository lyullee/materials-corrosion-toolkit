import runpy
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parent
CASES = (
    ("test_metallurgical_aging.py", "payload", "degradation.metallurgical_aging_exposure"),
    ("test_nonisothermal_oxidation.py", "payload", "degradation.nonisothermal_parabolic_oxidation"),
    ("test_sulfidation.py", "request", "degradation.sulfidation_exposure_applicability"),
    ("test_carburization.py", "request", "degradation.carburization_applicability"),
    ("test_nitriding_degradation.py", "inputs", "degradation.nitriding_applicability"),
    ("test_selective_leaching.py", "inputs", "degradation.selective_leaching_applicability"),
    ("test_brittle_applicability.py", "payload", "materials.brittle_applicability_evidence"),
    ("test_liquid_metal_embrittlement.py", "payload", "degradation.liquid_metal_embrittlement_applicability"),
    ("test_sour_environment.py", "request", "degradation.sour_environment_applicability"),
)


@pytest.fixture(scope="module")
def registry():
    return default_registry()


@pytest.mark.parametrize("filename,factory,model_id", CASES)
def test_environment_python_json_exchange_preserves_scoped_result(registry, filename, factory, model_id):
    inputs = registry.input_type(model_id).model_validate(runpy.run_path(str(ROOT / filename))[factory]())
    context = RunContext(
        asset_id=getattr(inputs, "asset_id", "synthetic-asset"),
        location_id=getattr(inputs, "location_id", "synthetic-location"),
        time_basis="synthetic-test",
    )
    direct = registry.run(model_id, inputs, context)
    serialized = registry.run_json(model_id, inputs.model_dump_json(), context)
    assert direct.status == serialized.status == "computed"
    assert direct.model_dump() == serialized.model_dump()
