"""TOFD acquisition records and symmetric straight-path geometry descriptors."""

from __future__ import annotations

import math
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec


class TofdProbePair(Contract):
    pair_id: str = Field(min_length=1)
    transmit_probe_id: str = Field(min_length=1)
    receive_probe_id: str = Field(min_length=1)
    transmit_wedge_id: str = Field(min_length=1)
    receive_wedge_id: str = Field(min_length=1)
    probe_index_separation_m: Positive
    center_frequency_Hz: Positive
    nominal_refracted_angle_rad: float = Field(gt=0, lt=math.pi / 2)
    index_separation_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def separate_roles(self):
        if self.transmit_probe_id == self.receive_probe_id:
            raise ValueError("TOFD transmit and receive probes must have distinct identities")
        if self.transmit_wedge_id == self.receive_wedge_id:
            raise ValueError("TOFD transmit and receive wedges must have distinct identities")
        return self


class EncodedTofdFrame(Contract):
    frame_id: str = Field(min_length=1)
    encoder_position_m: float
    data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_count: int = Field(gt=0)
    sample_interval_s: Positive
    amplitude_encoding: str = Field(min_length=1)
    time_zero_basis: str = Field(min_length=1)
    lateral_wave_arrival_time_s: Positive | None = None
    backwall_echo_arrival_time_s: Positive | None = None

    @model_validator(mode="after")
    def ordered_reference_arrivals(self):
        if (
            self.lateral_wave_arrival_time_s is not None
            and self.backwall_echo_arrival_time_s is not None
            and self.backwall_echo_arrival_time_s <= self.lateral_wave_arrival_time_s
        ):
            raise ValueError("TOFD backwall arrival must follow the lateral-wave arrival")
        return self


class TofdDiffractionPick(Contract):
    pick_id: str = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    reported_role: Literal["upper_tip", "lower_tip", "unclassified_diffraction"]
    arrival_time_s: Positive
    picking_basis: str = Field(min_length=1)
    reported_amplitude: float | None = None
    amplitude_unit: str | None = Field(default=None, min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def amplitude_unit_pair(self):
        if (self.reported_amplitude is None) != (self.amplitude_unit is None):
            raise ValueError("TOFD amplitude and its unit must be supplied together")
        return self


class TofdIndication(Contract):
    indication_id: str = Field(min_length=1)
    upper_tip_pick_id: str | None = Field(default=None, min_length=1)
    lower_tip_pick_id: str | None = Field(default=None, min_length=1)
    reported_indication_type: str = Field(min_length=1)
    acquisition_location_description: str = Field(min_length=1)
    physical_location_id: str | None = Field(default=None, min_length=1)
    object_mapping_basis: str | None = Field(default=None, min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_pick_and_location_mapping(self):
        if self.upper_tip_pick_id is None and self.lower_tip_pick_id is None:
            raise ValueError("TOFD indication requires at least one diffraction pick")
        if self.upper_tip_pick_id == self.lower_tip_pick_id:
            raise ValueError("upper and lower TOFD tip picks must be distinct")
        if (self.physical_location_id is None) != (self.object_mapping_basis is None):
            raise ValueError("physical location and object-mapping basis must be supplied together")
        return self


class TofdExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_longitudinal_velocity_m_s: Positive
    specimen_velocity_basis: str = Field(min_length=1)
    wall_thickness_m: Positive
    wall_thickness_basis: str = Field(min_length=1)
    probe_pair: TofdProbePair
    encoder_id: str = Field(min_length=1)
    encoder_direction: Literal["increasing", "decreasing"]
    frames: list[EncodedTofdFrame] = Field(min_length=1)
    diffraction_picks: list[TofdDiffractionPick] = Field(default_factory=list)
    indications: list[TofdIndication] = Field(default_factory=list)
    probe_pair_identity_reviewed: bool
    specimen_velocity_reviewed: bool
    wall_thickness_reviewed: bool
    encoder_calibration_reviewed: bool
    acquisition_calibration_reviewed: bool
    frame_identity_reviewed: bool
    time_picks_reviewed: bool
    indication_mapping_reviewed: bool
    symmetric_path_applicable: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_identities_and_roles(self):
        frame_ids = [item.frame_id for item in self.frames]
        pick_ids = [item.pick_id for item in self.diffraction_picks]
        indication_ids = [item.indication_id for item in self.indications]
        for values, label in (
            (frame_ids, "frame"),
            (pick_ids, "diffraction pick"),
            (indication_ids, "indication"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"TOFD {label} IDs must be unique")
        if {item.frame_id for item in self.diffraction_picks} - set(frame_ids):
            raise ValueError("every TOFD diffraction pick must reference a declared frame")
        positions = [item.encoder_position_m for item in self.frames]
        differences = [right - left for left, right in zip(positions, positions[1:], strict=False)]
        if self.encoder_direction == "increasing" and any(value < 0 for value in differences):
            raise ValueError("TOFD encoder positions contradict the increasing direction")
        if self.encoder_direction == "decreasing" and any(value > 0 for value in differences):
            raise ValueError("TOFD encoder positions contradict the decreasing direction")
        picks = {item.pick_id: item for item in self.diffraction_picks}
        used: list[str] = []
        for indication in self.indications:
            for identity, expected_role in (
                (indication.upper_tip_pick_id, "upper_tip"),
                (indication.lower_tip_pick_id, "lower_tip"),
            ):
                if identity is None:
                    continue
                if identity not in picks:
                    raise ValueError("every TOFD indication pick must be declared")
                if picks[identity].reported_role != expected_role:
                    raise ValueError("TOFD indication tip role conflicts with the referenced pick")
                used.append(identity)
        if len(set(used)) != len(used):
            raise ValueError("one TOFD tip pick cannot be assigned to multiple indications")
        return self


def _symmetric_depth(separation: float, velocity: float, delay: float) -> float:
    increment = velocity * delay / 2
    return math.sqrt(increment * (separation + increment))


def tofd_acquisition_summary(x: TofdExamination) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "probe_pair_identity_reviewed",
            "specimen_velocity_reviewed",
            "wall_thickness_reviewed",
            "encoder_calibration_reviewed",
            "acquisition_calibration_reviewed",
            "frame_identity_reviewed",
            "time_picks_reviewed",
            "indication_mapping_reviewed",
            "symmetric_path_applicable",
        )
        if not getattr(x, name)
    ]
    if not x.indications and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")
    unmapped_indications = [item.indication_id for item in x.indications if item.physical_location_id is None]

    separation = x.probe_pair.probe_index_separation_m
    velocity = x.specimen_longitudinal_velocity_m_s
    backwall_path = 2 * math.hypot(separation / 2, x.wall_thickness_m)
    frames = {item.frame_id: item for item in x.frames}
    backwall_diagnostics = {}
    for frame in x.frames:
        if frame.lateral_wave_arrival_time_s is None or frame.backwall_echo_arrival_time_s is None:
            continue
        delay = frame.backwall_echo_arrival_time_s - frame.lateral_wave_arrival_time_s
        equivalent_depth = _symmetric_depth(separation, velocity, delay)
        backwall_diagnostics[frame.frame_id] = {
            "measured_backwall_delay_from_lateral_s": delay,
            "equivalent_backwall_depth_m": equivalent_depth,
            "equivalent_depth_minus_declared_wall_m": equivalent_depth - x.wall_thickness_m,
        }

    depths: dict[str, float | None] = {}
    invalid_pick_ids = []
    for pick in x.diffraction_picks:
        lateral = frames[pick.frame_id].lateral_wave_arrival_time_s
        if lateral is None or pick.arrival_time_s <= lateral:
            depths[pick.pick_id] = None
            invalid_pick_ids.append(pick.pick_id)
        else:
            depths[pick.pick_id] = _symmetric_depth(separation, velocity, pick.arrival_time_s - lateral)

    indication_geometry = {}
    inconsistent_indication_ids = []
    for indication in x.indications:
        upper = depths.get(indication.upper_tip_pick_id) if indication.upper_tip_pick_id else None
        lower = depths.get(indication.lower_tip_pick_id) if indication.lower_tip_pick_id else None
        height = None
        if upper is not None and lower is not None:
            if lower < upper:
                inconsistent_indication_ids.append(indication.indication_id)
            else:
                height = lower - upper
        deepest = lower if lower is not None else upper
        indication_geometry[indication.indication_id] = {
            "upper_tip_depth_m": upper,
            "lower_tip_depth_m": lower,
            "tip_separation_height_m": height,
            "remaining_backwall_ligament_m": (x.wall_thickness_m - deepest if deepest is not None else None),
        }

    positions = [item.encoder_position_m for item in x.frames]
    increments = [abs(right - left) for left, right in zip(positions, positions[1:], strict=False)]
    nonzero_increments = [value for value in increments if value > 0]
    status = (
        "needs_data"
        if missing_reviews or unmapped_indications or invalid_pick_ids or inconsistent_indication_ids
        else "computed"
    )
    return Calculation(
        status=status,
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "physical_scope_id": x.physical_scope_id,
            "probe_pair_id": x.probe_pair.pair_id,
            "direct_lateral_path_length_m": separation,
            "declared_wall_backwall_path_length_m": backwall_path,
            "declared_wall_backwall_delay_from_lateral_s": (backwall_path - separation) / velocity,
            "backwall_timing_diagnostics_by_frame_id": backwall_diagnostics,
            "tip_depth_by_pick_id": depths,
            "indication_geometry_by_id": indication_geometry,
            "frame_count": len(x.frames),
            "diffraction_pick_count": len(x.diffraction_picks),
            "diffraction_pick_count_by_role": dict(
                Counter(item.reported_role for item in x.diffraction_picks)
            ),
            "indication_count": len(x.indications),
            "unique_encoder_position_count": len(set(positions)),
            "duplicate_adjacent_encoder_position_count": sum(value == 0 for value in increments),
            "encoder_span_m": abs(positions[-1] - positions[0]),
            "minimum_nonzero_encoder_increment_m": min(nonzero_increments, default=None),
            "maximum_nonzero_encoder_increment_m": max(nonzero_increments, default=None),
            "invalid_pick_ids": invalid_pick_ids,
            "inconsistent_indication_ids": inconsistent_indication_ids,
            "unmapped_indication_ids": unmapped_indications,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Depths use symmetric straight longitudinal paths beneath the probe midpoint and a same-frame lateral-wave time reference.",
            "Backwall timing is a geometry diagnostic, not calibration acceptance, near-surface coverage or dead-zone qualification.",
            "No waveform processing, automated picking, flaw identity, acceptance, POD, remaining life or failure probability is produced.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.tofd_acquisition_summary",
            TofdExamination,
            tofd_acquisition_summary,
            {
                "direct_lateral_path_length_m": "m",
                "declared_wall_backwall_path_length_m": "m",
                "declared_wall_backwall_delay_from_lateral_s": "s",
                "tip_depth_by_pick_id": "m",
                "indication_geometry_by_id": "mixed; see nested field names",
                "encoder_span_m": "m",
                "minimum_nonzero_encoder_increment_m": "m",
                "maximum_nonzero_encoder_increment_m": "m",
            },
            (
                "Caller-controlled TOFD probe pair, velocity, wall, encoder, frame, time-pick and indication record; symmetric straight paths only.",
            ),
            ("tofd_acquisition_definition",),
        )
    ]
