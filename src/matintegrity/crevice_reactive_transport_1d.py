"""Fixed-geometry one-dimensional reaction–diffusion for a caller-defined neutral network."""

from __future__ import annotations

import math
import numpy as np
from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_neutral_reactive_transport_1d"
NETWORK_SOURCE_ID = "caller_crevice_neutral_reaction_diffusion_network"
BOUNDARY_SOURCE_ID = "caller_crevice_reactive_transport_mouth_history"
MODEL_SOURCE_ID = "finite_volume_diffusion_with_local_reversible_mass_action"


class ReactiveTransportSpecies(Contract):
    species_id: str = Field(min_length=1)
    diffusivity_m2_s: Positive
    initial_cell_concentration_mol_m3: tuple[Positive, ...] = Field(min_length=2, max_length=300)
    elemental_composition: dict[str, StrictInt] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def validate_elements(self):
        if any(not symbol.strip() or count < 0 for symbol, count in self.elemental_composition.items()):
            raise ValueError("elemental composition requires nonempty symbols and nonnegative integer counts")
        return self


class ReactiveTransportTerm(Contract):
    species_id: str = Field(min_length=1)
    stoichiometric_coefficient: int = Field(ge=1, le=8)


class ReactiveTransportReaction(Contract):
    reaction_id: str = Field(min_length=1)
    reactants: tuple[ReactiveTransportTerm, ...] = Field(min_length=1, max_length=16)
    products: tuple[ReactiveTransportTerm, ...] = Field(min_length=1, max_length=16)
    forward_rate_constant_by_interval: tuple[float, ...] = Field(min_length=1, max_length=1000)
    forward_rate_constant_units: str = Field(min_length=1)
    reverse_rate_constant_by_interval: tuple[float, ...] = Field(min_length=1, max_length=1000)
    reverse_rate_constant_units: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_rates(self):
        if (any(not math.isfinite(k) or k < 0 for k in self.forward_rate_constant_by_interval)
                or any(not math.isfinite(k) or k < 0 for k in self.reverse_rate_constant_by_interval)):
            raise ValueError("rate constants must be finite and nonnegative")
        return self


class CreviceNeutralReactiveTransportRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    model_provider_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    length_m: Positive
    cross_section_area_m2: Positive
    cell_count: int = Field(ge=2, le=300)
    output_time_s: tuple[float, ...] = Field(min_length=2, max_length=1000)
    species: tuple[ReactiveTransportSpecies, ...] = Field(min_length=1, max_length=30)
    reactions: tuple[ReactiveTransportReaction, ...] = Field(min_length=1, max_length=100)
    mouth_boundary_concentration_mol_m3_by_species: dict[str, tuple[Positive, ...]] = Field(min_length=1, max_length=30)
    relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    absolute_tolerance_mol_m3: Positive = Field(default=1e-10)
    maximum_step_s: Positive
    maximum_function_evaluations: int = Field(default=200000, ge=100, le=10000000)
    provider_evidence: tuple[Evidence, ...] = Field(min_length=1)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    geometry_and_spatial_mapping_reviewed: bool
    homogeneous_neutral_mass_action_network_reviewed: bool
    kinetic_parameter_support_and_units_reviewed: bool
    no_advection_and_fixed_geometry_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_reaction_diffusion_problem(self):
        if not all((self.geometry_and_spatial_mapping_reviewed,
                    self.homogeneous_neutral_mass_action_network_reviewed,
                    self.kinetic_parameter_support_and_units_reviewed,
                    self.no_advection_and_fixed_geometry_reviewed,
                    self.usage_rights_reviewed, self.computational_use_authorized)):
            raise ValueError("explicit geometry, chemistry, parameter, transport and rights reviews are required")
        if any(not math.isfinite(t) for t in self.output_time_s) or any(
            b <= a for a, b in zip(self.output_time_s, self.output_time_s[1:])
        ):
            raise ValueError("output times must be finite and strictly increasing")
        species_by_id = {row.species_id: row for row in self.species}
        if len(species_by_id) != len(self.species):
            raise ValueError("species identifiers must be unique")
        if any(len(row.initial_cell_concentration_mol_m3) != self.cell_count for row in self.species):
            raise ValueError("initial state must contain exactly one positive concentration per spatial cell")
        if set(self.mouth_boundary_concentration_mol_m3_by_species) != set(species_by_id):
            raise ValueError("mouth boundary history must cover every declared species exactly once")
        if any(len(values) != len(self.output_time_s)
               for values in self.mouth_boundary_concentration_mol_m3_by_species.values()):
            raise ValueError("each mouth concentration history must align with the output clock")
        if len({row.reaction_id for row in self.reactions}) != len(self.reactions):
            raise ValueError("reaction identifiers must be unique")
        for reaction in self.reactions:
            if (len(reaction.forward_rate_constant_by_interval) != len(self.output_time_s)
                    or len(reaction.reverse_rate_constant_by_interval) != len(self.output_time_s)):
                raise ValueError("each rate-constant schedule must have a value at every output knot")
            terms = (*reaction.reactants, *reaction.products)
            if any(term.species_id not in species_by_id for term in terms):
                raise ValueError("reaction terms must refer to declared species")
            if len({term.species_id for term in reaction.reactants}) != len(reaction.reactants):
                raise ValueError("reactant species may occur once in each reaction side")
            if len({term.species_id for term in reaction.products}) != len(reaction.products):
                raise ValueError("product species may occur once in each reaction side")
            net: dict[str, int] = {}
            for term in reaction.reactants:
                net[term.species_id] = net.get(term.species_id, 0) - term.stoichiometric_coefficient
            for term in reaction.products:
                net[term.species_id] = net.get(term.species_id, 0) + term.stoichiometric_coefficient
            if not any(net.values()):
                raise ValueError("reaction must have a nonzero net stoichiometric vector")
            elements = set().union(*(set(row.elemental_composition) for row in self.species))
            for element in elements:
                residual = sum(net.get(key, 0) * row.elemental_composition.get(element, 0)
                               for key, row in species_by_id.items())
                if residual:
                    raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve element {element!r}")
        if not any(row.source_id == self.model_provider_id and row.sha256 for row in self.provider_evidence):
            raise ValueError("provider evidence must bind the declared model provider to a digest")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights evidence must identify a license or permitted-use basis")
        return self


def _reaction_network_arrays(request: CreviceNeutralReactiveTransportRequest):
    species_ids = [row.species_id for row in request.species]
    species_index = {name: i for i, name in enumerate(species_ids)}
    stoichiometry = np.zeros((len(species_ids), len(request.reactions)), dtype=float)
    reactant_order = np.zeros_like(stoichiometry)
    product_order = np.zeros_like(stoichiometry)
    for r, reaction in enumerate(request.reactions):
        for term in reaction.reactants:
            i = species_index[term.species_id]
            stoichiometry[i, r] -= term.stoichiometric_coefficient
            reactant_order[i, r] = term.stoichiometric_coefficient
        for term in reaction.products:
            i = species_index[term.species_id]
            stoichiometry[i, r] += term.stoichiometric_coefficient
            product_order[i, r] = term.stoichiometric_coefficient
    return stoichiometry, reactant_order, product_order


def solve_crevice_neutral_reactive_transport(
    request: CreviceNeutralReactiveTransportRequest,
) -> Calculation:
    """Integrate local reversible mass action and finite-volume diffusion together."""
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values={"model_id": MODEL_ID, "reason": "scipy_runtime_unavailable"})
    digest = canonical_digest(request.model_dump(mode="json"))
    n_species, n_cells, n_reactions = len(request.species), request.cell_count, len(request.reactions)
    n_mobile = n_species * n_cells
    dx = request.length_m / n_cells
    diffusivity = np.asarray([row.diffusivity_m2_s for row in request.species], dtype=float)
    initial = np.asarray([row.initial_cell_concentration_mol_m3 for row in request.species], dtype=float)
    boundary = np.asarray([request.mouth_boundary_concentration_mol_m3_by_species[row.species_id]
                           for row in request.species], dtype=float)
    forward_k = np.asarray([row.forward_rate_constant_by_interval for row in request.reactions], dtype=float)
    reverse_k = np.asarray([row.reverse_rate_constant_by_interval for row in request.reactions], dtype=float)
    stoich, forward_order, reverse_order = _reaction_network_arrays(request)
    state0 = np.concatenate((initial.reshape(-1), np.zeros(n_species), np.zeros(n_species)))
    time = np.asarray(request.output_time_s, dtype=float)
    evaluations = 0
    minimum_trial = float(np.min(initial))

    def derivative(t: float, state: np.ndarray) -> np.ndarray:
        nonlocal evaluations, minimum_trial
        evaluations += 1
        if evaluations > request.maximum_function_evaluations:
            raise RuntimeError("maximum_function_evaluations_exceeded")
        c = state[:n_mobile].reshape(n_species, n_cells)
        minimum_trial = min(minimum_trial, float(np.min(c)))
        # Numerical stages can probe infinitesimally below zero; use zero as the kinetic/reactive carrier floor.
        physical = np.maximum(c, 0.0)
        interval = min(max(int(np.searchsorted(time, t, side="right") - 1), 0), len(time) - 2)
        fraction = min(max((t - time[interval]) / (time[interval + 1] - time[interval]), 0.0), 1.0)
        mouth = boundary[:, interval] + fraction * (boundary[:, interval + 1] - boundary[:, interval])
        gradients = np.zeros((n_species, n_cells + 1), dtype=float)
        gradients[:, 0] = (c[:, 0] - mouth) / (0.5 * dx)
        gradients[:, 1:n_cells] = (c[:, 1:] - c[:, :-1]) / dx
        flux = -diffusivity[:, None] * gradients
        flux[:, -1] = 0.0
        diffusion_rate = -(flux[:, 1:] - flux[:, :-1]) / dx
        fk = forward_k[:, interval] + fraction * (forward_k[:, interval + 1] - forward_k[:, interval])
        rk = reverse_k[:, interval] + fraction * (reverse_k[:, interval + 1] - reverse_k[:, interval])
        forward_rate = fk[:, None] * np.prod(
            np.power(physical[:, None, :], forward_order[:, :, None]), axis=0
        )
        reverse_rate = rk[:, None] * np.prod(
            np.power(physical[:, None, :], reverse_order[:, :, None]), axis=0
        )
        net_rate = forward_rate - reverse_rate
        reaction_rate = stoich @ net_rate
        d_mobile = diffusion_rate + reaction_rate
        boundary_transfer = flux[:, 0]
        volume = request.cross_section_area_m2 * dx
        reaction_transfer = volume * np.sum(reaction_rate, axis=1)
        return np.concatenate((d_mobile.reshape(-1), boundary_transfer, reaction_transfer))

    try:
        solution = solve_ivp(
            derivative, (float(time[0]), float(time[-1])), state0, method="BDF", t_eval=time,
            rtol=request.relative_tolerance, atol=request.absolute_tolerance_mol_m3,
            max_step=request.maximum_step_s,
        )
    except (RuntimeError, FloatingPointError, ValueError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": str(error), "input_sha256": digest,
            "function_evaluations": evaluations,
        })
    if not solution.success or solution.y.shape[1] != len(time):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": "stiff_integrator_failed", "solver_message": solution.message,
            "input_sha256": digest, "function_evaluations": evaluations,
        })
    concentration = solution.y[:n_mobile].reshape(n_species, n_cells, len(time))
    if not np.isfinite(concentration).all() or float(np.min(concentration)) < -1e-7 * max(float(np.max(initial)), 1.0):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": "nonphysical_negative_concentration_from_numerical_integration",
            "input_sha256": digest, "minimum_trial_concentration_mol_m3": minimum_trial,
        })
    cumulative_boundary = solution.y[n_mobile:n_mobile + n_species]
    cumulative_reaction = solution.y[n_mobile + n_species:]
    cell_volume = request.cross_section_area_m2 * dx
    inventory = cell_volume * np.sum(np.maximum(concentration, 0.0), axis=1)
    boundary_transfer_mol = request.cross_section_area_m2 * cumulative_boundary
    residual = (inventory - inventory[:, [0]] - boundary_transfer_mol + boundary_transfer_mol[:, [0]]
                - cumulative_reaction + cumulative_reaction[:, [0]])
    history = []
    for j, t in enumerate(time):
        history.append({
            "time_s": float(t),
            "concentration_mol_m3_by_species": {
                request.species[k].species_id: [float(v) for v in concentration[k, :, j]]
                for k in range(n_species)
            },
            "inventory_mol_by_species": {
                request.species[k].species_id: float(inventory[k, j]) for k in range(n_species)
            },
            "integrated_boundary_transfer_mol_by_species": {
                request.species[k].species_id: float(boundary_transfer_mol[k, j]) for k in range(n_species)
            },
            "integrated_reaction_transfer_mol_by_species": {
                request.species[k].species_id: float(cumulative_reaction[k, j]) for k in range(n_species)
            },
        })
    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "model_provider_id": request.model_provider_id,
        "model_revision": request.model_revision,
        "input_sha256": digest,
        "cell_width_m": dx,
        "maximum_absolute_finite_volume_balance_residual_mol": float(np.max(np.abs(residual))),
        "finite_volume_balance_residual_mol_by_species": {
            request.species[k].species_id: [float(v) for v in residual[k]] for k in range(n_species)
        },
        "function_evaluations": evaluations,
        "state_history": history,
        "interpretation": "caller_parameterized_neutral_reaction_diffusion_history",
        "limitations": [
            "The model combines fixed-geometry one-dimensional Fick diffusion with local reversible mass-action kinetics for an explicitly declared neutral species network.",
            "Rate constants, rate units, reaction mechanism, temperature support and boundary history are caller supplied and evidence bound.",
            "No electromigration, advection, activity correction, speciation, phase transition, precipitation, moving geometry or wall reaction is inferred.",
            "Numerical balance closure is a computational diagnostic, not independent physical validation or qualification.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceNeutralReactiveTransportRequest,
        evaluator=solve_crevice_neutral_reactive_transport,
        units={
            "cell_width_m": "m",
            "maximum_absolute_finite_volume_balance_residual_mol": "mol",
            "finite_volume_balance_residual_mol_by_species.*[]": "mol",
            "state_history[].time_s": "s",
            "state_history[].concentration_mol_m3_by_species.*[]": "mol/m^3",
            "state_history[].inventory_mol_by_species.*": "mol",
            "state_history[].integrated_boundary_transfer_mol_by_species.*": "mol",
            "state_history[].integrated_reaction_transfer_mol_by_species.*": "mol",
        },
        assumptions=(
            "Caller-defined neutral chemical species undergo reversible local mass-action reactions while diffusing through a fixed one-dimensional finite-volume geometry.",
            "The caller supplies rate constant values at each output knot; both boundary concentrations and rate constants are linearly interpolated between knots.",
            "The mouth is Dirichlet and the blind tip is no-flux; advection, electromigration and wall reaction are excluded.",
        ),
        source_ids=(NETWORK_SOURCE_ID, BOUNDARY_SOURCE_ID, MODEL_SOURCE_ID,
                    "scipy_integrate_solve_ivp", "scipy_integrate_bdf"),
    )]
