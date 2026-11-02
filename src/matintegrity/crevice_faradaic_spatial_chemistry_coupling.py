"""Knotwise spatial Butler–Volmer and Faradaic inventory coupling for crevice chemistry transport."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec
from .crevice_spatial_chemistry_transport import (
    CreviceSpatialChemistryTransportRequest,
    _chemistry_at_knot,
    _elemental_inventory,
    _subinterval_request,
)
from .crevice_spatial_ohmic_mixed_potential import (
    FARADAY_CONSTANT_C_MOL,
    CreviceSpatialOhmicMixedPotentialRequest,
    solve_crevice_spatial_ohmic_mixed_potential,
)
from .crevice_variable_area_activity_transport import evaluate_variable_area_crevice_activity_transport

MODEL_ID = "integration.crevice_faradaic_spatial_chemistry_coupling"
FARADAIC_MAP_SOURCE_ID = "caller_faradaic_branch_species_and_reservoir_stoichiometry"
NERNST_SOURCE_ID = "caller_spatial_nernst_standard_potential_and_activity_quotient"
CONDUCTIVITY_SOURCE_ID = "caller_species_molar_conductivity_mapping"
METHOD_SOURCE_ID = "knotwise_spatial_mixed_potential_faradaic_inventory_split"
GAS_CONSTANT_J_MOL_K = 8.31446261815324


class CreviceNernstBranchMap(Contract):
    reaction_id: str = Field(min_length=1)
    standard_potential_V_by_cell_and_knot: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    log_quotient_coefficient_by_species: dict[str, float] = Field(min_length=1, max_length=40)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)


class CreviceFaradaicBranchMap(Contract):
    reaction_id: str = Field(min_length=1)
    electron_number: int = Field(ge=1, le=32)
    aqueous_species_stoichiometry_per_extent: dict[str, float] = Field(min_length=1, max_length=40)
    external_reservoir_element_stoichiometry_per_extent: dict[str, float] = Field(default_factory=dict, max_length=32)
    record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)


class CreviceFaradaicSpatialChemistryRequest(Contract):
    schema_version: Literal["matintegrity.crevice_faradaic_spatial_chemistry.v1"] = (
        "matintegrity.crevice_faradaic_spatial_chemistry.v1"
    )
    assessment_id: str = Field(min_length=1)
    transport_chemistry: CreviceSpatialChemistryTransportRequest
    mixed_potential_template: CreviceSpatialOhmicMixedPotentialRequest
    nernst_branch_maps: tuple[CreviceNernstBranchMap, ...] = Field(min_length=2, max_length=32)
    faradaic_branch_maps: tuple[CreviceFaradaicBranchMap, ...] = Field(min_length=2, max_length=32)
    background_conductivity_S_m_by_knot_and_cell: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=500)
    molar_conductivity_S_m2_mol_by_species_knot_and_cell: dict[str, tuple[tuple[Positive, ...], ...]] = Field(
        min_length=2, max_length=40
    )
    conductivity_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    conductivity_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    absolute_faradic_charge_source_tolerance_mol_eq_s: Positive = 1e-12
    relative_faradic_charge_source_tolerance: Positive = Field(default=1e-8, le=1e-3)
    current_balance_tolerance_A: Positive = 1e-8
    absolute_inventory_balance_tolerance_mol: Positive = 1e-10
    relative_inventory_balance_tolerance: Positive = Field(default=1e-8, le=1e-3)
    maximum_right_endpoint_iterations: int = Field(default=30, ge=2, le=1000)
    current_density_absolute_tolerance_A_m2: Positive = 1e-9
    current_relative_tolerance: Positive = Field(default=1e-7, le=1e-3)
    chemistry_state_relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    current_relaxation_fraction: Positive = Field(default=0.5, le=1.0)
    maximum_total_transport_function_evaluations: int = Field(default=5_000_000, ge=100, le=20_000_000)
    maximum_total_mixed_potential_evaluations: int = Field(default=2_000_000, ge=100, le=20_000_000)
    activity_quotient_mapping_reviewed: bool
    branch_species_and_reservoir_stoichiometry_reviewed: bool
    zero_net_aqueous_faradic_charge_source_reviewed: bool
    mixed_potential_current_and_area_mapping_reviewed: bool
    endpoint_trapezoid_faradic_extent_split_reviewed: bool
    no_unmodeled_double_layer_or_electrochemical_transport_current_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_faradaic_contract(self):
        coupled = self.transport_chemistry
        transport = coupled.transport.transport_request
        mixed = self.mixed_potential_template
        branch_ids = tuple(row.reaction_id for row in mixed.branches)
        if len(set(branch_ids)) != len(branch_ids):
            raise ValueError("mixed-potential branch IDs must be unique")
        if tuple(row.reaction_id for row in self.nernst_branch_maps) != branch_ids:
            raise ValueError("Nernst branch maps must exactly match mixed-potential branch order")
        if tuple(row.reaction_id for row in self.faradaic_branch_maps) != branch_ids:
            raise ValueError("Faradaic maps must exactly match mixed-potential branch order")
        species = {row.species_id: row for row in transport.species}
        elements = set().union(*(row.elemental_composition.keys() for row in species.values()))
        for branch, nernst, faradaic in zip(mixed.branches, self.nernst_branch_maps, self.faradaic_branch_maps, strict=True):
            if branch.electron_number != faradaic.electron_number or branch.reaction_id != nernst.reaction_id:
                raise ValueError("branch electron count, Nernst map and Faradaic map must agree")
            if set(nernst.log_quotient_coefficient_by_species) - set(species):
                raise ValueError("Nernst quotient references an undeclared transport species")
            if set(faradaic.aqueous_species_stoichiometry_per_extent) - set(species):
                raise ValueError("Faradaic reaction references an undeclared aqueous species")
            if set(faradaic.external_reservoir_element_stoichiometry_per_extent) - elements:
                raise ValueError("external reservoir element map references an undeclared element")
            charge_stoichiometry = math.fsum(
                species[sid].charge_number * coefficient
                for sid, coefficient in faradaic.aqueous_species_stoichiometry_per_extent.items()
            )
            if not math.isclose(abs(charge_stoichiometry), faradaic.electron_number,
                                rel_tol=1e-10, abs_tol=1e-10):
                raise ValueError("Faradaic aqueous reaction charge transfer magnitude must equal its electron number")
            for element in elements:
                balance = math.fsum(
                    coefficient * species[species_id].elemental_composition.get(element, 0)
                    for species_id, coefficient in faradaic.aqueous_species_stoichiometry_per_extent.items()
                ) + faradaic.external_reservoir_element_stoichiometry_per_extent.get(element, 0.0)
                scale = max(1.0, math.fsum(abs(coefficient * species[sid].elemental_composition.get(element, 0))
                                           for sid, coefficient in faradaic.aqueous_species_stoichiometry_per_extent.items()))
                if abs(balance) > 1e-10 * scale:
                    raise ValueError(f"Faradaic branch {branch.reaction_id} fails declared element/reservoir closure for {element}")
            if nernst.standard_potential_V_by_cell_and_knot and (
                len(nernst.standard_potential_V_by_cell_and_knot) != transport.cell_count
                or any(len(row) != len(transport.output_time_s) for row in nernst.standard_potential_V_by_cell_and_knot)
            ):
                raise ValueError("standard-potential schedule must match cell × exact transport knots")
            nernst_payload = {
                "reaction_id": nernst.reaction_id,
                "standard_potential_V_by_cell_and_knot": nernst.standard_potential_V_by_cell_and_knot,
                "log_quotient_coefficient_by_species": nernst.log_quotient_coefficient_by_species,
            }
            if canonical_digest(nernst_payload) != nernst.record_sha256 or not any(
                row.source_id == NERNST_SOURCE_ID and row.sha256 == nernst.record_sha256
                for row in nernst.evidence
            ):
                raise ValueError("Nernst record digest and Evidence must bind the complete standard-potential/quotient mapping")
            faradaic_payload = {
                "reaction_id": faradaic.reaction_id,
                "electron_number": faradaic.electron_number,
                "aqueous_species_stoichiometry_per_extent": faradaic.aqueous_species_stoichiometry_per_extent,
                "external_reservoir_element_stoichiometry_per_extent": faradaic.external_reservoir_element_stoichiometry_per_extent,
            }
            if canonical_digest(faradaic_payload) != faradaic.record_sha256 or not any(
                row.source_id == FARADAIC_MAP_SOURCE_ID and row.sha256 == faradaic.record_sha256 and row.license_id
                for row in faradaic.evidence
            ):
                raise ValueError("licensed Faradaic mapping Evidence must bind the complete stoichiometry map")
        nc, nt = transport.cell_count, len(transport.output_time_s)
        if mixed.cell_ids != tuple(cell.cell_id for cell in coupled.chemistry_by_knot[0].cells):
            raise ValueError("mixed-potential cell identities/order must match chemistry and transport")
        if mixed.time_s != transport.output_time_s or any(
            not math.isclose(length, transport.length_m / nc, rel_tol=1e-10, abs_tol=1e-14)
            for length in mixed.cell_lengths_m
        ):
            raise ValueError("mixed-potential clock and cell lengths must match transport exactly")
        if mixed.temperature_K_by_time != transport.temperature_K_by_knot:
            raise ValueError("mixed-potential and aqueous transport temperature schedules must align exactly")
        if any(not math.isclose(area, aperture * mixed.slit_width_m, rel_tol=1e-10, abs_tol=1e-14)
               for area, aperture in zip(coupled.transport.cell_cross_section_area_m2_by_knot[0],
                                         mixed.cell_apertures_m, strict=True)):
            raise ValueError("initial mixed-potential apertures × width must match transport cell areas")
        if len(self.background_conductivity_S_m_by_knot_and_cell) != nt or any(
            len(row) != nc for row in self.background_conductivity_S_m_by_knot_and_cell
        ):
            raise ValueError("background conductivity must match exact knot × cell grid")
        if set(self.molar_conductivity_S_m2_mol_by_species_knot_and_cell) != set(species):
            raise ValueError("molar conductivity coefficients must cover each transport species exactly")
        if any(len(values) != nt or any(len(row) != nc for row in values)
               for values in self.molar_conductivity_S_m2_mol_by_species_knot_and_cell.values()):
            raise ValueError("molar conductivity coefficients must match species × knot × cell grid")
        conductivity_payload = {
            "background_conductivity_S_m_by_knot_and_cell": [list(row) for row in self.background_conductivity_S_m_by_knot_and_cell],
            "molar_conductivity_S_m2_mol_by_species_knot_and_cell": {
                sid: [list(row) for row in values]
                for sid, values in self.molar_conductivity_S_m2_mol_by_species_knot_and_cell.items()
            },
        }
        if canonical_digest(conductivity_payload) != self.conductivity_record_sha256 or not any(
            row.source_id == CONDUCTIVITY_SOURCE_ID and row.sha256 == self.conductivity_record_sha256
            for row in self.conductivity_evidence
        ):
            raise ValueError("conductivity digest and Evidence must bind the caller species mapping")
        review_flags = (
            self.activity_quotient_mapping_reviewed,
            self.branch_species_and_reservoir_stoichiometry_reviewed,
            self.zero_net_aqueous_faradic_charge_source_reviewed,
            self.mixed_potential_current_and_area_mapping_reviewed,
            self.endpoint_trapezoid_faradaic_extent_split_reviewed,
            self.no_unmodeled_double_layer_or_electrochemical_transport_current_reviewed,
            self.computational_use_authorized,
        )
        if not all(review_flags):
            raise ValueError("all Nernst, charge/species, current transfer and applicability reviews are required")
        return self


def _rebind_evidence(evidence, source_id, old_sha, new_sha):
    rows, found = [], False
    for row in evidence:
        if row.source_id == source_id and row.sha256 == old_sha:
            rows.append(row.model_copy(update={"sha256": new_sha, "origin": "model_prediction"}))
            found = True
        else:
            rows.append(row)
    if not found:
        raise ValueError(f"missing source Evidence {source_id} for rebound digest")
    return tuple(rows)


def _mixed_potential_at_knot(request, state, gamma_by_cell, knot_index):
    template = request.mixed_potential_template
    coupled = request.transport_chemistry
    transport = coupled.transport.transport_request
    n, width = transport.cell_count, template.slit_width_m
    concentrations = state["concentration"]
    conductivity = []
    for cell in range(n):
        value = request.background_conductivity_S_m_by_knot_and_cell[knot_index][cell]
        for species in transport.species:
            value += request.molar_conductivity_S_m2_mol_by_species_knot_and_cell[species.species_id][knot_index][cell] \
                * concentrations[species.species_id][cell]
        if not math.isfinite(value) or value <= 0.0:
            raise ArithmeticError("chemistry-derived caller conductivity is nonpositive or nonfinite")
        conductivity.append(value)
    conductivity_sha = canonical_digest({
        "conductivity_record_sha256": request.conductivity_record_sha256,
        "knot_index": knot_index,
        "time_s": transport.output_time_s[knot_index],
        "conductivity_S_m_by_cell": conductivity,
    })
    branches = []
    nernst_by_id = {row.reaction_id: row for row in request.nernst_branch_maps}
    activity_by_id = {
        species.species_id: [gamma_by_cell[cell][species.species_id]
                             * concentrations[species.species_id][cell]
                             / transport.concentration_standard_state_mol_m3 for cell in range(n)]
        for species in transport.species
    }
    temperature = transport.temperature_K_by_knot[knot_index]
    for branch in template.branches:
        mapping = nernst_by_id[branch.reaction_id]
        eq_potential = []
        for cell in range(n):
            ln_q = math.fsum(coefficient * math.log(activity_by_id[species_id][cell])
                             for species_id, coefficient in mapping.log_quotient_coefficient_by_species.items())
            e0 = mapping.standard_potential_V_by_cell_and_knot[cell][knot_index]
            eq_potential.append(e0 - GAS_CONSTANT_J_MOL_K * temperature / (branch.electron_number * FARADAY_CONSTANT_C_MOL) * ln_q)
        branches.append(branch.model_copy(update={
            "equilibrium_potential_V_by_cell_and_time": tuple((float(value),) for value in eq_potential),
        }))
    geometry = {
        "geometry_id": coupled.transport.geometry_id,
        "area_history_sha256": coupled.transport.area_history_sha256,
        "knot_index": knot_index,
        "time_s": transport.output_time_s[knot_index],
        "cell_ids": list(template.cell_ids),
        "cell_lengths_m": list(template.cell_lengths_m),
        "cell_apertures_m": [area / width for area in coupled.transport.cell_cross_section_area_m2_by_knot[knot_index]],
        "slit_width_m": width,
    }
    geometry_sha = canonical_digest(geometry)
    evidence = list(template.evidence)
    evidence = list(_rebind_evidence(evidence, template.geometry_provider_id, template.geometry_sha256, geometry_sha))
    evidence = list(_rebind_evidence(evidence, template.conductivity_provider_id,
                                     template.conductivity_sha256, conductivity_sha))
    request_knot = template.model_copy(update={
        "time_s": (transport.output_time_s[knot_index],),
        "cell_apertures_m": tuple(area / width for area in coupled.transport.cell_cross_section_area_m2_by_knot[knot_index]),
        "temperature_K_by_time": (temperature,),
        "electrolyte_conductivity_S_m_by_cell_and_time": tuple((value,) for value in conductivity),
        "branches": tuple(branches),
        "geometry_sha256": geometry_sha,
        "conductivity_sha256": conductivity_sha,
        "evidence": tuple(evidence),
    })
    result = solve_crevice_spatial_ohmic_mixed_potential(request_knot)
    return result, request_knot, activity_by_id


def _system_element_total(result, request, knot_index):
    return _elemental_inventory(result["concentration"], result["solids"], request.transport_chemistry, knot_index)


def solve_crevice_faradaic_spatial_chemistry(
    request: CreviceFaradaicSpatialChemistryRequest,
) -> Calculation:
    """Sequentially solve variable-area transport, exact-knot chemistry, local mixed potentials and Faradaic extents."""
    digest = canonical_digest(request.model_dump(mode="json"))
    coupled = request.transport_chemistry
    variable = coupled.transport
    transport = variable.transport_request
    ids = [row.species_id for row in transport.species]
    nc, nt = transport.cell_count, len(transport.output_time_s)
    concentration = {row.species_id: list(row.initial_cell_concentration_mol_m3) for row in transport.species}
    solids = [{row.solid_species_id: row.initial_solid_moles_per_solution_volume_mol_m3
               for row in cell.solid_equilibrium_template.solid_phases}
              for cell in coupled.chemistry_by_knot[0].cells]
    try:
        initial_chemistry, state = _chemistry_at_knot(coupled, 0, concentration, solids)
    except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError) as error:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_knot_index": 0, "reason": str(error), "accepted_interval_prefix": [],
            "committed": False,
        })
    if state is None:
        return Calculation(status=initial_chemistry.status if hasattr(initial_chemistry, "status") else "needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_knot_index": 0, "failed_chemistry_result": initial_chemistry.model_dump(mode="json")
            if hasattr(initial_chemistry, "model_dump") else initial_chemistry, "accepted_interval_prefix": [],
        })
    concentration, solids, gamma = state["concentration"], state["solids"], state["gamma"]
    try:
        mixed_left, mixed_request_left, _ = _mixed_potential_at_knot(request, state, gamma, 0)
    except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError) as error:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_knot_index": 0, "reason": str(error), "accepted_interval_prefix": [],
            "committed": False,
        })
    if mixed_left.status != "computed":
        return Calculation(status=mixed_left.status, values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_knot_index": 0, "failed_mixed_potential": mixed_left.model_dump(mode="json"),
            "accepted_interval_prefix": [],
        })
    if mixed_left.values["maximum_absolute_cell_current_closure_residual_A"] > request.current_balance_tolerance_A:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_knot_index": 0, "reason": "mixed-potential cell current residual exceeds the coupling tolerance",
            "maximum_absolute_cell_current_closure_residual_A": mixed_left.values["maximum_absolute_cell_current_closure_residual_A"],
            "accepted_interval_prefix": [],
        })
    if any(abs(value) > request.current_balance_tolerance_A for value in
           mixed_left.values["state_history"][0]["electrolyte_face_current_A_by_cell_boundary"]):
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_knot_index": 0,
            "reason": "the reused NP kernel enforces zero ionic face current; nonzero ohmic face-current coupling is unsupported",
            "mixed_potential_face_current_A": mixed_left.values["state_history"][0]["electrolyte_face_current_A_by_cell_boundary"],
            "accepted_interval_prefix": [],
        })
    initial_elements = _system_element_total(state, coupled, 0)
    cumulative_transport_element_source = {element: 0.0 for element in initial_elements}
    cumulative_reservoir = {element: 0.0 for element in initial_elements}
    branch_maps = {row.reaction_id: row for row in request.faradaic_branch_maps}
    branch_template = {row.reaction_id: row for row in request.mixed_potential_template.branches}
    mixed_lineage = [{"knot_index": 0,
                      "input_sha256": canonical_digest(mixed_request_left.model_dump(mode="json")),
                      "result_sha256": canonical_digest(mixed_left.model_dump(mode="json"))}]
    accepted_intervals = []
    total_transport_evaluations = 0
    total_mixed_evaluations = int(mixed_left.values["solver_function_evaluations"])
    if total_mixed_evaluations > request.maximum_total_mixed_potential_evaluations:
        return Calculation(status="out_of_scope", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "reason": "initial mixed-potential solver evaluation budget exceeded",
            "accepted_interval_prefix": [], "committed": False,
        })

    for interval in range(nt - 1):
        try:
            tr_request, geometry_sha = _subinterval_request(coupled, interval, concentration, gamma)
            tr_result = evaluate_variable_area_crevice_activity_transport(tr_request)
        except (ValueError, KeyError, TypeError, ArithmeticError) as error:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval, "reason": str(error),
                "accepted_interval_prefix": accepted_intervals,
                "mixed_potential_lineage": mixed_lineage, "committed": False,
            })
        if tr_result.status != "computed":
            return Calculation(status=tr_result.status, values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval, "failed_transport_result": tr_result.model_dump(mode="json"),
                "accepted_interval_prefix": accepted_intervals,
                "mixed_potential_lineage": mixed_lineage, "committed": False,
            })
        interval_transport_evaluations = int(tr_result.values["function_evaluations"])
        if total_transport_evaluations + interval_transport_evaluations > request.maximum_total_transport_function_evaluations:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval, "reason": "transport solver evaluation budget exceeded",
                "accepted_interval_prefix": accepted_intervals,
                "mixed_potential_lineage": mixed_lineage, "committed": False,
            })
        endpoint_transport = tr_result.values["state_history"][-1]["species_concentration_mol_m3_by_id"]
        base_endpoint = {sid: list(endpoint_transport[sid]) for sid in ids}
        left_current = {
            branch_id: np.asarray(row["signed_current_density_A_m2_by_cell"], dtype=float)
            for row in mixed_left.values["state_history"][0]["reaction_branches"]
            for branch_id in (row["reaction_id"],)
        }
        current_guess = {branch_id: values.copy() for branch_id, values in left_current.items()}
        interval_history = []
        endpoint_converged = False
        endpoint_mixed = None
        endpoint_chemistry = None
        endpoint_state = None
        previous_chemistry_state = None
        dt = transport.output_time_s[interval + 1] - transport.output_time_s[interval]
        volumes = np.asarray(variable.cell_cross_section_area_m2_by_knot[interval + 1], dtype=float) \
            * (transport.length_m / nc)
        for iteration in range(1, request.maximum_right_endpoint_iterations + 1):
            source_moles = {sid: np.zeros(nc, dtype=float) for sid in ids}
            extent_by_branch = {}
            charge_source = np.zeros(nc, dtype=float)
            reservoir_delta = {element: 0.0 for element in initial_elements}
            for branch_id, fmap in branch_maps.items():
                branch = branch_template[branch_id]
                jbar = 0.5 * (left_current[branch_id] + current_guess[branch_id])
                area_reactive = np.asarray(transport.length_m / nc * request.mixed_potential_template.slit_width_m
                                           * request.mixed_potential_template.reactive_face_count, dtype=float)
                extent = jbar * area_reactive * dt / (branch.electron_number * FARADAY_CONSTANT_C_MOL)
                extent_by_branch[branch_id] = extent
                for species_id, coefficient in fmap.aqueous_species_stoichiometry_per_extent.items():
                    source_moles[species_id] += coefficient * extent
                charge_per_extent = math.fsum(
                    transport_species.charge_number * fmap.aqueous_species_stoichiometry_per_extent.get(transport_species.species_id, 0.0)
                    for transport_species in transport.species
                )
                charge_source += charge_per_extent * extent
                for element, coefficient in fmap.external_reservoir_element_stoichiometry_per_extent.items():
                    reservoir_delta[element] += coefficient * float(np.sum(extent))
            charge_limit = request.absolute_faradic_charge_source_tolerance_mol_eq_s * dt \
                + request.relative_faradic_charge_source_tolerance * max(float(np.max(np.abs(charge_source))), 1e-30)
            if float(np.max(np.abs(charge_source))) > charge_limit:
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                    "reason": "branch current to aqueous species source does not close local charge over the interval",
                    "faradaic_charge_inventory_residual_mol_eq_by_cell": charge_source.tolist(),
                    "accepted_interval_prefix": accepted_intervals,
                    "iteration_prefix": interval_history,
                    "committed": False,
                })
            post_faradic = {}
            for sid in ids:
                post_faradic[sid] = [base_endpoint[sid][cell] + source_moles[sid][cell] / volumes[cell]
                                     for cell in range(nc)]
                if any(value <= 0.0 or not math.isfinite(value) for value in post_faradic[sid]):
                    return Calculation(status="out_of_scope", values={
                        "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                        "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                        "reason": "Faradaic extent depletes or makes a declared aqueous species nonpositive",
                        "failed_species_id": sid, "accepted_interval_prefix": accepted_intervals,
                        "iteration_prefix": interval_history, "committed": False,
                    })
            try:
                chemistry_result, chemistry_state = _chemistry_at_knot(coupled, interval + 1, post_faradic, solids)
            except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError) as error:
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                    "reason": str(error), "accepted_interval_prefix": accepted_intervals,
                    "iteration_prefix": interval_history, "committed": False,
                })
            if chemistry_state is None:
                return Calculation(status=chemistry_result.status if hasattr(chemistry_result, "status") else "needs_data", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                    "failed_chemistry_result": chemistry_result.model_dump(mode="json")
                    if hasattr(chemistry_result, "model_dump") else chemistry_result,
                    "accepted_interval_prefix": accepted_intervals,
                    "iteration_prefix": interval_history, "committed": False,
                })
            try:
                mixed_result, mixed_request, _ = _mixed_potential_at_knot(
                    request, chemistry_state["concentration"], chemistry_state["gamma"], interval + 1
                )
            except (ValueError, KeyError, TypeError, ArithmeticError, OverflowError) as error:
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                    "reason": str(error), "accepted_interval_prefix": accepted_intervals,
                    "iteration_prefix": interval_history, "committed": False,
                })
            if mixed_result.status != "computed":
                return Calculation(status=mixed_result.status, values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                    "failed_mixed_potential": mixed_result.model_dump(mode="json"),
                    "accepted_interval_prefix": accepted_intervals,
                    "iteration_prefix": interval_history, "committed": False,
                })
            if mixed_result.values["maximum_absolute_cell_current_closure_residual_A"] > request.current_balance_tolerance_A:
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                    "reason": "mixed-potential cell current residual exceeds the coupling tolerance",
                    "maximum_absolute_cell_current_closure_residual_A": mixed_result.values["maximum_absolute_cell_current_closure_residual_A"],
                    "accepted_interval_prefix": accepted_intervals,
                    "iteration_prefix": interval_history, "committed": False,
                })
            face_current = mixed_result.values["state_history"][0]["electrolyte_face_current_A_by_cell_boundary"]
            if any(abs(value) > request.current_balance_tolerance_A for value in face_current):
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "failed_endpoint_iteration": iteration,
                    "reason": "nonzero mixed-potential electrolyte current cannot be reconciled with the reused zero-current NP flux kernel",
                    "electrolyte_face_current_A": face_current,
                    "accepted_interval_prefix": accepted_intervals,
                    "iteration_prefix": interval_history, "committed": False,
                })
            new_current = {
                row["reaction_id"]: np.asarray(row["signed_current_density_A_m2_by_cell"], dtype=float)
                for row in mixed_result.values["state_history"][0]["reaction_branches"]
            }
            max_residual = max(float(np.max(np.abs(new_current[key] - current_guess[key]))) for key in new_current)
            scale = max(1e-30, *(float(np.max(np.abs(value))) for value in new_current.values()))
            allowed = request.current_density_absolute_tolerance_A_m2 + request.current_relative_tolerance * scale
            chemistry_residual = math.inf
            if previous_chemistry_state is not None:
                c_now = chemistry_state["concentration"]
                c_prev = previous_chemistry_state["concentration"]
                s_now = chemistry_state["solids"]
                s_prev = previous_chemistry_state["solids"]
                c_scale = max(1e-30, *(abs(value) for values in c_now.values() for value in values))
                s_scale = max(1e-30, *(abs(value) for cell in s_now for value in cell.values()))
                chemistry_residual = max(
                    max(abs(c_now[sid][i] - c_prev[sid][i]) for sid in ids for i in range(nc)) / c_scale,
                    max(abs(s_now[i][phase] - s_prev[i][phase]) for i in range(nc) for phase in s_now[i]) / s_scale,
                )
            interval_history.append({
                "endpoint_iteration": iteration,
                "chemistry_input_sha256": canonical_digest(post_faradic),
                "chemistry_result_sha256": canonical_digest(chemistry_result.model_dump(mode="json")),
                "mixed_potential_input_sha256": canonical_digest(mixed_request.model_dump(mode="json")),
                "mixed_potential_result_sha256": canonical_digest(mixed_result.model_dump(mode="json")),
                "maximum_absolute_branch_current_residual_A_m2": max_residual,
                "allowed_branch_current_residual_A_m2": allowed,
                "maximum_relative_chemistry_state_residual": chemistry_residual if math.isfinite(chemistry_residual) else None,
                "allowed_relative_chemistry_state_residual": request.chemistry_state_relative_tolerance,
                "faradaic_charge_source_mol_eq_by_cell": charge_source.tolist(),
                "faradaic_extent_mol_by_branch_and_cell": {key: values.tolist() for key, values in extent_by_branch.items()},
            })
            total_mixed_evaluations += int(mixed_result.values["solver_function_evaluations"])
            if total_mixed_evaluations > request.maximum_total_mixed_potential_evaluations:
                return Calculation(status="out_of_scope", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                    "failed_interval_index": interval, "reason": "mixed-potential solver evaluation budget exceeded",
                    "accepted_interval_prefix": accepted_intervals, "iteration_prefix": interval_history,
                    "committed": False,
                })
            if max_residual <= allowed and chemistry_residual <= request.chemistry_state_relative_tolerance:
                endpoint_converged = True
                endpoint_mixed, endpoint_chemistry, endpoint_state = mixed_result, chemistry_result, chemistry_state
                accepted_extent = extent_by_branch
                accepted_reservoir_delta = reservoir_delta
                accepted_charge = charge_source
                break
            fraction = request.current_relaxation_fraction
            current_guess = {key: current_guess[key] + fraction * (new_current[key] - current_guess[key])
                             for key in new_current}
            previous_chemistry_state = chemistry_state
        if not endpoint_converged:
            return Calculation(status="out_of_scope", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval,
                "reason": "right-knot current/chemistry fixed point did not converge within the declared iteration budget",
                "accepted_interval_prefix": accepted_intervals,
                "iteration_prefix": interval_history, "committed": False,
            })
        # The knot solver includes reaction source and chemistry state. Verify total aqueous+solid+reservoir elements.
        new_total = _system_element_total(endpoint_state, coupled, interval + 1)
        mouth = tr_result.values["integrated_mouth_transfer_mol_by_species"]
        reaction_source = tr_result.values["integrated_reaction_source_mol_by_species"]
        species_by_id = {row.species_id: row for row in transport.species}
        for element in cumulative_transport_element_source:
            cumulative_transport_element_source[element] += math.fsum(
                species_by_id[sid].elemental_composition.get(element, 0)
                * (float(mouth[sid][-1]) + float(reaction_source[sid][-1])) for sid in ids
            )
            cumulative_reservoir[element] += accepted_reservoir_delta[element]
        element_residual = {element: new_total[element] - initial_elements[element]
                            - cumulative_transport_element_source[element] - cumulative_reservoir[element]
                            for element in initial_elements}
        total_scale = max(1e-30, *(abs(value) for value in new_total.values()),
                          *(abs(value) for value in initial_elements.values()))
        allowed_element = request.absolute_inventory_balance_tolerance_mol \
            + request.relative_inventory_balance_tolerance * total_scale
        if any(abs(value) > allowed_element for value in element_residual.values()):
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
                "failed_interval_index": interval,
                "reason": "Faradaic aqueous/solid/reservoir element ledger failed closure",
                "element_residual_mol_by_element": element_residual,
                "accepted_interval_prefix": accepted_intervals,
                "iteration_prefix": interval_history, "committed": False,
            })
        interval_record = {
            "interval_index": interval,
            "start_time_s": transport.output_time_s[interval],
            "end_time_s": transport.output_time_s[interval + 1],
            "transport_input_sha256": tr_result.values["input_sha256"],
            "transport_result_sha256": canonical_digest(tr_result.model_dump(mode="json")),
            "mixed_endpoint_input_sha256": canonical_digest(mixed_request.model_dump(mode="json")),
            "mixed_endpoint_result_sha256": canonical_digest(endpoint_mixed.model_dump(mode="json")),
            "chemistry_endpoint_result_sha256": canonical_digest(endpoint_chemistry.model_dump(mode="json")),
            "endpoint_fixed_point_iterations": len(interval_history),
            "faradaic_extent_mol_by_branch_and_cell": {key: values.tolist() for key, values in accepted_extent.items()},
            "faradaic_charge_source_residual_mol_eq_by_cell": accepted_charge.tolist(),
            "element_inventory_total_mol_by_element": new_total,
            "element_inventory_closure_residual_mol_by_element": element_residual,
            "allowed_element_inventory_residual_mol": allowed_element,
            "faradaic_charge_balance_verified": True,
            "endpoint_aqueous_concentration_mol_m3_by_species_and_cell": endpoint_state["concentration"],
            "endpoint_solid_inventory_mol_m3_by_cell": endpoint_state["solids"],
            "endpoint_chemistry_result": endpoint_chemistry.model_dump(mode="json"),
            "endpoint_mixed_potential_result": endpoint_mixed.model_dump(mode="json"),
            "maximum_absolute_cell_current_closure_residual_A": endpoint_mixed.values["maximum_absolute_cell_current_closure_residual_A"],
            "electrolyte_face_current_A_by_boundary": endpoint_mixed.values["state_history"][0]["electrolyte_face_current_A_by_cell_boundary"],
            "net_electrode_current_A_by_cell": endpoint_mixed.values["state_history"][0]["net_electrode_current_A_by_cell"],
            "branch_current_density_A_m2_by_id_and_cell": {
                row["reaction_id"]: row["signed_current_density_A_m2_by_cell"]
                for row in endpoint_mixed.values["state_history"][0]["reaction_branches"]
            },
            "committed": True,
        }
        accepted_intervals.append(interval_record)
        concentration, solids, gamma = endpoint_state["concentration"], endpoint_state["solids"], endpoint_state["gamma"]
        mixed_left = endpoint_mixed
        mixed_lineage.append({
            "knot_index": interval + 1,
            "input_sha256": interval_record["mixed_endpoint_input_sha256"],
            "result_sha256": interval_record["mixed_endpoint_result_sha256"],
        })
        total_transport_evaluations += interval_transport_evaluations

    return Calculation(values={
        "model_id": MODEL_ID,
        "status": "computed",
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "transport_chemistry_input_sha256": canonical_digest(coupled.model_dump(mode="json")),
        "mixed_potential_template_sha256": canonical_digest(request.mixed_potential_template.model_dump(mode="json")),
        "faradaic_branch_map_source_id": FARADAIC_MAP_SOURCE_ID,
        "nernst_source_id": NERNST_SOURCE_ID,
        "conductivity_source_id": CONDUCTIVITY_SOURCE_ID,
        "method_source_id": METHOD_SOURCE_ID,
        "committed_interval_count": len(accepted_intervals),
        "intervals": accepted_intervals,
        "mixed_potential_lineage": mixed_lineage,
        "transport_function_evaluations": total_transport_evaluations,
        "mixed_potential_function_evaluations": total_mixed_evaluations,
        "all_requested_intervals_committed": True,
        "qualification_claimed": False,
        "limitations": [
            "The existing transport kernel imposes zero ionic current at every face. Any mixed-potential solution with nonzero electrolyte face current is rejected; this API does not couple ohmic face current into Nernst-Planck migration.",
            "Transport is integrated first on the caller interval, then Faradaic branch extents are applied by endpoint trapezoid and local chemistry is re-solved. No capacitive/double-layer current or within-interval electrochemical integration is included.",
            "The caller supplies Butler-Volmer kinetics, branch stoichiometry, standard potentials, quotient coefficients, conductivity mapping and external element reservoir stoichiometry. No mechanism or chemistry is discovered.",
            "This is a computational screening coupling, not material qualification, corrosion-rate validation or integrity acceptance.",
        ],
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceFaradaicSpatialChemistryRequest,
        evaluator=solve_crevice_faradaic_spatial_chemistry,
        units={
            "intervals[].start_time_s": "s",
            "intervals[].end_time_s": "s",
            "intervals[].faradaic_extent_mol_by_branch_and_cell.*[]": "mol",
            "intervals[].net_electrode_current_A_by_cell[]": "A",
            "intervals[].branch_current_density_A_m2_by_id_and_cell.*[]": "A/m^2",
        },
        assumptions=(
            "Caller declares all branch kinetics, standard potentials, activity quotient coefficients, conductivity mappings, reaction stoichiometry and external element reservoirs.",
            "Transport is advanced first, Faradaic branch extents are applied by endpoint trapezoid, and the local caller chemistry is then re-solved at exact knots.",
            "The reused variable-area transport kernel requires zero ionic current at every face; any endpoint mixed-potential result with nonzero electrolyte face current is rejected.",
            "No double-layer current, intrastage chemistry/electrochemistry, automatic mechanism discovery or material qualification is included.",
        ),
        source_ids=(
            FARADAIC_MAP_SOURCE_ID,
            NERNST_SOURCE_ID,
            CONDUCTIVITY_SOURCE_ID,
            METHOD_SOURCE_ID,
        ),
        qualification="user_model",
    ),)
