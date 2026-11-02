"""Couple finite CO2 gas/liquid inventory to a caller-pinned electrochemical wall sink."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from .registry import ModelSpec
from .wet_co2_finite_gas_variable_liquid_history import (
    WetCo2FiniteGasVariableLiquidInterval,
    _overall_liquid_velocity,
)

MODEL_ID = "integration.wet_co2_finite_gas_wall_reaction_inventory_history"
SOURCE_ID = "caller_wet_co2_electrochemical_co2star_sink_mapping"
METAL_LOSS_MODEL_ID = "integration.electrochemical_partial_current_metal_loss"


class Co2starWallConsumptionMapping(Contract):
    """Caller-owned uptake stoichiometry from one removed-metal basis to neutral CO2*."""

    reaction_id: str = Field(min_length=1)
    co2star_consumed_mol_per_metal_mol: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reaction_and_carbon_balance_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def evidence_matches_mapping(self):
        if not any(
            item.source_id == self.provider_id and item.sha256 == self.record_sha256
            for item in self.evidence
        ):
            raise ValueError("caller wall-reaction stoichiometry must match provider-linked Evidence digest")
        if not math.isfinite(self.co2star_consumed_mol_per_metal_mol):
            raise ValueError("CO2-star consumption ratio must be finite")
        return self


class WetCo2WallReactionCoupledHistoryRequest(Contract):
    schema_version: Literal["matintegrity.wet_co2_wall_reaction_coupled_history.v1"] = (
        "matintegrity.wet_co2_wall_reaction_coupled_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    wall_patch_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    wall_patch_area_m2: Positive
    initial_liquid_volume_per_area_m: Positive
    initial_liquid_co2star_mol_m3: Nonnegative
    initial_gas_co2_fugacity_Pa: Nonnegative
    finite_gas_inventory_capacity_mol_m2_Pa: Positive
    initial_state_provider_id: str = Field(min_length=1)
    initial_state_provider_revision: str = Field(min_length=1)
    initial_state_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_state_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_state_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    intervals: tuple[WetCo2FiniteGasVariableLiquidInterval, ...] = Field(min_length=1, max_length=2000)
    electrochemical_metal_loss_result: AssessmentResult
    electrochemical_metal_loss_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    co2star_wall_consumption_mappings: tuple[Co2starWallConsumptionMapping, ...] = Field(min_length=1, max_length=32)
    relative_tolerance: float = Field(default=1e-9, ge=1e-12, le=1e-3)
    liquid_concentration_absolute_tolerance_mol_m3: Positive = 1e-10
    gas_fugacity_absolute_tolerance_Pa: Positive = 1e-3
    areal_mole_absolute_tolerance_mol_m2: Positive = 1e-12
    maximum_step_s: Positive | None = None
    fixed_area_and_gas_capacity_reviewed: bool
    positive_volume_flux_is_condensate_inflow_reviewed: bool
    negative_volume_flux_is_well_mixed_liquid_outflow_reviewed: bool
    no_dryout_within_simulated_history_reviewed: bool
    incoming_co2star_convention_reviewed: bool
    electrochemical_source_applicability_for_patch_reviewed: bool
    metal_loss_and_transfer_clock_alignment_reviewed: bool
    co2star_consumption_stoichiometry_reviewed: bool
    area_and_volume_loss_additivity_reviewed: bool
    solver_tolerances_and_use_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def consistent_sources_and_exact_intervals(self):
        finite = (
            self.wall_patch_area_m2,
            self.initial_liquid_volume_per_area_m,
            self.initial_liquid_co2star_mol_m3,
            self.initial_gas_co2_fugacity_Pa,
            self.finite_gas_inventory_capacity_mol_m2_Pa,
            self.relative_tolerance,
            self.liquid_concentration_absolute_tolerance_mol_m3,
            self.gas_fugacity_absolute_tolerance_Pa,
            self.areal_mole_absolute_tolerance_mol_m2,
        )
        if not all(math.isfinite(value) for value in finite):
            raise ValueError("initial states, patch area and solver tolerances must be finite")
        if self.maximum_step_s is not None and not math.isfinite(self.maximum_step_s):
            raise ValueError("maximum solver step must be finite")
        if self.initial_state_provider_id not in {row.source_id for row in self.initial_state_evidence}:
            raise ValueError("initial-state Evidence must identify its provider")
        if not self.intervals or self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at exact time zero")
        if any(left.end_time_s != right.start_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("gas/liquid intervals must be exactly contiguous")
        volume = self.initial_liquid_volume_per_area_m
        for interval in self.intervals:
            volume_end = volume + interval.liquid_volume_flux_m_s * (interval.end_time_s - interval.start_time_s)
            if not math.isfinite(volume_end) or volume_end <= 0.0:
                raise ValueError("caller liquid-volume path reaches dryout or invalid volume")
            volume = volume_end

        source = self.electrochemical_metal_loss_result
        if source.model_id != METAL_LOSS_MODEL_ID or source.status != "computed":
            raise ValueError("a computed electrochemical partial-current metal-loss AssessmentResult is required")
        if canonical_digest(source.model_dump(mode="json")) != self.electrochemical_metal_loss_result_sha256:
            raise ValueError("electrochemical metal-loss result digest mismatch")
        expected_input_digest = canonical_digest({
            "model_id": source.model_id,
            "model_version": source.model_version,
            "inputs": source.inputs,
            "context": source.context.model_dump(mode="json"),
        })
        if source.input_digest != expected_input_digest:
            raise ValueError("electrochemical metal-loss input digest does not match its request/context")
        source_values = source.values
        if (
            source_values.get("asset_id") != self.asset_id
            or source_values.get("location_id") != self.location_id
            or source_values.get("physical_scope_id") != self.physical_scope_id
            or (source.context.asset_id, source.context.location_id, source.context.time_basis)
            != (self.asset_id, self.location_id, self.time_basis)
        ):
            raise ValueError("electrochemical metal-loss result must match asset, location, scope and clock basis")
        source_rows = source_values.get("interval_metal_loss")
        reaction_mappings = source_values.get("reaction_to_metal_mapping")
        if not isinstance(source_rows, list) or len(source_rows) != len(self.intervals):
            raise ValueError("electrochemical loss intervals must match every caller gas/liquid interval")
        if not isinstance(reaction_mappings, list) or not reaction_mappings:
            raise ValueError("electrochemical result is missing its reaction-to-metal mappings")
        reaction_ids = tuple(row.get("reaction_id") for row in reaction_mappings)
        if any(not isinstance(key, str) for key in reaction_ids) or len(set(reaction_ids)) != len(reaction_ids):
            raise ValueError("electrochemical reaction IDs must be unique and ordered")
        if tuple(row.reaction_id for row in self.co2star_wall_consumption_mappings) != reaction_ids:
            raise ValueError("CO2-star sink mapping IDs and order must exactly match the electrochemical metal mapping")
        area = source_values.get("reference_area_m2")
        if isinstance(area, bool) or not isinstance(area, (int, float)) or not math.isclose(
            float(area), self.wall_patch_area_m2, rel_tol=1e-10, abs_tol=0.0
        ):
            raise ValueError("electrochemical reference area must equal the finite gas/liquid wall-patch area")
        source_origin = None
        for index, (interval, source_interval) in enumerate(zip(self.intervals, source_rows, strict=True)):
            if not isinstance(source_interval, dict):
                raise ValueError("electrochemical interval records must be objects")
            start, end = source_interval.get("start_time_s"), source_interval.get("end_time_s")
            if (start, end) != (interval.start_time_s, interval.end_time_s):
                raise ValueError("metal-loss and gas/liquid intervals must have exact shared endpoints")
            rows = source_interval.get("reaction_metal_loss")
            if not isinstance(rows, list) or tuple(row.get("reaction_id") for row in rows) != reaction_ids:
                raise ValueError("each source interval must retain the reaction mapping order")
            if index == 0:
                source_origin = start
            for metal_map, metal_row in zip(reaction_mappings, rows, strict=True):
                exposed_area = metal_row.get("exposed_area_m2")
                if isinstance(exposed_area, bool) or not isinstance(exposed_area, (int, float)) or not math.isclose(
                    float(exposed_area), self.wall_patch_area_m2, rel_tol=1e-10, abs_tol=0.0
                ):
                    raise ValueError("each electrochemical branch must use the same reviewed wall-patch area")
                amount = metal_row.get("anodic_metal_removal_mol")
                mass = metal_row.get("anodic_mass_loss_kg")
                molar_mass = metal_map.get("molar_mass_kg_mol")
                density = metal_map.get("density_kg_m3")
                if any(
                    isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                    for value in (amount, mass, molar_mass, density)
                ) or min(amount, mass) < 0.0 or min(molar_mass, density) <= 0.0:
                    raise ValueError("metal-loss interval and property data must be finite and nonnegative/positive")
                expected_mass = amount * molar_mass
                if not math.isclose(mass, expected_mass, rel_tol=1e-9, abs_tol=1e-15):
                    raise ValueError("electrochemical anodic mass and molar-loss ledger are inconsistent")
        if source_origin not in (0, 0.0):
            raise ValueError("electrochemical loss history must use the same time-zero origin")
        return self


def _required_reviews(request: WetCo2WallReactionCoupledHistoryRequest) -> list[str]:
    rows = {
        "fixed_area_and_gas_capacity_reviewed": request.fixed_area_and_gas_capacity_reviewed,
        "positive_volume_flux_is_condensate_inflow_reviewed": request.positive_volume_flux_is_condensate_inflow_reviewed,
        "negative_volume_flux_is_well_mixed_liquid_outflow_reviewed": request.negative_volume_flux_is_well_mixed_liquid_outflow_reviewed,
        "no_dryout_within_simulated_history_reviewed": request.no_dryout_within_simulated_history_reviewed,
        "incoming_co2star_convention_reviewed": request.incoming_co2star_convention_reviewed,
        "electrochemical_source_applicability_for_patch_reviewed": request.electrochemical_source_applicability_for_patch_reviewed,
        "metal_loss_and_transfer_clock_alignment_reviewed": request.metal_loss_and_transfer_clock_alignment_reviewed,
        "co2star_consumption_stoichiometry_reviewed": request.co2star_consumption_stoichiometry_reviewed,
        "area_and_volume_loss_additivity_reviewed": request.area_and_volume_loss_additivity_reviewed,
        "solver_tolerances_and_use_reviewed": request.solver_tolerances_and_use_reviewed,
        "calculation_use_authorized": request.calculation_use_authorized,
    }
    missing = [name for name, reviewed in rows.items() if not reviewed]
    missing.extend(
        f"interval[{index}].interval_state_and_units_reviewed"
        for index, interval in enumerate(request.intervals)
        if not interval.interval_state_and_units_reviewed
    )
    missing.extend(
        f"reaction[{row.reaction_id}].reaction_and_carbon_balance_reviewed"
        for row in request.co2star_wall_consumption_mappings
        if not row.reaction_and_carbon_balance_reviewed
    )
    return missing


def wet_co2_wall_reaction_coupled_history(
    request: WetCo2WallReactionCoupledHistoryRequest,
) -> Calculation:
    """Integrate finite gas/liquid CO2* exchange with a pinned, piecewise-constant wall sink."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "wall_patch_id": request.wall_patch_id,
        "condition_id": request.condition_id,
        "time_basis": request.time_basis,
        "wall_patch_area_m2": request.wall_patch_area_m2,
        "input_sha256": input_digest,
        "electrochemical_metal_loss_result_sha256": request.electrochemical_metal_loss_result_sha256,
        "initial_state_result_sha256": request.initial_state_result_sha256,
        "reaction_metal_loss_mapping": request.electrochemical_metal_loss_result.values["reaction_to_metal_mapping"],
        "co2star_wall_consumption_mappings": [row.model_dump(mode="json") for row in request.co2star_wall_consumption_mappings],
    }
    missing = _required_reviews(request)
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    try:
        import scipy
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values=base | {"missing_dependency": "scipy"})

    metal_result = request.electrochemical_metal_loss_result
    source_intervals = metal_result.values["interval_metal_loss"]
    metal_mappings = {row["reaction_id"]: row for row in metal_result.values["reaction_to_metal_mapping"]}
    sink_mappings = {row.reaction_id: row for row in request.co2star_wall_consumption_mappings}
    beta = request.finite_gas_inventory_capacity_mol_m2_Pa
    y = [
        request.initial_liquid_co2star_mol_m3,
        request.initial_gas_co2_fugacity_Pa,
        0.0,  # cumulative signed gas-to-liquid transfer, mol/m2
        0.0,  # cumulative signed waterborne CO2* transfer, mol/m2
        0.0,  # cumulative caller-declared wall-reaction CO2* consumption, mol/m2
    ]
    volume = request.initial_liquid_volume_per_area_m
    total0 = volume * y[0] + beta * y[1]
    if not math.isfinite(total0):
        return Calculation(status="out_of_scope", values=base | {"reason": "initial_inventory_not_finite"})
    history = [{
        "time_s": 0.0,
        "liquid_volume_per_area_m": volume,
        "liquid_co2star_mol_m3": y[0],
        "gas_co2_fugacity_Pa": y[1],
        "liquid_co2star_areal_inventory_mol_m2": volume * y[0],
        "gas_co2_areal_inventory_mol_m2": beta * y[1],
        "cumulative_wall_reaction_co2star_consumed_mol_m2": 0.0,
        "cumulative_anodic_wall_metal_loss_kg": 0.0,
        "cumulative_area_average_anodic_recession_m": 0.0,
    }]
    ledger = []
    cumulative_mass = 0.0
    cumulative_recession = 0.0
    cumulative_metal_mol = 0.0
    atol = (
        request.liquid_concentration_absolute_tolerance_mol_m3,
        request.gas_fugacity_absolute_tolerance_Pa,
        request.areal_mole_absolute_tolerance_mol_m2,
        request.areal_mole_absolute_tolerance_mol_m2,
        request.areal_mole_absolute_tolerance_mol_m2,
    )
    solver = {
        "provider_id": "scipy.integrate.solve_ivp:DOP853",
        "solver_method": "DOP853",
        "scipy_version": scipy.__version__,
        "relative_tolerance": request.relative_tolerance,
        "absolute_tolerances": list(atol),
        "maximum_step_s": request.maximum_step_s,
    }
    for index, (interval, metal_interval) in enumerate(zip(request.intervals, source_intervals, strict=True)):
        start, end = interval.start_time_s, interval.end_time_s
        dt = end - start
        liquid_flux = interval.liquid_volume_flux_m_s
        overall_k = _overall_liquid_velocity(
            interval.gas_film_coefficient_mol_m2_s_Pa,
            interval.henry_concentration_over_fugacity_mol_m3_Pa,
            interval.liquid_film_coefficient_m_s,
        )
        if overall_k is None:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "reason": "overall_two_film_velocity_not_finite",
            })
        metal_rows = metal_interval["reaction_metal_loss"]
        try:
            sink_mol_m2 = math.fsum(
                float(row["anodic_metal_removal_mol"])
                / request.wall_patch_area_m2
                * sink_mappings[row["reaction_id"]].co2star_consumed_mol_per_metal_mol
                for row in metal_rows
            )
            sink_rate = sink_mol_m2 / dt
            interval_metal_mol = math.fsum(float(row["anodic_metal_removal_mol"]) for row in metal_rows)
            interval_mass = math.fsum(float(row["anodic_mass_loss_kg"]) for row in metal_rows)
            interval_volume_loss = math.fsum(
                float(row["anodic_mass_loss_kg"])
                / float(metal_mappings[row["reaction_id"]]["density_kg_m3"])
                for row in metal_rows
            )
        except (OverflowError, ValueError, ZeroDivisionError):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "reason": "wall_sink_or_metal_loss_exceeds_finite_numeric_support",
            })
        interval_recession = interval_volume_loss / request.wall_patch_area_m2
        if not all(math.isfinite(value) and value >= 0.0 for value in (
            sink_mol_m2, sink_rate, interval_metal_mol, interval_mass, interval_recession,
        )):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "reason": "wall_sink_or_metal_loss_not_finite_nonnegative",
            })

        def rhs(time_s, state):
            c_liquid, fugacity, _, waterborne, _ = state
            liquid_volume = volume + liquid_flux * (time_s - start)
            if liquid_volume <= 0.0:
                raise ValueError("liquid inventory reached dryout inside the interval")
            transfer_flux = overall_k * (
                interval.henry_concentration_over_fugacity_mol_m3_Pa * fugacity - c_liquid
            )
            if liquid_flux > 0.0:
                dc_dt = (
                    transfer_flux
                    + liquid_flux * interval.incoming_co2star_mol_m3
                    - liquid_flux * c_liquid
                    - sink_rate
                ) / liquid_volume
                waterborne_rate = liquid_flux * interval.incoming_co2star_mol_m3
            elif liquid_flux < 0.0:
                dc_dt = (transfer_flux - sink_rate) / liquid_volume
                waterborne_rate = liquid_flux * c_liquid
            else:
                dc_dt = (transfer_flux - sink_rate) / liquid_volume
                waterborne_rate = 0.0
            return (
                dc_dt,
                -transfer_flux / beta,
                transfer_flux,
                waterborne_rate,
                sink_rate,
            )

        def liquid_depletion(time_s, state):
            return state[0]

        liquid_depletion.terminal = True
        liquid_depletion.direction = -1
        try:
            solution = solve_ivp(
                rhs,
                (start, end),
                y,
                method="DOP853",
                rtol=request.relative_tolerance,
                atol=atol,
                max_step=request.maximum_step_s if request.maximum_step_s is not None else math.inf,
                events=liquid_depletion,
            )
        except Exception as exc:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "reason": f"coupled gas-liquid-wall ODE failed: {type(exc).__name__}",
            })
        if solution.t[-1] != end:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failed_time_s": float(solution.t[-1]),
                "reason": "wall_reaction_consumed_liquid_CO2star_before_interval_end",
            })
        if not solution.success or solution.y.shape != (5, len(solution.t)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "reason": "DOP853_did_not_complete_exact_interval",
            })
        y_end = [float(row[-1]) for row in solution.y]
        volume_end = volume + liquid_flux * dt
        liquid_start = volume * y[0]
        gas_start = beta * y[1]
        liquid_end = volume_end * y_end[0]
        gas_end = beta * y_end[1]
        waterborne_delta = y_end[3] - y[3]
        consumed_delta = y_end[4] - y[4]
        total_start = liquid_start + gas_start
        total_end = liquid_end + gas_end
        balance_residual = total_end - total_start - waterborne_delta + consumed_delta
        balance_tolerance = request.areal_mole_absolute_tolerance_mol_m2 + request.relative_tolerance * max(
            abs(total_start), abs(total_end), abs(waterborne_delta), abs(consumed_delta)
        )
        if (
            not all(math.isfinite(value) for value in (*y_end, volume_end, balance_residual, interval_recession))
            or any(value < 0.0 for value in y_end[:2])
            or volume_end <= 0.0
            or abs(balance_residual) > balance_tolerance
        ):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "combined_co2star_inventory_balance_residual_mol_m2": balance_residual,
                "balance_tolerance_mol_m2": balance_tolerance,
                "reason": "nonnegative_state_or_combined_inventory_closure_not_met",
            })

        cumulative_mass += interval_mass
        cumulative_recession += interval_recession
        cumulative_metal_mol += interval_metal_mol
        ledger.append({
            "interval_index": index,
            "start_time_s": start,
            "end_time_s": end,
            "duration_s": dt,
            "temperature_K": interval.temperature_K,
            "liquid_volume_per_area_start_m": volume,
            "liquid_volume_per_area_end_m": volume_end,
            "initial_liquid_co2star_mol_m3": y[0],
            "final_liquid_co2star_mol_m3": y_end[0],
            "initial_gas_co2_fugacity_Pa": y[1],
            "final_gas_co2_fugacity_Pa": y_end[1],
            "overall_liquid_basis_transfer_velocity_m_s": overall_k,
            "signed_gas_to_liquid_transfer_mol_m2": y_end[2] - y[2],
            "signed_waterborne_co2star_transfer_mol_m2": waterborne_delta,
            "wall_reaction_co2star_consumed_mol_m2": consumed_delta,
            "anodic_metal_removal_mol": interval_metal_mol,
            "anodic_mass_loss_kg": interval_mass,
            "area_average_anodic_recession_m": interval_recession,
            "electrochemical_interval_digest": canonical_digest(metal_interval),
            "combined_inventory_start_mol_m2": total_start,
            "combined_inventory_end_mol_m2": total_end,
            "combined_inventory_balance_residual_mol_m2": balance_residual,
            "combined_inventory_balance_tolerance_mol_m2": balance_tolerance,
            "solver_method": "DOP853",
            "solver_evaluations": int(solution.nfev),
        })
        y = y_end
        volume = volume_end
        history.append({
            "time_s": end,
            "liquid_volume_per_area_m": volume,
            "liquid_co2star_mol_m3": y[0],
            "gas_co2_fugacity_Pa": y[1],
            "liquid_co2star_areal_inventory_mol_m2": volume * y[0],
            "gas_co2_areal_inventory_mol_m2": beta * y[1],
            "cumulative_signed_gas_to_liquid_transfer_mol_m2": y[2],
            "cumulative_signed_waterborne_co2star_transfer_mol_m2": y[3],
            "cumulative_wall_reaction_co2star_consumed_mol_m2": y[4],
            "cumulative_anodic_wall_metal_loss_kg": cumulative_mass,
            "cumulative_anodic_metal_removal_mol": cumulative_metal_mol,
            "cumulative_area_average_anodic_recession_m": cumulative_recession,
        })

    return Calculation(values=base | {
        "status": "computed",
        "solver": solver,
        "interval_count": len(ledger),
        "state_history": history,
        "interval_ledger": ledger,
        "final_liquid_volume_per_area_m": volume,
        "final_liquid_co2star_mol_m3": y[0],
        "final_gas_co2_fugacity_Pa": y[1],
        "cumulative_signed_gas_to_liquid_transfer_mol_m2": y[2],
        "cumulative_signed_waterborne_co2star_transfer_mol_m2": y[3],
        "cumulative_wall_reaction_co2star_consumed_mol_m2": y[4],
        "cumulative_anodic_metal_removal_mol": cumulative_metal_mol,
        "cumulative_anodic_mass_loss_kg": cumulative_mass,
        "cumulative_area_average_anodic_recession_m": cumulative_recession,
        "combined_co2star_inventory_balance_residual_mol_m2": ledger[-1]["combined_inventory_end_mol_m2"]
        - total0
        - y[3]
        + y[4],
        "temperature_interpolation_performed": False,
        "kinetics_inferred": False,
        "electrochemical_feedback_solved": False,
        "interpretation_boundary": (
            "Finite gas and well-mixed variable-volume liquid CO2* balance with an exact-interval, "
            "caller-pinned anodic metal-loss forcing and caller stoichiometric CO2* sink."
        ),
    })


def _validate_context(request: WetCo2WallReactionCoupledHistoryRequest, context: RunContext) -> None:
    if (context.asset_id, context.location_id, context.time_basis) != (
        request.asset_id,
        request.location_id,
        request.time_basis,
    ):
        raise ValueError("RunContext must match the gas/liquid/wall history asset, location and time basis")


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            WetCo2WallReactionCoupledHistoryRequest,
            wet_co2_wall_reaction_coupled_history,
            {
                "state_history[].time_s": "s",
                "state_history[].liquid_co2star_mol_m3": "mol/m3",
                "state_history[].gas_co2_fugacity_Pa": "Pa",
                "state_history[].liquid_co2star_areal_inventory_mol_m2": "mol/m2",
                "state_history[].gas_co2_areal_inventory_mol_m2": "mol/m2",
                "state_history[].cumulative_wall_reaction_co2star_consumed_mol_m2": "mol/m2",
                "state_history[].cumulative_anodic_wall_metal_loss_kg": "kg",
                "state_history[].cumulative_area_average_anodic_recession_m": "m",
                "interval_ledger[].combined_inventory_balance_residual_mol_m2": "mol/m2",
            },
            (
                "Finite gas inventory, Henry coefficient, film coefficients, volume flux, incoming dissolved CO2*, initial state and solver tolerances are caller-owned and Evidence-linked.",
                "A separately computed, digest-pinned anodic metal-loss history supplies piecewise-constant wall-source demand over exactly aligned intervals and the same physical wall area.",
                "CO2* consumption per removed-metal mole is an independent caller stoichiometric mapping with source Evidence and atom/carbon-balance review; it is never inferred from the metal-loss result.",
                "The coupled balance solves CO2* transfer and depletion with externally forced wall loss; it does not feed changing CO2 state back into electrochemical kinetics and does not solve full aqueous speciation, scale growth or corrosion qualification.",
                "Anodic area-average recession uses caller-mapped alloy molar masses, densities and uniform/additive-volume review; it is not a localized corrosion depth or remaining-wall assessment.",
            ),
            (
                "caller_wet_co2_electrochemical_co2star_sink_mapping",
                "caller_finite_gas_variable_liquid_two_film_balance",
                "electrochemical_partial_current_to_metal_loss",
                "scipy_integrate_solve_ivp",
                "scipy_integrate_dop853",
            ),
            qualification="user_model",
            context_validator=_validate_context,
            runtime_dependency_names=("scipy",),
        )
    ]
