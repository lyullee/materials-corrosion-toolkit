"""Synthetic connected-component and sampled-interface example; not grain sizing."""

import json

import numpy as np

from matintegrity.phase_map_data import PhaseLabelMapMetadata, PhasePixelLabel
from matintegrity.phase_map_topology import summarize_phase_map_topology
from matintegrity.spatial_fields import numeric_array_digest


def main():
    labels = np.array([[1, 1, 2], [1, 2, 2], [2, 2, 1]], dtype=np.int16)
    roi = np.ones(labels.shape, dtype=bool)
    missing = np.zeros(labels.shape, dtype=bool)
    metadata = PhaseLabelMapMetadata(
        map_id="synthetic-topology-example",
        physical_specimen_id="synthetic-specimen",
        source_group_id="synthetic-source",
        source_sha256="b" * 64,
        label_array_sha256=numeric_array_digest(labels),
        roi_mask_sha256=numeric_array_digest(roi),
        missing_mask_sha256=numeric_array_digest(missing),
        shape=labels.shape,
        region_id="synthetic-region",
        coordinate_frame_id="synthetic-image-frame",
        coordinate_basis="authored rectangular raster",
        pixel_width_m=2e-6,
        pixel_height_m=3e-6,
        segmentation_method_id="synthetic-segmentation",
        segmentation_basis="authored category assignment",
        labels=(
            PhasePixelLabel(label_value=1, phase_id="alpha"),
            PhasePixelLabel(label_value=2, phase_id="gamma"),
        ),
        scale_reviewed=True,
        roi_reviewed=True,
        phase_label_mapping_reviewed=True,
        evidence=({"source_id": "synthetic", "origin": "synthetic", "citation": "authored fixture"},),
    )
    result = summarize_phase_map_topology(labels, roi, missing, metadata)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
