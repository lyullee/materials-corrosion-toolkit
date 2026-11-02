"""Caller-parameterized aqueous kinetic network in a mixed crevice volume."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class CreviceKineticSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: int
    elemental_composition: dict[str, Positive] = Field(min_length=1)
    initial_concentration_mol_m3: Nonnegative


class CreviceKineticTerm(Contract):
    species_id: str = Field(min_length=1)
    stoichiometric_coefficient: int = Field(ge=1, le=8)


class CreviceKineticReaction(Contract):
    reaction_id: str = Field(min_length=1)
    reactants: tuple[CreviceKineticTerm, ...] = Field(min_length=1, max_length=16)
    products: tuple[CreviceKineticTerm, ...] = Field(min_length=1, max_length=16)
    forward_rate_constant_by_interval: tuple[Nonnegative, ...] = Field(min_length=1, max_length=10000)
    forward_rate_constant_units: str = Field(min_length=1)
    reverse_rate_constant_by_interval: tuple[Nonnegative, ...] = Field(min_length=1, max_length=10000)
    reverse_rate_constant_units: str = Field(min_length=1)


class CreviceKineticInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    temperature_K: Positive
    exchange_flow_m3_s: Nonnegative
    bulk_concentration_mol_m3_by_species: dict[str, Nonnegative] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s or not math.isfinite(self.end_time_s - self.start_time_s):
            raise ValueError("each interval must have a positive finite duration")
        return self


class CreviceAqueousKineticNetwork(Contract):
    """Finite homogeneous reaction network with caller-supplied interval rates."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    control_volume_m3: Positive
    species: tuple[CreviceKineticSpecies, ...] = Field(min_length=1, max_length=40)
    reactions: tuple[CreviceKineticReaction, ...] = Field(min_length=1, max_length=100)
    intervals: tuple[CreviceKineticInterval, ...] = Field(min_length=1, max_length=10000)
    solver_method: Literal["BDF", "Radau"] = "BDF"
    relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    absolute_tolerance_mol_m3: Positive = Field(default=1e-12)
    maximum_function_evaluations: int = Field(default=100000, ge=100, le=10000000)
    maximum_step_s: Positive
    temperature_support_min_K: Positive
    temperature_support_max_K: Positive
    model_provider_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    reaction_network_and_conservation_reviewed: bool
    kinetic_parameter_units_and_calibration_reviewed: bool
    mixed_volume_and_exchange_boundary_reviewed: bool
    temperature_knot_mapping_and_parameter_support_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_network(self):
        species_by_id = {row.species_id: row for row in self.species}
        if len(species_by_id) != len(self.species):
            raise ValueError("species IDs must be unique")
        if len({row.reaction_id for row in self.reactions}) != len(self.reactions):
            raise ValueError("reaction IDs must be unique")
        if len({row.interval_id for row in self.intervals}) != len(self.intervals):
            raise ValueError("interval IDs must be unique")
        if any(a.end_time_s != b.start_time_s for a, b in zip(self.intervals[:-1], self.intervals[1:])):
            raise ValueError("intervals must be exactly contiguous and ordered")
        if self.temperature_support_max_K < self.temperature_support_min_K:
            raise ValueError("temperature support maximum must not be below its minimum")
        species_ids = set(species_by_id)
        for interval in self.intervals:
            if not self.temperature_support_min_K <= interval.temperature_K <= self.temperature_support_max_K:
                raise ValueError("interval temperature lies outside the declared parameter support")
            if set(interval.bulk_concentration_mol_m3_by_species) != species_ids:
                raise ValueError("every interval must provide one bulk concentration for every declared species")
        for reaction in self.reactions:
            if len(reaction.forward_rate_constant_by_interval) != len(self.intervals) or len(reaction.reverse_rate_constant_by_interval) != len(self.intervals):
                raise ValueError("each reaction rate history must align with all kinetic intervals")
            reactant_ids = [row.species_id for row in reaction.reactants]
            product_ids = [row.species_id for row in reaction.products]
            if set(reactant_ids + product_ids) - species_ids:
                raise ValueError("reaction terms must reference declared species")
            if len(reactant_ids) != len(set(reactant_ids)) or len(product_ids) != len(set(product_ids)):
                raise ValueError("a species may occur once on each side of a reaction")
            signed: dict[str, int] = {}
            for term in reaction.reactants:
                signed[term.species_id] = signed.get(term.species_id, 0) - term.stoichiometric_coefficient
            for term in reaction.products:
                signed[term.species_id] = signed.get(term.species_id, 0) + term.stoichiometric_coefficient
            if not any(signed.values()):
                raise ValueError("reaction must have a nonzero net stoichiometric vector")
            element_names = set().union(*(set(row.elemental_composition) for row in species_by_id.values()))
            for element in element_names:
                balance = sum(signed.get(key, 0) * species_by_id[key].elemental_composition.get(element, 0.0) for key in species_ids)
                if balance != 0:
                    raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve element {element!r}")
            charge_balance = sum(signed.get(key, 0) * species_by_id[key].charge_number for key in species_ids)
            if charge_balance != 0:
                raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve charge")
        if not any(row.source_id == self.model_provider_id and row.sha256 for row in self.evidence):
            raise ValueError("provider/input Evidence must include the provider ID and a content digest")
        if not self.usage_rights_evidence or not any(row.license_id for row in self.usage_rights_evidence):
            raise ValueError("usage-rights Evidence must identify a license or permitted-use basis")
        return self


def solve_crevice_aqueous_kinetic_network(request: CreviceAqueousKineticNetwork) -> Calculation:
    """Integrate supplied reversible mass-action kinetics and mixed-volume exchange."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "model_provider_id": request.model_provider_id,
        "model_revision": request.model_revision,
        "input_sha256": digest,
        "species_ids": [row.species_id for row in request.species],
        "reaction_ids": [row.reaction_id for row in request.reactions],
        "solver_method": request.solver_method,
        "probability_or_acceptance_claim": False,
    }
    reviews = {
        "reaction_network_and_conservation_reviewed": request.reaction_network_and_conservation_reviewed,
        "kinetic_parameter_units_and_calibration_reviewed": request.kinetic_parameter_units_and_calibration_reviewed,
        "mixed_volume_and_exchange_boundary_reviewed": request.mixed_volume_and_exchange_boundary_reviewed,
        "temperature_knot_mapping_and_parameter_support_reviewed": request.temperature_knot_mapping_and_parameter_support_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    try:
        import numpy as np
        from scipy.integrate import BDF, Radau
    except ImportError:
        return Calculation(status="needs_data", values=base | {"dependency": "scipy"}, notes=("Install the optional scientific dependencies to run the implicit stiff ODE solver.",))

    species = request.species
    species_index = {row.species_id: index for index, row in enumerate(species)}
    ns, nr = len(species), len(request.reactions)
    # Augmented state: concentration (mol/m3), net exchange inventory concentration,
    # and reaction extents per mixture volume (mol/m3).
    state = np.zeros(2 * ns + nr, dtype=float)
    state[:ns] = [row.initial_concentration_mol_m3 for row in species]
    stoich = np.zeros((ns, nr), dtype=float)
    reactants: list[list[tuple[int, int]]] = []
    products: list[list[tuple[int, int]]] = []
    for j, reaction in enumerate(request.reactions):
        reactants.append([(species_index[t.species_id], t.stoichiometric_coefficient) for t in reaction.reactants])
        products.append([(species_index[t.species_id], t.stoichiometric_coefficient) for t in reaction.products])
        for i, coefficient in reactants[-1]:
            stoich[i, j] -= coefficient
        for i, coefficient in products[-1]:
            stoich[i, j] += coefficient
    solver_cls = BDF if request.solver_method == "BDF" else Radau
    committed = []
    total_nfev = 0
    for interval_index, interval in enumerate(request.intervals):
        bulk = np.array([interval.bulk_concentration_mol_m3_by_species[row.species_id] for row in species], dtype=float)
        forward = [reaction.forward_rate_constant_by_interval[interval_index] for reaction in request.reactions]
        reverse = [reaction.reverse_rate_constant_by_interval[interval_index] for reaction in request.reactions]
        exchange_rate = interval.exchange_flow_m3_s / request.control_volume_m3

        def rhs(_time: float, values):
            concentration = values[:ns]
            net_rates = np.empty(nr, dtype=float)
            for reaction_index in range(nr):
                fwd_product = 1.0
                rev_product = 1.0
                for i, order in reactants[reaction_index]:
                    fwd_product *= concentration[i] ** order
                for i, order in products[reaction_index]:
                    rev_product *= concentration[i] ** order
                net_rates[reaction_index] = forward[reaction_index] * fwd_product - reverse[reaction_index] * rev_product
            exchange = exchange_rate * (bulk - concentration)
            derivative = np.zeros_like(values)
            derivative[:ns] = exchange + stoich @ net_rates
            derivative[ns:2 * ns] = exchange
            derivative[2 * ns:] = net_rates
            if not np.isfinite(derivative).all():
                raise FloatingPointError("nonfinite kinetic rate")
            return derivative

        try:
            state_before = state.copy()
            solver = solver_cls(
                rhs,
                interval.start_time_s,
                state.copy(),
                interval.end_time_s,
                rtol=request.relative_tolerance,
                atol=request.absolute_tolerance_mol_m3,
                max_step=request.maximum_step_s,
            )
            last_nfev = 0
            while solver.status == "running":
                solver.step()
                current = solver.nfev
                total_nfev += current - last_nfev
                last_nfev = current
                if current < 0 or total_nfev > request.maximum_function_evaluations:
                    return Calculation(status="out_of_scope", values=base | {"computed_prefix": committed, "failed_interval_id": interval.interval_id, "function_evaluations": total_nfev}, notes=("Solver work budget exceeded; the current interval was not committed.",))
                if solver.status == "failed":
                    break
            if solver.status != "finished":
                return Calculation(status="out_of_scope", values=base | {"computed_prefix": committed, "failed_interval_id": interval.interval_id, "function_evaluations": total_nfev}, notes=("The stiff solver did not finish the interval; its state was not committed.",))
            candidate = np.asarray(solver.y, dtype=float)
            if not np.isfinite(candidate).all() or np.any(candidate[:ns] < 0.0):
                return Calculation(status="out_of_scope", values=base | {"computed_prefix": committed, "failed_interval_id": interval.interval_id}, notes=("Nonfinite or negative concentration state; the interval was not committed or clipped.",))
            state = candidate
            committed.append({
                "interval_id": interval.interval_id,
                "start_time_s": interval.start_time_s,
                "end_time_s": interval.end_time_s,
                "temperature_K": interval.temperature_K,
                "concentration_mol_m3_by_species": {row.species_id: float(state[i]) for i, row in enumerate(species)},
                "net_exchange_mol_m3_by_species": {row.species_id: float(state[ns + i] - state_before[ns + i]) for i, row in enumerate(species)},
                "reaction_extent_mol_m3_by_reaction": {row.reaction_id: float(state[2 * ns + j] - state_before[2 * ns + j]) for j, row in enumerate(request.reactions)},
                "solver_function_evaluations": int(solver.nfev),
            })
        except (FloatingPointError, OverflowError, ValueError, RuntimeError, np.linalg.LinAlgError) as exc:
            return Calculation(status="out_of_scope", values=base | {"computed_prefix": committed, "failed_interval_id": interval.interval_id, "solver_exception": type(exc).__name__}, notes=("Numerical support was exceeded; the failed interval was not committed.",))
    final_concentration = state[:ns]
    reaction_accounting = stoich @ state[2 * ns:]
    closure = final_concentration - np.array([row.initial_concentration_mol_m3 for row in species]) - state[ns:2 * ns] - reaction_accounting
    values = base | {
        "status_scope": "caller_defined_homogeneous_kinetic_mixed_volume",
        "history": committed,
        "final_concentration_mol_m3_by_species": {row.species_id: float(final_concentration[i]) for i, row in enumerate(species)},
        "species_inventory_closure_residual_mol_m3": {row.species_id: float(closure[i]) for i, row in enumerate(species)},
        "function_evaluations": sum(row["solver_function_evaluations"] for row in committed),
        "full_requested_history_completed": True,
    }
    return Calculation(values=values, notes=(
        "Caller-supplied interval rate constants drive reversible mass-action kinetics; exchange is a well-mixed constant-volume boundary term.",
        "No activity/speciation equilibrium, precipitation, phase discovery, electrochemistry, wall loss or physical qualification is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.crevice_aqueous_kinetic_network",
        CreviceAqueousKineticNetwork,
        solve_crevice_aqueous_kinetic_network,
        {"history[].concentration_mol_m3_by_species": "mol/m3", "history[].reaction_extent_mol_m3_by_reaction": "mol/m3"},
        (
            "Finite caller-declared species and element/charge-balanced reversible reactions in a single constant-volume mixed liquid.",
            "Piecewise-constant temperature, bulk concentrations, exchange flow and separately supplied forward/reverse rate constants.",
            "Implicit BDF or Radau ODE solution with interval-prefix commitment, finite work budget and no silent negative-concentration clipping.",
            "No activity model, phase change, spatial gradients, electrochemical kinetics, wall loss or material qualification.",
        ),
        ("caller_crevice_aqueous_kinetic_network",),
        qualification="user_model",
    )]
