"""Deterministic arrival picking for caller-reviewed acoustic-emission waveforms."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AcousticEmissionArrivalPick(Contract):
    pick_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    acquisition_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=8)
    signal_values: tuple[float, ...] = Field(min_length=8)
    signal_unit_token: str = Field(min_length=1)
    waveform_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    preprocessing: Literal["none", "demean_baseline"]
    polarity_basis: Literal["positive", "negative", "absolute"]
    method: Literal["threshold", "aic"]
    baseline_start_s: Nonnegative
    baseline_end_s: Positive
    search_start_s: Nonnegative
    search_end_s: Positive
    threshold_value: Positive | None = None
    threshold_sigma_multiplier: Positive | None = None
    aic_variance_floor: Positive | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    acquisition_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    waveform_clock_and_units_reviewed: bool
    preprocessing_and_polarity_reviewed: bool
    baseline_and_search_windows_reviewed: bool
    pick_method_settings_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def trace_and_settings(self):
        if len(self.elapsed_time_s) != len(self.signal_values):
            raise ValueError("AE waveform time and signal arrays must align")
        if any(b <= a for a, b in zip(self.elapsed_time_s, self.elapsed_time_s[1:], strict=False)):
            raise ValueError("AE waveform clock must be strictly increasing")
        if self.baseline_end_s <= self.baseline_start_s or self.search_end_s <= self.search_start_s:
            raise ValueError("AE baseline and search windows must have positive duration")
        if self.baseline_end_s > self.search_start_s:
            raise ValueError("AE baseline window must end no later than the search window")
        baseline_count = sum(self.baseline_start_s <= t <= self.baseline_end_s for t in self.elapsed_time_s)
        search_count = sum(self.search_start_s <= t <= self.search_end_s for t in self.elapsed_time_s)
        if baseline_count < 3 or search_count < 4:
            raise ValueError("AE baseline requires three and search requires four original samples")
        if self.method == "threshold":
            if (self.threshold_value is None) == (self.threshold_sigma_multiplier is None):
                raise ValueError("threshold picking requires exactly one absolute or sigma threshold")
            if self.aic_variance_floor is not None:
                raise ValueError("threshold picking cannot carry AIC settings")
        else:
            if self.aic_variance_floor is None:
                raise ValueError("AIC picking requires a positive variance floor")
            if self.threshold_value is not None or self.threshold_sigma_multiplier is not None:
                raise ValueError("AIC picking cannot carry threshold settings")
        return self


def _mean(values):
    return sum(values) / len(values)


def _variance(values):
    mean = _mean(values)
    return sum((value - mean) ** 2 for value in values) / len(values)


def acoustic_emission_arrival_pick(x: AcousticEmissionArrivalPick) -> Calculation:
    reviews = (
        "waveform_clock_and_units_reviewed",
        "preprocessing_and_polarity_reviewed",
        "baseline_and_search_windows_reviewed",
        "pick_method_settings_reviewed",
        "provider_lineage_and_digests_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    if missing_reviews:
        return Calculation(
            status="needs_data",
            values={"pick_id": x.pick_id, "missing_reviews": missing_reviews},
            notes=("Arrival picking is withheld until waveform and algorithm settings are reviewed.",),
        )
    baseline_indices = [
        index for index, time in enumerate(x.elapsed_time_s) if x.baseline_start_s <= time <= x.baseline_end_s
    ]
    search_indices = [
        index for index, time in enumerate(x.elapsed_time_s) if x.search_start_s <= time <= x.search_end_s
    ]
    baseline_raw = [x.signal_values[index] for index in baseline_indices]
    baseline_mean = _mean(baseline_raw)
    processed = [
        value - baseline_mean if x.preprocessing == "demean_baseline" else value for value in x.signal_values
    ]

    def transformed(value):
        if x.polarity_basis == "positive":
            return value
        if x.polarity_basis == "negative":
            return -value
        return abs(value)

    detection = [transformed(value) for value in processed]
    baseline_detection = [detection[index] for index in baseline_indices]
    baseline_detection_mean = _mean(baseline_detection)
    baseline_rms = math.sqrt(_mean([value * value for value in baseline_detection]))
    baseline_sigma = math.sqrt(_variance(baseline_detection))
    pick_index = None
    method_diagnostic = {}
    if x.method == "threshold":
        threshold = (
            x.threshold_value
            if x.threshold_value is not None
            else baseline_detection_mean + x.threshold_sigma_multiplier * baseline_sigma
        )
        candidates = [index for index in search_indices if detection[index] >= threshold]
        if not candidates:
            return Calculation(
                status="out_of_scope",
                values={
                    "pick_id": x.pick_id,
                    "threshold": threshold,
                    "baseline_rms": baseline_rms,
                    "baseline_standard_deviation": baseline_sigma,
                    "search_peak": max(detection[index] for index in search_indices),
                },
                notes=("No original sample crossed the caller-declared threshold inside the search window.",),
            )
        pick_index = candidates[0]
        method_diagnostic = {
            "threshold": threshold,
            "threshold_excess": detection[pick_index] - threshold,
        }
    else:
        search_values = [processed[index] for index in search_indices]
        scores = []
        for split in range(2, len(search_values) - 1):
            left = search_values[:split]
            right = search_values[split:]
            score = split * math.log(max(_variance(left), x.aic_variance_floor)) + (
                len(search_values) - split
            ) * math.log(max(_variance(right), x.aic_variance_floor))
            scores.append((score, split))
        minimum_score, split = min(scores)
        pick_index = search_indices[split]
        ordered_scores = sorted(score for score, _ in scores)
        method_diagnostic = {
            "minimum_aic_score": minimum_score,
            "second_best_aic_score_gap": ordered_scores[1] - ordered_scores[0]
            if len(ordered_scores) > 1
            else None,
            "aic_variance_floor": x.aic_variance_floor,
        }
    sample_intervals = [b - a for a, b in zip(x.elapsed_time_s, x.elapsed_time_s[1:], strict=False)]
    local_interval = min(
        sample_intervals[max(0, pick_index - 1) : min(len(sample_intervals), pick_index + 1)]
    )
    search_peak = max(detection[index] for index in search_indices)
    return Calculation(
        values={
            "pick_id": x.pick_id,
            "acquisition_id": x.acquisition_id,
            "channel_id": x.channel_id,
            "clock_id": x.clock_id,
            "method": x.method,
            "pick_sample_index": pick_index,
            "pick_time_s": x.elapsed_time_s[pick_index],
            "sample_interval_uncertainty_bound_s": local_interval,
            "baseline_mean_raw_signal": baseline_mean,
            "baseline_rms": baseline_rms,
            "baseline_standard_deviation": baseline_sigma,
            "search_peak": search_peak,
            "peak_to_baseline_rms_ratio": search_peak / baseline_rms if baseline_rms > 0 else None,
            "method_diagnostic": method_diagnostic,
        },
        notes=(
            "The pick is tied to an original sample; no interpolation, filtering or event association is implicit.",
            "Baseline, preprocessing, polarity, threshold or AIC settings are caller inputs and are not optimized here.",
            "No event mechanism, classification, damage severity, acceptance, POD or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("AE arrival pick asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.acoustic_emission_arrival_pick",
            AcousticEmissionArrivalPick,
            acoustic_emission_arrival_pick,
            {
                "pick_id": "1",
                "acquisition_id": "1",
                "channel_id": "1",
                "clock_id": "1",
                "method": "1",
                "pick_sample_index": "index",
                "pick_time_s": "s",
                "sample_interval_uncertainty_bound_s": "s",
                "baseline_mean_raw_signal": "caller_signal_unit",
                "baseline_rms": "caller_signal_unit",
                "baseline_standard_deviation": "caller_signal_unit",
                "search_peak": "caller_signal_unit",
                "peak_to_baseline_rms_ratio": "1",
                "method_diagnostic": "mixed",
            },
            (
                "Caller-reviewed monotonic sample clock, waveform unit, immutable waveform digest and fixed windows.",
                "Threshold or AIC-family settings and preprocessing are explicit inputs, not inferred from outcomes.",
                "The result is one original-sample arrival pick and quality diagnostics, not an event classification.",
            ),
            ("deterministic_threshold_or_aic_acoustic_emission_pick",),
            context_validator=same_identity,
        )
    ]
