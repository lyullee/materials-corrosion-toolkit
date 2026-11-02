"""Explicitly mapped MDEA EIS channels to complex impedance; no fitting."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .mendeley_mdea_co2_eis_rows import (
    DATASET_ID,
    LICENSE_ID,
    MDEAEISPointRow,
    MDEAEISReadAuthorization,
)
from .registry import ModelSpec

MODEL_ID = "electrochemistry.mendeley_mdea_eis_complex_channel_conversion"
MAPPING_SOURCE_ID = "caller_mendeley_eis_column_mapping"
DERIVATION_SOURCE_ID = "explicit_real_imaginary_eis_channel_to_complex_impedance"


def mendeley_mdea_eis_column_mapping_digest(
    *,
    frequency_column: str,
    real_impedance_column: str,
    imaginary_impedance_column: str,
    imaginary_axis_multiplier: Literal[-1, 1],
    experimental_or_simulated_kind: Literal["experimental", "simulated"],
    magnitude_column: str | None = None,
    magnitude_relative_tolerance: float = 0.02,
) -> str:
    """Return the canonical digest required by the reviewed mapping Evidence."""
    mapping = {
        "frequency_column": frequency_column,
        "frequency_unit": "Hz",
        "real_impedance_column": real_impedance_column,
        "real_impedance_unit": "Ohm",
        "imaginary_impedance_column": imaginary_impedance_column,
        "imaginary_impedance_unit": "Ohm",
        "imaginary_axis_multiplier": imaginary_axis_multiplier,
        "experimental_or_simulated_kind": experimental_or_simulated_kind,
        "magnitude_column": magnitude_column,
        "magnitude_relative_tolerance": magnitude_relative_tolerance,
    }
    return canonical_digest(mapping)


class MDEAEISComplexPoint(Contract):
    schema_version: Literal["matintegrity.mendeley_mdea_eis_complex_point.v1"] = (
        "matintegrity.mendeley_mdea_eis_complex_point.v1"
    )
    source_filename: str = Field(min_length=1, max_length=256)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_line_number: int = Field(ge=2, strict=True)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    data_kind: Literal["experimental", "simulated"]
    frequency_hz: float = Field(gt=0, allow_inf_nan=False)
    real_impedance_ohm: float = Field(allow_inf_nan=False)
    imaginary_impedance_ohm: float = Field(allow_inf_nan=False)
    magnitude_ohm: float = Field(ge=0, allow_inf_nan=False)
    phase_radians: float = Field(allow_inf_nan=False)
    source_magnitude_ohm: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    magnitude_relative_discrepancy: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class MDEAEISComplexConversionRequest(Contract):
    schema_version: Literal["matintegrity.mendeley_mdea_eis_complex_conversion.v1"] = (
        "matintegrity.mendeley_mdea_eis_complex_conversion.v1"
    )
    assessment_id: str = Field(min_length=1, max_length=160)
    authorization: MDEAEISReadAuthorization
    rows: tuple[MDEAEISPointRow, ...] = Field(min_length=1, max_length=100_000)
    frequency_column: str = Field(min_length=1, max_length=256)
    frequency_unit: Literal["Hz"] = "Hz"
    real_impedance_column: str = Field(min_length=1, max_length=256)
    real_impedance_unit: Literal["Ohm"] = "Ohm"
    imaginary_impedance_column: str = Field(min_length=1, max_length=256)
    imaginary_impedance_unit: Literal["Ohm"] = "Ohm"
    imaginary_axis_multiplier: Literal[-1, 1]
    column_mapping_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    column_mapping_evidence: Evidence
    column_mapping_reviewed: bool
    experimental_or_simulated_kind: Literal["experimental", "simulated"]
    magnitude_column: str | None = Field(default=None, min_length=1, max_length=256)
    magnitude_relative_tolerance: float = Field(default=0.02, gt=0.0, le=0.25)
    magnitude_consistency_reviewed: bool = False
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def validate_mapping_provenance(self):
        actual_mapping_digest = mendeley_mdea_eis_column_mapping_digest(
            frequency_column=self.frequency_column,
            real_impedance_column=self.real_impedance_column,
            imaginary_impedance_column=self.imaginary_impedance_column,
            imaginary_axis_multiplier=self.imaginary_axis_multiplier,
            experimental_or_simulated_kind=self.experimental_or_simulated_kind,
            magnitude_column=self.magnitude_column,
            magnitude_relative_tolerance=self.magnitude_relative_tolerance,
        )
        if self.column_mapping_sha256 != actual_mapping_digest:
            raise ValueError("column_mapping_sha256 must bind the exact selected columns, units and sign convention")
        if self.column_mapping_evidence.source_id != MAPPING_SOURCE_ID:
            raise ValueError("column mapping Evidence must use the dedicated caller mapping source ID")
        if self.column_mapping_evidence.sha256 != self.column_mapping_sha256 or not self.column_mapping_evidence.license_id:
            raise ValueError("column mapping Evidence must pin its reviewed mapping record and license")
        if self.magnitude_column is not None and not self.magnitude_consistency_reviewed:
            raise ValueError("magnitude comparison requires explicit column and tolerance review")
        row = self.rows[0]
        authorization_sha = canonical_digest(self.authorization.model_dump(mode="json"))
        for item in self.rows:
            if (
                item.dataset_id != DATASET_ID
                or item.license_id != LICENSE_ID
                or item.authorization_sha256 != authorization_sha
                or item.local_only is not True
                or item.data_kind != self.experimental_or_simulated_kind
                or item.source_filename != row.source_filename
                or item.provider_sha256 != row.provider_sha256
                or item.provider_file_id != row.provider_file_id
            ):
                raise ValueError("rows must share one authorized local source file and one declared data kind")
        if any(b.provider_line_number <= a.provider_line_number for a, b in zip(self.rows, self.rows[1:])):
            raise ValueError("selected rows must preserve strictly increasing provider line order")
        return self


def _numeric_column(row: MDEAEISPointRow, column_name: str) -> float:
    indices = [i for i, name in enumerate(row.ordered_header) if name == column_name]
    if len(indices) != 1:
        raise ValueError(f"mapped source column must occur exactly once: {column_name!r}")
    value = row.ordered_cells[indices[0]].numeric_value
    if value is None or not math.isfinite(value):
        raise ValueError(f"mapped source column has no finite numeric value: {column_name!r}")
    return float(value)


def evaluate_mendeley_mdea_eis_complex_conversion(
    request: MDEAEISComplexConversionRequest,
) -> Calculation:
    """Convert only caller-selected frequency, real and imaginary channels."""
    evidence = request.rows[0].evidence
    row_digest = canonical_digest([row.model_dump(mode="json") for row in request.rows])
    mapping_digest = request.column_mapping_sha256
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "request_sha256": canonical_digest(request.model_dump(mode="json")),
        "authorization_sha256": canonical_digest(request.authorization.model_dump(mode="json")),
        "dataset_id": DATASET_ID,
        "dataset_license_id": LICENSE_ID,
        "attribution": request.authorization.attribution,
        "source_filename": request.rows[0].source_filename,
        "source_file_sha256": request.rows[0].provider_sha256,
        "data_kind": request.experimental_or_simulated_kind,
        "row_set_sha256": row_digest,
        "column_mapping_sha256": mapping_digest,
        "column_mapping_evidence": request.column_mapping_evidence.model_dump(mode="json"),
        "dataset_evidence": evidence.model_dump(mode="json"),
        "input_rows_retained_in_original_order": True,
        "frequency_column": request.frequency_column,
        "frequency_unit": request.frequency_unit,
        "real_impedance_column": request.real_impedance_column,
        "real_impedance_unit": request.real_impedance_unit,
        "imaginary_impedance_column": request.imaginary_impedance_column,
        "imaginary_impedance_unit": request.imaginary_impedance_unit,
        "imaginary_axis_multiplier": request.imaginary_axis_multiplier,
        "magnitude_column": request.magnitude_column,
        "local_only": True,
        "equivalent_circuit_fitted": False,
        "corrosion_rate_inferred": False,
    }
    if not request.column_mapping_reviewed:
        return Calculation(status="needs_data", values=base | {"missing_reviews": ["column_mapping_reviewed"]})

    points: list[dict] = []
    for row in request.rows:
        try:
            frequency = _numeric_column(row, request.frequency_column)
            real = _numeric_column(row, request.real_impedance_column)
            imaginary = request.imaginary_axis_multiplier * _numeric_column(row, request.imaginary_impedance_column)
            magnitude_source = (
                _numeric_column(row, request.magnitude_column) if request.magnitude_column is not None else None
            )
        except ValueError as exc:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "mapped_source_cell_invalid",
                "source_line_number": row.provider_line_number,
                "detail": str(exc),
                "completed_point_count": len(points),
                "points": points,
            })
        if frequency <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "frequency_not_positive", "source_line_number": row.provider_line_number,
                "completed_point_count": len(points), "points": points,
            })
        magnitude = math.hypot(real, imaginary)
        phase = math.atan2(imaginary, real)
        if not (math.isfinite(magnitude) and math.isfinite(phase)):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "complex_impedance_conversion_nonfinite",
                "source_line_number": row.provider_line_number,
                "completed_point_count": len(points), "points": points,
            })
        if magnitude_source is not None:
            if magnitude_source < 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "source_magnitude_negative", "source_line_number": row.provider_line_number,
                    "completed_point_count": len(points), "points": points,
                })
            scale = max(abs(magnitude_source), magnitude, 1e-30)
            relative_error = abs(magnitude_source - magnitude) / scale
            if relative_error > request.magnitude_relative_tolerance:
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "mapped_magnitude_channel_disagrees_with_complex_components",
                    "source_line_number": row.provider_line_number,
                    "source_magnitude_ohm": magnitude_source,
                    "calculated_magnitude_ohm": magnitude,
                    "relative_discrepancy": relative_error,
                    "tolerance": request.magnitude_relative_tolerance,
                    "completed_point_count": len(points), "points": points,
                })
        point = MDEAEISComplexPoint(
            source_filename=row.source_filename,
            source_file_sha256=row.provider_sha256,
            source_line_number=row.provider_line_number,
            source_row_sha256=row.raw_line_sha256,
            data_kind=row.data_kind,
            frequency_hz=frequency,
            real_impedance_ohm=real,
            imaginary_impedance_ohm=imaginary,
            magnitude_ohm=magnitude,
            phase_radians=phase,
            source_magnitude_ohm=magnitude_source,
            magnitude_relative_discrepancy=(
                abs(magnitude_source - magnitude) / max(abs(magnitude_source), magnitude, 1e-30)
                if magnitude_source is not None else None
            ),
        )
        points.append(point.model_dump(mode="json"))
    return Calculation(status="computed", values=base | {
        "point_count": len(points),
        "points": points,
        "phase_unit": "rad",
        "impedance_unit": "Ohm",
        "magnitude_consistency_checked": request.magnitude_column is not None,
        "source_row_digest_preserved": True,
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=MDEAEISComplexConversionRequest,
        evaluator=evaluate_mendeley_mdea_eis_complex_conversion,
        units={
            "points[].frequency_hz": "Hz",
            "points[].real_impedance_ohm": "Ohm",
            "points[].imaginary_impedance_ohm": "Ohm",
            "points[].magnitude_ohm": "Ohm",
            "points[].phase_radians": "rad",
        },
        assumptions=(
            "Caller explicitly maps source headers and the imaginary-axis sign convention.",
            "Only rows from one digest-pinned local source file and one declared experimental or simulated class are accepted.",
            "The calculation preserves source row order and computes complex components, magnitude and phase only; it performs no circuit fit or corrosion inference.",
        ),
        source_ids=(MAPPING_SOURCE_ID, DERIVATION_SOURCE_ID, "mendeley_mdea_co2_eis_version3"),
        qualification="user_model",
    ),)
