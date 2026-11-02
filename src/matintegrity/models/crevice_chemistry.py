"""Evidence-bounded crevice species inventory accounting.

Species source rates are supplied by an external transport or reaction provider.
This module integrates those rates and checks inventory and charge bookkeeping;
it does not generate electrochemical kinetics, activities, pH or susceptibility.
"""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec

_CONDITION_BOUNDARY_RTOL = 1e-12
_TEMPERATURE_BOUNDARY_ATOL_K = 1e-12
_GAP_BOUNDARY_ATOL_M = 1e-15


class CreviceSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: int
    initial_amount_mol: Nonnegative
    species_definition: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CreviceRateSupport(Contract):
    support_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    bulk_solution_id: str = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_gap_m: Positive
    maximum_gap_m: Positive
    rate_provider_id: str = Field(min_length=1)
    rate_provider_version: str = Field(min_length=1)
    rate_provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    supported_species_ids: tuple[str, ...] = Field(min_length=1)
    maximum_absolute_charge_imbalance_mol_charge: Nonnegative
    calibration_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_support(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("crevice temperature support must be ordered")
        if self.maximum_gap_m < self.minimum_gap_m:
            raise ValueError("crevice gap support must be ordered")
        if len(set(self.supported_species_ids)) != len(self.supported_species_ids):
            raise ValueError("crevice supported species IDs must be unique")
        return self


class CreviceSpeciesRateInterval(Contract):
    interval_id: str = Field(min_length=1)
    support_id: str = Field(min_length=1)
    temperature_K: Positive
    gap_m: Positive
    end_temperature_K: Positive | None = None
    end_gap_m: Positive | None = None
    linear_condition_interpolation_reviewed: bool = False
    boundary_condition_jump_reviewed: bool = False
    net_species_source_mol_s: dict[str, float] = Field(min_length=1)
    net_species_source_end_mol_s: dict[str, float] | None = None
    linear_rate_interpolation_reviewed: bool = False
    provider_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_rate_record(self):
        endpoint_conditions_supplied = self.end_temperature_K is not None and self.end_gap_m is not None
        if (self.end_temperature_K is None) != (self.end_gap_m is None):
            raise ValueError("crevice endpoint conditions require both temperature and gap")
        if endpoint_conditions_supplied != self.linear_condition_interpolation_reviewed:
            raise ValueError("linear condition interpolation requires endpoint values and explicit review")
        if any(not species_id for species_id in self.net_species_source_mol_s):
            raise ValueError("crevice rate species IDs cannot be empty")
        if any(not math.isfinite(rate) for rate in self.net_species_source_mol_s.values()):
            raise ValueError("crevice interval start rates must be finite")
        if self.net_species_source_end_mol_s is not None:
            if set(self.net_species_source_end_mol_s) != set(self.net_species_source_mol_s):
                raise ValueError("crevice interval endpoint rates must match the start species exactly")
            if any(not math.isfinite(rate) for rate in self.net_species_source_end_mol_s.values()):
                raise ValueError("crevice interval endpoint rates must be finite")
            if not self.linear_rate_interpolation_reviewed:
                raise ValueError("linear rate interpolation requires explicit review")
        elif self.linear_rate_interpolation_reviewed:
            raise ValueError("linear rate interpolation review requires endpoint rates")
        if self.record_valid and self.provider_record_digest is None:
            raise ValueError("a valid crevice rate record requires a provider digest")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid crevice rate record requires a basis")
        return self


class CreviceSpeciesInventoryHistory(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    bulk_solution_id: str = Field(min_length=1)
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=5000)
    crevice_solution_volume_m3: tuple[Positive, ...] = Field(min_length=2, max_length=5000)
    species: tuple[CreviceSpecies, ...] = Field(min_length=1)
    rate_intervals: tuple[CreviceSpeciesRateInterval, ...] = Field(min_length=1)
    rate_supports: tuple[CreviceRateSupport, ...] = Field(min_length=1)
    geometry_and_volume_history_reviewed: bool
    material_and_bulk_solution_identity_reviewed: bool
    species_definitions_and_initial_inventory_reviewed: bool
    temperature_and_gap_history_reviewed: bool
    rate_provider_and_calibration_reviewed: bool
    clock_and_interval_alignment_reviewed: bool
    charge_balance_tolerance_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_unique_history(self):
        count = len(self.elapsed_time_s)
        if len(self.crevice_solution_volume_m3) != count:
            raise ValueError("crevice volume history must align to the clock")
        if len(self.rate_intervals) != count - 1:
            raise ValueError("one crevice rate record is required per time interval")
        if any(
            right <= left for left, right in zip(self.elapsed_time_s, self.elapsed_time_s[1:], strict=False)
        ):
            raise ValueError("crevice history clock must strictly increase")
        for values, label in (
            ([row.species_id for row in self.species], "crevice species"),
            ([row.interval_id for row in self.rate_intervals], "crevice interval"),
            ([row.support_id for row in self.rate_supports], "crevice support"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        species_ids = {row.species_id for row in self.species}
        for interval in self.rate_intervals:
            if set(interval.net_species_source_mol_s) != species_ids:
                raise ValueError("each crevice interval must provide exactly every declared species rate")
        if self.rate_intervals[0].boundary_condition_jump_reviewed:
            raise ValueError("the first crevice interval has no preceding boundary condition to review")
        for index in range(1, len(self.rate_intervals)):
            previous = self.rate_intervals[index - 1]
            current = self.rate_intervals[index]
            previous_end_temperature = previous.end_temperature_K or previous.temperature_K
            previous_end_gap = previous.end_gap_m or previous.gap_m
            temperature_jump = not math.isclose(
                previous_end_temperature,
                current.temperature_K,
                rel_tol=_CONDITION_BOUNDARY_RTOL,
                abs_tol=_TEMPERATURE_BOUNDARY_ATOL_K,
            )
            gap_jump = not math.isclose(
                previous_end_gap,
                current.gap_m,
                rel_tol=_CONDITION_BOUNDARY_RTOL,
                abs_tol=_GAP_BOUNDARY_ATOL_M,
            )
            if (temperature_jump or gap_jump) and not current.boundary_condition_jump_reviewed:
                raise ValueError(
                    "a discontinuous interval-boundary temperature or gap requires explicit review"
                )
        return self


def crevice_species_inventory_history(x: CreviceSpeciesInventoryHistory) -> Calculation:
    support_by_id = {row.support_id: row for row in x.rate_supports}
    condition_history = []
    for index, interval in enumerate(x.rate_intervals):
        support = support_by_id.get(interval.support_id)
        end_temperature = interval.end_temperature_K or interval.temperature_K
        end_gap = interval.end_gap_m or interval.gap_m
        mean_temperature = math.fsum((0.5 * interval.temperature_K, 0.5 * end_temperature))
        mean_gap = math.fsum((0.5 * interval.gap_m, 0.5 * end_gap))
        condition_history.append({
            "interval_index": index,
            "interval_id": interval.interval_id,
            "support_id": interval.support_id,
            "start_time_s": x.elapsed_time_s[index],
            "end_time_s": x.elapsed_time_s[index + 1],
            "start_temperature_K": interval.temperature_K,
            "end_temperature_K": end_temperature,
            "temperature_change_K": end_temperature - interval.temperature_K,
            "time_average_temperature_K": mean_temperature,
            "start_gap_m": interval.gap_m,
            "end_gap_m": end_gap,
            "gap_change_m": end_gap - interval.gap_m,
            "time_average_gap_m": mean_gap,
            "linear_condition_interpolation_reviewed": interval.linear_condition_interpolation_reviewed,
            "boundary_condition_jump_reviewed": interval.boundary_condition_jump_reviewed,
            "rate_provider_id": None if support is None else support.rate_provider_id,
            "rate_provider_version": None if support is None else support.rate_provider_version,
            "rate_provider_state_digest": None if support is None else support.rate_provider_state_digest,
            "provider_record_digest": interval.provider_record_digest,
        })
    condition_knot_history = []
    for knot_index, time_s in enumerate(x.elapsed_time_s):
        if knot_index == 0:
            first = x.rate_intervals[0]
            temperature = first.temperature_K
            gap = first.gap_m
            left_temperature = right_temperature = temperature
            left_gap = right_gap = gap
            boundary_jump_reviewed = False
        elif knot_index == len(x.elapsed_time_s) - 1:
            last = x.rate_intervals[-1]
            temperature = last.end_temperature_K or last.temperature_K
            gap = last.end_gap_m or last.gap_m
            left_temperature = right_temperature = temperature
            left_gap = right_gap = gap
            boundary_jump_reviewed = False
        else:
            previous = x.rate_intervals[knot_index - 1]
            following = x.rate_intervals[knot_index]
            left_temperature = previous.end_temperature_K or previous.temperature_K
            right_temperature = following.temperature_K
            left_gap = previous.end_gap_m or previous.gap_m
            right_gap = following.gap_m
            temperature = right_temperature
            gap = right_gap
            boundary_jump_reviewed = following.boundary_condition_jump_reviewed
        temperature_jump = right_temperature - left_temperature
        gap_jump = right_gap - left_gap
        jump_detected = (
            not math.isclose(
                left_temperature,
                right_temperature,
                rel_tol=_CONDITION_BOUNDARY_RTOL,
                abs_tol=_TEMPERATURE_BOUNDARY_ATOL_K,
            )
            or not math.isclose(
                left_gap,
                right_gap,
                rel_tol=_CONDITION_BOUNDARY_RTOL,
                abs_tol=_GAP_BOUNDARY_ATOL_M,
            )
        )
        condition_knot_history.append({
            "knot_index": knot_index,
            "time_s": time_s,
            "temperature_K": temperature,
            "gap_m": gap,
            "left_temperature_K": left_temperature,
            "right_temperature_K": right_temperature,
            "temperature_boundary_jump_K": temperature_jump,
            "left_gap_m": left_gap,
            "right_gap_m": right_gap,
            "gap_boundary_jump_m": gap_jump,
            "boundary_jump_detected": jump_detected,
            "boundary_condition_jump_reviewed": boundary_jump_reviewed,
            "condition_boundary_comparison_rtol": _CONDITION_BOUNDARY_RTOL,
            "temperature_boundary_comparison_atol_K": _TEMPERATURE_BOUNDARY_ATOL_K,
            "gap_boundary_comparison_atol_m": _GAP_BOUNDARY_ATOL_M,
        })
    inventory_lineage = {
        "initial_inventory_sha256": canonical_digest([
            {
                "species_id": row.species_id,
                "charge_number": row.charge_number,
                "initial_amount_mol": row.initial_amount_mol,
            }
            for row in x.species
        ]),
        "solution_volume_history_sha256": canonical_digest({
            "elapsed_time_s": list(x.elapsed_time_s),
            "crevice_solution_volume_m3": list(x.crevice_solution_volume_m3),
        }),
        "rate_interval_ledger_sha256": canonical_digest([
            {
                "interval_index": index,
                "start_time_s": x.elapsed_time_s[index],
                "end_time_s": x.elapsed_time_s[index + 1],
                "interval": row.model_dump(mode="json"),
            }
            for index, row in enumerate(x.rate_intervals)
        ]),
        "rate_support_ledger_sha256": canonical_digest([
            row.model_dump(mode="json") for row in x.rate_supports
        ]),
        "condition_history": condition_history,
        "condition_history_sha256": canonical_digest(condition_history),
        "condition_knot_history": condition_knot_history,
        "condition_knot_history_sha256": canonical_digest(condition_knot_history),
        "condition_boundary_comparison_tolerances": {
            "relative_tolerance": _CONDITION_BOUNDARY_RTOL,
            "temperature_absolute_tolerance_K": _TEMPERATURE_BOUNDARY_ATOL_K,
            "gap_absolute_tolerance_m": _GAP_BOUNDARY_ATOL_M,
        },
    }
    inventory_lineage["inventory_lineage_sha256"] = canonical_digest(inventory_lineage)
    missing_reviews = [
        name
        for name in (
            "geometry_and_volume_history_reviewed",
            "material_and_bulk_solution_identity_reviewed",
            "species_definitions_and_initial_inventory_reviewed",
            "temperature_and_gap_history_reviewed",
            "rate_provider_and_calibration_reviewed",
            "clock_and_interval_alignment_reviewed",
            "charge_balance_tolerance_reviewed",
        )
        if not getattr(x, name)
    ]
    supports = support_by_id
    species_ids = [row.species_id for row in x.species]
    interval_diagnostics = []
    invalid_interval_ids = []
    outside_support_interval_ids = []
    for index, interval in enumerate(x.rate_intervals):
        support = supports.get(interval.support_id)
        interval_input_sha256 = canonical_digest({
            "start_time_s": x.elapsed_time_s[index],
            "end_time_s": x.elapsed_time_s[index + 1],
            "interval": interval.model_dump(mode="json"),
        })
        condition_record_sha256 = canonical_digest(condition_history[index])
        if support is None:
            invalid_interval_ids.append(interval.interval_id)
            interval_diagnostics.append(
                {
                    "interval_index": index,
                    "interval_id": interval.interval_id,
                    "support_id": interval.support_id,
                    "support_found": False,
                    "start_time_s": x.elapsed_time_s[index],
                    "end_time_s": x.elapsed_time_s[index + 1],
                    "condition_history_record_sha256": condition_record_sha256,
                    "rate_interval_input_sha256": interval_input_sha256,
                    "provider_record_digest": interval.provider_record_digest,
                    "preflight_status": "missing_rate_support",
                }
            )
            continue
        identity_matches = (
            support.material_condition_id == x.material_condition_id
            and support.bulk_solution_id == x.bulk_solution_id
            and set(support.supported_species_ids) == set(species_ids)
        )
        start_within_temperature_support = (
            support.minimum_temperature_K <= interval.temperature_K <= support.maximum_temperature_K
        )
        end_temperature = interval.end_temperature_K or interval.temperature_K
        start_within_gap_support = support.minimum_gap_m <= interval.gap_m <= support.maximum_gap_m
        end_gap = interval.end_gap_m or interval.gap_m
        end_within_temperature_support = (
            support.minimum_temperature_K <= end_temperature <= support.maximum_temperature_K
        )
        end_within_gap_support = support.minimum_gap_m <= end_gap <= support.maximum_gap_m
        within_ranges = all((
            start_within_temperature_support,
            end_within_temperature_support,
            start_within_gap_support,
            end_within_gap_support,
        ))
        record_valid = interval.record_valid and interval.provider_record_digest is not None
        interval_diagnostics.append(
            {
                "interval_index": index,
                "interval_id": interval.interval_id,
                "support_id": interval.support_id,
                "support_found": True,
                "identity_matches": identity_matches,
                "within_temperature_and_gap_support": within_ranges,
                "start_within_temperature_support": start_within_temperature_support,
                "end_within_temperature_support": end_within_temperature_support,
                "start_within_gap_support": start_within_gap_support,
                "end_within_gap_support": end_within_gap_support,
                "rate_record_valid": record_valid,
                "rate_provider_id": support.rate_provider_id,
                "rate_provider_version": support.rate_provider_version,
                "rate_provider_state_digest": support.rate_provider_state_digest,
                "provider_record_digest": interval.provider_record_digest,
                "start_time_s": x.elapsed_time_s[index],
                "end_time_s": x.elapsed_time_s[index + 1],
                "condition_history_record_sha256": condition_record_sha256,
                "rate_interval_input_sha256": interval_input_sha256,
                "start_temperature_K": interval.temperature_K,
                "end_temperature_K": end_temperature,
                "start_gap_m": interval.gap_m,
                "end_gap_m": end_gap,
                "linear_condition_interpolation_reviewed": interval.linear_condition_interpolation_reviewed,
                "rate_interpolation": (
                    "piecewise_linear_between_interval_endpoints"
                    if interval.net_species_source_end_mol_s is not None
                    else "constant_over_interval"
                ),
                "linear_rate_interpolation_reviewed": interval.linear_rate_interpolation_reviewed,
                "preflight_status": (
                    "invalid_identity_or_provider_record"
                    if not identity_matches or not record_valid
                    else "outside_declared_support"
                    if not within_ranges
                    else "preflight_passed"
                ),
            }
        )
        if not identity_matches or not record_valid:
            invalid_interval_ids.append(interval.interval_id)
        elif not within_ranges:
            outside_support_interval_ids.append(interval.interval_id)

    if missing_reviews or invalid_interval_ids:
        preflight_ledger_sha256 = canonical_digest(interval_diagnostics)
        return Calculation(
            status="needs_data",
            values={
                "history_id": x.history_id,
                **inventory_lineage,
                "interval_diagnostics": interval_diagnostics,
                "preflight_interval_ledger_sha256": preflight_ledger_sha256,
                "failed_preflight_interval_ids": invalid_interval_ids,
                "invalid_interval_ids": invalid_interval_ids,
                "outside_support_interval_ids": outside_support_interval_ids,
                "missing_reviews": missing_reviews,
            },
            notes=("No inventory history is emitted until all rate records and reviews are complete.",),
        )
    if outside_support_interval_ids:
        preflight_ledger_sha256 = canonical_digest(interval_diagnostics)
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                **inventory_lineage,
                "interval_diagnostics": interval_diagnostics,
                "preflight_interval_ledger_sha256": preflight_ledger_sha256,
                "failed_preflight_interval_ids": outside_support_interval_ids,
                "invalid_interval_ids": [],
                "outside_support_interval_ids": outside_support_interval_ids,
                "missing_reviews": [],
            },
            notes=("No rate is extrapolated outside the caller-declared temperature or gap support.",),
        )

    amounts = {row.species_id: [row.initial_amount_mol] for row in x.species}
    interval_amount_changes = []
    interval_rate_diagnostics = []
    negative_inventory_records = []
    nonfinite_inventory_records = []
    failed_interval_id = None
    for index, interval in enumerate(x.rate_intervals):
        duration = x.elapsed_time_s[index + 1] - x.elapsed_time_s[index]
        changes = {}
        integrated_rates = {}
        proposed_amounts = {}
        for species_id in species_ids:
            start_rate = interval.net_species_source_mol_s[species_id]
            end_rates = interval.net_species_source_end_mol_s
            end_rate = start_rate if end_rates is None else end_rates[species_id]
            mean_rate = math.fsum((0.5 * start_rate, 0.5 * end_rate))
            change = mean_rate * duration
            next_amount = amounts[species_id][-1] + change
            finite_increment = math.isfinite(change) and math.isfinite(next_amount)
            changes[species_id] = change if finite_increment else None
            integrated_rates[species_id] = {
                "start_mol_s": start_rate,
                "end_mol_s": end_rate,
                "time_average_mol_s": mean_rate,
                "integrated_amount_change_mol": change if math.isfinite(change) else None,
            }
            if finite_increment:
                proposed_amounts[species_id] = next_amount
            if not math.isfinite(mean_rate) or not finite_increment:
                nonfinite_inventory_records.append(f"{interval.interval_id}:{species_id}")
            if next_amount < -1e-15:
                negative_inventory_records.append(f"{interval.interval_id}:{species_id}")
        interval_amount_changes.append(changes)
        support = supports[interval.support_id]
        interval_rate_diagnostics.append({
            "interval_index": index,
            "interval_id": interval.interval_id,
            "support_id": interval.support_id,
            "duration_s": duration,
            "rate_provider_id": support.rate_provider_id,
            "rate_provider_version": support.rate_provider_version,
            "rate_provider_state_digest": support.rate_provider_state_digest,
            "provider_record_digest": interval.provider_record_digest,
            "condition_history_record_sha256": canonical_digest(condition_history[index]),
            "rate_interval_input_sha256": canonical_digest({
                "start_time_s": x.elapsed_time_s[index],
                "end_time_s": x.elapsed_time_s[index + 1],
                "interval": interval.model_dump(mode="json"),
            }),
            "rate_interpolation": (
                "piecewise_linear_between_interval_endpoints"
                if interval.net_species_source_end_mol_s is not None
                else "constant_over_interval"
            ),
            "species_rate_basis": integrated_rates,
        })
        if nonfinite_inventory_records or negative_inventory_records:
            failed_interval_id = interval.interval_id
            break
        for species_id in species_ids:
            amounts[species_id].append(proposed_amounts[species_id])
    completed_interval_count = len(amounts[species_ids[0]]) - 1
    completed_prefix = {
        "completed_interval_count": completed_interval_count,
        "completed_time_knot_count": completed_interval_count + 1,
        "completed_through_time_s": x.elapsed_time_s[completed_interval_count],
        "completed_species_amount_history_mol": {
            species_id: values for species_id, values in amounts.items()
        },
        "completed_prefix_sha256": canonical_digest({
            "species_amount_history_mol": amounts,
            "elapsed_time_s": list(x.elapsed_time_s[: completed_interval_count + 1]),
        }),
        "interval_rate_diagnostics": interval_rate_diagnostics,
        "interval_rate_diagnostics_sha256": canonical_digest(interval_rate_diagnostics),
        "preflight_interval_ledger_sha256": canonical_digest(interval_diagnostics),
    }
    if nonfinite_inventory_records:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                **inventory_lineage,
                **completed_prefix,
                "failed_interval_id": failed_interval_id,
                "interval_diagnostics": interval_diagnostics,
                "nonfinite_inventory_records": nonfinite_inventory_records,
                "interval_amount_change_mol": interval_amount_changes,
                "interval_rate_diagnostics": interval_rate_diagnostics,
            },
            notes=("Rate integration exceeded finite numerical support; affected amount increments are withheld and no inventory is clipped or renormalized.",),
        )
    if negative_inventory_records:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                **inventory_lineage,
                **completed_prefix,
                "failed_interval_id": failed_interval_id,
                "interval_diagnostics": interval_diagnostics,
                "negative_inventory_records": negative_inventory_records,
                "interval_amount_change_mol": interval_amount_changes,
                "interval_rate_diagnostics": interval_rate_diagnostics,
            },
            notes=(
                "Provider rates create negative species inventory; values are not clipped or renormalized.",
            ),
        )

    concentrations = {}
    nonfinite_concentration_records = []
    for species_id, values in amounts.items():
        concentrations[species_id] = []
        for time_index, (amount, volume) in enumerate(
            zip(values, x.crevice_solution_volume_m3, strict=True)
        ):
            concentration = amount / volume
            if not math.isfinite(concentration):
                nonfinite_concentration_records.append(f"{time_index}:{species_id}")
            concentrations[species_id].append(concentration)
    if nonfinite_concentration_records:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                **inventory_lineage,
                **completed_prefix,
                "nonfinite_concentration_records": nonfinite_concentration_records,
                "species_amount_history_mol": amounts,
                "interval_amount_change_mol": interval_amount_changes,
                "interval_rate_diagnostics": interval_rate_diagnostics,
            },
            notes=("Concentration conversion exceeded finite numerical support for the declared volume history.",),
        )

    charge_by_time = []
    nonfinite_charge_times = []
    for time_index in range(len(x.elapsed_time_s)):
        try:
            charge = math.fsum(
                float(row.charge_number) * amounts[row.species_id][time_index]
                for row in x.species
            )
        except (OverflowError, ValueError):
            charge = math.inf
        if not math.isfinite(charge):
            nonfinite_charge_times.append(time_index)
        charge_by_time.append(charge)
    if nonfinite_charge_times:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                **inventory_lineage,
                **completed_prefix,
                "nonfinite_charge_inventory_time_indices": nonfinite_charge_times,
                "species_amount_history_mol": amounts,
                "species_concentration_history_mol_m3": concentrations,
                "interval_amount_change_mol": interval_amount_changes,
                "interval_rate_diagnostics": interval_rate_diagnostics,
            },
            notes=("Charge inventory aggregation exceeded finite numerical support; no imbalance result is reported.",),
        )
    cumulative_net_source = {}
    mass_balance_residual = {}
    cumulative_source_overflow_species = []
    initial_by_species = {row.species_id: row.initial_amount_mol for row in x.species}
    for species_id in species_ids:
        try:
            cumulative = math.fsum(row[species_id] for row in interval_amount_changes)
            residual = math.fsum((amounts[species_id][-1], -initial_by_species[species_id], -cumulative))
        except (OverflowError, ValueError):
            cumulative_source_overflow_species.append(species_id)
            continue
        if not math.isfinite(cumulative) or not math.isfinite(residual):
            cumulative_source_overflow_species.append(species_id)
            continue
        cumulative_net_source[species_id] = cumulative
        mass_balance_residual[species_id] = residual
    if cumulative_source_overflow_species:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": x.history_id,
                **inventory_lineage,
                **completed_prefix,
                "cumulative_source_overflow_species": cumulative_source_overflow_species,
                "species_amount_history_mol": amounts,
                "interval_amount_change_mol": interval_amount_changes,
                "interval_rate_diagnostics": interval_rate_diagnostics,
            },
            notes=("Cumulative source or mass-balance audit exceeded finite numeric support; no aggregate is reported.",),
        )
    interval_state_boundary_ledger = []
    for index, interval in enumerate(x.rate_intervals):
        start_amounts = {species_id: amounts[species_id][index] for species_id in species_ids}
        end_amounts = {species_id: amounts[species_id][index + 1] for species_id in species_ids}
        start_concentrations = {species_id: concentrations[species_id][index] for species_id in species_ids}
        end_concentrations = {species_id: concentrations[species_id][index + 1] for species_id in species_ids}
        interval_state_boundary_ledger.append({
            "interval_index": index,
            "interval_id": interval.interval_id,
            "start_time_s": x.elapsed_time_s[index],
            "end_time_s": x.elapsed_time_s[index + 1],
            "duration_s": x.elapsed_time_s[index + 1] - x.elapsed_time_s[index],
            "start_solution_volume_m3": x.crevice_solution_volume_m3[index],
            "end_solution_volume_m3": x.crevice_solution_volume_m3[index + 1],
            "start_inventory_sha256": canonical_digest(start_amounts),
            "end_inventory_sha256": canonical_digest(end_amounts),
            "start_concentration_sha256": canonical_digest(start_concentrations),
            "end_concentration_sha256": canonical_digest(end_concentrations),
            "integrated_source_sha256": canonical_digest(interval_amount_changes[index]),
        })
    interval_state_boundary_ledger_sha256 = canonical_digest(interval_state_boundary_ledger)
    maximum_tolerance = min(
        supports[interval.support_id].maximum_absolute_charge_imbalance_mol_charge
        for interval in x.rate_intervals
    )
    maximum_imbalance = max(abs(value) for value in charge_by_time)
    charge_ok = maximum_imbalance <= maximum_tolerance
    return Calculation(
        status="computed" if charge_ok else "needs_data",
        values={
            "history_id": x.history_id,
            **inventory_lineage,
            **completed_prefix,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "physical_scope_id": x.physical_scope_id,
            "clock_id": x.clock_id,
            "elapsed_time_s": list(x.elapsed_time_s),
            "species_amount_history_mol": amounts,
            "species_concentration_history_mol_m3": concentrations,
            "interval_amount_change_mol": interval_amount_changes,
            "interval_rate_diagnostics": interval_rate_diagnostics,
            "cumulative_net_species_source_mol": cumulative_net_source,
            "species_inventory_balance_residual_mol": mass_balance_residual,
            "interval_state_boundary_ledger": interval_state_boundary_ledger,
            "interval_state_boundary_ledger_sha256": interval_state_boundary_ledger_sha256,
            "net_charge_inventory_mol_charge": charge_by_time,
            "maximum_absolute_charge_imbalance_mol_charge": maximum_imbalance,
            "caller_charge_imbalance_tolerance_mol_charge": maximum_tolerance,
            "charge_balance_within_caller_tolerance": charge_ok,
            "interval_diagnostics": interval_diagnostics,
            "negative_inventory_records": [],
            "missing_reviews": [],
        },
        notes=(
            "Each interval integrates an externally supplied constant rate or an explicitly reviewed linear start-to-end rate history; no kinetic rate is generated by this bookkeeping model.",
            "Prescribed volume changes alter concentration but do not create or remove species inventory in this bookkeeping model.",
            "Activities, pH, electrochemical potential, precipitation, susceptibility, damage, life, probability and acceptance remain external.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("crevice history asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.crevice_species_inventory_history",
            CreviceSpeciesInventoryHistory,
            crevice_species_inventory_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "clock_id": "1",
                "elapsed_time_s": "s",
                "species_amount_history_mol": "mol",
                "species_concentration_history_mol_m3": "mol/m^3",
                "interval_amount_change_mol": "mol",
                "net_charge_inventory_mol_charge": "mol-charge",
                "maximum_absolute_charge_imbalance_mol_charge": "mol-charge",
                "caller_charge_imbalance_tolerance_mol_charge": "mol-charge",
                "charge_balance_within_caller_tolerance": "1",
                "interval_diagnostics": "mixed",
                "interval_rate_diagnostics": "mixed",
                "interval_rate_diagnostics_sha256": "1",
                "negative_inventory_records": "1",
                "nonfinite_inventory_records": "1",
                "nonfinite_concentration_records": "1",
                "nonfinite_charge_inventory_time_indices": "1",
                "initial_inventory_sha256": "1",
                "solution_volume_history_sha256": "1",
                "rate_interval_ledger_sha256": "1",
                "rate_support_ledger_sha256": "1",
                "condition_history": "mixed",
                "condition_history_sha256": "1",
                "condition_knot_history": "mixed",
                "condition_knot_history_sha256": "1",
                "condition_boundary_comparison_tolerances": "mixed",
                "inventory_lineage_sha256": "1",
                "cumulative_net_species_source_mol": "mol",
                "species_inventory_balance_residual_mol": "mol",
                "cumulative_source_overflow_species": "1",
                "interval_state_boundary_ledger": "mixed",
                "interval_state_boundary_ledger_sha256": "1",
                "completed_interval_count": "1",
                "completed_time_knot_count": "1",
                "completed_through_time_s": "s",
                "completed_species_amount_history_mol": "mol",
                "completed_prefix_sha256": "1",
                "failed_interval_id": "1",
                "missing_reviews": "1",
            },
            (
                "Geometry, volumes, species definitions, initial inventories and interval source rates are reviewed caller inputs.",
                "Rate-provider support matches exact material, bulk solution, species, temperature and gap identities.",
                "Net species source rates include every provider-selected transport and reaction term. Rates are constant unless a start/end pair and explicit linear interpolation review are provided; then trapezoidal integration is exact for the declared linear history.",
            ),
            ("external_crevice_species_rate_inventory_accounting",),
            context_validator=same_identity,
        )
    ]
