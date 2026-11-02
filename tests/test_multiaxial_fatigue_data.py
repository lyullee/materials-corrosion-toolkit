from pathlib import Path

import pytest

from matintegrity.multiaxial_fatigue_data import read_ecp_multiaxial_fatigue


def write_pair(folder: Path, stem: str, fs: str, swt: str):
    (folder / f"FS_{stem}.txt").write_text(fs, encoding="utf-8")
    (folder / f"SWT_{stem}.txt").write_text(swt, encoding="utf-8")


def test_loader_deduplicates_experimental_life_but_preserves_method_outputs(tmp_path):
    write_pair(
        tmp_path,
        "MULTI_BLUNT_PSI90_LAMB1_R-1",
        "100000\t0.004\t90000\n200000\t0.003\t180000\n",
        "100000\t0.8\t110000\n200000\t0.6\t210000\n",
    )
    loaded = read_ecp_multiaxial_fatigue(tmp_path)
    observations = loaded["experimental_observations"]
    processed = loaded["processed_method_rows"]
    assert len(observations) == 2
    assert len(processed) == 4
    assert observations.reported_cycles_to_failure.tolist() == [100000.0, 200000.0]
    assert set(processed.method) == {"FS", "SWT"}
    assert processed.independent_prediction_validation.eq(False).all()
    assert observations.physical_specimen_id.isna().all()
    assert observations.physical_specimen_independence_reviewed.eq(False).all()


def test_filename_conditions_are_preserved_without_expanding_provider_codes(tmp_path):
    write_pair(tmp_path, "ASS_SHARP_R05", "1000\t0.1\t900\n", "1000\t0.2\t1100\n")
    row = read_ecp_multiaxial_fatigue(tmp_path)["configurations"].iloc[0]
    assert row.provider_load_code == "ASS"
    assert row.specimen_geometry_code == "SHARP"
    assert row.stress_ratio == pytest.approx(0.5)
    assert row.phase_angle_deg is None
    assert row.biaxiality_ratio is None


@pytest.mark.parametrize(
    ("fs", "swt", "message"),
    [
        ("1000\t0.1\t900\n", "2000\t0.2\t1100\n", "experimental lives differ"),
        ("1000\t0.1\t900\n2000\t0.2\t1800\n", "1000\t0.2\t1100\n", "row count differs"),
    ],
)
def test_pair_mismatch_is_rejected(tmp_path, fs, swt, message):
    write_pair(tmp_path, "TOR_BLUNT_R01", fs, swt)
    with pytest.raises(ValueError, match=message):
        read_ecp_multiaxial_fatigue(tmp_path)


def test_missing_method_counterpart_is_rejected(tmp_path):
    (tmp_path / "FS_ASS_BLUNT_R-1.txt").write_text("1000\t0.1\t900\n", encoding="utf-8")
    with pytest.raises(ValueError, match="paired FS/SWT files required"):
        read_ecp_multiaxial_fatigue(tmp_path)


@pytest.mark.parametrize(
    "content",
    ["1000\t0.1\n", "1000\tbad\t900\n", "1000\t-0.1\t900\n", ""],
)
def test_malformed_rows_are_rejected(tmp_path, content):
    write_pair(tmp_path, "ASS_BLUNT_R-1", content, content)
    with pytest.raises(ValueError):
        read_ecp_multiaxial_fatigue(tmp_path)


def test_unknown_filename_is_rejected(tmp_path):
    (tmp_path / "FS_UNKNOWN.txt").write_text("1000\t0.1\t900\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unrecognized"):
        read_ecp_multiaxial_fatigue(tmp_path)
