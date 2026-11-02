import csv
import hashlib

import pytest
from openpyxl import Workbook

from matintegrity.models.corrosion import (
    CorrosionRateModelOutputWallLossScenario,
    SimulationRateWallLossScenario,
    corrosion_rate_model_output_wall_loss_scenario,
    simulation_rate_wall_loss_scenario,
    wet_co2_simulation_row_to_projection_row,
)
from matintegrity.wet_co2_data import (
    ASSOCIATED_PAPER_UNIT_BASIS_ID,
    HEADERS,
    JULIAN_YEAR_SECONDS,
    SIMULATION_UNIT_TABLE,
    WetCo2LiteratureEvidenceRow,
    WetCo2LiteratureFieldMap,
    WetCo2SimulationGridSummary,
    audit_wet_co2_literature_row,
    match_wet_co2_simulation_source,
    read_unresolved_wet_co2_compilation,
    read_wet_co2_simulation_grid,
    summarize_wet_co2_simulation_grid,
    wet_co2_si_observation_from_compilation_row,
)


def _fixture(tmp_path, *, headers=HEADERS, corrosion_rate="3.2"):
    path = tmp_path / "CO2.csv"
    row = ["30", "1.2", "1", "", "40", "", "4", corrosion_rate]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(headers)
        writer.writerow(row)
    return path


def _matching_simulation_fixtures(
    tmp_path, *, mismatch=False, units_mismatch=False, invalid_efficiency=False
):
    csv_path = tmp_path / "CO2.csv"
    workbook_path = tmp_path / "simulation.xlsx"
    values = [(30.0 + index / 100.0, 1.2, 1.0, 60.0, 40.0, 3.0, 4.0, 3.2) for index in range(243)]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(HEADERS)
        writer.writerows(values)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(HEADERS)
    for value in values:
        sheet.append(value)
    for row, (parameter, unit) in enumerate(SIMULATION_UNIT_TABLE, start=3):
        sheet.cell(row=row, column=10, value=parameter)
        sheet.cell(row=row, column=11, value=unit)
    if mismatch:
        sheet.cell(row=100, column=8, value=9.9)
    if units_mismatch:
        sheet.cell(row=3, column=11, value="kPa")
    if invalid_efficiency:
        sheet.cell(row=2, column=5, value=120.0)
    workbook.save(workbook_path)
    return csv_path, workbook_path


def test_reader_preserves_raw_values_missingness_and_unresolved_semantics(tmp_path):
    record = read_unresolved_wet_co2_compilation(_fixture(tmp_path), require_pinned_hash=False)[0]
    assert record.provider_source_row == 2
    assert record.raw_temperature == 30.0
    assert record.raw_internal_pressure is None
    assert record.raw_shear_stress is None
    assert record.raw_corrosion_rate == 3.2
    assert record.provider_units_status == "not_supplied"
    assert record.provider_source_group_id is None
    assert record.physical_specimen_id is None
    assert record.mechanistic_calibration_ready is False


def test_reader_requires_pinned_revision_by_default(tmp_path):
    with pytest.raises(ValueError, match="hash differs"):
        read_unresolved_wet_co2_compilation(_fixture(tmp_path))


def test_reader_refuses_schema_drift_and_nonfinite_values(tmp_path):
    with pytest.raises(ValueError, match="schema"):
        read_unresolved_wet_co2_compilation(
            _fixture(tmp_path, headers=tuple(reversed(HEADERS))), require_pinned_hash=False
        )
    with pytest.raises(ValueError, match="finite"):
        read_unresolved_wet_co2_compilation(
            _fixture(tmp_path, corrosion_rate="nan"), require_pinned_hash=False
        )


def test_associated_paper_unit_basis_converts_to_si_without_promoting_provenance(tmp_path):
    record = read_unresolved_wet_co2_compilation(_fixture(tmp_path), require_pinned_hash=False)[0]
    converted = wet_co2_si_observation_from_compilation_row(
        record, reviewed_unit_basis_id=ASSOCIATED_PAPER_UNIT_BASIS_ID
    )
    assert converted.source_file_units_status == "not_supplied"
    assert converted.unit_basis_reviewed is True
    assert converted.temperature_k == pytest.approx(303.15)
    assert converted.flow_velocity_m_s == pytest.approx(1.2)
    assert converted.co2_pressure_pa == pytest.approx(100_000.0)
    assert converted.internal_pressure_pa is None
    assert converted.corrosion_inhibitor_efficiency_fraction == pytest.approx(0.4)
    assert converted.shear_stress_pa is None
    assert converted.ph == pytest.approx(4.0)
    assert converted.corrosion_rate_m_s == pytest.approx(3.2e-3 / JULIAN_YEAR_SECONDS)
    assert converted.provider_source_group_id is None
    assert converted.row_level_source_mapping_status == "not_provided_by_associated_paper"
    assert converted.empirical_calibration_ready is False
    assert converted.mechanistic_calibration_ready is False


def test_associated_paper_unit_basis_requires_exact_opt_in(tmp_path):
    record = read_unresolved_wet_co2_compilation(_fixture(tmp_path), require_pinned_hash=False)[0]
    with pytest.raises(ValueError, match="requires the reviewed"):
        wet_co2_si_observation_from_compilation_row(record, reviewed_unit_basis_id="doi:unreviewed#table")


def test_simulation_workbook_exactly_crosswalks_243_compilation_rows(tmp_path):
    csv_path, workbook_path = _matching_simulation_fixtures(tmp_path)
    rows = read_unresolved_wet_co2_compilation(csv_path, require_pinned_hash=False)
    matches = match_wet_co2_simulation_source(rows, workbook_path, require_pinned_hash=False)
    assert len(matches) == 243
    assert matches[0].compilation_provider_source_row == 2
    assert matches[0].source_provider_row == 2
    assert matches[-1].compilation_provider_source_row == 244
    assert matches[-1].source_provider_row == 244
    assert matches[0].provider_data_type == "simulated_model_output"
    assert matches[0].source_group_id == "doi:10.17632/4nydhxjymw.1"
    assert matches[0].independent_physical_observation is False
    assert matches[0].physical_corrosion_calibration_ready is False
    assert matches[0].public_surrogate_release_review_required is True


def test_simulation_crosswalk_refuses_value_mismatch(tmp_path):
    csv_path, workbook_path = _matching_simulation_fixtures(tmp_path, mismatch=True)
    rows = read_unresolved_wet_co2_compilation(csv_path, require_pinned_hash=False)
    with pytest.raises(ValueError, match="does not exactly match"):
        match_wet_co2_simulation_source(rows, workbook_path, require_pinned_hash=False)


def test_simulation_grid_reader_converts_declared_units_and_preserves_public_provenance(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path)
    rows = read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)
    assert len(rows) == 243
    assert rows[0].provider_row == 2
    assert rows[0].temperature_K == pytest.approx(303.15)
    assert rows[0].co2_pressure_Pa == pytest.approx(100_000.0)
    assert rows[0].internal_pressure_Pa == pytest.approx(6_000_000.0)
    assert rows[0].corrosion_inhibitor_efficiency_fraction == pytest.approx(0.4)
    assert rows[0].corrosion_rate_m_s == pytest.approx(3.2e-3 / JULIAN_YEAR_SECONDS)
    assert rows[0].source_data_type == "simulated_model_output"
    assert rows[0].source_group_id == "doi:10.17632/4nydhxjymw.1"
    assert rows[0].source_archive_sha256 == hashlib.sha256(workbook_path.read_bytes()).hexdigest()
    assert rows[0].physical_specimen_id is None
    assert rows[0].empirical_calibration_ready is False
    assert rows[0].evidence[0].license_id == "CC-BY-4.0"
    assert rows[0].evidence[0].sha256 == rows[0].source_archive_sha256


def test_simulation_grid_reader_rejects_unit_table_drift(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path, units_mismatch=True)
    with pytest.raises(ValueError, match="unit table changed"):
        read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)


def test_simulation_grid_reader_rejects_efficiency_outside_declared_fraction(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path, invalid_efficiency=True)
    with pytest.raises(ValueError, match="between zero and one"):
        read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)


def test_simulation_grid_summary_is_descriptive_and_preserves_model_output_lineage(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path)
    rows = read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)
    result = summarize_wet_co2_simulation_grid(WetCo2SimulationGridSummary(rows=tuple(rows[:3])))
    assert result.values["row_count"] == 3
    assert result.values["provider_rows"] == [2, 3, 4]
    assert result.values["summary_basis"] == "unweighted_descriptive_summary_of_supplied_provider_model_rows"
    assert result.values["summaries"]["corrosion_rate_m_s"]["minimum"] == pytest.approx(
        3.2e-3 / JULIAN_YEAR_SECONDS
    )
    assert result.values["physical_observation_inferred"] is False
    assert result.values["failure_probability_inferred"] is False
    assert result.values["physical_calibration_inferred"] is False


def test_simulation_grid_summary_rejects_mixed_provider_digests(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path)
    rows = read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)
    rows[1] = rows[1].model_copy(update={"source_archive_sha256": "f" * 64})
    with pytest.raises(ValueError, match="source_archive_sha256"):
        WetCo2SimulationGridSummary(rows=tuple(rows[:2]))


def test_simulation_rows_can_feed_attributed_wall_loss_scenario_without_empirical_promotion(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path)
    rows = read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)[:2]
    scenario = SimulationRateWallLossScenario(
        rows=rows,
        current_thickness_m=0.01,
        required_thickness_m=0.005,
        horizon_s=JULIAN_YEAR_SECONDS,
        material_state_compatibility_reviewed=True,
        material_state_review_id="review:synthetic-material-state",
        condition_transferability_reviewed=True,
        condition_transfer_review_id="review:synthetic-condition-transfer",
        linear_loss_model_reviewed=True,
        linear_loss_model_review_id="review:synthetic-linear-loss",
        scenario_weights=[0.5, 0.5],
        weight_meaning="caller_declared_scenario_weight",
        scenario_set_id="synthetic-two-provider-row-set",
    )
    result = simulation_rate_wall_loss_scenario(scenario)
    assert result.values["source_data_type"] == "simulated_model_output"
    assert result.values["source_provider_rows"] == [2, 3]
    assert result.values["source_archive_sha256"] == scenario.rows[0].source_archive_sha256
    assert result.values["scenario_rate_weighted_mean_m_s"] == pytest.approx(rows[0].corrosion_rate_m_s)
    assert result.values["physical_observation_inferred"] is False
    assert result.values["physical_calibration_inferred"] is False
    assert result.values["failure_probability_inferred"] is False


def test_simulation_wall_loss_requires_explicit_review_and_matching_rows(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path)
    rows = read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)[:2]
    values = dict(
        rows=rows,
        current_thickness_m=0.01,
        required_thickness_m=0.005,
        horizon_s=JULIAN_YEAR_SECONDS,
        material_state_compatibility_reviewed=True,
        material_state_review_id="review:material",
        condition_transferability_reviewed=True,
        condition_transfer_review_id="review:transfer",
        linear_loss_model_reviewed=True,
        linear_loss_model_review_id="review:linear",
        scenario_weights=[0.5, 0.5],
        weight_meaning="caller_declared_scenario_weight",
        scenario_set_id="synthetic-set",
    )
    with pytest.raises(ValueError, match="condition-transfer"):
        SimulationRateWallLossScenario(**{**values, "condition_transferability_reviewed": False})
    mixed = rows[1].model_copy(update={"source_archive_sha256": "f" * 64})
    with pytest.raises(ValueError, match="source_archive_sha256"):
        SimulationRateWallLossScenario(**{**values, "rows": [rows[0], mixed]})


def test_portable_model_output_scenario_accepts_adapted_norsok_rows(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path)
    source_rows = read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)[:2]
    rows = [wet_co2_simulation_row_to_projection_row(row) for row in source_rows]
    scenario = CorrosionRateModelOutputWallLossScenario(
        rows=rows,
        current_thickness_m=0.01,
        required_thickness_m=0.005,
        horizon_s=JULIAN_YEAR_SECONDS,
        material_state_compatibility_reviewed=True,
        material_state_review_id="review:portable-material",
        condition_transferability_reviewed=True,
        condition_transfer_review_id="review:portable-transfer",
        linear_loss_model_reviewed=True,
        linear_loss_model_review_id="review:portable-linear-loss",
        scenario_weights=[0.5, 0.5],
        weight_meaning="caller_declared_scenario_weight",
        scenario_set_id="portable-two-row-norsok-set",
    )
    result = corrosion_rate_model_output_wall_loss_scenario(scenario)
    assert result.values["source_dataset_id"] == source_rows[0].dataset_id
    assert result.values["source_record_ids"] == ["provider-row:2", "provider-row:3"]
    assert result.values["source_role"] == "simulated_model_output"
    assert result.values["physical_observation_inferred"] is False
    assert result.values["failure_probability_inferred"] is False


def test_portable_model_output_scenario_rejects_mixed_lineage_and_physical_rows(tmp_path):
    _, workbook_path = _matching_simulation_fixtures(tmp_path)
    source_rows = read_wet_co2_simulation_grid(workbook_path, require_pinned_hash=False)[:2]
    rows = [wet_co2_simulation_row_to_projection_row(row) for row in source_rows]
    with pytest.raises(ValueError, match="matching its dataset and archive digest"):
        type(rows[1]).model_validate({**rows[1].model_dump(), "source_archive_sha256": "f" * 64})
    values = dict(
        rows=rows,
        current_thickness_m=0.01,
        required_thickness_m=0.005,
        horizon_s=JULIAN_YEAR_SECONDS,
        material_state_compatibility_reviewed=True,
        material_state_review_id="review:material",
        condition_transferability_reviewed=True,
        condition_transfer_review_id="review:transfer",
        linear_loss_model_reviewed=True,
        linear_loss_model_review_id="review:linear",
        scenario_weights=[0.5, 0.5],
        weight_meaning="caller_declared_scenario_weight",
        scenario_set_id="portable-set",
    )
    mixed_data = rows[1].model_dump()
    mixed_data["source_archive_sha256"] = "f" * 64
    mixed_data["evidence"] = tuple(
        {**evidence.model_dump(), "sha256": "f" * 64} for evidence in rows[1].evidence
    )
    mixed = type(rows[1]).model_validate(mixed_data)
    with pytest.raises(ValueError, match="source_archive_sha256"):
        CorrosionRateModelOutputWallLossScenario(**{**values, "rows": [rows[0], mixed]})
    with pytest.raises(ValueError, match="should be None"):
        type(rows[0]).model_validate({**rows[0].model_dump(), "physical_specimen_id": "coupon-1"})


def _literature_evidence(**updates):
    values = dict(
        evidence_id="local-review-1",
        source_group_id="doi:10.0000/example",
        source_record_id="table-2-row-1",
        source_locator="Table 2, row 1",
        bibliographic_id="doi:10.0000/example",
        bibliographic_link_status="primary_source_row",
        compilation_row_link_status="provider_explicit",
        compilation_row_link_basis_id="provider:data-dictionary-v1",
        evidence_asset_sha256="a" * 64,
        source_values={
            "temperature_c": 30.0,
            "total_pressure_kpa": 1000.0,
            "liquid_shear_pa": 5.0,
            "gas_shear_pa": 1.0,
            "corrosion_rate_mm_y": 3.2,
        },
        source_data_role="field_observation",
        publication_license_id=None,
        observation_redistribution_status="not_verified",
        data_dictionary_status="partial",
        physical_specimen_identity_status="unresolved",
    )
    values.update(updates)
    return WetCo2LiteratureEvidenceRow(**values)


def _field_maps():
    return (
        WetCo2LiteratureFieldMap(
            compilation_field="raw_temperature",
            source_fields=("temperature_c",),
            operation="single_value_affine",
            reviewed_transform_basis_id="review:temperature-identity",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_internal_pressure",
            source_fields=("total_pressure_kpa",),
            operation="single_value_affine",
            scale=0.01,
            reviewed_transform_basis_id="review:kpa-to-bar",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_shear_stress",
            source_fields=("liquid_shear_pa", "gas_shear_pa"),
            operation="arithmetic_mean_affine",
            reviewed_transform_basis_id="review:declared-two-phase-mean",
        ),
        WetCo2LiteratureFieldMap(
            compilation_field="raw_corrosion_rate",
            source_fields=("corrosion_rate_mm_y",),
            operation="single_value_affine",
            reviewed_transform_basis_id="review:rate-identity",
        ),
    )


def test_literature_crosswalk_applies_only_declared_reviewed_transforms(tmp_path):
    record = read_unresolved_wet_co2_compilation(_fixture(tmp_path), require_pinned_hash=False)[0]
    record = record.model_copy(update={"raw_internal_pressure": 10.0, "raw_shear_stress": 3.0})
    audit = audit_wet_co2_literature_row(record, _literature_evidence(), _field_maps())
    assert audit.crosswalk_status == "all_declared_fields_match"
    assert audit.all_declared_fields_match is True
    assert [comparison.transformed_source_value for comparison in audit.comparisons] == [
        30.0,
        10.0,
        3.0,
        3.2,
    ]
    assert all(comparison.status == "match" for comparison in audit.comparisons)
    assert audit.automatic_correction_performed is False
    assert audit.empirical_calibration_ready is False
    assert audit.mechanistic_calibration_ready is False


def test_literature_crosswalk_preserves_numeric_mismatch(tmp_path):
    record = read_unresolved_wet_co2_compilation(_fixture(tmp_path), require_pinned_hash=False)[0]
    evidence = _literature_evidence(
        source_values={
            **_literature_evidence().source_values,
            "corrosion_rate_mm_y": 3.11,
        }
    )
    audit = audit_wet_co2_literature_row(record, evidence, (_field_maps()[-1],))
    comparison = audit.comparisons[0]
    assert audit.crosswalk_status == "numeric_mismatch"
    assert comparison.compilation_value == 3.2
    assert comparison.transformed_source_value == 3.11
    assert comparison.absolute_difference == pytest.approx(0.09)
    assert comparison.status == "mismatch"


def test_literature_crosswalk_preserves_explicit_missing_value(tmp_path):
    record = read_unresolved_wet_co2_compilation(_fixture(tmp_path), require_pinned_hash=False)[0]
    evidence = _literature_evidence(
        source_values={**_literature_evidence().source_values, "temperature_c": None}
    )
    audit = audit_wet_co2_literature_row(record, evidence, (_field_maps()[0],))
    assert audit.crosswalk_status == "incomplete"
    assert audit.comparisons[0].status == "source_missing"
    assert audit.comparisons[0].transformed_source_value is None
    assert audit.comparisons[0].absolute_difference is None


def test_literature_crosswalk_rejects_ambiguous_or_undeclared_mapping(tmp_path):
    record = read_unresolved_wet_co2_compilation(_fixture(tmp_path), require_pinned_hash=False)[0]
    duplicate = (_field_maps()[0], _field_maps()[0])
    with pytest.raises(ValueError, match="more than once"):
        audit_wet_co2_literature_row(record, _literature_evidence(), duplicate)
    missing_source = WetCo2LiteratureFieldMap(
        compilation_field="raw_temperature",
        source_fields=("undeclared",),
        operation="single_value_affine",
        reviewed_transform_basis_id="review:missing",
    )
    with pytest.raises(ValueError, match="omits mapped source fields"):
        audit_wet_co2_literature_row(record, _literature_evidence(), (missing_source,))
