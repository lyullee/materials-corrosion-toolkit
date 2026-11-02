"""Convert reviewed electrochemical partial-current histories to metal loss."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from ..registry import ModelSpec

FARADAY_C_MOL = 96485.33212331001


class MetalDissolutionReactionMapping(Contract):
    """Caller mapping from one anodic reaction extent to removed metal atoms."""

    reaction_id: str = Field(min_length=1)
    metal_species_id: str = Field(min_length=1)
    metal_atoms_per_reaction_extent: Positive
    molar_mass_kg_mol: Positive
    density_kg_m3: Positive
    metal_data_provider_id: str = Field(min_length=1)
    metal_data_provider_revision: str = Field(min_length=1)
    metal_data_record_id: str = Field(min_length=1)
    metal_data_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    anodic_direction_is_metal_dissolution_reviewed: bool
    alloy_and_metal_basis_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def material_data_is_evidenced(self):
        if not any(
            row.source_id == self.metal_data_provider_id and row.sha256 == self.metal_data_sha256
            for row in self.evidence
        ):
            raise ValueError("metal property provider and source digest must match declared Evidence")
        return self


class ElectrochemicalMetalLossHistory(Contract):
    """Integrate branch currents from a pinned mixed-potential history.

    Current is reconstructed linearly between upstream knots. Positive anodic
    reaction extent removes caller-mapped metal; the cathodic branch is
    reported separately and subtracts from signed net removal.
    """

    schema_version: Literal["matintegrity.electrochemical_metal_loss_history.v1"] = (
        "matintegrity.electrochemical_metal_loss_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    mixed_potential_result: AssessmentResult
    mixed_potential_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    metal_reactions: tuple[MetalDissolutionReactionMapping, ...] = Field(min_length=1, max_length=32)
    linear_current_reconstruction_reviewed: bool
    mixed_potential_reference_area_reviewed: bool
    reaction_to_removed_metal_mapping_reviewed: bool
    uniform_recession_over_mapped_area_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_source_and_mappings(self):
        result = self.mixed_potential_result
        if result.model_id != "electrochemistry.crevice_mixed_potential_history" or result.status != "computed":
            raise ValueError("a computed mixed-potential AssessmentResult is required")
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("mixed-potential input digest does not match request and context")
        if canonical_digest(result.model_dump(mode="json")) != self.mixed_potential_result_sha256:
            raise ValueError("mixed-potential result digest mismatch")
        history = result.values.get("mixed_potential_history")
        if not isinstance(history, list) or len(history) < 2:
            raise ValueError("mixed-potential history must contain at least two knots")
        if result.values.get("mixed_potential_history_sha256") != canonical_digest(history):
            raise ValueError("mixed-potential history digest mismatch")
        reactions = result.inputs.get("reactions")
        if not isinstance(reactions, list):
            raise ValueError("mixed-potential source inputs lack reaction definitions")
        electron_counts = {
            row.get("reaction_id"): row.get("electron_number")
            for row in reactions
            if isinstance(row, dict)
        }
        if len(electron_counts) != len(reactions) or any(
            not isinstance(key, str) or not isinstance(value, int) or isinstance(value, bool) or value < 1
            for key, value in electron_counts.items()
        ):
            raise ValueError("source reaction electron counts are incomplete or invalid")
        mapped_ids = [row.reaction_id for row in self.metal_reactions]
        if len(mapped_ids) != len(set(mapped_ids)):
            raise ValueError("metal reaction mappings must have unique reaction IDs")
        if not set(mapped_ids) <= set(electron_counts):
            raise ValueError("every metal mapping must resolve to an upstream reaction")
        upstream_ids = tuple(row.get("reaction_id") for row in history[0].get("reaction_responses", []))
        if len(upstream_ids) != len(set(upstream_ids)) or not set(mapped_ids) <= set(upstream_ids):
            raise ValueError("every metal mapping must resolve to an upstream branch response")
        previous_time = None
        for row in history:
            time_s = row.get("time_s")
            if isinstance(time_s, bool) or not isinstance(time_s, (int, float)) or not math.isfinite(time_s):
                raise ValueError("mixed-potential history requires finite time knots")
            if previous_time is not None and time_s <= previous_time:
                raise ValueError("mixed-potential history times must strictly increase")
            previous_time = time_s
            branches = row.get("reaction_responses")
            if not isinstance(branches, list) or tuple(item.get("reaction_id") for item in branches) != upstream_ids:
                raise ValueError("reaction branch identity and order must remain stable")
            for branch in branches:
                for field in (
                    "reference_area_signed_current_density_A_m2",
                    "reference_area_gross_anodic_current_density_A_m2",
                    "reference_area_gross_cathodic_current_density_A_m2",
                ):
                    value = branch.get(field)
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        raise ValueError(f"branch {field} must be finite")
                    if field != "reference_area_signed_current_density_A_m2" and value < 0.0:
                        raise ValueError(f"branch {field} must be a nonnegative magnitude")
        for mapping in self.metal_reactions:
            source_reaction = next(row for row in reactions if row["reaction_id"] == mapping.reaction_id)
            if mapping.anodic_direction_is_metal_dissolution_reviewed and source_reaction.get(
                "kinetics_and_anodic_direction_reviewed"
            ) is not True:
                raise ValueError("metal dissolution mapping requires reviewed upstream anodic reaction direction")
        return self


def electrochemical_metal_loss_history(x: ElectrochemicalMetalLossHistory) -> Calculation:
    result = x.mixed_potential_result
    source = result.values["mixed_potential_history"]
    input_reactions = {row["reaction_id"]: row for row in result.inputs["reactions"]}
    maps = {row.reaction_id: row for row in x.metal_reactions}
    base = {
        "assessment_id": x.assessment_id,
        "material_condition_id": x.material_condition_id,
        "asset_id": result.values["asset_id"],
        "location_id": result.values["location_id"],
        "physical_scope_id": result.values["physical_scope_id"],
        "clock_id": result.values["clock_id"],
        "mixed_potential_result_sha256": x.mixed_potential_result_sha256,
        "mixed_potential_history_sha256": result.values["mixed_potential_history_sha256"],
        "reference_area_m2": result.values["reference_area_m2"],
        "integration_method": "piecewise_linear_current_density_exact_trapezoid",
        "reaction_to_metal_mapping": [row.model_dump(mode="json") for row in x.metal_reactions],
    }
    reviews = {
        "linear_current_reconstruction_reviewed": x.linear_current_reconstruction_reviewed,
        "mixed_potential_reference_area_reviewed": x.mixed_potential_reference_area_reviewed,
        "reaction_to_removed_metal_mapping_reviewed": x.reaction_to_removed_metal_mapping_reviewed,
        "uniform_recession_over_mapped_area_reviewed": x.uniform_recession_over_mapped_area_reviewed,
        "computational_use_authorized": x.computational_use_authorized,
        **{
            f"reaction[{row.reaction_id}].anodic_direction_is_metal_dissolution_reviewed": row.anodic_direction_is_metal_dissolution_reviewed
            for row in x.metal_reactions
        },
        **{
            f"reaction[{row.reaction_id}].alloy_and_metal_basis_reviewed": row.alloy_and_metal_basis_reviewed
            for row in x.metal_reactions
        },
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    reference_area = result.values["reference_area_m2"]
    cumulative = {
        reaction_id: {"anodic_charge_C": 0.0, "cathodic_charge_C": 0.0, "signed_charge_C": 0.0,
                      "anodic_metal_mol": 0.0, "cathodic_metal_mol": 0.0, "net_metal_removal_mol": 0.0,
                      "anodic_mass_kg": 0.0, "cathodic_mass_kg": 0.0, "signed_mass_loss_kg": 0.0,
                      "signed_recession_m": 0.0}
        for reaction_id in maps
    }
    intervals = []
    for left, right in zip(source, source[1:]):
        dt = right["time_s"] - left["time_s"]
        rows = []
        for reaction_id, mapping in maps.items():
            left_branch = next(row for row in left["reaction_responses"] if row["reaction_id"] == reaction_id)
            right_branch = next(row for row in right["reaction_responses"] if row["reaction_id"] == reaction_id)
            electron_number = input_reactions[reaction_id]["electron_number"]
            exposed_area = input_reactions[reaction_id]["exposed_area_m2"]
            q_anodic = reference_area * dt * (
                left_branch["reference_area_gross_anodic_current_density_A_m2"]
                + right_branch["reference_area_gross_anodic_current_density_A_m2"]
            ) / 2.0
            q_cathodic = reference_area * dt * (
                left_branch["reference_area_gross_cathodic_current_density_A_m2"]
                + right_branch["reference_area_gross_cathodic_current_density_A_m2"]
            ) / 2.0
            q_signed = reference_area * dt * (
                left_branch["reference_area_signed_current_density_A_m2"]
                + right_branch["reference_area_signed_current_density_A_m2"]
            ) / 2.0
            anodic_extent = q_anodic / (electron_number * FARADAY_C_MOL)
            cathodic_extent = q_cathodic / (electron_number * FARADAY_C_MOL)
            signed_extent = q_signed / (electron_number * FARADAY_C_MOL)
            anodic_metal = anodic_extent * mapping.metal_atoms_per_reaction_extent
            cathodic_metal = cathodic_extent * mapping.metal_atoms_per_reaction_extent
            net_metal = signed_extent * mapping.metal_atoms_per_reaction_extent
            anodic_mass = anodic_metal * mapping.molar_mass_kg_mol
            cathodic_mass = cathodic_metal * mapping.molar_mass_kg_mol
            signed_mass = net_metal * mapping.molar_mass_kg_mol
            recession = signed_mass / (mapping.density_kg_m3 * exposed_area)
            values = (q_anodic, q_cathodic, q_signed, anodic_metal, cathodic_metal, net_metal,
                      anodic_mass, cathodic_mass, signed_mass, recession)
            if not all(math.isfinite(value) for value in values):
                return Calculation(status="out_of_scope", values=base | {
                    "failed_interval_start_s": left["time_s"],
                    "failed_interval_end_s": right["time_s"],
                    "failure_reason": "integrated_metal_loss_exceeds_finite_numeric_support",
                    "computed_prefix": intervals,
                })
            cumulative[reaction_id]["anodic_charge_C"] += q_anodic
            cumulative[reaction_id]["cathodic_charge_C"] += q_cathodic
            cumulative[reaction_id]["signed_charge_C"] += q_signed
            cumulative[reaction_id]["anodic_metal_mol"] += anodic_metal
            cumulative[reaction_id]["cathodic_metal_mol"] += cathodic_metal
            cumulative[reaction_id]["net_metal_removal_mol"] += net_metal
            cumulative[reaction_id]["anodic_mass_kg"] += anodic_mass
            cumulative[reaction_id]["cathodic_mass_kg"] += cathodic_mass
            cumulative[reaction_id]["signed_mass_loss_kg"] += signed_mass
            cumulative[reaction_id]["signed_recession_m"] += recession
            if not all(math.isfinite(value) for value in cumulative[reaction_id].values()):
                return Calculation(status="out_of_scope", values=base | {
                    "failed_interval_start_s": left["time_s"],
                    "failed_interval_end_s": right["time_s"],
                    "failure_reason": "cumulative_metal_loss_exceeds_finite_numeric_support",
                    "computed_prefix": intervals,
                })
            rows.append({
                "reaction_id": reaction_id,
                "metal_species_id": mapping.metal_species_id,
                "electron_number": electron_number,
                "exposed_area_m2": exposed_area,
                "anodic_charge_C": q_anodic,
                "cathodic_charge_C": q_cathodic,
                "signed_charge_C": q_signed,
                "anodic_metal_removal_mol": anodic_metal,
                "cathodic_metal_equivalent_mol": cathodic_metal,
                "net_metal_removal_mol": net_metal,
                "anodic_mass_loss_kg": anodic_mass,
                "cathodic_metal_equivalent_kg": cathodic_mass,
                "signed_net_mass_loss_kg": signed_mass,
                "signed_area_average_recession_m": recession,
                "cumulative": dict(cumulative[reaction_id]),
            })
        intervals.append({"start_time_s": left["time_s"], "end_time_s": right["time_s"],
                          "reaction_metal_loss": rows})
    return Calculation(values=base | {
        "interval_metal_loss": intervals,
        "cumulative_metal_loss_by_reaction": cumulative,
        "metal_loss_history_sha256": canonical_digest({"intervals": intervals, "cumulative": cumulative}),
    }, notes=(
        "Positive mapped anodic reaction extent is caller-declared metal dissolution; cathodic equivalent and signed net transfer are reported separately.",
        "Current density is integrated exactly for the caller-reviewed linear interpolation between upstream time knots and the pinned reference area. Uniform recession is a caller-reviewed area average, not localized attack.",
        "This conversion does not qualify kinetics, infer alloy dissolution selectivity, model films/passivity, or establish corrosion rate acceptance, life, probability or fitness for service.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.electrochemical_partial_current_metal_loss",
        ElectrochemicalMetalLossHistory,
        electrochemical_metal_loss_history,
        {
            "reference_area_m2": "m2",
            "interval_metal_loss[].start_time_s": "s",
            "interval_metal_loss[].end_time_s": "s",
            "interval_metal_loss[].reaction_metal_loss[].anodic_charge_C": "C",
            "interval_metal_loss[].reaction_metal_loss[].cathodic_charge_C": "C",
            "interval_metal_loss[].reaction_metal_loss[].signed_charge_C": "C",
            "interval_metal_loss[].reaction_metal_loss[].anodic_metal_removal_mol": "mol",
            "interval_metal_loss[].reaction_metal_loss[].cathodic_metal_equivalent_mol": "mol",
            "interval_metal_loss[].reaction_metal_loss[].net_metal_removal_mol": "mol",
            "interval_metal_loss[].reaction_metal_loss[].anodic_mass_loss_kg": "kg",
            "interval_metal_loss[].reaction_metal_loss[].cathodic_metal_equivalent_kg": "kg",
            "interval_metal_loss[].reaction_metal_loss[].signed_net_mass_loss_kg": "kg",
            "interval_metal_loss[].reaction_metal_loss[].signed_area_average_recession_m": "m",
            "cumulative_metal_loss_by_reaction.*.signed_recession_m": "m",
        },
        (
            "A digest-pinned computed mixed-potential history is required; branch electron number and exposed area are read from that exact upstream request.",
            "Partial current is integrated using an exact trapezoidal integral under an explicit piecewise-linear between-knot review.",
            "Metal mapping, anodic dissolution direction, alloy basis and uniform area-average recession are caller-reviewed inputs; cathodic-equivalent and signed net quantities remain separately visible.",
        ),
        ("electrochemical_partial_current_to_metal_loss",),
        qualification="user_model",
        context_validator=_same_upstream_context,
    )]


def _same_upstream_context(x: ElectrochemicalMetalLossHistory, context: RunContext) -> None:
    upstream = x.mixed_potential_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        upstream.asset_id,
        upstream.location_id,
        upstream.time_basis,
    ):
        raise ValueError("metal-loss run context must match upstream asset, location and time basis")
