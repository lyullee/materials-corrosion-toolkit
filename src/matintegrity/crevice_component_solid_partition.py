"""Component-basis equilibrium partition between a crevice liquid and finite solids."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Positive, canonical_digest
from .crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from .crevice_component_state_bdf import CellAqueousEquilibriumTemplate
from .models.aqueous_activity_iteration import aqueous_davies_self_consistent_speciation
from .registry import ModelSpec

MODEL_ID = "chemistry.crevice_component_solid_partition"
SOURCE_ID = "caller_component_total_basis_competing_solid_equilibrium_partition"


class ComponentTotalInventory(Contract):
    component_id: str = Field(min_length=1)
    total_moles: float = Field(ge=0.0)


class CreviceComponentSolidPartitionRequest(Contract):
    """Solve one-cell instantaneous partition; total inventory includes solids."""

    schema_version: Literal["matintegrity.crevice_component_solid_partition.v1"] = (
        "matintegrity.crevice_component_solid_partition.v1"
    )
    assessment_id: str = Field(min_length=1)
    cell: CellAqueousEquilibriumTemplate
    activity_standard_state_id: Literal["dimensionless_molarity_1_mol_L"] = "dimensionless_molarity_1_mol_L"
    total_component_inventory: tuple[ComponentTotalInventory, ...] = Field(min_length=1, max_length=100)
    phase_candidates: tuple[CreviceCompetingSolidPhase, ...] = Field(min_length=1, max_length=12)
    log_saturation_tolerance: Positive = Field(default=1e-8, le=1e-3)
    relative_partition_tolerance: Positive = Field(default=1e-9, le=1e-3)
    maximum_active_set_sweeps: StrictInt = Field(default=100, ge=1, le=1000)
    maximum_total_aqueous_equilibrium_calls: StrictInt = Field(default=20_000, ge=1, le=2_000_000)
    maximum_total_nested_equilibrium_iteration_work: StrictInt = Field(default=20_000_000, ge=1, le=2_000_000_000)
    maximum_bisection_iterations_per_phase_update: StrictInt = Field(default=100, ge=8, le=500)
    maximum_total_bisection_iterations: StrictInt = Field(default=100_000, ge=1, le=20_000_000)
    total_inventory_includes_all_candidate_solids_reviewed: bool
    candidate_phase_set_complete_for_declared_scope_reviewed: bool
    equilibrium_constants_and_activity_basis_applicable_reviewed: bool
    instantaneous_equilibrium_and_no_nucleation_barrier_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_partition_contract(self):
        if not all((
            self.total_inventory_includes_all_candidate_solids_reviewed,
            self.candidate_phase_set_complete_for_declared_scope_reviewed,
            self.equilibrium_constants_and_activity_basis_applicable_reviewed,
            self.instantaneous_equilibrium_and_no_nucleation_barrier_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("total inventory, phase-set, equilibrium applicability and use reviews are required")
        components = {row.component_id for row in self.cell.conserved_components}
        supplied = [row.component_id for row in self.total_component_inventory]
        if len(set(supplied)) != len(supplied) or set(supplied) != components:
            raise ValueError("total component inventory must cover each cell component exactly once")
        if any(not math.isfinite(row.total_moles) or row.total_moles <= 0.0
               for row in self.total_component_inventory):
            raise ValueError("each total component inventory must be finite and positive")
        phase_ids = [row.solid_species_id for row in self.phase_candidates]
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("solid phase candidate IDs must be unique")
        if any(row.initial_solid_moles_per_solution_volume_mol_m3 != 0.0 for row in self.phase_candidates):
            raise ValueError("candidate phase records must have zero seed inventory; total-basis solid amounts are solved")
        if self.cell.aqueous_activity_request.system.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("solid activity products require the aqueous 1 mol/L standard state")
        return self


def _component_consumption(request: CreviceComponentSolidPartitionRequest):
    system = request.cell.aqueous_activity_request.system
    species = {row.species_id: row for row in system.species}
    maps = {component.component_id: {term.species_id: term.coefficient
                                     for term in component.species_coefficients}
            for component in request.cell.conserved_components}
    result = {}
    for phase in request.phase_candidates:
        if not set(phase.aqueous_reactant_stoichiometry) <= set(species):
            raise ValueError(f"phase {phase.solid_species_id} references undeclared aqueous species")
        if any(row.elemental_composition is None for row in system.species):
            raise ValueError("phase element closure requires formulas for every aqueous species")
        charge = math.fsum(species[sid].charge_number * coefficient
                           for sid, coefficient in phase.aqueous_reactant_stoichiometry.items())
        if not math.isclose(charge, 0.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"phase {phase.solid_species_id} does not conserve charge")
        elements = set(phase.solid_elemental_composition)
        for sid in phase.aqueous_reactant_stoichiometry:
            elements.update(species[sid].elemental_composition or {})
        for element in elements:
            aqueous_count = math.fsum((species[sid].elemental_composition or {}).get(element, 0) * coefficient
                                      for sid, coefficient in phase.aqueous_reactant_stoichiometry.items())
            if not math.isclose(aqueous_count, phase.solid_elemental_composition.get(element, 0),
                                rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"phase {phase.solid_species_id} does not conserve element {element}")
        consumed = {cid: math.fsum(mapping.get(sid, 0.0) * coefficient
                                   for sid, coefficient in phase.aqueous_reactant_stoichiometry.items())
                    for cid, mapping in maps.items()}
        if any(value < -1e-12 for value in consumed.values()) or not any(value > 0.0 for value in consumed.values()):
            raise ValueError(f"phase {phase.solid_species_id} has an invalid declared component stoichiometry")
        result[phase.solid_species_id] = {cid: max(0.0, value) for cid, value in consumed.items()}
    return result


def _aqueous_stage(request, totals_mol_L):
    template = request.cell
    system = template.aqueous_activity_request.system
    target = {assignment.constraint_id: totals_mol_L[assignment.component_id]
              for assignment in template.constraint_roles if assignment.role == "conserved_component"}
    stage_system = system.model_copy(update={
        "constraints": tuple(
            row.model_copy(update={"target_mol_L": target[row.constraint_id]})
            if row.constraint_id in target else row
            for row in system.constraints
        )
    })
    stage_request = template.aqueous_activity_request.model_copy(update={"system": stage_system})
    result = aqueous_davies_self_consistent_speciation(stage_request)
    if result.status != "computed":
        raise ArithmeticError(f"aqueous Davies/mass-action solve failed: {result.values.get('out_of_scope_reason', result.status)}")
    rows = result.values.get("species")
    expected = tuple(row.species_id for row in system.species)
    if not isinstance(rows, (list, tuple)) or tuple(row.get("species_id") for row in rows) != expected:
        raise ArithmeticError("aqueous solver species output does not match the declared species order")
    state = {}
    for row in rows:
        concentration, gamma = float(row["concentration_mol_L"]), float(row["activity_coefficient"])
        if not math.isfinite(concentration) or concentration < 0.0 or not math.isfinite(gamma) or gamma <= 0.0:
            raise ArithmeticError("aqueous stage returned nonfinite or negative species state")
        state[row["species_id"]] = (concentration, gamma)
    return result, state


def _log_q(phase, aqueous_state):
    values = []
    for sid, coefficient in phase.aqueous_reactant_stoichiometry.items():
        concentration, gamma = aqueous_state[sid]
        if concentration <= 0.0:
            return -math.inf
        # The composed solver declares dimensionless activities on the 1 mol/L basis.
        values.append(coefficient * (math.log(gamma) + math.log(concentration)))
    return math.fsum(values)


def solve_crevice_component_solid_partition(request: CreviceComponentSolidPartitionRequest) -> Calculation:
    """Recompute aqueous equilibrium as finite candidate solids partition a total inventory."""
    digest = canonical_digest(request.model_dump(mode="json"))
    try:
        coefficients = _component_consumption(request)
        total_moles = {row.component_id: float(row.total_moles) for row in request.total_component_inventory}
        volume = float(request.cell.solution_volume_L)
        total_mol_L = {key: value / volume for key, value in total_moles.items()}
        phase_by_id = {row.solid_species_id: row for row in request.phase_candidates}
        solid_mol_L = {key: 0.0 for key in phase_by_id}
        calls = 0
        bisection_work = 0
        nested_work = 0

        def fluid_totals():
            values = dict(total_mol_L)
            for pid, amount in solid_mol_L.items():
                for cid, consumed in coefficients[pid].items():
                    values[cid] -= consumed * amount
            if any(not math.isfinite(value) or value <= 0.0 for value in values.values()):
                raise ArithmeticError("solid partition leaves a nonpositive aqueous component target")
            return values

        def evaluate():
            nonlocal calls, nested_work
            if calls >= request.maximum_total_aqueous_equilibrium_calls:
                raise RuntimeError("aqueous equilibrium call budget exceeded")
            per_call_work = request.cell.aqueous_activity_request.maximum_outer_iterations * (
                request.cell.aqueous_activity_request.system.maximum_iterations + 1
            )
            if nested_work + per_call_work > request.maximum_total_nested_equilibrium_iteration_work:
                raise RuntimeError("nested aqueous iteration work budget exceeded")
            result, state = _aqueous_stage(request, fluid_totals())
            calls += 1
            nested_work += per_call_work
            return result, state

        def residual(phase):
            _, state = evaluate()
            return _log_q(phase, state) - math.log(phase.dimensionless_solubility_product)

        def count_bisection_iteration():
            nonlocal bisection_work
            if bisection_work >= request.maximum_total_bisection_iterations:
                raise RuntimeError("solid partition bisection budget exceeded")
            bisection_work += 1

        converged = False
        sweeps = 0
        for sweeps in range(1, request.maximum_active_set_sweeps + 1):
            before = dict(solid_mol_L)
            for phase in request.phase_candidates:
                pid = phase.solid_species_id
                ratio = residual(phase)
                if ratio > request.log_saturation_tolerance:
                    cap = min(fluid_totals()[cid] / amount for cid, amount in coefficients[pid].items()
                              if amount > 0.0)
                    old = solid_mol_L[pid]
                    # The logarithmic aqueous solver cannot evaluate an exact
                    # zero component target. Bracket from the liquid side of
                    # depletion while retaining the same conserved inventory.
                    upper = math.nextafter(old + cap, old)
                    cap = upper - old
                    if cap <= 0.0:
                        raise ArithmeticError("positive aqueous partition bracket is not representable")
                    solid_mol_L[pid] = upper
                    cap_ratio = residual(phase)
                    solid_mol_L[pid] = old
                    if cap_ratio > 0.0:
                        raise ArithmeticError("phase remains supersaturated when a component is depleted")
                    lo, hi = 0.0, cap
                    for _ in range(request.maximum_bisection_iterations_per_phase_update):
                        count_bisection_iteration()
                        mid = 0.5 * (lo + hi)
                        solid_mol_L[pid] = old + mid
                        if residual(phase) > 0.0:
                            lo = mid
                        else:
                            hi = mid
                        if hi - lo <= request.relative_partition_tolerance * max(cap, 1e-30):
                            break
                    solid_mol_L[pid] = old + 0.5 * (lo + hi)
                elif ratio < -request.log_saturation_tolerance and solid_mol_L[pid] > 0.0:
                    old = solid_mol_L[pid]
                    solid_mol_L[pid] = 0.0
                    depleted_ratio = residual(phase)
                    if depleted_ratio < 0.0:
                        continue
                    solid_mol_L[pid] = old
                    lo, hi = 0.0, old
                    for _ in range(request.maximum_bisection_iterations_per_phase_update):
                        count_bisection_iteration()
                        mid = 0.5 * (lo + hi)
                        solid_mol_L[pid] = mid
                        if residual(phase) > 0.0:
                            lo = mid
                        else:
                            hi = mid
                        if hi - lo <= request.relative_partition_tolerance * max(old, 1e-30):
                            break
                    solid_mol_L[pid] = 0.5 * (lo + hi)
            largest_change = max((abs(solid_mol_L[key] - before[key]) for key in solid_mol_L), default=0.0)
            scale = max(1e-30, *(abs(value) for value in total_mol_L.values()))
            if largest_change <= request.relative_partition_tolerance * scale:
                converged = True
                break
        if not converged:
            raise ArithmeticError("competing-phase active set did not converge within its sweep budget")

        final_liquid_totals = fluid_totals()
        aqueous_result, aqueous_state = evaluate()
        phase_output = []
        max_residual = 0.0
        for phase in request.phase_candidates:
            ratio = _log_q(phase, aqueous_state) - math.log(phase.dimensionless_solubility_product)
            present = solid_mol_L[phase.solid_species_id] > request.relative_partition_tolerance * max(total_mol_L.values())
            violation = abs(ratio) if present else max(0.0, ratio)
            max_residual = max(max_residual, violation)
            phase_output.append({
                "solid_species_id": phase.solid_species_id,
                "solid_mol": solid_mol_L[phase.solid_species_id] * volume,
                "solid_mol_L_solution": solid_mol_L[phase.solid_species_id],
                "log_saturation_ratio": ratio,
                "phase_present": present,
                "equilibrium_constant_record_id": phase.equilibrium_constant_record_id,
                "equilibrium_constant_record_sha256": phase.equilibrium_constant_record_sha256,
                "phase_record_sha256": phase.record_sha256,
            })
        if max_residual > request.log_saturation_tolerance:
            raise ArithmeticError("final active-set complementarity residual exceeds tolerance")
        liquid_moles = {cid: amount * volume for cid, amount in final_liquid_totals.items()}
        solid_moles = {cid: math.fsum(coefficients[pid][cid] * solid_mol_L[pid] * volume
                                      for pid in solid_mol_L)
                       for cid in total_moles}
        closure = {cid: liquid_moles[cid] + solid_moles[cid] - total_moles[cid] for cid in total_moles}
        if any(abs(value) > 1e-10 * max(1.0, total_moles[cid]) for cid, value in closure.items()):
            raise ArithmeticError("liquid plus solid component ledger does not close")
        return Calculation(values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "aqueous_result_sha256": canonical_digest(aqueous_result.model_dump(mode="json")),
            "cell_id": request.cell.cell_id,
            "solution_volume_L": volume,
            "activity_standard_state_id": request.activity_standard_state_id,
            "total_component_inventory_mol": total_moles,
            "aqueous_component_inventory_mol": liquid_moles,
            "solid_component_inventory_mol": solid_moles,
            "component_closure_residual_mol": closure,
            "aqueous_species": aqueous_result.values.get("species", []),
            "solid_phase_results": phase_output,
            "active_set_sweeps": sweeps,
            "aqueous_equilibrium_calls": calls,
            "nested_equilibrium_iteration_work_bound": nested_work,
            "bisection_iterations": bisection_work,
            "maximum_complementarity_residual": max_residual,
            "all_component_ledgers_close": True,
            "active_set_method": "caller_ordered_sequential_coordinate_bracketing",
            "global_gibbs_minimum_claimed": False,
            "committed": True,
            "qualification_claimed": False,
        })
    except (ArithmeticError, FloatingPointError, OverflowError, RuntimeError, ValueError, KeyError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": str(error),
            "aqueous_equilibrium_calls": locals().get("calls", 0),
            "active_set_sweeps": locals().get("sweeps", 0),
            "nested_equilibrium_iteration_work_bound": locals().get("nested_work", 0),
            "bisection_iterations": locals().get("bisection_work", 0),
            "committed": False, "qualification_claimed": False,
        })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceComponentSolidPartitionRequest,
        evaluator=solve_crevice_component_solid_partition,
        units={
            "total_component_inventory[].total_moles": "mol",
            "aqueous_component_inventory_mol.*": "mol",
            "solid_component_inventory_mol.*": "mol",
            "component_closure_residual_mol.*": "mol",
            "solid_phase_results[].solid_mol": "mol",
            "solid_phase_results[].solid_mol_L_solution": "mol/L",
            "solution_volume_L": "L",
            "active_set_sweeps": "1",
            "aqueous_equilibrium_calls": "1",
            "bisection_iterations": "1",
            "nested_equilibrium_iteration_work_bound": "1",
        },
        assumptions=(
            "Total component inventory includes all liquid and candidate solid material; the caller reviews candidate-set completeness and instantaneous equilibrium applicability.",
            "Active solid phases satisfy their caller tabulated saturation product; absent phases are not supersaturated.",
            "Davies/mass-action is recomputed after each bounded phase redistribution and liquid-plus-solid component inventories close before commit.",
            "This is a standalone one-cell equilibrium partition; it is not a BDF-stage hook, kinetic precipitation model or material qualification.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    ),)
