"""Aggregate hydrogen assets without redistributing their observations."""

import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd

from matintegrity import hydrogen_exports
from matintegrity.hydrogen_data import read_he_austenite


def inspect_compilation(raw):
    f = read_he_austenite(raw / "he-austenite")
    return {
        "he-austenite": dict(
            report_rows=len(f),
            source_labels=int(f.source_id.nunique()),
            declared_condition_signatures=int(f.declared_condition_signature.nunique()),
            property_counts=f.property_name.value_counts().to_dict(),
            zone_counts=f.zone.value_counts().to_dict(),
            exposure_counts=f.hydrogen_exposure.value_counts().to_dict(),
            compiler_verified_records=int(f.compiler_verified.sum()),
            ratio_only_records=int(f.arithmetic_retention_ratio.isna().sum()),
            reported_ratios_above_one=int(f.reported_retention_ratio.gt(1).sum()),
            maximum_absolute_ratio_rounding_difference=float(f.ratio_absolute_discrepancy.max()),
            unresolved_property_unit_records=int(f.property_unit.eq("unresolved").sum()),
            coincident_reported_condition_and_value_rows=int(
                f.coincident_reported_condition_and_values.sum()
            ),
            mapped_composition_groups=int(f.loc[f.comp_key.ne(""), "comp_key"].nunique()),
            composition_link_inconsistent_records=int(f.composition_link_consistent.eq(False).sum()),
            composition_basis_counts=f.composition_basis.replace("", "unreported").value_counts().to_dict(),
            records_with_compiler_zero_element_assumptions=int(f.derived_assumptions.ne("").sum()),
            records_without_heat_id=int(f.heat.eq("").sum()),
            source_hashes=f.attrs["source_hashes"],
            rights_status="underlying_literature_review_required",
            qualification="One row is a reported condition/property, not an independently identified specimen. Preserve precharge versus in-situ exposure, weld zone and reference condition. Fifteen row/link composition conflicts and four unresolved plastic-strain units require original-source review. Compiler verification is not re-extraction by this package. No service suitability, fracture-growth curve or failure probability is calibrated from this compilation; raw and pointwise derived observations remain excluded.",
        )
    }


def inspect_primary(raw):
    path = raw / "carbide-traps/NCOMMS-23-27903B data.zip"
    with zipfile.ZipFile(path) as archive:
        members = [
            m for m in archive.infolist() if not m.is_dir() and "__MACOSX" not in m.filename.split("/")
        ]
        workbook = "First principle simluation raw data/Fig.1FG.xlsx"
        content = archive.read(workbook)
        book = pd.ExcelFile(io.BytesIO(content))
        sheets = {s: list(pd.read_excel(book, sheet_name=s, header=None).shape) for s in book.sheet_names}
        projects = [m for m in members if Path(m.filename).suffix.lower() == ".opju"]
        project_metadata = [
            dict(
                member=m.filename,
                bytes=m.file_size,
                sha256=hashlib.sha256(archive.read(m)).hexdigest(),
                ingestion_status="numeric_exports_available_protocol_review_required"
                if (raw.parent / "derived/carbide-traps/viewer-export/export_manifest.json").exists()
                else "numeric_table_export_and_axis_review_required",
            )
            for m in projects
        ]
    return {
        "carbide-traps": dict(
            archive_bytes=path.stat().st_size,
            non_directory_members=len(members),
            top_level_file_counts=dict(Counter(m.filename.split("/")[0] for m in members)),
            suffix_counts=dict(Counter(Path(m.filename).suffix.lower() or "no_suffix" for m in members)),
            dft_workbook_member=workbook,
            dft_workbook_sha256=hashlib.sha256(content).hexdigest(),
            dft_workbook_sheet_shapes=sheets,
            origin_projects=project_metadata,
            potcar_named_members=sum(Path(m.filename).name.upper().startswith("POTCAR") for m in members),
            numeric_exports=inspect_exports(raw.parent / "derived/carbide-traps/viewer-export"),
            protocol_review=dict(
                source_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC10808193/",
                supplementary_information_url="https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-024-45017-4/MediaObjects/41467_2024_45017_MOESM1_ESM.pdf",
                supplementary_information_sha256="32e8e12be214f0421cb0d1de6bb6bf111c9ecb2d69d3a8c387d0830c25face43",
                source_license="CC-BY-4.0",
                tds_specimen_geometry="finite_cylinder",
                tds_specimen_diameter_m=0.005,
                tds_specimen_length_m=0.025,
                tds_precharge_duration_s=172800,
                tds_precharge_reported_current_density_magnitude_A_m2=3.0,
                tds_reported_content_basis="hydrogen_mass_per_sample_mass",
                tds_nominal_heating_rate_from_workbook_K_h=100,
                tds_nominal_heating_rate_measured_clock_equivalent=False,
                measured_sample_clock_available=False,
                tds_raw_workbook_material_mapping={
                    "IP0time": {
                        "candidate_material": "TiC steel",
                        "status": "probable_cross_file_label_exposure_and_scale_match_not_specimen_identity",
                        "zero_exposure_label": "IP0_100_repeat",
                    },
                    "IP2time": {
                        "candidate_material": "(Ti,Mo)C steel",
                        "status": "probable_cross_file_label_exposure_and_scale_match_not_specimen_identity",
                        "zero_exposure_label": "IP2_charged",
                    },
                },
                tds_mass_normalized_signal_conversion_ready=False,
                tds_mass_normalized_signal_blockers=[
                    "detector_response_not_calibrated",
                    "exact_curve_to_physical_specimen_identity_not_established",
                    "source_integral_unit_and_basis_not_established",
                ],
                tds_transport_inverse_ready=False,
                tds_transport_inverse_blockers=[
                    "measured_sample_clock_absent",
                    "initial_spatial_hydrogen_distribution_not_established",
                    "curved_and_end_surface_release_conditions_not_established",
                    "detector_dynamics_not_established",
                ],
                tds_end_surface_boundary="not_established",
                tds_transfer_delay_s=None,
                permeation_reported_potential_V=0.3,
                permeation_reported_solution="0.2 mol/L NaOH plus 0.3 mass-percent NH4SCN",
                permeation_potential_reference="not_explicit_in_main_methods",
                permeation_representative_plot_current_unit="microampere",
                permeation_summary_error_statistic="standard_deviation_from_at_least_two_measurements_in_supplementary_figure_4",
                permeation_membrane_thickness_m=None,
                permeation_exposed_area_m2=None,
                permeation_curve_to_material_and_replicate_mapping="not_established",
                permeation_transport_inverse_ready=False,
                permeation_transport_inverse_blockers=[
                    "membrane_thickness_not_reported",
                    "exposed_area_not_reported",
                    "potential_reference_not_reported",
                    "entry_and_exit_cell_mapping_not_established",
                    "raw_curve_to_material_and_replicate_mapping_not_established",
                ],
                exposure_label_reconciliation="TiC_and_TiMoC_summary_labels_are_explicit; raw_workbook_material_mapping_is_probable_but_physical_specimen_identity_remains_unresolved",
                qualification="The article and supplement establish the TDS cylinder geometry, precharge protocol, hydrogen mass-ppm basis, nominal 100 K/h program and article-level material/exposure labels. They do not establish a measured TDS clock, curve-level physical specimen identity, initial spatial distribution, all three release boundaries or detector dynamics. Main-article TDS geometry is not the permeation membrane geometry. Declared charging current is not absorbed hydrogen flux. Permeation thickness, area, potential reference and curve-to-replicate mapping remain absent, so neither raw experiment is ready for transport inversion.",
            ),
            qualification="Primary electrochemically charged steel trapping/desorption/permeation study with DFT, microscopy and atom-probe assets. DFT energy matrices are not measured transport histories. Reviewed CSV exports preserve signs, clocks and identities; the TDS hydrogen mass-ppm basis is now article-supported, while detector response, physical specimen mapping and transport boundary conditions remain unresolved. No project scripts, plot digitization or equilibrium/kinetic calibration are used. Raw assets and pointwise observations are excluded from public distributions.",
        )
    }


def inspect_exports(folder):
    manifest_path = folder / "export_manifest.json"
    if not manifest_path.exists():
        return dict(status="export_manifest_not_available")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    readers = {
        name: getattr(hydrogen_exports, name)
        for name in (
            "read_permeation_export",
            "read_permeation_summary",
            "read_tds_export",
            "read_tds_exposure_summary",
        )
    }
    result = []
    for record in manifest["exports"]:
        reference = hydrogen_exports.TabularExportProvenance.model_validate(record["provenance"])
        frame = readers[record["reader"]](folder / record["filename"], reference, **record["reader_kwargs"])
        for name in record["duplicate_filenames"]:
            if hashlib.sha256((folder / name).read_bytes()).hexdigest() != reference.csv_sha256:
                raise ValueError("duplicate export digest changed")
        metadata = dict(
            filename=record["filename"],
            duplicate_filenames=record["duplicate_filenames"],
            rows=len(frame),
            reader=record["reader"],
            provenance=reference.model_dump(mode="json"),
            declared_units=frame.attrs["declared_units"],
        )
        if record["reader"] == "read_permeation_export":
            metadata.update(
                {
                    key: frame.attrs[key]
                    for key in (
                        "instrument_minus_shifted_clock_source",
                        "comment_charging_time_s",
                        "repeated_clock_steps",
                        "reversed_clock_steps",
                    )
                }
            )
            metadata["negative_processed_current_rows"] = int(frame.processed_current_source.lt(0).sum())
        elif record["reader"] == "read_tds_export":
            metadata["ppm_basis"] = frame.attrs["ppm_basis"]
            metadata["series_count"] = int(frame.series_index.nunique())
            metadata["tail_missing_marker_rows"] = frame.attrs["tail_missing_marker_rows"]
            differences = frame.groupby("series_index").temperature_source.diff()
            metadata["repeated_temperature_steps"] = int(differences.eq(0).sum())
            metadata["reversed_temperature_steps"] = int(differences.lt(0).sum())
            metadata["negative_rate_rows"] = int(frame.rate_source.lt(0).sum())
        elif record["reader"] == "read_permeation_summary":
            metadata["structural_repair_source_rows"] = frame.attrs["structural_repair_source_rows"]
            metadata["missing_concentration_error_rows"] = int(frame.concentration_error_source.isna().sum())
        else:
            metadata["ppm_basis"] = frame.attrs["ppm_basis"]
            metadata["uncharged_control_rows"] = int(frame.uncharged.sum())
        result.append(metadata)
    return dict(
        status="numeric_exports_structurally_checked_not_physically_calibrated",
        unique_csv_exports=len(result),
        duplicate_csv_exports=sum(len(r["duplicate_filenames"]) for r in result),
        files=result,
        qualification="Retain original ordering, negative processed signals and uncharged controls. Clock offset disagrees with a BQ2 comment by one second. A known unquoted material-label comma is repaired only by explicit policy. The TDS hydrogen mass-ppm basis is article-supported, but detector response, source-integral unit, sample clock, physical specimen independence, boundary concentration and intrinsic lattice diffusivity remain unresolved. TDS full-range source integrals differ in scope from the room-temperature-to-260-C summary. Hashes do not establish experimental validity.",
    )


def inspect(raw):
    return {**inspect_compilation(raw), **inspect_primary(raw)}
