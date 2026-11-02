"""Exact-knot Arrhenius scaling for a caller-reviewed crevice wall-sink law."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from .models.corrosion import ArrheniusRate, arrhenius
from .registry import ModelSpec

MODEL_ID = "degradation.crevice_wall_sink_rate_history"
SOURCE_ID = "caller_crevice_arrhenius_wall_sink_rate_history"


class CreviceWallSinkRateHistoryRequest(Contract):
    """Caller-supplied exact temperature knots and one Arrhenius wall coefficient."""

    schema_version: Literal["matintegrity.crevice_wall_sink_rate_history.v1"] = (
        "matintegrity.crevice_wall_sink_rate_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    elapsed_time_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=5000)
    temperature_K: tuple[Positive, ...] = Field(min_length=2, max_length=5000)
    reference_wall_transfer_velocity_m_s: Nonnegative
    activation_energy_J_mol: Nonnegative
    reference_temperature_K: Positive
    minimum_supported_temperature_K: Positive
    maximum_supported_temperature_K: Positive
    activation_parameter_and_use_reviewed: bool
    temperature_history_to_condition_mapping_reviewed: bool
    first_order_irreversible_wall_law_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_history_and_support(self):
        if len(self.elapsed_time_s) != len(self.temperature_K):
            raise ValueError("time and temperature knot counts must match exactly")
        if any(b <= a for a, b in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)):
            raise ValueError("elapsed-time knots must be strictly increasing in caller order")
        if self.minimum_supported_temperature_K >= self.maximum_supported_temperature_K:
            raise ValueError("declared temperature support must have positive width")
        if not self.minimum_supported_temperature_K <= self.reference_temperature_K <= self.maximum_supported_temperature_K:
            raise ValueError("reference temperature must lie within declared support")
        return self


def evaluate_crevice_wall_sink_rate_history(
    request: CreviceWallSinkRateHistoryRequest,
) -> Calculation:
    """Scale a caller's linear wall-sink velocity at exact temperature knots.

    The shared corrosion Arrhenius calculator performs each temperature
    transform. This adapter adds crevice identities, explicit applicability
    support, Evidence lineage and exact clock alignment. It does not interpolate
    temperatures or integrate a transport history.
    """
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "geometry_id": request.geometry_id,
        "species_id": request.species_id,
        "condition_id": request.condition_id,
        "input_sha256": input_sha256,
        "reference_wall_transfer_velocity_m_s": request.reference_wall_transfer_velocity_m_s,
        "activation_energy_J_mol": request.activation_energy_J_mol,
        "reference_temperature_K": request.reference_temperature_K,
        "temperature_support_K": [
            request.minimum_supported_temperature_K,
            request.maximum_supported_temperature_K,
        ],
        "elapsed_time_s": list(request.elapsed_time_s),
        "temperature_K": list(request.temperature_K),
        "evidence": [row.model_dump(mode="json") for row in request.evidence],
        "source_ids": sorted({row.source_id for row in request.evidence}),
        "temperature_interpolation_performed": False,
        "temperature_extrapolation_performed": False,
        "wall_law_fitted": False,
    }
    missing_reviews = [
        name for name, reviewed in (
            ("activation_parameter_and_use_reviewed", request.activation_parameter_and_use_reviewed),
            ("temperature_history_to_condition_mapping_reviewed", request.temperature_history_to_condition_mapping_reviewed),
            ("first_order_irreversible_wall_law_reviewed", request.first_order_irreversible_wall_law_reviewed),
        ) if not reviewed
    ]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing_reviews})

    outside_support = [
        {"knot_index": index, "elapsed_time_s": time_s, "temperature_K": temperature}
        for index, (time_s, temperature) in enumerate(zip(
            request.elapsed_time_s, request.temperature_K, strict=True
        ))
        if not request.minimum_supported_temperature_K <= temperature <= request.maximum_supported_temperature_K
    ]
    if outside_support:
        return Calculation(status="out_of_scope", values=base | {
            "outside_temperature_support_knots": outside_support,
            "wall_rate_knots": [],
            "complete_history_returned": False,
        }, notes=("No temperature interpolation or extrapolation was used; the rate history is withheld when any knot is unsupported.",))

    rows = []
    for index, (time_s, temperature) in enumerate(zip(
        request.elapsed_time_s, request.temperature_K, strict=True
    )):
        try:
            scaled = arrhenius(ArrheniusRate(
                reference_rate=request.reference_wall_transfer_velocity_m_s,
                reference_temperature_K=request.reference_temperature_K,
                temperature_K=temperature,
                activation_energy_J_mol=request.activation_energy_J_mol,
            ))
        except (OverflowError, ValueError):
            return Calculation(status="out_of_scope", values=base | {
                "wall_rate_knots": [],
                "first_failure": {
                    "knot_index": index,
                    "elapsed_time_s": time_s,
                    "temperature_K": temperature,
                    "reason": "Arrhenius_factor_outside_finite_support",
                },
                "complete_history_returned": False,
            }, notes=("The result is atomic: no incomplete rate history was returned.",))
        rate = scaled.values["rate"]
        factor = scaled.values["temperature_factor"]
        if not (math.isfinite(rate) and math.isfinite(factor)) or (
            request.reference_wall_transfer_velocity_m_s > 0.0 and factor == 0.0
        ):
            return Calculation(status="out_of_scope", values=base | {
                "wall_rate_knots": [],
                "first_failure": {
                    "knot_index": index,
                    "elapsed_time_s": time_s,
                    "temperature_K": temperature,
                    "reason": "nonfinite_or_underflowed_Arrhenius_result",
                },
                "complete_history_returned": False,
            })
        rows.append({
            "knot_index": index,
            "elapsed_time_s": time_s,
            "temperature_K": temperature,
            "temperature_factor": factor,
            "wall_transfer_velocity_m_s": rate,
            "rate_input_sha256": canonical_digest({
                "history_input_sha256": input_sha256,
                "knot_index": index,
                "elapsed_time_s": time_s,
                "temperature_K": temperature,
                "reference_wall_transfer_velocity_m_s": request.reference_wall_transfer_velocity_m_s,
                "reference_temperature_K": request.reference_temperature_K,
                "activation_energy_J_mol": request.activation_energy_J_mol,
            }),
        })

    return Calculation(values=base | {
        "units": {
            "elapsed_time": "s",
            "temperature": "K",
            "activation_energy": "J/mol",
            "reference_wall_transfer_velocity": "m/s",
            "wall_transfer_velocity": "m/s",
            "temperature_factor": "1",
        },
        "wall_rate_knots": rows,
        "rate_law": "k(T) = k_ref * exp[-Ea/R * (1/T - 1/T_ref)]",
        "gas_constant_J_mol_K": 8.31446261815324,
        "law_parameter_origin": "caller_supplied_reviewed_reference_rate_and_activation_energy",
        "inter_knot_rate_evaluation": False,
        "transport_or_concentration_history_solved": False,
        "corrosion_rate_or_wall_loss_inferred": False,
        "qualification_claimed": False,
        "complete_history_returned": True,
    }, notes=(
        "The output is a finite table of caller-reviewed wall-transfer velocities at exact caller temperature knots.",
        "This adapter does not fit activation parameters, interpolate between knots, feed a time-varying coefficient into the transient solver, or establish corrosion kinetics or qualification.",
    ))


def _validate_context(request: CreviceWallSinkRateHistoryRequest, context: RunContext) -> None:
    if (request.asset_id, request.location_id) != (context.asset_id, context.location_id):
        raise ValueError("wall-sink rate-history RunContext must match the request asset and location")


def specifications() -> list[ModelSpec]:
    """Expose the exact-knot rate-history calculator for registry integration."""
    return [ModelSpec(
        MODEL_ID,
        CreviceWallSinkRateHistoryRequest,
        evaluate_crevice_wall_sink_rate_history,
        {
            "elapsed_time_s[]": "s",
            "temperature_K[]": "K",
            "reference_wall_transfer_velocity_m_s": "m/s",
            "activation_energy_J_mol": "J/mol",
            "reference_temperature_K": "K",
            "temperature_support_K[]": "K",
            "wall_rate_knots[].elapsed_time_s": "s",
            "wall_rate_knots[].temperature_K": "K",
            "wall_rate_knots[].temperature_factor": "1",
            "wall_rate_knots[].wall_transfer_velocity_m_s": "m/s",
        },
        (
            "Reference rate and activation energy are caller-supplied reviewed wall-law parameters; they are not fitted from the supplied temperature history.",
            "Every temperature knot must lie in the caller-declared support; no interpolation or extrapolation is performed.",
            "The finite rate table is not a transient transport solution and does not establish corrosion kinetics, wall loss or qualification.",
        ),
        (SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_context,
    )]
