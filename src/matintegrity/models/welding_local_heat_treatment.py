"""Local heat-treatment records checked against caller-owned procedure envelopes."""

from __future__ import annotations

from itertools import combinations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class LocalHeatTreatmentProcedureEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    treatment_procedure_id: str = Field(min_length=1)
    qualified_heat_zone_ids: tuple[str, ...] = Field(min_length=1)
    minimum_hold_temperature_K: Positive
    maximum_hold_temperature_K: Positive
    minimum_hold_duration_s: Nonnegative
    maximum_heating_rate_K_s: Positive
    maximum_cooling_rate_K_s: Positive
    maximum_spatial_gradient_K_m: Positive
    procedure_provider_id: str = Field(min_length=1)
    procedure_provider_version: str = Field(min_length=1)
    procedure_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_and_unique(self):
        if self.maximum_hold_temperature_K < self.minimum_hold_temperature_K:
            raise ValueError("local-heat-treatment hold-temperature bounds must be ordered")
        if len(self.qualified_heat_zone_ids) != len(set(self.qualified_heat_zone_ids)):
            raise ValueError("qualified heat-zone identifiers must be unique")
        return self


class LocalHeatTreatmentSensorHistory(Contract):
    sensor_id: str = Field(min_length=1)
    heat_zone_id: str = Field(min_length=1)
    sensor_position_m: Nonnegative
    time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    temperature_K: tuple[Positive, ...] = Field(min_length=2)
    acquisition_provider_id: str = Field(min_length=1)
    acquisition_provider_version: str = Field(min_length=1)
    acquisition_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_history(self):
        if len(self.time_s) != len(self.temperature_K):
            raise ValueError("sensor time and temperature arrays must have equal length")
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("sensor times must be strictly increasing")
        return self


class LocalHeatTreatmentAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    weld_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    treatment_procedure_id: str = Field(min_length=1)
    sensor_histories: tuple[LocalHeatTreatmentSensorHistory, ...] = Field(min_length=2)
    candidate_envelopes: tuple[LocalHeatTreatmentProcedureEnvelope, ...] = Field(min_length=1)
    sensor_layout_reviewed: bool
    time_and_temperature_records_reviewed: bool
    material_and_joint_identity_reviewed: bool
    procedure_identity_reviewed: bool
    provider_state_digests_reviewed: bool
    procedure_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_and_aligned_records(self):
        sensor_ids = [row.sensor_id for row in self.sensor_histories]
        if len(sensor_ids) != len(set(sensor_ids)):
            raise ValueError("local-heat-treatment sensor identifiers must be unique")
        envelope_ids = [row.envelope_id for row in self.candidate_envelopes]
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("local-heat-treatment envelope identifiers must be unique")

        for zone_id in {row.heat_zone_id for row in self.sensor_histories}:
            zone = [row for row in self.sensor_histories if row.heat_zone_id == zone_id]
            if len(zone) < 2:
                raise ValueError("each heat zone requires at least two sensor histories")
            if len({row.sensor_position_m for row in zone}) != len(zone):
                raise ValueError("sensor positions must be unique within each heat zone")
            reference_time = zone[0].time_s
            if any(row.time_s != reference_time for row in zone[1:]):
                raise ValueError("sensor time arrays must be aligned within each heat zone")
        return self


def _identity(envelope: LocalHeatTreatmentProcedureEnvelope):
    return (
        envelope.material_condition_id,
        envelope.joint_configuration_id,
        envelope.treatment_procedure_id,
    )


def _history_metrics(
    history: LocalHeatTreatmentSensorHistory,
    envelope: LocalHeatTreatmentProcedureEnvelope,
):
    rates = [
        (right_temperature - left_temperature) / (right_time - left_time)
        for left_time, right_time, left_temperature, right_temperature in zip(
            history.time_s[:-1],
            history.time_s[1:],
            history.temperature_K[:-1],
            history.temperature_K[1:],
            strict=True,
        )
    ]
    hold_duration = 0.0
    for left_time, right_time, left_temperature, right_temperature in zip(
        history.time_s[:-1],
        history.time_s[1:],
        history.temperature_K[:-1],
        history.temperature_K[1:],
        strict=True,
    ):
        duration = right_time - left_time
        temperature_change = right_temperature - left_temperature
        if temperature_change == 0.0:
            if envelope.minimum_hold_temperature_K <= left_temperature <= envelope.maximum_hold_temperature_K:
                hold_duration += duration
            continue
        band_fraction_at_left = (envelope.minimum_hold_temperature_K - left_temperature) / temperature_change
        band_fraction_at_right = (envelope.maximum_hold_temperature_K - left_temperature) / temperature_change
        segment_start = max(0.0, min(band_fraction_at_left, band_fraction_at_right))
        segment_end = min(1.0, max(band_fraction_at_left, band_fraction_at_right))
        hold_duration += max(0.0, segment_end - segment_start) * duration
    return {
        "sensor_id": history.sensor_id,
        "heat_zone_id": history.heat_zone_id,
        "sensor_position_m": history.sensor_position_m,
        "maximum_heating_rate_K_s": max(0.0, max(rates)),
        "maximum_cooling_rate_K_s": max(0.0, -min(rates)),
        "hold_band_duration_s": hold_duration,
    }


def _zone_gradient_metrics(histories: list[LocalHeatTreatmentSensorHistory]):
    gradients = []
    for time_index, time_s in enumerate(histories[0].time_s):
        maximum = max(
            abs(left.temperature_K[time_index] - right.temperature_K[time_index])
            / abs(left.sensor_position_m - right.sensor_position_m)
            for left, right in combinations(histories, 2)
        )
        gradients.append({"time_s": time_s, "maximum_spatial_gradient_K_m": maximum})
    maximum_row = max(gradients, key=lambda row: row["maximum_spatial_gradient_K_m"])
    return {
        "heat_zone_id": histories[0].heat_zone_id,
        "maximum_spatial_gradient_K_m": maximum_row["maximum_spatial_gradient_K_m"],
        "maximum_gradient_time_s": maximum_row["time_s"],
    }


def local_heat_treatment(x: LocalHeatTreatmentAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "sensor_layout_reviewed",
            "time_and_temperature_records_reviewed",
            "material_and_joint_identity_reviewed",
            "procedure_identity_reviewed",
            "provider_state_digests_reviewed",
            "procedure_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    target_identity = (
        x.material_condition_id,
        x.joint_configuration_id,
        x.treatment_procedure_id,
    )
    identity_matches = [row for row in x.candidate_envelopes if _identity(row) == target_identity]
    recorded_zones = {row.heat_zone_id for row in x.sensor_histories}
    supported = [row for row in identity_matches if set(row.qualified_heat_zone_ids) == recorded_zones]
    selection_values = {
        "assessment_id": x.assessment_id,
        "identity_matching_envelope_ids": [row.envelope_id for row in identity_matches],
        "supported_envelope_ids": [row.envelope_id for row in supported],
        "recorded_heat_zone_ids": sorted(recorded_zones),
        "missing_reviews": missing_reviews,
    }
    if missing_reviews or not identity_matches or len(supported) > 1:
        return Calculation(
            status="needs_data",
            values=selection_values,
            notes=("A unique reviewed caller-owned local-treatment envelope is required.",),
        )
    if not supported:
        return Calculation(
            status="out_of_scope",
            values=selection_values,
            notes=("Recorded heat zones are outside the matching procedure envelope.",),
        )

    envelope = supported[0]
    sensor_metrics = [_history_metrics(row, envelope) for row in x.sensor_histories]
    zone_metrics = [
        _zone_gradient_metrics([row for row in x.sensor_histories if row.heat_zone_id == zone_id])
        for zone_id in sorted(recorded_zones)
    ]
    maximum_heating_rate = max(row["maximum_heating_rate_K_s"] for row in sensor_metrics)
    maximum_cooling_rate = max(row["maximum_cooling_rate_K_s"] for row in sensor_metrics)
    minimum_hold_duration = min(row["hold_band_duration_s"] for row in sensor_metrics)
    maximum_spatial_gradient = max(row["maximum_spatial_gradient_K_m"] for row in zone_metrics)
    within = (
        maximum_heating_rate <= envelope.maximum_heating_rate_K_s
        and maximum_cooling_rate <= envelope.maximum_cooling_rate_K_s
        and minimum_hold_duration >= envelope.minimum_hold_duration_s
        and maximum_spatial_gradient <= envelope.maximum_spatial_gradient_K_m
    )
    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "selected_envelope_id": envelope.envelope_id,
            "sensor_metrics": sensor_metrics,
            "heat_zone_metrics": zone_metrics,
            "maximum_heating_rate_K_s": maximum_heating_rate,
            "maximum_cooling_rate_K_s": maximum_cooling_rate,
            "minimum_sensor_hold_band_duration_s": minimum_hold_duration,
            "maximum_spatial_gradient_K_m": maximum_spatial_gradient,
            "record_within_declared_procedure_envelope": within,
        },
        notes=(
            "Hold duration linearly interpolates adjacent recorded temperatures to estimate time inside the caller-declared band.",
            "This assumes a linear temperature path between samples and cannot detect unrecorded peaks or oscillations.",
            "The comparison does not establish metallurgical response, code compliance, equipment capability or production acceptance.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("local-treatment asset and location must match the run context")

    return [
        ModelSpec(
            "welding.local_heat_treatment",
            LocalHeatTreatmentAssessment,
            local_heat_treatment,
            {
                "assessment_id": "1",
                "selected_envelope_id": "1",
                "maximum_heating_rate_K_s": "K/s",
                "maximum_cooling_rate_K_s": "K/s",
                "minimum_sensor_hold_band_duration_s": "s",
                "maximum_spatial_gradient_K_m": "K/m",
                "record_within_declared_procedure_envelope": "1",
            },
            (
                "Sensor positions and synchronized histories are reviewed caller records.",
                "Treatment bounds and heat-zone applicability are supplied by a reviewed caller-owned procedure envelope.",
            ),
            ("reviewed_local_heat_treatment_record_comparison",),
            context_validator=same_identity,
        )
    ]
