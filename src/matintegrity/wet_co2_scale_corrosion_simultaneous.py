"""Continuously couple scale-controlled film transport, electrochemistry and recession."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec
from .wet_co2_scale_corrosion_coupled_history import (
    WetCo2MetalToScaleYield,
)
from .wet_co2_transport_limited_mixed_potential import (
    WetCo2TransportLimitedMixedPotentialRequest,
    evaluate_wet_co2_transport_limited_mixed_potential,
)

MODEL_ID = "integration.wet_co2_scale_corrosion_simultaneous_history"
SOURCE_ID = "continuous_within_interval_scale_transport_electrochemical_feedback"
SCALE_MOLAR_VOLUME_SOURCE_ID = "caller_wet_co2_simultaneous_scale_molar_volume"
FARADAY_C_MOL = 96485.33212


class WetCo2SimultaneousScaleInterval(Contract):
    """One boundary interval; the nested mixed-potential request supplies its chemistry and kinetics."""

    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    mixed_potential_request: WetCo2TransportLimitedMixedPotentialRequest
    external_net_scale_formation_flux_mol_m2_s: float
    external_flux_provider_id: str = Field(min_length=1)
    external_flux_provider_revision: str = Field(min_length=1)
    external_flux_source_record_id: str = Field(min_length=1)
    external_flux_evidence: Evidence
    external_scale_flux_and_sign_reviewed: bool

    @model_validator(mode="after")
    def validate_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must exceed start")
        if not math.isfinite(self.external_net_scale_formation_flux_mol_m2_s):
            raise ValueError("external scale formation flux must be finite")
        if self.external_flux_evidence.source_id != self.external_flux_provider_id:
            raise ValueError("external flux provider must match Evidence source_id")
        if self.external_flux_evidence.sha256 is None:
            raise ValueError("external scale-flux Evidence must include a SHA-256")
        return self


class WetCo2ScaleCorrosionSimultaneousHistoryRequest(Contract):
    """Finite-interval moving-scale feedback using caller chemistry and calibration records."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    initial_wall_thickness_m: Positive
    initial_scale_thickness_m: Positive
    minimum_supported_scale_thickness_m: Positive
    scale_molar_volume_m3_mol: Positive
    scale_property_provider_id: str = Field(min_length=1)
    scale_property_revision: str = Field(min_length=1)
    scale_property_source_record_id: str = Field(min_length=1)
    scale_property_evidence: Evidence
    metal_to_scale_yields: tuple[WetCo2MetalToScaleYield, ...] = Field(min_length=1, max_length=32)
    intervals: tuple[WetCo2SimultaneousScaleInterval, ...] = Field(min_length=1, max_length=10_000)
    relative_tolerance: float = Field(gt=0, le=1e-2)
    absolute_scale_tolerance_m: Positive
    absolute_wall_tolerance_m: Positive
    absolute_metal_inventory_tolerance_mol_m2: Positive
    absolute_external_scale_tolerance_mol_m2: Positive
    maximum_step_s: Positive
    initial_geometry_reviewed: bool
    mixed_potential_and_film_scope_reviewed: bool
    simultaneous_feedback_and_uniform_patch_reviewed: bool
    scale_stoichiometry_and_volume_additivity_reviewed: bool

    @model_validator(mode="after")
    def validate_history(self):
        if self.minimum_supported_scale_thickness_m >= self.initial_scale_thickness_m:
            raise ValueError("minimum supported scale thickness must be below the initial thickness")
        if self.scale_property_evidence.source_id != self.scale_property_provider_id:
            raise ValueError("scale property provider must match Evidence source_id")
        if self.scale_property_evidence.sha256 is None:
            raise ValueError("scale property Evidence must include a SHA-256")
        if not self.metal_to_scale_yields:
            raise ValueError("at least one metal-to-scale conversion is required")
        reaction_ids = [item.reaction_id for item in self.metal_to_scale_yields]
        if len(set(reaction_ids)) != len(reaction_ids):
            raise ValueError("metal-to-scale reaction IDs must be unique")
        mapping_ids = set(reaction_ids)
        for mapping in self.metal_to_scale_yields:
            if not mapping.alloy_volume_additivity_reviewed or not mapping.metal_to_scale_stoichiometry_reviewed:
                raise ValueError("metal-to-scale mapping requires reviewed stoichiometry and volume additivity")
        for left, right in zip(self.intervals[:-1], self.intervals[1:], strict=True):
            if left.end_time_s != right.start_time_s:
                raise ValueError("intervals must be contiguous exact time knots")
        for interval in self.intervals:
            if not interval.external_scale_flux_and_sign_reviewed:
                raise ValueError("each external scale flux requires explicit sign and scope review")
            reactions = interval.mixed_potential_request.reactions
            if {row.reaction_id for row in reactions} != mapping_ids:
                raise ValueError("every interval reaction must have exactly one metal-to-scale mapping")
            if not interval.mixed_potential_request.planar_steady_film_approximation_reviewed:
                raise ValueError("nested film model applicability must be reviewed")
        return self


def evaluate_wet_co2_scale_corrosion_simultaneous_history(request, scipy) -> Calculation:
    """Integrate scale thickness and wall recession while re-solving potential at every RHS call.

    The current scale thickness replaces the nested caller film thickness at each
    ODE evaluation, then the existing branch-limited zero-current solver supplies
    the instantaneous partial currents. Metal recession and product-scale fluxes
    update the geometry continuously within that interval. External scale flux,
    chemistry, temperature, and reaction calibration remain interval-constant.
    """
    flags = {
        "initial_geometry_reviewed": request.initial_geometry_reviewed,
        "mixed_potential_and_film_scope_reviewed": request.mixed_potential_and_film_scope_reviewed,
        "simultaneous_feedback_and_uniform_patch_reviewed": request.simultaneous_feedback_and_uniform_patch_reviewed,
        "scale_stoichiometry_and_volume_additivity_reviewed": request.scale_stoichiometry_and_volume_additivity_reviewed,
    }
    base = {
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "initial_wall_thickness_m": request.initial_wall_thickness_m,
        "initial_scale_thickness_m": request.initial_scale_thickness_m,
        "scale_molar_volume_m3_mol": request.scale_molar_volume_m3_mol,
        "scale_property_evidence_sha256": request.scale_property_evidence.sha256,
        "simultaneous_within_interval_transport_electrochemical_geometry": True,
        "chemistry_and_external_scale_flux_are_interval_constant": True,
        "interpolation_performed": False,
        "interval_count": len(request.intervals),
    }
    missing = [name for name, value in flags.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    solve_ivp = getattr(getattr(scipy, "integrate", None), "solve_ivp", None)
    if solve_ivp is None:
        return Calculation(status="needs_data", values=base | {"reason": "scipy_integrate_solve_ivp_unavailable"})

    mappings = {row.reaction_id: row for row in request.metal_to_scale_yields}
    reaction_ids = tuple(row.reaction_id for row in request.metal_to_scale_yields)
    count = len(reaction_ids)
    # State: scale thickness, wall thickness, cumulative metal moles per reaction,
    # cumulative external scale moles. All inventories use a unit patch area.
    state = [request.initial_scale_thickness_m, request.initial_wall_thickness_m] + [0.0] * (count + 1)
    history = [{
        "time_s": request.intervals[0].start_time_s,
        "scale_thickness_m": state[0],
        "wall_thickness_m": state[1],
        "cumulative_metal_loss_mol_m2_by_reaction": {key: 0.0 for key in reaction_ids},
        "origin": "caller_initial_state",
    }]
    ledger: list[dict] = []
    for index, interval in enumerate(request.intervals):
        start = list(state)
        nested = interval.mixed_potential_request
        reactions = {row.reaction_id: row for row in nested.reactions}
        last_eval: dict = {}
        failure: list[str] = []

        def rhs(_time, y):
            scale = float(y[0])
            wall = float(y[1])
            if not math.isfinite(scale) or not math.isfinite(wall) or scale <= request.minimum_supported_scale_thickness_m or wall <= 0.0:
                raise ArithmeticError("evolved wall or scale left its reviewed positive geometry support")
            films = tuple(row.model_copy(update={"film_thickness_m": scale}) for row in nested.reactant_films)
            dynamic_request = nested.model_copy(update={"reactant_films": films})
            result = evaluate_wet_co2_transport_limited_mixed_potential(dynamic_request)
            if result.status != "computed":
                failure.append(str(result.values.get("reason", result.status)))
                raise ArithmeticError("transport-limited mixed potential was not computed at the evolving geometry")
            reaction_results = result.values["reaction_results"]
            metal_flux: dict[str, float] = {}
            scale_product_flux = 0.0
            wall_recession_rate = 0.0
            for reaction_id in reaction_ids:
                reaction = reactions[reaction_id]
                mapping = mappings[reaction_id]
                anodic_current = float(reaction_results[reaction_id]["anodic_current_density_A_m2"])
                extent = anodic_current / (reaction.electron_count * FARADAY_C_MOL)
                molar_metal = extent * mapping.metal_atoms_per_reaction_extent
                if not all(math.isfinite(value) and value >= 0.0 for value in (anodic_current, extent, molar_metal)):
                    failure.append("anodic metal flux left finite nonnegative support")
                    raise ArithmeticError(failure[-1])
                metal_flux[reaction_id] = molar_metal
                scale_product_flux += molar_metal * mapping.scale_moles_per_metal_mole
                wall_recession_rate += molar_metal * mapping.metal_molar_mass_kg_mol / mapping.metal_density_kg_m3
            external_flux = interval.external_net_scale_formation_flux_mol_m2_s
            dscale = request.scale_molar_volume_m3_mol * (scale_product_flux + external_flux)
            if not math.isfinite(dscale) or not math.isfinite(wall_recession_rate):
                failure.append("scale growth or wall recession rate exceeded finite support")
                raise ArithmeticError(failure[-1])
            last_eval.clear()
            last_eval.update({
                "mixed_potential_V": result.values["mixed_potential_V"],
                "net_current_residual_A_m2": result.values["net_current_residual_A_m2"],
                "reaction_results": reaction_results,
                "metal_loss_flux_mol_m2_s_by_reaction": metal_flux,
                "scale_product_flux_mol_m2_s": scale_product_flux,
                "external_scale_flux_mol_m2_s": external_flux,
                "wall_recession_rate_m_s": wall_recession_rate,
            })
            return [dscale, -wall_recession_rate, *[metal_flux[key] for key in reaction_ids], external_flux]

        def scale_floor_event(_time, y):
            return y[0] - request.minimum_supported_scale_thickness_m
        scale_floor_event.terminal = True
        scale_floor_event.direction = -1

        def wall_zero_event(_time, y):
            return y[1]
        wall_zero_event.terminal = True
        wall_zero_event.direction = -1

        atol = [
            request.absolute_scale_tolerance_m,
            request.absolute_wall_tolerance_m,
            *[request.absolute_metal_inventory_tolerance_mol_m2] * count,
            request.absolute_external_scale_tolerance_mol_m2,
        ]
        try:
            solved = solve_ivp(
                rhs,
                (interval.start_time_s, interval.end_time_s),
                state,
                method="BDF",
                t_eval=[interval.end_time_s],
                rtol=request.relative_tolerance,
                atol=atol,
                max_step=min(request.maximum_step_s, interval.end_time_s - interval.start_time_s),
                events=(scale_floor_event, wall_zero_event),
            )
        except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "failure_reason": failure[-1] if failure else str(exc),
            })
        if not solved.success or solved.y.shape[1] != 1 or solved.t[-1] != interval.end_time_s:
            event_reason = (
                "scale_thickness_reached_minimum_supported_geometry"
                if solved.t_events[0].size else
                "wall_thickness_depleted" if solved.t_events[1].size else solved.message
            )
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "failure_reason": event_reason,
            })
        state = [float(value) for value in solved.y[:, -1]]
        if not all(math.isfinite(value) for value in state) or state[0] <= request.minimum_supported_scale_thickness_m or state[1] <= 0.0:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "failure_reason": "integrated_geometry_or_inventory_left_finite_support",
            })
        metal_delta = {key: state[2 + position] - start[2 + position] for position, key in enumerate(reaction_ids)}
        external_delta = state[-1] - start[-1]
        expected_product_delta = math.fsum(metal_delta[key] * mappings[key].scale_moles_per_metal_mole for key in reaction_ids)
        scale_delta_mol = (state[0] - start[0]) / request.scale_molar_volume_m3_mol
        scale_balance_residual = scale_delta_mol - expected_product_delta - external_delta
        expected_recession = math.fsum(
            metal_delta[key] * mappings[key].metal_molar_mass_kg_mol / mappings[key].metal_density_kg_m3
            for key in reaction_ids
        )
        wall_balance_residual = (start[1] - state[1]) - expected_recession
        try:
            rhs(interval.end_time_s, state)
        except (ArithmeticError, OverflowError, ValueError, ZeroDivisionError) as exc:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": index,
                "failed_interval_index": index,
                "history_prefix": history,
                "interval_ledger": ledger,
                "failure_reason": failure[-1] if failure else str(exc),
            })
        ledger.append({
            "interval_id": interval.interval_id,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "scale_thickness_start_m": start[0],
            "scale_thickness_end_m": state[0],
            "wall_thickness_start_m": start[1],
            "wall_thickness_end_m": state[1],
            "integrated_metal_loss_mol_m2_by_reaction": metal_delta,
            "integrated_external_scale_flux_mol_m2": external_delta,
            "integrated_scale_product_mol_m2": expected_product_delta,
            "scale_inventory_balance_residual_mol_m2": scale_balance_residual,
            "wall_recession_balance_residual_m": wall_balance_residual,
            "endpoint_mixed_potential_V": last_eval.get("mixed_potential_V"),
            "endpoint_net_current_residual_A_m2": last_eval.get("net_current_residual_A_m2"),
            "endpoint_reaction_results": last_eval.get("reaction_results"),
            "solver_method": "BDF",
            "nested_request_sha256": canonical_digest(nested.model_dump(mode="json")),
            "external_flux_evidence_sha256": interval.external_flux_evidence.sha256,
        })
        history.append({
            "time_s": interval.end_time_s,
            "scale_thickness_m": state[0],
            "scale_inventory_mol_m2": state[0] / request.scale_molar_volume_m3_mol,
            "wall_thickness_m": state[1],
            "cumulative_metal_loss_mol_m2_by_reaction": {key: state[2 + position] for position, key in enumerate(reaction_ids)},
            "cumulative_external_scale_flux_mol_m2": state[-1],
            "origin": "simultaneously_integrated_scale_film_and_electrode_feedback",
        })
    return Calculation(values=base | {
        "status": "computed",
        "final_scale_thickness_m": state[0],
        "final_scale_inventory_mol_m2": state[0] / request.scale_molar_volume_m3_mol,
        "final_wall_thickness_m": state[1],
        "cumulative_metal_loss_mol_m2_by_reaction": {key: state[2 + position] for position, key in enumerate(reaction_ids)},
        "cumulative_external_scale_flux_mol_m2": state[-1],
        "history": history,
        "interval_ledger": ledger,
        "limitations": [
            "At every BDF evaluation the current scale thickness is substituted into the caller steady planar-film record and the bounded mixed potential is re-solved.",
            "The nested film-cap and Butler-Volmer closure is still a reduced branch-limited model, not a spatial diffusion-reaction-electrode PDE.",
            "Each interval holds boundary chemistry, temperature, external scale flux and kinetic parameters constant.",
            "A uniform attached scale and uniform wall recession are assumed; scale detachment, cracking, morphology and lateral transport are not represented.",
            "Results are conditional calculations, not experimentally validated corrosion rates, material acceptance, life or probability.",
        ],
    }, notes=(
        "Unlike the sequential history adapter, the evolving scale thickness feeds the film-limited potential solve at each ODE evaluation within every interval.",
        "Mass and recession residuals are numerical balance diagnostics and do not establish physical qualification.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        WetCo2ScaleCorrosionSimultaneousHistoryRequest,
        evaluate_wet_co2_scale_corrosion_simultaneous_history,
        {
            "final_scale_thickness_m": "m",
            "final_scale_inventory_mol_m2": "mol/m^2",
            "final_wall_thickness_m": "m",
            "cumulative_metal_loss_mol_m2_by_reaction.*": "mol/m^2",
            "cumulative_external_scale_flux_mol_m2": "mol/m^2",
            "history[].time_s": "s",
            "history[].scale_thickness_m": "m",
            "history[].wall_thickness_m": "m",
            "interval_ledger[].scale_inventory_balance_residual_mol_m2": "mol/m^2",
            "interval_ledger[].wall_recession_balance_residual_m": "m",
        },
        (
            "Scale thickness is a continuous ODE state and updates the nested film-transport cap at each electrochemical solver call.",
            "Caller-provided metal stoichiometry, molar mass, density, scale yield and molar volume govern recession and product growth.",
            "The mixed-potential solve remains bounded by caller calibration support and caller-selected branch scaling.",
            "No spatially resolved scale PDE, independent corrosion validation, acceptance, probability or qualified life is provided.",
        ),
        (
            "caller_wet_co2_species_film_transport_parameters",
            "caller_calibrated_butler_volmer_reaction_set",
            "caller_wet_co2_scale_growth_per_metal_dissolution_mapping",
            "caller_wet_co2_scale_phase_molar_volume_and_external_flux",
            SCALE_MOLAR_VOLUME_SOURCE_ID,
            SOURCE_ID,
        ),
        qualification="user_model",
        runtime_dependency_names=("scipy",),
    )]
