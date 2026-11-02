"""Verify fatigue benchmark arithmetic and endpoint policies with authored cases."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.contracts import RunContext
from matintegrity.models import fatigue_benchmark
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "tmp/pdfs/Assignment_FABEST_LCF_FINAL.pdf"


def _require_close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
        raise AssertionError(f"{label}: expected {expected}, received {actual}")


def main():
    registry = default_registry()
    context = RunContext(
        asset_id="authored-fatigue-benchmark",
        location_id="laboratory-comparison",
        time_basis="declared cycle observations",
    )
    cyclic = registry.run(
        "fatigue.cyclic_response_relative_error",
        {
            "series": [
                {
                    "experiment_id": "authored-a",
                    "cycle": [1, 10],
                    "observed_mean": [10.0, 10.0],
                    "predicted_mean": [11.0, 8.0],
                    "observed_amplitude": [20.0, 20.0],
                    "predicted_amplitude": [24.0, 18.0],
                    "mean_normalizer": 10.0,
                    "amplitude_normalizer": 20.0,
                },
                {
                    "experiment_id": "authored-exact",
                    "cycle": [1],
                    "observed_mean": [3.0],
                    "predicted_mean": [3.0],
                    "observed_amplitude": [4.0],
                    "predicted_amplitude": [4.0],
                    "mean_normalizer": 3.0,
                    "amplitude_normalizer": 4.0,
                },
            ]
        },
        context,
    )
    _require_close(cyclic.values["aggregate_weighted_relative_error"], 0.075, "cyclic metric")

    life = registry.run(
        "fatigue.life_rmsle",
        {
            "case_id": ["authored-over", "authored-under"],
            "observed_cycles": [100.0, 100.0],
            "predicted_cycles": [1000.0, 10.0],
        },
        context,
    )
    _require_close(life.values["root_mean_square_log_error"], 1.0, "life RMSLE")

    endpoint_base = {
        "test_id": "authored-endpoint",
        "cycle": [1.0, 5.0, 10.0],
        "compressive_dynamic_modulus_Pa": [100.0, 95.0, 85.0],
        "reference_dynamic_modulus_Pa": 100.0,
        "drop_fraction_threshold": 0.1,
        "observation_window_closed": True,
    }
    sampled = registry.run(
        "fatigue.dynamic_modulus_drop_endpoint",
        endpoint_base | {"crossing_policy": "first_observed_sample"},
        context,
    )
    interpolated = registry.run(
        "fatigue.dynamic_modulus_drop_endpoint",
        endpoint_base | {"crossing_policy": "linear_between_samples"},
        context,
    )
    _require_close(sampled.values["endpoint_cycle"], 10.0, "sampled endpoint")
    _require_close(interpolated.values["endpoint_cycle"], 7.5, "interpolated endpoint")

    record = {
        "schema_version": "matintegrity.fatigue_benchmark_metrics.v1",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_source_sha256": hashlib.sha256(Path(fatigue_benchmark.__file__).read_bytes()).hexdigest(),
        "benchmark_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "official_rules_sha256": hashlib.sha256(RULES.read_bytes()).hexdigest() if RULES.exists() else None,
        "cases": {
            "cyclic_response": {
                "input_digest": cyclic.input_digest,
                "expected_score": 0.075,
                "actual_score": cyclic.values["aggregate_weighted_relative_error"],
            },
            "life_rmsle": {
                "input_digest": life.input_digest,
                "expected_score": 1.0,
                "actual_score": life.values["root_mean_square_log_error"],
            },
            "sampled_endpoint": {
                "input_digest": sampled.input_digest,
                "expected_cycle": 10.0,
                "actual_cycle": sampled.values["endpoint_cycle"],
            },
            "linearly_interpolated_endpoint": {
                "input_digest": interpolated.input_digest,
                "expected_cycle": 7.5,
                "actual_cycle": interpolated.values["endpoint_cycle"],
            },
        },
        "qualification": (
            "Closed-form arithmetic checks with independently authored synthetic values. The source digest binds "
            "the reviewed official-rules version when locally available. These checks are not calibration, blind-test "
            "results, experimental validation, fatigue-life qualification or acceptance evidence."
        ),
    }
    target = ROOT / "validation/fatigue_benchmark_metrics.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
