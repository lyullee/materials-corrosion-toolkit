"""Digest-bound area fractions from caller-provided categorical phase maps."""

from __future__ import annotations

from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Positive
from .models.phase_microstructure import PhaseFractionObservation
from .spatial_fields import numeric_array_digest


class PhasePixelLabel(Contract):
    label_value: int
    phase_id: str = Field(min_length=1)


class PhaseLabelMapMetadata(Contract):
    schema_version: Literal["matintegrity.phase_label_map_metadata.v1"] = (
        "matintegrity.phase_label_map_metadata.v1"
    )
    map_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    label_array_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    roi_mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    missing_mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    shape: tuple[int, int]
    region_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_basis: str = Field(min_length=1)
    pixel_width_m: Positive
    pixel_height_m: Positive
    segmentation_method_id: str = Field(min_length=1)
    segmentation_basis: str = Field(min_length=1)
    labels: tuple[PhasePixelLabel, ...] = Field(min_length=1)
    unclassified_label_values: tuple[int, ...] = ()
    scale_reviewed: bool
    roi_reviewed: bool
    phase_label_mapping_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_label_contract(self):
        if len(self.shape) != 2 or any(size <= 0 for size in self.shape):
            raise ValueError("phase label map shape must contain two positive dimensions")
        label_values = [row.label_value for row in self.labels]
        phase_ids = [row.phase_id for row in self.labels]
        if len(label_values) != len(set(label_values)):
            raise ValueError("phase label values must be unique")
        if len(phase_ids) != len(set(phase_ids)):
            raise ValueError("phase IDs must be unique in one label map")
        if len(self.unclassified_label_values) != len(set(self.unclassified_label_values)):
            raise ValueError("unclassified label values must be unique")
        if set(label_values) & set(self.unclassified_label_values):
            raise ValueError("a pixel label cannot be both a named phase and unclassified")
        return self


class PhaseFractionMapRow(Contract):
    phase_id: str = Field(min_length=1)
    label_value: int
    pixel_count: int = Field(ge=0)
    area_m2: float = Field(ge=0)
    area_fraction_of_analyzed_region: float = Field(ge=0, le=1)
    area_fraction_of_classified_region: float | None = Field(default=None, ge=0, le=1)


class PhaseLabelMapAreaFractionResult(Contract):
    schema_version: Literal["matintegrity.phase_label_map_area_fraction.v1"] = (
        "matintegrity.phase_label_map_area_fraction.v1"
    )
    map_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    label_array_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    roi_mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    missing_mask_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    region_id: str = Field(min_length=1)
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_basis: str = Field(min_length=1)
    segmentation_method_id: str = Field(min_length=1)
    segmentation_basis: str = Field(min_length=1)
    pixel_area_m2: float = Field(gt=0)
    roi_pixel_count: int = Field(gt=0)
    missing_pixel_count: int = Field(ge=0)
    analyzed_pixel_count: int = Field(ge=0)
    unclassified_pixel_count: int = Field(ge=0)
    classified_pixel_count: int = Field(ge=0)
    missing_area_m2: float = Field(ge=0)
    analyzed_area_m2: float = Field(ge=0)
    unclassified_area_m2: float = Field(ge=0)
    classified_area_m2: float = Field(ge=0)
    phase_rows: tuple[PhaseFractionMapRow, ...]
    status: Literal["computed", "needs_data"]
    uncertainty_status: Literal["not_estimated"] = "not_estimated"
    scale_reviewed: bool
    roi_reviewed: bool
    phase_label_mapping_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def pixel_accounting_closes(self):
        if self.roi_pixel_count != self.missing_pixel_count + self.analyzed_pixel_count:
            raise ValueError("ROI pixels must equal missing plus analyzed pixels")
        if self.analyzed_pixel_count != self.classified_pixel_count + self.unclassified_pixel_count:
            raise ValueError("analyzed pixels must equal classified plus unclassified pixels")
        if (self.status == "computed") != (self.analyzed_pixel_count > 0):
            raise ValueError("status must reflect whether any nonmissing ROI pixels were analyzed")
        if self.status == "computed":
            if sum(row.pixel_count for row in self.phase_rows) != self.classified_pixel_count:
                raise ValueError("phase row pixel counts must close to the classified pixel count")
        return self


def summarize_phase_label_map(
    labels: np.ndarray,
    roi_mask: np.ndarray,
    missing_mask: np.ndarray,
    metadata: PhaseLabelMapMetadata,
) -> PhaseLabelMapAreaFractionResult:
    """Count categorical labels in a reviewed ROI without inventing measurement uncertainty."""
    label_array = np.asarray(labels)
    roi = np.asarray(roi_mask)
    missing = np.asarray(missing_mask)
    expected_shape = metadata.shape
    if label_array.shape != expected_shape or roi.shape != expected_shape or missing.shape != expected_shape:
        raise ValueError("label, ROI and missing arrays must match the reviewed two-dimensional shape")
    if label_array.dtype.kind not in "iu" or label_array.dtype.kind == "b":
        raise ValueError("phase labels must use a real integer array")
    if roi.dtype.kind != "b" or missing.dtype.kind != "b":
        raise ValueError("ROI and missing masks must use Boolean arrays")
    if numeric_array_digest(label_array) != metadata.label_array_sha256:
        raise ValueError("phase-label array digest differs from reviewed metadata")
    if numeric_array_digest(roi) != metadata.roi_mask_sha256:
        raise ValueError("ROI mask digest differs from reviewed metadata")
    if numeric_array_digest(missing) != metadata.missing_mask_sha256:
        raise ValueError("missing mask digest differs from reviewed metadata")
    if np.any(missing & ~roi):
        raise ValueError("missing mask may mark only pixels inside the selected ROI")
    if not np.any(roi):
        raise ValueError("reviewed ROI must contain at least one pixel")

    label_to_phase = {row.label_value: row.phase_id for row in metadata.labels}
    valid_roi = roi & ~missing
    observed = set(int(value) for value in np.unique(label_array[valid_roi]))
    allowed = set(label_to_phase) | set(metadata.unclassified_label_values)
    unknown = observed - allowed
    if unknown:
        raise ValueError(f"undeclared phase label values occur inside ROI: {sorted(unknown)}")

    roi_count = int(np.count_nonzero(roi))
    missing_count = int(np.count_nonzero(roi & missing))
    analyzed_count = int(np.count_nonzero(valid_roi))
    counts = {label: int(np.count_nonzero(valid_roi & (label_array == label))) for label in label_to_phase}
    unclassified_count = int(
        sum(
            np.count_nonzero(valid_roi & (label_array == label))
            for label in metadata.unclassified_label_values
        )
    )
    classified_count = sum(counts.values())
    pixel_area = metadata.pixel_width_m * metadata.pixel_height_m
    rows = tuple(
        PhaseFractionMapRow(
            phase_id=phase_id,
            label_value=label,
            pixel_count=count,
            area_m2=count * pixel_area,
            area_fraction_of_analyzed_region=(count / analyzed_count if analyzed_count else 0.0),
            area_fraction_of_classified_region=(count / classified_count if classified_count else None),
        )
        for label, phase_id in label_to_phase.items()
        for count in (counts[label],)
    )
    return PhaseLabelMapAreaFractionResult(
        map_id=metadata.map_id,
        physical_specimen_id=metadata.physical_specimen_id,
        source_group_id=metadata.source_group_id,
        source_sha256=metadata.source_sha256,
        label_array_sha256=metadata.label_array_sha256,
        roi_mask_sha256=metadata.roi_mask_sha256,
        missing_mask_sha256=metadata.missing_mask_sha256,
        region_id=metadata.region_id,
        coordinate_frame_id=metadata.coordinate_frame_id,
        coordinate_basis=metadata.coordinate_basis,
        segmentation_method_id=metadata.segmentation_method_id,
        segmentation_basis=metadata.segmentation_basis,
        pixel_area_m2=pixel_area,
        roi_pixel_count=roi_count,
        missing_pixel_count=missing_count,
        analyzed_pixel_count=analyzed_count,
        unclassified_pixel_count=unclassified_count,
        classified_pixel_count=classified_count,
        missing_area_m2=missing_count * pixel_area,
        analyzed_area_m2=analyzed_count * pixel_area,
        unclassified_area_m2=unclassified_count * pixel_area,
        classified_area_m2=classified_count * pixel_area,
        phase_rows=rows,
        status="computed" if analyzed_count else "needs_data",
        scale_reviewed=metadata.scale_reviewed,
        roi_reviewed=metadata.roi_reviewed,
        phase_label_mapping_reviewed=metadata.phase_label_mapping_reviewed,
        evidence=metadata.evidence,
    )


def phase_label_map_to_observations(
    summary: PhaseLabelMapAreaFractionResult,
    expanded_uncertainty_by_phase: dict[str, float],
    *,
    uncertainty_basis: str,
    fraction_basis: Literal["analyzed_region", "classified_region"],
) -> tuple[PhaseFractionObservation, ...]:
    """Attach caller-owned expanded uncertainties to measured map fractions for phase assessment."""
    if summary.status != "computed":
        raise ValueError("phase map summary must contain at least one analyzed ROI pixel")
    if not all((summary.scale_reviewed, summary.roi_reviewed, summary.phase_label_mapping_reviewed)):
        raise ValueError(
            "map scale, ROI, and label mapping reviews must be complete before observation transfer"
        )
    if not uncertainty_basis.strip():
        raise ValueError("caller must identify the expanded-uncertainty basis")
    phase_ids = {row.phase_id for row in summary.phase_rows}
    if set(expanded_uncertainty_by_phase) != phase_ids:
        raise ValueError("caller uncertainties must cover exactly the phase IDs in the map summary")
    uncertainty_evidence = Evidence(
        source_id="caller_phase_fraction_uncertainty_basis",
        origin="user_declared",
        citation=uncertainty_basis,
    )
    observations = []
    for row in summary.phase_rows:
        expanded_uncertainty = expanded_uncertainty_by_phase[row.phase_id]
        fraction = (
            row.area_fraction_of_analyzed_region
            if fraction_basis == "analyzed_region"
            else row.area_fraction_of_classified_region
        )
        if fraction is None:
            raise ValueError("classified-region fraction is undefined when the ROI has no classified pixels")
        observations.append(
            PhaseFractionObservation(
                observation_id=f"{summary.map_id}:{row.phase_id}",
                sample_id=summary.physical_specimen_id,
                region_id=summary.region_id,
                phase_id=row.phase_id,
                measured_fraction=fraction,
                expanded_uncertainty_fraction=expanded_uncertainty,
                method_id=summary.segmentation_method_id,
                record_valid=True,
                evidence=summary.evidence + (uncertainty_evidence,),
            )
        )
    return tuple(observations)
