import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.metallurgical_aging import (
    MetallurgicalAgingExposure,
    metallurgical_aging_exposure,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored aging test"}


def payload(**updates):
    value = {
        "assessment_id": "aging-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "clock_id": "thermal-clock",
        "material_condition_id": "material-1",
        "aging_mechanism_id": "mechanism-1",
        "intervals": (
            {
                "interval_id": "i1",
                "start_time_s": 0.0,
                "end_time_s": 100.0,
                "temperature_K": 600.0,
                "equivalent_time_rate_multiplier": 2.0,
                "multiplier_provider_id": "provider-1",
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
            {
                "interval_id": "i2",
                "start_time_s": 100.0,
                "end_time_s": 300.0,
                "temperature_K": 550.0,
                "equivalent_time_rate_multiplier": 0.5,
                "multiplier_provider_id": "provider-1",
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "exposure_envelope": {
            "envelope_id": "envelope-1",
            "material_condition_id": "material-1",
            "aging_mechanism_id": "mechanism-1",
            "reference_temperature_K": 575.0,
            "multiplier_provider_id": "provider-1",
            "minimum_supported_temperature_K": 500.0,
            "maximum_supported_temperature_K": 650.0,
            "maximum_equivalent_exposure_s": 400.0,
            "applicability_basis": "caller calibration",
            "evidence": (EVIDENCE,),
        },
        "material_and_mechanism_reviewed": True,
        "clock_and_temperature_history_reviewed": True,
        "multiplier_provider_reviewed": True,
        "interval_completeness_reviewed": True,
        "envelope_authority_reviewed": True,
    }
    value.update(updates)
    return MetallurgicalAgingExposure(**value)


def test_equivalent_exposure_is_exact_weighted_duration_sum():
    result = metallurgical_aging_exposure(payload())
    assert result.status == "computed"
    assert result.values["elapsed_exposure_s"] == pytest.approx(300.0)
    assert result.values["equivalent_exposure_s"] == pytest.approx(300.0)
    assert result.values["remaining_equivalent_exposure_s"] == pytest.approx(100.0)


@pytest.mark.parametrize(
    "duration,multiplier,status",
    [
        (1e-200, 1e-200, "out_of_scope"),
        (1e200, 1e200, "out_of_scope"),
        (1e-200, 0.0, "computed"),
    ],
)
def test_nonzero_exposure_range_loss_is_not_zero_or_acceptance(duration, multiplier, status):
    row = (
        payload()
        .intervals[0]
        .model_copy(update={"end_time_s": duration, "equivalent_time_rate_multiplier": multiplier})
    )
    result = metallurgical_aging_exposure(payload(intervals=(row,)))
    assert result.status == status
    if status == "out_of_scope":
        assert "within_declared_equivalent_exposure" not in result.values
        assert "interval_contributions" not in result.values
    else:
        assert result.values["equivalent_exposure_s"] == 0.0


def test_tiny_clock_large_multiplier_preserves_finite_exposure():
    row = (
        payload()
        .intervals[0]
        .model_copy(update={"end_time_s": 1e-200, "equivalent_time_rate_multiplier": 1e200})
    )
    result = metallurgical_aging_exposure(payload(intervals=(row,)))
    assert result.status == "computed"
    assert result.values["equivalent_exposure_s"] == pytest.approx(1.0, rel=1e-14)


def test_unobserved_internal_span_cannot_pass_equivalent_exposure_limit():
    original = payload()
    later = original.intervals[1].model_copy(update={"start_time_s": 150.0})
    result = metallurgical_aging_exposure(payload(intervals=(original.intervals[0], later)))
    assert result.status == "needs_data"
    assert result.values["uncovered_duration_s"] == 50.0
    assert result.values["uncovered_intervals_s"] == [[100.0, 150.0]]
    assert "within_declared_equivalent_exposure" not in result.values


def test_common_clock_translation_keeps_exposure_and_reports_declared_span():
    original = payload()
    shifted = tuple(
        row.model_copy(
            update={"start_time_s": row.start_time_s + 1000.0, "end_time_s": row.end_time_s + 1000.0}
        )
        for row in original.intervals
    )
    result = metallurgical_aging_exposure(payload(intervals=shifted))
    assert result.status == "computed"
    assert result.values["equivalent_exposure_s"] == 300.0
    assert result.values["history_span_s"] == 300.0
    assert result.values["uncovered_duration_s"] == 0.0
    assert result.values["clock_id"] == "thermal-clock"


def test_invalid_provider_or_review_needs_data():
    row = payload().intervals[0].model_copy(update={"multiplier_provider_id": "other"})
    assert (
        metallurgical_aging_exposure(payload(intervals=(row, payload().intervals[1]))).status == "needs_data"
    )
    assert metallurgical_aging_exposure(payload(multiplier_provider_reviewed=False)).status == "needs_data"


def test_temperature_outside_support_is_out_of_scope():
    row = payload().intervals[0].model_copy(update={"temperature_K": 700.0})
    result = metallurgical_aging_exposure(payload(intervals=(row, payload().intervals[1])))
    assert result.status == "out_of_scope"
    assert result.values["outside_temperature_support_interval_ids"] == ["i1"]


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.metallurgical_aging_exposure",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
