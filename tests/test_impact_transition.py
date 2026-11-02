import copy
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from matintegrity import evaluate
from matintegrity.contracts import RunContext
from matintegrity.impact_data import read_charpy_compilation

ROOT = Path(__file__).resolve().parents[1]
INPUT = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
    "materials.impact_transition"
]
CONTEXT = RunContext(asset_id="synthetic", location_id="synthetic", time_basis="synthetic series")


def test_impact_recovers_shelves_width_and_observed_target_crossing():
    result = evaluate("materials.impact_transition", INPUT, CONTEXT)
    assert result.status == "computed"
    assert result.values["lower_shelf_energy_J"] == pytest.approx(5.0, abs=1e-5)
    assert result.values["upper_shelf_energy_J"] == pytest.approx(100.0, abs=1e-5)
    assert result.values["mid_shelf_temperature_K"] == pytest.approx(250.0, abs=1e-5)
    assert result.values["logistic_transition_width_K"] == pytest.approx(20.0, abs=1e-5)
    assert result.values["target_energy_crossing_temperature_K"] == pytest.approx(250.0, abs=1e-5)


def test_impact_missing_shelves_and_outside_energy_do_not_create_a_service_limit():
    inputs = copy.deepcopy(INPUT)
    inputs["temperature_K"] = np.linspace(249, 251, 9).tolist()
    inputs["absorbed_energy_J"] = [5 + 95 / (1 + math.exp(-(t - 250) / 20)) for t in inputs["temperature_K"]]
    assert evaluate("materials.impact_transition", inputs, CONTEXT).status == "needs_data"
    inputs = copy.deepcopy(INPUT)
    inputs["target_energy_J"] = 200.0
    assert (
        evaluate("materials.impact_transition", inputs, CONTEXT).values[
            "target_energy_crossing_temperature_K"
        ]
        is None
    )


def test_robust_impact_fit_limits_one_outliers_influence_on_unaffected_points():
    inputs = copy.deepcopy(INPUT)
    truth = np.array(inputs["absorbed_energy_J"])
    inputs["absorbed_energy_J"][5] += 100
    robust = evaluate("materials.impact_transition", inputs, CONTEXT)
    inputs["loss"] = "linear"
    conventional = evaluate("materials.impact_transition", inputs, CONTEXT)
    good = np.arange(len(truth)) != 5
    assert np.median(np.abs(np.array(robust.values["fitted_energy_J"])[good] - truth[good])) < np.median(
        np.abs(np.array(conventional.values["fitted_energy_J"])[good] - truth[good])
    )


def test_charpy_reader_converts_units_and_splits_mixed_irradiation_curve_ids(tmp_path):
    rows = []
    for irradiation in ["No", "Yes"]:
        rows.append(
            {
                "Reference": 1,
                "Material": "synthetic",
                "Irradiated Specimen": irradiation,
                "Test Temperature (C)": -100.0,
                "Impact energy (J)": 5.0,
                "Length (mm)": 55.0,
                "Width (mm)": 10.0,
                "Thickness (mm)": 5.0,
                "Orientation": "L",
                "DBTT Fitted Curve": 1,
            }
        )
    path = tmp_path / "synthetic.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name="Charpy Data", index=False, startrow=1)
        pd.DataFrame([{"Reference": 1, "Link": "https://example.org/synthetic"}]).to_excel(
            writer, sheet_name="References", index=False
        )
    frame = read_charpy_compilation(path)
    assert frame.temperature_K.tolist() == pytest.approx([173.15, 173.15])
    assert frame.width_m.tolist() == [0.01, 0.01] and frame.thickness_m.tolist() == [0.005, 0.005]
    assert frame.condition_group_digest.nunique() == 2
    assert frame.original_reference_link.tolist() == ["https://example.org/synthetic"] * 2
