"""Aggregate domain/quality audits; never export observations or infer field size truth."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from matintegrity.ultrasound_data import (
    iter_willow_simulations,
    read_willow_feature_table,
    read_willow_field_signals,
)


def fingerprint(path: Path):
    return dict(filename=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def descriptor_diagnostics(frame):
    result = {}
    for column in (
        "metrics_env_peak_dist_ec1_m",
        "metrics_ht_env_peak_distance_m",
        "metrics_xcr_ec1_proto_peak_distance_m",
    ):
        finite = np.isfinite(frame[column])
        usable = frame.processing_success & finite
        row = dict(
            processing_success_rows=int(frame.processing_success.sum()),
            finite_feature_rows=int(finite.sum()),
            usable_rows=int(usable.sum()),
        )
        if "synthetic_reference_depth_m" in frame:
            residual = (
                frame.loc[usable, column] - frame.loc[usable, "synthetic_reference_depth_m"]
            ).to_numpy()
            row.update(
                unadjusted_descriptor_minus_effective_depth_bias_m=float(residual.mean())
                if len(residual)
                else None,
                unadjusted_descriptor_minus_effective_depth_rmse_m=float(np.sqrt(np.mean(residual**2)))
                if len(residual)
                else None,
            )
        result[column] = row
    return result


def inspect(raw: Path) -> dict:
    simulations = []
    for thickness in (3, 5):
        table_path = raw / f"willow-synthetic/dataset_ml_{thickness}mm_1000samples.xlsx"
        waveform_path = raw / f"willow-synthetic/dataset_{thickness}mm_synthetic.mat"
        table = read_willow_feature_table(
            table_path,
            domain="simulation",
            series_id=f"synthetic-{thickness}mm",
            synthetic_length_unit="mm",
            specimen_thickness_m=thickness / 1000,
        ).set_index("simu", drop=False)
        errors, finite_count, sizes, shape_mismatches = [], 0, set(), 0
        indices = set()
        for row in iter_willow_simulations(waveform_path, source_length_unit="m"):
            indices.add(row["simulation_index"])
            reported = table.loc[row["simulation_index"]]
            for key, expected in (
                ("depth_eff_m", row["effective_depth_m"]),
                ("width_eff_m", row["effective_width_m"]),
                ("depth_m", row["input_geometry"]["depth_m"]),
                ("width_m", row["input_geometry"]["width_m"]),
                ("transducer_length_m", row["transducer_length_m"]),
            ):
                errors.append(abs(float(reported[key]) - expected))
            finite_count += row["raw_signal_finite"]
            sizes.add(len(row["raw_signal"]))
            shape_mismatches += str(reported["shape"]) != row["pit_shape"]
        if (
            indices != set(table.index)
            or not np.isfinite(errors).all()
            or max(errors) > 1e-12
            or shape_mismatches
        ):
            raise ValueError("simulation MAT and workbook geometry/case mapping is inconsistent")
        simulations.append(
            dict(
                table=fingerprint(table_path),
                waveforms=fingerprint(waveform_path),
                observations=len(table),
                processing_success_rows=int(table.processing_success.sum()),
                processing_failure_rows=int((~table.processing_success).sum()),
                simulation_cases=len(indices),
                finite_raw_signals=int(finite_count),
                waveform_sample_counts=sorted(sizes),
                geometry_max_abs_difference_m=max(errors),
                shape_mismatches=int(shape_mismatches),
                shape_counts={str(k): int(v) for k, v in table["shape"].value_counts().items()},
                descriptor_diagnostics=descriptor_diagnostics(table),
                descriptor_diagnostics_by_transducer={
                    str(label): descriptor_diagnostics(group) for label, group in table.groupby("transducer")
                },
                waveform_timebase="not published in selected MAT cells; no sample interval inferred",
            )
        )
    field = []
    for sensor, workbook, waveform in (
        ("V116", "Harshlab_V116_1mm_0p5mm_pit_evolution.xlsx", "april2july_DAA5_V116.json"),
        ("V212", "Harshlab_V212_2mm_0p7mm_pit_evolution.xlsx", "september2april_DA8F_V212.json"),
    ):
        table_path, waveform_path = (raw / "willow-harshlab" / name for name in (workbook, waveform))
        series = f"field-{sensor}"
        table = read_willow_feature_table(table_path, domain="field", series_id=series)
        signals = read_willow_field_signals(waveform_path, series_id=series)
        observations = signals["observations"]
        stamps = [row["timestamp"] for row in observations]
        if (
            set(stamps) != set(table.timestamp)
            or len(stamps) != len(table)
            or table.duplicate_timestamp.any()
        ):
            raise ValueError("field raw/processed timestamp mapping is not one-to-one")
        intervals = np.array([(b - a).total_seconds() for a, b in zip(stamps, stamps[1:], strict=False)])
        field.append(
            dict(
                table=fingerprint(table_path),
                raw_signals=fingerprint(waveform_path),
                transducer=sensor,
                observations=len(table),
                distinct_specimen_series=1,
                processing_success_rows=int(table.processing_success.sum()),
                processing_failure_rows=int((~table.processing_success).sum()),
                failure_reason_counts={
                    str(k): int(v)
                    for k, v in table.loc[~table.processing_success, "reason"].value_counts().items()
                },
                matched_raw_processed_timestamps=len(stamps),
                first_timestamp=stamps[0].isoformat(),
                last_timestamp=stamps[-1].isoformat(),
                timestamp_basis=signals["timestamp_basis"],
                recorded_interval_min_median_max_s=np.quantile(intervals, [0, 0.5, 1]).tolist(),
                recorded_intervals_over_12_h=int((intervals > 12 * 3600).sum()),
                finite_raw_signals=sum(row["raw_signal_finite"] for row in observations),
                raw_signal_sample_counts=sorted({len(row["raw_signal"]) for row in observations}),
                device_gain_configurations=len(
                    {str(row["reported_device_fields"].get("MeasGain")) for row in observations}
                ),
                device_filter_configurations=len(
                    {str(row["reported_device_fields"].get("Filtered")) for row in observations}
                ),
                recorded_initial_depth_distinct_values=int(table.initial_pit_depth_m.nunique()),
                descriptor_diagnostics=descriptor_diagnostics(table),
                time_varying_independent_depth_truth_available=False,
            )
        )
    return {
        "willow-synthetic": dict(
            workbooks=simulations,
            qualification="Two simulation domains, not physical inspection trials. Raw/feature geometry mapping is verified. Unadjusted descriptor errors are diagnostic comparisons to simulated effective geometry, not a qualified sizing curve. Missing/failed descriptors remain missing; all-pitted cases do not establish POD or false-positive rate.",
        ),
        "willow-harshlab": dict(
            specimen_series=field,
            qualification="Two repeated field specimen series, not 774 independent specimens. Initial pre-pit geometry is constant metadata, not a time-varying reference depth. Processing success is not sizing validity; timezone, sample clock and specimen-temperature basis remain unresolved. No block-maxima extreme fit, growth-rate truth or failure probability is inferred.",
        ),
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(json.dumps(inspect(root / "data/raw"), ensure_ascii=True, indent=2, allow_nan=False))
