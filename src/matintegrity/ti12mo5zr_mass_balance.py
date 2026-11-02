"""Caller-approved signed mass-balance conversion of TiMoZr AESEC rates.

No electrochemical charge, oxidation state, Faraday conversion, or localized-loss
model is involved. This is a uniform equivalent-thickness transform only.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Literal

from pydantic import Field

from .contracts import Calculation, Contract, Evidence, Positive
from .registry import ModelSpec
from .ti12mo5zr_corrosion_data import (
    ARCHIVE_SHA256,
    DATASET_ID,
    LICENSE_ID,
    PROVIDER_RECORD,
    Ti12Mo5ZrWorkbookRequest,
    Ti12Mo5ZrRawRow,
    iter_local_rows,
)

AESEC_MEMBER = (
    "zenodo_APSUC_2024/Fig.5/Fig.5d/"
    "TiMoZr_DissolutionRate_OCP_PSP_OCP_AESEC.xls"
)
SOURCE_HEADERS = (
    "time [s]",
    "vTi [ng·s^-1·cm^-2]",
    "vMo [ng·s^-1·cm^-2]",
    "vZr [ng·s^-1·cm^-2]",
)
NG_S_CM2_TO_KG_M2_S = 1.0e-8


class Ti12Mo5ZrMassBalanceRequest(Contract):
    """Input and explicit review attestations for one local AESEC file."""

    schema_version: Literal["matintegrity.ti12mo5zr_mass_balance_request.v1"] = (
        "matintegrity.ti12mo5zr_mass_balance_request.v1"
    )
    local_archive_path: str = Field(min_length=1)
    density_kg_m3: Positive
    density_evidence: Evidence
    alloy_label: Literal["Ti-12Mo-5Zr"]
    analyzed_elements: tuple[Literal["Ti", "Mo", "Zr"], ...]
    computational_use_authorized: Literal[True]
    local_only_authorized: Literal[True]
    source_time_axis_is_valid_for_interval_integration: Literal[True]
    provider_positive_rate_means_outward_loss_reviewed: Literal[True]
    analyzed_element_coverage_is_complete_for_this_conversion: Literal[True]
    uniform_area_and_density_equivalent_penetration_reviewed: Literal[True]
    linear_interpolation_between_time_rows_reviewed: Literal[True]
    missing_values_are_not_imputed: Literal[True] = True


class Ti12Mo5ZrPenetrationPoint(Contract):
    schema_version: Literal["matintegrity.ti12mo5zr_penetration_point.v1"] = (
        "matintegrity.ti12mo5zr_penetration_point.v1"
    )
    source_row_number: int = Field(ge=2)
    source_row_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_archive_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    provider_time_s: float = Field(ge=0)
    elemental_mass_flux_kg_m2_s: dict[Literal["Ti", "Mo", "Zr"], float]
    signed_net_mass_flux_kg_m2_s: float
    signed_equivalent_penetration_velocity_m_s: float
    cumulative_positive_penetration_m: float = Field(ge=0)
    cumulative_negative_penetration_m: float = Field(le=0)
    cumulative_signed_net_penetration_m: float


class Ti12Mo5ZrMassBalanceResult(Contract):
    schema_version: Literal["matintegrity.ti12mo5zr_mass_balance_result.v1"] = (
        "matintegrity.ti12mo5zr_mass_balance_result.v1"
    )
    model_id: Literal["corrosion.ti12mo5zr_aesec_signed_equivalent_penetration"] = (
        "corrosion.ti12mo5zr_aesec_signed_equivalent_penetration"
    )
    dataset_id: Literal[DATASET_ID] = DATASET_ID
    provider_record: Literal[PROVIDER_RECORD] = PROVIDER_RECORD
    license_id: Literal[LICENSE_ID] = LICENSE_ID
    source_member_path: Literal[AESEC_MEMBER] = AESEC_MEMBER
    source_archive_sha256: Literal[ARCHIVE_SHA256] = ARCHIVE_SHA256
    source_member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    exact_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    exact_input_rows_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    density_kg_m3: Positive
    density_evidence: Evidence
    density_evidence_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    analyzed_elements: tuple[Literal["Ti", "Mo", "Zr"], ...]
    input_row_count: int = Field(ge=2, le=20_000)
    first_provider_time_s: float = Field(ge=0)
    last_provider_time_s: float = Field(ge=0)
    signed_net_mass_flux_unit: Literal["kg/m^2/s"] = "kg/m^2/s"
    signed_equivalent_penetration_velocity_unit: Literal["m/s"] = "m/s"
    integrated_penetration_unit: Literal["m"] = "m"
    positive_cumulative_penetration_m: float = Field(ge=0)
    negative_cumulative_penetration_m: float = Field(le=0)
    signed_net_integrated_penetration_m: float
    integration_basis: Literal["piecewise_linear_trapezoid_over_provider_time_seconds"] = (
        "piecewise_linear_trapezoid_over_provider_time_seconds"
    )
    points: tuple[Ti12Mo5ZrPenetrationPoint, ...] = Field(min_length=2, max_length=20_000)
    interpretation_scope: Literal["signed_uniform_equivalent_thickness_not_localized_loss"] = (
        "signed_uniform_equivalent_thickness_not_localized_loss"
    )


def _digest_json(value) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _row_payload(row: Ti12Mo5ZrRawRow) -> dict:
    return row.model_dump(mode="json")


def _positive_negative_interval(v0: float, v1: float, dt: float) -> tuple[float, float]:
    """Integrate positive and negative parts of the linearly interpolated interval."""
    if v0 >= 0 and v1 >= 0:
        return ((v0 + v1) * 0.5 * dt, 0.0)
    if v0 <= 0 and v1 <= 0:
        return (0.0, (v0 + v1) * 0.5 * dt)
    if v0 > 0 > v1:
        fraction_to_zero = v0 / (v0 - v1)
        return (
            0.5 * v0 * fraction_to_zero * dt,
            0.5 * v1 * (1.0 - fraction_to_zero) * dt,
        )
    fraction_to_zero = -v0 / (v1 - v0)
    return (
        0.5 * v1 * (1.0 - fraction_to_zero) * dt,
        0.5 * v0 * fraction_to_zero * dt,
    )


def calculate_mass_balance(
    request: Ti12Mo5ZrMassBalanceRequest,
) -> Ti12Mo5ZrMassBalanceResult:
    """Convert all signed element rates to a density-based equivalent penetration.

    The function reads one exact allowlisted source member through the local
    row importer. It requires explicit caller approval for time integration,
    source sign orientation, analytical-element coverage, and uniform-equivalent
    penetration. Missing values and non-increasing times fail closed.
    """
    if request.analyzed_elements != ("Ti", "Mo", "Zr"):
        raise ValueError("Analyzed element coverage must explicitly equal Ti, Mo, Zr in provider column order")
    row_request = Ti12Mo5ZrWorkbookRequest(
        local_archive_path=request.local_archive_path,
        member_path=AESEC_MEMBER,
        computational_use_authorized=request.computational_use_authorized,
        local_only_authorized=request.local_only_authorized,
    )

    points: list[Ti12Mo5ZrPenetrationPoint] = []
    rows_digest = hashlib.sha256()
    last_time: float | None = None
    last_velocity: float | None = None
    positive_total = 0.0
    negative_total = 0.0
    signed_total = 0.0
    expected_row = 2
    shared_member_sha: str | None = None
    shared_archive_sha: str | None = None
    for row in iter_local_rows(row_request):
        if row.provenance.source_kind != "aesec_elemental_dissolution_rate":
            raise ValueError("Source workbook is not the pinned AESEC dissolution-rate table")
        if row.provenance.member_path != AESEC_MEMBER or row.raw_headers != SOURCE_HEADERS:
            raise ValueError("Source member or header mapping differs from the reviewed AESEC source")
        if row.source_row_number != expected_row:
            raise ValueError("Source rows are incomplete, duplicated, or reordered")
        expected_row += 1
        if shared_member_sha is None:
            shared_member_sha = row.provenance.member_sha256
            shared_archive_sha = row.provenance.archive_sha256
        elif (row.provenance.member_sha256 != shared_member_sha
              or row.provenance.archive_sha256 != shared_archive_sha):
            raise ValueError("Source provenance changed within the supplied time series")
        if len(row.raw_cells) != 4 or any(value is None or isinstance(value, (str, bool)) for value in row.raw_cells):
            raise ValueError(f"Missing or non-numeric source cell at row {row.source_row_number}")
        time_s, ti_rate, mo_rate, zr_rate = (float(value) for value in row.raw_cells)
        if any(not math.isfinite(value) for value in (time_s, ti_rate, mo_rate, zr_rate)):
            raise ValueError(f"Non-finite source cell at row {row.source_row_number}")
        if time_s < 0 or (last_time is not None and time_s <= last_time):
            raise ValueError("Provider time must be non-negative and strictly increasing")

        row_data = _row_payload(row)
        row_json = json.dumps(row_data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        row_sha = hashlib.sha256(row_json.encode("utf-8")).hexdigest()
        rows_digest.update(row_json.encode("utf-8"))
        rows_digest.update(b"\n")
        element_flux = {
            "Ti": ti_rate * NG_S_CM2_TO_KG_M2_S,
            "Mo": mo_rate * NG_S_CM2_TO_KG_M2_S,
            "Zr": zr_rate * NG_S_CM2_TO_KG_M2_S,
        }
        net_flux = math.fsum(element_flux.values())
        velocity = net_flux / request.density_kg_m3
        if last_time is not None:
            dt = time_s - last_time
            delta = (last_velocity + velocity) * 0.5 * dt
            pos_delta, neg_delta = _positive_negative_interval(last_velocity, velocity, dt)
            signed_total += delta
            positive_total += pos_delta
            negative_total += neg_delta
        points.append(Ti12Mo5ZrPenetrationPoint(
            source_row_number=row.source_row_number,
            source_row_sha256=row_sha,
            source_member_sha256=row.provenance.member_sha256,
            provider_time_s=time_s,
            elemental_mass_flux_kg_m2_s=element_flux,
            signed_net_mass_flux_kg_m2_s=net_flux,
            signed_equivalent_penetration_velocity_m_s=velocity,
            cumulative_positive_penetration_m=positive_total,
            cumulative_negative_penetration_m=negative_total,
            cumulative_signed_net_penetration_m=signed_total,
        ))
        last_time = time_s
        last_velocity = velocity

    if len(points) < 2 or shared_member_sha is None or shared_archive_sha != ARCHIVE_SHA256:
        raise ValueError("A complete pinned time series with at least two rows is required")
    # The pinned source contains 6,121 data rows (6,122 worksheet rows including the header).
    if len(points) != 6_121:
        raise ValueError("AESEC source series is incomplete relative to the pinned worksheet shape")
    evidence_sha = _digest_json(request.density_evidence.model_dump(mode="json"))
    request_payload = request.model_dump(mode="json")
    request_sha = _digest_json(request_payload)
    return Ti12Mo5ZrMassBalanceResult(
        source_member_sha256=shared_member_sha,
        exact_request_sha256=request_sha,
        exact_input_rows_sha256=rows_digest.hexdigest(),
        density_kg_m3=request.density_kg_m3,
        density_evidence=request.density_evidence,
        density_evidence_sha256=evidence_sha,
        analyzed_elements=request.analyzed_elements,
        input_row_count=len(points),
        first_provider_time_s=points[0].provider_time_s,
        last_provider_time_s=points[-1].provider_time_s,
        positive_cumulative_penetration_m=positive_total,
        negative_cumulative_penetration_m=negative_total,
        signed_net_integrated_penetration_m=signed_total,
        points=tuple(points),
    )


def evaluate_mass_balance(request: Ti12Mo5ZrMassBalanceRequest) -> Calculation:
    result = calculate_mass_balance(request)
    return Calculation(
        values={"mass_balance": result.model_dump(mode="json")},
        notes=(
            "Signed AESEC element areal mass fluxes were converted to uniform density-equivalent penetration.",
            "No Faraday-current conversion, oxidation-state inference, spatial localization, life estimate, or probability was computed.",
            "Caller attestations govern source sign, element coverage, time integration, and uniform-equivalent penetration assumptions.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            model_id="corrosion.ti12mo5zr_aesec_signed_equivalent_penetration",
            input_type=Ti12Mo5ZrMassBalanceRequest,
            evaluator=evaluate_mass_balance,
            units={
                "mass_balance.points[].signed_net_mass_flux_kg_m2_s": "kg/m^2/s",
                "mass_balance.points[].signed_equivalent_penetration_velocity_m_s": "m/s",
                "mass_balance.signed_net_integrated_penetration_m": "m",
                "mass_balance.positive_cumulative_penetration_m": "m",
                "mass_balance.negative_cumulative_penetration_m": "m",
            },
            assumptions=(
                "Caller-approved Ti-12Mo-5Zr density is applicable to the analyzed material.",
                "All AESEC dissolution-rate columns for Ti, Mo, and Zr are complete for this conversion.",
                "Provider time is valid for interval integration, source positive sign denotes outward material loss, and linear interpolation is acceptable.",
                "The result is a uniform density-equivalent thickness over the reported area-normalized mass flux, not localized damage.",
            ),
            source_ids=(DATASET_ID, "caller-density-evidence"),
            qualification="engineering_screening",
        )
    ]
