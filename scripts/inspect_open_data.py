"""Produce reproducible inventory and limited calibration evidence from acquired data."""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from inspect_aquasoldb_data import audit as inspect_aquasoldb_co2
from inspect_burst_data import inspect as inspect_burst
from inspect_ceit_pulse_echo_method import inspect as inspect_ceit_pulse_echo_method
from inspect_ceit_uniform_corrosion_field import inspect as inspect_ceit_uniform_corrosion_field
from inspect_corrosion_alloy_metrics import inspect_corrosion_alloy_metrics
from inspect_creep_data import inspect as inspect_creep
from inspect_ecp_multiaxial_data import inspect as inspect_ecp_multiaxial
from inspect_fabest_data import inspect_fabest_data
from inspect_fabest_hcf_data import inspect_fabest_hcf_package
from inspect_fabest_lcf_data import inspect_fabest_lcf_package
from inspect_fracture_data import inspect_fracture_data
from inspect_fracture_toughness_data import inspect_fracture_toughness_data
from inspect_guided_wave_data import inspect as inspect_guided_wave
from inspect_hydrogen_data import inspect as inspect_hydrogen
from inspect_polarization_data import inspect as inspect_polarization
from inspect_thermal_data import inspect as inspect_thermal
from inspect_wet_co2_data import inspect as inspect_wet_co2
from inspect_willow_data import inspect as inspect_willow

from matintegrity import evaluate
from matintegrity.atmospheric_data import read_atmospheric_corrosion_observations
from matintegrity.calibration import fit_censored_sn
from matintegrity.contracts import Evidence, RunContext
from matintegrity.data import (
    process_chunks,
    read_bam_creep_fatigue,
    read_corr_data,
    read_weld_fatigue,
)
from matintegrity.fatigue_data import read_fabest, summarize_recorded_bam_cycles
from matintegrity.hydrogen_fatigue_data import audit_hymatbase_hydrogen_fatigue
from matintegrity.impact_data import read_charpy_compilation
from matintegrity.signals import (
    coqtel_electrochemistry,
    coqtel_waveform,
    inspect_coqtel_experiment,
    waveform_change,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"


def main():
    summary = {"schema": "matintegrity.data_inventory.v1", "checked_on": "2026-10-27", "datasets": {}}
    rows = read_corr_data(RAW / "nist-corr/CORR-DATA_Database.zip")
    summary["datasets"]["nist-corr"] = {
        "rows": len(rows),
        "reported_value_kinds": dict(Counter(r["reported_rate_mm_year"]["kind"] for r in rows)),
        "rights_status": "redistribution_review_required",
        "use": "Material/environment lookup with preserved qualifiers; no fleet failure inference.",
    }
    coqtel = []
    for path in sorted((RAW / "coqtel").glob("*.h5")):
        inventory = inspect_coqtel_experiment(path)
        ec = coqtel_electrochemistry(path, duplicate_policy="preserve_identical", require_pinned_hash=True)
        baseline = coqtel_waveform(path, state=1, actuator=1, sensor=4, require_pinned_hash=True)
        final = coqtel_waveform(path, state=len(ec["time_s"]), actuator=1, sensor=4, require_pinned_hash=True)
        inventory["final_waveform_change"] = waveform_change(baseline, final)
        coqtel.append(inventory)
    summary["datasets"]["coqtel"] = {
        "independent_experiments": len(coqtel),
        "experiments": coqtel,
        "use": (
            "Two-specimen signal ingestion and electrochemical integration with repeated-state and "
            "reported anomaly boundaries; no state-resolved pit-depth validation."
        ),
    }
    fatigue = read_weld_fatigue(RAW / "hannover-weld/fatigue_test_data.txt")
    selected = fatigue[
        fatigue.row_valid
        & ~fatigue.repeated_specimen
        & (fatigue.Outlier == 0)
        & (fatigue.material == "S355")
        & (fatigue.treatment == "AW")
        & (fatigue.StressRatio == 0.1)
    ].copy()
    selected["partition"] = selected.SpecimenName.map(
        lambda value: int(hashlib.sha256(value.encode()).hexdigest()[:8], 16) % 5
    )
    train = selected[selected.partition != 0]
    heldout = selected[selected.partition == 0]
    fit = fit_censored_sn(train.stress_range_Pa, train.LoadCyclesToFailure, train.runout.astype(bool))
    failures = heldout[heldout.RunOut == 0]
    prediction = (
        fit["median_reference_cycles"]
        * (fit["reference_range_Pa"] / failures.stress_range_Pa) ** fit["exponent"]
    )
    error = np.log(failures.LoadCyclesToFailure / prediction)
    summary["datasets"]["hannover-weld"] = {
        "raw_rows": len(fatigue),
        "repeated_specimen_rows": int(fatigue.repeated_specimen.sum()),
        "valid_rows": int(fatigue.row_valid.sum()),
        "pilot_condition": "S355, as-welded, R=0.1, unique single-stage non-outlier specimens",
        "training_rows": len(train),
        "heldout_rows": len(heldout),
        "heldout_failures": len(failures),
        "censored_sn_fit": fit,
        "heldout_failure_log_rmse": float(np.sqrt(np.mean(error**2))),
        "qualification": "Small within-dataset specimen holdout; no external apparatus or material-domain validation.",
    }
    workbook = RAW / "hydrogen-316l/Tensile tests.xlsx"
    tensile = pd.read_excel(workbook, sheet_name="vysledky", header=None)
    if str(tensile.iat[0, 6]).strip() != "Rm" or str(tensile.iat[1, 6]).strip() != "[MPa]":
        raise ValueError("hydrogen tensile workbook schema changed")
    specimen_rows = [2, 3, 4, 10, 11, 12]
    summary["datasets"]["hydrogen-316l"] = {
        "tensile_specimens": len(specimen_rows),
        "uts_range_Pa": [
            float(tensile.iloc[specimen_rows, 6].min() * 1e6),
            float(tensile.iloc[specimen_rows, 6].max() * 1e6),
        ],
        "elongation_fraction_range": [
            float(tensile.iloc[specimen_rows, 8].min() / 100),
            float(tensile.iloc[specimen_rows, 8].max() / 100),
        ],
        "hardness_sheets": len(pd.ExcelFile(RAW / "hydrogen-316l/Hardness.xlsx").sheet_names),
        "qualification": "Electrolytically charged additively manufactured 316L; six tensile specimens do not qualify a service failure model.",
    }
    count = 0
    intervals = Counter()
    minimum = None
    maximum = None
    last = None
    for frame in process_chunks(RAW / "metropt3/metropt+3+dataset.zip"):
        times = pd.to_datetime(frame.timestamp, errors="raise")
        differences = times.diff().dt.total_seconds().dropna()
        intervals.update(float(value) for value in differences)
        if last is not None:
            intervals.update([float((times.iloc[0] - last).total_seconds())])
        minimum = times.iloc[0] if minimum is None else min(minimum, times.iloc[0])
        maximum = times.iloc[-1] if maximum is None else max(maximum, times.iloc[-1])
        last = times.iloc[-1]
        count += len(frame)
    summary["datasets"]["metropt3"] = {
        "rows": count,
        "first_timestamp_as_published": str(minimum),
        "last_timestamp_as_published": str(maximum),
        "most_common_time_steps_s": intervals.most_common(5),
        "nonpositive_time_steps": sum(v for k, v in intervals.items() if k <= 0),
        "pressure_basis": "unresolved; do not silently treat published bar readings as absolute pressure",
        "qualification": "Process-history and ingestion evidence only; no corrosion labels or fleet exposure denominator.",
    }
    with zipfile.ZipFile(RAW / "steel-plates/steel+plates+faults.zip") as archive:
        lines = archive.read("Faults.NNA").decode().splitlines()
    summary["datasets"]["steel-plates"] = {
        "rows": sum(bool(line.strip()) for line in lines),
        "qualification": "Manufacturing surface-fault classification, not measured corrosion growth.",
    }
    summary["datasets"]["coating-pem"] = {
        "acquired_archives": 2,
        "machine_readable_tables_ready": False,
        "format_findings": "Initial assets contain Origin project and illustration/presentation files; no numerical calibration claimed.",
    }
    bam = []
    for path in sorted((RAW / "bam-p92").glob("*.lis")):
        loaded = read_bam_creep_fatigue(path)
        frame = loaded["waveform"]
        paths = summarize_recorded_bam_cycles(loaded)
        extrema = loaded["cycle_extrema"]
        peak_difference = (
            frame.groupby("cycle").stress_Pa.max() - extrema.set_index("cycle").maximum_stress_Pa
        )
        bam.append(
            dict(
                file=path.name,
                waveform_rows=len(frame),
                recorded_cycles=int(frame.cycle.nunique()),
                zero_duration_intervals=loaded["zero_duration_intervals"],
                test_design=loaded["metadata"]["Test Design"],
                reported_failure_cycles=float(loaded["metadata"]["Cycles to Failure, Nf"]),
                min_temperature_K=float(frame.temperature_K.min()),
                max_temperature_K=float(frame.temperature_K.max()),
                cycle_extrema_rows=len(extrema),
                maximum_peak_stress_difference_Pa=float(peak_difference.abs().max()),
                unrecorded_cycles_in_recorded_span=int(
                    frame.cycle.max() - frame.cycle.min() + 1 - len(paths)
                ),
                maximum_endpoint_strain_mismatch=float(paths.endpoint_strain_difference.abs().max()),
            )
        )
    summary["datasets"]["bam-p92"] = {
        "independent_tests": len(bam),
        "tests": bam,
        "qualification": "First-party service-like P92 tests; loading/control modes remain separate and no creep-fatigue interaction is calibrated.",
    }
    fabest = RAW / "fabest/FAB_v20260730.xlsm"
    fabest_data = read_fabest(fabest)
    observations = fabest_data["observations"]
    selected = observations[
        (observations.group_id == "FAB005")
        & observations.row_valid
        & observations.calibration_role.isin(
            ["candidate_failure_observation", "candidate_censored_observation"]
        )
    ]
    pilot_fit = fit_censored_sn(
        [c[0]["stress_range_Pa"] for c in selected.channels],
        selected.cycles_to_end,
        selected.provider_interrupted.astype(bool),
        reference_range_Pa=1e9,
    )
    summary["datasets"]["fabest"] = {
        **inspect_fabest_data(fabest),
        "numerical_specimen_table_mapping_complete": True,
        "specimen_protocol_review_complete": False,
        "pilot_group": "FAB005; reported numeric hollow-specimen axial observations, no letter suffix or endpoint comment",
        "pilot_censoring_assumption": (
            "Within the screened FAB005 subset only, provider interruption is treated as right "
            "censoring for a descriptive fit; this is not a dataset-wide endpoint interpretation."
        ),
        "pilot_censored_sn_fit": pilot_fit,
        "qualification": "Observation sections are separated from static references and regression output. Curve-level END criteria are absent, letter suffix meanings and comment temperatures remain unresolved, and provider interruption is not automatically a runout. The small single-power-law pilot uses an explicit local censoring assumption, has steep slope and high scatter, and is not a qualified material curve.",
    }
    summary["datasets"]["fabest-hcf-competition"] = inspect_fabest_hcf_package()
    summary["datasets"]["fabest-lcf-v2"] = inspect_fabest_lcf_package()
    summary["datasets"]["ecp-multiaxial-fatigue"] = inspect_ecp_multiaxial()
    summary["datasets"]["guided-wave-pipeline-shm"] = inspect_guided_wave()
    summary["datasets"]["galvanized-polarization"] = inspect_polarization()
    summary["datasets"]["corrosion-resistant-alloy-metrics"] = inspect_corrosion_alloy_metrics()
    summary["datasets"]["thermal-rod-transient"] = inspect_thermal()
    impact_path = RAW / "charpy-impact/Charpy_Impact_Test_Dataset.xlsx"
    impact = read_charpy_compilation(impact_path)
    selected = impact[
        (impact.reported_curve_id == 1)
        & impact.row_valid
        & (impact.orientation == "L")
        & (impact.irradiation_label == "No")
    ]
    if selected.condition_group_digest.nunique() != 1:
        raise ValueError("pilot impact selection no longer identifies one condition group")
    context = RunContext(
        asset_id="research-source",
        location_id="charpy-series-1",
        time_basis="reported test temperatures",
        evidence=(
            Evidence(
                source_id="charpy-impact",
                origin="open_dataset",
                citation="https://doi.org/10.24435/materialscloud:p6-5y; original reference 1, https://doi.org/10.2172/6609271",
                license_id="MIT",
                sha256=hashlib.sha256(impact_path.read_bytes()).hexdigest(),
            ),
        ),
    )
    fitted = evaluate(
        "materials.impact_transition",
        dict(
            series_id="source curve 1, unirradiated L",
            specimen_geometry_id="source pre-cracked 55x10x10 mm",
            material_condition_id=selected.condition_group_digest.iloc[0],
            orientation_id="L",
            observational_unit_description="Literature observations; physical specimen independence not established",
            observation_ids=[f"source-row-{i}" for i in selected.source_row],
            temperature_K=selected.temperature_K.tolist(),
            absorbed_energy_J=selected.absorbed_energy_J.tolist(),
            target_energy_J=50.0,
            minimum_relative_shelf_coverage=0.9,
            loss="soft_l1",
            residual_scale_J=5.0,
        ),
        context,
    )
    summary["datasets"]["charpy-impact"] = dict(
        rows=len(impact),
        columns_as_published=56,
        valid_numeric_geometry_rows=int(impact.row_valid.sum()),
        source_references=int(impact.original_reference_id.nunique()),
        reported_curve_ids=int(impact.reported_curve_id.nunique()),
        condition_groups=int(impact.condition_group_digest.nunique()),
        identical_reported_rows=int(impact.identical_reported_record.sum()),
        invalid_or_missing_temperature_rows=int(
            (impact.temperature_K.isna() | impact.temperature_K.le(0)).sum()
        ),
        incomplete_geometry_rows=int(impact[["length_m", "width_m", "thickness_m"]].isna().any(axis=1).sum()),
        reported_curve_ids_mixing_irradiation=int(
            (impact.groupby("reported_curve_id").irradiation_label.nunique(dropna=False) > 1).sum()
        ),
        pilot_rows=len(selected),
        pilot_input_digest=fitted.input_digest,
        pilot_status=fitted.status,
        pilot_aggregate_fit={
            key: value for key, value in fitted.values.items() if key not in {"fitted_energy_J", "residual_J"}
        },
        qualification="Descriptive source-series fit, not independent specimen validation. Preserve geometry, irradiation and original-reference distinctions. Do not infer fracture toughness, allowable service temperature or a generic specimen-size correction. Raw and pointwise derived observations are not redistributed.",
    )
    summary["datasets"].update(inspect_willow(RAW))
    ceit_field = inspect_ceit_uniform_corrosion_field()
    ceit_field["pulse_echo_method_evidence"] = inspect_ceit_pulse_echo_method()
    summary["datasets"]["ceit-uniform-corrosion-field"] = ceit_field
    summary["datasets"]["compiled-pipe-burst"] = inspect_burst(RAW)
    summary["datasets"]["cmsx6-creep"] = inspect_creep(RAW)
    summary["datasets"]["crack-arrest-c1-c2"] = inspect_fracture_data(
        RAW / "crack-arrest-c1-c2/g69875w65c-1.zip"
    )
    summary["datasets"]["fracture-toughness-temperature"] = inspect_fracture_toughness_data(
        RAW / "fracture-toughness-temperature/2vkgrbsy8j-1.zip"
    )
    atmospheric = read_atmospheric_corrosion_observations(
        RAW / "atmospheric-carbon-steel-first-year/ysr7wy3y7z-1.zip"
    )
    atmospheric_programme = [row for row in atmospheric if row.provider_partition == "programme"]
    atmospheric_independent = [row for row in atmospheric if row.provider_partition == "independent"]
    summary["datasets"]["atmospheric-carbon-steel-first-year"] = {
        "programme_records": len(atmospheric_programme),
        "independent_records": len(atmospheric_independent),
        "independent_tiers": dict(Counter(row.provider_tier for row in atmospheric_independent)),
        "programme_source_groups": len({row.source_group_id for row in atmospheric_programme}),
        "independent_source_groups": len({row.source_group_id for row in atmospheric_independent}),
        "physical_specimen_ids_available": False,
        "rights_status": "declared_compilation_license_review; source-specific observation review required",
        "use": "First-year average atmospheric carbon-steel loss screening and source-separated transfer diagnostics only.",
    }
    summary["datasets"]["heterogeneous-wet-co2-corrosion"] = inspect_wet_co2(
        RAW / "heterogeneous-wet-co2-corrosion/CO2.csv"
    )
    summary["datasets"]["aquasoldb-gas-solubility-v2-1"] = inspect_aquasoldb_co2()
    summary["datasets"].update(inspect_hydrogen(RAW))
    hydrogen_fatigue = audit_hymatbase_hydrogen_fatigue(
        RAW / "hymatbase-4130x-hydrogen-fracture-fatigue/1211_NIB10_fra_fat.xlsx",
        expected_sha256="d8358b11538f35bd87c7512263b6e3907a48ffe28309a841c2974d3eaec3b528",
        source_group_id="hymatbase-j1e8n-2bz97",
        physical_material_condition_id="4130X-QT-SAND2012-7321",
        provider_record_pressure_Pa=4.5e6,
        provider_record_temperature_K=298.15,
        acknowledge_pressure_conflict=True,
    )
    summary["datasets"]["hymatbase-4130x-hydrogen-fracture-fatigue"] = {
        "series_count": hydrogen_fatigue.series_count,
        "point_count": hydrogen_fatigue.point_count,
        "point_count_by_series": hydrogen_fatigue.point_count_by_series,
        "pressure_reconciliation_status": hydrogen_fatigue.pressure_reconciliation_status,
        "rights_status": "review_required_record_rights_section_blank",
        "use": "Local structure audit only; no redistributed points, qualified curve, life or probability.",
    }
    ledger = json.loads((ROOT / "data/acquisition_log.json").read_text(encoding="utf-8"))
    latest = {(r["dataset_id"], r["filename"]): r for r in ledger["attempts"]}
    summary["acquired_assets"] = sum(r["status"] == "downloaded" for r in latest.values())
    summary["acquired_bytes"] = sum(r.get("bytes", 0) for r in latest.values() if r["status"] == "downloaded")
    target = ROOT / "data/data_inventory.json"
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
