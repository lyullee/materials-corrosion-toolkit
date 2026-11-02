import numpy as np
import pytest

from matintegrity.models.phase_microstructure import PhaseFractionObservation
from matintegrity.phase_map_data import (
    PhaseLabelMapMetadata,
    PhasePixelLabel,
    phase_label_map_to_observations,
    summarize_phase_label_map,
)
from matintegrity.spatial_fields import numeric_array_digest

EVIDENCE = {"source_id": "authored-map", "origin": "synthetic", "citation": "authored raster fixture"}


def fixture(*, reviewed=True):
    labels = np.array([[1, 1, 2], [-1, 2, 2]], dtype=np.int16)
    roi = np.ones(labels.shape, dtype=bool)
    missing = np.array([[False, False, False], [False, True, False]], dtype=bool)
    metadata = PhaseLabelMapMetadata(
        map_id="map-1",
        physical_specimen_id="specimen-1",
        source_group_id="group-1",
        source_sha256="a" * 64,
        label_array_sha256=numeric_array_digest(labels),
        roi_mask_sha256=numeric_array_digest(roi),
        missing_mask_sha256=numeric_array_digest(missing),
        shape=labels.shape,
        region_id="weld-metal",
        coordinate_frame_id="image-frame-1",
        coordinate_basis="caller-reviewed rectangular pixels",
        pixel_width_m=2e-6,
        pixel_height_m=3e-6,
        segmentation_method_id="ebsd-phase-segmentation-v1",
        segmentation_basis="caller-supplied phase mapping",
        labels=(
            PhasePixelLabel(label_value=1, phase_id="alpha"),
            PhasePixelLabel(label_value=2, phase_id="gamma"),
        ),
        unclassified_label_values=(-1,),
        scale_reviewed=reviewed,
        roi_reviewed=reviewed,
        phase_label_mapping_reviewed=reviewed,
        evidence=(EVIDENCE,),
    )
    return labels, roi, missing, metadata


def test_phase_area_summary_preserves_missing_and_unclassified_pixels():
    labels, roi, missing, metadata = fixture()
    summary = summarize_phase_label_map(labels, roi, missing, metadata)
    rows = {row.phase_id: row for row in summary.phase_rows}
    assert summary.status == "computed"
    assert (summary.roi_pixel_count, summary.missing_pixel_count, summary.analyzed_pixel_count) == (6, 1, 5)
    assert (summary.classified_pixel_count, summary.unclassified_pixel_count) == (4, 1)
    assert rows["alpha"].area_fraction_of_analyzed_region == pytest.approx(0.4)
    assert rows["alpha"].area_fraction_of_classified_region == pytest.approx(0.5)
    assert rows["alpha"].area_m2 == pytest.approx(12e-12)
    assert summary.uncertainty_status == "not_estimated"


def test_map_summary_transfers_only_after_reviews_and_caller_uncertainties():
    labels, roi, missing, metadata = fixture()
    summary = summarize_phase_label_map(labels, roi, missing, metadata)
    observations = phase_label_map_to_observations(
        summary,
        {"alpha": 0.04, "gamma": 0.05},
        uncertainty_basis="caller expanded uncertainty, k=2, separate calibration study",
        fraction_basis="classified_region",
    )
    assert all(isinstance(row, PhaseFractionObservation) for row in observations)
    assert [row.measured_fraction for row in observations] == pytest.approx([0.5, 0.5])
    assert observations[0].expanded_uncertainty_fraction == 0.04
    assert observations[0].evidence[-1].origin == "user_declared"


def test_unreviewed_map_cannot_be_promoted_to_phase_observations():
    labels, roi, missing, metadata = fixture(reviewed=False)
    summary = summarize_phase_label_map(labels, roi, missing, metadata)
    with pytest.raises(ValueError, match="reviews must be complete"):
        phase_label_map_to_observations(
            summary,
            {"alpha": 0.04, "gamma": 0.05},
            uncertainty_basis="authored uncertainty",
            fraction_basis="analyzed_region",
        )


def test_undeclared_label_and_digest_mismatch_are_rejected():
    labels, roi, missing, metadata = fixture()
    labels[0, 0] = 7
    with pytest.raises(ValueError, match="digest"):
        summarize_phase_label_map(labels, roi, missing, metadata)
    changed = metadata.model_copy(update={"label_array_sha256": numeric_array_digest(labels)})
    with pytest.raises(ValueError, match="undeclared phase label"):
        summarize_phase_label_map(labels, roi, missing, changed)


def test_uncertainty_mapping_must_cover_exact_phase_set():
    labels, roi, missing, metadata = fixture()
    summary = summarize_phase_label_map(labels, roi, missing, metadata)
    with pytest.raises(ValueError, match="exactly the phase IDs"):
        phase_label_map_to_observations(
            summary,
            {"alpha": 0.04},
            uncertainty_basis="authored uncertainty",
            fraction_basis="analyzed_region",
        )
