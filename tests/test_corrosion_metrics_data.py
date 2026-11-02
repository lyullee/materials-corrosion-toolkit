import zipfile

import pytest

from matintegrity.corrosion_metrics_data import SHEETS, read_corrosion_alloy_metrics

openpyxl = pytest.importorskip("openpyxl")
pd = pytest.importorskip("pandas")


def source_workbook(tmp_path):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    for title, definition in SHEETS.items():
        sheet = workbook.create_sheet(title)
        sheet.cell(3, 1, 1)
        for element, column in definition.composition_columns:
            sheet.cell(3, column, 1.0 if element == "Fe" else "NA")
        for field, column in definition.condition_columns:
            if field == "test_temperature_degC":
                sheet.cell(3, column, 25.0)
            elif field == "pH":
                sheet.cell(3, column, 7.0)
            else:
                sheet.cell(3, column, f"test-{field}")
        sheet.cell(3, definition.reference_column, 1)
        sheet.cell(3, definition.material_class_column, "test-alloy")
        for metric in definition.metric_columns:
            sheet.cell(3, metric.column, 10.0)

    pitting = workbook["Pitting Potential"]
    pitting.cell(3, 26, ">800")
    pitting.cell(3, 27, "Transpassive")
    pitting.cell(3, 28, "NA")
    crevice_temperature = workbook["Crevice Corrosion Temp"]
    crevice_temperature.cell(3, 22, "<-2.5")
    hea = workbook["HEAs_Ecorr, icorr, ipass, Rate"]
    hea.cell(3, 25, "1.70 E -7")
    hea.cell(3, 27, 1.0)

    references = workbook.create_sheet("References")
    references.append(["No", "References", "DOI"])
    references.append([1, "Synthetic citation", "\ufeff10.0000/example"])
    path = tmp_path / "source.xlsx"
    workbook.save(path)
    return path


def test_reader_preserves_endpoints_bounds_qualitative_and_missing_values(tmp_path):
    frame = read_corrosion_alloy_metrics(source_workbook(tmp_path))
    assert frame.source_observation_id.nunique() == 6
    assert len(frame) == sum(len(definition.metric_columns) for definition in SHEETS.values())
    pitting = frame.loc[frame.metric.eq("pitting_potential")].set_index("statistic")
    assert pitting.loc["average", "value_status"] == "lower_bound"
    assert pitting.loc["average", "reported_value"] == 800.0
    assert pitting.loc["average", "normalized_value"] == pytest.approx(0.8)
    assert pitting.loc["average", "normalized_unit"] == "V_vs_SCE"
    assert pitting.loc["maximum", "value_status"] == "qualitative"
    assert pitting.loc["maximum", "qualifier"] == "Transpassive"
    assert pitting.loc["minimum", "value_status"] == "missing"
    assert pd.isna(pitting.loc["minimum", "reported_value"])


def test_reader_normalizes_temperature_current_density_rate_and_spaced_scientific_text(tmp_path):
    frame = read_corrosion_alloy_metrics(source_workbook(tmp_path))
    cct = frame.loc[frame.metric.eq("critical_crevice_temperature") & frame.statistic.eq("average")].iloc[0]
    assert cct.value_status == "upper_bound"
    assert cct.reported_value == -2.5
    assert cct.normalized_value == pytest.approx(270.65)
    icorr = frame.loc[frame.metric.eq("corrosion_current_density") & frame.statistic.eq("average")].iloc[0]
    assert icorr.value_status == "exact_text_numeric"
    assert icorr.reported_value == pytest.approx(1.70e-7)
    assert icorr.normalized_value == pytest.approx(1.70e-3)
    rate = frame.loc[frame.metric.eq("corrosion_rate")].iloc[0]
    assert rate.normalized_value == pytest.approx(1e-3 / (365.25 * 86400.0))
    assert rate.normalized_unit == "m_per_s"
    ecorr_se = frame.loc[frame.metric.eq("corrosion_potential") & frame.statistic.eq("standard_error")].iloc[
        0
    ]
    assert ecorr_se.normalized_unit == "V"
    assert pd.isna(ecorr_se.potential_reference)


def test_reader_preserves_reference_rights_and_does_not_claim_specimen_identity(tmp_path):
    frame = read_corrosion_alloy_metrics(source_workbook(tmp_path))
    assert frame.underlying_reference_doi.unique().tolist() == ["10.0000/example"]
    assert frame.source_group_id.unique().tolist() == ["compilation-reference:1"]
    assert frame.physical_specimen_id.isna().all()
    assert not frame.physical_specimen_independence_reviewed.any()
    assert not frame.test_validity_reviewed.any()
    assert frame.underlying_observation_rights_status.unique().tolist() == ["unresolved"]
    assert frame.attrs["workbook_formula_execution"] is False
    assert frame.attrs["workbook_macro_execution"] is False


def test_reader_keeps_composition_and_conditions_as_explicit_source_fields(tmp_path):
    frame = read_corrosion_alloy_metrics(source_workbook(tmp_path))
    row = frame.iloc[0]
    assert row.composition_wt_percent["Fe"] == 1.0
    assert row.composition_raw["Cr"] == "NA"
    assert row.conditions["test_temperature_degC"] == 25.0
    assert row.material_class == "test-alloy"


def test_reader_rejects_unpinned_workbook_when_pin_is_required(tmp_path):
    with pytest.raises(ValueError, match="pinned Figshare"):
        read_corrosion_alloy_metrics(source_workbook(tmp_path), require_pinned_hash=True)


def test_reader_rejects_macro_content(tmp_path):
    path = source_workbook(tmp_path)
    with zipfile.ZipFile(path, "a") as archive:
        archive.writestr("xl/vbaProject.bin", b"not executed")
    with pytest.raises(ValueError, match="macro-enabled"):
        read_corrosion_alloy_metrics(path)


def test_reader_rejects_missing_required_sheet(tmp_path):
    path = source_workbook(tmp_path)
    workbook = openpyxl.load_workbook(path)
    workbook.remove(workbook["Pitting Potential"])
    workbook.save(path)
    with pytest.raises(ValueError, match="required workbook sheets"):
        read_corrosion_alloy_metrics(path)
