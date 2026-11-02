"""Digest-bound composition of aqueous mass-action activities into a Nernst history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, RunContext, canonical_digest
from ..registry import ModelSpec
from .crevice_nernst_profile import CreviceNernstProfile, crevice_nernst_profile


class AqueousMassActionToNernstHistory(Contract):
    schema_version: Literal["matintegrity.aqueous_mass_action_to_nernst_history.v1"] = (
        "matintegrity.aqueous_mass_action_to_nernst_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    mass_action_history_result: AssessmentResult
    mass_action_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    reaction_id: str = Field(min_length=1)
    standard_potential_reference_id: str = Field(min_length=1)
    reaction_quotient_stoichiometry: dict[str, float] = Field(min_length=1)
    electron_number: int = Field(ge=1, le=32)
    standard_potential_V: tuple[float, ...] = Field(min_length=2, max_length=5000)
    standard_potential_provider_id: str = Field(min_length=1)
    standard_potential_provider_revision: str = Field(min_length=1)
    standard_potential_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    standard_potential_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    redox_reaction_direction_and_electron_number_reviewed: bool
    activity_standard_state_and_species_mapping_reviewed: bool
    standard_potential_temperature_history_reviewed: bool
    local_activity_history_applicability_reviewed: bool
    potential_only_no_rate_or_acceptance_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_activity_history(self):
        result = self.mass_action_history_result
        supported_history_models = {
            "integration.crevice_composition_to_aqueous_mass_action_history",
            "integration.aqueous_bdot_speciation_history",
        }
        if result.model_id not in supported_history_models or result.status != "computed":
            raise ValueError("a computed digest-bound aqueous mass-action or B-dot speciation history is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("aqueous mass-action assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.mass_action_history_result_sha256:
            raise ValueError("aqueous mass-action assessment result digest mismatch")
        knots = result.values.get("knot_results")
        if not isinstance(knots, list) or len(knots) < 2:
            raise ValueError("mass-action history must contain at least two exact knots")
        if result.values.get("knot_results_sha256") != canonical_digest(knots):
            raise ValueError("aqueous mass-action knot-history digest mismatch")
        if result.model_id == "integration.aqueous_bdot_speciation_history" and not result.values.get(
            "parameter_record_sha256_by_knot"
        ):
            raise ValueError("B-dot history must preserve each exact-knot parameter record digest")
        if result.model_id == "integration.aqueous_bdot_speciation_history":
            parameter_digests = result.values["parameter_record_sha256_by_knot"]
            times = result.values.get("elapsed_time_s")
            temperatures = result.values.get("temperature_K")
            if (
                not isinstance(parameter_digests, list)
                or len(parameter_digests) != len(knots)
                or not isinstance(times, list)
                or len(times) != len(knots)
                or not isinstance(temperatures, list)
                or len(temperatures) != len(knots)
            ):
                raise ValueError("B-dot knot times, temperatures and parameter hashes must align exactly")
            for index, (knot, expected_hash, expected_time, expected_temperature) in enumerate(zip(
                knots, parameter_digests, times, temperatures, strict=True
            )):
                knot_values = knot.get("values")
                if (
                    not isinstance(expected_hash, str)
                    or len(expected_hash) != 64
                    or any(character not in "0123456789abcdef" for character in expected_hash)
                    or knot.get("time_s") != expected_time
                    or knot.get("temperature_K") != expected_temperature
                    or not isinstance(knot_values, dict)
                    or knot_values.get("parameter_record_sha256") != expected_hash
                ):
                    raise ValueError(f"B-dot knot {index} time, temperature or parameter digest is inconsistent")
        if len(self.standard_potential_V) != len(knots):
            raise ValueError("standard-potential history must match all mass-action output knots")
        for field in ("asset_id", "location_id", "physical_scope_id", "clock_id"):
            if result.values.get(field) != getattr(self, field):
                raise ValueError(f"{field} must match the upstream aqueous mass-action result")
        if any(not math.isfinite(value) for value in self.standard_potential_V):
            raise ValueError("standard-potential values must be finite")
        if any(
            not species.strip() or isinstance(coefficient, bool) or not math.isfinite(coefficient) or coefficient == 0.0
            for species, coefficient in self.reaction_quotient_stoichiometry.items()
        ):
            raise ValueError("reaction quotient species and signed coefficients must be finite and nonzero")
        if self.standard_potential_provider_id not in {row.source_id for row in self.evidence}:
            raise ValueError("standard-potential provider must map to declared Evidence")
        expected_species = set(self.reaction_quotient_stoichiometry)
        previous_time = None
        for knot in knots:
            if knot.get("status") != "computed":
                raise ValueError("every upstream mass-action knot must be computed")
            time_s = knot.get("time_s")
            temperature_K = knot.get("temperature_K")
            if (
                isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s)
                or isinstance(temperature_K, bool) or not isinstance(temperature_K, (int, float))
                or not math.isfinite(temperature_K) or temperature_K <= 0.0
            ):
                raise ValueError("each mass-action knot requires finite time and positive temperature")
            if previous_time is not None and time_s <= previous_time:
                raise ValueError("mass-action knots must be in strictly increasing time order")
            previous_time = time_s
            values = knot.get("values")
            supported_standard_states = {"molarity_1_mol_L"}
            if result.model_id == "integration.aqueous_bdot_speciation_history":
                supported_standard_states.add("dimensionless_molarity_1_mol_L")
            if not isinstance(values, dict) or values.get("activity_standard_state") not in supported_standard_states:
                raise ValueError("mass-action output must use the dimensionless 1 mol/L activity standard state")
            species_rows = values.get("species")
            if not isinstance(species_rows, list):
                raise ValueError("mass-action knot must expose species activities")
            activities = {}
            for row in species_rows:
                species_id = row.get("species_id")
                activity = row.get("dimensionless_activity")
                if (
                    not isinstance(species_id, str) or not species_id.strip()
                    or isinstance(activity, bool) or not isinstance(activity, (int, float))
                    or not math.isfinite(activity) or activity <= 0.0
                ):
                    raise ValueError("mass-action activity rows must contain finite positive dimensionless activities")
                if species_id in activities:
                    raise ValueError("mass-action result repeats a species activity ID")
                activities[species_id] = activity
            if not expected_species.issubset(activities):
                raise ValueError("every reaction quotient species must be present in the solved network")
        return self


def evaluate_aqueous_mass_action_to_nernst_history(
    x: AqueousMassActionToNernstHistory,
) -> Calculation:
    result = x.mass_action_history_result
    knots = result.values["knot_results"]
    activity_history = {
        species_id: tuple(
            next(
                row["dimensionless_activity"]
                for row in knot["values"]["species"]
                if row["species_id"] == species_id
            )
            for knot in knots
        )
        for species_id in sorted(x.reaction_quotient_stoichiometry)
    }
    activity_provider_id = "matintegrity_aqueous_mass_action_history"
    activity_evidence = Evidence(
        source_id=activity_provider_id,
        origin="model_prediction",
        citation=(
            "Dimensionless activities from digest-pinned aqueous mass-action AssessmentResult "
            f"{result.model_id}, assessment {result.values.get('assessment_id', 'unknown')}."
        ),
        sha256=x.mass_action_history_result_sha256,
    )
    source_inventory_sha256 = (
        result.values.get("composition_history_sha256")
        if result.model_id == "integration.crevice_composition_to_aqueous_mass_action_history"
        else result.values.get("knot_results_sha256")
    )
    if not isinstance(source_inventory_sha256, str) or len(source_inventory_sha256) != 64:
        raise ValueError("upstream history lacks an exact source-composition or B-dot knot-history digest")
    profile = CreviceNernstProfile(
        assessment_id=x.assessment_id,
        asset_id=x.asset_id,
        location_id=x.location_id,
        physical_scope_id=x.physical_scope_id,
        clock_id=x.clock_id,
        source_inventory_sha256=source_inventory_sha256,
        reaction_id=x.reaction_id,
        standard_potential_reference_id=x.standard_potential_reference_id,
        reaction_quotient_stoichiometry=x.reaction_quotient_stoichiometry,
        electron_number=x.electron_number,
        elapsed_time_s=tuple(knot["time_s"] for knot in knots),
        temperature_K=tuple(knot["temperature_K"] for knot in knots),
        standard_potential_V=x.standard_potential_V,
        species_activity_history=activity_history,
        activity_provider_id=activity_provider_id,
        activity_provider_revision=result.model_version,
        activity_configuration_sha256=canonical_digest({
            "mass_action_model_id": result.model_id,
            "mass_action_model_version": result.model_version,
            "mass_action_input_digest": result.input_digest,
            "knot_results_sha256": result.values["knot_results_sha256"],
        }),
        activity_record_sha256=result.values["knot_results_sha256"],
        standard_potential_provider_id=x.standard_potential_provider_id,
        standard_potential_provider_revision=x.standard_potential_provider_revision,
        standard_potential_configuration_sha256=x.standard_potential_configuration_sha256,
        standard_potential_record_sha256=x.standard_potential_record_sha256,
        redox_reaction_direction_and_electron_number_reviewed=x.redox_reaction_direction_and_electron_number_reviewed,
        activity_standard_state_and_species_mapping_reviewed=x.activity_standard_state_and_species_mapping_reviewed,
        standard_potential_temperature_history_reviewed=x.standard_potential_temperature_history_reviewed,
        local_activity_history_applicability_reviewed=x.local_activity_history_applicability_reviewed,
        potential_only_no_rate_or_acceptance_reviewed=x.potential_only_no_rate_or_acceptance_reviewed,
        computational_use_authorized=x.computational_use_authorized,
        evidence=(activity_evidence, *x.evidence),
    )
    calculation = crevice_nernst_profile(profile)
    lineage = {
        "source_history_sha256": source_inventory_sha256,
        "source_history_kind": (
            "aqueous_bdot_speciation_history"
            if result.model_id == "integration.aqueous_bdot_speciation_history"
            else "crevice_composition_to_aqueous_mass_action_history"
        ),
    }
    if result.model_id == "integration.aqueous_bdot_speciation_history":
        lineage["source_activity_history_sha256"] = x.mass_action_history_result_sha256
    values = calculation.values | lineage | {
        "mass_action_history_result_sha256": x.mass_action_history_result_sha256,
        "mass_action_knot_results_sha256": result.values["knot_results_sha256"],
        "mass_action_history_model_id": result.model_id,
        "standard_potential_reference_id": x.standard_potential_reference_id,
        "activity_coupling_policy": "computed_mass_action_activities_at_exact_shared_time_knots",
        "derived_activity_provider_evidence": activity_evidence.model_dump(mode="json"),
    }
    if result.model_id == "integration.aqueous_bdot_speciation_history":
        values.pop("source_inventory_sha256", None)
    return Calculation(
        values=values,
        status=calculation.status,
        notes=calculation.notes + (
        "This is a sequential aqueous-activity-history-to-Nernst handoff. It does not iteratively couple electrochemical current back into the same composition history or infer temperature-dependent standard potentials.",
        ),
    )


def _validate_context(x: AqueousMassActionToNernstHistory, context: RunContext) -> None:
    source = x.mass_action_history_result.values
    if context.asset_id != x.asset_id or context.asset_id != source.get("asset_id"):
        raise ValueError("run context and request asset must match the upstream aqueous composition")
    if context.location_id != x.location_id or context.location_id != source.get("location_id"):
        raise ValueError("run context and request location must match the upstream aqueous composition")
    if x.physical_scope_id != source.get("physical_scope_id"):
        raise ValueError("request physical scope must match the upstream aqueous composition")
    if context.time_basis != x.clock_id or x.clock_id != source.get("clock_id"):
        raise ValueError("run context and request time basis must match the upstream aqueous clock ID")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_mass_action_to_crevice_nernst_history",
        AqueousMassActionToNernstHistory,
        evaluate_aqueous_mass_action_to_nernst_history,
        {
            "source_inventory_sha256": "1",
            "elapsed_time_s": "s",
            "temperature_K": "K",
            "standard_potential_V": "V",
            "potential_history[].time_s": "s",
            "potential_history[].temperature_K": "K",
            "potential_history[].standard_potential_V": "V",
            "potential_history[].potential_V": "V",
            "potential_history[].ln_reaction_quotient": "1",
        },
        (
            "Only dimensionless activities and exact time/temperature knots from a computed digest-pinned crevice mass-action or B-dot speciation history are consumed.",
            "The caller supplies the redox equation, reference identity, electron number and standard-potential history, which must align with the solved aqueous species and time basis.",
            "The upstream activity-history digest supplies source lineage when no raw composition-history digest exists; B-dot parameter-record hashes remain in the upstream result.",
            "This composes sequential calculations; it does not perform simultaneous speciation/electrode coupling, activity inference, kinetics or corrosion qualification.",
        ),
        ("aqueous_mass_action_activities_to_crevice_nernst_potential_history",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
