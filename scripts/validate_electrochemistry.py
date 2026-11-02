"""Verify nonlinear interpolant refinement against an independently derived current balance."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.contracts import RunContext
from matintegrity.models import electrochemistry
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]


def main():
    k = 11.0
    e0, density, areas = np.array([-0.8, -0.3]), np.array([0.03, 0.01]), np.array([1e-4, 3e-4])
    # Sum of opposing exponentials is zero when exp(2*k*E) equals their coefficient ratio.
    expected = math.log(
        np.sum(areas * density * np.exp(k * e0)) / np.sum(areas * density * np.exp(-k * e0))
    ) / (2 * k)
    expected_current = areas * 2 * density * np.sinh(k * (expected - e0))
    template = json.loads((ROOT / "examples/model_inputs.json").read_text(encoding="utf-8"))["models"][
        "corrosion.mixed_potential"
    ]
    records = []
    registry = default_registry()
    for count in (17, 65, 257, 1025):
        definition = json.loads(json.dumps(template))
        potential = np.linspace(-1.0, 0.0, count)
        for i, electrode in enumerate(definition["electrodes"]):
            curve = electrode["curve"]
            curve["point_ids"] = [f"authored-{i}-{j}" for j in range(count)]
            curve["potential_V"] = potential.tolist()
            curve["signed_net_current_density_A_m2"] = (
                2 * density[i] * np.sinh(k * (potential - e0[i]))
            ).tolist()
        result = registry.run_json(
            "corrosion.mixed_potential",
            json.dumps(definition),
            RunContext(
                asset_id="authored", location_id="two-kinetic-electrodes", time_basis="static response"
            ),
        )
        assert result.status == "computed"
        records.append(
            dict(
                points_per_electrode=count,
                input_digest=result.input_digest,
                potential_V=result.values["mixed_potential_V"],
                absolute_potential_error_V=abs(result.values["mixed_potential_V"] - expected),
                maximum_absolute_electrode_current_error_A=float(
                    np.max(np.abs(np.asarray(result.values["electrode_net_current_A"]) - expected_current))
                ),
                current_balance_residual_A=result.values["equilibria"][0]["current_balance_residual_A"],
            )
        )
    assert records[-1]["absolute_potential_error_V"] < 1e-7
    assert records[0]["absolute_potential_error_V"] / records[-1]["absolute_potential_error_V"] > 1000
    record = dict(
        schema_version="matintegrity.electrochemistry_math.v1",
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        status="passed",
        model_id="corrosion.mixed_potential",
        model_version=result.model_version,
        model_source_sha256=hashlib.sha256(Path(electrochemistry.__file__).read_bytes()).hexdigest(),
        benchmark_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        expected_potential_V=expected,
        expected_electrode_net_current_A=expected_current.tolist(),
        authored_parameters=dict(
            k_per_V=k,
            zero_current_potentials_V=e0.tolist(),
            reaction_current_density_A_m2=density.tolist(),
            exposed_areas_m2=areas.tolist(),
        ),
        refinements=records,
        runtime=result.runtime,
        qualification="Authored symmetric opposing-reaction benchmark and interpolation refinement only; no experimental calibration, kinetic parameter identification or galvanic validation.",
    )
    (ROOT / "validation/electrochemistry_math.json").write_text(
        json.dumps(record, indent=2), encoding="utf-8"
    )
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
