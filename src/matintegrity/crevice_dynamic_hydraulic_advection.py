"""Trial-state hydraulic momentum and upwind advection for moving crevice cells."""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Evidence, Positive, canonical_digest
from .crevice_aqueous_component_ledger import ConservedAqueousComponent

SOURCE_ID = "caller_reviewed_dynamic_slit_pressure_and_boundary_composition_schedule"


class CreviceDynamicHydraulicAdvection(Contract):
    """Caller pressure and reservoir histories used with trial-state BDF geometry."""

    schema_version: str = "matintegrity.crevice_dynamic_hydraulic_advection.v1"
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    time_s: tuple[float, ...] = Field(min_length=2, max_length=500)
    cell_ids: tuple[str, ...] = Field(min_length=2, max_length=300)
    species_order: tuple[str, ...] = Field(min_length=2, max_length=100)
    species_charge_numbers: tuple[int, ...] = Field(min_length=2, max_length=100)
    species_elemental_composition: dict[str, dict[str, float]]
    signed_pressure_drop_Pa_by_knot: tuple[float, ...] = Field(min_length=2, max_length=500)
    left_boundary_species_concentration_mol_m3_by_knot: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    right_boundary_species_concentration_mol_m3_by_knot: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=500)
    transverse_width_m: Positive
    density_kg_m3: Positive
    dynamic_viscosity_Pa_s: Positive
    resistance_correction_multiplier: Positive = 1.0
    inertance_correction_multiplier: Positive = 1.0
    maximum_reviewed_reynolds_number: Positive = Field(default=1000.0, ge=1.0, le=1000.0)
    minimum_width_to_aperture_ratio: Positive = Field(default=20.0, ge=20.0, le=1000.0)
    maximum_abs_flow_m3_s: Positive
    initial_signed_volumetric_flow_m3_s: float
    schedule_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=128)
    pressure_and_boundary_schedule_reviewed: bool
    geometry_pressure_and_dynamic_volume_balance_reviewed: bool
    boundary_electroneutrality_reviewed: bool
    incompressible_newtonian_laminar_slit_scope_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_dynamic_schedule(self):
        if len(set(self.cell_ids)) != len(self.cell_ids) or len(set(self.species_order)) != len(self.species_order):
            raise ValueError("dynamic hydraulic cell and species identities must be unique and ordered")
        if len(self.species_order) != len(self.species_charge_numbers):
            raise ValueError("dynamic hydraulic charge numbers must match species order")
        if len(self.time_s) != len(self.signed_pressure_drop_Pa_by_knot):
            raise ValueError("pressure history must match the exact BDF time grid")
        if any(not math.isfinite(value) for value in self.time_s + self.signed_pressure_drop_Pa_by_knot):
            raise ValueError("dynamic hydraulic clock and pressure must be finite")
        if any(b <= a for a, b in zip(self.time_s, self.time_s[1:])):
            raise ValueError("dynamic hydraulic clock must be strictly increasing")
        for side in (self.left_boundary_species_concentration_mol_m3_by_knot,
                     self.right_boundary_species_concentration_mol_m3_by_knot):
            if len(side) != len(self.time_s) or any(len(row) != len(self.species_order) for row in side):
                raise ValueError("both reservoir compositions must cover each BDF knot and ordered species")
            for row in side:
                if any(not math.isfinite(value) or value < 0.0 for value in row):
                    raise ValueError("reservoir concentrations must be finite and nonnegative")
                charge = math.fsum(z * c for z, c in zip(self.species_charge_numbers, row, strict=True))
                scale = max(1.0, math.fsum(abs(z * c) for z, c in zip(self.species_charge_numbers, row, strict=True)))
                if abs(charge) > 1e-10 * scale:
                    raise ValueError("each reservoir composition must be electroneutral")
        if set(self.species_elemental_composition) != set(self.species_order):
            raise ValueError("elemental composition must cover every species exactly")
        for formula in self.species_elemental_composition.values():
            if any(not key or not math.isfinite(value) or value < 0.0 for key, value in formula.items()):
                raise ValueError("species elemental coefficients must be named, finite and nonnegative")
        if not math.isfinite(self.initial_signed_volumetric_flow_m3_s):
            raise ValueError("initial flow must be finite")
        if abs(self.initial_signed_volumetric_flow_m3_s) > self.maximum_abs_flow_m3_s:
            raise ValueError("initial flow exceeds the caller-declared bound")
        payload = {
            "assessment_id": self.assessment_id,
            "physical_scope_id": self.physical_scope_id,
            "time_s": list(self.time_s),
            "cell_ids": list(self.cell_ids),
            "species_order": list(self.species_order),
            "species_charge_numbers": list(self.species_charge_numbers),
            "species_elemental_composition": self.species_elemental_composition,
            "signed_pressure_drop_Pa_by_knot": list(self.signed_pressure_drop_Pa_by_knot),
            "left_boundary_species_concentration_mol_m3_by_knot": [list(row) for row in self.left_boundary_species_concentration_mol_m3_by_knot],
            "right_boundary_species_concentration_mol_m3_by_knot": [list(row) for row in self.right_boundary_species_concentration_mol_m3_by_knot],
            "transverse_width_m": float(self.transverse_width_m),
            "density_kg_m3": float(self.density_kg_m3),
            "dynamic_viscosity_Pa_s": float(self.dynamic_viscosity_Pa_s),
            "resistance_correction_multiplier": float(self.resistance_correction_multiplier),
            "inertance_correction_multiplier": float(self.inertance_correction_multiplier),
            "maximum_reviewed_reynolds_number": float(self.maximum_reviewed_reynolds_number),
            "minimum_width_to_aperture_ratio": float(self.minimum_width_to_aperture_ratio),
            "maximum_abs_flow_m3_s": float(self.maximum_abs_flow_m3_s),
            "initial_signed_volumetric_flow_m3_s": float(self.initial_signed_volumetric_flow_m3_s),
        }
        if self.schedule_sha256 != canonical_digest(payload) or not any(
            row.source_id == SOURCE_ID and row.sha256 == self.schedule_sha256 and row.license_id
            for row in self.evidence
        ):
            raise ValueError("pressure, fluid, boundary and scope data require exact licensed Evidence")
        if not all((self.pressure_and_boundary_schedule_reviewed,
                    self.geometry_pressure_and_dynamic_volume_balance_reviewed,
                    self.boundary_electroneutrality_reviewed,
                    self.incompressible_newtonian_laminar_slit_scope_reviewed,
                    self.computational_use_authorized)):
            raise ValueError("dynamic hydraulic, reservoir, applicability and use reviews are required")
        return self


def _interpolate(schedule: Sequence[Sequence[float]] | Sequence[float], time_s: float,
                 knots: Sequence[float]) -> np.ndarray | float:
    if time_s < knots[0] or time_s > knots[-1]:
        raise ValueError("BDF stage time lies outside dynamic hydraulic schedule")
    if time_s == knots[-1]:
        return np.asarray(schedule[-1], dtype=float) if isinstance(schedule[-1], (list, tuple)) else float(schedule[-1])
    index = max(0, int(np.searchsorted(knots, time_s, side="right") - 1))
    fraction = (time_s - knots[index]) / (knots[index + 1] - knots[index])
    left, right = schedule[index], schedule[index + 1]
    if isinstance(left, (list, tuple)):
        return np.asarray(left, dtype=float) + fraction * (np.asarray(right, dtype=float) - np.asarray(left, dtype=float))
    return float(left) + fraction * (float(right) - float(left))


def evaluate_dynamic_hydraulic_advection_stage(
    binding: CreviceDynamicHydraulicAdvection,
    *,
    time_s: float,
    inlet_flow_m3_s: float,
    cell_lengths_m: Sequence[float],
    aperture_by_cell_m: Sequence[float],
    liquid_volume_rate_m3_s_by_cell: Sequence[float],
    concentration_mol_m3_by_cell_and_species: Sequence[Sequence[float]],
    components: Sequence[ConservedAqueousComponent],
) -> dict:
    """Calculate same-trial face flow, pressure RHS, advection and reservoir rates."""
    ncell, nspecies = len(binding.cell_ids), len(binding.species_order)
    lengths = np.asarray(cell_lengths_m, dtype=float)
    gaps = np.asarray(aperture_by_cell_m, dtype=float)
    volume_rates = np.asarray(liquid_volume_rate_m3_s_by_cell, dtype=float)
    concentrations = np.asarray(concentration_mol_m3_by_cell_and_species, dtype=float)
    if any(a.shape != (ncell,) for a in (lengths, gaps, volume_rates)):
        raise ValueError("dynamic hydraulic stage lengths, gaps and volume rates must match ordered cells")
    if concentrations.shape != (ncell, nspecies):
        raise ValueError("dynamic hydraulic chemistry must match ordered cell/species axes")
    if (not np.isfinite(lengths).all() or np.any(lengths <= 0.0)
            or not np.isfinite(gaps).all() or np.any(gaps <= 0.0)
            or not np.isfinite(volume_rates).all() or not np.isfinite(concentrations).all()
            or np.any(concentrations < 0.0) or not math.isfinite(inlet_flow_m3_s)):
        raise ValueError("dynamic hydraulic stage arrays must be finite and physically signed")
    width, density, viscosity = (float(binding.transverse_width_m), float(binding.density_kg_m3),
                                 float(binding.dynamic_viscosity_Pa_s))
    ratios = width / gaps
    if np.any(ratios < float(binding.minimum_width_to_aperture_ratio)):
        raise ValueError("dynamic slit aspect ratio is outside reviewed support")
    pressure = float(_interpolate(binding.signed_pressure_drop_Pa_by_knot, time_s, binding.time_s))
    face_flow = np.concatenate(([inlet_flow_m3_s], inlet_flow_m3_s - np.cumsum(volume_rates)))
    mean_flow = 0.5 * (face_flow[:-1] + face_flow[1:])
    resistance_terms = 12.0 * viscosity * lengths / (width * gaps**3)
    inertance_terms = density * lengths / (width * gaps)
    resistance_factor = float(binding.resistance_correction_multiplier)
    inertance_factor = float(binding.inertance_correction_multiplier)
    resistance = math.fsum(resistance_terms) * resistance_factor
    inertance = math.fsum(inertance_terms) * inertance_factor
    pressure_resistance = math.fsum(float(r) * float(q) for r, q in zip(resistance_terms, mean_flow, strict=True)) * resistance_factor
    flow_rate = (pressure - pressure_resistance) / inertance
    reynolds = 2.0 * density * np.abs(mean_flow) / (width * viscosity)
    if (not math.isfinite(flow_rate) or not math.isfinite(resistance) or not math.isfinite(inertance)
            or resistance <= 0.0 or inertance <= 0.0):
        raise ArithmeticError("dynamic hydraulic momentum RHS exceeds numeric support")
    if np.any(np.abs(face_flow) > float(binding.maximum_abs_flow_m3_s)):
        raise ArithmeticError("dynamic hydraulic face flow exceeds the caller-declared bound")
    if np.any(reynolds > float(binding.maximum_reviewed_reynolds_number)):
        raise ValueError("dynamic hydraulic Reynolds support exceeded")
    pressure_by_cell = inertance_terms * inertance_factor * flow_rate + resistance_terms * resistance_factor * mean_flow
    closure = math.fsum(float(value) for value in pressure_by_cell) - pressure
    closure_scale = max(abs(pressure), math.fsum(abs(float(value)) for value in pressure_by_cell), 1e-300)
    closure_limit = 64.0 * math.ulp(closure_scale)
    if abs(closure) > closure_limit:
        raise ArithmeticError("dynamic hydraulic series pressure closure failed")

    left = np.asarray(_interpolate(binding.left_boundary_species_concentration_mol_m3_by_knot,
                                   time_s, binding.time_s), dtype=float)
    right = np.asarray(_interpolate(binding.right_boundary_species_concentration_mol_m3_by_knot,
                                    time_s, binding.time_s), dtype=float)
    species_flux = np.zeros((ncell + 1, nspecies), dtype=float)
    for face, q in enumerate(face_flow):
        upstream = (left if face == 0 and q >= 0.0 else
                    right if face == ncell and q < 0.0 else
                    concentrations[face] if face < ncell and q < 0.0 else
                    concentrations[face - 1] if face > 0 else left)
        species_flux[face] = q * upstream
    component_flux = np.zeros((len(components), ncell + 1), dtype=float)
    for cindex, component in enumerate(components):
        coefficients = {row.species_id: float(row.coefficient) for row in component.species_coefficients}
        component_flux[cindex] = [math.fsum(
            coefficients.get(species_id, 0.0) * float(species_flux[face, sindex])
            for sindex, species_id in enumerate(binding.species_order)
        ) for face in range(ncell + 1)]

    boundary = []
    for sign, face, boundary_concentration in ((-1.0, 0, left), (1.0, ncell, right)):
        q = float(face_flow[face])
        upstream = boundary_concentration if ((face == 0 and q >= 0.0) or (face == ncell and q < 0.0)) else concentrations[0 if face == 0 else -1]
        species_rate = sign * q * upstream
        component_rates = {component.component_id: sign * math.fsum(
            float(next((row.coefficient for row in component.species_coefficients
                        if row.species_id == species_id), 0.0)) * float(q) * float(upstream[sindex])
            for sindex, species_id in enumerate(binding.species_order)
        ) for component in components}
        element_rates = {element: sign * q * math.fsum(
            float(binding.species_elemental_composition[species_id].get(element, 0.0)) * float(upstream[sindex])
            for sindex, species_id in enumerate(binding.species_order)
        ) for element in sorted(set().union(*(set(row) for row in binding.species_elemental_composition.values())))}
        charge_rate = sign * q * math.fsum(
            float(binding.species_charge_numbers[sindex]) * float(upstream[sindex])
            for sindex in range(nspecies)
        )
        boundary.append({"component_mol_s": component_rates, "element_mol_s": element_rates,
                         "charge_mol_equivalent_s": charge_rate})
    return {
        "pressure_drop_Pa": pressure,
        "signed_inlet_flow_m3_s": float(inlet_flow_m3_s),
        "inlet_flow_derivative_m3_s2": flow_rate,
        "face_flow_m3_s": face_flow,
        "cell_mean_flow_m3_s": mean_flow,
        "cell_liquid_volume_rate_m3_s": volume_rates,
        "continuity_residual_m3_s": face_flow[:-1] - face_flow[1:] - volume_rates,
        "resistance_terms_Pa_s_m3": resistance_terms,
        "inertance_terms_Pa_s2_m3": inertance_terms,
        "cell_pressure_drop_Pa": pressure_by_cell,
        "pressure_closure_residual_Pa": closure,
        "pressure_closure_roundoff_limit_Pa": closure_limit,
        "reynolds_number_by_cell": reynolds,
        "species_flux_mol_s_by_face": species_flux,
        "component_flux_mol_s_by_component_and_face": component_flux,
        "boundary_reservoir_rates": boundary,
    }
