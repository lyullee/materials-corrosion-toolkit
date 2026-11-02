import csv
import hashlib
import io
import zipfile

import pytest

import matintegrity.aquasoldb_data as aquasoldb_data
from matintegrity.aquasoldb_data import (
    SOLUBILITY_COLUMNS,
    AquaSolDBCo2SolubilityObservation,
    AquaSolDBCo2SolubilityQuery,
    AquaSolDBFixedFugacityComparisonInput,
    compare_aquasoldb_to_fixed_fugacity_model,
    iter_aquasoldb_co2_solubility,
    select_aquasoldb_co2_records,
)
from matintegrity.contracts import Evidence
from matintegrity.models.co2_fixed_fugacity_equilibrium import Co2HenrySolubilityRecord


def _archive(tmp_path, *, columns=SOLUBILITY_COLUMNS, rows=None, member="root/csv/solubility.csv"):
    values = rows or [
        {
            "point_id": "fixture-1",
            "gas": "CO2",
            "temperature_K": "298.15",
            "pressure_MPa": "0.1",
            "pressure_basis": "partial_CO2",
            "salt": "none",
            "salt_molality": "",
            "salt_composition": "",
            "m_Na": "0",
            "m_Cl": "0",
            "m_K": "0",
            "m_Ca": "0",
            "m_Mg": "0",
            "m_SO4": "0",
            "solubility_mol_per_kgw": "0.033",
            "status": "measured",
            "status_reason": "fixture",
            "flags": "",
            "method": "fixture_method",
            "source_id": "fixture-source-1",
        }
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    writer.writerows(values)
    path = tmp_path / "fixture.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, buffer.getvalue().encode("utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, digest


def test_reader_returns_only_co2_rows_and_keeps_source_limits(tmp_path, monkeypatch):
    co2 = {
        "point_id": "fixture-1",
        "gas": "CO2",
        "temperature_K": "298.15",
        "pressure_MPa": "0.1",
        "pressure_basis": "partial_CO2",
        "salt": "none",
        "salt_molality": "",
        "salt_composition": "",
        "m_Na": "0",
        "m_Cl": "0",
        "m_K": "0",
        "m_Ca": "0",
        "m_Mg": "0",
        "m_SO4": "0",
        "solubility_mol_per_kgw": "0.033",
        "status": "measured",
        "status_reason": "fixture",
        "flags": "replicate;suspect_value",
        "method": "fixture_method",
        "source_id": "fixture-source-1",
    }
    other = dict(co2, point_id="fixture-2", gas="H2")
    path, digest = _archive(tmp_path, rows=[co2, other])
    monkeypatch.setattr(aquasoldb_data, "PINNED_ARCHIVE_SHA256", digest)

    result = list(iter_aquasoldb_co2_solubility(path))

    assert len(result) == 1
    assert result[0].solubility_mol_per_kg_water == pytest.approx(0.033)
    assert result[0].flags == ("replicate", "suspect_value")
    assert result[0].source_id == "fixture-source-1"
    assert result[0].source_specific_original_paper_citation_required is True
    assert result[0].henry_coefficient_derived is False
    assert result[0].corrosion_calibration_ready is False


def test_reader_rejects_archive_digest_and_schema_mismatch(tmp_path, monkeypatch):
    path, digest = _archive(tmp_path)
    monkeypatch.setattr(aquasoldb_data, "PINNED_ARCHIVE_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="SHA-256"):
        list(iter_aquasoldb_co2_solubility(path))
    path, digest = _archive(tmp_path, columns=SOLUBILITY_COLUMNS[:-1])
    monkeypatch.setattr(aquasoldb_data, "PINNED_ARCHIVE_SHA256", digest)
    with pytest.raises(ValueError, match="schema"):
        list(iter_aquasoldb_co2_solubility(path))


def test_reader_preserves_missing_condition_values_as_missing(tmp_path, monkeypatch):
    row = {
        "point_id": "fixture-1",
        "gas": "CO2",
        "temperature_K": "",
        "pressure_MPa": "",
        "pressure_basis": "partial_CO2",
        "salt": "none",
        "salt_molality": "",
        "salt_composition": "",
        "m_Na": "",
        "m_Cl": "",
        "m_K": "",
        "m_Ca": "",
        "m_Mg": "",
        "m_SO4": "",
        "solubility_mol_per_kgw": "0.033",
        "status": "measured",
        "status_reason": "fixture",
        "flags": "",
        "method": "fixture_method",
        "source_id": "fixture-source-1",
    }
    path, digest = _archive(tmp_path, rows=[row])
    monkeypatch.setattr(aquasoldb_data, "PINNED_ARCHIVE_SHA256", digest)
    record = next(iter_aquasoldb_co2_solubility(path))
    assert record.temperature_K is None
    assert record.pressure_MPa is None
    assert record.solubility_mol_per_kg_water == pytest.approx(0.033)


def test_reader_rejects_unsafe_member_paths(tmp_path, monkeypatch):
    path, digest = _archive(tmp_path, member="root/../csv/solubility.csv")
    monkeypatch.setattr(aquasoldb_data, "PINNED_ARCHIVE_SHA256", digest)
    with pytest.raises(ValueError, match="unsafe"):
        list(iter_aquasoldb_co2_solubility(path))


def _observation(point_id="p1", *, pressure_basis="partial_CO2", flags=()):
    return AquaSolDBCo2SolubilityObservation(
        source_archive_sha256="a" * 64,
        point_id=point_id,
        source_id="source-1",
        temperature_K=298.15,
        pressure_MPa=0.1,
        pressure_basis=pressure_basis,
        salt="none",
        solubility_mol_per_kg_water=0.05,
        status="measured",
        flags=flags,
        method="synthetic fixture",
        evidence=(
            Evidence(
                source_id="dataset",
                origin="synthetic",
                citation="synthetic test fixture",
            ),
        ),
    )


def test_query_applies_explicit_filters_and_rejects_silent_truncation():
    clean = _observation("clean")
    flagged = _observation("flagged", flags=("replicate",))
    query = AquaSolDBCo2SolubilityQuery(
        temperature_range_K=(298.15, 298.15), pressure_basis="partial_CO2", maximum_records=1
    )
    assert select_aquasoldb_co2_records((clean, flagged), query) == (clean,)
    with pytest.raises(ValueError, match="maximum_records"):
        select_aquasoldb_co2_records((clean, _observation("clean-2")), query)


def test_independent_henry_fugacity_comparison_requires_review_and_preserves_lineage():
    digest = "b" * 64
    evidence = (Evidence(source_id="provider", origin="user_declared", citation="user-supplied record"),)
    henry = Co2HenrySolubilityRecord(
        temperature_K=298.15,
        coefficient_mol_L_Pa=1e-6,
        convention="aqueous_CO2star_concentration_over_gas_fugacity",
        solvent_composition_sha256=digest,
        provider_id="caller-henry",
        provider_revision="r1",
        configuration_digest=digest,
        record_digest=digest,
        evidence=evidence,
    )
    values = dict(
        observation=_observation(),
        henry=henry,
        co2_fugacity_Pa=100_000.0,
        fugacity_temperature_K=298.15,
        fugacity_provider_id="caller-eos",
        fugacity_provider_revision="r1",
        fugacity_configuration_digest=digest,
        fugacity_record_digest=digest,
        solvent_composition_sha256=digest,
        solvent_water_mass_concentration_kg_per_L=2.0,
        expanded_comparison_uncertainty_mol_L=0.01,
        expanded_comparison_uncertainty_basis="declared combined uncertainty",
        comparison_review_id="review-1",
        observation_record_reviewed=True,
        pressure_and_fugacity_basis_reviewed=True,
        solvent_composition_and_water_mass_concentration_reviewed=True,
        Henry_record_independence_reviewed=True,
        Henry_convention_and_activity_basis_reviewed=True,
        original_source_citation_and_rights_reviewed=True,
        observation_flags_reviewed=True,
        evidence=evidence,
    )
    result = compare_aquasoldb_to_fixed_fugacity_model(AquaSolDBFixedFugacityComparisonInput(**values))
    assert result.values["measured_co2_concentration_mol_L"] == pytest.approx(0.1)
    assert result.values["predicted_co2_concentration_mol_L"] == pytest.approx(0.1)
    assert result.values["absolute_residual_over_declared_expanded_uncertainty"] == pytest.approx(0.0)
    assert result.values["original_source_id"] == "source-1"

    missing_review = AquaSolDBFixedFugacityComparisonInput(
        **(values | {"Henry_record_independence_reviewed": False})
    )
    assert compare_aquasoldb_to_fixed_fugacity_model(missing_review).status == "needs_data"
    total_pressure = AquaSolDBFixedFugacityComparisonInput(
        **(values | {"observation": _observation(pressure_basis="total_pressure")})
    )
    assert compare_aquasoldb_to_fixed_fugacity_model(total_pressure).status == "needs_data"
