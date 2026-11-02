"""Classical elasticity calculations with explicit geometric boundaries."""

from __future__ import annotations

import math
from bisect import bisect_right
from fractions import Fraction as Rational
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec


class Cylinder(Contract):
    inner_radius_m: Positive
    outer_radius_m: Positive
    internal_pressure_Pa: Nonnegative
    external_pressure_Pa: Nonnegative
    evaluation_radius_m: Positive
    closed_ends: bool

    @model_validator(mode="after")
    def geometry(self):
        if not self.inner_radius_m < self.outer_radius_m:
            raise ValueError("positive annular thickness required")
        if not self.inner_radius_m <= self.evaluation_radius_m <= self.outer_radius_m:
            raise ValueError("evaluation point must lie inside cylinder wall")
        return self


def lame_cylinder(x: Cylinder) -> Calculation:
    a, b, r = x.inner_radius_m, x.outer_radius_m, x.evaluation_radius_m
    A = (x.internal_pressure_Pa * a * a - x.external_pressure_Pa * b * b) / (b * b - a * a)
    B = (x.internal_pressure_Pa - x.external_pressure_Pa) * a * a * b * b / (b * b - a * a)
    hoop, radial, axial = A + B / r**2, A - B / r**2, A if x.closed_ends else 0.0
    mises = math.sqrt(((hoop - radial) ** 2 + (radial - axial) ** 2 + (axial - hoop) ** 2) / 2)
    return Calculation(
        values=dict(hoop_stress_Pa=hoop, radial_stress_Pa=radial, axial_stress_Pa=axial, von_mises_Pa=mises)
    )


class ThinCylinder(Contract):
    pressure_difference_Pa: Nonnegative
    mean_radius_m: Positive
    wall_thickness_m: Positive
    allowable_hoop_stress_Pa: Positive


def thin_cylinder(x: ThinCylinder) -> Calculation:
    if x.wall_thickness_m / x.mean_radius_m > 0.1:
        return Calculation(
            status="out_of_scope", values={}, notes=("Use a thick-cylinder or numerical model.",)
        )
    hoop = x.pressure_difference_Pa * x.mean_radius_m / x.wall_thickness_m
    return Calculation(
        values=dict(
            hoop_stress_Pa=hoop,
            axial_stress_Pa=hoop / 2,
            allowable_pressure_difference_Pa=x.allowable_hoop_stress_Pa
            * x.wall_thickness_m
            / x.mean_radius_m,
            hoop_margin_Pa=x.allowable_hoop_stress_Pa - hoop,
        )
    )


class PlaneStress(Contract):
    stress_x_Pa: float
    stress_y_Pa: float
    shear_xy_Pa: float


def plane_stress(x: PlaneStress) -> Calculation:
    scale = max(abs(x.stress_x_Pa), abs(x.stress_y_Pa), abs(x.shear_xy_Pa))
    sx, sy, shear = (0.0, 0.0, 0.0) if scale == 0 else (x.stress_x_Pa/scale, x.stress_y_Pa/scale, x.shear_xy_Pa/scale)
    mean = sx/2 + sy/2
    radius = math.hypot(sx/2 - sy/2, shear)
    values = dict(principal_max_Pa=scale*(mean+radius), principal_min_Pa=scale*(mean-radius),
                  von_mises_Pa=scale*math.sqrt(sx*sx-sx*sy+sy*sy+3*shear*shear))
    if not all(math.isfinite(value) for value in values.values()):
        return Calculation(status="out_of_scope", values={"reason":"plane_stress_output_exceeds_finite_numeric_support"})
    return Calculation(values=values)


class ThermalRestraint(Contract):
    young_modulus_Pa: Positive
    expansion_coefficient_per_K: Nonnegative
    temperature_change_K: float
    restraint_fraction: float = Field(ge=0, le=1)


def thermal_restraint(x: ThermalRestraint) -> Calculation:
    strain = x.expansion_coefficient_per_K * x.temperature_change_K
    return Calculation(
        values=dict(
            free_thermal_strain=strain,
            restrained_uniaxial_stress_Pa=-x.restraint_fraction * x.young_modulus_Pa * strain,
        )
    )


class StressIntensity(Contract):
    crack_depth_m: Positive
    tensile_stress_Pa: Nonnegative
    geometry_factor: Positive
    fracture_toughness_Pa_sqrt_m: Positive


def stress_intensity(x: StressIntensity) -> Calculation:
    try:
        K = x.geometry_factor * x.tensile_stress_Pa * math.sqrt(math.pi * x.crack_depth_m)
        critical = (
            None
            if x.tensile_stress_Pa == 0
            else (x.fracture_toughness_Pa_sqrt_m / (x.geometry_factor * x.tensile_stress_Pa)) ** 2 / math.pi
        )
        margin = x.fracture_toughness_Pa_sqrt_m - K
        if not all(math.isfinite(value) for value in (K, margin)) or (
            critical is not None and not math.isfinite(critical)
        ):
            raise ArithmeticError("fracture result exceeds finite numeric support")
    except (ArithmeticError, OverflowError, ZeroDivisionError):
        return Calculation(status="out_of_scope", values={}, notes=("Required stress-intensity outputs exceed finite numeric support.",))
    return Calculation(
        values=dict(
            stress_intensity_Pa_sqrt_m=K,
            toughness_margin_Pa_sqrt_m=margin,
            critical_depth_m=critical,
        )
    )


class PressureTemperatureEnvelopeKnot(Contract):
    temperature_K: Positive
    allowable_pressure_Pa: Positive


class PressureTemperatureOperatingPoint(Contract):
    point_id: str = Field(min_length=1)
    temperature_K: Positive
    pressure_Pa: Nonnegative


class PressureTemperatureEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    applicability_basis: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    knots: list[PressureTemperatureEnvelopeKnot] = Field(min_length=2)
    operating_points: list[PressureTemperatureOperatingPoint] = Field(min_length=1)
    interpolation: Literal["piecewise_linear"] = "piecewise_linear"
    applicability_reviewed: bool
    operating_points_reviewed: bool

    @model_validator(mode="after")
    def ordered_unique_contract(self):
        temperatures = [knot.temperature_K for knot in self.knots]
        if any(right <= left for left, right in zip(temperatures, temperatures[1:], strict=False)):
            raise ValueError("envelope-knot temperatures must be strictly increasing")
        point_ids = [point.point_id for point in self.operating_points]
        if len(point_ids) != len(set(point_ids)):
            raise ValueError("operating-point identifiers must be unique")
        return self


def pressure_temperature_envelope(x: PressureTemperatureEnvelope) -> Calculation:
    if not x.applicability_reviewed or not x.operating_points_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Envelope applicability and operating-point identity require explicit review.",),
        )

    minimum_temperature = x.knots[0].temperature_K
    maximum_temperature = x.knots[-1].temperature_K
    outside = [
        point.point_id
        for point in x.operating_points
        if point.temperature_K < minimum_temperature or point.temperature_K > maximum_temperature
    ]
    if outside:
        return Calculation(
            status="out_of_scope",
            values={
                "outside_support_point_ids": outside,
                "support_temperature_min_K": minimum_temperature,
                "support_temperature_max_K": maximum_temperature,
            },
            notes=("Operating points outside the supplied temperature support are not extrapolated.",),
        )

    allowable_pressures: list[float] = []
    margins: list[float] = []
    utilizations: list[float] = []
    within: list[bool] = []
    knot_temperatures = [knot.temperature_K for knot in x.knots]
    for point in x.operating_points:
        knot_index = min(bisect_right(knot_temperatures, point.temperature_K) - 1, len(x.knots) - 2)
        left = x.knots[knot_index]
        right = x.knots[knot_index + 1]
        fraction = (Rational(point.temperature_K) - Rational(left.temperature_K)) / (
            Rational(right.temperature_K) - Rational(left.temperature_K)
        )
        allowable_exact = Rational(left.allowable_pressure_Pa) + fraction * (
            Rational(right.allowable_pressure_Pa) - Rational(left.allowable_pressure_Pa)
        )
        margin_exact = allowable_exact - Rational(point.pressure_Pa)
        utilization_exact = Rational(point.pressure_Pa) / allowable_exact
        try:
            converted = [float(value) for value in (allowable_exact, margin_exact, utilization_exact)]
            if any(not math.isfinite(value) for value in converted) or any(
                exact != 0 and value == 0
                for exact, value in zip((allowable_exact, margin_exact, utilization_exact), converted, strict=True)
            ):
                raise ArithmeticError
        except ArithmeticError:
            return Calculation(
                status="out_of_scope", values={"numeric_range_point_id": point.point_id},
                notes=("A derived envelope quantity is outside finite nonzero arithmetic support.",),
            )
        allowable, margin, utilization = converted
        allowable_pressures.append(allowable)
        margins.append(margin)
        utilizations.append(utilization)
        within.append(margin_exact >= 0)

    margin_index = min(range(len(margins)), key=margins.__getitem__)
    utilization_index = max(range(len(utilizations)), key=utilizations.__getitem__)
    point_ids = [point.point_id for point in x.operating_points]
    return Calculation(
        values={
            "point_ids": point_ids,
            "allowable_pressures_Pa": allowable_pressures,
            "pressure_margins_Pa": margins,
            "utilization_ratios": utilizations,
            "within_supplied_envelope": within,
            "all_within_supplied_envelope": all(within),
            "minimum_pressure_margin_Pa": margins[margin_index],
            "minimum_margin_point_id": point_ids[margin_index],
            "maximum_utilization_ratio": utilizations[utilization_index],
            "maximum_utilization_point_id": point_ids[utilization_index],
            "support_temperature_min_K": minimum_temperature,
            "support_temperature_max_K": maximum_temperature,
        },
        notes=(
            "Results compare reviewed points only with the caller-supplied curve; they are not code acceptance.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "mechanics.lame_cylinder",
            Cylinder,
            lame_cylinder,
            {"hoop_stress_Pa": "Pa", "radial_stress_Pa": "Pa", "axial_stress_Pa": "Pa", "von_mises_Pa": "Pa"},
            ("Long homogeneous isotropic linear-elastic cylinder; end effects and instability excluded.",),
            ("cambridge_lame",),
        ),
        ModelSpec(
            "mechanics.thin_cylinder",
            ThinCylinder,
            thin_cylinder,
            {
                "hoop_stress_Pa": "Pa",
                "axial_stress_Pa": "Pa",
                "allowable_pressure_difference_Pa": "Pa",
                "hoop_margin_Pa": "Pa",
            },
            ("Closed-end membrane approximation, t/r <= 0.1; user allowable is not an inferred code value.",),
            ("membrane_equilibrium",),
        ),
        ModelSpec(
            "mechanics.plane_stress",
            PlaneStress,
            plane_stress,
            {"principal_max_Pa": "Pa", "principal_min_Pa": "Pa", "von_mises_Pa": "Pa"},
            ("Two-dimensional Cauchy stress with zero out-of-plane normal/shear components.",),
            ("stress_invariants",),
        ),
        ModelSpec(
            "mechanics.thermal_restraint",
            ThermalRestraint,
            thermal_restraint,
            {"free_thermal_strain": "1", "restrained_uniaxial_stress_Pa": "Pa"},
            ("Uniform temperature change, uniaxial linear elasticity and constant properties.",),
            ("thermoelasticity",),
        ),
        ModelSpec(
            "fracture.stress_intensity",
            StressIntensity,
            stress_intensity,
            {
                "stress_intensity_Pa_sqrt_m": "Pa*m^0.5",
                "toughness_margin_Pa_sqrt_m": "Pa*m^0.5",
                "critical_depth_m": "m",
            },
            (
                "Mode-I LEFM and constant user geometry factor; plastic collapse and crack interaction excluded.",
            ),
            ("nasa_fracture_control",),
        ),
        ModelSpec(
            "structural.pressure_temperature_envelope",
            PressureTemperatureEnvelope,
            pressure_temperature_envelope,
            {
                "point_ids": "1",
                "allowable_pressures_Pa": "Pa",
                "pressure_margins_Pa": "Pa",
                "utilization_ratios": "1",
                "within_supplied_envelope": "1",
                "all_within_supplied_envelope": "1",
                "minimum_pressure_margin_Pa": "Pa",
                "minimum_margin_point_id": "1",
                "maximum_utilization_ratio": "1",
                "maximum_utilization_point_id": "1",
                "outside_support_point_ids": "1",
                "support_temperature_min_K": "K",
                "support_temperature_max_K": "K",
            },
            (
                "Caller-reviewed positive pressure limit at strictly increasing absolute-temperature knots; piecewise-linear interpolation is restricted to supplied support.",
                "No design-code table, load combination, transient reconstruction, uncertainty factor, extrapolation or acceptance decision is inferred.",
            ),
            ("user_supplied_pressure_temperature_envelope",),
            version="1.0.1",
        ),
    ]
