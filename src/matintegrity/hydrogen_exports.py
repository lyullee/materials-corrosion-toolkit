"""Read reviewed numeric exports while retaining unresolved experimental conventions."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Fraction, Positive, canonical_digest

FARADAY_C_MOL_ELECTRONS = 96485.33212331001
TDS_PPM_BASES = {"unresolved", "hydrogen_mass_per_sample_mass"}


class TabularExportProvenance(Contract):
    """Declared export chain; matching digests establish bytes, not physical validity."""

    schema_version: Literal["matintegrity.tabular_export.v1"] = "matintegrity.tabular_export.v1"
    dataset_id: str = Field(min_length=1)
    archive_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    member_path: str = Field(min_length=1)
    member_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    tool_name: str = Field(min_length=1)
    tool_version: str = Field(min_length=1)
    workbook_id: str = Field(min_length=1)
    worksheet_id: str = Field(min_length=1)
    csv_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    export_method: Literal["origin_viewer_csv"] = "origin_viewer_csv"
    identity_review: Literal["viewer_reviewed", "mapping_requires_review"] = "mapping_requires_review"


class HydrogenPermeationSignalCalibration(Contract):
    """Reviewed conversion from one exported current/clock pair to atomic-hydrogen flux."""

    schema_version: Literal["matintegrity.hydrogen_permeation_signal_calibration.v1"] = (
        "matintegrity.hydrogen_permeation_signal_calibration.v1"
    )
    calibration_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    export_csv_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_current_channel: Literal["current_A", "processed_current_A"]
    selected_clock_channel: Literal["instrument_clock_s", "shifted_clock_s"]
    clock_origin_s: float
    current_sign_for_outward_hydrogen: Literal[-1, 1]
    membrane_area_m2: Positive
    electron_mol_per_hydrogen_atom_mol: Positive
    current_efficiency: Fraction
    background_handling: Literal["none_raw_channel", "source_processed_channel"]
    area_basis: str = Field(min_length=1)
    clock_origin_basis: str = Field(min_length=1)
    physical_mapping_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HydrogenTdsSignalCalibration(Contract):
    """Reviewed mass-ppm conversion for exactly one exported TDS series."""

    schema_version: Literal["matintegrity.hydrogen_tds_signal_calibration.v1"] = (
        "matintegrity.hydrogen_tds_signal_calibration.v1"
    )
    calibration_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    heating_program_id: str = Field(min_length=1)
    export_csv_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    series_index: int = Field(ge=1)
    series_label: str = Field(min_length=1)
    sample_mass_kg: Positive | None = None
    hydrogen_atomic_molar_mass_kg_mol: Positive
    rate_basis: Literal["hydrogen_mass_ppm_per_sample_mass_per_s"]
    integral_basis: Literal["hydrogen_mass_ppm_per_sample_mass"]
    detector_response_reviewed: bool
    sample_mass_reviewed: bool
    ppm_basis_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def reviewed_optional_mass(self):
        if self.sample_mass_kg is None and self.sample_mass_reviewed:
            raise ValueError("sample mass cannot be reviewed when no mass is supplied")
        if self.sample_mass_kg is not None and not self.sample_mass_reviewed:
            raise ValueError("a supplied sample mass must be reviewed")
        return self


def _load(path, provenance):
    if not isinstance(provenance, TabularExportProvenance):
        raise TypeError("a validated TabularExportProvenance is required")
    content = Path(path).read_bytes()
    if hashlib.sha256(content).hexdigest() != provenance.csv_sha256:
        raise ValueError("export content digest mismatch")
    rows = list(csv.reader(io.StringIO(content.decode("utf-8-sig")), strict=True))
    while rows and not any(cell.strip() for cell in rows[-1]):
        rows.pop()
    if not rows:
        raise ValueError("empty export")
    return rows


def _number(value, *, optional=False):
    if optional and value.strip() in {"", "--"}:
        return math.nan
    try:
        number = float(value)
    except ValueError as error:
        raise ValueError("non-numeric or incomplete observation") from error
    if not math.isfinite(number):
        raise ValueError("non-finite observation")
    return number


def _factor(unit, supported):
    if unit == "unresolved":
        return math.nan
    if unit not in supported:
        raise ValueError(f"unsupported declared unit: {unit}")
    return supported[unit]


def _attrs(frame, provenance, **metadata):
    frame.attrs.update(
        export_provenance=provenance.model_dump(mode="json"),
        specimen_independence="not_established_by_export",
        physical_qualification="axis_and_protocol_review_required_before_calibration",
        **metadata,
    )
    return frame


def read_permeation_export(
    path: str | Path,
    provenance: TabularExportProvenance,
    *,
    potential_unit: str = "unresolved",
    current_unit: str = "unresolved",
    clock_unit: str = "unresolved",
    clock_policy: Literal["strict", "preserve"] = "strict",
):
    """Keep instrument and processed channels separate; never choose a charging origin."""
    import numpy as np
    import pandas as pd

    if clock_policy not in {"strict", "preserve"}:
        raise ValueError("unknown clock policy")
    voltage = _factor(potential_unit, {"V": 1.0, "mV": 1e-3})
    current = _factor(current_unit, {"A": 1.0, "mA": 1e-3, "uA": 1e-6})
    clock = _factor(clock_unit, {"s": 1.0, "ms": 1e-3, "min": 60.0})
    rows = _load(path, provenance)
    headers, records = [], []
    width = None
    for index, row in enumerate(rows, 1):
        try:
            float(row[0])
            starts_numeric = True
        except (ValueError, IndexError):
            starts_numeric = False
        if not starts_numeric and not records:
            for cell in row[1:3]:
                try:
                    float(cell)
                except ValueError:
                    continue
                raise ValueError("partial numeric observation cannot be treated as a header")
            headers.append(row)
            if len(headers) > 8:
                raise ValueError("unrecognized numeric export header")
            continue
        if width is None:
            width = len(row)
        if not starts_numeric or len(row) != width or not 3 <= width <= 5:
            raise ValueError("malformed or interleaved permeation observation")
        values = [_number(v, optional=i >= 3) for i, v in enumerate(row)]
        values += [math.nan] * (5 - width)
        records.append([index, *values])
    if not records:
        raise ValueError("no permeation observations")
    frame = pd.DataFrame(
        records,
        columns=[
            "source_row",
            "potential_source",
            "current_source",
            "instrument_clock_source",
            "shifted_clock_source",
            "processed_current_source",
        ],
    )
    delta = np.diff(frame.instrument_clock_source.to_numpy())
    if clock_policy == "strict" and np.any(delta <= 0):
        raise ValueError("instrument clock must increase; use explicit preserve policy to retain it")
    for source, target, factor in (
        ("potential_source", "potential_V", voltage),
        ("current_source", "current_A", current),
        ("instrument_clock_source", "instrument_clock_s", clock),
        ("shifted_clock_source", "shifted_clock_s", clock),
        ("processed_current_source", "processed_current_A", current),
    ):
        frame[target] = frame[source] * factor
    offsets = frame.instrument_clock_source - frame.shifted_clock_source
    corrections = frame.current_source - frame.processed_current_source

    def constant_or_none(values):
        values = values.dropna().to_numpy()
        return (
            float(values[0])
            if len(values) and np.allclose(values, values[0], rtol=1e-10, atol=1e-12)
            else None
        )

    text = " ".join(" ".join(r) for r in headers)
    match = re.search(r"start charging time:\s*([0-9.]+)\s*s", text, flags=re.I)
    return _attrs(
        frame,
        provenance,
        header_rows=headers,
        declared_units=dict(potential=potential_unit, current=current_unit, clock=clock_unit),
        clock_policy=clock_policy,
        repeated_clock_steps=int(np.sum(delta == 0)),
        reversed_clock_steps=int(np.sum(delta < 0)),
        instrument_minus_shifted_clock_source=constant_or_none(offsets),
        source_current_subtraction=constant_or_none(corrections),
        comment_charging_time_s=float(match[1]) if match else None,
        charging_origin="not_selected",
        current_density_area="unresolved",
        processed_channel_definition="source_processing_not_recomputed",
    )


def read_permeation_summary(
    path: str | Path,
    provenance: TabularExportProvenance,
    *,
    label_policy: Literal["strict", "join_split_ti_mo"] = "strict",
    diffusivity_unit: str = "unresolved",
    concentration_unit: str = "unresolved",
):
    """Read reported effective coefficients, keeping unknown ppm/error conventions."""
    import pandas as pd

    if label_policy not in {"strict", "join_split_ti_mo"}:
        raise ValueError("unknown label policy")
    factor = _factor(diffusivity_unit, {"m2/s": 1.0})
    _factor(concentration_unit, {"ppm": 1.0})
    records, repaired = [], []
    for index, original in enumerate(_load(path, provenance), 1):
        row = original
        if len(row) == 7 and row[:2] == ["(Ti", "Mo)C steel"] and label_policy == "join_split_ti_mo":
            row = [",".join(row[:2]), *row[2:]]
            repaired.append(index)
        if len(row) != 6 or not row[0].strip() or not row[5].strip():
            raise ValueError("summary requires six columns; any split-label repair must be explicit")
        values = [_number(row[1]), *[_number(v, optional=True) for v in row[2:5]]]
        if values[0] <= 0 or any(v < 0 for v in values[1:]):
            raise ValueError("invalid summary coefficient or error value")
        records.append([index, row[0], *values, row[5]])
    frame = pd.DataFrame(
        records,
        columns=[
            "source_row",
            "material_label",
            "effective_diffusivity_source",
            "diffusivity_error_source",
            "concentration_source",
            "concentration_error_source",
            "material_alias",
        ],
    )
    frame["effective_diffusivity_m2_s"] = frame.effective_diffusivity_source * factor
    return _attrs(
        frame,
        provenance,
        structural_repair_source_rows=repaired,
        declared_units=dict(diffusivity=diffusivity_unit, concentration=concentration_unit),
        ppm_basis="unresolved",
        error_statistic="unresolved",
        diffusivity_meaning="source_reported_effective_not_intrinsic_lattice",
    )


def read_tds_export(
    path: str | Path,
    provenance: TabularExportProvenance,
    *,
    temperature_unit: str = "unresolved",
    rate_unit: str = "unresolved",
    integral_unit: str = "unresolved",
    ppm_basis: Literal["unresolved", "hydrogen_mass_per_sample_mass"] = "unresolved",
):
    """Read variable-length temperature/rate/derived-integral triples without sorting."""
    import pandas as pd

    _factor(temperature_unit, {"degC": 1.0, "K": 1.0})
    _factor(rate_unit, {"ppm/s": 1.0})
    _factor(integral_unit, {"ppm": 1.0})
    if ppm_basis not in TDS_PPM_BASES:
        raise ValueError("unknown TDS ppm basis")
    rows = _load(path, provenance)
    headers = rows[0]
    if not headers or len(headers) % 3 or any(len(r) != len(headers) for r in rows):
        raise ValueError("TDS export must contain complete column triples")
    records, tail_missing_marker_rows = [], {}
    for start in range(0, len(headers), 3):
        label = headers[start + 1]
        if not label or headers[start + 2] != label or headers[start].strip():
            raise ValueError("TDS rate/integral series labels must agree")
        ended, count, missing_marker_rows = False, 0, 0
        for index, row in enumerate(rows[1:], 2):
            triple = row[start : start + 3]
            if all(v.strip() in {"", "--"} for v in triple):
                ended = True
                missing_marker_rows += int(any(v.strip() == "--" for v in triple))
                continue
            if ended:
                raise ValueError("interior missing TDS observations must be reviewed")
            values = [_number(v) for v in triple]
            count += 1
            records.append([start // 3 + 1, label, count, index, *values])
        if not count:
            raise ValueError("empty TDS series")
        tail_missing_marker_rows[str(start // 3 + 1)] = missing_marker_rows
    frame = pd.DataFrame(
        records,
        columns=[
            "series_index",
            "series_label",
            "observation_index",
            "source_row",
            "temperature_source",
            "rate_source",
            "integral_source",
        ],
    )
    if temperature_unit == "unresolved":
        frame["temperature_K"] = math.nan
    else:
        frame["temperature_K"] = frame.temperature_source + (273.15 if temperature_unit == "degC" else 0)
        if frame.temperature_K.le(0).any():
            raise ValueError("temperature is outside the absolute scale")
    return _attrs(
        frame,
        provenance,
        declared_units=dict(temperature=temperature_unit, rate=rate_unit, integral=integral_unit),
        ppm_basis=ppm_basis,
        sample_clock="not_available_in_export",
        tail_missing_marker_rows=tail_missing_marker_rows,
        integral_meaning="source_derived_integral_not_independent_measurement",
        ordering="original_temperature_observation_order",
        full_temperature_range_is_summary_integration_range=False,
    )


def read_tds_exposure_summary(
    path: str | Path,
    provenance: TabularExportProvenance,
    *,
    exposure_unit: str = "unresolved",
    content_unit: str = "unresolved",
    ppm_basis: Literal["unresolved", "hydrogen_mass_per_sample_mass"] = "unresolved",
):
    """Preserve unsorted source conditions and separate uncharged from zero exposure."""
    import pandas as pd

    time_factor = _factor(exposure_unit, {"h": 3600.0, "s": 1.0})
    _factor(content_unit, {"ppm": 1.0})
    if ppm_basis not in TDS_PPM_BASES:
        raise ValueError("unknown TDS ppm basis")
    rows = _load(path, provenance)
    if len(rows) < 3 or any(len(r) != 5 for r in rows):
        raise ValueError("unexpected exposure summary shape")
    if rows[0][0] or rows[0][2] or not rows[0][1] or not rows[0][3]:
        raise ValueError("missing exposure summary series headers")
    records = []
    for index, row in enumerate(rows[2:], 3):
        if row[4].strip() not in {"", "--"}:
            raise ValueError("unreviewed auxiliary summary column")
        for start in (0, 2):
            uncharged = row[start].strip().lower() == "uncharged"
            exposure = math.nan if uncharged else _number(row[start])
            content = _number(row[start + 1])
            if exposure < 0 or content < 0:
                raise ValueError("invalid exposure or content")
            records.append(
                [
                    index,
                    start // 2 + 1,
                    rows[0][start + 1],
                    row[start],
                    uncharged,
                    exposure,
                    exposure * time_factor,
                    content,
                ]
            )
    frame = pd.DataFrame(
        records,
        columns=[
            "source_row",
            "series_index",
            "series_label",
            "exposure_label",
            "uncharged",
            "exposure_source",
            "exposure_s",
            "residual_content_source",
        ],
    )
    return _attrs(
        frame,
        provenance,
        header_rows=rows[:2],
        declared_units=dict(exposure=exposure_unit, content=content_unit),
        ppm_basis=ppm_basis,
        summary_meaning="source_integrated_content_not_independent_rate_measurement",
        ordering="original_conditions_not_a_specimen_history",
    )


def _require_export_digest(frame, expected: str) -> None:
    provenance = frame.attrs.get("export_provenance")
    if not isinstance(provenance, dict) or provenance.get("csv_sha256") != expected:
        raise ValueError("signal calibration must match the loaded export content digest")


def permeation_flux_observations(frame, calibration: HydrogenPermeationSignalCalibration):
    """Convert a reviewed electrochemical current signal without filtering or clipping signs."""
    import numpy as np
    import pandas as pd

    if not isinstance(calibration, HydrogenPermeationSignalCalibration):
        raise TypeError("a validated HydrogenPermeationSignalCalibration is required")
    _require_export_digest(frame, calibration.export_csv_sha256)
    if not calibration.physical_mapping_reviewed:
        raise ValueError("permeation area, clock, sign and electrochemical mapping require review")
    expected_background = (
        "source_processed_channel"
        if calibration.selected_current_channel == "processed_current_A"
        else "none_raw_channel"
    )
    if calibration.background_handling != expected_background:
        raise ValueError("selected current channel conflicts with the declared background handling")
    declared = frame.attrs.get("declared_units", {})
    if declared.get("current") == "unresolved" or declared.get("clock") == "unresolved":
        raise ValueError("resolved current and clock units are required for permeation flux")
    required = {"source_row", calibration.selected_current_channel, calibration.selected_clock_channel}
    if not required.issubset(frame.columns):
        raise ValueError("loaded permeation export lacks a selected signal column")
    current = frame[calibration.selected_current_channel].to_numpy(dtype=float)
    clock = frame[calibration.selected_clock_channel].to_numpy(dtype=float)
    if not np.all(np.isfinite(current)) or not np.all(np.isfinite(clock)):
        raise ValueError("selected permeation current and clock must be complete finite observations")
    elapsed = clock - calibration.clock_origin_s
    if np.any(elapsed < 0) or np.any(np.diff(elapsed) <= 0):
        raise ValueError("model-ready permeation elapsed time must be nonnegative and strictly increasing")
    flux = (
        calibration.current_sign_for_outward_hydrogen
        * calibration.current_efficiency
        * current
        / (
            FARADAY_C_MOL_ELECTRONS
            * calibration.electron_mol_per_hydrogen_atom_mol
            * calibration.membrane_area_m2
        )
    )
    cumulative = np.zeros(len(flux), dtype=float)
    if len(flux) > 1:
        cumulative[1:] = np.cumsum(0.5 * (flux[:-1] + flux[1:]) * np.diff(elapsed))
    result = pd.DataFrame(
        {
            "source_row": frame.source_row.to_numpy(copy=True),
            "elapsed_time_s": elapsed,
            "selected_current_A": current,
            "outward_hydrogen_flux_mol_m2_s": flux,
            "cumulative_outward_hydrogen_mol_m2": cumulative,
        }
    )
    result.attrs.update(
        signal_calibration=calibration.model_dump(mode="json"),
        signal_calibration_digest=canonical_digest(calibration.model_dump(mode="json")),
        export_provenance=frame.attrs["export_provenance"],
        sign_policy="signed_signal_preserved_without_clipping",
        flux_meaning="electrochemical_equivalent_outward_hydrogen_atom_flux",
        boundary_concentration_inference="not_performed",
        calibration_scope="signal_conversion_not_transport_parameter_fit",
    )
    return result


def tds_molar_observations(frame, calibration: HydrogenTdsSignalCalibration):
    """Convert one reviewed mass-ppm TDS series while retaining temperature order and signs."""
    import numpy as np
    import pandas as pd

    if not isinstance(calibration, HydrogenTdsSignalCalibration):
        raise TypeError("a validated HydrogenTdsSignalCalibration is required")
    _require_export_digest(frame, calibration.export_csv_sha256)
    if not (calibration.detector_response_reviewed and calibration.ppm_basis_reviewed):
        raise ValueError("TDS detector response and ppm mass basis require review")
    declared = frame.attrs.get("declared_units", {})
    if declared != {"temperature": "degC", "rate": "ppm/s", "integral": "ppm"} and declared != {
        "temperature": "K",
        "rate": "ppm/s",
        "integral": "ppm",
    }:
        raise ValueError("resolved TDS temperature, ppm/s rate and ppm integral units are required")
    selected = frame.loc[frame.series_index.eq(calibration.series_index)].copy()
    if selected.empty or set(selected.series_label) != {calibration.series_label}:
        raise ValueError("TDS series index and label must identify exactly the reviewed source series")
    required = {"temperature_K", "rate_source", "integral_source", "source_row", "observation_index"}
    if not required.issubset(selected.columns):
        raise ValueError("loaded TDS export lacks a required observation column")
    numeric = selected[["temperature_K", "rate_source", "integral_source"]].to_numpy(dtype=float)
    if not np.all(np.isfinite(numeric)):
        raise ValueError("selected TDS observations must have resolved finite temperature and signals")
    mass_fraction_to_moles_per_kg = 1e-6 / calibration.hydrogen_atomic_molar_mass_kg_mol
    result = pd.DataFrame(
        {
            "source_row": selected.source_row.to_numpy(copy=True),
            "observation_index": selected.observation_index.to_numpy(copy=True),
            "temperature_K": selected.temperature_K.to_numpy(copy=True),
            "desorption_rate_hydrogen_atoms_mol_kg_sample_s": (
                selected.rate_source.to_numpy() * mass_fraction_to_moles_per_kg
            ),
            "source_integrated_hydrogen_atoms_mol_kg_sample": (
                selected.integral_source.to_numpy() * mass_fraction_to_moles_per_kg
            ),
        }
    )
    if calibration.sample_mass_kg is not None:
        result["desorption_rate_hydrogen_atoms_mol_s"] = (
            result.desorption_rate_hydrogen_atoms_mol_kg_sample_s * calibration.sample_mass_kg
        )
        result["source_integrated_hydrogen_atoms_mol"] = (
            result.source_integrated_hydrogen_atoms_mol_kg_sample * calibration.sample_mass_kg
        )
    result.attrs.update(
        signal_calibration=calibration.model_dump(mode="json"),
        signal_calibration_digest=canonical_digest(calibration.model_dump(mode="json")),
        export_provenance=frame.attrs["export_provenance"],
        sign_policy="signed_signal_preserved_without_clipping",
        sample_clock="not_available_in_export",
        temperature_order="source_order_preserved_without_sorting",
        source_integral_meaning="source_derived_not_an_independent_observation",
        total_moles_available=calibration.sample_mass_kg is not None,
        kinetic_time_alignment_ready=False,
        calibration_scope="signal_conversion_not_trap_parameter_fit",
    )
    return result
