import io
import zipfile

import pytest
from openpyxl import Workbook
from openpyxl.styles import PatternFill

from matintegrity.burst_data import read_burst_compilation


def workbook():
    book = Workbook()
    sheet = book.active
    sheet.title = "Burst Database"
    sheet["B3"].fill = PatternFill("solid", fgColor="FFFF0000")
    sheet["B4"].fill = PatternFill("solid", fgColor="FF0000FF")
    sheet["C3"] = "standard property completion"
    sheet["C4"] = "calculated geometry"
    sheet["B7"] = "source-one"
    sheet["C7"] = "Synthetic authored source"
    headers = [
        "Case",
        "Tipo",
        "D (mm)",
        "t (mm)",
        "sigmay (Mpa)",
        "sigmau (Mpa)",
        "E (Mpa)",
        "d (mm)",
        "l (mm)",
        "w (mm)",
        "Pb (Mpa)",
        "Ref. ID",
        "Material",
    ]
    for column, value in enumerate(headers, 2):
        sheet.cell(21, column, value)
    for i, kind in enumerate(["EXP", "FEM", "EXP"], 1):
        values = [
            i,
            kind,
            400.0,
            10.0,
            300.0,
            450.0,
            200000.0,
            3.0,
            100.0,
            20.0,
            8.0,
            "source-one" if i < 3 else "unresolved",
            "synthetic",
        ]
        for column, value in enumerate(values, 2):
            sheet.cell(21 + i, column, value)
    sheet["H22"].fill = sheet["B3"].fill.__copy__()
    sheet["K22"].fill = sheet["B4"].fill.__copy__()
    book.create_sheet("auxiliary-not-extra")["A1"] = 1
    return book


def test_reader_preserves_experiment_simulation_units_and_compiler_flags(tmp_path):
    book = workbook()
    buffer = io.BytesIO()
    book.save(buffer)
    path = tmp_path / "synthetic.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("nested/BursTests.xlsx", buffer.getvalue())
    frame = read_burst_compilation(path)
    assert len(frame) == 3 and frame.observation_domain.tolist() == [
        "experimental",
        "finite_element",
        "experimental",
    ]
    assert frame.wall_thickness_m.tolist() == [0.01] * 3
    assert frame.burst_pressure_Pa.tolist() == [8e6] * 3
    assert frame.field_provenance.iloc[0]["elastic_modulus_Pa"] == "compiler_completed_material_property"
    assert frame.field_provenance.iloc[0]["defect_width_m"] == "compiler_inferred_geometry"
    assert frame.source_reference_resolved.tolist() == [True, True, False]
    assert frame.reference_mapping_status.tolist() == [
        "compilation_legend_reference",
        "compilation_legend_reference",
        "unresolved_compilation_label",
    ]
    assert frame.pressure_result_role.tolist() == [
        "reported_experimental_burst_pressure",
        "reported_finite_element_failure_pressure",
        "reported_experimental_burst_pressure",
    ]
    assert set(frame.physical_specimen_identity_status) == {"not_provided_in_primary_table"}
    assert set(frame.underlying_observation_rights_status) == {"not_reviewed"}
    assert frame.identical_reported_input_and_target.all()
    assert frame.diameter_basis.iloc[0] == "not_explicit_in_primary_table"
    assert frame.pressure_basis.iloc[0] == "not_explicit_in_primary_table"
    assert frame.attrs["supplementary_sheets_excluded"] == ["auxiliary-not-extra"]


def test_unknown_domain_and_unexecuted_formula_do_not_become_measured_data(tmp_path):
    book = workbook()
    path = tmp_path / "synthetic.xlsx"
    book["Burst Database"]["C22"] = "OTHER"
    book.save(path)
    with pytest.raises(ValueError, match="observation type"):
        read_burst_compilation(path)
    book["Burst Database"]["C22"] = "EXP"
    book["Burst Database"]["H22"] = "=1+1"
    book.save(path)
    frame = read_burst_compilation(path)
    assert not frame.numeric_geometry_material_valid.iloc[0]
    assert frame.unexecuted_formulas.iloc[0]["elastic_modulus_Pa"] == "=1+1"
