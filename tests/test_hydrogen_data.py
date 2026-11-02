import csv
import math

import pytest

from matintegrity.hydrogen_data import ELEMENTS, read_he_austenite


def write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def fixture(folder):
    base = dict(
        record_id="one",
        source_id="authored-source",
        alloy="synthetic",
        heat="",
        material_family="synthetic",
        zone="weld metal",
        hydrogen_exposure="gaseous in-situ",
        h2_pressure_MPa=10.0,
        hydrogen_content_wppm=2.0,
        charging_time_h=1.0,
        test_temperature_K=300.0,
        strain_rate_per_s=1e-5,
        property_name="elongation",
        property_reference=20.0,
        property_h2=24.0,
        relative_ratio=1.2,
        reference_environment="air",
        verified="no",
        composition_basis="heat_analysis",
        derived="relative_ratio",
        derived_assumptions="N assumed zero only in compiler-derived fields",
    )
    base.update({e + "_wt_pct": "" for e in ELEMENTS})
    base["Cr_wt_pct"] = 18.0
    rows = [
        base,
        dict(
            base,
            record_id="two",
            property_name="plastic strain to failure",
            property_reference=1.5,
            property_h2=0.9,
            relative_ratio=0.6,
        ),
        dict(base, record_id="three", Cr_wt_pct=19.0),
    ]
    write(folder / "he_austenite_v1.0.csv", rows)
    comp = dict(comp_key="composition-one", **{e: "" for e in ELEMENTS})
    comp["Cr"] = 18.0
    write(folder / "compositions.csv", [comp])
    links = [dict(record_id=r["record_id"], comp_key="composition-one") for r in rows]
    write(folder / "record_composition_map.csv", links)
    return rows, links


def test_reader_preserves_units_improvement_missing_chemistry_and_conflicts(tmp_path):
    fixture(tmp_path)
    f = read_he_austenite(tmp_path)
    assert len(f) == 3
    assert f.reference_property_SI.iloc[0] == 0.2
    assert f.hydrogen_property_SI.iloc[0] == 0.24
    assert f.reported_retention_ratio.iloc[0] == 1.2
    assert math.isnan(f.reference_property_SI.iloc[1])
    assert f.property_unit.iloc[1] == "unresolved"
    assert f.reported_gas_pressure_Pa.iloc[0] == 1e7
    assert f.charging_duration_s.iloc[0] == 3600.0
    assert f.hydrogen_mass_fraction.iloc[0] == 2e-6
    assert f.reported_composition_mass_fraction.iloc[0] == {"Cr": 0.18}
    assert f.reported_composition_mass_fraction.iloc[2] == {"Cr": 0.19}
    assert f.linked_composition_mass_fraction.iloc[2] == {"Cr": 0.18}
    assert f.composition_link_consistent.tolist() == [True, True, False]
    assert not f.compiler_verified.any()
    assert f.gas_pressure_basis.str.contains("unresolved").all()


def test_coincident_values_do_not_merge_physical_specimens(tmp_path):
    rows, links = fixture(tmp_path)
    rows[2] = dict(rows[0], record_id="three")
    write(tmp_path / "he_austenite_v1.0.csv", rows)
    f = read_he_austenite(tmp_path)
    assert len(f) == 3 and f.coincident_reported_condition_and_values.tolist() == [True, False, True]
    assert f.specimen_independence.eq("not_established_by_compilation").all()
    links[0]["comp_key"] = "absent"
    write(tmp_path / "record_composition_map.csv", links)
    with pytest.raises(ValueError, match="unresolved composition map"):
        read_he_austenite(tmp_path)


def test_ratio_only_record_does_not_fabricate_absolute_properties(tmp_path):
    rows, _ = fixture(tmp_path)
    rows[0].update(property_reference="", property_h2="", verified="yes")
    write(tmp_path / "he_austenite_v1.0.csv", rows)
    f = read_he_austenite(tmp_path)
    assert f.reported_retention_ratio.iloc[0] == 1.2
    assert math.isnan(f.arithmetic_retention_ratio.iloc[0]) and math.isnan(f.reference_property_SI.iloc[0])
    assert f.compiler_verified.iloc[0]
