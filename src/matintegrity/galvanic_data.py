"""Provenance-bound import of a selected open Ti-6Al-4V polarization dataset."""

from __future__ import annotations

import csv
import hashlib
import io
import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .models.electrochemistry import PolarizationCurve

TI6AL4V_FIG1_SHA256 = "b119b00c03068f8e217c4ec7ae8f52dd079d6a69f52bda44221c077f6d9e9800"


class Ti6Al4VCathodicPolarizationImportRequest(Contract):
    curve_id: str = Field(min_length=1)
    medium: Literal["pbs", "pbs_h2o2"]
    expected_csv_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    surface_condition_id: str = Field(min_length=1)
    protocol_id: str = Field(min_length=1)
    electrolyte_id: str = Field(min_length=1)
    reference_electrode_id: str = Field(min_length=1)
    temperature_K: Positive
    source_conditions_reviewed: bool
    source_reference_and_scan_identity_reviewed: bool
    unit_conversion_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def pin_provider_evidence(self):
        if self.expected_csv_sha256 != TI6AL4V_FIG1_SHA256:
            raise ValueError("this provider-specific importer only accepts the pinned Zenodo Fig1.csv snapshot")
        if not any(
            row.origin == "open_dataset"
            and row.source_id == "zenodo-ti6al4v-cathodic-corrosion"
            and row.license_id == "CC0-1.0"
            and row.sha256 == self.expected_csv_sha256
            and "12727325" in row.citation
            for row in self.evidence
        ):
            raise ValueError("an open-dataset Evidence row must bind the pinned Zenodo record, CC0 license and CSV SHA-256")
        return self


def import_ti6al4v_cathodic_polarization_csv(
    csv_bytes: bytes, request: Ti6Al4VCathodicPolarizationImportRequest
) -> Calculation:
    """Import Fig1.csv; preserve signed net and Ti partial-dissolution current separately."""
    if not isinstance(csv_bytes, bytes) or len(csv_bytes) > 2_000_000:
        raise ValueError("CSV input must be bytes no larger than 2 MB")
    actual_sha256 = hashlib.sha256(csv_bytes).hexdigest()
    request_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "curve_id": request.curve_id,
        "dataset_id": "zenodo-ti6al4v-cathodic-corrosion",
        "record_url": "https://zenodo.org/records/12727325",
        "license_id": "CC0-1.0",
        "expected_csv_sha256": request.expected_csv_sha256,
        "actual_csv_sha256": actual_sha256,
        "request_sha256": request_digest,
        "medium": request.medium,
        "potential_reference_electrode_id": request.reference_electrode_id,
        "temperature_K": request.temperature_K,
        "current_density_input_unit": "microampere/cm2",
        "current_density_output_unit": "A/m2",
        "current_density_conversion_factor": 0.01,
        "net_current_and_metal_dissolution_current_separated": True,
        "partial_current_semantics": "provider-reported Ti dissolution current density derived from ICP-AES; not the electrochemical net current",
    }
    if actual_sha256 != request.expected_csv_sha256:
        return Calculation(status="out_of_scope", values=base | {"reason": "source_sha256_mismatch"})
    missing_reviews = [
        name for name in (
            "source_conditions_reviewed",
            "source_reference_and_scan_identity_reviewed",
            "unit_conversion_reviewed",
        ) if not getattr(request, name)
    ]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})

    if request.medium == "pbs":
        net_header, dissolution_header = "je (PBS)", "jTi (PBS)"
    else:
        net_header, dissolution_header = "je (PBS+33mM H2O2)", "jTi (PBS+33mM H2O2)"
    required_headers = {"Potential [V ]", net_header, dissolution_header}
    try:
        text = csv_bytes.decode("utf-8-sig", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames is None or not required_headers.issubset(reader.fieldnames):
            return Calculation(status="out_of_scope", values=base | {
                "reason": "provider_header_mismatch",
                "required_headers": sorted(required_headers),
            })
        rows = list(reader)
        if not rows:
            return Calculation(status="out_of_scope", values=base | {"reason": "empty_provider_table"})
        potentials: list[float] = []
        net_current: list[float] = []
        dissolution_current: list[float | None] = []
        point_ids: list[str] = []
        omitted_rows: list[dict[str, str | int]] = []
        for row_number, row in enumerate(rows, start=2):
            potential_token = (row.get("Potential [V ]") or "").strip()
            net_token = (row.get(net_header) or "").strip()
            dissolution_token = (row.get(dissolution_header) or "").strip()
            if not potential_token or not net_token:
                omitted_rows.append({
                    "source_row_number": row_number,
                    "reason": "missing_potential_or_net_current",
                })
                continue
            potential = float(potential_token)
            net = float(net_token)
            dissolution = float(dissolution_token) if dissolution_token else None
            if not math.isfinite(potential) or not math.isfinite(net) or (
                dissolution is not None and not math.isfinite(dissolution)
            ):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "nonfinite_numeric_value",
                    "source_row_number": row_number,
                })
            potentials.append(potential)
            net_current.append(net * 0.01)
            dissolution_current.append(None if dissolution is None else dissolution * 0.01)
            point_ids.append(f"zenodo-12727325:Fig1.csv:row-{row_number}")
    except (UnicodeDecodeError, csv.Error, TypeError, ValueError, OverflowError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "provider_csv_parse_or_numeric_error",
            "detail": str(error),
        })

    if len(potentials) < 2:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "fewer_than_two_usable_net_current_points",
            "usable_point_count": len(potentials),
            "omitted_rows": omitted_rows,
        })
    if len(potentials) > 20_000:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "polarization_curve_point_limit_exceeded",
            "usable_point_count": len(potentials),
            "maximum_point_count": 20_000,
            "omitted_rows": omitted_rows,
        })
    differences = [right - left for left, right in zip(potentials[:-1], potentials[1:], strict=True)]
    increasing = all(delta > 0 for delta in differences)
    decreasing = all(delta < 0 for delta in differences)
    if not (increasing or decreasing):
        return Calculation(status="out_of_scope", values=base | {
            "reason": "nonmonotone_or_repeated_potential_branch",
            "usable_point_count": len(potentials),
            "omitted_rows": omitted_rows,
        })
    traversal = "increasing" if increasing else "decreasing"
    if decreasing:
        potentials.reverse()
        net_current.reverse()
        dissolution_current.reverse()
        point_ids.reverse()
    curve = PolarizationCurve(
        curve_id=request.curve_id,
        surface_condition_id=request.surface_condition_id,
        protocol_id=request.protocol_id,
        electrolyte_id=request.electrolyte_id,
        reference_electrode_id=request.reference_electrode_id,
        temperature_K=request.temperature_K,
        point_ids=point_ids,
        potential_V=potentials,
        signed_net_current_density_A_m2=net_current,
        current_convention="unreviewed_signed_net",
        evidence=request.evidence,
    )
    return Calculation(status="computed", values=base | {
        "polarization_curve": curve.model_dump(mode="json"),
        "ti_dissolution_partial_current_density_A_m2": dissolution_current,
        "point_ids": point_ids,
        "source_csv_row_numbers": [int(value.rsplit("-", 1)[1]) for value in point_ids],
        "provider_scan_traversal_order": traversal,
        "arrays_reversed_for_increasing_api_potential": decreasing,
        "usable_point_count": len(potentials),
        "omitted_rows": omitted_rows,
        "actual_exposed_area_m2": None,
        "current_sign_convention": "unreviewed_signed_net",
        "scope": "One selected medium and one monotone provider branch from a single research dataset. Actual exposed area and anodic-positive sign review are not supplied by this importer.",
    }, notes=(
        "The source traversal order is retained in point IDs and reported explicitly. A monotone descending branch is reversed as a whole only to satisfy the increasing-potential PolarizationCurve contract; nonmonotone scans are rejected rather than sorted.",
        "The electrochemical net current is separate from the ICP-AES-derived Ti dissolution partial current. The importer does not infer metal loss, actual electrode area, anodic-positive convention, specimen independence, or transferability.",
    ))
