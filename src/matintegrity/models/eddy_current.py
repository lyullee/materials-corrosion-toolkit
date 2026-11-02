"""Eddy-current acquisition records and bounded electromagnetic descriptors."""

from __future__ import annotations

import math
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive
from ..registry import ModelSpec

VACUUM_PERMEABILITY_H_M = 4e-7 * math.pi


class EddyCurrentProbe(Contract):
    probe_id: str = Field(min_length=1)
    probe_mode: Literal["absolute", "differential", "reflection", "array", "remote_field", "other"]
    coil_configuration: str = Field(min_length=1)
    nominal_excitation_frequencies_Hz: list[Positive] = Field(min_length=1)
    active_channel_ids: list[str] = Field(min_length=1)
    probe_geometry_basis: str = Field(min_length=1)
    lift_off_control_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_frequency_and_channels(self):
        if len(set(self.nominal_excitation_frequencies_Hz)) != len(self.nominal_excitation_frequencies_Hz):
            raise ValueError("eddy-current probe frequencies must be unique")
        if len(set(self.active_channel_ids)) != len(self.active_channel_ids):
            raise ValueError("eddy-current channel IDs must be unique")
        return self


class EddyCurrentReferenceFeature(Contract):
    feature_id: str = Field(min_length=1)
    feature_kind: str = Field(min_length=1)
    geometry_description: str = Field(min_length=1)
    nominal_depth_m: Positive | None = None
    nominal_length_m: Positive | None = None
    nominal_width_m: Positive | None = None
    physical_feature_identity_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)


class EddyCurrentReferenceStandard(Contract):
    reference_standard_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    applicable_probe_ids: list[str] = Field(min_length=1)
    applicable_frequencies_Hz: list[Positive] = Field(min_length=1)
    conductivity_S_m: Positive | None = None
    relative_magnetic_permeability: Positive | None = None
    property_temperature_K: Positive | None = None
    electromagnetic_property_basis: str | None = Field(default=None, min_length=1)
    features: list[EddyCurrentReferenceFeature] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_properties_and_unique_features(self):
        optional = (
            self.conductivity_S_m,
            self.relative_magnetic_permeability,
            self.property_temperature_K,
            self.electromagnetic_property_basis,
        )
        if any(value is not None for value in optional) and any(value is None for value in optional):
            raise ValueError("eddy-current electromagnetic properties require value, temperature and basis")
        ids = [item.feature_id for item in self.features]
        if len(set(ids)) != len(ids):
            raise ValueError("eddy-current reference feature IDs must be unique")
        if len(set(self.applicable_probe_ids)) != len(self.applicable_probe_ids):
            raise ValueError("eddy-current applicable probe IDs must be unique")
        if len(set(self.applicable_frequencies_Hz)) != len(self.applicable_frequencies_Hz):
            raise ValueError("eddy-current applicable frequencies must be unique")
        return self


class EncodedEddyCurrentScan(Contract):
    scan_id: str = Field(min_length=1)
    probe_id: str = Field(min_length=1)
    excitation_frequency_Hz: Positive
    data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    row_count: int = Field(gt=0)
    column_count: int = Field(gt=0)
    component_order: list[str] = Field(min_length=1)
    signal_encoding: str = Field(min_length=1)
    signal_unit_token: str = Field(min_length=1)
    x_increment_m: Positive | None = None
    y_increment_m: Positive | None = None
    coordinate_mapping_basis: str | None = Field(default=None, min_length=1)
    scan_origin_x_m: float | None = None
    scan_origin_y_m: float | None = None
    acquisition_order: int = Field(ge=0)
    time_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def complete_coordinates_and_components(self):
        coordinates = (
            self.x_increment_m,
            self.y_increment_m,
            self.coordinate_mapping_basis,
            self.scan_origin_x_m,
            self.scan_origin_y_m,
        )
        if any(value is not None for value in coordinates) and any(value is None for value in coordinates):
            raise ValueError("eddy-current scan coordinates require increments, origin and mapping basis")
        if len(set(self.component_order)) != len(self.component_order):
            raise ValueError("eddy-current signal components must be unique")
        return self


class EddyCurrentIndication(Contract):
    indication_id: str = Field(min_length=1)
    scan_ids: list[str] = Field(min_length=1)
    reported_indication_type: str = Field(min_length=1)
    signal_response_description: str = Field(min_length=1)
    reference_feature_ids: list[str] = Field(default_factory=list)
    physical_location_id: str | None = Field(default=None, min_length=1)
    object_mapping_basis: str | None = Field(default=None, min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def mapping_and_unique_references(self):
        if len(set(self.scan_ids)) != len(self.scan_ids):
            raise ValueError("eddy-current indication scan references must be unique")
        if len(set(self.reference_feature_ids)) != len(self.reference_feature_ids):
            raise ValueError("eddy-current indication reference features must be unique")
        if (self.physical_location_id is None) != (self.object_mapping_basis is None):
            raise ValueError("physical location and object-mapping basis must be supplied together")
        return self


class EddyCurrentExamination(Contract):
    examination_id: str = Field(min_length=1)
    procedure_id: str = Field(min_length=1)
    procedure_revision: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    probe: EddyCurrentProbe
    reference_standard: EddyCurrentReferenceStandard
    scans: list[EncodedEddyCurrentScan] = Field(min_length=1)
    indications: list[EddyCurrentIndication] = Field(default_factory=list)
    probe_identity_reviewed: bool
    reference_standard_reviewed: bool
    excitation_and_receiver_settings_reviewed: bool
    lift_off_and_surface_condition_reviewed: bool
    encoder_calibration_reviewed: bool
    scan_identity_reviewed: bool
    indication_mapping_reviewed: bool
    linear_homogeneous_skin_depth_applicable: bool = False
    negative_result_reviewed: bool = False
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_identities(self):
        scan_ids = [item.scan_id for item in self.scans]
        indication_ids = [item.indication_id for item in self.indications]
        if len(set(scan_ids)) != len(scan_ids):
            raise ValueError("eddy-current scan IDs must be unique")
        if len(set(indication_ids)) != len(indication_ids):
            raise ValueError("eddy-current indication IDs must be unique")
        orders = [item.acquisition_order for item in self.scans]
        if len(set(orders)) != len(orders) or orders != sorted(orders):
            raise ValueError("eddy-current acquisition order must be unique and nondecreasing")
        if any(item.probe_id != self.probe.probe_id for item in self.scans):
            raise ValueError("every eddy-current scan must reference the examination probe")
        if self.probe.probe_id not in self.reference_standard.applicable_probe_ids:
            raise ValueError("eddy-current reference standard does not cover the examination probe")
        declared_frequencies = set(self.probe.nominal_excitation_frequencies_Hz)
        reference_frequencies = set(self.reference_standard.applicable_frequencies_Hz)
        scan_frequencies = {item.excitation_frequency_Hz for item in self.scans}
        if scan_frequencies - declared_frequencies:
            raise ValueError("eddy-current scan frequency is not declared by the probe")
        if scan_frequencies - reference_frequencies:
            raise ValueError("eddy-current scan frequency is not covered by the reference standard")
        scan_id_set = set(scan_ids)
        feature_ids = {item.feature_id for item in self.reference_standard.features}
        for indication in self.indications:
            if set(indication.scan_ids) - scan_id_set:
                raise ValueError("every eddy-current indication scan must be declared")
            if set(indication.reference_feature_ids) - feature_ids:
                raise ValueError("every eddy-current reference feature must be declared")
        return self


def eddy_current_acquisition_summary(x: EddyCurrentExamination) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "probe_identity_reviewed",
            "reference_standard_reviewed",
            "excitation_and_receiver_settings_reviewed",
            "lift_off_and_surface_condition_reviewed",
            "encoder_calibration_reviewed",
            "scan_identity_reviewed",
            "indication_mapping_reviewed",
        )
        if not getattr(x, name)
    ]
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
            "x_span_m": (scan.column_count - 1) * scan.x_increment_m if mapped else None,
            "y_span_m": (scan.row_count - 1) * scan.y_increment_m if mapped else None,
            "sample_position_count": scan.row_count * scan.column_count,
            "component_count": len(scan.component_order),
        }

    properties = x.reference_standard
    skin_depth_by_frequency = {}
    property_inputs_available = properties.conductivity_S_m is not None
    if property_inputs_available and x.linear_homogeneous_skin_depth_applicable:
        absolute_permeability = VACUUM_PERMEABILITY_H_M * properties.relative_magnetic_permeability
        for frequency in sorted({item.excitation_frequency_Hz for item in x.scans}):
            skin_depth_by_frequency[str(frequency)] = math.sqrt(
                1 / (math.pi * frequency * absolute_permeability * properties.conductivity_S_m)
            )
    elif x.linear_homogeneous_skin_depth_applicable and not property_inputs_available:
        missing_reviews.append("electromagnetic_property_values")

    status = "needs_data" if missing_reviews or unmapped_indications else "computed"
    return Calculation(
        status=status,
        values={
            "examination_id": x.examination_id,
            "procedure_id": x.procedure_id,
            "procedure_revision": x.procedure_revision,
            "physical_scope_id": x.physical_scope_id,
            "probe_id": x.probe.probe_id,
            "reference_standard_id": x.reference_standard.reference_standard_id,
            "scan_count": len(x.scans),
            "scan_count_by_frequency_Hz": dict(
                Counter(str(item.excitation_frequency_Hz) for item in x.scans)
            ),
            "scan_geometry_by_id": scan_geometry,
            "skin_depth_m_by_frequency_Hz": skin_depth_by_frequency,
            "skin_depth_model_applied": bool(skin_depth_by_frequency),
            "indication_count": len(x.indications),
            "unmapped_indication_ids": unmapped_indications,
            "missing_reviews": missing_reviews,
        },
        notes=(
            "Scan extents are calculated only from caller-reviewed coordinate mapping and preserve original component order.",
            "Classical skin depth is reported only for reviewed linear homogeneous conductivity/permeability inputs; it is not penetration or flaw-detection qualification.",
            "No signal rotation, filtering, mixing, thresholding, defect sizing, acceptance, POD, remaining life or failure probability is produced.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "inspection.eddy_current_acquisition_summary",
            EddyCurrentExamination,
            eddy_current_acquisition_summary,
            {
                "scan_geometry_by_id": "mixed; see nested field names",
                "skin_depth_m_by_frequency_Hz": "m",
            },
            (
                "Caller-controlled probe, reference standard, electromagnetic properties, encoded scan and indication record; no embedded detection or acceptance rule.",
            ),
            ("eddy_current_acquisition_definition",),
        )
    ]
