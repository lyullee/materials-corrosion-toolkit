import copy
import json
from pathlib import Path

import pytest

from matintegrity import evaluate
from matintegrity.contracts import RunContext

EXAMPLE = json.loads(
    (Path(__file__).resolve().parents[1] / "examples/model_inputs.json").read_text(encoding="utf-8")
)["models"]["workflow.pressure_fatigue"]
CONTEXT = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="synthetic seconds")


def test_pressure_history_preserves_full_half_cycles_and_damage_conventions():
    result = evaluate("workflow.pressure_fatigue", EXAMPLE, CONTEXT)
    assert result.values["counted_cycles"] == 2
    life = 1e6 * (100e6 / 20e6) ** 3
    assert result.values["damage_increment"] == pytest.approx(2 / life)
    assert all(row["stress_ratio"] == pytest.approx(0.5) for row in result.values["cycles"])


@pytest.mark.parametrize("change", ["gap", "temperature", "range", "identity"])
def test_history_contract_does_not_bridge_missing_data_or_mix_domains(change):
    inputs = copy.deepcopy(EXAMPLE)
    if change == "gap":
        inputs["history"]["valid"][2] = False
    if change == "temperature":
        inputs["history"]["temperature_K"][2] = 400.0
    if change == "range":
        inputs["maximum_calibrated_stress_range_Pa"] = 15e6
    if change == "identity":
        inputs["history"]["asset_id"] = "other-asset"
        with pytest.raises(ValueError, match="asset and location"):
            evaluate("workflow.pressure_fatigue", inputs, CONTEXT)
        return
    assert evaluate("workflow.pressure_fatigue", inputs, CONTEXT).status == "out_of_scope"
