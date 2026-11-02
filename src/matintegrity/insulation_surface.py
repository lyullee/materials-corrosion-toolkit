"""Steady cylindrical conduction coupled to external convection and radiation."""

import math

from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class InsulationSurfaceRequest(Contract):
    inner_radius_m: Positive
    outer_radius_m: Positive
    length_m: Positive
    conductivity_W_m_K: Positive
    inner_surface_temperature_K: Positive
    ambient_temperature_K: Positive
    radiative_surroundings_temperature_K: Positive
    convection_W_m2_K: Nonnegative
    emissivity: float = Field(ge=0, le=1)
    steady_constant_conductivity_reviewed: bool

    @model_validator(mode="after")
    def geometry(self):
        if self.outer_radius_m <= self.inner_radius_m:
            raise ValueError("insulation outer radius must exceed inner radius")
        if self.convection_W_m2_K == 0 and self.emissivity == 0:
            raise ValueError("at least one external heat-transfer path is required")
        return self


def solve_insulation_surface(request: InsulationSurfaceRequest) -> dict:
    """Solve a monotone absolute-temperature surface energy balance by bisection."""
    base = dict(input_sha256=canonical_digest(request.model_dump(mode="json")), status="needs_data")
    if not request.steady_constant_conductivity_reviewed:
        return base
    log_radius_ratio = (
        math.log1p((request.outer_radius_m - request.inner_radius_m) / request.inner_radius_m)
        if request.outer_radius_m < 2.0 * request.inner_radius_m
        else math.log(request.outer_radius_m) - math.log(request.inner_radius_m)
    )
    conductance = 2 * math.pi * request.conductivity_W_m_K * request.length_m / log_radius_ratio
    area = 2 * math.pi * request.outer_radius_m * request.length_m
    if not all(math.isfinite(value) and value > 0.0 for value in (conductance, area)):
        return base | {
            "status": "out_of_scope",
            "reason": "Geometry conductance or area exceeds numeric support",
        }
    sigma = 5.670374419e-8

    def components(surface):
        conduction = conductance * (request.inner_surface_temperature_K - surface)
        convection = (
            area * request.convection_W_m2_K * (surface - request.ambient_temperature_K)
            if request.convection_W_m2_K > 0.0 and surface != request.ambient_temperature_K
            else 0.0
        )
        surroundings = request.radiative_surroundings_temperature_K
        radiation = (
            (
                area
                * request.emissivity
                * sigma
                * (surface - surroundings)
                * (surface + surroundings)
                * (surface * surface + surroundings * surroundings)
            )
            if request.emissivity > 0.0 and surface != surroundings
            else 0.0
        )
        return conduction, convection, radiation

    active_temperatures = [request.inner_surface_temperature_K]
    if request.convection_W_m2_K > 0.0:
        active_temperatures.append(request.ambient_temperature_K)
    if request.emissivity > 0.0:
        active_temperatures.append(request.radiative_surroundings_temperature_K)
    low, high = min(active_temperatures), max(active_temperatures)
    iterations = 0
    converged = low == high
    for _ in range(200):
        iterations += 1
        middle = low + (high - low) * 0.5
        conduction, convection, radiation = components(middle)
        if not all(math.isfinite(value) for value in (conduction, convection, radiation)):
            return base | {"status": "out_of_scope", "reason": "Heat flow exceeds numeric support"}
        residual = conduction - convection - radiation
        if not math.isfinite(residual):
            return base | {"status": "out_of_scope", "reason": "Heat residual exceeds numeric support"}
        flux_scale = max(abs(conduction), abs(convection), abs(radiation))
        if residual == 0.0 or abs(residual) <= 1e-9 * flux_scale:
            low = high = middle
            converged = True
            break
        if middle == low or middle == high:
            break
        if residual > 0:
            low = middle
        else:
            high = middle
    if not converged:
        return base | {
            "status": "out_of_scope",
            "reason": "Surface energy balance did not converge",
            "iterations": iterations,
        }
    surface = low + (high - low) * 0.5
    conduction, convection, radiation = components(surface)
    residual = conduction - convection - radiation
    if not all(math.isfinite(value) for value in (conduction, convection, radiation, residual)):
        return base | {"status": "out_of_scope", "reason": "Heat flow exceeds numeric support"}
    return dict(
        **(base | {"status": "computed"}),
        outer_surface_temperature_K=surface,
        heat_from_inner_surface_W=conduction,
        convective_heat_out_W=convection,
        radiative_heat_out_W=radiation,
        balance_residual_W=residual,
        iterations=iterations,
        basis="Steady single-layer radial conduction with caller constant convection and gray diffuse radiation to declared surroundings.",
    )
