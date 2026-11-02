"""Independent analytic checks for the authored tensor-work execution examples."""

import json
import math
import runpy
from functools import lru_cache
from pathlib import Path

import pytest

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


@lru_cache(maxsize=1)
def cases():
    return runpy.run_path(str(Path(__file__).resolve().parents[1] / "examples/core_full_execution_cases.py"))[
        "sample_requests"
    ]()


@pytest.mark.parametrize(
    "model_id,quantity,expected",
    [
        ("fatigue.periodic_fourier_tensor_work", "signed_work_density_J_m3", math.pi * 1e5),
        (
            "fatigue.sampled_tensor_stress_strain_work_cycle",
            "signed_net_work_density_J_m3",
            4 * 1e5 * math.sin(math.pi / 4),
        ),
        ("fatigue.periodic_fourier_tensor_work_life", "cumulative_miner_damage", 10 * math.pi * 1e5 / 1e10),
    ],
)
def test_work_examples_match_independent_closed_form(model_id, quantity, expected):
    registry = default_registry()
    result = registry.run_json(
        model_id,
        json.dumps(cases()[model_id]),
        RunContext(asset_id="toy", location_id="toy", time_basis="normalized cycle"),
    )
    assert result.status == "computed"
    assert result.values[quantity] == pytest.approx(expected, rel=1e-12)
