"""Exact-knot wrapper around the steady wet-CO2 two-film transfer calculation."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Nonnegative, RunContext, canonical_digest
from .registry import ModelSpec
from .wet_co2_two_film_transfer import (
    WetCo2TwoFilmTransferRequest,
    evaluate_wet_co2_two_film_transfer,
)

MODEL_ID = "degradation.wet_co2_two_film_transfer_history"
SOURCE_ID = "caller_wet_co2_two_film_transfer_history"


class WetCo2TwoFilmTransferKnot(Contract):
    """One exact point state; no interpolation is performed around it."""

    time_s: Nonnegative
    transfer_request: WetCo2TwoFilmTransferRequest

    @model_validator(mode="after")
    def exact_request_clock(self):
        if self.transfer_request.time_s != self.time_s:
            raise ValueError("knot time must exactly match the nested two-film request time")
        return self


class WetCo2TwoFilmTransferHistoryRequest(Contract):
    """Caller-ordered exact-time states for independent steady two-film solves."""

    schema_version: Literal["matintegrity.wet_co2_two_film_transfer_history.v1"] = (
        "matintegrity.wet_co2_two_film_transfer_history.v1"
    )
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    knots: tuple[WetCo2TwoFilmTransferKnot, ...] = Field(min_length=1, max_length=5000)
    exact_knot_state_alignment_reviewed: bool
    independent_steady_state_interpretation_reviewed: bool
    no_inter_knot_interpolation_or_dynamics_reviewed: bool
    complete_prefix_failure_semantics_reviewed: bool

    @model_validator(mode="after")
    def validate_knot_identity_and_clock(self):
        times = [row.time_s for row in self.knots]
        if any(right <= left for left, right in zip(times[:-1], times[1:], strict=True)):
            raise ValueError("history knots must be strictly increasing in caller order")
        request_ids = [row.transfer_request.assessment_id for row in self.knots]
        if len(request_ids) != len(set(request_ids)):
            raise ValueError("each history knot must have a unique nested assessment ID")
        for row in self.knots:
            request = row.transfer_request
            if (request.asset_id, request.location_id) != (self.asset_id, self.location_id):
                raise ValueError("each two-film request must match the history asset and location")
        return self


def evaluate_wet_co2_two_film_transfer_history(
    request: WetCo2TwoFilmTransferHistoryRequest,
) -> Calculation:
    """Evaluate each explicitly supplied steady state in strict time order.

    Every point is passed independently to the existing two-film evaluator.
    On the first non-computed point, retain only the complete successful prefix
    and report the failed point and its input/result lineage. No temporal model,
    interpolation, equilibrium propagation or averaging is performed.
    """
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "history_id": request.history_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "time_basis": request.time_basis,
        "input_sha256": input_sha256,
        "requested_knot_count": len(request.knots),
        "exact_knot_state_alignment_reviewed": request.exact_knot_state_alignment_reviewed,
        "independent_steady_state_interpretation_reviewed": request.independent_steady_state_interpretation_reviewed,
        "no_inter_knot_interpolation_or_dynamics_reviewed": request.no_inter_knot_interpolation_or_dynamics_reviewed,
        "complete_prefix_failure_semantics_reviewed": request.complete_prefix_failure_semantics_reviewed,
        "inter_knot_interpolation_performed": False,
        "inter_knot_dynamics_solved": False,
        "equilibrium_propagation_performed": False,
    }
    missing_reviews = [
        name for name, reviewed in (
            ("exact_knot_state_alignment_reviewed", request.exact_knot_state_alignment_reviewed),
            ("independent_steady_state_interpretation_reviewed", request.independent_steady_state_interpretation_reviewed),
            ("no_inter_knot_interpolation_or_dynamics_reviewed", request.no_inter_knot_interpolation_or_dynamics_reviewed),
            ("complete_prefix_failure_semantics_reviewed", request.complete_prefix_failure_semantics_reviewed),
        ) if not reviewed
    ]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing_reviews,
            "committed_prefix": [],
            "committed_prefix_length": 0,
            "complete_requested_history_returned": False,
        })

    prefix = []
    for index, knot in enumerate(request.knots):
        transfer_request = knot.transfer_request
        transfer_input = transfer_request.model_dump(mode="json")
        transfer_input_sha256 = canonical_digest(transfer_input)
        source_evidence = [row.model_dump(mode="json") for row in transfer_request.evidence]
        source_lineage_sha256 = canonical_digest({
            "evidence": source_evidence,
            "fugacity_provider_id": transfer_request.fugacity_provider_id,
            "fugacity_provider_revision": transfer_request.fugacity_provider_revision,
            "henry_record_id": transfer_request.henry_record_id,
            "solvent_composition_sha256": transfer_request.solvent_composition_sha256,
        })
        result = evaluate_wet_co2_two_film_transfer(transfer_request)
        result_sha256 = canonical_digest(result.model_dump(mode="json"))
        if result.status != "computed":
            return Calculation(status=result.status, values=base | {
                "committed_prefix": prefix,
                "committed_prefix_length": len(prefix),
                "committed_prefix_sha256": canonical_digest(prefix),
                "first_failure": {
                    "knot_index": index,
                    "time_s": knot.time_s,
                    "assessment_id": transfer_request.assessment_id,
                    "input_sha256": transfer_input_sha256,
                    "source_lineage_sha256": source_lineage_sha256,
                    "source_ids": sorted({row.source_id for row in transfer_request.evidence}),
                    "source_evidence": source_evidence,
                    "source_evidence_sha256": [
                        row.sha256 for row in transfer_request.evidence if row.sha256 is not None
                    ],
                    "result_sha256": result_sha256,
                    "status": result.status,
                    "values": result.values,
                    "notes": list(result.notes),
                },
                "complete_requested_history_returned": False,
            }, notes=(
                "Evaluation stopped at the first non-computed point; no later knot was evaluated and the failed point was not appended to the committed prefix.",
            ))
        prefix.append({
            "knot_index": index,
            "time_s": knot.time_s,
            "assessment_id": transfer_request.assessment_id,
            "input_sha256": transfer_input_sha256,
            "source_lineage_sha256": source_lineage_sha256,
            "source_ids": sorted({row.source_id for row in transfer_request.evidence}),
            "source_evidence": source_evidence,
            "source_evidence_sha256": [
                row.sha256 for row in transfer_request.evidence if row.sha256 is not None
            ],
            "result_sha256": result_sha256,
            "result_values": result.values,
        })

    return Calculation(values=base | {
        "units": {
            "time_s": "s",
            "knot_rows[].time_s": "s",
            "knot_rows[].result_values.temperature_K": "K",
            "knot_rows[].result_values.co2_fugacity_Pa": "Pa",
            "knot_rows[].result_values.bulk_co2star_mol_m3": "mol/m3",
            "knot_rows[].result_values.interfacial_fugacity_Pa": "Pa",
            "knot_rows[].result_values.interfacial_CO2star_mol_m3": "mol/m3",
            "knot_rows[].result_values.signed_gas_to_liquid_CO2_flux_mol_m2_s": "mol/m2/s",
        },
        "knot_rows": prefix,
        "committed_prefix": prefix,
        "committed_prefix_length": len(prefix),
        "committed_prefix_sha256": canonical_digest(prefix),
        "first_failure": None,
        "complete_requested_history_returned": True,
    }, notes=(
        "Each caller knot was evaluated as an independent steady two-film state using the existing point evaluator.",
        "The returned ordered table is not a transient gas/liquid transfer history; no inter-knot interpolation, dynamic storage, equilibrium propagation or corrosion response was computed.",
    ))


def _validate_context(request: WetCo2TwoFilmTransferHistoryRequest, context: RunContext) -> None:
    if (request.asset_id, request.location_id, request.time_basis) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("two-film history RunContext must match request asset, location and time basis")


def specifications() -> list[ModelSpec]:
    """Expose the exact-knot history wrapper for registry integration."""
    return [ModelSpec(
        MODEL_ID,
        WetCo2TwoFilmTransferHistoryRequest,
        evaluate_wet_co2_two_film_transfer_history,
        {
            "committed_prefix_length": "count",
            "knot_rows[].time_s": "s",
            "knot_rows[].result_values.temperature_K": "K",
            "knot_rows[].result_values.co2_fugacity_Pa": "Pa",
            "knot_rows[].result_values.bulk_co2star_mol_m3": "mol/m3",
            "knot_rows[].result_values.interfacial_fugacity_Pa": "Pa",
            "knot_rows[].result_values.interfacial_CO2star_mol_m3": "mol/m3",
            "knot_rows[].result_values.signed_gas_to_liquid_CO2_flux_mol_m2_s": "mol/m2/s",
        },
        (
            "Every point is a caller-declared steady gas/liquid state and uses the existing two-film point evaluator independently.",
            "Knot times are strictly increasing and exactly match each nested request; caller order is preserved and the first non-computed point stops evaluation.",
            "No inter-knot interpolation, transient accumulation, equilibrium propagation, corrosion response or qualification is inferred.",
        ),
        (SOURCE_ID,),
        qualification="user_model",
        context_validator=_validate_context,
    )]
