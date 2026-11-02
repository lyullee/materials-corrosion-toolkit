"""Closed finite-gas water vapor exchange with a wall liquid inventory."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_finite_gas_water_condensation_history"
TRANSFER_SOURCE_ID = "caller_finite_gas_water_fugacity_transfer_parameters"
WALL_STATE_SOURCE_ID = "caller_wall_water_saturation_fugacity_history"
ALGORITHM_SOURCE_ID = "finite_well_mixed_gas_water_wall_film_exchange"
R_GAS_J_MOL_K = 8.31446261815324
WATER_MOLAR_MASS_KG_MOL = 0.01801528
MAX_INTERVALS = 100_000


class FiniteGasWaterExchangeInterval(Contract):
    """Constant transfer/thermodynamic inputs over a contiguous interval."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    gas_temperature_K: float = Field(gt=0)
    gas_volume_m3: float = Field(gt=0)
    water_vapor_fugacity_coefficient: float = Field(gt=0)
    wall_water_saturation_fugacity_Pa: float = Field(gt=0)
    gas_film_molar_transfer_coefficient_mol_m2_s_Pa: float = Field(ge=0)
    transfer_area_m2: float = Field(gt=0)
    liquid_water_density_kg_m3: float = Field(gt=0)
    transfer_provider_id: str = Field(min_length=1)
    transfer_provider_revision: str = Field(min_length=1)
    transfer_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transfer_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_state_provider_id: str = Field(min_length=1)
    wall_state_provider_revision: str = Field(min_length=1)
    wall_state_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_state_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    density_record_id: str = Field(min_length=1)
    density_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    interval_model_assumptions_reviewed: bool

    @model_validator(mode="after")
    def validate_interval(self):
        values = (
            self.start_time_s, self.end_time_s, self.gas_temperature_K, self.gas_volume_m3,
            self.water_vapor_fugacity_coefficient, self.wall_water_saturation_fugacity_Pa,
            self.gas_film_molar_transfer_coefficient_mol_m2_s_Pa, self.transfer_area_m2,
            self.liquid_water_density_kg_m3,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("finite-gas interval inputs must all be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must be later than start")
        ids = {item.source_id for item in self.evidence}
        if not {self.transfer_provider_id, self.wall_state_provider_id, self.density_record_id}.issubset(ids):
            raise ValueError("Evidence must identify transfer, wall saturation, and liquid density inputs")
        digest_pairs = {(item.source_id, item.sha256) for item in self.evidence}
        if (self.density_record_id, self.density_record_sha256) not in digest_pairs:
            raise ValueError("density record digest must match its Evidence")
        return self


class FiniteGasWaterCondensationHistoryRequest(Contract):
    """Finite ideal-gas water vapor inventory exchanging with one wall patch."""

    schema_version: Literal["matintegrity.wet_co2_finite_gas_water_condensation_history.v1"] = (
        "matintegrity.wet_co2_finite_gas_water_condensation_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    wall_patch_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    initial_gas_water_vapor_moles: float = Field(ge=0)
    initial_wall_water_areal_inventory_kg_m2: float = Field(ge=0)
    intervals: tuple[FiniteGasWaterExchangeInterval, ...] = Field(min_length=1, max_length=MAX_INTERVALS)
    closed_gas_inventory_and_ideal_partial_pressure_reviewed: bool
    fugacity_coefficient_and_transfer_basis_reviewed: bool
    fixed_patch_no_lateral_transport_reviewed: bool
    wall_saturation_and_liquid_density_applicability_reviewed: bool
    piecewise_constant_interval_state_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def validate_history(self):
        values = (self.initial_gas_water_vapor_moles, self.initial_wall_water_areal_inventory_kg_m2)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("initial gas and liquid inventories must be finite")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at elapsed time zero")
        if any(left.end_time_s != right.start_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("history intervals must be contiguous at exact knots")
        return self


def _finite_gas_interval_end(
    *, n0_mol: float, liquid0_kg_m2: float, interval: FiniteGasWaterExchangeInterval
) -> tuple[float, float, float, float, float, float]:
    """Exact constant-state solution; returns n1, liquid1, requested transfer, dry time, p0, p1."""
    dt = interval.end_time_s - interval.start_time_s
    p0 = n0_mol * R_GAS_J_MOL_K * interval.gas_temperature_K / interval.gas_volume_m3
    f0 = interval.water_vapor_fugacity_coefficient * p0
    fugacity_equilibrium_pressure = (
        interval.wall_water_saturation_fugacity_Pa / interval.water_vapor_fugacity_coefficient
    )
    n_equilibrium = (
        fugacity_equilibrium_pressure * interval.gas_volume_m3
        / (R_GAS_J_MOL_K * interval.gas_temperature_K)
    )
    rate = (
        interval.transfer_area_m2
        * interval.gas_film_molar_transfer_coefficient_mol_m2_s_Pa
        * interval.water_vapor_fugacity_coefficient
        * R_GAS_J_MOL_K
        * interval.gas_temperature_K
        / interval.gas_volume_m3
    )
    exposure = rate * dt
    if not all(math.isfinite(value) for value in (p0, f0, n_equilibrium, rate, exposure)):
        raise ArithmeticError("finite-gas transfer intermediate exceeds finite support")
    factor = math.exp(-exposure)
    n_requested = n_equilibrium + (n0_mol - n_equilibrium) * factor
    requested_transfer_mol = n0_mol - n_requested  # positive means gas -> liquid
    available_liquid_mol = liquid0_kg_m2 * interval.transfer_area_m2 / WATER_MOLAR_MASS_KG_MOL
    dry_time_s: float | None = math.nan

    if requested_transfer_mol < 0.0 and -requested_transfer_mol > available_liquid_mol:
        # Evaporation is limited by the existing film. Find its exact dryout time,
        # then hold gas inventory constant for the remainder of this interval.
        rise_to_equilibrium = n_equilibrium - n0_mol
        target_fraction = available_liquid_mol / rise_to_equilibrium if rise_to_equilibrium > 0.0 else math.inf
        if not 0.0 <= target_fraction < 1.0:
            raise ArithmeticError("dryout crossing is outside finite-gas equilibrium support")
        dry_time_s = -math.log1p(-target_fraction) / rate if rate > 0.0 else math.inf
        if not math.isfinite(dry_time_s) or dry_time_s < 0.0 or dry_time_s > dt:
            raise ArithmeticError("computed dryout time is outside its interval")
        n1 = n0_mol + available_liquid_mol
        liquid1 = 0.0
        requested_transfer_mol = -available_liquid_mol
    else:
        n1 = n_requested
        liquid1 = liquid0_kg_m2 + requested_transfer_mol * WATER_MOLAR_MASS_KG_MOL / interval.transfer_area_m2
        if liquid1 < 0.0 and liquid1 > -1e-12:
            liquid1 = 0.0

    p1 = n1 * R_GAS_J_MOL_K * interval.gas_temperature_K / interval.gas_volume_m3
    if not all(math.isfinite(value) for value in (n1, liquid1, p1, requested_transfer_mol)) or n1 < 0.0 or liquid1 < 0.0:
        raise ArithmeticError("finite-gas exchange left its nonnegative finite-state domain")
    return n1, liquid1, requested_transfer_mol, dry_time_s, p0, p1


def evaluate_finite_gas_water_condensation_history(
    request: FiniteGasWaterCondensationHistoryRequest,
) -> Calculation:
    """Couple finite gas water inventory to an exact wall-film exchange solution."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "wall_patch_id": request.wall_patch_id,
        "condition_id": request.condition_id,
        "input_sha256": input_digest,
        "initial_gas_water_vapor_moles": request.initial_gas_water_vapor_moles,
        "initial_wall_water_areal_inventory_kg_m2": request.initial_wall_water_areal_inventory_kg_m2,
    }
    reviews = (
        "closed_gas_inventory_and_ideal_partial_pressure_reviewed",
        "fugacity_coefficient_and_transfer_basis_reviewed",
        "fixed_patch_no_lateral_transport_reviewed",
        "wall_saturation_and_liquid_density_applicability_reviewed",
        "piecewise_constant_interval_state_reviewed",
        "calculation_use_authorized",
    )
    missing = [name for name in reviews if not getattr(request, name)]
    missing.extend(
        f"interval[{index}].interval_model_assumptions_reviewed"
        for index, interval in enumerate(request.intervals)
        if not interval.interval_model_assumptions_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing,
            "state_history": [],
            "interval_ledger": [],
        })

    gas_moles = request.initial_gas_water_vapor_moles
    liquid_inventory = request.initial_wall_water_areal_inventory_kg_m2
    state_history: list[dict] = []
    ledger: list[dict] = []
    start_density = request.intervals[0].liquid_water_density_kg_m3
    state_history.append({
        "time_s": 0.0,
        "gas_water_vapor_moles": gas_moles,
        "wall_water_areal_inventory_kg_m2": liquid_inventory,
        "wall_equivalent_film_thickness_m": liquid_inventory / start_density,
        "origin": "caller_initial_state",
    })
    total_gas_to_liquid_mol = 0.0
    total_liquid_to_gas_mol = 0.0
    total_unavailable_evaporation_mol = 0.0
    for index, interval in enumerate(request.intervals):
        n_start, liquid_start = gas_moles, liquid_inventory
        try:
            n_end, liquid_end, transfer_mol, dry_time, p_start, p_end = _finite_gas_interval_end(
                n0_mol=n_start, liquid0_kg_m2=liquid_start, interval=interval
            )
        except (ArithmeticError, OverflowError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": state_history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": str(error),
            })
        dt = interval.end_time_s - interval.start_time_s
        amount_gas_to_liquid = max(0.0, transfer_mol)
        amount_liquid_to_gas = max(0.0, -transfer_mol)
        requested_transfer = (
            (n_start - interval.wall_water_saturation_fugacity_Pa * interval.gas_volume_m3
             / (interval.water_vapor_fugacity_coefficient * R_GAS_J_MOL_K * interval.gas_temperature_K))
            * (1.0 - math.exp(-(
                interval.transfer_area_m2
                * interval.gas_film_molar_transfer_coefficient_mol_m2_s_Pa
                * interval.water_vapor_fugacity_coefficient * R_GAS_J_MOL_K
                * interval.gas_temperature_K / interval.gas_volume_m3
            ) * dt))
        )
        unavailable = max(0.0, -requested_transfer - liquid_start * interval.transfer_area_m2 / WATER_MOLAR_MASS_KG_MOL)
        gas_delta = n_end - n_start
        liquid_delta_mol = (liquid_end - liquid_start) * interval.transfer_area_m2 / WATER_MOLAR_MASS_KG_MOL
        balance_residual = gas_delta + liquid_delta_mol
        if not all(math.isfinite(value) for value in (unavailable, balance_residual, p_start, p_end)):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger),
                "state_history": state_history,
                "interval_ledger": ledger,
                "failed_interval_index": index,
                "failure_reason": "interval closure exceeds finite numeric support",
            })
        total_gas_to_liquid_mol += amount_gas_to_liquid
        total_liquid_to_gas_mol += amount_liquid_to_gas
        total_unavailable_evaporation_mol += unavailable
        ledger.append({
            "interval_index": index,
            "start_time_s": interval.start_time_s,
            "end_time_s": interval.end_time_s,
            "duration_s": dt,
            "gas_temperature_K": interval.gas_temperature_K,
            "gas_volume_m3": interval.gas_volume_m3,
            "water_vapor_fugacity_coefficient": interval.water_vapor_fugacity_coefficient,
            "gas_water_partial_pressure_start_Pa": p_start,
            "gas_water_partial_pressure_end_Pa": p_end,
            "gas_water_fugacity_start_Pa": p_start * interval.water_vapor_fugacity_coefficient,
            "wall_saturation_water_fugacity_Pa": interval.wall_water_saturation_fugacity_Pa,
            "gas_water_vapor_moles_start": n_start,
            "gas_water_vapor_moles_end": n_end,
            "wall_water_areal_inventory_start_kg_m2": liquid_start,
            "wall_water_areal_inventory_end_kg_m2": liquid_end,
            "gas_to_liquid_transfer_mol": amount_gas_to_liquid,
            "liquid_to_gas_transfer_mol": amount_liquid_to_gas,
            "evaporation_requested_beyond_available_film_mol": unavailable,
            "dryout_time_s": None if math.isnan(dry_time) else dry_time,
            "inventory_balance_residual_mol": balance_residual,
            "gas_film_molar_transfer_coefficient_mol_m2_s_Pa": interval.gas_film_molar_transfer_coefficient_mol_m2_s_Pa,
            "transfer_area_m2": interval.transfer_area_m2,
            "transfer_provider_id": interval.transfer_provider_id,
            "transfer_provider_revision": interval.transfer_provider_revision,
            "transfer_configuration_sha256": interval.transfer_configuration_sha256,
            "transfer_result_sha256": interval.transfer_result_sha256,
            "wall_state_provider_id": interval.wall_state_provider_id,
            "wall_state_provider_revision": interval.wall_state_provider_revision,
            "wall_state_configuration_sha256": interval.wall_state_configuration_sha256,
            "wall_state_result_sha256": interval.wall_state_result_sha256,
            "density_record_id": interval.density_record_id,
            "density_record_sha256": interval.density_record_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
            "evidence": [e.model_dump(mode="json") for e in interval.evidence],
        })
        gas_moles, liquid_inventory = n_end, liquid_end
        state_history.append({
            "time_s": interval.end_time_s,
            "gas_water_vapor_moles": gas_moles,
            "wall_water_areal_inventory_kg_m2": liquid_inventory,
            "wall_equivalent_film_thickness_m": liquid_inventory / interval.liquid_water_density_kg_m3,
            "origin": "finite_gas_fugacity_transfer",
        })

    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(ledger),
        "final_gas_water_vapor_moles": gas_moles,
        "final_wall_water_areal_inventory_kg_m2": liquid_inventory,
        "final_wall_equivalent_film_thickness_m": state_history[-1]["wall_equivalent_film_thickness_m"],
        "cumulative_gas_to_liquid_transfer_mol": total_gas_to_liquid_mol,
        "cumulative_liquid_to_gas_transfer_mol": total_liquid_to_gas_mol,
        "cumulative_evaporation_unavailable_after_dryout_mol": total_unavailable_evaporation_mol,
        "state_history": state_history,
        "interval_ledger": ledger,
        "limitations": [
            "Gas water partial pressure uses an ideal-gas species inventory and caller fugacity coefficient; other gas species are not solved.",
            "Each interval is isothermal and isochoric with constant wall saturation fugacity and gas-film transfer coefficient.",
            "No energy balance, latent heat, wall-temperature response, brine/MEG activity, droplets, drainage, or lateral liquid flow is included.",
            "No corrosion rate, scale protection, probability, acceptance, or qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=FiniteGasWaterCondensationHistoryRequest,
        evaluator=evaluate_finite_gas_water_condensation_history,
        units={
            "final_gas_water_vapor_moles": "mol",
            "final_wall_water_areal_inventory_kg_m2": "kg/m^2",
            "final_wall_equivalent_film_thickness_m": "m",
            "cumulative_gas_to_liquid_transfer_mol": "mol",
            "cumulative_liquid_to_gas_transfer_mol": "mol",
            "cumulative_evaporation_unavailable_after_dryout_mol": "mol",
            "interval_ledger[].inventory_balance_residual_mol": "mol",
        },
        assumptions=(
            "Water vapor component pressure follows the ideal-gas relation from finite vapor moles at the supplied interval temperature and gas volume.",
            "Gas-film molar flux is linear in caller fugacity difference with constant coefficient over each interval; the exact exponential solution is used.",
            "The wall liquid is a uniform film on a fixed patch; evaporation is limited to available inventory with exact dryout time under constant interval inputs.",
        ),
        source_ids=(TRANSFER_SOURCE_ID, WALL_STATE_SOURCE_ID, ALGORITHM_SOURCE_ID),
    )]
