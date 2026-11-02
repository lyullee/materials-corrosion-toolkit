from __future__ import annotations

import numpy as np
import pytest
from pydantic import ValidationError

from matintegrity.adapters import guided_wave_pair_feature_inputs, guided_wave_reference_ensemble_inputs
from matintegrity.contracts import RunContext
from matintegrity.models.inspection import (
    GuidedWavePairFeatures,
    GuidedWaveReferenceEnsemble,
    guided_wave_pair_features,
    guided_wave_reference_ensemble,
)
from matintegrity.registry import default_registry


def _inputs(**updates):
    values = {
        "specimen_id": "tube-1",
        "baseline_acquisition_id": "1622",
        "observation_acquisition_id": "1902",
        "frequency_Hz": 14_000.0,
        "wave_mode": "torsional",
        "baseline_distance_m": [0.0, 1.0, 2.0],
        "baseline_voltage_V": [1.0, 2.0, 3.0],
        "observation_distance_m": [0.0, 1.0, 2.0],
        "observation_voltage_V": [2.0, 4.0, 6.0],
        "window_start_m": 0.0,
        "window_end_m": 2.0,
        "distance_match_tolerance_m": 0.0,
        "duplicate_distance_policy": "preserve_samples",
    }
    values.update(updates)
    return values


def _reader_record(acquisition_id, *, specimen_id="tube-1", archive_hash="a" * 64):
    return {
        "dataset_id": "guided-wave-pipeline-shm",
        "specimen_id": specimen_id,
        "acquisition_id": acquisition_id,
        "outer_archive_sha256": archive_hash,
        "signals": [
            {
                "frequency_Hz": 14_000.0,
                "distance_m": np.asarray([0.0, 1.0, 2.0]),
                "torsional_V": np.asarray([1.0, 2.0, 3.0]) + acquisition_id,
                "flexural_V": np.asarray([-1.0, -2.0, -3.0]) - acquisition_id,
            }
        ],
    }


def _ensemble_inputs(**updates):
    values = {
        "specimen_id": "tube-1",
        "baseline_acquisition_ids": ["1", "2", "3"],
        "observation_acquisition_id": "4",
        "baseline_source_group_id": "declared-baseline-group",
        "observation_source_group_id": "declared-observation-group",
        "baseline_selection_basis": "three authored acquisitions selected before comparison",
        "frequency_Hz": 14_000.0,
        "wave_mode": "torsional",
        "distance_m": [0.0, 1.0, 2.0],
        "baseline_voltage_V": [[0.0, 1.0, 2.0], [0.0, 2.0, 4.0], [0.0, 3.0, 6.0]],
        "observation_distance_m": [0.0, 1.0, 2.0],
        "observation_voltage_V": [0.0, 4.0, 8.0],
        "window_start_m": 0.0,
        "window_end_m": 2.0,
        "distance_match_tolerance_m": 0.0,
        "duplicate_distance_policy": "preserve_samples",
        "reference_statistic": "mean",
    }
    values.update(updates)
    return values


def test_pair_features_match_direct_descriptive_identities():
    result = guided_wave_pair_features(GuidedWavePairFeatures.model_validate(_inputs()))
    expected_rms = np.sqrt(14.0 / 3.0)
    assert result.status == "computed"
    assert result.values["baseline_rms_V"] == pytest.approx(expected_rms)
    assert result.values["observation_rms_V"] == pytest.approx(2.0 * expected_rms)
    assert result.values["residual_rms_V"] == pytest.approx(expected_rms)
    assert result.values["normalized_residual_rms"] == pytest.approx(1.0)
    assert result.values["voltage_energy_ratio"] == pytest.approx(4.0)
    assert result.values["correlation_coefficient"] == pytest.approx(1.0)
    assert result.values["peak_absolute_difference_V"] == pytest.approx(3.0)
    assert result.values["signed_mean_difference_V"] == pytest.approx(2.0)


def test_spatial_window_is_inclusive_and_not_interpolated():
    result = guided_wave_pair_features(
        GuidedWavePairFeatures.model_validate(_inputs(window_start_m=1.0, window_end_m=2.0))
    )
    assert result.values["raw_selected_samples"] == 2
    assert result.values["effective_distance_start_m"] == 1.0
    assert result.values["effective_distance_end_m"] == 2.0


def test_window_with_one_sample_reports_needs_data():
    result = guided_wave_pair_features(
        GuidedWavePairFeatures.model_validate(_inputs(window_start_m=1.5, window_end_m=2.0))
    )
    assert result.status == "needs_data"
    assert result.values == {"selected_samples": 1}


@pytest.mark.parametrize(
    "updates",
    [
        {"observation_acquisition_id": "1622"},
        {"observation_voltage_V": [2.0, 4.0]},
        {"baseline_distance_m": [0.0, 2.0, 1.0]},
        {"observation_distance_m": [0.0, 1.0, 2.1]},
        {
            "baseline_distance_m": [0.0, 1.0, 1.0],
            "observation_distance_m": [0.0, 1.0, 1.0001],
            "distance_match_tolerance_m": 0.001,
        },
    ],
)
def test_contract_rejects_identity_axis_and_alignment_errors(updates):
    with pytest.raises(ValidationError):
        GuidedWavePairFeatures.model_validate(_inputs(**updates))


def test_repeated_distance_policies_are_explicit():
    common = _inputs(
        baseline_distance_m=[0.0, 1.0, 1.0, 2.0],
        baseline_voltage_V=[1.0, 2.0, 4.0, 3.0],
        observation_distance_m=[0.0, 1.0, 1.0, 2.0],
        observation_voltage_V=[2.0, 4.0, 8.0, 6.0],
    )
    preserved = guided_wave_pair_features(GuidedWavePairFeatures.model_validate(common))
    assert preserved.values["raw_selected_samples"] == 4
    assert preserved.values["effective_selected_samples"] == 4
    assert preserved.values["repeated_distance_intervals"] == 1

    averaged = guided_wave_pair_features(
        GuidedWavePairFeatures.model_validate(
            {**common, "duplicate_distance_policy": "mean_aligned_duplicates"}
        )
    )
    assert averaged.values["raw_selected_samples"] == 4
    assert averaged.values["effective_selected_samples"] == 3
    assert averaged.values["voltage_energy_ratio"] == pytest.approx(4.0)

    rejected = guided_wave_pair_features(
        GuidedWavePairFeatures.model_validate({**common, "duplicate_distance_policy": "reject"})
    )
    assert rejected.status == "out_of_scope"
    assert rejected.values["repeated_distance_intervals"] == 1


def test_zero_baseline_keeps_undefined_ratios_explicit():
    result = guided_wave_pair_features(
        GuidedWavePairFeatures.model_validate(
            _inputs(baseline_voltage_V=[0.0, 0.0, 0.0], observation_voltage_V=[1.0, 2.0, 3.0])
        )
    )
    assert result.values["normalized_residual_rms"] is None
    assert result.values["voltage_energy_ratio"] is None
    assert result.values["correlation_coefficient"] is None


def test_reader_adapter_selects_exact_frequency_and_mode():
    baseline = _reader_record(1)
    observation = _reader_record(2)
    inputs = guided_wave_pair_feature_inputs(
        baseline,
        observation,
        frequency_Hz=14_000.0,
        wave_mode="flexural",
        window_start_m=0.0,
        window_end_m=2.0,
    )
    assert inputs["baseline_acquisition_id"] == "1"
    assert inputs["observation_acquisition_id"] == "2"
    assert inputs["baseline_voltage_V"] == [-2.0, -3.0, -4.0]
    assert inputs["observation_voltage_V"] == [-3.0, -4.0, -5.0]


@pytest.mark.parametrize(
    ("baseline", "observation", "kwargs"),
    [
        (_reader_record(1), _reader_record(1), {}),
        (_reader_record(1), _reader_record(2, specimen_id="tube-2"), {}),
        (_reader_record(1), _reader_record(2, archive_hash="b" * 64), {}),
        (_reader_record(1), _reader_record(2), {"frequency_Hz": 18_000.0}),
        (_reader_record(1), _reader_record(2), {"wave_mode": "longitudinal"}),
    ],
)
def test_reader_adapter_rejects_unaligned_identity_or_channel(baseline, observation, kwargs):
    arguments = {
        "frequency_Hz": 14_000.0,
        "wave_mode": "torsional",
        "window_start_m": 0.0,
        "window_end_m": 2.0,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        guided_wave_pair_feature_inputs(baseline, observation, **arguments)


def test_registered_route_preserves_source_and_nonprobability_meaning():
    registry = default_registry()
    result = registry.run(
        "inspection.guided_wave_pair_features",
        _inputs(),
        RunContext(asset_id="tube-1", location_id="pipe", time_basis="provider acquisition order"),
    )
    assert result.status == "computed"
    assert result.source_ids == ("guided_wave_pair_feature_definition",)
    assert result.probability_semantics == {}
    assert result.values["specimen_id"] == "tube-1"


def test_reference_ensemble_matches_direct_mean_and_leave_one_out_identities():
    result = guided_wave_reference_ensemble(GuidedWaveReferenceEnsemble.model_validate(_ensemble_inputs()))
    observation_residual = np.sqrt(20.0 / 3.0)
    leave_one_out = np.sqrt(3.75)
    assert result.status == "computed"
    assert result.values["reference_rms_V"] == pytest.approx(np.sqrt(20.0 / 3.0))
    assert result.values["observation_residual_rms_V"] == pytest.approx(observation_residual)
    assert result.values["baseline_spread_rms_V"] == pytest.approx(np.sqrt(10.0 / 9.0))
    assert result.values["leave_one_out_residual_rms_V"] == pytest.approx([leave_one_out, 0.0, leave_one_out])
    assert result.values["leave_one_out_residual_median_V"] == pytest.approx(leave_one_out)
    assert result.values["observation_to_leave_one_out_maximum_ratio"] == pytest.approx(
        observation_residual / leave_one_out
    )
    assert result.values["reference_observation_correlation"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    "updates",
    [
        {"baseline_acquisition_ids": ["1", "1", "3"]},
        {"observation_acquisition_id": "2"},
        {"baseline_voltage_V": [[0.0, 1.0, 2.0], [0.0, 2.0, 4.0]]},
        {"observation_distance_m": [0.0, 1.0, 2.1]},
        {"distance_m": [0.0, 2.0, 1.0]},
    ],
)
def test_reference_ensemble_contract_rejects_identity_shape_and_axis_errors(updates):
    with pytest.raises(ValidationError):
        GuidedWaveReferenceEnsemble.model_validate(_ensemble_inputs(**updates))


def test_reference_ensemble_repeated_distance_and_zero_spread_policies():
    repeated = _ensemble_inputs(
        distance_m=[0.0, 1.0, 1.0, 2.0],
        baseline_voltage_V=[
            [1.0, 2.0, 4.0, 3.0],
            [1.0, 2.0, 4.0, 3.0],
            [1.0, 2.0, 4.0, 3.0],
        ],
        observation_distance_m=[0.0, 1.0, 1.0, 2.0],
        observation_voltage_V=[2.0, 4.0, 8.0, 6.0],
        duplicate_distance_policy="mean_aligned_duplicates",
    )
    result = guided_wave_reference_ensemble(GuidedWaveReferenceEnsemble.model_validate(repeated))
    assert result.values["effective_selected_samples"] == 3
    assert result.values["observation_to_baseline_spread_ratio"] is None
    assert result.values["observation_to_leave_one_out_median_ratio"] is None
    rejected = guided_wave_reference_ensemble(
        GuidedWaveReferenceEnsemble.model_validate({**repeated, "duplicate_distance_policy": "reject"})
    )
    assert rejected.status == "out_of_scope"


def test_reference_ensemble_reader_adapter_and_registry_route():
    baselines = [_reader_record(index) for index in (1, 2, 3)]
    observation = _reader_record(4)
    inputs = guided_wave_reference_ensemble_inputs(
        baselines,
        observation,
        baseline_source_group_id="authored-baseline",
        observation_source_group_id="authored-observation",
        baseline_selection_basis="selected before comparison",
        frequency_Hz=14_000.0,
        wave_mode="torsional",
        window_start_m=0.0,
        window_end_m=2.0,
    )
    result = default_registry().run(
        "inspection.guided_wave_reference_ensemble",
        inputs,
        RunContext(asset_id="tube-1", location_id="pipe", time_basis="provider acquisition order"),
    )
    assert result.status == "computed"
    assert result.values["baseline_acquisition_count"] == 3
    assert result.source_ids == ("guided_wave_reference_ensemble_definition",)
    assert result.probability_semantics == {}


@pytest.mark.parametrize(
    ("baselines", "observation"),
    [
        ([_reader_record(1), _reader_record(2)], _reader_record(4)),
        ([_reader_record(1), _reader_record(1), _reader_record(3)], _reader_record(4)),
        ([_reader_record(1), _reader_record(2), _reader_record(3)], _reader_record(2)),
        (
            [_reader_record(1), _reader_record(2), _reader_record(3, specimen_id="tube-2")],
            _reader_record(4),
        ),
        (
            [_reader_record(1), _reader_record(2), _reader_record(3, archive_hash="b" * 64)],
            _reader_record(4),
        ),
    ],
)
def test_reference_ensemble_adapter_rejects_invalid_record_sets(baselines, observation):
    with pytest.raises(ValueError):
        guided_wave_reference_ensemble_inputs(
            baselines,
            observation,
            baseline_source_group_id="authored-baseline",
            observation_source_group_id="authored-observation",
            baseline_selection_basis="selected before comparison",
            frequency_Hz=14_000.0,
            wave_mode="torsional",
            window_start_m=0.0,
            window_end_m=2.0,
        )
