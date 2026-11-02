"""Create a public-safe aggregate audit of the CEIT near-shore field dataset."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from matintegrity.ultrasound_data import read_ceit_uniform_corrosion_field

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/raw/ceit-uniform-corrosion-field/UniformCorrosionExperiment_Ceit.json"
OUTPUT = ROOT / "validation/ceit_uniform_corrosion_field.json"
EXPECTED_SHA256 = "87033b35f7964eb34265e6e4e5f0e1252b2214480b6f39871029811e3e3dbf1b"


def numeric_range(observations: list[dict], key: str) -> list[float]:
    values = np.asarray([row[key] for row in observations], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError(f"nonfinite {key} values")
    return [float(values.min()), float(values.max())]


def inspect() -> dict:
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("CEIT field source hash changed")
    result = read_ceit_uniform_corrosion_field(SOURCE, series_id="S355-00-02")
    observations = result["observations"]
    timestamps = [row["timestamp"] for row in observations]
    gaps_s = np.diff(np.asarray([stamp.timestamp() for stamp in timestamps], dtype=float))
    day_counts = Counter(stamp.date().isoformat() for stamp in timestamps)
    day_count_histogram = Counter(day_counts.values())
    signal_lengths = {
        key: dict(sorted(Counter(len(row[key]) for row in observations).items()))
        for key in ("raw_signal", "filtered_signal", "correlation_signal", "envelope_signal")
    }
    rail_counts = np.asarray([row["raw_adc_rail_count"] for row in observations], dtype=int)
    return {
        "schema": "matintegrity.ceit_uniform_corrosion_field_aggregate.v1",
        "dataset_id": result["source_id"],
        "dataset_doi": "10.5281/zenodo.13897090",
        "license": "CC-BY-4.0",
        "source_file": SOURCE.name,
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": digest,
        "physical_specimens": 1,
        "observational_unit": result["observational_unit"],
        "record_count": len(observations),
        "identities": result["identities"],
        "provider_clock": {
            "basis": result["timestamp_basis"],
            "start": timestamps[0].isoformat(timespec="milliseconds"),
            "end": timestamps[-1].isoformat(timespec="milliseconds"),
            "strictly_increasing": bool(np.all(gaps_s > 0)),
            "minimum_gap_s": float(gaps_s.min()),
            "median_gap_s": float(np.median(gaps_s)),
            "maximum_gap_s": float(gaps_s.max()),
            "gaps_over_one_hour": int(np.count_nonzero(gaps_s > 3600)),
            "gaps_over_one_day": int(np.count_nonzero(gaps_s > 86400)),
            "observed_calendar_days": len(day_counts),
            "records_per_observed_calendar_day_histogram": {
                str(count): days for count, days in sorted(day_count_histogram.items())
            },
        },
        "reported_ranges_unqualified_units": {
            key: numeric_range(observations, key)
            for key in (
                "reported_tof_reference",
                "tof_reported",
                "tof_compensated_reported",
                "reported_temperature",
                "reported_battery",
                "reported_amplitude",
            )
        },
        "signal_lengths": signal_lengths,
        "all_signal_samples_finite": True,
        "records_with_raw_adc_rail_values": int(np.count_nonzero(rail_counts)),
        "raw_adc_rail_count_range": [int(rail_counts.min()), int(rail_counts.max())],
        "reported_tof_first_to_last_change_unqualified": float(
            observations[-1]["tof_reported"] - observations[0]["tof_reported"]
        ),
        "reported_compensated_tof_first_to_last_change_unqualified": float(
            observations[-1]["tof_compensated_reported"] - observations[0]["tof_compensated_reported"]
        ),
        "provider_summary_corrosion_rate_um_per_year": 134.0,
        "provider_summary_reproduced_from_file": False,
        "thickness_series_ready": False,
        "corrosion_rate_fit_ready": False,
        "remaining_life_ready": False,
        "failure_probability_ready": False,
        "qualification": (
            "The file proves one repeated device series and its raw/processed arrays. ToF and temperature "
            "units, wave speed, propagation path, calibration, spatial footprint, measurement uncertainty "
            "and independent dimensional ground truth are not supplied in the JSON, so no wall-thickness "
            "or corrosion-rate series is inferred. The provider's 134 micrometres/year summary is recorded "
            "but not reproduced from undocumented assumptions."
        ),
        "public_release_boundary": (
            "Only this aggregate audit and independently authored reader are public. Raw observations and "
            "waveforms remain outside source distributions."
        ),
    }


if __name__ == "__main__":
    audit = inspect()
    OUTPUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
