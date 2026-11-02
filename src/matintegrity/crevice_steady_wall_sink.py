"""Analytical steady 1-D diffusion with a distributed first-order wall sink.

This reduced model is a transparent limiting calculation for a blind slit. It
does not replace the transient spatial transport and chemistry workflows.
"""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec


MODEL_ID = "chemistry.crevice_steady_wall_sink"
SOURCE_ID = "caller_crevice_steady_wall_sink"


class CreviceSteadyWallSinkRequest(Contract):
    """Caller-reviewed constant-property, one-species blind-slit model."""

    schema_version: Literal["matintegrity.crevice_steady_wall_sink.v1"] = (
        "matintegrity.crevice_steady_wall_sink.v1"
    )
    calculation_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    geometry_id: str = Field(min_length=1)
    species_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    length_m: Positive
    effective_diffusivity_m2_s: Positive
    wall_area_per_volume_m_inv: Positive
    wall_transfer_velocity_m_s: Nonnegative
    mouth_concentration_mol_m3: Nonnegative
    sample_positions_m: tuple[Nonnegative, ...] = Field(default=(), max_length=1001)
    constant_property_and_geometry_reviewed: bool
    blind_tip_zero_flux_reviewed: bool
    first_order_irreversible_wall_sink_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_sample_positions(self):
        if any(position > self.length_m for position in self.sample_positions_m):
            raise ValueError("sample positions must lie within the caller-declared slit length")
        return self


def evaluate_crevice_steady_wall_sink(request: CreviceSteadyWallSinkRequest) -> Calculation:
    """Evaluate the steady blind-slit diffusion/reaction solution.

    The equation is ``D C'' - k_w a_w C = 0``, with mouth concentration
    ``C(0)=C0`` and a sealed blind tip ``C'(L)=0``. ``a_w`` is the wetted wall
    area per solution volume and ``k_w`` is a caller-supplied linear wall
    consumption velocity. The calculation is deliberately limited to one
    dissolved species, constant parameters, fixed geometry and irreversible
    first-order uptake.
    """
    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    base = {
        "calculation_id": request.calculation_id,
        "asset_id": request.asset_id,
        "location_id": request.location_id,
        "geometry_id": request.geometry_id,
        "species_id": request.species_id,
        "condition_id": request.condition_id,
        "input_sha256": input_sha256,
        "model_equation": "D*d2C/dx2 - k_wall*a_wall*C = 0",
        "boundary_conditions": {"mouth": "C(0)=C0", "blind_tip": "dC/dx(L)=0"},
        "assumptions_reviewed": {
            "constant_property_and_geometry": request.constant_property_and_geometry_reviewed,
            "blind_tip_zero_flux": request.blind_tip_zero_flux_reviewed,
            "first_order_irreversible_wall_sink": request.first_order_irreversible_wall_sink_reviewed,
        },
        "evidence": [row.model_dump(mode="json") for row in request.evidence],
        "source_ids": sorted({row.source_id for row in request.evidence}),
    }
    missing = [name for name, reviewed in (
        ("constant_property_and_geometry_reviewed", request.constant_property_and_geometry_reviewed),
        ("blind_tip_zero_flux_reviewed", request.blind_tip_zero_flux_reviewed),
        ("first_order_irreversible_wall_sink_reviewed", request.first_order_irreversible_wall_sink_reviewed),
    ) if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    positions = request.sample_positions_m or tuple(
        request.length_m * fraction for fraction in (0.0, 0.25, 0.5, 0.75, 1.0)
    )
    c0 = request.mouth_concentration_mol_m3
    kw = request.wall_transfer_velocity_m_s
    area_density = request.wall_area_per_volume_m_inv
    diffusivity = request.effective_diffusivity_m2_s
    if c0 == 0.0 or kw == 0.0:
        concentrations = [c0 for _ in positions]
        phi = 0.0
        inlet_flux = 0.0
        average_concentration = c0
    else:
        # Work in log space so products such as k_w*a_w/D do not overflow
        # before we can return a bounded out-of-scope result.
        log_lambda = 0.5 * (math.log(kw) + math.log(area_density) - math.log(diffusivity))
        log_phi = log_lambda + math.log(request.length_m)
        if log_phi > math.log(sys.float_info.max):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "dimensionless_reaction_diffusion_length_exceeds_float_support",
                "dimensionless_reaction_diffusion_length_log": log_phi,
            }, notes=("No clipping was applied because the reaction-diffusion length is outside floating-point support.",))
        lam = math.exp(log_lambda) if log_lambda < math.log(sys.float_info.max) else math.inf
        phi = math.exp(log_phi) if log_phi > -745.0 else 0.0
        if not math.isfinite(lam) or not math.isfinite(phi):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "reaction_diffusion_parameter_exceeds_float_support",
                "dimensionless_reaction_diffusion_length_log": log_phi,
            })

        # Stable normalized cosh ratio, including large phi and positions at
        # either boundary. Underflow to zero represents an unresolvable tail.
        profile = []
        for x in positions:
            distance = request.length_m - x
            attenuation = lam * x
            ratio = math.exp(-attenuation) * (
                1.0 + math.exp(-2.0 * lam * distance)
            ) / (1.0 + math.exp(-2.0 * phi))
            profile.append(c0 * ratio)
        concentrations = profile
        average_factor = 1.0 if phi < 1e-8 else math.tanh(phi) / phi
        average_concentration = c0 * average_factor
        inlet_flux = diffusivity * lam * c0 * math.tanh(phi)

    wall_flux_per_surface_area = kw * average_concentration
    integrated_wall_sink_per_mouth_area = (
        kw * area_density * request.length_m * average_concentration
    )
    residual = inlet_flux - integrated_wall_sink_per_mouth_area
    scale = max(abs(inlet_flux), abs(integrated_wall_sink_per_mouth_area), sys.float_info.min)
    if not all(math.isfinite(value) for value in (
        inlet_flux, average_concentration, wall_flux_per_surface_area,
        integrated_wall_sink_per_mouth_area, residual,
    )) or any(not math.isfinite(value) for value in concentrations):
        return Calculation(status="out_of_scope", values=base | {
            "out_of_scope_reason": "steady_solution_exceeds_float_support",
            "dimensionless_reaction_diffusion_length": phi,
        })

    return Calculation(values=base | {
        "status_basis": "analytical_steady_one_dimensional_blind_slit_screen",
        "units": {
            "position": "m",
            "concentration": "mol/m^3",
            "dimensionless_reaction_diffusion_length": "1",
            "inlet_flux_per_mouth_area": "mol/(m^2 s)",
            "mean_wall_flux_per_wetted_area": "mol/(m^2 s)",
            "integrated_wall_sink_per_mouth_area": "mol/(m^2 s)",
        },
        "position_m": list(positions),
        "concentration_mol_m3": concentrations,
        "mouth_concentration_mol_m3": c0,
        "tip_concentration_mol_m3": concentrations[positions.index(request.length_m)]
            if request.length_m in positions else c0 / math.cosh(phi) if phi < 710.0 else 0.0,
        "mean_concentration_mol_m3": average_concentration,
        "dimensionless_reaction_diffusion_length": phi,
        "inlet_flux_per_mouth_area_mol_m2_s": inlet_flux,
        "mean_wall_flux_per_wetted_area_mol_m2_s": wall_flux_per_surface_area,
        "integrated_wall_sink_per_mouth_area_mol_m2_s": integrated_wall_sink_per_mouth_area,
        "steady_mass_balance_residual_mol_m2_s": residual,
        "steady_mass_balance_relative_residual": residual / scale,
        "spatial_transport_solved": False,
        "speciation_or_phase_equilibrium_solved": False,
        "corrosion_rate_or_wall_loss_inferred": False,
        "qualification_claimed": False,
    }, notes=(
        "This exact solution is a reduced steady one-species diffusion/sink screen for fixed blind-slit geometry, not a transient crevice transport or chemistry model.",
        "Diffusivity, wall transfer velocity, wall area density, concentration, boundary interpretation and applicability are caller-owned; no corrosion rate, wall loss or phase selection is inferred.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceSteadyWallSinkRequest,
        evaluator=evaluate_crevice_steady_wall_sink,
        units={
            "position_m": "m",
            "concentration_mol_m3": "mol/m3",
            "mean_concentration_mol_m3": "mol/m3",
            "inlet_flux_per_mouth_area_mol_m2_s": "mol/(m2 s)",
            "mean_wall_flux_per_wetted_area_mol_m2_s": "mol/(m2 s)",
            "integrated_wall_sink_per_mouth_area_mol_m2_s": "mol/(m2 s)",
            "steady_mass_balance_residual_mol_m2_s": "mol/(m2 s)",
        },
        assumptions=(
            "One dissolved species follows steady one-dimensional diffusion and irreversible first-order wall consumption in a caller-reviewed fixed blind slit.",
            "Diffusivity, wall transfer, wetted area density, boundary conditions and evidence are caller-supplied; no corrosion rate or wall loss is inferred.",
            "The calculation does not replace transient transport, speciation, phase equilibrium, geometry feedback or qualification.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
