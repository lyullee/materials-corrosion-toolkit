"""Magnetic-flux-leakage acquisition records without hidden sizing rules."""

from __future__ import annotations

import math
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class MflMagnetizer(Contract):
    magnetizer_id: str = Field(min_length=1)
    excitation_type: Literal["permanent_magnet", "electromagnet", "hybrid", "other"]
    nominal_magnetization_direction: Literal["axial", "circumferential", "other"]
    pole_spacing_m: Positive | None = None
    excitation_current_A: Nonnegative | None = None
    excitation_current_basis: str | None = Field(default=None, min_length=1)
    magnetization_control_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def paired_current_basis(self):
        if (self.excitation_current_A is None) != (self.excitation_current_basis is None):
            raise ValueError("MFL excitation current and basis must be supplied together")
        return self


class MflSensorArray(Contract):
    sensor_array_id: str = Field(min_length=1)
    channel_ids: list[str] = Field(min_length=1)
    measured_components: list[Literal["axial", "circumferential", "radial"]] = Field(min_length=1)
    channel_component_by_id: dict[str, Literal["axial", "circumferential", "radial"]]
    nominal_channel_pitch_m: Positive | None = None
    lift_off_control_basis: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    calibration_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_unique_channels(self):
        if len(set(self.channel_ids)) != len(self.channel_ids):
            raise ValueError("MFL sensor channel IDs must be unique")
        if len(set(self.measured_components)) != len(self.measured_components):
            raise ValueError("MFL measured components must be unique")
        if set(self.channel_component_by_id) != set(self.channel_ids):
            raise ValueError("MFL channel-component mapping must cover every channel exactly")
        if set(self.channel_component_by_id.values()) - set(self.measured_components):
            raise ValueError("MFL channel-component mapping uses an undeclared component")
        return self


class MflReferenceFeature(Contract):
    feature_id: str = Field(min_length=1)
    feature_kind: str = Field(min_length=1)
    surface: Literal["internal", "external", "through_wall", "not_applicable", "unresolved"]
    geometry_description: str = Field(min_length=1)
    nominal_depth_m: Positive | None = None
    nominal_length_m: Positive | None = None
    nominal_width_m: Positive | None = None
    physical_feature_identity_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)


class MflReferenceStandard(Contract):
    reference_standard_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    wall_thickness_m: Positive
    applicable_magnetizer_ids: list[str] = Field(min_length=1)
    applicable_sensor_array_ids: list[str] = Field(min_length=1)
    features: list[MflReferenceFeature] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_coverage_and_features(self):
        for values, label in (
            (self.applicable_magnetizer_ids, "magnetizer"),
            (self.applicable_sensor_array_ids, "sensor array"),
            ([item.feature_id for item in self.features], "reference feature"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"MFL {label} IDs must be unique")
        return self


class MflMagneticFieldCheckpoint(Contract):
    checkpoint_id: str = Field(min_length=1)
    physical_location_description: str = Field(min_length=1)
    coordinate_frame: str = Field(min_length=1)
    magnetic_field_strength_A_m: tuple[float, float, float] | None = None
    magnetic_flux_density_T: tuple[float, float, float] | None = None
    measurement_temperature_K: Positive | None = None
    measurement_basis: str = Field(min_length=1)
    state_identity_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def finite_nonempty_vectors(self):
        if self.magnetic_field_strength_A_m is None and self.magnetic_flux_density_T is None:
            raise ValueError("MFL field checkpoint requires H or B vector data")
        values = (self.magnetic_field_strength_A_m or ()) + (self.magnetic_flux_density_T or ())
        if any(not math.isfinite(value) for value in values):
            raise ValueError("MFL field checkpoint vectors must be finite")
        return self


class EncodedMflScan(Contract):
    scan_id: str = Field(min_length=1)
    magnetizer_id: str = Field(min_length=1)
    sensor_array_id: str = Field(min_length=1)
    active_channel_ids: list[str] = Field(min_length=1)
    data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    sample_count: int = Field(gt=0)
    signal_encoding: str = Field(min_length=1)
    signal_unit_token: str = Field(min_length=1)
    pass_direction: Literal["forward", "reverse", "stationary", "other"]
    scan_speed_m_s: Nonnegative
    scan_speed_basis: str = Field(min_length=1)
    sample_spacing_m: Positive | None = None
    encoder_origin_m: float | None = None
    coordinate_mapping_basis: str | None = Field(default=None, min_length=1)
    acquisition_order: int = Field(ge=0)
    time_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def complete_coordinates_and_unique_channels(self):
        coordinates = (self.sample_spacing_m, self.encoder_origin_m, self.coordinate_mapping_basis)
        if any(value is not None for value in coordinates) and any(value is None for value in coordinates):
            raise ValueError("MFL encoded coordinates require spacing, origin and mapping basis")
        if len(set(self.active_channel_ids)) != len(self.active_channel_ids):
            raise ValueError("MFL active channel IDs must be unique")
        return self


class MflIndication(Contract):
    indication_id: str = Field(min_length=1)
    scan_ids: list[str] = Field(min_length=1)
    reported_indication_type: str = Field(min_length=1)
    signal_response_description: str = Field(min_length=1)
    reference_feature_ids: list[str] = Field(default_factory=list)
    physical_location_id: str | None = Field(default=None, min_length=1)
    object_mapping_basis: str | None = Field(default=None, min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_mapping_and_unique_references(self):
        if len(set(self.scan_ids)) != len(self.scan_ids):
            raise ValueError("MFL indication scan references must be unique")
        if len(set(self.reference_feature_ids)) != len(self.reference_feature_ids):
            raise ValueError("MFL indication reference features must be unique")
        if (self.physical_location_id is None) != (self.object_mapping_basis is None):
            raise ValueError("MFL physical location and object-mapping basis must be supplied together")
        return self


class MflExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    surface_condition: str = Field(min_length=1)
    magnetizer: MflMagnetizer
    sensor_arrays: list[MflSensorArray] = Field(min_length=1)
    reference_standard: MflReferenceStandard
    magnetic_field_checkpoints: list[MflMagneticFieldCheckpoint] = Field(default_factory=list)
    scans: list[EncodedMflScan] = Field(min_length=1)
    indications: list[MflIndication] = Field(default_factory=list)
    magnetizer_identity_reviewed: bool
    sensor_calibration_reviewed: bool
    reference_standard_reviewed: bool
    magnetization_state_reviewed: bool
    lift_off_and_surface_condition_reviewed: bool
    encoder_calibration_reviewed: bool
    scan_identity_reviewed: bool
    indication_mapping_reviewed: bool
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_identities(self):
        array_ids = [item.sensor_array_id for item in self.sensor_arrays]
        checkpoint_ids = [item.checkpoint_id for item in self.magnetic_field_checkpoints]
        scan_ids = [item.scan_id for item in self.scans]
        indication_ids = [item.indication_id for item in self.indications]
        for values, label in (
            (array_ids, "sensor array"),
            (checkpoint_ids, "field checkpoint"),
            (scan_ids, "scan"),
            (indication_ids, "indication"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"MFL {label} IDs must be unique")
        orders = [item.acquisition_order for item in self.scans]
        if len(set(orders)) != len(orders) or orders != sorted(orders):
            raise ValueError("MFL acquisition order must be unique and nondecreasing")
        if self.magnetizer.magnetizer_id not in self.reference_standard.applicable_magnetizer_ids:
            raise ValueError("MFL reference standard does not cover the examination magnetizer")
        if set(array_ids) - set(self.reference_standard.applicable_sensor_array_ids):
            raise ValueError("MFL reference standard does not cover every sensor array")
        array_by_id = {item.sensor_array_id: item for item in self.sensor_arrays}
        for scan in self.scans:
            if scan.magnetizer_id != self.magnetizer.magnetizer_id:
                raise ValueError("every MFL scan must reference the examination magnetizer")
            if scan.sensor_array_id not in array_by_id:
                raise ValueError("every MFL scan must reference a declared sensor array")
            if set(scan.active_channel_ids) - set(array_by_id[scan.sensor_array_id].channel_ids):
                raise ValueError("MFL scan uses a channel absent from its sensor array")
        scan_id_set = set(scan_ids)
        feature_ids = {item.feature_id for item in self.reference_standard.features}
        for indication in self.indications:
            if set(indication.scan_ids) - scan_id_set:
                raise ValueError("every MFL indication scan must be declared")
            if set(indication.reference_feature_ids) - feature_ids:
                raise ValueError("every MFL reference feature must be declared")
        return self


def _magnitude(vector: tuple[float, float, float] | None) -> float | None:
    if vector is None:
        return None
    return math.sqrt(sum(value * value for value in vector))


def magnetic_flux_leakage_acquisition_summary(x: MflExamination) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "magnetizer_identity_reviewed",
            "sensor_calibration_reviewed",
            "reference_standard_reviewed",
            "magnetization_state_reviewed",
            "lift_off_and_surface_condition_reviewed",
            "encoder_calibration_reviewed",
            "scan_identity_reviewed",
            "indication_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
    if not x.magnetic_field_checkpoints:
        missing_reviews.append("magnetic_field_checkpoint")
    if any(not item.state_identity_reviewed for item in x.magnetic_field_checkpoints):
        missing_reviews.append("magnetic_field_checkpoint_identity_reviewed")
    if any(not item.physical_feature_identity_reviewed for item in x.reference_standard.features):
        missing_reviews.append("reference_feature_identity_reviewed")
    if not x.indications and not x.negative_result_reviewed:
        missing_reviews.append("negative_result_reviewed")
    unmapped_indications = [item.indication_id for item in x.indications if item.physical_location_id is None]

    scan_geometry = {}
    for scan in x.scans:
        mapped = scan.coordinate_mapping_basis is not None
        scan_geometry[scan.scan_id] = {
            "coordinate_mapping_available": mapped,
            "encoded_span_m": (scan.sample_count - 1) * scan.sample_spacing_m if mapped else None,
            "sample_count": scan.sample_count,
            "active_channel_count": len(scan.active_channel_ids),
        }

    checkpoints = {}
    for item in x.magnetic_field_checkpoints:
        h_magnitude = _magnitude(item.magnetic_field_strength_A_m)
        b_magnitude = _magnitude(item.magnetic_flux_density_T)
        checkpoints[item.checkpoint_id] = {
            "magnetic_field_strength_magnitude_A_m": h_magnitude,
            "magnetic_flux_density_magnitude_T": b_magnitude,
            "magnitude_ratio_B_T_per_H_A_m": (
                b_magnitude / h_magnitude
                if b_magnitude is not None and h_magnitude is not None and h_magnitude > 0
                else None
            ),
            "state_identity_reviewed": item.state_identity_reviewed,
        }

    return Calculation(
        status="needs_data" if missing_reviews or unmapped_indications else "computed",
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "physical_scope_id": x.physical_scope_id,
            "magnetizer_id": x.magnetizer.magnetizer_id,
            "reference_standard_id": x.reference_standard.reference_standard_id,
            "sensor_array_count": len(x.sensor_arrays),
            "scan_count": len(x.scans),
            "scan_count_by_direction": dict(Counter(item.pass_direction for item in x.scans)),
            "scan_geometry_by_id": scan_geometry,
            "magnetic_field_checkpoints": checkpoints,
            "indication_count": len(x.indications),
            "unmapped_indication_ids": unmapped_indications,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Encoded span and vector magnitudes are descriptive acquisition checks only.",
            "The B/H magnitude ratio is not a constitutive permeability or proof of magnetic saturation, field uniformity or flaw sensitivity.",
            "No baseline removal, velocity/lift-off compensation, signal fusion, detection, classification, sizing, acceptance, POD, remaining life or failure probability is produced.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.magnetic_flux_leakage_acquisition_summary",
            MflExamination,
            magnetic_flux_leakage_acquisition_summary,
            {
                "scan_geometry_by_id": "mixed; see nested field names",
                "magnetic_field_checkpoints": "mixed; see nested field names",
            },
            (
                "Caller-controlled magnetizer, sensor array, field-state checkpoint, reference-standard, encoded-scan and indication record; no embedded sizing or acceptance rule.",
            ),
            ("magnetic_flux_leakage_acquisition_definition",),
        )
    ]
