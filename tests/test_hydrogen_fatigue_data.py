from __future__ import annotations

import hashlib

import pytest
from openpyxl import Workbook

from matintegrity.hydrogen_fatigue_data import (
    HYDROGEN_FATIGUE_SERIES_COLUMNS,
    audit_hymatbase_hydrogen_fatigue,
    read_hymatbase_hydrogen_fatigue,
)


def _workbook(tmp_path, *, partial_pair=False, formula_point=False, bad_header=False):
    path = tmp_path / "hydrogen-fatigue.xlsx"
    workbook = Workbook()
    material = workbook.active
    material.title = "Material"
    material["A1"] = "4130X"
    material["A3"] = " vessel"
    material["A4"] = "Q&T"
    material["F9"] = "(tempered martensite)"
    environment = workbook.create_sheet("Environment")
    environment["D7"] = "Temperature (\u02daC)"
    environment["D8"] = "Pressure (MPa)"
    environment["D9"] = "test environment"
    environment["F7"] = "RT"
    environment["F8"] = 45
    environment["F9"] = "H2"
    workbook.create_sheet("Mechanical Properties-Fracture")
    fatigue = workbook.create_sheet("Mechanical Properties-Fatigue")
    for index, (delta_column, growth_column) in enumerate(HYDROGEN_FATIGUE_SERIES_COLUMNS):
        fatigue[f"{delta_column}12"] = "bad" if bad_header and index == 0 else "∆K\n(MPa m1/2)"
        fatigue[f"{growth_column}12"] = "da/dN\n(m/cycle)"
        fatigue[f"{growth_column}6"] = "CL"
        fatigue[f"{growth_column}7"] = "ASTM E647"
        fatigue[f"{growth_column}8"] = 0.1 if index < 2 else 0.5
        fatigue[f"{growth_column}9"] = 0.1 if index % 2 == 0 else 1.0
        fatigue[f"{delta_column}14"] = 10.0 + index
        fatigue[f"{growth_column}14"] = 1e-8 * (index + 1)
        fatigue[f"{delta_column}15"] = 11.0 + index
        fatigue[f"{growth_column}15"] = 2e-8 * (index + 1)
    if partial_pair:
        fatigue["F15"] = None
    if formula_point:
        fatigue["F15"] = "=1E-8+1E-8"
    # The provider file uses a chartsheet. A plain sheet avoids an openpyxl
    # empty-chartsheet round-trip defect while exercising the same name contract.
    workbook.create_sheet("fatigue plot")
    workbook.save(path)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path, digest, *, pressure=4.5e6, acknowledge=True):
    return read_hymatbase_hydrogen_fatigue(
        path,
        expected_sha256=digest,
        source_group_id="source-group",
        physical_material_condition_id="4130X-QT-provider-condition",
        provider_record_pressure_Pa=pressure,
        provider_record_temperature_K=298.15,
        acknowledge_pressure_conflict=acknowledge,
    )


def test_reader_preserves_series_conditions_and_converts_delta_k(tmp_path):
    path, digest = _workbook(tmp_path)
    series, points = _read(path, digest)
    assert len(series) == 4
    assert len(points) == 8
    assert [item.point_count for item in series] == [2, 2, 2, 2]
    assert series[0].workbook_pressure_Pa == 45e6
    assert series[0].provider_record_pressure_Pa == 4.5e6
    assert series[0].pressure_reconciliation_status == "record_conflicts_with_workbook"
    assert series[0].stress_ratio == 0.1
    assert series[0].frequency_Hz == 0.1
    assert points[0].provider_row_number == 14
    assert points[0].delta_k_Pa_sqrt_m == 10e6
    assert points[0].crack_growth_m_cycle == 1e-8
    assert points[0].physical_specimen_id is None


def test_reader_requires_explicit_pressure_conflict_acknowledgement(tmp_path):
    path, digest = _workbook(tmp_path)
    with pytest.raises(ValueError, match="pressure conflict must be acknowledged"):
        _read(path, digest, acknowledge=False)


def test_reader_does_not_accept_spurious_conflict_acknowledgement(tmp_path):
    path, digest = _workbook(tmp_path)
    with pytest.raises(ValueError, match="without a detected conflict"):
        _read(path, digest, pressure=45e6, acknowledge=True)


def test_reader_rejects_hash_header_formula_and_unpaired_point(tmp_path):
    path, digest = _workbook(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        _read(path, "0" * 64)
    path, digest = _workbook(tmp_path, bad_header=True)
    with pytest.raises(ValueError, match="headers differ"):
        _read(path, digest)
    path, digest = _workbook(tmp_path, formula_point=True)
    with pytest.raises(ValueError, match="rejects formula"):
        _read(path, digest)
    path, digest = _workbook(tmp_path, partial_pair=True)
    with pytest.raises(ValueError, match="one missing"):
        _read(path, digest)


def test_audit_reports_aggregates_without_pointwise_rows(tmp_path):
    path, digest = _workbook(tmp_path)
    audit = audit_hymatbase_hydrogen_fatigue(
        path,
        expected_sha256=digest,
        source_group_id="source-group",
        physical_material_condition_id="condition",
        provider_record_pressure_Pa=4.5e6,
        provider_record_temperature_K=298.15,
        acknowledge_pressure_conflict=True,
    )
    assert audit.series_count == 4
    assert audit.point_count == 8
    assert audit.formula_cell_count == 0
    assert audit.delta_k_minimum_Pa_sqrt_m == 10e6
    assert audit.delta_k_maximum_Pa_sqrt_m == 14e6
    assert audit.pressure_reconciliation_status == "record_conflicts_with_workbook"
