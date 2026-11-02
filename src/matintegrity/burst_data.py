"""Compiled pipe-burst observations with numerical/experimental and cell-origin distinctions."""

from __future__ import annotations

import hashlib
import io
import math
import zipfile
from pathlib import Path

from .contracts import canonical_digest

FIELDS = {
    "D (mm)": ("reported_diameter_m", 1e-3),
    "t (mm)": ("wall_thickness_m", 1e-3),
    "sigmay (Mpa)": ("yield_stress_Pa", 1e6),
    "sigmau (Mpa)": ("ultimate_stress_Pa", 1e6),
    "E (Mpa)": ("elastic_modulus_Pa", 1e6),
    "d (mm)": ("defect_depth_m", 1e-3),
    "l (mm)": ("defect_length_m", 1e-3),
    "w (mm)": ("defect_width_m", 1e-3),
    "Pb (Mpa)": ("burst_pressure_Pa", 1e6),
}


def read_burst_compilation(path: str | Path):
    """Read only the primary 453-row table; supplementary sheets are not extra specimens."""
    import pandas as pd
    from openpyxl import load_workbook

    data = Path(path).read_bytes()
    member = None
    if zipfile.is_zipfile(io.BytesIO(data)) and Path(path).suffix.lower() != ".xlsx":
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            members = [name for name in archive.namelist() if Path(name).name == "BursTests.xlsx"]
            if len(members) != 1:
                raise ValueError("expected one named primary burst workbook")
            member = members[0]
            workbook_data = archive.read(member)
    else:
        workbook_data = data
    workbook = load_workbook(io.BytesIO(workbook_data), data_only=False)
    sheet = workbook["Burst Database"]
    headers = {str(cell.value).strip(): cell.column for cell in sheet[21] if cell.value is not None}
    if not {"Case", "Tipo", "Ref. ID", "Material", *FIELDS} <= set(headers):
        raise ValueError("primary burst-table schema or units changed")
    if "standard" not in str(sheet["C3"].value).lower() or "calculated" not in str(sheet["C4"].value).lower():
        raise ValueError("compiler completion/geometry legend changed; review cell-origin mapping")

    def fill_signature(cell):
        return cell.fill.patternType, cell.fill.fgColor.type, cell.fill.fgColor.value, cell.fill.fgColor.tint

    property_fill, width_fill = fill_signature(sheet["B3"]), fill_signature(sheet["B4"])
    if property_fill == width_fill:
        raise ValueError("compiler legend fills are not distinguishable")
    references = {
        str(sheet.cell(row, 2).value).strip(): str(sheet.cell(row, 3).value).strip()
        for row in range(7, 20)
        if sheet.cell(row, 2).value is not None
    }

    def number(value):
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if math.isfinite(result) else None

    records = []
    for row in range(22, sheet.max_row + 1):
        case = sheet.cell(row, headers["Case"]).value
        if case is None:
            continue
        case_number = number(case)
        if case_number is None or case_number < 1 or case_number != int(case_number):
            raise ValueError("source case must be a positive integer")
        kind = str(sheet.cell(row, headers["Tipo"]).value).strip()
        if kind not in {"EXP", "FEM"}:
            raise ValueError("unknown source observation type; no experimental default is assumed")
        reference = str(sheet.cell(row, headers["Ref. ID"]).value).strip()
        values, origins, formulas = {}, {}, {}
        for header, (key, scale) in FIELDS.items():
            cell = sheet.cell(row, headers[header])
            numeric = number(cell.value)
            values[key] = None if numeric is None else numeric * scale
            marker = fill_signature(cell)
            origins[key] = (
                "non_numeric_or_missing"
                if numeric is None
                else "compiler_completed_material_property"
                if marker == property_fill
                else "compiler_inferred_geometry"
                if marker == width_fill
                else "source_reported_unverified"
            )
            if cell.data_type == "f":
                formulas[key] = str(cell.value)
        valid = all(v is not None for v in values.values())
        if valid:
            valid = (
                min(
                    values[k]
                    for k in (
                        "reported_diameter_m",
                        "wall_thickness_m",
                        "yield_stress_Pa",
                        "ultimate_stress_Pa",
                        "elastic_modulus_Pa",
                        "burst_pressure_Pa",
                    )
                )
                > 0
                and 0 <= values["defect_depth_m"] < values["wall_thickness_m"]
                and min(values["defect_length_m"], values["defect_width_m"]) >= 0
                and values["ultimate_stress_Pa"] >= values["yield_stress_Pa"]
            )
        records.append(
            dict(
                source_id="compiled-pipe-burst",
                source_row=row,
                source_case_id=int(case_number),
                observation_domain="experimental" if kind == "EXP" else "finite_element",
                pressure_result_role=(
                    "reported_experimental_burst_pressure"
                    if kind == "EXP"
                    else "reported_finite_element_failure_pressure"
                ),
                source_reference_id=reference,
                source_reference_resolved=reference in references,
                reference_mapping_status=(
                    "compilation_legend_reference"
                    if reference in references
                    else "unresolved_compilation_label"
                ),
                original_reference=references.get(reference),
                physical_specimen_identity_status="not_provided_in_primary_table",
                underlying_observation_rights_status="not_reviewed",
                material_label=str(sheet.cell(row, headers["Material"]).value).strip(),
                diameter_basis="not_explicit_in_primary_table",
                pressure_basis="not_explicit_in_primary_table",
                field_provenance=origins,
                unexecuted_formulas=formulas,
                numeric_geometry_material_valid=bool(valid),
                **values,
            )
        )
    frame = pd.DataFrame(records)
    if frame.empty or frame.source_case_id.duplicated().any():
        raise ValueError("primary burst cases must be nonempty and uniquely identified")
    numeric_fields = [key for key, _ in FIELDS.values()]
    frame["identical_reported_input_and_target"] = frame.duplicated(numeric_fields, keep=False)
    input_fields = [key for key in numeric_fields if key != "burst_pressure_Pa"]
    frame["reported_input_digest"] = [
        canonical_digest({key: row[key] for key in input_fields}) for row in records
    ]
    frame["reported_relative_depth"] = frame.defect_depth_m / frame.wall_thickness_m
    frame.attrs = dict(
        source_sha256=hashlib.sha256(data).hexdigest(),
        workbook_member=member,
        workbook_sha256=hashlib.sha256(workbook_data).hexdigest(),
        supplementary_sheets_excluded=[name for name in workbook.sheetnames if name != "Burst Database"],
        limitations="Compiler-filled properties and inferred widths are flagged, not measured. Experimental burst pressure and FEM failure pressure remain different result roles. Diameter/pressure basis, physical specimen independence, underlying-observation rights and original protocols require review. Supplementary sheets and repeated/cross-cited values are not additional independent tests. No observation is silently deduplicated or used for a qualified pressure assessment.",
    )
    return frame
