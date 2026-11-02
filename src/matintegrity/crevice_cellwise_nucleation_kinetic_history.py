"""Fixed-volume cellwise adapter for exact seed-event kinetic ledgers.

This module evaluates independent, digest-bound closed-batch ledgers per cell.
It does not couple those ledgers to transport, inter-cell flux, or geometry change.
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_nucleation_kinetic_history import (
    CreviceNucleationKineticHistoryRequest,
    solve_crevice_nucleation_kinetic_history,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_cellwise_nucleation_kinetic_history"
SOURCE_ID = "caller_fixed_volume_cellwise_seed_threshold_kinetic_ledgers"
MAX_CELL_TIME_PHASE_RECORDS = 2_000_000


def cell_order_digest_payload(assessment_id: str, physical_scope_id: str, clock_id: str,
                              cells: tuple["FixedKineticCell", ...]) -> dict[str, Any]:
    """Return the canonical mapping payload to pin before building the request."""
    return {
        "assessment_id": assessment_id,
        "physical_scope_id": physical_scope_id,
        "clock_id": clock_id,
        "cells": [
            {
                "cell_id": cell.cell_id,
                "geometry_sha256": cell.geometry_sha256,
                "kinetic_request_sha256": canonical_digest(cell.kinetic_history.model_dump(mode="json")),
            }
            for cell in cells
        ],
    }


def compute_cell_order_sha256(assessment_id: str, physical_scope_id: str, clock_id: str,
                              cells: tuple["FixedKineticCell", ...]) -> str:
    """Compute the canonical digest required by the outer cell-order contract."""
    return canonical_digest(cell_order_digest_payload(assessment_id, physical_scope_id, clock_id, cells))


class FixedKineticCell(Contract):
    """One fixed liquid cell and its independently evidenced batch request."""

    cell_id: str = Field(min_length=1)
    cell_length_m: Positive
    cross_section_area_m2: Positive
    solution_volume_m3: Positive
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    kinetic_history: CreviceNucleationKineticHistoryRequest

    @model_validator(mode="after")
    def verify_geometry_record(self):
        expected_volume = float(self.cell_length_m) * float(self.cross_section_area_m2)
        if not math.isclose(float(self.solution_volume_m3), expected_volume, rel_tol=1e-10, abs_tol=1e-18):
            raise ValueError("fixed cell solution volume must equal cell length times cross-sectional area")
        payload = {
            "cell_id": self.cell_id,
            "cell_length_m": float(self.cell_length_m),
            "cross_section_area_m2": float(self.cross_section_area_m2),
            "solution_volume_m3": float(self.solution_volume_m3),
        }
        if canonical_digest(payload) != self.geometry_sha256 or not any(
            row.sha256 == self.geometry_sha256 for row in self.geometry_evidence
        ):
            raise ValueError("cell geometry Evidence must pin the exact fixed cell record")
        return self


class CreviceCellwiseNucleationKineticHistoryRequest(Contract):
    """Run independent threshold-split kinetics in an ordered fixed-volume mesh."""

    schema_version: Literal["matintegrity.crevice_cellwise_nucleation_kinetic_history.v1"] = (
        "matintegrity.crevice_cellwise_nucleation_kinetic_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    cells: tuple[FixedKineticCell, ...] = Field(min_length=2, max_length=300)
    cell_order_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cell_order_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    maximum_total_cell_time_phase_records: int = Field(default=2_000_000, ge=1, le=20_000_000)
    maximum_total_ledger_evaluations: int = Field(default=1_000_000, ge=1, le=20_000_000)
    independent_cell_batch_scope_reviewed: bool
    no_intercell_transfer_during_kinetic_substep_reviewed: bool
    fixed_cell_solution_volume_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def aligned_cell_histories(self):
        cell_ids = tuple(cell.cell_id for cell in self.cells)
        if len(set(cell_ids)) != len(cell_ids):
            raise ValueError("cell IDs must be unique and ordered")
        if compute_cell_order_sha256(self.assessment_id, self.physical_scope_id,
                                     self.clock_id, self.cells) != self.cell_order_sha256 or not any(
            row.sha256 == self.cell_order_sha256 for row in self.cell_order_evidence
        ):
            raise ValueError("cell-order Evidence must pin ordered cell geometry and kinetic requests")

        reference = self.cells[0].kinetic_history
        reference_species = tuple(reference.aqueous_species)
        reference_phases = tuple(reference.candidate_solid_phases)
        reference_nucleation = tuple(reference.nucleation_laws)
        reference_growth = tuple(reference.growth_laws)
        reference_intervals = tuple(reference.intervals)
        reference_provider = (reference.provider_id, reference.provider_revision,
                              reference.kinetic_configuration_sha256,
                              reference.kinetic_parameter_source_sha256)
        record_count = 0
        ledger_evaluation_budget = 0
        for cell in self.cells:
            request = cell.kinetic_history
            if request.physical_scope_id != self.physical_scope_id or request.clock_id != self.clock_id:
                raise ValueError("cell kinetic scope and clock must match the spatial request")
            if request.temperature_K != reference.temperature_K:
                raise ValueError("all cells must share one reviewed isothermal kinetic temperature")
            if (request.provider_id, request.provider_revision,
                request.kinetic_configuration_sha256, request.kinetic_parameter_source_sha256) != reference_provider:
                raise ValueError("cell provider and kinetic configuration/parameter digests must match")
            if tuple(row.model_dump(mode="json", exclude={"initial_concentration_mol_m3"})
                     for row in request.aqueous_species) != tuple(
                         row.model_dump(mode="json", exclude={"initial_concentration_mol_m3"})
                         for row in reference_species
                     ):
                raise ValueError("cell aqueous species identity, charge, composition and source digest must match")
            if tuple(row.model_dump(mode="json", exclude={"initial_solid_moles_per_solution_volume_mol_m3"})
                     for row in request.candidate_solid_phases) != tuple(
                         row.model_dump(mode="json", exclude={"initial_solid_moles_per_solution_volume_mol_m3"})
                         for row in reference_phases
                     ):
                raise ValueError("cell phase reaction order and source records must match")
            if tuple(row.model_dump(mode="json") for row in request.nucleation_laws) != tuple(
                row.model_dump(mode="json") for row in reference_nucleation
            ) or tuple(row.model_dump(mode="json") for row in request.growth_laws) != tuple(
                row.model_dump(mode="json") for row in reference_growth
            ):
                raise ValueError("all cells must use identical digest-bound nucleation and seeded-growth laws")
            if len(request.intervals) != len(reference_intervals) or any(
                (left.start_time_s, left.end_time_s) != (right.start_time_s, right.end_time_s)
                for left, right in zip(request.intervals, reference_intervals, strict=True)
            ):
                raise ValueError("cell saturation histories must share the same exact interval clock")
            record_count += len(request.intervals) * len(request.candidate_solid_phases)
            ledger_evaluation_budget += request.maximum_total_ledger_evaluations

        if record_count > self.maximum_total_cell_time_phase_records:
            raise ValueError("cell × interval × phase records exceed the declared work budget")
        if ledger_evaluation_budget > self.maximum_total_ledger_evaluations:
            raise ValueError("sum of per-cell ledger evaluation budgets exceeds the spatial budget")
        if not all((self.independent_cell_batch_scope_reviewed,
                    self.no_intercell_transfer_during_kinetic_substep_reviewed,
                    self.fixed_cell_solution_volume_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("fixed geometry, isolated-cell splitting and use reviews are required")
        return self


def _cell_amount_history(result: dict[str, Any], volume_m3: float):
    history = result["history"]
    aqueous_ids = tuple(history[0]["aqueous_concentration_mol_m3"])
    phase_ids = tuple(history[0]["solid_inventory_mol_m3"])
    times = [float(row["time_s"]) for row in history]
    aqueous = {
        species_id: [float(row["aqueous_concentration_mol_m3"][species_id]) * volume_m3 for row in history]
        for species_id in aqueous_ids
    }
    solids = {
        phase_id: [float(row["solid_inventory_mol_m3"][phase_id]) * volume_m3 for row in history]
        for phase_id in phase_ids
    }
    return times, aqueous, solids


def evaluate_crevice_cellwise_nucleation_kinetic_history(
    request: CreviceCellwiseNucleationKineticHistoryRequest,
) -> Calculation:
    """Evaluate each fixed cell ledger and aggregate inventories as amounts."""
    digest = canonical_digest(request.model_dump(mode="json"))
    outputs: list[dict[str, Any]] = []
    aggregate_aqueous: dict[str, list[float]] = {}
    aggregate_solids: dict[str, list[float]] = {}
    common_times: list[float] | None = None
    total_ledger_evaluations = 0
    total_seed_events = 0
    maximum_element_residual_mol = 0.0
    maximum_charge_residual_mol_eq = 0.0

    for cell in request.cells:
        result = solve_crevice_nucleation_kinetic_history(cell.kinetic_history)
        values = result.values
        if result.status != "computed" or not values.get("all_intervals_committed", False):
            completed_ledger_evaluations = sum(
                int(row["kinetic_result"]["values"].get("ledger_evaluation_count", 0))
                for row in outputs
            )
            completed_seed_events = sum(
                int(row["kinetic_result"]["values"].get("seed_threshold_split_count", 0))
                for row in outputs
            )
            return Calculation(status=result.status, values={
                "model_id": MODEL_ID,
                "assessment_id": request.assessment_id,
                "input_sha256": digest,
                "failed_cell_id": cell.cell_id,
                "cell_result": result.model_dump(mode="json"),
                "completed_cell_ids": [row["cell_id"] for row in outputs],
                "ledger_evaluation_count": completed_ledger_evaluations + int(
                    values.get("ledger_evaluation_count", 0)
                ),
                "seed_threshold_split_count": completed_seed_events + int(
                    values.get("seed_threshold_split_count", 0)
                ),
                "committed": False,
                "qualification_claimed": False,
            })
        times, aqueous, solids = _cell_amount_history(values, float(cell.solution_volume_m3))
        if common_times is None:
            common_times = times
            aggregate_aqueous = {key: [0.0] * len(times) for key in aqueous}
            aggregate_solids = {key: [0.0] * len(times) for key in solids}
        elif times != common_times or set(aqueous) != set(aggregate_aqueous) or set(solids) != set(aggregate_solids):
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest, "failed_cell_id": cell.cell_id,
                "reason": "cell result time/species/phase alignment changed after contract validation",
                "committed": False, "qualification_claimed": False,
            })
        for key, values_by_time in aqueous.items():
            aggregate_aqueous[key] = [a + b for a, b in zip(aggregate_aqueous[key], values_by_time, strict=True)]
        for key, values_by_time in solids.items():
            aggregate_solids[key] = [a + b for a, b in zip(aggregate_solids[key], values_by_time, strict=True)]
        total_ledger_evaluations += int(values.get("ledger_evaluation_count", 0))
        total_seed_events += int(values.get("seed_threshold_split_count", 0))
        maximum_element_residual_mol = max(
            maximum_element_residual_mol,
            float(values.get("maximum_element_balance_residual_mol_m3", 0.0)) * float(cell.solution_volume_m3),
        )
        maximum_charge_residual_mol_eq = max(
            maximum_charge_residual_mol_eq,
            float(values.get("maximum_charge_balance_residual_mol_charge_m3", 0.0)) * float(cell.solution_volume_m3),
        )
        outputs.append({
            "cell_id": cell.cell_id,
            "geometry_sha256": cell.geometry_sha256,
            "solution_volume_m3": float(cell.solution_volume_m3),
            "kinetic_request_sha256": canonical_digest(cell.kinetic_history.model_dump(mode="json")),
            "kinetic_result_sha256": canonical_digest(result.model_dump(mode="json")),
            "kinetic_result": result.model_dump(mode="json"),
            "aqueous_moles_by_species_and_time": aqueous,
            "solid_moles_by_phase_and_time": solids,
        })

    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "input_sha256": digest,
        "cell_order_sha256": request.cell_order_sha256,
        "time_s": common_times or [],
        "cell_results": outputs,
        "total_aqueous_moles_by_species_and_time": aggregate_aqueous,
        "total_solid_moles_by_phase_and_time": aggregate_solids,
        "ledger_evaluation_count": total_ledger_evaluations,
        "seed_threshold_split_count": total_seed_events,
        "maximum_cell_element_closure_residual_mol": maximum_element_residual_mol,
        "maximum_cell_charge_closure_residual_mol_eq": maximum_charge_residual_mol_eq,
        "cell_results_committed": True,
        "committed": True,
        "qualification_claimed": False,
        "operator_split_basis": "Independent fixed-volume cell ledgers run from each cell's caller-provided exact interval saturation records. The results contain no transport flux and must be consumed as a separate local kinetic stage by a caller-owned transport workflow.",
        "limitations": [
            "Cells do not exchange species or component flux during kinetic substeps; aggregate totals are reporting sums, not a spatial transport balance.",
            "Each cell's exact seed-event split uses constant caller saturation and a constant pre-seed molar source, verified by the conservative ledger.",
            "Cell geometry and solution volume are fixed over the complete history; no aperture, area, porosity or morphology feedback is inferred.",
            "No automatic phase discovery, electrochemical coupling, wall kinetics, corrosion rate, life, risk or material qualification is inferred.",
        ],
    }, notes=(
        "All cell calculations must commit for the spatial result to commit.",
        "Run cellwise kinetic ledgers as a separate operator-split stage; this API is not a transport solver.",
    ))


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCellwiseNucleationKineticHistoryRequest,
        evaluator=evaluate_crevice_cellwise_nucleation_kinetic_history,
        units={
            "cells[].solution_volume_m3": "m^3",
            "cells[].kinetic_history.aqueous_species[].initial_concentration_mol_m3": "mol/m^3",
            "cells[].kinetic_history.candidate_solid_phases[].initial_solid_moles_per_solution_volume_mol_m3": "mol/m^3",
            "cell_results[].aqueous_moles_by_species_and_time.*[]": "mol",
            "cell_results[].solid_moles_by_phase_and_time.*[]": "mol",
            "total_aqueous_moles_by_species_and_time.*[]": "mol",
            "total_solid_moles_by_phase_and_time.*[]": "mol",
            "maximum_cell_element_closure_residual_mol": "mol",
            "maximum_cell_charge_closure_residual_mol_eq": "mol_eq",
        },
        assumptions=(
            "Cell rows are independent closed-batch kinetic ledgers with identical ordered species/phase laws and exact common output times.",
            "Concentrations and solid inventories are converted to amounts using Evidence-pinned, fixed cell solution volumes.",
            "Each underlying batch history performs its own analytic seed-threshold split and conservative ledger verification.",
            "No inter-cell transport or geometry change occurs inside this adapter; callers must explicitly operator-split it with a separate transport calculation.",
        ),
        source_ids=(SOURCE_ID, "digest_bound_saturation_nucleation_and_growth_kinetic_history",
                    "caller_rate_competitive_solid_mass_balance_ledger"),
        version="0.1.0",
        qualification="user_model",
    ),)
