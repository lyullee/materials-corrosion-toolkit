"""Fixed-geometry, dilute-solution multi-ion diffusion with zero-current closure."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "transport.crevice_electroneutral_multispecies_diffusion_1d"
SPECIES_SOURCE_ID = "caller_crevice_nernst_planck_species_transport"
BOUNDARY_SOURCE_ID = "caller_crevice_electroneutral_boundary_history"
MODEL_SOURCE_ID = "finite_volume_zero_current_nernst_planck_transport"


class CreviceElectroneutralSpecies(Contract):
    species_id: str = Field(min_length=1)
    charge_number: StrictInt = Field(ge=-8, le=8)
    diffusivity_m2_s: Positive
    initial_cell_concentration_mol_m3: tuple[Positive, ...] = Field(min_length=2, max_length=500)
    elemental_composition: dict[str, StrictInt] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def valid_elements(self):
        if any(not element.strip() or count < 0 for element, count in self.elemental_composition.items()):
            raise ValueError("elemental composition requires nonempty symbols and nonnegative counts")
        return self


class CreviceElectroneutralDiffusionRequest(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    model_provider_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    length_m: Positive
    cross_section_area_m2: Positive
    cell_count: int = Field(ge=2, le=500)
    output_time_s: tuple[float, ...] = Field(min_length=2, max_length=1000)
    species: tuple[CreviceElectroneutralSpecies, ...] = Field(min_length=2, max_length=40)
    mouth_boundary_concentration_mol_m3_by_species: dict[str, tuple[Positive, ...]] = Field(min_length=2, max_length=40)
    relative_tolerance: Positive = Field(default=1e-8, le=1e-3)
    absolute_tolerance_mol_m3: Positive = Field(default=1e-10)
    maximum_step_s: Positive
    maximum_function_evaluations: int = Field(default=200000, ge=100, le=10000000)
    provider_evidence: tuple[Evidence, ...] = Field(min_length=1)
    rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    geometry_reviewed: bool
    dilute_solution_nernst_planck_applicability_reviewed: bool
    local_electroneutrality_and_zero_current_reviewed: bool
    reaction_free_interval_reviewed: bool
    provider_and_parameter_support_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_transport_basis(self):
        if not all((self.geometry_reviewed, self.dilute_solution_nernst_planck_applicability_reviewed,
                    self.local_electroneutrality_and_zero_current_reviewed, self.reaction_free_interval_reviewed,
                    self.provider_and_parameter_support_reviewed, self.usage_rights_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("all declared transport, applicability, evidence and rights reviews are required")
        if len(self.output_time_s) < 2 or any(not math.isfinite(t) for t in self.output_time_s):
            raise ValueError("output times must be finite")
        if any(b <= a for a, b in zip(self.output_time_s, self.output_time_s[1:])):
            raise ValueError("output times must be strictly increasing")
        species_ids = [row.species_id for row in self.species]
        if len(set(species_ids)) != len(species_ids):
            raise ValueError("species identifiers must be unique")
        if not any(row.charge_number > 0 for row in self.species) or not any(row.charge_number < 0 for row in self.species):
            raise ValueError("the declared transport set must include positive and negative ions")
        if any(len(row.initial_cell_concentration_mol_m3) != self.cell_count for row in self.species):
            raise ValueError("each species must have one initial concentration per cell")
        if set(self.mouth_boundary_concentration_mol_m3_by_species) != set(species_ids):
            raise ValueError("mouth boundary history must declare every species exactly once")
        if any(len(values) != len(self.output_time_s) for values in self.mouth_boundary_concentration_mol_m3_by_species.values()):
            raise ValueError("each mouth boundary history must align exactly with output times")
        species_by_id = {row.species_id: row for row in self.species}
        for k in range(self.cell_count):
            charge = math.fsum(row.charge_number * row.initial_cell_concentration_mol_m3[k] for row in self.species)
            scale = math.fsum(abs(row.charge_number) * row.initial_cell_concentration_mol_m3[k] for row in self.species)
            if scale == 0 or abs(charge) > 1e-9 * scale:
                raise ValueError("each initial cell composition must be locally electroneutral")
        for j in range(len(self.output_time_s)):
            charge = math.fsum(species_by_id[key].charge_number * values[j]
                               for key, values in self.mouth_boundary_concentration_mol_m3_by_species.items())
            scale = math.fsum(abs(species_by_id[key].charge_number) * values[j]
                              for key, values in self.mouth_boundary_concentration_mol_m3_by_species.items())
            if scale == 0 or abs(charge) > 1e-9 * scale:
                raise ValueError("each mouth boundary knot must be locally electroneutral")
        if not any(row.source_id == self.model_provider_id and row.sha256 for row in self.provider_evidence):
            raise ValueError("provider evidence must bind the declared provider to a content digest")
        if not any(row.license_id for row in self.rights_evidence):
            raise ValueError("rights evidence must state a license or permitted-use basis")
        return self


def solve_crevice_electroneutral_diffusion(request: CreviceElectroneutralDiffusionRequest) -> Calculation:
    """Solve a 1-D finite-volume multi-ion Nernst–Planck balance with zero current at every face."""
    try:
        from scipy.integrate import solve_ivp
    except ImportError:
        return Calculation(status="needs_data", values={"model_id": MODEL_ID, "reason": "scipy_runtime_unavailable"})

    digest = canonical_digest(request.model_dump(mode="json"))
    species = request.species
    n_species, n_cells = len(species), request.cell_count
    dx = request.length_m / n_cells
    z = np.asarray([row.charge_number for row in species], dtype=float)
    diffusivity = np.asarray([row.diffusivity_m2_s for row in species], dtype=float)
    initial = np.asarray([row.initial_cell_concentration_mol_m3 for row in species], dtype=float)
    boundary = np.asarray([request.mouth_boundary_concentration_mol_m3_by_species[row.species_id] for row in species], dtype=float)
    n_state = n_species * n_cells
    state0 = np.concatenate((initial.reshape(-1), np.zeros(n_species)))
    times = np.asarray(request.output_time_s, dtype=float)
    function_evaluations = 0
    minimum_seen = float(np.min(initial))
    current_residual_max = 0.0

    def derivative(t: float, state: np.ndarray) -> np.ndarray:
        nonlocal function_evaluations, minimum_seen, current_residual_max
        function_evaluations += 1
        if function_evaluations > request.maximum_function_evaluations:
            raise RuntimeError("maximum_function_evaluations_exceeded")
        c = state[:n_state].reshape(n_species, n_cells)
        minimum_seen = min(minimum_seen, float(np.min(c)))
        # BDF stages may make tiny negative trial states; never use negative carrier amount for migration mobility.
        mobility_c = np.maximum(c, 0.0)
        interval = min(max(int(np.searchsorted(times, t, side="right") - 1), 0), len(times) - 2)
        fraction = min(max((t - times[interval]) / (times[interval + 1] - times[interval]), 0.0), 1.0)
        mouth = boundary[:, interval] + fraction * (boundary[:, interval + 1] - boundary[:, interval])
        gradients = np.zeros((n_species, n_cells + 1), dtype=float)
        face_c = np.zeros_like(gradients)
        gradients[:, 0] = (c[:, 0] - mouth) / (0.5 * dx)
        face_c[:, 0] = 0.5 * (mobility_c[:, 0] + mouth)
        gradients[:, 1:n_cells] = (c[:, 1:] - c[:, :-1]) / dx
        face_c[:, 1:n_cells] = 0.5 * (mobility_c[:, 1:] + mobility_c[:, :-1])
        # Blind tip is no-flux. The electric-field gradient enforces zero ionic current at all remaining faces.
        den = np.sum((z[:, None] ** 2) * diffusivity[:, None] * face_c, axis=0)
        num = np.sum((z[:, None] * diffusivity[:, None]) * gradients, axis=0)
        dpsi_dx = np.divide(-num, den, out=np.zeros_like(num), where=den > 0)
        flux = -diffusivity[:, None] * (gradients + z[:, None] * face_c * dpsi_dx)
        flux[:, -1] = 0.0
        current = np.sum(z[:, None] * flux, axis=0)
        current_residual_max = max(current_residual_max, float(np.max(np.abs(current))))
        dc_dt = -(flux[:, 1:] - flux[:, :-1]) / dx
        d_cumulative = flux[:, 0]
        return np.concatenate((dc_dt.reshape(-1), d_cumulative))

    try:
        solution = solve_ivp(
            derivative, (float(times[0]), float(times[-1])), state0, method="BDF", t_eval=times,
            rtol=request.relative_tolerance, atol=request.absolute_tolerance_mol_m3,
            max_step=request.maximum_step_s,
        )
    except (RuntimeError, FloatingPointError, ValueError) as error:
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": str(error), "input_sha256": digest,
            "function_evaluations": function_evaluations,
        })
    if not solution.success or solution.y.shape[1] != len(times):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": "stiff_integrator_failed", "solver_message": solution.message,
            "input_sha256": digest, "function_evaluations": function_evaluations,
        })
    concentration = solution.y[:n_state].reshape(n_species, n_cells, len(times))
    if not np.isfinite(concentration).all() or float(np.min(concentration)) < -1e-7 * max(float(np.max(initial)), 1.0):
        return Calculation(status="needs_data", values={
            "model_id": MODEL_ID, "reason": "nonphysical_negative_concentration_from_numerical_integration",
            "input_sha256": digest, "minimum_trial_concentration_mol_m3": minimum_seen,
        })
    cumulative_boundary = solution.y[n_state:, :]
    cell_volume = request.cross_section_area_m2 * dx
    inventory = cell_volume * np.sum(np.maximum(concentration, 0.0), axis=1)
    incoming = request.cross_section_area_m2 * cumulative_boundary
    balance_residual = inventory - inventory[:, [0]] - incoming + incoming[:, [0]]
    charge_residual = np.einsum("s,sct->tc", z, concentration)
    states = []
    for j, time in enumerate(times):
        states.append({
            "time_s": float(time),
            "species_concentration_mol_m3_by_id": {
                species[k].species_id: [float(value) for value in concentration[k, :, j]]
                for k in range(n_species)
            },
            "local_charge_residual_mol_eq_m3_by_cell": [float(value) for value in charge_residual[j]],
            "species_inventory_mol_by_id": {species[k].species_id: float(inventory[k, j]) for k in range(n_species)},
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
        "finite_volume_inventory_balance_residual_mol_by_species": {
            species[k].species_id: [float(value) for value in balance_residual[k]] for k in range(n_species)
        },
        "peak_absolute_local_charge_residual_mol_eq_m3": float(np.max(np.abs(charge_residual))),
        "peak_zero_current_residual_mol_eq_m2_s": current_residual_max,
        "minimum_accepted_concentration_mol_m3": float(np.min(concentration)),
        "function_evaluations": function_evaluations,
        "state_history": states,
        "interpretation": "conditional_fixed_geometry_reaction_free_dilute_solution_1d_transport",
        "limitations": [
            "The model assumes dilute-solution Nernst-Planck transport, local electroneutrality, zero current and constant caller diffusivities.",
            "Geometry is fixed, the mouth concentration is caller prescribed and the blind tip is no-flux; no flow, reaction, precipitation or electromigration-current boundary is modeled.",
            "No speciation, activity coefficients, pH, phase kinetics, corrosion susceptibility, wall loss, life, probability or acceptance is inferred.",
            "A numerical inventory or current residual is a discrete accounting diagnostic, not independent physical validation.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceElectroneutralDiffusionRequest,
        evaluator=solve_crevice_electroneutral_diffusion,
        units={
            "cell_width_m": "m",
            "state_history[].time_s": "s",
            "state_history[].species_concentration_mol_m3_by_id.*[]": "mol/m^3",
            "state_history[].species_inventory_mol_by_id.*": "mol",
            "state_history[].local_charge_residual_mol_eq_m3_by_cell[]": "mol_eq/m^3",
            "finite_volume_inventory_balance_residual_mol_by_species.*[]": "mol",
            "peak_absolute_local_charge_residual_mol_eq_m3": "mol_eq/m^3",
            "peak_zero_current_residual_mol_eq_m2_s": "mol_eq/(m^2*s)",
            "minimum_accepted_concentration_mol_m3": "mol/m^3",
        },
        assumptions=(
            "Fixed-geometry one-dimensional finite-volume transport of a caller-defined dilute ionic species set with constant diffusivities.",
            "Local electroneutrality and zero-current closure determine the dimensionless electric-potential gradient at each face; mouth concentrations vary linearly between caller time knots and the blind tip is no-flux.",
            "No reactions, phase changes, activity model, fluid flow, corrosion rate, acceptance or qualification are included.",
        ),
        source_ids=(SPECIES_SOURCE_ID, BOUNDARY_SOURCE_ID, MODEL_SOURCE_ID, "scipy_integrate_solve_ivp", "scipy_integrate_bdf"),
    )]
