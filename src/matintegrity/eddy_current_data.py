"""Read DICONDE eddy-current C-scans without inferring defects or acceptance."""

from __future__ import annotations

import hashlib
import math
import warnings
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Positive

EDDY_CURRENT_IMAGE_STORAGE_UID = "1.2.840.10008.5.1.4.1.1.601.2"
MAX_DICONDE_BYTES = 64 * 1024 * 1024


class EddyCurrentDicondeRecord(Contract):
    schema_version: Literal["matintegrity.eddy_current_diconde_record.v1"] = (
        "matintegrity.eddy_current_diconde_record.v1"
    )
    physical_specimen_id: str = Field(min_length=1)
    source_role: Literal["laboratory_observation", "simulation_output", "user_record"]
    source_filename: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_bytes: int = Field(gt=0)
    sop_class_uid: str = Field(min_length=1)
    sop_instance_uid: str = Field(min_length=1)
    modality: Literal["EC"]
    acquisition_datetime_token: str | None = None
    series_description: str | None = None
    drive_type_token: str | None = None
    excitation_frequency_Hz: Positive | None = None
    rows: int = Field(gt=0)
    columns: int = Field(gt=0)
    frame_count: int = Field(gt=0)
    samples_per_pixel: int = Field(gt=0)
    bits_allocated: int = Field(gt=0)
    bits_stored: int = Field(gt=0)
    pixel_representation: Literal["unsigned_integer", "signed_integer"]
    pixel_padding_value: int | None = None
    component_order: tuple[str, ...]
    component_order_basis: str = Field(min_length=1)
    frame_view_name_tokens: tuple[str | None, ...]
    frame_rescale_slopes: tuple[float | None, ...]
    frame_rescale_intercepts: tuple[float | None, ...]
    rescale_type_token: str | None = None
    padding_count_by_component: dict[str, int]
    pixel_spacing_row_m: Positive | None = None
    pixel_spacing_column_m: Positive | None = None
    physical_unit_code_x: int | None = None
    physical_unit_code_y: int | None = None
    physical_delta_x_raw: float | None = None
    physical_delta_y_raw: float | None = None
    physical_delta_x_m: Positive | None = None
    physical_delta_y_m: Positive | None = None
    coordinate_sources_agree: bool | None = None
    coordinate_interpretation: str
    decode_warning_messages: tuple[str, ...] = ()

    @model_validator(mode="after")
    def aligned_frames(self):
        for values, label in (
            (self.component_order, "component order"),
            (self.frame_view_name_tokens, "view names"),
            (self.frame_rescale_slopes, "rescale slopes"),
            (self.frame_rescale_intercepts, "rescale intercepts"),
        ):
            if len(values) != self.frame_count:
                raise ValueError(f"DICONDE {label} must align with the frame count")
        if len(set(self.component_order)) != len(self.component_order):
            raise ValueError("DICONDE component names must be unique")
        if set(self.padding_count_by_component) != set(self.component_order):
            raise ValueError("DICONDE padding counts must align with component names")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _optional_float(value) -> float | None:
    if value is None:
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("DICONDE numeric metadata must be finite")
    return result


def _frame_values(dataset, keyword: str) -> tuple[float | None, ...]:
    values = []
    groups = getattr(dataset, "PerFrameFunctionalGroupsSequence", ())
    if len(groups) != int(dataset.NumberOfFrames):
        return tuple(None for _ in range(int(dataset.NumberOfFrames)))
    for group in groups:
        value = getattr(group, keyword, None)
        values.append(_optional_float(value))
    return tuple(values)


def _frame_text(dataset, keyword: str) -> tuple[str | None, ...]:
    values = []
    groups = getattr(dataset, "PerFrameFunctionalGroupsSequence", ())
    if len(groups) != int(dataset.NumberOfFrames):
        return tuple(None for _ in range(int(dataset.NumberOfFrames)))
    for group in groups:
        value = getattr(group, keyword, None)
        values.append(str(value) if value is not None else None)
    return tuple(values)


def _excitation_frequency(dataset) -> float | None:
    sequence = getattr(dataset, "ProbeDriveSettingsSequence", ())
    values = {
        float(item.ExcitationFrequency)
        for item in sequence
        if getattr(item, "ExcitationFrequency", None) is not None
    }
    if len(values) > 1:
        raise ValueError("DICONDE contains multiple unlabelled excitation frequencies")
    return next(iter(values), None)


def _coordinates(dataset) -> dict:
    pixel_spacing = getattr(dataset, "PixelSpacing", None)
    pixel_row_m = float(pixel_spacing[0]) * 1e-3 if pixel_spacing is not None else None
    pixel_column_m = float(pixel_spacing[1]) * 1e-3 if pixel_spacing is not None else None
    code_x = getattr(dataset, "PhysicalUnitsXDirection", None)
    code_y = getattr(dataset, "PhysicalUnitsYDirection", None)
    delta_x = _optional_float(getattr(dataset, "PhysicalDeltaX", None))
    delta_y = _optional_float(getattr(dataset, "PhysicalDeltaY", None))
    physical_x_m = None
    physical_y_m = None
    interpretation = "raw_physical_unit_codes_preserved"
    if code_x == 3 and code_y == 3 and delta_x is not None and delta_y is not None:
        # DICOM physical unit code 3 denotes centimetres; PixelSpacing uses millimetres.
        physical_x_m = abs(delta_x) * 1e-2
        physical_y_m = abs(delta_y) * 1e-2
        interpretation = "dicom_physical_unit_code_3_centimetres"
    agreement = None
    if None not in (pixel_row_m, pixel_column_m, physical_x_m, physical_y_m):
        agreement = math.isclose(pixel_column_m, physical_x_m, rel_tol=1e-6, abs_tol=1e-12) and math.isclose(
            pixel_row_m, physical_y_m, rel_tol=1e-6, abs_tol=1e-12
        )
    return {
        "pixel_spacing_row_m": pixel_row_m,
        "pixel_spacing_column_m": pixel_column_m,
        "physical_unit_code_x": int(code_x) if code_x is not None else None,
        "physical_unit_code_y": int(code_y) if code_y is not None else None,
        "physical_delta_x_raw": delta_x,
        "physical_delta_y_raw": delta_y,
        "physical_delta_x_m": physical_x_m,
        "physical_delta_y_m": physical_y_m,
        "coordinate_sources_agree": agreement,
        "coordinate_interpretation": interpretation,
    }


def read_eddy_current_diconde(
    path: str | Path,
    *,
    physical_specimen_id: str,
    source_role: Literal["laboratory_observation", "simulation_output", "user_record"],
    component_order: tuple[str, ...],
    component_order_basis: str,
) -> dict:
    """Return reviewed metadata and raw component arrays; never rotate or threshold signals."""
    if not physical_specimen_id.strip() or not component_order_basis.strip():
        raise ValueError("DICONDE specimen identity and component-order basis are required")
    source = Path(path).resolve()
    if source.stat().st_size > MAX_DICONDE_BYTES:
        raise ValueError("DICONDE file exceeds the reader safety limit")
    try:
        import pydicom
    except ImportError as exc:
        raise ImportError("DICONDE reading requires the optional science dependency pydicom") from exc

    with warnings.catch_warnings(record=True) as metadata_warnings:
        warnings.simplefilter("always")
        dataset = pydicom.dcmread(source, force=False)
    if str(dataset.SOPClassUID) != EDDY_CURRENT_IMAGE_STORAGE_UID:
        raise ValueError("DICONDE SOP class is not Eddy Current Image Storage")
    if str(dataset.Modality) != "EC":
        raise ValueError("DICONDE modality must be EC")
    transfer_syntax = dataset.file_meta.TransferSyntaxUID
    if transfer_syntax.is_compressed:
        raise ValueError("compressed DICONDE pixel data is not supported")
    frame_count = int(dataset.NumberOfFrames)
    if len(component_order) != frame_count:
        raise ValueError("caller component order must align with the DICONDE frame count")
    if int(dataset.SamplesPerPixel) != 1:
        raise ValueError("only one-sample-per-pixel DICONDE scans are supported")
    with warnings.catch_warnings(record=True) as pixel_warnings:
        warnings.simplefilter("always")
        pixels = dataset.pixel_array
    expected_shape = (frame_count, int(dataset.Rows), int(dataset.Columns))
    if pixels.shape != expected_shape:
        raise ValueError("decoded DICONDE pixel shape differs from declared dimensions")
    padding_value = getattr(dataset, "PixelPaddingValue", None)
    components = {}
    masks = {}
    padding_counts = {}
    for index, name in enumerate(component_order):
        component = np.asarray(pixels[index]).copy()
        mask = (
            component == int(padding_value)
            if padding_value is not None
            else np.zeros(component.shape, dtype=bool)
        )
        components[name] = component
        masks[name] = mask
        padding_counts[name] = int(mask.sum())

    with warnings.catch_warnings(record=True) as value_warnings:
        warnings.simplefilter("always")
        excitation_frequency = _excitation_frequency(dataset)
        view_names = _frame_text(dataset, "ViewName")
        rescale_slopes = _frame_values(dataset, "RescaleSlope")
        rescale_intercepts = _frame_values(dataset, "RescaleIntercept")
        coordinate_values = _coordinates(dataset)
        acquisition_datetime = (
            str(dataset.AcquisitionDateTime) if getattr(dataset, "AcquisitionDateTime", None) else None
        )
        series_description = (
            str(dataset.SeriesDescription) if getattr(dataset, "SeriesDescription", None) else None
        )
        drive_type = str(dataset.DriveType) if getattr(dataset, "DriveType", None) else None
        rescale_type = str(dataset.RescaleType) if getattr(dataset, "RescaleType", None) else None

    metadata = EddyCurrentDicondeRecord(
        physical_specimen_id=physical_specimen_id,
        source_role=source_role,
        source_filename=source.name,
        source_sha256=_sha256(source),
        source_bytes=source.stat().st_size,
        sop_class_uid=str(dataset.SOPClassUID),
        sop_instance_uid=str(dataset.SOPInstanceUID),
        modality="EC",
        acquisition_datetime_token=acquisition_datetime,
        series_description=series_description,
        drive_type_token=drive_type,
        excitation_frequency_Hz=excitation_frequency,
        rows=int(dataset.Rows),
        columns=int(dataset.Columns),
        frame_count=frame_count,
        samples_per_pixel=int(dataset.SamplesPerPixel),
        bits_allocated=int(dataset.BitsAllocated),
        bits_stored=int(dataset.BitsStored),
        pixel_representation=(
            "signed_integer" if int(dataset.PixelRepresentation) == 1 else "unsigned_integer"
        ),
        pixel_padding_value=int(padding_value) if padding_value is not None else None,
        component_order=component_order,
        component_order_basis=component_order_basis,
        frame_view_name_tokens=view_names,
        frame_rescale_slopes=rescale_slopes,
        frame_rescale_intercepts=rescale_intercepts,
        rescale_type_token=rescale_type,
        padding_count_by_component=padding_counts,
        decode_warning_messages=tuple(
            str(item.message) for item in (*metadata_warnings, *pixel_warnings, *value_warnings)
        ),
        **coordinate_values,
    )
    return {
        "metadata": metadata,
        "raw_component_arrays": components,
        "padding_masks": masks,
        "qualification": (
            "Raw stored components and metadata only; no rescale, phase rotation, filtering, detection, sizing, acceptance or POD interpretation is applied."
        ),
    }
