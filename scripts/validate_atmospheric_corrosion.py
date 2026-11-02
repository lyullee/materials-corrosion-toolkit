"""Validate the atmospheric first-year model and record source-separated transfer limits."""

import json
import math
from pathlib import Path

import numpy as np

from matintegrity.atmospheric_data import read_atmospheric_corrosion_observations
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "data/raw/atmospheric-carbon-steel-first-year/ysr7wy3y7z-1.zip"
OUTPUT = ROOT / "validation/atmospheric_corrosion_first_year.json"


def feature(row):
    return [
        1.0,
        (row["temperature_K"] - 288.15) / 10.0,
        (row["relative_humidity_fraction"] - 0.75) / 0.1,
        math.log1p(row["chloride_deposition_mg_m2_day"]),
        math.log1p(row["sulfur_dioxide_deposition_mg_m2_day"]),
    ]


def main():
    records = read_atmospheric_corrosion_observations(ARCHIVE)
    programme = [row for row in records if row.provider_partition == "programme"]
    independent_ab = [
        row
        for row in records
        if row.provider_partition == "independent"
        and row.provider_tier in {"A", "B"}
        and row.chloride_deposition_mg_m2_day is not None
        and row.sulfur_dioxide_deposition_mg_m2_day is not None
    ]
    excluded_independent = [
        row for row in records if row.provider_partition == "independent" and row not in independent_ab
    ]
    fit_rows = []
    for partition, selected in (("calibration", programme), ("holdout", independent_ab)):
        for row in selected:
            fit_rows.append(
                {
                    "observation_id": row.observation_id,
                    "source_group_id": row.source_group_id,
                    "partition": partition,
                    "first_year_loss_m": row.first_year_loss_m,
                    "temperature_K": row.era5_corrected_temperature_K,
                    "relative_humidity_fraction": row.era5_relative_humidity_fraction,
                    "chloride_deposition_mg_m2_day": row.chloride_deposition_mg_m2_day,
                    "sulfur_dioxide_deposition_mg_m2_day": row.sulfur_dioxide_deposition_mg_m2_day,
                    "source_content_sha256": row.source_archive_sha256,
                }
            )
    thresholds = {
        "maximum_holdout_log_rmse": math.log(2.0),
        "maximum_absolute_holdout_log_bias": math.log(1.5),
        "maximum_holdout_outside_support_fraction": 0.1,
    }
    payload = {
        "fit_id": "mendeley-ysr7wy3y7z-v1-programme-to-independent-ab",
        "model_id": "atmospheric-carbon-steel-first-year-loglinear-v1",
        "observations": fit_rows,
        "minimum_calibration_source_groups": 2,
        "minimum_holdout_source_groups": 2,
        **thresholds,
        "source_group_partition_reviewed": True,
        "first_year_endpoint_reviewed": True,
        "atmospheric_carbon_steel_scope_reviewed": True,
        "covariate_origin_reviewed": True,
        "aggregate_analysis_authorized": True,
        "pointwise_redistribution_authorized": False,
    }
    result = default_registry().run(
        "corrosion.atmospheric_first_year_fit",
        payload,
        RunContext(asset_id="dataset", location_id="multiple-sites", time_basis="first year"),
    )
    design = np.asarray([feature(row) for row in fit_rows if row["partition"] == "calibration"])
    response = np.log(
        np.asarray([row["first_year_loss_m"] for row in fit_rows if row["partition"] == "calibration"])
    )
    direct = np.linalg.lstsq(design, response, rcond=None)[0]
    model = result.values["model"]
    implementation = np.asarray(
        [
            model["coefficient_log_m"],
            model["coefficient_temperature_per_10_K"],
            model["coefficient_relative_humidity_per_0_1"],
            model["coefficient_log1p_chloride"],
            model["coefficient_log1p_sulfur_dioxide"],
        ]
    )
    software_math_passed = bool(np.allclose(direct, implementation, rtol=1e-12, atol=1e-12))
    report = {
        "schema": "matintegrity.atmospheric_corrosion_validation.v1",
        "dataset_id": "atmospheric-carbon-steel-first-year",
        "archive_sha256": programme[0].source_archive_sha256,
        "partition": {
            "calibration_programme_records": len(programme),
            "holdout_independent_tier_a_b_records": len(independent_ab),
            "excluded_independent_records": len(excluded_independent),
            "exclusion_reason": "Provider tier C and/or missing deposition covariates were excluded before fitting.",
            "physical_specimen_independence_claimed": False,
        },
        "predeclared_transfer_thresholds": thresholds,
        "calibration_metrics": result.values["calibration_metrics"],
        "holdout_metrics": result.values["holdout_metrics"],
        "holdout_source_group_metrics": result.values["holdout_source_group_metrics"],
        "maximum_holdout_source_group_log_rmse": result.values["maximum_holdout_source_group_log_rmse"],
        "maximum_holdout_source_group_absolute_log_bias": result.values[
            "maximum_holdout_source_group_absolute_log_bias"
        ],
        "source_group_transfer_criteria_met": result.values["source_group_transfer_criteria_met"],
        "holdout_input_digest": result.values["holdout_input_digest"],
        "calibration_input_digest": model["calibration_input_digest"],
        "holdout_outside_calibration_support_count": result.values[
            "holdout_outside_calibration_support_count"
        ],
        "holdout_outside_calibration_support_fraction": model["holdout_outside_support_fraction"],
        "coefficients": implementation.tolist(),
        "direct_numpy_coefficient_max_absolute_difference": float(np.max(np.abs(direct - implementation))),
        "software_math_validation_passed": software_math_passed,
        "transfer_criteria_met": result.values["transfer_criteria_met"],
        "operational_prediction_qualified": False,
        "conclusion": (
            "The implementation reproduces the independently evaluated least-squares calculation, "
            "but source-separated transfer does not meet the predeclared criteria."
        ),
        "limitations": [
            "First-year average atmospheric carbon-steel thickness loss only.",
            "Not wet CO2, internal corrosion, localized penetration, multi-year growth, remaining life or failure probability.",
            "ERA5/Open-Meteo fields are harmonised model covariates rather than simultaneous specimen measurements.",
            "Dataset-level CC BY 4.0 does not by itself resolve every underlying observation's redistribution rights.",
        ],
    }
    if not software_math_passed:
        raise SystemExit("independent coefficient comparison failed")
    if report["transfer_criteria_met"]:
        raise SystemExit("expected the predeclared source-separated transfer gate to remain unmet")
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
