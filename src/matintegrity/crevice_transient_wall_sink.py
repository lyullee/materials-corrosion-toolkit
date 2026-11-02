"""Finite eigenfunction approximation for transient slit diffusion and wall sink."""

from __future__ import annotations

import math
import sys
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from .registry import ModelSpec

MODEL_ID = "chemistry.crevice_transient_wall_sink"
SOURCE_ID = "caller_crevice_transient_wall_sink"


class CreviceTransientWallSinkRequest(Contract):
    """Fixed blind-slit, one-species transient diffusion/reaction request."""

    schema_version: Literal["matintegrity.crevice_transient_wall_sink.v1"] = (
        "matintegrity.crevice_transient_wall_sink.v1"
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
    elapsed_times_s: tuple[Nonnegative, ...] = Field(min_length=1, max_length=200)
    sample_positions_m: tuple[Nonnegative, ...] = Field(min_length=1, max_length=200)
    eigenfunction_term_count: int = Field(ge=1, le=2000)
    constant_property_and_geometry_reviewed: bool
    fixed_mouth_concentration_reviewed: bool
    blind_tip_zero_flux_reviewed: bool
    uniform_initial_concentration_equals_mouth_reviewed: bool
    first_order_irreversible_wall_sink_reviewed: bool
    finite_truncation_use_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_grid(self):
        if any(value > self.length_m for value in self.sample_positions_m):
            raise ValueError("sample positions must lie within the caller-declared slit length")
        if any(right <= left for left, right in zip(self.elapsed_times_s[:-1], self.elapsed_times_s[1:], strict=True)):
            raise ValueError("elapsed times must be strictly increasing in caller order")
        if len(self.elapsed_times_s) * len(self.sample_positions_m) * self.eigenfunction_term_count > 500_000:
            raise ValueError("requested time-position-term product exceeds the bounded calculation limit")
        return self


def _stable_steady_concentration_fraction(phi: float, x_fraction: float) -> float:
    """Return cosh(phi*(1-x/L))/cosh(phi) without large cosh values."""
    remaining = 1.0 - x_fraction
    attenuation = phi * x_fraction
    return math.exp(-attenuation) * (
        1.0 + math.exp(-2.0 * phi * remaining)
    ) / (1.0 + math.exp(-2.0 * phi))


def _coefficient(phi: float, alpha: float) -> float:
    """Fourier sine coefficient of C0 minus the steady solution, divided by C0."""
    if phi == 0.0:
        return 0.0
    if phi >= alpha:
        ratio = 1.0 / (1.0 + (alpha / phi) ** 2)
    else:
        ratio_value = phi / alpha
        ratio = ratio_value * ratio_value / (1.0 + ratio_value * ratio_value)
    return (2.0 / alpha) * ratio


def evaluate_crevice_transient_wall_sink(request: CreviceTransientWallSinkRequest) -> Calculation:
    """Return caller-requested samples of a finite analytical eigenfunction sum.

    The governing equation is ``dC/dt = D*d2C/dx2 - k_w*a_w*C`` for one
    dissolved species on a fixed interval. The mouth has a fixed concentration,
    the blind tip has zero diffusive flux, and the initial concentration is
    spatially uniform and equal to the mouth value. The finite series is a
    declared truncation; no error bound or convergence claim is made.
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
        "governing_equation": "dC/dt = D*d2C/dx2 - k_wall*a_wall*C",
        "boundary_conditions": {"mouth": "C(0,t)=C0", "blind_tip": "dC/dx(L,t)=0"},
        "initial_condition": "C(x,0)=C0",
        "reviewed_assumptions": {
            "constant_property_and_geometry": request.constant_property_and_geometry_reviewed,
            "fixed_mouth_concentration": request.fixed_mouth_concentration_reviewed,
            "blind_tip_zero_flux": request.blind_tip_zero_flux_reviewed,
            "uniform_initial_concentration_equals_mouth": request.uniform_initial_concentration_equals_mouth_reviewed,
            "first_order_irreversible_wall_sink": request.first_order_irreversible_wall_sink_reviewed,
            "finite_truncation_use": request.finite_truncation_use_reviewed,
        },
        "evidence": [row.model_dump(mode="json") for row in request.evidence],
        "source_ids": sorted({row.source_id for row in request.evidence}),
        "requested_elapsed_times_s": list(request.elapsed_times_s),
        "requested_positions_m": list(request.sample_positions_m),
        "eigenfunction_term_count": request.eigenfunction_term_count,
    }
    review_fields = (
        ("constant_property_and_geometry_reviewed", request.constant_property_and_geometry_reviewed),
        ("fixed_mouth_concentration_reviewed", request.fixed_mouth_concentration_reviewed),
        ("blind_tip_zero_flux_reviewed", request.blind_tip_zero_flux_reviewed),
        ("uniform_initial_concentration_equals_mouth_reviewed", request.uniform_initial_concentration_equals_mouth_reviewed),
        ("first_order_irreversible_wall_sink_reviewed", request.first_order_irreversible_wall_sink_reviewed),
        ("finite_truncation_use_reviewed", request.finite_truncation_use_reviewed),
    )
    missing = [name for name, reviewed in review_fields if not reviewed]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    length = request.length_m
    diffusivity = request.effective_diffusivity_m2_s
    if request.wall_transfer_velocity_m_s == 0.0:
        log_wall_rate = -math.inf
        phi = 0.0
        lam = 0.0
    else:
        log_wall_rate = (
            math.log(request.wall_transfer_velocity_m_s)
            + math.log(request.wall_area_per_volume_m_inv)
        )
        if log_wall_rate > math.log(sys.float_info.max):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "wall_sink_rate_exceeds_float_support",
            })
        log_lam = 0.5 * (log_wall_rate - math.log(diffusivity))
        log_phi = log_lam + math.log(length)
        if log_phi > math.log(sys.float_info.max):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "reaction_diffusion_length_exceeds_float_support",
                "dimensionless_reaction_diffusion_length_log": log_phi,
            })
        if log_phi < math.log(float.fromhex("0x0.0000000000001p-1022")):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "reaction_diffusion_length_underflows_float_support",
                "dimensionless_reaction_diffusion_length_log": log_phi,
            })
        lam = math.exp(log_lam) if log_lam <= math.log(sys.float_info.max) else math.inf
        phi = math.exp(log_phi)
        if not math.isfinite(lam) or not math.isfinite(phi):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "reaction_diffusion_parameter_exceeds_float_support",
                "dimensionless_reaction_diffusion_length_log": log_phi,
            })

    # The eigenvalues satisfy cos(alpha_n)=0 and sin(alpha_n*x/L)=0 at x=0.
    # The coefficient below follows from the exact initial-minus-steady profile.
    term_data = []
    for n in range(request.eigenfunction_term_count):
        alpha = (n + 0.5) * math.pi
        coefficient = _coefficient(phi, alpha)
        log_diffusion_rate = math.log(diffusivity) + 2.0 * (math.log(alpha) - math.log(length))
        if phi == 0.0:
            log_rate = log_diffusion_rate
        else:
            log_ratio_squared = 2.0 * (math.log(phi) - math.log(alpha))
            log_rate = log_diffusion_rate + (
                log_ratio_squared + math.log1p(math.exp(-log_ratio_squared))
                if log_ratio_squared > 0.0
                else math.log1p(math.exp(log_ratio_squared))
            )
        if log_rate > math.log(sys.float_info.max):
            return Calculation(status="out_of_scope", values=base | {
                "out_of_scope_reason": "eigenmode_decay_rate_exceeds_float_support",
                "first_unsupported_term_index": n,
            })
        rate = math.exp(log_rate)
        term_data.append((alpha, coefficient, rate))

    c0 = request.mouth_concentration_mol_m3
    rows = []
    for time_index, time_s in enumerate(request.elapsed_times_s):
        row = []
        for position_index, position_m in enumerate(request.sample_positions_m):
            x_fraction = position_m / length
            steady_fraction = _stable_steady_concentration_fraction(phi, x_fraction)
            value = c0 * steady_fraction
            for alpha, coefficient, rate in term_data:
                decay_argument = rate * time_s
                decay = math.exp(-decay_argument) if math.isfinite(decay_argument) else 0.0
                value += c0 * coefficient * math.sin(alpha * x_fraction) * decay
            if not math.isfinite(value):
                return Calculation(status="out_of_scope", values=base | {
                    "committed_time_rows": rows,
                    "first_failure": {
                        "time_index": time_index,
                        "position_index": position_index,
                        "elapsed_time_s": time_s,
                        "position_m": position_m,
                        "reason": "nonfinite_truncated_series_value",
                    },
                    "complete_requested_grid_returned": False,
                }, notes=("The incomplete time row was not committed; only the successful time-prefix is returned.",))
            row.append(value)
        rows.append({"elapsed_time_s": time_s, "concentration_mol_m3": row})

    return Calculation(values=base | {
        "units": {
            "elapsed_time": "s",
            "position": "m",
            "concentration": "mol/m^3",
            "dimensionless_reaction_diffusion_length": "1",
            "mode_decay_rate": "1/s",
        },
        "dimensionless_reaction_diffusion_length": phi,
        "eigenfunction_indices": list(range(request.eigenfunction_term_count)),
        "mode_decay_rates_per_s": [rate for _, _, rate in term_data],
        "concentration_rows": rows,
        "series_basis": "steady_solution_plus_finite_sine_modes_with_dirichlet_mouth_and_neumann_blind_tip",
        "finite_truncated_expansion": True,
        "exact_solution_claimed": False,
        "truncation_error_bound_provided": False,
        "convergence_proven": False,
        "spatial_transport_solver_called": False,
        "speciation_or_phase_equilibrium_solved": False,
        "corrosion_rate_or_wall_loss_inferred": False,
        "qualification_claimed": False,
        "complete_requested_grid_returned": True,
    }, notes=(
        "Concentrations are values of the caller-selected finite eigenfunction sum. Term count controls truncation; no truncation error bound, exactness or convergence proof is provided.",
        "This model uses one dissolved species, fixed geometry and caller-supplied constant coefficients; it does not represent flow, evolving chemistry, phase change, corrosion kinetics or qualification.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id=MODEL_ID,
        input_type=CreviceTransientWallSinkRequest,
        evaluator=evaluate_crevice_transient_wall_sink,
        units={
            "concentration_rows[].elapsed_time_s": "s",
            "concentration_rows[].concentration_mol_m3[]": "mol/m3",
            "dimensionless_reaction_diffusion_length": "1",
            "mode_decay_rates_per_s[]": "1/s",
        },
        assumptions=(
            "One dissolved species follows fixed-geometry one-dimensional diffusion with a fixed-concentration mouth, zero-flux blind tip and first-order wall sink.",
            "The initial concentration equals the mouth value; only the caller-selected finite eigenfunction expansion is returned and no truncation error bound is claimed.",
            "No speciation, phase equilibrium, corrosion rate, wall loss, probability or qualification is inferred.",
        ),
        source_ids=(SOURCE_ID,),
        qualification="user_model",
    )]
