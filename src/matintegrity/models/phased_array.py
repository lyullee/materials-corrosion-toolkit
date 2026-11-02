"""Encoded phased-array acquisition records without hidden imaging or acceptance rules."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class PhasedArrayProbe(Contract):
    probe_id: str = Field(min_length=1)
    role: Literal["pulse_echo", "transmit", "receive"]
    element_count: int = Field(gt=0)
    element_pitch_m: Positive
    element_width_m: Positive
    center_frequency_Hz: Positive
    element_layout_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class PhasedArrayWedge(Contract):
    wedge_id: str = Field(min_length=1)
    probe_id: str = Field(min_length=1)
    wedge_material_id: str = Field(min_length=1)
    wedge_longitudinal_velocity_m_s: Positive
    nominal_exit_point_offset_m: float
    mounting_orientation: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class PhasedArrayBeamLaw(Contract):
    law_id: str = Field(min_length=1)
    transmit_probe_id: str = Field(min_length=1)
    receive_probe_id: str = Field(min_length=1)
    refracted_angle_rad: float
    refracted_wave_mode: Literal["longitudinal", "shear"]
    focus_distance_m: Positive | None = None
    first_transmit_element: int = Field(ge=0)
    transmit_element_count: int = Field(gt=0)
    transmit_delay_s: list[Nonnegative] = Field(min_length=1)
    first_receive_element: int = Field(ge=0)
    receive_element_count: int = Field(gt=0)
    receive_delay_s: list[Nonnegative] = Field(min_length=1)
    law_generation_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def delay_lengths(self):
        if len(self.transmit_delay_s) != self.transmit_element_count:
            raise ValueError("transmit delay count must match active transmit elements")
        if len(self.receive_delay_s) != self.receive_element_count:
            raise ValueError("receive delay count must match active receive elements")
        return self


class EncodedPhasedArrayFrame(Contract):
    frame_id: str = Field(min_length=1)
    encoder_position_m: float
    beam_law_id: str | None = Field(default=None, min_length=1)
    data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_count: int = Field(gt=0)
    sample_interval_s: Positive
    transmit_event_count: int = Field(gt=0)
    receive_channel_count: int = Field(gt=0)
    amplitude_encoding: str = Field(min_length=1)
    time_zero_basis: str = Field(min_length=1)


class PhasedArrayIndication(Contract):
    indication_id: str = Field(min_length=1)
    frame_ids: list[str] = Field(min_length=1)
    reported_indication_type: str = Field(min_length=1)
    acquisition_location_description: str = Field(min_length=1)
    physical_location_id: str | None = Field(default=None, min_length=1)
    object_mapping_basis: str | None = Field(default=None, min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_mapping_and_unique_frames(self):
        if len(set(self.frame_ids)) != len(self.frame_ids):
            raise ValueError("indication frame references must be unique")
        if (self.physical_location_id is None) != (self.object_mapping_basis is None):
            raise ValueError("physical location and object-mapping basis must be supplied together")
        return self


class PhasedArrayExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    acquisition_mode: Literal["sectorial", "linear", "transmit_receive", "full_matrix_capture"]
    specimen_wave_velocity_m_s: Positive
    specimen_wave_velocity_basis: str = Field(min_length=1)
    encoder_id: str = Field(min_length=1)
    encoder_direction: Literal["increasing", "decreasing"]
    probes: list[PhasedArrayProbe] = Field(min_length=1)
    wedges: list[PhasedArrayWedge] = Field(min_length=1)
    beam_laws: list[PhasedArrayBeamLaw] = Field(default_factory=list)
    frames: list[EncodedPhasedArrayFrame] = Field(min_length=1)
    indications: list[PhasedArrayIndication] = Field(default_factory=list)
    probe_and_wedge_identity_reviewed: bool
    material_velocity_reviewed: bool
    beam_law_reviewed: bool
    encoder_calibration_reviewed: bool
    acquisition_calibration_reviewed: bool
    frame_identity_reviewed: bool
    indication_mapping_reviewed: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_identities_and_order(self):
        probe_ids = [item.probe_id for item in self.probes]
        wedge_ids = [item.wedge_id for item in self.wedges]
        law_ids = [item.law_id for item in self.beam_laws]
        frame_ids = [item.frame_id for item in self.frames]
        indication_ids = [item.indication_id for item in self.indications]
        for values, label in (
            (probe_ids, "probe"),
            (wedge_ids, "wedge"),
            (law_ids, "beam law"),
            (frame_ids, "frame"),
            (indication_ids, "indication"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"{label} IDs must be unique")
        probe_id_set = set(probe_ids)
        if {item.probe_id for item in self.wedges} - probe_id_set:
            raise ValueError("every wedge must reference a declared probe")
        probe_by_id = {item.probe_id: item for item in self.probes}
        for law in self.beam_laws:
            if {law.transmit_probe_id, law.receive_probe_id} - probe_id_set:
                raise ValueError("every beam law must reference declared probes")
            transmit = probe_by_id[law.transmit_probe_id]
            receive = probe_by_id[law.receive_probe_id]
            if law.first_transmit_element + law.transmit_element_count > transmit.element_count:
                raise ValueError("active transmit aperture exceeds the referenced probe")
            if law.first_receive_element + law.receive_element_count > receive.element_count:
                raise ValueError("active receive aperture exceeds the referenced probe")
        if self.acquisition_mode == "full_matrix_capture":
            if any(item.beam_law_id is not None for item in self.frames):
                raise ValueError("full-matrix frames cannot reference precomputed beam laws")
        else:
            if not self.beam_laws:
                raise ValueError("conventional phased-array acquisition requires beam laws")
            if any(item.beam_law_id is None for item in self.frames):
                raise ValueError("every conventional frame must reference a beam law")
        if {item.beam_law_id for item in self.frames if item.beam_law_id} - set(law_ids):
            raise ValueError("every frame beam-law reference must be declared")
        positions = [item.encoder_position_m for item in self.frames]
        differences = [right - left for left, right in zip(positions, positions[1:], strict=False)]
        if self.encoder_direction == "increasing" and any(value < 0 for value in differences):
            raise ValueError("encoder positions contradict the declared increasing direction")
        if self.encoder_direction == "decreasing" and any(value > 0 for value in differences):
            raise ValueError("encoder positions contradict the declared decreasing direction")
        frame_id_set = set(frame_ids)
        if {frame_id for indication in self.indications for frame_id in indication.frame_ids} - frame_id_set:
            raise ValueError("every indication must reference declared frames")
        return self


def phased_array_acquisition_summary(x: PhasedArrayExamination) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "probe_and_wedge_identity_reviewed",
            "material_velocity_reviewed",
            "beam_law_reviewed",
            "encoder_calibration_reviewed",
            "acquisition_calibration_reviewed",
            "frame_identity_reviewed",
            "indication_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
    if not x.indications and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")
    unmapped_indication_ids = [
        item.indication_id for item in x.indications if item.physical_location_id is None
    ]
    positions = [item.encoder_position_m for item in x.frames]
    increments = [abs(right - left) for left, right in zip(positions, positions[1:], strict=False)]
    nonzero_increments = [value for value in increments if value > 0]
    probe_values = {
        probe.probe_id: {
            "physical_aperture_m": (probe.element_count - 1) * probe.element_pitch_m + probe.element_width_m,
            "nominal_specimen_wavelength_m": x.specimen_wave_velocity_m_s / probe.center_frequency_Hz,
            "pitch_to_nominal_wavelength_ratio": probe.element_pitch_m
            / (x.specimen_wave_velocity_m_s / probe.center_frequency_Hz),
        }
        for probe in x.probes
    }
    law_delay_spans = {
        law.law_id: {
            "transmit_delay_span_s": max(law.transmit_delay_s) - min(law.transmit_delay_s),
            "receive_delay_span_s": max(law.receive_delay_s) - min(law.receive_delay_s),
        }
        for law in x.beam_laws
    }
    return Calculation(
        status=("needs_data" if missing_reviews or unmapped_indication_ids else "computed"),
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "physical_scope_id": x.physical_scope_id,
            "acquisition_mode": x.acquisition_mode,
            "probe_geometry_by_id": probe_values,
            "beam_law_delay_span_by_id": law_delay_spans,
            "probe_count": len(x.probes),
            "wedge_count": len(x.wedges),
            "beam_law_count": len(x.beam_laws),
            "frame_count": len(x.frames),
            "unique_encoder_position_count": len(set(positions)),
            "duplicate_adjacent_encoder_position_count": sum(value == 0 for value in increments),
            "encoder_span_m": abs(positions[-1] - positions[0]),
            "minimum_nonzero_encoder_increment_m": min(nonzero_increments, default=None),
            "maximum_nonzero_encoder_increment_m": max(nonzero_increments, default=None),
            "frame_count_by_beam_law_id": dict(
                Counter(item.beam_law_id or "full_matrix_capture" for item in x.frames)
            ),
            "indication_count": len(x.indications),
            "unmapped_indication_ids": unmapped_indication_ids,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Aperture, wavelength, pitch ratio, delay span and encoder spacing are acquisition descriptors, not beam-field or image-quality qualification.",
            "Frame order and duplicate encoder positions are preserved; no waveform sorting, resampling, focusing, TFM reconstruction or indication detection is performed.",
            "Reported indications are not defect identity, physical dimensions, acceptance, probability of detection, remaining life or failure probability.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.phased_array_acquisition_summary",
            PhasedArrayExamination,
            phased_array_acquisition_summary,
            {
                "probe_geometry_by_id": "mixed; see nested field names",
                "beam_law_delay_span_by_id": "s",
                "encoder_span_m": "m",
                "minimum_nonzero_encoder_increment_m": "m",
                "maximum_nonzero_encoder_increment_m": "m",
            },
            (
                "Caller-controlled probe, wedge, material velocity, beam-law, encoder, frame and indication record; no embedded reconstruction or acceptance rule.",
            ),
            ("phased_array_acquisition_definition",),
        )
    ]
