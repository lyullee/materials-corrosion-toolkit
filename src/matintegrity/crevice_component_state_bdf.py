"""Component-inventory BDF transport with local caller-evidenced aqueous equilibrium.

This isolated child solver evolves conserved component moles, not aqueous species
moles. Nernst–Planck species face fluxes are projected through explicit component
maps; each BDF RHS reconstructs local aqueous equilibrium at the trial totals.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from typing import Literal
from types import SimpleNamespace

import numpy as np
from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .crevice_aqueous_component_ledger import (
    ConservedAqueousComponent,
    ConstraintRoleAssignment,
)
from .crevice_competing_solid_equilibrium import CreviceCompetingSolidPhase
from .crevice_bdf_kinetic_phase_set import CreviceBDFKineticPhaseSet
from .crevice_stage_kinetic_rates import trial_phase_rate_mol_s, trial_saturation_ratio
from .crevice_coupled_seed_bdf import integrate_coupled_seed_bdf
from .crevice_faradaic_spatial_chemistry_coupling import CreviceFaradaicSpatialChemistryRequest
from .crevice_current_carrying_np_faradaic import _solve_spatial_mixed_potential_at_stage
from .crevice_spatial_chemistry_transport import _subinterval_request
from .crevice_hydraulic_component_advection import (
    CreviceHydraulicComponentAdvection,
    component_advection_face_rates_mol_s,
    boundary_advection_reservoir_rates,
)
from .crevice_dynamic_hydraulic_advection import (
    CreviceDynamicHydraulicAdvection,
    SOURCE_ID as DYNAMIC_HYDRAULIC_SOURCE_ID,
    evaluate_dynamic_hydraulic_advection_stage,
)
from .models.aqueous_activity_iteration import (
    AqueousDaviesIteration,
    aqueous_davies_self_consistent_speciation,
)
from .crevice_spatial_ohmic_mixed_potential import (
    FARADAY_CONSTANT_C_MOL,
    GAS_CONSTANT_J_MOL_K,
    _branch_current_density,
)
from .crevice_dynamic_double_layer_faradaic_history import (
    _integrated_capacitance_charge,
)
from .models.aqueous_mass_action import AqueousStoichiometricTerm
from .registry import ModelSpec

MODEL_ID = "integration.crevice_component_state_bdf"
COMPONENT_STATE_SOURCE_ID = "finite_volume_conserved_component_inventory_bdf_state"
STAGE_EQUILIBRIUM_SOURCE_ID = "caller_evidenced_cellwise_davies_mass_action_at_bdf_stages"
ELECTRONEUTRAL_NP_SOURCE_ID = "electroneutral_nernst_planck_species_flux_projected_to_components"
CALLER_ELECTROCHEMICAL_SOURCE_ID = "caller_evidenced_component_source_extent_schedule"
CALLER_IONIC_CURRENT_SOURCE_ID = "caller_evidenced_ionic_face_current_schedule"
CALLER_CAPACITIVE_CURRENT_SOURCE_ID = "caller_evidenced_double_layer_capacitive_current_schedule"
DERIVED_DYNAMIC_CAPACITIVE_CURRENT_SOURCE_ID = "integration.crevice_dynamic_double_layer_to_component_bdf_binding"
DYNAMIC_DOUBLE_LAYER_BDF_SOURCE_ID = "same_stage_component_bdf_dynamic_double_layer_spatial_ohmic_faradaic_feedback"
DYNAMIC_DOUBLE_LAYER_INITIAL_STATE_SOURCE_ID = "caller_evidenced_initial_crevice_double_layer_interfacial_state"
STAGE_SPATIAL_MIXED_POTENTIAL_SOURCE_ID = "component_state_bdf_stage_spatial_ohmic_butler_volmer_faradaic_coupling"
SCHEDULE_BINDING_SOURCE_ID = "bound_crevice_current_carrying_result_to_component_state_schedules"
STAGE_SOLID_PARTITION_SOURCE_ID = "component_state_bdf_stage_total_component_solid_equilibrium_partition"
CALLER_HYDRAULIC_ADVECTION_SOURCE_ID = "caller_digest_bound_planar_slit_inertance_upwind_component_advection"


class CellSolidPhaseSet(Contract):
    """One stationary, digest-bound phase set for a cell over the exact BDF horizon."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    cell_id: str = Field(min_length=1)
    phase_set_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    valid_time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    temperature_K: Positive
    activity_standard_state_id: Literal["dimensionless_molarity_1_mol_L"] = "dimensionless_molarity_1_mol_L"
    phase_candidates: tuple[CreviceCompetingSolidPhase, ...] = Field(min_length=1, max_length=12)
    phase_set_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    phase_set_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_phase_set_digest(self):
        phase_ids = [row.solid_species_id for row in self.phase_candidates]
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("cell solid phase candidate IDs must be unique")
        payload = self.model_dump(mode="json", exclude={"phase_set_sha256", "phase_set_evidence"})
        if canonical_digest(payload) != self.phase_set_sha256:
            raise ValueError("cell phase-set digest must bind cell/material/environment/time and phase records")
        if not any(row.sha256 == self.phase_set_sha256 for row in self.phase_set_evidence):
            raise ValueError("phase-set Evidence must pin its exact phase-set digest")
        return self


class SolidPhaseGeometryMap(Contract):
    solid_species_id: str = Field(min_length=1)
    molar_volume_m3_mol: Positive
    occupies_gap: bool


class CellDynamicSolidGeometry(Contract):
    """Caller-evidenced cell dimensions and phase-to-gap volume mapping."""

    cell_id: str = Field(min_length=1)
    cell_length_m: Positive
    transverse_width_m: Positive
    initial_aperture_m: Positive
    minimum_aperture_m: Positive
    phase_geometry: tuple[SolidPhaseGeometryMap, ...] = Field(min_length=1, max_length=12)
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_source_id: str = Field(min_length=1)
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_geometry_digest(self):
        phase_ids = tuple(row.solid_species_id for row in self.phase_geometry)
        if len(set(phase_ids)) != len(phase_ids):
            raise ValueError("dynamic geometry phase IDs must be unique and ordered")
        payload = {
            "cell_id": self.cell_id,
            "cell_length_m": float(self.cell_length_m),
            "transverse_width_m": float(self.transverse_width_m),
            "initial_aperture_m": float(self.initial_aperture_m),
            "minimum_aperture_m": float(self.minimum_aperture_m),
            "phase_geometry": [row.model_dump(mode="json") for row in self.phase_geometry],
        }
        if canonical_digest(payload) != self.geometry_sha256 or not any(
            evidence.source_id == self.geometry_source_id and evidence.sha256 == self.geometry_sha256
            for evidence in self.geometry_evidence
        ):
            raise ValueError("dynamic geometry Evidence must pin the complete cell/phase mapping digest")
        if self.minimum_aperture_m >= self.initial_aperture_m:
            raise ValueError("minimum aperture must be strictly below the initial aperture")
        return self


class CellAqueousEquilibriumTemplate(Contract):
    cell_id: str = Field(min_length=1)
    solution_volume_L: Positive
    aqueous_activity_request: AqueousDaviesIteration
    constraint_roles: tuple[ConstraintRoleAssignment, ...] = Field(min_length=1, max_length=100)
    conserved_components: tuple[ConservedAqueousComponent, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_local_component_basis(self):
        system = self.aqueous_activity_request.system
        species_ids = {row.species_id for row in system.species}
        constraints = {row.constraint_id: row for row in system.constraints}
        if any(not math.isfinite(row.target_mol_L)
               or any(not math.isfinite(term.coefficient) for term in row.terms)
               for row in system.constraints):
            raise ValueError("cell constraint targets and coefficients must be finite")
        if any(not math.isfinite(term.coefficient)
               for reaction in system.reactions for term in reaction.terms):
            raise ValueError("cell reaction coefficients must be finite")
        roles = {row.constraint_id: row for row in self.constraint_roles}
        if len(roles) != len(self.constraint_roles) or set(roles) != set(constraints):
            raise ValueError("cell chemistry roles must cover every declared constraint exactly once")
        components = {row.component_id: row for row in self.conserved_components}
        if len(components) != len(self.conserved_components):
            raise ValueError("cell conserved component IDs must be unique")
        component_roles = [row for row in self.constraint_roles if row.role == "conserved_component"]
        if ({row.component_id for row in component_roles} != set(components)
                or len(component_roles) != len(components)):
            raise ValueError("each cell component must map one-to-one to a conserved component constraint")
        charge_roles = [row for row in self.constraint_roles if row.role == "charge_neutrality"]
        if len(charge_roles) != 1:
            raise ValueError("each cell requires exactly one charge-neutrality constraint")
        charge = constraints[charge_roles[0].constraint_id]
        expected_charge = {row.species_id: row.charge_number for row in system.species if row.charge_number != 0}
        if ({term.species_id: term.coefficient for term in charge.terms} != expected_charge
                or charge.target_mol_L != 0.0):
            raise ValueError("cell charge row must exactly match species charges and have a zero target")
        for assignment in component_roles:
            component = components[assignment.component_id]
            component_map = {row.species_id: row.coefficient for row in component.species_coefficients}
            constraint_map = {term.species_id: term.coefficient for term in constraints[assignment.constraint_id].terms}
            if component_map.keys() - species_ids or component_map != constraint_map:
                raise ValueError("cell component map must exactly match its constraint coefficient row")
            for reaction in system.reactions:
                reaction_terms = {term.species_id: term.coefficient for term in reaction.terms}
                residual = math.fsum(component_map.get(sid, 0.0) * coefficient
                                     for sid, coefficient in reaction_terms.items())
                scale = max(1.0, math.fsum(abs(component_map.get(sid, 0.0) * coefficient)
                                          for sid, coefficient in reaction_terms.items()))
                if not math.isfinite(residual) or abs(residual) > 1e-12 * scale:
                    raise ValueError(f"reaction {reaction.reaction_id} does not conserve {component.component_id}")
        return self


class ComponentInventoryByCell(Contract):
    component_id: str = Field(min_length=1)
    inventory_mol_by_cell: tuple[float, ...] = Field(min_length=1, max_length=300)


class SpeciesFaceDiffusivity(Contract):
    species_id: str = Field(min_length=1)
    diffusivity_m2_s_by_interior_face: tuple[Positive, ...] = Field(min_length=1, max_length=299)


class ExternalReservoirElementChange(Contract):
    element_id: str = Field(min_length=1)
    reservoir_change_mol_per_extent: float


class ExternalReservoirComponentChange(Contract):
    component_id: str = Field(min_length=1)
    reservoir_change_mol_per_extent: float


class ElectrochemicalSourceReaction(Contract):
    reaction_id: str = Field(min_length=1)
    aqueous_species_stoichiometry: tuple[AqueousStoichiometricTerm, ...] = Field(min_length=1, max_length=100)
    external_reservoir_element_change: tuple[ExternalReservoirElementChange, ...] = Field(min_length=1, max_length=100)
    external_reservoir_component_change: tuple[ExternalReservoirComponentChange, ...] = Field(min_length=1, max_length=100)
    external_reservoir_charge_change_mol_eq_per_extent: float
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ElectrochemicalSourceExtentSchedule(Contract):
    reaction: ElectrochemicalSourceReaction
    # Knot-major; each knot row contains one signed extent rate per cell.
    extent_rate_mol_s_by_knot_and_cell: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)


class IonicFaceCurrentSchedule(Contract):
    time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    # Knot-major; each row contains ncell + 1 signed currents, positive left-to-right.
    current_A_by_knot_and_face: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CapacitiveCellCurrentSchedule(Contract):
    """Caller-supplied double-layer current density integrated as charge source per cell.

    Positive current is defined into the aqueous phase from the interface. This is
    an explicit forcing schedule, not a potential state or constitutive capacitor law.
    """

    time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    current_A_by_knot_and_cell: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    schedule_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_capacitive_current_schedule(self):
        if any(not math.isfinite(value) or value < 0 for value in self.time_s):
            raise ValueError("capacitive-current times must be finite and nonnegative")
        if self.time_s[0] != 0.0 or any(b <= a for a, b in zip(self.time_s[:-1], self.time_s[1:], strict=True)):
            raise ValueError("capacitive-current times must begin at zero and increase strictly")
        if len(self.current_A_by_knot_and_cell) != len(self.time_s) or not self.current_A_by_knot_and_cell:
            raise ValueError("capacitive current must have a row at every exact time knot")
        cell_count = len(self.current_A_by_knot_and_cell[0])
        if cell_count < 2 or any(len(row) != cell_count for row in self.current_A_by_knot_and_cell):
            raise ValueError("capacitive current must provide the same per-cell layout at every knot")
        if any(not math.isfinite(value) for row in self.current_A_by_knot_and_cell for value in row):
            raise ValueError("capacitive current values must be finite")
        record = {"time_s": list(self.time_s),
                  "current_A_by_knot_and_cell": [list(row) for row in self.current_A_by_knot_and_cell]}
        if canonical_digest(record) != self.schedule_sha256:
            raise ValueError("capacitive-current digest must bind exact ordered time and cell values")
        if not any(row.sha256 == self.schedule_sha256
                   and row.source_id in (CALLER_CAPACITIVE_CURRENT_SOURCE_ID,
                                         DERIVED_DYNAMIC_CAPACITIVE_CURRENT_SOURCE_ID)
                   and row.license_id
                   for row in self.evidence):
            raise ValueError("capacitive-current Evidence must identify its licensed exact schedule digest")
        return self


class CreviceBDFDoubleLayerCapacitance(Contract):
    """Caller-evidenced differential Cdl curve and per-cell initial interfacial state."""

    cell_ids: tuple[str, ...] = Field(min_length=2, max_length=300)
    initial_interfacial_potential_V_by_cell: tuple[float, ...] = Field(min_length=2, max_length=300)
    reference_interfacial_potential_V_by_cell: tuple[float, ...] = Field(min_length=2, max_length=300)
    differential_capacitance_potential_axis_V: tuple[float, ...] = Field(min_length=2, max_length=2000)
    differential_capacitance_F_m2: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    capacitance_curve_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    capacitance_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    initial_state_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    initial_state_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    initial_state_and_reference_reviewed: bool
    differential_curve_interpretation_reviewed: bool
    closed_electrolyte_boundary_and_charge_sign_reviewed: bool
    parameter_applicability_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_capacitance(self):
        if len(set(self.cell_ids)) != len(self.cell_ids) or any(not value for value in self.cell_ids):
            raise ValueError("double-layer cell IDs must be nonempty, unique and ordered")
        if len(self.initial_interfacial_potential_V_by_cell) != len(self.cell_ids) or len(
            self.reference_interfacial_potential_V_by_cell
        ) != len(self.cell_ids):
            raise ValueError("double-layer initial/reference potentials must align with ordered cell IDs")
        if any(not math.isfinite(value) for value in (
            *self.initial_interfacial_potential_V_by_cell,
            *self.reference_interfacial_potential_V_by_cell,
            *self.differential_capacitance_potential_axis_V,
        )):
            raise ValueError("double-layer potential values and support must be finite")
        if any(right <= left for left, right in zip(
            self.differential_capacitance_potential_axis_V[:-1],
            self.differential_capacitance_potential_axis_V[1:], strict=True,
        )):
            raise ValueError("double-layer capacitance potential support must increase strictly")
        if len(self.differential_capacitance_potential_axis_V) != len(self.differential_capacitance_F_m2):
            raise ValueError("double-layer capacitance axis and values must have equal length")
        payload = {
            "potential_axis_V": list(self.differential_capacitance_potential_axis_V),
            "differential_capacitance_F_m2": [float(value) for value in self.differential_capacitance_F_m2],
        }
        if canonical_digest(payload) != self.capacitance_curve_sha256:
            raise ValueError("double-layer capacitance digest must bind its complete ordered curve")
        if not any(row.source_id == "caller_evidenced_dynamic_double_layer_and_faradaic_polarization_curves"
                   and row.sha256 == self.capacitance_curve_sha256 and row.license_id
                   for row in self.capacitance_evidence):
            raise ValueError("double-layer capacitance Evidence must license and pin the exact curve")
        initial_state_payload = {
            "cell_ids": list(self.cell_ids),
            "initial_interfacial_potential_V_by_cell": list(self.initial_interfacial_potential_V_by_cell),
            "reference_interfacial_potential_V_by_cell": list(self.reference_interfacial_potential_V_by_cell),
            "capacitance_curve_sha256": self.capacitance_curve_sha256,
        }
        if canonical_digest(initial_state_payload) != self.initial_state_record_sha256 or not any(
            row.source_id == DYNAMIC_DOUBLE_LAYER_INITIAL_STATE_SOURCE_ID
            and row.sha256 == self.initial_state_record_sha256 and row.license_id
            for row in self.initial_state_evidence
        ):
            raise ValueError("initial-state Evidence must pin its ordered potential/reference vectors and Cdl curve")
        lo, hi = self.differential_capacitance_potential_axis_V[0], self.differential_capacitance_potential_axis_V[-1]
        if any(not lo <= value <= hi for value in (
            *self.initial_interfacial_potential_V_by_cell,
            *self.reference_interfacial_potential_V_by_cell,
        )):
            raise ValueError("initial/reference interfacial potential is outside capacitance support")
        if not all((self.initial_state_and_reference_reviewed,
                    self.differential_curve_interpretation_reviewed,
                    self.closed_electrolyte_boundary_and_charge_sign_reviewed,
                    self.parameter_applicability_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("double-layer initial state, charge sign, applicability and use reviews are required")
        return self


class CreviceComponentStateBDFRequest(Contract):
    schema_version: Literal[
        "matintegrity.crevice_component_state_bdf.v1",
        "matintegrity.crevice_component_state_bdf.v2",
        "matintegrity.crevice_component_state_bdf.v3",
        "matintegrity.crevice_component_state_bdf.v4",
        "matintegrity.crevice_component_state_bdf.v5",
        "matintegrity.crevice_component_state_bdf.v6",
        "matintegrity.crevice_component_state_bdf.v7",
    ] = (
        "matintegrity.crevice_component_state_bdf.v1"
    )
    assessment_id: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    cells: tuple[CellAqueousEquilibriumTemplate, ...] = Field(min_length=2, max_length=300)
    initial_component_inventory: tuple[ComponentInventoryByCell, ...] = Field(min_length=1, max_length=100)
    solid_equilibrium_mode: Literal["aqueous_only", "instantaneous_solid_equilibrium"] = "aqueous_only"
    solid_phase_sets_by_cell: tuple[CellSolidPhaseSet, ...] = Field(default=(), max_length=300)
    kinetic_phase_sets_by_cell: tuple[CreviceBDFKineticPhaseSet, ...] = Field(default=(), max_length=300)
    kinetic_phase_mode_reviewed: bool = False
    kinetic_rate_evaluation_budget: int = Field(default=2_000_000, ge=1, le=20_000_000)
    maximum_phase_event_count: int = Field(default=100_000, ge=1, le=2_000_000)
    absolute_solid_inventory_tolerance_mol: Positive = 1e-12
    solid_phase_set_clock_id: str | None = None
    total_component_inventory_includes_solid_reviewed: bool = False
    instantaneous_equilibrium_no_nucleation_barrier_reviewed: bool = False
    solid_phase_set_applicability_and_completeness_reviewed: bool = False
    moving_geometry_mode: Literal["fixed_volume", "instantaneous_solid_aperture_feedback"] = "fixed_volume"
    dynamic_solid_geometry_by_cell: tuple[CellDynamicSolidGeometry, ...] = Field(default=(), max_length=300)
    moving_geometry_stage_feedback_reviewed: bool = False
    dynamic_geometry_relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    dynamic_geometry_relaxation_factor: Positive = Field(default=0.5, le=1.0)
    maximum_dynamic_geometry_iterations_per_cell_stage: int = Field(default=30, ge=2, le=500)
    maximum_total_dynamic_geometry_iterations: int = Field(default=1_000_000, ge=1, le=20_000_000)
    electrochemical_sources: tuple[ElectrochemicalSourceExtentSchedule, ...] = Field(default=(), max_length=100)
    ionic_face_current_schedule: IonicFaceCurrentSchedule | None = None
    capacitive_current_schedule: CapacitiveCellCurrentSchedule | None = None
    hydraulic_component_advection: CreviceHydraulicComponentAdvection | None = None
    dynamic_hydraulic_component_advection: CreviceDynamicHydraulicAdvection | None = None
    faradaic_stage_coupling: CreviceFaradaicSpatialChemistryRequest | None = None
    dynamic_double_layer: CreviceBDFDoubleLayerCapacitance | None = None
    interior_face_area_m2: tuple[Positive, ...] = Field(min_length=1, max_length=299)
    center_distance_m_by_interior_face: tuple[Positive, ...] = Field(min_length=1, max_length=299)
    species_face_diffusivity: tuple[SpeciesFaceDiffusivity, ...] = Field(min_length=2, max_length=100)
    relative_tolerance: Positive = Field(default=1e-7, le=1e-2)
    absolute_component_inventory_tolerance_mol: Positive = 1e-10
    absolute_component_closure_tolerance_mol: Positive = 1e-10
    relative_component_closure_tolerance: Positive = Field(default=1e-7, le=1e-2)
    solid_equilibrium_log_saturation_tolerance: Positive = Field(default=1e-8, le=1e-3)
    absolute_face_current_closure_tolerance_A: Positive = 1e-12
    relative_face_current_closure_tolerance: Positive = Field(default=1e-10, le=1e-3)
    absolute_double_layer_charge_tolerance_C: Positive = 1e-10
    maximum_absolute_source_extent_rate_mol_s: Positive | None = None
    maximum_step_s: Positive = Field(default=1e6, le=1e12)
    maximum_total_rhs_evaluations: int = Field(default=100_000, ge=1, le=2_000_000)
    maximum_total_stage_equilibrium_calls: int = Field(default=1_000_000, ge=1, le=20_000_000)
    maximum_total_nested_equilibrium_iteration_work: int = Field(default=20_000_000, ge=1, le=2_000_000_000)
    maximum_total_solid_partition_evaluations: int = Field(default=1_000_000, ge=1, le=20_000_000)
    maximum_total_solid_active_set_sweeps: int = Field(default=2_000_000, ge=1, le=200_000_000)
    maximum_total_solid_bisection_iterations: int = Field(default=20_000_000, ge=1, le=2_000_000_000)
    maximum_total_source_projection_operations: int = Field(default=2_000_000, ge=1, le=200_000_000)
    maximum_total_ionic_current_face_evaluations: int = Field(default=2_000_000, ge=1, le=200_000_000)
    maximum_total_stage_mixed_potential_function_evaluations: int = Field(default=2_000_000, ge=100, le=20_000_000)
    maximum_absolute_stage_faradaic_extent_rate_mol_s: Positive | None = None
    maximum_output_species_values: int = Field(default=1_000_000, ge=1, le=20_000_000)
    maximum_output_solid_phase_values: int = Field(default=1_000_000, ge=1, le=20_000_000)
    component_state_and_flux_basis_reviewed: bool
    cell_equilibrium_templates_and_evidence_reviewed: bool
    fixed_volume_and_boundary_scope_reviewed: bool
    electrochemical_source_stoichiometry_and_reservoir_reviewed: bool = False
    ionic_face_current_schedule_reviewed: bool = False
    capacitive_current_schedule_reviewed: bool = False
    hydraulic_component_advection_reviewed: bool = False
    dynamic_hydraulic_component_advection_reviewed: bool = False
    dynamic_volume_and_boundary_scope_reviewed: bool = False
    dynamic_hydraulic_fixed_point_relative_tolerance: Positive = Field(default=1e-5, le=1e-2)
    dynamic_hydraulic_fixed_point_relaxation: Positive = Field(default=0.5, le=1.0)
    maximum_dynamic_hydraulic_fixed_point_iterations: int = Field(default=8, ge=2, le=100)
    absolute_flow_tolerance_m3_s: Positive = 1e-12
    component_state_faradaic_stage_coupling_reviewed: bool = False
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_component_state_request(self):
        nt, nc = len(self.time_s), len(self.cells)
        if any(not math.isfinite(value) for value in self.time_s):
            raise ValueError("BDF times must be finite")
        if any(right <= left for left, right in zip(self.time_s, self.time_s[1:])):
            raise ValueError("BDF times must be strictly increasing")
        cell_ids = tuple(row.cell_id for row in self.cells)
        if len(set(cell_ids)) != nc:
            raise ValueError("cell IDs must be unique")
        kinetic_mode = bool(self.kinetic_phase_sets_by_cell)
        if not kinetic_mode and (
            self.maximum_phase_event_count != 100_000
            or self.kinetic_rate_evaluation_budget != 2_000_000
            or self.kinetic_phase_mode_reviewed
        ):
            raise ValueError("kinetic phase controls cannot be customized without kinetic phase sets")
        if kinetic_mode:
            if self.schema_version not in {"matintegrity.crevice_component_state_bdf.v6",
                                           "matintegrity.crevice_component_state_bdf.v7"}:
                raise ValueError("same-stage phase kinetics requires component-state BDF schema v6 or later")
            if not self.kinetic_phase_mode_reviewed:
                raise ValueError("same-stage phase kinetics requires explicit caller review")
            if not self.total_component_inventory_includes_solid_reviewed:
                raise ValueError("same-stage kinetic mode requires review that initial component moles are total aqueous-plus-solid")
            if self.solid_equilibrium_mode != "aqueous_only" or self.solid_phase_sets_by_cell:
                raise ValueError("same-stage phase kinetics uses explicit kinetic solids, not instantaneous solid equilibrium")
            if len(self.kinetic_phase_sets_by_cell) != nc or tuple(
                row.cell_id for row in self.kinetic_phase_sets_by_cell
            ) != cell_ids:
                raise ValueError("kinetic phase sets must match every BDF cell in exact order")
            if len({row.phase_set_id for row in self.kinetic_phase_sets_by_cell}) != nc:
                raise ValueError("each kinetic BDF cell requires a unique phase-set identity")
            for cell, phase_set in zip(self.cells, self.kinetic_phase_sets_by_cell, strict=True):
                if (phase_set.assessment_id != self.assessment_id
                        or phase_set.valid_time_s != self.time_s
                        or phase_set.temperature_K != cell.aqueous_activity_request.system.temperature_K):
                    raise ValueError("kinetic phase-set assessment, exact clock or temperature differs from BDF")
                if not phase_set.asset_id or not phase_set.location_id or not phase_set.physical_scope_id:
                    raise ValueError("kinetic phase set requires asset, location and physical-scope identities")
                for cell_attribute, phase_attribute in (("asset_id", "asset_id"), ("location_id", "location_id")):
                    cell_identity = getattr(cell, cell_attribute, None)
                    if cell_identity is not None and getattr(phase_set, phase_attribute) != cell_identity:
                        raise ValueError(f"kinetic phase-set {phase_attribute} must match its cell identity")
                if any(phase.initial_solid_moles_per_solution_volume_mol_m3 != 0.0
                       for phase in phase_set.phase_candidates):
                    raise ValueError("kinetic candidate records must not embed an additional initial solid inventory")
        elif self.kinetic_phase_mode_reviewed:
            raise ValueError("kinetic mode review cannot be set without per-cell kinetic phase sets")
        if self.solid_equilibrium_mode == "aqueous_only":
            if (self.solid_phase_sets_by_cell or self.solid_phase_set_clock_id is not None
                    or self.total_component_inventory_includes_solid_reviewed
                    or self.instantaneous_equilibrium_no_nucleation_barrier_reviewed
                    or self.solid_phase_set_applicability_and_completeness_reviewed) and not kinetic_mode:
                raise ValueError("aqueous-only mode cannot carry solid phase sets or solid-mode review declarations")
        else:
            if self.schema_version not in {
                "matintegrity.crevice_component_state_bdf.v2",
                "matintegrity.crevice_component_state_bdf.v3",
                "matintegrity.crevice_component_state_bdf.v4",
                "matintegrity.crevice_component_state_bdf.v5",
                "matintegrity.crevice_component_state_bdf.v6",
                "matintegrity.crevice_component_state_bdf.v7",
            }:
                raise ValueError("instantaneous solid equilibrium requires component-state BDF schema v2 or later")
            if not all((self.solid_phase_set_clock_id,
                        self.total_component_inventory_includes_solid_reviewed,
                        self.instantaneous_equilibrium_no_nucleation_barrier_reviewed,
                        self.solid_phase_set_applicability_and_completeness_reviewed)):
                raise ValueError("solid equilibrium mode requires clock, total-inventory, phase-set and instant-equilibrium reviews")
            if len(self.solid_phase_sets_by_cell) != nc:
                raise ValueError("solid equilibrium mode requires exactly one phase set per BDF cell")
            if tuple(row.cell_id for row in self.solid_phase_sets_by_cell) != cell_ids:
                raise ValueError("phase-set cell identities and order must exactly match the BDF cells")
            if len({row.phase_set_id for row in self.solid_phase_sets_by_cell}) != nc:
                raise ValueError("each BDF cell requires a distinct phase-set identity")
            for cell, phase_set in zip(self.cells, self.solid_phase_sets_by_cell, strict=True):
                if phase_set.assessment_id != self.assessment_id:
                    raise ValueError("phase-set assessment identity must match the BDF request")
                if phase_set.clock_id != self.solid_phase_set_clock_id or phase_set.valid_time_s != self.time_s:
                    raise ValueError("phase-set clock and exact time knots must match the BDF horizon")
                if phase_set.temperature_K != cell.aqueous_activity_request.system.temperature_K:
                    raise ValueError("phase-set temperature must exactly match its cell aqueous temperature")
                if any(row.initial_solid_moles_per_solution_volume_mol_m3 != 0.0
                       for row in phase_set.phase_candidates):
                    raise ValueError("phase-set candidate records must have zero seed inventory")
        dynamic_geometry = self.moving_geometry_mode == "instantaneous_solid_aperture_feedback"
        if dynamic_geometry:
            if self.schema_version not in {
                "matintegrity.crevice_component_state_bdf.v4",
                "matintegrity.crevice_component_state_bdf.v5",
                "matintegrity.crevice_component_state_bdf.v6",
                "matintegrity.crevice_component_state_bdf.v7",
            }:
                raise ValueError("inside-stage dynamic geometry requires component-state BDF schema v4 or later")
            if self.solid_equilibrium_mode != "instantaneous_solid_equilibrium" and not kinetic_mode:
                raise ValueError("dynamic solid-aperture feedback requires total-component solid or kinetic phase mode")
            if not self.moving_geometry_stage_feedback_reviewed:
                raise ValueError("dynamic geometry requires explicit caller review of aperture/volume fixed-point feedback")
            if len(self.dynamic_solid_geometry_by_cell) != nc:
                raise ValueError("dynamic geometry requires one caller-evidenced geometry map per BDF cell")
            if tuple(row.cell_id for row in self.dynamic_solid_geometry_by_cell) != cell_ids:
                raise ValueError("dynamic geometry cell IDs/order must exactly match the BDF mesh")
            if self.faradaic_stage_coupling is not None or self.hydraulic_component_advection is not None:
                raise ValueError("dynamic solid geometry cannot use the fixed-geometry Faradaic or hydraulic history bindings")
            for cell, geometry, phase_set in zip(
                self.cells, self.dynamic_solid_geometry_by_cell,
                self.kinetic_phase_sets_by_cell if kinetic_mode else self.solid_phase_sets_by_cell, strict=True,
            ):
                phase_ids = tuple(row.solid_species_id for row in geometry.phase_geometry)
                if phase_ids != tuple(row.solid_species_id for row in phase_set.phase_candidates):
                    raise ValueError("dynamic geometry phase map order must match the exact cell solid phase set")
                expected_volume_L = float(geometry.cell_length_m) * float(geometry.transverse_width_m) * float(
                    geometry.initial_aperture_m
                ) * 1000.0
                if not math.isclose(float(cell.solution_volume_L), expected_volume_L, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError("initial BDF liquid volume must equal caller initial length*width*aperture")
        elif (self.dynamic_solid_geometry_by_cell or self.moving_geometry_stage_feedback_reviewed):
            raise ValueError("dynamic geometry maps/review cannot be provided while moving_geometry_mode is fixed_volume")
        dynamic_hydraulic = self.dynamic_hydraulic_component_advection
        if dynamic_hydraulic is not None:
            if self.schema_version not in {"matintegrity.crevice_component_state_bdf.v5", "matintegrity.crevice_component_state_bdf.v6",
                                           "matintegrity.crevice_component_state_bdf.v7"}:
                raise ValueError("trial-state hydraulic momentum coupling requires BDF schema v5 or later")
            if not dynamic_geometry:
                raise ValueError("trial-state hydraulic momentum coupling requires instantaneous solid-aperture feedback")
            if not self.dynamic_hydraulic_component_advection_reviewed or not self.dynamic_volume_and_boundary_scope_reviewed:
                raise ValueError("dynamic hydraulic coupling and moving-volume scope require caller review")
            phase_scopes = {row.physical_scope_id for row in (
                self.kinetic_phase_sets_by_cell if kinetic_mode else self.solid_phase_sets_by_cell
            )}
            if phase_scopes != {dynamic_hydraulic.physical_scope_id}:
                raise ValueError("dynamic hydraulic physical scope must exactly match every cell solid-phase scope")
            if (dynamic_hydraulic.assessment_id != self.assessment_id
                    or dynamic_hydraulic.time_s != self.time_s
                    or dynamic_hydraulic.cell_ids != cell_ids):
                raise ValueError("dynamic hydraulic assessment, exact clock and cell order must match BDF")
            if any(not math.isclose(
                    float(geometry.transverse_width_m), float(dynamic_hydraulic.transverse_width_m),
                    rel_tol=1e-10, abs_tol=1e-12,
            ) for geometry in self.dynamic_solid_geometry_by_cell):
                raise ValueError("dynamic hydraulic width must match each cell solid-geometry width")
            species_rows = self.cells[0].aqueous_activity_request.system.species
            if (dynamic_hydraulic.species_order != tuple(row.species_id for row in species_rows)
                    or dynamic_hydraulic.species_charge_numbers != tuple(row.charge_number for row in species_rows)):
                raise ValueError("dynamic hydraulic species and charge order must match BDF chemistry")
            formula_map = {row.species_id: row.elemental_composition for row in species_rows}
            if any(value is None for value in formula_map.values()) or formula_map != dynamic_hydraulic.species_elemental_composition:
                raise ValueError("dynamic hydraulic element ledger must match every BDF species formula")
            if not set().union(*(set(row or {}) for row in formula_map.values())):
                raise ValueError("dynamic hydraulic element ledger requires at least one declared element")
            if self.faradaic_stage_coupling is not None:
                raise ValueError("dynamic hydraulic BDF currently excludes stage Faradaic chemistry coupling")
        elif self.dynamic_hydraulic_component_advection_reviewed or self.dynamic_volume_and_boundary_scope_reviewed:
            raise ValueError("dynamic hydraulic coupling review cannot be set without its request")
        if (self.solid_equilibrium_mode == "instantaneous_solid_equilibrium" or kinetic_mode) and \
                (sum(len(row.phase_candidates) for row in (
                    self.kinetic_phase_sets_by_cell if kinetic_mode else self.solid_phase_sets_by_cell
                )) * len(self.time_s)
                 + 2 * len(self.initial_component_inventory) * nc * len(self.time_s)) > self.maximum_output_solid_phase_values:
            raise ValueError("solid phase-history output exceeds maximum_output_solid_phase_values")
        if kinetic_mode:
            if (sum(len(row.phase_candidates) for row in self.kinetic_phase_sets_by_cell) * len(self.time_s)
                    + 2 * len(self.initial_component_inventory) * nc * len(self.time_s)) > self.maximum_output_solid_phase_values:
                raise ValueError("kinetic solid/component histories exceed maximum_output_solid_phase_values")
        template0 = self.cells[0]
        species_ids = tuple(row.species_id for row in template0.aqueous_activity_request.system.species)
        component_ids = tuple(row.component_id for row in template0.conserved_components)
        component_maps = {
            row.component_id: tuple((term.species_id, term.coefficient) for term in row.species_coefficients)
            for row in template0.conserved_components
        }
        temperature = template0.aqueous_activity_request.system.temperature_K
        for cell in self.cells:
            system = cell.aqueous_activity_request.system
            if tuple(row.species_id for row in system.species) != species_ids:
                raise ValueError("cell equilibrium species order must be identical across the component mesh")
            if tuple(row.charge_number for row in system.species) != tuple(
                row.charge_number for row in template0.aqueous_activity_request.system.species
            ):
                raise ValueError("cell species charges must match exactly")
            if system.temperature_K != temperature:
                raise ValueError("all cells must share one exact isothermal BDF temperature")
            if tuple(row.component_id for row in cell.conserved_components) != component_ids:
                raise ValueError("all cells must declare conserved components in the same order")
            local_maps = {
                row.component_id: tuple((term.species_id, term.coefficient) for term in row.species_coefficients)
                for row in cell.conserved_components
            }
            if local_maps != component_maps:
                raise ValueError("component coefficient maps must match exactly across cells")
        if 2 * len(self.time_s) * nc * len(species_ids) > self.maximum_output_species_values:
            raise ValueError("requested knot species output exceeds maximum_output_species_values")
        initial = {row.component_id: row.inventory_mol_by_cell for row in self.initial_component_inventory}
        if len(initial) != len(self.initial_component_inventory) or set(initial) != set(component_ids):
            raise ValueError("initial component inventory must cover each declared component exactly once")
        nf = nc - 1
        if (len(self.interior_face_area_m2) != nf
                or len(self.center_distance_m_by_interior_face) != nf):
            raise ValueError("interior face area and center-distance vectors must have cell_count - 1 entries")
        diffusivities = {row.species_id: row.diffusivity_m2_s_by_interior_face
                         for row in self.species_face_diffusivity}
        if len(diffusivities) != len(self.species_face_diffusivity) or set(diffusivities) != set(species_ids):
            raise ValueError("face diffusivities must cover every aqueous species exactly once")
        for component_id in component_ids:
            if (len(initial[component_id]) != nc
                    or any(not math.isfinite(v) or v < 0.0 for v in initial[component_id])):
                raise ValueError("initial component inventory must be finite, nonnegative and match cell count")
        if any(len(values) != nf for values in diffusivities.values()):
            raise ValueError("each species face diffusivity vector must have cell_count - 1 entries")
        source_ids = [row.reaction.reaction_id for row in self.electrochemical_sources]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("electrochemical source reaction IDs must be unique")
        if self.electrochemical_sources:
            if not self.electrochemical_source_stoichiometry_and_reservoir_reviewed:
                raise ValueError("opt-in source schedules require explicit source stoichiometry and reservoir review")
            if self.maximum_absolute_source_extent_rate_mol_s is None:
                raise ValueError("opt-in source schedules require a caller-declared maximum_absolute_source_extent_rate_mol_s")
            source_system = template0.aqueous_activity_request.system
            if any(row.elemental_composition is None for row in source_system.species):
                raise ValueError("electrochemical source balance requires explicit elemental formulas for every aqueous species")
            reference_formulas = {row.species_id: row.elemental_composition
                                  for row in source_system.species}
            for cell in self.cells:
                cell_formulas = {row.species_id: row.elemental_composition
                                 for row in cell.aqueous_activity_request.system.species}
                if cell_formulas != reference_formulas:
                    raise ValueError("source element-balance proof requires identical species formulas in every cell")
            element_ids = set().union(*(row.elemental_composition or {} for row in source_system.species))
            if not element_ids:
                raise ValueError("electrochemical source balance requires at least one declared element")
            charge_by_species = {row.species_id: row.charge_number for row in source_system.species}
            formula_by_species = {row.species_id: row.elemental_composition or {}
                                  for row in source_system.species}
            source_projection_ops = len(self.electrochemical_sources) * len(component_ids) * nc
            if source_projection_ops > self.maximum_total_source_projection_operations:
                raise ValueError("one RHS source projection exceeds maximum_total_source_projection_operations")
            source_ids_set = set(species_ids)
            components_by_id = {row.component_id: row for row in template0.conserved_components}
            for schedule in self.electrochemical_sources:
                reaction = schedule.reaction
                stoich = {row.species_id: row.coefficient for row in reaction.aqueous_species_stoichiometry}
                if len(stoich) != len(reaction.aqueous_species_stoichiometry) or not stoich:
                    raise ValueError("source stoichiometry must contain unique species IDs")
                if set(stoich) - source_ids_set or any(not math.isfinite(value) or value == 0.0
                                                       for value in stoich.values()):
                    raise ValueError("source stoichiometry must use declared species and finite nonzero coefficients")
                charge_delta = math.fsum(charge_by_species[sid] * coefficient
                                         for sid, coefficient in stoich.items())
                reservoir_charge = reaction.external_reservoir_charge_change_mol_eq_per_extent
                if not math.isfinite(reservoir_charge) or abs(charge_delta + reservoir_charge) > 1e-12 * max(1.0, abs(charge_delta), abs(reservoir_charge)):
                    raise ValueError("source species charge plus external-reservoir charge change must close")
                if (self.ionic_face_current_schedule is None
                        and (abs(charge_delta) > 1e-12 or abs(reservoir_charge) > 1e-12)):
                    raise ValueError("charged source extents require a matching ionic face-current schedule")
                ext_elements = {row.element_id: row.reservoir_change_mol_per_extent
                                for row in reaction.external_reservoir_element_change}
                if len(ext_elements) != len(reaction.external_reservoir_element_change) or set(ext_elements) != element_ids:
                    raise ValueError("external reservoir element ledger must cover every declared element exactly once")
                if any(not math.isfinite(value) for value in ext_elements.values()):
                    raise ValueError("external reservoir element changes must be finite")
                for element in element_ids:
                    aqueous_delta = math.fsum(stoich.get(sid, 0.0) * formula_by_species[sid].get(element, 0)
                                              for sid in source_ids_set)
                    reservoir_delta = ext_elements[element]
                    if abs(aqueous_delta + reservoir_delta) > 1e-12 * max(1.0, abs(aqueous_delta), abs(reservoir_delta)):
                        raise ValueError(f"source reaction does not close external reservoir element {element}")
                ext_components = {row.component_id: row.reservoir_change_mol_per_extent
                                  for row in reaction.external_reservoir_component_change}
                if len(ext_components) != len(reaction.external_reservoir_component_change) or set(ext_components) != set(component_ids):
                    raise ValueError("external reservoir component ledger must cover every component exactly once")
                for component_id in component_ids:
                    component_map = {row.species_id: row.coefficient
                                     for row in components_by_id[component_id].species_coefficients}
                    aqueous_delta = math.fsum(component_map.get(sid, 0.0) * coefficient
                                              for sid, coefficient in stoich.items())
                    reservoir_delta = ext_components[component_id]
                    if not math.isfinite(reservoir_delta) or abs(aqueous_delta + reservoir_delta) > \
                            1e-12 * max(1.0, abs(aqueous_delta), abs(reservoir_delta)):
                        raise ValueError(f"source reaction does not close external reservoir component {component_id}")
                if len(schedule.extent_rate_mol_s_by_knot_and_cell) != nt or any(
                    len(row) != nc or any(not math.isfinite(value) for value in row)
                    for row in schedule.extent_rate_mol_s_by_knot_and_cell
                ):
                    raise ValueError("source extent schedule must give finite per-cell rates at every exact time knot")
                if any(abs(value) > self.maximum_absolute_source_extent_rate_mol_s
                       for row in schedule.extent_rate_mol_s_by_knot_and_cell for value in row):
                    raise ValueError("source extent schedule exceeds the caller-declared absolute extent-rate limit")
        elif self.electrochemical_source_stoichiometry_and_reservoir_reviewed:
            raise ValueError("source stoichiometry review cannot be set without source schedules")
        if self.capacitive_current_schedule is not None:
            capacitor = self.capacitive_current_schedule
            if not self.capacitive_current_schedule_reviewed:
                raise ValueError("capacitive current requires explicit caller review")
            if capacitor.time_s != self.time_s:
                raise ValueError("capacitive-current knots must exactly match the BDF clock")
            if len(capacitor.current_A_by_knot_and_cell[0]) != nc:
                raise ValueError("capacitive current cell order/count must match BDF cells")
            if self.ionic_face_current_schedule is None:
                raise ValueError("capacitive current requires an explicit ionic face-current schedule for charge closure")
        elif self.capacitive_current_schedule_reviewed:
            raise ValueError("capacitive-current review cannot be set without a schedule")
        if self.dynamic_double_layer is not None:
            if self.schema_version != "matintegrity.crevice_component_state_bdf.v7":
                raise ValueError("same-stage dynamic double-layer state requires component-state BDF schema v7")
            if self.faradaic_stage_coupling is None:
                raise ValueError("same-stage dynamic double-layer state requires spatial stage Faradaic coupling")
            if self.moving_geometry_mode != "fixed_volume" or self.dynamic_hydraulic_component_advection is not None:
                raise ValueError("same-stage dynamic double-layer coupling currently requires fixed geometry and no hydraulic state")
            if self.capacitive_current_schedule is not None or self.ionic_face_current_schedule is not None:
                raise ValueError("dynamic double-layer state owns capacitive charge and ionic face current; schedules cannot be mixed in")
            if self.electrochemical_sources or self.hydraulic_component_advection is not None:
                raise ValueError("dynamic double-layer state owns Faradaic component sources and excludes schedule-based sources/advection")
            if len(self.dynamic_double_layer.initial_interfacial_potential_V_by_cell) != nc:
                raise ValueError("dynamic double-layer initial potential must align with every BDF cell")
            if self.dynamic_double_layer.cell_ids != cell_ids:
                raise ValueError("dynamic double-layer ordered cell IDs must exactly match the BDF cell mesh")
        elif self.schema_version == "matintegrity.crevice_component_state_bdf.v7":
            raise ValueError("schema v7 requires an explicit dynamic double-layer state")
        if self.hydraulic_component_advection is not None:
            hydraulic = self.hydraulic_component_advection
            if not self.hydraulic_component_advection_reviewed:
                raise ValueError("hydraulic advection requires explicit BDF coupling review")
            if self.schema_version != "matintegrity.crevice_component_state_bdf.v3":
                raise ValueError("hydraulic component advection requires component-state BDF schema v3")
            if hydraulic.assessment_id != self.assessment_id or hydraulic.time_s != self.time_s:
                raise ValueError("hydraulic advection assessment and exact clock must match the BDF request")
            if hydraulic.cell_ids != tuple(row.cell_id for row in self.cells):
                raise ValueError("hydraulic advection cell IDs/order must match BDF cells")
            if hydraulic.cell_solution_volume_L != tuple(row.solution_volume_L for row in self.cells):
                raise ValueError("hydraulic advection volume snapshot must match BDF cell volumes")
            system_species = self.cells[0].aqueous_activity_request.system.species
            if hydraulic.species_order != tuple(row.species_id for row in system_species) or hydraulic.species_charge_numbers != tuple(row.charge_number for row in system_species):
                raise ValueError("hydraulic advection species/charge order must match BDF chemistry")
            if any(row.elemental_composition is None for row in system_species):
                raise ValueError("hydraulic boundary exchange ledger requires elemental formulas for all species")
            if self.faradaic_stage_coupling is not None and self.ionic_face_current_schedule is not None:
                raise ValueError("hydraulic advection cannot be combined with an independent ionic-current schedule")
        elif self.hydraulic_component_advection_reviewed:
            raise ValueError("hydraulic advection review cannot be set without a bound schedule")
        if self.ionic_face_current_schedule is not None:
            current = self.ionic_face_current_schedule
            if not self.ionic_face_current_schedule_reviewed:
                raise ValueError("ionic face-current schedules require explicit caller review")
            if current.time_s != self.time_s:
                raise ValueError("ionic current knots must exactly match component and source schedule times")
            if len(current.current_A_by_knot_and_face) != nt or any(
                len(row) != nc + 1 or any(not math.isfinite(value) for value in row)
                for row in current.current_A_by_knot_and_face
            ):
                raise ValueError("ionic current schedule must contain finite ncell+1 face currents at every knot")
            if any(row[0] != 0.0 or row[-1] != 0.0 for row in current.current_A_by_knot_and_face):
                raise ValueError("this child solver requires zero ionic current at both external boundaries")
            for knot_index, knot_currents in enumerate(current.current_A_by_knot_and_face):
                for cell_index in range(nc):
                    aqueous_charge_rate = math.fsum(
                        math.fsum(
                            row.charge_number * term.coefficient
                            for row in template0.aqueous_activity_request.system.species
                            for term in schedule.reaction.aqueous_species_stoichiometry
                            if term.species_id == row.species_id
                        ) * schedule.extent_rate_mol_s_by_knot_and_cell[knot_index][cell_index]
                        for schedule in self.electrochemical_sources
                    )
                    capacitive_current_A = (self.capacitive_current_schedule.current_A_by_knot_and_cell[knot_index][cell_index]
                                            if self.capacitive_current_schedule is not None else 0.0)
                    expected_delta_A = FARADAY_CONSTANT_C_MOL * aqueous_charge_rate + capacitive_current_A
                    actual_delta_A = knot_currents[cell_index + 1] - knot_currents[cell_index]
                    allowed = self.absolute_face_current_closure_tolerance_A + \
                        self.relative_face_current_closure_tolerance * max(abs(actual_delta_A), abs(expected_delta_A))
                    if abs(actual_delta_A - expected_delta_A) > allowed:
                        raise ValueError(
                            f"ionic current schedule does not close charge continuity at knot {knot_index}, cell {cell_index}"
                        )
        elif self.ionic_face_current_schedule_reviewed:
            raise ValueError("ionic current review cannot be set without an ionic face-current schedule")
        if self.faradaic_stage_coupling is not None:
            if not self.component_state_faradaic_stage_coupling_reviewed:
                raise ValueError("stage mixed-potential coupling requires explicit component-state coupling review")
            if self.maximum_absolute_stage_faradaic_extent_rate_mol_s is None:
                raise ValueError("stage mixed-potential coupling requires a caller-declared maximum branch extent rate")
            if (self.electrochemical_sources or self.ionic_face_current_schedule is not None
                    or (self.capacitive_current_schedule is not None and self.dynamic_double_layer is None)):
                raise ValueError("stage mixed-potential coupling owns its quasi-steady branch/current closure; caller source/current schedules, including capacitive current, are mutually exclusive")
            coupled = self.faradaic_stage_coupling
            if self.solid_equilibrium_mode == "instantaneous_solid_equilibrium" and \
                    coupled.assessment_id != self.assessment_id:
                raise ValueError("Faradaic coupling assessment identity must match the component-state BDF request")
            faradaic_transport = coupled.transport_chemistry.transport.transport_request
            if self.solid_equilibrium_mode == "instantaneous_solid_equilibrium":
                mixed_identity = coupled.mixed_potential_template
                for phase_set in self.solid_phase_sets_by_cell:
                    if (phase_set.assessment_id, phase_set.asset_id, phase_set.location_id,
                            phase_set.physical_scope_id, phase_set.clock_id, phase_set.valid_time_s) != (
                            mixed_identity.assessment_id, mixed_identity.asset_id, mixed_identity.location_id,
                            mixed_identity.physical_scope_id, mixed_identity.clock_id, mixed_identity.time_s):
                        raise ValueError("phase-set assessment, asset, location, scope and clock must match the Faradaic stage context")
            faradaic_species = tuple(row.species_id for row in faradaic_transport.species)
            if faradaic_transport.output_time_s != self.time_s:
                raise ValueError("mixed-potential transport knots must exactly match component BDF knots")
            if len(coupled.mixed_potential_template.cell_ids) != nc or \
                    coupled.mixed_potential_template.cell_ids != cell_ids:
                raise ValueError("mixed-potential cells must exactly match component-state cell order")
            if faradaic_transport.cell_count != nc:
                raise ValueError("Faradaic transport and component-state cell counts must match")
            if faradaic_species != species_ids:
                raise ValueError("Faradaic transport species order must match cell equilibrium species order")
            reference_species = template0.aqueous_activity_request.system.species
            if tuple(row.charge_number for row in faradaic_transport.species) != tuple(
                row.charge_number for row in reference_species
            ):
                raise ValueError("Faradaic transport species charges must match equilibrium species")
            if any(value != temperature for value in faradaic_transport.temperature_K_by_knot):
                raise ValueError("Davies stage chemistry currently requires the mixed-potential interval to be isothermal at its parameter temperature")
            if any(not math.isclose(length, faradaic_transport.length_m / nc,
                                    rel_tol=1e-10, abs_tol=1e-14)
                   for length in coupled.mixed_potential_template.cell_lengths_m):
                raise ValueError("mixed-potential cell lengths must match the component-state uniform finite-volume mesh")
            stage_projection_operations = len(coupled.faradaic_branch_maps) * len(component_ids) * nc
            if stage_projection_operations > self.maximum_total_source_projection_operations:
                raise ValueError("one RHS stage Faradaic projection exceeds maximum_total_source_projection_operations")
            # This component-state child has fixed cell volumes and fixed NP face areas.
            # Do not silently combine that state with the moving-area histories accepted
            # by the spatial Faradaic transport API.
            area_history = np.asarray(
                coupled.transport_chemistry.transport.cell_cross_section_area_m2_by_knot,
                dtype=float,
            )
            face_area_history = np.asarray(
                coupled.transport_chemistry.transport.face_cross_section_area_m2_by_knot,
                dtype=float,
            )
            area_scale = np.maximum(np.abs(area_history[0]), 1e-30)
            if np.any(np.abs(area_history - area_history[0]) > 1e-10 * area_scale[None, :] + 1e-18):
                raise ValueError("component-state Faradaic BDF currently requires fixed cross-section area at every knot")
            if np.any(np.abs(face_area_history - face_area_history[0]) >
                      1e-10 * np.maximum(np.abs(face_area_history[0]), 1e-30)[None, :] + 1e-18):
                raise ValueError("component-state Faradaic BDF currently requires fixed face areas at every knot")
            expected_cell_volume_L = area_history[0] * (faradaic_transport.length_m / nc) * 1000.0
            supplied_cell_volume_L = np.asarray([row.solution_volume_L for row in self.cells], dtype=float)
            volume_scale = np.maximum(np.maximum(np.abs(expected_cell_volume_L),
                                                 np.abs(supplied_cell_volume_L)), 1e-30)
            if np.any(np.abs(expected_cell_volume_L - supplied_cell_volume_L) >
                      1e-10 * volume_scale + 1e-15):
                raise ValueError("component-state cell solution volumes must match fixed Faradaic cross-section × cell length")
            supplied_face_area = np.asarray(self.interior_face_area_m2, dtype=float)
            geometry_face_area = face_area_history[0, 1:-1]
            aperture = np.asarray(coupled.mixed_potential_template.cell_apertures_m, dtype=float)
            ohmic_face_area = (2.0 * aperture[:-1] * aperture[1:]
                               / (aperture[:-1] + aperture[1:])
                               * coupled.mixed_potential_template.slit_width_m)
            face_scale = np.maximum(np.maximum(np.abs(supplied_face_area),
                                               np.abs(geometry_face_area)), 1e-30)
            if (np.any(np.abs(supplied_face_area - geometry_face_area) > 1e-10 * face_scale + 1e-18)
                    or np.any(np.abs(geometry_face_area - ohmic_face_area) >
                              1e-10 * np.maximum(np.abs(ohmic_face_area), 1e-30) + 1e-18)):
                raise ValueError("component-state NP face areas must match the mixed-potential geometry faces")
            lengths = np.asarray(coupled.mixed_potential_template.cell_lengths_m, dtype=float)
            centers = np.cumsum(lengths) - 0.5 * lengths
            expected_center_distances = np.diff(centers)
            supplied_center_distances = np.asarray(self.center_distance_m_by_interior_face, dtype=float)
            distance_scale = np.maximum(np.maximum(np.abs(supplied_center_distances),
                                                   np.abs(expected_center_distances)), 1e-30)
            if np.any(np.abs(supplied_center_distances - expected_center_distances) >
                      1e-10 * distance_scale + 1e-15):
                raise ValueError("component-state center distances must match mixed-potential cell-center spacing")
        elif self.component_state_faradaic_stage_coupling_reviewed:
            raise ValueError("stage coupling review cannot be set without a mixed-potential coupling contract")
        if (kinetic_mode and self.maximum_phase_event_count > self.maximum_total_rhs_evaluations):
            raise ValueError("kinetic event budget cannot exceed maximum_total_rhs_evaluations")
        if len(self.cells) + 1 > self.maximum_total_ionic_current_face_evaluations:
            raise ValueError("one RHS ionic-current face evaluation exceeds its declared budget")
        scope_reviewed = self.fixed_volume_and_boundary_scope_reviewed or (
            dynamic_hydraulic is not None and self.dynamic_volume_and_boundary_scope_reviewed
        )
        reviews = (self.component_state_and_flux_basis_reviewed,
                   self.cell_equilibrium_templates_and_evidence_reviewed,
                   scope_reviewed,
                   self.computational_use_authorized)
        if not all(reviews):
            raise ValueError("component-state, flux, equilibrium, volume, boundary and use reviews are required")
        return self


def _crevice_bdf_kinetic_phase_set_specifications() -> tuple[ModelSpec, ...]:
    return (ModelSpec(
        model_id="chemistry.crevice_bdf_kinetic_phase_set",
        input_type=CreviceBDFKineticPhaseSet,
        evaluator=lambda request: Calculation(values={
            "model_id": "chemistry.crevice_bdf_kinetic_phase_set",
            "assessment_id": request.assessment_id,
            "cell_id": request.cell_id,
            "phase_set_id": request.phase_set_id,
            "phase_set_sha256": request.phase_set_sha256,
            "phase_candidate_ids": [row.solid_species_id for row in request.phase_candidates],
            "ready_for_component_state_bdf": True,
            "qualification_claimed": False,
        }),
        units={"temperature_K": "K", "valid_time_s[]": "s",
               "initial_solid_inventory_by_phase[].initial_solid_moles_mol": "mol"},
        assumptions=("The contract binds exact ordered caller phase and kinetic-law records; it does not calculate a trajectory.",),
        source_ids=("caller_digest_bound_same_stage_solid_kinetic_input_contract",),
        version="1.0.0",
        qualification="user_model",
    ),)


def specifications() -> tuple[ModelSpec, ...]:
    return _crevice_bdf_kinetic_phase_set_specifications()


def _stage_system(template: CellAqueousEquilibriumTemplate, component_mol: dict[str, float]):
    system = template.aqueous_activity_request.system
    target_by_constraint = {}
    for assignment in template.constraint_roles:
        if assignment.role == "conserved_component":
            target_by_constraint[assignment.constraint_id] = (
                component_mol[assignment.component_id] / template.solution_volume_L
            )
    constraints = tuple(
        row.model_copy(update={"target_mol_L": target_by_constraint[row.constraint_id]})
        if row.constraint_id in target_by_constraint else row
        for row in system.constraints
    )
    return template.aqueous_activity_request.model_copy(
        update={"system": system.model_copy(update={"constraints": constraints})}
    )


def _double_layer_potential_from_charge_density(
    charge_density_C_m2: float,
    reference_potential_V: float,
    potential_axis_V: tuple[float, ...],
    capacitance_F_m2: tuple[float, ...],
    cumulative_charge_C_m2_by_knot: tuple[float, ...] | None = None,
) -> float:
    """Invert the monotone piecewise-quadratic primitive of a positive Cdl curve."""
    if cumulative_charge_C_m2_by_knot is None:
        cumulative = [0.0]
        for index in range(len(potential_axis_V) - 1):
            width = potential_axis_V[index + 1] - potential_axis_V[index]
            cumulative.append(cumulative[-1] + 0.5 * width * (
                capacitance_F_m2[index] + capacitance_F_m2[index + 1]
            ))
    else:
        cumulative = list(cumulative_charge_C_m2_by_knot)
    if len(cumulative) != len(potential_axis_V):
        raise ArithmeticError("double_layer_capacitance_cumulative_shape_mismatch")
    ref_index = min(max(bisect_right(potential_axis_V, reference_potential_V) - 1, 0), len(potential_axis_V) - 2)
    ref_dx = reference_potential_V - potential_axis_V[ref_index]
    ref_slope = (capacitance_F_m2[ref_index + 1] - capacitance_F_m2[ref_index]) / (
        potential_axis_V[ref_index + 1] - potential_axis_V[ref_index]
    )
    reference_charge = cumulative[ref_index] + capacitance_F_m2[ref_index] * ref_dx \
        + 0.5 * ref_slope * ref_dx * ref_dx
    target = reference_charge + charge_density_C_m2
    if not math.isfinite(target) or target < cumulative[0] or target > cumulative[-1]:
        raise ArithmeticError("dynamic_double_layer_charge_outside_capacitance_support")
    segment = min(max(bisect_right(cumulative, target) - 1, 0), len(potential_axis_V) - 2)
    delta_charge = target - cumulative[segment]
    c0 = float(capacitance_F_m2[segment])
    slope = (float(capacitance_F_m2[segment + 1]) - c0) / (
        float(potential_axis_V[segment + 1]) - float(potential_axis_V[segment])
    )
    discriminant = c0 * c0 + 2.0 * slope * delta_charge
    if discriminant < 0.0 or not math.isfinite(discriminant):
        raise ArithmeticError("double_layer_capacitance_inverse_discriminant_invalid")
    root = math.sqrt(discriminant)
    delta_potential = delta_charge / c0 if abs(slope) <= 1e-14 * max(abs(c0), 1.0) else (
        2.0 * delta_charge / (c0 + root)
    )
    result = float(potential_axis_V[segment]) + delta_potential
    if not math.isfinite(result):
        raise ArithmeticError("dynamic_double_layer_charge_inversion_nonfinite")
    return result


def solve_crevice_component_state_bdf(request: CreviceComponentStateBDFRequest) -> Calculation:
    """Integrate a caller-flux-driven conserved-component state with stage equilibrium."""
    digest = canonical_digest(request.model_dump(mode="json"))
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "assessment_id": request.assessment_id,
            "input_sha256": digest, "reason": "scipy_runtime_unavailable", "committed": False,
        })
    try:
        component_ids = [row.component_id for row in request.initial_component_inventory]
        nc, nt = len(request.cells), len(request.time_s)
        cell_ids = [row.cell_id for row in request.cells]
        ncomp = len(component_ids)
        kinetic_mode = bool(request.kinetic_phase_sets_by_cell)
        times = np.asarray(request.time_s, dtype=float)
        initial = np.asarray([row.inventory_mol_by_cell for row in request.initial_component_inventory], dtype=float)
        species_ids = [row.species_id for row in request.cells[0].aqueous_activity_request.system.species]
        species_index = {species_id: index for index, species_id in enumerate(species_ids)}
        charges = np.asarray([
            row.charge_number for row in request.cells[0].aqueous_activity_request.system.species
        ], dtype=float)
        diffusivity_by_species = {row.species_id: np.asarray(row.diffusivity_m2_s_by_interior_face, dtype=float)
                                  for row in request.species_face_diffusivity}
        component_coefficient = np.zeros((ncomp, len(species_ids)), dtype=float)
        for component_index, component_id in enumerate(component_ids):
            component = next(row for row in request.cells[0].conserved_components
                             if row.component_id == component_id)
            for term in component.species_coefficients:
                component_coefficient[component_index, species_index[term.species_id]] = term.coefficient
        element_ids: list[str] = []
        component_element_coefficient = None
        if (request.solid_equilibrium_mode == "instantaneous_solid_equilibrium" or kinetic_mode
                or request.hydraulic_component_advection is not None
                or request.dynamic_hydraulic_component_advection is not None):
            reference_species = request.cells[0].aqueous_activity_request.system.species
            if any(row.elemental_composition is None for row in reference_species):
                raise ValueError("solid BDF mode requires elemental formulas for every aqueous species")
            reference_formulas = {row.species_id: row.elemental_composition for row in reference_species}
            if any(
                {row.species_id: row.elemental_composition for row in cell.aqueous_activity_request.system.species}
                != reference_formulas
                for cell in request.cells
            ):
                raise ValueError("solid BDF mode requires exact aqueous elemental formulas across all cells")
            element_ids = sorted(set().union(*(row.elemental_composition or {} for row in reference_species)))
            formula_matrix = np.asarray([
                [(row.elemental_composition or {}).get(element, 0) for row in reference_species]
                for element in element_ids
            ], dtype=float)
            if np.linalg.matrix_rank(component_coefficient) != ncomp:
                raise ValueError("solid BDF element ledgers require an independent conserved-component basis")
            active_component_species = np.any(component_coefficient != 0.0, axis=0)
            if not np.any(active_component_species):
                raise ValueError("solid BDF component basis does not map any aqueous species")
            active_component_map = component_coefficient[:, active_component_species]
            solved, _, _, _ = np.linalg.lstsq(active_component_map.T, formula_matrix[:, active_component_species].T,
                                               rcond=None)
            component_element_coefficient = solved.T
            reconstructed = component_element_coefficient @ active_component_map
            active_formula_matrix = formula_matrix[:, active_component_species]
            scale = np.maximum(1.0, np.abs(active_formula_matrix))
            if np.any(np.abs(reconstructed - active_formula_matrix) > 1e-10 * scale):
                raise ValueError("declared component basis cannot exactly reconstruct mapped aqueous element formulas")
            for phase_set in request.solid_phase_sets_by_cell:
                for phase in phase_set.phase_candidates:
                    phase_species_extent = np.asarray([
                        phase.aqueous_reactant_stoichiometry.get(sid, 0.0) for sid in species_ids
                    ], dtype=float)
                    component_extent = component_coefficient @ phase_species_extent
                    element_extent = component_element_coefficient @ component_extent
                    expected_element_extent = np.asarray([
                        phase.solid_elemental_composition.get(element, 0) for element in element_ids
                    ], dtype=float)
                    if np.any(np.abs(element_extent - expected_element_extent) >
                              1e-10 * np.maximum(1.0, np.abs(expected_element_extent))):
                        raise ValueError("component basis does not reproduce solid phase elemental stoichiometry")
        faradaic_stage = request.faradaic_stage_coupling is not None
        dynamic_double_layer = request.dynamic_double_layer
        n_dynamic_double_layer_state = nc if dynamic_double_layer is not None else 0
        double_layer_area_m2 = np.zeros(nc, dtype=float)
        initial_double_layer_charge_C = np.zeros(nc, dtype=float)
        double_layer_capacitance_cumulative = None
        if dynamic_double_layer is not None:
            cap_axis = dynamic_double_layer.differential_capacitance_potential_axis_V
            cap_values = tuple(float(value) for value in dynamic_double_layer.differential_capacitance_F_m2)
            cumulative = [0.0]
            for cap_index in range(len(cap_axis) - 1):
                cumulative.append(cumulative[-1] + 0.5 * (cap_axis[cap_index + 1] - cap_axis[cap_index])
                                  * (cap_values[cap_index] + cap_values[cap_index + 1]))
            double_layer_capacitance_cumulative = tuple(cumulative)
            mixed_template = request.faradaic_stage_coupling.mixed_potential_template
            double_layer_area_m2 = (
                np.asarray(mixed_template.cell_lengths_m, dtype=float)
                * float(mixed_template.slit_width_m)
                * int(mixed_template.reactive_face_count)
            )
            for cell_index, potential in enumerate(dynamic_double_layer.initial_interfacial_potential_V_by_cell):
                charge_per_area = _integrated_capacitance_charge(
                    float(potential),
                    float(dynamic_double_layer.reference_interfacial_potential_V_by_cell[cell_index]),
                    dynamic_double_layer.differential_capacitance_potential_axis_V,
                    tuple(float(value) for value in dynamic_double_layer.differential_capacitance_F_m2),
                )
                initial_double_layer_charge_C[cell_index] = double_layer_area_m2[cell_index] * charge_per_area
            if not np.isfinite(initial_double_layer_charge_C).all():
                raise ValueError("initial double-layer charge is nonfinite")
        source_schedules = list(request.electrochemical_sources)
        if faradaic_stage:
            coupling = request.faradaic_stage_coupling
            source_reactions = list(coupling.faradaic_branch_maps)
            source_ids = [row.reaction_id for row in source_reactions]
            source_extent_knots = np.zeros((len(source_reactions), nt, nc), dtype=float)
        else:
            source_reactions = [row.reaction for row in source_schedules]
            source_ids = [row.reaction_id for row in source_reactions]
            source_extent_knots = np.asarray([
                row.extent_rate_mol_s_by_knot_and_cell for row in source_schedules
            ], dtype=float) if source_schedules else np.zeros((0, nt, nc), dtype=float)
        nsource = len(source_reactions)
        source_component_coefficient = np.zeros((ncomp, nsource), dtype=float)
        source_metadata = []
        for source_index, reaction in enumerate(source_reactions):
            if faradaic_stage:
                stoich = reaction.aqueous_species_stoichiometry_per_extent
                external_elements = reaction.external_reservoir_element_stoichiometry_per_extent
                external_charge = -math.fsum(
                    row.charge_number * stoich.get(row.species_id, 0.0)
                    for row in request.cells[0].aqueous_activity_request.system.species
                )
                evidence_rows = reaction.evidence
                source_digest = canonical_digest(reaction.model_dump(mode="json"))
            else:
                stoich = {row.species_id: row.coefficient for row in reaction.aqueous_species_stoichiometry}
                external_elements = {row.element_id: row.reservoir_change_mol_per_extent
                                     for row in reaction.external_reservoir_element_change}
                external_charge = reaction.external_reservoir_charge_change_mol_eq_per_extent
                evidence_rows = reaction.evidence
                source_digest = canonical_digest(source_schedules[source_index].model_dump(mode="json"))
            component_reservoir = {}
            for component_index, component_id in enumerate(component_ids):
                component = next(row for row in request.cells[0].conserved_components
                                 if row.component_id == component_id)
                component_map = {row.species_id: row.coefficient for row in component.species_coefficients}
                source_component_coefficient[component_index, source_index] = math.fsum(
                    component_map.get(sid, 0.0) * coefficient for sid, coefficient in stoich.items()
                )
                component_reservoir[component_id] = -source_component_coefficient[component_index, source_index]
            source_metadata.append({
                "reaction_id": reaction.reaction_id,
                "species_stoichiometry": stoich,
                "external_element_change_per_extent": external_elements,
                "external_component_change_per_extent": component_reservoir,
                "external_charge_change_per_extent": external_charge,
                "evidence": evidence_rows,
                "source_digest": source_digest,
            })
        face_area = np.asarray(request.interior_face_area_m2, dtype=float)
        center_distance = np.asarray(request.center_distance_m_by_interior_face, dtype=float)
        if request.ionic_face_current_schedule is None:
            ionic_current_knots = np.zeros((nt, nc + 1), dtype=float)
        else:
            ionic_current_knots = np.asarray(
                request.ionic_face_current_schedule.current_A_by_knot_and_face, dtype=float
            )
        if request.capacitive_current_schedule is None:
            capacitive_current_knots = np.zeros((nt, nc), dtype=float)
        else:
            capacitive_current_knots = np.asarray(
                request.capacitive_current_schedule.current_A_by_knot_and_cell, dtype=float
            )
        n_component_state = ncomp * nc
        kinetic_phase_sets = request.kinetic_phase_sets_by_cell
        kinetic_phase_ids_by_cell = [tuple(row.solid_species_id for row in phase_set.phase_candidates)
                                     for phase_set in kinetic_phase_sets]
        if kinetic_mode and len({ids for ids in kinetic_phase_ids_by_cell}) != 1:
            raise ValueError("kinetic BDF currently requires identical ordered phase identities in every mesh cell")
        kinetic_phase_ids = list(kinetic_phase_ids_by_cell[0]) if kinetic_mode else []
        nkinetic_phase = len(kinetic_phase_ids)
        n_kinetic_solid_state = nkinetic_phase * nc
        kinetic_phase_index = {phase_id: i for i, phase_id in enumerate(kinetic_phase_ids)}
        kinetic_layout_state_size = n_component_state + n_kinetic_solid_state
        initial_kinetic_solids = np.zeros((nkinetic_phase, nc), dtype=float)
        if kinetic_mode:
            for cell_index, phase_set in enumerate(kinetic_phase_sets):
                if not phase_set.asset_id or not phase_set.location_id or not phase_set.physical_scope_id:
                    raise ValueError("kinetic phase set requires explicit asset identity")
                phase_species_ids = {sid for phase in phase_set.phase_candidates
                                     for sid in phase.aqueous_reactant_stoichiometry}
                if not phase_species_ids <= set(species_ids):
                    raise ValueError("kinetic phase stoichiometry references species outside the BDF chemistry")
                reference_species = request.cells[cell_index].aqueous_activity_request.system.species
                species_by_id = {row.species_id: row for row in reference_species}
                for phase in phase_set.phase_candidates:
                    if not math.isclose(math.fsum(
                        species_by_id[sid].charge_number * coefficient
                        for sid, coefficient in phase.aqueous_reactant_stoichiometry.items()
                    ), 0.0, rel_tol=0.0, abs_tol=1e-12):
                        raise ValueError("kinetic neutral solid reaction must conserve aqueous charge")
                    element_ids_phase = set(phase.solid_elemental_composition)
                    for sid in phase.aqueous_reactant_stoichiometry:
                        formula = species_by_id[sid].elemental_composition
                        if formula is None:
                            raise ValueError("kinetic phase checks require elemental formulas for every species")
                        element_ids_phase.update(formula)
                    for element in element_ids_phase:
                        aqueous_count = math.fsum(
                            (species_by_id[sid].elemental_composition or {}).get(element, 0) * coefficient
                            for sid, coefficient in phase.aqueous_reactant_stoichiometry.items()
                        )
                        solid_count = phase.solid_elemental_composition.get(element, 0)
                        if not math.isclose(aqueous_count, solid_count, rel_tol=1e-12, abs_tol=1e-12):
                            raise ValueError("kinetic solid precipitation must conserve each declared element")
                for phase_inventory in phase_set.initial_solid_inventory_by_phase:
                    initial_kinetic_solids[kinetic_phase_index[phase_inventory.solid_species_id], cell_index] = float(
                        phase_inventory.initial_solid_moles_mol
                    )
        initial_state_components = initial.copy()
        if kinetic_mode:
            for cell_index, phase_set in enumerate(kinetic_phase_sets):
                for phase in phase_set.phase_candidates:
                    phase_vector = np.asarray([phase.aqueous_reactant_stoichiometry.get(sid, 0.0)
                                               for sid in species_ids], dtype=float)
                    comp_per_phase = component_coefficient @ phase_vector
                    initial_state_components[:, cell_index] += (
                        comp_per_phase * initial_kinetic_solids[kinetic_phase_index[phase.solid_species_id], cell_index]
                    )
        n_face_state = ncomp * (nc + 1)
        n_extent_state = nsource * nc
        n_current_state = nc + 1
        hydraulic_advection = request.hydraulic_component_advection
        dynamic_hydraulic_advection = request.dynamic_hydraulic_component_advection
        hydraulic_transport_enabled = hydraulic_advection is not None or dynamic_hydraulic_advection is not None
        n_dynamic_flow_state = 1 if dynamic_hydraulic_advection is not None else 0
        n_hydraulic_ledger_state = (2 * (ncomp + len(element_ids) + 1)
                                    if hydraulic_transport_enabled else 0)
        state0 = np.concatenate((initial_state_components.reshape(-1), initial_kinetic_solids.reshape(-1), np.zeros(
            n_face_state + n_extent_state + n_current_state),
            np.asarray([float(dynamic_hydraulic_advection.initial_signed_volumetric_flow_m3_s)])
            if dynamic_hydraulic_advection is not None else np.zeros(0),
            np.zeros(n_hydraulic_ledger_state),
            initial_double_layer_charge_C if dynamic_double_layer is not None else np.zeros(0)))
        extent_state_start = kinetic_layout_state_size + n_face_state
        current_state_start = extent_state_start + n_extent_state
        dynamic_flow_state_index = current_state_start + n_current_state
        hydraulic_ledger_state_start = dynamic_flow_state_index + n_dynamic_flow_state
        rhs_evaluations = 0
        equilibrium_calls = 0
        nested_equilibrium_work_bound = 0
        maximum_face_current_residual_A = 0.0
        maximum_face_current_scale_A = 0.0
        source_projection_operations = 0
        ionic_current_face_evaluations = 0
        stage_mixed_potential_evaluations = 0
        solid_partition_evaluations = 0
        solid_active_set_sweeps = 0
        solid_bisection_iterations = 0
        dynamic_geometry_iterations = 0
        maximum_dynamic_geometry_residual = 0.0
        dynamic_hydraulic_iterations = 0
        maximum_dynamic_hydraulic_fixed_point_residual = 0.0
        stage_mixed_knot_lineage = []
        lineage_chain = canonical_digest({"input_sha256": digest, "seed": "component-stage-equilibrium-lineage-v1"})
        last_stage_summary = None
        solid_mode = request.solid_equilibrium_mode == "instantaneous_solid_equilibrium"
        dynamic_geometry = request.moving_geometry_mode == "instantaneous_solid_aperture_feedback"
        phase_set_by_cell = {row.cell_id: row for row in request.solid_phase_sets_by_cell}
        kinetic_seed_modes = [
            [initial_kinetic_solids[phase_index, cell_index] / (float(request.cells[cell_index].solution_volume_L) / 1000.0)
             >= float(phase_set.nucleation_laws[phase_index].nucleated_inventory_threshold_mol_m3)
             for cell_index, phase_set in enumerate(kinetic_phase_sets)]
            for phase_index in range(nkinetic_phase)
        ] if kinetic_mode else []
        if kinetic_mode:
            phase_count = nkinetic_phase
            kinetic_layout = SimpleNamespace(
                component_ids=tuple(component_ids),
                phase_ids=tuple(kinetic_phase_ids),
                cell_ids=tuple(cell_ids),
                total_size=kinetic_layout_state_size,
            )

            def kinetic_unpack_trial(values):
                vector = np.asarray(values, dtype=float)
                if vector.shape != (kinetic_layout_state_size,) or not np.isfinite(vector).all():
                    raise ValueError("kinetic physical state shape or finiteness mismatch")
                totals = vector[:n_component_state].reshape(ncomp, nc)
                solids = vector[n_component_state:].reshape(phase_count, nc)
                if np.any(solids < -request.absolute_solid_inventory_tolerance_mol):
                    raise ValueError("kinetic solid state is below the declared negative tolerance")
                return totals, solids

            class _KineticEventRHS:
                layout = kinetic_layout
                nucleation_phase_major = True
                nucleation = tuple(
                    tuple(phase_set.nucleation_laws[j] for phase_set in kinetic_phase_sets)
                    for j in range(phase_count)
                )
                volumes = tuple(float(cell.solution_volume_L) / 1000.0 for cell in request.cells)
                evaluations = 0

                def unpack_trial(self, values):
                    return kinetic_unpack_trial(values)

                def __call__(self, time_s, values):
                    self.evaluations += 1
                    if self.evaluations > request.maximum_total_rhs_evaluations:
                        raise RuntimeError("component_state_bdf_rhs_budget_exceeded")
                    return rhs(time_s, np.asarray(values, dtype=float))

                def set_seed_modes_at_boundary(self, modes):
                    nonlocal kinetic_seed_modes
                    if len(modes) != phase_count or any(len(row) != nc for row in modes):
                        raise ValueError("kinetic event seed-mode shape mismatch")
                    kinetic_seed_modes = [list(row) for row in modes]

                def threshold_inventory(self, phase_index, cell_index, time_s, integration_state):
                    concentration = np.asarray(integration_state[:n_component_state], dtype=float).reshape(ncomp, nc)
                    solids = np.asarray(integration_state[n_component_state:kinetic_layout_state_size], dtype=float).reshape(
                        nkinetic_phase, nc
                    )
                    if dynamic_geometry:
                        geometry = request.dynamic_solid_geometry_by_cell[cell_index]
                        section = float(geometry.cell_length_m) * float(geometry.transverse_width_m)
                        geometry_by_phase = {row.solid_species_id: row for row in geometry.phase_geometry}
                        occupied = math.fsum(
                            float(solids[kinetic_phase_index[phase_id], cell_index])
                            * float(geometry_by_phase[phase_id].molar_volume_m3_mol)
                            for phase_id in kinetic_phase_ids if geometry_by_phase[phase_id].occupies_gap
                        )
                        aperture = float(geometry.initial_aperture_m) - occupied / section
                        if not math.isfinite(aperture) or aperture < float(geometry.minimum_aperture_m):
                            raise RuntimeError("kinetic_seed_threshold_aperture_below_minimum")
                        volume_m3 = section * aperture
                    else:
                        volume_m3 = float(request.cells[cell_index].solution_volume_L) / 1000.0
                    amount = float(self.nucleation[phase_index][cell_index].nucleated_inventory_threshold_mol_m3) * volume_m3
                    if not math.isfinite(amount) or amount <= 0.0:
                        raise ArithmeticError("kinetic seed threshold amount is not finite and positive")
                    return amount

            kinetic_event_rhs = _KineticEventRHS()
        else:
            kinetic_event_rhs = None
        kinetic_rate_evaluations = 0
        maximum_kinetic_phase_rate_mol_s = 0.0
        kinetic_rate_records_by_time: dict[float, list[dict]] = {}

        def _solid_partition_at_volume(template, component_mol, phase_set, solution_volume_L):
            from .crevice_component_solid_partition import (
                ComponentTotalInventory,
                CreviceComponentSolidPartitionRequest,
                solve_crevice_component_solid_partition,
            )
            nonlocal equilibrium_calls, nested_equilibrium_work_bound
            nonlocal solid_partition_evaluations, solid_active_set_sweeps, solid_bisection_iterations
            remaining_eq = request.maximum_total_stage_equilibrium_calls - equilibrium_calls
            remaining_work = request.maximum_total_nested_equilibrium_iteration_work - nested_equilibrium_work_bound
            remaining_sweeps = request.maximum_total_solid_active_set_sweeps - solid_active_set_sweeps
            remaining_bisections = request.maximum_total_solid_bisection_iterations - solid_bisection_iterations
            if (solid_partition_evaluations >= request.maximum_total_solid_partition_evaluations
                    or min(remaining_eq, remaining_work, remaining_sweeps, remaining_bisections) < 1):
                raise RuntimeError("stage_solid_partition_aggregate_work_budget_exceeded")
            stage_template = template.model_copy(update={"solution_volume_L": float(solution_volume_L)})
            partition_request = CreviceComponentSolidPartitionRequest(
                assessment_id=f"{request.assessment_id}:{phase_set.phase_set_id}",
                cell=stage_template,
                total_component_inventory=tuple(ComponentTotalInventory(component_id=key, total_moles=value)
                                                for key, value in component_mol.items()),
                phase_candidates=phase_set.phase_candidates,
                log_saturation_tolerance=request.solid_equilibrium_log_saturation_tolerance,
                relative_partition_tolerance=request.relative_tolerance,
                maximum_active_set_sweeps=min(100, remaining_sweeps),
                maximum_total_aqueous_equilibrium_calls=min(2_000_000, remaining_eq),
                maximum_total_nested_equilibrium_iteration_work=remaining_work,
                maximum_bisection_iterations_per_phase_update=min(100, max(8, remaining_bisections)),
                maximum_total_bisection_iterations=min(20_000_000, remaining_bisections),
                total_inventory_includes_all_candidate_solids_reviewed=True,
                candidate_phase_set_complete_for_declared_scope_reviewed=True,
                equilibrium_constants_and_activity_basis_applicable_reviewed=True,
                instantaneous_equilibrium_and_no_nucleation_barrier_reviewed=True,
                computational_use_authorized=request.computational_use_authorized,
            )
            stage_result = solve_crevice_component_solid_partition(partition_request)
            solid_partition_evaluations += 1
            equilibrium_calls += int(stage_result.values.get("aqueous_equilibrium_calls", 0))
            nested_equilibrium_work_bound += int(stage_result.values.get("nested_equilibrium_iteration_work_bound", 0))
            solid_active_set_sweeps += int(stage_result.values.get("active_set_sweeps", 0))
            solid_bisection_iterations += int(stage_result.values.get("bisection_iterations", 0))
            if stage_result.status != "computed" or not stage_result.values.get("committed", False):
                raise RuntimeError(f"stage_solid_partition_failed:{template.cell_id}:"
                                   f"{stage_result.values.get('reason', stage_result.status)}")
            return stage_template, stage_result

        def kinetic_component_exchange(cell_index: int, phase_rate_by_id: dict[str, float]):
            exchange = np.zeros(ncomp, dtype=float)
            solid_exchange_by_phase = {}
            for phase in kinetic_phase_sets[cell_index].phase_candidates:
                phase_rate = float(phase_rate_by_id[phase.solid_species_id])
                species_extent = np.asarray([phase.aqueous_reactant_stoichiometry.get(sid, 0.0)
                                             for sid in species_ids], dtype=float)
                component_extent = component_coefficient @ species_extent
                element_extent = component_element_coefficient @ component_extent
                expected_elements = np.asarray([phase.solid_elemental_composition.get(element, 0)
                                                for element in element_ids], dtype=float)
                if np.any(np.abs(element_extent - expected_elements) >
                          1e-10 * np.maximum(1.0, np.abs(expected_elements))):
                    raise RuntimeError("kinetic_phase_component_basis_does_not_conserve_elements")
                aqueous_species_by_id = {
                    row.species_id: row for row in request.cells[cell_index].aqueous_activity_request.system.species
                }
                charge_extent = math.fsum(
                    float(aqueous_species_by_id[sid].charge_number) * float(coefficient)
                    for sid, coefficient in phase.aqueous_reactant_stoichiometry.items()
                )
                if not math.isclose(charge_extent, 0.0, rel_tol=0.0, abs_tol=1e-12):
                    raise RuntimeError("kinetic_phase_charge_stoichiometry_not_conserved")
                exchange += component_extent * phase_rate
                solid_exchange_by_phase[phase.solid_species_id] = component_extent * phase_rate
            return exchange, solid_exchange_by_phase

        def equilibrate_cells(component_inventory: np.ndarray, time_s: float, kinetic_solid_inventory=None):
            nonlocal equilibrium_calls, lineage_chain, last_stage_summary, nested_equilibrium_work_bound
            nonlocal solid_partition_evaluations, solid_active_set_sweeps, solid_bisection_iterations
            nonlocal maximum_dynamic_geometry_residual
            nonlocal dynamic_geometry_iterations
            if not solid_mode and equilibrium_calls + nc > request.maximum_total_stage_equilibrium_calls:
                raise RuntimeError("stage_equilibrium_call_budget_exceeded")
            if solid_mode and solid_partition_evaluations + nc > request.maximum_total_solid_partition_evaluations:
                raise RuntimeError("stage_solid_partition_evaluation_budget_exceeded")
            concentration_mol_m3_by_cell = []
            gamma_by_cell = []
            cell_result_digests = []
            cell_partition_results = []
            dynamic_geometry_by_cell = []
            for cell_index, template in enumerate(request.cells):
                component_mol = {
                    component_ids[i]: float(component_inventory[i, cell_index]) for i in range(ncomp)
                }
                if kinetic_mode:
                    solid_moles = np.asarray(kinetic_solid_inventory[:, cell_index], dtype=float)
                    aqueous_component = component_inventory[:, cell_index].copy()
                    solid_component = np.zeros(ncomp, dtype=float)
                    for phase in kinetic_phase_sets[cell_index].phase_candidates:
                        phase_index = kinetic_phase_index[phase.solid_species_id]
                        extent = np.asarray([phase.aqueous_reactant_stoichiometry.get(sid, 0.0)
                                             for sid in species_ids], dtype=float)
                        component_extent = component_coefficient @ extent
                        solid_component += component_extent * solid_moles[phase_index]
                    aqueous_component -= solid_component
                    if (not np.isfinite(aqueous_component).all() or np.any(aqueous_component < 0.0)):
                        raise RuntimeError(f"kinetic_aqueous_component_inventory_negative:{template.cell_id}")
                    volume_L = float(template.solution_volume_L)
                    dynamic_detail = None
                    if dynamic_geometry:
                        geometry = request.dynamic_solid_geometry_by_cell[cell_index]
                        cross_section_m2 = float(geometry.cell_length_m) * float(geometry.transverse_width_m)
                        phase_geometry = {row.solid_species_id: row for row in geometry.phase_geometry}
                        solid_volume_m3 = math.fsum(
                            float(solid_moles[kinetic_phase_index[phase_id]])
                            * float(phase_geometry[phase_id].molar_volume_m3_mol)
                            for phase_id in kinetic_phase_ids if phase_geometry[phase_id].occupies_gap
                        )
                        aperture = float(geometry.initial_aperture_m) - solid_volume_m3 / cross_section_m2
                        if aperture < float(geometry.minimum_aperture_m) or not math.isfinite(aperture):
                            raise RuntimeError(f"kinetic_dynamic_geometry_aperture_below_minimum:{template.cell_id}")
                        volume_L = cross_section_m2 * aperture * 1000.0
                        dynamic_detail = {
                            "cell_id": template.cell_id,
                            "geometry_sha256": geometry.geometry_sha256,
                            "aperture_m": aperture,
                            "solution_volume_L": volume_L,
                            "solid_gap_occupancy_volume_m3": solid_volume_m3,
                            "kinetic_inventory_geometry": True,
                        }
                    stage_request = _stage_system(template.model_copy(update={"solution_volume_L": volume_L}),
                                                  {key: float(aqueous_component[i]) for i, key in enumerate(component_ids)})
                    per_call_work_bound = template.aqueous_activity_request.maximum_outer_iterations * (
                        template.aqueous_activity_request.system.maximum_iterations + 1
                    )
                    if equilibrium_calls + 1 > request.maximum_total_stage_equilibrium_calls or \
                            nested_equilibrium_work_bound + per_call_work_bound > request.maximum_total_nested_equilibrium_iteration_work:
                        raise RuntimeError("kinetic_stage_equilibrium_work_budget_exceeded")
                    stage_result = aqueous_davies_self_consistent_speciation(stage_request)
                    equilibrium_calls += 1
                    nested_equilibrium_work_bound += per_call_work_bound
                    if stage_result.status != "computed":
                        raise RuntimeError(
                            f"kinetic_stage_aqueous_equilibrium_failed:{template.cell_id}:"
                            f"{stage_result.values.get('out_of_scope_reason', stage_result.status)}"
                        )
                    rows = stage_result.values.get("species")
                    expected = tuple(row.species_id for row in template.aqueous_activity_request.system.species)
                    if not isinstance(rows, (list, tuple)) or tuple(row.get("species_id") for row in rows) != expected:
                        raise RuntimeError(f"kinetic_stage_species_output_identity_mismatch:{template.cell_id}")
                    values = np.asarray([float(row["concentration_mol_L"]) * 1000.0 for row in rows], dtype=float)
                    gamma = np.asarray([float(row["activity_coefficient"]) for row in rows], dtype=float)
                    if not np.isfinite(values).all() or np.any(values <= 0.0) or not np.isfinite(gamma).all() or np.any(gamma <= 0.0):
                        raise RuntimeError(f"kinetic_stage_species_state_invalid:{template.cell_id}")
                    concentration_mol_m3_by_cell.append(values)
                    gamma_by_cell.append(gamma)
                    phase_details = []
                    activities = {sid: float(gamma[i] * values[i] / 1000.0)
                                  for i, sid in enumerate(species_ids)}
                    for phase_index, phase in enumerate(kinetic_phase_sets[cell_index].phase_candidates):
                        phase_details.append({
                            "solid_species_id": phase.solid_species_id,
                            "solid_moles": float(solid_moles[phase_index]),
                            "solid_component_inventory_mol": {
                                component_ids[i]: float((component_coefficient @ np.asarray([
                                    phase.aqueous_reactant_stoichiometry.get(sid, 0.0) for sid in species_ids
                                ], dtype=float))[i] * solid_moles[phase_index])
                                for i in range(ncomp)
                            },
                        })
                    aqueous_by_component = {key: float(aqueous_component[i]) for i, key in enumerate(component_ids)}
                    solid_by_component = {key: float(solid_component[i]) for i, key in enumerate(component_ids)}
                    total_by_component = {key: float(component_inventory[i, cell_index]) for i, key in enumerate(component_ids)}
                    partition = {
                        "cell_id": template.cell_id,
                        "phase_set_id": kinetic_phase_sets[cell_index].phase_set_id,
                        "phase_set_sha256": kinetic_phase_sets[cell_index].phase_set_sha256,
                        "solution_volume_L": volume_L,
                        "aqueous_component_inventory_mol": aqueous_by_component,
                        "solid_component_inventory_mol": solid_by_component,
                        "solid_phase_results": phase_details,
                        "kinetic_phase_set": True,
                        "dynamic_geometry": dynamic_detail,
                        "total_component_inventory_mol": total_by_component,
                    }
                    cell_partition_results.append(partition)
                    dynamic_geometry_by_cell.append(dynamic_detail)
                    stage_input_sha = canonical_digest(stage_request.model_dump(mode="json"))
                elif solid_mode:
                    phase_set = phase_set_by_cell[template.cell_id]
                    dynamic_detail = None
                    if dynamic_geometry:
                        geometry = request.dynamic_solid_geometry_by_cell[cell_index]
                        cross_section_m2 = float(geometry.cell_length_m) * float(geometry.transverse_width_m)
                        base_volume_L = cross_section_m2 * float(geometry.initial_aperture_m) * 1000.0
                        min_volume_L = cross_section_m2 * float(geometry.minimum_aperture_m) * 1000.0
                        phase_map = {row.solid_species_id: row for row in geometry.phase_geometry}
                        volume_guess_L = base_volume_L
                        history = []
                        converged = False
                        for _geometry_iteration in range(max(1, request.maximum_dynamic_geometry_iterations_per_cell_stage - 1)):
                            if dynamic_geometry_iterations >= request.maximum_total_dynamic_geometry_iterations:
                                raise RuntimeError("dynamic_geometry_total_iteration_budget_exceeded")
                            dynamic_geometry_iterations += 1
                            stage_template, stage_result = _solid_partition_at_volume(
                                template, component_mol, phase_set, volume_guess_L
                            )
                            solid_m3 = 0.0
                            phase_moles = {}
                            for phase_row in stage_result.values["solid_phase_results"]:
                                phase_id = phase_row["solid_species_id"]
                                amount_mol = float(phase_row["solid_mol"])
                                phase_moles[phase_id] = amount_mol
                                if phase_map[phase_id].occupies_gap:
                                    solid_m3 += amount_mol * float(phase_map[phase_id].molar_volume_m3_mol)
                            target_aperture_m = float(geometry.initial_aperture_m) - solid_m3 / cross_section_m2
                            if not math.isfinite(target_aperture_m) or target_aperture_m < float(geometry.minimum_aperture_m):
                                raise RuntimeError(f"dynamic_geometry_aperture_below_minimum:{template.cell_id}")
                            target_volume_L = cross_section_m2 * target_aperture_m * 1000.0
                            residual = abs(target_volume_L - volume_guess_L) / max(base_volume_L, 1e-300)
                            history.append({"iteration": dynamic_geometry_iterations,
                                            "trial_solution_volume_L": volume_guess_L,
                                            "target_solution_volume_L": target_volume_L,
                                            "target_aperture_m": target_aperture_m,
                                            "normalized_volume_residual": residual,
                                            "solid_moles_by_phase": phase_moles})
                            if residual <= float(request.dynamic_geometry_relative_tolerance):
                                converged = True
                                dynamic_detail = {"cell_id": template.cell_id,
                                                  "geometry_sha256": geometry.geometry_sha256,
                                                  "geometry_source_id": geometry.geometry_source_id,
                                                  "solution_volume_L": target_volume_L,
                                                  "aperture_m": target_aperture_m,
                                                  "cross_section_area_m2": float(geometry.transverse_width_m) * target_aperture_m,
                                                  "normalized_fixed_point_residual": residual,
                                                  "iterations": len(history), "iteration_history": history}
                                # Re-evaluate at the reported target volume so returned chemistry is consistent.
                                if dynamic_geometry_iterations >= request.maximum_total_dynamic_geometry_iterations:
                                    raise RuntimeError("dynamic_geometry_total_iteration_budget_exceeded")
                                dynamic_geometry_iterations += 1
                                stage_template, stage_result = _solid_partition_at_volume(
                                    template, component_mol, phase_set, target_volume_L
                                )
                                final_solid_m3 = math.fsum(
                                    float(row["solid_mol"]) * float(phase_map[row["solid_species_id"]].molar_volume_m3_mol)
                                    for row in stage_result.values["solid_phase_results"]
                                    if phase_map[row["solid_species_id"]].occupies_gap
                                )
                                final_aperture_m = float(geometry.initial_aperture_m) - final_solid_m3 / cross_section_m2
                                if not math.isfinite(final_aperture_m) or final_aperture_m < float(geometry.minimum_aperture_m):
                                    raise RuntimeError(f"dynamic_geometry_aperture_below_minimum:{template.cell_id}")
                                final_target_volume_L = cross_section_m2 * final_aperture_m * 1000.0
                                final_residual = abs(final_target_volume_L - target_volume_L) / max(base_volume_L, 1e-300)
                                maximum_dynamic_geometry_residual = max(maximum_dynamic_geometry_residual, final_residual)
                                if final_residual > float(request.dynamic_geometry_relative_tolerance):
                                    raise RuntimeError(f"dynamic_geometry_final_closure_failed:{template.cell_id}")
                                history.append({"iteration": dynamic_geometry_iterations,
                                                "trial_solution_volume_L": float(stage_template.solution_volume_L),
                                                "target_solution_volume_L": final_target_volume_L,
                                                "target_aperture_m": final_aperture_m,
                                                "normalized_volume_residual": final_residual,
                                                "solid_moles_by_phase": {
                                                    row["solid_species_id"]: float(row["solid_mol"])
                                                    for row in stage_result.values["solid_phase_results"]
                                                },
                                                "final_closure_recheck": True})
                                dynamic_detail["normalized_fixed_point_residual"] = final_residual
                                dynamic_detail["aperture_m"] = final_aperture_m
                                dynamic_detail["cross_section_area_m2"] = float(geometry.transverse_width_m) * final_aperture_m
                                dynamic_detail["final_partition_solution_volume_L"] = float(stage_template.solution_volume_L)
                                dynamic_detail["iterations"] = len(history)
                                break
                            alpha = float(request.dynamic_geometry_relaxation_factor)
                            volume_guess_L = min(base_volume_L, max(min_volume_L,
                                                 volume_guess_L + alpha * (target_volume_L - volume_guess_L)))
                        if not converged:
                            raise RuntimeError(f"dynamic_geometry_fixed_point_budget_or_convergence_failed:{template.cell_id}")
                        dynamic_geometry_by_cell.append(dynamic_detail)
                    else:
                        stage_template, stage_result = _solid_partition_at_volume(
                            template, component_mol, phase_set, float(template.solution_volume_L)
                        )
                    rows = stage_result.values.get("aqueous_species")
                    expected = tuple(row.species_id for row in template.aqueous_activity_request.system.species)
                    cell_partition_results.append({
                        "cell_id": template.cell_id,
                        "phase_set_id": phase_set.phase_set_id,
                        "phase_set_sha256": phase_set.phase_set_sha256,
                        "material_condition_id": phase_set.material_condition_id,
                        "metallurgy_id": phase_set.metallurgy_id,
                        "environment_id": phase_set.environment_id,
                        "temperature_K": phase_set.temperature_K,
                        "solution_volume_L": float(stage_template.solution_volume_L),
                        "activity_standard_state_id": phase_set.activity_standard_state_id,
                        "phase_set_evidence_sha256": canonical_digest([
                            row.model_dump(mode="json") for row in phase_set.phase_set_evidence
                        ]),
                        "aqueous_component_inventory_mol": stage_result.values["aqueous_component_inventory_mol"],
                        "solid_component_inventory_mol": stage_result.values["solid_component_inventory_mol"],
                        "solid_phase_results": stage_result.values["solid_phase_results"],
                        "partition_input_sha256": stage_result.values["input_sha256"],
                        "partition_result_sha256": canonical_digest(stage_result.model_dump(mode="json")),
                        "dynamic_geometry": dynamic_detail,
                    })
                    stage_input_sha = stage_result.values["input_sha256"]
                else:
                    stage_request = _stage_system(template, component_mol)
                    per_call_work_bound = template.aqueous_activity_request.maximum_outer_iterations * (
                        template.aqueous_activity_request.system.maximum_iterations + 1
                    )
                    if nested_equilibrium_work_bound + per_call_work_bound > \
                            request.maximum_total_nested_equilibrium_iteration_work:
                        raise RuntimeError("stage_nested_equilibrium_iteration_work_budget_exceeded")
                    stage_result = aqueous_davies_self_consistent_speciation(stage_request)
                    equilibrium_calls += 1
                    nested_equilibrium_work_bound += per_call_work_bound
                    if stage_result.status != "computed":
                        raise RuntimeError(
                            f"stage_aqueous_equilibrium_failed:{template.cell_id}:"
                            f"{stage_result.values.get('out_of_scope_reason', stage_result.values.get('missing_reviews', stage_result.status))}"
                        )
                    rows = stage_result.values.get("species")
                    expected = tuple(row.species_id for row in stage_request.system.species)
                    stage_input_sha = canonical_digest(stage_request.model_dump(mode="json"))
                    cell_partition_results.append(None)
                if not isinstance(rows, (list, tuple)) or tuple(row.get("species_id") for row in rows) != expected:
                    raise RuntimeError(f"stage_species_output_identity_mismatch:{template.cell_id}")
                values = np.asarray([float(row["concentration_mol_L"]) * 1000.0 for row in rows], dtype=float)
                gamma = np.asarray([float(row["activity_coefficient"]) for row in rows], dtype=float)
                if (not np.isfinite(values).all() or np.any(values <= 0.0)
                        or not np.isfinite(gamma).all() or np.any(gamma <= 0.0)):
                    raise RuntimeError(f"stage_species_concentrations_invalid:{template.cell_id}")
                concentration_mol_m3_by_cell.append(values)
                gamma_by_cell.append(gamma)
                result_sha = canonical_digest(stage_result.model_dump(mode="json"))
                input_sha = stage_input_sha
                lineage_chain = canonical_digest({
                    "previous_chain_sha256": lineage_chain,
                    "time_s": float(time_s),
                    "cell_id": template.cell_id,
                    "stage_input_sha256": input_sha,
                    "stage_result_sha256": result_sha,
                })
                cell_result_digests.append({"cell_id": template.cell_id,
                                            "input_sha256": input_sha,
                                            "result_sha256": result_sha,
                                            "solid_partition": cell_partition_results[-1]})
            stage_face_area = face_area
            if dynamic_geometry:
                cell_cross_section = np.asarray([row["cross_section_area_m2"] for row in dynamic_geometry_by_cell], dtype=float)
                stage_face_area = np.asarray([
                    cell_cross_section[face] + (0.5 * float(request.dynamic_solid_geometry_by_cell[face].cell_length_m)
                        / center_distance[face]) * (cell_cross_section[face + 1] - cell_cross_section[face])
                    for face in range(nc - 1)
                ], dtype=float)
                if not np.isfinite(stage_face_area).all() or np.any(stage_face_area <= 0.0):
                    raise RuntimeError("dynamic_geometry_interior_face_area_invalid")
            last_stage_summary = {"time_s": float(time_s), "cells": cell_result_digests,
                                  "moving_geometry_mode": request.moving_geometry_mode,
                                  "dynamic_geometry": dynamic_geometry_by_cell}
            return (np.asarray(concentration_mol_m3_by_cell, dtype=float),
                    np.asarray(gamma_by_cell, dtype=float), cell_partition_results, stage_face_area)

        def moving_liquid_volume_probe(component_inventory: np.ndarray, time_s: float) -> np.ndarray:
            """Re-evaluate trial solid geometry without extending committed stage lineage."""
            nonlocal lineage_chain, last_stage_summary
            old_lineage = lineage_chain
            old_summary = last_stage_summary
            try:
                _, _, partitions, _ = equilibrate_cells(component_inventory, time_s)
            finally:
                lineage_chain = old_lineage
                last_stage_summary = old_summary
            if len(partitions) != nc or any(row is None for row in partitions):
                raise RuntimeError("dynamic_volume_probe_requires_committed_cell_solid_partitions")
            volumes = np.asarray([float(row["solution_volume_L"]) / 1000.0 for row in partitions], dtype=float)
            if not np.isfinite(volumes).all() or np.any(volumes <= 0.0):
                raise RuntimeError("dynamic_volume_probe_returned_invalid_liquid_volume")
            return volumes

        def directional_dynamic_volume_rate(
            component_inventory: np.ndarray,
            component_rate: np.ndarray,
            base_volume_L: np.ndarray,
            time_s: float,
        ) -> np.ndarray:
            """Approximate dV/dt along the current BDF component-state RHS direction."""
            rate_scale = float(np.max(np.abs(component_rate)))
            if rate_scale == 0.0:
                return np.zeros(nc, dtype=float)
            inventory_scale = float(np.max(np.abs(component_inventory)))
            characteristic_time = min(float(times[-1] - times[0]),
                                      max(1e-12, inventory_scale / rate_scale))
            step = max(1e-12, 2e-5 * characteristic_time)
            y = np.asarray(component_inventory, dtype=float)
            f = np.asarray(component_rate, dtype=float)
            negative_direction = f < 0.0
            if np.any(negative_direction):
                available = y[negative_direction] / (-f[negative_direction])
                positive_available = available[available > 0.0]
                if positive_available.size:
                    step = min(step, 0.25 * float(np.min(positive_available)))
            if not math.isfinite(step) or step <= 0.0:
                raise RuntimeError("dynamic_volume_directional_step_is_not_representable")
            plus = y + step * f
            if np.any(plus < 0.0) or not np.isfinite(plus).all():
                raise RuntimeError("dynamic_volume_forward_probe_left_nonnegative_inventory_domain")
            base = np.asarray(base_volume_L, dtype=float) / 1000.0
            if np.all(y - step * f >= 0.0):
                minus = y - step * f
                v_plus = moving_liquid_volume_probe(plus, time_s)
                v_minus = moving_liquid_volume_probe(minus, time_s)
                derivative = (v_plus - v_minus) / (2.0 * step)
            else:
                v_plus = moving_liquid_volume_probe(plus, time_s)
                derivative = (v_plus - base) / step
            if not np.isfinite(derivative).all():
                raise RuntimeError("dynamic liquid-volume directional derivative is nonfinite")
            return derivative

        def kinetic_cell_volumes_m3(kinetic_solid_inventory: np.ndarray) -> np.ndarray:
            volumes = []
            for cell_index, geometry in enumerate(request.dynamic_solid_geometry_by_cell):
                cross_section = float(geometry.cell_length_m) * float(geometry.transverse_width_m)
                geometry_by_phase = {row.solid_species_id: row for row in geometry.phase_geometry}
                solid_volume = math.fsum(
                    float(kinetic_solid_inventory[kinetic_phase_index[phase_id], cell_index])
                    * float(geometry_by_phase[phase_id].molar_volume_m3_mol)
                    for phase_id in kinetic_phase_ids if geometry_by_phase[phase_id].occupies_gap
                )
                aperture = float(geometry.initial_aperture_m) - solid_volume / cross_section
                if aperture < float(geometry.minimum_aperture_m) or not math.isfinite(aperture):
                    raise RuntimeError("kinetic_dynamic_geometry_aperture_below_minimum")
                volumes.append(cross_section * aperture)
            return np.asarray(volumes, dtype=float)

        def directional_kinetic_volume_rate(
            solid_inventory: np.ndarray, solid_rate: np.ndarray, _base_volume_L: np.ndarray
        ) -> np.ndarray:
            if not kinetic_mode or not dynamic_geometry:
                raise RuntimeError("kinetic_volume_rate_requires_kinetic_dynamic_geometry")
            derivative = np.zeros(nc, dtype=float)
            for cell_index, geometry in enumerate(request.dynamic_solid_geometry_by_cell):
                cross_section = float(geometry.cell_length_m) * float(geometry.transverse_width_m)
                geometry_by_phase = {row.solid_species_id: row for row in geometry.phase_geometry}
                occupied_rate = math.fsum(
                    float(solid_rate[kinetic_phase_index[phase_id], cell_index])
                    * float(geometry_by_phase[phase_id].molar_volume_m3_mol)
                    for phase_id in kinetic_phase_ids if geometry_by_phase[phase_id].occupies_gap
                )
                derivative[cell_index] = -occupied_rate
            if not np.isfinite(derivative).all():
                raise RuntimeError("kinetic_dynamic_volume_rate_nonfinite")
            return derivative

        def interpolate_source_extent_rates(time_s: float):
            if nsource == 0:
                return np.zeros((0, nc), dtype=float)
            if time_s <= times[0]:
                return source_extent_knots[:, 0, :]
            if time_s >= times[-1]:
                return source_extent_knots[:, -1, :]
            time_index = int(np.searchsorted(times, time_s, side="right") - 1)
            fraction = (time_s - times[time_index]) / (times[time_index + 1] - times[time_index])
            return source_extent_knots[:, time_index, :] + fraction * (
                source_extent_knots[:, time_index + 1, :] - source_extent_knots[:, time_index, :]
            )

        def interpolate_capacitive_current(time_s: float):
            if request.capacitive_current_schedule is None:
                return np.zeros(nc, dtype=float)
            if time_s <= times[0]:
                return capacitive_current_knots[0]
            if time_s >= times[-1]:
                return capacitive_current_knots[-1]
            time_index = int(np.searchsorted(times, time_s, side="right") - 1)
            fraction = (time_s - times[time_index]) / (times[time_index + 1] - times[time_index])
            return capacitive_current_knots[time_index] + fraction * (
                capacitive_current_knots[time_index + 1] - capacitive_current_knots[time_index]
            )

        def interpolate_ionic_face_current(time_s: float):
            if time_s <= times[0]:
                return ionic_current_knots[0]
            if time_s >= times[-1]:
                return ionic_current_knots[-1]
            time_index = int(np.searchsorted(times, time_s, side="right") - 1)
            fraction = (time_s - times[time_index]) / (times[time_index + 1] - times[time_index])
            return ionic_current_knots[time_index] + fraction * (
                ionic_current_knots[time_index + 1] - ionic_current_knots[time_index]
            )

        def evaluate_stage_mixed_potential(
            concentration, gamma, time_s: float, *, double_layer_charge_C=None, record_knot=False
        ):
            nonlocal stage_mixed_potential_evaluations, lineage_chain
            if not faradaic_stage:
                return None, interpolate_ionic_face_current(time_s), None, None
            coupling = request.faradaic_stage_coupling
            faradaic_transport = coupling.transport_chemistry.transport.transport_request
            if time_s <= times[0]:
                interval_index, fraction = 0, 0.0
            elif time_s >= times[-1]:
                interval_index, fraction = nt - 2, 1.0
            else:
                interval_index = int(np.searchsorted(times, time_s, side="right") - 1)
                fraction = (time_s - times[interval_index]) / (times[interval_index + 1] - times[interval_index])
            initial_by_species = {
                species_id: concentration[:, species_index[species_id]].tolist()
                for species_id in species_ids
            }
            gamma_by_cell = [
                {species_id: float(gamma[cell, species_index[species_id]]) for species_id in species_ids}
                for cell in range(nc)
            ]
            sub_variable, _ = _subinterval_request(
                coupling.transport_chemistry, interval_index, initial_by_species, gamma_by_cell
            )
            remaining = (request.maximum_total_stage_mixed_potential_function_evaluations
                         - stage_mixed_potential_evaluations)
            if dynamic_double_layer is not None:
                if double_layer_charge_C is None or np.asarray(double_layer_charge_C).shape != (nc,):
                    raise RuntimeError("dynamic_double_layer_charge_state_shape_mismatch")
                mixed_result, mixed_request = _solve_spatial_mixed_potential_at_stage(
                    coupling, sub_variable, interval_index, fraction,
                    concentration.T, np.log(gamma.T), remaining,
                    solve_mixed_potential=False,
                )
            else:
                if remaining < 100:
                    raise RuntimeError("stage_mixed_potential_function_evaluation_budget_exceeded")
                mixed_result, mixed_request = _solve_spatial_mixed_potential_at_stage(
                    coupling, sub_variable, interval_index, fraction,
                    concentration.T, np.log(gamma.T), remaining,
                )
            if dynamic_double_layer is not None:
                cap_axis = dynamic_double_layer.differential_capacitance_potential_axis_V
                cap_values = tuple(float(value) for value in dynamic_double_layer.differential_capacitance_F_m2)
                interfacial_potential = np.asarray([
                    _double_layer_potential_from_charge_density(
                        float(double_layer_charge_C[cell]) / double_layer_area_m2[cell],
                        float(dynamic_double_layer.reference_interfacial_potential_V_by_cell[cell]),
                        cap_axis, cap_values, double_layer_capacitance_cumulative,
                    ) for cell in range(nc)
                ], dtype=float)
                temperature = float(mixed_request.temperature_K_by_time[0])
                branch_current = {}
                total_current = np.zeros(nc, dtype=float)
                source_rate = np.zeros((nsource, nc), dtype=float)
                branch_index = {reaction_id: index for index, reaction_id in enumerate(source_ids)}
                reactive_area = (np.asarray(mixed_request.cell_lengths_m, dtype=float)
                                 * float(mixed_request.slit_width_m)
                                 * int(mixed_request.reactive_face_count))
                for branch in mixed_request.branches:
                    currents = np.zeros(nc, dtype=float)
                    for cell in range(nc):
                        equilibrium = float(branch.equilibrium_potential_V_by_cell_and_time[cell][0])
                        overpotential = float(interfacial_potential[cell]) - equilibrium
                        if not branch.minimum_overpotential_V <= overpotential <= branch.maximum_overpotential_V:
                            raise RuntimeError("dynamic_double_layer_branch_overpotential_outside_caller_support")
                        currents[cell] = _branch_current_density(
                            branch, cell, 0, float(interfacial_potential[cell]), 0.0, temperature
                        )
                    branch_current[branch.reaction_id] = currents
                    total_current += reactive_area * currents
                    source_rate[branch_index[branch.reaction_id]] = (
                        reactive_area * currents / (branch.electron_number * FARADAY_CONSTANT_C_MOL)
                    )
                if np.any(np.abs(source_rate) > request.maximum_absolute_stage_faradaic_extent_rate_mol_s):
                    raise RuntimeError("stage_faradaic_extent_rate_exceeds_caller_bound")
                conductivity = np.asarray([
                    float(row[0]) for row in mixed_request.electrolyte_conductivity_S_m_by_cell_and_time
                ], dtype=float)
                aperture = np.asarray(mixed_request.cell_apertures_m, dtype=float)
                lengths = np.asarray(mixed_request.cell_lengths_m, dtype=float)
                centers = np.cumsum(lengths) - 0.5 * lengths
                face_spacing = np.diff(centers)
                face_k = 2.0 * conductivity[:-1] * conductivity[1:] / (conductivity[:-1] + conductivity[1:])
                face_h = 2.0 * aperture[:-1] * aperture[1:] / (aperture[:-1] + aperture[1:])
                face_area_ohmic = face_h * float(mixed_request.slit_width_m)
                interior_current = face_k * face_area_ohmic / face_spacing * np.diff(interfacial_potential)
                face_current = np.concatenate(([0.0], interior_current, [0.0]))
                double_layer_current = face_current[1:] - face_current[:-1] - total_current
                if not np.isfinite(double_layer_current).all():
                    raise RuntimeError("dynamic_double_layer_current_rate_nonfinite")
                aqueous_charge_rate = np.zeros(nc, dtype=float)
                for source_index, metadata in enumerate(source_metadata):
                    charge_per_extent = math.fsum(
                        charges[species_index[sid]] * coefficient
                        for sid, coefficient in metadata["species_stoichiometry"].items()
                    )
                    aqueous_charge_rate += charge_per_extent * source_rate[source_index]
                charge_residual = face_current[1:] - face_current[:-1] \
                    - FARADAY_CONSTANT_C_MOL * aqueous_charge_rate - double_layer_current
                allowed = coupling.current_balance_tolerance_A + request.relative_face_current_closure_tolerance * np.maximum(
                    np.maximum(np.abs(face_current[1:]), np.abs(face_current[:-1])),
                    np.maximum(np.abs(total_current), FARADAY_CONSTANT_C_MOL * np.abs(aqueous_charge_rate)),
                )
                if np.any(np.abs(charge_residual) > allowed):
                    raise RuntimeError("dynamic_double_layer_faradaic_charge_continuity_failed")
                if record_knot:
                    stage_mixed_knot_lineage.append({
                        "time_s": float(time_s),
                        "input_sha256": canonical_digest(mixed_request.model_dump(mode="json")),
                        "dynamic_double_layer_charge_C_by_cell": np.asarray(double_layer_charge_C).tolist(),
                        "interfacial_potential_V_by_cell": interfacial_potential.tolist(),
                        "face_current_A_by_boundary": face_current.tolist(),
                        "branch_current_density_A_m2_by_branch_and_cell": {
                            reaction_id: values.tolist() for reaction_id, values in branch_current.items()
                        },
                        "faradaic_current_A_by_cell": total_current.tolist(),
                        "capacitive_current_A_by_cell": double_layer_current.tolist(),
                        "charge_continuity_residual_A_by_cell": charge_residual.tolist(),
                    })
                return source_rate, face_current, double_layer_current, interfacial_potential
            stage_mixed_potential_evaluations += int(
                mixed_result.values.get("solver_function_evaluations", 0)
            )
            if stage_mixed_potential_evaluations > request.maximum_total_stage_mixed_potential_function_evaluations:
                raise RuntimeError("stage_mixed_potential_function_evaluation_budget_exceeded")
            if mixed_result.status != "computed":
                raise RuntimeError(
                    "stage_spatial_mixed_potential_failed: "
                    + str(mixed_result.values.get("reason", mixed_result.status))
                )
            stage = mixed_result.values["state_history"][0]
            face_current = np.asarray(stage["electrolyte_face_current_A_by_cell_boundary"], dtype=float)
            if face_current.shape != (nc + 1,) or not np.isfinite(face_current).all():
                raise RuntimeError("stage_mixed_potential_face_current_shape_or_finiteness_mismatch")
            branch_current = {
                row["reaction_id"]: np.asarray(row["signed_current_density_A_m2_by_cell"], dtype=float)
                for row in stage["reaction_branches"]
            }
            source_rate = np.zeros((nsource, nc), dtype=float)
            branch_index = {reaction_id: index for index, reaction_id in enumerate(source_ids)}
            reactive_area = (coupling.transport_chemistry.transport.transport_request.length_m / nc
                             * coupling.mixed_potential_template.slit_width_m
                             * coupling.mixed_potential_template.reactive_face_count)
            for branch in coupling.mixed_potential_template.branches:
                current_density = branch_current.get(branch.reaction_id)
                if current_density is None or current_density.shape != (nc,) or not np.isfinite(current_density).all():
                    raise RuntimeError(f"stage_faradaic_branch_current_missing_or_invalid:{branch.reaction_id}")
                source_rate[branch_index[branch.reaction_id]] = (
                    current_density * reactive_area / (branch.electron_number * FARADAY_CONSTANT_C_MOL)
                )
            if np.any(np.abs(source_rate) > request.maximum_absolute_stage_faradaic_extent_rate_mol_s):
                raise RuntimeError("stage_faradaic_extent_rate_exceeds_caller_bound")
            aqueous_charge_rate = np.zeros(nc, dtype=float)
            for source_index, metadata in enumerate(source_metadata):
                charge_per_extent = math.fsum(
                    charges[species_index[sid]] * coefficient
                    for sid, coefficient in metadata["species_stoichiometry"].items()
                )
                aqueous_charge_rate += charge_per_extent * source_rate[source_index]
            charge_residual_A = face_current[1:] - face_current[:-1] \
                - FARADAY_CONSTANT_C_MOL * aqueous_charge_rate \
                - interpolate_capacitive_current(float(time_s))
            allowed_charge_residual = coupling.current_balance_tolerance_A \
                + request.relative_face_current_closure_tolerance * np.maximum(
                    np.maximum(np.abs(face_current[1:]), np.abs(face_current[:-1])),
                    FARADAY_CONSTANT_C_MOL * np.abs(aqueous_charge_rate),
                )
            if np.any(np.abs(charge_residual_A) > allowed_charge_residual):
                raise RuntimeError("stage_mixed_potential_and_faradaic_component_charge_continuity_failed")
            result_sha = canonical_digest(mixed_result.model_dump(mode="json"))
            request_sha = canonical_digest(mixed_request.model_dump(mode="json"))
            lineage_chain = canonical_digest({
                "previous_chain_sha256": lineage_chain,
                "time_s": float(time_s),
                "stage_mixed_potential_input_sha256": request_sha,
                "stage_mixed_potential_result_sha256": result_sha,
                "face_current_A": face_current.tolist(),
                "branch_extent_rate_mol_s_by_cell": source_rate.tolist(),
                "charge_continuity_residual_A_by_cell": charge_residual_A.tolist(),
            })
            if record_knot:
                stage_mixed_knot_lineage.append({
                    "time_s": float(time_s),
                    "input_sha256": request_sha,
                    "result_sha256": result_sha,
                    "solver_function_evaluations": int(mixed_result.values.get("solver_function_evaluations", 0)),
                    "face_current_A_by_boundary": face_current.tolist(),
                    "branch_current_density_A_m2_by_branch_and_cell": {
                        reaction_id: values.tolist() for reaction_id, values in branch_current.items()
                    },
                    "branch_extent_rate_mol_s_by_cell": source_rate.tolist(),
                })
            return source_rate, face_current, None, None

        def component_flux_from_stage_chemistry(concentration, gamma, target_face_current_A, stage_face_area=None):
            nonlocal maximum_face_current_residual_A, maximum_face_current_scale_A
            nonlocal ionic_current_face_evaluations
            ns = len(species_ids)
            local_face_area = face_area if stage_face_area is None else np.asarray(stage_face_area, dtype=float)
            if local_face_area.shape != face_area.shape or not np.isfinite(local_face_area).all() or np.any(local_face_area <= 0.0):
                raise RuntimeError("stage_geometry_interior_face_area_shape_or_value_invalid")
            if target_face_current_A.shape != (nc + 1,):
                raise RuntimeError("stage_ionic_current_face_shape_mismatch")
            face_component_rate = np.zeros((ncomp, nc + 1), dtype=float)
            ionic_current_face_evaluations += nc + 1
            if ionic_current_face_evaluations > request.maximum_total_ionic_current_face_evaluations:
                raise RuntimeError("ionic_current_face_evaluation_budget_exceeded")
            if faradaic_stage and max(abs(float(target_face_current_A[0])),
                                      abs(float(target_face_current_A[-1]))) > \
                    request.faradaic_stage_coupling.current_balance_tolerance_A:
                raise RuntimeError("stage_mixed_potential_external_boundary_current_is_not_insulated")
            for face in range(nc - 1):
                c_left = concentration[face]
                c_right = concentration[face + 1]
                gamma_left = gamma[face]
                gamma_right = gamma[face + 1]
                distance = center_distance[face]
                gradient_c = (c_right - c_left) / distance
                face_c = 0.5 * (c_right + c_left)
                gradient_log_gamma = (np.log(gamma_right) - np.log(gamma_left)) / distance
                baseline = gradient_c + face_c * gradient_log_gamma
                diffusivity = np.asarray([diffusivity_by_species[sid][face] for sid in species_ids], dtype=float)
                denominator = float(np.sum(np.square(charges) * diffusivity * face_c))
                nonmigration_current_density = -float(np.sum(charges * diffusivity * baseline))
                target_internal_current_A = float(target_face_current_A[face + 1])
                target_current_density = target_internal_current_A / local_face_area[face]
                if denominator <= 0.0:
                    if abs(nonmigration_current_density) > 1e-30 or target_internal_current_A != 0.0:
                        raise RuntimeError("zero_mobility_face_has_nonzero_diffusive_or_target_current")
                    dimensionless_potential_gradient = 0.0
                else:
                    dimensionless_potential_gradient = (
                        nonmigration_current_density
                        - target_current_density / FARADAY_CONSTANT_C_MOL
                    ) / denominator
                species_flux_density = -diffusivity * (
                    baseline + charges * face_c * dimensionless_potential_gradient
                )
                if not np.isfinite(species_flux_density).all():
                    raise RuntimeError("nonfinite_electroneutral_NP_species_flux")
                current_density = float(np.sum(charges * species_flux_density))
                current_A = FARADAY_CONSTANT_C_MOL * current_density * local_face_area[face]
                current_scale_A = float(
                    FARADAY_CONSTANT_C_MOL
                    * np.sum(np.abs(charges * species_flux_density))
                    * local_face_area[face]
                )
                current_residual_A = current_A - target_internal_current_A
                current_scale_A = max(current_scale_A, abs(current_A), abs(target_internal_current_A))
                maximum_face_current_residual_A = max(maximum_face_current_residual_A, abs(current_residual_A))
                maximum_face_current_scale_A = max(maximum_face_current_scale_A, current_scale_A)
                if abs(current_residual_A) > request.absolute_face_current_closure_tolerance_A \
                        + request.relative_face_current_closure_tolerance * current_scale_A:
                    raise RuntimeError("electroneutral_NP_face_current_closure_failed")
                face_component_rate[:, face + 1] = (
                    component_coefficient @ species_flux_density
                ) * local_face_area[face]
            if not np.isfinite(face_component_rate).all():
                raise RuntimeError("nonfinite_component_face_transfer_rate")
            return face_component_rate

        def rhs(time_s, state):
            nonlocal rhs_evaluations, source_projection_operations, kinetic_rate_evaluations
            nonlocal maximum_kinetic_phase_rate_mol_s
            nonlocal dynamic_hydraulic_iterations, maximum_dynamic_hydraulic_fixed_point_residual
            rhs_evaluations += 1
            if rhs_evaluations > request.maximum_total_rhs_evaluations:
                raise RuntimeError("component_state_bdf_rhs_budget_exceeded")
            component_inventory = state[:n_component_state].reshape(ncomp, nc)
            kinetic_solid_inventory = (
                state[n_component_state:kinetic_layout_state_size].reshape(nkinetic_phase, nc)
                if kinetic_mode else None
            )
            double_layer_charge_C = state[-nc:].copy() if dynamic_double_layer is not None else None
            if dynamic_double_layer is not None and not np.isfinite(double_layer_charge_C).all():
                raise RuntimeError("dynamic_double_layer_charge_trial_state_nonfinite")
            if (not np.isfinite(component_inventory).all()
                    or np.any(component_inventory < -request.absolute_component_inventory_tolerance_mol)):
                raise RuntimeError("negative_or_nonfinite_component_inventory_trial_state")
            if kinetic_mode and (not np.isfinite(kinetic_solid_inventory).all()
                                 or np.any(kinetic_solid_inventory < -request.absolute_solid_inventory_tolerance_mol)):
                raise RuntimeError("negative_or_nonfinite_kinetic_solid_trial_state")
            # Aqueous equilibrium is evaluated for every BDF trial state before its derivative is formed.
            stage_concentration, stage_gamma, stage_partitions, stage_face_area = equilibrate_cells(
                component_inventory, float(time_s), kinetic_solid_inventory
            )
            if faradaic_stage:
                source_rate, target_current, double_layer_charge_rate, _ = evaluate_stage_mixed_potential(
                    stage_concentration, stage_gamma, float(time_s), double_layer_charge_C=double_layer_charge_C
                )
            else:
                source_rate = interpolate_source_extent_rates(float(time_s))
                target_current = interpolate_ionic_face_current(float(time_s))
                double_layer_charge_rate = None
            face_rate = component_flux_from_stage_chemistry(
                stage_concentration, stage_gamma, target_current, stage_face_area
            )
            hydraulic_ledger_rate = np.zeros(n_hydraulic_ledger_state, dtype=float)
            dynamic_flow_rate = np.zeros(n_dynamic_flow_state, dtype=float)
            if hydraulic_advection is not None:
                stage_components = component_advection_face_rates_mol_s(
                    hydraulic_advection, float(time_s), stage_concentration, request.cells[0].conserved_components
                )
                face_rate = face_rate + stage_components
                formulas = {row.species_id: row.elemental_composition for row in request.cells[0].aqueous_activity_request.system.species}
                boundary_left, boundary_right = boundary_advection_reservoir_rates(
                    hydraulic_advection, float(time_s), stage_concentration, formulas,
                    request.cells[0].conserved_components,
                )
                left_components, left_elements, left_charge = boundary_left
                right_components, right_elements, right_charge = boundary_right
                hydraulic_ledger_rate = np.asarray(
                    [left_components[cid] for cid in component_ids]
                    + [right_components[cid] for cid in component_ids]
                    + [left_elements[eid] for eid in element_ids]
                    + [right_elements[eid] for eid in element_ids]
                    + [left_charge, right_charge], dtype=float,
                )
                if not np.isfinite(hydraulic_ledger_rate).all():
                    raise RuntimeError("nonfinite_hydraulic_boundary_reservoir_rate")
            derivative = face_rate[:, :-1] - face_rate[:, 1:]
            source_projection_operations += nsource * ncomp * nc
            if source_projection_operations > request.maximum_total_source_projection_operations:
                raise RuntimeError("electrochemical_source_projection_budget_exceeded")
            if nsource:
                derivative += source_component_coefficient @ source_rate
            kinetic_solid_rate = np.zeros((nkinetic_phase, nc), dtype=float)
            kinetic_mode_records = []
            if kinetic_mode:
                for cell_index, phase_set in enumerate(kinetic_phase_sets):
                    activities = {
                        sid: float(stage_gamma[cell_index, species_index[sid]]
                                   * stage_concentration[cell_index, species_index[sid]] / 1000.0)
                        for sid in species_ids
                    }
                    phase_rates = {}
                    for phase_index, phase in enumerate(phase_set.phase_candidates):
                        saturation = trial_saturation_ratio(phase, activities)
                        rate, mode = trial_phase_rate_mol_s(
                            solid_inventory_mol=float(kinetic_solid_inventory[phase_index, cell_index]),
                            solution_volume_m3=float(stage_partitions[cell_index]["solution_volume_L"]) / 1000.0,
                            saturation_ratio=saturation,
                            temperature_K=float(phase_set.temperature_K),
                            nucleation_law=phase_set.nucleation_laws[phase_index],
                            growth_law=phase_set.growth_laws[phase_index].law,
                            seeded_override=kinetic_seed_modes[phase_index][cell_index],
                        )
                        phase_rates[phase.solid_species_id] = rate
                        kinetic_solid_rate[phase_index, cell_index] = rate
                        maximum_kinetic_phase_rate_mol_s = max(maximum_kinetic_phase_rate_mol_s, abs(rate))
                        kinetic_rate_evaluations += 1
                        if kinetic_rate_evaluations > request.kinetic_rate_evaluation_budget:
                            raise RuntimeError("kinetic_phase_rate_evaluation_budget_exceeded")
                        kinetic_mode_records.append({
                            "cell_id": phase_set.cell_id,
                            "solid_species_id": phase.solid_species_id,
                            "saturation_ratio": saturation,
                            "signed_extent_rate_mol_s": rate,
                            "mode": mode,
                        })
                    component_exchange, _ = kinetic_component_exchange(cell_index, phase_rates)
                    # Phase exchange is internal: dissolved and solid amounts move
                    # in opposite directions, leaving total conserved components unchanged.
                    _ = component_exchange
                kinetic_rate_records_by_time[float(time_s)] = kinetic_mode_records
            if dynamic_hydraulic_advection is not None:
                base_derivative = derivative.copy()
                base_volume_L = np.asarray([float(row["solution_volume_L"]) for row in stage_partitions])
                stage_geometry = [row["dynamic_geometry"] for row in stage_partitions]
                if any(row is None for row in stage_geometry):
                    raise RuntimeError("dynamic_hydraulic_stage_requires_trial_solid_geometry")
                lengths = [float(row.cell_length_m) for row in request.dynamic_solid_geometry_by_cell]
                apertures = [float(row["aperture_m"]) for row in stage_geometry]
                inlet_flow = float(state[dynamic_flow_state_index])
                volume_rate = np.zeros(nc, dtype=float)
                converged = False
                hydraulic_stage = None
                for _coupling_iteration in range(request.maximum_dynamic_hydraulic_fixed_point_iterations):
                    dynamic_hydraulic_iterations += 1
                    hydraulic_stage = evaluate_dynamic_hydraulic_advection_stage(
                        dynamic_hydraulic_advection,
                        time_s=float(time_s), inlet_flow_m3_s=inlet_flow,
                        cell_lengths_m=lengths, aperture_by_cell_m=apertures,
                        liquid_volume_rate_m3_s_by_cell=volume_rate,
                        concentration_mol_m3_by_cell_and_species=stage_concentration,
                        components=request.cells[0].conserved_components,
                    )
                    advective_face_rate = np.asarray(
                        hydraulic_stage["component_flux_mol_s_by_component_and_face"], dtype=float
                    )
                    trial_derivative = base_derivative + advective_face_rate[:, :-1] - advective_face_rate[:, 1:]
                    if kinetic_mode:
                        updated_volume_rate = directional_kinetic_volume_rate(
                            kinetic_solid_inventory, kinetic_solid_rate, base_volume_L
                        )
                    else:
                        updated_volume_rate = directional_dynamic_volume_rate(
                            component_inventory, trial_derivative, base_volume_L, float(time_s)
                        )
                    residual_scale = max(float(np.max(np.abs(updated_volume_rate))),
                                         float(np.max(np.abs(volume_rate))), 1e-30)
                    residual = float(np.max(np.abs(updated_volume_rate - volume_rate))) / residual_scale
                    maximum_dynamic_hydraulic_fixed_point_residual = max(
                        maximum_dynamic_hydraulic_fixed_point_residual, residual
                    )
                    if residual <= float(request.dynamic_hydraulic_fixed_point_relative_tolerance):
                        # Keep the volume rate that produced this exact hydraulic and component RHS.
                        converged = True
                        break
                    alpha = float(request.dynamic_hydraulic_fixed_point_relaxation)
                    volume_rate = volume_rate + alpha * (updated_volume_rate - volume_rate)
                if not converged:
                    raise RuntimeError("dynamic_hydraulic_volume_rate_fixed_point_not_converged")
                hydraulic_stage = evaluate_dynamic_hydraulic_advection_stage(
                    dynamic_hydraulic_advection,
                    time_s=float(time_s), inlet_flow_m3_s=inlet_flow,
                    cell_lengths_m=lengths, aperture_by_cell_m=apertures,
                    liquid_volume_rate_m3_s_by_cell=volume_rate,
                    concentration_mol_m3_by_cell_and_species=stage_concentration,
                    components=request.cells[0].conserved_components,
                )
                advective_face_rate = np.asarray(
                    hydraulic_stage["component_flux_mol_s_by_component_and_face"], dtype=float
                )
                face_rate = face_rate + advective_face_rate
                derivative = base_derivative + advective_face_rate[:, :-1] - advective_face_rate[:, 1:]
                dynamic_flow_rate[0] = float(hydraulic_stage["inlet_flow_derivative_m3_s2"])
                left, right = hydraulic_stage["boundary_reservoir_rates"]
                hydraulic_ledger_rate = np.asarray(
                    [left["component_mol_s"].get(cid, 0.0) for cid in component_ids]
                    + [right["component_mol_s"].get(cid, 0.0) for cid in component_ids]
                    + [left["element_mol_s"].get(eid, 0.0) for eid in element_ids]
                    + [right["element_mol_s"].get(eid, 0.0) for eid in element_ids]
                    + [left["charge_mol_equivalent_s"], right["charge_mol_equivalent_s"]], dtype=float,
                )
                if not np.isfinite(derivative).all() or not np.isfinite(hydraulic_ledger_rate).all():
                    raise RuntimeError("dynamic_hydraulic_component_or_reservoir_rate_nonfinite")
            return np.concatenate((derivative.reshape(-1), kinetic_solid_rate.reshape(-1), face_rate.reshape(-1),
                                   source_rate.reshape(-1), target_current, dynamic_flow_rate,
                                   hydraulic_ledger_rate,
                                   double_layer_charge_rate if double_layer_charge_rate is not None else np.zeros(0)))

        if kinetic_mode:
            kinetic_absolute_tolerance = np.concatenate((
                np.full(n_component_state, float(request.absolute_component_inventory_tolerance_mol)),
                np.full(n_kinetic_solid_state, float(request.absolute_solid_inventory_tolerance_mol)),
                np.full(n_face_state + n_extent_state,
                        float(request.absolute_component_inventory_tolerance_mol)),
                np.full(n_current_state,
                        float(request.absolute_face_current_closure_tolerance_A)
                        * max(float(times[-1] - times[0]), 1.0)),
                np.full(n_dynamic_flow_state, float(request.absolute_flow_tolerance_m3_s)),
                np.full(n_hydraulic_ledger_state, float(request.absolute_component_inventory_tolerance_mol)),
                np.full(n_dynamic_double_layer_state,
                        float(request.absolute_double_layer_charge_tolerance_C)),
            ))
            event_report = integrate_coupled_seed_bdf(
                kinetic_event_rhs,
                tuple(float(value) for value in state0),
                tuple(float(value) for value in times),
                relative_tolerance=float(request.relative_tolerance),
                absolute_tolerance_mol=float(request.absolute_solid_inventory_tolerance_mol),
                maximum_step_s=float(request.maximum_step_s),
                maximum_seed_events=request.maximum_phase_event_count,
                seed_threshold_inventory=kinetic_event_rhs.threshold_inventory,
                absolute_tolerance_vector=tuple(float(value) for value in kinetic_absolute_tolerance),
            )
            solution = (SimpleNamespace(
                success=True,
                y=np.asarray(event_report["state_by_time"], dtype=float).T,
                message="event-driven same-stage kinetic BDF completed",
            ) if event_report.get("committed") else None)
        else:
            event_report = None
            solution = solve_ivp(
                rhs,
                (float(times[0]), float(times[-1])),
                state0,
                method="BDF",
                t_eval=tuple(float(value) for value in times),
                rtol=request.relative_tolerance,
                atol=np.concatenate((
                    np.full(kinetic_layout_state_size + n_face_state + n_extent_state + n_current_state,
                             request.absolute_component_inventory_tolerance_mol),
                    np.full(n_dynamic_flow_state, request.absolute_flow_tolerance_m3_s),
                    np.full(n_hydraulic_ledger_state, request.absolute_component_inventory_tolerance_mol),
                    np.full(n_dynamic_double_layer_state,
                            float(request.absolute_double_layer_charge_tolerance_C)),
                )),
                max_step=request.maximum_step_s,
            )
        if solution is None or not solution.success or solution.y.shape[1] != nt:
            return Calculation(status="needs_data", values={
                "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                "input_sha256": digest,
                "reason": event_report.get("reason") if event_report else "component_state_bdf_integrator_failed",
                "solver_message": event_report.get("reason") if event_report else solution.message,
                "phase_seed_transitions": event_report.get("seed_transitions", []) if event_report else None,
                "phase_depletion_events": event_report.get("phase_depletions", []) if event_report else None,
                "kinetic_event_rhs_evaluations": event_report.get("rhs_evaluations", 0) if event_report else None,
                "kinetic_phase_rate_evaluations": kinetic_rate_evaluations,
                "rhs_evaluations": rhs_evaluations,
                "stage_equilibrium_calls": equilibrium_calls,
                "solid_partition_evaluations": solid_partition_evaluations,
                "solid_active_set_sweeps": solid_active_set_sweeps,
                "solid_bisection_iterations": solid_bisection_iterations,
                "source_projection_operations": source_projection_operations,
                "ionic_current_face_evaluations": ionic_current_face_evaluations,
                "dynamic_hydraulic_iterations": dynamic_hydraulic_iterations,
                "maximum_dynamic_hydraulic_fixed_point_residual": maximum_dynamic_hydraulic_fixed_point_residual,
                "dynamic_hydraulic_fixed_point_relative_tolerance": float(
                    request.dynamic_hydraulic_fixed_point_relative_tolerance
                ),
                "dynamic_hydraulic_fixed_point_iteration_budget": request.maximum_dynamic_hydraulic_fixed_point_iterations,
                "committed": False,
            })
        component_history = solution.y[:n_component_state].reshape(ncomp, nc, nt)
        kinetic_solid_history = (solution.y[n_component_state:kinetic_layout_state_size]
                                 .reshape(nkinetic_phase, nc, nt) if kinetic_mode
                                 else np.zeros((0, nc, nt)))
        face_start = kinetic_layout_state_size
        face_history = solution.y[face_start:face_start + n_face_state].reshape(ncomp, nc + 1, nt)
        extent_start = face_start + n_face_state
        extent_history = solution.y[extent_start:extent_start + n_extent_state].reshape(nsource, nc, nt)
        current_start = extent_start + n_extent_state
        current_charge_history = solution.y[current_start:current_start + n_current_state].reshape(n_current_state, nt)
        dynamic_flow_start = current_start + n_current_state
        dynamic_flow_history = (solution.y[dynamic_flow_start:dynamic_flow_start + n_dynamic_flow_state].reshape(nt)
                                if n_dynamic_flow_state else np.zeros((0, nt)))
        hydraulic_ledger_start = dynamic_flow_start + n_dynamic_flow_state
        hydraulic_ledger_history = (solution.y[hydraulic_ledger_start:hydraulic_ledger_start + n_hydraulic_ledger_state]
                                    .reshape(n_hydraulic_ledger_state, nt)
                                    if n_hydraulic_ledger_state else np.zeros((0, nt)))
        dynamic_double_layer_charge_history = (
            solution.y[-n_dynamic_double_layer_state:].reshape(n_dynamic_double_layer_state, nt)
            if n_dynamic_double_layer_state else np.zeros((0, nt))
        )
        dynamic_double_layer_potential_history = np.zeros((nc, nt), dtype=float)
        if dynamic_double_layer is not None:
            cap_axis = dynamic_double_layer.differential_capacitance_potential_axis_V
            cap_values = tuple(float(value) for value in dynamic_double_layer.differential_capacitance_F_m2)
            for knot_index in range(nt):
                for cell_index in range(nc):
                    dynamic_double_layer_potential_history[cell_index, knot_index] = (
                        _double_layer_potential_from_charge_density(
                            float(dynamic_double_layer_charge_history[cell_index, knot_index])
                            / double_layer_area_m2[cell_index],
                            float(dynamic_double_layer.reference_interfacial_potential_V_by_cell[cell_index]),
                            cap_axis, cap_values, double_layer_capacitance_cumulative,
                        )
                    )
        if kinetic_mode:
            mode_history = event_report.get("seed_modes_by_time", ())
            if len(mode_history) != nt or not mode_history:
                return Calculation(status="needs_data", values={
                    "model_id": MODEL_ID, "assessment_id": request.assessment_id,
                    "input_sha256": digest,
                    "reason": "kinetic_event_seed_mode_history_shape_mismatch",
                    "committed": False,
                })
            kinetic_seed_modes = [list(mode_row) for mode_row in mode_history[-1]]
        maximum_residual = 0.0
        maximum_hydraulic_boundary_closure_ratio = 0.0
        closure_records = []
        if hydraulic_transport_enabled:
            ledger_offset = ncomp
            hydraulic_component_reservoir_left = hydraulic_ledger_history[:ncomp]
            hydraulic_component_reservoir_right = hydraulic_ledger_history[ledger_offset:ledger_offset+ncomp]
            ledger_offset += ncomp
            hydraulic_element_reservoir_left = hydraulic_ledger_history[ledger_offset:ledger_offset+len(element_ids)]
            hydraulic_element_reservoir_right = hydraulic_ledger_history[ledger_offset+len(element_ids):ledger_offset+2*len(element_ids)]
            ledger_offset += 2*len(element_ids)
            hydraulic_charge_reservoir_left = hydraulic_ledger_history[ledger_offset]
            hydraulic_charge_reservoir_right = hydraulic_ledger_history[ledger_offset+1]
        else:
            hydraulic_component_reservoir_left = hydraulic_component_reservoir_right = np.zeros((ncomp, nt))
            hydraulic_element_reservoir_left = hydraulic_element_reservoir_right = np.zeros((len(element_ids), nt))
            hydraulic_charge_reservoir_left = hydraulic_charge_reservoir_right = np.zeros((nt,))
        for component_index, component_id in enumerate(component_ids):
            start = component_history[component_index, :, 0]
            end = component_history[component_index, :, -1]
            transfer = face_history[component_index, :, -1]
            source_transfer = (source_component_coefficient[component_index] @ extent_history[:, :, -1]
                              if nsource else np.zeros(nc, dtype=float))
            residual = end - start - (transfer[:-1] - transfer[1:] + source_transfer)
            allowed = request.absolute_component_closure_tolerance_mol + request.relative_component_closure_tolerance * np.maximum(
                np.maximum(np.abs(start), np.abs(end)),
                np.maximum(np.abs(transfer[:-1]), np.abs(transfer[1:])),
            )
            normalized = np.abs(residual) / allowed
            maximum_residual = max(maximum_residual, float(np.max(normalized)))
            external_reservoir_by_cell = -source_transfer.copy()
            if hydraulic_transport_enabled:
                external_reservoir_by_cell[0] += hydraulic_component_reservoir_left[component_index, -1]
                external_reservoir_by_cell[-1] += hydraulic_component_reservoir_right[component_index, -1]
            global_reservoir_closure = float(np.sum(end-start) + np.sum(external_reservoir_by_cell))
            global_allowed = request.absolute_component_closure_tolerance_mol + request.relative_component_closure_tolerance * max(float(np.sum(np.abs(start))), float(np.sum(np.abs(end))), 1e-30)
            maximum_hydraulic_boundary_closure_ratio = max(maximum_hydraulic_boundary_closure_ratio, abs(global_reservoir_closure)/global_allowed)
            closure_records.append({
                "component_id": component_id,
                "inventory_mol_by_time_and_cell": component_history[component_index].T.tolist(),
                "integrated_face_transfer_mol_by_time_and_face": face_history[component_index].T.tolist(),
                "integrated_aqueous_source_transfer_mol_by_cell": source_transfer.tolist(),
                "integrated_external_reservoir_component_change_mol_by_cell": external_reservoir_by_cell.tolist(),
                "global_system_plus_reservoir_residual_mol": global_reservoir_closure,
                "global_system_plus_reservoir_residual_normalized": abs(global_reservoir_closure)/global_allowed,
                "cell_inventory_residual_mol": residual.tolist(),
                "allowed_residual_mol_by_cell": allowed.tolist(),
                "global_inventory_residual_mol": float(np.sum(end) - np.sum(start)
                    - (transfer[0] - transfer[-1] + np.sum(source_transfer))),
            })
        element_ledger_records = []
        if element_ids:
            element_total_history = np.einsum("ec,cjt->ejt", component_element_coefficient, component_history)
            element_face_history = np.einsum("ec,cft->eft", component_element_coefficient, face_history)
            element_source_coefficient = component_element_coefficient @ source_component_coefficient
            element_source_history = np.einsum("es,sjt->ejt", element_source_coefficient, extent_history)
            for element_index, element_id in enumerate(element_ids):
                start = element_total_history[element_index, :, 0]
                end = element_total_history[element_index, :, -1]
                transfer = element_face_history[element_index, :, -1]
                source_transfer = element_source_history[element_index, :, -1]
                residual = end - start - (transfer[:-1] - transfer[1:] + source_transfer)
                allowed = request.absolute_component_closure_tolerance_mol + \
                    request.relative_component_closure_tolerance * np.maximum(
                        np.maximum(np.abs(start), np.abs(end)),
                        np.maximum(np.abs(transfer[:-1]), np.abs(transfer[1:])),
                    )
                normalized = np.abs(residual) / allowed
                maximum_residual = max(maximum_residual, float(np.max(normalized)))
                source_reservoir_change = np.zeros(nc, dtype=float)
                for source_index, metadata in enumerate(source_metadata):
                    coefficient = metadata["external_element_change_per_extent"].get(element_id)
                    if coefficient is not None:
                        source_reservoir_change += coefficient * extent_history[source_index, :, -1]
                reservoir_residual = source_transfer + source_reservoir_change
                reservoir_change = source_reservoir_change.copy()
                if hydraulic_transport_enabled:
                    hydraulic_left = hydraulic_element_reservoir_left[element_index, -1]
                    hydraulic_right = hydraulic_element_reservoir_right[element_index, -1]
                    reservoir_change[0] += hydraulic_left
                    reservoir_change[-1] += hydraulic_right
                reservoir_allowed = request.absolute_component_closure_tolerance_mol + \
                    request.relative_component_closure_tolerance * np.maximum(
                        np.maximum(np.abs(source_transfer), np.abs(reservoir_change)), 1e-30
                    )
                reservoir_normalized = np.abs(reservoir_residual) / reservoir_allowed
                maximum_residual = max(maximum_residual, float(np.max(reservoir_normalized)))
                global_element_reservoir_residual = float(np.sum(end-start)+np.sum(reservoir_change))
                global_element_allowed = request.absolute_component_closure_tolerance_mol + request.relative_component_closure_tolerance * max(float(np.sum(np.abs(start))),float(np.sum(np.abs(end))),1e-30)
                maximum_hydraulic_boundary_closure_ratio = max(maximum_hydraulic_boundary_closure_ratio,abs(global_element_reservoir_residual)/global_element_allowed)
                element_ledger_records.append({
                    "element_id": element_id,
                    "total_inventory_mol_by_time_and_cell": element_total_history[element_index].T.tolist(),
                    "integrated_face_transfer_mol_by_time_and_face": element_face_history[element_index].T.tolist(),
                    "integrated_aqueous_source_change_mol_by_cell": source_transfer.tolist(),
                    "integrated_external_reservoir_change_mol_by_cell": reservoir_change.tolist(),
                    "cell_element_balance_residual_mol": residual.tolist(),
                    "system_plus_reservoir_source_residual_mol_by_cell": reservoir_residual.tolist(),
                    "global_element_residual_mol": float(
                        np.sum(end) - np.sum(start) - (transfer[0] - transfer[-1] + np.sum(source_transfer))
                    ),
                    "global_system_plus_reservoir_residual_mol": global_element_reservoir_residual,
                    "global_system_plus_reservoir_residual_normalized": abs(global_element_reservoir_residual)/global_element_allowed,
                })
        source_ledger = []
        for source_index, metadata in enumerate(source_metadata):
            integrated_extent_by_cell = extent_history[source_index, :, -1]
            total_extent = float(np.sum(integrated_extent_by_cell))
            source_ledger.append({
                "reaction_id": metadata["reaction_id"],
                "evidence_sha256": canonical_digest([row.model_dump(mode="json")
                                                       for row in metadata["evidence"]]),
                "source_record_sha256": metadata["source_digest"],
                "extent_mol_by_cell": integrated_extent_by_cell.tolist(),
                "external_reservoir_element_change_mol_by_cell": {
                    element: [coefficient * float(value) for value in integrated_extent_by_cell]
                    for element, coefficient in metadata["external_element_change_per_extent"].items()
                },
                "external_reservoir_element_change_mol": {
                    element: coefficient * total_extent
                    for element, coefficient in metadata["external_element_change_per_extent"].items()
                },
                "external_reservoir_component_change_mol_by_cell": {
                    component_id: [coefficient * float(value) for value in integrated_extent_by_cell]
                    for component_id, coefficient in metadata["external_component_change_per_extent"].items()
                },
                "external_reservoir_charge_change_mol_eq": (
                    metadata["external_charge_change_per_extent"] * total_extent
                ),
                "external_reservoir_charge_change_mol_eq_by_cell": [
                    metadata["external_charge_change_per_extent"] * float(value)
                    for value in integrated_extent_by_cell
                ],
                "source_schedule_sha256": metadata["source_digest"],
            })
        # Explicit knot chemistry snapshots are included in the same equilibrium-call budget.
        species_ids = [row.species_id for row in request.cells[0].aqueous_activity_request.system.species]
        species_by_time_cell = {species_id: [[None for _ in range(nc)] for _ in range(nt)]
                                for species_id in species_ids}
        gamma_by_time_cell = {species_id: [[None for _ in range(nc)] for _ in range(nt)]
                              for species_id in species_ids}
        knot_equilibrium_digests = []
        exact_knot_current = []
        charge_continuity_knots = []
        solid_phase_history_by_cell: dict[str, dict[str, list[float | None]]] = {}
        aqueous_component_history = {
            component_id: [[None for _ in range(nc)] for _ in range(nt)]
            for component_id in component_ids
        }
        solid_component_history = {
            component_id: [[None for _ in range(nc)] for _ in range(nt)]
            for component_id in component_ids
        }
        kinetic_aqueous_component_history = {
            component_id: [[None for _ in range(nc)] for _ in range(nt)] for component_id in component_ids
        }
        kinetic_solid_component_history = {
            component_id: [[None for _ in range(nc)] for _ in range(nt)] for component_id in component_ids
        }
        for time_index, time_s in enumerate(times):
            knot_kinetic_solids = kinetic_solid_history[:, :, time_index] if kinetic_mode else None
            c_by_cell, g_by_cell, partition_by_cell, _knot_face_area = equilibrate_cells(
                component_history[:, :, time_index], float(time_s), knot_kinetic_solids
            )
            knot_equilibrium_digests.append(last_stage_summary)
            if kinetic_mode:
                for cell_index, partition in enumerate(partition_by_cell):
                    if partition is None:
                        raise RuntimeError("kinetic phase state knot output is missing")
                    for component_id in component_ids:
                        kinetic_aqueous_component_history[component_id][time_index][cell_index] = float(
                            partition["aqueous_component_inventory_mol"][component_id]
                        )
                        kinetic_solid_component_history[component_id][time_index][cell_index] = float(
                            partition["solid_component_inventory_mol"][component_id]
                        )
                    cell_id = partition["cell_id"]
                    phase_history = solid_phase_history_by_cell.setdefault(cell_id, {})
                    for phase_row in partition["solid_phase_results"]:
                        phase_history.setdefault(phase_row["solid_species_id"], [None for _ in range(nt)])[time_index] = float(
                            phase_row["solid_moles"]
                        )
            elif solid_mode:
                for cell_index, partition in enumerate(partition_by_cell):
                    if partition is None:
                        raise RuntimeError("solid partition knot output is missing")
                    cell_id = partition["cell_id"]
                    phase_history = solid_phase_history_by_cell.setdefault(cell_id, {})
                    for phase_row in partition["solid_phase_results"]:
                        phase_values = phase_history.setdefault(
                            phase_row["solid_species_id"], [None for _ in range(nt)]
                        )
                        phase_values[time_index] = float(phase_row["solid_mol"])
                    for component_id in component_ids:
                        aq_value = float(partition["aqueous_component_inventory_mol"][component_id])
                        solid_value = float(partition["solid_component_inventory_mol"][component_id])
                        total_value = float(component_history[component_ids.index(component_id), cell_index, time_index])
                        allowed_value = (request.absolute_component_closure_tolerance_mol
                                         + request.relative_component_closure_tolerance * max(
                                             abs(total_value), abs(aq_value), abs(solid_value)
                                         ))
                        if abs(aq_value + solid_value - total_value) > allowed_value:
                            raise RuntimeError("stage aqueous-plus-solid total component closure failed")
                        aqueous_component_history[component_id][time_index][cell_index] = aq_value
                        solid_component_history[component_id][time_index][cell_index] = solid_value
            if faradaic_stage:
                knot_source_rate, knot_current, knot_dynamic_capacitive_current, _ = evaluate_stage_mixed_potential(
                    c_by_cell, g_by_cell, float(time_s),
                    double_layer_charge_C=(dynamic_double_layer_charge_history[:, time_index]
                                           if dynamic_double_layer is not None else None),
                    record_knot=True,
                )
            else:
                knot_source_rate = source_extent_knots[:, time_index, :]
                knot_current = ionic_current_knots[time_index]
                knot_dynamic_capacitive_current = None
            exact_knot_current.append(knot_current.tolist())
            knot_charge_rate = np.zeros(nc, dtype=float)
            for source_index, metadata in enumerate(source_metadata):
                charge_per_extent = math.fsum(
                    charges[species_index[sid]] * coefficient
                    for sid, coefficient in metadata["species_stoichiometry"].items()
                )
                knot_charge_rate += charge_per_extent * knot_source_rate[source_index]
            charge_continuity_knots.append({
                "time_s": float(time_s),
                "charge_continuity_residual_A_by_cell": (
                    knot_current[1:] - knot_current[:-1]
                    - FARADAY_CONSTANT_C_MOL * knot_charge_rate
                    - (knot_dynamic_capacitive_current if knot_dynamic_capacitive_current is not None
                       else capacitive_current_knots[time_index])
                ).tolist(),
                "dynamic_double_layer_capacitive_current_A_by_cell": (
                    knot_dynamic_capacitive_current.tolist()
                    if knot_dynamic_capacitive_current is not None else None
                ),
            })
            for cell_index in range(nc):
                for species_index, species_id in enumerate(species_ids):
                    species_by_time_cell[species_id][time_index][cell_index] = float(
                        c_by_cell[cell_index, species_index]
                    )
                    gamma_by_time_cell[species_id][time_index][cell_index] = float(
                        g_by_cell[cell_index, species_index]
                    )
        integrated_capacitive_charge_C_by_cell_and_time = np.zeros((nc, nt), dtype=float)
        if dynamic_double_layer is not None:
            integrated_capacitive_charge_C_by_cell_and_time = (
                dynamic_double_layer_charge_history - dynamic_double_layer_charge_history[:, :1]
            )
        else:
            for interval in range(nt - 1):
                duration = times[interval + 1] - times[interval]
                integrated_capacitive_charge_C_by_cell_and_time[:, interval + 1] = (
                    integrated_capacitive_charge_C_by_cell_and_time[:, interval]
                    + 0.5 * duration * (capacitive_current_knots[interval] + capacitive_current_knots[interval + 1])
                )
        hydraulic_charge_net_history = (hydraulic_charge_reservoir_left + hydraulic_charge_reservoir_right)
        hydraulic_charge_max_abs_mol_eq = float(np.max(np.abs(hydraulic_charge_net_history))) if hydraulic_transport_enabled else 0.0
        hydraulic_charge_scale_mol_eq = float(np.max(np.abs(hydraulic_charge_reservoir_left)+np.abs(hydraulic_charge_reservoir_right))) if hydraulic_transport_enabled else 0.0
        hydraulic_charge_closed = (not hydraulic_transport_enabled or hydraulic_charge_max_abs_mol_eq <= 1e-10*max(1.0,hydraulic_charge_scale_mol_eq))
        if hydraulic_transport_enabled:
            maximum_residual = max(maximum_residual, maximum_hydraulic_boundary_closure_ratio)
            if not hydraulic_charge_closed:
                maximum_residual = max(maximum_residual, 2.0)
        if dynamic_geometry:
            maximum_residual = max(
                maximum_residual,
                maximum_dynamic_geometry_residual / float(request.dynamic_geometry_relative_tolerance),
            )
        committed = maximum_residual <= 1.0
        return Calculation(status="computed" if committed else "needs_data", values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "component_state_source_id": COMPONENT_STATE_SOURCE_ID,
            "kinetic_phase_source_id": "same_stage_activity_based_competing_solid_kinetics_with_seed_depletion_events" if kinetic_mode else None,
            "kinetic_event_policy": ({
                "seed_transitions": list(event_report.get("seed_transitions", ())),
                "phase_depletions": list(event_report.get("phase_depletions", ())),
                "event_count": len(event_report.get("seed_transitions", ())) + len(event_report.get("phase_depletions", ())),
                "maximum_event_count": request.maximum_phase_event_count,
                "seed_threshold_policy": event_report.get("seed_threshold_policy"),
                "solid_state_policy": event_report.get("solid_state_policy"),
            } if event_report else None),
            "stage_equilibrium_source_id": STAGE_EQUILIBRIUM_SOURCE_ID,
            "solid_phase_partition_source_id": STAGE_SOLID_PARTITION_SOURCE_ID if solid_mode else None,
            "moving_geometry_mode": request.moving_geometry_mode,
            "dynamic_geometry_source_id": (
                "caller_evidenced_solid_molar_volume_gap_occupancy_fixed_point_geometry" if dynamic_geometry else None
            ),
            "dynamic_geometry_work_budget": ({
                "iterations_used": dynamic_geometry_iterations,
                "maximum_total_iterations": request.maximum_total_dynamic_geometry_iterations,
                "maximum_iterations_per_cell_per_stage": request.maximum_dynamic_geometry_iterations_per_cell_stage,
            } if dynamic_geometry else None),
            "dynamic_geometry_fixed_point_residual": ({
                "maximum_relative_volume_residual": maximum_dynamic_geometry_residual,
                "relative_tolerance": float(request.dynamic_geometry_relative_tolerance),
                "normalized_closure_ratio": maximum_dynamic_geometry_residual / float(request.dynamic_geometry_relative_tolerance),
                "closed": maximum_dynamic_geometry_residual <= float(request.dynamic_geometry_relative_tolerance),
            } if dynamic_geometry else None),
            "exact_knot_dynamic_geometry_by_cell": (
                [row.get("dynamic_geometry", []) for row in knot_equilibrium_digests] if dynamic_geometry else None
            ),
            "component_flux_source_id": ELECTRONEUTRAL_NP_SOURCE_ID,
            "hydraulic_advection_source_id": (
                DYNAMIC_HYDRAULIC_SOURCE_ID if dynamic_hydraulic_advection is not None
                else CALLER_HYDRAULIC_ADVECTION_SOURCE_ID if hydraulic_advection is not None else None
            ),
            "electrochemical_source_method_source_id": (
                STAGE_SPATIAL_MIXED_POTENTIAL_SOURCE_ID if faradaic_stage
                else CALLER_ELECTROCHEMICAL_SOURCE_ID if source_schedules else None
            ),
            "electrochemical_source_schedule_sha256": [
                row["source_digest"] for row in source_metadata
            ],
            "ionic_face_current_schedule_A_by_knot_and_face": exact_knot_current,
            "capacitive_current_schedule_A_by_knot_and_cell": capacitive_current_knots.tolist(),
            "hydraulic_component_advection_enabled": hydraulic_transport_enabled,
            "dynamic_hydraulic_advection_enabled": dynamic_hydraulic_advection is not None,
            "dynamic_hydraulic_schedule_sha256": (
                dynamic_hydraulic_advection.schedule_sha256 if dynamic_hydraulic_advection is not None else None
            ),
            "dynamic_inlet_flow_m3_s_by_time": dynamic_flow_history.tolist() if n_dynamic_flow_state else None,
            "dynamic_hydraulic_fixed_point_work": ({
                "rhs_stage_iterations": dynamic_hydraulic_iterations,
                "maximum_iterations_per_stage": request.maximum_dynamic_hydraulic_fixed_point_iterations,
                "maximum_normalized_volume_rate_residual": maximum_dynamic_hydraulic_fixed_point_residual,
                "relative_tolerance": float(request.dynamic_hydraulic_fixed_point_relative_tolerance),
                "closed": maximum_dynamic_hydraulic_fixed_point_residual <= float(
                    request.dynamic_hydraulic_fixed_point_relative_tolerance
                ),
            } if dynamic_hydraulic_advection is not None else None),
            "hydraulic_component_advection_source_sha256": (
                hydraulic_advection.hydraulic_result_sha256 if hydraulic_advection else None
            ),
            "hydraulic_boundary_schedule_sha256": (
                hydraulic_advection.boundary_schedule_sha256 if hydraulic_advection
                else dynamic_hydraulic_advection.schedule_sha256 if dynamic_hydraulic_advection else None
            ),
            "maximum_normalized_hydraulic_boundary_closure_residual": maximum_hydraulic_boundary_closure_ratio,
            "hydraulic_boundary_charge_ledger_closed": hydraulic_charge_closed,
            "hydraulic_boundary_net_charge_change_mol_eq_by_time": hydraulic_charge_net_history.tolist() if hydraulic_transport_enabled else None,
            "hydraulic_boundary_exchange_component_change_mol_by_side_and_time": (
                hydraulic_ledger_history[:2*ncomp].T.tolist() if hydraulic_transport_enabled else None
            ),
            "hydraulic_boundary_exchange_element_change_mol_by_side_and_time": (
                hydraulic_ledger_history[2*ncomp:2*ncomp+2*len(element_ids)].T.tolist() if hydraulic_transport_enabled else None
            ),
            "hydraulic_boundary_exchange_charge_change_mol_eq_by_side_and_time": (
                hydraulic_ledger_history[-2:].T.tolist() if hydraulic_transport_enabled else None
            ),
            "capacitive_current_schedule_sha256": (request.capacitive_current_schedule.schedule_sha256
                                                   if request.capacitive_current_schedule is not None else None),
            "capacitive_current_source_id": (
                request.capacitive_current_schedule.evidence[0].source_id
                if request.capacitive_current_schedule is not None else None
            ),
            "capacitive_current_evidence_sha256": ([row.sha256 for row in request.capacitive_current_schedule.evidence]
                                                   if request.capacitive_current_schedule is not None else []),
            "integrated_capacitive_charge_C_by_cell_and_time": integrated_capacitive_charge_C_by_cell_and_time.T.tolist(),
            "dynamic_double_layer_state_enabled": dynamic_double_layer is not None,
            "dynamic_double_layer_state_source_id": (
                DYNAMIC_DOUBLE_LAYER_BDF_SOURCE_ID if dynamic_double_layer is not None else None
            ),
            "dynamic_double_layer_charge_C_by_cell_and_time": (
                dynamic_double_layer_charge_history.T.tolist() if dynamic_double_layer is not None else None
            ),
            "dynamic_double_layer_interfacial_potential_V_by_time_and_cell": (
                dynamic_double_layer_potential_history.T.tolist() if dynamic_double_layer is not None else None
            ),
            "dynamic_double_layer_solution_potential_V_by_time_and_cell_relative_to_metal_gauge": (
                (-dynamic_double_layer_potential_history).T.tolist() if dynamic_double_layer is not None else None
            ),
            "dynamic_double_layer_capacitance_curve_sha256": (
                dynamic_double_layer.capacitance_curve_sha256 if dynamic_double_layer is not None else None
            ),
            "dynamic_double_layer_capacitance_evidence_sha256": (
                [row.sha256 for row in dynamic_double_layer.capacitance_evidence]
                if dynamic_double_layer is not None else []
            ),
            "dynamic_double_layer_initial_state_record_sha256": (
                dynamic_double_layer.initial_state_record_sha256 if dynamic_double_layer is not None else None
            ),
            "dynamic_double_layer_initial_state_evidence_sha256": (
                [row.sha256 for row in dynamic_double_layer.initial_state_evidence]
                if dynamic_double_layer is not None else []
            ),
            "exact_knot_ionic_face_current_A_by_boundary": exact_knot_current,
            "exact_knot_branch_current_density_A_m2_by_branch_and_cell": [
                row.get("branch_current_density_A_m2_by_branch_and_cell", {})
                for row in stage_mixed_knot_lineage
            ],
            "exact_knot_current_time_s": list(request.time_s),
            "ionic_face_current_schedule_sha256": (
                canonical_digest(request.ionic_face_current_schedule.model_dump(mode="json"))
                if request.ionic_face_current_schedule is not None else None
            ),
            "ionic_face_current_source_id": (
                STAGE_SPATIAL_MIXED_POTENTIAL_SOURCE_ID if faradaic_stage
                else CALLER_IONIC_CURRENT_SOURCE_ID if request.ionic_face_current_schedule is not None else None
            ),
            "ionic_face_current_evidence_sha256": (
                canonical_digest([row.model_dump(mode="json")
                                 for row in request.ionic_face_current_schedule.evidence])
                if request.ionic_face_current_schedule is not None else None
            ),
            "charge_continuity_knot_diagnostics": charge_continuity_knots,
            "maximum_face_current_residual_A": maximum_face_current_residual_A,
            "maximum_face_current_scale_A": maximum_face_current_scale_A,
            "cell_ids": [row.cell_id for row in request.cells],
            "time_s": list(request.time_s),
            "species_concentration_mol_m3_by_species_time_cell": species_by_time_cell,
            "activity_coefficient_by_species_time_cell": gamma_by_time_cell,
            "component_ledgers": closure_records,
            "element_ledgers": element_ledger_records if element_ids else None,
            "component_to_element_basis": {
                element_id: {
                    component_id: float(component_element_coefficient[element_index, component_index])
                    for component_index, component_id in enumerate(component_ids)
                }
                for element_index, element_id in enumerate(element_ids)
            } if element_ids else None,
            "component_state_basis": ("total_aqueous_plus_kinetic_candidate_solid" if kinetic_mode
                                      else "total_aqueous_plus_candidate_solid" if solid_mode
                                      else "aqueous_component_inventory"),
            "aqueous_component_inventory_mol_by_component_time_cell": (
                kinetic_aqueous_component_history if kinetic_mode else aqueous_component_history if solid_mode else None
            ),
            "solid_component_inventory_mol_by_component_time_cell": (
                kinetic_solid_component_history if kinetic_mode else solid_component_history if solid_mode else None
            ),
            "solid_phase_inventory_mol_by_cell_phase_time": solid_phase_history_by_cell if (solid_mode or kinetic_mode) else None,
            "kinetic_phase_mode_enabled": kinetic_mode,
            "kinetic_phase_sets_by_cell": ([{
                "cell_id": row.cell_id,
                "phase_set_id": row.phase_set_id,
                "phase_set_sha256": row.phase_set_sha256,
                "phase_candidate_ids": [phase.solid_species_id for phase in row.phase_candidates],
                "initial_solid_moles_by_phase": {
                    amount.solid_species_id: float(amount.initial_solid_moles_mol)
                    for amount in row.initial_solid_inventory_by_phase
                },
            } for row in kinetic_phase_sets] if kinetic_mode else None),
            "kinetic_phase_rate_evaluations": kinetic_rate_evaluations,
            "kinetic_phase_rate_records_by_time": [
                {"time_s": time_value, "phase_rates": rows}
                for time_value, rows in sorted(kinetic_rate_records_by_time.items())
            ] if kinetic_mode else None,
            "maximum_absolute_kinetic_phase_rate_mol_s": maximum_kinetic_phase_rate_mol_s,
            "kinetic_phase_rate_evaluation_budget": request.kinetic_rate_evaluation_budget,
            "phase_seed_transitions": list(event_report.get("seed_transitions", ())) if event_report else None,
            "phase_depletion_events": list(event_report.get("phase_depletions", ())) if event_report else None,
            "kinetic_event_rhs_evaluations": event_report.get("rhs_evaluations", 0) if event_report else None,
            "solid_phase_sets_by_cell": [
                {
                    "cell_id": row.cell_id,
                    "assessment_id": row.assessment_id,
                    "asset_id": row.asset_id,
                    "location_id": row.location_id,
                    "physical_scope_id": row.physical_scope_id,
                    "phase_set_id": row.phase_set_id,
                    "phase_set_sha256": row.phase_set_sha256,
                    "clock_id": row.clock_id,
                    "valid_time_s": list(row.valid_time_s),
                    "material_condition_id": row.material_condition_id,
                    "metallurgy_id": row.metallurgy_id,
                    "environment_id": row.environment_id,
                    "temperature_K": row.temperature_K,
                    "activity_standard_state_id": row.activity_standard_state_id,
                    "phase_set_evidence_sha256": canonical_digest([
                        evidence.model_dump(mode="json") for evidence in row.phase_set_evidence
                    ]),
                    "phase_candidate_ids": [phase.solid_species_id for phase in row.phase_candidates],
                }
                for row in request.solid_phase_sets_by_cell
            ] if solid_mode else None,
            "electrochemical_source_ledgers": source_ledger,
            "maximum_normalized_component_closure_residual": maximum_residual,
            "all_component_ledgers_close": committed,
            "all_hydraulic_boundary_ledgers_close": (maximum_hydraulic_boundary_closure_ratio <= 1.0 and hydraulic_charge_closed) if hydraulic_transport_enabled else None,
            "rhs_evaluations": rhs_evaluations,
            "stage_equilibrium_calls": equilibrium_calls,
            "solid_partition_evaluations": solid_partition_evaluations,
            "solid_active_set_sweeps": solid_active_set_sweeps,
            "solid_bisection_iterations": solid_bisection_iterations,
            "source_projection_operations": source_projection_operations,
            "ionic_current_face_evaluations": ionic_current_face_evaluations,
            "stage_mixed_potential_function_evaluations": stage_mixed_potential_evaluations,
            "integrated_ionic_charge_C_by_face_and_time": current_charge_history.T.tolist(),
            "reserved_nested_equilibrium_iteration_work_bound": nested_equilibrium_work_bound,
            "stage_equilibrium_lineage_chain_sha256": lineage_chain,
            "stage_mixed_potential_lineage_chain_sha256": lineage_chain if faradaic_stage else None,
            "stage_mixed_potential_knot_lineage": stage_mixed_knot_lineage,
            "knot_equilibrium_lineage": knot_equilibrium_digests,
            "committed": committed,
            "qualification_claimed": False,
            "limitations": [
                "The integrated state is conserved component moles at fixed cell volumes; species concentrations are local Davies/mass-action equilibrium reconstructions.",
                ("Species face fluxes use caller diffusivity and geometry with zero ionic current by default; a paired, reviewed current schedule may prescribe nonzero interior current for charge-producing caller extents. Caller source extent and source-reservoir ledgers remain explicit." if hydraulic_transport_enabled else "Species face fluxes use caller diffusivity and geometry with zero ionic current by default; a paired, reviewed current schedule may prescribe nonzero interior current for charge-producing caller extents. No hydraulic advection or external boundary flux is applied."),
                *( ["Opt-in hydraulic advection uses a digest-bound lumped inertance flow history, exact signed flow at each BDF RHS, stage-equilibrium upwind concentrations and caller reservoir compositions. Aperture and cell volume remain fixed; left/right component, element and charge exchanges are integrated as separate boundary reservoir ledgers."] if hydraulic_advection is not None else [] ),
                *( ["Opt-in dynamic hydraulic transport couples trial solid-equilibrium aperture/volume to cell liquid-volume rates, slit momentum and upwind component flux in a bounded damped fixed point at every RHS. A directional finite-difference volume-rate estimate is used. This is an unverified user model; electrochemical Faradaic area feedback, deposition mechanics, compressibility, turbulence and qualification are outside scope."] if dynamic_hydraulic_advection is not None else [] ),
                "Opt-in stage mixed-potential mode recomputes spatial Ohmic/Butler-Volmer at each component-state trial and projects branch extents plus its face current into the same component RHS after charge and component closure checks; it does not modify the existing species-state Crevice BDF solver.",
                "Opt-in instantaneous solid mode interprets BDF component states as total liquid-plus-candidate-solid inventory and re-partitions each cell at every RHS trial; candidate phase sets are constant over the exact declared clock/horizon and do not include nucleation or kinetics.",
                "Sequential caller-ordered phase active-set results do not prove global Gibbs-energy stability or uniqueness.",
            ],
        })
    except (ArithmeticError, FloatingPointError, OverflowError, RuntimeError, ValueError, KeyError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID,
            "assessment_id": request.assessment_id,
            "input_sha256": digest,
            "reason": str(error),
            "rhs_evaluations": locals().get("rhs_evaluations", 0),
            "stage_equilibrium_calls": locals().get("equilibrium_calls", 0),
            "solid_partition_evaluations": locals().get("solid_partition_evaluations", 0),
            "solid_active_set_sweeps": locals().get("solid_active_set_sweeps", 0),
            "solid_bisection_iterations": locals().get("solid_bisection_iterations", 0),
            "dynamic_geometry_iterations": locals().get("dynamic_geometry_iterations", 0),
            "maximum_dynamic_geometry_relative_volume_residual": locals().get("maximum_dynamic_geometry_residual", 0.0),
            "dynamic_geometry_relative_tolerance": float(request.dynamic_geometry_relative_tolerance),
            "dynamic_geometry_iteration_budget": request.maximum_total_dynamic_geometry_iterations,
            "dynamic_hydraulic_iterations": locals().get("dynamic_hydraulic_iterations", 0),
            "maximum_dynamic_hydraulic_fixed_point_residual": locals().get(
                "maximum_dynamic_hydraulic_fixed_point_residual", 0.0
            ),
            "dynamic_hydraulic_fixed_point_relative_tolerance": float(
                request.dynamic_hydraulic_fixed_point_relative_tolerance
            ),
            "dynamic_hydraulic_fixed_point_iteration_budget": request.maximum_dynamic_hydraulic_fixed_point_iterations,
            "source_projection_operations": locals().get("source_projection_operations", 0),
            "ionic_current_face_evaluations": locals().get("ionic_current_face_evaluations", 0),
            "stage_mixed_potential_function_evaluations": locals().get("stage_mixed_potential_evaluations", 0),
            "reserved_nested_equilibrium_iteration_work_bound": locals().get("nested_equilibrium_work_bound", 0),
            "committed": False,
            "qualification_claimed": False,
        })


def specifications() -> tuple[ModelSpec, ...]:
    bdf_spec = ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceComponentStateBDFRequest,
        evaluator=solve_crevice_component_state_bdf,
        units={
            "time_s[]": "s",
            "cells[].solution_volume_L": "L",
            "initial_component_inventory[].inventory_mol_by_cell[]": "mol",
            "electrochemical_sources[].extent_rate_mol_s_by_knot_and_cell[][]": "mol/s",
            "electrochemical_source_ledgers[].extent_mol_by_cell[]": "mol",
            "ionic_face_current_schedule_A_by_knot_and_face[][]": "A",
            "capacitive_current_schedule.current_A_by_knot_and_cell[][]": "A",
            "hydraulic_component_advection.left_boundary_species_concentration_mol_m3_by_knot[][]": "mol/m^3",
            "hydraulic_component_advection.right_boundary_species_concentration_mol_m3_by_knot[][]": "mol/m^3",
            "dynamic_hydraulic_component_advection.signed_pressure_drop_Pa_by_knot[]": "Pa",
            "dynamic_hydraulic_component_advection.left_boundary_species_concentration_mol_m3_by_knot[][]": "mol/m^3",
            "dynamic_hydraulic_component_advection.right_boundary_species_concentration_mol_m3_by_knot[][]": "mol/m^3",
            "dynamic_hydraulic_component_advection.transverse_width_m": "m",
            "dynamic_hydraulic_component_advection.density_kg_m3": "kg/m^3",
            "dynamic_hydraulic_component_advection.dynamic_viscosity_Pa_s": "Pa*s",
            "dynamic_hydraulic_component_advection.maximum_abs_flow_m3_s": "m^3/s",
            "dynamic_hydraulic_component_advection.initial_signed_volumetric_flow_m3_s": "m^3/s",
            "dynamic_hydraulic_fixed_point_relative_tolerance": "1",
            "dynamic_hydraulic_fixed_point_relaxation": "1",
            "absolute_flow_tolerance_m3_s": "m^3/s",
            "dynamic_inlet_flow_m3_s_by_time[]": "m^3/s",
            "dynamic_hydraulic_fixed_point_work.maximum_normalized_volume_rate_residual": "1",
            "dynamic_hydraulic_fixed_point_work.relative_tolerance": "1",
            "dynamic_hydraulic_iterations": "1",
            "maximum_dynamic_hydraulic_fixed_point_residual": "1",
            "dynamic_hydraulic_fixed_point_iteration_budget": "1",
            "hydraulic_boundary_exchange_component_change_mol_by_side_and_time[][]": "mol",
            "hydraulic_boundary_exchange_element_change_mol_by_side_and_time[][]": "mol",
            "hydraulic_boundary_exchange_charge_change_mol_eq_by_side_and_time[][]": "mol_eq",
            "integrated_capacitive_charge_C_by_cell_and_time[][]": "C",
            "dynamic_double_layer.initial_interfacial_potential_V_by_cell[]": "V",
            "dynamic_double_layer.reference_interfacial_potential_V_by_cell[]": "V",
            "dynamic_double_layer.differential_capacitance_potential_axis_V[]": "V",
            "dynamic_double_layer.differential_capacitance_F_m2[]": "F/m^2",
            "absolute_double_layer_charge_tolerance_C": "C",
            "dynamic_double_layer_charge_C_by_cell_and_time[][]": "C",
            "dynamic_double_layer_interfacial_potential_V_by_time_and_cell[][]": "V",
            "dynamic_double_layer_solution_potential_V_by_time_and_cell_relative_to_metal_gauge[][]": "V",
            "exact_knot_ionic_face_current_A_by_boundary[][]": "A",
            "exact_knot_branch_current_density_A_m2_by_branch_and_cell.*[][]": "A/m^2",
            "exact_knot_current_time_s[]": "s",
            "stage_mixed_potential_function_evaluations": "1",
            "integrated_ionic_charge_C_by_face_and_time[][]": "C",
            "electrochemical_source_ledgers[].external_reservoir_element_change_mol.*[]": "mol",
            "electrochemical_source_ledgers[].external_reservoir_component_change_mol_by_cell.*[]": "mol",
            "electrochemical_source_ledgers[].external_reservoir_charge_change_mol_eq": "mol_eq",
            "aqueous_component_inventory_mol_by_component_time_cell.*[][]": "mol",
            "solid_component_inventory_mol_by_component_time_cell.*[][]": "mol",
            "solid_phase_inventory_mol_by_cell_phase_time.*.*[]": "mol",
            "kinetic_phase_sets_by_cell[].initial_solid_moles_by_phase.*": "mol",
            "kinetic_phase_rate_evaluations": "1",
            "maximum_absolute_kinetic_phase_rate_mol_s": "mol/s",
            "kinetic_event_policy.event_count": "1",
            "element_ledgers[].total_inventory_mol_by_time_and_cell[][]": "mol",
            "element_ledgers[].integrated_face_transfer_mol_by_time_and_face[][]": "mol",
            "element_ledgers[].integrated_aqueous_source_change_mol_by_cell[]": "mol",
            "element_ledgers[].integrated_external_reservoir_change_mol_by_cell[]": "mol",
            "solid_partition_evaluations": "1",
            "solid_active_set_sweeps": "1",
            "solid_bisection_iterations": "1",
            "dynamic_geometry_iterations": "1",
            "maximum_dynamic_geometry_relative_volume_residual": "1",
            "dynamic_geometry_relative_tolerance": "1",
            "dynamic_geometry_iteration_budget": "1",
            "dynamic_solid_geometry_by_cell[].cell_length_m": "m",
            "dynamic_solid_geometry_by_cell[].transverse_width_m": "m",
            "dynamic_solid_geometry_by_cell[].initial_aperture_m": "m",
            "dynamic_solid_geometry_by_cell[].minimum_aperture_m": "m",
            "dynamic_solid_geometry_by_cell[].phase_geometry[].molar_volume_m3_mol": "m^3/mol",
            "exact_knot_dynamic_geometry_by_cell[][].solution_volume_L": "L",
            "exact_knot_dynamic_geometry_by_cell[][].aperture_m": "m",
            "exact_knot_dynamic_geometry_by_cell[][].cross_section_area_m2": "m^2",
            "exact_knot_dynamic_geometry_by_cell[][].normalized_fixed_point_residual": "1",
            "reserved_nested_equilibrium_iteration_work_bound": "1",
            "maximum_normalized_component_closure_residual": "1",
            "maximum_normalized_hydraulic_boundary_closure_residual": "1",
            "interior_face_area_m2[]": "m^2",
            "center_distance_m_by_interior_face[]": "m",
            "species_face_diffusivity[].diffusivity_m2_s_by_interior_face[]": "m^2/s",
            "component_ledgers[].inventory_mol_by_time_and_cell[][]": "mol",
            "component_ledgers[].integrated_face_transfer_mol_by_time_and_face[][]": "mol",
            "species_concentration_mol_m3_by_species_time_cell.*[][]": "mol/m^3",
            "activity_coefficient_by_species_time_cell.*[][]": "1",
            "maximum_face_current_residual_A": "A",
            "maximum_face_current_scale_A": "A",
            "ionic_current_face_evaluations": "1",
            "source_projection_operations": "1",
            "dynamic_hydraulic_iterations": "1",
        },
        assumptions=(
            "BDF state variables are component moles, and each aqueous reaction conserves every transported component map.",
            "Each trial state is projected to local caller-evidenced single-liquid Davies/mass-action equilibrium before the RHS is formed; volume is fixed by default, while the opt-in solid-occupancy geometry mode iterates equilibrium at the derived trial volume.",
            "Interior species Nernst-Planck diffusion uses caller-supplied face diffusivity/geometry; a per-face algebraic migration field enforces the requested ionic current.",
            "Optional fixed-geometry hydraulic advection uses digest-bound transient slit flow and electroneutral reservoir compositions with upwind stage concentrations.",
            "Optional moving-geometry hydraulic transport uses an explicit signed pressure and electroneutral boundary-composition schedule, trial solid-equilibrium aperture, directional finite-difference liquid-volume rate, slit momentum, upwind component flux and integrated reservoir ledgers in a damped fixed point. It has not been physically verified; Faradaic area coupling is rejected.",
            "The default aqueous-only mode excludes solid transfer; the opt-in total-component solid-equilibrium mode is separate. Caller source schedules and reviewed spatial Ohmic/Butler-Volmer stage coupling remain mutually exclusive.",
            "The stage electrochemical path rejects conflicting caller extent/current schedules, enforces a caller branch-rate bound and a total stage-work budget, and records branch/evidence digests and knot lineage.",
            "Schema v7 optionally appends per-cell integrated double-layer charge to the BDF state. At every trial, the caller Cdl curve is inverted without extrapolation, trial chemistry refreshes Nernst equilibrium potentials and conductivity, spatial Ohmic face current is reconstructed, and branch Faradaic current plus charge continuity provide same-stage chemical source and charge derivatives. This mode requires fixed geometry and insulated ionic boundaries; moving hydraulic coupling and external circuit forcing are not represented.",
            "Opt-in dynamic geometry is restricted to aqueous plus instantaneous-solid equilibrium. At each BDF RHS and exact output knot, a damped fixed-point iteration maps caller-mapped gap-occupying solid moles through caller-reviewed molar volumes to aperture and solution volume, repeats equilibrium at that volume, and uses the resulting interpolated cell cross-section for NP face conductance. This is a bounded operator-split stage solve, not a monolithic coupled geometry/chemistry Newton solve; deposition mechanics, porosity, particle packing, fracture, and unlisted phases are outside scope.",
            "Dynamic geometry fails closed when the aperture reaches its caller minimum, the relative volume fixed-point residual exceeds tolerance, or the per-cell-stage or aggregate geometry iteration budget is exhausted. Fixed-volume v1-v3 behavior and the default mode are retained.",
            "Opt-in solid equilibrium mode treats the BDF conserved-component state as liquid-plus-candidate-solid total inventory and invokes a digest-bound, cell-specific instantaneous phase partition at every trial before NP/Faradaic flux evaluation; aqueous-only mode remains the default.",
            "Opt-in kinetic phase mode evolves total component inventory together with explicit per-phase solid moles. Every trial is equilibrated against the derived dissolved inventory, evaluates dimensionless ion activities and saturation ratios, then applies caller-pinned nucleation/growth laws in the same BDF stage; seed and depletion crossings restart at accepted event boundaries. Kinetic moving geometry maps explicit solid moles to gap occupancy. This user model is not independently verified or qualified.",
            "Solid mode requires the component basis to reconstruct every declared element, closes cellwise total-component and element balances plus external reservoir and current/charge ledgers, and aggregates partition, active-set, bisection and nested-equilibrium work across RHS and knot snapshots.",
            "Solid phase candidate identities and thermochemical records are stationary across the exact request clock/horizon and caller reviewed. Candidate amounts may change through instantaneous equilibrium and, in the opt-in geometry mode, change aperture and liquid volume. Phase kinetics, nucleation, global Gibbs minimization, discovery of unlisted phases and qualification are not calculated.",
            "Optional fixed-geometry hydraulic advection applies the exact interval inertance flow with signed upwind stage species concentrations and explicit neutral left/right reservoir states; its boundary component/element/charge amounts are separately integrated into the ODE ledger.",
            "Optional capacitive current is supplied as an exact-knot per-cell schedule, enters charge continuity with the declared sign convention, and is linearly interpolated with the matching ionic face-current schedule. It is forcing-only and cannot be interpreted as a solved potential/charge state or a Cdl constitutive relation.",
            "Capacitive-current schedules are forcing-only; schema-v7 same-stage dynamic double-layer owns its capacitive charge and ionic current and rejects caller capacitive/ionic schedules.",
        ),
        source_ids=(COMPONENT_STATE_SOURCE_ID, STAGE_EQUILIBRIUM_SOURCE_ID,
                    ELECTRONEUTRAL_NP_SOURCE_ID,
                    CALLER_ELECTROCHEMICAL_SOURCE_ID,
                    CALLER_IONIC_CURRENT_SOURCE_ID,
                    CALLER_CAPACITIVE_CURRENT_SOURCE_ID,
                    STAGE_SPATIAL_MIXED_POTENTIAL_SOURCE_ID,
                    STAGE_SOLID_PARTITION_SOURCE_ID,
                    "caller_evidenced_solid_molar_volume_gap_occupancy_fixed_point_geometry",
                    SCHEDULE_BINDING_SOURCE_ID,
                    "caller_general_aqueous_mass_action_speciation",
                    "nist_codata_faraday_constant_2022",
                    "caller_lumped_slit_inertance_resistance",
                    CALLER_HYDRAULIC_ADVECTION_SOURCE_ID,
                    DYNAMIC_HYDRAULIC_SOURCE_ID,
                    "caller_evidenced_dynamic_double_layer_and_faradaic_polarization_curves",
                    DYNAMIC_DOUBLE_LAYER_INITIAL_STATE_SOURCE_ID,
                    DYNAMIC_DOUBLE_LAYER_BDF_SOURCE_ID,
                    "same_stage_activity_based_competing_solid_kinetics_with_seed_depletion_events"),
        version="1.7.0",
        qualification="user_model",
    )
    return (bdf_spec, *_crevice_bdf_kinetic_phase_set_specifications())
