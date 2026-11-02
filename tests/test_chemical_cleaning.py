import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.chemical_cleaning import (
    ChemicalCleaningRecord,
    chemical_cleaning_envelope,
)
from matintegrity.registry import default_registry

EVIDENCE = {
    "source_id": "caller-cleaning-record",
    "origin": "user_declared",
    "citation": "caller-controlled cleaning and compatibility evidence",
}


def envelope(**updates):
    values = {
        "envelope_id": "acid-envelope",
        "material_condition_id": "material-heat-1",
        "solution_id": "solution-a",
        "chemical_family": "authored-acid-family",
        "minimum_concentration_mass_fraction": 0.05,
        "maximum_concentration_mass_fraction": 0.15,
        "minimum_temperature_K": 290.0,
        "maximum_temperature_K": 330.0,
        "minimum_pH": 1.0,
        "maximum_pH": 3.0,
        "maximum_single_exposure_s": 1800.0,
        "maximum_cumulative_exposure_s": 2400.0,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def step(identifier, start, end, **updates):
    values = {
        "step_id": identifier,
        "envelope_id": "acid-envelope",
        "solution_id": "solution-a",
        "chemical_family": "authored-acid-family",
        "start_time_s": start,
        "end_time_s": end,
        "concentration_mass_fraction": 0.1,
        "temperature_K": 310.0,
        "pH": 2.0,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def record(**updates):
    values = {
        "cleaning_record_id": "cleaning-1",
        "asset_id": "asset-1",
        "location_id": "vessel-internal",
        "material_condition_id": "material-heat-1",
        "clock_id": "cleaning-clock-1",
        "steps": (step("s1", 0.0, 900.0), step("s2", 1000.0, 2000.0)),
        "compatibility_envelopes": (envelope(),),
        "record_completeness_reviewed": True,
        "sequence_and_clock_reviewed": True,
        "material_identity_reviewed": True,
        "compatibility_envelopes_reviewed": True,
    }
    values.update(updates)
    return ChemicalCleaningRecord(**values)


def test_steps_and_cumulative_exposure_are_compared_independently():
    result = chemical_cleaning_envelope(record())
    assert result.status == "computed"
    assert result.values["declared_envelope_outcome"] == "within"
    assert result.values["cumulative_exposure_by_envelope"][0]["cumulative_exposure_s"] == 1900.0


@pytest.mark.parametrize("material,status", [(None, "needs_data"), ("other-material", "out_of_scope")])
def test_compatibility_envelope_must_bind_the_actual_material(material, status):
    result = chemical_cleaning_envelope(
        record(compatibility_envelopes=(envelope(material_condition_id=material),))
    )
    assert result.status == status
    assert "declared_envelope_outcome" not in result.values


def test_default_registry_exchange_and_context_binding():
    registry = default_registry()
    value = record()
    context = RunContext(asset_id=value.asset_id, location_id=value.location_id, time_basis="synthetic")
    direct = registry.run("fabrication.chemical_cleaning_envelope", value, context)
    assert direct.status == "computed" and direct.model_version == "1.1.0"
    assert (
        direct.model_dump()
        == registry.run_json(
            "fabrication.chemical_cleaning_envelope", value.model_dump_json(), context
        ).model_dump()
    )
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.chemical_cleaning_envelope", value, context.model_copy(update={"asset_id": "other"})
        )


def test_range_and_cumulative_violations_are_not_hidden():
    request = record(
        steps=(step("s1", 0.0, 1500.0, pH=5.0), step("s2", 1500.0, 3000.0)),
        compatibility_envelopes=(envelope(maximum_cumulative_exposure_s=2500.0),),
    )
    result = chemical_cleaning_envelope(request)
    assert result.values["declared_envelope_outcome"] == "outside"
    assert result.values["violating_step_ids"] == ["s1"]
    assert result.values["violating_envelope_ids"] == ["acid-envelope"]
    assert "pH" in result.values["step_comparisons"][0]["violations"]


def test_unreviewed_invalid_or_unmapped_records_need_data():
    unreviewed = chemical_cleaning_envelope(record(material_identity_reviewed=False))
    assert unreviewed.status == "needs_data"
    invalid = chemical_cleaning_envelope(record(steps=(step("s1", 0.0, 10.0, record_valid=False),)))
    assert invalid.status == "needs_data"
    unmapped = chemical_cleaning_envelope(record(steps=(step("s1", 0.0, 10.0, envelope_id="missing"),)))
    assert unmapped.status == "needs_data"


def test_clock_overlap_and_envelope_order_are_rejected():
    with pytest.raises(ValueError, match="cannot overlap"):
        record(steps=(step("s1", 0.0, 20.0), step("s2", 10.0, 30.0)))
    with pytest.raises(ValueError, match="concentration envelope"):
        record(compatibility_envelopes=(envelope(minimum_concentration_mass_fraction=0.2),))
