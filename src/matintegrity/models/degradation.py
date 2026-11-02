"""Declared electrochemical, transport, wear and measured-geometry models."""

from __future__ import annotations

import math
from fractions import Fraction as Rational
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive, RunContext
from ..registry import ModelSpec


class SternGeary(Contract):
    anodic_tafel_slope_V_decade: Positive
    cathodic_tafel_slope_V_decade: Positive
    area_normalized_resistance_ohm_m2: Positive


def _finite_circuit_value(exact):
    result = float(exact)
    if not math.isfinite(result) or (exact and result == 0):
        raise ArithmeticError("nonzero circuit result is not representable")
    return result


def stern_geary(x: SternGeary) -> Calculation:
    a, c = Rational(x.anodic_tafel_slope_V_decade), Rational(x.cathodic_tafel_slope_V_decade)
    coefficient = a * c / ((a + c) * Rational(math.log(10)))
    try:
        values = dict(
            stern_geary_coefficient_V=_finite_circuit_value(coefficient),
            corrosion_current_density_A_m2=_finite_circuit_value(
                coefficient / Rational(x.area_normalized_resistance_ohm_m2)
            ),
        )
    except ArithmeticError:
        return Calculation(
            status="out_of_scope", values={"reason": "Stern-Geary result exceeds finite arithmetic support"}
        )
    return Calculation(
        values=values,
        notes=(
            "Positive Tafel-slope magnitudes are in volts per decade, not natural-log slope units.",
            "Caller area-normalized polarization resistance must be corrected for solution resistance and applicable to the activation-controlled small-signal model; no correction or current separation is inferred.",
        ),
    )


class GalvanicLinear(Contract):
    anodic_free_potential_V: float
    cathodic_free_potential_V: float
    anodic_area_m2: Positive
    cathodic_area_m2: Positive
    anodic_polarization_resistance_ohm_m2: Positive
    cathodic_polarization_resistance_ohm_m2: Positive
    electrolyte_resistance_ohm: Nonnegative
    maximum_linear_overpotential_V: Positive


def galvanic_linear(x: GalvanicLinear) -> Calculation:
    difference = Rational(x.cathodic_free_potential_V) - Rational(x.anodic_free_potential_V)
    if difference < 0:
        return Calculation(status="out_of_scope", values={}, notes=("Swap the declared electrode roles.",))
    ra = Rational(x.anodic_polarization_resistance_ohm_m2) / Rational(x.anodic_area_m2)
    rc = Rational(x.cathodic_polarization_resistance_ohm_m2) / Rational(x.cathodic_area_m2)
    current = difference / (ra + rc + Rational(x.electrolyte_resistance_ohm))
    try:
        values = dict(
            coupling_current_A=_finite_circuit_value(current),
            anodic_current_density_A_m2=_finite_circuit_value(current / Rational(x.anodic_area_m2)),
            cathodic_current_density_A_m2=_finite_circuit_value(current / Rational(x.cathodic_area_m2)),
            anodic_overpotential_V=_finite_circuit_value(current * ra),
            cathodic_overpotential_magnitude_V=_finite_circuit_value(current * rc),
        )
    except ArithmeticError:
        return Calculation(
            status="out_of_scope",
            values={"reason": "linear galvanic result exceeds finite arithmetic support"},
        )
    valid = max(current * ra, current * rc) <= Rational(x.maximum_linear_overpotential_V)
    return Calculation(
        values=values,
        status="computed" if valid else "out_of_scope",
        notes=("Only the incremental coupling current is computed; uncoupled self-corrosion is separate.",),
    )


class SemiInfiniteDiffusion(Contract):
    diffusivity_m2_s: Positive
    exposure_s: Positive
    depth_m: list[Nonnegative] = Field(min_length=1)
    initial_concentration_mol_m3: Nonnegative
    surface_concentration_mol_m3: Nonnegative


def semi_infinite_diffusion(x: SemiInfiniteDiffusion) -> Calculation:
    try:
        scale = math.sqrt(x.diffusivity_m2_s * x.exposure_s)
        change = x.surface_concentration_mol_m3 - x.initial_concentration_mol_m3
        concentrations = [x.initial_concentration_mol_m3 + change * math.erfc(z / (2 * scale)) for z in x.depth_m]
        surface_flux = change * math.sqrt(x.diffusivity_m2_s / (math.pi * x.exposure_s))
        integrated_excess = 2 * change * scale / math.sqrt(math.pi)
        if not all(math.isfinite(value) for value in [*concentrations, surface_flux, integrated_excess]):
            raise ArithmeticError("diffusion result exceeds finite numeric support")
    except (ArithmeticError, OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values={}, notes=("Required semi-infinite diffusion outputs exceed finite numeric support.",))
    return Calculation(
        values=dict(
            concentration_mol_m3=concentrations,
            surface_flux_mol_m2_s=surface_flux,
            integrated_excess_mol_m2=integrated_excess,
        ),
        notes=(
            "Constant diffusivity and fixed surface concentration; traps, stress coupling and finite back walls excluded.",
        ),
    )


class ParabolicOxidation(Contract):
    initial_oxide_thickness_m: Nonnegative
    parabolic_constant_m2_s: Nonnegative
    exposure_s: Nonnegative


def parabolic_oxidation(x: ParabolicOxidation) -> Calculation:
    final = math.hypot(x.initial_oxide_thickness_m, math.sqrt(x.parabolic_constant_m2_s * x.exposure_s))
    return Calculation(
        values=dict(oxide_thickness_m=final, oxide_growth_m=final - x.initial_oxide_thickness_m),
        notes=(
            "Oxide growth is not metal penetration; conversion needs stoichiometry, densities and scale retention.",
        ),
    )


class ArchardWear(Contract):
    dimensionless_wear_coefficient: Nonnegative
    normal_force_N: Nonnegative
    sliding_distance_m: Nonnegative
    hardness_Pa: Positive
    distributed_area_m2: Positive


def archard_wear(x: ArchardWear) -> Calculation:
    try:
        volume = x.dimensionless_wear_coefficient * x.normal_force_N * x.sliding_distance_m / x.hardness_Pa
        depth = volume / x.distributed_area_m2
        if not math.isfinite(volume) or not math.isfinite(depth):
            raise ArithmeticError("wear result exceeds finite numeric support")
    except (ArithmeticError, OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values={}, notes=("Required Archard wear outputs exceed finite numeric support.",))
    return Calculation(
        values=dict(wear_volume_m3=volume, mean_wear_depth_m=depth),
        notes=(
            "Coefficient is specific to the calibrated contact pair and regime; no fretting-corrosion interaction inferred.",
        ),
    )


class CavitationMargin(Contract):
    """Reviewed local liquid state for thermodynamic cavitation screening."""

    fluid_id: str = Field(min_length=1)
    temperature_K: Positive
    pressure_basis: Literal["absolute"] = "absolute"
    local_static_pressure_Pa: Positive
    vapor_pressure_Pa: Positive
    liquid_density_kg_m3: Positive
    characteristic_velocity_m_s: Positive
    property_provider_id: str = Field(min_length=1)
    property_provider_version: str = Field(min_length=1)
    property_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_pressure_definition: str = Field(min_length=1)
    velocity_definition: str = Field(min_length=1)
    absolute_pressure_reviewed: bool
    thermodynamic_state_reviewed: bool


def cavitation_margin(x: CavitationMargin) -> Calculation:
    if not x.absolute_pressure_reviewed or not x.thermodynamic_state_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Absolute local pressure and the liquid thermodynamic state require caller review.",),
        )
    dynamic_pressure = 0.5 * x.liquid_density_kg_m3 * x.characteristic_velocity_m_s**2
    pressure_margin = x.local_static_pressure_Pa - x.vapor_pressure_Pa
    return Calculation(
        values=dict(
            static_pressure_margin_Pa=pressure_margin,
            static_head_margin_m=pressure_margin / (x.liquid_density_kg_m3 * 9.80665),
            characteristic_dynamic_pressure_Pa=dynamic_pressure,
            local_cavitation_number=pressure_margin / dynamic_pressure,
            local_static_to_vapor_pressure_ratio=x.local_static_pressure_Pa / x.vapor_pressure_Pa,
            thermodynamic_cavitation_possible=x.local_static_pressure_Pa <= x.vapor_pressure_Pa,
        ),
        notes=(
            "A nonpositive static margin indicates local thermodynamic vapor formation is possible under the supplied state.",
            "The result does not predict nuclei, inception under unsteady pressure, bubble collapse, erosion rate, material damage or acceptance.",
        ),
    )


class CavitationHistory(Contract):
    """Reviewed local pressure and equilibrium liquid-property history."""

    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    history_origin: Literal["measured", "model_prediction", "user_declared", "synthetic"]
    hydraulic_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    fluid_id: str = Field(min_length=1)
    pressure_basis: Literal["absolute"] = "absolute"
    sample_ids: list[str] = Field(min_length=2)
    time_s: list[Nonnegative] = Field(min_length=2)
    local_static_pressure_Pa: list[Positive] = Field(min_length=2)
    temperature_K: list[Positive] = Field(min_length=2)
    vapor_pressure_Pa: list[Positive] = Field(min_length=2)
    liquid_density_kg_m3: list[Positive] = Field(min_length=2)
    characteristic_velocity_m_s: list[Positive] = Field(min_length=2)
    sample_valid: list[bool] = Field(min_length=2)
    property_provider_id: str = Field(min_length=1)
    property_provider_version: str = Field(min_length=1)
    property_state_digests: list[str] = Field(min_length=2)
    property_history_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    local_pressure_definition: str = Field(min_length=1)
    velocity_definition: str = Field(min_length=1)
    interpolation: Literal["linear"] = "linear"
    absolute_pressure_reviewed: bool
    thermodynamic_state_reviewed: bool

    @model_validator(mode="after")
    def aligned_history(self):
        count = len(self.sample_ids)
        vectors = (
            self.time_s,
            self.local_static_pressure_Pa,
            self.temperature_K,
            self.vapor_pressure_Pa,
            self.liquid_density_kg_m3,
            self.characteristic_velocity_m_s,
            self.sample_valid,
            self.property_state_digests,
        )
        if any(len(vector) != count for vector in vectors):
            raise ValueError("cavitation-history sample vectors must align")
        if len(set(self.sample_ids)) != count:
            raise ValueError("cavitation-history sample identifiers must be unique")
        if any(later <= earlier for earlier, later in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("cavitation-history time must be strictly increasing")
        if any(
            len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest)
            for digest in self.property_state_digests
        ):
            raise ValueError("each property-state digest must be lowercase SHA-256")
        return self


def _linear_nonpositive_interval(t0: float, t1: float, y0: float, y1: float):
    if y0 <= 0 and y1 <= 0:
        return t0, t1
    if y0 > 0 and y1 > 0:
        return None
    crossing = t0 + (t1 - t0) * y0 / (y0 - y1)
    return (t0, crossing) if y0 <= 0 else (crossing, t1)


def _linear_value(t: float, t0: float, t1: float, y0: float, y1: float) -> float:
    return y0 + (y1 - y0) * (t - t0) / (t1 - t0)


def cavitation_history(x: CavitationHistory) -> Calculation:
    if not x.absolute_pressure_reviewed or not x.thermodynamic_state_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Absolute local pressure and every liquid thermodynamic state require caller review.",),
        )
    if not all(x.sample_valid):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Invalid history samples cannot be filtered or interpolated silently.",),
        )
    margins = [
        pressure - vapor
        for pressure, vapor in zip(x.local_static_pressure_Pa, x.vapor_pressure_Pa, strict=True)
    ]
    dynamic_pressures = [
        0.5 * density * velocity**2
        for density, velocity in zip(x.liquid_density_kg_m3, x.characteristic_velocity_m_s, strict=True)
    ]
    numbers = [margin / dynamic for margin, dynamic in zip(margins, dynamic_pressures, strict=True)]
    intervals: list[list[float]] = []
    deficit_exposure = 0.0
    for index in range(len(x.time_s) - 1):
        t0, t1 = x.time_s[index], x.time_s[index + 1]
        y0, y1 = margins[index], margins[index + 1]
        interval = _linear_nonpositive_interval(t0, t1, y0, y1)
        if interval is None:
            continue
        start, end = interval
        start_margin = _linear_value(start, t0, t1, y0, y1)
        end_margin = _linear_value(end, t0, t1, y0, y1)
        deficit_exposure += -0.5 * (start_margin + end_margin) * (end - start)
        if intervals and math.isclose(intervals[-1][1], start, rel_tol=0.0, abs_tol=1e-12):
            intervals[-1][1] = end
        else:
            intervals.append([start, end])
    below_duration = sum(end - start for start, end in intervals)
    minimum_index = min(range(len(margins)), key=margins.__getitem__)
    return Calculation(
        values=dict(
            static_pressure_margin_Pa=margins,
            characteristic_dynamic_pressure_Pa=dynamic_pressures,
            local_cavitation_number=numbers,
            minimum_static_pressure_margin_Pa=margins[minimum_index],
            minimum_margin_sample_id=x.sample_ids[minimum_index],
            minimum_margin_time_s=x.time_s[minimum_index],
            thermodynamic_possible_intervals_s=intervals,
            total_thermodynamic_possible_duration_s=below_duration,
            observed_duration_s=x.time_s[-1] - x.time_s[0],
            thermodynamic_possible_time_fraction=below_duration / (x.time_s[-1] - x.time_s[0]),
            pressure_deficit_exposure_Pa_s=max(deficit_exposure, 0.0),
            any_thermodynamic_cavitation_possible=min(margins) <= 0,
        ),
        notes=(
            "Crossings and pressure-deficit exposure use piecewise-linear interpolation of the supplied samples.",
            "Duration and pressure deficit are screening descriptors, not bubble-collapse energy, erosion damage, life or failure probability.",
        ),
    )


def _cavitation_history_context(x: CavitationHistory, context: RunContext) -> None:
    if x.asset_id != context.asset_id or x.location_id != context.location_id:
        raise ValueError("cavitation-history asset and location must match the evaluation context")


class ThicknessGrid(Contract):
    cell_thickness_m: list[list[Positive | None]] = Field(min_length=1)
    cell_size_x_m: Positive
    cell_size_y_m: Positive
    reference_thickness_m: Positive
    reporting_threshold_m: Positive

    @model_validator(mode="after")
    def rectangular(self):
        lengths = {len(row) for row in self.cell_thickness_m}
        if len(lengths) != 1 or 0 in lengths:
            raise ValueError("a nonempty rectangular cell map is required")
        if not any(value is not None for row in self.cell_thickness_m for value in row):
            raise ValueError("at least one measured cell is required")
        return self


def thickness_grid(x: ThicknessGrid) -> Calculation:
    grid = x.cell_thickness_m
    rows, columns = len(grid), len(grid[0])
    observed = [v for row in grid for v in row if v is not None]
    marked = {
        (i, j)
        for i, row in enumerate(grid)
        for j, v in enumerate(row)
        if v is not None and v < x.reporting_threshold_m
    }
    counts = []
    while marked:
        stack = [marked.pop()]
        count = 0
        while stack:
            i, j = stack.pop()
            count += 1
            for neighbour in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if neighbour in marked:
                    marked.remove(neighbour)
                    stack.append(neighbour)
        counts.append(count)
    area = x.cell_size_x_m * x.cell_size_y_m
    return Calculation(
        values=dict(
            minimum_measured_thickness_m=min(observed),
            mean_measured_thickness_m=float(np.mean(observed)),
            observed_area_m2=len(observed) * area,
            missing_area_m2=(rows * columns - len(observed)) * area,
            observed_fraction=len(observed) / (rows * columns),
            net_measured_loss_volume_m3=sum(x.reference_thickness_m - v for v in observed) * area,
            connected_below_threshold_areas_m2=[n * area for n in sorted(counts, reverse=True)],
        ),
        notes=(
            "Cells represent equal areas; missing cells are not interpolated or counted as sound. Four-neighbour clusters describe measured geometry, not an FFS acceptance result.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "corrosion.stern_geary",
            SternGeary,
            stern_geary,
            {"stern_geary_coefficient_V": "V", "corrosion_current_density_A_m2": "A/m^2"},
            (
                "Small-signal polarization resistance is corrected for solution resistance and normalized by exposed area.",
            ),
            ("osti_polarization",),
            version="1.0.1",
        ),
        ModelSpec(
            "corrosion.galvanic_linear",
            GalvanicLinear,
            galvanic_linear,
            {
                "coupling_current_A": "A",
                "anodic_current_density_A_m2": "A/m^2",
                "cathodic_current_density_A_m2": "A/m^2",
                "anodic_overpotential_V": "V",
                "cathodic_overpotential_magnitude_V": "V",
            },
            (
                "Same potential reference, linear electrode polarization and an explicit validity bound; no mass-transport limitation.",
            ),
            ("linear_circuit_equilibrium",),
            version="1.0.1",
        ),
        ModelSpec(
            "transport.semi_infinite_diffusion",
            SemiInfiniteDiffusion,
            semi_infinite_diffusion,
            {
                "concentration_mol_m3": "mol/m^3",
                "surface_flux_mol_m2_s": "mol/m^2/s",
                "integrated_excess_mol_m2": "mol/m^2",
            },
            ("One-dimensional semi-infinite Fickian diffusion with a constant boundary concentration.",),
            ("cambridge_diffusion",),
        ),
        ModelSpec(
            "degradation.parabolic_oxidation",
            ParabolicOxidation,
            parabolic_oxidation,
            {"oxide_thickness_m": "m", "oxide_growth_m": "m"},
            (
                "Retained protective scale in one declared isothermal parabolic-growth regime; spallation excluded.",
            ),
            ("parabolic_kinetics",),
        ),
        ModelSpec(
            "degradation.archard_wear",
            ArchardWear,
            archard_wear,
            {"wear_volume_m3": "m^3", "mean_wear_depth_m": "m"},
            ("User-calibrated dimensionless wear coefficient, SI hardness and uniformly distributed loss.",),
            ("archard_relation",),
        ),
        ModelSpec(
            "degradation.cavitation_margin",
            CavitationMargin,
            cavitation_margin,
            {
                "static_pressure_margin_Pa": "Pa",
                "static_head_margin_m": "m",
                "characteristic_dynamic_pressure_Pa": "Pa",
                "local_cavitation_number": "1",
                "local_static_to_vapor_pressure_ratio": "1",
                "thermodynamic_cavitation_possible": "1",
            },
            (
                "Absolute local static pressure, equilibrium vapor pressure, liquid density and a caller-defined characteristic velocity; thermodynamic screening is separate from damage.",
            ),
            ("cavitation_margin_definition",),
        ),
        ModelSpec(
            "degradation.cavitation_history",
            CavitationHistory,
            cavitation_history,
            {
                "static_pressure_margin_Pa": "Pa",
                "characteristic_dynamic_pressure_Pa": "Pa",
                "local_cavitation_number": "1",
                "minimum_static_pressure_margin_Pa": "Pa",
                "minimum_margin_sample_id": "1",
                "minimum_margin_time_s": "s",
                "thermodynamic_possible_intervals_s": "s",
                "total_thermodynamic_possible_duration_s": "s",
                "observed_duration_s": "s",
                "thermodynamic_possible_time_fraction": "1",
                "pressure_deficit_exposure_Pa_s": "Pa*s",
                "any_thermodynamic_cavitation_possible": "1",
            },
            (
                "Aligned reviewed absolute local-pressure and equilibrium liquid-property samples with piecewise-linear crossings; duration and pressure deficit are not damage.",
            ),
            ("cavitation_history_definition",),
            context_validator=_cavitation_history_context,
        ),
        ModelSpec(
            "geometry.thickness_grid",
            ThicknessGrid,
            thickness_grid,
            {
                "minimum_measured_thickness_m": "m",
                "mean_measured_thickness_m": "m",
                "observed_area_m2": "m^2",
                "missing_area_m2": "m^2",
                "observed_fraction": "1",
                "net_measured_loss_volume_m3": "m^3",
                "connected_below_threshold_areas_m2": "m^2",
            },
            (
                "Equal-area cell observations with explicit missing coverage; reporting threshold is caller supplied.",
            ),
            ("discrete_geometry",),
        ),
    ]
