"""Reproduce analytical sensitivity benchmarks; no acquired observations are redistributed."""

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from matintegrity.sensitivity import SobolRequest, run_sobol

ROOT = Path(__file__).resolve().parents[1]


def main():
    evidence = dict(
        source_id="authored-benchmark",
        origin="synthetic",
        citation="Ishigami-Homma mathematical benchmark; authored expression and analytical moments",
    )
    specification = SobolRequest.model_validate_json(
        json.dumps(
            dict(
                analysis_id="ishigami-verification",
                context=dict(
                    asset_id="synthetic", location_id="mathematical-function", time_basis="static response"
                ),
                evaluator_id="ishigami-a7-b0.1",
                evaluator_revision=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                parameters=[
                    dict(
                        name=s, unit="1", family="uniform", lower=-math.pi, upper=math.pi, evidence=[evidence]
                    )
                    for s in ("x", "y", "z")
                ],
                quantities=[dict(name="response", unit="1")],
                sample_powers=[8, 10, 12],
                scrambles=8,
                seed=2026,
                independence_declared=True,
                deterministic_response_declared=True,
            )
        )
    )
    report = run_sobol(
        specification, lambda d: np.sin(d["x"]) * (1 + 0.1 * d["z"] ** 4) + 7 * np.sin(d["y"]) ** 2
    )
    v1 = 0.5 * (1 + 0.1 * math.pi**4 / 5) ** 2
    v2 = 49 / 8
    interaction = 0.01 * math.pi**8 * 8 / 225
    variance = v1 + v2 + interaction
    expected_first = np.asarray([v1 / variance, v2 / variance, 0.0])
    expected_total = np.asarray([(v1 + interaction) / variance, v2 / variance, interaction / variance])
    actual = report.quantities[0].levels[-1]
    first_error = float(np.max(np.abs(actual.first_order - expected_first)))
    total_error = float(np.max(np.abs(actual.total_order - expected_total)))
    if report.status != "computed" or max(first_error, total_error) > 0.015:
        raise ValueError("closed-moment sensitivity comparison failed")
    record = dict(
        schema_version="matintegrity.sensitivity_verification.v1",
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        status="passed",
        module_source_sha256=hashlib.sha256(
            (ROOT / "src/matintegrity/sensitivity.py").read_bytes()
        ).hexdigest(),
        benchmark_source="https://doi.org/10.1109/ISUMA.1990.151285",
        expected_first_order=expected_first.tolist(),
        expected_total_order=expected_total.tolist(),
        maximum_absolute_first_error=first_error,
        maximum_absolute_total_error=total_error,
        report=report.model_dump(mode="json"),
        qualification="Known analytical benchmark only; criteria and intervals diagnose integration of this declared deterministic function. They do not certify physical models, empirical marginal distributions or nominal coverage.",
    )
    (ROOT / "validation/sensitivity_math.json").write_text(
        json.dumps(record, indent=2, allow_nan=False), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: record[k]
                for k in ("status", "maximum_absolute_first_error", "maximum_absolute_total_error")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
