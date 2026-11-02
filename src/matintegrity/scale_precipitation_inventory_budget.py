"""Check caller-supplied dissolved-reactant inventories against a computed scale history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from .registry import ModelSpec


class ScaleReactantIntervalSupply(Contract):
    """Caller-reported addition to a limiting-reactant inventory for one interval."""

    interval_id: str = Field(min_length=1)
    added_mol: Nonnegative
    source_record_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def source_is_cited(self):
        if self.source_record_id not in {row.source_id for row in self.evidence}:
            raise ValueError("interval supply source_record_id must be present in Evidence")
        return self


class ScaleLimitingReactantInventory(Contract):
    """Available formula-unit reactant plus one declared supply per scale interval."""

    aqueous_species_id: str = Field(min_length=1)
    moles_required_per_scale_formula_mol: Positive
    initial_available_mol: Nonnegative
    initial_inventory_record_id: str = Field(min_length=1)
    initial_inventory_evidence: tuple[Evidence, ...] = Field(min_length=1)
    interval_supply: tuple[ScaleReactantIntervalSupply, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def initial_source_is_cited(self):
        if self.initial_inventory_record_id not in {row.source_id for row in self.initial_inventory_evidence}:
            raise ValueError("initial inventory record ID must be present in Evidence")
        if len({row.interval_id for row in self.interval_supply}) != len(self.interval_supply):
            raise ValueError("reactant interval supply IDs must be unique")
        return self


class ScalePrecipitationInventoryBudget(Contract):
    """Compare gross computed phase precipitation with caller-owned reactant stocks."""

    schema_version: Literal["matintegrity.scale_precipitation_inventory_budget.v1"] = (
        "matintegrity.scale_precipitation_inventory_budget.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    scale_history_result: AssessmentResult
    scale_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    exposed_area_m2: Positive
    exposed_area_record_id: str = Field(min_length=1)
    exposed_area_evidence: tuple[Evidence, ...] = Field(min_length=1)
    limiting_reactants: tuple[ScaleLimitingReactantInventory, ...] = Field(min_length=1, max_length=100)
    scale_formula_stoichiometry_reviewed: bool
    inventory_accessibility_and_interval_supply_reviewed: bool
    scale_history_scope_and_area_mapping_reviewed: bool
    gross_precipitation_only_no_dissolution_credit_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def align_with_scale_history(self):
        if self.exposed_area_record_id not in {row.source_id for row in self.exposed_area_evidence}:
            raise ValueError("exposed area record ID must be present in Evidence")
        result = self.scale_history_result
        if result.model_id != "chemistry.caller_surface_scale_kinetics" or result.status != "computed":
            raise ValueError("a computed caller single-phase scale-thickness history is required")
        if canonical_digest(result.model_dump(mode="json")) != self.scale_history_result_sha256:
            raise ValueError("scale-history result digest does not match")
        if result.values.get("input_digest") != canonical_digest(result.inputs):
            raise ValueError("scale-history input digest does not match its request")
        if result.values.get("physical_scope_id") != self.physical_scope_id or result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("scale history must match the declared physical scope")
        rows = result.values.get("scale_history")
        if not isinstance(rows, list) or len(rows) < 2:
            raise ValueError("scale history must contain an initial knot and at least one interval result")
        intervals = rows[1:]
        interval_ids = []
        previous_time = rows[0].get("time_s") if isinstance(rows[0], dict) else None
        if isinstance(previous_time, bool) or not isinstance(previous_time, (int, float)) or not math.isfinite(previous_time):
            raise ValueError("initial scale-history time must be finite")
        for row in intervals:
            if not isinstance(row, dict):
                raise ValueError("scale history rows must be objects")
            interval_id = row.get("interval_id")
            time_s = row.get("time_s")
            precipitated = row.get("precipitated_mol_m2")
            if not isinstance(interval_id, str) or not interval_id:
                raise ValueError("each post-initial scale-history row must declare an interval ID")
            if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s) or time_s <= previous_time:
                raise ValueError("scale-history interval end times must be finite and strictly increasing")
            if isinstance(precipitated, bool) or not isinstance(precipitated, (int, float)) or not math.isfinite(precipitated) or precipitated < 0:
                raise ValueError("each interval must report finite nonnegative gross precipitated moles per area")
            interval_ids.append(interval_id)
            previous_time = time_s
        if len(set(interval_ids)) != len(interval_ids):
            raise ValueError("scale-history interval IDs must be unique")
        species = [row.aqueous_species_id for row in self.limiting_reactants]
        if len(set(species)) != len(species):
            raise ValueError("limiting aqueous reactant species IDs must be unique")
        for reactant in self.limiting_reactants:
            supply_ids = [row.interval_id for row in reactant.interval_supply]
            if supply_ids != interval_ids:
                raise ValueError("every reactant must provide one ordered supply record for each scale-history interval")
        return self


def evaluate_scale_precipitation_inventory_budget(request: ScalePrecipitationInventoryBudget) -> Calculation:
    """Reconcile gross scale precipitation against finite caller-declared reactant stocks."""
    history = request.scale_history_result.values["scale_history"]
    interval_rows = history[1:]
    scale_result_digest = request.scale_history_result_sha256
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "scale_phase_id": request.scale_history_result.values.get("scale_phase_id"),
        "scale_history_result_sha256": scale_result_digest,
        "scale_history_input_sha256": request.scale_history_result.values["input_digest"],
        "input_sha256": input_digest,
        "exposed_area_m2": request.exposed_area_m2,
        "exposed_area_record_id": request.exposed_area_record_id,
        "exposed_area_evidence": [row.model_dump(mode="json") for row in request.exposed_area_evidence],
        "inventory_evidence": {
            reactant.aqueous_species_id: {
                "initial": [row.model_dump(mode="json") for row in reactant.initial_inventory_evidence],
                "interval_supply": {
                    supply.interval_id: [row.model_dump(mode="json") for row in supply.evidence]
                    for supply in reactant.interval_supply
                },
            }
            for reactant in request.limiting_reactants
        },
    }
    reviews = {
        "scale_formula_stoichiometry_reviewed": request.scale_formula_stoichiometry_reviewed,
        "inventory_accessibility_and_interval_supply_reviewed": request.inventory_accessibility_and_interval_supply_reviewed,
        "scale_history_scope_and_area_mapping_reviewed": request.scale_history_scope_and_area_mapping_reviewed,
        "gross_precipitation_only_no_dissolution_credit_reviewed": request.gross_precipitation_only_no_dissolution_credit_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {
            "completed_interval_count": 0,
            "intervals": [],
            "missing_reviews": missing,
            "interpretation": "stoichiometric_availability_screen_only",
        })

    inventories = {row.aqueous_species_id: row.initial_available_mol for row in request.limiting_reactants}
    additions = {
        row.aqueous_species_id: {supply.interval_id: supply.added_mol for supply in row.interval_supply}
        for row in request.limiting_reactants
    }
    rows = []
    for scale_row in interval_rows:
        scale_mol = scale_row["precipitated_mol_m2"] * request.exposed_area_m2
        if not math.isfinite(scale_mol):
            return Calculation(status="out_of_scope", values=base | {
                "completed_interval_count": len(rows),
                "completed_intervals": rows,
                "first_unsupported_interval_id": scale_row["interval_id"],
                "reason": "gross_scale_precipitation_amount_exceeds_finite_numeric_support",
            })
        reactant_rows = []
        shortfalls = []
        for reactant in request.limiting_reactants:
            species = reactant.aqueous_species_id
            available = inventories[species] + additions[species][scale_row["interval_id"]]
            demand = scale_mol * reactant.moles_required_per_scale_formula_mol
            if not all(math.isfinite(value) for value in (available, demand)):
                return Calculation(status="out_of_scope", values=base | {
                    "completed_interval_count": len(rows),
                    "completed_intervals": rows,
                    "first_unsupported_interval_id": scale_row["interval_id"],
                    "first_unsupported_species_id": species,
                    "reason": "reactant_inventory_arithmetic_exceeds_finite_numeric_support",
                })
            if demand > available:
                shortfalls.append({
                    "aqueous_species_id": species,
                    "available_before_mol": available,
                    "gross_precipitation_demand_mol": demand,
                    "shortfall_mol": demand - available,
                })
            reactant_rows.append({
                "aqueous_species_id": species,
                "available_before_mol": available,
                "interval_supply_mol": additions[species][scale_row["interval_id"]],
                "gross_precipitation_demand_mol": demand,
                "remaining_after_mol": max(0.0, available - demand),
                "moles_required_per_scale_formula_mol": reactant.moles_required_per_scale_formula_mol,
            })
        if shortfalls:
            return Calculation(status="out_of_scope", values=base | {
                "completed_interval_count": len(rows),
                "completed_intervals": rows,
                "first_inventory_shortfall_interval_id": scale_row["interval_id"],
                "first_inventory_shortfalls": shortfalls,
                "rejected_interval_is_not_committed": True,
                "interpretation": "declared_scale_precipitation_exceeds_caller_declared_reactant_supply",
            }, notes=(
                "The scale history is a caller-calibrated prediction. This separate ledger reports when its gross precipitation demand exceeds the declared finite reactant inventory; it does not alter the upstream history.",
            ))
        for reactant, row in zip(request.limiting_reactants, reactant_rows, strict=True):
            inventories[reactant.aqueous_species_id] = row["remaining_after_mol"]
        rows.append({
            "interval_id": scale_row["interval_id"],
            "end_time_s": scale_row["time_s"],
            "gross_precipitated_mol_m2": scale_row["precipitated_mol_m2"],
            "exposed_area_m2": request.exposed_area_m2,
            "gross_scale_formula_units_mol": scale_mol,
            "reactants": reactant_rows,
            "gross_dissolution_credit_mol": 0.0,
        })
    return Calculation(values=base | {
        "completed_interval_count": len(rows),
        "completed_intervals": rows,
        "final_available_inventory_mol": inventories,
        "interpretation": "finite_stoichiometric_inventory_feasibility_for_caller_computed_gross_scale_precipitation",
        "no_saturation_or_kinetic_feedback": True,
        "not_inferred": ["aqueous_speciation", "equilibrium", "transport", "precipitation_law", "corrosion_rate", "wall_loss", "acceptance", "failure_probability"],
    }, notes=(
        "The upstream scale history is preserved and is never re-solved or altered.",
        "Gross precipitation is charged against supplied reactant inventories; dissolution is not credited as recycled reactant.",
        "A computed result is only an availability ledger conditional on caller-provided stoichiometry, area and inventory accessibility.",
    ))


def _validate_scale_history_context(request: ScalePrecipitationInventoryBudget, context: RunContext) -> None:
    """Keep the inventory ledger in the same asset/location/clock as its scale history."""
    upstream = request.scale_history_result.context
    if (upstream.asset_id, upstream.location_id, upstream.time_basis) != (
        context.asset_id,
        context.location_id,
        context.time_basis,
    ):
        raise ValueError("RunContext asset, location and time basis must match the supplied scale history")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="chemistry.scale_precipitation_inventory_budget",
        input_type=ScalePrecipitationInventoryBudget,
        evaluator=evaluate_scale_precipitation_inventory_budget,
        units={
            "exposed_area_m2": "m^2",
            "limiting_reactants[].initial_available_mol": "mol",
            "limiting_reactants[].moles_required_per_scale_formula_mol": "mol/mol",
            "limiting_reactants[].interval_supply[].added_mol": "mol",
            "completed_intervals[].end_time_s": "s",
            "completed_intervals[].gross_precipitated_mol_m2": "mol/m^2",
            "completed_intervals[].gross_scale_formula_units_mol": "mol",
            "completed_intervals[].reactants[].gross_precipitation_demand_mol": "mol",
            "final_available_inventory_mol.*": "mol",
        },
        assumptions=(
            "Use the gross per-area precipitation amounts from one exact digest-pinned caller scale history and multiply by one caller-declared exposed area.",
            "Subtract caller-declared formula-unit stoichiometric reactant demand from initial and interval-added finite species inventories.",
            "Require caller review of stoichiometry, area/scope mapping, inventory accessibility, supplied interval additions, gross-only accounting and computational use.",
            "Do not infer equilibrium, speciation, transport, kinetic feedback, scale dissolution recycling, corrosion, wall loss, acceptance or probability.",
        ),
        source_ids=("caller_scale_precipitation_inventory_budget",),
        qualification="user_model",
        context_validator=_validate_scale_history_context,
    )]
