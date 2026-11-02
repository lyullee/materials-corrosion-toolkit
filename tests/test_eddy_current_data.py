from __future__ import annotations

import hashlib

import numpy as np
import pytest

from matintegrity.eddy_current_data import read_eddy_current_diconde

pydicom = pytest.importorskip("pydicom")
from pydicom.dataset import Dataset, FileDataset, FileMetaDataset  # noqa: E402
from pydicom.sequence import Sequence  # noqa: E402
from pydicom.uid import ExplicitVRLittleEndian  # noqa: E402


def _diconde(tmp_path, *, modality="EC", sop_class="1.2.840.10008.5.1.4.1.1.601.2"):
    path = tmp_path / "scan.dcm"
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = sop_class
    meta.MediaStorageSOPInstanceUID = "2.25.123"
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    dataset = FileDataset(path, {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = sop_class
    dataset.SOPInstanceUID = "2.25.123"
    dataset.Modality = modality
    dataset.AcquisitionDateTime = "20261027120000"
    dataset.SeriesDescription = "authored eddy-current C-scan"
    dataset.DriveType = "SINUSODIAL"
    drive = Dataset()
    drive.ExcitationFrequency = 150000
    dataset.ProbeDriveSettingsSequence = Sequence([drive])
    dataset.Rows = 2
    dataset.Columns = 3
    dataset.NumberOfFrames = 2
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME1"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 1
    dataset.PixelPaddingValue = -32768
    dataset.PixelSpacing = [1.0, 0.1]
    dataset.PhysicalUnitsXDirection = 3
    dataset.PhysicalUnitsYDirection = 3
    dataset.PhysicalDeltaX = 0.01
    dataset.PhysicalDeltaY = 0.1
    dataset.RescaleType = "VOL="
    groups = []
    for view, slope in (("Channel 1 X", 0.01), ("Channel 1 Y", 0.02)):
        group = Dataset()
        group.ViewName = view
        group.RescaleSlope = slope
        groups.append(group)
    dataset.PerFrameFunctionalGroupsSequence = Sequence(groups)
    pixels = np.asarray(
        [
            [[1, 2, -32768], [4, 5, 6]],
            [[-1, -2, -3], [-4, -32768, -6]],
        ],
        dtype="<i2",
    )
    dataset.PixelData = pixels.tobytes()
    dataset.save_as(path, enforce_file_format=True)
    return path, pixels


def _read(path):
    return read_eddy_current_diconde(
        path,
        physical_specimen_id="specimen-1",
        source_role="laboratory_observation",
        component_order=("real", "imaginary"),
        component_order_basis="provider record states first real and second imaginary",
    )


def test_reads_raw_diconde_components_without_rescaling_or_thresholding(tmp_path):
    path, pixels = _diconde(tmp_path)
    result = _read(path)
    metadata = result["metadata"]
    assert metadata.modality == "EC"
    assert metadata.excitation_frequency_Hz == 150000.0
    assert metadata.component_order == ("real", "imaginary")
    assert metadata.frame_rescale_slopes == (0.01, 0.02)
    assert metadata.frame_rescale_intercepts == (None, None)
    assert metadata.padding_count_by_component == {"real": 1, "imaginary": 1}
    np.testing.assert_array_equal(result["raw_component_arrays"]["real"], pixels[0])
    np.testing.assert_array_equal(result["raw_component_arrays"]["imaginary"], pixels[1])
    assert result["raw_component_arrays"]["real"][0, 2] == -32768
    assert result["padding_masks"]["imaginary"][1, 1]
    assert metadata.source_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()


def test_reconciles_dicom_centimetre_delta_with_millimetre_pixel_spacing(tmp_path):
    path, _ = _diconde(tmp_path)
    metadata = _read(path)["metadata"]
    assert metadata.pixel_spacing_row_m == pytest.approx(0.001)
    assert metadata.pixel_spacing_column_m == pytest.approx(0.0001)
    assert metadata.physical_delta_x_m == pytest.approx(0.0001)
    assert metadata.physical_delta_y_m == pytest.approx(0.001)
    assert metadata.coordinate_sources_agree is True
    assert metadata.coordinate_interpretation == "dicom_physical_unit_code_3_centimetres"


def test_preserves_coordinate_disagreement_instead_of_selecting_one_source(tmp_path):
    path, _ = _diconde(tmp_path)
    dataset = pydicom.dcmread(path)
    dataset.PixelSpacing = [2.0, 0.1]
    dataset.save_as(path, enforce_file_format=True)
    assert _read(path)["metadata"].coordinate_sources_agree is False


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"modality": "US"}, "modality"),
        ({"sop_class": "1.2.840.10008.5.1.4.1.1.7"}, "SOP class"),
    ],
)
def test_rejects_non_eddy_current_diconde(tmp_path, kwargs, message):
    path, _ = _diconde(tmp_path, **kwargs)
    with pytest.raises(ValueError, match=message):
        _read(path)


def test_requires_caller_reviewed_component_order(tmp_path):
    path, _ = _diconde(tmp_path)
    with pytest.raises(ValueError, match="align"):
        read_eddy_current_diconde(
            path,
            physical_specimen_id="specimen-1",
            source_role="laboratory_observation",
            component_order=("complex",),
            component_order_basis="invalid one-component claim",
        )
    with pytest.raises(ValueError, match="component names"):
        read_eddy_current_diconde(
            path,
            physical_specimen_id="specimen-1",
            source_role="laboratory_observation",
            component_order=("same", "same"),
            component_order_basis="invalid duplicate claim",
        )
