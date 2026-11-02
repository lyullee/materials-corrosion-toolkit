"""Verify reviewed hydrogen signal conversions using authored SI-scale examples."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from matintegrity.hydrogen_exports import (
    FARADAY_C_MOL_ELECTRONS,
    HydrogenPermeationSignalCalibration,
    HydrogenTdsSignalCalibration,
    TabularExportProvenance,
    permeation_flux_observations,
    read_permeation_export,
    read_tds_export,
    tds_molar_observations,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ({"source_id": "authored", "origin": "synthetic", "citation": "Authored SI identity"},)


def provenance(path: Path, worksheet_id: str) -> TabularExportProvenance:
    return TabularExportProvenance(
        dataset_id="authored",
        archive_sha256="a" * 64,
        member_path="authored.opju",
        member_sha256="b" * 64,
        tool_name="authored fixture",
        tool_version="1",
        workbook_id="authored",
        worksheet_id=worksheet_id,
        csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        identity_review="viewer_reviewed",
    )


def main() -> None:
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        permeation_path = folder / "permeation.csv"
        permeation_path.write_text("0,1,10\n0,3,12\n", encoding="utf-8")
        permeation_source = provenance(permeation_path, "permeation")
        permeation_frame = read_permeation_export(
            permeation_path,
            permeation_source,
            potential_unit="V",
            current_unit="A",
            clock_unit="s",
        )
        permeation_contract = HydrogenPermeationSignalCalibration(
            calibration_id="authored-permeation",
            material_condition_id="authored-material",
            specimen_id="authored-specimen",
            export_csv_sha256=permeation_source.csv_sha256,
            selected_current_channel="current_A",
            selected_clock_channel="instrument_clock_s",
            clock_origin_s=10.0,
            current_sign_for_outward_hydrogen=1,
            membrane_area_m2=0.5,
            electron_mol_per_hydrogen_atom_mol=1.0,
            current_efficiency=0.5,
            background_handling="none_raw_channel",
            area_basis="authored area",
            clock_origin_basis="authored clock origin",
            physical_mapping_reviewed=True,
            evidence=EVIDENCE,
        )
        permeation = permeation_flux_observations(permeation_frame, permeation_contract)
        expected_flux = [1.0 / FARADAY_C_MOL_ELECTRONS, 3.0 / FARADAY_C_MOL_ELECTRONS]
        expected_cumulative = 4.0 / FARADAY_C_MOL_ELECTRONS

        tds_path = folder / "tds.csv"
        tds_path.write_text(",sample,sample\n20,2,0\n30,-1,3\n", encoding="utf-8")
        tds_source = provenance(tds_path, "tds")
        tds_frame = read_tds_export(
            tds_path,
            tds_source,
            temperature_unit="degC",
            rate_unit="ppm/s",
            integral_unit="ppm",
        )
        tds_contract = HydrogenTdsSignalCalibration(
            calibration_id="authored-tds",
            material_condition_id="authored-material",
            specimen_id="authored-specimen",
            heating_program_id="authored-program",
            export_csv_sha256=tds_source.csv_sha256,
            series_index=1,
            series_label="sample",
            sample_mass_kg=0.002,
            hydrogen_atomic_molar_mass_kg_mol=0.001,
            rate_basis="hydrogen_mass_ppm_per_sample_mass_per_s",
            integral_basis="hydrogen_mass_ppm_per_sample_mass",
            detector_response_reviewed=True,
            sample_mass_reviewed=True,
            ppm_basis_reviewed=True,
            evidence=EVIDENCE,
        )
        tds = tds_molar_observations(tds_frame, tds_contract)
        expected_tds_rate = [4e-6, -2e-6]
        expected_tds_integral = [0.0, 6e-6]
        expected_tds_rate_per_kg = [0.002, -0.001]

    errors = {
        "permeation_flux": max(
            abs(actual - expected)
            for actual, expected in zip(permeation.outward_hydrogen_flux_mol_m2_s, expected_flux, strict=True)
        ),
        "permeation_cumulative": abs(
            permeation.cumulative_outward_hydrogen_mol_m2.iloc[-1] - expected_cumulative
        ),
        "tds_rate": max(
            abs(actual - expected)
            for actual, expected in zip(
                tds.desorption_rate_hydrogen_atoms_mol_s, expected_tds_rate, strict=True
            )
        ),
        "tds_rate_per_kg": max(
            abs(actual - expected)
            for actual, expected in zip(
                tds.desorption_rate_hydrogen_atoms_mol_kg_sample_s,
                expected_tds_rate_per_kg,
                strict=True,
            )
        ),
        "tds_integral": max(
            abs(actual - expected)
            for actual, expected in zip(
                tds.source_integrated_hydrogen_atoms_mol, expected_tds_integral, strict=True
            )
        ),
    }
    if max(errors.values()) > 1e-15:
        raise AssertionError(f"hydrogen signal conversion mismatch: {errors}")
    record = {
        "schema_version": "matintegrity.validation.hydrogen_signal_calibration.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": (
            "Authored Faraday and mass-ppm signal-conversion identities; not detector calibration, "
            "transport-parameter fitting or experimental validation."
        ),
        "absolute_errors": errors,
        "permeation_calibration_digest": permeation.attrs["signal_calibration_digest"],
        "tds_calibration_digest": tds.attrs["signal_calibration_digest"],
        "source_sha256": hashlib.sha256(
            (ROOT / "src/matintegrity/hydrogen_exports.py").read_bytes()
        ).hexdigest(),
    }
    target = ROOT / "validation/hydrogen_signal_calibration_math.json"
    target.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
