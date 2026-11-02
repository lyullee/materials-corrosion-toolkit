"""Audit public pulse-echo method evidence without redistributing article content."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from pypdf import PdfReader

from matintegrity.ultrasound_data import read_ceit_uniform_corrosion_field

ROOT = Path(__file__).resolve().parents[1]
ARTICLE = ROOT / "data/evidence/ceit-uniform-corrosion-field/applsci-12-00808-v2.pdf"
DATASET = ROOT / "data/raw/ceit-uniform-corrosion-field/UniformCorrosionExperiment_Ceit.json"
OUTPUT = ROOT / "validation/ceit_pulse_echo_method.json"
EXPECTED_ARTICLE_SHA256 = "775d1d6789d8b8d2ecb0bb6195765d2c38e4f792298ddd38ee041172dbda8fd7"


def inspect() -> dict:
    article_digest = hashlib.sha256(ARTICLE.read_bytes()).hexdigest()
    if article_digest != EXPECTED_ARTICLE_SHA256:
        raise ValueError("CEIT pulse-echo article hash changed")
    reader = PdfReader(ARTICLE)
    pages = {
        number: reader.pages[number - 1].extract_text() or "" for number in (1, 7, 8, 9, 13, 14, 16, 17, 18)
    }
    required_tokens = {
        1: ("10.3390/app12020808", "Creative Commons"),
        7: ("V111", "1.69"),
        8: ("125 MHz", "cross-correlation"),
        9: ("14-bit ADC", "JSON"),
        13: ("S355J2G3", "5950 m/s", "Equation (1)"),
        14: ("bandpass", "standard deviation"),
        16: ("same sensor position", "positioning"),
        17: ("thickness", "exposed time"),
        18: ("below 1", "50 mV"),
    }
    missing = {
        page: [token for token in tokens if token not in pages[page]]
        for page, tokens in required_tokens.items()
        if any(token not in pages[page] for token in tokens)
    }
    if missing:
        raise ValueError(f"CEIT pulse-echo article evidence changed: {missing}")

    field = read_ceit_uniform_corrosion_field(
        DATASET,
        series_id="S355-00-02",
        reported_tof_unit="ns",
    )
    observed_tof_s = np.asarray([row["tof_s"] for row in field["observations"]], dtype=float)
    candidate_thickness_m = observed_tof_s * 5950.0 / 2
    return {
        "schema": "matintegrity.ceit_pulse_echo_method_evidence.v1",
        "article": {
            "doi": "10.3390/app12020808",
            "zenodo_record": "10.5281/zenodo.7400271",
            "license": "CC-BY-4.0",
            "file_bytes": ARTICLE.stat().st_size,
            "file_sha256": article_digest,
            "pages": len(reader.pages),
        },
        "documented_method_facts": {
            "path": "normal-incidence longitudinal pulse echo between consecutive back-wall echoes",
            "thickness_identity": "thickness_m = sound_speed_m_s * corrected_round_trip_time_s / 2",
            "probe_model": "V111",
            "reference_material": "S355J2G3",
            "article_calibrated_room_temperature_sound_speed_m_s": 5950.0,
            "speed_calibration_design": {
                "reference_zones": 8,
                "tof_repeats_per_zone": 5,
                "reference_dimension_method": "digital micrometer",
            },
            "reported_measurement_batch_size": 25,
            "reported_batch_precision_statistic": "standard deviation of ToF at one location",
            "signal_processing_sequence": [
                "band-pass filtering",
                "echo windowing",
                "cross-correlation of consecutive echoes",
                "peak analysis",
            ],
            "source_pages_checked": [1, 7, 8, 9, 13, 14, 16, 17, 18],
        },
        "field_series_compatibility_evidence": {
            "dataset_doi": "10.5281/zenodo.13897090",
            "sample_ids": field["identities"]["sample_id"],
            "probe_ids": field["identities"]["piezo_id"],
            "record_count": len(field["observations"]),
            "caller_reviewed_candidate_tof_unit": "ns",
            "raw_tof_range_s": [float(observed_tof_s.min()), float(observed_tof_s.max())],
            "candidate_zero_offset_assumption_s": 0.0,
            "candidate_5950_m_s_thickness_range_m": [
                float(candidate_thickness_m.min()),
                float(candidate_thickness_m.max()),
            ],
        },
        "automatic_calibration_qualified": False,
        "field_thickness_series_qualified": False,
        "corrosion_rate_qualified": False,
        "open_requirements": [
            "provider confirmation that JSON ToF is nanoseconds",
            "field-device calibration lineage and time-zero correction",
            "definition and validation of the compensated ToF field",
            "field-sample material state and temperature-specific sound speed",
            "stable physical measurement-location identity",
            "pointwise measurement uncertainty and independent dimensional ground truth",
        ],
        "qualification": (
            "The article establishes the general pulse-echo identity and one laboratory calibration. "
            "Matching provider, steel family, probe model and numerical scale are compatibility evidence, "
            "not proof that the later field JSON inherited the same calibration. Candidate converted ranges "
            "are diagnostics only and are not released as qualified thickness observations."
        ),
        "public_release_boundary": (
            "Only paraphrased method facts, hashes, page locators and aggregate diagnostics are released. "
            "The article PDF, raw JSON, figures, tables, prose and pointwise values remain excluded."
        ),
    }


if __name__ == "__main__":
    result = inspect()
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
