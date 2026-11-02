import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.acoustic_emission_pick import (
    AcousticEmissionArrivalPick,
    acoustic_emission_arrival_pick,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored"}
D = "a" * 64


def payload(**updates):
    value = {
        "pick_id": "pick-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "acquisition_id": "acquisition-1",
        "channel_id": "channel-1",
        "clock_id": "clock-1",
        "elapsed_time_s": [index * 0.001 for index in range(12)],
        "signal_values": [0.0, 0.1, -0.1, 0.0, 0.1, 0.2, 0.3, 2.0, 3.0, 2.0, 1.0, 0.5],
        "signal_unit_token": "V",
        "waveform_digest": D,
        "preprocessing": "demean_baseline",
        "polarity_basis": "absolute",
        "method": "threshold",
        "baseline_start_s": 0.0,
        "baseline_end_s": 0.003,
        "search_start_s": 0.004,
        "search_end_s": 0.011,
        "threshold_value": 1.0,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "acquisition_configuration_digest": D,
        "waveform_clock_and_units_reviewed": True,
        "preprocessing_and_polarity_reviewed": True,
        "baseline_and_search_windows_reviewed": True,
        "pick_method_settings_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "evidence": [E],
    }
    value.update(updates)
    return AcousticEmissionArrivalPick.model_validate_json(json.dumps(value))


def test_threshold_pick_is_original_sample():
    result = acoustic_emission_arrival_pick(payload())
    assert result.status == "computed"
    assert result.values["pick_sample_index"] == 7
    assert result.values["pick_time_s"] == pytest.approx(0.007)


def test_aic_pick_and_diagnostics():
    result = acoustic_emission_arrival_pick(
        payload(method="aic", threshold_value=None, aic_variance_floor=1e-12)
    )
    assert result.status == "computed"
    assert 6 <= result.values["pick_sample_index"] <= 9
    assert result.values["method_diagnostic"]["minimum_aic_score"] is not None


def test_no_threshold_crossing_and_review_gate():
    assert acoustic_emission_arrival_pick(payload(threshold_value=10.0)).status == "out_of_scope"
    assert acoustic_emission_arrival_pick(payload(pick_method_settings_reviewed=False)).status == "needs_data"


def test_clock_and_context_are_strict():
    with pytest.raises(ValueError, match="strictly increasing"):
        payload(
            elapsed_time_s=[0.0, 0.001, 0.002, 0.002, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.01, 0.011]
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.acoustic_emission_arrival_pick",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="clock-1"),
        )
