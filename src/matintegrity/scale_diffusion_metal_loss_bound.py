"""Translate one scale-limited product flux into a caller-mapped metal-loss ceiling."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, RunContext, canonical_digest
from .registry import ModelSpec


class ScaleLimitedMetalDissolutionPathway(Contract):
    """Caller reaction stoichiometry and metal properties for one productive branch."""

    reaction_id: str = Field(min_length=1)
    transported_species_id: str = Field(min_length=1)
    transported_species_mol_per_reaction_extent: Positive
    dissolved_metal_species_id: str = Field(min_length=1)
    metal_atoms_per_reaction_extent: Positive
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    property_provider_id: str = Field(min_length=1)
    property_provider_revision: str = Field(min_length=1)
    property_record_id: str = Field(min_length=1)
    property_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def property_record_is_evidenced(self):
        if not any(
            item.source_id == self.property_provider_id
            and item.sha256 == self.property_record_sha256
            for item in self.evidence
        ):
            raise ValueError("metal property provider and digest must match declared Evidence")
        return self


class ScaleDiffusionMetalLossBound(Contract):
    """Derive a finite dissolution-rate ceiling from a computed scale flux cap."""

    schema_version: Literal["matintegrity.scale_diffusion_metal_loss_bound.v1"] = (
        "matintegrity.scale_diffusion_metal_loss_bound.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    scale_transport_result: AssessmentResult
    scale_transport_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    surface_area_basis_id: str = Field(min_length=1)
    exposure_duration_s: Positive
    candidate_pathways: tuple[ScaleLimitedMetalDissolutionPathway, ...] = Field(min_length=1, max_length=64)
    sustained_steady_flux_limit_reviewed: bool
    complete_productive_branch_set_reviewed: bool
    reaction_stoichiometry_and_metal_mapping_reviewed: bool
    common_area_density_and_uniform_recession_reviewed: bool
    scope_state_and_duration_transfer_reviewed: bool
    no_other_metal_loss_path_over_duration_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_transport_and_reaction_mapping(self):
        result = self.scale_transport_result
        if result.status != "computed" or result.model_id != "chemistry.layered_scale_diffusion_limit":
            raise ValueError("a computed layered-scale diffusion-limit assessment is required")
        if result.units.get("area_average_flux_limit_mol_m2_s") not in {"mol/m2/s", "mol/m^2/s"}:
            raise ValueError("scale transport assessment must declare a molar area-flux unit")
        if canonical_digest(result.model_dump(mode="json")) != self.scale_transport_result_sha256:
            raise ValueError("scale transport result digest does not match")
        if result.input_digest != canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        }):
            raise ValueError("scale transport registry input digest does not match its inputs and context")
        values = result.values
        if values.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("scale transport result must match the declared physical scope")
        if values.get("surface_area_basis_id") != self.surface_area_basis_id:
            raise ValueError("metal recession area basis must match the scale transport area basis")
        cap = values.get("area_average_flux_limit_mol_m2_s")
        if isinstance(cap, bool) or not isinstance(cap, (int, float)) or not math.isfinite(cap) or cap < 0:
            raise ValueError("scale transport result must provide a finite nonnegative average flux cap")
        species_ids = {path.transported_species_id for path in self.candidate_pathways}
        reaction_ids = [path.reaction_id for path in self.candidate_pathways]
        metal_ids = {path.dissolved_metal_species_id for path in self.candidate_pathways}
        property_bases = {
            (path.property_provider_id, path.property_provider_revision, path.property_record_id, path.property_record_sha256)
            for path in self.candidate_pathways
        }
        if len(species_ids) != 1 or values.get("transported_species_id") not in species_ids:
            raise ValueError("every reaction branch must map to the scale-limited transported species")
        if len(set(reaction_ids)) != len(reaction_ids):
            raise ValueError("candidate reaction IDs must be unique")
        if len(metal_ids) != 1 or len(property_bases) != 1:
            raise ValueError("candidate branches must share one dissolved metal and one pinned property record")
        return self


def evaluate_scale_diffusion_metal_loss_bound(request: ScaleDiffusionMetalLossBound) -> Calculation:
    """Compute a conditional constant-duration metal penetration upper bound."""
    scale = request.scale_transport_result
    scale_values = scale.values
    cap = float(scale_values["area_average_flux_limit_mol_m2_s"])
    request_digest = canonical_digest(request.model_dump(mode="json"))
    reviews = {
        "sustained_steady_flux_limit_reviewed": request.sustained_steady_flux_limit_reviewed,
        "complete_productive_branch_set_reviewed": request.complete_productive_branch_set_reviewed,
        "reaction_stoichiometry_and_metal_mapping_reviewed": request.reaction_stoichiometry_and_metal_mapping_reviewed,
        "common_area_density_and_uniform_recession_reviewed": request.common_area_density_and_uniform_recession_reviewed,
        "scope_state_and_duration_transfer_reviewed": request.scope_state_and_duration_transfer_reviewed,
        "no_other_metal_loss_path_over_duration_reviewed": request.no_other_metal_loss_path_over_duration_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    common = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "input_sha256": request_digest,
        "scale_transport_model_id": scale.model_id,
        "scale_transport_result_sha256": request.scale_transport_result_sha256,
        "scale_transport_request_input_sha256": scale.input_digest,
        "scale_state_id": scale_values.get("scale_state_id"),
        "scale_history_result_digest": scale_values.get("scale_history_result_digest"),
        "scale_history_time_s": scale_values.get("scale_history_time_s"),
        "surface_area_basis_id": request.surface_area_basis_id,
        "transported_species_id": scale_values.get("transported_species_id"),
        "area_average_flux_limit_mol_m2_s": cap,
        "exposure_duration_s": request.exposure_duration_s,
        "candidate_pathways": [path.model_dump(mode="json") for path in request.candidate_pathways],
        "flux_cap_interpretation": "caller-reviewed sustained ceiling over the declared duration; not an estimated operating flux",
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=common | {"missing_reviews": missing})

    pathway_results = []
    for path in request.candidate_pathways:
        extent_flux = cap / path.transported_species_mol_per_reaction_extent
        metal_atom_flux = extent_flux * path.metal_atoms_per_reaction_extent
        mass_flux = metal_atom_flux * path.metal_molar_mass_kg_mol
        penetration_rate = mass_flux / path.metal_density_kg_m3
        penetration_loss = penetration_rate * request.exposure_duration_s
        if not all(math.isfinite(value) and value >= 0 for value in (
            extent_flux, metal_atom_flux, mass_flux, penetration_rate, penetration_loss,
        )):
            return Calculation(status="out_of_scope", values=common | {
                "reason": "transport_to_metal_conversion_exceeds_finite_numeric_support",
                "unsupported_reaction_id": path.reaction_id,
                "completed_pathway_results": pathway_results,
            })
        pathway_results.append({
            "reaction_id": path.reaction_id,
            "dissolved_metal_species_id": path.dissolved_metal_species_id,
            "reactant_flux_ceiling_mol_m2_s": extent_flux,
            "metal_atom_flux_ceiling_mol_m2_s": metal_atom_flux,
            "metal_mass_flux_ceiling_kg_m2_s": mass_flux,
            "uniform_penetration_rate_ceiling_m_s": penetration_rate,
            "uniform_penetration_loss_ceiling_m": penetration_loss,
            "metal_property_provider_id": path.property_provider_id,
            "metal_property_provider_revision": path.property_provider_revision,
            "metal_property_record_id": path.property_record_id,
            "metal_property_record_sha256": path.property_record_sha256,
            "metal_property_evidence": [row.model_dump(mode="json") for row in path.evidence],
        })
    maximum = max(pathway_results, key=lambda row: row["uniform_penetration_loss_ceiling_m"])
    return Calculation(values=common | {
        "pathway_rate_ceilings": pathway_results,
        "maximum_uniform_penetration_rate_ceiling_m_s": maximum["uniform_penetration_rate_ceiling_m_s"],
        "maximum_uniform_penetration_loss_ceiling_m": maximum["uniform_penetration_loss_ceiling_m"],
        "maximum_bound_reaction_id": maximum["reaction_id"],
        "bound_semantics": "maximum_candidate_metal_per_transported_species_ratio_times_the_caller_scale_flux_ceiling",
        "not_inferred": ["actual_electrochemical_current", "reaction_branch_allocation", "kinetic_corrosion_rate", "localization_factor", "remaining_life", "acceptance", "failure_probability"],
    }, notes=(
        "The computed value is a transport-compatible ceiling conditional on every mapped dissolution route passing through the same scale-limited product flux.",
        "The ceiling assumes the exact caller scale state, flux bound and material mapping remain applicable for the full declared duration.",
        "It is not an actual corrosion-rate estimate and does not qualify the scale or electrochemical model.",
    ))


def _validate_scale_transport_context(request: ScaleDiffusionMetalLossBound, context: RunContext) -> None:
    """Require the adapter assessment to retain its source asset/location/clock identity."""
    upstream = request.scale_transport_result.context
    for field in ("asset_id", "location_id", "time_basis"):
        if getattr(context, field) != getattr(upstream, field):
            raise ValueError(f"outer RunContext {field} must match the scale transport assessment")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="corrosion.scale_diffusion_metal_loss_bound",
        input_type=ScaleDiffusionMetalLossBound,
        evaluator=evaluate_scale_diffusion_metal_loss_bound,
        units={
            "area_average_flux_limit_mol_m2_s": "mol/m^2/s",
            "exposure_duration_s": "s",
            "pathway_rate_ceilings[].reactant_flux_ceiling_mol_m2_s": "mol/m^2/s",
            "pathway_rate_ceilings[].metal_atom_flux_ceiling_mol_m2_s": "mol/m^2/s",
            "pathway_rate_ceilings[].metal_mass_flux_ceiling_kg_m2_s": "kg/m^2/s",
            "pathway_rate_ceilings[].uniform_penetration_rate_ceiling_m_s": "m/s",
            "pathway_rate_ceilings[].uniform_penetration_loss_ceiling_m": "m",
            "maximum_uniform_penetration_rate_ceiling_m_s": "m/s",
            "maximum_uniform_penetration_loss_ceiling_m": "m",
        },
        assumptions=(
            "A single computed layered-scale flux limit caps a caller-declared complete set of branches that produce the same transported species.",
            "For each branch, transported-species stoichiometry maps its area molar-flux ceiling to an extent ceiling, then caller metal stoichiometry and pinned mass/density map that ceiling to uniform recession.",
            "The maximum branch ratio is a conditional upper envelope when the branch allocation is unknown; it is not a current, corrosion-rate prediction or probability.",
            "The caller-reviewed steady transport ceiling and material state are assumed maintained for the supplied duration; no time integration of changing scale state is performed.",
        ),
        source_ids=("caller_scale_diffusion_metal_loss_bound",),
        qualification="user_model",
        context_validator=_validate_scale_transport_context,
    )]
