"""Iterate caller-defined crevice aqueous activity/speciation with finite solid transfer."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_competing_solid_equilibrium import (
    CreviceCompetingSolidEquilibriumRequest,
    evaluate_crevice_competing_solid_equilibrium,
)
from .models.aqueous_activity_iteration import (
    AqueousDaviesIteration,
    aqueous_davies_self_consistent_speciation,
)
from .registry import ModelSpec

MODEL_ID = "chemistry.crevice_spatial_activity_solid_fixed_point"
SPECIES_SOURCE_ID = "caller_cell_aqueous_mass_action_and_solids"
ITERATION_SOURCE_ID = "aqueous_solid_inventory_feedback_fixed_point"


class CreviceCellActivitySolidInput(Contract):
    cell_id: str = Field(min_length=1)
    aqueous_activity_input: AqueousDaviesIteration
    solid_equilibrium_template: CreviceCompetingSolidEquilibriumRequest

    @model_validator(mode="after")
    def coherent_cell_chemistry(self):
        aqueous_ids = tuple(row.species_id for row in self.aqueous_activity_input.system.species)
        solid_ids = tuple(row.species_id for row in self.solid_equilibrium_template.aqueous_species)
        if set(aqueous_ids) != set(solid_ids) or len(aqueous_ids) != len(solid_ids):
            raise ValueError("aqueous and solid-equilibrium templates must declare exactly the same cell species")
        if self.aqueous_activity_input.system.temperature_K != self.solid_equilibrium_template.temperature_K:
            raise ValueError("activity/speciation and solid equilibrium temperatures must match exactly")
        if self.aqueous_activity_input.system.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("this coupling currently supports only the 1 mol/L activity standard state")
        aq_by_id = {row.species_id: row for row in self.aqueous_activity_input.system.species}
        solid_by_id = {row.species_id: row for row in self.solid_equilibrium_template.aqueous_species}
        for species_id in aqueous_ids:
            aq, solid = aq_by_id[species_id], solid_by_id[species_id]
            if aq.charge_number != solid.charge_number or aq.elemental_composition != solid.elemental_composition:
                raise ValueError("species charge and elemental composition must match across the two chemistry contracts")
        return self


class CreviceSpatialActivitySolidFixedPointRequest(Contract):
    schema_version: Literal["matintegrity.crevice_spatial_activity_solid_fixed_point.v1"] = (
        "matintegrity.crevice_spatial_activity_solid_fixed_point.v1"
    )
    assessment_id: str = Field(min_length=1)
    geometry_mode: Literal["fixed_single_knot"]
    geometry_provider_id: str = Field(min_length=1)
    geometry_revision: str = Field(min_length=1)
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cells: tuple[CreviceCellActivitySolidInput, ...] = Field(min_length=1, max_length=500)
    maximum_outer_iterations: int = Field(default=50, ge=1, le=1000)
    maximum_total_cell_iterations: int = Field(default=20_000, ge=1, le=1_000_000)
    concentration_relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    solid_inventory_relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    constraint_relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    complete_cell_mapping_and_species_scope_reviewed: bool
    aqueous_linear_constraints_are_conserved_including_solid_transfer_reviewed: bool
    standard_state_and_equilibrium_records_reviewed: bool
    fixed_geometry_single_knot_scope_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_cells(self):
        ids = [row.cell_id for row in self.cells]
        if len(set(ids)) != len(ids):
            raise ValueError("cell IDs must be unique")
        if not any(row.source_id == self.geometry_provider_id and row.sha256 == self.geometry_sha256
                   for row in self.evidence):
            raise ValueError("geometry provider digest must match a declared Evidence row")
        if any(cell.solid_equilibrium_template.physical_scope_id == "" for cell in self.cells):
            raise ValueError("each cell must declare a physical scope")
        physical_scopes = {cell.solid_equilibrium_template.physical_scope_id for cell in self.cells}
        if len(physical_scopes) != 1:
            raise ValueError("all independent cells in one assessment must share the same physical scope")
        if len(self.cells) * self.maximum_outer_iterations > self.maximum_total_cell_iterations:
            raise ValueError("cell count times outer iteration limit exceeds the declared assessment work budget")
        return self


def _replace_digest_evidence(evidence, old_digest: str, new_digest: str):
    rows = []
    pinned = False
    for row in evidence:
        if row.sha256 == old_digest:
            rows.append(row.model_copy(update={"sha256": new_digest}))
            pinned = True
        else:
            rows.append(row)
    if not pinned:
        raise ValueError("cannot update a chemistry record without an Evidence row pinning its previous digest")
    return tuple(rows)


def _phase_request_with_state(template, concentrations_m3, gammas, solid_inventory):
    species_rows = []
    for row in template.aqueous_species:
        payload = {
            "species_id": row.species_id,
            "initial_concentration_mol_m3": float(concentrations_m3[row.species_id]),
            "activity_reference_concentration_mol_m3": row.activity_reference_concentration_mol_m3,
            "activity_coefficient": float(gammas[row.species_id]),
            "charge_number": row.charge_number,
            "elemental_composition": row.elemental_composition,
        }
        digest = canonical_digest(payload)
        evidence = _replace_digest_evidence(row.evidence, row.record_sha256, digest)
        species_rows.append(row.model_copy(update=payload | {"record_sha256": digest, "evidence": evidence}))
    phase_rows = []
    for row in template.solid_phases:
        payload = {
            "solid_species_id": row.solid_species_id,
            "solid_elemental_composition": row.solid_elemental_composition,
            "aqueous_reactant_stoichiometry": row.aqueous_reactant_stoichiometry,
            "initial_solid_moles_per_solution_volume_mol_m3": float(solid_inventory[row.solid_species_id]),
            "dimensionless_solubility_product": row.dimensionless_solubility_product,
            "equilibrium_constant_record_id": row.equilibrium_constant_record_id,
            "equilibrium_constant_record_sha256": row.equilibrium_constant_record_sha256,
        }
        digest = canonical_digest(payload)
        evidence = _replace_digest_evidence(row.evidence, row.record_sha256, digest)
        phase_rows.append(row.model_copy(update=payload | {"record_sha256": digest, "evidence": evidence}))
    return template.model_copy(update={"aqueous_species": tuple(species_rows), "solid_phases": tuple(phase_rows)})


def _system_with_constraint_targets(system, targets):
    constraints = tuple(
        row.model_copy(update={"target_mol_L": float(targets[row.constraint_id])})
        for row in system.constraints
    )
    return system.model_copy(update={"constraints": constraints})


def solve_crevice_spatial_activity_solid_fixed_point(
    request: CreviceSpatialActivitySolidFixedPointRequest,
) -> Calculation:
    """Solve each exact caller cell independently, feeding finite solid transfer back to aqueous inventory constraints."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "geometry_mode": request.geometry_mode,
        "geometry_provider_id": request.geometry_provider_id,
        "geometry_revision": request.geometry_revision,
        "geometry_sha256": request.geometry_sha256,
        "physical_scope_id": request.cells[0].solid_equilibrium_template.physical_scope_id,
        "cell_count": len(request.cells),
        "maximum_total_cell_iterations": request.maximum_total_cell_iterations,
        "maximum_outer_iterations_per_cell": request.maximum_outer_iterations,
        "evidence_lineage": [row.model_dump(mode="json") for row in request.evidence],
        "species_source_id": SPECIES_SOURCE_ID,
        "iteration_source_id": ITERATION_SOURCE_ID,
        "completed_cell_count": 0,
        "cell_results": [],
        "prefix_policy": "only fully converged cells are accepted; any failed cell withholds the aggregate result",
    }
    review_names = (
        "complete_cell_mapping_and_species_scope_reviewed",
        "aqueous_linear_constraints_are_conserved_including_solid_transfer_reviewed",
        "standard_state_and_equilibrium_records_reviewed",
        "fixed_geometry_single_knot_scope_reviewed",
        "computational_use_authorized",
    )
    missing = [name for name in review_names if not getattr(request, name)]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    accepted = []
    for cell_index, cell in enumerate(request.cells):
        system = cell.aqueous_activity_input.system
        targets = {row.constraint_id: row.target_mol_L for row in system.constraints}
        phase_template = cell.solid_equilibrium_template
        solids = {row.solid_species_id: row.initial_solid_moles_per_solution_volume_mol_m3
                  for row in phase_template.solid_phases}
        previous_state = None
        history = []
        converged = False
        for iteration in range(1, request.maximum_outer_iterations + 1):
            activity_input = cell.aqueous_activity_input.model_copy(update={
                "system": _system_with_constraint_targets(system, targets),
            })
            activity_result = aqueous_davies_self_consistent_speciation(activity_input)
            row_record = {
                "iteration": iteration,
                "aqueous_input_sha256": canonical_digest(activity_input.model_dump(mode="json")),
                "aqueous_result_sha256": canonical_digest(activity_result.model_dump(mode="json")),
                "aqueous_status": activity_result.status,
            }
            if activity_result.status != "computed":
                return Calculation(status=activity_result.status, values=base | {
                    "completed_cell_count": len(accepted), "cell_results": accepted,
                    "failed_cell_id": cell.cell_id, "failed_cell_index": cell_index,
                    "failed_iteration": iteration, "failed_aqueous_result": activity_result.model_dump(mode="json"),
                    "failed_iteration_lineage": history + [row_record],
                })
            species_rows = activity_result.values["species"]
            c_m3 = {row["species_id"]: float(row["concentration_mol_L"]) * 1000.0 for row in species_rows}
            gamma = {row["species_id"]: float(row["activity_coefficient"]) for row in species_rows}
            phase_request = _phase_request_with_state(phase_template, c_m3, gamma, solids)
            phase_result = evaluate_crevice_competing_solid_equilibrium(phase_request)
            row_record.update({
                "solid_input_sha256": canonical_digest(phase_request.model_dump(mode="json")),
                "solid_result_sha256": canonical_digest(phase_result.model_dump(mode="json")),
                "solid_status": phase_result.status,
            })
            if phase_result.status != "computed":
                return Calculation(status=phase_result.status, values=base | {
                    "completed_cell_count": len(accepted), "cell_results": accepted,
                    "failed_cell_id": cell.cell_id, "failed_cell_index": cell_index,
                    "failed_iteration": iteration, "failed_solid_result": phase_result.model_dump(mode="json"),
                    "failed_iteration_lineage": history + [row_record],
                })
            final_aq = {sid: float(v["final_concentration_mol_m3"]) for sid, v in phase_result.values["aqueous_species"].items()}
            phase_rows = {row["solid_species_id"]: row for row in phase_result.values["solid_phases"]}
            next_solids = {sid: float(row["final_solid_moles_per_solution_volume_mol_m3"])
                           for sid, row in phase_rows.items()}
            increments = {sid: final_aq[sid] - c_m3[sid] for sid in c_m3}
            next_targets = dict(targets)
            for constraint in system.constraints:
                transfer_mol_l = math.fsum(term.coefficient * increments[term.species_id] / 1000.0
                                           for term in constraint.terms)
                next_targets[constraint.constraint_id] += transfer_mol_l
            c_change = math.inf
            solid_change = math.inf
            target_change = math.inf
            if previous_state is not None:
                c_scale = max(1e-30, *(abs(v) for v in final_aq.values()))
                s_scale = max(1e-30, *(abs(v) for v in next_solids.values()))
                t_scale = max(1e-30, *(abs(v) for v in next_targets.values()))
                c_change = max(abs(final_aq[k] - previous_state["aqueous"][k]) for k in final_aq) / c_scale
                solid_change = max(abs(next_solids[k] - previous_state["solids"][k]) for k in next_solids) / s_scale
                target_change = max(abs(next_targets[k] - previous_state["targets"][k]) for k in next_targets) / t_scale
            row_record.update({
                "maximum_relative_aqueous_state_change": c_change if math.isfinite(c_change) else None,
                "maximum_relative_solid_inventory_change": solid_change if math.isfinite(solid_change) else None,
                "maximum_relative_constraint_change": target_change if math.isfinite(target_change) else None,
                "aqueous_charge_balance_residual_mol_charge_m3": phase_result.values["aqueous_charge_balance_residual_mol_charge_m3"],
                "phase_complementarity_verified": phase_result.values["phase_complementarity_verified"],
            })
            history.append(row_record)
            if previous_state is not None and c_change <= request.concentration_relative_tolerance \
                    and solid_change <= request.solid_inventory_relative_tolerance \
                    and target_change <= request.constraint_relative_tolerance:
                converged = True
                final_state = {
                    "activity_result": activity_result, "phase_result": phase_result,
                    "aqueous": final_aq, "solids": next_solids, "targets": next_targets,
                }
                break
            previous_state = {"aqueous": final_aq, "solids": next_solids, "targets": next_targets}
            fraction = request.damping_fraction
            targets = {key: targets[key] + fraction * (next_targets[key] - targets[key]) for key in targets}
            solids = {key: solids[key] + fraction * (next_solids[key] - solids[key]) for key in solids}
            phase_template = _phase_request_with_state(
                phase_template,
                {row.species_id: row.initial_concentration_mol_m3 for row in phase_template.aqueous_species},
                {row.species_id: row.activity_coefficient for row in phase_template.aqueous_species},
                solids,
            )
        if not converged:
            return Calculation(status="out_of_scope", values=base | {
                "completed_cell_count": len(accepted), "cell_results": accepted,
                "failed_cell_id": cell.cell_id, "failed_cell_index": cell_index,
                "outer_iteration_count": len(history), "iteration_lineage": history,
                "termination_reason": "caller iteration budget exhausted before all declared residuals converged",
                "committed": False,
            })
        accepted.append({
            "cell_id": cell.cell_id,
            "outer_iteration_count": len(history),
            "iteration_lineage": history,
            "aqueous_activity_result": final_state["activity_result"].model_dump(mode="json"),
            "solid_equilibrium_result": final_state["phase_result"].model_dump(mode="json"),
            "aqueous_species_concentration_mol_m3": final_state["aqueous"],
            "solid_inventory_mol_m3": final_state["solids"],
            "converged": True,
        })
    return Calculation(values=base | {
        "completed_cell_count": len(accepted),
        "cell_results": accepted,
        "all_cells_converged": True,
        "committed": True,
        "coupling_scope": "cellwise Davies activity/speciation fixed point coupled to finite caller-defined solid equilibrium through linear aqueous inventory constraints",
        "geometry_feedback": False,
        "intercell_transport": False,
        "faradaic_source_coupling": False,
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSpatialActivitySolidFixedPointRequest,
        evaluator=solve_crevice_spatial_activity_solid_fixed_point,
        units={
            "cells[].aqueous_activity_input.system.constraints[].target_mol_L": "mol/L",
            "cells[].solid_equilibrium_template.aqueous_species[].initial_concentration_mol_m3": "mol/m^3",
            "cells[].solid_equilibrium_template.solid_phases[].initial_solid_moles_per_solution_volume_mol_m3": "mol/m^3",
            "cells[].solid_equilibrium_template.temperature_K": "K",
            "cell_results[].aqueous_species_concentration_mol_m3.*": "mol/m^3",
            "cell_results[].solid_inventory_mol_m3.*": "mol/m^3",
        },
        assumptions=(
            "Each caller cell is solved independently at one fixed geometry knot using the existing Davies activity/speciation and finite competing-solid equilibrium evaluators.",
            "Solid transfer updates only caller-declared linear aqueous conservation targets; no intercell flux or Faradaic source is introduced.",
            "Convergence requires caller tolerances for aqueous concentration, solid inventory, and constraint target changes.",
            "The finite solid list is caller selected; global Gibbs minimization, automatic species/phase discovery, kinetics, and corrosion qualification are not provided.",
        ),
        source_ids=(SPECIES_SOURCE_ID, ITERATION_SOURCE_ID),
        qualification="user_model",
        runtime_dependency_names=("scipy",),
    ),)
