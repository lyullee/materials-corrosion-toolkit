import zipfile

import pytest

from matintegrity.fracture_toughness_data import (
    ARTICLE_REFERENCE_CATALOG,
    _assign_condition_groups,
    read_fracture_toughness_temperature,
    resolve_article_source_group,
)

openpyxl = pytest.importorskip("openpyxl")
pd = pytest.importorskip("pandas")


def source_archive(tmp_path, *, invalid_flags=False):
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)
    headers = ["No.", "wt%", "K", "MPa", "CT", "SEB", "PCCv", "W", "B", "a", "MPam1/2", "Material"]
    rows = {
        "Table A.2": [
            [1, 0.12, -100, 599.2, 0, 1, 0, 30, 15, 15, 101.3, "S460M"],
            [2, 0.15, -120, 941.1, 1, 0, 0, 50, 25, 25, 65.7, "S690Q"],
        ],
        "Table A.3": [[1, 0.22, -160, 777.2, 0, 0, 1, 10, 10, 5, 69.4, "SQV2A"]],
    }
    if invalid_flags:
        rows["Table A.3"][0][4:7] = [1, 1, 0]
    for title, values in rows.items():
        sheet = workbook.create_sheet(title)
        for column, value in enumerate(headers, start=2):
            sheet.cell(4, column, value)
        for row_number, row in enumerate(values, start=5):
            for column, value in enumerate(row, start=2):
                sheet.cell(row_number, column, value)
    xlsx = tmp_path / "source.xlsx"
    workbook.save(xlsx)
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as target:
        target.write(xlsx, "provider/source.xlsx")
    return archive


def test_reader_preserves_partitions_and_uses_reviewed_article_temperature_unit(tmp_path):
    frame = read_fracture_toughness_temperature(source_archive(tmp_path))
    assert frame.source_partition.tolist() == ["training", "training", "test"]
    assert frame.observation_id.tolist() == ["training:1", "training:2", "test:1"]
    assert frame.specimen_type.tolist() == ["SEB", "CT", "PCCv"]
    assert frame.temperature_K.tolist() == pytest.approx([173.15, 153.15, 113.15])
    assert frame.temperature_unit_basis.unique().tolist() == ["article_degC"]
    assert frame.W_m.tolist() == pytest.approx([0.03, 0.05, 0.01])
    assert frame.dimension_unit_basis.unique().tolist() == ["article_mm"]
    assert frame.condition_group_status.unique().tolist() == ["geometry_condition_only"]
    assert frame.condition_group_id.nunique() == 3
    assert frame.reported_temperature_unit_label.unique().tolist() == ["K"]
    assert frame.physical_specimen_id.isna().all()
    assert frame.reported_KJc_Pa_sqrt_m.tolist() == pytest.approx([101.3e6, 65.7e6, 69.4e6])
    assert frame.attrs["workbook_formula_execution"] is False
    assert frame.article_source_group_status.tolist() == [
        "article_table_exact",
        "article_table_exact",
        "unresolved",
    ]
    assert frame.underlying_literature_id.isna().all()


def test_article_source_groups_preserve_exact_probable_unresolved_and_mismatch_states():
    exact = resolve_article_source_group("A508C", 0.19)
    probable = resolve_article_source_group("S55CFY2012", 0.55)
    unresolved = resolve_article_source_group("SS400", 0.12)
    mismatch = resolve_article_source_group("A533B", 0.21)

    assert exact["article_source_group_id"].endswith("#ref-16")
    assert exact["article_source_group_status"] == "article_table_exact"
    assert probable["article_source_group_id"] == "doi:10.1016/j.engfailanal.2020.104458#ref-8"
    assert probable["article_source_group_status"] == "probable_name_variant"
    assert probable["article_source_material_label"] == "S55C"
    assert probable["article_reference_bibliographic_id"] == "doi:10.1177/1687814019870897"
    assert probable["article_reference_observation_rights_status"] == "unresolved"
    assert unresolved["article_source_group_id"] is None
    assert unresolved["article_source_group_status"] == "unresolved"
    assert mismatch["article_source_group_id"] is None
    assert mismatch["article_source_group_status"] == "material_condition_mismatch"


def test_article_reference_catalog_separates_identity_publication_license_and_observation_rights():
    assert set(ARTICLE_REFERENCE_CATALOG) == {
        "ref-6",
        "ref-8",
        "ref-16",
        "ref-17",
        "ref-18",
        "ref-19",
        "ref-20",
        "ref-21",
        "ref-22",
    }
    assert ARTICLE_REFERENCE_CATALOG["ref-6"]["publication_license_id"] == "CC-BY-NC-ND-4.0"
    assert ARTICLE_REFERENCE_CATALOG["ref-16"]["identity_status"] == "bibliography_only"
    assert ARTICLE_REFERENCE_CATALOG["ref-17"]["bibliographic_id"] is None
    assert {record["observation_rights_status"] for record in ARTICLE_REFERENCE_CATALOG.values()} == {
        "unresolved"
    }


def test_reviewed_unit_overrides_produce_si_values(tmp_path):
    frame = read_fracture_toughness_temperature(
        source_archive(tmp_path), temperature_unit_override="degC", dimension_unit_override="mm"
    )
    assert frame.temperature_K.tolist() == pytest.approx([173.15, 153.15, 113.15])
    assert frame.temperature_unit_basis.unique().tolist() == ["degC"]
    assert frame.W_m.tolist() == pytest.approx([0.03, 0.05, 0.01])
    assert frame.carbon_mass_fraction.tolist() == pytest.approx([0.0012, 0.0015, 0.0022])


def test_article_dimension_review_can_be_disabled_without_inventing_si_geometry(tmp_path):
    frame = read_fracture_toughness_temperature(
        source_archive(tmp_path), apply_article_dimension_review=False
    )
    assert frame[["W_m", "B_m", "a_m"]].isna().all().all()
    assert frame.dimension_unit_basis.unique().tolist() == ["unresolved"]
    assert frame.condition_group_id.isna().all()
    assert frame.condition_group_status.unique().tolist() == ["unresolved_dimension_unit"]


def test_condition_groups_merge_close_geometry_without_claiming_specimen_identity():
    frame = pd.DataFrame(
        {
            "material_label": ["steel-a", "steel-a", "steel-a", "steel-b"],
            "specimen_type": ["SEB", "SEB", "SEB", "SEB"],
            "W_m": [0.03000, 0.03005, 0.06000, 0.03000],
            "B_m": [0.01500, 0.01502, 0.03000, 0.01500],
        }
    )
    _assign_condition_groups(frame, relative_tolerance=0.01, absolute_tolerance_m=1e-4)
    assert frame.condition_group_id.tolist() == [
        "steel-a|SEB|geometry-01",
        "steel-a|SEB|geometry-01",
        "steel-a|SEB|geometry-02",
        "steel-b|SEB|geometry-01",
    ]
    assert not frame.condition_group_physical_independence_reviewed.any()


def test_default_condition_group_tolerance_consolidates_nominal_geometry_variation(tmp_path):
    archive = source_archive(tmp_path)
    frame = read_fracture_toughness_temperature(archive)
    frame.loc[0, ["material_label", "specimen_type", "W_m", "B_m"]] = [
        "steel-a",
        "CT",
        0.02477,
        0.01016,
    ]
    frame.loc[1, ["material_label", "specimen_type", "W_m", "B_m"]] = [
        "steel-a",
        "CT",
        0.02540,
        0.01016,
    ]
    _assign_condition_groups(
        frame,
        relative_tolerance=frame.attrs["condition_group_relative_tolerance"],
        absolute_tolerance_m=frame.attrs["condition_group_absolute_tolerance_m"],
    )
    assert frame.loc[0, "condition_group_id"] == frame.loc[1, "condition_group_id"]
    assert frame.attrs["condition_group_relative_tolerance"] == 0.03


def test_inconsistent_kelvin_override_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="nonpositive absolute temperature"):
        read_fracture_toughness_temperature(source_archive(tmp_path), temperature_unit_override="K")


def test_non_one_hot_specimen_type_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="one-hot"):
        read_fracture_toughness_temperature(source_archive(tmp_path, invalid_flags=True))


@pytest.mark.parametrize(
    "temperature, dimension",
    [("C", None), (None, "cm")],
)
def test_unknown_unit_overrides_are_rejected(tmp_path, temperature, dimension):
    with pytest.raises(ValueError, match="override"):
        read_fracture_toughness_temperature(
            source_archive(tmp_path),
            temperature_unit_override=temperature,
            dimension_unit_override=dimension,
        )
