"""Interval-wise operator split between aqueous component BDF and cell kinetics."""

from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_cellwise_nucleation_kinetic_history import (
    CreviceCellwiseNucleationKineticHistoryRequest,
    FixedKineticCell,
    compute_cell_order_sha256,
    evaluate_crevice_cellwise_nucleation_kinetic_history,
)
from .crevice_component_state_bdf import (
    ComponentInventoryByCell,
    CreviceComponentStateBDFRequest,
    solve_crevice_component_state_bdf,
)
from .crevice_nucleation_kinetic_history import (
    CreviceNucleationKineticHistoryRequest,
    NucleationSaturationInterval,
)
from .registry import ModelSpec

MODEL_ID = "integration.crevice_bdf_nucleation_operator_split"
SOURCE_ID = "caller_component_bdf_then_cellwise_seed_kinetic_operator_split"
INTERVAL_DERIVATION_SOURCE_ID = "exact_translation_of_absolute_saturation_interval_to_local_ledger_clock"


class CreviceBDFNucleationOperatorSplitRequest(Contract):
    """Run fixed-volume aqueous transport then cellwise nucleation per exact interval."""

    schema_version: Literal["matintegrity.crevice_bdf_nucleation_operator_split.v1"] = (
        "matintegrity.crevice_bdf_nucleation_operator_split.v1"
    )
    assessment_id: str = Field(min_length=1)
    bdf_request: CreviceComponentStateBDFRequest
    kinetic_cells: tuple[FixedKineticCell, ...] = Field(min_length=2, max_length=300)
    kinetic_cell_order_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    kinetic_cell_order_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    maximum_total_bdf_rhs_evaluations: int = Field(default=1_000_000, ge=2, le=20_000_000)
    maximum_total_stage_equilibrium_calls: int = Field(default=2_000_000, ge=2, le=40_000_000)
    maximum_total_nested_equilibrium_iteration_work: int = Field(default=100_000_000, ge=2, le=2_000_000_000)
    maximum_total_kinetic_ledger_evaluations: int = Field(default=2_000_000, ge=2, le=40_000_000)
    maximum_output_records: int = Field(default=2_000_000, ge=1, le=20_000_000)
    bdf_then_kinetics_split_order_reviewed: bool
    phase_component_projection_reviewed: bool
    fixed_geometry_and_volume_reviewed: bool
    no_external_sources_or_boundary_advection_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_split_contract(self):
        bdf = self.bdf_request
        nc = len(bdf.cells)
        if bdf.assessment_id != self.assessment_id:
            raise ValueError("operator split and component BDF assessment IDs must match exactly")
        kinetic_assessment_ids = tuple(cell.kinetic_history.assessment_id for cell in self.kinetic_cells)
        if (len(set(kinetic_assessment_ids)) != len(kinetic_assessment_ids)
                or any(not value.startswith(f"{self.assessment_id}:") for value in kinetic_assessment_ids)):
            raise ValueError("per-cell kinetic assessment IDs must be unique descendants of the operator split assessment")
        if tuple(row.cell_id for row in self.kinetic_cells) != tuple(row.cell_id for row in bdf.cells):
            raise ValueError("kinetic cells must exactly match BDF cell identity and order")
        if compute_cell_order_sha256(self.assessment_id,
                                    self.kinetic_cells[0].kinetic_history.physical_scope_id,
                                    self.kinetic_cells[0].kinetic_history.clock_id,
                                    self.kinetic_cells) != self.kinetic_cell_order_sha256:
            raise ValueError("kinetic cell-order digest does not match exact ordered cells and template histories")
        if not any(row.sha256 == self.kinetic_cell_order_sha256 for row in self.kinetic_cell_order_evidence):
            raise ValueError("kinetic cell-order Evidence must pin the exact order digest")
        if bdf.solid_equilibrium_mode != "aqueous_only":
            raise ValueError("operator split requires aqueous-only BDF; solid inventories are advanced by the kinetic ledger")
        if bdf.moving_geometry_mode != "fixed_volume":
            raise ValueError("operator split supports fixed geometry only")
        if (bdf.electrochemical_sources or bdf.ionic_face_current_schedule is not None
                or bdf.capacitive_current_schedule is not None or bdf.hydraulic_component_advection is not None
                or bdf.faradaic_stage_coupling is not None):
            raise ValueError("operator split rejects source/current/capacitive/hydraulic/Faradaic BDF schedules")
        if len(self.kinetic_cells) != nc:
            raise ValueError("one kinetic ledger template is required for every BDF cell")
        species_ids = tuple(row.species_id for row in bdf.cells[0].aqueous_activity_request.system.species)
        bdf_species = bdf.cells[0].aqueous_activity_request.system.species
        component_ids = tuple(row.component_id for row in bdf.initial_component_inventory)
        reference_kinetic = self.kinetic_cells[0].kinetic_history
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("BDF component IDs must be unique")
        initial_by_component = {row.component_id: row.inventory_mol_by_cell for row in bdf.initial_component_inventory}
        geometry_lengths = [float(row.cell_length_m) for row in self.kinetic_cells]
        geometry_areas = [float(row.cross_section_area_m2) for row in self.kinetic_cells]
        expected_center_distance = tuple(
            0.5 * (geometry_lengths[i] + geometry_lengths[i + 1]) for i in range(nc - 1)
        )
        expected_face_area = tuple(
            2.0 * geometry_areas[i] * geometry_areas[i + 1] / (geometry_areas[i] + geometry_areas[i + 1])
            for i in range(nc - 1)
        )
        for supplied, expected, label in (
            (bdf.center_distance_m_by_interior_face, expected_center_distance, "center-distance geometry"),
            (bdf.interior_face_area_m2, expected_face_area, "interior-face cross-section"),
        ):
            for actual_value, expected_value in zip(supplied, expected, strict=True):
                if not math.isclose(float(actual_value), expected_value, rel_tol=1e-8, abs_tol=1e-15):
                    raise ValueError(f"BDF {label} does not match the evidence-pinned fixed kinetic cell mesh")
        for cell_index, (bdf_cell, kinetic_cell) in enumerate(zip(bdf.cells, self.kinetic_cells, strict=True)):
            kinetic = kinetic_cell.kinetic_history
            if (kinetic.clock_id != reference_kinetic.clock_id
                    or kinetic.physical_scope_id != reference_kinetic.physical_scope_id):
                raise ValueError("all kinetic templates must share one physical scope and exact clock identity")
            if tuple(row.solid_species_id for row in kinetic.candidate_solid_phases) != tuple(
                row.solid_species_id for row in reference_kinetic.candidate_solid_phases
            ):
                raise ValueError("kinetic phase identities and order must match across cells")
            if tuple(row.model_dump(mode="json", exclude={"initial_solid_moles_per_solution_volume_mol_m3"})
                     for row in kinetic.candidate_solid_phases) != tuple(
                         row.model_dump(mode="json", exclude={"initial_solid_moles_per_solution_volume_mol_m3"})
                         for row in reference_kinetic.candidate_solid_phases
                     ):
                raise ValueError("cell kinetic phase stoichiometry, formula and source records must match")
            if (tuple(row.model_dump(mode="json") for row in kinetic.nucleation_laws)
                    != tuple(row.model_dump(mode="json") for row in reference_kinetic.nucleation_laws)
                    or tuple(row.model_dump(mode="json") for row in kinetic.growth_laws)
                    != tuple(row.model_dump(mode="json") for row in reference_kinetic.growth_laws)):
                raise ValueError("cell kinetic laws must be identical digest-bound records")
            if (kinetic.provider_id, kinetic.provider_revision, kinetic.kinetic_configuration_sha256,
                kinetic.kinetic_parameter_source_sha256) != (
                    reference_kinetic.provider_id, reference_kinetic.provider_revision,
                    reference_kinetic.kinetic_configuration_sha256,
                    reference_kinetic.kinetic_parameter_source_sha256,
                ):
                raise ValueError("cell kinetic provider and parameter lineage must match")
            if tuple(row.species_id for row in kinetic.aqueous_species) != species_ids:
                raise ValueError("kinetic species order must exactly match BDF equilibrium species order")
            if tuple((row.charge_number, row.elemental_composition) for row in kinetic.aqueous_species) != tuple(
                (row.charge_number, row.elemental_composition) for row in bdf_species
            ):
                raise ValueError("kinetic species charge and elemental composition must exactly match BDF chemistry")
            if tuple(row.model_dump(mode="json", exclude={"initial_concentration_mol_m3"})
                     for row in kinetic.aqueous_species) != tuple(
                         row.model_dump(mode="json", exclude={"initial_concentration_mol_m3"})
                         for row in reference_kinetic.aqueous_species
                     ):
                raise ValueError("cell kinetic species Evidence/source records must match")
            if kinetic.temperature_K != bdf_cell.aqueous_activity_request.system.temperature_K:
                raise ValueError("kinetic temperature must exactly match the fixed BDF cell temperature")
            volume_m3 = float(bdf_cell.solution_volume_L) / 1000.0
            if not math.isclose(float(kinetic_cell.solution_volume_m3), volume_m3, rel_tol=1e-10, abs_tol=1e-18):
                raise ValueError("kinetic fixed volume must match BDF cell solution volume")
            if len(kinetic.intervals) != len(bdf.time_s) - 1:
                raise ValueError("kinetic saturation interval count must equal BDF interval count")
            for interval_index, interval in enumerate(kinetic.intervals):
                if (interval.start_time_s, interval.end_time_s) != (bdf.time_s[interval_index], bdf.time_s[interval_index + 1]):
                    raise ValueError("each kinetic saturation record must match the exact absolute BDF interval")
            species_conc = {row.species_id: float(row.initial_concentration_mol_m3)
                            for row in kinetic.aqueous_species}
            initial_charge = math.fsum(float(row.charge_number) * species_conc[row.species_id]
                                       for row in kinetic.aqueous_species)
            charge_scale = math.fsum(abs(float(row.charge_number) * species_conc[row.species_id])
                                     for row in kinetic.aqueous_species)
            if abs(initial_charge) > kinetic.absolute_balance_tolerance_mol_m3 + kinetic.relative_balance_tolerance * max(charge_scale, 1e-30):
                raise ValueError("initial kinetic aqueous species must be charge neutral for the BDF equilibrium basis")
            for component_id in component_ids:
                component = next(row for row in bdf_cell.conserved_components if row.component_id == component_id)
                amount = math.fsum(float(term.coefficient) * species_conc[term.species_id]
                                   for term in component.species_coefficients) * volume_m3
                allowed = bdf.absolute_component_inventory_tolerance_mol + bdf.relative_component_closure_tolerance * max(
                    abs(amount), abs(float(initial_by_component[component_id][cell_index])), 1e-30
                )
                if abs(amount - float(initial_by_component[component_id][cell_index])) > allowed:
                    raise ValueError("initial kinetic aqueous species do not reconstruct the BDF component inventory")
        components = bdf.cells[0].conserved_components
        component_matrix = np.zeros((len(components), len(species_ids)), dtype=float)
        species_index = {species_id: i for i, species_id in enumerate(species_ids)}
        for row_index, component in enumerate(components):
            for term in component.species_coefficients:
                component_matrix[row_index, species_index[term.species_id]] = float(term.coefficient)
        elements = set().union(*(row.elemental_composition for row in self.kinetic_cells[0].kinetic_history.aqueous_species))
        for element in elements:
            element_vector = np.asarray([
                row.elemental_composition.get(element, 0)
                for row in self.kinetic_cells[0].kinetic_history.aqueous_species
            ], dtype=float)
            if np.linalg.matrix_rank(component_matrix) != np.linalg.matrix_rank(
                np.vstack((component_matrix, element_vector))
            ):
                raise ValueError(f"BDF conserved components cannot reconstruct elemental total {element!r}")
        phase_count = len(self.kinetic_cells[0].kinetic_history.candidate_solid_phases)
        expected_rows = (len(bdf.time_s) * nc * (len(species_ids) + phase_count)
                         + (len(bdf.time_s) - 1) * nc * phase_count)
        if expected_rows > self.maximum_output_records:
            raise ValueError("requested time × cell × species/phase output exceeds record budget")
        if not all((self.bdf_then_kinetics_split_order_reviewed,
                    self.phase_component_projection_reviewed,
                    self.fixed_geometry_and_volume_reviewed,
                    self.no_external_sources_or_boundary_advection_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("split order, component mapping, fixed geometry, boundary scope and use reviews are required")
        return self


def _derived_local_interval(request: CreviceNucleationKineticHistoryRequest, index: int):
    absolute = request.intervals[index]
    duration = float(absolute.end_time_s - absolute.start_time_s)
    payload = {
        "interval_id": f"{absolute.interval_id}:local-relative",
        "start_time_s": 0.0,
        "end_time_s": duration,
        "temperature_K": absolute.temperature_K,
        "saturation_ratio_by_phase": dict(absolute.saturation_ratio_by_phase),
    }
    derived_sha = canonical_digest(payload)
    source_rows = [row for row in absolute.evidence if row.sha256 == absolute.record_sha256]
    if not source_rows:
        raise ValueError("absolute saturation interval has no Evidence pin for its source digest")
    derived_evidence = tuple(Evidence(
        source_id=INTERVAL_DERIVATION_SOURCE_ID,
        origin="model_prediction",
        citation=(f"Exact local-clock translation of absolute interval {absolute.record_sha256}; "
                  f"offset={absolute.start_time_s} s, duration={duration} s"),
        license_id=row.license_id,
        sha256=derived_sha,
    ) for row in source_rows[:1])
    local = NucleationSaturationInterval.model_validate(payload | {
        "record_sha256": derived_sha,
        "evidence": derived_evidence,
    })
    return absolute, local, derived_sha


def _make_kinetic_cell(cell: FixedKineticCell, interval_index: int, species_concentration: dict[str, float],
                       solid_inventory: dict[str, float], ledger_budget: int) -> FixedKineticCell:
    template = cell.kinetic_history
    _absolute, local_interval, _derived_sha = _derived_local_interval(template, interval_index)
    original_evidence = list(template.evidence)
    original_evidence.extend(local_interval.evidence)
    species = tuple(row.model_copy(update={"initial_concentration_mol_m3": species_concentration[row.species_id]})
                    for row in template.aqueous_species)
    phases = tuple(row.model_copy(update={
        "initial_solid_moles_per_solution_volume_mol_m3": solid_inventory[row.solid_species_id]
    }) for row in template.candidate_solid_phases)
    local_payload = template.model_dump(mode="python")
    local_payload.update(
        assessment_id=f"{template.assessment_id}:split:{interval_index}",
        aqueous_species=species,
        candidate_solid_phases=phases,
        intervals=(local_interval,),
        evidence=tuple(original_evidence),
        maximum_total_ledger_evaluations=ledger_budget,
        maximum_interval_phase_updates=max(len(phases), template.maximum_interval_phase_updates),
    )
    local_request = CreviceNucleationKineticHistoryRequest.model_validate(local_payload)
    return FixedKineticCell.model_validate(cell.model_dump(mode="python") | {"kinetic_history": local_request})


def _component_moles_by_cell(bdf: CreviceComponentStateBDFRequest,
                             species_by_cell: list[dict[str, float]]) -> dict[str, tuple[float, ...]]:
    component_ids = tuple(row.component_id for row in bdf.initial_component_inventory)
    by_component: dict[str, list[float]] = {component_id: [] for component_id in component_ids}
    for cell, concentrations in zip(bdf.cells, species_by_cell, strict=True):
        volume_m3 = float(cell.solution_volume_L) / 1000.0
        for component_id in component_ids:
            component = next(row for row in cell.conserved_components if row.component_id == component_id)
            amount = math.fsum(float(term.coefficient) * concentrations[term.species_id]
                               for term in component.species_coefficients) * volume_m3
            if not math.isfinite(amount) or amount < -bdf.absolute_component_inventory_tolerance_mol:
                raise ArithmeticError(f"negative or nonfinite post-kinetic aqueous component inventory: {component_id}")
            by_component[component_id].append(max(0.0, amount))
    return {key: tuple(values) for key, values in by_component.items()}


def _spatial_amount_snapshot(cells: tuple[FixedKineticCell, ...],
                             aqueous_by_cell: list[dict[str, float]],
                             solids_by_cell: list[dict[str, float]]) -> dict[str, Any]:
    species_ids = tuple(row.species_id for row in cells[0].kinetic_history.aqueous_species)
    phase_ids = tuple(row.solid_species_id for row in cells[0].kinetic_history.candidate_solid_phases)
    species_moles = {species_id: [] for species_id in species_ids}
    phase_moles = {phase_id: [] for phase_id in phase_ids}
    elements: set[str] = set()
    charge_mol_eq = 0.0
    for cell, aqueous, solids in zip(cells, aqueous_by_cell, solids_by_cell, strict=True):
        volume = float(cell.solution_volume_m3)
        for species in cell.kinetic_history.aqueous_species:
            amount = float(aqueous[species.species_id]) * volume
            species_moles[species.species_id].append(amount)
            for element, coefficient in species.elemental_composition.items():
                elements.add(element)
            charge_mol_eq += float(species.charge_number) * amount
        for phase in cell.kinetic_history.candidate_solid_phases:
            phase_moles[phase.solid_species_id].append(float(solids[phase.solid_species_id]) * volume)
            elements.update(phase.solid_elemental_composition)
    element_moles = {element: 0.0 for element in elements}
    for cell, aqueous, solids in zip(cells, aqueous_by_cell, solids_by_cell, strict=True):
        volume = float(cell.solution_volume_m3)
        for species in cell.kinetic_history.aqueous_species:
            amount = float(aqueous[species.species_id]) * volume
            for element, coefficient in species.elemental_composition.items():
                element_moles[element] += float(coefficient) * amount
        for phase in cell.kinetic_history.candidate_solid_phases:
            amount = float(solids[phase.solid_species_id]) * volume
            for element, coefficient in phase.solid_elemental_composition.items():
                element_moles[element] += float(coefficient) * amount
    return {
        "aqueous_moles_by_species_and_cell": species_moles,
        "solid_moles_by_phase_and_cell": phase_moles,
        "element_moles_by_element": element_moles,
        "aqueous_charge_mol_eq": charge_mol_eq,
    }


def solve_crevice_bdf_nucleation_operator_split(
    request: CreviceBDFNucleationOperatorSplitRequest,
) -> Calculation:
    """Commit each fixed-geometry BDF interval and its cellwise kinetic ledger atomically."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = request.bdf_request
    original_bdf_digest = canonical_digest(base.model_dump(mode="json"))
    species_ids = tuple(row.species_id for row in base.cells[0].aqueous_activity_request.system.species)
    phase_ids = tuple(row.solid_species_id for row in request.kinetic_cells[0].kinetic_history.candidate_solid_phases)
    current_components = {
        row.component_id: tuple(float(value) for value in row.inventory_mol_by_cell)
        for row in base.initial_component_inventory
    }
    current_species = [
        {row.species_id: float(row.initial_concentration_mol_m3)
         for row in cell.kinetic_history.aqueous_species}
        for cell in request.kinetic_cells
    ]
    current_solids = [
        {row.solid_species_id: float(row.initial_solid_moles_per_solution_volume_mol_m3)
         for row in cell.kinetic_history.candidate_solid_phases}
        for cell in request.kinetic_cells
    ]
    initial_amounts = _spatial_amount_snapshot(request.kinetic_cells, current_species, current_solids)
    state_history = [{
        "absolute_time_s": float(base.time_s[0]),
        "state_basis": "caller_initial_kinetic_species_before_first_BDF_equilibrium_reconstruction",
        "aqueous_concentration_mol_m3_by_cell": current_species,
        "solid_inventory_mol_m3_by_cell": current_solids,
        **initial_amounts,
        "aqueous_component_moles_by_component_and_cell": {
            key: list(values) for key, values in current_components.items()
        },
    }]
    interval_history: list[dict[str, Any]] = []
    total_rhs = 0
    total_equilibrium = 0
    total_nested_work = 0
    total_kinetic_ledgers = 0
    max_component_closure_mol = 0.0
    max_charge_closure_mol_eq = 0.0

    def fail(interval_index: int, phase: str, reason: str, detail: dict[str, Any] | None = None,
             status: Literal["needs_data", "out_of_scope"] = "needs_data"):
        return Calculation(status=status, values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id, "input_sha256": digest,
            "failed_interval_index": interval_index, "failed_stage": phase, "reason": reason,
            "committed_interval_count": len(interval_history), "committed_state_history": state_history,
            "committed_interval_history": interval_history,
            "cumulative_work": {"bdf_rhs_evaluations": total_rhs,
                                "stage_equilibrium_calls": total_equilibrium,
                                "nested_equilibrium_iteration_work_bound": total_nested_work,
                                "kinetic_ledger_evaluations": total_kinetic_ledgers},
            "failed_stage_detail": detail or {}, "committed": False, "qualification_claimed": False,
        })

    for interval_index, (abs_start, abs_end) in enumerate(zip(base.time_s[:-1], base.time_s[1:], strict=True)):
        duration = float(abs_end - abs_start)
        if (request.maximum_total_bdf_rhs_evaluations - total_rhs < 1
                or request.maximum_total_stage_equilibrium_calls - total_equilibrium < len(base.cells)
                or request.maximum_total_nested_equilibrium_iteration_work - total_nested_work < 1
                or request.maximum_total_kinetic_ledger_evaluations - total_kinetic_ledgers < len(base.cells)):
            return fail(interval_index, "budget", "remaining aggregate work budget cannot start another interval")

        bdf_payload = base.model_dump(mode="python")
        bdf_payload.update(
            assessment_id=f"{base.assessment_id}:operator-split:{interval_index}",
            time_s=(0.0, duration),
            initial_component_inventory=tuple(ComponentInventoryByCell(
                component_id=component_id,
                inventory_mol_by_cell=values,
            ) for component_id, values in current_components.items()),
            maximum_total_rhs_evaluations=min(base.maximum_total_rhs_evaluations,
                                                request.maximum_total_bdf_rhs_evaluations - total_rhs),
            maximum_total_stage_equilibrium_calls=min(base.maximum_total_stage_equilibrium_calls,
                                                        request.maximum_total_stage_equilibrium_calls - total_equilibrium),
            maximum_total_nested_equilibrium_iteration_work=min(
                base.maximum_total_nested_equilibrium_iteration_work,
                request.maximum_total_nested_equilibrium_iteration_work - total_nested_work,
            ),
            maximum_total_ionic_current_face_evaluations=min(
                base.maximum_total_ionic_current_face_evaluations,
                max(len(base.cells) + 1,
                    (request.maximum_total_bdf_rhs_evaluations - total_rhs) * (len(base.cells) + 1)),
            ),
        )
        try:
            bdf_segment = CreviceComponentStateBDFRequest.model_validate(bdf_payload)
            bdf_result = solve_crevice_component_state_bdf(bdf_segment)
        except (ValueError, ArithmeticError, RuntimeError) as error:
            return fail(interval_index, "bdf_request", str(error))
        total_rhs += int(bdf_result.values.get("rhs_evaluations", 0))
        total_equilibrium += int(bdf_result.values.get("stage_equilibrium_calls", 0))
        total_nested_work += int(bdf_result.values.get("reserved_nested_equilibrium_iteration_work_bound", 0))
        if bdf_result.status != "computed" or not bdf_result.values.get("committed", False):
            return fail(interval_index, "bdf", str(bdf_result.values.get("reason", bdf_result.status)),
                        {"bdf_result": bdf_result.model_dump(mode="json")},
                        status="out_of_scope" if bdf_result.status == "out_of_scope" else "needs_data")
        if (total_rhs > request.maximum_total_bdf_rhs_evaluations
                or total_equilibrium > request.maximum_total_stage_equilibrium_calls
                or total_nested_work > request.maximum_total_nested_equilibrium_iteration_work):
            return fail(interval_index, "bdf_budget", "BDF segment exceeded aggregate work budget")

        bdf_species_field = bdf_result.values["species_concentration_mol_m3_by_species_time_cell"]
        transported_species = [
            {species_id: float(bdf_species_field[species_id][-1][cell_index]) for species_id in species_ids}
            for cell_index in range(len(base.cells))
        ]
        bdf_reconstructed_start_species = [
            {species_id: float(bdf_species_field[species_id][0][cell_index]) for species_id in species_ids}
            for cell_index in range(len(base.cells))
        ]
        species_reconstruction_delta_mol = {
            species_id: [
                (bdf_reconstructed_start_species[cell_index][species_id] - current_species[cell_index][species_id])
                * float(request.kinetic_cells[cell_index].solution_volume_m3)
                for cell_index in range(len(base.cells))
            ]
            for species_id in species_ids
        }
        post_bdf_amounts = _spatial_amount_snapshot(request.kinetic_cells, transported_species, current_solids)
        start_amounts = _spatial_amount_snapshot(request.kinetic_cells, current_species, current_solids)
        bdf_element_closure = {
            element: float(post_bdf_amounts["element_moles_by_element"].get(element, 0.0)
                           - start_amounts["element_moles_by_element"].get(element, 0.0))
            for element in set(post_bdf_amounts["element_moles_by_element"]) | set(start_amounts["element_moles_by_element"])
        }
        for element, residual in bdf_element_closure.items():
            allowed = base.absolute_component_closure_tolerance_mol + base.relative_component_closure_tolerance * max(
                abs(post_bdf_amounts["element_moles_by_element"].get(element, 0.0)),
                abs(start_amounts["element_moles_by_element"].get(element, 0.0)), 1e-30,
            )
            if abs(residual) > allowed:
                return fail(interval_index, "bdf_element_closure",
                            f"global closed-boundary transport changed elemental inventory {element}",
                            {"residual_mol": residual, "allowed_mol": allowed,
                             "bdf_result_sha256": canonical_digest(bdf_result.model_dump(mode="json"))})
        # Derive local-clock saturation records from exact absolute source records.
        kinetic_cells = []
        interval_kinetic_budget = min(
            20_000_000,
            request.maximum_total_kinetic_ledger_evaluations - total_kinetic_ledgers,
        )
        each_cell_budget = min(1_000_000, max(1, interval_kinetic_budget // len(request.kinetic_cells)))
        try:
            for cell_index, cell in enumerate(request.kinetic_cells):
                kinetic_cells.append(_make_kinetic_cell(
                    cell, interval_index, transported_species[cell_index], current_solids[cell_index], each_cell_budget
                ))
            kinetic_assessment_id = f"{request.assessment_id}:kinetic:{interval_index}"
            kinetic_scope_id = request.kinetic_cells[0].kinetic_history.physical_scope_id
            kinetic_clock_id = request.kinetic_cells[0].kinetic_history.clock_id
            order_sha = compute_cell_order_sha256(
                kinetic_assessment_id, kinetic_scope_id, kinetic_clock_id,
                tuple(kinetic_cells),
            )
            origin_interval = request.kinetic_cells[0].kinetic_history.intervals[interval_index]
            order_evidence = (Evidence(
                source_id=MODEL_ID, origin="model_prediction",
                citation=f"Per-interval cell order derived from orchestration input {digest}; original schedule {origin_interval.record_sha256}",
                sha256=order_sha,
            ),)
            kinetic_request = CreviceCellwiseNucleationKineticHistoryRequest.model_validate({
                "assessment_id": kinetic_assessment_id,
                "physical_scope_id": kinetic_scope_id,
                "clock_id": kinetic_clock_id,
                "cells": tuple(kinetic_cells),
                "cell_order_sha256": order_sha,
                "cell_order_evidence": order_evidence,
                "maximum_total_cell_time_phase_records": len(kinetic_cells) * len(phase_ids),
                "maximum_total_ledger_evaluations": interval_kinetic_budget,
                "independent_cell_batch_scope_reviewed": True,
                "no_intercell_transfer_during_kinetic_substep_reviewed": True,
                "fixed_cell_solution_volume_reviewed": True,
                "computational_use_authorized": request.computational_use_authorized,
            })
        except (ValueError, ArithmeticError, RuntimeError, KeyError) as error:
            return fail(interval_index, "kinetic_contract", str(error))
        kinetic_result = evaluate_crevice_cellwise_nucleation_kinetic_history(kinetic_request)
        ledger_count = int(kinetic_result.values.get("ledger_evaluation_count", 0))
        total_kinetic_ledgers += ledger_count
        if kinetic_result.status != "computed" or not kinetic_result.values.get("committed", False):
            return fail(interval_index, "kinetics", str(kinetic_result.values.get("reason", kinetic_result.status)),
                        {"kinetic_result": kinetic_result.model_dump(mode="json")},
                        status="out_of_scope" if kinetic_result.status == "out_of_scope" else "needs_data")
        if total_kinetic_ledgers > request.maximum_total_kinetic_ledger_evaluations:
            return fail(interval_index, "kinetic_budget", "cell ledgers exceeded aggregate kinetic budget")

        post_species = []
        post_solids = []
        absolute_seed_events = []
        for cell_result in kinetic_result.values["cell_results"]:
            source_cell = next(row for row in request.kinetic_cells if row.cell_id == cell_result["cell_id"])
            values = cell_result["kinetic_result"]["values"]
            final = values["history"][-1]
            post_species.append({key: float(value) for key, value in final["aqueous_concentration_mol_m3"].items()})
            post_solids.append({key: float(value) for key, value in final["solid_inventory_mol_m3"].items()})
            for knot in values["history"][1:]:
                for event in knot.get("seed_threshold_crossings", []):
                    local_event_time = float(event["absolute_crossing_time_s"])
                    absolute_seed_events.append({
                        "cell_id": cell_result["cell_id"],
                        "solid_species_id": event["phase_id"],
                        "local_event_time_s": local_event_time,
                        "absolute_event_time_s": float(abs_start) + local_event_time,
                        "absolute_saturation_record_sha256": source_cell.kinetic_history.intervals[
                            interval_index
                        ].record_sha256,
                        "ledger_verification_sha256": event["ledger_verification_sha256"],
                        "committed_crossing_result_sha256": event["committed_crossing_result_sha256"],
                    })
        post_kinetic_amounts = _spatial_amount_snapshot(request.kinetic_cells, post_species, post_solids)

        try:
            next_components = _component_moles_by_cell(base, post_species)
            bdf_end_components = {
                row["component_id"]: tuple(float(value) for value in row["inventory_mol_by_time_and_cell"][-1])
                for row in bdf_result.values["component_ledgers"]
            }
            solid_component_before = {key: [0.0] * len(base.cells) for key in bdf_end_components}
            solid_component_after = {key: [0.0] * len(base.cells) for key in bdf_end_components}
            for cell_index, cell in enumerate(request.kinetic_cells):
                kinetic_req = cell.kinetic_history
                cell_volume_m3 = float(cell.solution_volume_m3)
                for phase in kinetic_req.candidate_solid_phases:
                    for component_id in bdf_end_components:
                        component = next(row for row in base.cells[cell_index].conserved_components
                                         if row.component_id == component_id)
                        coefficient = math.fsum(
                            float(term.coefficient) * float(phase.precipitation_stoichiometry.get(term.species_id, 0.0))
                            for term in component.species_coefficients
                        )
                        solid_component_before[component_id][cell_index] += (
                            coefficient * float(current_solids[cell_index][phase.solid_species_id]) * cell_volume_m3
                        )
                        solid_component_after[component_id][cell_index] += (
                            coefficient * float(post_solids[cell_index][phase.solid_species_id]) * cell_volume_m3
                        )
            component_closure = {}
            for component_id in bdf_end_components:
                endpoint = next_components[component_id]
                bdf_endpoint = bdf_end_components[component_id]
                before_kinetic_total = [bdf_endpoint[i] + solid_component_before[component_id][i]
                                        for i in range(len(base.cells))]
                after_kinetic_total = [endpoint[i] + solid_component_after[component_id][i]
                                       for i in range(len(base.cells))]
                residual = [after_kinetic_total[i] - before_kinetic_total[i]
                            for i in range(len(base.cells))]
                allowed = [base.absolute_component_closure_tolerance_mol
                           + base.relative_component_closure_tolerance * max(
                               abs(after_kinetic_total[i]), abs(before_kinetic_total[i]), 1e-30
                           ) for i in range(len(base.cells))]
                if any(abs(residual[i]) > allowed[i] for i in range(len(residual))):
                    raise ArithmeticError(f"kinetic aqueous-plus-solid component closure failed for {component_id}")
                max_component_closure_mol = max(max_component_closure_mol,
                                                max((abs(value) for value in residual), default=0.0))
                component_closure[component_id] = {
                    "bdf_inventory_before_kinetics_mol_by_cell": list(bdf_endpoint),
                    "kinetic_aqueous_plus_solid_before_mol_by_cell": before_kinetic_total,
                    "kinetic_aqueous_plus_solid_after_mol_by_cell": after_kinetic_total,
                    "residual_mol_by_cell": residual,
                    "allowed_residual_mol_by_cell": allowed,
                    "global_residual_mol": math.fsum(residual),
                }
            # Existing kinetic ledgers expose exact element and charge residuals per cell.
            element_closure_mol = {}
            charge_closure_mol_eq = 0.0
            for cell_result, cell in zip(kinetic_result.values["cell_results"], request.kinetic_cells, strict=True):
                values = cell_result["kinetic_result"]["values"]
                vol = float(cell.solution_volume_m3)
                for interval_log in values["history"][1:]:
                    for segment in interval_log["segments"]:
                        for element, residual in segment["element_balance_residual_mol_m3"].items():
                            element_closure_mol[element] = max(element_closure_mol.get(element, 0.0),
                                                                abs(float(residual)) * vol)
                        charge_closure_mol_eq = max(
                            charge_closure_mol_eq,
                            abs(float(segment["charge_balance_residual_mol_charge_m3"])) * vol,
                        )
            kinetic_global_element_residual = {
                element: float(post_kinetic_amounts["element_moles_by_element"].get(element, 0.0)
                               - post_bdf_amounts["element_moles_by_element"].get(element, 0.0))
                for element in set(post_kinetic_amounts["element_moles_by_element"])
                | set(post_bdf_amounts["element_moles_by_element"])
            }
            absolute_tolerance = math.fsum(
                float(cell.kinetic_history.absolute_balance_tolerance_mol_m3)
                * float(cell.solution_volume_m3) for cell in request.kinetic_cells
            )
            relative_tolerance = max(float(cell.kinetic_history.relative_balance_tolerance)
                                     for cell in request.kinetic_cells)
            for element, residual in kinetic_global_element_residual.items():
                before_amount = float(post_bdf_amounts["element_moles_by_element"].get(element, 0.0))
                after_amount = float(post_kinetic_amounts["element_moles_by_element"].get(element, 0.0))
                allowed = absolute_tolerance + relative_tolerance * max(abs(before_amount), abs(after_amount), 1e-30)
                if abs(residual) > allowed:
                    raise ArithmeticError(f"global post-kinetic elemental inventory does not close for {element}")
            kinetic_global_charge_residual = float(
                post_kinetic_amounts["aqueous_charge_mol_eq"] - post_bdf_amounts["aqueous_charge_mol_eq"]
            )
            charge_allowed = absolute_tolerance + relative_tolerance * max(
                abs(float(post_bdf_amounts["aqueous_charge_mol_eq"])),
                abs(float(post_kinetic_amounts["aqueous_charge_mol_eq"])), 1e-30,
            )
            if abs(kinetic_global_charge_residual) > charge_allowed:
                raise ArithmeticError("global post-kinetic charge inventory does not close")
            max_charge_closure_mol_eq = max(max_charge_closure_mol_eq, abs(kinetic_global_charge_residual))
            max_charge_closure_mol_eq = max(max_charge_closure_mol_eq, charge_closure_mol_eq)
        except (ArithmeticError, KeyError, ValueError, TypeError) as error:
            return fail(interval_index, "closure", str(error), {
                "bdf_result_sha256": canonical_digest(bdf_result.model_dump(mode="json")),
                "kinetic_result_sha256": canonical_digest(kinetic_result.model_dump(mode="json")),
            })

        # Atomic interval commit after both models and closure checks succeed.
        current_components = next_components
        current_species = post_species
        current_solids = post_solids
        origin_rows = [row.kinetic_history.intervals[interval_index] for row in request.kinetic_cells]
        interval_history.append({
            "interval_index": interval_index,
            "absolute_start_time_s": float(abs_start),
            "absolute_end_time_s": float(abs_end),
            "duration_s": duration,
            "time_affine_map": {
                "local_start_time_s": 0.0,
                "local_end_time_s": duration,
                "absolute_time_s_from_local": "t_local + absolute_start_time_s",
                "absolute_start_time_s": float(abs_start),
            },
            "operator_order": ["aqueous_component_bdf", "cellwise_nucleation_kinetic_ledgers"],
            "saturation_source_sha256_by_cell": [row.record_sha256 for row in origin_rows],
            "local_interval_derivation_sha256_by_cell": [
                _derived_local_interval(row.kinetic_history, interval_index)[2] for row in request.kinetic_cells
            ],
            "bdf_input_sha256": bdf_result.values["input_sha256"],
            "original_bdf_request_sha256": original_bdf_digest,
            "bdf_result_sha256": canonical_digest(bdf_result.model_dump(mode="json")),
            "bdf_local_time_s": [0.0, duration],
            "bdf_input_original_absolute_interval": [float(abs_start), float(abs_end)],
            "bdf_species_reconstruction_at_interval_start_mol_m3_by_cell": bdf_reconstructed_start_species,
            "bdf_start_species_re_equilibration_delta_mol_by_species_and_cell": species_reconstruction_delta_mol,
            "amount_state_before_bdf": start_amounts,
            "amount_state_after_bdf_before_kinetics": post_bdf_amounts,
            "amount_state_after_kinetics": post_kinetic_amounts,
            "bdf_global_element_closure_residual_mol_by_element": bdf_element_closure,
            "bdf_component_ledgers": bdf_result.values["component_ledgers"],
            "bdf_element_ledgers": bdf_result.values.get("element_ledgers"),
            "bdf_rhs_evaluations": int(bdf_result.values.get("rhs_evaluations", 0)),
            "bdf_maximum_face_current_residual_A": float(bdf_result.values.get("maximum_face_current_residual_A", 0.0)),
            "bdf_stage_equilibrium_calls": int(bdf_result.values.get("stage_equilibrium_calls", 0)),
            "bdf_nested_equilibrium_iteration_work_bound": int(
                bdf_result.values.get("reserved_nested_equilibrium_iteration_work_bound", 0)
            ),
            "kinetic_input_sha256": kinetic_result.values["input_sha256"],
            "kinetic_result_sha256": canonical_digest(kinetic_result.model_dump(mode="json")),
            "kinetic_ledger_evaluations": ledger_count,
            "kinetic_seed_threshold_split_count": int(kinetic_result.values.get("seed_threshold_split_count", 0)),
            "seed_threshold_events_absolute_time": absolute_seed_events,
            "aqueous_plus_solid_component_closure": component_closure,
            "kinetic_element_closure_max_mol_by_element": element_closure_mol,
            "kinetic_global_element_inventory_residual_mol_by_element": kinetic_global_element_residual,
            "kinetic_global_charge_inventory_residual_mol_eq": kinetic_global_charge_residual,
            "kinetic_charge_closure_max_mol_eq": charge_closure_mol_eq,
            "committed": True,
        })
        state_history.append({
            "absolute_time_s": float(abs_end),
            "aqueous_concentration_mol_m3_by_cell": current_species,
            "solid_inventory_mol_m3_by_cell": current_solids,
            "aqueous_component_moles_by_component_and_cell": {
                key: list(values) for key, values in current_components.items()
            },
            **post_kinetic_amounts,
        })

    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "input_sha256": digest,
        "original_bdf_request_sha256": original_bdf_digest,
        "physical_scope_id": request.kinetic_cells[0].kinetic_history.physical_scope_id,
        "clock_id": request.kinetic_cells[0].kinetic_history.clock_id,
        "time_s": list(base.time_s),
        "state_history": state_history,
        "interval_ledgers": interval_history,
        "maximum_aqueous_plus_solid_component_closure_residual_mol": max_component_closure_mol,
        "maximum_kinetic_charge_closure_residual_mol_eq": max_charge_closure_mol_eq,
        "cumulative_work": {"bdf_rhs_evaluations": total_rhs,
                            "stage_equilibrium_calls": total_equilibrium,
                            "nested_equilibrium_iteration_work_bound": total_nested_work,
                            "kinetic_ledger_evaluations": total_kinetic_ledgers},
        "committed_interval_count": len(interval_history),
        "committed": True,
        "qualification_claimed": False,
        "operator_split_basis": "For each exact absolute interval, aqueous component BDF transport runs first. Its endpoint aqueous species concentrations feed a fixed-volume cellwise nucleation/growth ledger. The post-kinetic aqueous species are projected to conserved-component moles and carried to the next BDF interval; solid concentrations carry separately.",
        "limitations": [
            "BDF time is locally translated to [0, interval duration] because the existing nucleation history contract requires its own clock origin at zero. Exact absolute interval bounds and source digests are retained; derived local saturation record digests are emitted for each segment.",
            "Kinetics occur only after each completed BDF transport interval; there is no within-interval reaction/transport coupling.",
            "Fixed cell volumes and face geometry are required. Kinetic solids do not change aperture, area, porosity or BDF diffusivity.",
            "Only aqueous-only, no-source, zero-boundary-flux BDF requests are accepted; hydraulic, Faradaic, capacitive, prescribed-current and external source schedules fail closed.",
            "Phase and species networks, saturation ratios and kinetic laws remain caller supplied; no automatic chemistry discovery, qualification, corrosion rate, risk or life is inferred.",
        ],
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceBDFNucleationOperatorSplitRequest,
        evaluator=solve_crevice_bdf_nucleation_operator_split,
        units={
            "time_s[]": "s",
            "state_history[].aqueous_concentration_mol_m3_by_cell[][]": "mol/m^3",
            "state_history[].solid_inventory_mol_m3_by_cell[][]": "mol/m^3",
            "state_history[].aqueous_component_moles_by_component_and_cell.*[]": "mol",
            "maximum_aqueous_plus_solid_component_closure_residual_mol": "mol",
            "maximum_kinetic_charge_closure_residual_mol_eq": "mol_eq",
            "interval_ledgers[].absolute_start_time_s": "s",
            "interval_ledgers[].absolute_end_time_s": "s",
        },
        assumptions=(
            "Each original interval is operator split: aqueous-only fixed-volume component BDF first, cellwise seed/growth ledger second.",
            "Post-kinetic dissolved species are projected through explicit BDF conserved-component maps; solid phase amounts remain separately carried between intervals.",
            "Absolute caller saturation record digests are retained while the existing zero-origin batch ledger uses an exact relative-time translation per interval.",
            "No transport occurs during kinetic substeps and no geometry feedback is applied.",
        ),
        source_ids=(SOURCE_ID, INTERVAL_DERIVATION_SOURCE_ID,
                    "finite_volume_conserved_component_inventory_bdf_state",
                    "caller_fixed_volume_cellwise_seed_threshold_kinetic_ledgers"),
        version="0.1.0",
        qualification="user_model",
    ),)
