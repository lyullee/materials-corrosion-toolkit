"""Caller-calibrated single-phase surface-scale thickness history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, ValidationError, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from .scale_coverage_kinetics import CallerScaleCoverageKinetics, caller_scale_coverage_kinetics


class SurfaceScaleKineticInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    saturation_ratio: Nonnegative
    saturation_ratio_end: Nonnegative | None = None
    temperature_K: Positive | None = None

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("scale-kinetic interval must have positive duration")
        return self


class CallerSurfaceScaleKinetics(Contract):
    schema_version: Literal["matintegrity.caller_surface_scale_kinetics.v1"] = (
        "matintegrity.caller_surface_scale_kinetics.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    solution_condition_id: str = Field(min_length=1)
    scale_phase_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: Positive
    initial_scale_thickness_m: Nonnegative
    precipitation_rate_constant_mol_m2_s: Nonnegative
    rate_reference_temperature_K: Positive | None = None
    minimum_rate_valid_temperature_K: Positive | None = None
    maximum_rate_valid_temperature_K: Positive | None = None
    precipitation_activation_energy_J_mol: Nonnegative | None = None
    precipitation_order: Positive = Field(le=8.0)
    dissolution_rate_constant_mol_m2_s: Nonnegative
    dissolution_activation_energy_J_mol: Nonnegative | None = None
    dissolution_order: Positive = Field(le=8.0)
    scale_molar_volume_m3_mol: Positive
    intervals: tuple[SurfaceScaleKineticInterval, ...] = Field(min_length=1, max_length=100000)
    interval_constant_saturation_reviewed: bool = False
    linearly_varying_saturation_reviewed: bool = False
    interval_temperature_profile_reviewed: bool = False
    arrhenius_temperature_scaling_reviewed: bool = False
    supersaturation_kinetics_and_standard_state_reviewed: bool
    precipitation_and_dissolution_coefficients_reviewed: bool
    scale_phase_identity_and_molar_volume_reviewed: bool
    single_uniform_scale_layer_scope_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_intervals(self):
        varying = any(
            row.saturation_ratio_end is not None
            and row.saturation_ratio_end != row.saturation_ratio
            for row in self.intervals
        )
        has_constant_interval = any(
            row.saturation_ratio_end is None
            or row.saturation_ratio_end == row.saturation_ratio
            for row in self.intervals
        )
        if varying and not self.linearly_varying_saturation_reviewed:
            raise ValueError("varying interval saturation requires explicit linear-path review")
        if self.linearly_varying_saturation_reviewed and not varying:
            raise ValueError("linear saturation review is declared without a varying saturation path")
        interval_temperatures = [row.temperature_K for row in self.intervals]
        has_interval_temperatures = any(value is not None for value in interval_temperatures)
        if has_interval_temperatures and any(value is None for value in interval_temperatures):
            raise ValueError("interval temperature must be supplied for every interval or none")
        if has_interval_temperatures and not self.interval_temperature_profile_reviewed:
            raise ValueError("piecewise-constant interval temperatures require explicit profile review")
        if self.interval_temperature_profile_reviewed and not has_interval_temperatures:
            raise ValueError("interval temperature review is declared without interval temperatures")
        if has_interval_temperatures:
            declared_temperatures = [float(value) for value in interval_temperatures if value is not None]
            if any(value != self.temperature_K for value in declared_temperatures) and self.rate_reference_temperature_K is None:
                raise ValueError("temperature-varying intervals require caller-reviewed Arrhenius rate parameters")
            if self.rate_reference_temperature_K is not None and any(
                not self.minimum_rate_valid_temperature_K <= value <= self.maximum_rate_valid_temperature_K
                for value in declared_temperatures
            ):
                raise ValueError("an interval temperature lies outside the caller-declared Arrhenius support")
        elif self.interval_temperature_profile_reviewed:
            raise ValueError("interval temperature profile review requires interval temperature values")
        if not has_constant_interval and self.interval_constant_saturation_reviewed:
            raise ValueError("constant saturation review is declared without a constant interval")
        arrhenius_values = (
            self.rate_reference_temperature_K,
            self.minimum_rate_valid_temperature_K,
            self.maximum_rate_valid_temperature_K,
            self.precipitation_activation_energy_J_mol,
            self.dissolution_activation_energy_J_mol,
        )
        if any(value is not None for value in arrhenius_values):
            if any(value is None for value in arrhenius_values):
                raise ValueError("Arrhenius scaling requires reference/support temperatures and both activation energies")
            if not self.arrhenius_temperature_scaling_reviewed:
                raise ValueError("Arrhenius scaling requires explicit parameter applicability review")
            if self.maximum_rate_valid_temperature_K <= self.minimum_rate_valid_temperature_K:
                raise ValueError("Arrhenius temperature support must be a nonempty interval")
            if not self.minimum_rate_valid_temperature_K <= self.rate_reference_temperature_K <= self.maximum_rate_valid_temperature_K:
                raise ValueError("Arrhenius reference temperature must lie within declared support")
            if not self.minimum_rate_valid_temperature_K <= self.temperature_K <= self.maximum_rate_valid_temperature_K:
                raise ValueError("target temperature lies outside caller-declared rate support")
        elif self.arrhenius_temperature_scaling_reviewed:
            raise ValueError("Arrhenius scaling review requires its parameters")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("scale-kinetic history must start at zero elapsed time")
        ids = [row.interval_id for row in self.intervals]
        if len(ids) != len(set(ids)):
            raise ValueError("scale-kinetic interval IDs must be unique")
        if any(right.start_time_s != left.end_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:], strict=True)):
            raise ValueError("scale-kinetic intervals must be contiguous and ordered")
        return self


def _arrhenius_rate_constant(
    reference_rate: float,
    activation_energy_J_mol: float,
    reference_temperature_K: float,
    temperature_K: float,
) -> float:
    if reference_rate == 0.0:
        return 0.0
    exponent = -activation_energy_J_mol / 8.31446261815324 * (
        1.0 / temperature_K - 1.0 / reference_temperature_K
    )
    log_rate = math.log(reference_rate) + exponent
    if not math.isfinite(log_rate) or log_rate > math.log(float.fromhex("0x1.fffffffffffffp+1023")):
        raise ArithmeticError("scale thickness rate exceeds finite Arrhenius support")
    if log_rate < math.log(math.ulp(0.0)):
        raise ArithmeticError("scale thickness rate underflows declared Arrhenius support")
    rate = math.exp(log_rate)
    if not math.isfinite(rate) or rate <= 0.0:
        raise ArithmeticError("scale thickness rate exceeds finite Arrhenius support")
    return rate


def _integrated_positive_power_path(
    start_value: float,
    end_value: float,
    power: float,
    duration_s: float,
) -> float:
    """Exactly integrate max(y(t), 0)**power for a linear endpoint path."""
    difference = end_value - start_value
    if difference == 0.0:
        return duration_s * max(start_value, 0.0) ** power
    return duration_s * (
        max(end_value, 0.0) ** (power + 1.0)
        - max(start_value, 0.0) ** (power + 1.0)
    ) / (difference * (power + 1.0))


def caller_surface_scale_kinetics(x: CallerSurfaceScaleKinetics) -> Calculation:
    """Integrate caller-specified precipitation/dissolution molar fluxes.

    Saturation may be constant or caller-reviewed linear between interval
    endpoints. Positive-part power laws are integrated analytically; inventory
    ordering is bounded conservatively when a path crosses saturation. No
    protective effect on substrate corrosion is inferred.
    """
    digest = canonical_digest(x.model_dump(mode="json"))
    base = {
        "assessment_id": x.assessment_id,
        "physical_scope_id": x.physical_scope_id,
        "substrate_condition_id": x.substrate_condition_id,
        "solution_condition_id": x.solution_condition_id,
        "scale_phase_id": x.scale_phase_id,
        "physical_specimen_id": x.physical_specimen_id,
        "source_group_id": x.source_group_id,
        "provider_id": x.provider_id,
        "provider_revision": x.provider_revision,
        "source_sha256": x.source_sha256,
        "condition_sha256": x.condition_sha256,
        "kinetic_configuration_sha256": x.kinetic_configuration_sha256,
        "temperature_K": x.temperature_K,
        "rate_reference_temperature_K": x.rate_reference_temperature_K,
        "minimum_rate_valid_temperature_K": x.minimum_rate_valid_temperature_K,
        "maximum_rate_valid_temperature_K": x.maximum_rate_valid_temperature_K,
        "precipitation_rate_constant_mol_m2_s": x.precipitation_rate_constant_mol_m2_s,
        "precipitation_activation_energy_J_mol": x.precipitation_activation_energy_J_mol,
        "dissolution_rate_constant_mol_m2_s": x.dissolution_rate_constant_mol_m2_s,
        "dissolution_activation_energy_J_mol": x.dissolution_activation_energy_J_mol,
        "arrhenius_temperature_scaling_reviewed": x.arrhenius_temperature_scaling_reviewed,
        "interval_temperature_profile_reviewed": x.interval_temperature_profile_reviewed,
        "input_digest": digest,
    }
    reviews = {
        "supersaturation_kinetics_and_standard_state_reviewed": x.supersaturation_kinetics_and_standard_state_reviewed,
        "precipitation_and_dissolution_coefficients_reviewed": x.precipitation_and_dissolution_coefficients_reviewed,
        "scale_phase_identity_and_molar_volume_reviewed": x.scale_phase_identity_and_molar_volume_reviewed,
        "single_uniform_scale_layer_scope_reviewed": x.single_uniform_scale_layer_scope_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    if any(row.saturation_ratio_end is None or row.saturation_ratio_end == row.saturation_ratio for row in x.intervals):
        reviews["interval_constant_saturation_reviewed"] = x.interval_constant_saturation_reviewed
    if x.linearly_varying_saturation_reviewed:
        reviews["linearly_varying_saturation_reviewed"] = x.linearly_varying_saturation_reviewed
    if x.interval_temperature_profile_reviewed:
        reviews["interval_temperature_profile_reviewed"] = x.interval_temperature_profile_reviewed
    missing = [name for name, reviewed in reviews.items() if not reviewed]
    if missing:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": missing},
            notes=("Review the interval saturation interpretation, phase identity, kinetic coefficients, molar volume and uniform-layer scope before integrating.",),
        )

    try:
        if x.rate_reference_temperature_K is None:
            precipitation_rate_constant = x.precipitation_rate_constant_mol_m2_s
            dissolution_rate_constant = x.dissolution_rate_constant_mol_m2_s
            rate_scaling = "caller_constants_at_declared_temperature"
        else:
            precipitation_rate_constant = _arrhenius_rate_constant(
                x.precipitation_rate_constant_mol_m2_s,
                x.precipitation_activation_energy_J_mol,
                x.rate_reference_temperature_K,
                x.temperature_K,
            )
            dissolution_rate_constant = _arrhenius_rate_constant(
                x.dissolution_rate_constant_mol_m2_s,
                x.dissolution_activation_energy_J_mol,
                x.rate_reference_temperature_K,
                x.temperature_K,
            )
            rate_scaling = "caller_arrhenius_scaled_from_reference_temperature"
    except ArithmeticError as error:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": str(error)})
    base |= {
        "effective_precipitation_rate_constant_at_temperature_mol_m2_s": precipitation_rate_constant,
        "effective_dissolution_rate_constant_at_temperature_mol_m2_s": dissolution_rate_constant,
        "rate_temperature_scaling": rate_scaling,
    }

    thickness = x.initial_scale_thickness_m
    cumulative_precipitated_mol_m2 = 0.0
    cumulative_dissolved_mol_m2 = 0.0
    rows = [{
        "time_s": x.intervals[0].start_time_s,
        "scale_thickness_m": thickness,
        "cumulative_precipitated_mol_m2": 0.0,
        "cumulative_dissolved_mol_m2": 0.0,
        "saturation_ratio_for_next_interval": x.intervals[0].saturation_ratio,
        "saturation_ratio_end_for_next_interval": x.intervals[0].saturation_ratio_end,
    }]
    try:
        for interval in x.intervals:
            dt = interval.end_time_s - interval.start_time_s
            interval_temperature = x.temperature_K if interval.temperature_K is None else interval.temperature_K
            if x.rate_reference_temperature_K is None:
                interval_precipitation_rate_constant = x.precipitation_rate_constant_mol_m2_s
                interval_dissolution_rate_constant = x.dissolution_rate_constant_mol_m2_s
            else:
                interval_precipitation_rate_constant = _arrhenius_rate_constant(
                    x.precipitation_rate_constant_mol_m2_s,
                    x.precipitation_activation_energy_J_mol,
                    x.rate_reference_temperature_K,
                    interval_temperature,
                )
                interval_dissolution_rate_constant = _arrhenius_rate_constant(
                    x.dissolution_rate_constant_mol_m2_s,
                    x.dissolution_activation_energy_J_mol,
                    x.rate_reference_temperature_K,
                    interval_temperature,
                )
            saturation_end = (
                interval.saturation_ratio
                if interval.saturation_ratio_end is None
                else interval.saturation_ratio_end
            )
            # Roundoff after a fully dissolved layer can leave a tiny negative
            # inventory. Never let that numerical residue create negative
            # available material (which would reverse the dissolution flux).
            thickness = max(thickness, 0.0)
            precipitation_exposure = _integrated_positive_power_path(
                interval.saturation_ratio - 1.0,
                saturation_end - 1.0,
                x.precipitation_order,
                dt,
            )
            dissolution_exposure = _integrated_positive_power_path(
                1.0 - interval.saturation_ratio,
                1.0 - saturation_end,
                x.dissolution_order,
                dt,
            )
            precipitated = interval_precipitation_rate_constant * precipitation_exposure
            dissolution_demand = interval_dissolution_rate_constant * dissolution_exposure
            precipitation_precedes_dissolution = interval.saturation_ratio > 1.0 and saturation_end < 1.0
            available = max(thickness, 0.0) / x.scale_molar_volume_m3_mol
            if precipitation_precedes_dissolution:
                available += precipitated
            dissolved = min(dissolution_demand, available)
            precipitation_flux = precipitated / dt
            dissolution_flux = dissolved / dt
            cumulative_precipitated_mol_m2 += precipitated
            cumulative_dissolved_mol_m2 += dissolved
            thickness = max(0.0, x.initial_scale_thickness_m + x.scale_molar_volume_m3_mol * (
                cumulative_precipitated_mol_m2 - cumulative_dissolved_mol_m2
            ))
            if not all(math.isfinite(value) for value in (
                precipitated, dissolved, cumulative_precipitated_mol_m2,
                cumulative_dissolved_mol_m2, thickness,
            )):
                return Calculation(
                    status="out_of_scope",
                    values=base | {
                        "out_of_scope_reason": "scale_kinetic_state_exceeded_finite_numeric_range",
                        "first_unsupported_interval_id": interval.interval_id,
                        "computed_prefix": rows,
                    },
                    notes=("The kinetic law overflowed finite numeric support; the incomplete history is not returned as a complete result.",),
                )
            rows.append({
                "time_s": interval.end_time_s,
                "interval_id": interval.interval_id,
                "temperature_K": interval_temperature,
                "precipitation_rate_constant_mol_m2_s": interval_precipitation_rate_constant,
                "dissolution_rate_constant_mol_m2_s": interval_dissolution_rate_constant,
                "saturation_ratio": interval.saturation_ratio,
                "saturation_ratio_end": saturation_end,
                "precipitation_flux_mol_m2_s": precipitation_flux,
                "dissolution_flux_mol_m2_s": dissolution_flux,
                "precipitated_mol_m2": precipitated,
                "dissolved_mol_m2": dissolved,
                "scale_thickness_m": thickness,
                "cumulative_precipitated_mol_m2": cumulative_precipitated_mol_m2,
                "cumulative_dissolved_mol_m2": cumulative_dissolved_mol_m2,
            })
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(
            status="out_of_scope",
            values=base | {"out_of_scope_reason": str(error), "computed_prefix": rows},
            notes=("The caller's phase-specific kinetic law left finite numerical support; no complete history is reported.",),
        )

    return Calculation(
        values=base | {
            "initial_scale_thickness_m": x.initial_scale_thickness_m,
            "final_scale_thickness_m": thickness,
            "cumulative_precipitated_mol_m2": cumulative_precipitated_mol_m2,
            "cumulative_dissolved_mol_m2": cumulative_dissolved_mol_m2,
            "scale_history": rows,
            "interval_saturation_interpretation": (
                "caller_supplied_piecewise_linear_endpoints"
                if x.linearly_varying_saturation_reviewed
                else "caller_supplied_constant_per_interval"
            ),
            "scale_model": "single_uniform_phase_with_bounded_inventory_dissolution",
        },
        notes=(
            "Scale thickness is an area-average geometric inventory derived from caller molar flux coefficients and molar volume.",
            "The calculation does not solve saturation chemistry, phase competition, nucleation, porosity, morphology, transport, scale adhesion, protective effectiveness, corrosion rate, life or acceptance.",
        ),
    )


def run_surface_scale_kinetics_from_saturation_history(
    saturation_history: AssessmentResult,
    *,
    saturation_history_sha256: str,
    candidate_solid_id: str,
    kinetics_request: CallerSurfaceScaleKinetics,
    temperature_knot_mapping_reviewed: bool = False,
) -> Calculation:
    """Bind exact chemistry-screen knots to reviewed single-phase kinetics.

    Only the saturation trajectory is transferred. The caller still supplies and
    reviews all empirical rate coefficients and their applicability.
    """
    upstream_digest = canonical_digest(saturation_history.model_dump(mode="json"))
    expected_input_digest = canonical_digest({
        "model_id": saturation_history.model_id,
        "model_version": saturation_history.model_version,
        "inputs": saturation_history.inputs,
        "context": saturation_history.context.model_dump(mode="json"),
    })
    if (
        saturation_history.model_id != "integration.aqueous_vant_hoff_saturation_history"
        or saturation_history.status != "computed"
        or saturation_history.input_digest != expected_input_digest
        or upstream_digest != saturation_history_sha256
    ):
        return Calculation(status="needs_data", values={
            "upstream_saturation_history_sha256": upstream_digest,
            "upstream_model_id": saturation_history.model_id,
            "reason": "computed_digest_pinned_saturation_history_required",
        })
    values = saturation_history.values
    times, rows = values.get("times_s"), values.get("saturation_history")
    temperatures = values.get("temperatures_K")
    raw_equilibrium = saturation_history.inputs.get("equilibrium_history")
    equilibrium_digest = saturation_history.inputs.get("equilibrium_history_sha256")
    if isinstance(raw_equilibrium, dict):
        equilibrium_values = raw_equilibrium.get("values")
        equilibrium_context = raw_equilibrium.get("context")
        try:
            equilibrium_input_digest = canonical_digest({
                "model_id": raw_equilibrium["model_id"],
                "model_version": raw_equilibrium["model_version"],
                "inputs": raw_equilibrium["inputs"],
                "context": equilibrium_context,
            })
        except (KeyError, TypeError, ValueError):
            equilibrium_input_digest = None
    else:
        equilibrium_values = None
        equilibrium_input_digest = None
    source_times = equilibrium_values.get("times_s") if isinstance(equilibrium_values, dict) else None
    source_temperatures = equilibrium_values.get("temperatures_K") if isinstance(equilibrium_values, dict) else None
    source_knots = equilibrium_values.get("equilibrium_history") if isinstance(equilibrium_values, dict) else None
    if (
        not isinstance(times, list)
        or not isinstance(temperatures, list)
        or not isinstance(rows, list)
        or len(times) != len(temperatures)
        or len(times) != len(rows)
        or len(times) < 2
        or not isinstance(raw_equilibrium, dict)
        or raw_equilibrium.get("model_id") != "integration.aqueous_mass_action_vant_hoff_history"
        or raw_equilibrium.get("status") != "computed"
        or raw_equilibrium.get("input_digest") != equilibrium_input_digest
        or canonical_digest(raw_equilibrium) != equilibrium_digest
        or not isinstance(source_times, list)
        or not isinstance(source_temperatures, list)
        or not isinstance(source_knots, list)
        or not (len(source_times) == len(source_temperatures) == len(source_knots) == len(times))
        or times != source_times
        or temperatures != source_temperatures
    ):
        return Calculation(status="needs_data", values={
            "upstream_saturation_history_sha256": upstream_digest,
            "reason": "saturation_history_knots_or_nested_equilibrium_provenance_are_missing_or_misaligned",
        })
    if len(kinetics_request.intervals) != len(times) - 1:
        return Calculation(status="needs_data", values={
            "upstream_saturation_history_sha256": upstream_digest,
            "reason": "kinetic_intervals_must_span_each_adjacent_saturation_knot_pair",
            "required_interval_count": len(times) - 1,
            "provided_interval_count": len(kinetics_request.intervals),
        })
    if temperature_knot_mapping_reviewed and temperatures[0] != kinetics_request.temperature_K:
        return Calculation(status="needs_data", values={
            "upstream_saturation_history_sha256": upstream_digest,
            "reason": "kinetic_reference_temperature_must_match_initial_history_knot",
            "initial_history_temperature_K": temperatures[0],
            "kinetic_temperature_K": kinetics_request.temperature_K,
        })
    if any(value != kinetics_request.temperature_K for value in temperatures) and not temperature_knot_mapping_reviewed:
        return Calculation(status="needs_data", values={
            "upstream_saturation_history_sha256": upstream_digest,
            "reason": "varying_history_temperature_requires_explicit_knot_mapping_review",
            "history_temperatures_K": temperatures,
        })
    ratios: list[float] = []
    for index, row in enumerate(rows):
        source_row = source_knots[index]
        source_calculation = source_row.get("calculation") if isinstance(source_row, dict) else None
        source_knot_digest = canonical_digest(source_calculation) if isinstance(source_calculation, dict) else None
        if (
            not isinstance(row, dict)
            or row.get("time_s") != times[index]
            or row.get("temperature_K") != temperatures[index]
            or row.get("status") != "computed"
            or row.get("upstream_knot_sha256") != source_knot_digest
        ):
            return Calculation(status="needs_data", values={
                "upstream_saturation_history_sha256": upstream_digest,
                "reason": "saturation_knot_is_not_computed_or_clock_aligned",
                "knot_index": index,
            })
        try:
            screen = Calculation.model_validate(row.get("screen"))
        except (ValidationError, TypeError, ValueError):
            screen = None
        candidates = screen.values.get("candidate_results") if isinstance(screen, Calculation) else None
        matches = [item for item in candidates if isinstance(item, dict) and item.get("solid_id") == candidate_solid_id] if isinstance(candidates, list) else []
        if (
            not isinstance(screen, Calculation)
            or screen.status != "computed"
            or screen.values.get("upstream_mass_action_result_sha256") != source_knot_digest
            or screen.values.get("temperature_K") != temperatures[index]
            or screen.values.get("solubility_data_digest") != row.get("solubility_data_sha256")
            or len(matches) != 1
        ):
            return Calculation(status="needs_data", values={
                "upstream_saturation_history_sha256": upstream_digest,
                "reason": "selected_solid_is_missing_or_ambiguous_at_saturation_knot",
                "candidate_solid_id": candidate_solid_id,
                "knot_index": index,
            })
        log_ratio = matches[0].get("log10_saturation_ratio")
        if isinstance(log_ratio, bool) or not isinstance(log_ratio, (int, float)) or not math.isfinite(log_ratio):
            return Calculation(status="out_of_scope", values={
                "upstream_saturation_history_sha256": upstream_digest,
                "reason": "saturation_ratio_is_not_finite",
                "candidate_solid_id": candidate_solid_id,
                "knot_index": index,
            })
        if not -300.0 <= log_ratio <= 300.0:
            return Calculation(status="out_of_scope", values={
                "upstream_saturation_history_sha256": upstream_digest,
                "reason": "saturation_ratio_exceeds_supported_float_transfer_range",
                "candidate_solid_id": candidate_solid_id,
                "knot_index": index,
            })
        ratios.append(10.0 ** float(log_ratio))
    if any(
        interval.start_time_s != times[index] or interval.end_time_s != times[index + 1]
        for index, interval in enumerate(kinetics_request.intervals)
    ):
        return Calculation(status="needs_data", values={
            "upstream_saturation_history_sha256": upstream_digest,
            "reason": "kinetic_interval_endpoints_must_exactly_match_saturation_knots",
            "history_times_s": times,
        })
    request_data = kinetics_request.model_dump(mode="json")
    request_data["intervals"] = [
        interval.model_dump(mode="json") | ({
            "saturation_ratio": ratios[index],
            "saturation_ratio_end": ratios[index + 1],
        } | ({"temperature_K": temperatures[index]} if temperature_knot_mapping_reviewed else {}))
        for index, interval in enumerate(kinetics_request.intervals)
    ]
    if temperature_knot_mapping_reviewed:
        request_data["interval_temperature_profile_reviewed"] = True
    try:
        bound_request = CallerSurfaceScaleKinetics.model_validate(request_data)
    except (ValidationError, TypeError, ValueError) as exc:
        return Calculation(status="needs_data", values={
            "upstream_saturation_history_sha256": upstream_digest,
            "reason": "chemistry_bound_kinetic_request_failed_contract_validation",
            "validation_error": str(exc),
        })
    result = caller_surface_scale_kinetics(bound_request)
    return Calculation(status=result.status, values=result.values | {
        "upstream_saturation_history_sha256": upstream_digest,
        "upstream_saturation_history_input_digest": saturation_history.input_digest,
        "upstream_saturation_history_id": values.get("history_id"),
        "candidate_solid_id": candidate_solid_id,
        "saturation_history_times_s": times,
        "saturation_history_temperatures_K": temperatures,
        "saturation_ratios_from_upstream": ratios,
        "temperature_knot_mapping_reviewed": temperature_knot_mapping_reviewed,
        "saturation_knot_screen_digests": [canonical_digest(row["screen"]) for row in rows],
        "chemistry_to_kinetics_mapping": "exact adjacent history knots; caller-calibrated kinetic coefficients unchanged",
    }, notes=(
        "Only the selected candidate solid's digest-pinned saturation-ratio history is transferred; empirical kinetic parameters remain caller supplied.",
        *result.notes,
    ))


class AqueousSaturationToSurfaceScaleKinetics(Contract):
    assessment_id: str = Field(min_length=1)
    saturation_history: AssessmentResult
    saturation_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    candidate_solid_id: str = Field(min_length=1)
    kinetics_request: CallerSurfaceScaleKinetics
    coverage_kinetics_request: CallerScaleCoverageKinetics | None = None
    temperature_knot_mapping_reviewed: bool = False


def aqueous_saturation_to_surface_scale_kinetics(
    x: AqueousSaturationToSurfaceScaleKinetics,
) -> Calculation:
    result = run_surface_scale_kinetics_from_saturation_history(
        x.saturation_history,
        saturation_history_sha256=x.saturation_history_sha256,
        candidate_solid_id=x.candidate_solid_id,
        kinetics_request=x.kinetics_request,
        temperature_knot_mapping_reviewed=x.temperature_knot_mapping_reviewed,
    )
    if x.coverage_kinetics_request is None or result.status != "computed":
        return Calculation(status=result.status, values={"assessment_id": x.assessment_id, **result.values}, notes=result.notes)
    coverage_request = x.coverage_kinetics_request
    coverage_base = {
        "candidate_solid_id": x.candidate_solid_id,
        "coverage_kinetic_input_sha256": canonical_digest(coverage_request.model_dump(mode="json")),
    }
    times = result.values["saturation_history_times_s"]
    temperatures = result.values["saturation_history_temperatures_K"]
    ratios = result.values["saturation_ratios_from_upstream"]
    if (
        coverage_request.scale_phase_id != x.candidate_solid_id
        or coverage_request.physical_scope_id != x.kinetics_request.physical_scope_id
        or coverage_request.substrate_condition_id != x.kinetics_request.substrate_condition_id
        or coverage_request.solution_condition_id != x.kinetics_request.solution_condition_id
        or coverage_request.physical_specimen_id != x.kinetics_request.physical_specimen_id
    ):
        coverage = Calculation(status="needs_data", values=coverage_base | {
            "reason": "coverage_and_thickness_kinetics_phase_or_physical_identity_mismatch",
        })
    elif (
        (x.temperature_knot_mapping_reviewed and temperatures[0] != coverage_request.temperature_K)
        or (not x.temperature_knot_mapping_reviewed and any(
            temperature != coverage_request.temperature_K for temperature in temperatures
        ))
    ):
        coverage = Calculation(status="needs_data", values=coverage_base | {
            "reason": "coverage_temperature_must_match_the_initial_history_knot_and_reviewed_knot_mapping",
            "history_temperatures_K": temperatures,
            "coverage_temperature_K": coverage_request.temperature_K,
        })
    elif len(coverage_request.intervals) != len(times) - 1 or any(
        interval.start_time_s != times[index] or interval.end_time_s != times[index + 1]
        for index, interval in enumerate(coverage_request.intervals)
    ):
        coverage = Calculation(status="needs_data", values=coverage_base | {
            "reason": "coverage_intervals_must_match_every_adjacent_aqueous_history_knot",
            "history_times_s": times,
        })
    else:
        coverage_data = coverage_request.model_dump(mode="json")
        coverage_data["intervals"] = [
            interval.model_dump(mode="json") | ({
                "saturation_ratio": ratios[index],
                "saturation_ratio_end": ratios[index + 1],
            } | ({"temperature_K": temperatures[index]} if x.temperature_knot_mapping_reviewed else {}))
            for index, interval in enumerate(coverage_request.intervals)
        ]
        if x.temperature_knot_mapping_reviewed:
            coverage_data["interval_temperature_profile_reviewed"] = True
        try:
            bound_coverage_request = CallerScaleCoverageKinetics.model_validate(coverage_data)
            coverage_result = caller_scale_coverage_kinetics(bound_coverage_request)
            coverage = Calculation(status=coverage_result.status, values=coverage_result.values | {
                "upstream_saturation_history_sha256": result.values["upstream_saturation_history_sha256"],
                "candidate_solid_id": x.candidate_solid_id,
                "saturation_history_times_s": times,
                "saturation_history_temperatures_K": temperatures,
            }, notes=coverage_result.notes)
        except (ValidationError, TypeError, ValueError) as exc:
            coverage = Calculation(status="needs_data", values=coverage_base | {
                "reason": "chemistry_bound_coverage_request_failed_contract_validation",
                "validation_error": str(exc),
            })
    status = "computed" if coverage.status == "computed" else coverage.status
    return Calculation(status=status, values={
        "assessment_id": x.assessment_id,
        **result.values,
        "area_average_coverage_kinetics": coverage.model_dump(mode="json"),
        "thickness_and_coverage_coupling": "independent laws share only the selected saturation history; evolving thickness does not modify coverage or transport",
    }, notes=result.notes)


def _validate_saturation_kinetics_context(
    x: AqueousSaturationToSurfaceScaleKinetics, context: RunContext,
) -> None:
    source = x.saturation_history.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis
    ):
        raise ValueError("integration RunContext must match saturation-history asset/location/time identities")


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            "integration.aqueous_saturation_to_surface_scale_kinetics",
            AqueousSaturationToSurfaceScaleKinetics,
            aqueous_saturation_to_surface_scale_kinetics,
            {
                "temperature_K": "K",
                "scale_history[].temperature_K": "K",
                "scale_history[].saturation_ratio": "1",
                "area_average_coverage_kinetics.values.scale_history[].covered_area_fraction": "1",
                "area_average_coverage_kinetics.values.final_covered_area_fraction": "1",
            },
            (
                "Transfers one caller-selected solid saturation-ratio history from exact digest-pinned aqueous equilibrium knots to an explicit single-phase scale-thickness law and optionally an area-average coverage law.",
                "Thickness and coverage laws remain independent and share only the selected saturation trajectory. Kinetic coefficients, phase identity, scale molar volume and applicability remain caller supplied and reviewed; no phase discovery, chemistry-derived rate law, feedback coupling or corrosion qualification is inferred.",
            ),
            ("caller_aqueous_saturation_to_surface_scale_kinetics",),
            qualification="user_model",
            context_validator=_validate_saturation_kinetics_context,
        ),
        ModelSpec(
            "chemistry.caller_surface_scale_kinetics",
            CallerSurfaceScaleKinetics,
            caller_surface_scale_kinetics,
            {
                "temperature_K": "K",
                "rate_reference_temperature_K": "K",
                "minimum_rate_valid_temperature_K": "K",
                "maximum_rate_valid_temperature_K": "K",
                "initial_scale_thickness_m": "m",
                "precipitation_rate_constant_mol_m2_s": "mol/m2/s",
                "effective_precipitation_rate_constant_at_temperature_mol_m2_s": "mol/m2/s",
                "precipitation_activation_energy_J_mol": "J/mol",
                "dissolution_rate_constant_mol_m2_s": "mol/m2/s",
                "effective_dissolution_rate_constant_at_temperature_mol_m2_s": "mol/m2/s",
                "dissolution_activation_energy_J_mol": "J/mol",
                "final_scale_thickness_m": "m",
                "scale_history[].time_s": "s",
                "scale_history[].saturation_ratio": "1",
                "scale_history[].precipitation_flux_mol_m2_s": "mol/m2/s",
                "scale_history[].dissolution_flux_mol_m2_s": "mol/m2/s",
                "scale_history[].precipitated_mol_m2": "mol/m2",
                "scale_history[].dissolved_mol_m2": "mol/m2",
                "scale_history[].scale_thickness_m": "m",
                "scale_history[].cumulative_precipitated_mol_m2": "mol/m2",
                "scale_history[].cumulative_dissolved_mol_m2": "mol/m2",
                "cumulative_precipitated_mol_m2": "mol/m2",
                "cumulative_dissolved_mol_m2": "mol/m2",
            },
            (
                "Integrate caller-calibrated single-phase precipitation and dissolution flux laws over constant or explicitly reviewed linear saturation intervals, with inventory-bounded dissolution.",
                "Caller supplies phase identity, condition-specific rate constants, reaction orders, molar volume and saturation history; linear positive-part power exposure is integrated analytically, and optional Arrhenius scaling is bounded by explicit temperature support and review. The uniform-layer thickness is descriptive and confers no protective credit.",
            ),
            ("caller_surface_scale_kinetic_balance", "arrhenius_kinetics"),
            qualification="user_model",
        )
    ]
