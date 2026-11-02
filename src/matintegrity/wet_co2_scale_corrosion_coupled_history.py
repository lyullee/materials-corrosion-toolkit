"""Operator-split history coupling scale thickness, film-limited kinetics and metal recession."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_transport_limited_mixed_potential import (
    WetCo2TransportLimitedMixedPotentialRequest,
    evaluate_wet_co2_transport_limited_mixed_potential,
)

MODEL_ID = "integration.wet_co2_scale_corrosion_moving_geometry_history"
SOURCE_ID = "caller_wet_co2_scale_growth_per_metal_dissolution_mapping"
SCALE_SOURCE_ID = "caller_wet_co2_scale_phase_molar_volume_and_external_flux"


class WetCo2MetalToScaleYield(Contract):
    reaction_id: str = Field(min_length=1)
    metal_atoms_per_reaction_extent: Positive
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive
    scale_moles_per_metal_mole: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    evidence: Evidence
    alloy_volume_additivity_reviewed: bool
    metal_to_scale_stoichiometry_reviewed: bool

    @model_validator(mode="after")
    def provider_match(self):
        if self.provider_id != self.evidence.source_id:
            raise ValueError("metal/scale mapping provider must match Evidence source ID")
        if self.evidence.sha256 is None:
            raise ValueError("metal/scale mapping Evidence must include a content SHA-256")
        return self


class WetCo2MovingScaleInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    mixed_potential_request: WetCo2TransportLimitedMixedPotentialRequest
    external_net_scale_formation_flux_mol_m2_s: float
    external_flux_provider_id: str = Field(min_length=1)
    external_flux_provider_revision: str = Field(min_length=1)
    external_flux_source_record_id: str = Field(min_length=1)
    external_flux_evidence: Evidence
    external_scale_flux_reviewed: bool

    @model_validator(mode="after")
    def validate_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("moving-scale interval end must exceed start")
        if isinstance(self.external_net_scale_formation_flux_mol_m2_s, bool) or not math.isfinite(self.external_net_scale_formation_flux_mol_m2_s):
            raise ValueError("external net scale flux must be finite and signed")
        if self.external_flux_provider_id != self.external_flux_evidence.source_id:
            raise ValueError("external flux provider must match Evidence source ID")
        if self.external_flux_evidence.sha256 is None:
            raise ValueError("external scale-flux Evidence must include a content SHA-256")
        return self


class WetCo2ScaleCorrosionMovingGeometryHistoryRequest(Contract):
    initial_wall_thickness_m: Positive
    initial_scale_thickness_m: Positive
    scale_molar_volume_m3_mol: Positive
    scale_property_provider_id: str = Field(min_length=1)
    scale_property_provider_revision: str = Field(min_length=1)
    scale_property_source_record_id: str = Field(min_length=1)
    scale_property_evidence: Evidence
    metal_to_scale_yields: tuple[WetCo2MetalToScaleYield, ...] = Field(min_length=1, max_length=32)
    intervals: tuple[WetCo2MovingScaleInterval, ...] = Field(min_length=1, max_length=10000)
    initial_geometry_and_attachment_reviewed: bool
    interval_clock_and_asset_scope_reviewed: bool
    piecewise_constant_operator_split_reviewed: bool
    uniform_wall_recession_and_volume_additivity_reviewed: bool

    @model_validator(mode="after")
    def validate_history(self):
        if self.scale_property_provider_id != self.scale_property_evidence.source_id:
            raise ValueError("scale property provider must match Evidence source ID")
        if self.scale_property_evidence.sha256 is None:
            raise ValueError("scale property Evidence must include a content SHA-256")
        if len({row.reaction_id for row in self.metal_to_scale_yields}) != len(self.metal_to_scale_yields):
            raise ValueError("metal-to-scale reaction mappings must have unique IDs")
        for left, right in zip(self.intervals[:-1], self.intervals[1:], strict=True):
            if left.end_time_s != right.start_time_s:
                raise ValueError("moving-scale intervals must be contiguous exact knots")
        yield_ids = {row.reaction_id for row in self.metal_to_scale_yields}
        for interval in self.intervals:
            reaction_ids = {row.reaction_id for row in interval.mixed_potential_request.reactions}
            if reaction_ids != yield_ids:
                raise ValueError("every interval must use the exact mapped metal-dissolution reaction set")
        return self


def evaluate_wet_co2_scale_corrosion_moving_geometry_history(
    request: WetCo2ScaleCorrosionMovingGeometryHistoryRequest,
) -> Calculation:
    """Solve each interval at its start geometry, then advance wall and scale.

    Scale growth per area is the caller's net external scale formation flux
    plus a caller-defined yield times the computed anodic metal dissolution
    extent. Area-average wall recession uses caller metal molar mass/density.
    The evolved scale thickness becomes the next interval's diffusion-film
    thickness. This is a sequential operator split, not simultaneous feedback
    within each interval.
    """
    flags = {
        "initial_geometry_and_attachment_reviewed": request.initial_geometry_and_attachment_reviewed,
        "interval_clock_and_asset_scope_reviewed": request.interval_clock_and_asset_scope_reviewed,
        "piecewise_constant_operator_split_reviewed": request.piecewise_constant_operator_split_reviewed,
        "uniform_wall_recession_and_volume_additivity_reviewed": request.uniform_wall_recession_and_volume_additivity_reviewed,
    }
    base = {
        "model_id": MODEL_ID,
        "initial_wall_thickness_m": request.initial_wall_thickness_m,
        "initial_scale_thickness_m": request.initial_scale_thickness_m,
        "scale_molar_volume_m3_mol": request.scale_molar_volume_m3_mol,
        "scale_property_evidence_sha256": request.scale_property_evidence.sha256,
        "interval_count": len(request.intervals),
        "interpolation_performed": False,
        "simultaneous_within_interval_kinetics_geometry_feedback": False,
    }
    missing = [key for key, value in flags.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    if any(
        not row.alloy_volume_additivity_reviewed or not row.metal_to_scale_stoichiometry_reviewed
        for row in request.metal_to_scale_yields
    ):
        return Calculation(status="needs_data", values=base | {"reason": "metal_volume_or_scale_yield_mapping_not_reviewed"})

    mappings = {row.reaction_id: row for row in request.metal_to_scale_yields}
    wall_thickness = request.initial_wall_thickness_m
    scale_thickness = request.initial_scale_thickness_m
    cumulative_wall_recession = 0.0
    cumulative_anodic_metal_loss_mol_m2: dict[str, float] = {key: 0.0 for key in mappings}
    history = [{
        "time_s": request.intervals[0].start_time_s,
        "wall_thickness_m": wall_thickness,
        "scale_thickness_m": scale_thickness,
        "scale_inventory_mol_m2": scale_thickness / request.scale_molar_volume_m3_mol,
        "cumulative_wall_recession_m": 0.0,
    }]
    ledger = []
    for index, interval in enumerate(request.intervals):
        if not interval.external_scale_flux_reviewed:
            return Calculation(status="needs_data", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "reason": "external_scale_formation_or_dissolution_flux_not_reviewed",
            })
        if scale_thickness <= 0.0 or wall_thickness <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "reason": "wall_or_scale_geometry_depleted",
            })
        nested = interval.mixed_potential_request
        # Keep tuple-valued nested fields as tuples while rebuilding the validated
        # request. JSON-mode dumps turn them into lists, which strict tuple
        # contracts correctly reject even though the source request was valid.
        film_records = [
            film.model_dump(mode="python") | {"film_thickness_m": scale_thickness}
            for film in nested.reactant_films
        ]
        nested_data = nested.model_dump(mode="python")
        nested_data["reactant_films"] = tuple(film_records)
        try:
            updated_request = WetCo2TransportLimitedMixedPotentialRequest.model_validate(nested_data)
        except Exception as exc:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "reason": "evolved_scale_transport_request_invalid",
                "detail": str(exc),
            })
        electrochemical = evaluate_wet_co2_transport_limited_mixed_potential(updated_request)
        if electrochemical.status != "computed":
            return Calculation(status=electrochemical.status, values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "failed_electrochemical_calculation": electrochemical.model_dump(mode="json"),
                "reason": "transport_limited_mixed_potential_interval_not_computed",
            })
        dt = interval.end_time_s - interval.start_time_s
        reactions = {row.reaction_id: row for row in nested.reactions}
        reaction_results = electrochemical.values["reaction_results"]
        anodic_metal_flux = {}
        product_scale_flux = 0.0
        reaction_ledger = []
        for reaction_id, mapping in mappings.items():
            response = reaction_results[reaction_id]
            reaction = reactions[reaction_id]
            anodic_extent = response["anodic_current_density_A_m2"] / (reaction.electron_count * 96485.33212)
            metal_flux = anodic_extent * mapping.metal_atoms_per_reaction_extent
            mass_flux = metal_flux * mapping.metal_molar_mass_kg_mol
            recession_rate = mass_flux / mapping.metal_density_kg_m3
            scale_flux = metal_flux * mapping.scale_moles_per_metal_mole
            if not all(math.isfinite(value) and value >= 0.0 for value in (anodic_extent, metal_flux, mass_flux, recession_rate, scale_flux)):
                return Calculation(status="out_of_scope", values=base | {
                    "committed_interval_count": index,
                    "failed_interval_index": index,
                    "history_prefix": history,
                    "interval_ledger": ledger,
                    "reason": "metal_or_scale_conversion_exceeds_finite_support",
                })
            anodic_metal_flux[reaction_id] = metal_flux
            product_scale_flux += scale_flux
            reaction_ledger.append({
                "reaction_id": reaction_id,
                "anodic_extent_flux_mol_m2_s": anodic_extent,
                "anodic_metal_loss_flux_mol_m2_s": metal_flux,
                "metal_mass_flux_kg_m2_s": mass_flux,
                "wall_recession_rate_m_s": recession_rate,
                "scale_product_flux_mol_m2_s": scale_flux,
            })
        recession_delta = math.fsum(
            anodic_metal_flux[key] * mapping.metal_molar_mass_kg_mol / mapping.metal_density_kg_m3
            for key, mapping in mappings.items()
        ) * dt
        net_scale_flux = product_scale_flux + interval.external_net_scale_formation_flux_mol_m2_s
        scale_inventory_start = scale_thickness / request.scale_molar_volume_m3_mol
        scale_inventory_end = scale_inventory_start + net_scale_flux * dt
        if not math.isfinite(scale_inventory_end) or scale_inventory_end < 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "reason": "caller_dissolution_exceeds_available_scale_inventory",
                "scale_inventory_start_mol_m2": scale_inventory_start,
                "scale_inventory_trial_end_mol_m2": scale_inventory_end,
            })
        wall_end = wall_thickness - recession_delta
        scale_end = scale_inventory_end * request.scale_molar_volume_m3_mol
        if not math.isfinite(wall_end) or wall_end <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "reason": "substrate_wall_thickness_depleted_during_interval",
            })
        cumulative_wall_recession += recession_delta
        for key, amount in anodic_metal_flux.items():
            cumulative_anodic_metal_loss_mol_m2[key] += amount * dt
        ledger.append({
            "interval_index": index,
            "interval_id": interval.interval_id,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "start_wall_thickness_m": wall_thickness,
            "end_wall_thickness_m": wall_end,
            "start_scale_thickness_m": scale_thickness,
            "end_scale_thickness_m": scale_end,
            "scale_inventory_start_mol_m2": scale_inventory_start,
            "scale_inventory_end_mol_m2": scale_inventory_end,
            "scale_external_flux_mol_m2_s": interval.external_net_scale_formation_flux_mol_m2_s,
            "scale_from_anodic_metal_flux_mol_m2_s": product_scale_flux,
            "net_scale_formation_flux_mol_m2_s": net_scale_flux,
            "metal_reaction_ledger": reaction_ledger,
            "electrochemical_result_sha256": canonical_digest(electrochemical.model_dump(mode="json")),
            "boundary_sha256": nested.boundary_sha256,
            "mixed_potential_V": electrochemical.values["mixed_potential_V"],
        })
        wall_thickness = wall_end
        scale_thickness = scale_end
        history.append({
            "time_s": interval.end_time_s,
            "wall_thickness_m": wall_thickness,
            "scale_thickness_m": scale_thickness,
            "scale_inventory_mol_m2": scale_inventory_end,
            "cumulative_wall_recession_m": cumulative_wall_recession,
            "cumulative_anodic_metal_loss_mol_m2": dict(cumulative_anodic_metal_loss_mol_m2),
        })
    return Calculation(values=base | {
        "all_intervals_computed": True,
        "final_wall_thickness_m": wall_thickness,
        "final_scale_thickness_m": scale_thickness,
        "final_scale_inventory_mol_m2": scale_thickness / request.scale_molar_volume_m3_mol,
        "cumulative_wall_recession_m": cumulative_wall_recession,
        "cumulative_anodic_metal_loss_mol_m2": cumulative_anodic_metal_loss_mol_m2,
        "state_history": history,
        "interval_ledger": ledger,
    }, notes=(
        "At each exact interval knot, the current scale thickness is applied as the film thickness in the transport-limited mixed-potential solve; interval metal/scale rates are then held to the endpoint.",
        "Scale gain from metal dissolution uses only caller stoichiometric yield; an independent caller flux may add or remove scale.",
        "This is sequential operator splitting, not simultaneous moving-mesh diffusion, local geometry, or scale-adhesion physics.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        WetCo2ScaleCorrosionMovingGeometryHistoryRequest,
        evaluate_wet_co2_scale_corrosion_moving_geometry_history,
        {
            "time_s": "s",
            "wall_thickness_m": "m",
            "scale_thickness_m": "m",
            "cumulative_wall_recession_m": "m",
            "final_scale_inventory_mol_m2": "mol/m2",
            "cumulative_anodic_metal_loss_mol_m2.*": "mol/m2",
        },
        (
            "Scale molar volume, metal conversion, product yield and external scale formation/dissolution schedules are caller provided and evidence linked.",
            "Each interval re-evaluates a film-limited mixed potential using the current scale thickness, then advances wall and scale geometry with piecewise-constant rates.",
            "The sequential update does not implement simultaneous kinetic-transport feedback, local corrosion morphology, or experimentally qualified protection laws.",
        ),
        (SOURCE_ID, SCALE_SOURCE_ID, "integration.wet_co2_film_transport_limited_mixed_potential"),
    )]
