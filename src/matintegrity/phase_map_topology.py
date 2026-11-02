"""Categorical connected-region and grid-interface descriptors for reviewed phase maps."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

import numpy as np
from pydantic import Field

from .contracts import Contract
from .phase_map_data import PhaseLabelMapMetadata, summarize_phase_label_map


class PhaseMapClusterStatistics(Contract):
    phase_id: str = Field(min_length=1)
    label_value: int
    pixel_count: int = Field(ge=0)
    component_count: int = Field(ge=0)
    largest_component_pixel_count: int = Field(ge=0)
    median_component_area_m2: float | None = Field(default=None, ge=0)
    largest_component_fraction_of_phase: float | None = Field(default=None, ge=0, le=1)
    components_touching_roi_boundary: int = Field(ge=0)
    components_touching_missing_boundary: int = Field(ge=0)


class PhaseMapInterfaceLength(Contract):
    left_label_value: int
    left_region_id: str = Field(min_length=1)
    right_label_value: int
    right_region_id: str = Field(min_length=1)
    horizontal_grid_edge_count: int = Field(ge=0)
    vertical_grid_edge_count: int = Field(ge=0)
    sampled_interface_length_m: float = Field(ge=0)


class PhaseMapTopologySummary(Contract):
    schema_version: Literal["matintegrity.phase_map_topology_summary.v1"] = (
        "matintegrity.phase_map_topology_summary.v1"
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
    connectivity: Literal[4, 8]
    roi_pixel_count: int = Field(gt=0)
    analyzed_pixel_count: int = Field(ge=0)
    classified_pixel_count: int = Field(ge=0)
    unclassified_pixel_count: int = Field(ge=0)
    phase_clusters: tuple[PhaseMapClusterStatistics, ...]
    interfaces: tuple[PhaseMapInterfaceLength, ...]
    status: Literal["computed", "needs_data"]
    interpretation: Literal["categorical_pixel_grid_descriptors"] = "categorical_pixel_grid_descriptors"
    uncertainty_status: Literal["not_estimated"] = "not_estimated"


def summarize_phase_map_topology(
    labels: np.ndarray,
    roi_mask: np.ndarray,
    missing_mask: np.ndarray,
    metadata: PhaseLabelMapMetadata,
    *,
    connectivity: Literal[4, 8] = 4,
) -> PhaseMapTopologySummary:
    """Summarize raster-connected phase regions and sampled 4-neighbor interfaces.

    Pixel connectivity and grid-edge lengths are geometric image descriptors. They are not
    grain segmentation, stereological correction, material properties, or qualification results.
    """
    if connectivity not in (4, 8):
        raise ValueError("connectivity must be 4 or 8")
    array = np.asarray(labels)
    roi = np.asarray(roi_mask)
    missing = np.asarray(missing_mask)
    base = summarize_phase_label_map(array, roi, missing, metadata)
    if base.status != "computed":
        return PhaseMapTopologySummary(
            map_id=base.map_id,
            physical_specimen_id=base.physical_specimen_id,
            source_group_id=base.source_group_id,
            source_sha256=base.source_sha256,
            label_array_sha256=base.label_array_sha256,
            roi_mask_sha256=base.roi_mask_sha256,
            missing_mask_sha256=base.missing_mask_sha256,
            region_id=base.region_id,
            coordinate_frame_id=base.coordinate_frame_id,
            connectivity=connectivity,
            roi_pixel_count=base.roi_pixel_count,
            analyzed_pixel_count=base.analyzed_pixel_count,
            classified_pixel_count=base.classified_pixel_count,
            unclassified_pixel_count=base.unclassified_pixel_count,
            phase_clusters=tuple(
                PhaseMapClusterStatistics(
                    phase_id=row.phase_id,
                    label_value=row.label_value,
                    pixel_count=0,
                    component_count=0,
                    largest_component_pixel_count=0,
                    median_component_area_m2=None,
                    largest_component_fraction_of_phase=None,
                    components_touching_roi_boundary=0,
                    components_touching_missing_boundary=0,
                )
                for row in base.phase_rows
            ),
            interfaces=(),
            status="needs_data",
        )

    try:
        from scipy import ndimage
    except ImportError as exc:
        raise ImportError(
            "phase-map topology requires the optional 'science' extra: pip install matintegrity[science]"
        ) from exc

    valid = roi & ~missing
    padded_roi = np.pad(roi, 1, mode="constant", constant_values=False)
    height, width = valid.shape
    outside_roi_neighbor = np.zeros(valid.shape, dtype=bool)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        outside_roi_neighbor |= ~padded_roi[1 + dy : 1 + dy + height, 1 + dx : 1 + dx + width]
    roi_boundary = valid & outside_roi_neighbor
    # Mark valid pixels with at least one 4-neighbor missing inside the selected ROI.
    padded_missing = np.pad(missing & roi, 1, mode="constant", constant_values=False)
    missing_boundary = np.zeros(valid.shape, dtype=bool)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        missing_boundary |= padded_missing[1 + dy : 1 + dy + height, 1 + dx : 1 + dx + width]
    missing_boundary &= valid

    structure = ndimage.generate_binary_structure(2, 1 if connectivity == 4 else 2)
    clusters = []
    for row in base.phase_rows:
        phase_pixels = valid & (array == row.label_value)
        component_labels, component_count = ndimage.label(phase_pixels, structure=structure)
        sizes = np.bincount(component_labels.ravel())[1:]
        if sizes.size != component_count:
            raise RuntimeError("connected-component count differs from its label-size inventory")
        largest = int(sizes.max()) if sizes.size else 0
        touched_roi = int(np.unique(component_labels[roi_boundary & phase_pixels]).size)
        touched_missing = int(np.unique(component_labels[missing_boundary & phase_pixels]).size)
        clusters.append(
            PhaseMapClusterStatistics(
                phase_id=row.phase_id,
                label_value=row.label_value,
                pixel_count=row.pixel_count,
                component_count=int(component_count),
                largest_component_pixel_count=largest,
                median_component_area_m2=(
                    float(np.median(sizes)) * base.pixel_area_m2 if sizes.size else None
                ),
                largest_component_fraction_of_phase=(largest / row.pixel_count if row.pixel_count else None),
                components_touching_roi_boundary=touched_roi,
                components_touching_missing_boundary=touched_missing,
            )
        )

    allowed = {row.label_value for row in base.phase_rows}
    unclassified_values = set(metadata.unclassified_label_values)
    category_by_label = {row.label_value: row.phase_id for row in base.phase_rows}
    category_by_label.update({value: f"unclassified:{value}" for value in unclassified_values})
    edge_counts: dict[tuple[int, int], list[int]] = defaultdict(lambda: [0, 0])

    def accumulate_interfaces(first_values: np.ndarray, second_values: np.ndarray, axis_index: int) -> None:
        if first_values.size == 0:
            return
        pairs = np.column_stack((first_values, second_values)).astype(np.int64, copy=False)
        pairs.sort(axis=1)
        unique_pairs, counts = np.unique(pairs, axis=0, return_counts=True)
        for (first_value, second_value), count in zip(unique_pairs, counts, strict=True):
            edge_counts[(int(first_value), int(second_value))][axis_index] += int(count)

    if width > 1:
        left, right = array[:, :-1], array[:, 1:]
        pairs = valid[:, :-1] & valid[:, 1:] & (left != right)
        accumulate_interfaces(left[pairs], right[pairs], 0)
    if height > 1:
        top, bottom = array[:-1, :], array[1:, :]
        pairs = valid[:-1, :] & valid[1:, :] & (top != bottom)
        accumulate_interfaces(top[pairs], bottom[pairs], 1)

    interfaces = []
    for (first, second), (horizontal_count, vertical_count) in sorted(edge_counts.items()):
        if first not in allowed | unclassified_values or second not in allowed | unclassified_values:
            raise ValueError("observed phase-map category is missing its reviewed metadata mapping")
        interfaces.append(
            PhaseMapInterfaceLength(
                left_label_value=first,
                left_region_id=category_by_label[first],
                right_label_value=second,
                right_region_id=category_by_label[second],
                horizontal_grid_edge_count=horizontal_count,
                vertical_grid_edge_count=vertical_count,
                sampled_interface_length_m=(
                    horizontal_count * metadata.pixel_height_m + vertical_count * metadata.pixel_width_m
                ),
            )
        )
    return PhaseMapTopologySummary(
        map_id=base.map_id,
        physical_specimen_id=base.physical_specimen_id,
        source_group_id=base.source_group_id,
        source_sha256=base.source_sha256,
        label_array_sha256=base.label_array_sha256,
        roi_mask_sha256=base.roi_mask_sha256,
        missing_mask_sha256=base.missing_mask_sha256,
        region_id=base.region_id,
        coordinate_frame_id=base.coordinate_frame_id,
        connectivity=connectivity,
        roi_pixel_count=base.roi_pixel_count,
        analyzed_pixel_count=base.analyzed_pixel_count,
        classified_pixel_count=base.classified_pixel_count,
        unclassified_pixel_count=base.unclassified_pixel_count,
        phase_clusters=tuple(clusters),
        interfaces=tuple(interfaces),
        status="computed",
    )
