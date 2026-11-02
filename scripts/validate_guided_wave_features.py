"""Record bounded descriptive comparisons from the pinned guided-wave dataset."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from matintegrity.adapters import guided_wave_pair_feature_inputs
from matintegrity.contracts import Evidence, RunContext
from matintegrity.guided_wave_data import GUIDED_WAVE_ARCHIVE_SHA256, read_guided_wave_acquisition
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/guided-wave-pipeline-shm/ttb63krg6d-1.zip"
SPECIMEN_ID = "published-single-steel-tube"
BASELINE_ACQUISITION_ID = 1622
COMPARISONS = (
    (1901, "later_reported_healthy_period_descriptive"),
    (1902, "first_post_machining_period_descriptive"),
    (1930, "last_post_machining_period_descriptive"),
)
FREQUENCY_HZ = 14_000.0
WINDOW_M = (2.0, 3.2)


def _source_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(path: Path = ARCHIVE) -> dict:
    baseline = read_guided_wave_acquisition(path, BASELINE_ACQUISITION_ID, specimen_id=SPECIMEN_ID)
    registry = default_registry()
    evidence = Evidence(
        source_id="guided-wave-pipeline-shm",
        origin="open_dataset",
        citation="El Mountassir, M., Mendeley Data v1, doi:10.17632/ttb63krg6d.1",
        license_id="CC-BY-4.0",
        sha256=GUIDED_WAVE_ARCHIVE_SHA256,
    )
    records = []
    for acquisition_id, role in COMPARISONS:
        observation = read_guided_wave_acquisition(path, acquisition_id, specimen_id=SPECIMEN_ID)
        for wave_mode in ("torsional", "flexural"):
            inputs = guided_wave_pair_feature_inputs(
                baseline,
                observation,
                frequency_Hz=FREQUENCY_HZ,
                wave_mode=wave_mode,
                window_start_m=WINDOW_M[0],
                window_end_m=WINDOW_M[1],
                duplicate_distance_policy="mean_aligned_duplicates",
            )
            result = registry.run(
                "inspection.guided_wave_pair_features",
                inputs,
                RunContext(
                    asset_id=SPECIMEN_ID,
                    location_id="positive-distance-2.0-to-3.2-m-window",
                    time_basis="provider acquisition order; acquisition timestamps unavailable",
                    evidence=(evidence,),
                    metadata={
                        "baseline_article_period_group": baseline["article_period_group"],
                        "observation_article_period_group": observation["article_period_group"],
                        "comparison_role": role,
                    },
                ),
            )
            if result.status != "computed":
                raise ValueError(f"guided-wave descriptive comparison was not computed: {role}/{wave_mode}")
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
        "schema_version": "matintegrity.validation.guided_wave_pair_features.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "model_id": "inspection.guided_wave_pair_features",
        "model_source_sha256": _source_digest(ROOT / "src/matintegrity/models/inspection.py"),
        "adapter_source_sha256": _source_digest(ROOT / "src/matintegrity/adapters.py"),
        "dataset_id": "guided-wave-pipeline-shm",
        "dataset_doi": "10.17632/ttb63krg6d.1",
        "dataset_license": "CC-BY-4.0",
        "outer_archive_sha256": baseline["outer_archive_sha256"],
        "specimen_id": SPECIMEN_ID,
        "baseline_acquisition_id": BASELINE_ACQUISITION_ID,
        "frequency_Hz": FREQUENCY_HZ,
        "window_m": list(WINDOW_M),
        "duplicate_distance_policy": "mean_aligned_duplicates",
        "comparisons": records,
        "qualification": (
            "Descriptive same-specimen voltage comparisons for one predeclared frequency and positive-distance "
            "window. The later healthy-period record and two post-machining-period records are not independent "
            "specimens or a calibrated holdout set. Acquisition temperature, timestamp, coupling variation, the "
            "six machining-step mapping, remaining wall thickness and defect dimensions are unavailable. These "
            "features therefore do not validate localization, damage classification, POD, acceptance, remaining "
            "life or failure probability. No point waveform arrays are copied into this public validation record."
        ),
    }


if __name__ == "__main__":
    target = ROOT / "validation/guided_wave_pair_features.json"
    target.write_text(json.dumps(validate(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(target)
