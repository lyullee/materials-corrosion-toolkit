"""Knotwise mixed-potential balance from caller-evidenced crevice redox profiles."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..electrode_kinetics import ButlerVolmerReaction, solve_electrode_mixed_potential
from ..registry import ModelSpec


class CreviceMixedPotentialReaction(Contract):
    reaction_id: str = Field(min_length=1)
    nernst_result: AssessmentResult
    nernst_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reference_electrode_id: str = Field(min_length=1)
    exposed_area_m2: Positive
    exchange_current_density_A_m2: Nonnegative
    electron_number: int = Field(ge=1, le=32)
    anodic_transfer_coefficient: Positive = Field(le=1.0)
    cathodic_transfer_coefficient: Positive = Field(le=1.0)
    minimum_overpotential_V: float
    maximum_overpotential_V: float
    stoichiometric_species_coefficients: dict[str, float] = Field(min_length=1)
    kinetics_provider_id: str = Field(min_length=1)
    kinetics_provider_revision: str = Field(min_length=1)
    kinetics_calibration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetics_and_anodic_direction_reviewed: bool
    species_flux_mapping_and_area_basis_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_half_cell_and_kinetics(self):
        result = self.nernst_result
        if result.model_id not in {
            "degradation.crevice_nernst_potential_history",
            "integration.aqueous_mass_action_to_crevice_nernst_history",
        } or result.status != "computed":
            raise ValueError("each branch requires a computed, supported crevice Nernst AssessmentResult")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("Nernst profile assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.nernst_result_sha256:
            raise ValueError("Nernst result digest does not match the complete assessment")
        history = result.values.get("potential_history")
        if not isinstance(history, list) or len(history) < 2:
            raise ValueError("Nernst profile must retain at least two potential knots")
        if result.values.get("potential_history_sha256") != canonical_digest(history):
            raise ValueError("Nernst potential history digest mismatch")
        if result.inputs.get("reaction_id") != self.reaction_id:
            raise ValueError("reaction ID must match its Nernst profile")
        if result.inputs.get("standard_potential_reference_id") != self.reference_electrode_id:
            raise ValueError("branch reference ID must match its Nernst standard-potential reference")
        if self.maximum_overpotential_V < self.minimum_overpotential_V:
            raise ValueError("reaction overpotential support must be ordered")
        if not self.stoichiometric_species_coefficients or any(
            not species.strip() or not math.isfinite(value) or value == 0.0
            for species, value in self.stoichiometric_species_coefficients.items()
        ):
            raise ValueError("reaction stoichiometric flux coefficients must be finite and nonzero")
        if self.kinetics_provider_id not in {row.source_id for row in self.evidence}:
            raise ValueError("kinetics provider must map to declared Evidence")
        return self


class CreviceMixedPotentialHistory(Contract):
    schema_version: Literal["matintegrity.crevice_mixed_potential_history.v1"] = (
        "matintegrity.crevice_mixed_potential_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    common_reference_electrode_id: str = Field(min_length=1)
    reference_area_m2: Positive
    reactions: tuple[CreviceMixedPotentialReaction, ...] = Field(min_length=2, max_length=32)
    quasi_steady_local_balance_reviewed: bool
    negligible_solution_ohmic_drop_reviewed: bool
    common_electronic_potential_basis_reviewed: bool
    reaction_set_and_area_partition_complete_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def aligned_kinetic_histories(self):
        if len({row.reaction_id for row in self.reactions}) != len(self.reactions):
            raise ValueError("mixed-potential reaction IDs must be unique")
        first = self.reactions[0]
        first_inputs = first.nernst_result.inputs
        first_history = first.nernst_result.values["potential_history"]
        first_times = tuple(row["time_s"] for row in first_history)
        first_temperatures = tuple(row["temperature_K"] for row in first_history)
        first_lineage = _nernst_source_lineage(first.nernst_result)
        if first.reference_electrode_id != self.common_reference_electrode_id:
            raise ValueError("first branch reference does not match the common reference")
        if (
            first_inputs.get("clock_id") != self.clock_id
            or first_inputs.get("physical_scope_id") != self.physical_scope_id
            or first_inputs.get("asset_id") != self.asset_id
            or first_inputs.get("location_id") != self.location_id
        ):
            raise ValueError("first branch clock, asset, location and physical scope must match the mixed-potential request")
        for branch in self.reactions[1:]:
            result = branch.nernst_result
            rows = result.values["potential_history"]
            if branch.reference_electrode_id != self.common_reference_electrode_id:
                raise ValueError("all half-cell profiles must use the common reference electrode")
            if (
                result.inputs.get("clock_id") != self.clock_id
                or result.inputs.get("physical_scope_id") != self.physical_scope_id
                or result.inputs.get("asset_id") != self.asset_id
                or result.inputs.get("location_id") != self.location_id
            ):
                raise ValueError("all half-cell profiles must use the same clock, asset, location and physical scope")
            if tuple(row["time_s"] for row in rows) != first_times:
                raise ValueError("all Nernst profiles must have identical time knots")
            if tuple(row["temperature_K"] for row in rows) != first_temperatures:
                raise ValueError("all reaction kinetics must share the same temperature at every knot")
            if _nernst_source_lineage(result) != first_lineage:
                raise ValueError("all reaction profiles must bind to the same aqueous history lineage")
        if not first_times or first_temperatures is None:
            raise ValueError("at least one aligned temperature/time history is required")
        return self


def _nernst_source_lineage(result: AssessmentResult) -> dict[str, str]:
    """Return the declared source identity without relabeling a history as inventory."""
    values = result.values
    source_history_sha256 = values.get("source_history_sha256")
    if source_history_sha256 is None:
        source_history_sha256 = values.get("source_inventory_sha256")
    if not isinstance(source_history_sha256, str) or len(source_history_sha256) != 64:
        raise ValueError("Nernst result must expose a source history or inventory digest")
    if any(character not in "0123456789abcdef" for character in source_history_sha256):
        raise ValueError("Nernst source history digest must be lowercase hexadecimal SHA-256")
    lineage = {
        "source_history_sha256": source_history_sha256,
        "source_history_kind": values.get("source_history_kind", "inventory_assessment"),
    }
    if not isinstance(lineage["source_history_kind"], str) or not lineage["source_history_kind"].strip():
        raise ValueError("source history kind must be a nonempty string")
    activity_digest = values.get("source_activity_history_sha256")
    if activity_digest is None:
        activity_digest = values.get("mass_action_history_result_sha256")
    if activity_digest is not None:
        if (
            not isinstance(activity_digest, str)
            or len(activity_digest) != 64
            or any(character not in "0123456789abcdef" for character in activity_digest)
        ):
            raise ValueError("source activity-history digest must be a SHA-256 value")
        lineage["source_activity_history_sha256"] = activity_digest
    return lineage


def evaluate_crevice_mixed_potential_history(x: CreviceMixedPotentialHistory) -> Calculation:
    digest = canonical_digest(x.model_dump(mode="json"))
    first_result = x.reactions[0].nernst_result
    times = [row["time_s"] for row in first_result.values["potential_history"]]
    lineage = _nernst_source_lineage(first_result)
    reviews = {
        "quasi_steady_local_balance_reviewed": x.quasi_steady_local_balance_reviewed,
        "negligible_solution_ohmic_drop_reviewed": x.negligible_solution_ohmic_drop_reviewed,
        "common_electronic_potential_basis_reviewed": x.common_electronic_potential_basis_reviewed,
        "reaction_set_and_area_partition_complete_reviewed": x.reaction_set_and_area_partition_complete_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
        **{
            f"reaction[{row.reaction_id}].kinetics_and_anodic_direction_reviewed": row.kinetics_and_anodic_direction_reviewed
            for row in x.reactions
        },
        **{
            f"reaction[{row.reaction_id}].species_flux_mapping_and_area_basis_reviewed": row.species_flux_mapping_and_area_basis_reviewed
            for row in x.reactions
        },
    }
    base = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "clock_id": x.clock_id,
        "common_reference_electrode_id": x.common_reference_electrode_id,
        "reference_area_m2": x.reference_area_m2,
        **lineage,
        "reaction_ids": [row.reaction_id for row in x.reactions],
        "nernst_result_sha256_by_reaction": {
            row.reaction_id: row.nernst_result_sha256 for row in x.reactions
        },
        "kinetics_calibration_sha256_by_reaction": {
            row.reaction_id: row.kinetics_calibration_sha256 for row in x.reactions
        },
        "input_sha256": digest,
    }
    if isinstance(first_result.values.get("source_inventory_sha256"), str):
        base["source_inventory_sha256"] = first_result.values["source_inventory_sha256"]
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    history = []
    for index, time_s in enumerate(times):
        reactions = []
        try:
            for branch in x.reactions:
                half_cell = branch.nernst_result.values["potential_history"][index]
                area_fraction = branch.exposed_area_m2 / x.reference_area_m2
                effective_exchange_current = branch.exchange_current_density_A_m2 * area_fraction
                if not math.isfinite(effective_exchange_current) or (
                    branch.exchange_current_density_A_m2 > 0.0 and effective_exchange_current == 0.0
                ):
                    raise ArithmeticError("area-scaled exchange current is outside finite support")
                reactions.append(ButlerVolmerReaction(
                    reaction_id=branch.reaction_id,
                    calibration_sha256=branch.kinetics_calibration_sha256,
                    exchange_current_density_A_m2=effective_exchange_current,
                    electron_count=branch.electron_number,
                    anodic_transfer_coefficient=branch.anodic_transfer_coefficient,
                    cathodic_transfer_coefficient=branch.cathodic_transfer_coefficient,
                    equilibrium_potential_V=half_cell["potential_V"],
                    temperature_K=half_cell["temperature_K"],
                    minimum_overpotential_V=branch.minimum_overpotential_V,
                    maximum_overpotential_V=branch.maximum_overpotential_V,
                    stoichiometric_species_coefficients=branch.stoichiometric_species_coefficients,
                    calibration_and_reaction_direction_reviewed=True,
                ))
            balance = solve_electrode_mixed_potential(tuple(reactions))
        except (ArithmeticError, OverflowError, ValueError, ImportError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "failed_time_index": index,
                "failed_time_s": time_s,
                "failure_reason": str(error),
                "computed_prefix": history,
            })
        if balance.get("status") != "computed":
            status = "needs_data" if balance.get("status") == "needs_data" else "out_of_scope"
            return Calculation(status=status, values=base | {
                "failed_time_index": index,
                "failed_time_s": time_s,
                "failure_reason": balance.get("reason", "mixed_potential_not_supported_at_knot"),
                "computed_prefix": history,
            })
        branch_results = []
        for branch, response in zip(x.reactions, balance["partial_reactions"], strict=True):
            branch_results.append({
                "reaction_id": branch.reaction_id,
                "exposed_area_m2": branch.exposed_area_m2,
                "area_fraction_of_reference": branch.exposed_area_m2 / x.reference_area_m2,
                "equilibrium_potential_V": response["equilibrium_potential_V"],
                "overpotential_V": response["overpotential_V"],
                "reference_area_signed_current_density_A_m2": response["signed_current_density_A_m2"],
                "reference_area_gross_anodic_current_density_A_m2": response["gross_anodic_current_density_A_m2"],
                "reference_area_gross_cathodic_current_density_A_m2": response["gross_cathodic_current_density_A_m2"],
                "reference_area_species_flux_mol_m2_s": response["inward_species_flux_mol_m2_s"],
            })
        history.append({
            "time_s": time_s,
            "temperature_K": first_result.values["potential_history"][index]["temperature_K"],
            "mixed_potential_V": balance["metal_minus_solution_potential_V"],
            "net_current_density_on_reference_area_A_m2": balance["net_current_density_A_m2"],
            "reaction_responses": branch_results,
        })
    return Calculation(values=base | {
        "mixed_potential_history": history,
        "mixed_potential_history_sha256": canonical_digest(history),
        "solver": "knotwise_shared-potential_Butler-Volmer_current-balance",
        "area_basis": "all reaction currents and species fluxes normalized to caller reference_area_m2",
        "time_policy": "evaluate_exact_caller_knots_without_interpolation_or_integration",
    }, notes=(
        "At each declared knot, the solver balances caller-calibrated anodic-positive reaction currents over the common overpotential support.",
        "This is conditional on the complete caller reaction set, area partition, shared potential, negligible ohmic drop and quasi-steady review. It does not infer activities, kinetic parameters, dynamic stability, charge integral, total metal loss or corrosion acceptance.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "electrochemistry.crevice_mixed_potential_history",
        CreviceMixedPotentialHistory,
        evaluate_crevice_mixed_potential_history,
        {
            "source_history_sha256": "1",
            "source_inventory_sha256": "1",
            "source_activity_history_sha256": "1",
            "reference_area_m2": "m2",
            "mixed_potential_history[].time_s": "s",
            "mixed_potential_history[].temperature_K": "K",
            "mixed_potential_history[].mixed_potential_V": "V",
            "mixed_potential_history[].net_current_density_on_reference_area_A_m2": "A/m2",
            "mixed_potential_history[].reaction_responses[].exposed_area_m2": "m2",
            "mixed_potential_history[].reaction_responses[].area_fraction_of_reference": "1",
            "mixed_potential_history[].reaction_responses[].equilibrium_potential_V": "V",
            "mixed_potential_history[].reaction_responses[].overpotential_V": "V",
            "mixed_potential_history[].reaction_responses[].reference_area_signed_current_density_A_m2": "A/m2",
            "mixed_potential_history[].reaction_responses[].reference_area_gross_anodic_current_density_A_m2": "A/m2",
            "mixed_potential_history[].reaction_responses[].reference_area_gross_cathodic_current_density_A_m2": "A/m2",
            "mixed_potential_history[].reaction_responses[].reference_area_species_flux_mol_m2_s.*": "mol/m2/s",
        },
        (
            "At every aligned knot, evaluate multiple caller-provided Nernst half-cell profiles and caller-calibrated Butler-Volmer reactions, area-normalize the currents, and solve for a common zero-net-current potential within all reaction overpotential supports.",
            "Branches must carry the same explicit source-history lineage. Raw inventory digests remain available where supplied; aqueous mass-action and B-dot activity-history digests are retained under separate names.",
            "The API requires the complete declared reaction set, shared clock/temperature/reference, area partition, quasi-steady state and negligible-ohmic-drop review. It returns instantaneous partial reaction currents only; no time integration, dynamic stability, activity/kinetic fitting or total corrosion qualification is included.",
        ),
        ("crevice_multireaction_nernst_butler_volmer_balance",),
        qualification="user_model",
    )]
