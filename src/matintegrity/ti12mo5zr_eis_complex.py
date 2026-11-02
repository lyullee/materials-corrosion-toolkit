"""Caller-reviewed conversion of pinned Ti-12Mo-5Zr EIS rows to complex Z."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .ti12mo5zr_corrosion_data import (
    ARCHIVE_SHA256,
    DATASET_ID,
    LICENSE_ID,
    PROVIDER_RECORD,
    Ti12Mo5ZrRawRow,
)

EIS_HEADERS = (
    "Index",
    "Frequency (Hz)",
    "Time [s]",
    "|Z| [Ohm]",
    "WE.-Phase [deg]",
)
EIS_MEMBER_BYTES = 33_280
EIS_MEMBER_SHA256 = {
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMoZr_5100s_EIS.1.xls": "3fa4c218671ed7fb977d63f4aa8e7fbf283b9b1f11e1771361a6714b2ce8a815",
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMoZr_5100s_EIS.2.xls": "e052ebfc8059e75d80eff1fbc3c4bca55cd7f7a8efaa501df8c16895770b0578",
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMoZr_5100s_EIS.3.xls": "a68df7e1ad9769437dbeda246c4bafc58209648d3a9eb87806eae248efb51d3e",
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMo_5100s_EIS.1.xls": "f6f502c39793664ee2ef5381a657337facaf76b8db0d31bb7c96cdb37988d537",
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMo_5100s_EIS.2.xls": "001f608ea1a986fea783d4d436274b9b60f8cfb368b07197667cea8da185c832",
    "zenodo_APSUC_2024/Fig.3/Fig.3a/TiMo_5100s_EIS.3.xls": "f64374b39a6dfa3802f463286dce7a299f6ca3e3d19d4d8a3945da2069088491",
}
PHASE_CONVENTION_SOURCE_ID = "caller_ti12mo5zr_eis_phase_convention"


class Ti12Mo5ZrComplexEISPoint(Contract):
    """One complex-impedance point retaining the exact provider row lineage."""

    schema_version: Literal["matintegrity.ti12mo5zr_complex_eis_point.v1"] = (
        "matintegrity.ti12mo5zr_complex_eis_point.v1"
    )
    source_row_number: int = Field(ge=2, le=75, strict=True)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_member_path: str = Field(min_length=1)
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_archive_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    provider_frequency_Hz: float = Field(gt=0, allow_inf_nan=False)
    provider_time_s: float = Field(ge=0, allow_inf_nan=False)
    magnitude_ohm: float = Field(ge=0, allow_inf_nan=False)
    phase_degrees_as_reported: float = Field(allow_inf_nan=False)
    phase_sign: Literal[1, -1]
    phase_convention: Literal["reported_phase_positive_imaginary", "reported_phase_negative_imaginary"]
    impedance_real_ohm: float = Field(allow_inf_nan=False)
    impedance_imaginary_ohm: float = Field(allow_inf_nan=False)


class Ti12Mo5ZrComplexEISRequest(Contract):
    """Convert one complete allowlisted spectrum under explicit phase-sign review."""

    schema_version: Literal["matintegrity.ti12mo5zr_complex_eis_request.v1"] = (
        "matintegrity.ti12mo5zr_complex_eis_request.v1"
    )
    rows: tuple[Ti12Mo5ZrRawRow, ...] = Field(min_length=74, max_length=74)
    phase_sign: Literal[1, -1]
    phase_convention: Literal["reported_phase_positive_imaginary", "reported_phase_negative_imaginary"]
    phase_convention_evidence: Evidence
    phase_convention_reviewed: bool
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def validate_source_rows(self):
        if self.phase_sign == 1 and self.phase_convention != "reported_phase_positive_imaginary":
            raise ValueError("phase sign and convention label disagree")
        if self.phase_sign == -1 and self.phase_convention != "reported_phase_negative_imaginary":
            raise ValueError("phase sign and convention label disagree")
        if self.phase_convention_evidence.source_id != PHASE_CONVENTION_SOURCE_ID:
            raise ValueError("phase convention Evidence must use the declared caller phase-convention source ID")

        first = self.rows[0].provenance
        expected_member_digest = EIS_MEMBER_SHA256.get(first.member_path)
        if expected_member_digest is None:
            raise ValueError("rows must come from one exact allowlisted Ti-12Mo-5Zr EIS member")
        if (
            first.source_kind != "eis_spectrum"
            or first.dataset_id != DATASET_ID
            or first.provider_record != PROVIDER_RECORD
            or first.license_id != LICENSE_ID
            or first.archive_sha256 != ARCHIVE_SHA256
            or first.member_sha256 != expected_member_digest
            or first.member_bytes != EIS_MEMBER_BYTES
            or first.row_count_including_header != 75
            or first.column_count != len(EIS_HEADERS)
        ):
            raise ValueError("EIS row provenance differs from the reviewed archive/member pins")
        for index, row in enumerate(self.rows):
            provenance = row.provenance
            if provenance.model_dump(mode="json") != first.model_dump(mode="json"):
                raise ValueError("all rows must share one workbook provenance record")
            if row.source_row_number != index + 2:
                raise ValueError("the complete 74-row spectrum must retain provider row order 2 through 75")
            if row.raw_headers != EIS_HEADERS or len(row.raw_cells) != len(EIS_HEADERS):
                raise ValueError("EIS headers and five-column row shape must match the pinned source")
        if self.phase_convention_evidence.origin == "open_dataset":
            if self.phase_convention_evidence.license_id is None or self.phase_convention_evidence.sha256 is None:
                raise ValueError("open phase-convention evidence requires a license and source digest")
        return self


def _finite_cell(value: object, label: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a numeric source cell")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{label} must be finite")
    if positive and numeric <= 0:
        raise ValueError(f"{label} must be positive")
    if nonnegative and numeric < 0:
        raise ValueError(f"{label} must be nonnegative")
    return numeric


def evaluate_ti12mo5zr_complex_eis(request: Ti12Mo5ZrComplexEISRequest) -> Calculation:
    """Resolve |Z| and reviewed phase into real/imaginary components."""
    provenance = request.rows[0].provenance
    rows_sha256 = canonical_digest([row.model_dump(mode="json") for row in request.rows])
    request_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "dataset_id": DATASET_ID,
        "provider_record": PROVIDER_RECORD,
        "license_id": LICENSE_ID,
        "archive_sha256": ARCHIVE_SHA256,
        "member_path": provenance.member_path,
        "member_sha256": provenance.member_sha256,
        "row_count": len(request.rows),
        "input_rows_sha256": rows_sha256,
        "request_sha256": request_sha256,
        "phase_sign": request.phase_sign,
        "phase_convention": request.phase_convention,
        "phase_convention_evidence": request.phase_convention_evidence.model_dump(mode="json"),
        "provider_time_interpretation": "preserved_scan_time_not_inferred_immersion_time",
        "impedance_area_normalization_performed": False,
        "equivalent_circuit_fit_performed": False,
        "corrosion_or_alloy_ranking_inferred": False,
        "local_only": True,
    }
    if not request.phase_convention_reviewed:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": ["phase_convention_reviewed"]},
            notes=("Review the instrument's phase sign convention before interpreting the complex-impedance components.",),
        )

    points: list[dict] = []
    for row in request.rows:
        cells = row.raw_cells
        try:
            frequency = _finite_cell(cells[1], "frequency", positive=True)
            scan_time = _finite_cell(cells[2], "provider time", nonnegative=True)
            magnitude = _finite_cell(cells[3], "impedance magnitude", nonnegative=True)
            phase_deg = _finite_cell(cells[4], "phase")
        except ValueError as error:
            return Calculation(
                status="out_of_scope",
                values=base | {
                    "out_of_scope_reason": "invalid_numeric_eis_source_cell",
                    "source_row_number": row.source_row_number,
                    "reason": str(error),
                    "completed_point_count": len(points),
                    "points": points,
                },
                notes=("Every EIS cell must be numeric and finite with a positive frequency and nonnegative magnitude/time.",),
            )

        # Reduce before converting to radians so very large finite phase values
        # cannot overflow an intermediate multiplication.
        reduced_phase = math.remainder(phase_deg, 360.0) * (math.pi / 180.0) * request.phase_sign
        real = magnitude * math.cos(reduced_phase)
        imaginary = magnitude * math.sin(reduced_phase)
        if not (math.isfinite(real) and math.isfinite(imaginary)):
            return Calculation(
                status="out_of_scope",
                values=base | {
                    "out_of_scope_reason": "nonfinite_complex_impedance",
                    "source_row_number": row.source_row_number,
                    "completed_point_count": len(points),
                    "points": points,
                },
                notes=("Complex impedance conversion exceeded finite numeric support; no clipping was applied.",),
            )
        point = Ti12Mo5ZrComplexEISPoint(
            source_row_number=row.source_row_number,
            source_row_sha256=canonical_digest(row.model_dump(mode="json")),
            source_member_path=provenance.member_path,
            source_member_sha256=provenance.member_sha256,
            provider_frequency_Hz=frequency,
            provider_time_s=scan_time,
            magnitude_ohm=magnitude,
            phase_degrees_as_reported=phase_deg,
            phase_sign=request.phase_sign,
            phase_convention=request.phase_convention,
            impedance_real_ohm=real,
            impedance_imaginary_ohm=imaginary,
        )
        points.append(point.model_dump(mode="json"))

    return Calculation(
        values=base | {
            "points": points,
            "point_count": len(points),
            "provider_order_preserved": True,
            "conversion": "Z = magnitude * exp(i * caller_reviewed_signed_phase)",
            "output_units": {
                "frequency": "Hz",
                "provider_time": "s",
                "impedance_magnitude": "ohm",
                "impedance_real": "ohm",
                "impedance_imaginary": "ohm",
            },
        },
        notes=(
            "Only the caller-selected phase sign is applied to the provider-reported phase; source row order and scan-time values are preserved.",
            "This conversion does not establish immersion-time semantics, normalize by electrode area, fit an equivalent circuit, infer corrosion resistance, or rank alloys.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "corrosion.ti12mo5zr_eis_complex_impedance",
        Ti12Mo5ZrComplexEISRequest,
        evaluate_ti12mo5zr_complex_eis,
        {
            "points[].provider_frequency_Hz": "Hz",
            "points[].provider_time_s": "s",
            "points[].magnitude_ohm": "ohm",
            "points[].impedance_real_ohm": "ohm",
            "points[].impedance_imaginary_ohm": "ohm",
        },
        (
            "Convert one exact allowlisted Ti-12Mo-5Zr EIS spectrum from provider impedance magnitude and degrees to complex components under a caller-evidenced phase-sign convention.",
            "Provider order and scan-time values are retained; there is no immersion-time inference, area normalization, equivalent-circuit fitting, corrosion inference, or alloy ranking.",
        ),
        (DATASET_ID, "caller_ti12mo5zr_eis_phase_convention"),
        qualification="engineering_screening",
    )]
