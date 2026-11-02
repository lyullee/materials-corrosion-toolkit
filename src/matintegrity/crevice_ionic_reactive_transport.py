"""Caller-driven electrodiffusion, advection and balanced reaction kinetics in a fixed crevice slit."""

from __future__ import annotations

import math

import numpy as np
from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.crevice_ionic_reactive_transport_1d"
SPECIES_SOURCE_ID = "caller_crevice_ionic_reactive_transport_species"
NETWORK_SOURCE_ID = "caller_crevice_ionic_reaction_network"
BOUNDARY_SOURCE_ID = "caller_crevice_ionic_transport_boundary_history"
VELOCITY_SOURCE_ID = "caller_crevice_axial_velocity_face_history"
METHOD_SOURCE_ID = "finite_volume_advection_nernst_planck_and_mass_action"
MAX_SPECIES = 32
MAX_CELLS = 300
MAX_KNOTS = 1000
MAX_REACTIONS = 100


class CreviceIonicReactiveSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    diffusivity_m2_s: Positive
    initial_cell_concentration_mol_m3: tuple[Positive, ...] = Field(min_length=2, max_length=MAX_CELLS)
    elemental_composition: dict[str, StrictInt] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def valid_formula(self):
        if any(not name.strip() or count < 0 for name, count in self.elemental_composition.items()):
            raise ValueError("species elemental formula requires nonempty symbols and nonnegative integer counts")
        return self


class CreviceIonicReactionTerm(Contract):
    species_id: str = Field(min_length=1)
    stoichiometric_coefficient: int = Field(ge=1, le=8)


class CreviceIonicReaction(Contract):
    reaction_id: str = Field(min_length=1)
    reactants: tuple[CreviceIonicReactionTerm, ...] = Field(min_length=1, max_length=16)
    products: tuple[CreviceIonicReactionTerm, ...] = Field(min_length=1, max_length=16)
    forward_rate_constant_by_knot: tuple[float, ...] = Field(min_length=2, max_length=MAX_KNOTS)
    reverse_rate_constant_by_knot: tuple[float, ...] = Field(min_length=2, max_length=MAX_KNOTS)
    forward_rate_constant_units: str = Field(min_length=1)
    reverse_rate_constant_units: str = Field(min_length=1)
    parameter_record_id: str = Field(min_length=1)
    parameter_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def validate_rates(self):
        if any(not math.isfinite(value) or value < 0 for value in (
            *self.forward_rate_constant_by_knot, *self.reverse_rate_constant_by_knot
        )):
            raise ValueError("reaction-rate constants must be finite and nonnegative")
        return self


class CreviceIonicReactiveTransportRequest(Contract):
    """Fixed slit geometry with caller face velocity, ionic boundaries and kinetic network."""

    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    transport_provider_id: str = Field(min_length=1)
    transport_provider_revision: str = Field(min_length=1)
    length_m: Positive
    cross_section_area_m2: Positive
    cell_count: int = Field(ge=2, le=MAX_CELLS)
    output_time_s: tuple[float, ...] = Field(min_length=2, max_length=MAX_KNOTS)
    cell_face_axial_velocity_m_s_by_knot: tuple[tuple[float, ...], ...] = Field(min_length=3, max_length=MAX_CELLS + 1)
    species: tuple[CreviceIonicReactiveSpecies, ...] = Field(min_length=2, max_length=MAX_SPECIES)
    mouth_boundary_concentration_mol_m3_by_species: dict[str, tuple[Positive, ...]] = Field(
        min_length=2, max_length=MAX_SPECIES
    )
    reactions: tuple[CreviceIonicReaction, ...] = Field(min_length=1, max_length=MAX_REACTIONS)
    relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    absolute_tolerance_mol_m3: Positive = Field(default=1e-10)
    maximum_step_s: Positive
    maximum_function_evaluations: int = Field(default=300000, ge=100, le=10_000_000)
    provider_evidence: tuple[Evidence, ...] = Field(min_length=2, max_length=128)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    fixed_geometry_and_cell_order_reviewed: bool
    face_velocity_sign_and_spatial_mapping_reviewed: bool
    dilute_nernst_planck_zero_current_reviewed: bool
    reaction_charge_and_element_balance_reviewed: bool
    rate_units_and_temperature_support_reviewed: bool
    mouth_boundary_and_blind_tip_condition_reviewed: bool
    phase_absence_and_no_wall_reaction_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_model_support(self):
        if not all((
            self.fixed_geometry_and_cell_order_reviewed,
            self.face_velocity_sign_and_spatial_mapping_reviewed,
            self.dilute_nernst_planck_zero_current_reviewed,
            self.reaction_charge_and_element_balance_reviewed,
            self.rate_units_and_temperature_support_reviewed,
            self.mouth_boundary_and_blind_tip_condition_reviewed,
            self.phase_absence_and_no_wall_reaction_reviewed,
            self.computational_use_authorized,
        )):
            raise ValueError("all geometry, flux, chemistry, applicability and authorization reviews are required")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights Evidence must identify a license or permitted-use basis")
        if any(not math.isfinite(t) for t in self.output_time_s) or any(
            right <= left for left, right in zip(self.output_time_s, self.output_time_s[1:])
        ):
            raise ValueError("output times must be finite and strictly increasing")
        n_time = len(self.output_time_s)
        if len(self.cell_face_axial_velocity_m_s_by_knot) != self.cell_count + 1:
            raise ValueError("face velocity history must have one record per spatial face")
        if any(len(row) != n_time or any(not math.isfinite(v) for v in row)
               for row in self.cell_face_axial_velocity_m_s_by_knot):
            raise ValueError("face velocity records must be finite and align exactly with the time knots")
        # A blind terminal face is impermeable; the mouth can admit or discharge caller flow.
        if any(value != 0.0 for value in self.cell_face_axial_velocity_m_s_by_knot[-1]):
            raise ValueError("the blind-tip face velocity must be exactly zero at every knot")
        ids = [row.species_id for row in self.species]
        if len(ids) != len(set(ids)) or not any(row.charge_number > 0 for row in self.species) or not any(
            row.charge_number < 0 for row in self.species
        ):
            raise ValueError("species IDs must be unique and include positive and negative ions")
        species_by_id = {row.species_id: row for row in self.species}
        if any(len(row.initial_cell_concentration_mol_m3) != self.cell_count for row in self.species):
            raise ValueError("initial concentration fields must align with the cell count")
        if set(self.mouth_boundary_concentration_mol_m3_by_species) != set(ids):
            raise ValueError("mouth boundary data must cover every declared species exactly")
        if any(len(row) != n_time for row in self.mouth_boundary_concentration_mol_m3_by_species.values()):
            raise ValueError("mouth concentration schedules must align with every output knot")
        z = {row.species_id: row.charge_number for row in self.species}
        for cell in range(self.cell_count):
            charge = math.fsum(row.charge_number * row.initial_cell_concentration_mol_m3[cell] for row in self.species)
            scale = math.fsum(abs(row.charge_number) * row.initial_cell_concentration_mol_m3[cell] for row in self.species)
            if scale == 0 or abs(charge) > 1e-9 * scale:
                raise ValueError("initial ionic composition must be locally electroneutral in every cell")
        for k in range(n_time):
            charge = math.fsum(z[key] * values[k] for key, values in self.mouth_boundary_concentration_mol_m3_by_species.items())
            scale = math.fsum(abs(z[key]) * values[k] for key, values in self.mouth_boundary_concentration_mol_m3_by_species.items())
            if scale == 0 or abs(charge) > 1e-9 * scale:
                raise ValueError("every caller mouth boundary knot must be locally electroneutral")
        if not self.reactions or len({row.reaction_id for row in self.reactions}) != len(self.reactions):
            raise ValueError("reaction IDs must be nonempty and unique")
        for reaction in self.reactions:
            if len(reaction.forward_rate_constant_by_knot) != n_time or len(reaction.reverse_rate_constant_by_knot) != n_time:
                raise ValueError("every reaction rate schedule must align with the output knots")
            terms = (*reaction.reactants, *reaction.products)
            if any(term.species_id not in species_by_id for term in terms):
                raise ValueError("reaction terms must refer to declared ionic species")
            if len({term.species_id for term in reaction.reactants}) != len(reaction.reactants) or len(
                {term.species_id for term in reaction.products}
            ) != len(reaction.products):
                raise ValueError("species terms may occur once on each reaction side")
            net: dict[str, int] = {}
            for term in reaction.reactants:
                net[term.species_id] = net.get(term.species_id, 0) - term.stoichiometric_coefficient
            for term in reaction.products:
                net[term.species_id] = net.get(term.species_id, 0) + term.stoichiometric_coefficient
            if not any(net.values()):
                raise ValueError("reaction must have a nonzero net stoichiometric vector")
            charge_residual = sum(net.get(row.species_id, 0) * row.charge_number for row in self.species)
            if charge_residual:
                raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve charge")
            elements = set().union(*(set(row.elemental_composition) for row in self.species))
            for element in elements:
                residual = sum(net.get(row.species_id, 0) * row.elemental_composition.get(element, 0)
                               for row in self.species)
                if residual:
                    raise ValueError(f"reaction {reaction.reaction_id!r} does not conserve element {element!r}")
            if not any(row.source_id == NETWORK_SOURCE_ID and row.sha256 == reaction.parameter_sha256
                       for row in self.provider_evidence):
                raise ValueError("each kinetic parameter digest must be linked to the reaction-network Evidence")
        if not any(row.source_id == self.transport_provider_id and row.sha256
                   for row in self.provider_evidence):
            raise ValueError("provider Evidence must bind the declared transport model provider")
        if not any(row.source_id == VELOCITY_SOURCE_ID and row.sha256
                   for row in self.provider_evidence):
            raise ValueError("provider Evidence must pin the caller face-velocity history")
        return self


def _reaction_arrays(request: CreviceIonicReactiveTransportRequest):
    species_ids = [row.species_id for row in request.species]
    index = {name: i for i, name in enumerate(species_ids)}
    stoich = np.zeros((len(species_ids), len(request.reactions)), dtype=float)
    forward_order = np.zeros_like(stoich)
    reverse_order = np.zeros_like(stoich)
    for j, reaction in enumerate(request.reactions):
        for term in reaction.reactants:
            i = index[term.species_id]
            stoich[i, j] -= term.stoichiometric_coefficient
            forward_order[i, j] = term.stoichiometric_coefficient
        for term in reaction.products:
            i = index[term.species_id]
            stoich[i, j] += term.stoichiometric_coefficient
            reverse_order[i, j] = term.stoichiometric_coefficient
    return stoich, forward_order, reverse_order


def solve_crevice_ionic_reactive_transport(request: CreviceIonicReactiveTransportRequest) -> Calculation:
    """Co-integrate dilute ionic advection/electrodiffusion with local balanced mass action."""
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values={"model_id": MODEL_ID, "reason": "scipy_runtime_unavailable"})
    digest = canonical_digest(request.model_dump(mode="json"))
    n_species, n_cells, n_reactions = len(request.species), request.cell_count, len(request.reactions)
    n_mobile = n_species * n_cells
    dx = request.length_m / n_cells
    volume = request.cross_section_area_m2 * dx
    area = request.cross_section_area_m2
    z = np.asarray([row.charge_number for row in request.species], dtype=float)
    diffusivity = np.asarray([row.diffusivity_m2_s for row in request.species], dtype=float)
    initial = np.asarray([row.initial_cell_concentration_mol_m3 for row in request.species], dtype=float)
    boundary = np.asarray([request.mouth_boundary_concentration_mol_m3_by_species[row.species_id]
                           for row in request.species], dtype=float)
    velocity = np.asarray(request.cell_face_axial_velocity_m_s_by_knot, dtype=float)
    forward_k = np.asarray([row.forward_rate_constant_by_knot for row in request.reactions], dtype=float)
    reverse_k = np.asarray([row.reverse_rate_constant_by_knot for row in request.reactions], dtype=float)
    stoich, forward_order, reverse_order = _reaction_arrays(request)
    state0 = np.concatenate((initial.reshape(-1), np.zeros(n_species), np.zeros(n_species)))
    times = np.asarray(request.output_time_s, dtype=float)
    evaluations = 0
    minimum_trial = float(np.min(initial))
    peak_zero_current = 0.0

    def derivative(t: float, state: np.ndarray) -> np.ndarray:
        nonlocal evaluations, minimum_trial, peak_zero_current
        evaluations += 1
        if evaluations > request.maximum_function_evaluations:
            raise RuntimeError("maximum_function_evaluations_exceeded")
        c = state[:n_mobile].reshape(n_species, n_cells)
        minimum_trial = min(minimum_trial, float(np.min(c)))
        mobility = np.maximum(c, 0.0)
        interval = min(max(int(np.searchsorted(times, t, side="right") - 1), 0), len(times) - 2)
        fraction = min(max((t - times[interval]) / (times[interval + 1] - times[interval]), 0.0), 1.0)
        mouth = boundary[:, interval] + fraction * (boundary[:, interval + 1] - boundary[:, interval])
        face_velocity = velocity[:, interval] + fraction * (velocity[:, interval + 1] - velocity[:, interval])
        gradients = np.zeros((n_species, n_cells + 1), dtype=float)
        face_concentration = np.zeros_like(gradients)
        upwind = np.zeros_like(gradients)
        gradients[:, 0] = (c[:, 0] - mouth) / (0.5 * dx)
        face_concentration[:, 0] = 0.5 * (mobility[:, 0] + mouth)
        upwind[:, 0] = mouth if face_velocity[0] >= 0.0 else mobility[:, 0]
        gradients[:, 1:n_cells] = (c[:, 1:] - c[:, :-1]) / dx
        face_concentration[:, 1:n_cells] = 0.5 * (mobility[:, 1:] + mobility[:, :-1])
        upwind[:, 1:n_cells] = np.where(face_velocity[None, 1:n_cells] >= 0.0,
                                          mobility[:, :-1], mobility[:, 1:])
        electric_gradient = np.zeros(n_cells + 1, dtype=float)
        denominator = np.sum((z[:, None] ** 2) * diffusivity[:, None] * face_concentration, axis=0)
        numerator = np.sum((z[:, None] * diffusivity[:, None]) * gradients, axis=0)
        advective_current = face_velocity * np.sum(z[:, None] * upwind, axis=0)
        electric_gradient = np.divide(-numerator + advective_current, denominator,
                                      out=np.zeros_like(numerator), where=denominator > 0.0)
        flux = (-diffusivity[:, None] * gradients
                - (z * diffusivity)[:, None] * face_concentration * electric_gradient[None, :]
                + upwind * face_velocity[None, :])
        # Blind tip has zero advection by contract and no diffusive/electric transfer.
        flux[:, -1] = 0.0
        ionic_current = np.sum(z[:, None] * flux, axis=0)
        peak_zero_current = max(peak_zero_current, float(np.max(np.abs(ionic_current))))
        transport_rate = -(flux[:, 1:] - flux[:, :-1]) / dx
        rate_fraction = fraction
        fk = forward_k[:, interval] + rate_fraction * (forward_k[:, interval + 1] - forward_k[:, interval])
        rk = reverse_k[:, interval] + rate_fraction * (reverse_k[:, interval + 1] - reverse_k[:, interval])
        forward_rate = fk[:, None] * np.prod(np.power(mobility[:, None, :], forward_order[:, :, None]), axis=0)
        reverse_rate = rk[:, None] * np.prod(np.power(mobility[:, None, :], reverse_order[:, :, None]), axis=0)
        reaction_rate = stoich @ (forward_rate - reverse_rate)
        species_rate = transport_rate + reaction_rate
        cumulative_boundary_rate = flux[:, 0]
        cumulative_reaction_rate = volume * np.sum(reaction_rate, axis=1)
        return np.concatenate((species_rate.reshape(-1), cumulative_boundary_rate, cumulative_reaction_rate))

    try:
        solution = solve_ivp(
            derivative, (float(times[0]), float(times[-1])), state0, method="BDF", t_eval=times,
            rtol=request.relative_tolerance, atol=request.absolute_tolerance_mol_m3,
            max_step=request.maximum_step_s,
        )
    except (RuntimeError, FloatingPointError, ValueError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": str(error), "input_sha256": digest,
            "function_evaluations": evaluations,
        })
    if not solution.success or solution.y.shape[1] != len(times):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": "stiff_integrator_failed", "solver_message": solution.message,
            "input_sha256": digest, "function_evaluations": evaluations,
        })
    concentration = solution.y[:n_mobile].reshape(n_species, n_cells, len(times))
    if (not np.isfinite(concentration).all()
            or float(np.min(concentration)) < -1e-7 * max(float(np.max(initial)), 1.0)):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": "nonphysical_negative_concentration_from_numerical_integration",
            "minimum_trial_concentration_mol_m3": minimum_trial, "input_sha256": digest,
        })
    integrated_boundary = area * solution.y[n_mobile:n_mobile + n_species]
    integrated_reaction = solution.y[n_mobile + n_species:]
    inventory = volume * np.sum(np.maximum(concentration, 0.0), axis=1)
    balance = inventory - inventory[:, [0]] - (integrated_boundary - integrated_boundary[:, [0]]) \
        - (integrated_reaction - integrated_reaction[:, [0]])
    charge = np.einsum("s,sct->tc", z, concentration)
    state_history = []
    for k, time in enumerate(times):
        state_history.append({
            "time_s": float(time),
            "species_concentration_mol_m3_by_id": {
                request.species[i].species_id: [float(v) for v in concentration[i, :, k]]
                for i in range(n_species)
            },
            "species_inventory_mol_by_id": {
                request.species[i].species_id: float(inventory[i, k]) for i in range(n_species)
            },
            "integrated_mouth_transfer_mol_by_species": {
                request.species[i].species_id: float(integrated_boundary[i, k]) for i in range(n_species)
            },
            "integrated_reaction_transfer_mol_by_species": {
                request.species[i].species_id: float(integrated_reaction[i, k]) for i in range(n_species)
            },
            "local_charge_residual_mol_eq_m3_by_cell": [float(v) for v in charge[k]],
            "face_velocity_m_s": [float(v) for v in velocity[:, k]],
        })
    return Calculation(status="computed", values={
        "model_id": MODEL_ID,
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "physical_scope_id": request.physical_scope_id,
        "clock_id": request.clock_id,
        "transport_provider_id": request.transport_provider_id,
        "transport_provider_revision": request.transport_provider_revision,
        "input_sha256": digest,
        "cell_width_m": dx,
        "maximum_absolute_finite_volume_balance_residual_mol": float(np.max(np.abs(balance))),
        "finite_volume_balance_residual_mol_by_species": {
            request.species[i].species_id: [float(v) for v in balance[i]] for i in range(n_species)
        },
        "peak_absolute_local_charge_residual_mol_eq_m3": float(np.max(np.abs(charge))),
        "peak_zero_current_residual_mol_eq_m2_s": peak_zero_current,
        "minimum_trial_concentration_mol_m3": minimum_trial,
        "function_evaluations": evaluations,
        "state_history": state_history,
        "interpretation": "caller_velocity_driven_fixed_geometry_ionic_reactive_crevice_transport",
        "limitations": [
            "Dilute Nernst-Planck electromigration, caller face velocity and homogeneous reversible mass action are co-integrated; all species and reactions are explicit caller inputs.",
            "Face velocity and mouth concentrations are linearly interpolated between exact knots; flow momentum and velocity derivation are external caller responsibilities.",
            "The blind tip is no-flux; geometry, diffusivities and cell volumes are fixed, and rate laws have no automatic temperature or activity correction.",
            "No solid phases, precipitation, wall reaction, metal loss, pH inference, service corrosion rate, probability or qualification is computed.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceIonicReactiveTransportRequest,
        evaluator=solve_crevice_ionic_reactive_transport,
        units={
            "cell_width_m": "m",
            "maximum_absolute_finite_volume_balance_residual_mol": "mol",
            "finite_volume_balance_residual_mol_by_species.*[]": "mol",
            "peak_absolute_local_charge_residual_mol_eq_m3": "mol_eq/m^3",
            "peak_zero_current_residual_mol_eq_m2_s": "mol_eq/(m^2*s)",
            "state_history[].time_s": "s",
            "state_history[].species_concentration_mol_m3_by_id.*[]": "mol/m^3",
            "state_history[].species_inventory_mol_by_id.*": "mol",
            "state_history[].integrated_mouth_transfer_mol_by_species.*": "mol",
            "state_history[].integrated_reaction_transfer_mol_by_species.*": "mol",
        },
        assumptions=(
            "Fixed geometry dilute-ion finite-volume transport with caller-defined linearly varying axial face velocity, electroneutral states and zero ionic current.",
            "Caller-defined homogeneous reversible reaction kinetics are element- and charge-balanced and linearly interpolated between exact rate knots.",
            "Transport and chemistry use a common implicit BDF state solve; flow, activity models, phases, wall reactions and metal loss remain outside the evaluator.",
        ),
        source_ids=(SPECIES_SOURCE_ID, NETWORK_SOURCE_ID, BOUNDARY_SOURCE_ID, VELOCITY_SOURCE_ID,
                    METHOD_SOURCE_ID, "scipy_integrate_solve_ivp", "scipy_integrate_bdf"),
    )]
