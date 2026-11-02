"""Caller-volume composition history driven by a verified electrochemical transfer ledger."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class CreviceElectrolyteVolumeKnot(Contract):
    time_s: Nonnegative
    liquid_volume_m3: Positive


class CreviceInitialSpeciesInventory(Contract):
    species_id: str = Field(min_length=1)
    initial_amount_mol: Nonnegative


class CreviceElectrochemicalCompositionHistory(Contract):
    schema_version: Literal["matintegrity.crevice_electrochemical_composition_history.v1"] = (
        "matintegrity.crevice_electrochemical_composition_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    transfer_result: AssessmentResult
    transfer_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_inventory: tuple[CreviceInitialSpeciesInventory, ...] = Field(min_length=1)
    liquid_volume_history: tuple[CreviceElectrolyteVolumeKnot, ...] = Field(min_length=2)
    complete_species_inventory_reviewed: bool
    all_other_sources_and_sinks_included_reviewed: bool
    well_mixed_single_volume_reviewed: bool
    fixed_basis_and_interval_transfer_mapping_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_transfer_ledger(self):
        result = self.transfer_result
        if result.model_id != "integration.crevice_electrochemical_inventory_transfer" or result.status != "computed":
            raise ValueError("a computed electrochemical inventory-transfer assessment is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("transfer assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.transfer_result_sha256:
            raise ValueError("transfer assessment result digest mismatch")
        history = result.values.get("interval_inventory_transfer")
        if not isinstance(history, list) or not history:
            raise ValueError("transfer assessment must contain interval inventory records")
        expected_ledger_digest = canonical_digest({
            "intervals": history,
            "cumulative": result.values.get("cumulative_inventory_transfer_by_reaction"),
        })
        if result.values.get("inventory_transfer_sha256") != expected_ledger_digest:
            raise ValueError("transfer ledger digest mismatch")
        if len({row.species_id for row in self.initial_inventory}) != len(self.initial_inventory):
            raise ValueError("initial inventory species IDs must be unique")
        if len({row.time_s for row in self.liquid_volume_history}) != len(self.liquid_volume_history):
            raise ValueError("liquid volume times must be unique")
        for left, right in zip(self.liquid_volume_history, self.liquid_volume_history[1:]):
            if right.time_s <= left.time_s:
                raise ValueError("liquid-volume knots must be strictly increasing")
        expected_times = [history[0]["start_time_s"], *[row["end_time_s"] for row in history]]
        actual_times = [row.time_s for row in self.liquid_volume_history]
        if actual_times != expected_times:
            raise ValueError("liquid-volume knots must match transfer start/end times exactly")
        declared_species = {row.species_id for row in self.initial_inventory}
        transferred_species = {
            entry["species_id"]
            for interval in history
            for branch in interval["reaction_species_transfer"]
            for entry in branch["species_transfer"]
        }
        if not transferred_species.issubset(declared_species):
            raise ValueError("initial inventory must explicitly include every transferred species")
        if not declared_species:
            raise ValueError("at least one initial species amount is required")
        return self


def evaluate_crevice_electrochemical_composition_history(
    x: CreviceElectrochemicalCompositionHistory,
) -> Calculation:
    source = x.transfer_result
    transfer = source.values["interval_inventory_transfer"]
    volumes = x.liquid_volume_history
    inventories = {row.species_id: row.initial_amount_mol for row in x.initial_inventory}
    reviews = {
        "complete_species_inventory_reviewed": x.complete_species_inventory_reviewed,
        "all_other_sources_and_sinks_included_reviewed": x.all_other_sources_and_sinks_included_reviewed,
        "well_mixed_single_volume_reviewed": x.well_mixed_single_volume_reviewed,
        "fixed_basis_and_interval_transfer_mapping_reviewed": x.fixed_basis_and_interval_transfer_mapping_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
    }
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": source.values["asset_id"],
        "location_id": source.values["location_id"],
        "physical_scope_id": source.values["physical_scope_id"],
        "clock_id": source.values["clock_id"],
        "reference_area_m2": source.values["reference_area_m2"],
        "transfer_result_sha256": x.transfer_result_sha256,
        "transfer_inventory_sha256": source.values["inventory_transfer_sha256"],
        "volume_history_policy": "caller_supplied_exact_time_knots_no_interpolation",
        "inventory_balance_policy": "initial_moles_plus_all_reaction_species_transfer_on_reference_area",
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    rows = [{
        "time_s": volumes[0].time_s,
        "temperature_K": transfer[0]["start_temperature_K"],
        "liquid_volume_m3": volumes[0].liquid_volume_m3,
        "species": [
            {"species_id": key, "amount_mol": amount, "concentration_mol_m3": amount / volumes[0].liquid_volume_m3}
            for key, amount in sorted(inventories.items())
        ],
    }]
    for index, interval in enumerate(transfer):
        interval_delta = {key: 0.0 for key in inventories}
        for branch in interval["reaction_species_transfer"]:
            for entry in branch["species_transfer"]:
                interval_delta[entry["species_id"]] += entry["signed_net_transfer_mol"]
        for key, delta in interval_delta.items():
            inventories[key] += delta
            if not math.isfinite(inventories[key]) or inventories[key] < 0.0:
                return Calculation(status="out_of_scope", values=base | {
                    "failed_interval_index": index,
                    "failed_interval_start_s": interval["start_time_s"],
                    "failed_interval_end_s": interval["end_time_s"],
                    "failed_species_id": key,
                    "computed_prefix": rows,
                    "failure_reason": "net_electrochemical_transfer_exceeds_available_species_inventory",
                })
        volume = volumes[index + 1]
        concentration_rows = [
            {"species_id": key, "amount_mol": amount, "concentration_mol_m3": amount / volume.liquid_volume_m3}
            for key, amount in sorted(inventories.items())
        ]
        if not all(math.isfinite(item["concentration_mol_m3"]) for item in concentration_rows):
            return Calculation(status="out_of_scope", values=base | {
                "failed_time_s": volume.time_s,
                "computed_prefix": rows,
                "failure_reason": "concentration_exceeds_numeric_range",
            })
        rows.append({
            "time_s": volume.time_s,
            "temperature_K": interval["end_temperature_K"],
            "liquid_volume_m3": volume.liquid_volume_m3,
            "interval_signed_transfer_mol_by_species": interval_delta,
            "species": concentration_rows,
        })
    return Calculation(values=base | {
        "composition_history": rows,
        "composition_history_sha256": canonical_digest(rows),
    }, notes=(
        "Amounts are propagated by adding the upstream signed transfer ledger to the caller's initial species amounts; concentrations divide by caller-supplied liquid volumes at exact aligned knots.",
        "This is a well-mixed bookkeeping adapter. It does not solve aqueous equilibrium, transport, precipitation, liquid loss, additional source/sink kinetics, or metal wall loss; all non-electrochemical contributions must be included in the caller's declared baseline/other-sink model.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.crevice_electrochemical_composition_history",
        CreviceElectrochemicalCompositionHistory,
        evaluate_crevice_electrochemical_composition_history,
        {
            "composition_history[].time_s": "s",
            "composition_history[].temperature_K": "K",
            "composition_history[].liquid_volume_m3": "m3",
            "composition_history[].species[].amount_mol": "mol",
            "composition_history[].species[].concentration_mol_m3": "mol/m3",
            "composition_history[].interval_signed_transfer_mol_by_species.*": "mol",
        },
        (
            "The digest-pinned upstream flux ledger is area-scaled and mapped directly into caller-declared aqueous species inventories using the caller sign convention.",
            "All affected species need initial mole inventories; all other sources/sinks and the single well-mixed liquid volume are caller-reviewed assumptions.",
            "Concentrations are only mole amounts divided by caller volume at exact knots; no equilibrium, speciation, transport or material-loss law is solved.",
        ),
        ("crevice_electrochemical_transfer_to_well_mixed_composition_history",),
        qualification="user_model",
    )]
