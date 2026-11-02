"""Caller-parameterized nucleation and growth for a closed crevice batch."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .multiphase_kinetic_ledger import (
    CompetingSolidKineticInterval,
    CompetingSolidKineticLedger,
    KineticAqueousSpecies,
    KineticSolidPhase,
    SolidSaturationRateLaw,
    _derive_solid_saturation_rate,
    evaluate_competing_solid_kinetic_ledger,
    validate_neutral_solid_reaction_network,
)
from .registry import ModelSpec

MODEL_ID = "chemistry.crevice_nucleation_kinetic_history"
NUCLEATION_SOURCE_ID = "caller_evidenced_crevice_molar_nucleation_source"
SOURCE_ID = "digest_bound_saturation_nucleation_and_growth_kinetic_history"


class NucleationSaturationInterval(Contract):
    """One exact interval of caller-provided phase saturation ratios."""

    interval_id: str = Field(min_length=1)
    start_time_s: float = Field(ge=0.0)
    end_time_s: Positive
    temperature_K: Positive | None = None
    saturation_ratio_by_phase: dict[str, float] = Field(min_length=2, max_length=16)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_interval_record(self):
        if not math.isfinite(self.start_time_s) or not math.isfinite(self.end_time_s) or self.end_time_s <= self.start_time_s:
            raise ValueError("saturation interval must have finite positive duration")
        if any(not math.isfinite(value) or value < 0 for value in self.saturation_ratio_by_phase.values()):
            raise ValueError("saturation ratios must be finite and nonnegative")
        payload = {
            "interval_id": self.interval_id,
            "start_time_s": self.start_time_s,
            "end_time_s": self.end_time_s,
            "temperature_K": self.temperature_K,
            "saturation_ratio_by_phase": self.saturation_ratio_by_phase,
        }
        if canonical_digest(payload) != self.record_sha256:
            raise ValueError("saturation interval digest mismatch")
        if not any(row.sha256 == self.record_sha256 for row in self.evidence):
            raise ValueError("saturation interval Evidence must pin the exact interval record")
        return self


class CreviceMolarNucleationLaw(Contract):
    """A caller-calibrated phase-appearance source in molar inventory units."""

    solid_species_id: str = Field(min_length=1)
    critical_saturation_ratio: Positive
    source_rate_constant_mol_m3_s: float = Field(ge=0.0)
    supersaturation_order: Positive = Field(le=8.0)
    nucleated_inventory_threshold_mol_m3: Positive
    maximum_rate_mol_m3_s: Positive
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_nucleation_record(self):
        if not math.isfinite(self.source_rate_constant_mol_m3_s):
            raise ValueError("nucleation source rate constant must be finite")
        payload = self.model_dump(mode="json", exclude={"source_sha256", "evidence"})
        if canonical_digest(payload) != self.source_sha256:
            raise ValueError("nucleation source digest mismatch")
        if not any(row.sha256 == self.source_sha256 for row in self.evidence):
            raise ValueError("nucleation Evidence must pin its source record")
        return self


class EvidenceBoundSaturationGrowthLaw(Contract):
    """Existing caller rate law plus Evidence pin for phase growth/dissolution."""

    law: SolidSaturationRateLaw
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def bind_growth_law(self):
        if not any(row.sha256 == self.law.source_sha256 for row in self.evidence):
            raise ValueError("growth-law Evidence must pin its source digest")
        return self


class CreviceNucleationKineticHistoryRequest(Contract):
    schema_version: Literal["matintegrity.crevice_nucleation_kinetic_history.v1"] = "matintegrity.crevice_nucleation_kinetic_history.v1"
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    kinetic_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_parameter_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    temperature_K: Positive
    aqueous_species: tuple[KineticAqueousSpecies, ...] = Field(min_length=2, max_length=64)
    candidate_solid_phases: tuple[KineticSolidPhase, ...] = Field(min_length=2, max_length=16)
    nucleation_laws: tuple[CreviceMolarNucleationLaw, ...] = Field(min_length=2, max_length=16)
    growth_laws: tuple[EvidenceBoundSaturationGrowthLaw, ...] = Field(min_length=2, max_length=16)
    intervals: tuple[NucleationSaturationInterval, ...] = Field(min_length=1, max_length=5000)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=512)
    absolute_balance_tolerance_mol_m3: Positive = 1e-10
    relative_balance_tolerance: float = Field(default=1e-9, gt=0.0, le=0.01)
    maximum_total_nucleation_rate_mol_m3_s: Positive
    maximum_interval_phase_updates: int = Field(default=100_000, ge=1, le=500_000)
    maximum_total_ledger_evaluations: int = Field(default=100_000, ge=1, le=1_000_000)
    maximum_seed_threshold_splits_per_interval: int = Field(default=128, ge=1, le=10_000)
    phase_stoichiometry_and_volume_reviewed: bool
    saturation_source_and_standard_state_reviewed: bool
    nucleation_law_units_threshold_and_support_reviewed: bool
    growth_law_temperature_support_reviewed: bool
    dissolution_then_formation_split_reviewed: bool
    closed_batch_scope_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_history_bindings(self):
        validate_neutral_solid_reaction_network(self.aqueous_species, self.candidate_solid_phases)
        species_ids = tuple(row.species_id for row in self.aqueous_species)
        phase_ids = tuple(row.solid_species_id for row in self.candidate_solid_phases)
        if len(set(species_ids)) != len(species_ids) or len(set(phase_ids)) != len(phase_ids):
            raise ValueError("aqueous species and solid phase IDs must be unique")
        if set(row.solid_species_id for row in self.nucleation_laws) != set(phase_ids) or len(self.nucleation_laws) != len(phase_ids):
            raise ValueError("one nucleation law is required for every declared candidate phase")
        growth_ids = [row.law.solid_species_id for row in self.growth_laws]
        if len(set(growth_ids)) != len(growth_ids) or set(growth_ids) != set(phase_ids):
            raise ValueError("one growth/dissolution law is required for every candidate phase")
        interval_ids = [row.interval_id for row in self.intervals]
        if len(set(interval_ids)) != len(interval_ids):
            raise ValueError("saturation interval IDs must be unique")
        if any(row.end_time_s != self.intervals[i + 1].start_time_s for i, row in enumerate(self.intervals[:-1])):
            raise ValueError("saturation intervals must be contiguous and ordered")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history clock must start at zero")
        for interval in self.intervals:
            if set(interval.saturation_ratio_by_phase) != set(phase_ids):
                raise ValueError("every saturation interval must cover all and only candidate phases")
            if interval.temperature_K is not None and interval.temperature_K != self.temperature_K:
                raise ValueError("this batch implementation requires one exact isothermal temperature")
        if len(self.intervals) * len(phase_ids) > self.maximum_interval_phase_updates:
            raise ValueError("interval/phase update budget exceeded")
        digests = {row.sha256 for row in self.evidence if row.sha256}
        required = {row.source_sha256 for row in self.aqueous_species}
        required.update(row.source_sha256 for row in self.candidate_solid_phases)
        required.update(row.source_sha256 for row in self.nucleation_laws)
        required.update(row.law.source_sha256 for row in self.growth_laws)
        required.update(row.record_sha256 for row in self.intervals)
        required.update((self.kinetic_configuration_sha256, self.kinetic_parameter_source_sha256))
        if not required <= digests:
            raise ValueError("request Evidence must pin every species, phase, law, saturation interval and parameter digest")
        reviews = (
            self.phase_stoichiometry_and_volume_reviewed,
            self.saturation_source_and_standard_state_reviewed,
            self.nucleation_law_units_threshold_and_support_reviewed,
            self.growth_law_temperature_support_reviewed,
            self.dissolution_then_formation_split_reviewed,
            self.closed_batch_scope_reviewed,
            self.computational_use_authorized,
        )
        if not all(reviews):
            raise ValueError("all phase, law, scope and computational-use reviews are required")
        return self


def solve_crevice_nucleation_kinetic_history(request: CreviceNucleationKineticHistoryRequest) -> Calculation:
    """Split each interval at the first seed-inventory threshold crossing."""
    digest = canonical_digest(request.model_dump(mode="json"))
    phases = list(request.candidate_solid_phases)
    concentrations = {row.species_id: float(row.initial_concentration_mol_m3) for row in request.aqueous_species}
    solids = {row.solid_species_id: float(row.initial_solid_moles_per_solution_volume_mol_m3) for row in phases}
    nucleation_law = {row.solid_species_id: row for row in request.nucleation_laws}
    growth_law = {row.law.solid_species_id: row.law for row in request.growth_laws}
    nucleated = {pid: amount >= nucleation_law[pid].nucleated_inventory_threshold_mol_m3 for pid, amount in solids.items()}
    history: list[dict] = [{
        "time_s": 0.0,
        "aqueous_concentration_mol_m3": dict(concentrations),
        "solid_inventory_mol_m3": dict(solids),
        "nucleated_phase": dict(nucleated),
    }]
    max_element_residual = 0.0
    max_charge_residual = 0.0
    max_rate = 0.0
    total_ledger_evaluations = 0
    total_seed_threshold_splits = 0
    interval_records: list[dict] = []

    def interval_rates(interval):
        nonlocal max_rate
        rates: dict[str, float] = {}
        records: dict[str, dict] = {}
        for phase_id in solids:
            saturation = float(interval.saturation_ratio_by_phase[phase_id])
            law = nucleation_law[phase_id]
            if not nucleated[phase_id]:
                driving = max(0.0, saturation / float(law.critical_saturation_ratio) - 1.0)
                rate = float(law.source_rate_constant_mol_m3_s) * driving ** float(law.supersaturation_order)
                if rate > float(law.maximum_rate_mol_m3_s):
                    raise ArithmeticError(f"nucleation rate for {phase_id} exceeds its law-specific bound")
                records[phase_id] = {
                    "mode": "nucleation_source", "saturation_ratio": saturation,
                    "critical_saturation_ratio": float(law.critical_saturation_ratio),
                    "dimensionless_driving": driving, "requested_rate_mol_m3_s": rate,
                    "nucleation_law_sha256": law.source_sha256,
                    "rate_law": "nucleation_molar_source" if rate > 0.0 else "below_nucleation_threshold",
                }
            else:
                derived = _derive_solid_saturation_rate(
                    growth_law[phase_id], saturation, temperature_K=float(interval.temperature_K or request.temperature_K)
                )
                rate = float(derived["signed_extent_rate_mol_m3_s"])
                records[phase_id] = {
                    "mode": "seeded_growth_or_dissolution", **derived,
                    "growth_law_sha256": growth_law[phase_id].source_sha256,
                }
            if not math.isfinite(rate) or abs(rate) > request.maximum_total_nucleation_rate_mol_m3_s:
                raise ArithmeticError(f"phase rate for {phase_id} exceeds the declared total rate bound")
            rates[phase_id] = rate
            max_rate = max(max_rate, abs(rate))
        if math.fsum(abs(value) for value in rates.values()) > request.maximum_total_nucleation_rate_mol_m3_s:
            raise ArithmeticError("summed phase-rate request exceeds the declared total rate bound")
        return rates, records

    def run_ledger(interval, rates, duration_s, segment_label):
        nonlocal total_ledger_evaluations
        if duration_s <= 0.0 or not math.isfinite(duration_s):
            raise ArithmeticError("within-interval segment duration must be finite and positive")
        if total_ledger_evaluations >= request.maximum_total_ledger_evaluations:
            raise RuntimeError("conservative ledger evaluation budget exceeded")
        total_ledger_evaluations += 1
        current_species = tuple(
            row.model_copy(update={"initial_concentration_mol_m3": concentrations[row.species_id]})
            for row in request.aqueous_species
        )
        current_phases = tuple(
            row.model_copy(update={"initial_solid_moles_per_solution_volume_mol_m3": solids[row.solid_species_id]})
            for row in phases
        )
        ledger_request = CompetingSolidKineticLedger(
            assessment_id=f"{request.assessment_id}:{interval.interval_id}:{segment_label}",
            physical_scope_id=request.physical_scope_id,
            provider_id=request.provider_id,
            provider_revision=request.provider_revision,
            kinetic_configuration_sha256=request.kinetic_configuration_sha256,
            kinetic_parameter_source_sha256=request.kinetic_parameter_source_sha256,
            temperature_K=float(interval.temperature_K or request.temperature_K),
            aqueous_species=current_species,
            candidate_solid_phases=current_phases,
            # The reusable ledger is relative-time based; exact elapsed duration is preserved.
            intervals=(CompetingSolidKineticInterval(
                interval_id=f"{interval.interval_id}:{segment_label}",
                start_time_s=0.0,
                end_time_s=float(duration_s),
                phase_extent_rate_mol_m3_s=rates,
            ),),
            absolute_balance_tolerance_mol_m3=request.absolute_balance_tolerance_mol_m3,
            relative_balance_tolerance=request.relative_balance_tolerance,
            phase_stoichiometry_and_solution_volume_reviewed=True,
            caller_rate_law_units_temperature_and_support_reviewed=True,
            dissolution_then_precipitation_split_order_reviewed=True,
            computational_use_authorized=True,
        )
        result = evaluate_competing_solid_kinetic_ledger(ledger_request)
        if result.status != "computed":
            raise ArithmeticError(str(result.values.get("out_of_scope_reason", result.status)))
        return result

    def commit_segment(interval, rates, rate_records, duration_s, elapsed_start_s, label):
        nonlocal concentrations, solids, nucleated, max_element_residual, max_charge_residual
        result = run_ledger(interval, rates, duration_s, label)
        concentrations = dict(result.values["final_aqueous_concentration_mol_m3"])
        solids = dict(result.values["final_solid_inventory_mol_m3"])
        newly_nucleated = [
            pid for pid, amount in solids.items()
            if not nucleated[pid] and amount >= nucleation_law[pid].nucleated_inventory_threshold_mol_m3
        ]
        nucleated = {
            pid: nucleated[pid] or pid in newly_nucleated
            for pid in solids
        }
        final_knot = result.values["history"][-1]
        element_residuals = final_knot["element_balance_residual_mol_m3"]
        charge_residual = final_knot["charge_balance_residual_mol_charge_m3"]
        max_element_residual = max(max_element_residual, max((abs(v) for v in element_residuals.values()), default=0.0))
        max_charge_residual = max(max_charge_residual, abs(float(charge_residual)))
        return {
            "segment_start_time_s": float(elapsed_start_s),
            "segment_end_time_s": float(elapsed_start_s + duration_s),
            "duration_s": float(duration_s),
            "segment_kind": label,
            "rate_law_by_phase": rate_records,
            "requested_phase_extent_rate_mol_m3_s": rates,
            "ledger_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "ledger_result": result.model_dump(mode="json"),
            "aqueous_concentration_mol_m3": concentrations,
            "solid_inventory_mol_m3": solids,
            "nucleated_phase": nucleated,
            "newly_nucleated_phase_ids": newly_nucleated,
            "element_balance_residual_mol_m3": element_residuals,
            "charge_balance_residual_mol_charge_m3": charge_residual,
        }

    try:
        for interval in request.intervals:
            elapsed = float(interval.start_time_s)
            interval_end = float(interval.end_time_s)
            segment_number = 0
            interval_split_count = 0
            segments: list[dict] = []
            crossing_events: list[dict] = []
            while elapsed < interval_end:
                remaining = interval_end - elapsed
                rates, rate_records = interval_rates(interval)
                # Evaluate the full interval once to identify reachable thresholds.
                full_trial = run_ledger(interval, rates, remaining, f"interval{len(history)}_segment{segment_number}_full_trial")
                full_inventory = full_trial.values["final_solid_inventory_mol_m3"]
                candidate_crossings: list[dict] = []
                for phase_id in solids:
                    if nucleated[phase_id] or rates[phase_id] <= 0.0:
                        continue
                    threshold = float(nucleation_law[phase_id].nucleated_inventory_threshold_mol_m3)
                    if float(full_inventory[phase_id]) < threshold:
                        continue
                    # With the interval-constant molar source, the nominal event time
                    # follows directly from inventory deficit divided by source rate.
                    # The conservative ledger below verifies that aqueous-resource
                    # competition did not invalidate this event time.
                    deficit = threshold - float(solids[phase_id])
                    event_time = deficit / float(rates[phase_id])
                    if not math.isfinite(event_time) or event_time <= 0.0:
                        raise ArithmeticError(f"invalid nominal seed event time for {phase_id}")
                    if event_time > remaining:
                        raise ArithmeticError(
                            f"ledger indicates {phase_id} crosses its seed threshold before the interval end, "
                            "but the constant-source event time lies beyond that interval"
                        )
                    candidate_crossings.append({
                        "phase_id": phase_id,
                        "threshold_mol_m3": threshold,
                        "time_offset_s": event_time,
                        "nominal_source_rate_mol_m3_s": float(rates[phase_id]),
                        "nominal_inventory_deficit_mol_m3": deficit,
                    })
                if not candidate_crossings:
                    # Reuse the already evaluated full-remainder result to commit.
                    concentrations = dict(full_trial.values["final_aqueous_concentration_mol_m3"])
                    solids = dict(full_trial.values["final_solid_inventory_mol_m3"])
                    final_knot = full_trial.values["history"][-1]
                    element_residuals = final_knot["element_balance_residual_mol_m3"]
                    charge_residual = final_knot["charge_balance_residual_mol_charge_m3"]
                    max_element_residual = max(max_element_residual, max((abs(v) for v in element_residuals.values()), default=0.0))
                    max_charge_residual = max(max_charge_residual, abs(float(charge_residual)))
                    segments.append({
                        "segment_start_time_s": elapsed,
                        "segment_end_time_s": interval_end,
                        "duration_s": remaining,
                        "segment_kind": "interval_remainder_no_seed_crossing",
                        "rate_law_by_phase": rate_records,
                        "requested_phase_extent_rate_mol_m3_s": rates,
                        "ledger_result_sha256": canonical_digest(full_trial.model_dump(mode="json")),
                        "ledger_result": full_trial.model_dump(mode="json"),
                        "aqueous_concentration_mol_m3": concentrations,
                        "solid_inventory_mol_m3": solids,
                        "nucleated_phase": dict(nucleated),
                        "newly_nucleated_phase_ids": [],
                        "element_balance_residual_mol_m3": element_residuals,
                        "charge_balance_residual_mol_charge_m3": charge_residual,
                    })
                    elapsed = interval_end
                    break

                first = min(candidate_crossings, key=lambda row: row["time_offset_s"])
                if interval_split_count >= min(request.maximum_seed_threshold_splits_per_interval, len(solids)):
                    raise RuntimeError("within-interval seed-threshold split budget exceeded before commit")
                split_duration = float(first["time_offset_s"])
                if split_duration <= 0.0 or split_duration > remaining:
                    raise ArithmeticError("computed seed-threshold split is outside the remaining interval")
                split_trial = run_ledger(interval, rates, split_duration,
                                         f"interval{len(history)}_segment{segment_number}_threshold_trial")
                split_inventory = split_trial.values["final_solid_inventory_mol_m3"]
                crossing_ids = {
                    phase_id for phase_id in solids
                    if not nucleated[phase_id]
                    and float(split_inventory[phase_id]) >= float(nucleation_law[phase_id].nucleated_inventory_threshold_mol_m3)
                }
                if first["phase_id"] not in crossing_ids:
                    raise ArithmeticError(
                        f"nominal seed event for {first['phase_id']} was not attained by the conservative ledger; "
                        "the source rate is resource-limited and no event-time approximation is committed"
                    )
                segment = commit_segment(interval, rates, rate_records, split_duration, elapsed,
                                         f"seed_threshold_crossing_{segment_number}")
                segments.append(segment)
                interval_split_count += 1
                total_seed_threshold_splits += 1
                newly_nucleated = set(segment["newly_nucleated_phase_ids"])
                if not newly_nucleated or first["phase_id"] not in newly_nucleated:
                    raise ArithmeticError("committed threshold substep did not attain its nominal seed event")
                for candidate in candidate_crossings:
                    if candidate["phase_id"] in newly_nucleated and abs(candidate["time_offset_s"] - split_duration) <= max(1e-12, 1e-12 * remaining):
                        crossing_events.append({
                            **candidate,
                            "absolute_crossing_time_s": float(elapsed + split_duration),
                            "time_split_method": "inventory_deficit_divided_by_constant_molar_source_rate",
                            "event_time_error_bound_s": 0.0,
                            "interval_split_ordinal": interval_split_count,
                            "interval_split_budget": min(request.maximum_seed_threshold_splits_per_interval, len(solids)),
                            "ledger_evaluation_count_at_event": total_ledger_evaluations,
                            "ledger_verification_sha256": canonical_digest(split_trial.model_dump(mode="json")),
                            "committed_crossing_result_sha256": segment["ledger_result_sha256"],
                        })
                elapsed += split_duration
                segment_number += 1

            history.append({
                "time_s": interval_end,
                "interval_id": interval.interval_id,
                "saturation_record_sha256": interval.record_sha256,
                "segments": segments,
                "seed_threshold_crossings": crossing_events,
                "aqueous_concentration_mol_m3": dict(concentrations),
                "solid_inventory_mol_m3": dict(solids),
                "nucleated_phase": dict(nucleated),
                "interval_element_balance_residual_max_mol_m3": max(
                    (abs(v) for seg in segments for v in seg["element_balance_residual_mol_m3"].values()), default=0.0
                ),
                "interval_charge_balance_residual_max_mol_charge_m3": max(
                    (abs(float(seg["charge_balance_residual_mol_charge_m3"])) for seg in segments), default=0.0
                ),
            })
    except (ArithmeticError, OverflowError, RuntimeError, ValueError, KeyError) as error:
        return Calculation(status="out_of_scope", values={
            "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "completed_interval_count": len(history) - 1,
            "history": history,
            "ledger_evaluation_count": total_ledger_evaluations,
            "seed_threshold_split_count": total_seed_threshold_splits,
            "maximum_seed_threshold_splits_per_interval": request.maximum_seed_threshold_splits_per_interval,
            "reason": str(error),
            "qualification_claimed": False,
        })
    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "input_sha256": digest,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "kinetic_configuration_sha256": request.kinetic_configuration_sha256,
        "kinetic_parameter_source_sha256": request.kinetic_parameter_source_sha256,
        "evidence_sha256": canonical_digest([row.model_dump(mode="json") for row in request.evidence]),
        "completed_interval_count": len(history) - 1,
        "history": history,
        "ledger_evaluation_count": total_ledger_evaluations,
        "seed_threshold_split_count": total_seed_threshold_splits,
        "maximum_seed_threshold_splits_per_interval": request.maximum_seed_threshold_splits_per_interval,
        "maximum_absolute_requested_rate_mol_m3_s": max_rate,
        "maximum_element_balance_residual_mol_m3": max_element_residual,
        "maximum_charge_balance_residual_mol_charge_m3": max_charge_residual,
        "all_intervals_committed": True,
        "interpretation_boundary": "Molar nucleation source and seeded saturation growth/dissolution are caller laws applied interval-wise to a closed batch. The conservative ledger limits aqueous reactant availability and checks charge/element closure.",
        "limitations": [
            "Saturation ratios are caller-provided exact interval records; no activity/speciation, thermodynamic phase discovery or saturation calculation is performed.",
            "Nucleation source is a caller-calibrated molar phase-formation rate with a declared supersaturation threshold. It is not a particle-number population balance, induction-time model, classical nucleation theory result or universal nucleation law.",
            "Within an interval, saturation and the nucleation source remain constant up to the seed event. The event time is computed from inventory deficit divided by molar source rate, then verified by the conservative ledger before commit; the remainder is recalculated with the seeded growth/dissolution law.",
            "No spatial transport, moving geometry, morphology, wall coverage, corrosion rate, risk, life or qualification is inferred.",
        ],
        "qualification_claimed": False,
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceNucleationKineticHistoryRequest,
        evaluator=solve_crevice_nucleation_kinetic_history,
        units={
            "temperature_K": "K",
            "intervals[].start_time_s": "s",
            "intervals[].end_time_s": "s",
            "intervals[].saturation_ratio_by_phase.*": "1",
            "nucleation_laws[].source_rate_constant_mol_m3_s": "mol/m^3/s",
            "nucleation_laws[].nucleated_inventory_threshold_mol_m3": "mol/m^3",
            "history[].aqueous_concentration_mol_m3.*": "mol/m^3",
            "history[].solid_inventory_mol_m3.*": "mol/m^3",
        },
        assumptions=(
            "Saturation is caller supplied and held constant over each exact interval.",
            "Below the caller-declared phase seed inventory, a thresholded molar nucleation source is used; after the seed threshold is reached, the caller growth/dissolution law is used.",
            "Each interval's constant rates are applied through the existing dissolution-first, common aqueous-resource-limited ledger with element and charge checks.",
            "The nucleation source is expressed as moles of formed solid per solution volume per time, not nuclei count or a particle population balance.",
            "No automatic chemistry/phase discovery, moving geometry, spatial transport or qualification is included.",
        ),
        source_ids=(SOURCE_ID, NUCLEATION_SOURCE_ID, "caller_rate_competitive_solid_mass_balance_ledger"),
        version="1.0.0",
        qualification="user_model",
    )]
