"""Sequential knot-coupled NP transport and caller-defined aqueous/solid chemistry."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec
from .crevice_activity_corrected_transport import CreviceActivityReactiveTransportRequest
from .crevice_activity_corrected_transport import REACTION_SOURCE_ID
from .crevice_spatial_activity_solid_fixed_point import (
    CreviceCellActivitySolidInput,
    CreviceSpatialActivitySolidFixedPointRequest,
    _phase_request_with_state,
    solve_crevice_spatial_activity_solid_fixed_point,
)
from .crevice_variable_area_activity_transport import (
    AREA_HISTORY_SOURCE_ID,
    VariableAreaCreviceActivityReactiveTransportRequest,
    evaluate_variable_area_crevice_activity_transport,
)

MODEL_ID = "transport.crevice_spatial_activity_solid_nernst_planck_1d"
CELL_CHEMISTRY_SOURCE_ID = "caller_cellwise_aqueous_and_solid_equilibrium_by_knot"
METHOD_SOURCE_ID = "sequential_variable_volume_nernst_planck_and_local_chemistry_operator_split"


class CreviceChemistryKnot(Contract):
    knot_index: int = Field(ge=0)
    time_s: float
    cells: tuple[CreviceCellActivitySolidInput, ...] = Field(min_length=2, max_length=300)


class CreviceSpatialChemistryTransportRequest(Contract):
    schema_version: Literal["matintegrity.crevice_spatial_chemistry_transport.v1"] = (
        "matintegrity.crevice_spatial_chemistry_transport.v1"
    )
    assessment_id: str = Field(min_length=1)
    transport: VariableAreaCreviceActivityReactiveTransportRequest
    chemistry_by_knot: tuple[CreviceChemistryKnot, ...] = Field(min_length=2, max_length=500)
    maximum_cell_chemistry_iterations: int = Field(default=50, ge=2, le=1000)
    maximum_total_transport_function_evaluations: int = Field(default=2_000_000, ge=100, le=20_000_000)
    fixed_point_concentration_tolerance: Positive = Field(default=1e-8, le=1e-3)
    fixed_point_solid_tolerance: Positive = Field(default=1e-8, le=1e-3)
    fixed_point_constraint_tolerance: Positive = Field(default=1e-8, le=1e-3)
    chemistry_damping_fraction: Positive = Field(default=0.5, le=1.0)
    chemistry_transport_species_mapping_reviewed: bool
    conserved_linear_constraint_mapping_reviewed: bool
    zero_current_and_electroneutrality_reviewed: bool
    knotwise_instantaneous_chemistry_operator_split_reviewed: bool
    geometry_and_cell_order_alignment_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_knot_cells(self):
        transport = self.transport.transport_request
        if len(self.chemistry_by_knot) != len(transport.output_time_s):
            raise ValueError("chemistry knot count must equal transport output knot count")
        species = {row.species_id: row for row in transport.species}
        first_cells = self.chemistry_by_knot[0].cells
        first_phase_ids = tuple(row.solid_species_id for row in first_cells[0].solid_equilibrium_template.solid_phases)
        if len({cell.cell_id for cell in first_cells}) != len(first_cells):
            raise ValueError("cell IDs must be unique within each knot")
        for knot_index, (knot, time_s) in enumerate(zip(self.chemistry_by_knot, transport.output_time_s, strict=True)):
            if knot.knot_index != knot_index or knot.time_s != time_s:
                raise ValueError("chemistry knots must preserve exact transport index and time identity")
            if len(knot.cells) != transport.cell_count:
                raise ValueError("every chemistry knot must declare one chemistry input per transport cell")
            if tuple(row.cell_id for row in knot.cells) != tuple(row.cell_id for row in self.chemistry_by_knot[0].cells):
                raise ValueError("cell IDs and order must remain identical at all knots")
            for cell in knot.cells:
                if cell.solid_equilibrium_template.physical_scope_id != transport.physical_scope_id:
                    raise ValueError("cell chemistry and transport physical_scope_id must match")
                if cell.aqueous_activity_input.system.temperature_K != transport.temperature_K_by_knot[knot_index]:
                    raise ValueError("aqueous activity and transport temperatures must match at each exact knot")
                if tuple(row.solid_species_id for row in cell.solid_equilibrium_template.solid_phases) != first_phase_ids:
                    raise ValueError("caller solid-phase identities and order must remain stable across knots")
                system_species = {row.species_id: row for row in cell.aqueous_activity_input.system.species}
                solid_species = {row.species_id: row for row in cell.solid_equilibrium_template.aqueous_species}
                if set(system_species) != set(species) or set(solid_species) != set(species):
                    raise ValueError("aqueous, solid and transport species inventories must match exactly")
                for species_id, tr in species.items():
                    aq = system_species[species_id]
                    phase = solid_species[species_id]
                    if tr.charge_number != aq.charge_number or tr.elemental_composition != aq.elemental_composition:
                        raise ValueError("transport and aqueous chemistry charge/formula records must agree")
                    if tr.charge_number != phase.charge_number or tr.elemental_composition != phase.elemental_composition:
                        raise ValueError("transport and solid chemistry charge/formula records must agree")
                constraints = cell.aqueous_activity_input.system.constraints
                cindex = {row.species_id: i for i, row in enumerate(cell.aqueous_activity_input.system.species)}
                matrix = np.zeros((len(constraints), len(cindex)), dtype=float)
                for ri, constraint in enumerate(constraints):
                    for term in constraint.terms:
                        matrix[ri, cindex[term.species_id]] = term.coefficient
                elements = set().union(*(row.elemental_composition.keys() for row in species.values()))
                for element in elements:
                    vector = np.asarray([species[sid].elemental_composition.get(element, 0)
                                         for sid in cindex], dtype=float)
                    if np.linalg.matrix_rank(matrix) != np.linalg.matrix_rank(np.vstack((matrix, vector))):
                        raise ValueError(f"aqueous constraints do not conserve declared element {element!r}")
        if not all((self.chemistry_transport_species_mapping_reviewed,
                    self.conserved_linear_constraint_mapping_reviewed,
                    self.zero_current_and_electroneutrality_reviewed,
                    self.knotwise_instantaneous_chemistry_operator_split_reviewed,
                    self.geometry_and_cell_order_alignment_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all species mapping, conservation, operator-split and use reviews are required")
        return self


def _elemental_inventory(concentration, solids, request, knot_index):
    transport = request.transport.transport_request
    area = np.asarray(request.transport.cell_cross_section_area_m2_by_knot[knot_index], dtype=float)
    volume = area * transport.length_m / transport.cell_count
    species = {row.species_id: row for row in transport.species}
    elements = set().union(*(row.elemental_composition.keys() for row in species.values()))
    total = {element: 0.0 for element in elements}
    for species_id, by_cell in concentration.items():
        formula = species[species_id].elemental_composition
        for element in elements:
            total[element] += math.fsum(formula.get(element, 0) * by_cell[i] * volume[i]
                                        for i in range(transport.cell_count))
    for cell_index, cell in enumerate(request.chemistry_by_knot[knot_index].cells):
        phase_rows = {row.solid_species_id: row for row in cell.solid_equilibrium_template.solid_phases}
        for solid_id, mol_m3 in solids[cell_index].items():
            formula = phase_rows[solid_id].solid_elemental_composition
            for element in elements:
                total[element] += mol_m3 * volume[cell_index] * formula.get(element, 0)
    return total


def _face_flux_density(request, interval, concentration, gamma_by_cell):
    """Reconstruct the endpoint NP face flux using the same zero-current closure as the transport kernel."""
    transport = request.transport.transport_request
    nc = transport.cell_count
    dx = transport.length_m / nc
    rows = transport.species
    z = np.asarray([row.charge_number for row in rows], dtype=float)
    diffusivity = np.asarray([row.diffusivity_m2_s for row in rows], dtype=float)
    c = np.asarray([concentration[row.species_id] for row in rows], dtype=float)
    boundary = np.asarray([transport.mouth_boundary_concentration_mol_m3_by_species[row.species_id][interval + 1]
                           for row in rows], dtype=float)
    logg = np.log(np.asarray([[gamma_by_cell[cell][row.species_id] for cell in range(nc)] for row in rows]))
    mouth_gamma = np.asarray([row.mouth_activity_coefficient_by_time[interval + 1] for row in rows], dtype=float)
    velocity = np.asarray([schedule[interval + 1] for schedule in transport.cell_face_axial_velocity_m_s_by_knot], dtype=float)
    mobility = np.maximum(c, 0.0)
    grad_c = np.zeros((len(rows), nc + 1), dtype=float)
    face_c = np.zeros_like(grad_c)
    grad_lng = np.zeros_like(grad_c)
    grad_c[:, 0] = (c[:, 0] - boundary) / (0.5 * dx)
    face_c[:, 0] = 0.5 * (mobility[:, 0] + boundary)
    grad_lng[:, 0] = (logg[:, 0] - np.log(mouth_gamma)) / (0.5 * dx)
    grad_c[:, 1:nc] = (c[:, 1:] - c[:, :-1]) / dx
    face_c[:, 1:nc] = 0.5 * (mobility[:, 1:] + mobility[:, :-1])
    grad_lng[:, 1:nc] = (logg[:, 1:] - logg[:, :-1]) / dx
    upwind = np.where(velocity[None, :] >= 0.0,
                      np.concatenate((np.broadcast_to(boundary[:, None], (len(rows), 1)), mobility), axis=1),
                      np.concatenate((mobility, np.zeros((len(rows), 1))), axis=1))
    baseline = grad_c + face_c * grad_lng
    denominator = np.sum((z[:, None] ** 2) * diffusivity[:, None] * face_c, axis=0)
    numerator = -np.sum(z[:, None] * diffusivity[:, None] * baseline, axis=0) \
        + np.sum(z[:, None] * velocity[None, :] * upwind, axis=0)
    if np.any((denominator <= 0.0) & (np.abs(numerator) > 0.0)):
        raise ArithmeticError("zero_ionic_mobility_cannot_close_reported_face_current")
    dpsi = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0.0)
    flux = -diffusivity[:, None] * (baseline + z[:, None] * face_c * dpsi) + velocity[None, :] * upwind
    flux[:, -1] = 0.0
    area = np.asarray(request.transport.face_cross_section_area_m2_by_knot[interval + 1], dtype=float)
    molar_rate = flux * area[None, :]
    return {row.species_id: {
        "flux_density_mol_m2_s_by_face": [float(value) for value in flux[i]],
        "molar_rate_mol_s_by_face": [float(value) for value in molar_rate[i]],
    } for i, row in enumerate(rows)}


def _replace_pinned_evidence(rows, source_id: str, old_sha: str, new_sha: str):
    result = []
    found = False
    for row in rows:
        if row.source_id == source_id and row.sha256 == old_sha:
            result.append(row.model_copy(update={"sha256": new_sha}))
            found = True
        else:
            result.append(row)
    if not found:
        raise ValueError(f"no digest-pinned Evidence row for {source_id}")
    return tuple(result)


def _subinterval_request(request, interval: int, initial_by_species, gamma_by_cell):
    full = request.transport.transport_request
    time_slice = (interval, interval + 1)
    species_rows = []
    for row in full.species:
        species_rows.append(row.model_copy(update={
            "initial_cell_concentration_mol_m3": tuple(float(v) for v in initial_by_species[row.species_id]),
            # Piecewise constant activity field over this interval: re-equilibrated at its left knot.
            "activity_coefficient_by_time_and_cell": tuple(
                tuple(float(gamma_by_cell[cell][row.species_id]) for cell in range(full.cell_count))
                for _ in range(2)
            ),
            "mouth_activity_coefficient_by_time": tuple(row.mouth_activity_coefficient_by_time[k] for k in time_slice),
        }))
    reactions = []
    for reaction in full.reactions:
        forward = tuple(reaction.forward_rate_constant_mol_m3_s_by_knot[k] for k in time_slice)
        reverse = tuple(reaction.reverse_rate_constant_mol_m3_s_by_knot[k] for k in time_slice)
        equilibrium = tuple(reaction.equilibrium_constant_dimensionless_by_knot[k] for k in time_slice)
        payload = {
            "reaction_id": reaction.reaction_id,
            "forward_rate_constant_mol_m3_s_by_knot": forward,
            "reverse_rate_constant_mol_m3_s_by_knot": reverse,
            "equilibrium_constant_dimensionless_by_knot": equilibrium,
        }
        sha = canonical_digest(payload)
        evidence = _replace_pinned_evidence(reaction.evidence, reaction.parameter_record_id,
                                            reaction.parameter_record_sha256, sha)
        reactions.append(reaction.model_copy(update=payload | {
            "parameter_record_sha256": sha, "evidence": evidence,
        }))
    network_sha = canonical_digest([row.model_dump(mode="json") for row in reactions])
    network_evidence = _replace_pinned_evidence(full.reaction_network_evidence, REACTION_SOURCE_ID,
                                                full.reaction_network_sha256, network_sha)
    tr_payload = {
        "cross_section_area_m2": math.fsum(request.transport.cell_cross_section_area_m2_by_knot[interval]) / full.cell_count,
        "output_time_s": tuple(full.output_time_s[k] for k in time_slice),
        "species": tuple(species_rows),
        "mouth_boundary_concentration_mol_m3_by_species": {
            sid: tuple(values[k] for k in time_slice)
            for sid, values in full.mouth_boundary_concentration_mol_m3_by_species.items()
        },
        "cell_face_axial_velocity_m_s_by_knot": tuple(
            tuple(schedule[k] for k in time_slice) for schedule in full.cell_face_axial_velocity_m_s_by_knot
        ),
        "reactions": tuple(reactions),
        "temperature_K_by_knot": tuple(full.temperature_K_by_knot[k] for k in time_slice),
        "reaction_network_sha256": network_sha,
        "reaction_network_evidence": network_evidence,
    }
    sub_transport = full.model_copy(update=tr_payload)
    area = request.transport
    sub_cells = tuple(area.cell_cross_section_area_m2_by_knot[k] for k in time_slice)
    sub_faces = tuple(area.face_cross_section_area_m2_by_knot[k] for k in time_slice)
    area_payload = {
        "geometry_id": area.geometry_id,
        "provider_id": area.area_provider_id,
        "provider_revision": area.area_provider_revision,
        "configuration_sha256": area.area_configuration_sha256,
        "time_s": list(tr_payload["output_time_s"]),
        "cell_cross_section_area_m2_by_knot": [list(row) for row in sub_cells],
        "face_cross_section_area_m2_by_knot": [list(row) for row in sub_faces],
    }
    sub_area_sha = canonical_digest(area_payload)
    sub_evidence = _replace_pinned_evidence(area.area_history_evidence, AREA_HISTORY_SOURCE_ID,
                                            area.area_history_sha256, sub_area_sha)
    sub_area = area.model_copy(update={
        "transport_request": sub_transport,
        "cell_cross_section_area_m2_by_knot": sub_cells,
        "face_cross_section_area_m2_by_knot": sub_faces,
        "area_history_sha256": sub_area_sha,
        "area_history_evidence": sub_evidence,
    })
    return sub_area, sub_area_sha


def _chemistry_at_knot(request, knot_index, concentration_by_species, solids_by_cell):
    knot = request.chemistry_by_knot[knot_index]
    cells = []
    for cell_index, template_cell in enumerate(knot.cells):
        system = template_cell.aqueous_activity_input.system
        targets = {}
        concentration_m3 = {sid: concentration_by_species[sid][cell_index]
                            for sid in concentration_by_species}
        for constraint in system.constraints:
            targets[constraint.constraint_id] = math.fsum(
                term.coefficient * concentration_m3[term.species_id] / 1000.0
                for term in constraint.terms
            )
        constraints = tuple(row.model_copy(update={"target_mol_L": targets[row.constraint_id]})
                            for row in system.constraints)
        activity_input = template_cell.aqueous_activity_input.model_copy(update={
            "system": system.model_copy(update={"constraints": constraints}),
        })
        gamma = {row.species_id: row.activity_coefficient for row in system.species}
        solid_template = _phase_request_with_state(
            template_cell.solid_equilibrium_template,
            concentration_m3,
            gamma,
            solids_by_cell[cell_index],
        )
        cells.append(template_cell.model_copy(update={
            "aqueous_activity_input": activity_input,
            "solid_equilibrium_template": solid_template,
        }))
    geometry_sha = request.transport.area_history_sha256
    evidence = tuple(row for row in request.transport.area_history_evidence
                     if row.source_id == AREA_HISTORY_SOURCE_ID and row.sha256 == geometry_sha)
    if not evidence:
        return None, {"reason": "geometry_history_digest_evidence_missing"}
    fixed = CreviceSpatialActivitySolidFixedPointRequest(
        assessment_id=f"{request.assessment_id}:knot:{knot_index}",
        geometry_mode="fixed_single_knot",
        geometry_provider_id=AREA_HISTORY_SOURCE_ID,
        geometry_revision=request.transport.area_provider_revision,
        geometry_sha256=geometry_sha,
        cells=tuple(cells),
        maximum_outer_iterations=request.maximum_cell_chemistry_iterations,
        maximum_total_cell_iterations=request.maximum_cell_chemistry_iterations * len(cells),
        concentration_relative_tolerance=request.fixed_point_concentration_tolerance,
        solid_inventory_relative_tolerance=request.fixed_point_solid_tolerance,
        constraint_relative_tolerance=request.fixed_point_constraint_tolerance,
        damping_fraction=request.chemistry_damping_fraction,
        evidence=evidence,
        complete_cell_mapping_and_species_scope_reviewed=True,
        aqueous_linear_constraints_are_conserved_including_solid_transfer_reviewed=True,
        standard_state_and_equilibrium_records_reviewed=True,
        fixed_geometry_single_knot_scope_reviewed=True,
        computational_use_authorized=True,
    )
    result = solve_crevice_spatial_activity_solid_fixed_point(fixed)
    if result.status != "computed":
        return result, None
    next_concentration = {sid: [float(cell["aqueous_species_concentration_mol_m3"][sid])
                                for cell in result.values["cell_results"]]
                          for sid in concentration_by_species}
    next_solids = []
    for cell in result.values["cell_results"]:
        next_solids.append(cell["solid_inventory_mol_m3"])
    next_gamma = []
    for cell in result.values["cell_results"]:
        species_rows = cell["aqueous_activity_result"]["values"]["species"]
        next_gamma.append({row["species_id"]: float(row["activity_coefficient"]) for row in species_rows})
    return result, {"concentration": next_concentration, "solids": next_solids, "gamma": next_gamma}


def solve_crevice_spatial_chemistry_transport(request: CreviceSpatialChemistryTransportRequest) -> Calculation:
    """Advance conservative NP transport interval by interval and equilibrate caller chemistry at every knot."""
    digest = canonical_digest(request.model_dump(mode="json"))
    transport = request.transport.transport_request
    species_rows = transport.species
    ns, nc, nt = len(species_rows), transport.cell_count, len(transport.output_time_s)
    ids = [row.species_id for row in species_rows]
    c = {row.species_id: list(row.initial_cell_concentration_mol_m3) for row in species_rows}
    solid_states = [
        {row.solid_species_id: row.initial_solid_moles_per_solution_volume_mol_m3
         for row in cell.solid_equilibrium_template.solid_phases}
        for cell in request.chemistry_by_knot[0].cells
    ]
    state_history = []
    transport_lineage = []
    chemistry_lineage = []
    face_flux_history = []
    total_evaluations = 0
    first_chem, first_state = _chemistry_at_knot(request, 0, c, solid_states)
    if first_state is None:
        return Calculation(status=first_chem.status if hasattr(first_chem, "status") else "needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_knot_index": 0, "failed_chemistry_result": first_chem.model_dump(mode="json")
            if hasattr(first_chem, "model_dump") else first_chem,
            "accepted_knot_prefix": [],
        })
    c, solid_states = first_state["concentration"], first_state["solids"]
    gamma_state = first_state["gamma"]
    initial_element_inventory = _elemental_inventory(c, solid_states, request, 0)
    cumulative_element_inflow = {element: 0.0 for element in initial_element_inventory}
    element_inventory_history = [{"knot_index": 0, "total_moles_by_element": initial_element_inventory,
                                  "external_inflow_moles_by_element": dict(cumulative_element_inflow),
                                  "closure_residual_moles_by_element": {element: 0.0 for element in initial_element_inventory}}]
    chemistry_lineage.append({"knot_index": 0, "time_s": transport.output_time_s[0],
                              "result_sha256": canonical_digest(first_chem.model_dump(mode="json"))})
    state_history.append({"knot_index": 0, "time_s": transport.output_time_s[0],
                          "geometry_knot_sha256": canonical_digest({
                              "geometry_id": request.transport.geometry_id,
                              "time_s": transport.output_time_s[0],
                              "cell_area_m2": request.transport.cell_cross_section_area_m2_by_knot[0],
                              "face_area_m2": request.transport.face_cross_section_area_m2_by_knot[0],
                          }),
                          "chemistry_result_sha256": chemistry_lineage[-1]["result_sha256"],
                          "aqueous_concentration_mol_m3_by_species_and_cell": c,
                          "solid_inventory_mol_m3_by_cell": solid_states})

    for interval in range(nt - 1):
        try:
            subrequest, interval_geometry_sha = _subinterval_request(request, interval, c, gamma_state)
        except (ValueError, KeyError, ArithmeticError) as error:
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval, "reason": str(error),
                "accepted_knot_prefix": state_history, "transport_lineage": transport_lineage,
                "chemistry_lineage": chemistry_lineage,
            })
        interval_result = evaluate_variable_area_crevice_activity_transport(subrequest)
        if interval_result.status != "computed":
            return Calculation(status=interval_result.status, values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval, "failed_transport_result": interval_result.model_dump(mode="json"),
                "accepted_knot_prefix": state_history, "transport_lineage": transport_lineage,
                "chemistry_lineage": chemistry_lineage,
            })
        total_evaluations += int(interval_result.values["function_evaluations"])
        transport_lineage.append({"interval_index": interval,
                                  "geometry_history_sha256": interval_geometry_sha,
                                  "input_sha256": interval_result.values["input_sha256"],
                                  "result_sha256": canonical_digest(interval_result.model_dump(mode="json")),
                                  "function_evaluations": interval_result.values["function_evaluations"]})
        if total_evaluations > request.maximum_total_transport_function_evaluations:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval, "termination_reason": "assessment transport evaluation budget exceeded",
                "function_evaluations": total_evaluations, "accepted_knot_prefix": state_history,
                "transport_lineage": transport_lineage, "chemistry_lineage": chemistry_lineage,
            })
        endpoint = interval_result.values["state_history"][-1]["species_concentration_mol_m3_by_id"]
        try:
            face_flux_history.append({
                "interval_index": interval,
                "endpoint_time_s": transport.output_time_s[interval + 1],
                "geometry_history_sha256": interval_geometry_sha,
                "species_fluxes": _face_flux_density(request, interval, endpoint, gamma_state),
            })
        except (ArithmeticError, ValueError, FloatingPointError) as error:
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval, "reason": str(error),
                "accepted_knot_prefix": state_history, "transport_lineage": transport_lineage,
                "chemistry_lineage": chemistry_lineage, "face_flux_prefix": face_flux_history,
            })
        mouth = interval_result.values["integrated_mouth_transfer_mol_by_species"]
        reaction_source = interval_result.values["integrated_reaction_source_mol_by_species"]
        transport_species_by_id = {row.species_id: row for row in species_rows}
        for element in cumulative_element_inflow:
            cumulative_element_inflow[element] += math.fsum(
                transport_species_by_id[sid].elemental_composition.get(element, 0)
                * (float(mouth[sid][-1]) + float(reaction_source[sid][-1]))
                for sid in ids
            )
        c = {sid: list(endpoint[sid]) for sid in ids}
        chemistry_result, chemistry_state = _chemistry_at_knot(request, interval + 1, c, solid_states)
        if chemistry_state is None:
            return Calculation(status=chemistry_result.status if hasattr(chemistry_result, "status") else "needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_knot_index": interval + 1,
                "failed_chemistry_result": chemistry_result.model_dump(mode="json")
                if hasattr(chemistry_result, "model_dump") else chemistry_result,
                "accepted_knot_prefix": state_history, "transport_lineage": transport_lineage,
                "chemistry_lineage": chemistry_lineage,
            })
        c, solid_states, gamma_state = chemistry_state["concentration"], chemistry_state["solids"], chemistry_state["gamma"]
        total_elements = _elemental_inventory(c, solid_states, request, interval + 1)
        element_residual = {element: total_elements[element] - initial_element_inventory[element]
                            - cumulative_element_inflow[element] for element in total_elements}
        total_volume = math.fsum(request.transport.cell_cross_section_area_m2_by_knot[interval + 1]) \
            * transport.length_m / transport.cell_count
        element_scale = max(1e-30, *(abs(value) for value in total_elements.values()),
                            *(abs(value) for value in initial_element_inventory.values()))
        element_allowed = transport.absolute_tolerance_mol_m3 * total_volume + transport.relative_tolerance * element_scale
        if any(not math.isfinite(value) or abs(value) > element_allowed for value in element_residual.values()):
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_knot_index": interval + 1,
                "reason": "aqueous-plus-solid elemental inventory closure exceeded tolerance",
                "element_inventory_mol_by_element": total_elements,
                "element_inflow_mol_by_element": dict(cumulative_element_inflow),
                "element_closure_residual_mol_by_element": element_residual,
                "accepted_knot_prefix": state_history, "transport_lineage": transport_lineage,
                "chemistry_lineage": chemistry_lineage,
            })
        element_inventory_history.append({
            "knot_index": interval + 1,
            "total_moles_by_element": total_elements,
            "external_inflow_moles_by_element": dict(cumulative_element_inflow),
            "closure_residual_moles_by_element": element_residual,
            "allowed_absolute_residual_mol": element_allowed,
        })
        chemistry_lineage.append({"knot_index": interval + 1, "time_s": transport.output_time_s[interval + 1],
                                  "result_sha256": canonical_digest(chemistry_result.model_dump(mode="json"))})
        state_history.append({"knot_index": interval + 1, "time_s": transport.output_time_s[interval + 1],
                              "chemistry_result_sha256": chemistry_lineage[-1]["result_sha256"],
                              "geometry_knot_sha256": canonical_digest({
                                  "geometry_id": request.transport.geometry_id,
                                  "time_s": transport.output_time_s[interval + 1],
                                  "cell_area_m2": request.transport.cell_cross_section_area_m2_by_knot[interval + 1],
                                  "face_area_m2": request.transport.face_cross_section_area_m2_by_knot[interval + 1],
                              }),
                              "aqueous_concentration_mol_m3_by_species_and_cell": c,
                              "solid_inventory_mol_m3_by_cell": solid_states})
    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": transport.asset_id,
        "physical_scope_id": transport.physical_scope_id,
        "clock_id": transport.clock_id,
        "input_sha256": digest,
        "transport_geometry_history_sha256": request.transport.area_history_sha256,
        "cell_chemistry_source_id": CELL_CHEMISTRY_SOURCE_ID,
        "method_source_id": METHOD_SOURCE_ID,
        "committed_knot_count": len(state_history),
        "state_history": state_history,
        "transport_face_flux_history": face_flux_history,
        "element_inventory_closure_history": element_inventory_history,
        "transport_interval_lineage": transport_lineage,
        "chemistry_knot_lineage": chemistry_lineage,
        "total_transport_function_evaluations": total_evaluations,
        "all_requested_knots_completed": True,
        "operator_split": "BDF variable-volume NP transport over each exact interval; instantaneous Davies/speciation/solid equilibrium at every knot; endpoint activity held at left-knot chemistry within next interval",
        "intercell_flux": "Nernst-Planck with caller diffusivities, face areas, velocities, zero-current closure and prescribed mouth boundary; blind-tip flux zero",
        "phase_discovery": False,
        "geometry_feedback": False,
        "limitations": [
            "Activity/speciation and solid transfer are applied at exact knots; chemistry is not re-solved at every BDF internal stage.",
            "Transport uses left-knot cell activity coefficients held over each interval; temporal activity variation within an interval is not iterated to convergence.",
            "Caller kinetic reaction network is integrated by the existing variable-area solver. Solid transfer is instantaneous at knots, not a precipitation/dissolution kinetic law.",
            "No automatic chemistry/phase discovery, pH model, gas phases, mixed potential, electrochemical source term, corrosion rate or aperture feedback is inferred.",
        ],
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSpatialChemistryTransportRequest,
        evaluator=solve_crevice_spatial_chemistry_transport,
        units={
            "state_history[].time_s": "s",
            "state_history[].aqueous_concentration_mol_m3_by_species_and_cell.*[]": "mol/m^3",
            "state_history[].solid_inventory_mol_m3_by_cell.*": "mol/m^3_solution",
            "element_inventory_closure_history[].total_moles_by_element.*": "mol",
            "element_inventory_closure_history[].external_inflow_moles_by_element.*": "mol",
            "element_inventory_closure_history[].closure_residual_moles_by_element.*": "mol",
            "total_transport_function_evaluations": "1",
        },
        assumptions=(
            "Each interval uses the existing conservative variable-volume finite-volume Nernst-Planck BDF solver, including caller face areas, velocity, ionic diffusivity, zero-current closure and blind-tip no-flux boundary.",
            "At each exact knot, caller mass-action/Davies and finite competing-solid equilibria are solved; aqueous and solid states are carried into the next interval.",
            "The left-knot chemistry activity coefficients are held constant within each BDF interval; chemistry is not solved at internal integrator stages.",
            "Every caller linear chemistry constraint must span each declared aqueous elemental inventory; kinetic and phase discovery are not automatic.",
        ),
        source_ids=(CELL_CHEMISTRY_SOURCE_ID, METHOD_SOURCE_ID, AREA_HISTORY_SOURCE_ID,
                    "caller_crevice_activity_corrected_transport_species",
                    "caller_activity_based_crevice_reaction_network",
                    "aqueous_solid_inventory_feedback_fixed_point", "scipy_integrate_bdf"),
    ),)
