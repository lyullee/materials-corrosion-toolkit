"""Unrun synthetic regression contracts for phase-map topology descriptors."""

import numpy as np
import pytest

from matintegrity.phase_map_data import PhaseLabelMapMetadata, PhasePixelLabel
from matintegrity.phase_map_topology import summarize_phase_map_topology
from matintegrity.spatial_fields import numeric_array_digest


def _metadata(labels, roi, missing):
    return PhaseLabelMapMetadata(
        map_id="synthetic-topology-map",
        physical_specimen_id="synthetic-specimen",
        source_group_id="synthetic-source",
        source_sha256="a" * 64,
        label_array_sha256=numeric_array_digest(labels),
        roi_mask_sha256=numeric_array_digest(roi),
        missing_mask_sha256=numeric_array_digest(missing),
        shape=labels.shape,
        region_id="synthetic-region",
        coordinate_frame_id="image-frame",
        coordinate_basis="authored rectangular raster",
        pixel_width_m=2e-6,
        pixel_height_m=3e-6,
        segmentation_method_id="synthetic-segmentation",
        segmentation_basis="authored categorical fixture",
        labels=(
            PhasePixelLabel(label_value=1, phase_id="alpha"),
            PhasePixelLabel(label_value=2, phase_id="gamma"),
        ),
        unclassified_label_values=(-1,),
        scale_reviewed=True,
        roi_reviewed=True,
        phase_label_mapping_reviewed=True,
        evidence=({"source_id": "synthetic", "origin": "synthetic", "citation": "authored fixture"},),
    )


def test_diagonal_phase_pixels_respect_selected_connectivity():
    labels = np.array([[1, 2], [2, 1]], dtype=np.int16)
    roi = np.ones(labels.shape, dtype=bool)
    missing = np.zeros(labels.shape, dtype=bool)
    metadata = _metadata(labels, roi, missing)

    four = summarize_phase_map_topology(labels, roi, missing, metadata, connectivity=4)
    eight = summarize_phase_map_topology(labels, roi, missing, metadata, connectivity=8)

    assert four.phase_clusters[0].component_count == 2
    assert eight.phase_clusters[0].component_count == 1
    assert len(four.interfaces) == 1
    assert four.interfaces[0].horizontal_grid_edge_count == 2
    assert four.interfaces[0].vertical_grid_edge_count == 2
    assert four.interfaces[0].sampled_interface_length_m == pytest.approx(10e-6)


def test_missing_pixels_do_not_create_interfaces_and_boundary_is_reported():
    labels = np.array([[1, 2, 2]], dtype=np.int16)
    roi = np.ones(labels.shape, dtype=bool)
    missing = np.array([[False, True, False]], dtype=bool)
    result = summarize_phase_map_topology(labels, roi, missing, _metadata(labels, roi, missing))

    assert result.interfaces == ()
    assert result.phase_clusters[1].components_touching_missing_boundary == 1


def test_digest_contract_rejects_modified_map():
    labels = np.array([[1, 2]], dtype=np.int16)
    roi = np.ones(labels.shape, dtype=bool)
    missing = np.zeros(labels.shape, dtype=bool)
    metadata = _metadata(labels, roi, missing)

    with pytest.raises(ValueError, match="digest"):
        summarize_phase_map_topology(labels[:, ::-1].copy(), roi, missing, metadata)
