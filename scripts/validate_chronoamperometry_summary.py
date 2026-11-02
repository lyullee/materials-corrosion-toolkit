"""Validate authored window integration and exercise it on one pinned raw SECCM trace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from matintegrity.adapters import seccm_chronoamperometry_summary_inputs
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.seccm_data import read_seccm_ca_trace

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--archive",
        type=Path,
        default=ROOT / "data/raw/seccm-ebsd-316l-pitting-v1/seccm-ebsd-316l-pitting_dataset.zip",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "validation/chronoamperometry_window_summary_math.json",
    )
    args = parser.parse_args()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="authored", time_basis="declared trace time")
    synthetic = registry.run(
        "corrosion.chronoamperometry_window_summary",
        {
            "trace_id": "authored-affine-trace",
            "physical_specimen_id": "authored-specimen",
            "source_group_id": "authored-math-check",
            "source_trace_sha256": "a" * 64,
            "time_s": [0.0, 1.0, 3.0, 4.0],
            "current_A": [-2.0, 0.0, 4.0, 6.0],
            "analysis_window_s": [0.5, 3.5],
            "baseline_window_s": [0.0, 1.0],
            "boundary_policy": "piecewise_linear",
            "sample_order_reviewed": True,
            "time_unit_reviewed_as_seconds": True,
            "current_unit_reviewed_as_amperes": True,
            "current_sign_basis": "authored I(t)=2t-2 A",
            "current_sign_reviewed": True,
        },
        context,
    )
    expected = {
        "signed_charge_C": 6.0,
        "absolute_charge_C": 6.5,
        "baseline_time_mean_current_A": -1.0,
        "minimum_current_A": -1.0,
        "maximum_current_A": 5.0,
    }
    errors = {key: abs(synthetic.values[key] - value) for key, value in expected.items()}
    if synthetic.status != "computed" or max(errors.values()) > 1e-14:
        raise ValueError("authored chronoamperometry closed-form comparison failed")

    trace = read_seccm_ca_trace(
        args.archive,
        1,
        physical_specimen_id="provider-map-physical-scope-unresolved",
        source_group_id="seccm-map-1031-c",
    )
    seccm_inputs = seccm_chronoamperometry_summary_inputs(
        trace,
        analysis_window_s=[float(trace["time_s"][0]), float(trace["time_s"][-1])],
        boundary_policy="exact_samples",
        current_sign_basis="provider-reported substrate-current sign; electrochemical polarity not inferred",
        current_sign_reviewed=True,
    )
    seccm = registry.run(
        "corrosion.chronoamperometry_window_summary",
        seccm_inputs,
        RunContext(
            asset_id="provider-map-physical-scope-unresolved",
            location_id="MAP_Point_1",
            time_basis="provider hold time",
        ),
    )
    if seccm.status != "computed":
        raise ValueError("pinned SECCM raw trace integration did not compute")
    record = {
        "schema_version": "matintegrity.validation.chronoamperometry_window_summary.v1",
        "model_id": "corrosion.chronoamperometry_window_summary",
        "synthetic_piecewise_linear_check": {
            "status": synthetic.status,
            "expected": expected,
            "absolute_errors": errors,
            "maximum_absolute_error": max(errors.values()),
        },
        "pinned_seccm_application": {
            "status": seccm.status,
            "trace_id": seccm.values["trace_id"],
            "physical_specimen_id": seccm.values["physical_specimen_id"],
            "source_group_id": seccm.values["source_group_id"],
            "source_trace_sha256": seccm.values["source_trace_sha256"],
            "source_archive_sha256": seccm.values["source_archive_sha256"],
            "source_member_sha256": seccm.values["source_member_sha256"],
            "analysis_window_s": seccm.values["analysis_window_s"],
            "analysis_sample_count": seccm.values["analysis_sample_count"],
            "signed_charge_C": seccm.values["signed_charge_C"],
            "absolute_charge_C": seccm.values["absolute_charge_C"],
            "minimum_current_A": seccm.values["minimum_current_A"],
            "maximum_current_A": seccm.values["maximum_current_A"],
            "current_sign_basis": seccm.values["current_sign_basis"],
        },
        "qualification": (
            "The synthetic comparison validates authored piecewise-linear window arithmetic. The pinned "
            "SECCM application is one descriptive map-point trace, not an independent specimen, provider-"
            "descriptor reproduction, electrochemical polarity determination, event class, pit size, POD, "
            "life, acceptance or failure probability."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
