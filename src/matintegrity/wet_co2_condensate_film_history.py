"""Integrate caller-supplied net condensate flux into a bounded wall-film inventory history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_condensate_film_history"
SOURCE_ID = "caller_net_retained_condensate_flux_history"
MAX_INTERVALS = 100000


class WetCo2CondensateFilmInterval(Contract):
    """One constant net retained-water flux interval on a declared wall patch."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    net_retained_water_mass_flux_kg_m2_s: float
    liquid_water_density_kg_m3: float = Field(gt=0)
    flux_provider_id: str = Field(min_length=1)
    flux_provider_revision: str = Field(min_length=1)
    flux_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    flux_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    density_provider_id: str = Field(min_length=1)
    density_provider_revision: str = Field(min_length=1)
    density_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=2, max_length=64)
    interval_state_and_units_reviewed: bool

    @model_validator(mode="after")
    def finite_and_provenance(self):
        numeric = (
            self.start_time_s, self.end_time_s,
            self.net_retained_water_mass_flux_kg_m2_s, self.liquid_water_density_kg_m3,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("interval time, flux and density must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must be after start")
        evidence_ids = {row.source_id for row in self.evidence}
        if not {self.flux_provider_id, self.density_provider_id}.issubset(evidence_ids):
            raise ValueError("Evidence must identify the net retained flux and water density sources")
        if not any(
            row.source_id == self.density_provider_id and row.sha256 == self.density_record_sha256
            for row in self.evidence
        ):
            raise ValueError("water-density record digest must match its Evidence")
        return self


class WetCo2CondensateFilmHistoryRequest(Contract):
    """Finite nonnegative condensate areal inventory for one fixed wall patch."""

    schema_version: Literal["matintegrity.wet_co2_condensate_film_history.v1"] = (
        "matintegrity.wet_co2_condensate_film_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    wall_patch_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    initial_water_areal_inventory_kg_m2: float = Field(ge=0)
    intervals: tuple[WetCo2CondensateFilmInterval, ...] = Field(min_length=1, max_length=MAX_INTERVALS)
    fixed_wall_patch_and_area_basis_reviewed: bool
    net_flux_includes_retention_drainage_and_evaporation_reviewed: bool
    uniform_film_thickness_interpretation_reviewed: bool
    no_lateral_water_exchange_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def contiguous_history(self):
        if not math.isfinite(self.initial_water_areal_inventory_kg_m2):
            raise ValueError("initial water inventory must be finite")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("film history must start at time zero")
        if any(
            left.end_time_s != right.start_time_s
            for left, right in zip(self.intervals[:-1], self.intervals[1:])
        ):
            raise ValueError("film intervals must be exactly contiguous")
        return self


def evaluate_wet_co2_condensate_film_history(request: WetCo2CondensateFilmHistoryRequest) -> Calculation:
    """Integrate net water source/sink, clamping sink removal when the wall patch dries."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "wall_patch_id": request.wall_patch_id,
        "condition_id": request.condition_id,
        "input_sha256": input_sha,
        "initial_water_areal_inventory_kg_m2": request.initial_water_areal_inventory_kg_m2,
    }
    reviews = (
        "fixed_wall_patch_and_area_basis_reviewed",
        "net_flux_includes_retention_drainage_and_evaporation_reviewed",
        "uniform_film_thickness_interpretation_reviewed",
        "no_lateral_water_exchange_reviewed",
        "calculation_use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    missing.extend(
        f"interval[{index}].interval_state_and_units_reviewed"
        for index, interval in enumerate(request.intervals)
        if not interval.interval_state_and_units_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "inventory_history": [],
            "interval_ledger": [],
        })

    inventory = request.initial_water_areal_inventory_kg_m2
    current_wet_start = 0.0 if inventory > 0.0 else None
    cumulative_condensation = 0.0
    cumulative_liquid_sink = 0.0
    cumulative_sink_unmet = 0.0
    total_wet_duration = 0.0
    maximum_contiguous_wet_duration = 0.0
    current_contiguous_wet_duration = 0.0
    history: list[dict] = []
    first_density = request.intervals[0].liquid_water_density_kg_m3
    initial_thickness = inventory / first_density
    if not math.isfinite(initial_thickness):
        return Calculation(status="out_of_scope", values=base | {
            "failure_reason": "initial equivalent film thickness exceeds finite numeric support",
        })
    history.append({
        "time_s": 0.0,
        "water_areal_inventory_kg_m2": inventory,
        "uniform_equivalent_film_thickness_m": initial_thickness,
        "wet_state": inventory > 0.0,
        "origin": "caller_initial_inventory",
    })
    ledger: list[dict] = []

    for index, interval in enumerate(request.intervals):
        dt = interval.end_time_s - interval.start_time_s
        flux = interval.net_retained_water_mass_flux_kg_m2_s
        inventory_start = inventory
        requested_transfer = flux * dt
        if not math.isfinite(requested_transfer):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "inventory_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "integrated water flux exceeds finite numeric support",
            })

        if flux >= 0.0:
            admitted_transfer = requested_transfer
            inventory_end = inventory_start + admitted_transfer
            requested_sink_unmet = 0.0
            condensation_added = admitted_transfer
            liquid_removed = 0.0
            wet_duration = dt if inventory_start > 0.0 or flux > 0.0 else 0.0
            dry_time_s = None
        else:
            requested_removal = -requested_transfer
            liquid_removed = min(inventory_start, requested_removal)
            admitted_transfer = -liquid_removed
            inventory_end = inventory_start - liquid_removed
            requested_sink_unmet = requested_removal - liquid_removed
            condensation_added = 0.0
            if inventory_start > 0.0:
                raw_dry_time = inventory_start / (-flux)
                wet_duration = min(dt, raw_dry_time)
                dry_time_s = interval.start_time_s + raw_dry_time if raw_dry_time <= dt else None
            else:
                wet_duration = 0.0
                dry_time_s = interval.start_time_s

        if not all(math.isfinite(value) for value in (
            inventory_end, admitted_transfer, requested_sink_unmet,
            condensation_added, liquid_removed, wet_duration,
        )) or inventory_end < 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "inventory_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "film inventory or interval ledger exceeds finite nonnegative support",
            })

        if wet_duration > 0.0:
            total_wet_duration += wet_duration
            if current_wet_start is None:
                current_wet_start = interval.start_time_s
                current_contiguous_wet_duration = 0.0
            current_contiguous_wet_duration += wet_duration
            maximum_contiguous_wet_duration = max(
                maximum_contiguous_wet_duration, current_contiguous_wet_duration
            )
        if inventory_end <= 0.0:
            current_wet_start = None
            current_contiguous_wet_duration = 0.0
        elif current_wet_start is None:
            current_wet_start = interval.end_time_s

        cumulative_condensation_candidate = cumulative_condensation + condensation_added
        cumulative_sink_candidate = cumulative_liquid_sink + liquid_removed
        cumulative_unmet_candidate = cumulative_sink_unmet + requested_sink_unmet
        balance_residual = inventory_end - inventory_start - admitted_transfer
        density = interval.liquid_water_density_kg_m3
        thickness_start = inventory_start / density
        thickness_end = inventory_end / density
        if not all(math.isfinite(value) for value in (
            cumulative_condensation_candidate, cumulative_sink_candidate,
            cumulative_unmet_candidate, balance_residual, total_wet_duration,
            current_contiguous_wet_duration, maximum_contiguous_wet_duration,
            thickness_start, thickness_end,
        )):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "inventory_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "cumulative film ledger exceeds finite support",
            })

        ledger.append({
            "interval_index": index,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": dt,
            "net_retained_water_mass_flux_kg_m2_s": flux,
            "requested_net_transfer_kg_m2": requested_transfer,
            "admitted_net_transfer_kg_m2": admitted_transfer,
            "condensation_added_kg_m2": condensation_added,
            "liquid_sink_removed_kg_m2": liquid_removed,
            "requested_sink_beyond_dryout_kg_m2": requested_sink_unmet,
            "water_areal_inventory_start_kg_m2": inventory_start,
            "water_areal_inventory_end_kg_m2": inventory_end,
            "uniform_equivalent_film_thickness_start_m": thickness_start,
            "uniform_equivalent_film_thickness_end_m": thickness_end,
            "wet_duration_s": wet_duration,
            "dry_time_s": dry_time_s,
            "inventory_balance_residual_kg_m2": balance_residual,
            "flux_provider_id": interval.flux_provider_id,
            "flux_provider_revision": interval.flux_provider_revision,
            "flux_configuration_sha256": interval.flux_configuration_sha256,
            "flux_result_sha256": interval.flux_result_sha256,
            "density_provider_id": interval.density_provider_id,
            "density_provider_revision": interval.density_provider_revision,
            "density_record_sha256": interval.density_record_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
            "evidence": [row.model_dump(mode="json") for row in interval.evidence],
        })
        cumulative_condensation = cumulative_condensation_candidate
        cumulative_liquid_sink = cumulative_sink_candidate
        cumulative_sink_unmet = cumulative_unmet_candidate
        inventory = inventory_end
        history.append({
            "time_s": interval.end_time_s,
            "water_areal_inventory_kg_m2": inventory,
            "uniform_equivalent_film_thickness_m": thickness_end,
            "wet_state": inventory > 0.0,
            "cumulative_condensation_added_kg_m2": cumulative_condensation,
            "cumulative_liquid_sink_removed_kg_m2": cumulative_liquid_sink,
            "cumulative_sink_beyond_dryout_kg_m2": cumulative_sink_unmet,
            "origin": "integrated_caller_net_retained_water_flux",
        })

    final_thickness = inventory / request.intervals[-1].liquid_water_density_kg_m3
    if not math.isfinite(final_thickness):
        return Calculation(status="out_of_scope", values=base | {
            "interval_ledger": ledger,
            "inventory_history": history,
            "failure_reason": "final equivalent film thickness exceeds finite numeric support",
        })
    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(ledger),
        "interval_ledger": ledger,
        "inventory_history": history,
        "final_water_areal_inventory_kg_m2": inventory,
        "final_uniform_equivalent_film_thickness_m": final_thickness,
        "cumulative_condensation_added_kg_m2": cumulative_condensation,
        "cumulative_liquid_sink_removed_kg_m2": cumulative_liquid_sink,
        "cumulative_sink_beyond_dryout_kg_m2": cumulative_sink_unmet,
        "total_wet_duration_s": total_wet_duration,
        "maximum_contiguous_wet_duration_s": maximum_contiguous_wet_duration,
        "film_geometry_interpretation": "uniform equivalent thickness from liquid areal inventory and caller density; not a measured local droplet or film thickness",
        "interpretation_boundary": "One fixed wall patch receiving a caller-supplied net retained-water flux. Negative net flux cannot remove more inventory than is present; unmet sink is ledgered after dryout.",
        "not_inferred": [
            "condensation, evaporation or drainage flux from gas thermodynamics or hydrodynamics",
            "surface coverage, droplet morphology, contact angle, local film shape or lateral redistribution",
            "water chemistry, dissolved CO2, pH, alkalinity, reactions or inhibitor transport",
            "corrosion rate, metal loss, remaining life, acceptance or risk probability",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2CondensateFilmHistoryRequest,
        evaluator=evaluate_wet_co2_condensate_film_history,
        units={
            "initial_water_areal_inventory_kg_m2": "kg/m2",
            "inventory_history[].time_s": "s",
            "inventory_history[].water_areal_inventory_kg_m2": "kg/m2",
            "inventory_history[].uniform_equivalent_film_thickness_m": "m",
            "total_wet_duration_s": "s",
            "maximum_contiguous_wet_duration_s": "s",
        },
        assumptions=(
            "The caller flux is the net retained water source per actual fixed wall-patch area, including condensation, evaporation, drainage and retention effects.",
            "Net flux and liquid density are constant within each exact time interval.",
            "Film areal inventory is nonnegative; a requested negative flux is clipped at dryout and excess sink request is reported separately.",
            "Equivalent thickness assumes spatially uniform full coverage and does not represent resolved droplets or surface morphology.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
