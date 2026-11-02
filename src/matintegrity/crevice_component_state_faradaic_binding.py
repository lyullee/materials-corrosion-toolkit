"""Bind exact-knot current-carrying CREVICE output to component-state BDF inputs.

This is a sequential, digest-bound adapter. It does not rerun mixed potential
inside the component-state BDF stages.
"""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, canonical_digest
from .crevice_component_state_bdf import (
    CALLER_IONIC_CURRENT_SOURCE_ID,
    CreviceComponentStateBDFRequest,
    ElectrochemicalSourceExtentSchedule,
    ElectrochemicalSourceReaction,
    ExternalReservoirComponentChange,
    ExternalReservoirElementChange,
    IonicFaceCurrentSchedule,
    FARADAY_CONSTANT_C_MOL,
)
from .crevice_current_carrying_np_faradaic import (
    MODEL_ID as CURRENT_CARRYING_MODEL_ID,
    CreviceCurrentCarryingNernstPlanckRequest,
)
from .crevice_faradaic_spatial_chemistry_coupling import CreviceFaradaicBranchMap
from .models.aqueous_mass_action import AqueousStoichiometricTerm
from .registry import ModelSpec

MODEL_ID = "integration.crevice_component_state_faradaic_schedule_binding"
METHOD_SOURCE_ID = "bound_crevice_current_carrying_result_to_component_state_schedules"


class CreviceCurrentCarryingCellBinding(Contract):
    component_cell_id: str = Field(min_length=1)
    producer_cell_index: int = Field(ge=0, le=299)


class CreviceCurrentCarryingComponentStateBinding(Contract):
    assessment_id: str = Field(min_length=1)
    component_state_request: CreviceComponentStateBDFRequest
    current_carrying_request: CreviceCurrentCarryingNernstPlanckRequest
    current_carrying_result: Calculation
    cell_bindings: tuple[CreviceCurrentCarryingCellBinding, ...] = Field(min_length=2, max_length=300)
    cell_order_and_physical_scope_reviewed: bool
    sequential_endpoint_current_reconstruction_reviewed: bool
    source_and_reservoir_mapping_reviewed: bool
    derived_current_schedule_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_binding(self):
        base = self.component_state_request
        producer = self.current_carrying_request
        transport = producer.faradaic_coupling.transport_chemistry.transport.transport_request
        component_cell_ids = tuple(row.cell_id for row in base.cells)
        producer_indices = tuple(row.producer_cell_index for row in self.cell_bindings)
        if tuple(row.component_cell_id for row in self.cell_bindings) != component_cell_ids:
            raise ValueError("cell bindings must exactly follow the component-state cell order")
        if producer_indices != tuple(range(transport.cell_count)):
            raise ValueError("the explicit cell binding must preserve producer left-to-right order")
        if len(self.cell_bindings) != transport.cell_count:
            raise ValueError("producer and component-state cell counts must match exactly")
        if base.time_s != tuple(transport.output_time_s):
            raise ValueError("producer and component-state exact time knots must match")
        if base.electrochemical_sources or base.ionic_face_current_schedule is not None:
            raise ValueError("binding adapter accepts a clean base request without prior source/current schedules")
        if base.maximum_absolute_source_extent_rate_mol_s is None:
            raise ValueError("the base request must set a finite source-rate ceiling before binding")
        if not (self.cell_order_and_physical_scope_reviewed
                and self.sequential_endpoint_current_reconstruction_reviewed
                and self.source_and_reservoir_mapping_reviewed
                and self.derived_current_schedule_reviewed
                and self.computational_use_authorized):
            raise ValueError("cell order, source/reservoir mapping, current schedule, sequential reconstruction, and use require review")
        if producer.faradaic_source_integration_mode == "bdf_stage_spatial_mixed_potential":
            raise ValueError("stage-re-solved mixed-potential currents cannot be reconstructed from endpoint knots")
        return self


def _component_inventory_mapping(
    request: CreviceComponentStateBDFRequest,
    producer: CreviceCurrentCarryingNernstPlanckRequest,
    cell_index: int,
) -> dict[str, float]:
    transport = producer.faradaic_coupling.transport_chemistry.transport.transport_request
    concentration = {row.species_id: row.initial_cell_concentration_mol_m3[cell_index]
                     for row in transport.species}
    inventory = {row.component_id: row.inventory_mol_by_cell[cell_index]
                 for row in request.initial_component_inventory}
    result: dict[str, float] = {}
    for component in request.cells[cell_index].conserved_components:
        expected = request.cells[cell_index].solution_volume_L / 1000.0 * math.fsum(
            term.coefficient * concentration[term.species_id]
            for term in component.species_coefficients
        )
        actual = inventory[component.component_id]
        tolerance = request.absolute_component_closure_tolerance_mol + \
            request.relative_component_closure_tolerance * max(abs(expected), abs(actual))
        if not math.isfinite(expected) or abs(expected - actual) > tolerance:
            raise ValueError(
                f"initial component inventory does not match producer aqueous state for "
                f"cell {request.cells[cell_index].cell_id}, component {component.component_id}"
            )
        result[component.component_id] = expected
    return result


def bind_crevice_current_carrying_result_to_component_state_bdf(
    binding: CreviceCurrentCarryingComponentStateBinding,
) -> CreviceComponentStateBDFRequest:
    """Build review-gated component-state schedules from an exact-knot computed result."""
    producer = binding.current_carrying_request
    output = binding.current_carrying_result
    base = binding.component_state_request
    if output.status != "computed":
        raise ValueError("only a fully computed current-carrying result may be bound")
    expected_input_digest = canonical_digest(producer.model_dump(mode="json"))
    if output.values.get("model_id") != CURRENT_CARRYING_MODEL_ID:
        raise ValueError("producer result model identity mismatch")
    if output.values.get("input_sha256") != expected_input_digest:
        raise ValueError("producer result input digest does not match the supplied request")
    if output.values.get("all_requested_intervals_committed") is not True:
        raise ValueError("producer result does not commit every requested interval")
    if output.values.get("exact_knot_current_time_s") != list(base.time_s):
        raise ValueError("producer output lacks a matching exact-knot current history")

    faradaic = producer.faradaic_coupling
    transport = faradaic.transport_chemistry.transport.transport_request
    species = {row.species_id: row for row in transport.species}
    template_species = base.cells[0].aqueous_activity_request.system.species
    if tuple((row.species_id, row.charge_number) for row in template_species) != tuple(
        (row.species_id, row.charge_number) for row in transport.species
    ):
        raise ValueError("producer and component-state species identities/order/charges must match")
    for cell_index in range(transport.cell_count):
        _component_inventory_mapping(base, producer, cell_index)

    current_history = output.values.get("exact_knot_ionic_face_current_A_by_boundary")
    branch_history = output.values.get("exact_knot_branch_current_density_A_m2_by_branch_and_cell")
    times = tuple(base.time_s)
    nc, nt = len(base.cells), len(times)
    if not isinstance(current_history, list) or len(current_history) != nt:
        raise ValueError("producer result has an incomplete ionic-current knot history")
    if any(not isinstance(row, list) or len(row) != nc + 1
           or any(not math.isfinite(float(value)) for value in row) for row in current_history):
        raise ValueError("producer ionic-current knot history has invalid face shape or values")
    branch_maps: tuple[CreviceFaradaicBranchMap, ...] = faradaic.faradaic_branch_maps
    branch_ids = tuple(row.reaction_id for row in branch_maps)
    if not isinstance(branch_history, dict) or set(branch_history) != set(branch_ids):
        raise ValueError("producer branch-current history does not exactly match Faradaic branch identities")
    template = faradaic.mixed_potential_template
    reactive_area_m2 = transport.length_m / nc * template.slit_width_m * template.reactive_face_count
    element_ids = sorted(set().union(*(row.elemental_composition.keys() for row in species.values())))
    component_coefficients = {
        component.component_id: {term.species_id: term.coefficient for term in component.species_coefficients}
        for component in base.cells[0].conserved_components
    }
    extent_schedules = []
    max_rate = float(base.maximum_absolute_source_extent_rate_mol_s)
    for branch in branch_maps:
        values = branch_history[branch.reaction_id]
        if not isinstance(values, list) or len(values) != nt or any(
            not isinstance(row, list) or len(row) != nc
            or any(not math.isfinite(float(value)) for value in row)
            for row in values
        ):
            raise ValueError(f"producer branch-current history is malformed for {branch.reaction_id}")
        rates = tuple(tuple(
            float(current_density) * reactive_area_m2
            / (branch.electron_number * FARADAY_CONSTANT_C_MOL)
            for current_density in knot_values
        ) for knot_values in values)
        if any(abs(rate) > max_rate for row in rates for rate in row):
            raise ValueError(f"branch extent rate exceeds the base request ceiling for {branch.reaction_id}")
        stoich = branch.aqueous_species_stoichiometry_per_extent
        charge_delta = math.fsum(species[sid].charge_number * coefficient
                                 for sid, coefficient in stoich.items())
        reservoir_components = tuple(
            ExternalReservoirComponentChange(
                component_id=component_id,
                reservoir_change_mol_per_extent=-math.fsum(
                    coefficient * stoich.get(sid, 0.0) for sid, coefficient in coefficients.items()
                ),
            )
            for component_id, coefficients in component_coefficients.items()
        )
        reservoir_elements = tuple(
            ExternalReservoirElementChange(
                element_id=element,
                reservoir_change_mol_per_extent=branch.external_reservoir_element_stoichiometry_per_extent.get(
                    element, 0.0
                ),
            )
            for element in element_ids
        )
        reaction = ElectrochemicalSourceReaction(
            reaction_id=branch.reaction_id,
            aqueous_species_stoichiometry=tuple(
                AqueousStoichiometricTerm(species_id=sid, coefficient=coefficient)
                for sid, coefficient in stoich.items()
            ),
            external_reservoir_element_change=reservoir_elements,
            external_reservoir_component_change=reservoir_components,
            external_reservoir_charge_change_mol_eq_per_extent=-charge_delta,
            evidence=branch.evidence,
        )
        extent_schedules.append(ElectrochemicalSourceExtentSchedule(
            reaction=reaction,
            extent_rate_mol_s_by_knot_and_cell=rates,
        ))

    derived_schedule_digest = canonical_digest({
        "producer_input_sha256": expected_input_digest,
        "producer_result_sha256": canonical_digest(output.model_dump(mode="json")),
        "time_s": times,
        "ionic_face_current_A_by_boundary": current_history,
        "branch_current_density_A_m2_by_branch_and_cell": branch_history,
        "cell_bindings": [row.model_dump(mode="json") for row in binding.cell_bindings],
    })
    derived_evidence = Evidence(
        source_id=METHOD_SOURCE_ID,
        origin="model_prediction",
        citation=(f"Derived exact-knot schedules from computed {CURRENT_CARRYING_MODEL_ID} result; assessment {binding.assessment_id}."),
        sha256=derived_schedule_digest,
    )
    caller_current_evidence = Evidence(
        source_id=CALLER_IONIC_CURRENT_SOURCE_ID,
        origin="model_prediction",
        citation=f"Caller reviewed derived face-current history; producer input digest {expected_input_digest}.",
        sha256=derived_schedule_digest,
    )
    schedule = IonicFaceCurrentSchedule(
        time_s=times,
        current_A_by_knot_and_face=tuple(tuple(float(value) for value in row) for row in current_history),
        evidence=(caller_current_evidence, derived_evidence),
    )
    payload = base.model_dump(mode="json")
    payload["electrochemical_sources"] = [row.model_dump(mode="json") for row in extent_schedules]
    payload["ionic_face_current_schedule"] = schedule.model_dump(mode="json")
    payload["electrochemical_source_stoichiometry_and_reservoir_reviewed"] = True
    payload["ionic_face_current_schedule_reviewed"] = True
    return CreviceComponentStateBDFRequest.model_validate(payload)


def evaluate_crevice_current_carrying_component_state_binding(
    binding: CreviceCurrentCarryingComponentStateBinding,
) -> Calculation:
    digest = canonical_digest(binding.model_dump(mode="json"))
    try:
        request = bind_crevice_current_carrying_result_to_component_state_bdf(binding)
    except (ArithmeticError, KeyError, TypeError, ValueError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID,
            "assessment_id": binding.assessment_id,
            "input_sha256": digest,
            "reason": str(error),
            "committed": False,
            "qualification_claimed": False,
        })
    request_digest = canonical_digest(request.model_dump(mode="json"))
    return Calculation(values={
        "model_id": MODEL_ID,
        "assessment_id": binding.assessment_id,
        "input_sha256": digest,
        "component_state_request": request.model_dump(mode="json"),
        "component_state_request_sha256": request_digest,
        "producer_input_sha256": binding.current_carrying_result.values["input_sha256"],
        "producer_model_id": binding.current_carrying_result.values["model_id"],
        "current_schedule_sha256": canonical_digest(request.ionic_face_current_schedule.model_dump(mode="json")),
        "source_schedule_sha256_by_reaction": {
            row.reaction.reaction_id: canonical_digest(row.model_dump(mode="json"))
            for row in request.electrochemical_sources
        },
        "composition_and_kinetics_are_sequential_not_monolithic": True,
        "qualification_claimed": False,
        "limitations": [
            "The adapter converts exact-knot branch current-density histories into caller-prescribed component-state source-rate schedules.",
            "It does not re-solve mixed potential from component-state BDF stage chemistry; the existing stage-re-solved mixed-potential producer mode is rejected.",
            "Cell volume, geometry and scope must match by caller review; hydraulic aperture evolution, solids and variable volume are not added.",
        ],
    })


def specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceCurrentCarryingComponentStateBinding,
        evaluator=evaluate_crevice_current_carrying_component_state_binding,
        units={
            "current_carrying_result.values.exact_knot_ionic_face_current_A_by_boundary[][]": "A",
            "current_carrying_result.values.exact_knot_branch_current_density_A_m2_by_branch_and_cell.*[][]": "A/m^2",
            "component_state_request.electrochemical_sources[].extent_rate_mol_s_by_knot_and_cell[][]": "mol/s",
            "component_state_request.ionic_face_current_schedule.current_A_by_knot_and_face[][]": "A",
        },
        assumptions=(
            "Producer and component-state time knots, species order/charge, cell order and initial conserved inventories must match.",
            "Exact-knot current density is converted to extent rate using the producer's declared per-cell reactive area and electron number.",
            "The resulting current and extent schedules are linearly reconstructed between exact knots; no stage mixed-potential feedback is implied.",
            "Caller source, reservoir, current, cell mapping and computational-use reviews are mandatory.",
        ),
        source_ids=(METHOD_SOURCE_ID, CALLER_IONIC_CURRENT_SOURCE_ID, "nist_codata_faraday_constant_2022"),
        qualification="user_model",
    ),)
