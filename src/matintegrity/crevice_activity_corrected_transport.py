"""Caller-field activity-corrected Nernst–Planck transport in a fixed crevice slit."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "transport.crevice_activity_corrected_nernst_planck_1d"
SPECIES_SOURCE_ID = "caller_crevice_activity_corrected_transport_species"
FIELD_SOURCE_ID = "caller_crevice_activity_coefficient_cell_time_fields"
BOUNDARY_SOURCE_ID = "caller_crevice_activity_corrected_mouth_boundary_history"
METHOD_SOURCE_ID = "finite_volume_activity_corrected_zero_current_nernst_planck_transport"
REACTIVE_MODEL_ID = "transport.crevice_activity_corrected_reactive_nernst_planck_1d"
REACTION_SOURCE_ID = "caller_activity_based_crevice_reaction_network"
REACTIVE_METHOD_SOURCE_ID = "finite_volume_activity_nernst_planck_with_local_mass_action"


class CreviceActivityTransportSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    diffusivity_m2_s: Positive
    initial_cell_concentration_mol_m3: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    activity_coefficient_by_time_and_cell: tuple[tuple[Positive, ...], ...] = Field(min_length=2, max_length=500)
    mouth_activity_coefficient_by_time: tuple[Positive, ...] = Field(min_length=2, max_length=500)


class CreviceActivityCorrectedTransportRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    length_m: Positive
    cross_section_area_m2: Positive
    cell_count: int = Field(ge=2, le=300)
    output_time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    concentration_standard_state_mol_m3: Positive = 1000.0
    species: tuple[CreviceActivityTransportSpecies, ...] = Field(min_length=2, max_length=40)
    mouth_boundary_concentration_mol_m3_by_species: dict[str, tuple[Positive, ...]] = Field(min_length=2, max_length=40)
    cell_face_axial_velocity_m_s_by_knot: tuple[tuple[float, ...], ...] = Field(min_length=3, max_length=301)
    relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    absolute_tolerance_mol_m3: Positive = Field(default=1e-10)
    maximum_step_s: Positive
    maximum_function_evaluations: int = Field(default=300000, ge=100, le=10_000_000)
    provider_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    fixed_geometry_and_cell_order_reviewed: bool
    activity_standard_state_single_ion_convention_reviewed: bool
    activity_fields_and_time_interpolation_reviewed: bool
    diffusivity_and_temperature_support_reviewed: bool
    face_velocity_sign_mapping_reviewed: bool
    local_electroneutrality_and_zero_current_reviewed: bool
    mouth_boundary_and_blind_tip_reviewed: bool
    reaction_free_single_liquid_interval_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_transport_basis(self):
        if not all((
            self.fixed_geometry_and_cell_order_reviewed,
            self.activity_standard_state_single_ion_convention_reviewed,
            self.activity_fields_and_time_interpolation_reviewed,
            self.diffusivity_and_temperature_support_reviewed,
            self.face_velocity_sign_mapping_reviewed,
            self.local_electroneutrality_and_zero_current_reviewed,
            self.mouth_boundary_and_blind_tip_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("all geometry, activity, transport, boundary, applicability and authorization reviews are required")
        if getattr(self, "reactions", ()):
            if not getattr(self, "activity_mass_action_network_reviewed", False):
                raise ValueError("the activity-based kinetic network must be explicitly reviewed")
        elif not self.reaction_free_single_liquid_interval_reviewed:
            raise ValueError("reaction-free transport must be explicitly declared")
        times = self.output_time_s
        if any(not math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
            raise ValueError("output times must be finite and strictly increasing")
        ids = [row.species_id for row in self.species]
        if len(ids) != len(set(ids)) or not any(row.charge_number > 0 for row in self.species) or not any(
            row.charge_number < 0 for row in self.species
        ):
            raise ValueError("species IDs must be unique and include positive and negative ions")
        if set(self.mouth_boundary_concentration_mol_m3_by_species) != set(ids):
            raise ValueError("mouth concentration schedules must cover every declared species exactly")
        if any(len(row) != len(times) for row in self.mouth_boundary_concentration_mol_m3_by_species.values()):
            raise ValueError("mouth concentration schedules must align with time knots")
        if len(self.cell_face_axial_velocity_m_s_by_knot) != self.cell_count + 1:
            raise ValueError("velocity history must contain one schedule for each spatial face")
        if any(len(row) != len(times) or any(not math.isfinite(v) for v in row)
               for row in self.cell_face_axial_velocity_m_s_by_knot):
            raise ValueError("velocity schedules must be finite and align with time knots")
        if any(v != 0.0 for v in self.cell_face_axial_velocity_m_s_by_knot[-1]):
            raise ValueError("blind-tip velocity must be exactly zero at every knot")
        for row in self.species:
            if len(row.initial_cell_concentration_mol_m3) != self.cell_count:
                raise ValueError("initial concentration fields must align with cell count")
            if len(row.activity_coefficient_by_time_and_cell) != len(times) or any(
                len(knot) != self.cell_count for knot in row.activity_coefficient_by_time_and_cell
            ):
                raise ValueError("activity coefficient field must align with every time knot and cell")
            if len(row.mouth_activity_coefficient_by_time) != len(times):
                raise ValueError("mouth activity coefficients must align with time knots")
        z = {row.species_id: row.charge_number for row in self.species}
        for cell in range(self.cell_count):
            charge = math.fsum(row.charge_number * row.initial_cell_concentration_mol_m3[cell] for row in self.species)
            scale = math.fsum(abs(row.charge_number) * row.initial_cell_concentration_mol_m3[cell] for row in self.species)
            if scale == 0 or abs(charge) > 1e-9 * scale:
                raise ValueError("initial cell composition must be locally electroneutral")
        for knot in range(len(times)):
            charge = math.fsum(z[key] * values[knot] for key, values in self.mouth_boundary_concentration_mol_m3_by_species.items())
            scale = math.fsum(abs(z[key]) * values[knot] for key, values in self.mouth_boundary_concentration_mol_m3_by_species.items())
            if scale == 0 or abs(charge) > 1e-9 * scale:
                raise ValueError("mouth boundary must be locally electroneutral at every knot")
        if not any(row.source_id == self.provider_id and row.sha256 for row in self.provider_evidence):
            raise ValueError("provider Evidence must bind declared provider identity to a digest")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights Evidence must identify a license or permitted-use basis")
        return self


class CreviceActivityReactiveSpecies(CreviceActivityTransportSpecies):
    elemental_composition: dict[str, StrictInt] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def valid_elements(self):
        if any(not name.strip() or count < 0 for name, count in self.elemental_composition.items()):
            raise ValueError("elemental composition requires nonempty symbols and nonnegative counts")
        return self


class CreviceActivityReactiveTerm(Contract):
    species_id: str = Field(min_length=1)
    coefficient: StrictInt = Field(ge=1, le=16)


class CreviceActivityReactiveReaction(Contract):
    reaction_id: str = Field(min_length=1)
    reactants: tuple[CreviceActivityReactiveTerm, ...] = Field(min_length=1, max_length=24)
    products: tuple[CreviceActivityReactiveTerm, ...] = Field(min_length=1, max_length=24)
    forward_rate_constant_mol_m3_s_by_knot: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    reverse_rate_constant_mol_m3_s_by_knot: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    equilibrium_constant_dimensionless_by_knot: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    parameter_record_id: str = Field(min_length=1)
    parameter_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def validate_rate_record_digest(self):
        payload = {
            "reaction_id": self.reaction_id,
            "forward_rate_constant_mol_m3_s_by_knot": self.forward_rate_constant_mol_m3_s_by_knot,
            "reverse_rate_constant_mol_m3_s_by_knot": self.reverse_rate_constant_mol_m3_s_by_knot,
            "equilibrium_constant_dimensionless_by_knot": self.equilibrium_constant_dimensionless_by_knot,
        }
        if canonical_digest(payload) != self.parameter_record_sha256:
            raise ValueError("rate-record digest must bind exact reaction and full parameter schedules")
        if not any(row.source_id == self.parameter_record_id and row.sha256 == self.parameter_record_sha256
                   and row.license_id for row in self.evidence):
            raise ValueError("licensed Evidence must pin the declared reaction parameter record")
        return self


class CreviceActivityReactiveTransportRequest(CreviceActivityCorrectedTransportRequest):
    schema_version: Literal["matintegrity.crevice_activity_corrected_reactive_transport.v1"] = (
        "matintegrity.crevice_activity_corrected_reactive_transport.v1"
    )
    species: tuple[CreviceActivityReactiveSpecies, ...] = Field(min_length=2, max_length=40)
    reactions: tuple[CreviceActivityReactiveReaction, ...] = Field(min_length=1, max_length=100)
    temperature_K_by_knot: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    reaction_network_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reaction_network_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    reaction_free_single_liquid_interval_reviewed: bool = False
    activity_mass_action_network_reviewed: bool
    reaction_charge_element_balance_reviewed: bool
    kinetic_parameter_temperature_support_reviewed: bool

    @model_validator(mode="after")
    def validate_reaction_network(self):
        if not all((self.activity_mass_action_network_reviewed, self.reaction_charge_element_balance_reviewed,
                    self.kinetic_parameter_temperature_support_reviewed)):
            raise ValueError("activity kinetics, reaction balance and temperature support reviews are required")
        nt = len(self.output_time_s)
        if len(self.temperature_K_by_knot) != nt:
            raise ValueError("temperature schedule must align with transport time knots")
        ids = [row.reaction_id for row in self.reactions]
        if len(ids) != len(set(ids)):
            raise ValueError("reaction IDs must be unique")
        species = {row.species_id: row for row in self.species}
        for reaction in self.reactions:
            if any(len(schedule) != nt for schedule in (
                reaction.forward_rate_constant_mol_m3_s_by_knot,
                reaction.reverse_rate_constant_mol_m3_s_by_knot,
                reaction.equilibrium_constant_dimensionless_by_knot,
            )):
                raise ValueError("kinetic and equilibrium schedules must align with every transport knot")
            terms = (*reaction.reactants, *reaction.products)
            if any(row.species_id not in species for row in terms):
                raise ValueError("reaction terms must reference declared transport species")
            if len({row.species_id for row in reaction.reactants}) != len(reaction.reactants) or len(
                {row.species_id for row in reaction.products}
            ) != len(reaction.products):
                raise ValueError("species may appear only once per side of a reaction")
            net: dict[str, int] = {}
            for row in reaction.reactants:
                net[row.species_id] = net.get(row.species_id, 0) - row.coefficient
            for row in reaction.products:
                net[row.species_id] = net.get(row.species_id, 0) + row.coefficient
            if not any(net.values()):
                raise ValueError("reaction must have a nonzero net stoichiometric vector")
            if sum(net.get(row.species_id, 0) * row.charge_number for row in self.species) != 0:
                raise ValueError("reaction must conserve charge")
            elements = set().union(*(row.elemental_composition.keys() for row in self.species))
            for element in elements:
                if sum(net.get(row.species_id, 0) * row.elemental_composition.get(element, 0)
                       for row in self.species) != 0:
                    raise ValueError(f"reaction must conserve element {element!r}")
            for kf, kr, equilibrium in zip(
                reaction.forward_rate_constant_mol_m3_s_by_knot,
                reaction.reverse_rate_constant_mol_m3_s_by_knot,
                reaction.equilibrium_constant_dimensionless_by_knot,
                strict=True,
            ):
                log_error = math.log(kf) - math.log(kr) - math.log(equilibrium)
                if abs(log_error) > math.log1p(1e-6):
                    raise ValueError(f"reaction {reaction.reaction_id!r} violates detailed balance at a knot")
        expected_network_digest = canonical_digest([row.model_dump(mode="json") for row in self.reactions])
        if self.reaction_network_sha256 != expected_network_digest:
            raise ValueError("reaction-network digest must bind the exact ordered reaction schedules")
        if not any(row.source_id == REACTION_SOURCE_ID and row.sha256 == self.reaction_network_sha256
                   for row in self.reaction_network_evidence):
            raise ValueError("reaction-network Evidence must bind the exact caller reaction-network digest")
        return self


def solve_crevice_activity_corrected_transport(
    request: CreviceActivityCorrectedTransportRequest,
    *,
    model_id: str = MODEL_ID,
) -> Calculation:
    """Integrate finite-volume cell inventories with caller gamma fields and zero-current face closure."""
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values={"model_id": model_id, "reason": "scipy_runtime_unavailable"})

    digest = canonical_digest(request.model_dump(mode="json"))
    rows = request.species
    ns, nc, nt = len(rows), request.cell_count, len(request.output_time_s)
    times = np.asarray(request.output_time_s, dtype=float)
    dx = request.length_m / nc
    z = np.asarray([row.charge_number for row in rows], dtype=float)
    diffusivity = np.asarray([row.diffusivity_m2_s for row in rows], dtype=float)
    initial = np.asarray([row.initial_cell_concentration_mol_m3 for row in rows], dtype=float)
    boundary = np.asarray([request.mouth_boundary_concentration_mol_m3_by_species[row.species_id] for row in rows], dtype=float)
    gamma_cells = np.asarray([row.activity_coefficient_by_time_and_cell for row in rows], dtype=float)  # species,time,cell
    gamma_mouth = np.asarray([row.mouth_activity_coefficient_by_time for row in rows], dtype=float)
    velocity_knots = np.asarray(request.cell_face_axial_velocity_m_s_by_knot, dtype=float)  # face,time
    reactions = tuple(getattr(request, "reactions", ()))
    n_reactions = len(reactions)
    species_index = {row.species_id: i for i, row in enumerate(rows)}
    stoich = np.zeros((ns, n_reactions), dtype=float)
    forward_knots = np.empty((n_reactions, nt), dtype=float)
    reverse_knots = np.empty((n_reactions, nt), dtype=float)
    reaction_ids = []
    for j, reaction in enumerate(reactions):
        reaction_ids.append(reaction.reaction_id)
        for term in reaction.reactants:
            stoich[species_index[term.species_id], j] -= term.coefficient
        for term in reaction.products:
            stoich[species_index[term.species_id], j] += term.coefficient
        forward_knots[j] = reaction.forward_rate_constant_mol_m3_s_by_knot
        reverse_knots[j] = reaction.reverse_rate_constant_mol_m3_s_by_knot
    n_state = ns * nc
    y0 = np.concatenate((initial.reshape(-1), np.zeros(ns), np.zeros(ns if n_reactions else 0)))
    evaluations = 0
    max_current_residual = 0.0

    def interpolate_fields(t: float):
        interval = min(max(int(np.searchsorted(times, t, side="right") - 1), 0), nt - 2)
        f = min(max((t - times[interval]) / (times[interval + 1] - times[interval]), 0.0), 1.0)
        mouth_c = boundary[:, interval] + f * (boundary[:, interval + 1] - boundary[:, interval])
        logg0 = np.log(gamma_cells[:, interval])
        logg1 = np.log(gamma_cells[:, interval + 1])
        cell_logg = logg0 + f * (logg1 - logg0)
        mouth_logg = np.log(gamma_mouth[:, interval]) + f * (
            np.log(gamma_mouth[:, interval + 1]) - np.log(gamma_mouth[:, interval])
        )
        velocity = velocity_knots[:, interval] + f * (velocity_knots[:, interval + 1] - velocity_knots[:, interval])
        if n_reactions:
            forward = np.exp(np.log(forward_knots[:, interval]) + f * (
                np.log(forward_knots[:, interval + 1]) - np.log(forward_knots[:, interval])
            ))
            reverse = np.exp(np.log(reverse_knots[:, interval]) + f * (
                np.log(reverse_knots[:, interval + 1]) - np.log(reverse_knots[:, interval])
            ))
        else:
            forward = reverse = np.empty((0,), dtype=float)
        return mouth_c, cell_logg, mouth_logg, velocity, forward, reverse

    def rhs(t: float, state: np.ndarray) -> np.ndarray:
        nonlocal evaluations, max_current_residual
        evaluations += 1
        if evaluations > request.maximum_function_evaluations:
            raise RuntimeError("maximum_function_evaluations_exceeded")
        c = state[:n_state].reshape(ns, nc)
        mobility = np.maximum(c, 0.0)
        mouth_c, logg, mouth_logg, velocity, forward, reverse = interpolate_fields(t)
        grad_c = np.zeros((ns, nc + 1), dtype=float)
        face_c = np.zeros_like(grad_c)
        grad_lng = np.zeros_like(grad_c)
        grad_c[:, 0] = (c[:, 0] - mouth_c) / (0.5 * dx)
        face_c[:, 0] = 0.5 * (mobility[:, 0] + mouth_c)
        grad_lng[:, 0] = (logg[:, 0] - mouth_logg) / (0.5 * dx)
        grad_c[:, 1:nc] = (c[:, 1:] - c[:, :-1]) / dx
        face_c[:, 1:nc] = 0.5 * (mobility[:, 1:] + mobility[:, :-1])
        grad_lng[:, 1:nc] = (logg[:, 1:] - logg[:, :-1]) / dx
        cup = np.where(velocity[None, :] >= 0.0,
                       np.concatenate((np.broadcast_to(mouth_c[:, None], (ns, 1)), mobility), axis=1)[:, :nc + 1],
                       np.concatenate((mobility, np.zeros((ns, 1))), axis=1)[:, :nc + 1])
        # Blind-tip flux is set to zero after the interior zero-current closure.
        denominator = np.sum((z[:, None] ** 2) * diffusivity[:, None] * face_c, axis=0)
        baseline = grad_c + face_c * grad_lng
        numerator = -np.sum(z[:, None] * diffusivity[:, None] * baseline, axis=0) + np.sum(z[:, None] * velocity[None, :] * cup, axis=0)
        if np.any((denominator <= 0.0) & (np.abs(numerator) > 0.0)):
            raise RuntimeError("zero_ionic_mobility_cannot_close_face_current")
        dpsi = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0.0)
        flux = -diffusivity[:, None] * (baseline + z[:, None] * face_c * dpsi) + velocity[None, :] * cup
        flux[:, -1] = 0.0
        current = np.sum(z[:, None] * flux, axis=0)
        max_current_residual = max(max_current_residual, float(np.max(np.abs(current))))
        dc = -(flux[:, 1:] - flux[:, :-1]) / dx
        if n_reactions:
            activities = np.exp(logg) * mobility / request.concentration_standard_state_mol_m3
            rates = np.empty((n_reactions, nc), dtype=float)
            for j, reaction in enumerate(reactions):
                forward_product = np.ones(nc, dtype=float)
                reverse_product = np.ones(nc, dtype=float)
                for term in reaction.reactants:
                    forward_product *= activities[species_index[term.species_id]] ** term.coefficient
                for term in reaction.products:
                    reverse_product *= activities[species_index[term.species_id]] ** term.coefficient
                rates[j] = forward[j] * forward_product - reverse[j] * reverse_product
            if not np.isfinite(rates).all():
                raise RuntimeError("nonfinite_activity_mass_action_rate")
            reaction_source = stoich @ rates
            dc += reaction_source
            reaction_inventory_rate = request.cross_section_area_m2 * dx * np.sum(reaction_source, axis=1)
            return np.concatenate((dc.reshape(-1), flux[:, 0], reaction_inventory_rate))
        return np.concatenate((dc.reshape(-1), flux[:, 0]))

    try:
        solution = solve_ivp(
            rhs, (float(times[0]), float(times[-1])), y0, method="BDF", t_eval=times,
            rtol=request.relative_tolerance, atol=request.absolute_tolerance_mol_m3,
            max_step=request.maximum_step_s,
        )
    except (RuntimeError, FloatingPointError, ValueError, OverflowError) as error:
        return Calculation(status="needs_data", values={
            "model_id": model_id, "reason": str(error), "input_sha256": digest,
            "function_evaluations": evaluations,
        })
    if not solution.success or solution.y.shape[1] != nt:
        return Calculation(status="needs_data", values={
            "model_id": model_id, "reason": "stiff_integrator_failed", "solver_message": solution.message,
            "input_sha256": digest, "function_evaluations": evaluations,
        })
    concentration = solution.y[:n_state].reshape(ns, nc, nt)
    if not np.isfinite(concentration).all() or float(np.min(concentration)) < -1e-7 * max(float(np.max(initial)), 1.0):
        return Calculation(status="needs_data", values={
            "model_id": model_id, "reason": "nonphysical_negative_concentration_from_numerical_integration",
            "input_sha256": digest, "minimum_concentration_mol_m3": float(np.min(concentration)),
        })
    cumulative_mouth = solution.y[n_state:n_state + ns, :]
    cumulative_reaction = solution.y[n_state + ns:n_state + 2 * ns, :] if n_reactions else np.zeros((ns, nt))
    cell_volume = request.cross_section_area_m2 * dx
    inventory = cell_volume * np.sum(np.maximum(concentration, 0.0), axis=1)
    inflow = request.cross_section_area_m2 * cumulative_mouth
    balance = inventory - inventory[:, [0]] - inflow + inflow[:, [0]] - cumulative_reaction + cumulative_reaction[:, [0]]
    charge = np.einsum("s,sct->tc", z, concentration)
    full_volume = request.cross_section_area_m2 * request.length_m
    allowed_balance = request.absolute_tolerance_mol_m3 * full_volume + request.relative_tolerance * np.maximum(
        np.max(inventory, axis=1), 1e-30
    )
    if np.any(np.max(np.abs(balance), axis=1) > allowed_balance):
        return Calculation(status="needs_data", values={
            "model_id": model_id, "reason": "finite_volume_inventory_balance_tolerance_exceeded",
            "input_sha256": digest,
            "finite_volume_inventory_balance_residual_mol_by_species": {
                rows[i].species_id: [float(v) for v in balance[i]] for i in range(ns)
            },
            "allowed_inventory_balance_residual_mol_by_species": {
                rows[i].species_id: float(allowed_balance[i]) for i in range(ns)
            },
            "function_evaluations": evaluations,
        })
    charge_scale = max(float(np.max(np.abs(np.einsum("s,sct->tc", np.abs(z), concentration)))), 1e-30)
    if float(np.max(np.abs(charge))) > 1e-7 * charge_scale:
        return Calculation(status="needs_data", values={
            "model_id": model_id, "reason": "local_electroneutrality_residual_tolerance_exceeded",
            "input_sha256": digest,
            "peak_absolute_local_charge_residual_mol_eq_m3": float(np.max(np.abs(charge))),
            "function_evaluations": evaluations,
        })
    history = []
    for k in range(nt):
        state = {
            "time_s": float(times[k]),
            "species_concentration_mol_m3_by_id": {rows[i].species_id: [float(v) for v in concentration[i, :, k]] for i in range(ns)},
            "species_inventory_mol_by_id": {rows[i].species_id: float(inventory[i, k]) for i in range(ns)},
            "local_charge_residual_mol_eq_m3_by_cell": [float(v) for v in charge[k]],
        }
        if n_reactions:
            activities = gamma_cells[:, k, :] * np.maximum(concentration[:, :, k], 0.0) / request.concentration_standard_state_mol_m3
            rates_by_reaction = {}
            source_by_species = {row.species_id: np.zeros(nc, dtype=float) for row in rows}
            for j, reaction in enumerate(reactions):
                forward_product = np.ones(nc, dtype=float)
                reverse_product = np.ones(nc, dtype=float)
                for term in reaction.reactants:
                    forward_product *= activities[species_index[term.species_id]] ** term.coefficient
                for term in reaction.products:
                    reverse_product *= activities[species_index[term.species_id]] ** term.coefficient
                forward_rate = forward_knots[j, k] * forward_product
                reverse_rate = reverse_knots[j, k] * reverse_product
                net_rate = forward_rate - reverse_rate
                rates_by_reaction[reaction.reaction_id] = {
                    "forward_extent_rate_mol_m3_s_by_cell": [float(v) for v in forward_rate],
                    "reverse_extent_rate_mol_m3_s_by_cell": [float(v) for v in reverse_rate],
                    "net_extent_rate_mol_m3_s_by_cell": [float(v) for v in net_rate],
                }
                for i, row in enumerate(rows):
                    source_by_species[row.species_id] += stoich[i, j] * net_rate
            if not all(np.isfinite(values).all() for values in source_by_species.values()):
                return Calculation(status="needs_data", values={
                    "model_id": model_id, "reason": "nonfinite_reported_reaction_rate",
                    "input_sha256": digest, "failed_knot_index": k,
                })
            state["reaction_extent_rate_mol_m3_s_by_id_and_cell"] = rates_by_reaction
            state["net_reaction_source_mol_m3_s_by_species_and_cell"] = {
                species_id: [float(v) for v in values] for species_id, values in source_by_species.items()
            }
        history.append(state)
    return Calculation(status="computed", values={
        "model_id": model_id,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "input_sha256": digest,
        "cell_width_m": dx,
        "finite_volume_inventory_balance_residual_mol_by_species": {
            rows[i].species_id: [float(v) for v in balance[i]] for i in range(ns)
        },
        "peak_absolute_local_charge_residual_mol_eq_m3": float(np.max(np.abs(charge))),
        "peak_zero_current_residual_mol_eq_m2_s": max_current_residual,
        "minimum_accepted_concentration_mol_m3": float(np.min(concentration)),
        "function_evaluations": evaluations,
        "state_history": history,
        "interpretation": "caller_activity_field_fixed_geometry_1d_transport_with_mass_action" if n_reactions else "caller_activity_field_fixed_geometry_reaction_free_1d_transport",
        "limitations": [
            "Activity coefficients are caller cell/time fields; they are not computed, calibrated or checked against an electrolyte model.",
            "Gamma is interpolated linearly in log space between supplied time knots and in space by endpoint differences; no extrapolation beyond the time knots is intended.",
            "The calculation assumes a fixed single-liquid slit, local electroneutrality, zero ionic current, caller diffusivities and a prescribed mouth boundary; the blind tip is no-flux.",
            "No automatic acid-base/complex speciation, phase equilibrium, precipitation, wall reaction, metal loss, corrosion rate, life or acceptance is inferred.",
            "Inventory/current residuals are discrete numerical diagnostics, not physical validation or qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceActivityCorrectedTransportRequest,
        evaluator=solve_crevice_activity_corrected_transport,
        units={
            "cell_width_m": "m",
            "state_history[].time_s": "s",
            "state_history[].species_concentration_mol_m3_by_id.*[]": "mol/m^3",
            "state_history[].species_inventory_mol_by_id.*": "mol",
            "state_history[].local_charge_residual_mol_eq_m3_by_cell[]": "mol_eq/m^3",
            "finite_volume_inventory_balance_residual_mol_by_species.*[]": "mol",
            "peak_absolute_local_charge_residual_mol_eq_m3": "mol_eq/m^3",
            "peak_zero_current_residual_mol_eq_m2_s": "mol_eq/(m^2*s)",
        },
        assumptions=(
            "Fixed-geometry finite-volume transport on caller time knots; diffusivity is constant over the supplied run.",
            "Caller-supplied species-specific gamma fields are interpolated in log space over time; concentration and mouth fields use linear time interpolation.",
            "At every open face, the dimensionless potential gradient enforces zero total ionic current including upwind advection; the blind tip is impermeable.",
            "This API does not solve aqueous speciation, reactions, phase changes, wall kinetics or material damage.",
        ),
        source_ids=(SPECIES_SOURCE_ID, FIELD_SOURCE_ID, BOUNDARY_SOURCE_ID, METHOD_SOURCE_ID, "scipy_integrate_bdf"),
    ), ModelSpec(
        model_id=REACTIVE_MODEL_ID,
        input_type=CreviceActivityReactiveTransportRequest,
        evaluator=solve_crevice_activity_corrected_reactive_transport,
        units={
            "state_history[].time_s": "s",
            "state_history[].species_concentration_mol_m3_by_id.*[]": "mol/m^3",
            "state_history[].species_inventory_mol_by_id.*": "mol",
            "state_history[].reaction_extent_rate_mol_m3_s_by_id_and_cell.*.net_extent_rate_mol_m3_s_by_cell[]": "mol/(m^3*s)",
            "state_history[].net_reaction_source_mol_m3_s_by_species_and_cell.*[]": "mol/(m^3*s)",
            "finite_volume_inventory_balance_residual_mol_by_species.*[]": "mol",
            "peak_zero_current_residual_mol_eq_m2_s": "mol_eq/(m^2*s)",
        },
        assumptions=(
            "Caller activity-coefficient cell/time fields drive both the activity-gradient flux term and reversible local mass-action rates.",
            "Reaction rates use caller parameter schedules on dimensionless activities; positive rate constants are interpolated in log space and co-integrated with finite-volume transport in one BDF system.",
            "Every reaction is charge- and element-balanced; equilibrium-constant and forward/reverse rate schedules are caller supplied and detailed-balance checked.",
            "No automatic speciation, phase transition, wall reaction, metal loss or corrosion rate is inferred.",
        ),
        source_ids=(SPECIES_SOURCE_ID, FIELD_SOURCE_ID, BOUNDARY_SOURCE_ID, REACTION_SOURCE_ID,
                    "caller_crevice_activity_rate_reaction_records", REACTIVE_METHOD_SOURCE_ID, "scipy_integrate_bdf"),
    )]


def solve_crevice_activity_corrected_reactive_transport(
    request: CreviceActivityReactiveTransportRequest,
) -> Calculation:
    """Co-integrate activity-corrected ionic transport and caller reversible kinetics."""
    return solve_crevice_activity_corrected_transport(request, model_id=REACTIVE_MODEL_ID)
