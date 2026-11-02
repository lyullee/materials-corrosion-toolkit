"""Neutral contracts for independently versioned process and risk projects."""

from __future__ import annotations

import hashlib
import json
import math
import re
import csv
import io
from pathlib import Path
from typing import Any, Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import (
    AssessmentResult,
    Contract,
    EventProbability,
    Evidence,
    Fraction,
    Nonnegative,
    Positive,
    ProbabilityMeaning,
    RunContext,
    canonical_digest,
)
from .consequence_exchange import IntegrityEventBasis
from .models.inspection import RiskCostComponent
from .units import SECONDS_PER_YEAR


def seccm_chronoamperometry_summary_inputs(
    trace: dict[str, Any],
    *,
    analysis_window_s: list[float],
    baseline_window_s: list[float] | None = None,
    boundary_policy: Literal["exact_samples", "piecewise_linear"] = "piecewise_linear",
    current_sign_basis: str,
    current_sign_reviewed: bool,
) -> dict[str, Any]:
    """Compose a pinned raw SECCM reader result into the generic registered summary contract."""
    from .seccm_data import SeccmChronoamperometryTrace

    if not isinstance(trace, dict) or set(trace) != {"metadata", "time_s", "substrate_current_A"}:
        raise ValueError("SECCM adapter requires the exact raw trace reader result")
    metadata = SeccmChronoamperometryTrace.model_validate(trace["metadata"])
    time_s = np.asarray(trace["time_s"], dtype=float)
    current_A = np.asarray(trace["substrate_current_A"], dtype=float)
    if time_s.ndim != 1 or current_A.ndim != 1 or len(time_s) != len(current_A):
        raise ValueError("SECCM trace arrays must be aligned one-dimensional vectors")
    if len(time_s) != metadata.sample_count:
        raise ValueError("SECCM trace sample count differs from its metadata")
    if metadata.time_unit != "s" or metadata.current_unit != "A":
        raise ValueError("SECCM adapter supports only the reviewed seconds and amperes contract")
    if metadata.interpretation_status != "raw_signal_only":
        raise ValueError("SECCM adapter accepts only raw-signal reader records")
    digest = hashlib.sha256()
    digest.update(b"matintegrity.seccm_trace_arrays.v1\0")
    for name, values in ((b"time_s\0", time_s), (b"substrate_current_A\0", current_A)):
        canonical = np.ascontiguousarray(values, dtype="<f8")
        digest.update(name)
        digest.update(len(canonical).to_bytes(8, "big"))
        digest.update(canonical.tobytes())
    return {
        "trace_id": f"{metadata.dataset_id}:map-{metadata.map_id}",
        "physical_specimen_id": metadata.physical_specimen_id,
        "source_group_id": metadata.source_group_id,
        "source_trace_sha256": digest.hexdigest(),
        "source_archive_sha256": metadata.source_archive_sha256,
        "source_member_sha256": metadata.source_member_sha256,
        "time_s": time_s.tolist(),
        "current_A": current_A.tolist(),
        "analysis_window_s": analysis_window_s,
        "baseline_window_s": baseline_window_s,
        "boundary_policy": boundary_policy,
        "sample_order_reviewed": True,
        "time_unit_reviewed_as_seconds": True,
        "current_unit_reviewed_as_amperes": True,
        "current_sign_basis": current_sign_basis,
        "current_sign_reviewed": current_sign_reviewed,
    }


def under_insulation_inputs_from_condensation_result(
    result: AssessmentResult,
    *,
    record_id: str,
    insulation_condition_id_by_interval: dict[str, str],
    exposure_definition,
    condensation_potential_state_id: str = "thermodynamic_condensation_possible",
    no_condensation_potential_state_id: str = "no_thermodynamic_condensation_indicated",
) -> dict[str, Any]:
    """Compose a complete condensation screen into the CUI exposure-accounting contract."""
    from .contracts import Evidence
    from .models.under_insulation import (
        DeclaredUnderInsulationExposure,
        InsulationExposureInterval,
    )

    if not isinstance(result, AssessmentResult):
        raise TypeError("condensation adapter requires an AssessmentResult")
    if result.model_id != "fabrication.insulation_condensation_exposure":
        raise ValueError("condensation adapter requires the registered condensation model result")
    if result.status != "computed":
        raise ValueError("only a complete computed condensation result can be adapted")
    if not record_id or not condensation_potential_state_id or not no_condensation_potential_state_id:
        raise ValueError("record and wetness-state identifiers are required")
    if condensation_potential_state_id == no_condensation_potential_state_id:
        raise ValueError("potential and nonpotential wetness-state identifiers must differ")
    if not isinstance(exposure_definition, DeclaredUnderInsulationExposure):
        raise TypeError("exposure_definition must be a strict DeclaredUnderInsulationExposure")

    source_rows = result.inputs["intervals"]
    source_ids = [row["interval_id"] for row in source_rows]
    if set(insulation_condition_id_by_interval) != set(source_ids):
        raise ValueError("insulation-condition mapping must cover exactly the condensation intervals")
    if any(not value for value in insulation_condition_id_by_interval.values()):
        raise ValueError("insulation-condition identifiers cannot be blank")

    possible = set(result.values["conservative_condensation_possible_interval_ids"])
    if not possible.issubset(source_ids):
        raise ValueError("condensation result refers to an unknown source interval")
    intervals = []
    for row in source_rows:
        wetness = (
            condensation_potential_state_id
            if row["interval_id"] in possible
            else no_condensation_potential_state_id
        )
        intervals.append(
            InsulationExposureInterval(
                interval_id=row["interval_id"],
                start_time_s=row["start_time_s"],
                end_time_s=row["end_time_s"],
                record_valid=True,
                surface_temperature_K=row["outer_surface_temperature_K"],
                wetness_state_id=wetness,
                insulation_condition_id=insulation_condition_id_by_interval[row["interval_id"]],
                evidence=tuple(Evidence.model_validate(item) for item in row["evidence"]),
            )
        )
    return {
        "record_id": record_id,
        "source_model_id": result.model_id,
        "source_result_digest": canonical_digest(result.model_dump(mode="json")),
        "wetness_state_semantics": (
            "one-sided thermodynamic condensation potential from reviewed surface temperature and dew point; "
            "not measured insulation wetness or water ingress"
        ),
        "asset_id": result.context.asset_id,
        "location_id": result.context.location_id,
        "clock_id": result.inputs["clock_id"],
        "horizon_start_s": result.inputs["horizon_start_s"],
        "horizon_end_s": result.inputs["horizon_end_s"],
        "intervals": tuple(intervals),
        "exposure_definition": exposure_definition,
        "clock_and_coverage_reviewed": True,
        "temperature_measurement_reviewed": True,
        "wetness_state_mapping_reviewed": True,
        "insulation_condition_mapping_reviewed": True,
        "exposure_definition_reviewed": True,
    }


def guided_wave_pair_feature_inputs(
    baseline: dict[str, Any],
    observation: dict[str, Any],
    *,
    frequency_Hz: float,
    wave_mode: Literal["torsional", "flexural"],
    window_start_m: float,
    window_end_m: float,
    distance_match_tolerance_m: float = 0.0,
    duplicate_distance_policy: Literal[
        "preserve_samples", "mean_aligned_duplicates", "reject"
    ] = "preserve_samples",
) -> dict[str, Any]:
    """Compose one reader pair into the registered descriptive feature contract."""
    if wave_mode not in {"torsional", "flexural"}:
        raise ValueError("guided-wave mode must be torsional or flexural")
    for name, value in (("baseline", baseline), ("observation", observation)):
        if not isinstance(value, dict) or value.get("dataset_id") != "guided-wave-pipeline-shm":
            raise ValueError(f"{name} must be a guided-wave pipeline reader result")
    if baseline["specimen_id"] != observation["specimen_id"]:
        raise ValueError("guided-wave baseline and observation must refer to the same physical specimen")
    if baseline["outer_archive_sha256"] != observation["outer_archive_sha256"]:
        raise ValueError("guided-wave baseline and observation archives differ")
    if baseline["acquisition_id"] == observation["acquisition_id"]:
        raise ValueError("guided-wave baseline and observation acquisitions must differ")

    def select(record):
        matches = [signal for signal in record["signals"] if signal["frequency_Hz"] == frequency_Hz]
        if len(matches) != 1:
            raise ValueError("exactly one requested guided-wave frequency is required")
        return matches[0]

    baseline_signal = select(baseline)
    observation_signal = select(observation)
    channel = {"torsional": "torsional_V", "flexural": "flexural_V"}[wave_mode]
    return {
        "specimen_id": baseline["specimen_id"],
        "baseline_acquisition_id": str(baseline["acquisition_id"]),
        "observation_acquisition_id": str(observation["acquisition_id"]),
        "frequency_Hz": frequency_Hz,
        "wave_mode": wave_mode,
        "baseline_distance_m": baseline_signal["distance_m"].tolist(),
        "baseline_voltage_V": baseline_signal[channel].tolist(),
        "observation_distance_m": observation_signal["distance_m"].tolist(),
        "observation_voltage_V": observation_signal[channel].tolist(),
        "window_start_m": window_start_m,
        "window_end_m": window_end_m,
        "distance_match_tolerance_m": distance_match_tolerance_m,
        "duplicate_distance_policy": duplicate_distance_policy,
    }


def guided_wave_reference_ensemble_inputs(
    baselines: list[dict[str, Any]],
    observation: dict[str, Any],
    *,
    baseline_source_group_id: str,
    observation_source_group_id: str,
    baseline_selection_basis: str,
    frequency_Hz: float,
    wave_mode: Literal["torsional", "flexural"],
    window_start_m: float,
    window_end_m: float,
    reference_statistic: Literal["mean", "median"] = "median",
    distance_match_tolerance_m: float = 0.0,
    duplicate_distance_policy: Literal[
        "preserve_samples", "mean_aligned_duplicates", "reject"
    ] = "preserve_samples",
) -> dict[str, Any]:
    """Compose reader records into the guided-wave reference-ensemble contract."""
    if len(baselines) < 3:
        raise ValueError("at least three guided-wave baseline acquisitions are required")
    if wave_mode not in {"torsional", "flexural"}:
        raise ValueError("guided-wave mode must be torsional or flexural")
    records = [*baselines, observation]
    for index, record in enumerate(records):
        if not isinstance(record, dict) or record.get("dataset_id") != "guided-wave-pipeline-shm":
            raise ValueError(f"guided-wave ensemble record {index} is not a reader result")
    if len({record["specimen_id"] for record in records}) != 1:
        raise ValueError("guided-wave ensemble records must refer to one physical specimen")
    if len({record["outer_archive_sha256"] for record in records}) != 1:
        raise ValueError("guided-wave ensemble records must refer to one archive")
    baseline_ids = [record["acquisition_id"] for record in baselines]
    if len(set(baseline_ids)) != len(baseline_ids):
        raise ValueError("guided-wave ensemble baseline acquisitions must be unique")
    if observation["acquisition_id"] in baseline_ids:
        raise ValueError("guided-wave ensemble observation cannot be a baseline acquisition")

    def select(record):
        matches = [signal for signal in record["signals"] if signal["frequency_Hz"] == frequency_Hz]
        if len(matches) != 1:
            raise ValueError("exactly one requested guided-wave ensemble frequency is required")
        return matches[0]

    baseline_signals = [select(record) for record in baselines]
    observation_signal = select(observation)
    channel = {"torsional": "torsional_V", "flexural": "flexural_V"}[wave_mode]
    return {
        "specimen_id": baselines[0]["specimen_id"],
        "baseline_acquisition_ids": [str(value) for value in baseline_ids],
        "observation_acquisition_id": str(observation["acquisition_id"]),
        "baseline_source_group_id": baseline_source_group_id,
        "observation_source_group_id": observation_source_group_id,
        "baseline_selection_basis": baseline_selection_basis,
        "frequency_Hz": frequency_Hz,
        "wave_mode": wave_mode,
        "distance_m": baseline_signals[0]["distance_m"].tolist(),
        "baseline_voltage_V": [signal[channel].tolist() for signal in baseline_signals],
        "observation_distance_m": observation_signal["distance_m"].tolist(),
        "observation_voltage_V": observation_signal[channel].tolist(),
        "window_start_m": window_start_m,
        "window_end_m": window_end_m,
        "distance_match_tolerance_m": distance_match_tolerance_m,
        "duplicate_distance_policy": duplicate_distance_policy,
        "reference_statistic": reference_statistic,
    }


def hydrogen_observation_inputs_from_transport_result(
    result: AssessmentResult,
    *,
    observation_id: str,
    specimen_id: str,
    surface_role: Literal["left", "right", "curved_surface", "lower_end", "upper_end"],
    detector_calibration_id: str,
    detector_kind: Literal["electrochemical_current", "mass_normalized_tds"],
    evidence: tuple,
    source_surface_mapping_reviewed: bool,
    detector_response_mapping_reviewed: bool,
    planar_surface_area_m2: float | None = None,
    planar_surface_area_basis: str | None = None,
    current_sign_for_outward_hydrogen: Literal[-1, 1] | None = None,
    electron_mol_per_hydrogen_atom_mol: float | None = None,
    current_efficiency: float | None = None,
    background_current_A: float | None = None,
    sample_mass_kg: float | None = None,
    hydrogen_atomic_molar_mass_kg_mol: float | None = None,
) -> dict[str, Any]:
    """Adapt a computed slab/cylinder surface flow to the detector-observation contract."""
    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if result.status != "computed":
        raise ValueError("a noncomputed transport result cannot supply an observation history")
    if result.model_id == "transport.hydrogen_slab_kinetic":
        if surface_role not in {"left", "right"}:
            raise ValueError("planar transport only has left and right surface roles")
        if planar_surface_area_m2 is None or planar_surface_area_m2 <= 0:
            raise ValueError("planar flux needs a positive reviewed physical surface area")
        if not planar_surface_area_basis:
            raise ValueError("planar surface-area basis is required")
        inward = result.values[f"{surface_role}_inward_flux_mol_m2_s"]
        outward = [-value * planar_surface_area_m2 for value in inward]
        surface_id = result.inputs[f"{surface_role}_boundary"]["boundary_id"]
        source_flow_basis = (
            f"negative {surface_role} inward flux multiplied by planar area "
            f"{planar_surface_area_m2!r} m2; {planar_surface_area_basis}"
        )
    elif result.model_id == "transport.hydrogen_finite_cylinder_kinetic":
        if surface_role not in {"curved_surface", "lower_end", "upper_end"}:
            raise ValueError("finite-cylinder transport requires a curved or end surface role")
        if planar_surface_area_m2 is not None or planar_surface_area_basis is not None:
            raise ValueError("finite-cylinder results already contain integrated surface flow")
        inward = result.values["inward_surface_flow_mol_s"][surface_role]
        outward = [-value for value in inward]
        boundary_key = {
            "curved_surface": "curved_surface_boundary",
            "lower_end": "lower_end_boundary",
            "upper_end": "upper_end_boundary",
        }[surface_role]
        surface_id = result.inputs[boundary_key]["boundary_id"]
        source_flow_basis = "negative solver-integrated inward flow on the named finite-cylinder surface"
    else:
        raise ValueError("only hydrogen slab or finite-cylinder transport results are supported")
    from .models.hydrogen_observation import HydrogenDetectorObservation

    contract = HydrogenDetectorObservation(
        observation_id=observation_id,
        material_condition_id=result.inputs["material_condition_id"],
        specimen_id=specimen_id,
        elapsed_time_origin_id=result.values["elapsed_time_origin_id"],
        source_model_id=result.model_id,
        source_model_result_digest=canonical_digest(result.model_dump(mode="json")),
        source_surface_id=surface_id,
        source_flow_basis=source_flow_basis,
        detector_calibration_id=detector_calibration_id,
        detector_kind=detector_kind,
        elapsed_time_s=result.values["elapsed_time_s"],
        outward_hydrogen_atoms_mol_s=outward,
        current_sign_for_outward_hydrogen=current_sign_for_outward_hydrogen,
        electron_mol_per_hydrogen_atom_mol=electron_mol_per_hydrogen_atom_mol,
        current_efficiency=current_efficiency,
        background_current_A=background_current_A,
        sample_mass_kg=sample_mass_kg,
        hydrogen_atomic_molar_mass_kg_mol=hydrogen_atomic_molar_mass_kg_mol,
        source_surface_mapping_reviewed=source_surface_mapping_reviewed,
        detector_response_mapping_reviewed=detector_response_mapping_reviewed,
        evidence=evidence,
    )
    return contract.model_dump(mode="json")


class OperatingHistory(Contract):
    schema_version: Literal["matintegrity.operating_history.v1"] = "matintegrity.operating_history.v1"
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    origin: Literal["measured", "model_prediction"]
    time_s: list[Nonnegative] = Field(min_length=2)
    pressure_absolute_Pa: list[Positive]
    temperature_K: list[Positive]
    valid: list[bool]
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def align(self):
        vectors = (self.time_s, self.pressure_absolute_Pa, self.temperature_K, self.valid)
        if len({len(vector) for vector in vectors}) != 1:
            raise ValueError("operating histories must share a clock and vector length")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("strictly increasing operating-history time required")
        return self


class Co2MixtureFugacityHistory(Contract):
    """Aligned transient gas states for per-sample CO2-mixture fugacity evaluation."""

    schema_version: Literal["matintegrity.co2_mixture_fugacity_history.v1"] = (
        "matintegrity.co2_mixture_fugacity_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    stream_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    origin: Literal["measured", "model_prediction"]
    sample_ids: tuple[str, ...] = Field(min_length=2)
    time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    total_pressure_Pa: tuple[Positive | None, ...] = Field(min_length=2)
    temperature_K: tuple[Positive | None, ...] = Field(min_length=2)
    components: tuple[str, ...] = Field(min_length=2)
    mole_fractions_by_sample: tuple[tuple[float | None, ...], ...] = Field(min_length=2)
    sample_valid: tuple[bool, ...] = Field(min_length=2)
    composition_sum_absolute_tolerance: Positive = Field(default=1e-10, le=1e-6)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    case_id: str = Field(min_length=1)
    case_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    solver_revision: str = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_mixture_history(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count or any(not value.strip() for value in self.sample_ids):
            raise ValueError("mixture-history sample IDs must be unique and nonblank")
        aligned = (self.time_s, self.total_pressure_Pa, self.temperature_K, self.mole_fractions_by_sample, self.sample_valid)
        if any(len(values) != count for values in aligned):
            raise ValueError("mixture-history samples, states, composition and validity mask must align")
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("mixture-history time must increase strictly")
        normalized_names = tuple(value.casefold() for value in self.components)
        if any(not value.strip() for value in self.components) or len(set(normalized_names)) != len(self.components):
            raise ValueError("mixture component names must be nonblank and unique ignoring case")
        co2_indices = [i for i, value in enumerate(normalized_names) if value in {"co2", "carbondioxide"}]
        if len(co2_indices) != 1:
            raise ValueError("mixture history must declare exactly one CO2 component")
        for index, (valid, row) in enumerate(zip(self.sample_valid, self.mole_fractions_by_sample, strict=True)):
            if len(row) != len(self.components):
                raise ValueError("each mixture-history composition row must match the declared component order")
            if valid and (
                self.total_pressure_Pa[index] is None
                or self.temperature_K[index] is None
                or any(value is None for value in row)
            ):
                raise ValueError("valid mixture-history rows require pressure, temperature and every component fraction")
            present = [value for value in row if value is not None]
            if any(not math.isfinite(value) or value < 0.0 or value > 1.0 for value in present):
                raise ValueError("mixture mole fractions must be finite and between zero and one")
            if valid and abs(math.fsum(value for value in row if value is not None) - 1.0) > self.composition_sum_absolute_tolerance:
                raise ValueError("valid mixture-history composition rows must sum to one within tolerance")
            co2_fraction = row[co2_indices[0]]
            if valid and (co2_fraction is None or co2_fraction <= 0.0):
                raise ValueError("valid mixture-history rows require a positive CO2 mole fraction")
        return self


def read_co2_mixture_history_csv(
    content: bytes,
    *,
    history_id: str,
    asset_id: str,
    location_id: str,
    stream_id: str,
    clock_id: str,
    origin: Literal["measured", "model_prediction"],
    case_id: str,
    case_input_digest: str,
    solver_revision: str,
    sample_id_column: str,
    time_seconds_column: str,
    absolute_pressure_pa_column: str,
    temperature_kelvin_column: str,
    validity_column: str,
    component_columns: dict[str, str],
    composition_sum_absolute_tolerance: float = 1e-10,
) -> Co2MixtureFugacityHistory:
    """Read caller-mapped UTF-8 CSV bytes into a provenance-pinned CO2 history.

    Column units are explicit in the argument names: time is seconds, pressure is
    absolute pascals, temperature is kelvin, and component values are mole fractions.
    The reader does not infer units, normalize compositions, or repair malformed rows.
    """
    if not isinstance(content, bytes) or not content:
        raise ValueError("CSV content must be non-empty bytes")
    try:
        text = content.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV input must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ValueError("CSV must have a header with unique column names")
    if not component_columns or any(not name.strip() or not column.strip() for name, column in component_columns.items()):
        raise ValueError("component-to-column mapping must be non-empty and contain nonblank names")
    required_columns = [sample_id_column, time_seconds_column, absolute_pressure_pa_column,
                        temperature_kelvin_column, validity_column, *component_columns.values()]
    if any(not column for column in required_columns) or len(set(required_columns)) != len(required_columns):
        raise ValueError("mapped CSV columns must be nonblank and uniquely assigned")
    missing = sorted(set(required_columns) - set(reader.fieldnames))
    if missing:
        raise ValueError(f"CSV is missing mapped columns: {missing}")

    def number(value: str | None, field: str, *, nullable: bool) -> float | None:
        if value is None or not value.strip():
            if nullable:
                return None
            raise ValueError(f"CSV field {field!r} is required")
        try:
            result = float(value)
        except ValueError as exc:
            raise ValueError(f"CSV field {field!r} must be numeric") from exc
        if not math.isfinite(result):
            raise ValueError(f"CSV field {field!r} must be finite")
        return result

    sample_ids: list[str] = []
    times: list[float] = []
    pressures: list[float | None] = []
    temperatures: list[float | None] = []
    fractions: list[tuple[float | None, ...]] = []
    valid_rows: list[bool] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError(f"CSV row {row_number} contains more fields than the header")
        sample_id = (row.get(sample_id_column) or "").strip()
        if not sample_id:
            raise ValueError(f"CSV row {row_number} has a blank sample ID")
        validity = (row.get(validity_column) or "").strip().casefold()
        if validity not in {"true", "false", "1", "0"}:
            raise ValueError(f"CSV row {row_number} validity must be true/false or 1/0")
        valid = validity in {"true", "1"}
        sample_ids.append(sample_id)
        times.append(number(row.get(time_seconds_column), time_seconds_column, nullable=False))
        pressures.append(number(row.get(absolute_pressure_pa_column), absolute_pressure_pa_column, nullable=not valid))
        temperatures.append(number(row.get(temperature_kelvin_column), temperature_kelvin_column, nullable=not valid))
        fractions.append(tuple(number(row.get(column), column, nullable=not valid) for column in component_columns.values()))
        valid_rows.append(valid)
    source_digest = hashlib.sha256(content).hexdigest()
    return Co2MixtureFugacityHistory(
        history_id=history_id, asset_id=asset_id, location_id=location_id, stream_id=stream_id,
        clock_id=clock_id, origin=origin, case_id=case_id, case_input_digest=case_input_digest,
        solver_revision=solver_revision, source_digest=source_digest, sample_ids=tuple(sample_ids),
        time_s=tuple(times), total_pressure_Pa=tuple(pressures), temperature_K=tuple(temperatures),
        components=tuple(component_columns), mole_fractions_by_sample=tuple(fractions),
        sample_valid=tuple(valid_rows), composition_sum_absolute_tolerance=composition_sum_absolute_tolerance,
    )


def load_co2_mixture_history_csv(
    path: str | Path,
    *,
    history_id: str,
    asset_id: str,
    location_id: str,
    stream_id: str,
    clock_id: str,
    origin: Literal["measured", "model_prediction"],
    case_id: str,
    case_input_digest: str,
    solver_revision: str,
    sample_id_column: str,
    time_seconds_column: str,
    absolute_pressure_pa_column: str,
    temperature_kelvin_column: str,
    validity_column: str,
    component_columns: dict[str, str],
    composition_sum_absolute_tolerance: float = 1e-10,
) -> Co2MixtureFugacityHistory:
    """Load a caller-owned CSV file and retain the digest of its exact bytes."""
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    return read_co2_mixture_history_csv(
        source_path.read_bytes(), history_id=history_id, asset_id=asset_id,
        location_id=location_id, stream_id=stream_id, clock_id=clock_id, origin=origin,
        case_id=case_id, case_input_digest=case_input_digest, solver_revision=solver_revision,
        sample_id_column=sample_id_column, time_seconds_column=time_seconds_column,
        absolute_pressure_pa_column=absolute_pressure_pa_column,
        temperature_kelvin_column=temperature_kelvin_column, validity_column=validity_column,
        component_columns=component_columns,
        composition_sum_absolute_tolerance=composition_sum_absolute_tolerance,
    )


class PSADynaMeanStreamFugacityRow(Contract):
    """One selected cycle-mean PSA stream and its optional CoolProp request."""

    stream_id: str = Field(min_length=1)
    status: Literal["ready", "needs_data", "out_of_scope"]
    state_basis: str | None
    total_pressure_Pa: Positive | None
    temperature_K: Positive | None
    components: tuple[str, ...]
    mole_fractions: tuple[float, ...] | None
    reason: str | None
    request: dict[str, Any] | None


class PSADynaMeanStreamFugacityBatch(Contract):
    """Lineage-preserving requests derived from a PSA-Dyna cycle-mean report."""

    schema_version: Literal["matintegrity.psa_dyna_mean_stream_fugacity_batch.v1"] = (
        "matintegrity.psa_dyna_mean_stream_fugacity_batch.v1"
    )
    source_schema: Literal["dynamic-psa-mean-stream/v1"] = "dynamic-psa-mean-stream/v1"
    payload_schema: Literal["dynamic-psa-dwsim-mean-stream-input/v1"] = (
        "dynamic-psa-dwsim-mean-stream-input/v1"
    )
    case_id: str = Field(min_length=1)
    upstream_payload_status: str = Field(min_length=1)
    upstream_release_flags: dict[str, Any]
    case_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_code_zip_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    upstream_report_file_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    upstream_report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    mean_stream_payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    components: tuple[str, ...] = Field(min_length=2)
    provider_backend: str = Field(min_length=1)
    stream_count: int = Field(ge=1)
    ready_count: int = Field(ge=0)
    needs_data_count: int = Field(ge=0)
    out_of_scope_count: int = Field(ge=0)
    cycle_mean_only: Literal[True] = True
    corrosion_boundary_qualification: Literal[False] = False
    stream_requests: tuple[PSADynaMeanStreamFugacityRow, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def stream_counts_match(self):
        if len(self.stream_requests) != self.stream_count:
            raise ValueError("PSA-Dyna stream row count must match stream_count")
        counts = {
            "ready": sum(row.status == "ready" for row in self.stream_requests),
            "needs_data": sum(row.status == "needs_data" for row in self.stream_requests),
            "out_of_scope": sum(row.status == "out_of_scope" for row in self.stream_requests),
        }
        if counts != {
            "ready": self.ready_count,
            "needs_data": self.needs_data_count,
            "out_of_scope": self.out_of_scope_count,
        }:
            raise ValueError("PSA-Dyna stream status counts do not match row results")
        return self


def _co2_mixture_fugacity_requests_from_psa_dyna_mean_stream_report(
    report: dict[str, Any],
    *,
    upstream_report_file_sha256: str | None,
    stream_ids: tuple[str, ...],
    backend: str,
    composition_review_id: str,
    absolute_pressure_basis_reviewed: bool,
    composition_reviewed: bool,
    mixture_eos_applicability_reviewed: bool,
    single_phase_gas_or_supercritical_reviewed: bool,
    evidence: tuple[Evidence, ...],
) -> PSADynaMeanStreamFugacityBatch:
    """Create CoolProp requests from selected PSA-Dyna mean streams, never transient histories.

    The absolute-pressure basis, CO2 mixture, EOS applicability and gas-phase
    assumptions are caller-reviewed. The stream-to-metal exposure relation is
    intentionally not included; this adapter does not qualify a corrosion boundary.
    """
    from .models.co2_fugacity import CoolPropCo2MixtureFugacityRequest

    if not isinstance(report, dict) or report.get("schema") != "dynamic-psa-mean-stream/v1":
        raise ValueError("expected a complete PSA-Dyna dynamic-psa-mean-stream/v1 report")
    if upstream_report_file_sha256 is not None:
        upstream_report_file_sha256 = upstream_report_file_sha256.lower()
        if not re.fullmatch(r"[a-f0-9]{64}", upstream_report_file_sha256):
            raise ValueError("upstream report file digest must be a SHA-256 value")
    payload = report.get("dwsim_input_payload")
    if not isinstance(payload, dict) or payload.get("schema") != "dynamic-psa-dwsim-mean-stream-input/v1":
        raise ValueError("PSA-Dyna report is missing the supported mean-stream payload")
    if not stream_ids or len(set(stream_ids)) != len(stream_ids) or any(not item.strip() for item in stream_ids):
        raise ValueError("select one or more unique nonblank stream IDs explicitly")
    if not backend.strip() or not composition_review_id.strip() or not evidence:
        raise ValueError("backend, review ID and at least one Evidence record are required")
    components_raw = payload.get("components")
    streams = payload.get("streams")
    units = payload.get("units")
    if not isinstance(components_raw, list) or any(not isinstance(x, str) for x in components_raw):
        raise ValueError("PSA-Dyna mean-stream component order is missing or malformed")
    components = tuple(components_raw)
    if len(components) < 2 or len({x.casefold() for x in components}) != len(components) or any(not x.strip() for x in components):
        raise ValueError("PSA-Dyna mean-stream component names must be unique and nonblank")
    if not isinstance(streams, dict) or not isinstance(units, dict):
        raise ValueError("PSA-Dyna stream states and unit declarations are required")
    payload_status = payload.get("status")
    release_flags = payload.get("release_flags")
    if not isinstance(payload_status, str) or not payload_status.strip() or not isinstance(release_flags, dict):
        raise ValueError("PSA-Dyna mean-stream status and release flags must be retained")
    if units.get("pressure") != "bar" or units.get("temperature") != "K" or units.get("mole_fraction") != "1":
        raise ValueError("PSA-Dyna pressure, temperature and composition units must be bar, K and dimensionless")
    case = report.get("case")
    result = report.get("result")
    if not isinstance(case, dict) or not isinstance(result, dict):
        raise ValueError("PSA-Dyna case and result provenance are required")
    case_digest = case.get("sha256")
    result_digest = result.get("sha256")
    if not isinstance(case_digest, str) or not isinstance(result_digest, str):
        raise ValueError("PSA-Dyna case and result SHA-256 digests are required")
    case_digest, result_digest = case_digest.lower(), result_digest.lower()
    if not re.fullmatch(r"[a-f0-9]{64}", case_digest) or not re.fullmatch(r"[a-f0-9]{64}", result_digest):
        raise ValueError("PSA-Dyna case and result digests must be lowercase or uppercase SHA-256 values")
    source_observations = report.get("upstream_gate_observations")
    source_zip_digest = source_observations.get("source_code_zip_sha256") if isinstance(source_observations, dict) else None
    if source_zip_digest is not None:
        source_zip_digest = str(source_zip_digest).lower()
        if not re.fullmatch(r"[a-f0-9]{64}", source_zip_digest):
            raise ValueError("PSA-Dyna source-code archive digest must be a SHA-256 value")
    report_digest = canonical_digest(report)
    payload_digest = canonical_digest(payload)
    rows = []
    for stream_id in stream_ids:
        stream = streams.get(stream_id)
        if not isinstance(stream, dict):
            rows.append(PSADynaMeanStreamFugacityRow(
                stream_id=stream_id, status="needs_data", state_basis=None,
                total_pressure_Pa=None, temperature_K=None, components=components,
                mole_fractions=None, reason="selected_mean_stream_not_present", request=None,
            ))
            continue
        state_basis = stream.get("state_basis")
        pressure_bar = stream.get("pressure_bar")
        temperature = stream.get("temperature_k")
        fractions_raw = stream.get("mole_fractions")
        if pressure_bar is None or temperature is None or fractions_raw is None:
            rows.append(PSADynaMeanStreamFugacityRow(
                stream_id=stream_id, status="needs_data",
                state_basis=state_basis if isinstance(state_basis, str) else None,
                total_pressure_Pa=None, temperature_K=None, components=components,
                mole_fractions=None, reason="phase_aligned_mean_stream_PT_or_composition_unresolved", request=None,
            ))
            continue
        try:
            pressure_pa = float(pressure_bar) * 100_000.0
            temperature_k = float(temperature)
            fractions = tuple(float(value) for value in fractions_raw)
        except (TypeError, ValueError, OverflowError):
            rows.append(PSADynaMeanStreamFugacityRow(
                stream_id=stream_id, status="needs_data",
                state_basis=state_basis if isinstance(state_basis, str) else None,
                total_pressure_Pa=None, temperature_K=None, components=components,
                mole_fractions=None, reason="mean_stream_state_not_numeric", request=None,
            ))
            continue
        if (len(fractions) != len(components) or not math.isfinite(pressure_pa) or pressure_pa <= 0
                or not math.isfinite(temperature_k) or temperature_k <= 0
                or any(not math.isfinite(value) or value < 0 or value > 1 for value in fractions)
                or not math.isclose(math.fsum(fractions), 1.0, rel_tol=0.0, abs_tol=1e-10)):
            rows.append(PSADynaMeanStreamFugacityRow(
                stream_id=stream_id, status="out_of_scope",
                state_basis=state_basis if isinstance(state_basis, str) else None,
                total_pressure_Pa=None, temperature_K=None, components=components,
                mole_fractions=fractions, reason="mean_stream_PT_or_composition_violates_contract", request=None,
            ))
            continue
        co2_match = [i for i, name in enumerate(components) if name.casefold() in {"co2", "carbondioxide"}]
        if len(co2_match) != 1 or fractions[co2_match[0]] <= 0:
            rows.append(PSADynaMeanStreamFugacityRow(
                stream_id=stream_id, status="out_of_scope",
                state_basis=state_basis if isinstance(state_basis, str) else None,
                total_pressure_Pa=pressure_pa, temperature_K=temperature_k, components=components,
                mole_fractions=fractions, reason="stream_has_no_positive_CO2_component", request=None,
            ))
            continue
        if not absolute_pressure_basis_reviewed:
            rows.append(PSADynaMeanStreamFugacityRow(
                stream_id=stream_id, status="needs_data",
                state_basis=state_basis if isinstance(state_basis, str) else None,
                total_pressure_Pa=pressure_pa, temperature_K=temperature_k, components=components,
                mole_fractions=fractions, reason="absolute_pressure_basis_review_missing", request=None,
            ))
            continue
        request = CoolPropCo2MixtureFugacityRequest(
            assessment_id=f"{case.get('case_id', 'psa-dyna')}:{stream_id}:cycle-mean",
            total_pressure_Pa=pressure_pa,
            temperature_K=temperature_k,
            components=components,
            mole_fractions=fractions,
            backend=backend,
            mixture_composition_reviewed=composition_reviewed,
            mixture_eos_applicability_reviewed=mixture_eos_applicability_reviewed,
            single_phase_gas_or_supercritical_reviewed=single_phase_gas_or_supercritical_reviewed,
            review_id=f"{composition_review_id}:{stream_id}",
            evidence=evidence,
        )
        review_ready = all((composition_reviewed, mixture_eos_applicability_reviewed,
                            single_phase_gas_or_supercritical_reviewed))
        rows.append(PSADynaMeanStreamFugacityRow(
            stream_id=stream_id, status="ready" if review_ready else "needs_data",
            state_basis=state_basis if isinstance(state_basis, str) else None,
            total_pressure_Pa=pressure_pa, temperature_K=temperature_k, components=components,
            mole_fractions=fractions,
            reason=None if review_ready else "mixture_composition_EOS_or_phase_review_missing",
            request=request.model_dump(mode="json"),
        ))
    return PSADynaMeanStreamFugacityBatch(
        case_id=str(case.get("case_id") or "unknown-case"),
        upstream_payload_status=payload_status,
        upstream_release_flags=release_flags,
        case_input_sha256=case_digest,
        result_sha256=result_digest,
        source_code_zip_sha256=source_zip_digest,
        upstream_report_file_sha256=upstream_report_file_sha256,
        upstream_report_digest=report_digest,
        mean_stream_payload_digest=payload_digest,
        components=components,
        provider_backend=backend,
        stream_count=len(rows),
        ready_count=sum(row.status == "ready" for row in rows),
        needs_data_count=sum(row.status == "needs_data" for row in rows),
        out_of_scope_count=sum(row.status == "out_of_scope" for row in rows),
        stream_requests=tuple(rows),
    )


def co2_mixture_fugacity_requests_from_psa_dyna_mean_stream(
    report: dict[str, Any],
    *,
    stream_ids: tuple[str, ...],
    backend: str,
    composition_review_id: str,
    absolute_pressure_basis_reviewed: bool,
    composition_reviewed: bool,
    mixture_eos_applicability_reviewed: bool,
    single_phase_gas_or_supercritical_reviewed: bool,
    evidence: tuple[Evidence, ...],
) -> PSADynaMeanStreamFugacityBatch:
    """Build requests from an in-memory upstream report without claiming a file digest."""
    return _co2_mixture_fugacity_requests_from_psa_dyna_mean_stream_report(
        report,
        upstream_report_file_sha256=None,
        stream_ids=stream_ids,
        backend=backend,
        composition_review_id=composition_review_id,
        absolute_pressure_basis_reviewed=absolute_pressure_basis_reviewed,
        composition_reviewed=composition_reviewed,
        mixture_eos_applicability_reviewed=mixture_eos_applicability_reviewed,
        single_phase_gas_or_supercritical_reviewed=single_phase_gas_or_supercritical_reviewed,
        evidence=evidence,
    )


def load_co2_mixture_fugacity_requests_from_psa_dyna_mean_stream(
    path: str | Path,
    *,
    stream_ids: tuple[str, ...],
    backend: str,
    composition_review_id: str,
    absolute_pressure_basis_reviewed: bool,
    composition_reviewed: bool,
    mixture_eos_applicability_reviewed: bool,
    single_phase_gas_or_supercritical_reviewed: bool,
    evidence: tuple[Evidence, ...],
) -> PSADynaMeanStreamFugacityBatch:
    """Read a PSA-Dyna JSON report file and preserve its exact-byte SHA-256."""
    report_path = Path(path)
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    raw = report_path.read_bytes()
    try:
        report = json.loads(raw.decode("utf-8-sig", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("PSA-Dyna report must be valid UTF-8 JSON") from exc
    if not isinstance(report, dict):
        raise ValueError("PSA-Dyna JSON report root must be an object")
    return _co2_mixture_fugacity_requests_from_psa_dyna_mean_stream_report(
        report,
        upstream_report_file_sha256=hashlib.sha256(raw).hexdigest(),
        stream_ids=stream_ids,
        backend=backend,
        composition_review_id=composition_review_id,
        absolute_pressure_basis_reviewed=absolute_pressure_basis_reviewed,
        composition_reviewed=composition_reviewed,
        mixture_eos_applicability_reviewed=mixture_eos_applicability_reviewed,
        single_phase_gas_or_supercritical_reviewed=single_phase_gas_or_supercritical_reviewed,
        evidence=evidence,
    )


def co2_mixture_fugacity_requests_from_history(
    history: Co2MixtureFugacityHistory,
    *,
    backend: str,
    composition_review_id: str,
    composition_reviewed: bool,
    mixture_eos_applicability_reviewed: bool,
    single_phase_gas_or_supercritical_reviewed: bool,
    evidence: tuple[Evidence, ...],
) -> dict[str, Any]:
    """Create one review-gated CoolProp request per valid history sample without dropping invalid rows."""
    if not backend.strip() or not composition_review_id.strip():
        raise ValueError("backend and composition review ID must be nonblank")
    from .models.co2_fugacity import CoolPropCo2MixtureFugacityRequest

    history_digest = canonical_digest(history.model_dump(mode="json"))
    component_order_digest = canonical_digest(history.components)
    rows = []
    for index, sample_id in enumerate(history.sample_ids):
        if not history.sample_valid[index]:
            rows.append({
                "sample_id": sample_id,
                "time_s": history.time_s[index],
                "status": "needs_data",
                "request": None,
                "reason": "source_sample_marked_invalid",
                "total_pressure_Pa": history.total_pressure_Pa[index],
                "temperature_K": history.temperature_K[index],
                "mole_fractions": history.mole_fractions_by_sample[index],
            })
            continue
        request = CoolPropCo2MixtureFugacityRequest(
            assessment_id=f"{history.history_id}:{sample_id}",
            temperature_K=history.temperature_K[index],
            total_pressure_Pa=history.total_pressure_Pa[index],
            components=history.components,
            mole_fractions=history.mole_fractions_by_sample[index],
            backend=backend,
            mixture_composition_reviewed=composition_reviewed,
            mixture_eos_applicability_reviewed=mixture_eos_applicability_reviewed,
            single_phase_gas_or_supercritical_reviewed=single_phase_gas_or_supercritical_reviewed,
            review_id=f"{composition_review_id}:{sample_id}",
            evidence=evidence,
        )
        rows.append({
            "sample_id": sample_id,
            "time_s": history.time_s[index],
            "status": "ready" if all((
                composition_reviewed,
                mixture_eos_applicability_reviewed,
                single_phase_gas_or_supercritical_reviewed,
            )) else "needs_data",
            "request": request.model_dump(mode="json"),
            "reason": None if all((
                composition_reviewed,
                mixture_eos_applicability_reviewed,
                single_phase_gas_or_supercritical_reviewed,
            )) else "mixture_EOS_composition_or_phase_review_missing",
        })
    return {
        "schema_version": "matintegrity.co2_mixture_fugacity_request_batch.v1",
        "history_id": history.history_id,
        "asset_id": history.asset_id,
        "location_id": history.location_id,
        "stream_id": history.stream_id,
        "clock_id": history.clock_id,
        "origin": history.origin,
        "case_id": history.case_id,
        "case_input_digest": history.case_input_digest,
        "solver_revision": history.solver_revision,
        "source_digest": history.source_digest,
        "history_digest": history_digest,
        "components": history.components,
        "component_order_digest": component_order_digest,
        "provider_backend": backend,
        "sample_count": len(rows),
        "ready_count": sum(row["status"] == "ready" for row in rows),
        "needs_data_count": sum(row["status"] == "needs_data" for row in rows),
        "sample_requests": rows,
    }


def cavitation_history_inputs_from_operating_history(
    history: OperatingHistory,
    *,
    context: RunContext,
    fluid: str,
    characteristic_velocity_m_s: list[float],
    local_pressure_definition: str,
    velocity_definition: str,
    pressure_represents_local_static_reviewed: bool,
    backend: str = "HEOS",
) -> dict[str, Any]:
    """Compose a reviewed operating-history pressure channel with CoolProp saturation states."""
    if history.asset_id != context.asset_id or history.location_id != context.location_id:
        raise ValueError("operating-history asset and location must match the evaluation context")
    if not pressure_represents_local_static_reviewed:
        raise ValueError("operating pressure must be reviewed as the local absolute static pressure")
    if len(characteristic_velocity_m_s) != len(history.time_s):
        raise ValueError("the velocity history must align with the operating-history clock")
    from .thermo import cavitation_history_inputs_from_coolprop

    return cavitation_history_inputs_from_coolprop(
        history_id=f"operating-history:{history.clock_id}",
        asset_id=history.asset_id,
        location_id=history.location_id,
        clock_id=history.clock_id,
        history_origin=history.origin,
        hydraulic_source_digest=history.source_digest,
        fluid=fluid,
        sample_ids=[f"{history.clock_id}:{index}" for index in range(len(history.time_s))],
        time_s=history.time_s,
        temperature_K=history.temperature_K,
        local_static_pressure_Pa=history.pressure_absolute_Pa,
        characteristic_velocity_m_s=characteristic_velocity_m_s,
        sample_valid=history.valid,
        local_pressure_definition=local_pressure_definition,
        velocity_definition=velocity_definition,
        backend=backend,
    )


class LocalTensorHistory(Contract):
    """Versioned exchange record for one extracted local stress-strain history."""

    schema_version: Literal["matintegrity.local_tensor_history.v1"] = "matintegrity.local_tensor_history.v1"
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    solver_name: str = Field(min_length=1)
    solver_version: str = Field(min_length=1)
    analysis_id: str = Field(min_length=1)
    solution_revision: str = Field(min_length=1)
    mesh_id: str = Field(min_length=1)
    field_location_kind: Literal["node", "integration_point", "surface_point", "user_defined"]
    field_location_id: str = Field(min_length=1)
    spatial_averaging: Literal["none", "nodal_averaged", "element_averaged", "other"]
    coordinate_frame_id: str = Field(min_length=1)
    coordinate_basis_vectors_global: tuple[
        tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]
    ]
    stress_measure: Literal["cauchy", "second_piola_kirchhoff", "other"]
    strain_measure: Literal["infinitesimal", "green_lagrange", "logarithmic", "other"]
    tensor_component_order: Literal["xx_yy_zz_xy_yz_zx"] = "xx_yy_zz_xy_yz_zx"
    strain_shear_convention: Literal["tensor", "engineering"]
    stress_unit: Literal["Pa"] = "Pa"
    strain_unit: Literal["1"] = "1"
    sample_ids: list[str] = Field(min_length=3)
    sample_times_s: list[Nonnegative] = Field(min_length=3)
    sample_valid: list[bool] = Field(min_length=3)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3)
    strain_tensor_components: list[list[float]] = Field(min_length=3)
    representative_cycle_declared: bool
    tensor_field_review_status: Literal["qualified_by_caller", "unreviewed"]
    source_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def aligned_right_handed_history(self):
        count = len(self.sample_ids)
        vectors = (
            self.sample_times_s,
            self.sample_valid,
            self.stress_tensor_components_Pa,
            self.strain_tensor_components,
        )
        if any(len(vector) != count for vector in vectors):
            raise ValueError("tensor-history identifiers, times, validity and tensors must align")
        if len(set(self.sample_ids)) != count:
            raise ValueError("tensor-history sample identifiers must be unique")
        if any(
            later <= earlier
            for earlier, later in zip(self.sample_times_s, self.sample_times_s[1:], strict=False)
        ):
            raise ValueError("tensor-history sample times must be strictly increasing")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        axes = self.coordinate_basis_vectors_global
        for axis in axes:
            if not math.isclose(sum(value * value for value in axis), 1.0, rel_tol=0.0, abs_tol=1e-10):
                raise ValueError("coordinate-frame basis vectors must be unit length")
        for first in range(3):
            for second in range(first + 1, 3):
                if not math.isclose(
                    sum(a * b for a, b in zip(axes[first], axes[second], strict=True)),
                    0.0,
                    rel_tol=0.0,
                    abs_tol=1e-10,
                ):
                    raise ValueError("coordinate-frame basis vectors must be orthogonal")
        cross = (
            axes[0][1] * axes[1][2] - axes[0][2] * axes[1][1],
            axes[0][2] * axes[1][0] - axes[0][0] * axes[1][2],
            axes[0][0] * axes[1][1] - axes[0][1] * axes[1][0],
        )
        handedness = sum(a * b for a, b in zip(cross, axes[2], strict=True))
        if not math.isclose(handedness, 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("coordinate-frame basis must be right handed")
        return self


def critical_plane_inputs_from_local_tensor_history(
    history: LocalTensorHistory,
    *,
    context: RunContext,
    candidate_planes: tuple[dict[str, Any], ...],
    maximum_stress_closure_error_Pa: float,
    maximum_strain_closure_error: float,
    fatemi_socie_coefficient: float,
    normalization_stress_Pa: float,
) -> dict[str, Any]:
    """Validate provenance and adapt one qualified exchange record to critical-plane inputs."""
    if history.asset_id != context.asset_id or history.location_id != context.location_id:
        raise ValueError("tensor-history asset and location must match the evaluation context")
    if history.tensor_field_review_status != "qualified_by_caller":
        raise ValueError("an unreviewed local tensor field cannot feed critical-plane factors")
    if not all(history.sample_valid):
        raise ValueError("invalid or missing tensor samples cannot be silently filtered")
    if history.stress_measure != "cauchy" or history.strain_measure != "infinitesimal":
        raise ValueError("critical-plane factors require Cauchy stress and infinitesimal strain")
    strain_tensors = [list(row) for row in history.strain_tensor_components]
    if history.strain_shear_convention == "engineering":
        strain_tensors = [
            [row[0], row[1], row[2], row[3] / 2, row[4] / 2, row[5] / 2] for row in strain_tensors
        ]
    from .models.fatigue import CriticalPlaneCandidate, CriticalPlaneHistory

    planes = [CriticalPlaneCandidate.model_validate(candidate) for candidate in candidate_planes]
    record_digest = canonical_digest(history.model_dump(mode="json"))
    adapted = CriticalPlaneHistory(
        history_id=history.history_id,
        material_condition_id=history.material_condition_id,
        location_id=history.location_id,
        tensor_source_id=history.tensor_source_id,
        load_case_id=history.load_case_id,
        tensor_provider_id=history.provider_id,
        tensor_provider_version=history.provider_version,
        solver_name=history.solver_name,
        solver_version=history.solver_version,
        analysis_id=history.analysis_id,
        solution_revision=history.solution_revision,
        mesh_id=history.mesh_id,
        field_location_kind=history.field_location_kind,
        field_location_id=history.field_location_id,
        spatial_averaging=history.spatial_averaging,
        coordinate_frame_id=history.coordinate_frame_id,
        coordinate_basis_vectors_global=[list(axis) for axis in history.coordinate_basis_vectors_global],
        stress_measure="cauchy",
        strain_measure="infinitesimal",
        input_strain_shear_convention=history.strain_shear_convention,
        source_content_sha256=history.source_content_sha256,
        provider_configuration_digest=history.provider_configuration_digest,
        tensor_history_record_digest=record_digest,
        sample_ids=history.sample_ids,
        sample_times_s=history.sample_times_s,
        stress_tensor_components_Pa=history.stress_tensor_components_Pa,
        strain_tensor_components=strain_tensors,
        candidate_planes=planes,
        representative_cycle_declared=history.representative_cycle_declared,
        maximum_stress_closure_error_Pa=maximum_stress_closure_error_Pa,
        maximum_strain_closure_error=maximum_strain_closure_error,
        fatemi_socie_coefficient=fatemi_socie_coefficient,
        normalization_stress_Pa=normalization_stress_Pa,
    )
    return adapted.model_dump(mode="json")


def probability_event(
    result: AssessmentResult,
    *,
    event_id: str,
    physical_scope_id: str,
    failure_mode: str,
    horizon_start_s: float,
    horizon_end_s: float,
    conditioning: str,
    probability_key: str = "probability_given_survival",
    common_cause_groups: tuple[str, ...] = (),
) -> EventProbability:
    if result.status != "computed":
        raise ValueError("a noncomputed assessment cannot supply an event probability")
    if result.probability_semantics.get(probability_key) != "conditional_first_failure_in_period":
        raise ValueError(
            "only an explicitly declared conditional first-failure probability may enter a period event; spatial exceedance, detection and unscoped probabilities need a separate qualified physical/temporal model"
        )
    if result.model_id in {"reliability.weibull_interval", "creep.conditional_life"}:
        start = result.inputs["current_age_s"]
        end = start + result.inputs["horizon_s"]
        clock_tolerance_s = 1e-12 * max(1.0, result.inputs["horizon_s"])
        if not math.isclose(horizon_start_s, start, rel_tol=0, abs_tol=clock_tolerance_s) or not math.isclose(
            horizon_end_s, end, rel_tol=0, abs_tol=clock_tolerance_s
        ):
            raise ValueError("event horizon must match the lifetime model's age clock and interval")
    if result.model_id == "reliability.joint_event_probability":
        start = result.inputs["horizon_start_s"]
        end = result.inputs["horizon_end_s"]
        clock_tolerance_s = 1e-12 * max(1.0, end - start)
        if not math.isclose(horizon_start_s, start, rel_tol=0, abs_tol=clock_tolerance_s) or not math.isclose(
            horizon_end_s, end, rel_tol=0, abs_tol=clock_tolerance_s
        ):
            raise ValueError("event horizon must match the joint distribution interval")
        if event_id != result.inputs["top_event_id"]:
            raise ValueError("event identity must match the joint distribution top event")
        if physical_scope_id != result.inputs["physical_scope_id"]:
            raise ValueError("physical scope must match the joint distribution")
        if conditioning != result.inputs["conditioning"]:
            raise ValueError("conditioning must match the joint distribution")
        if tuple(common_cause_groups) != tuple(result.inputs["common_cause_group_ids"]):
            raise ValueError("common-cause groups must match the joint distribution")
    if result.model_id in {
        "reliability.continuous_time_markov_chain",
        "reliability.piecewise_continuous_time_markov_chain",
    }:
        start = result.inputs["horizon_start_s"]
        end = result.inputs["horizon_end_s"]
        clock_tolerance_s = 1e-12 * max(1.0, end - start)
        if not math.isclose(horizon_start_s, start, rel_tol=0, abs_tol=clock_tolerance_s) or not math.isclose(
            horizon_end_s, end, rel_tol=0, abs_tol=clock_tolerance_s
        ):
            raise ValueError("event horizon must match the Markov-chain interval")
        if event_id != result.inputs["top_event_id"]:
            raise ValueError("event identity must match the Markov-chain top event")
        if physical_scope_id != result.inputs["physical_scope_id"]:
            raise ValueError("physical scope must match the Markov chain")
        if conditioning != result.inputs["conditioning"]:
            raise ValueError("conditioning must match the Markov chain")
        if tuple(common_cause_groups) != tuple(result.inputs["common_cause_group_ids"]):
            raise ValueError("common-cause groups must match the Markov chain")
    probability = result.values[probability_key]
    return EventProbability(
        event_id=event_id,
        asset_id=result.context.asset_id,
        physical_scope_id=physical_scope_id,
        failure_mode=failure_mode,
        horizon_start_s=horizon_start_s,
        horizon_end_s=horizon_end_s,
        probability_given_survival=probability,
        conditioning=conditioning,
        model_result_digest=canonical_digest(result.model_dump(mode="json")),
        common_cause_groups=common_cause_groups,
    )


def gaussian_thickness_posterior_sample_inputs(
    result: AssessmentResult,
    *,
    sample_design_id: str,
    assessment_time_s: float,
    required_thickness_m: float,
    requested_accepted_sample_count: int,
    maximum_candidate_draw_multiplier: int,
    random_seed_uint64: int,
    assessment_conditioning_reviewed: bool,
    required_thickness_basis_reviewed: bool,
    deterministic_sampler_reviewed: bool,
    covariance_symmetry_tolerance: float = 1e-24,
) -> dict[str, Any]:
    """Compose a computed linear-Gaussian thickness posterior into its joint sampler."""
    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if result.model_id not in {
        "reliability.bayesian_linear_thickness_update",
        "reliability.linear_thickness_state_space_update",
    }:
        raise ValueError(
            "only a supported linear-Gaussian thickness update can supply this posterior sample design"
        )
    if result.status != "computed":
        raise ValueError("a noncomputed Bayesian thickness update cannot supply a posterior sample design")
    source = result.model_dump(mode="json")
    inputs = result.inputs
    values = result.values
    if result.model_id == "reliability.bayesian_linear_thickness_update":
        reference_time_s = inputs["reference_time_s"]
        reference_thickness_mean_m = values["posterior_remaining_thickness_at_reference_mean_m"]
    else:
        reference_time_s = values["state_time_s"]
        reference_thickness_mean_m = values["posterior_remaining_thickness_at_state_time_mean_m"]
    return {
        "sample_design_id": sample_design_id,
        "asset_id": inputs["asset_id"],
        "location_id": inputs["location_id"],
        "physical_scope_id": inputs["physical_scope_id"],
        "physical_location_id": inputs["physical_location_id"],
        "time_basis": inputs["time_basis"],
        "posterior_definition_id": f"{inputs['update_id']}:{result.model_version}",
        "posterior_source_sha256": canonical_digest(source),
        "posterior_reference_time_s": reference_time_s,
        "assessment_time_s": assessment_time_s,
        "posterior_remaining_thickness_at_reference_mean_m": reference_thickness_mean_m,
        "posterior_loss_rate_mean_m_s": values["posterior_loss_rate_mean_m_s"],
        "posterior_covariance": values["posterior_covariance"],
        "required_thickness_m": required_thickness_m,
        "requested_accepted_sample_count": requested_accepted_sample_count,
        "maximum_candidate_draw_multiplier": maximum_candidate_draw_multiplier,
        "random_seed_uint64": random_seed_uint64,
        "covariance_symmetry_tolerance": covariance_symmetry_tolerance,
        "posterior_basis_reviewed": True,
        "covariance_reviewed": True,
        "assessment_conditioning_reviewed": assessment_conditioning_reviewed,
        "required_thickness_basis_reviewed": required_thickness_basis_reviewed,
        "deterministic_sampler_reviewed": deterministic_sampler_reviewed,
    }


def sampled_linear_thickness_first_passage_inputs(
    result: AssessmentResult,
    *,
    forecast_id: str,
    conditioning: str,
    event_id: str,
    event_definition: str,
    candidate_horizon_end_s: list[float],
    maximum_weight_sum_error: float,
    constant_nonnegative_loss_model_reviewed: bool,
    joint_sample_distribution_reviewed: bool,
    required_thickness_basis_reviewed: bool,
    candidate_horizons_reviewed: bool,
) -> dict[str, Any]:
    """Compose one complete Gaussian posterior sample design into first passage."""
    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if result.model_id != "reliability.gaussian_thickness_posterior_sample_design":
        raise ValueError(
            "only a Gaussian thickness posterior sample design can supply this first-passage input"
        )
    if result.status != "computed" or result.values.get("sample_design_state") != "computed":
        raise ValueError("an incomplete posterior sample design cannot supply first-passage inputs")
    inputs = result.inputs
    values = result.values
    return {
        "forecast_id": forecast_id,
        "asset_id": inputs["asset_id"],
        "location_id": inputs["location_id"],
        "physical_scope_id": inputs["physical_scope_id"],
        "physical_location_id": inputs["physical_location_id"],
        "time_basis": inputs["time_basis"],
        "assessment_time_s": values["assessment_time_s"],
        "conditioning": conditioning,
        "event_id": event_id,
        "event_definition": event_definition,
        "required_thickness_m": values["required_thickness_m"],
        "distribution_definition_id": values["distribution_definition_id"],
        "sample_design_id": values["sample_design_id"],
        "joint_sample_source_sha256": values["joint_sample_source_sha256"],
        "samples": values["samples"],
        "candidate_horizon_end_s": candidate_horizon_end_s,
        "maximum_weight_sum_error": maximum_weight_sum_error,
        "samples_conditioned_on_survival_to_assessment": values[
            "samples_conditioned_on_survival_to_assessment"
        ],
        "constant_nonnegative_loss_model_reviewed": constant_nonnegative_loss_model_reviewed,
        "joint_sample_distribution_reviewed": joint_sample_distribution_reviewed,
        "required_thickness_basis_reviewed": required_thickness_basis_reviewed,
        "candidate_horizons_reviewed": candidate_horizons_reviewed,
    }


def equivalent_stationary_hazard(
    event: EventProbability, *, stationary_hazard_approximation_declared: bool
) -> dict:
    if not stationary_hazard_approximation_declared:
        raise ValueError("a finite-period probability needs an explicit approximation before rate conversion")
    p = event.probability_given_survival
    if p == 1:
        raise ValueError("unit probability has no finite equivalent constant hazard")
    intensity = -math.log1p(-p) / (event.horizon_end_s - event.horizon_start_s)
    return dict(
        schema_version="matintegrity.equivalent_hazard.v1",
        event=event.model_dump(mode="json"),
        equivalent_hazard_per_s=intensity,
        equivalent_hazard_per_year=intensity * SECONDS_PER_YEAR,
        meaning="Equivalent constant first-failure hazard; not an observed recurrent-event frequency.",
        prism_frequency_event_compatible=False,
        required_extension="model-derived source and probability semantics",
    )


class ActionEventProbabilityEvaluation(Contract):
    """One complete external action evaluation before economic comparison."""

    schema_version: Literal["matintegrity.action_event_probability_evaluation.v1"] = (
        "matintegrity.action_event_probability_evaluation.v1"
    )
    action_id: str = Field(min_length=1)
    action_label: str = Field(min_length=1)
    candidate_kind: Literal["baseline", "intervention"]
    action_definition: str = Field(min_length=1)
    evaluator_id: str = Field(min_length=1)
    evaluator_revision: str = Field(min_length=1)
    evaluator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evaluator_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    risk_model_structure_id: str = Field(min_length=1)
    evaluation_status: Literal["computed", "needs_data", "out_of_scope", "invalid_input", "execution_failed"]
    event_probability: EventProbability | None = None
    probability_upper_bound: Fraction | None = None
    status_detail: str = Field(min_length=1)

    @model_validator(mode="after")
    def status_and_probability(self):
        if self.evaluation_status == "computed" and self.event_probability is None:
            raise ValueError("a computed action evaluation requires an event probability")
        if self.evaluation_status != "computed" and self.event_probability is not None:
            raise ValueError("a noncomputed action evaluation cannot carry an event probability")
        if (
            self.event_probability is not None
            and self.probability_upper_bound is not None
            and self.probability_upper_bound < self.event_probability.probability_given_survival
        ):
            raise ValueError("action probability upper bound cannot be below its estimate")
        return self


class FaultTreeActionEventInput(Contract):
    """One action-specific FTA result plus caller-owned economic-comparison metadata."""

    action_id: str = Field(min_length=1)
    action_label: str = Field(min_length=1)
    candidate_kind: Literal["baseline", "intervention"]
    action_definition: str = Field(min_length=1)
    fault_tree_result: AssessmentResult
    top_event_basis: IntegrityEventBasis
    risk_model_structure_id: str = Field(min_length=1)
    evaluator_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    status_detail: str = Field(min_length=1)
    probability_upper_bound: Fraction | None = None
    common_cause_group_ids: tuple[str, ...] = ()
    action_cost_components: list[RiskCostComponent] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_action_costs(self):
        component_ids = [row.component_id for row in self.action_cost_components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("action cost component IDs must be unique")
        if len(self.common_cause_group_ids) != len(set(self.common_cause_group_ids)):
            raise ValueError("common-cause group IDs must be unique")
        return self


class FaultTreeActionResultLineage(Contract):
    action_id: str = Field(min_length=1)
    fault_tree_model_id: Literal["reliability.fault_tree_minimal_cut_sets"]
    fault_tree_model_version: str = Field(min_length=1)
    fault_tree_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    fault_tree_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    fault_tree_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


class FaultTreeInspectionRiskCampaignReport(Contract):
    schema_version: Literal["matintegrity.fault_tree_inspection_risk_campaign.v1"] = (
        "matintegrity.fault_tree_inspection_risk_campaign.v1"
    )
    campaign_id: str = Field(min_length=1)
    action_result_lineage: tuple[FaultTreeActionResultLineage, ...] = Field(min_length=2)
    comparison_input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    comparison_result: AssessmentResult
    comparison_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def aligned_action_lineage(self):
        if self.comparison_result.model_id != "inspection.action_expected_loss":
            raise ValueError("campaign comparison result must be inspection.action_expected_loss")
        if canonical_digest(self.comparison_result.model_dump(mode="json")) != self.comparison_result_digest:
            raise ValueError("comparison result digest does not match the embedded result")
        if canonical_digest(self.comparison_result.inputs) != self.comparison_input_digest:
            raise ValueError("comparison input digest does not match the embedded inputs")
        lineages = {row.action_id: row for row in self.action_result_lineage}
        if len(lineages) != len(self.action_result_lineage):
            raise ValueError("action result lineage IDs must be unique")
        candidates = self.comparison_result.inputs.get("candidates")
        if not isinstance(candidates, list) or {row.get("action_id") for row in candidates} != set(lineages):
            raise ValueError("FTA lineage action coverage must match comparison candidates exactly")
        for row in candidates:
            lineage = lineages[row["action_id"]]
            if (
                row.get("event_probability_result_sha256") != lineage.fault_tree_result_digest
                or row.get("action_effect_input_sha256") != lineage.fault_tree_input_digest
                or row.get("action_effect_model_id") != lineage.fault_tree_model_id
                or row.get("action_effect_model_revision") != lineage.fault_tree_model_version
                or row.get("action_effect_configuration_sha256") != lineage.fault_tree_configuration_digest
            ):
                raise ValueError("comparison action lineage differs from its FTA source result")
        return self


def action_event_probability_from_fault_tree_result(
    result: AssessmentResult,
    *,
    event_basis: IntegrityEventBasis,
    action_id: str,
    action_label: str,
    candidate_kind: Literal["baseline", "intervention"],
    action_definition: str,
    risk_model_structure_id: str,
    evaluator_configuration_sha256: str,
    status_detail: str,
    probability_upper_bound: Fraction | None = None,
    common_cause_group_ids: tuple[str, ...] = (),
) -> ActionEventProbabilityEvaluation:
    """Adapt one scoped FTA top-event result to inspection action probability exchange."""
    from .models.fault_tree import FaultTreeAssessment

    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if not isinstance(event_basis, IntegrityEventBasis):
        raise TypeError("event_basis must be a validated IntegrityEventBasis")
    if result.model_id != "reliability.fault_tree_minimal_cut_sets":
        raise ValueError("fault-tree adapter requires reliability.fault_tree_minimal_cut_sets")
    if result.status != "computed":
        raise ValueError("only a computed fault-tree result can be adapted")
    validated_input = FaultTreeAssessment.model_validate(result.inputs)
    if (
        result.probability_semantics.get("top_event_probability") != "fault_tree_top_event_probability"
        or result.values.get("input_basic_event_probability_meaning") != "conditional_first_failure_in_period"
        or event_basis.probability_conditioning != result.values.get("probability_conditioning")
    ):
        raise ValueError("inspection risk comparison requires first-failure probabilities over a declared period")
    event_probability = result.values.get("top_event_probability")
    result_digest = canonical_digest(result.model_dump(mode="json"))
    if (
        event_basis.event_id != validated_input.top_event_id
        or event_basis.event_probability != event_probability
        or event_basis.probability_semantics != "conditional_first_failure_in_period"
        or event_basis.integrity_model_id != result.model_id
        or event_basis.integrity_model_version != result.model_version
        or event_basis.integrity_input_digest != result.input_digest
        or event_basis.integrity_result_digest != result_digest
    ):
        raise ValueError("top-event basis must exactly identify and match the supplied computed fault-tree result")
    embedded_bases = [row.integrity_event_basis for row in validated_input.basic_events if row.integrity_event_basis]
    if embedded_bases and any(
        (basis.clock_id, basis.horizon_start_s, basis.horizon_end_s)
        != (event_basis.clock_id, event_basis.horizon_start_s, event_basis.horizon_end_s)
        for basis in embedded_bases
    ):
        raise ValueError("top-event basis clock and horizon must match embedded integrity-event horizons")
    return ActionEventProbabilityEvaluation(
        action_id=action_id,
        action_label=action_label,
        candidate_kind=candidate_kind,
        action_definition=action_definition,
        evaluator_id=result.model_id,
        evaluator_revision=result.model_version,
        evaluator_configuration_sha256=evaluator_configuration_sha256,
        evaluator_input_sha256=result.input_digest,
        risk_model_structure_id=risk_model_structure_id,
        evaluation_status="computed",
        event_probability=EventProbability(
            event_id=event_basis.event_id,
            asset_id=event_basis.asset_id,
            physical_scope_id=event_basis.physical_scope_id,
            failure_mode=event_basis.failure_mode,
            horizon_start_s=event_basis.horizon_start_s,
            horizon_end_s=event_basis.horizon_end_s,
            probability_given_survival=event_probability,
            conditioning=event_basis.probability_conditioning,
            model_result_digest=result_digest,
            common_cause_groups=common_cause_group_ids,
        ),
        probability_upper_bound=probability_upper_bound,
        status_detail=(
            status_detail
            + f" FTA result {result_digest} is adapted under independent basic-event assumptions; action-specific FTA input and review remain caller-owned."
        ),
    )


def inspection_action_candidate_from_disposition_tree_result(
    result: AssessmentResult,
) -> dict[str, Any]:
    """Convert one complete disposition-tree result into an estimate-basis action candidate."""
    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if result.model_id != "inspection.disposition_decision_tree":
        raise ValueError("only an inspection disposition-tree result can supply this action candidate")
    if result.status != "computed" or result.values.get("tree_state") != "computed":
        raise ValueError("a noncomputed disposition tree cannot supply an action candidate")
    inputs = result.inputs
    values = result.values
    aggregate_component_id = f"{inputs['tree_id']}:expected-disposition-cost"
    existing_ids = {component["component_id"] for component in inputs["inspection_cost_components"]}
    if aggregate_component_id in existing_ids:
        raise ValueError("reserved expected-disposition cost component ID collides with an input component")
    action_cost_components = [*inputs["inspection_cost_components"]]
    action_cost_components.append(
        {
            "component_id": aggregate_component_id,
            "category": "probability-weighted disposition cost",
            "amount": values["expected_disposition_cost"],
            "basis": (
                f"finite expectation from disposition tree {inputs['tree_id']} result "
                f"{canonical_digest(result.model_dump(mode='json'))}"
            ),
        }
    )
    from .models.inspection import InspectionActionRiskCandidate

    candidate = InspectionActionRiskCandidate.model_validate(
        {
            "action_id": inputs["inspection_action_id"],
            "action_label": inputs["inspection_action_label"],
            "candidate_kind": "intervention",
            "action_definition": inputs["inspection_action_definition"],
            "action_effect_model_id": result.model_id,
            "action_effect_model_revision": result.model_version,
            "action_effect_input_sha256": result.input_digest,
            "action_effect_configuration_sha256": inputs["inspection_outcome_configuration_sha256"],
            "risk_model_structure_id": inputs["risk_model_structure_id"],
            "event_probability_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "common_cause_group_ids": inputs["common_cause_group_ids"],
            "residual_failure_probability_estimate": values["residual_failure_probability_estimate"],
            "residual_failure_probability_upper_bound": None,
            "action_cost_components": action_cost_components,
        }
    )
    return candidate.model_dump(mode="json")


def inspection_policy_candidate_from_evaluation_result(
    result: AssessmentResult,
    *,
    evaluation_configuration_sha256: str,
    resource_usage: list[dict[str, Any]],
    conditional_first_failure_probability_upper_bound: float | None = None,
) -> dict[str, Any]:
    """Preserve one computed fixed-policy evaluation as a comparison candidate."""
    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if result.model_id != "inspection.multi_period_policy_evaluation":
        raise ValueError("only a multi-period policy evaluation can supply this candidate")
    if result.status != "computed" or result.values.get("policy_evaluation_state") != "computed":
        raise ValueError("a noncomputed multi-period policy cannot supply a comparison candidate")
    from .models.inspection import MultiPeriodInspectionPolicyCandidate

    inputs = result.inputs
    values = result.values
    candidate = MultiPeriodInspectionPolicyCandidate.model_validate(
        {
            "policy_id": inputs["policy_id"],
            "policy_revision": inputs["policy_revision"],
            "policy_definition": inputs["policy_definition"],
            "policy_configuration_sha256": inputs["policy_configuration_sha256"],
            "evaluation_model_id": result.model_id,
            "evaluation_model_revision": result.model_version,
            "evaluation_configuration_sha256": evaluation_configuration_sha256,
            "evaluation_input_sha256": result.input_digest,
            "evaluation_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "asset_id": inputs["asset_id"],
            "location_id": inputs["location_id"],
            "physical_scope_id": inputs["physical_scope_id"],
            "event_id": inputs["event_id"],
            "horizon_start_s": inputs["horizon_start_s"],
            "horizon_end_s": inputs["horizon_end_s"],
            "conditioning": inputs["conditioning"],
            "event_probability_meaning": inputs["event_probability_meaning"],
            "cost_basis_id": inputs["cost_basis_id"],
            "currency_or_normalized_unit": inputs["currency_or_normalized_unit"],
            "discount_basis_id": inputs["discount_basis_id"],
            "conditional_first_failure_probability": values["conditional_first_failure_probability"],
            "conditional_first_failure_probability_upper_bound": (
                conditional_first_failure_probability_upper_bound
            ),
            "expected_discounted_action_cost": values["expected_discounted_action_cost"],
            "expected_discounted_failure_consequence": values["expected_discounted_failure_consequence"],
            "expected_discounted_total_loss": values["expected_discounted_total_loss"],
            "resource_usage": resource_usage,
        }
    )
    return candidate.model_dump(mode="json")


def multi_period_policy_evaluation_inputs_from_generated_paths(
    result: AssessmentResult,
    *,
    evaluation_id: str,
    failure_consequence_components: list[dict[str, Any]],
    complete_path_manifest_reviewed: bool,
    path_probabilities_reviewed: bool,
    policy_actions_reviewed: bool,
    first_failure_events_reviewed: bool,
    costs_and_discount_factors_reviewed: bool,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compose one exact finite-policy path expansion into the evaluation contract."""
    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if result.model_id != "inspection.finite_policy_path_generation":
        raise ValueError("only a finite policy path-generation result can supply policy paths")
    if result.status != "computed" or result.values.get("path_generation_state") != "computed":
        raise ValueError("a noncomputed path generation cannot supply a policy evaluation")
    from .models.inspection import MultiPeriodInspectionPolicyEvaluation

    inputs = result.inputs
    values = result.values
    contract = MultiPeriodInspectionPolicyEvaluation.model_validate(
        {
            "evaluation_id": evaluation_id,
            "policy_id": inputs["policy_id"],
            "policy_revision": inputs["policy_revision"],
            "policy_definition": inputs["policy_definition"],
            "policy_configuration_sha256": inputs["policy_configuration_sha256"],
            "path_generator_id": result.model_id,
            "path_generator_revision": result.model_version,
            "path_generator_configuration_sha256": inputs["generator_configuration_sha256"],
            "path_manifest_sha256": values["path_manifest_sha256"],
            "asset_id": inputs["asset_id"],
            "location_id": inputs["location_id"],
            "physical_scope_id": inputs["physical_scope_id"],
            "event_id": inputs["event_id"],
            "event_definition": inputs["event_definition"],
            "horizon_start_s": inputs["horizon_start_s"],
            "horizon_end_s": inputs["horizon_end_s"],
            "conditioning": inputs["conditioning"],
            "event_probability_meaning": inputs["event_probability_meaning"],
            "cost_basis_id": inputs["cost_basis_id"],
            "currency_or_normalized_unit": inputs["currency_or_normalized_unit"],
            "discount_basis_id": inputs["discount_basis_id"],
            "failure_consequence_components": failure_consequence_components,
            "paths": values["paths"],
            "maximum_path_probability_sum_error": inputs["maximum_probability_sum_error"],
            "complete_path_manifest_reviewed": complete_path_manifest_reviewed,
            "path_probabilities_reviewed": path_probabilities_reviewed,
            "policy_actions_reviewed": policy_actions_reviewed,
            "first_failure_events_reviewed": first_failure_events_reviewed,
            "costs_and_discount_factors_reviewed": costs_and_discount_factors_reviewed,
            "evidence": evidence,
        }
    )
    return contract.model_dump(mode="json")


def finite_policy_epoch_from_probability_calibration(
    result: AssessmentResult,
    *,
    stage_id: str,
    stage_time_s: float,
    decision_rules: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    failure_consequence_present_value_factor_by_state_id: dict[str, float],
) -> dict[str, Any]:
    """Compose calibrated tables into one reviewed finite-policy decision epoch."""
    if not isinstance(result, AssessmentResult):
        raise TypeError("a validated AssessmentResult is required")
    if result.model_id != "inspection.finite_policy_probability_calibration":
        raise ValueError("only a finite policy probability calibration can supply calibrated tables")
    if result.status != "computed" or result.values.get("calibration_state") != "computed":
        raise ValueError("a noncomputed probability calibration cannot supply a policy epoch")
    from .models.inspection import FinitePolicyDecisionEpoch

    input_observation_ids = {row["observation_id"] for row in result.inputs["observation_labels"]}
    decision_observation_ids = [row.get("observation_id") for row in decision_rules]
    if (
        len(set(decision_observation_ids)) != len(decision_observation_ids)
        or set(decision_observation_ids) != input_observation_ids
    ):
        raise ValueError("decision rules must cover every calibrated observation label exactly")
    action_ids = [row.get("action_id") for row in actions]
    decision_action_ids = {row.get("action_id") for row in decision_rules}
    if len(set(action_ids)) != len(action_ids) or set(action_ids) != decision_action_ids:
        raise ValueError("actions must cover the calibrated decision-rule action set exactly")
    calibrated_action_ids = {row["action_id"] for row in result.inputs["actions"]}
    if not set(action_ids) <= calibrated_action_ids:
        raise ValueError("policy epoch references an action absent from the probability calibration")
    state_by_id = {row["state_id"]: row for row in result.inputs["states"]}
    failure_state_ids = {state_id for state_id, row in state_by_id.items() if row["is_failure_state"]}
    if set(failure_consequence_present_value_factor_by_state_id) != failure_state_ids:
        raise ValueError("failure consequence factors must cover every calibrated failure state exactly")
    decision_by_observation = {row["observation_id"]: row["action_id"] for row in decision_rules}
    reachable_pairs = {
        (row["state_id"], decision_by_observation[row["observation_id"]])
        for row in result.values["observation_probabilities"]
        if row["probability_given_state"] > 0
    }
    observation_probabilities = [
        {
            "state_id": row["state_id"],
            "observation_id": row["observation_id"],
            "probability_given_state": row["probability_given_state"],
        }
        for row in result.values["observation_probabilities"]
    ]
    transition_probabilities = []
    for row in result.values["transition_probabilities"]:
        pair = (row["from_state_id"], row["action_id"])
        if pair not in reachable_pairs:
            continue
        to_state_id = row["to_state_id"]
        transition_probabilities.append(
            {
                "from_state_id": row["from_state_id"],
                "action_id": row["action_id"],
                "to_state_id": to_state_id,
                "probability_given_state_and_action": row["probability_given_state_and_action"],
                "failure_consequence_present_value_factor": (
                    failure_consequence_present_value_factor_by_state_id[to_state_id]
                    if to_state_id in failure_state_ids
                    else None
                ),
            }
        )
    contract = FinitePolicyDecisionEpoch.model_validate(
        {
            "stage_id": stage_id,
            "stage_time_s": stage_time_s,
            "observation_probabilities": observation_probabilities,
            "decision_rules": decision_rules,
            "actions": actions,
            "transition_probabilities": transition_probabilities,
        }
    )
    return contract.model_dump(mode="json")


def inspection_action_expected_loss_inputs(
    evaluations: list[ActionEventProbabilityEvaluation],
    *,
    expected_action_ids: list[str],
    comparison_id: str,
    location_id: str,
    event_definition: str,
    probability_basis: Literal["estimate", "upper_bound"],
    cost_basis_id: str,
    currency_or_normalized_unit: str,
    failure_consequence_components: list[dict[str, Any]],
    action_cost_components_by_action_id: dict[str, list[dict[str, Any]]],
    cost_tie_absolute_tolerance: float,
    action_definitions_reviewed: bool,
    residual_probabilities_reviewed: bool,
    costs_and_consequences_reviewed: bool,
    decision_criterion_user_approved: bool,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compose complete aligned action evaluations into the expected-loss model contract."""
    if len(expected_action_ids) < 2 or len(set(expected_action_ids)) != len(expected_action_ids):
        raise ValueError("at least two unique expected action IDs are required")
    evaluation_ids = [row.action_id for row in evaluations]
    if len(set(evaluation_ids)) != len(evaluation_ids):
        raise ValueError("action evaluation IDs must be unique")
    expected = set(expected_action_ids)
    supplied = set(evaluation_ids)
    if supplied != expected:
        missing = sorted(expected - supplied)
        extra = sorted(supplied - expected)
        raise ValueError(f"action evaluation coverage differs; missing={missing}, extra={extra}")
    cost_ids = set(action_cost_components_by_action_id)
    if cost_ids != expected:
        missing = sorted(expected - cost_ids)
        extra = sorted(cost_ids - expected)
        raise ValueError(f"action cost coverage differs; missing={missing}, extra={extra}")
    incomplete = [row.action_id for row in evaluations if row.evaluation_status != "computed"]
    if incomplete:
        raise ValueError(
            f"every expected action must have a computed event probability; incomplete={incomplete}"
        )
    by_id = {row.action_id: row for row in evaluations}
    ordered = [by_id[action_id] for action_id in expected_action_ids]
    first_event = ordered[0].event_probability
    assert first_event is not None
    aligned_fields = (
        "event_id",
        "asset_id",
        "physical_scope_id",
        "failure_mode",
        "horizon_start_s",
        "horizon_end_s",
        "conditioning",
    )
    for row in ordered[1:]:
        event = row.event_probability
        assert event is not None
        mismatched = [
            field for field in aligned_fields if getattr(event, field) != getattr(first_event, field)
        ]
        if mismatched:
            raise ValueError(
                f"action event probabilities must share one event context; action={row.action_id}, fields={mismatched}"
            )
    candidates = []
    for row in ordered:
        event = row.event_probability
        assert event is not None
        candidates.append(
            {
                "action_id": row.action_id,
                "action_label": row.action_label,
                "candidate_kind": row.candidate_kind,
                "action_definition": row.action_definition,
                "action_effect_model_id": row.evaluator_id,
                "action_effect_model_revision": row.evaluator_revision,
                "action_effect_input_sha256": row.evaluator_input_sha256,
                "action_effect_configuration_sha256": row.evaluator_configuration_sha256,
                "risk_model_structure_id": row.risk_model_structure_id,
                "event_probability_result_sha256": event.model_result_digest,
                "common_cause_group_ids": list(event.common_cause_groups),
                "residual_failure_probability_estimate": event.probability_given_survival,
                "residual_failure_probability_upper_bound": row.probability_upper_bound,
                "action_cost_components": action_cost_components_by_action_id[row.action_id],
            }
        )
    from .models.inspection import InspectionActionExpectedLossComparison

    contract = InspectionActionExpectedLossComparison.model_validate(
        {
            "comparison_id": comparison_id,
            "asset_id": first_event.asset_id,
            "location_id": location_id,
            "physical_scope_id": first_event.physical_scope_id,
            "event_id": first_event.event_id,
            "event_definition": event_definition,
            "horizon_start_s": first_event.horizon_start_s,
            "horizon_end_s": first_event.horizon_end_s,
            "conditioning": first_event.conditioning,
            "event_probability_meaning": "conditional_first_failure_in_period",
            "probability_basis": probability_basis,
            "cost_basis_id": cost_basis_id,
            "currency_or_normalized_unit": currency_or_normalized_unit,
            "failure_consequence_components": failure_consequence_components,
            "candidates": candidates,
            "cost_tie_absolute_tolerance": cost_tie_absolute_tolerance,
            "action_definitions_reviewed": action_definitions_reviewed,
            "residual_probabilities_reviewed": residual_probabilities_reviewed,
            "costs_and_consequences_reviewed": costs_and_consequences_reviewed,
            "decision_criterion_user_approved": decision_criterion_user_approved,
            "evidence": evidence,
        }
    )
    return contract.model_dump(mode="json")


def inspection_action_expected_loss_inputs_from_fault_trees(
    action_evaluations: list[FaultTreeActionEventInput],
    *,
    expected_action_ids: list[str],
    comparison_id: str,
    location_id: str,
    event_definition: str,
    probability_basis: Literal["estimate", "upper_bound"],
    cost_basis_id: str,
    currency_or_normalized_unit: str,
    failure_consequence_components: list[dict[str, Any]],
    cost_tie_absolute_tolerance: float,
    action_definitions_reviewed: bool,
    residual_probabilities_reviewed: bool,
    costs_and_consequences_reviewed: bool,
    decision_criterion_user_approved: bool,
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compose action-specific FTA results directly into an expected-loss input contract."""
    if any(not isinstance(item, FaultTreeActionEventInput) for item in action_evaluations):
        raise TypeError("every action evaluation must be a validated FaultTreeActionEventInput")
    event_locations = {item.top_event_basis.location_id for item in action_evaluations}
    if event_locations != {location_id}:
        raise ValueError("every FTA top-event basis location must match the comparison location")
    evaluations = [
        action_event_probability_from_fault_tree_result(
            item.fault_tree_result,
            event_basis=item.top_event_basis,
            action_id=item.action_id,
            action_label=item.action_label,
            candidate_kind=item.candidate_kind,
            action_definition=item.action_definition,
            risk_model_structure_id=item.risk_model_structure_id,
            evaluator_configuration_sha256=item.evaluator_configuration_sha256,
            status_detail=item.status_detail,
            probability_upper_bound=item.probability_upper_bound,
            common_cause_group_ids=item.common_cause_group_ids,
        )
        for item in action_evaluations
    ]
    return inspection_action_expected_loss_inputs(
        evaluations,
        expected_action_ids=expected_action_ids,
        comparison_id=comparison_id,
        location_id=location_id,
        event_definition=event_definition,
        probability_basis=probability_basis,
        cost_basis_id=cost_basis_id,
        currency_or_normalized_unit=currency_or_normalized_unit,
        failure_consequence_components=failure_consequence_components,
        action_cost_components_by_action_id={
            item.action_id: [row.model_dump(mode="json") for row in item.action_cost_components]
            for item in action_evaluations
        },
        cost_tie_absolute_tolerance=cost_tie_absolute_tolerance,
        action_definitions_reviewed=action_definitions_reviewed,
        residual_probabilities_reviewed=residual_probabilities_reviewed,
        costs_and_consequences_reviewed=costs_and_consequences_reviewed,
        decision_criterion_user_approved=decision_criterion_user_approved,
        evidence=evidence,
    )


def evaluate_fault_tree_inspection_risk_campaign(
    registry,
    action_evaluations: list[FaultTreeActionEventInput],
    *,
    campaign_id: str,
    context: RunContext,
    expected_action_ids: list[str],
    comparison_id: str,
    location_id: str,
    event_definition: str,
    probability_basis: Literal["estimate", "upper_bound"],
    cost_basis_id: str,
    currency_or_normalized_unit: str,
    failure_consequence_components: list[dict[str, Any]],
    cost_tie_absolute_tolerance: float,
    action_definitions_reviewed: bool,
    residual_probabilities_reviewed: bool,
    costs_and_consequences_reviewed: bool,
    decision_criterion_user_approved: bool,
    evidence: list[dict[str, Any]],
) -> FaultTreeInspectionRiskCampaignReport:
    """Run the registered expected-loss model and preserve all action/result digests."""
    from .registry import ModelRegistry

    if not isinstance(registry, ModelRegistry):
        raise TypeError("registry must be a ModelRegistry")
    if not isinstance(context, RunContext):
        raise TypeError("context must be a RunContext")
    comparison_inputs = inspection_action_expected_loss_inputs_from_fault_trees(
        action_evaluations,
        expected_action_ids=expected_action_ids,
        comparison_id=comparison_id,
        location_id=location_id,
        event_definition=event_definition,
        probability_basis=probability_basis,
        cost_basis_id=cost_basis_id,
        currency_or_normalized_unit=currency_or_normalized_unit,
        failure_consequence_components=failure_consequence_components,
        cost_tie_absolute_tolerance=cost_tie_absolute_tolerance,
        action_definitions_reviewed=action_definitions_reviewed,
        residual_probabilities_reviewed=residual_probabilities_reviewed,
        costs_and_consequences_reviewed=costs_and_consequences_reviewed,
        decision_criterion_user_approved=decision_criterion_user_approved,
        evidence=evidence,
    )
    result = registry.run("inspection.action_expected_loss", comparison_inputs, context)
    lineage = tuple(
        FaultTreeActionResultLineage(
            action_id=item.action_id,
            fault_tree_model_id=item.fault_tree_result.model_id,
            fault_tree_model_version=item.fault_tree_result.model_version,
            fault_tree_configuration_digest=item.evaluator_configuration_sha256,
            fault_tree_input_digest=item.fault_tree_result.input_digest,
            fault_tree_result_digest=canonical_digest(item.fault_tree_result.model_dump(mode="json")),
        )
        for item in action_evaluations
    )
    result_payload = result.model_dump(mode="json")
    return FaultTreeInspectionRiskCampaignReport(
        campaign_id=campaign_id,
        action_result_lineage=lineage,
        comparison_input_digest=canonical_digest(comparison_inputs),
        comparison_result=result,
        comparison_result_digest=canonical_digest(result_payload),
    )


def explanation_payload(result: AssessmentResult) -> dict:
    return dict(
        schema_version="matintegrity.explanation_context.v1",
        assessment=result.model_dump(mode="json"),
        instruction_boundary="Explain supplied calculations, assumptions and missing evidence; do not invent acceptance limits.",
    )


class MonitoringAssessmentRecord(Contract):
    schema_version: Literal["matintegrity.monitoring_context.v1"] = "matintegrity.monitoring_context.v1"
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    status: Literal["computed", "out_of_scope", "needs_data"]
    inputs: dict[str, Any]
    values: dict[str, Any]
    units: dict[str, str]
    assumptions: list[str]
    notes: list[str]
    context: dict[str, Any]
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_ids: list[str]
    qualification: Literal["engineering_screening", "user_model"]
    runtime: dict[str, str]
    probability_semantics: dict[str, ProbabilityMeaning]
    time_basis: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    meaning: Literal[
        "Calculated features with preserved origin; anomalies do not themselves define failure probability."
    ] = "Calculated features with preserved origin; anomalies do not themselves define failure probability."

    @model_validator(mode="after")
    def identity_and_digest_match_assessment(self):
        context = RunContext.model_validate_json(json.dumps(self.context, allow_nan=False))
        if (
            self.asset_id != context.asset_id
            or self.location_id != context.location_id
            or self.time_basis != context.time_basis
        ):
            raise ValueError("monitoring identity and time basis must match the assessment context")
        assessment = AssessmentResult(
            model_id=self.model_id,
            model_version=self.model_version,
            status=self.status,
            inputs=self.inputs,
            values=self.values,
            units=self.units,
            assumptions=tuple(self.assumptions),
            notes=tuple(self.notes),
            context=context,
            input_digest=self.input_digest,
            source_ids=tuple(self.source_ids),
            qualification=self.qualification,
            runtime=self.runtime,
            probability_semantics=self.probability_semantics,
        )
        if canonical_digest(assessment.model_dump(mode="json")) != self.source_digest:
            raise ValueError("monitoring source digest does not match the complete assessment snapshot")
        return self


def monitoring_record(result: AssessmentResult) -> dict:
    snapshot = result.model_dump(mode="json")
    record = MonitoringAssessmentRecord(
        asset_id=result.context.asset_id,
        location_id=result.context.location_id,
        model_id=result.model_id,
        model_version=result.model_version,
        status=result.status,
        values=snapshot["values"],
        units=snapshot["units"],
        inputs=snapshot["inputs"],
        assumptions=snapshot["assumptions"],
        notes=snapshot["notes"],
        context=snapshot["context"],
        input_digest=result.input_digest,
        source_ids=snapshot["source_ids"],
        qualification=result.qualification,
        runtime=result.runtime,
        probability_semantics=result.probability_semantics,
        time_basis=result.context.time_basis,
        source_digest=canonical_digest(snapshot),
    )
    return record.model_dump(mode="json")


def layered_scale_transport_request_from_history(
    result: AssessmentResult,
    transport_request,
    *,
    selected_time_s: float,
    scale_layer_id: str,
    scale_state_to_layer_mapping_reviewed: bool,
    coverage_characteristic_thickness_m: float | None = None,
    coverage_shape_exponent: float | None = None,
    thickness_to_coverage_relation_reviewed: bool = False,
):
    """Bind one exact scale-kinetics output knot to one caller-selected transport layer.

    Layer diffusivity, partition and all other transport inputs remain caller
    supplied. Coverage may optionally use an explicitly reviewed monotone
    relation ``1 - exp(-(thickness / characteristic_thickness) ** exponent)``.
    This is a caller model, not an inferred morphology law. The complete source
    assessment digest and selected time are written into the returned request.
    """
    from .models.scale_film_transport import LayeredScaleDiffusionLimit

    if not isinstance(result, AssessmentResult):
        raise TypeError("scale-history adapter requires a validated AssessmentResult")
    if not isinstance(transport_request, LayeredScaleDiffusionLimit):
        raise TypeError("scale-history adapter requires a LayeredScaleDiffusionLimit request")
    supported_scale_models = {
        "chemistry.caller_surface_scale_kinetics",
        "chemistry.caller_scale_coverage_kinetics",
    }
    if result.model_id not in supported_scale_models:
        raise ValueError("only registered single-phase scale-thickness or coverage kinetics can supply this history")
    if result.status != "computed":
        raise ValueError("scale-kinetics result must be computed before it can supply a thickness")
    calculation_input_digest = canonical_digest(result.inputs)
    if result.values.get("input_digest") != calculation_input_digest:
        raise ValueError("scale result values do not match the pinned calculation input digest")
    assessment_payload = {
        "model_id": result.model_id,
        "model_version": result.model_version,
        "inputs": result.inputs,
        "context": result.context.model_dump(mode="json"),
    }
    if canonical_digest(assessment_payload) != result.input_digest:
        raise ValueError("scale AssessmentResult does not match its pinned model/input/context digest")
    if not scale_state_to_layer_mapping_reviewed:
        raise ValueError("caller review is required to map the identified scale phase to a transport layer")

    values = result.values
    if values.get("physical_scope_id") != transport_request.physical_scope_id:
        raise ValueError("scale and transport physical scopes differ")
    if values.get("substrate_condition_id") != transport_request.substrate_condition_id:
        raise ValueError("scale and transport substrate conditions differ")
    if values.get("solution_condition_id") != transport_request.solution_condition_id:
        raise ValueError("scale and transport solution conditions differ")
    if values.get("condition_sha256") != transport_request.condition_sha256:
        raise ValueError("scale and transport condition digests differ")
    if values.get("scale_phase_id") != transport_request.scale_phase_id:
        raise ValueError("scale phase identity differs from the selected transport scale phase")
    if isinstance(selected_time_s, bool) or not math.isfinite(selected_time_s) or selected_time_s < 0:
        raise ValueError("selected scale-history time must be finite and nonnegative")

    history = values.get("scale_history")
    if not isinstance(history, list):
        raise ValueError("scale-kinetics result has no typed scale history")
    matches = [row for row in history if isinstance(row, dict) and row.get("time_s") == selected_time_s]
    if len(matches) != 1:
        raise ValueError("selected time must exactly match one recorded scale-history knot; no interpolation is performed")
    coverage_result = result.model_id == "chemistry.caller_scale_coverage_kinetics"
    thickness = matches[0].get("scale_thickness_m")
    direct_coverage = matches[0].get("covered_area_fraction")
    if coverage_result:
        if isinstance(direct_coverage, bool) or not isinstance(direct_coverage, (int, float)) or not math.isfinite(direct_coverage) or not 0.0 <= direct_coverage <= 1.0:
            raise ValueError("selected scale coverage is not a finite fraction")
        if coverage_characteristic_thickness_m is not None or coverage_shape_exponent is not None or thickness_to_coverage_relation_reviewed:
            raise ValueError("direct scale coverage history cannot be combined with a thickness-to-coverage relation")
    else:
        if isinstance(thickness, bool) or not isinstance(thickness, (int, float)) or not math.isfinite(thickness) or thickness < 0:
            raise ValueError("selected scale thickness is not a finite nonnegative scalar")

    coverage_parameters = (coverage_characteristic_thickness_m, coverage_shape_exponent)
    if any(value is not None for value in coverage_parameters):
        if any(value is None for value in coverage_parameters) or not thickness_to_coverage_relation_reviewed:
            raise ValueError("coverage mapping requires both caller parameters and an explicit review")
        if any(isinstance(value, bool) or not math.isfinite(value) or value <= 0 for value in coverage_parameters):
            raise ValueError("coverage mapping parameters must be finite and positive")
    elif thickness_to_coverage_relation_reviewed:
        raise ValueError("coverage mapping review requires caller-supplied parameters")

    payload = transport_request.model_dump(mode="json")
    layers = payload["layers"]
    selected_layers = [index for index, row in enumerate(layers) if row.get("layer_id") == scale_layer_id]
    if len(selected_layers) != 1:
        raise ValueError("scale_layer_id must identify exactly one caller-supplied layer")
    if not coverage_result:
        layers[selected_layers[0]]["thickness_m"] = float(thickness)
    if coverage_result:
        payload["covered_area_fraction"] = float(direct_coverage)
    elif coverage_characteristic_thickness_m is not None:
        if thickness == 0.0:
            covered_fraction = 0.0
        else:
            log_scaled_thickness = coverage_shape_exponent * math.log(
                thickness / coverage_characteristic_thickness_m
            )
            scaled_thickness = (
                math.inf if log_scaled_thickness > math.log(745.0) else math.exp(log_scaled_thickness)
            )
            covered_fraction = -math.expm1(-scaled_thickness)
        if not math.isfinite(covered_fraction) or not 0.0 <= covered_fraction <= 1.0:
            raise ValueError("caller thickness-to-coverage relation exceeded finite [0, 1] support")
        payload["covered_area_fraction"] = covered_fraction
    result_digest = canonical_digest(result.model_dump(mode="json"))
    state_digest = canonical_digest({
        "scale_history_result_digest": result_digest,
        "selected_time_s": selected_time_s,
        "scale_phase_id": transport_request.scale_phase_id,
        "scale_layer_id": scale_layer_id,
        "coverage_characteristic_thickness_m": coverage_characteristic_thickness_m,
        "coverage_shape_exponent": coverage_shape_exponent,
        "covered_area_fraction": direct_coverage if coverage_result else payload["covered_area_fraction"],
    })
    payload.update({
        "scale_state_id": state_digest,
        "scale_history_result_digest": result_digest,
        "scale_history_time_s": selected_time_s,
        "scale_history_model_id": result.model_id,
        "scale_history_phase_id": transport_request.scale_phase_id,
        "scale_history_layer_id": scale_layer_id,
        "scale_history_covered_area_fraction": float(direct_coverage) if coverage_result else None,
        "scale_history_mapping_reviewed": True,
    })
    return LayeredScaleDiffusionLimit.model_validate(payload)
