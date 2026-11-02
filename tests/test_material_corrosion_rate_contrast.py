import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.corrosion import MaterialCorrosionRateContrast, material_corrosion_rate_contrast
from matintegrity.registry import default_registry

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "validation/ct110_weld_corrosion_rates.json"
METRES_PER_SECOND_PER_MM_PER_YEAR = 1e-3 / (365.25 * 24 * 60 * 60)


def _inputs(observation):
    return MaterialCorrosionRateContrast(
        comparison_id=observation["comparison_id"],
        numerator_material_id="CT110-weld-metal",
        reference_material_id="CT110-base-metal",
        numerator_rate_m_s=observation["weld_rate_m_s"],
        reference_rate_m_s=observation["base_rate_m_s"],
        condition_signature=observation["condition_signature"],
        condition_group_id=observation["condition_group_id"],
        source_group_id="doi:10.1371/journal.pone.0244237#weight-loss-corrosion-tests",
        measurement_method="weight_loss",
    )


def test_ct110_open_supplement_contrasts_reproduce_reported_rounded_ratios():
    dataset = json.loads(DATA.read_text(encoding="utf-8"))
    assert dataset["physical_specimen_ids_available"] is False
    assert dataset["replicate_counts_available"] is False
    assert dataset["uncertainty_available"] is False
    for row in dataset["observations"]:
        result = material_corrosion_rate_contrast(_inputs(row))
        assert row["weld_rate_m_s"] == pytest.approx(
            row["weld_rate_mm_year"] * METRES_PER_SECOND_PER_MM_PER_YEAR
        )
        assert row["base_rate_m_s"] == pytest.approx(
            row["base_rate_mm_year"] * METRES_PER_SECOND_PER_MM_PER_YEAR
        )
        assert result.values["rate_ratio"] == pytest.approx(
            row["weld_rate_mm_year"] / row["base_rate_mm_year"]
        )
        assert round(result.values["rate_ratio"], 1) == row["reported_ratio_rounded"]


def test_contrast_keeps_condition_and_source_group_lineage():
    dataset = json.loads(DATA.read_text(encoding="utf-8"))
    result = material_corrosion_rate_contrast(_inputs(dataset["observations"][0]))
    assert result.values["condition_group_id"] == "temperature_sweep_co2_0.3_mpa"
    assert result.values["source_group_id"] == dataset["source_group_id"]
    assert result.values["condition_signature"]["temperature_C"] == 30
    assert len(result.values["condition_signature_sha256"]) == 64


def test_contrast_rejects_same_material_identity_and_empty_conditions():
    dataset = json.loads(DATA.read_text(encoding="utf-8"))
    row = _inputs(dataset["observations"][0]).model_dump()
    with pytest.raises(ValidationError):
        MaterialCorrosionRateContrast(**{**row, "reference_material_id": row["numerator_material_id"]})
    with pytest.raises(ValidationError):
        MaterialCorrosionRateContrast(**{**row, "condition_signature": {}})
    with pytest.raises(ValidationError):
        MaterialCorrosionRateContrast(**{**row, "condition_signature": {"nested": {"value": 1}}})


def test_zero_rate_comparison_keeps_undefined_ratio_explicit():
    dataset = json.loads(DATA.read_text(encoding="utf-8"))
    row = _inputs(dataset["observations"][0]).model_dump()
    zero_numerator = material_corrosion_rate_contrast(
        MaterialCorrosionRateContrast(**{**row, "numerator_rate_m_s": 0.0})
    )
    assert zero_numerator.values["rate_ratio"] == 0
    assert zero_numerator.values["log_rate_ratio"] is None
    zero_reference = material_corrosion_rate_contrast(
        MaterialCorrosionRateContrast(**{**row, "reference_rate_m_s": 0.0})
    )
    assert zero_reference.values["rate_ratio"] is None
    assert zero_reference.values["log_rate_ratio"] is None


def test_contrast_registered_api_runs_with_explicit_context():
    dataset = json.loads(DATA.read_text(encoding="utf-8"))
    row = dataset["observations"][0]
    result = default_registry().run(
        "corrosion.material_rate_contrast",
        _inputs(row),
        RunContext(
            asset_id="CT110-study", location_id="reported-condition-group", time_basis="96 h exposure"
        ),
    )
    assert result.values["rate_ratio"] == pytest.approx(row["reported_ratio_rounded"], rel=0.01)
    assert result.values["reference_material_id"] == "CT110-base-metal"
