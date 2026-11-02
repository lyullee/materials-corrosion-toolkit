"""Synthetic illustration of phase-area counting; values are not material guidance."""

import json

import numpy as np

from matintegrity.phase_map_data import PhaseLabelMapMetadata, PhasePixelLabel, summarize_phase_label_map
from matintegrity.spatial_fields import numeric_array_digest


def main():
    labels = np.array([[1, 1, 2], [-1, 2, 2]], dtype=np.int16)
    roi = np.ones(labels.shape, dtype=bool)
    missing = np.array([[False, False, False], [False, True, False]], dtype=bool)
    metadata = PhaseLabelMapMetadata(
        map_id="synthetic-phase-map",
        physical_specimen_id="synthetic-specimen",
        source_group_id="synthetic-group",
        source_sha256="a" * 64,
        label_array_sha256=numeric_array_digest(labels),
        roi_mask_sha256=numeric_array_digest(roi),
        missing_mask_sha256=numeric_array_digest(missing),
        shape=labels.shape,
        region_id="synthetic-region",
        coordinate_frame_id="synthetic-image-frame",
        coordinate_basis="authored uniform rectangular pixel fixture",
        pixel_width_m=2e-6,
        pixel_height_m=3e-6,
        segmentation_method_id="authored-segmentation-example",
        segmentation_basis="synthetic label assignment",
        labels=(
            PhasePixelLabel(label_value=1, phase_id="alpha"),
            PhasePixelLabel(label_value=2, phase_id="gamma"),
        ),
        unclassified_label_values=(-1,),
        scale_reviewed=True,
        roi_reviewed=True,
        phase_label_mapping_reviewed=True,
        evidence=(
            {
                "source_id": "authored-example",
                "origin": "synthetic",
                "citation": "authored synthetic label raster",
            },
        ),
    )
    result = summarize_phase_label_map(labels, roi, missing, metadata)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
