"""Impact observations with specimen, irradiation and source-reference distinctions."""

from __future__ import annotations

import math
from pathlib import Path

from .contracts import canonical_digest


def read_charpy_compilation(path: str | Path):
    import pandas as pd

    frame = pd.read_excel(path, sheet_name="Charpy Data", header=1)
    frame.columns = frame.columns.str.strip()
    required = {
        "Reference",
        "Material",
        "Irradiated Specimen",
        "Test Temperature (C)",
        "Impact energy (J)",
        "Length (mm)",
        "Width (mm)",
        "Thickness (mm)",
        "Orientation",
        "DBTT Fitted Curve",
    }
    if not required <= set(frame):
        raise ValueError("Charpy compilation schema or units changed")
    references = pd.read_excel(path, sheet_name="References")
    if not {"Reference", "Link"} <= set(references):
        raise ValueError("Charpy source-reference table changed")
    links = {str(row.Reference): row.Link for row in references.itertuples(index=False)}

    def native(value):
        if pd.isna(value):
            return None
        return value.item() if hasattr(value, "item") else value

    def number(value):
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if math.isfinite(result) else None

    grouping = [
        column
        for column in frame
        if column not in {"Test Temperature (C)", "Impact energy (J)", "USE (J)", "DBTT (ºC)"}
    ]
    records = []
    for index, row in frame.iterrows():
        fields = {column: native(row[column]) for column in frame}
        temperature = number(fields["Test Temperature (C)"])
        energy = number(fields["Impact energy (J)"])
        geometry = {
            f"{name.lower()}_m": None
            if number(fields[name + " (mm)"]) is None
            else number(fields[name + " (mm)"]) / 1000
            for name in ("Length", "Width", "Thickness")
        }
        temperature_K = None if temperature is None else temperature + 273.15
        valid = (
            temperature_K is not None
            and temperature_K > 0
            and energy is not None
            and energy >= 0
            and all(v is not None and v > 0 for v in geometry.values())
        )
        reference = str(fields["Reference"])
        records.append(
            dict(
                source_id="charpy-impact",
                source_row=int(index) + 3,
                reported_fields=fields,
                original_reference_id=reference,
                original_reference_link=links.get(reference),
                reported_curve_id=fields["DBTT Fitted Curve"],
                temperature_K=temperature_K,
                absorbed_energy_J=energy,
                material_label=fields["Material"],
                irradiation_label=fields["Irradiated Specimen"],
                orientation=fields["Orientation"],
                condition_group_digest=canonical_digest({key: fields[key] for key in grouping}),
                row_valid=valid,
                **geometry,
            )
        )
    result = pd.DataFrame(records)
    result["identical_reported_record"] = frame.astype(str).duplicated(keep=False).to_numpy()
    return result
