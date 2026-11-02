"""Steady finite-volume scale reaction–diffusion coupled to a mixed-potential electrode."""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, StrictInt, model_validator

from .contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "integration.wet_co2_scale_diffusion_electrode_mixed_potential"
FARADAY_C_MOL = 96485.33212
GAS_CONSTANT_J_MOL_K = 8.31446261815324
MAX_HISTORY_KNOTS = 20_000
MAX_SCALE_CELLS = 500
MAX_BRANCHES = 32


class ScaleAnodicBranch(Contract):
    """Caller Butler–Volmer oxidation branch with an explicit metal stoichiometry."""

    reaction_id: str = Field(min_length=1)
    equilibrium_potential_V: float
    exchange_current_density_A_m2: Positive
    electron_count: StrictInt = Field(ge=1, le=32)
    anodic_transfer_coefficient: Positive
    cathodic_transfer_coefficient: Positive
    metal_atoms_per_reaction_extent: Positive
    metal_molar_mass_kg_mol: Positive
    metal_density_kg_m3: Positive

    @model_validator(mode="after")
    def validate_branch(self):
        values = (
            self.equilibrium_potential_V,
            self.exchange_current_density_A_m2,
            self.anodic_transfer_coefficient,
            self.cathodic_transfer_coefficient,
            self.metal_atoms_per_reaction_extent,
            self.metal_molar_mass_kg_mol,
            self.metal_density_kg_m3,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("anodic branch inputs must be finite")
        if self.anodic_transfer_coefficient >= 1 or self.cathodic_transfer_coefficient >= 1:
            raise ValueError("Butler–Volmer transfer coefficients must be below one")
        return self


class ScaleCathodicReactantBranch(Contract):
    """Caller Butler–Volmer reduction branch consuming one transported scale species."""

    reaction_id: str = Field(min_length=1)
    reactant_species_id: str = Field(min_length=1)
    equilibrium_potential_V: float
    exchange_current_density_A_m2: Positive
    electron_count: StrictInt = Field(ge=1, le=32)
    reactant_moles_per_reaction_extent: Positive
    anodic_transfer_coefficient: Positive
    cathodic_transfer_coefficient: Positive

    @model_validator(mode="after")
    def validate_branch(self):
        values = (
            self.equilibrium_potential_V,
            self.exchange_current_density_A_m2,
            self.reactant_moles_per_reaction_extent,
            self.anodic_transfer_coefficient,
            self.cathodic_transfer_coefficient,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("cathodic branch inputs must be finite")
        if self.anodic_transfer_coefficient >= 1 or self.cathodic_transfer_coefficient >= 1:
            raise ValueError("Butler–Volmer transfer coefficients must be below one")
        return self


class ScaleDiffusionElectrodeKnot(Contract):
    """One independent steady operating knot with a fixed scale layer and condition."""

    knot_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    temperature_K: Positive
    scale_thickness_m: Positive
    cell_count: StrictInt = Field(ge=2, le=MAX_SCALE_CELLS)
    effective_diffusivity_m2_s: Positive
    first_order_scale_sink_rate_s: float = Field(ge=0)
    bulk_reactant_concentration_mol_m3: Positive
    reference_reactant_concentration_mol_m3: Positive
    reactant_species_id: str = Field(min_length=1)
    potential_reference_id: str = Field(min_length=1)
    potential_lower_V: float
    potential_upper_V: float
    anodic_branches: tuple[ScaleAnodicBranch, ...] = Field(min_length=1, max_length=MAX_BRANCHES)
    cathodic_branches: tuple[ScaleCathodicReactantBranch, ...] = Field(min_length=1, max_length=MAX_BRANCHES)
    transport_provider_id: str = Field(min_length=1)
    transport_provider_revision: str = Field(min_length=1)
    transport_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    electrode_provider_id: str = Field(min_length=1)
    electrode_provider_revision: str = Field(min_length=1)
    electrode_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    transport_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    electrode_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    potential_support_and_branch_signs_reviewed: bool

    @model_validator(mode="after")
    def validate_knot(self):
        numeric = (
            self.time_s,
            self.temperature_K,
            self.scale_thickness_m,
            self.effective_diffusivity_m2_s,
            self.first_order_scale_sink_rate_s,
            self.bulk_reactant_concentration_mol_m3,
            self.reference_reactant_concentration_mol_m3,
            self.potential_lower_V,
            self.potential_upper_V,
        )
        if not all(math.isfinite(value) for value in numeric):
            raise ValueError("scale/electrode knot inputs must be finite")
        if self.potential_lower_V >= self.potential_upper_V:
            raise ValueError("potential root bracket must be strictly ordered")
        if not all(math.isfinite(value) for value in (self.potential_lower_V, self.potential_upper_V)):
            raise ValueError("potential root bracket must be finite")
        if len({row.reaction_id for row in self.anodic_branches}) != len(self.anodic_branches):
            raise ValueError("anodic reaction IDs must be unique")
        if len({row.reaction_id for row in self.cathodic_branches}) != len(self.cathodic_branches):
            raise ValueError("cathodic reaction IDs must be unique")
        if any(row.reactant_species_id != self.reactant_species_id for row in self.cathodic_branches):
            raise ValueError("every cathodic branch must consume the declared transported species")
        if not {self.transport_provider_id}.issubset({item.source_id for item in self.transport_evidence}):
            raise ValueError("transport Evidence must identify the transport provider")
        if not {self.electrode_provider_id}.issubset({item.source_id for item in self.electrode_evidence}):
            raise ValueError("electrode Evidence must identify the electrode provider")
        return self


class WetCo2ScaleDiffusionElectrodeHistory(Contract):
    """Finite scale reaction–diffusion and electrode mixed-potential history."""

    schema_version: Literal["matintegrity.wet_co2_scale_diffusion_electrode_mixed_potential.v1"] = (
        "matintegrity.wet_co2_scale_diffusion_electrode_mixed_potential.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    knots: tuple[ScaleDiffusionElectrodeKnot, ...] = Field(min_length=1, max_length=MAX_HISTORY_KNOTS)
    fixed_geometry_patch_reviewed: bool
    finite_volume_and_first_order_sink_reviewed: bool
    common_metal_potential_and_no_ohmic_drop_reviewed: bool
    steady_state_at_each_knot_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_ordered_knots(self):
        if len({row.knot_id for row in self.knots}) != len(self.knots):
            raise ValueError("history knot IDs must be unique")
        times = [row.time_s for row in self.knots]
        if any(right <= left for left, right in zip(times, times[1:])):
            raise ValueError("history knot times must strictly increase")
        if any(not math.isfinite(value) for value in times):
            raise ValueError("history knot times must be finite")
        return self


def _exp(value: float) -> float | None:
    if not math.isfinite(value) or value > 700.0 or value < -745.0:
        return None
    result = math.exp(value)
    return result if math.isfinite(result) else None


def _bv_factor(branch: ScaleAnodicBranch | ScaleCathodicReactantBranch, potential_V: float,
               temperature_K: float) -> float | None:
    eta = potential_V - branch.equilibrium_potential_V
    thermal_voltage = GAS_CONSTANT_J_MOL_K * temperature_K
    anodic_arg = branch.anodic_transfer_coefficient * branch.electron_count * FARADAY_C_MOL * eta / thermal_voltage
    cathodic_arg = -branch.cathodic_transfer_coefficient * branch.electron_count * FARADAY_C_MOL * eta / thermal_voltage
    anodic = _exp(anodic_arg)
    cathodic = _exp(cathodic_arg)
    if anodic is None or cathodic is None:
        return None
    value = anodic - cathodic
    return value if math.isfinite(value) else None


def _solve_tridiagonal(lower: list[float], diagonal: list[float], upper: list[float], rhs: list[float]) -> list[float] | None:
    """Thomas solve for the caller finite-volume concentration system."""
    n = len(diagonal)
    d = list(diagonal)
    b = list(rhs)
    u = list(upper)
    l = list(lower)
    if n == 0 or len(b) != n or len(l) != n or len(u) != n:
        return None
    if not all(math.isfinite(value) for value in (*d, *b, *u, *l)):
        return None
    # Pivot conditioning is determined by the matrix, not the RHS concentration
    # scale (which has different units and may legitimately be very large).
    scale = max(abs(value) for value in (*d, *u, *l))
    if scale == 0.0:
        return None
    for i in range(1, n):
        if abs(d[i - 1]) <= 1.0e-14 * scale:
            return None
        factor = l[i] / d[i - 1]
        d[i] -= factor * u[i - 1]
        b[i] -= factor * b[i - 1]
    if abs(d[-1]) <= 1.0e-14 * scale:
        return None
    x = [0.0] * n
    x[-1] = b[-1] / d[-1]
    for i in range(n - 2, -1, -1):
        if abs(d[i]) <= 1.0e-14 * scale:
            return None
        x[i] = (b[i] - u[i] * x[i + 1]) / d[i]
    return x if all(math.isfinite(value) for value in x) else None


def _concentration_profile(knot: ScaleDiffusionElectrodeKnot, potential_V: float) -> dict[str, Any] | None:
    dx = knot.scale_thickness_m / knot.cell_count
    D = knot.effective_diffusivity_m2_s
    k = knot.first_order_scale_sink_rate_s
    c_bulk = knot.bulk_reactant_concentration_mol_m3
    c_ref = knot.reference_reactant_concentration_mol_m3
    conductance = 0.0
    for branch in knot.cathodic_branches:
        factor = _bv_factor(branch, potential_V, knot.temperature_K)
        if factor is None:
            return None
        conductance += -branch.exchange_current_density_A_m2 * factor * (
            branch.reactant_moles_per_reaction_extent
            / (branch.electron_count * FARADAY_C_MOL * c_ref)
        )
    denominator = 1.0 + conductance * dx / (2.0 * D)
    if not math.isfinite(denominator) or denominator <= 1.0e-12:
        return None
    wall_ratio = 1.0 / denominator
    n = knot.cell_count
    lower = [0.0] * n
    diagonal = [0.0] * n
    upper = [0.0] * n
    rhs = [0.0] * n
    if n == 1:
        diagonal[0] = 2.0 * D / dx + conductance * wall_ratio + k * dx
        rhs[0] = 2.0 * D * c_bulk / dx
    else:
        lower[0] = 0.0
        diagonal[0] = -D / dx - conductance * wall_ratio - k * dx
        upper[0] = D / dx
        for i in range(1, n - 1):
            lower[i] = D / dx
            diagonal[i] = -2.0 * D / dx - k * dx
            upper[i] = D / dx
        lower[-1] = -D / dx
        diagonal[-1] = 3.0 * D / dx + k * dx
        upper[-1] = 0.0
        rhs[-1] = 2.0 * D * c_bulk / dx
    cells = _solve_tridiagonal(lower, diagonal, upper, rhs)
    if cells is None:
        return None
    wall_concentration = cells[0] * wall_ratio
    if wall_concentration <= 0.0 or any(value <= 0.0 for value in cells):
        return None
    currents = {}
    for branch in knot.cathodic_branches:
        factor = _bv_factor(branch, potential_V, knot.temperature_K)
        if factor is None:
            return None
        currents[branch.reaction_id] = branch.exchange_current_density_A_m2 * (
            wall_concentration / c_ref
        ) * factor
    consumption = math.fsum(
        -currents[branch.reaction_id] * branch.reactant_moles_per_reaction_extent
        / (branch.electron_count * FARADAY_C_MOL)
        for branch in knot.cathodic_branches
    )
    bulk_flux = 2.0 * D * (c_bulk - cells[-1]) / dx
    volume_reaction_flux = k * math.fsum(cells) * dx
    mass_residual = bulk_flux - consumption - volume_reaction_flux
    if not all(math.isfinite(value) for value in (consumption, bulk_flux, volume_reaction_flux, mass_residual)):
        return None
    return {
        "cell_concentrations_mol_m3": cells,
        "wall_concentration_mol_m3": wall_concentration,
        "cathodic_current_density_A_m2_by_reaction": currents,
        "wall_reactant_consumption_mol_m2_s": consumption,
        "bulk_to_scale_diffusive_flux_mol_m2_s": bulk_flux,
        "distributed_first_order_reaction_consumption_mol_m2_s": volume_reaction_flux,
        "reactant_mass_balance_residual_mol_m2_s": mass_residual,
    }


def _mixed_state(knot: ScaleDiffusionElectrodeKnot, potential_V: float) -> dict[str, Any] | None:
    profile = _concentration_profile(knot, potential_V)
    if profile is None:
        return None
    anodic_currents = {}
    for branch in knot.anodic_branches:
        factor = _bv_factor(branch, potential_V, knot.temperature_K)
        if factor is None:
            return None
        anodic_currents[branch.reaction_id] = branch.exchange_current_density_A_m2 * factor
    net_current = math.fsum(anodic_currents.values()) + math.fsum(
        profile["cathodic_current_density_A_m2_by_reaction"].values()
    )
    if not math.isfinite(net_current):
        return None
    return profile | {
        "anodic_current_density_A_m2_by_reaction": anodic_currents,
        "net_current_density_A_m2": net_current,
    }


def _solve_knot(knot: ScaleDiffusionElectrodeKnot, scipy: Any, absolute_tolerance_A_m2: float) -> dict[str, Any] | None:
    brentq = getattr(getattr(scipy, "optimize", None), "brentq", None)
    if not callable(brentq):
        return None
    lower = knot.potential_lower_V
    upper = knot.potential_upper_V
    low_state = _mixed_state(knot, lower)
    high_state = _mixed_state(knot, upper)
    if low_state is None or high_state is None:
        return None
    f_lower = low_state["net_current_density_A_m2"]
    f_upper = high_state["net_current_density_A_m2"]
    if abs(f_lower) <= absolute_tolerance_A_m2:
        root = lower
    elif abs(f_upper) <= absolute_tolerance_A_m2:
        root = upper
    elif f_lower * f_upper >= 0.0:
        return None
    else:
        try:
            root = float(brentq(
                lambda potential: (
                    state["net_current_density_A_m2"]
                    if (state := _mixed_state(knot, potential)) is not None
                    else math.nan
                ),
                lower,
                upper,
                xtol=1.0e-12,
                rtol=1.0e-12,
                maxiter=200,
            ))
        except (ArithmeticError, TypeError, ValueError, RuntimeError, OverflowError):
            return None
    state = _mixed_state(knot, root)
    if state is None or abs(state["net_current_density_A_m2"]) > absolute_tolerance_A_m2:
        return None
    metal_fluxes = {}
    recession_rates = {}
    for branch in knot.anodic_branches:
        current = state["anodic_current_density_A_m2_by_reaction"][branch.reaction_id]
        if current < 0.0:
            return None
        extent_flux = current / (branch.electron_count * FARADAY_C_MOL)
        metal_flux = extent_flux * branch.metal_atoms_per_reaction_extent
        recession = metal_flux * branch.metal_molar_mass_kg_mol / branch.metal_density_kg_m3
        if not all(math.isfinite(value) and value >= 0.0 for value in (extent_flux, metal_flux, recession)):
            return None
        metal_fluxes[branch.reaction_id] = metal_flux
        recession_rates[branch.reaction_id] = recession
    state.update({
        "knot_id": knot.knot_id,
        "time_s": knot.time_s,
        "temperature_K": knot.temperature_K,
        "mixed_potential_V": root,
        "potential_reference_id": knot.potential_reference_id,
        "scale_thickness_m": knot.scale_thickness_m,
        "effective_diffusivity_m2_s": knot.effective_diffusivity_m2_s,
        "first_order_scale_sink_rate_s": knot.first_order_scale_sink_rate_s,
        "metal_loss_flux_mol_m2_s_by_reaction": metal_fluxes,
        "uniform_wall_recession_rate_m_s_by_reaction": recession_rates,
        "total_uniform_wall_recession_rate_m_s": math.fsum(recession_rates.values()),
        "current_balance_residual_A_m2": state["net_current_density_A_m2"],
        "transport_configuration_sha256": knot.transport_configuration_sha256,
        "electrode_configuration_sha256": knot.electrode_configuration_sha256,
        "transport_evidence": [item.model_dump(mode="json") for item in knot.transport_evidence],
        "electrode_evidence": [item.model_dump(mode="json") for item in knot.electrode_evidence],
    })
    return state


def evaluate_wet_co2_scale_diffusion_electrode_mixed_potential(
    request: WetCo2ScaleDiffusionElectrodeHistory,
    *,
    scipy: Any,
) -> Calculation:
    """Solve a steady scale finite-volume mass balance and interfacial mixed potential at each exact knot."""
    common = {
        "assessment_id": request.assessment_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "physical_scope_id": request.physical_scope_id,
        "condition_id": request.condition_id,
        "request_sha256": canonical_digest(request.model_dump(mode="json")),
        "model_id": MODEL_ID,
        "simultaneous_scale_finite_volume_diffusion_reaction_and_electrode_balance": True,
        "steady_independent_exact_knots_no_interpolation": True,
    }
    reviews = {
        "fixed_geometry_patch_reviewed": request.fixed_geometry_patch_reviewed,
        "finite_volume_and_first_order_sink_reviewed": request.finite_volume_and_first_order_sink_reviewed,
        "common_metal_potential_and_no_ohmic_drop_reviewed": request.common_metal_potential_and_no_ohmic_drop_reviewed,
        "steady_state_at_each_knot_reviewed": request.steady_state_at_each_knot_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=common | {"missing_reviews": missing})
    results = []
    for index, knot in enumerate(request.knots):
        solved = _solve_knot(knot, scipy, absolute_tolerance_A_m2=1.0e-8)
        if solved is None:
            return Calculation(status="out_of_scope", values=common | {
                "computed_prefix": results,
                "failed_knot_index": index,
                "failed_knot_id": knot.knot_id,
                "reason": "no finite nonnegative concentration profile and mixed-potential root satisfied the caller bracket",
            })
        results.append(solved)
    return Calculation(status="computed", values=common | {
        "knot_count": len(results),
        "history": results,
        "limitations": [
            "One dissolved reactant uses fixed effective diffusivity and caller first-order homogeneous sink in a planar, fixed-thickness scale; phase structure and porosity are not inferred.",
            "All electrode branches share one equipotential metal and use caller Butler-Volmer coefficients; solution ohmic drop, double-layer charging and concentration dependence beyond the declared first-order cathodic factor are omitted.",
            "Each knot is a steady independent balance. There is no temporal integration, moving geometry, scale growth, hydrodynamic model or within-knot interpolation.",
            "Metal recession is a nominal Faraday-equivalent uniform rate from caller branch stoichiometry and density, not a pitting, localized corrosion or qualification prediction.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=WetCo2ScaleDiffusionElectrodeHistory,
        evaluator=evaluate_wet_co2_scale_diffusion_electrode_mixed_potential,
        units={
            "history[].time_s": "s",
            "history[].temperature_K": "K",
            "history[].scale_thickness_m": "m",
            "history[].mixed_potential_V": "V",
            "history[].cell_concentrations_mol_m3[]": "mol/m^3",
            "history[].wall_concentration_mol_m3": "mol/m^3",
            "history[].cathodic_current_density_A_m2_by_reaction.*": "A/m^2",
            "history[].anodic_current_density_A_m2_by_reaction.*": "A/m^2",
            "history[].wall_reactant_consumption_mol_m2_s": "mol/m^2/s",
            "history[].bulk_to_scale_diffusive_flux_mol_m2_s": "mol/m^2/s",
            "history[].distributed_first_order_reaction_consumption_mol_m2_s": "mol/m^2/s",
            "history[].reactant_mass_balance_residual_mol_m2_s": "mol/m^2/s",
            "history[].metal_loss_flux_mol_m2_s_by_reaction.*": "mol/m^2/s",
            "history[].total_uniform_wall_recession_rate_m_s": "m/s",
        },
        assumptions=(
            "At each caller time knot, a one-dimensional steady finite-volume reactant balance inside a fixed scale is solved simultaneously with one common mixed potential.",
            "Scale consumption is a caller-defined first-order volumetric sink; cathodic Butler-Volmer branches consume the same declared species in proportion to wall concentration.",
            "The caller provides all electrochemical and transport parameters, temperature, root bracket, stoichiometry, and evidence; no parameter fitting or thermodynamic inference is performed.",
        ),
        source_ids=(
            "caller_scale_reaction_diffusion_transport_parameters",
            "caller_scale_anodic_butler_volmer_branches",
            "caller_scale_cathodic_butler_volmer_branches",
            "caller_scale_reactant_and_metal_stoichiometry",
            "finite_volume_scale_first_order_sink_with_butler_volmer_mixed_potential",
            "butler_erdey_gruz_volmer_electrode_kinetics",
            "nist_codata_faraday_constant_2022",
        ),
        runtime_dependency_names=("scipy",),
        qualification="user_model",
    )]
