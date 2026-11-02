"""Provenance-preserving summaries of caller-selected TiMoZr OCP time windows."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec
from .ti12mo5zr_corrosion_data import (
    ARCHIVE_SHA256, DATASET_ID, LICENSE_ID, PROVIDER_RECORD, Ti12Mo5ZrRawRow,
)

OCP_HEADERS = ("Index", "Time [s]", "Potential [V]")
OCP_MEMBER_SHA256 = {
    "zenodo_APSUC_2024/Fig.2/TiMoZr_5100s_OCP.1.xls": "e1e76ff4cb2216ea03968032e7cf4fdc2805afb632dc3243a3e181348d73d516",
    "zenodo_APSUC_2024/Fig.2/TiMoZr_5100s_OCP.2.xls": "d81d71195e3ebf75c6d671c9405e5e77a2affb7c42474565dd333f868c7f9d57",
    "zenodo_APSUC_2024/Fig.2/TiMoZr_5100s_OCP.3.xls": "6f8ad5522adb0e53ad1338ed629c093b9655e105461eefce439271d2c80c9e68",
}
INTERFACE_ID = "corrosion.ti12mo5zr_ocp_signed_window_summary"
SOURCE_ID = "caller_ti12mo5zr_ocp_window_summary"


class Ti12Mo5ZrOCPWindowRequest(Contract):
    """Summarize one exact pinned OCP record over a finite caller time window."""

    schema_version: Literal["matintegrity.ti12mo5zr_ocp_window_request.v1"] = "matintegrity.ti12mo5zr_ocp_window_request.v1"
    rows: tuple[Ti12Mo5ZrRawRow, ...] = Field(min_length=2, max_length=10_200)
    window_start_s: float = Field(ge=0, allow_inf_nan=False)
    window_end_s: float = Field(gt=0, allow_inf_nan=False)
    potential_reference_label: str = Field(min_length=1)
    potential_reference_evidence: Evidence
    linear_interpolation_reviewed: bool
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]

    @model_validator(mode="after")
    def validate_source(self):
        if self.window_end_s <= self.window_start_s:
            raise ValueError("OCP summary window must have positive duration")
        first = self.rows[0].provenance
        digest = OCP_MEMBER_SHA256.get(first.member_path)
        if digest is None or first.source_kind != "ocp_monitor" or first.member_sha256 != digest:
            raise ValueError("rows must belong to one exact pinned Ti-12Mo-5Zr OCP monitor")
        if (first.dataset_id != DATASET_ID or first.provider_record != PROVIDER_RECORD
                or first.license_id != LICENSE_ID or first.archive_sha256 != ARCHIVE_SHA256
                or first.row_count_including_header != 10_201 or first.column_count != 3):
            raise ValueError("OCP provenance does not match the reviewed source pin")
        if len(self.rows) != first.row_count_including_header - 1:
            raise ValueError("complete OCP row sequence is required; partial selections are unsupported")
        for i, row in enumerate(self.rows):
            if row.provenance.model_dump(mode="json") != first.model_dump(mode="json"):
                raise ValueError("all rows must share exact workbook provenance")
            if row.source_row_number != i + 2 or row.raw_headers != OCP_HEADERS:
                raise ValueError("OCP rows must preserve the complete provider order and headers")
        return self


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be a numeric provider value")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def summarize_ti12mo5zr_ocp_window(request: Ti12Mo5ZrOCPWindowRequest) -> Calculation:
    """Compute signed potential descriptors over an explicitly reviewed window.

    The integration uses piecewise-linear interpolation of provider samples,
    including interpolated values at the requested boundaries. Potential
    reference is caller-labeled and carried verbatim; it is never inferred.
    """
    provenance = request.rows[0].provenance
    base = {
        "model_id": INTERFACE_ID,
        "dataset_id": DATASET_ID, "provider_record": PROVIDER_RECORD,
        "license_id": LICENSE_ID, "archive_sha256": ARCHIVE_SHA256,
        "member_path": provenance.member_path, "member_sha256": provenance.member_sha256,
        "input_rows_sha256": canonical_digest([row.model_dump(mode="json") for row in request.rows]),
        "request_sha256": canonical_digest(request.model_dump(mode="json")),
        "potential_reference_label": request.potential_reference_label,
        "potential_reference_evidence": request.potential_reference_evidence.model_dump(mode="json"),
        "window_start_s": request.window_start_s, "window_end_s": request.window_end_s,
        "local_only": True,
        "interpretation_limits": ["provider potential reference is not inferred", "OCP descriptors are not corrosion rate, polarization resistance, alloy ranking, acceptance, life, or failure probability"],
    }
    if not request.linear_interpolation_reviewed:
        return Calculation(status="needs_data", values=base | {"missing_reviews": ["linear_interpolation_reviewed"]},
                           notes=("Review piecewise-linear interpolation over the selected OCP window.",))
    times: list[float] = []
    potentials: list[float] = []
    try:
        for row in request.rows:
            times.append(_number(row.raw_cells[1], "time"))
            potentials.append(_number(row.raw_cells[2], "potential"))
    except (ValueError, IndexError) as exc:
        return Calculation(status="out_of_scope", values=base | {"reason": str(exc)}, notes=("Missing or invalid provider cells are not imputed.",))
    if any(b <= a for a, b in zip(times, times[1:])):
        return Calculation(status="out_of_scope", values=base | {"reason": "provider times are not strictly increasing"},
                           notes=("Provider order is retained and never silently sorted.",))
    start, end = request.window_start_s, request.window_end_s
    if start < times[0] or end > times[-1]:
        return Calculation(status="out_of_scope", values=base | {"reason": "requested window is outside provider time support"},
                           notes=("No extrapolation is performed.",))
    def at(t: float) -> float:
        import bisect
        j = bisect.bisect_left(times, t)
        if j < len(times) and times[j] == t:
            return potentials[j]
        i = j - 1
        fraction = (t - times[i]) / (times[j] - times[i])
        return potentials[i] + fraction * (potentials[j] - potentials[i])
    inner = [i for i, t in enumerate(times) if start < t < end]
    ts = [start, *(times[i] for i in inner), end]
    vs = [at(t) for t in ts]
    area = math.fsum((b - a) * (x + y) * 0.5 for a, b, x, y in zip(ts[:-1], ts[1:], vs[:-1], vs[1:], strict=True))
    if not math.isfinite(area):
        return Calculation(status="out_of_scope", values=base | {"reason": "window integral exceeds finite numeric range"})
    values = base | {
        "sample_count_in_window_including_interpolated_boundaries": len(ts),
        "potential_start_V": vs[0], "potential_end_V": vs[-1],
        "signed_change_V": vs[-1] - vs[0], "time_average_potential_V": area / (end - start),
        "signed_potential_time_integral_V_s": area,
        "minimum_potential_V": min(vs), "maximum_potential_V": max(vs),
        "provider_time_unit": "s", "provider_potential_unit": "V",
        "integration": "piecewise_linear_trapezoid_with_interpolated_window_boundaries",
    }
    return Calculation(values=values, notes=("These are signed potential-window descriptors and do not establish corrosion kinetics or material performance.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=INTERFACE_ID,
        input_type=Ti12Mo5ZrOCPWindowRequest,
        evaluator=summarize_ti12mo5zr_ocp_window,
        units={"window_start_s": "s", "window_end_s": "s", "potential_start_V": "V", "potential_end_V": "V", "signed_change_V": "V", "time_average_potential_V": "V", "signed_potential_time_integral_V_s": "V*s", "minimum_potential_V": "V", "maximum_potential_V": "V"},
        assumptions=("OCP rows are complete and ordered within the exact pinned source member.", "Potential reference and piecewise-linear interpolation review are explicit caller inputs."),
        source_ids=(SOURCE_ID,),
        qualification="engineering_screening",
    )]
