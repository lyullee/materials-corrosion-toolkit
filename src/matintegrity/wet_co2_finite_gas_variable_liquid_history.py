"""Coupled finite-gas/variable-liquid CO2star history using caller-owned interval states."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_finite_gas_variable_liquid_history"
SOURCE_ID = "caller_finite_gas_variable_liquid_two_film_balance"
SOLVER_ID = "scipy.integrate.solve_ivp:DOP853"


class WetCo2FiniteGasVariableLiquidInterval(Contract):
    """Piecewise-constant Henry, film, and signed volume-flux conditions."""

    start_time_s: float = Field(ge=0)
    end_time_s: float = Field(gt=0)
    temperature_K: float = Field(gt=0)
    liquid_volume_flux_m_s: float
    incoming_co2star_mol_m3: float = Field(ge=0)
    henry_concentration_over_fugacity_mol_m3_Pa: float = Field(gt=0)
    gas_film_coefficient_mol_m2_s_Pa: float = Field(gt=0)
    liquid_film_coefficient_m_s: float = Field(gt=0)
    interval_provider_id: str = Field(min_length=1)
    interval_provider_revision: str = Field(min_length=1)
    interval_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    interval_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=3, max_length=64)
    interval_state_and_units_reviewed: bool

    @model_validator(mode="after")
    def finite_and_provenance(self):
        numeric = (
            self.start_time_s, self.end_time_s, self.temperature_K,
            self.liquid_volume_flux_m_s, self.incoming_co2star_mol_m3,
            self.henry_concentration_over_fugacity_mol_m3_Pa,
            self.gas_film_coefficient_mol_m2_s_Pa, self.liquid_film_coefficient_m_s,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("all interval inputs must be finite")
        if self.end_time_s <= self.start_time_s:
            raise ValueError("interval end must follow interval start")
        if self.interval_provider_id not in {row.source_id for row in self.evidence}:
            raise ValueError("Evidence must identify the interval state provider")
        return self


class WetCo2FiniteGasVariableLiquidHistoryRequest(Contract):
    """Finite gas inventory exchanging with a time-varying liquid volume per patch area."""

    schema_version: Literal["matintegrity.wet_co2_finite_gas_variable_liquid_history.v1"] = (
        "matintegrity.wet_co2_finite_gas_variable_liquid_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    wall_patch_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    initial_liquid_volume_per_area_m: float = Field(gt=0)
    initial_liquid_co2star_mol_m3: float = Field(ge=0)
    initial_gas_co2_fugacity_Pa: float = Field(ge=0)
    finite_gas_inventory_capacity_mol_m2_Pa: float = Field(gt=0)
    initial_state_provider_id: str = Field(min_length=1)
    initial_state_provider_revision: str = Field(min_length=1)
    initial_state_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_state_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_state_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    intervals: tuple[WetCo2FiniteGasVariableLiquidInterval, ...] = Field(min_length=1, max_length=2000)
    relative_tolerance: float = Field(default=1e-9, ge=1e-12, le=1e-3)
    liquid_concentration_absolute_tolerance_mol_m3: float = Field(default=1e-10, gt=0)
    gas_fugacity_absolute_tolerance_Pa: float = Field(default=1e-3, gt=0)
    areal_mole_absolute_tolerance_mol_m2: float = Field(default=1e-12, gt=0)
    maximum_step_s: float | None = Field(default=None, gt=0)
    fixed_area_and_gas_capacity_reviewed: bool
    positive_volume_flux_is_condensate_inflow_reviewed: bool
    negative_volume_flux_is_well_mixed_liquid_outflow_reviewed: bool
    no_dryout_within_simulated_history_reviewed: bool
    incoming_co2star_convention_reviewed: bool
    no_reaction_or_speciation_change_reviewed: bool
    solver_tolerances_and_use_reviewed: bool
    calculation_use_authorized: bool

    @model_validator(mode="after")
    def exact_intervals_and_positive_volume(self):
        if not all(math.isfinite(value) for value in (
            self.initial_liquid_volume_per_area_m,
            self.initial_liquid_co2star_mol_m3,
            self.initial_gas_co2_fugacity_Pa,
            self.finite_gas_inventory_capacity_mol_m2_Pa,
            self.relative_tolerance,
            self.liquid_concentration_absolute_tolerance_mol_m3,
            self.gas_fugacity_absolute_tolerance_Pa,
            self.areal_mole_absolute_tolerance_mol_m2,
        )):
            raise ValueError("initial state and solver tolerances must be finite")
        if self.maximum_step_s is not None and not math.isfinite(self.maximum_step_s):
            raise ValueError("maximum solver step must be finite when supplied")
        if self.intervals[0].start_time_s != 0.0:
            raise ValueError("history must start at time zero")
        if any(left.end_time_s != right.start_time_s for left, right in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("intervals must be exactly contiguous")
        if self.initial_state_provider_id not in {row.source_id for row in self.initial_state_evidence}:
            raise ValueError("initial-state Evidence must identify its provider")
        volume = self.initial_liquid_volume_per_area_m
        for interval in self.intervals:
            duration = interval.end_time_s - interval.start_time_s
            volume_end = volume + interval.liquid_volume_flux_m_s * duration
            if not math.isfinite(volume_end) or volume_end <= 0.0:
                raise ValueError("liquid volume per area must stay strictly positive; split/restart at dryout")
            volume = volume_end
        return self


def _overall_liquid_velocity(gas_k: float, henry: float, liquid_k: float) -> float | None:
    log_gh = math.log(gas_k) + math.log(henry)
    log_ratio = math.log(liquid_k) - log_gh
    if log_ratio >= 0.0:
        log_overall = log_gh - math.log1p(math.exp(-log_ratio))
    else:
        log_overall = math.log(liquid_k) - math.log1p(math.exp(log_ratio))
    if log_overall > math.log(float.fromhex("0x1.fffffffffffffp+1023")):
        return None
    result = math.exp(log_overall)
    return result if math.isfinite(result) and result > 0.0 else None


def evaluate_wet_co2_finite_gas_variable_liquid_history(
    request: WetCo2FiniteGasVariableLiquidHistoryRequest,
) -> Calculation:
    """Numerically integrate gas/liquid CO2star inventories and water-volume flux by interval."""
    input_sha = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "wall_patch_id": request.wall_patch_id,
        "condition_id": request.condition_id,
        "input_sha256": input_sha,
        "initial_liquid_volume_per_area_m": request.initial_liquid_volume_per_area_m,
        "initial_liquid_co2star_mol_m3": request.initial_liquid_co2star_mol_m3,
        "initial_gas_co2_fugacity_Pa": request.initial_gas_co2_fugacity_Pa,
        "finite_gas_inventory_capacity_mol_m2_Pa": request.finite_gas_inventory_capacity_mol_m2_Pa,
        "initial_state_provider_id": request.initial_state_provider_id,
        "initial_state_provider_revision": request.initial_state_provider_revision,
        "initial_state_configuration_sha256": request.initial_state_configuration_sha256,
        "initial_state_result_sha256": request.initial_state_result_sha256,
        "initial_state_evidence": [row.model_dump(mode="json") for row in request.initial_state_evidence],
    }
    review_names = (
        "fixed_area_and_gas_capacity_reviewed",
        "positive_volume_flux_is_condensate_inflow_reviewed",
        "negative_volume_flux_is_well_mixed_liquid_outflow_reviewed",
        "no_dryout_within_simulated_history_reviewed",
        "incoming_co2star_convention_reviewed",
        "no_reaction_or_speciation_change_reviewed",
        "solver_tolerances_and_use_reviewed",
        "calculation_use_authorized",
    )
    missing = [name for name in review_names if not getattr(request, name)]
    missing.extend(
        f"interval[{index}].interval_state_and_units_reviewed"
        for index, interval in enumerate(request.intervals)
        if not interval.interval_state_and_units_reviewed
    )
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    try:
        import scipy
        from scipy.integrate import solve_ivp
    except ImportError as exc:
        return Calculation(status="needs_data", values=base | {
            "missing_dependency": "scipy",
            "failure_reason": "SciPy is optional for this coupled variable-volume integration path",
        })

    y = [
        request.initial_liquid_co2star_mol_m3,
        request.initial_gas_co2_fugacity_Pa,
        0.0,
        0.0,
    ]
    volume = request.initial_liquid_volume_per_area_m
    initial_total_inventory = (
        volume * y[0] + request.finite_gas_inventory_capacity_mol_m2_Pa * y[1]
    )
    if not math.isfinite(initial_total_inventory):
        return Calculation(status="out_of_scope", values=base | {
            "failure_reason": "initial combined gas/liquid CO2star inventory exceeds finite support",
        })
    history = [{
        "time_s": 0.0,
        "liquid_volume_per_area_m": volume,
        "liquid_co2star_mol_m3": y[0],
        "gas_co2_fugacity_Pa": y[1],
        "liquid_co2star_areal_inventory_mol_m2": volume * y[0],
        "gas_co2_areal_inventory_mol_m2": request.finite_gas_inventory_capacity_mol_m2_Pa * y[1],
        "cumulative_signed_gas_to_liquid_transfer_mol_m2": 0.0,
        "cumulative_waterborne_co2star_transfer_mol_m2": 0.0,
        "origin": "caller_initial_state",
    }]
    ledger: list[dict] = []
    atol = (
        request.liquid_concentration_absolute_tolerance_mol_m3,
        request.gas_fugacity_absolute_tolerance_Pa,
        request.areal_mole_absolute_tolerance_mol_m2,
        request.areal_mole_absolute_tolerance_mol_m2,
    )
    solver_config = {
        "provider_id": SOLVER_ID,
        "solver_method": "DOP853",
        "relative_tolerance": request.relative_tolerance,
        "absolute_tolerances": list(atol),
        "maximum_step_s": request.maximum_step_s,
        "scipy_version": scipy.__version__,
    }

    for index, interval in enumerate(request.intervals):
        start, end = interval.start_time_s, interval.end_time_s
        dt = end - start
        q = interval.liquid_volume_flux_m_s
        beta = request.finite_gas_inventory_capacity_mol_m2_Pa
        henry = interval.henry_concentration_over_fugacity_mol_m3_Pa
        overall_k = _overall_liquid_velocity(
            interval.gas_film_coefficient_mol_m2_s_Pa, henry,
            interval.liquid_film_coefficient_m_s,
        )
        if overall_k is None:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "failure_reason": "overall transfer velocity outside finite support",
            })

        def rhs(time_s, state):
            c_liquid, fugacity, gas_to_liquid_cumulative, waterborne_cumulative = state
            liquid_volume = volume + q * (time_s - start)
            if liquid_volume <= 0.0:
                raise ValueError("liquid volume reached dryout inside an interval")
            transfer_flux = overall_k * (henry * fugacity - c_liquid)
            if q > 0.0:
                dc_dt = (transfer_flux + q * interval.incoming_co2star_mol_m3 - q * c_liquid) / liquid_volume
                waterborne_rate = q * interval.incoming_co2star_mol_m3
            elif q < 0.0:
                dc_dt = transfer_flux / liquid_volume
                waterborne_rate = q * c_liquid
            else:
                dc_dt = transfer_flux / liquid_volume
                waterborne_rate = 0.0
            df_dt = -transfer_flux / beta
            return (dc_dt, df_dt, transfer_flux, waterborne_rate)

        try:
            solution = solve_ivp(
                rhs,
                (start, end),
                y,
                method="DOP853",
                rtol=request.relative_tolerance,
                atol=atol,
                max_step=request.maximum_step_s if request.maximum_step_s is not None else math.inf,
            )
        except Exception as exc:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "failure_reason": f"coupled variable-volume ODE solver failed: {type(exc).__name__}",
            })
        if not solution.success or solution.y.shape != (4, len(solution.t)) or solution.t[-1] != end:
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "solver_message": str(solution.message),
                "failure_reason": "DOP853 did not reach the exact interval endpoint",
            })
        y_end = [float(row[-1]) for row in solution.y]
        interval_gas_transfer = y_end[2] - y[2]
        interval_waterborne_transfer = y_end[3] - y[3]
        volume_end = volume + q * dt
        c_start, f_start = y[0], y[1]
        liquid_inventory_start = volume * c_start
        gas_inventory_start = beta * f_start
        liquid_inventory_end = volume_end * y_end[0]
        gas_inventory_end = beta * y_end[1]
        total_start = liquid_inventory_start + gas_inventory_start
        total_end = liquid_inventory_end + gas_inventory_end
        residual = total_end - total_start - interval_waterborne_transfer
        outputs = (
            *y_end, volume_end, liquid_inventory_end, gas_inventory_end,
            total_start, total_end, interval_waterborne_transfer,
            interval_gas_transfer, residual,
        )
        if not all(math.isfinite(value) for value in outputs) or any(value < 0.0 for value in y_end[:2]):
            return Calculation(status="out_of_scope", values=base | {
                "committed_interval_count": len(ledger), "state_history": history,
                "interval_ledger": ledger, "failed_interval_index": index,
                "failure_reason": "integrated state or inventory is outside finite nonnegative support",
            })

        gas_to_liquid_transfer = interval_gas_transfer
        ledger.append({
            "interval_index": index,
            "start_time_s": start,
            "end_time_s": end,
            "duration_s": dt,
            "temperature_K": interval.temperature_K,
            "liquid_volume_flux_m_s": q,
            "liquid_volume_per_area_start_m": volume,
            "liquid_volume_per_area_end_m": volume_end,
            "initial_liquid_co2star_mol_m3": c_start,
            "final_liquid_co2star_mol_m3": y_end[0],
            "initial_gas_co2_fugacity_Pa": f_start,
            "final_gas_co2_fugacity_Pa": y_end[1],
            "henry_concentration_over_fugacity_mol_m3_Pa": henry,
            "overall_liquid_basis_transfer_velocity_m_s": overall_k,
            "signed_gas_to_liquid_transfer_mol_m2": gas_to_liquid_transfer,
            "signed_waterborne_co2star_transfer_mol_m2": interval_waterborne_transfer,
            "gas_inventory_start_mol_m2": gas_inventory_start,
            "gas_inventory_end_mol_m2": gas_inventory_end,
            "liquid_inventory_start_mol_m2": liquid_inventory_start,
            "liquid_inventory_end_mol_m2": liquid_inventory_end,
            "combined_inventory_balance_residual_mol_m2": residual,
            "solver_id": SOLVER_ID,
            "solver_revision": scipy.__version__,
            "solver_nfev": int(solution.nfev),
            "solver_configuration": solver_config,
            "solver_configuration_sha256": canonical_digest(solver_config),
            "interval_provider_id": interval.interval_provider_id,
            "interval_provider_revision": interval.interval_provider_revision,
            "interval_configuration_sha256": interval.interval_configuration_sha256,
            "interval_result_sha256": interval.interval_result_sha256,
            "interval_input_sha256": canonical_digest(interval.model_dump(mode="json")),
            "evidence": [row.model_dump(mode="json") for row in interval.evidence],
        })
        y = y_end
        volume = volume_end
        history.append({
            "time_s": end,
            "liquid_volume_per_area_m": volume,
            "liquid_co2star_mol_m3": y[0],
            "gas_co2_fugacity_Pa": y[1],
            "liquid_co2star_areal_inventory_mol_m2": liquid_inventory_end,
            "gas_co2_areal_inventory_mol_m2": gas_inventory_end,
            "cumulative_signed_gas_to_liquid_transfer_mol_m2": y[2],
            "cumulative_waterborne_co2star_transfer_mol_m2": y[3],
            "origin": "integrated_finite_gas_variable_liquid_two_film_balance",
        })

    return Calculation(values=base | {
        "status": "computed",
        "interval_count": len(ledger),
        "state_history": history,
        "interval_ledger": ledger,
        "final_liquid_volume_per_area_m": volume,
        "final_liquid_co2star_mol_m3": y[0],
        "final_gas_co2_fugacity_Pa": y[1],
        "cumulative_signed_gas_to_liquid_transfer_mol_m2": y[2],
        "cumulative_signed_waterborne_co2star_transfer_mol_m2": y[3],
        "solver": solver_config,
        "interpretation_boundary": "Finite gas capacity and variable-volume, well-mixed CO2star liquid inventory per fixed interface area; no gas EOS or carbonate chemistry is solved.",
        "not_inferred": [
            "liquid volume flux, incoming-condensate CO2star state or any property data",
            "gas inventory capacity from pressure-volume-temperature or an EOS",
            "gas-liquid hydrodynamics, liquid spatial gradients or dryout events",
            "reaction, carbonate speciation, pH, scale, corrosion, wall loss or risk",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2FiniteGasVariableLiquidHistoryRequest,
        evaluator=evaluate_wet_co2_finite_gas_variable_liquid_history,
        units={
            "initial_liquid_volume_per_area_m": "m3/m2",
            "initial_liquid_co2star_mol_m3": "mol/m3",
            "initial_gas_co2_fugacity_Pa": "Pa",
            "finite_gas_inventory_capacity_mol_m2_Pa": "mol/(m2 Pa)",
            "state_history[].liquid_volume_per_area_m": "m3/m2",
            "state_history[].liquid_co2star_areal_inventory_mol_m2": "mol/m2",
            "state_history[].gas_co2_areal_inventory_mol_m2": "mol/m2",
            "cumulative_signed_gas_to_liquid_transfer_mol_m2": "mol/m2",
        },
        assumptions=(
            "Per-area gas inventory capacity, patch area, volume flux, Henry coefficient and film coefficients are caller-reviewed.",
            "Liquid is well mixed; volume influx has caller-supplied CO2star concentration and outflow removes dissolved CO2star at bulk concentration.",
            "Finite gas reservoir pressure/fugacity responds only through the declared constant inventory capacity; no equation of state is used.",
            "The piecewise interval ODE is numerically integrated with caller-declared tolerances using SciPy DOP853.",
        ),
        source_ids=(SOURCE_ID, "scipy_integrate_solve_ivp", "scipy_integrate_dop853"),
        qualification="user_model",
        runtime_dependency_names=("scipy",),
    )]
