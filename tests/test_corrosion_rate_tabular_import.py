import csv
import json
from pathlib import Path

from examples.import_corrosion_rate_samples import (
    import_corrosion_rate_observations_csv,
    import_corrosion_rate_samples,
)

ROOT = Path(__file__).resolve().parents[1]


def _sample_record():
    row = {
        "observation_id": "coupon-1-rate",
        "physical_specimen_id": "coupon-1",
        "material_id": "alloy-A",
        "rate_m_s": 1e-9,
        "condition_signature": {"temperature_K": 298.15},
        "condition_group_id": "condition-1",
        "source_group_id": "study-1",
        "measurement_method": "gravimetric",
        "rate_standard_uncertainty_m_s": 1e-10,
        "rate_uncertainty_basis": "synthetic covariance example",
        "evidence": [
            {
                "source_id": "study-1",
                "origin": "synthetic",
                "citation": "project-authored synthetic fixture",
            }
        ],
    }
    return {
        "observations": [row],
        "quantile_probabilities": [0.5],
        "measurement_error_covariance_m_s2": [[1e-20]],
    }


def test_jsonl_import_builds_reviewable_nested_sample_contract(tmp_path):
    source = tmp_path / "coupon-samples.jsonl"
    source.write_text(json.dumps(_sample_record()) + "\n", encoding="utf-8")
    records, report = import_corrosion_rate_samples(source)
    assert report.imported_rows == 1
    assert report.rejected_rows == 0
    assert records[0].observations[0].physical_specimen_id == "coupon-1"
    assert records[0].measurement_error_covariance_m_s2 == [[1e-20]]
    assert report.source_sha256
    assert report.imported_records_digest


def test_bundled_synthetic_sample_uses_public_jsonl_import_profile():
    fixture = ROOT / "examples/corrosion_rate_samples.synthetic.jsonl"
    records, report = import_corrosion_rate_samples(fixture)
    assert report.imported_rows == 1
    assert len(records[0].observations) == 2
    assert records[0].measurement_error_covariance_m_s2[1][1] == 2.25e-20


def test_csv_observation_profile_imports_one_specimen_per_row_without_inference(tmp_path):
    source = tmp_path / "rates.csv"
    headers = [
        "observation_id",
        "physical_specimen_id",
        "material_id",
        "rate_m_s",
        "condition_signature_json",
        "condition_group_id",
        "source_group_id",
        "measurement_method",
        "rate_standard_uncertainty_m_s",
        "rate_uncertainty_basis",
        "evidence_json",
    ]
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers)
        writer.writeheader()
        writer.writerow(
            {
                "observation_id": "obs-1",
                "physical_specimen_id": "coupon-1",
                "material_id": "alloy-A",
                "rate_m_s": "1e-9",
                "condition_signature_json": json.dumps({"temperature_K": 298.15}),
                "condition_group_id": "condition-1",
                "source_group_id": "study-1",
                "measurement_method": "gravimetric",
                "rate_standard_uncertainty_m_s": "1e-10",
                "rate_uncertainty_basis": "synthetic",
                "evidence_json": json.dumps(
                    [{"source_id": "study-1", "origin": "synthetic", "citation": "synthetic"}]
                ),
            }
        )
    records, report = import_corrosion_rate_observations_csv(source)
    assert report.imported_rows == 1
    assert records[0].rate_m_s == 1e-9
    assert records[0].rate_standard_uncertainty_m_s == 1e-10
    assert records[0].evidence[0].source_id == "study-1"


def test_jsonl_import_rejects_unknown_columns_and_inconsistent_uncertainty(tmp_path):
    source = tmp_path / "coupon-samples.jsonl"
    source.write_text(json.dumps(_sample_record() | {"unreviewed": 3}) + "\n", encoding="utf-8")
    records, report = import_corrosion_rate_samples(source)
    assert records == ()
    assert "source.unreviewed" in report.findings[0].issue_paths

    record = _sample_record()
    record["measurement_error_covariance_m_s2"] = [[4e-20]]
    source.write_text(json.dumps(record) + "\n", encoding="utf-8")
    records, report = import_corrosion_rate_samples(source)
    assert records == ()
    assert report.findings[0].status == "rejected"
