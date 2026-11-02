"""Review flags gate only the creep output they declare."""

import json
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def test_unreviewed_rupture_fraction_is_withheld_without_suppressing_creep_strain():
    baselines = json.loads(
        (Path(__file__).parent / "data" / "core_physics_valid_input_baselines.json").read_text(
            encoding="utf-8"
        )
    )["model_inputs"]
    request = dict(baselines["creep.secondary_history"])
    request["linear_rupture_time_fraction_reviewed"] = False

    result = default_registry().run_json(
        "creep.secondary_history",
        json.dumps(request),
        RunContext(asset_id="synthetic", location_id="synthetic", time_basis="input-gate"),
    )

    assert result.status == "computed"
    assert result.values["secondary_creep_strain"] is not None
    assert result.values["linear_rupture_time_fraction"] is None
