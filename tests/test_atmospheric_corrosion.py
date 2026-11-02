import csv
import io
import json
import math
import zipfile

import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity.atmospheric_data import read_atmospheric_corrosion_observations
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry
from matintegrity.units import SECONDS_PER_YEAR

CONTEXT = RunContext(asset_id="asset", location_id="surface", time_basis="exposure seconds")


def _write_csv(archive, name, fields, rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    archive.writestr(f"root/{name}", stream.getvalue())


def source_archive(tmp_path):
    common = {
        "site": "Site",
        "country": "Country",
        "lat": "10",
        "lon": "20",
        "r_um_per_yr": "12.5",
        "Cl_dep_mg_m2_d": "2.0",
        "SO2_dep_mg_m2_d": "3.0",
        "era5_cell": "cell",
        "T_era5_corrected_C": "20",
        "RH_era5_pct": "80",
        "lapse_correction_K": "1",
        "tw80_h": "3000",
        "Tw80_C": "18",
        "precipitation_mm": "900",
    }
    programme = common | {
        "source": "source-a",
        "programme": "programme-a",
        "exposure_period": "2020",
        "site_id": "site-a",
        "Cl_assumed_zero": "False",
    }
    independent = common | {
        "study": "study-b",
        "exposure_years": "2021",
        "tier": "A",
        "rate_source": "table",
        "doi": "10.example/test",
        "note": "authored fixture",
    }
    path = tmp_path / "source.zip"
    with zipfile.ZipFile(path, "w") as archive:
        _write_csv(archive, "programme_records_617.csv", list(programme), [programme])
        _write_csv(archive, "independent_records_106.csv", list(independent), [independent])
    return path


def test_loader_preserves_provider_partitions_units_and_provenance(tmp_path):
    records = read_atmospheric_corrosion_observations(source_archive(tmp_path), require_pinned_hash=False)
    assert len(records) == 2
    programme, independent = records
    assert programme.provider_partition == "programme"
    assert programme.source_group_id == "programme:source-a"
    assert programme.first_year_loss_m == pytest.approx(12.5e-6)
    assert programme.equivalent_first_year_rate_m_s == pytest.approx(12.5e-6 / SECONDS_PER_YEAR)
    assert programme.era5_corrected_temperature_K == pytest.approx(293.15)
    assert programme.era5_wet_hour_mean_temperature_K == pytest.approx(292.15)
    assert programme.era5_annual_precipitation_m == pytest.approx(0.9)
    assert programme.physical_specimen_id is None
    assert independent.provider_partition == "independent"
    assert independent.source_group_id == "independent-study:study-b"
    assert independent.provider_tier == "A"
    assert independent.programme_id is None
    assert programme.source_archive_sha256 == independent.source_archive_sha256


def test_loader_refuses_unreviewed_hash_and_unsafe_archive(tmp_path):
    path = source_archive(tmp_path)
    with pytest.raises(ValueError, match="hash differs"):
        read_atmospheric_corrosion_observations(path)
    unsafe = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(unsafe, "w") as archive:
        archive.writestr("../programme_records_617.csv", "x\n")
        archive.writestr("root/independent_records_106.csv", "x\n")
    with pytest.raises(ValueError, match="unsafe"):
        read_atmospheric_corrosion_observations(unsafe, require_pinned_hash=False)


def _features(temperature, humidity, chloride, sulfur):
    return np.asarray(
        [
            1.0,
            (temperature - 288.15) / 10.0,
            (humidity - 0.75) / 0.1,
            math.log1p(chloride),
            math.log1p(sulfur),
        ]
    )


def fit_inputs():
    beta = np.asarray([-11.0, 0.2, 0.3, 0.4, 0.1])
    conditions = [
        (280.0, 0.60, 0.0, 0.0),
        (285.0, 0.70, 1.0, 4.0),
        (290.0, 0.80, 3.0, 1.0),
        (295.0, 0.90, 8.0, 2.0),
        (300.0, 0.65, 2.0, 10.0),
        (305.0, 0.75, 5.0, 5.0),
        (282.0, 0.85, 12.0, 0.5),
        (298.0, 0.72, 0.5, 12.0),
        (288.0, 0.88, 15.0, 8.0),
        (302.0, 0.68, 7.0, 15.0),
        (292.0, 0.77, 4.0, 3.0),
        (296.0, 0.82, 9.0, 6.0),
        (286.0, 0.74, 6.0, 9.0),
        (301.0, 0.79, 10.0, 7.0),
    ]
    rows = []
    for index, (temperature, humidity, chloride, sulfur) in enumerate(conditions):
        partition = "calibration" if index < 10 else "holdout"
        group = f"cal-{index % 2}" if partition == "calibration" else f"hold-{index % 2}"
        rows.append(
            {
                "observation_id": f"row-{index}",
                "source_group_id": group,
                "partition": partition,
                "first_year_loss_m": float(
                    math.exp(_features(temperature, humidity, chloride, sulfur) @ beta)
                ),
                "temperature_K": temperature,
                "relative_humidity_fraction": humidity,
                "chloride_deposition_mg_m2_day": chloride,
                "sulfur_dioxide_deposition_mg_m2_day": sulfur,
                "source_content_sha256": "a" * 64,
            }
        )
    return {
        "fit_id": "fit-1",
        "model_id": "atmospheric-demo",
        "observations": rows,
        "minimum_calibration_source_groups": 2,
        "minimum_holdout_source_groups": 2,
        "maximum_holdout_log_rmse": 0.01,
        "maximum_absolute_holdout_log_bias": 0.01,
        "maximum_holdout_outside_support_fraction": 0.0,
        "source_group_partition_reviewed": True,
        "first_year_endpoint_reviewed": True,
        "atmospheric_carbon_steel_scope_reviewed": True,
        "covariate_origin_reviewed": True,
        "aggregate_analysis_authorized": True,
        "pointwise_redistribution_authorized": False,
    }


def test_loglinear_fit_recovers_authored_coefficients_and_holdout():
    result = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    model = result.values["model"]
    assert model["coefficient_log_m"] == pytest.approx(-11.0)
    assert model["coefficient_temperature_per_10_K"] == pytest.approx(0.2)
    assert model["coefficient_relative_humidity_per_0_1"] == pytest.approx(0.3)
    assert model["coefficient_log1p_chloride"] == pytest.approx(0.4)
    assert model["coefficient_log1p_sulfur_dioxide"] == pytest.approx(0.1)
    assert result.values["calibration_metrics"]["log_rmse"] < 1e-12
    assert result.values["holdout_metrics"]["log_rmse"] < 1e-12
    assert result.values["pointwise_redistribution_authorized"] is False
    assert result.values["transfer_criteria_met"] is True
    assert model["transfer_criteria_met"] is True
    assert len(model["holdout_input_digest"]) == 64
    assert model["holdout_input_digest"] != model["calibration_input_digest"]
    assert result.values["holdout_input_digest"] == model["holdout_input_digest"]
    assert result.values["source_group_transfer_criteria_met"] is True
    assert {item["source_group_id"] for item in result.values["holdout_source_group_metrics"]} == {
        "hold-0",
        "hold-1",
    }
    assert sum(item["observation_count"] for item in result.values["holdout_source_group_metrics"]) == 4


def test_large_holdout_group_cannot_mask_one_poor_source_group():
    payload = fit_inputs()
    observations = payload["observations"]
    holdout_template = observations[-2].copy()
    holdout_group_rows = []
    for index in range(99):
        row = holdout_template.copy()
        row["observation_id"] = f"large-holdout-{index}"
        row["source_group_id"] = "large-group"
        holdout_group_rows.append(row)
    outlier = observations[-1].copy()
    outlier["source_group_id"] = "small-poor-group"
    outlier["first_year_loss_m"] *= math.exp(0.2)
    payload["observations"] = observations[:-4] + holdout_group_rows + [outlier]
    payload["maximum_holdout_log_rmse"] = 0.1
    payload["maximum_absolute_holdout_log_bias"] = 0.1

    result = default_registry().run("corrosion.atmospheric_first_year_fit", payload, CONTEXT)

    assert result.values["holdout_metrics"]["log_rmse"] < 0.1
    assert result.values["source_group_transfer_criteria_met"] is False
    assert result.values["maximum_holdout_source_group_log_rmse"] == pytest.approx(0.2)
    assert result.values["transfer_criteria_met"] is False


def test_holdout_digest_changes_without_changing_calibration_digest():
    payload = fit_inputs()
    baseline = default_registry().run("corrosion.atmospheric_first_year_fit", payload, CONTEXT)
    changed_payload = fit_inputs()
    changed_payload["observations"][-1]["first_year_loss_m"] *= math.exp(0.05)
    changed = default_registry().run("corrosion.atmospheric_first_year_fit", changed_payload, CONTEXT)

    assert (
        changed.values["model"]["calibration_input_digest"]
        == baseline.values["model"]["calibration_input_digest"]
    )
    assert changed.values["holdout_input_digest"] != baseline.values["holdout_input_digest"]


def prediction_inputs(model):
    return {
        "prediction_id": "prediction-1",
        "asset_id": "asset",
        "location_id": "surface",
        "physical_scope_id": "external-wall",
        "material_condition_id": "carbon-steel-demo",
        "exposure_environment_id": "atmosphere-demo",
        "time_basis": "exposure seconds",
        "exposure_start_s": 0.0,
        "exposure_duration_s": SECONDS_PER_YEAR,
        "model": model,
        "temperature_K": 292.0,
        "relative_humidity_fraction": 0.77,
        "chloride_deposition_mg_m2_day": 4.0,
        "sulfur_dioxide_deposition_mg_m2_day": 3.0,
        "confidence_level": 0.95,
        "first_year_atmospheric_carbon_steel_scope_reviewed": True,
        "covariates_reviewed": True,
        "model_applicability_reviewed": True,
        "extrapolation_reviewed": False,
    }


def test_fitted_model_is_directly_reusable_for_prediction():
    fit = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    payload = prediction_inputs(fit.values["model"])
    result = default_registry().run("corrosion.atmospheric_first_year_prediction", payload, CONTEXT)
    expected = math.exp(_features(292.0, 0.77, 4.0, 3.0) @ np.asarray([-11, 0.2, 0.3, 0.4, 0.1]))
    assert result.values["predicted_first_year_loss_m"] == pytest.approx(expected)
    assert result.values["equivalent_first_year_rate_m_s"] == pytest.approx(expected / SECONDS_PER_YEAR)
    assert result.values["extrapolation_used"] is False


def test_prediction_rejects_non_positive_semidefinite_coefficient_covariance():
    fit = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    payload = prediction_inputs(fit.values["model"])
    payload["model"]["coefficient_covariance"] = np.diag([1.0, 1.0, -0.01, 1.0, 1.0]).tolist()
    with pytest.raises(ValidationError, match="positive semidefinite"):
        default_registry().run("corrosion.atmospheric_first_year_prediction", payload, CONTEXT)


def test_prediction_accepts_singular_positive_semidefinite_coefficient_covariance():
    fit = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    payload = prediction_inputs(fit.values["model"])
    payload["model"]["coefficient_covariance"] = np.zeros((5, 5)).tolist()
    result = default_registry().run("corrosion.atmospheric_first_year_prediction", payload, CONTEXT)
    assert result.status == "computed"
    assert result.values["conditional_mean_standard_error_log_m"] == pytest.approx(0.0)


def test_prediction_stops_outside_support_without_review():
    fit = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    payload = prediction_inputs(fit.values["model"])
    payload["temperature_K"] = 400.0
    result = default_registry().run("corrosion.atmospheric_first_year_prediction", payload, CONTEXT)
    assert result.status == "out_of_scope"
    assert result.values["outside_support_fields"] == ["temperature_K"]
    payload["extrapolation_reviewed"] = True
    result = default_registry().run("corrosion.atmospheric_first_year_prediction", payload, CONTEXT)
    assert result.status == "computed"
    assert result.values["extrapolation_used"] is True


def test_prediction_stops_when_source_separated_transfer_criteria_fail():
    fit = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    model = dict(fit.values["model"])
    model["transfer_criteria_met"] = False
    model["holdout_log_rmse"] = 1.2
    payload = prediction_inputs(model)
    result = default_registry().run("corrosion.atmospheric_first_year_prediction", payload, CONTEXT)
    assert result.status == "needs_data"
    assert result.values["transfer_criteria_met"] is False
    payload["limited_transfer_override_reviewed"] = True
    result = default_registry().run("corrosion.atmospheric_first_year_prediction", payload, CONTEXT)
    assert result.status == "computed"


def test_legacy_model_without_source_group_diagnostics_does_not_pass_gate():
    fit = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    model = dict(fit.values["model"])
    model.pop("holdout_source_group_metrics")
    model.pop("maximum_holdout_source_group_log_rmse")
    model.pop("maximum_holdout_source_group_absolute_log_bias")
    model.pop("source_group_transfer_criteria_met")
    result = default_registry().run(
        "corrosion.atmospheric_first_year_prediction",
        prediction_inputs(model),
        CONTEXT,
    )
    assert result.status == "needs_data"


def test_model_rejects_group_diagnostics_that_reuse_calibration_source():
    fit = default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT)
    model = dict(fit.values["model"])
    model["holdout_source_group_metrics"][0]["source_group_id"] = "cal-0"
    with pytest.raises(ValidationError, match="cannot overlap"):
        default_registry().run(
            "corrosion.atmospheric_first_year_prediction",
            prediction_inputs(model),
            CONTEXT,
        )


def test_fit_refuses_source_group_leakage_and_unreviewed_evidence():
    payload = fit_inputs()
    payload["observations"][-1]["source_group_id"] = "cal-0"
    with pytest.raises(ValidationError, match="cannot cross"):
        default_registry().run("corrosion.atmospheric_first_year_fit", payload, CONTEXT)
    payload = fit_inputs()
    payload["aggregate_analysis_authorized"] = False
    result = default_registry().run("corrosion.atmospheric_first_year_fit", payload, CONTEXT)
    assert result.status == "needs_data"


def test_prediction_preserves_context_and_one_year_scope():
    model = (
        default_registry().run("corrosion.atmospheric_first_year_fit", fit_inputs(), CONTEXT).values["model"]
    )
    payload = prediction_inputs(model)
    payload["exposure_duration_s"] = 2 * SECONDS_PER_YEAR
    with pytest.raises(ValidationError, match="one declared first-year"):
        default_registry().run(
            "corrosion.atmospheric_first_year_prediction", json.loads(json.dumps(payload)), CONTEXT
        )
    payload = prediction_inputs(model)
    with pytest.raises(ValueError, match="must match"):
        default_registry().run(
            "corrosion.atmospheric_first_year_prediction",
            payload,
            CONTEXT.model_copy(update={"asset_id": "other"}),
        )
