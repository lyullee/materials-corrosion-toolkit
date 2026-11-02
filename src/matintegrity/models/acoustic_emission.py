"""Acoustic-emission campaign records summarized without diagnostic inference."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec

Digest = str


class AcousticEmissionZone(Contract):
    zone_id: str = Field(min_length=1)
    coordinate_frame: str = Field(min_length=1)
    geometry_description: str = Field(min_length=1)
    geometry_state_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class AcousticEmissionSensorChannel(Contract):
    sensor_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    zone_ids: tuple[str, ...] = Field(min_length=1)
    coordinate_frame: str = Field(min_length=1)
    position_m: tuple[float, float, float]
    coupling_description: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def finite_unique_geometry(self):
        if not all(math.isfinite(value) for value in self.position_m):
            raise ValueError("acoustic-emission sensor coordinates must be finite")
        if len(self.zone_ids) != len(set(self.zone_ids)):
            raise ValueError("sensor zone identifiers must be unique")
        return self


class AcousticEmissionCalibrationRecord(Contract):
    calibration_id: str = Field(min_length=1)
    channel_ids: tuple[str, ...] = Field(min_length=1)
    source_location_coordinate_frame: str = Field(min_length=1)
    source_location_m: tuple[float, float, float]
    source_description: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        if len(self.channel_ids) != len(set(self.channel_ids)):
            raise ValueError("calibration channel identifiers must be unique")
        if not all(math.isfinite(value) for value in self.source_location_m):
            raise ValueError("calibration source coordinates must be finite")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid calibration record requires a basis")
        return self


class AcousticEmissionAcquisitionInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    active_channel_ids: tuple[str, ...] = Field(min_length=1)
    operating_state_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("acoustic-emission acquisition interval must have positive duration")
        if len(self.active_channel_ids) != len(set(self.active_channel_ids)):
            raise ValueError("active channel identifiers must be unique")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid acquisition interval requires a basis")
        return self


class AcousticEmissionEventFeatureRecord(Contract):
    event_id: str = Field(min_length=1)
    interval_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    event_time_s: Nonnegative
    feature_values: dict[str, float] = Field(min_length=1)
    feature_units: dict[str, str] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_features(self):
        if set(self.feature_values) != set(self.feature_units):
            raise ValueError("event feature values and unit tokens must have identical keys")
        if any(not name or not unit for name, unit in self.feature_units.items()):
            raise ValueError("event feature names and unit tokens cannot be empty")
        if any(not math.isfinite(value) for value in self.feature_values.values()):
            raise ValueError("event feature values must be finite")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid event-feature record requires a basis")
        return self


class AcousticEmissionSourceLocationRecord(Contract):
    location_record_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    coordinate_frame: str = Field(min_length=1)
    reported_location_m: tuple[float, float, float] | None = None
    expanded_uncertainty_m: Nonnegative | None = None
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: Digest | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_location(self):
        reported = (
            self.reported_location_m,
            self.expanded_uncertainty_m,
            self.result_digest,
        )
        if self.record_valid and any(value is None for value in reported):
            raise ValueError("a valid source-location record requires location, uncertainty and digest")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid source-location record requires a basis")
        if self.reported_location_m is not None and not all(
            math.isfinite(value) for value in self.reported_location_m
        ):
            raise ValueError("reported source coordinates must be finite")
        return self


class AcousticEmissionFeatureSupport(Contract):
    feature_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_value: float
    maximum_value: float

    @model_validator(mode="after")
    def finite_ordered_support(self):
        if not math.isfinite(self.minimum_value) or not math.isfinite(self.maximum_value):
            raise ValueError("feature-support bounds must be finite")
        if self.maximum_value < self.minimum_value:
            raise ValueError("feature-support bounds must be ordered")
        return self


class AcousticEmissionSupportEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    applicable_zone_ids: tuple[str, ...] = Field(min_length=1)
    applicable_channel_ids: tuple[str, ...] = Field(min_length=1)
    feature_support: tuple[AcousticEmissionFeatureSupport, ...] = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    configuration_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    data_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: Digest = Field(pattern=r"^[a-f0-9]{64}$")
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_support(self):
        for values, label in (
            (self.applicable_zone_ids, "zone"),
            (self.applicable_channel_ids, "channel"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"support-envelope {label} identifiers must be unique")
        keys = [(row.feature_id, row.unit_token) for row in self.feature_support]
        if len(keys) != len(set(keys)):
            raise ValueError("feature-support keys must be unique")
        return self


class AcousticEmissionCampaign(Contract):
    campaign_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    zones: tuple[AcousticEmissionZone, ...] = Field(min_length=1)
    sensors: tuple[AcousticEmissionSensorChannel, ...] = Field(min_length=1)
    calibrations: tuple[AcousticEmissionCalibrationRecord, ...] = Field(min_length=1)
    acquisition_intervals: tuple[AcousticEmissionAcquisitionInterval, ...] = Field(min_length=1)
    event_records: tuple[AcousticEmissionEventFeatureRecord, ...] = Field(default_factory=tuple)
    source_location_records: tuple[AcousticEmissionSourceLocationRecord, ...] = Field(default_factory=tuple)
    support_envelope: AcousticEmissionSupportEnvelope
    asset_zone_geometry_reviewed: bool
    sensor_channel_mapping_reviewed: bool
    sensor_coupling_reviewed: bool
    calibration_evidence_reviewed: bool
    acquisition_intervals_reviewed: bool
    event_feature_definitions_reviewed: bool
    source_location_evidence_reviewed: bool
    provider_and_digest_lineage_reviewed: bool
    support_envelope_authority_reviewed: bool

    @model_validator(mode="after")
    def unique_primary_identifiers(self):
        collections = (
            ([row.zone_id for row in self.zones], "zone"),
            ([row.sensor_id for row in self.sensors], "sensor"),
            ([row.channel_id for row in self.sensors], "channel"),
            ([row.calibration_id for row in self.calibrations], "calibration"),
            ([row.interval_id for row in self.acquisition_intervals], "interval"),
            ([row.event_id for row in self.event_records], "event"),
            ([row.location_record_id for row in self.source_location_records], "location record"),
        )
        for identifiers, label in collections:
            if len(identifiers) != len(set(identifiers)):
                raise ValueError(f"acoustic-emission {label} identifiers must be unique")
        return self


def acoustic_emission_campaign(x: AcousticEmissionCampaign) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "asset_zone_geometry_reviewed",
            "sensor_channel_mapping_reviewed",
            "sensor_coupling_reviewed",
            "calibration_evidence_reviewed",
            "acquisition_intervals_reviewed",
            "event_feature_definitions_reviewed",
            "source_location_evidence_reviewed",
            "provider_and_digest_lineage_reviewed",
            "support_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    zone_ids = {row.zone_id for row in x.zones}
    channel_ids = {row.channel_id for row in x.sensors}
    interval_by_id = {row.interval_id: row for row in x.acquisition_intervals}
    calibration_by_id = {row.calibration_id: row for row in x.calibrations}
    event_ids = {row.event_id for row in x.event_records}
    calibration_ids = {row.calibration_id for row in x.calibrations}
    invalid_records = [
        *(f"calibration:{row.calibration_id}" for row in x.calibrations if not row.record_valid),
        *(f"interval:{row.interval_id}" for row in x.acquisition_intervals if not row.record_valid),
        *(f"event:{row.event_id}" for row in x.event_records if not row.record_valid),
        *(
            f"source_location:{row.location_record_id}"
            for row in x.source_location_records
            if not row.record_valid
        ),
    ]
    missing_references = []
    for sensor in x.sensors:
        missing_references.extend(
            f"sensor:{sensor.sensor_id}:zone:{zone_id}"
            for zone_id in sensor.zone_ids
            if zone_id not in zone_ids
        )
        if sensor.calibration_id not in calibration_ids:
            missing_references.append(f"sensor:{sensor.sensor_id}:calibration:{sensor.calibration_id}")
        elif sensor.channel_id not in calibration_by_id[sensor.calibration_id].channel_ids:
            missing_references.append(f"sensor:{sensor.sensor_id}:calibration_channel:{sensor.channel_id}")
    for calibration in x.calibrations:
        missing_references.extend(
            f"calibration:{calibration.calibration_id}:channel:{channel_id}"
            for channel_id in calibration.channel_ids
            if channel_id not in channel_ids
        )
    for interval in x.acquisition_intervals:
        missing_references.extend(
            f"interval:{interval.interval_id}:channel:{channel_id}"
            for channel_id in interval.active_channel_ids
            if channel_id not in channel_ids
        )
    for event in x.event_records:
        if event.interval_id not in interval_by_id:
            missing_references.append(f"event:{event.event_id}:interval:{event.interval_id}")
        else:
            interval = interval_by_id[event.interval_id]
            if event.channel_id not in interval.active_channel_ids:
                missing_references.append(f"event:{event.event_id}:inactive_channel:{event.channel_id}")
            if not interval.start_time_s <= event.event_time_s <= interval.end_time_s:
                missing_references.append(f"event:{event.event_id}:time_outside_interval")
        if event.channel_id not in channel_ids:
            missing_references.append(f"event:{event.event_id}:channel:{event.channel_id}")
        if event.zone_id not in zone_ids:
            missing_references.append(f"event:{event.event_id}:zone:{event.zone_id}")
    for location in x.source_location_records:
        if location.event_id not in event_ids:
            missing_references.append(
                f"source_location:{location.location_record_id}:event:{location.event_id}"
            )
        if location.zone_id not in zone_ids:
            missing_references.append(
                f"source_location:{location.location_record_id}:zone:{location.zone_id}"
            )

    support = {(row.feature_id, row.unit_token): row for row in x.support_envelope.feature_support}
    missing_feature_support = []
    outside_support_rows = []
    event_rows = []
    for event in x.event_records:
        if not event.record_valid:
            continue
        event_outside = (
            event.zone_id not in x.support_envelope.applicable_zone_ids
            or event.channel_id not in x.support_envelope.applicable_channel_ids
        )
        feature_rows = []
        for feature_id, value in event.feature_values.items():
            unit = event.feature_units[feature_id]
            declared = support.get((feature_id, unit))
            if declared is None:
                missing_feature_support.append(f"event:{event.event_id}:feature:{feature_id}:{unit}")
                continue
            within = declared.minimum_value <= value <= declared.maximum_value
            if not within:
                event_outside = True
                outside_support_rows.append(f"event:{event.event_id}:feature:{feature_id}")
            feature_rows.append(
                {
                    "feature_id": feature_id,
                    "value": value,
                    "unit_token": unit,
                    "within_declared_support": within,
                }
            )
        if event_outside:
            outside_support_rows.append(f"event:{event.event_id}:geometry")
        event_rows.append(
            {
                "event_id": event.event_id,
                "interval_id": event.interval_id,
                "zone_id": event.zone_id,
                "channel_id": event.channel_id,
                "event_time_s": event.event_time_s,
                "features": feature_rows,
                "within_declared_support": not event_outside,
            }
        )

    total_valid_duration = sum(
        row.end_time_s - row.start_time_s for row in x.acquisition_intervals if row.record_valid
    )
    if missing_reviews or invalid_records or missing_references or missing_feature_support:
        status = "needs_data"
    elif outside_support_rows:
        status = "out_of_scope"
    else:
        status = "computed"
    return Calculation(
        status=status,
        values={
            "campaign_id": x.campaign_id,
            "valid_acquisition_duration_s": total_valid_duration,
            "valid_event_count": len(event_rows),
            "valid_source_location_record_count": sum(row.record_valid for row in x.source_location_records),
            "event_feature_summary": event_rows,
            "invalid_record_ids": invalid_records,
            "missing_reference_records": missing_references,
            "missing_feature_support_records": missing_feature_support,
            "outside_declared_support_records": sorted(set(outside_support_rows)),
            "missing_reviews": missing_reviews,
        },
        notes=(
            "The output is a technical inventory and caller-envelope comparison of recorded acoustic-emission features.",
            "Reported source locations and uncertainties are preserved as provider results; localization accuracy is not established.",
            "No defect class, leak source, probability of detection, remaining life, event probability or acceptance is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("acoustic-emission asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.acoustic_emission_campaign",
            AcousticEmissionCampaign,
            acoustic_emission_campaign,
            {
                "campaign_id": "1",
                "valid_acquisition_duration_s": "s",
                "valid_event_count": "1",
                "valid_source_location_record_count": "1",
                "event_feature_summary": "mixed",
                "invalid_record_ids": "1",
                "missing_reference_records": "1",
                "missing_feature_support_records": "1",
                "outside_declared_support_records": "1",
                "missing_reviews": "1",
            },
            (
                "Asset geometry, zones, sensors, channels, acquisition intervals and event features are reviewed caller records.",
                "Calibration and source-location results retain exact provider, configuration, data and result digests.",
            ),
            ("reviewed_acoustic_emission_campaign_summary",),
            context_validator=same_identity,
        )
    ]
