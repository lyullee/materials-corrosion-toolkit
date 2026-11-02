"""Literature condition/property records with explicit unresolved conventions."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .contracts import canonical_digest

ELEMENTS = ("C", "Si", "Mn", "Cr", "Ni", "Mo", "N", "Cu", "Nb", "Ti")


def read_he_austenite(directory: str | Path):
    """Read the fixed release; rows are condition/property observations, not specimens."""
    import numpy as np
    import pandas as pd

    folder = Path(directory)
    csv = folder / "he_austenite_v1.0.csv"
    comp = folder / "compositions.csv"
    mapping = folder / "record_composition_map.csv"
    frame = pd.read_csv(csv, keep_default_na=False)
    compositions = pd.read_csv(comp, keep_default_na=False)
    links = pd.read_csv(mapping, keep_default_na=False)
    required = {
        "record_id",
        "source_id",
        "alloy",
        "heat",
        "material_family",
        "zone",
        "hydrogen_exposure",
        "h2_pressure_MPa",
        "hydrogen_content_wppm",
        "charging_time_h",
        "test_temperature_K",
        "strain_rate_per_s",
        "property_name",
        "property_reference",
        "property_h2",
        "relative_ratio",
        "reference_environment",
        "verified",
        "composition_basis",
        "derived",
        "derived_assumptions",
        *[e + "_wt_pct" for e in ELEMENTS],
    }
    if (
        not required.issubset(frame.columns)
        or not {"record_id", "comp_key"}.issubset(links.columns)
        or not {"comp_key", *ELEMENTS}.issubset(compositions.columns)
    ):
        raise ValueError("hydrogen compilation schema changed")
    if not frame.record_id.is_unique or not links.record_id.is_unique or not compositions.comp_key.is_unique:
        raise ValueError("unique report, mapping and composition keys required")
    if not set(links.record_id).issubset(frame.record_id) or not set(links.comp_key).issubset(
        compositions.comp_key
    ):
        raise ValueError("unresolved composition map identity")
    frame = frame.merge(links, on="record_id", how="left", validate="one_to_one").fillna({"comp_key": ""})
    comp_rows = compositions.set_index("comp_key").to_dict("index")

    def numeric(column):
        values = pd.to_numeric(frame[column].replace("", np.nan), errors="raise")
        if np.isinf(values).any():
            raise ValueError("infinite source value")
        return values

    frame["reported_gas_pressure_Pa"] = numeric("h2_pressure_MPa") * 1e6
    frame["gas_pressure_basis"] = "total_vs_partial_and_absolute_vs_gauge_unresolved"
    frame["hydrogen_mass_fraction"] = numeric("hydrogen_content_wppm") * 1e-6
    frame["charging_duration_s"] = numeric("charging_time_h") * 3600
    frame["reported_test_temperature_K"] = numeric("test_temperature_K")
    frame["reported_strain_rate_per_s"] = numeric("strain_rate_per_s")
    ref, exposed, ratio = numeric("property_reference"), numeric("property_h2"), numeric("relative_ratio")
    # The dictionary does not disambiguate the plastic-strain unit. Do not guess.
    factors = {
        "elongation": 0.01,
        "reduction of area": 0.01,
        "tensile strength": 1e6,
        "notched tensile strength": 1e6,
    }
    frame["property_unit"] = frame.property_name.map(
        {
            "elongation": "1",
            "reduction of area": "1",
            "tensile strength": "Pa",
            "notched tensile strength": "Pa",
        }
    ).fillna("unresolved")
    frame["reference_property_SI"] = ref * frame.property_name.map(factors)
    frame["hydrogen_property_SI"] = exposed * frame.property_name.map(factors)
    frame["reported_retention_ratio"] = ratio
    valid = ref.gt(0) & exposed.ge(0) & ref.notna() & exposed.notna()
    frame["arithmetic_retention_ratio"] = (exposed / ref).where(valid)
    frame["ratio_absolute_discrepancy"] = (frame.arithmetic_retention_ratio - ratio).abs()
    frame["compiler_verified"] = frame.verified.map({"yes": True, "no": False})
    if frame.compiler_verified.isna().any():
        raise ValueError("unknown compiler verification status")
    frame["compiler_category"] = frame.get("embrittlement_flag", pd.Series("", index=frame.index))
    chemistry = []
    linked_chemistry = []
    consistent = []
    for row in frame.to_dict("records"):
        fractions = {e: float(row[e + "_wt_pct"]) / 100 for e in ELEMENTS if str(row[e + "_wt_pct"]).strip()}
        if (
            any(not np.isfinite(v) or not 0 <= v <= 1 for v in fractions.values())
            or sum(fractions.values()) > 1 + 1e-12
        ):
            raise ValueError("reported chemistry lies outside mass-fraction bounds")
        key = row["comp_key"]
        if key:
            source = {e: float(comp_rows[key][e]) / 100 for e in ELEMENTS if str(comp_rows[key][e]).strip()}
            matches = fractions.keys() == source.keys() and all(
                abs(fractions[e] - source[e]) <= 1e-12 for e in fractions
            )
        elif fractions:
            raise ValueError("chemistry lacks an explicit composition identity")
        else:
            source = {}
            matches = None
        chemistry.append(fractions)
        linked_chemistry.append(source)
        consistent.append(matches)
    frame["reported_composition_mass_fraction"] = chemistry
    frame["linked_composition_mass_fraction"] = linked_chemistry
    frame["composition_link_consistent"] = consistent
    frame["specimen_independence"] = "not_established_by_compilation"
    frame["declared_condition_signature"] = [
        canonical_digest(
            {
                k: (None if row[k] == "" else row[k])
                for k in (
                    "source_id",
                    "alloy",
                    "heat",
                    "zone",
                    "hydrogen_exposure",
                    "h2_pressure_MPa",
                    "test_temperature_K",
                    "strain_rate_per_s",
                    "reference_environment",
                    "comp_key",
                )
            }
        )
        for row in frame.to_dict("records")
    ]
    columns = [
        "alloy",
        "zone",
        "hydrogen_exposure",
        "h2_pressure_MPa",
        "test_temperature_K",
        "property_name",
        "property_reference",
        "property_h2",
        "reference_environment",
    ]
    frame["coincident_reported_condition_and_values"] = frame.duplicated(columns, keep=False)
    frame.attrs.update(
        source_id="he-austenite",
        source_doi="10.5281/zenodo.23107780",
        source_hashes={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (csv, comp, mapping)},
        license_id="CC-BY-4.0",
        limitations=[
            "Report rows are not independently identified specimens. Multiple properties may share a physical test or source observation.",
            "Precharge and in-situ gas, weld zone, test/reference conditions, composition basis and compiler zero-element assumptions remain separate.",
            "Pressure meaning and plastic-strain units require original-source review. No regulatory category, missing composition, gas fugacity or period failure probability is inferred.",
            "Compiler verification is the compiler's assertion, not independent re-extraction in this package. Raw/pointwise observations are excluded from public distributions.",
        ],
    )
    return frame
