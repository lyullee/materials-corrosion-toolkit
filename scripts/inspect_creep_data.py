"""Aggregate primary creep data audit and a small within-source holdout."""

from __future__ import annotations

import hashlib
import math

import numpy as np
from scipy.stats import norm

from matintegrity import evaluate
from matintegrity.contracts import Evidence, RunContext, canonical_digest
from matintegrity.creep_data import read_cmsx6_creep, read_cmsx6_trace


def inspect(raw):
    folder = raw / "cmsx6-creep"
    workbook = next(folder.glob("*.xlsx"))
    frame = read_cmsx6_creep(workbook)
    if frame.endpoint_kind.eq("unresolved").any():
        raise ValueError("resolve termination criteria before calibration")
    traces = []
    ids = set(frame.specimen_id)
    for path in sorted(folder.glob("*.LIS")):
        trace = read_cmsx6_trace(path, duplicate_policy="preserve")
        if trace.attrs["specimen_id"] not in ids:
            raise ValueError("processed trace has no matching test record")
        traces.append(
            dict(
                specimen_id=path.stem,
                rows=len(trace),
                repeated_clock_intervals=trace.attrs["repeated_clock_intervals"],
                source_sha256=trace.attrs["source_sha256"],
            )
        )
    if {r["specimen_id"] for r in traces} != ids:
        raise ValueError("missing processed test trace")
    # Reserve one specimen at every stress level without looking at life/endpoint.
    held_ids = []
    for _, group in frame.groupby("initial_stress_Pa", sort=True):
        held_ids.append(min(group.specimen_id, key=lambda s: hashlib.sha256(s.encode()).hexdigest()))
    held = frame[frame.specimen_id.isin(held_ids)]
    train = frame[~frame.specimen_id.isin(held_ids)]
    context = RunContext(
        asset_id="cmsx6-reference-pilot",
        location_id="specimen-gauge",
        time_basis="reported seconds of constant-load creep from fresh test condition",
    )
    evidence = Evidence(
        source_id="cmsx6-creep",
        origin="open_dataset",
        citation="BAM reference data v1, DOI 10.5281/zenodo.14750432",
        license_id="CC-BY-4.0",
        sha256=frame.attrs["source_sha256"],
    )
    inputs = dict(
        material_condition_id=str(train.material_condition_id.iloc[0]),
        stress_basis="initial_nominal_constant_load",
        temperature_basis="nominal_specified",
        family="stress_only",
        specimen_id=train.specimen_id.tolist(),
        initial_stress_Pa=train.initial_stress_Pa.tolist(),
        temperature_K=train.temperature_K.tolist(),
        endpoint_time_s=train.endpoint_time_s.tolist(),
        right_censored=train.right_censored.tolist(),
        temperature_tolerance_K=0.0,
        independent_specimens_confirmed=True,
        common_mechanism_and_condition_confirmed=True,
        evidence=(evidence,),
    )
    fit = evaluate("creep.lognormal_life_fit", inputs, context)
    if fit.status != "computed":
        raise ValueError(f"pilot fit did not compute: {fit.notes}")
    m = fit.values["model"]
    mu = m["log_reference_median_time_s"] - m["stress_exponent"] * (
        np.log(held.initial_stress_Pa.to_numpy()) - math.log(m["reference_stress_Pa"])
    )
    y = np.log(held.endpoint_time_s.to_numpy())
    c = held.right_censored.to_numpy(dtype=bool)
    nll = -np.where(c, norm.logsf(y, mu, m["log_life_sigma"]), norm.logpdf(y, mu, m["log_life_sigma"]) - y)
    return dict(
        observations=len(frame),
        observed_ruptures=int((~frame.right_censored).sum()),
        administrative_right_censored=int(frame.right_censored.sum()),
        nominal_temperatures_K=sorted(frame.temperature_K.unique().tolist()),
        initial_nominal_stress_levels_Pa=sorted(frame.initial_stress_Pa.unique().tolist()),
        stress_basis="initial_nominal_constant_load",
        temperature_basis="nominal_specified",
        trace_rows=sum(t["rows"] for t in traces),
        repeated_clock_intervals=sum(t["repeated_clock_intervals"] for t in traces),
        traces=traces,
        source_sha256=frame.attrs["source_sha256"],
        license_id="CC-BY-4.0",
        training_rows=len(train),
        heldout_rows=len(held),
        heldout_failures=int((~c).sum()),
        split_algorithm="lowest SHA-256 specimen ID at each initial stress level is held out",
        split_digest=canonical_digest(
            dict(train=sorted(train.specimen_id), heldout=sorted(held.specimen_id))
        ),
        pilot_fit=fit.values,
        heldout_failure_log_rmse=float(np.sqrt(np.mean((y[~c] - mu[~c]) ** 2))),
        heldout_negative_log_likelihood_seconds=float(nll.sum()),
        qualification="One material condition and one nominal temperature from the same laboratory. Four within-source held-out specimens are not external validation. Activation energy is unestimated; do not transfer constant-load initial nominal stress to constant true stress or infer variable-history creep-fatigue. Rounded repeated clocks are preserved. Raw/pointwise life and waveform observations are not redistributed.",
    )
