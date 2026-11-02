"""Exact piecewise-constant solution for a caller-defined lumped crevice species balance."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class CreviceLumpedExchangeReactionHistory(Contract):
    """Single-species, constant-volume well-mixed control-volume screening model."""

    schema_version: Literal["matintegrity.crevice_lumped_exchange_reaction_history.v1"] = (
        "matintegrity.crevice_lumped_exchange_reaction_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    time_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=100001)
    control_volume_m3: Positive
    initial_concentration_mol_m3: Nonnegative
    bulk_concentration_by_interval_mol_m3: tuple[Nonnegative, ...] = Field(min_length=1, max_length=100000)
    exchange_flow_by_interval_m3_s: tuple[Nonnegative, ...] = Field(min_length=1, max_length=100000)
    first_order_sink_rate_by_interval_s: tuple[Nonnegative, ...] = Field(min_length=1, max_length=100000)
    model_provider_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    single_mixed_volume_and_constant_volume_reviewed: bool
    interval_constant_forcing_and_sink_law_reviewed: bool
    concentration_units_and_species_identity_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_interval_inputs(self):
        interval_count = len(self.time_s) - 1
        if any(right <= left for left, right in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("time knots must increase strictly")
        if any(len(values) != interval_count for values in (
            self.bulk_concentration_by_interval_mol_m3,
            self.exchange_flow_by_interval_m3_s,
            self.first_order_sink_rate_by_interval_s,
        )):
            raise ValueError("each forcing and sink history must provide one value per half-open interval")
        if not self.usage_rights_evidence:
            raise ValueError("usage-rights Evidence is required")
        if not any(row.license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify a license or permitted-use basis")
        if not any(
            row.source_id == self.model_provider_id and row.sha256 is not None
            for row in self.evidence
        ):
            raise ValueError("model/input provider ID and hashed Evidence must be linked")
        return self


def solve_crevice_lumped_exchange_reaction(
    request: CreviceLumpedExchangeReactionHistory,
) -> Calculation:
    """Solve dC/dt=(Q/V)(C_bulk-C)-k*C exactly on caller-declared intervals."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "species_id": request.species_id,
        "model_provider_id": request.model_provider_id,
        "model_revision": request.model_revision,
        "input_sha256": input_digest,
        "time_s": list(request.time_s),
        "control_volume_m3": request.control_volume_m3,
        "state_model": "single_species_constant_volume_well_mixed_linear_exchange_plus_first_order_sink",
        "probability_or_acceptance_claim": False,
    }
    reviews = {
        "single_mixed_volume_and_constant_volume_reviewed": request.single_mixed_volume_and_constant_volume_reviewed,
        "interval_constant_forcing_and_sink_law_reviewed": request.interval_constant_forcing_and_sink_law_reviewed,
        "concentration_units_and_species_identity_reviewed": request.concentration_units_and_species_identity_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, passed in reviews.items() if not passed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    concentration = request.initial_concentration_mol_m3
    concentrations = [concentration]
    interval_rows = []
    cumulative_sink = 0.0
    cumulative_exchange = 0.0
    try:
        for index, (start, end, bulk, flow, sink_rate) in enumerate(zip(
            request.time_s[:-1], request.time_s[1:],
            request.bulk_concentration_by_interval_mol_m3,
            request.exchange_flow_by_interval_m3_s,
            request.first_order_sink_rate_by_interval_s,
            strict=True,
        )):
            duration = end - start
            exchange_rate = flow / request.control_volume_m3
            total_rate = math.fsum((exchange_rate, sink_rate))
            if not math.isfinite(exchange_rate) or not math.isfinite(total_rate):
                raise ArithmeticError("combined exchange and sink rate exceeds finite numeric support")
            if total_rate == 0.0:
                steady = concentration
                decay = 1.0
                concentration_integral = concentration * duration
            else:
                steady = exchange_rate * bulk / total_rate
                exponent = total_rate * duration
                if exponent > 745.0:
                    decay = 0.0
                    integral_kernel = 1.0 / total_rate
                else:
                    decay = math.exp(-exponent)
                    integral_kernel = -math.expm1(-exponent) / total_rate
                concentration_integral = steady * duration + (concentration - steady) * integral_kernel
            next_concentration = steady + (concentration - steady) * decay
            if not all(math.isfinite(value) for value in (steady, next_concentration, concentration_integral)):
                raise ArithmeticError("concentration solution exceeds finite numeric support")
            if next_concentration < 0.0 or concentration_integral < 0.0:
                raise ArithmeticError("computed state left the nonnegative concentration domain")

            net_exchange_mol = flow * (bulk * duration - concentration_integral)
            sink_consumed_mol = request.control_volume_m3 * sink_rate * concentration_integral
            inventory_change_mol = request.control_volume_m3 * (next_concentration - concentration)
            closure_residual_mol = inventory_change_mol - (net_exchange_mol - sink_consumed_mol)
            if not all(math.isfinite(value) for value in (
                net_exchange_mol, sink_consumed_mol, inventory_change_mol, closure_residual_mol
            )):
                raise ArithmeticError("integrated exchange or reaction ledger exceeds finite numeric support")
            cumulative_exchange = math.fsum((cumulative_exchange, net_exchange_mol))
            cumulative_sink = math.fsum((cumulative_sink, sink_consumed_mol))
            if not math.isfinite(cumulative_exchange) or not math.isfinite(cumulative_sink):
                raise ArithmeticError("cumulative ledger exceeds finite numeric support")
            interval_rows.append({
                "interval_index": index,
                "start_time_s": start,
                "end_time_s": end,
                "bulk_concentration_mol_m3": bulk,
                "exchange_flow_m3_s": flow,
                "first_order_sink_rate_s": sink_rate,
                "start_concentration_mol_m3": concentration,
                "end_concentration_mol_m3": next_concentration,
                "net_exchange_mol": net_exchange_mol,
                "sink_consumed_mol": sink_consumed_mol,
                "inventory_change_mol": inventory_change_mol,
                "mass_balance_residual_mol": closure_residual_mol,
            })
            concentration = next_concentration
            concentrations.append(concentration)
    except (ArithmeticError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "completed_interval_count": len(interval_rows),
            "concentration_prefix_mol_m3": concentrations,
            "failed_interval_index": len(interval_rows),
            "reason": str(error),
        })

    final_inventory = request.control_volume_m3 * concentration
    if not math.isfinite(final_inventory):
        return Calculation(status="out_of_scope", values=base | {
            "completed_interval_count": len(interval_rows),
            "concentration_prefix_mol_m3": concentrations,
            "reason": "final_inventory_exceeded_finite_numeric_support",
        })
    return Calculation(values=base | {
        "concentration_history_mol_m3": concentrations,
        "interval_balances": interval_rows,
        "cumulative_net_exchange_mol": cumulative_exchange,
        "cumulative_sink_consumed_mol": cumulative_sink,
        "final_inventory_mol": final_inventory,
        "interval_solution": "closed_form_exact_for_piecewise_constant_Q_Cbulk_k_and_fixed_volume",
        "mixing_assumption": "each control volume is spatially uniform; no gradients are represented",
    }, notes=(
        "The state follows dC/dt=(Q/V)(C_bulk-C)-k*C with nonnegative caller-supplied flow, bulk concentration and first-order sink coefficient on each interval.",
        "This lumped single-species calculation is not the spatial restricted-transport solver, a multiphase speciation model, a calibrated reaction law, or a corrosion/acceptance prediction.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "degradation.crevice_lumped_exchange_reaction_history",
        CreviceLumpedExchangeReactionHistory,
        solve_crevice_lumped_exchange_reaction,
        {
            "concentration_history_mol_m3[]": "mol/m^3",
            "final_inventory_mol": "mol",
            "cumulative_net_exchange_mol": "mol",
            "cumulative_sink_consumed_mol": "mol",
            "interval_balances[].mass_balance_residual_mol": "mol",
        },
        (
            "Solve a caller-declared fixed-volume, single-species well-mixed exchange and first-order sink balance with exact interval propagation.",
            "This is a lumped screening model; it does not replace spatial transport, speciation, calibrated kinetics, wall loss or qualification.",
        ),
        ("caller_lumped_crevice_exchange_first_order_reaction",),
        qualification="user_model",
    )]
