import hashlib
import math

import pytest

from matintegrity.hydrogen_exports import (
    FARADAY_C_MOL_ELECTRONS,
    HydrogenPermeationSignalCalibration,
    HydrogenTdsSignalCalibration,
    TabularExportProvenance,
    permeation_flux_observations,
    read_permeation_export,
    read_permeation_summary,
    read_tds_export,
    read_tds_exposure_summary,
    tds_molar_observations,
)


def exported(folder, text):
    path = folder / "synthetic.csv"
    path.write_bytes(text.encode("utf-8-sig"))
    reference = TabularExportProvenance(
        dataset_id="synthetic",
        archive_sha256="a" * 64,
        member_path="synthetic.opju",
        member_sha256="b" * 64,
        tool_name="synthetic fixture",
        tool_version="1",
        workbook_id="synthetic",
        worksheet_id="source",
        csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    return path, reference


EVIDENCE = ({"source_id": "synthetic", "origin": "synthetic", "citation": "Authored test"},)


def permeation_calibration(reference, **updates):
    values = dict(
        calibration_id="synthetic-permeation",
        material_condition_id="synthetic-state",
        specimen_id="synthetic-specimen",
        export_csv_sha256=reference.csv_sha256,
        selected_current_channel="current_A",
        selected_clock_channel="instrument_clock_s",
        clock_origin_s=10.0,
        current_sign_for_outward_hydrogen=1,
        membrane_area_m2=0.5,
        electron_mol_per_hydrogen_atom_mol=1.0,
        current_efficiency=0.5,
        background_handling="none_raw_channel",
        area_basis="synthetic reviewed exposed area",
        clock_origin_basis="synthetic charging origin",
        physical_mapping_reviewed=True,
        evidence=EVIDENCE,
    )
    values.update(updates)
    return HydrogenPermeationSignalCalibration.model_validate(values)


def tds_calibration(reference, **updates):
    values = dict(
        calibration_id="synthetic-tds",
        material_condition_id="synthetic-state",
        specimen_id="synthetic-specimen",
        heating_program_id="synthetic-ramp",
        export_csv_sha256=reference.csv_sha256,
        series_index=1,
        series_label="sample-a",
        sample_mass_kg=0.002,
        hydrogen_atomic_molar_mass_kg_mol=0.001,
        rate_basis="hydrogen_mass_ppm_per_sample_mass_per_s",
        integral_basis="hydrogen_mass_ppm_per_sample_mass",
        detector_response_reviewed=True,
        sample_mass_reviewed=True,
        ppm_basis_reviewed=True,
        evidence=EVIDENCE,
    )
    values.update(updates)
    return HydrogenTdsSignalCalibration.model_validate(values)


def test_export_digest_detects_changed_bytes_without_claiming_source_validity(tmp_path):
    path, reference = exported(tmp_path, "1,2,3\n")
    frame = read_permeation_export(path, reference)
    assert frame.attrs["export_provenance"]["identity_review"] == "mapping_requires_review"
    assert frame.attrs["physical_qualification"] == "axis_and_protocol_review_required_before_calibration"
    path.write_text("1,2,4\n", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        read_permeation_export(path, reference)


def test_permeation_keeps_negative_processing_and_disagreed_clock_origin(tmp_path):
    path, reference = exported(
        tmp_path, '"start charging time: 11s density: 99",synthetic,,,\n0.3,2,11,1,-1\n0.3,4,12,2,1\n'
    )
    frame = read_permeation_export(path, reference)
    assert frame.processed_current_source.tolist() == [-1.0, 1.0]
    assert frame.attrs["instrument_minus_shifted_clock_source"] == 10.0
    assert frame.attrs["comment_charging_time_s"] == 11.0
    assert frame.attrs["source_current_subtraction"] == 3.0
    assert frame.attrs["charging_origin"] == "not_selected"
    assert frame.current_A.isna().all() and frame.instrument_clock_s.isna().all()
    converted = read_permeation_export(
        path, reference, current_unit="mA", clock_unit="min", potential_unit="V"
    )
    assert converted.current_A.tolist() == [0.002, 0.004]
    assert converted.instrument_clock_s.tolist() == [660.0, 720.0]
    assert converted.processed_current_A.tolist() == [-0.001, 0.001]
    assert converted.source_row.tolist() == [2, 3]


def test_explicit_clock_preservation_does_not_sort_or_remove_observations(tmp_path):
    path, reference = exported(tmp_path, "1,2,3\n1,4,3\n1,5,2\n")
    with pytest.raises(ValueError, match="clock must increase"):
        read_permeation_export(path, reference)
    frame = read_permeation_export(path, reference, clock_policy="preserve")
    assert frame.current_source.tolist() == [2.0, 4.0, 5.0]
    assert frame.attrs["repeated_clock_steps"] == 1 and frame.attrs["reversed_clock_steps"] == 1


@pytest.mark.parametrize("bad", ["comment,2,4", "1,NaN,4", "1,2", "1,2,4,unknown", ",,"])
def test_numeric_observation_failure_is_not_silently_skipped(tmp_path, bad):
    path, reference = exported(tmp_path, "1,2,3\n" + bad + "\n1,2,5\n")
    with pytest.raises(ValueError):
        read_permeation_export(path, reference)


def test_summary_repair_is_explicit_and_never_applies_plot_axis_scale_again(tmp_path):
    path, reference = exported(tmp_path, "synthetic,2e-10,0,3,--,A\n(Ti,Mo)C steel,4e-11,1e-12,2,0.1,B\n")
    with pytest.raises(ValueError, match="six columns"):
        read_permeation_summary(path, reference)
    frame = read_permeation_summary(path, reference, label_policy="join_split_ti_mo", diffusivity_unit="m2/s")
    assert frame.material_label.tolist() == ["synthetic", "(Ti,Mo)C steel"]
    assert frame.effective_diffusivity_m2_s.tolist() == [2e-10, 4e-11]
    assert frame.diffusivity_error_source.iloc[0] == 0.0
    assert math.isnan(frame.concentration_error_source.iloc[0])
    assert frame.attrs["structural_repair_source_rows"] == [2]
    assert frame.attrs["ppm_basis"] == frame.attrs["error_statistic"] == "unresolved"
    assert (
        read_permeation_summary(path, reference, label_policy="join_split_ti_mo")
        .effective_diffusivity_m2_s.isna()
        .all()
    )


def test_summary_repair_rejects_an_unrecognized_seventh_column(tmp_path):
    path, reference = exported(tmp_path, "another,label,1,2,3,4,5\n")
    with pytest.raises(ValueError, match="six columns"):
        read_permeation_summary(path, reference, label_policy="join_split_ti_mo")


def test_tds_preserves_reversal_negative_rate_variable_length_and_integral_identity(tmp_path):
    path, reference = exported(
        tmp_path, ",first,first,,second,second\n20,1e-5,0,21,2e-5,0\n19,-1e-6,0.1,,,\n19,3e-5,0.2,,,\n"
    )
    frame = read_tds_export(path, reference, temperature_unit="degC", rate_unit="ppm/s")
    first = frame[frame.series_index.eq(1)]
    assert first.temperature_source.tolist() == [20.0, 19.0, 19.0]
    assert first.temperature_K.tolist() == [293.15, 292.15, 292.15]
    assert first.rate_source.tolist() == [1e-5, -1e-6, 3e-5]
    assert len(frame) == 4 and frame.source_row.tolist() == [2, 3, 4, 2]
    assert frame.attrs["sample_clock"] == "not_available_in_export"
    assert frame.attrs["integral_meaning"] == "source_derived_integral_not_independent_measurement"
    assert not frame.attrs["full_temperature_range_is_summary_integration_range"]


def test_tds_reader_preserves_explicit_article_reviewed_mass_ppm_basis(tmp_path):
    path, reference = exported(tmp_path, ",sample,sample\n20,1e-5,0\n")
    frame = read_tds_export(
        path,
        reference,
        temperature_unit="degC",
        rate_unit="ppm/s",
        ppm_basis="hydrogen_mass_per_sample_mass",
    )
    assert frame.attrs["ppm_basis"] == "hydrogen_mass_per_sample_mass"
    with pytest.raises(ValueError, match="unknown TDS ppm basis"):
        read_tds_export(path, reference, ppm_basis="volume_ppm")


@pytest.mark.parametrize("text", [",a,b\n20,1,0\n", ",a,a\n20,,0\n", ",a,a\n20,1,0\n,,\n21,2,1\n"])
def test_tds_rejects_mismatched_incomplete_or_gapped_triples(tmp_path, text):
    path, reference = exported(tmp_path, text)
    with pytest.raises(ValueError):
        read_tds_export(path, reference)


def test_explicit_missing_tail_is_counted_without_fabricating_a_temperature_point(tmp_path):
    path, reference = exported(tmp_path, ",a,a,,b,b\n20,1,0,20,1,0\n--,,,21,2,1\n")
    frame = read_tds_export(path, reference)
    assert len(frame) == 3
    assert frame.attrs["tail_missing_marker_rows"] == {"1": 1, "2": 0}


def test_incomplete_first_permeation_row_is_not_a_header(tmp_path):
    path, reference = exported(tmp_path, ",2,3\n1,2,4\n")
    with pytest.raises(ValueError, match="partial numeric"):
        read_permeation_export(path, reference)


def test_exposure_summary_keeps_unsorted_conditions_and_uncharged_control(tmp_path):
    path, reference = exported(
        tmp_path,
        ",material-a,,material-b,\n,review-window,,review-window,\n12,2,0,5,\n0,3,12,4,\nuncharged,0.1,uncharged,0.2,--\n",
    )
    frame = read_tds_exposure_summary(path, reference, exposure_unit="h", content_unit="ppm")
    first = frame[frame.series_index.eq(1)]
    assert first.exposure_s.iloc[:2].tolist() == [43200.0, 0.0]
    assert math.isnan(first.exposure_s.iloc[2]) and first.uncharged.tolist() == [False, False, True]
    assert frame.attrs["ordering"] == "original_conditions_not_a_specimen_history"
    assert read_tds_exposure_summary(path, reference).exposure_s.isna().all()


@pytest.mark.parametrize(
    "reader,kwargs",
    [
        (read_permeation_export, {"current_unit": "A/m2"}),
        (read_permeation_export, {"clock_policy": "sort"}),
        (read_permeation_summary, {"diffusivity_unit": "plot_1e-11"}),
        (read_tds_export, {"temperature_unit": "F"}),
        (read_tds_exposure_summary, {"content_unit": "mass_fraction"}),
    ],
)
def test_unreviewed_units_and_implicit_transformations_are_refused(tmp_path, reader, kwargs):
    path, reference = exported(tmp_path, "1,2,3\n")
    with pytest.raises(ValueError):
        reader(path, reference, **kwargs)


def test_reviewed_permeation_signal_converts_current_to_signed_atomic_flux(tmp_path):
    path, reference = exported(tmp_path, "0,1,10\n0,2,12\n0,-1,15\n")
    frame = read_permeation_export(path, reference, current_unit="A", clock_unit="s")
    converted = permeation_flux_observations(frame, permeation_calibration(reference))
    factor = 0.5 / (FARADAY_C_MOL_ELECTRONS * 0.5)
    assert converted.elapsed_time_s.tolist() == [0.0, 2.0, 5.0]
    assert converted.outward_hydrogen_flux_mol_m2_s.tolist() == pytest.approx([factor, 2 * factor, -factor])
    assert converted.cumulative_outward_hydrogen_mol_m2.tolist() == pytest.approx(
        [0.0, 3 * factor, 4.5 * factor]
    )
    assert converted.attrs["boundary_concentration_inference"] == "not_performed"
    assert converted.attrs["sign_policy"] == "signed_signal_preserved_without_clipping"


@pytest.mark.parametrize(
    ("calibration_updates", "loader_kwargs", "message"),
    [
        ({"physical_mapping_reviewed": False}, {"current_unit": "A", "clock_unit": "s"}, "require review"),
        ({"export_csv_sha256": "f" * 64}, {"current_unit": "A", "clock_unit": "s"}, "digest"),
        ({}, {}, "resolved current and clock"),
        (
            {
                "selected_current_channel": "processed_current_A",
                "background_handling": "none_raw_channel",
            },
            {"current_unit": "A", "clock_unit": "s"},
            "background handling",
        ),
    ],
)
def test_permeation_signal_conversion_refuses_unresolved_or_inconsistent_mapping(
    tmp_path, calibration_updates, loader_kwargs, message
):
    path, reference = exported(tmp_path, "0,1,10,0,1\n0,2,12,2,2\n")
    frame = read_permeation_export(path, reference, **loader_kwargs)
    with pytest.raises(ValueError, match=message):
        permeation_flux_observations(frame, permeation_calibration(reference, **calibration_updates))


def test_permeation_signal_conversion_does_not_sort_or_filter_invalid_model_clock(tmp_path):
    path, reference = exported(tmp_path, "0,1,10\n0,2,10\n")
    frame = read_permeation_export(path, reference, current_unit="A", clock_unit="s", clock_policy="preserve")
    with pytest.raises(ValueError, match="strictly increasing"):
        permeation_flux_observations(frame, permeation_calibration(reference))


def test_reviewed_tds_mass_ppm_converts_one_series_without_fabricating_time(tmp_path):
    path, reference = exported(
        tmp_path,
        ",sample-a,sample-a,,sample-b,sample-b\n20,1,0,30,4,0\n19,-2,3,31,5,1\n",
    )
    frame = read_tds_export(
        path,
        reference,
        temperature_unit="degC",
        rate_unit="ppm/s",
        integral_unit="ppm",
    )
    converted = tds_molar_observations(frame, tds_calibration(reference))
    assert converted.temperature_K.tolist() == pytest.approx([293.15, 292.15])
    assert converted.desorption_rate_hydrogen_atoms_mol_kg_sample_s.tolist() == pytest.approx([1e-3, -2e-3])
    assert converted.source_integrated_hydrogen_atoms_mol_kg_sample.tolist() == pytest.approx([0.0, 3e-3])
    assert converted.desorption_rate_hydrogen_atoms_mol_s.tolist() == pytest.approx([2e-6, -4e-6])
    assert converted.source_integrated_hydrogen_atoms_mol.tolist() == pytest.approx([0.0, 6e-6])
    assert converted.attrs["kinetic_time_alignment_ready"] is False
    assert converted.attrs["temperature_order"] == "source_order_preserved_without_sorting"


def test_tds_mass_normalized_conversion_does_not_require_unreported_sample_mass(tmp_path):
    path, reference = exported(tmp_path, ",sample-a,sample-a\n20,2,0\n21,3,4\n")
    frame = read_tds_export(
        path,
        reference,
        temperature_unit="K",
        rate_unit="ppm/s",
        integral_unit="ppm",
    )
    calibration = tds_calibration(
        reference,
        sample_mass_kg=None,
        sample_mass_reviewed=False,
    )
    converted = tds_molar_observations(frame, calibration)
    assert converted.desorption_rate_hydrogen_atoms_mol_kg_sample_s.tolist() == pytest.approx([2e-3, 3e-3])
    assert "desorption_rate_hydrogen_atoms_mol_s" not in converted
    assert converted.attrs["total_moles_available"] is False


@pytest.mark.parametrize(
    ("sample_mass_kg", "sample_mass_reviewed", "message"),
    [
        (None, True, "cannot be reviewed"),
        (0.002, False, "must be reviewed"),
    ],
)
def test_tds_calibration_keeps_optional_mass_and_review_state_consistent(
    sample_mass_kg, sample_mass_reviewed, message
):
    with pytest.raises(ValueError, match=message):
        tds_calibration(
            type("Reference", (), {"csv_sha256": "a" * 64})(),
            sample_mass_kg=sample_mass_kg,
            sample_mass_reviewed=sample_mass_reviewed,
        )


@pytest.mark.parametrize(
    ("updates", "units", "message"),
    [
        ({"ppm_basis_reviewed": False}, True, "require review"),
        ({"series_label": "other"}, True, "series index and label"),
        ({"export_csv_sha256": "f" * 64}, True, "digest"),
        ({}, False, "resolved TDS"),
    ],
)
def test_tds_signal_conversion_refuses_unreviewed_identity_units_and_basis(tmp_path, updates, units, message):
    path, reference = exported(tmp_path, ",sample-a,sample-a\n20,1,0\n21,2,1\n")
    kwargs = dict(temperature_unit="K", rate_unit="ppm/s", integral_unit="ppm") if units else {}
    frame = read_tds_export(path, reference, **kwargs)
    with pytest.raises(ValueError, match=message):
        tds_molar_observations(frame, tds_calibration(reference, **updates))
