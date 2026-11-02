"""Exact-knot carbonate-composition handoff to transport boundary records."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .carbonate_transport_adapter import CarbonateBoundarySelection, CarbonateTransportBoundary
from .contracts import AssessmentResult, Calculation, Contract, Evidence, RunContext, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_carbonate_transport_boundary_history"
SOURCE_ID = "caller_reviewed_carbonate_transport_boundary_history"
FIXED_CARBONATE_HISTORY_ID = "chemistry.fixed_fugacity_carbonate_history"
HENRY_CARBONATE_HISTORY_ADAPTER_ID = "integration.co2_henry_temperature_to_fixed_fugacity_carbonate_history"
EXPECTED_CONCENTRATION_UNIT = "mol/L"


class CarbonateBoundaryPartitionUse(Contract):
    selection: CarbonateBoundarySelection
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    source_record_id: str = Field(min_length=1)
    evidence: Evidence

    @model_validator(mode="after")
    def provider_and_evidence_match(self):
        if self.provider_id != self.evidence.source_id:
            raise ValueError("partition provider ID must match Evidence source ID")
        if self.selection.partition_provider_sha256 != self.evidence.sha256:
            raise ValueError("partition-provider digest must match its Evidence SHA-256")
        return self


class CarbonateTransportBoundaryHistoryKnot(Contract):
    index: int = Field(ge=0)
    time_s: float = Field(ge=0.0)
    sample_id: str = Field(min_length=1)
    point_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    henry_corrected_record_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    solvent_composition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    partition_provider_id: str = Field(min_length=1)
    partition_provider_revision: str = Field(min_length=1)
    partition_source_record_id: str = Field(min_length=1)
    partition_evidence_sha256: str | None = Field(pattern=r"^[a-f0-9]{64}$")
    boundary: CarbonateTransportBoundary


class WetCo2CarbonateTransportBoundaryHistoryRequest(Contract):
    source_history_result: AssessmentResult
    source_history_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary_partitions: tuple[CarbonateBoundaryPartitionUse, ...] = Field(min_length=1, max_length=20000)
    history_clock_and_boundary_selection_reviewed: bool
    maximum_point_mappings: int = Field(default=20000, ge=1, le=20000)

    @model_validator(mode="after")
    def require_complete_supported_history(self):
        result = self.source_history_result
        if result.model_id not in {FIXED_CARBONATE_HISTORY_ID, HENRY_CARBONATE_HISTORY_ADAPTER_ID}:
            raise ValueError("source must be one of the explicitly supported carbonate-history APIs")
        if result.status != "computed" or result.values.get("all_points_computed") is not True:
            raise ValueError("only a complete computed carbonate history can be mapped")
        if canonical_digest(result.model_dump(mode="json")) != self.source_history_result_sha256:
            raise ValueError("source history AssessmentResult digest differs")
        expected_input_digest = canonical_digest(
            {
                "model_id": result.model_id,
                "model_version": result.model_version,
                "inputs": result.inputs,
                "context": result.context.model_dump(mode="json"),
            }
        )
        if result.input_digest != expected_input_digest:
            raise ValueError("source history AssessmentResult input digest does not match its inputs and context")
        if (result.values.get("asset_id"), result.values.get("location_id"), result.values.get("time_basis")) != (
            result.context.asset_id,
            result.context.location_id,
            result.context.time_basis,
        ):
            raise ValueError("source history values and AssessmentResult context have different physical/time scopes")
        rows = result.values.get("sample_results")
        times = result.values.get("time_s")
        if not isinstance(rows, list) or not isinstance(times, list) or len(rows) != len(times):
            raise ValueError("source history must expose aligned exact-knot times and sample results")
        if len(rows) != len(self.boundary_partitions):
            raise ValueError("exactly one caller-reviewed boundary partition is required per source knot")
        if any(right <= left for left, right in zip(times[:-1], times[1:], strict=True)):
            raise ValueError("source history times must be strictly increasing")
        if len({item.selection.boundary_id for item in self.boundary_partitions}) != len(rows):
            raise ValueError("boundary IDs must be unique across the mapped history")
        for row, time_s, selection in zip(rows, times, self.boundary_partitions, strict=True):
            if row.get("status") != "computed" or row.get("time_s") != time_s:
                raise ValueError("every source history point must be computed at its exact ordered time")
            if not selection.selection.co2star_partition_and_water_basis_reviewed:
                raise ValueError("every knot's CO2-star partition and water basis must be reviewed")
        return self


def carbonate_transport_boundary_history(
    request: WetCo2CarbonateTransportBoundaryHistoryRequest,
) -> Calculation:
    """Map a complete carbonate AssessmentResult to exact-knot transport boundaries."""
    result = request.source_history_result
    values = result.values
    source_result_digest = request.source_history_result_sha256
    rows = values["sample_results"]
    times = values["time_s"]
    base = {
        "model_id": MODEL_ID,
        "source_history_model_id": result.model_id,
        "source_history_result_sha256": source_result_digest,
        "history_point_count": len(rows),
        "time_s": times,
        "mapping_complete": False,
        "interpolation_performed": False,
        "full_aqueous_composition_inferred": False,
        "charge_balance_inferred": False,
    }
    if len(rows) > request.maximum_point_mappings:
        return Calculation(
            status="out_of_scope",
            values=base | {
                "reason": "point_mapping_budget_exceeded",
                "maximum_point_mappings": request.maximum_point_mappings,
            },
        )
    if not request.history_clock_and_boundary_selection_reviewed:
        return Calculation(
            status="needs_data",
            values=base | {"missing_reviews": ["history_clock_and_boundary_selection_reviewed"]},
        )

    output_rows = []
    for index, (point, time_s, partition_use) in enumerate(
        zip(rows, times, request.boundary_partitions, strict=True)
    ):
        point_values = point.get("values")
        selection = partition_use.selection
        if not isinstance(point_values, dict):
            return Calculation(status="needs_data", values=base | {
                "completed_point_count": len(output_rows),
                "completed_prefix": output_rows,
                "failed_point_index": index,
                "failure_reason": "source_point_values_missing",
            })
        required = (
            "temperature_K",
            "sample_solvent_composition_sha256",
            "co2star_mol_L",
            "h_mol_L",
            "hco3_mol_L",
            "co3_mol_L",
            "oh_mol_L",
        )
        if any(key not in point_values for key in required):
            return Calculation(status="needs_data", values=base | {
                "completed_point_count": len(output_rows),
                "completed_prefix": output_rows,
                "failed_point_index": index,
                "failure_reason": "source_point_missing_required_carbonate_species_or_lineage",
            })
        concentration_fields = (
            point_values["co2star_mol_L"],
            point_values["h_mol_L"],
            point_values["hco3_mol_L"],
            point_values["co3_mol_L"],
            point_values["oh_mol_L"],
        )
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0.0
            for value in concentration_fields
        ):
            return Calculation(status="out_of_scope", values=base | {
                "completed_point_count": len(output_rows),
                "completed_prefix": output_rows,
                "failed_point_index": index,
                "failure_reason": "source_carbonate_concentration_invalid",
            })
        temperature_K = point_values["temperature_K"]
        solvent_digest = point_values["sample_solvent_composition_sha256"]
        if (
            not isinstance(temperature_K, (int, float))
            or isinstance(temperature_K, bool)
            or not math.isfinite(temperature_K)
            or temperature_K <= 0.0
            or not isinstance(solvent_digest, str)
            or len(solvent_digest) != 64
            or any(character not in "0123456789abcdef" for character in solvent_digest)
        ):
            return Calculation(status="needs_data", values=base | {
                "completed_point_count": len(output_rows),
                "completed_prefix": output_rows,
                "failed_point_index": index,
                "failure_reason": "source_temperature_or_solvent_digest_invalid",
            })
        if point_values.get("henry_coefficient_mol_L_Pa") is None:
            return Calculation(status="needs_data", values=base | {
                "completed_point_count": len(output_rows),
                "completed_prefix": output_rows,
                "failed_point_index": index,
                "failure_reason": "henry_coefficient_missing",
            })
        if result.units.get("co2star_mol_L_history[]") != EXPECTED_CONCENTRATION_UNIT:
            return Calculation(status="needs_data", values=base | {
                "completed_point_count": len(output_rows),
                "completed_prefix": output_rows,
                "failed_point_index": index,
                "failure_reason": "history_species_unit_contract_mismatch",
            })
        fraction = selection.hydrated_carbonic_fraction_of_co2star
        co2star_mol_m3 = point_values["co2star_mol_L"] * 1000.0
        species_ids = ("CO2_aq", "H2O", "H2CO3", "H_plus", "HCO3_minus", "CO3_2minus", "OH_minus")
        concentrations = (
            co2star_mol_m3 * (1.0 - fraction),
            selection.water_concentration_mol_m3,
            co2star_mol_m3 * fraction,
            point_values["h_mol_L"] * 1000.0,
            point_values["hco3_mol_L"] * 1000.0,
            point_values["co3_mol_L"] * 1000.0,
            point_values["oh_mol_L"] * 1000.0,
        )
        if any(not math.isfinite(value) or value < 0.0 for value in concentrations):
            return Calculation(status="out_of_scope", values=base | {
                "completed_point_count": len(output_rows),
                "completed_prefix": output_rows,
                "failed_point_index": index,
                "failure_reason": "mol_L_to_mol_m3_mapping_invalid",
            })
        point_digest = canonical_digest(point)
        boundary = CarbonateTransportBoundary(
            boundary_id=selection.boundary_id,
            equilibrium_result_sha256=source_result_digest,
            selection_sha256=canonical_digest(selection.model_dump(mode="json")),
            species_ids=species_ids,
            concentration_mol_m3=concentrations,
            temperature_K=temperature_K,
            solvent_composition_sha256=solvent_digest,
            interpretation=(
                "Exact-knot carbonate-only concentrations; CO2* hydration split and water concentration are caller reviewed. "
                "Other ions and complete-solution electroneutrality are unresolved."
            ),
        )
        output_rows.append(
            CarbonateTransportBoundaryHistoryKnot(
                index=index,
                time_s=time_s,
                sample_id=point.get("sample_id", "unknown"),
                point_result_sha256=point_digest,
                henry_corrected_record_sha256=point_values.get("henry_corrected_record_sha256")
                or point_values.get("henry_record_digest"),
                solvent_composition_sha256=solvent_digest,
                partition_provider_id=partition_use.provider_id,
                partition_provider_revision=partition_use.provider_revision,
                partition_source_record_id=partition_use.source_record_id,
                partition_evidence_sha256=partition_use.evidence.sha256,
                boundary=boundary,
            ).model_dump(mode="json")
        )
    return Calculation(
        values=base | {
            "mapping_complete": True,
            "boundary_history": output_rows,
            "boundary_ids": [row["boundary"]["boundary_id"] for row in output_rows],
            "temperature_K_history": [row["boundary"]["temperature_K"] for row in output_rows],
            "concentration_mol_m3_history": [
                row["boundary"]["concentration_mol_m3"] for row in output_rows
            ],
            "solvent_composition_sha256_history": [row["solvent_composition_sha256"] for row in output_rows],
            "henry_corrected_record_sha256_history": [row["henry_corrected_record_sha256"] for row in output_rows],
            "concentration_unit": "mol/m3",
            "partition_applied_at_each_exact_knot": True,
        },
        notes=(
            "Each boundary is mapped from one exact computed carbonate-history point and a matching reviewed partition Evidence record.",
            "The CO2* concentration is split into unhydrated CO2 and H2CO3 using the caller fraction; no partition coefficient is inferred.",
            "This is a carbonate boundary transfer, not full aqueous composition, charge balance, reaction-network or transport solution.",
            "No inter-knot concentration, temperature or solvent interpolation is performed.",
        ),
    )


def _validate_context(request: WetCo2CarbonateTransportBoundaryHistoryRequest, context: RunContext) -> None:
    source_context = request.source_history_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source_context.asset_id,
        source_context.location_id,
        source_context.time_basis,
    ):
        raise ValueError("adapter RunContext must match the exact source-history asset, location and time basis")


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            WetCo2CarbonateTransportBoundaryHistoryRequest,
            carbonate_transport_boundary_history,
            {
                "time_s": "s",
                "temperature_K_history": "K",
                "concentration_mol_m3_history": "mol/m3",
                "history_point_count": "count",
            },
            (
                "The input must be a complete computed fixed-fugacity carbonate history or digest-bound Henry-carbonate adapter history.",
                "Every knot needs a source-pinned partition provider and Evidence; the exact point digest, solvent composition digest, temperature and corrected Henry record lineage are retained.",
                "Only the seven explicit carbonate/water boundary species are returned in mol/m3; unresolved ions, charge balance and full aqueous composition are not inferred.",
                "A complete history is mapped only when all exact knots pass; no interpolation or extrapolation is performed.",
            ),
            (SOURCE_ID, "caller_reviewed_co2star_partition_and_water_concentration"),
            qualification="user_model",
            context_validator=_validate_context,
        )
    ]
