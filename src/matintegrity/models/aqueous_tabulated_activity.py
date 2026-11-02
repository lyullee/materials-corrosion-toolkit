"""Caller-tabulated activity coefficients coupled to aqueous mass action."""

from __future__ import annotations

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation


class AqueousActivityCoefficientPoint(Contract):
    ionic_strength_mol_kg: float = Field(ge=0)
    activity_coefficient: Positive
    source_id: str | None = Field(default=None, min_length=1)
    source_record_id: str | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def paired_source_identity(self):
        if (self.source_id is None) != (self.source_record_id is None):
            raise ValueError("activity table source_id and source_record_id must be supplied together")
        return self


class AqueousActivityCoefficientTemperatureSlice(Contract):
    temperature_K: Positive
    points: tuple[AqueousActivityCoefficientPoint, ...] = Field(min_length=2, max_length=1000)

    @model_validator(mode="after")
    def ordered_support(self):
        values = [row.ionic_strength_mol_kg for row in self.points]
        if values[0] != 0 or any(right <= left for left, right in zip(values[:-1], values[1:], strict=True)):
            raise ValueError("each temperature slice must start at zero ionic strength and strictly increase")
        return self


class AqueousSpeciesActivityCurve(Contract):
    species_id: str = Field(min_length=1)
    points: tuple[AqueousActivityCoefficientPoint, ...] = Field(default=(), max_length=1000)
    temperature_slices: tuple[AqueousActivityCoefficientTemperatureSlice, ...] = Field(default=(), max_length=100)

    @model_validator(mode="after")
    def ordered_support(self):
        if bool(self.points) == bool(self.temperature_slices):
            raise ValueError("provide either a fixed-temperature ionic-strength table or temperature slices")
        values = [row.ionic_strength_mol_kg for row in self.points]
        if values and (values[0] != 0 or any(right <= left for left, right in zip(values[:-1], values[1:], strict=True))):
            raise ValueError("activity tables must start at zero ionic strength and strictly increase")
        temperatures = [row.temperature_K for row in self.temperature_slices]
        if temperatures and (
            len(temperatures) < 2
            or any(right <= left for left, right in zip(temperatures[:-1], temperatures[1:], strict=True))
        ):
            raise ValueError("temperature slices must contain at least two strictly increasing temperatures")
        return self


class AqueousTabulatedActivityIteration(Contract):
    schema_version: Literal["matintegrity.aqueous_tabulated_activity_iteration.v1"] = "matintegrity.aqueous_tabulated_activity_iteration.v1"
    system: AqueousMassActionSystem
    activity_table_temperature_K: Positive
    water_mass_per_solution_volume_kg_L: Positive
    species_activity_curves: tuple[AqueousSpeciesActivityCurve, ...] = Field(min_length=2, max_length=100)
    activity_table_provider_id: str = Field(min_length=1)
    activity_table_provider_revision: str = Field(min_length=1)
    activity_table_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    activity_table_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    interpolation_method: Literal["piecewise_linear", "shape_preserving_pchip"] = "piecewise_linear"
    interpolation_method_reviewed: bool = False
    ionic_strength_limit_mol_kg: Positive
    charge_balance_tolerance_mol_kg: Positive
    maximum_outer_iterations: int = Field(default=100, ge=1, le=1000)
    log_gamma_tolerance: Positive = Field(default=1e-9, le=1e-3)
    damping_fraction: Positive = Field(default=0.5, le=1.0)
    temperature_solvent_and_table_condition_reviewed: bool
    water_mass_conversion_reviewed: bool
    table_species_and_standard_state_mapping_reviewed: bool
    complete_inventory_and_charge_scope_reviewed: bool
    fixed_point_solver_settings_reviewed: bool
    single_liquid_no_precipitation_scope_reviewed: bool
    maximum_activity_table_points: int = Field(default=250_000, ge=1, le=10_000_000)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def table_coverage_and_species_alignment(self):
        if self.activity_table_temperature_K != self.system.temperature_K:
            raise ValueError("activity-table temperature must exactly match the aqueous system temperature")
        if self.interpolation_method == "shape_preserving_pchip" and not self.interpolation_method_reviewed:
            raise ValueError("shape-preserving PCHIP interpolation requires explicit caller review")
        if self.interpolation_method == "piecewise_linear" and self.interpolation_method_reviewed:
            raise ValueError("interpolation-method review flag is reserved for the optional PCHIP method")
        ids = [curve.species_id for curve in self.species_activity_curves]
        system_ids = [species.species_id for species in self.system.species]
        if len(ids) != len(set(ids)) or set(ids) != set(system_ids):
            raise ValueError("activity tables must cover every aqueous species exactly once")
        by_id = {curve.species_id: curve for curve in self.species_activity_curves}
        table_modes = {"temperature_slices" if curve.temperature_slices else "fixed" for curve in self.species_activity_curves}
        if len(table_modes) != 1:
            raise ValueError("all species must use the same fixed-temperature or temperature-sliced table mode")
        table_point_count = sum(
            len(curve.points) if curve.points else sum(len(row.points) for row in curve.temperature_slices)
            for curve in self.species_activity_curves
        )
        if table_point_count > self.maximum_activity_table_points:
            raise ValueError("activity table exceeds the declared point-count budget")
        all_points = (
            point
            for curve in self.species_activity_curves
            for point in (
                curve.points
                if curve.points
                else tuple(point for temperature_slice in curve.temperature_slices for point in temperature_slice.points)
            )
        )
        row_level_source_required = any(item.origin in {"measured", "open_dataset"} for item in self.evidence)
        evidence_by_id = {item.source_id: item for item in self.evidence}
        if len(evidence_by_id) != len(self.evidence):
            raise ValueError("activity table Evidence.source_id values must be unique")
        points = tuple(all_points)
        for point in points:
            if point.source_id is not None and point.source_id not in evidence_by_id:
                raise ValueError("activity table point source_id must match a declared Evidence.source_id")
            if row_level_source_required and point.source_id is not None and evidence_by_id[point.source_id].origin not in {
                "measured", "open_dataset"
            }:
                raise ValueError("measured/open-dataset activity knots must link to measured or open-dataset evidence")
        if row_level_source_required and any(
            not point.source_id or not point.source_record_id or point.source_id not in evidence_by_id
            for point in points
        ):
            raise ValueError("measured/open-dataset activity knots must link source_id and source_record_id to declared evidence")
        if any(item.origin == "open_dataset" and not (item.license_id and item.license_id.strip()) for item in self.evidence):
            raise ValueError("open-dataset activity evidence must declare its license or reuse policy")
        for species_id in system_ids:
            curve = by_id[species_id]
            if curve.points:
                if curve.points[-1].ionic_strength_mol_kg < self.ionic_strength_limit_mol_kg:
                    raise ValueError("each activity table must cover the requested ionic-strength limit")
            else:
                temperatures = [row.temperature_K for row in curve.temperature_slices]
                if temperatures[0] > self.system.temperature_K or temperatures[-1] < self.system.temperature_K:
                    raise ValueError("activity temperature slices must cover system temperature without extrapolation")
                if any(row.points[-1].ionic_strength_mol_kg < self.ionic_strength_limit_mol_kg for row in curve.temperature_slices):
                    raise ValueError("every temperature slice must cover the requested ionic-strength limit")
        if self.system.activity_standard_state != "molarity_1_mol_L":
            raise ValueError("tabulated coefficient coupling currently requires the molarity 1 mol/L standard state")
        return self


def _interpolate_ionic_log_gamma(points, ionic_strength: float) -> float:
    knots = [row.ionic_strength_mol_kg for row in points]
    if not math.isfinite(ionic_strength) or ionic_strength < knots[0] or ionic_strength > knots[-1]:
        raise ValueError("ionic strength is outside caller activity table support")
    index = min(max(int(np.searchsorted(knots, ionic_strength, side="right") - 1), 0), len(knots) - 2)
    left, right = points[index], points[index + 1]
    fraction = (ionic_strength - left.ionic_strength_mol_kg) / (right.ionic_strength_mol_kg - left.ionic_strength_mol_kg)
    return math.log(left.activity_coefficient) + fraction * (
        math.log(right.activity_coefficient) - math.log(left.activity_coefficient)
    )


def _pchip_value(knots: list[float], values: list[float], query: float) -> float:
    """Evaluate SciPy's shape-preserving cubic Hermite interpolant in support."""
    x = np.asarray(knots, dtype=float)
    y = np.asarray(values, dtype=float)
    if x.ndim != 1 or y.shape != x.shape or len(x) < 2 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("PCHIP requires aligned finite one-dimensional knot arrays")
    if not math.isfinite(query) or query < x[0] or query > x[-1]:
        raise ValueError("query is outside caller PCHIP support")
    if np.any(np.diff(x) <= 0):
        raise ValueError("PCHIP knots must be strictly increasing")
    try:
        from scipy.interpolate import PchipInterpolator
    except ImportError as error:
        raise ValueError("PCHIP interpolation requires the optional 'science' dependencies; install matintegrity[science]") from error
    result = PchipInterpolator(x, y, extrapolate=False)(query)
    if not math.isfinite(float(result)):
        raise ArithmeticError("PCHIP interpolation exceeded finite support")
    return float(result)


def _interpolate_ionic_log_gamma_with_method(points, ionic_strength: float, method: str) -> float:
    if method == "piecewise_linear":
        return _interpolate_ionic_log_gamma(points, ionic_strength)
    knots = [row.ionic_strength_mol_kg for row in points]
    values = [math.log(row.activity_coefficient) for row in points]
    return _pchip_value(knots, values, ionic_strength)


def _interpolate_log_gamma(
    curve: AqueousSpeciesActivityCurve,
    ionic_strength: float,
    temperature_K: float,
    method: str = "piecewise_linear",
) -> float:
    if curve.points:
        return _interpolate_ionic_log_gamma_with_method(curve.points, ionic_strength, method)
    slices = curve.temperature_slices
    temperatures = [row.temperature_K for row in slices]
    if not math.isfinite(temperature_K) or temperature_K < temperatures[0] or temperature_K > temperatures[-1]:
        raise ValueError("temperature is outside caller activity table support")
    index = min(max(int(np.searchsorted(temperatures, temperature_K, side="right") - 1), 0), len(slices) - 2)
    left, right = slices[index], slices[index + 1]
    left_log_gamma = _interpolate_ionic_log_gamma_with_method(left.points, ionic_strength, method)
    right_log_gamma = _interpolate_ionic_log_gamma_with_method(right.points, ionic_strength, method)
    if method == "piecewise_linear":
        fraction = (temperature_K - left.temperature_K) / (right.temperature_K - left.temperature_K)
        return left_log_gamma + fraction * (right_log_gamma - left_log_gamma)
    return _pchip_value(
        temperatures,
        [
            _interpolate_ionic_log_gamma_with_method(row.points, ionic_strength, method)
            for row in slices
        ],
        temperature_K,
    )


def _activity_table_lineage(request: AqueousTabulatedActivityIteration) -> dict[str, str]:
    table_records = []
    source_records = []
    for curve in request.species_activity_curves:
        if curve.points:
            rows = ((None, point) for point in curve.points)
        else:
            rows = (
                (temperature_slice.temperature_K, point)
                for temperature_slice in curve.temperature_slices
                for point in temperature_slice.points
            )
        for temperature_K, point in rows:
            table_records.append({
                "species_id": curve.species_id,
                "temperature_K": temperature_K,
                "ionic_strength_mol_kg": point.ionic_strength_mol_kg,
                "activity_coefficient": point.activity_coefficient,
                "source_id": point.source_id,
                "source_record_id": point.source_record_id,
            })
            source_records.append({
                "species_id": curve.species_id,
                "temperature_K": temperature_K,
                "ionic_strength_mol_kg": point.ionic_strength_mol_kg,
                "source_id": point.source_id,
                "source_record_id": point.source_record_id,
            })
    evidence_records = [item.model_dump(mode="json") for item in request.evidence]
    return {
        "normalized_activity_table_sha256": canonical_digest(table_records),
        "activity_table_source_record_lineage_sha256": canonical_digest(source_records),
        "activity_table_evidence_sha256": canonical_digest(evidence_records),
    }


def build_tabulated_activity_transport_callback(
    request: AqueousTabulatedActivityIteration,
    *,
    transport_species_ids: tuple[str, ...],
    temperature_K: float,
):
    """Build a digest-pinned activity callback for restricted transport.

    The transport callback receives mol/m3 concentrations at the mouth and
    every cell. It returns gamma at each location by converting to molality
    with the request's declared water-mass factor, calculating ionic strength,
    and interpolating the same caller table used by the speciation API.
    """
    expected_species = tuple(row.species_id for row in request.system.species)
    if tuple(transport_species_ids) != expected_species:
        raise ValueError("transport species order must exactly match the aqueous activity system")
    if temperature_K != request.system.temperature_K:
        raise ValueError("transport temperature must match the reviewed aqueous activity-system temperature")
    if len(set(transport_species_ids)) != len(transport_species_ids):
        raise ValueError("transport species identifiers must be unique")

    charges = np.asarray([row.charge_number for row in request.system.species], dtype=float)
    curves = {row.species_id: row for row in request.species_activity_curves}
    point_limit = request.ionic_strength_limit_mol_kg
    water_mass = request.water_mass_per_solution_volume_kg_L
    temperature = float(temperature_K)
    table_lineage = _activity_table_lineage(request)

    def activity_coefficients(time_s: float, concentration_mol_m3: np.ndarray) -> np.ndarray:
        del time_s  # The supplied table has no independent time coordinate.
        concentrations = np.asarray(concentration_mol_m3, dtype=float)
        if concentrations.ndim != 2 or concentrations.shape[0] != len(transport_species_ids):
            raise ValueError("activity callback expects species by mouth-plus-cell concentration values")
        if not np.isfinite(concentrations).all() or np.any(concentrations < 0):
            raise ValueError("activity callback concentrations must be finite and nonnegative")
        molality = concentrations / 1000.0 / water_mass
        ionic_strength = 0.5 * np.sum(np.square(charges)[:, None] * molality, axis=0)
        if not np.isfinite(ionic_strength).all() or np.any(ionic_strength > point_limit):
            raise ValueError("transport ionic strength exceeds the declared activity-table limit")
        output = np.empty_like(concentrations, dtype=float)
        for species_index, species_id in enumerate(transport_species_ids):
            curve = curves[species_id]
            output[species_index] = [
                math.exp(_interpolate_log_gamma(curve, float(value), temperature, request.interpolation_method))
                for value in ionic_strength
            ]
        if not np.isfinite(output).all() or np.any(output <= 0):
            raise ValueError("interpolated activity coefficients exceed finite positive support")
        return output

    activity_coefficients.provider_id = request.activity_table_provider_id
    activity_coefficients.provider_revision = request.activity_table_provider_revision
    activity_coefficients.configuration_sha256 = request.activity_table_configuration_digest
    activity_coefficients.record_sha256 = request.activity_table_record_digest
    activity_coefficients.temperature_K = temperature
    activity_coefficients.species_ids = tuple(transport_species_ids)
    activity_coefficients.source_request_sha256 = canonical_digest(request.model_dump(mode="json"))
    activity_coefficients.normalized_activity_table_sha256 = table_lineage["normalized_activity_table_sha256"]
    activity_coefficients.activity_table_source_record_lineage_sha256 = table_lineage["activity_table_source_record_lineage_sha256"]
    activity_coefficients.activity_table_evidence_sha256 = table_lineage["activity_table_evidence_sha256"]
    activity_coefficients.interpolation_method = request.interpolation_method
    return activity_coefficients


def aqueous_tabulated_activity_self_consistent_speciation(x: AqueousTabulatedActivityIteration) -> Calculation:
    """Iterate a caller's finite activity tables against speciation-derived ionic strength."""
    system = x.system
    digest = canonical_digest(x.model_dump(mode="json"))
    curves = {curve.species_id: curve for curve in x.species_activity_curves}
    species = system.species
    charges = np.asarray([row.charge_number for row in species], dtype=float)
    gamma = np.asarray([row.activity_coefficient for row in species], dtype=float)
    base = {
        "assessment_id": system.assessment_id,
        "solution_id": system.solution_id,
        "temperature_K": system.temperature_K,
        "activity_table_temperature_K": x.activity_table_temperature_K,
        "activity_table_temperature_support_K_by_species": {
            curve.species_id: (
                [curve.temperature_slices[0].temperature_K, curve.temperature_slices[-1].temperature_K]
                if curve.temperature_slices
                else [x.activity_table_temperature_K, x.activity_table_temperature_K]
            )
            for curve in x.species_activity_curves
        },
        "activity_table_support_by_species": {
            curve.species_id: {
                "mode": "temperature_slices" if curve.temperature_slices else "fixed_temperature",
                "temperature_slices": (
                    [
                        {
                            "temperature_K": temperature_slice.temperature_K,
                            "ionic_strength_min_mol_kg": temperature_slice.points[0].ionic_strength_mol_kg,
                            "ionic_strength_max_mol_kg": temperature_slice.points[-1].ionic_strength_mol_kg,
                            "ionic_strength_point_count": len(temperature_slice.points),
                            "source_record_id_count": sum(point.source_record_id is not None for point in temperature_slice.points),
                            "source_record_ids_sha256": canonical_digest([point.source_record_id for point in temperature_slice.points]),
                        }
                        for temperature_slice in curve.temperature_slices
                    ]
                    if curve.temperature_slices
                    else [{
                        "temperature_K": x.activity_table_temperature_K,
                        "ionic_strength_min_mol_kg": curve.points[0].ionic_strength_mol_kg,
                        "ionic_strength_max_mol_kg": curve.points[-1].ionic_strength_mol_kg,
                        "ionic_strength_point_count": len(curve.points),
                        "source_record_id_count": sum(point.source_record_id is not None for point in curve.points),
                        "source_record_ids_sha256": canonical_digest([point.source_record_id for point in curve.points]),
                    }]
                ),
            }
            for curve in x.species_activity_curves
        },
        "input_digest": digest,
        **_activity_table_lineage(x),
        "water_mass_per_solution_volume_kg_L": x.water_mass_per_solution_volume_kg_L,
        "activity_table_provider_id": x.activity_table_provider_id,
        "activity_table_provider_revision": x.activity_table_provider_revision,
        "activity_table_evidence": [item.model_dump(mode="json") for item in x.evidence],
        "activity_table_configuration_digest": x.activity_table_configuration_digest,
        "activity_table_record_digest": x.activity_table_record_digest,
        "ionic_strength_limit_mol_kg": x.ionic_strength_limit_mol_kg,
        "activity_table_point_count": sum(
            len(curve.points) if curve.points else sum(len(row.points) for row in curve.temperature_slices)
            for curve in x.species_activity_curves
        ),
        "maximum_activity_table_points": x.maximum_activity_table_points,
        "activity_table_interpolation_method": x.interpolation_method,
        "activity_table_interpolation_method_reviewed": x.interpolation_method_reviewed,
    }
    reviews = {
        "temperature_solvent_and_table_condition_reviewed": x.temperature_solvent_and_table_condition_reviewed,
        "water_mass_conversion_reviewed": x.water_mass_conversion_reviewed,
        "table_species_and_standard_state_mapping_reviewed": x.table_species_and_standard_state_mapping_reviewed,
        "complete_inventory_and_charge_scope_reviewed": x.complete_inventory_and_charge_scope_reviewed,
        "fixed_point_solver_settings_reviewed": x.fixed_point_solver_settings_reviewed,
        "single_liquid_no_precipitation_scope_reviewed": x.single_liquid_no_precipitation_scope_reviewed,
    }
    missing = [name for name, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "outer_iterations": 0})
    history: list[dict] = []
    last_solution = None
    try:
        for iteration in range(1, x.maximum_outer_iterations + 1):
            iteration_system = system.model_copy(update={
                "species": tuple(row.model_copy(update={"activity_coefficient": float(gamma[i])}) for i, row in enumerate(species)),
                "activity_provider_id": x.activity_table_provider_id,
                "activity_provider_revision": x.activity_table_provider_revision,
                "activity_configuration_digest": x.activity_table_configuration_digest,
                "activity_record_digest": x.activity_table_record_digest,
            })
            solved = aqueous_mass_action_speciation(iteration_system)
            last_solution = solved
            if solved.status != "computed":
                return Calculation(status=solved.status, values=base | {
                    "outer_iterations": iteration, "fixed_point_history": history,
                    "inner_solver_status": solved.status, "inner_solver_values": solved.values,
                }, notes=("The fixed-activity mass-action subproblem did not converge; no outer fixed-point result is promoted.", *solved.notes))
            concentration = np.asarray([row["concentration_mol_L"] for row in solved.values["species"]], dtype=float)
            molality = concentration / x.water_mass_per_solution_volume_kg_L
            ionic_strength = 0.5 * float(np.dot(molality, np.square(charges)))
            charge_residual = float(np.dot(molality, charges))
            if not math.isfinite(ionic_strength) or ionic_strength > x.ionic_strength_limit_mol_kg:
                return Calculation(status="out_of_scope", values=base | {
                    "outer_iterations": iteration, "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "out_of_scope_reason": "ionic_strength_exceeds_caller_table_limit",
                    "fixed_point_history": history,
                }, notes=("The speciation-derived ionic strength exceeds the explicitly declared table limit; no extrapolation or replacement model is used.",))
            if not math.isfinite(charge_residual) or abs(charge_residual) > x.charge_balance_tolerance_mol_kg:
                return Calculation(status="needs_data", values=base | {
                    "outer_iterations": iteration, "ionic_strength_mol_kg": ionic_strength,
                    "charge_balance_residual_mol_kg": charge_residual,
                    "out_of_scope_reason": "speciation_charge_balance_tolerance_exceeded",
                    "fixed_point_history": history,
                })
            target_log_gamma = np.asarray([
                _interpolate_log_gamma(curves[row.species_id], ionic_strength, system.temperature_K, x.interpolation_method)
                for row in species
            ], dtype=float)
            log_residual = float(np.max(np.abs(target_log_gamma - np.log(gamma))))
            history.append({
                "iteration": iteration,
                "ionic_strength_mol_kg": ionic_strength,
                "charge_balance_residual_mol_kg": charge_residual,
                "maximum_log_gamma_fixed_point_residual": log_residual,
                "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
            })
            if not math.isfinite(log_residual):
                raise ArithmeticError("activity table fixed-point residual is not finite")
            if log_residual <= x.log_gamma_tolerance:
                result_species = []
                for i, row in enumerate(solved.values["species"]):
                    result_species.append({
                        **row,
                        "molality_mol_kg": float(molality[i]),
                        "ionic_strength_contribution_mol_kg": float(0.5 * molality[i] * charges[i] ** 2),
                        "table_target_activity_coefficient": float(math.exp(target_log_gamma[i])),
                        "activity_coefficient_fixed_point_residual_ln": float(target_log_gamma[i] - math.log(gamma[i])),
                    })
                return Calculation(values=base | {
                    "outer_iterations": iteration,
                    "ionic_strength_mol_kg": ionic_strength,
                    "activity_table_evaluation_point": {
                        "temperature_K": system.temperature_K,
                        "ionic_strength_mol_kg": ionic_strength,
                    },
                    "charge_balance_residual_mol_kg": charge_residual,
                    "maximum_log_gamma_fixed_point_residual": log_residual,
                    "fixed_point_history": history,
                    "species": result_species,
                    "constraint_closure": solved.values["constraint_closure"],
                    "reaction_closure": solved.values["reaction_closure"],
                    "inner_normalized_residual_norm": solved.values["normalized_residual_norm"],
                    "converged": True,
                    "activity_table_interpolation": (
                        f"{x.interpolation_method}_in_temperature_and_ionic_strength_for_ln_gamma_without_extrapolation"
                        if any(curve.temperature_slices for curve in x.species_activity_curves)
                        else f"{x.interpolation_method}_in_ionic_strength_for_ln_gamma_without_extrapolation"
                    ),
                    "activity_standard_state": "dimensionless_molarity_1_mol_L; ionic-strength basis mol/kg water via caller water-mass conversion",
                    "aqueous_liquid_only": True,
                }, notes=(
                    "A damped fixed-point iteration couples caller-defined single-liquid mass-action speciation to species-specific tabulated activity coefficients using the declared in-support interpolation method in ionic strength and, when supplied, temperature.",
                    "Tables, species mapping, temperature/solvent applicability, water-mass conversion, reaction constants and constraints remain caller-supplied. This interpolation is not an independently validated electrolyte model and adds no gas/solid phase, precipitation, scale kinetics or corrosion rate.",
                ))
            gamma = np.exp(np.log(gamma) + x.damping_fraction * (target_log_gamma - np.log(gamma)))
            if np.any(~np.isfinite(gamma)) or np.any(gamma <= 0):
                raise ArithmeticError("damped activity-table update is not finite and positive")
    except (ArithmeticError, FloatingPointError, OverflowError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "outer_iterations": len(history),
            "out_of_scope_reason": str(error),
            "fixed_point_history": history,
            "inner_solver_status": last_solution.status if last_solution is not None else None,
        }, notes=("The caller table iteration encountered an unsupported or nonfinite state; no last iterate is promoted as equilibrium.",))
    return Calculation(status="out_of_scope", values=base | {
        "outer_iterations": len(history),
        "out_of_scope_reason": "activity_table_fixed_point_not_converged",
        "maximum_log_gamma_fixed_point_residual": history[-1]["maximum_log_gamma_fixed_point_residual"] if history else None,
        "fixed_point_history": history,
        "inner_solver_status": last_solution.status if last_solution is not None else None,
    }, notes=("The caller iteration budget ended before the declared log-coefficient tolerance was met; no unconverged speciation is returned.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "chemistry.aqueous_tabulated_activity_speciation",
        AqueousTabulatedActivityIteration,
        aqueous_tabulated_activity_self_consistent_speciation,
        {
            "temperature_K": "K", "activity_table_temperature_K": "K", "ionic_strength_mol_kg": "mol/kg",
            "charge_balance_residual_mol_kg": "mol/kg",
            "species.activity_coefficient": "1", "species.dimensionless_activity": "1",
            "species.concentration_mol_L": "mol/L", "species.molality_mol_kg": "mol/kg",
            "species.ionic_strength_contribution_mol_kg": "mol/kg",
            "species.table_target_activity_coefficient": "1",
            "species.activity_coefficient_fixed_point_residual_ln": "1",
            "maximum_log_gamma_fixed_point_residual": "1",
            "activity_table_point_count": "1", "maximum_activity_table_points": "1",
            "inner_normalized_residual_norm": "1", "outer_iterations": "1",
        },
        (
            "Caller-defined single-liquid mass-action equations are iterated with species-specific caller activity tables using bounded piecewise-linear interpolation of ln(gamma) in ionic strength and, when supplied, temperature.",
            "No extrapolation, table fitting, solvent transfer, alternative phase, precipitation kinetics or model qualification is inferred.",
        ),
        ("caller_tabulated_aqueous_activity_coefficients",),
    )]
