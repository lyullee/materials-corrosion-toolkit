from pathlib import Path
from zipfile import ZipFile

import pytest

from matintegrity.fabest_lcf_data import (
    TABLE_FILENAMES,
    audit_fabest_lcf_archive,
    iter_fabest_lcf_numeric_rows,
)


def _archive(path: Path, *, ragged=False, validation_csv=False, blank_field=False):
    root = "04_Calibration_Set_Cases_1_2_3/Case_1_Strain_R-1/Exp_1_1H"
    with ZipFile(path, "w") as archive:
        for filename in TABLE_FILENAMES:
            header = "a,b\n"
            body = (
                "1\n"
                if ragged and filename == "For_FEM.csv"
                else "1,\n3,4"
                if blank_field and filename == "For_FEM.csv"
                else "1,2\n3,4"
            )
            archive.writestr(f"{root}/{filename}", header + body)
        archive.writestr(f"{root}/Protocol_LCF.pdf", b"authored fixture")
        archive.writestr("05_Validation_Targets_Cases_4_5/targets.pdf", b"authored fixture")
        if validation_csv:
            archive.writestr("05_Validation_Targets_Cases_4_5/outcomes.csv", "x\n1\n")


def test_archive_audit_preserves_experiment_and_table_hierarchy(tmp_path):
    path = tmp_path / "fixture.zip"
    _archive(path)
    result = audit_fabest_lcf_archive(path)
    assert result.calibration_experiment_count == 1
    assert result.calibration_table_count == 4
    assert result.unsafe_member_paths == ()
    assert result.duplicate_member_paths == ()
    assert result.encrypted_members == ()
    experiment = result.experiments[0]
    assert experiment.experiment_id == "Exp_1_1H"
    assert experiment.case_id == 1
    assert experiment.control_mode == "strain_controlled"
    assert experiment.physical_specimen_id is None
    assert set(experiment.table_members) == set(TABLE_FILENAMES.values())
    assert {table.data_rows for table in result.tables} == {2}


def test_archive_audit_rejects_validation_outcome_table(tmp_path):
    path = tmp_path / "fixture.zip"
    _archive(path, validation_csv=True)
    with pytest.raises(ValueError, match="unexpectedly contains CSV outcomes"):
        audit_fabest_lcf_archive(path)


def test_numeric_iterator_requires_reviewed_header_and_shape(tmp_path):
    path = tmp_path / "fixture.zip"
    _archive(path)
    member = "04_Calibration_Set_Cases_1_2_3/Case_1_Strain_R-1/Exp_1_1H/For_FEM.csv"
    assert list(iter_fabest_lcf_numeric_rows(path, member=member, expected_header=("a", "b"))) == [
        (2, (1.0, 2.0)),
        (3, (3.0, 4.0)),
    ]
    with pytest.raises(ValueError, match="header differs"):
        list(iter_fabest_lcf_numeric_rows(path, member=member, expected_header=("x", "y")))


def test_numeric_iterator_rejects_ragged_rows(tmp_path):
    path = tmp_path / "fixture.zip"
    _archive(path, ragged=True)
    member = "04_Calibration_Set_Cases_1_2_3/Case_1_Strain_R-1/Exp_1_1H/For_FEM.csv"
    with pytest.raises(ValueError, match="ragged CSV row"):
        list(iter_fabest_lcf_numeric_rows(path, member=member, expected_header=("a", "b")))


def test_numeric_iterator_can_preserve_blank_cells_without_imputation(tmp_path):
    path = tmp_path / "fixture.zip"
    _archive(path, blank_field=True)
    member = "04_Calibration_Set_Cases_1_2_3/Case_1_Strain_R-1/Exp_1_1H/For_FEM.csv"
    with pytest.raises(ValueError, match="nonnumeric CSV value"):
        list(iter_fabest_lcf_numeric_rows(path, member=member, expected_header=("a", "b")))
    rows = list(
        iter_fabest_lcf_numeric_rows(
            path,
            member=member,
            expected_header=("a", "b"),
            preserve_empty_fields=True,
        )
    )
    assert rows == [(2, (1.0, None)), (3, (3.0, 4.0))]
