"""Compare selected guided-wave records with a predeclared healthy-period ensemble."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.adapters import guided_wave_reference_ensemble_inputs
from matintegrity.contracts import Evidence, RunContext
from matintegrity.guided_wave_data import GUIDED_WAVE_ARCHIVE_SHA256, read_guided_wave_acquisition
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/guided-wave-pipeline-shm/ttb63krg6d-1.zip"
SPECIMEN_ID = "published-single-steel-tube"
BASELINE_IDS = (1622, 1673, 1700, 1750, 1800, 1850, 1890)
OBSERVATIONS = (
    (1901, "later_reported_healthy_period_descriptive"),
    (1902, "first_post_machining_period_descriptive"),
    (1930, "last_post_machining_period_descriptive"),
)
FREQUENCY_HZ = 14_000.0
WINDOW_M = (2.0, 3.2)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(path: Path = ARCHIVE) -> dict:
    baselines = [
        read_guided_wave_acquisition(path, acquisition_id, specimen_id=SPECIMEN_ID)
        for acquisition_id in BASELINE_IDS
    ]
    if {record["article_period_group"] for record in baselines} != {"reported_healthy_period"}:
        raise ValueError(
            "predeclared guided-wave reference records are not all in the reviewed healthy period"
        )
    registry = default_registry()
    evidence = Evidence(
        source_id="guided-wave-pipeline-shm",
        origin="open_dataset",
        citation="El Mountassir, M., Mendeley Data v1, doi:10.17632/ttb63krg6d.1",
        license_id="CC-BY-4.0",
        sha256=GUIDED_WAVE_ARCHIVE_SHA256,
    )
    records = []
    for acquisition_id, role in OBSERVATIONS:
        observation = read_guided_wave_acquisition(path, acquisition_id, specimen_id=SPECIMEN_ID)
        for wave_mode in ("torsional", "flexural"):
            inputs = guided_wave_reference_ensemble_inputs(
                baselines,
                observation,
                baseline_source_group_id="predeclared-seven-record-healthy-period-reference",
                observation_source_group_id=role,
                baseline_selection_basis=(
                    "seven acquisition IDs distributed across the reviewed healthy period and fixed in source "
                    "before calculating the three observation comparisons"
                ),
                frequency_Hz=FREQUENCY_HZ,
                wave_mode=wave_mode,
                window_start_m=WINDOW_M[0],
                window_end_m=WINDOW_M[1],
                reference_statistic="median",
                duplicate_distance_policy="mean_aligned_duplicates",
            )
            result = registry.run(
                "inspection.guided_wave_reference_ensemble",
                inputs,
                RunContext(
                    asset_id=SPECIMEN_ID,
                    location_id="positive-distance-2.0-to-3.2-m-window",
                    time_basis="provider acquisition order; acquisition timestamps unavailable",
                    evidence=(evidence,),
                    metadata={
                        "baseline_article_period_group": "reported_healthy_period",
                        "observation_article_period_group": observation["article_period_group"],
                        "comparison_role": role,
                    },
                ),
            )
            if result.status != "computed":
                raise ValueError(f"guided-wave ensemble comparison was not computed: {role}/{wave_mode}")
            records.append(
                {
                    "comparison_role": role,
                    "observation_article_period_group": observation["article_period_group"],
                    "wave_mode": wave_mode,
                    "input_digest": result.input_digest,
                    "values": result.values,
                    "notes": list(result.notes),
                }
            )
    return {
        "schema_version": "matintegrity.validation.guided_wave_reference_ensemble.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "inspection.guided_wave_reference_ensemble",
        "model_source_sha256": _digest(ROOT / "src/matintegrity/models/inspection.py"),
        "adapter_source_sha256": _digest(ROOT / "src/matintegrity/adapters.py"),
        "dataset_id": "guided-wave-pipeline-shm",
        "dataset_doi": "10.17632/ttb63krg6d.1",
        "dataset_license": "CC-BY-4.0",
        "outer_archive_sha256": GUIDED_WAVE_ARCHIVE_SHA256,
        "specimen_id": SPECIMEN_ID,
        "baseline_acquisition_ids": list(BASELINE_IDS),
        "baseline_article_period_group": "reported_healthy_period",
        "frequency_Hz": FREQUENCY_HZ,
        "window_m": list(WINDOW_M),
        "reference_statistic": "median",
        "duplicate_distance_policy": "mean_aligned_duplicates",
        "comparisons": records,
        "qualification": (
            "Descriptive comparisons against seven predeclared records distributed across the reviewed healthy "
            "period. All records come from the same reported tube and are not independent specimens. The dataset "
            "does not supply acquisition temperature, timestamp, coupling state, six-step mapping, remaining wall "
            "thickness or defect dimensions. Leave-one-out and observation ratios describe only this selected "
            "ensemble and are not anomaly probabilities, calibrated thresholds, damage classification, POD, "
            "acceptance, remaining life or failure probability. No point waveform arrays are copied here."
        ),
    }


if __name__ == "__main__":
    target = ROOT / "validation/guided_wave_reference_ensemble.json"
    target.write_text(json.dumps(validate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
