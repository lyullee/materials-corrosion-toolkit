"""Original transformations of declared laboratory and inspection measurements."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


class OffsetYield(Contract):
    engineering_strain: list[Nonnegative] = Field(min_length=3)
    engineering_stress_Pa: list[Nonnegative] = Field(min_length=3)
    elastic_modulus_Pa: Positive
    offset_strain: Positive

    @model_validator(mode="after")
    def align(self):
        if len(self.engineering_strain) != len(self.engineering_stress_Pa):
            raise ValueError("stress and strain observations must align")
        if any(b <= a for a, b in zip(self.engineering_strain, self.engineering_strain[1:], strict=False)):
            raise ValueError("use the monotonic loading branch with strictly increasing strain")
        return self


def offset_yield(x: OffsetYield) -> Calculation:
    residual = [
        e - s / x.elastic_modulus_Pa - x.offset_strain
        for e, s in zip(x.engineering_strain, x.engineering_stress_Pa, strict=True)
    ]
    if residual[0] >= 0:
        return Calculation(
            status="needs_data",
            values={},
            notes=("The recorded branch starts beyond the offset intersection.",),
        )
    for i, (a, b) in enumerate(zip(residual, residual[1:], strict=False)):
        if a < 0 <= b:
            fraction = -a / (b - a)
            stress = x.engineering_stress_Pa[i] + fraction * (
                x.engineering_stress_Pa[i + 1] - x.engineering_stress_Pa[i]
            )
            strain = x.engineering_strain[i] + fraction * (
                x.engineering_strain[i + 1] - x.engineering_strain[i]
            )
            return Calculation(
                values=dict(
                    offset_yield_stress_Pa=stress, intersection_strain=strain, bracket_indices=[i, i + 1]
                )
            )
    return Calculation(
        status="needs_data",
        values={},
        notes=("No offset intersection is bracketed by the recorded loading branch.",),
    )


class ToFDDepth(Contract):
    probe_index_separation_m: Positive
    longitudinal_sound_speed_m_s: Positive
    delay_from_lateral_wave_s: Nonnegative
    wall_thickness_m: Positive


def tofd_depth(x: ToFDDepth) -> Calculation:
    increment = x.longitudinal_sound_speed_m_s * x.delay_from_lateral_wave_s / 2
    depth = math.sqrt(increment * (x.probe_index_separation_m + increment))
    return Calculation(
        values=dict(tip_depth_m=depth, remaining_backwall_ligament_m=x.wall_thickness_m - depth),
        status="computed" if depth <= x.wall_thickness_m else "out_of_scope",
        notes=(
            "Symmetric tip beneath the probe midpoint; lateral-wave reference removes only common calibrated delays. No POD or dead-zone clearance is established.",
        ),
    )


class VickersIndent(Contract):
    test_force_N: Positive
    first_diagonal_m: Positive
    second_diagonal_m: Positive


def vickers_indent(x: VickersIndent) -> Calculation:
    diagonal = (x.first_diagonal_m + x.second_diagonal_m) / 2
    stress = 2 * math.sin(math.radians(68)) * x.test_force_N / diagonal**2
    return Calculation(
        values=dict(indentation_hardness_Pa=stress, conventional_HV=stress / (9.80665 * 1e6)),
        notes=(
            "Geometry conversion only; dwell, surface, force range and diagonal quality remain test-procedure checks.",
        ),
    )


class BrinellIndent(Contract):
    test_force_N: Positive
    ball_diameter_m: Positive
    mean_indentation_diameter_m: Positive

    @model_validator(mode="after")
    def geometry(self):
        if self.mean_indentation_diameter_m >= self.ball_diameter_m:
            raise ValueError("indentation diameter must be smaller than ball diameter")
        return self


def brinell_indent(x: BrinellIndent) -> Calculation:
    d = x.mean_indentation_diameter_m
    diam = x.ball_diameter_m
    # Rationalized spherical-cap depth avoids cancellation for small impressions.
    sag = d * d / (diam + math.sqrt((diam - d) * (diam + d)))
    stress = 2 * x.test_force_N / (math.pi * diam * sag)
    return Calculation(
        values=dict(indentation_hardness_Pa=stress, conventional_HBW=stress / (9.80665 * 1e6)),
        notes=(
            "Geometry conversion only; this does not qualify force/diameter ratio or material hardness conversions.",
        ),
    )


class RockwellDepth(Contract):
    initial_depth_m: float
    final_depth_m: float
    scale_id: str = Field(min_length=1)
    scale_offset: float
    depth_per_scale_unit_m: Positive
    scale_definition_basis: str = Field(min_length=1)
    applicability_reviewed: bool


def rockwell_depth(x: RockwellDepth) -> Calculation:
    if not x.applicability_reviewed:
        return Calculation(
            status="needs_data",
            values={},
            notes=("Review the scale, indenter, load cycle and depth reference before conversion.",),
        )
    increment = x.final_depth_m - x.initial_depth_m
    return Calculation(
        values=dict(
            permanent_depth_increment_m=increment,
            hardness_number=x.scale_offset - increment / x.depth_per_scale_unit_m,
            scale_id=x.scale_id,
            scale_definition_basis=x.scale_definition_basis,
        ),
        status="computed" if increment >= 0 else "out_of_scope",
        notes=(
            "Both readings must share the preliminary-force reference. No curvature correction, valid hardness range, material conversion or acceptance decision is inferred.",
        ),
    )


class KnoopIndent(Contract):
    test_force_N: Positive
    long_diagonal_m: Positive
    longitudinal_edge_angle_deg: float = Field(gt=0, lt=180)
    transverse_edge_angle_deg: float = Field(gt=0, lt=180)
    indenter_geometry_basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def angle_order(self):
        if self.longitudinal_edge_angle_deg <= self.transverse_edge_angle_deg:
            raise ValueError("longitudinal edge angle must exceed transverse edge angle")
        return self


def knoop_indent(x: KnoopIndent) -> Calculation:
    ratio = math.tan(math.radians(x.transverse_edge_angle_deg / 2)) / math.tan(
        math.radians(x.longitudinal_edge_angle_deg / 2)
    )
    short_diagonal = x.long_diagonal_m * ratio
    projected_area = x.long_diagonal_m * short_diagonal / 2
    stress = x.test_force_N / projected_area
    return Calculation(
        values=dict(
            projected_area_m2=projected_area,
            ideal_short_diagonal_m=short_diagonal,
            indentation_hardness_Pa=stress,
            conventional_HK=stress / (9.80665 * 1e6),
            indenter_geometry_basis=x.indenter_geometry_basis,
        ),
        notes=(
            "The short diagonal is derived from declared ideal indenter angles, not measured elastic recovery. Force, diagonal quality, calibration, dwell and test validity require separate evidence.",
        ),
    )


class SaturationCalorimetryState(Contract):
    fluid_id: str = Field(min_length=1)
    pressure_Pa: Positive
    temperature_K: Positive
    liquid_density_kg_m3: Positive
    vapor_density_kg_m3: Positive
    liquid_enthalpy_J_kg: float
    vapor_enthalpy_J_kg: float
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def two_phase_order(self):
        if self.vapor_density_kg_m3 >= self.liquid_density_kg_m3:
            raise ValueError("distinct saturated phases require vapor density below liquid density")
        if self.vapor_enthalpy_J_kg <= self.liquid_enthalpy_J_kg:
            raise ValueError("positive vaporization enthalpy required")
        expected = canonical_digest(
            self.model_dump(mode="json", exclude={"provider_state_digest", "evidence"})
        )
        if expected != self.provider_state_digest:
            raise ValueError("saturation property record digest mismatch")
        return self


class BoilOffCalorimetry(Contract):
    saturation_state: SaturationCalorimetryState
    escaping_vapor_mass_flow_kg_s: Nonnegative
    inventory_mode: Literal["falling_liquid_level_rigid_vessel", "constant_level_saturated_liquid_makeup"]
    separately_accounted_heat_input_W: Nonnegative = 0.0
    isobaric_saturated_bath_reviewed: bool
    flow_is_escaping_vapor_mass_at_bath_outlet_reviewed: bool
    inventory_mode_and_no_other_mass_exchange_reviewed: bool
    sensible_transient_and_other_energy_terms_negligible_reviewed: bool
    property_state_and_measurement_applicability_reviewed: bool


def boil_off_calorimetry(x: BoilOffCalorimetry) -> Calculation:
    reviews = [name for name in type(x).model_fields if name.endswith("_reviewed") and not getattr(x, name)]
    if reviews:
        return Calculation(status="needs_data", values={"missing_reviews": reviews})
    state = x.saturation_state
    ratio = state.vapor_density_kg_m3 / state.liquid_density_kg_m3
    correction = 1 / (1 - ratio) if x.inventory_mode == "falling_liquid_level_rigid_vessel" else 1.0
    vaporization = x.escaping_vapor_mass_flow_kg_s * correction
    latent = state.vapor_enthalpy_J_kg - state.liquid_enthalpy_J_kg
    total = vaporization * latent
    return Calculation(
        values=dict(
            liquid_to_vapor_mass_rate_kg_s=vaporization,
            vapor_accumulation_mass_rate_kg_s=vaporization - x.escaping_vapor_mass_flow_kg_s,
            escaping_flow_correction_factor=correction,
            vaporization_enthalpy_J_kg=latent,
            total_bath_heat_input_W=total,
            residual_heat_input_W=total - x.separately_accounted_heat_input_W,
            fluid_id=state.fluid_id,
            pressure_Pa=state.pressure_Pa,
            temperature_K=state.temperature_K,
            provider_id=state.provider_id,
            provider_version=state.provider_version,
            provider_revision=state.provider_revision,
            provider_state_digest=state.provider_state_digest,
        ),
        notes=(
            "Mass flow is at the bath outlet; warmed gas volume must first be converted using its own measured reference state.",
            "Residual heat is signed. The calculation does not infer vacuum leakage, insulation damage, hold time, acceptance or pressure-relief capacity.",
        ),
    )


class GasPressureDecay(Contract):
    rigid_volume_m3: Positive
    initial_absolute_pressure_Pa: Positive
    final_absolute_pressure_Pa: Positive
    initial_temperature_K: Positive
    final_temperature_K: Positive
    initial_compressibility_factor: Positive
    final_compressibility_factor: Positive
    duration_s: Positive
    reference_pressure_Pa: Positive
    reference_temperature_K: Positive
    reference_compressibility_factor: Positive
    fluid_id: str | None = None
    property_provider_id: str | None = None
    property_provider_version: str | None = None
    property_state_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    absolute_pressure_temperature_and_phase_reviewed: bool | None = None

    @model_validator(mode="after")
    def coherent_optional_provider(self):
        provider_fields = (
            self.fluid_id,
            self.property_provider_id,
            self.property_provider_version,
            self.property_state_digest,
            self.absolute_pressure_temperature_and_phase_reviewed,
        )
        if any(value is not None for value in provider_fields) and (
            any(value is None for value in provider_fields)
            or not self.absolute_pressure_temperature_and_phase_reviewed
        ):
            raise ValueError("optional gas-property provenance must be complete and reviewed")
        return self


def gas_pressure_decay(x: GasPressureDecay) -> Calculation:
    gas_constant = 8.31446261815324
    initial = (
        x.initial_absolute_pressure_Pa
        * x.rigid_volume_m3
        / (x.initial_compressibility_factor * gas_constant * x.initial_temperature_K)
    )
    final = (
        x.final_absolute_pressure_Pa
        * x.rigid_volume_m3
        / (x.final_compressibility_factor * gas_constant * x.final_temperature_K)
    )
    rate = (initial - final) / x.duration_s
    return Calculation(
        values=dict(
            net_molar_outflow_mol_s=rate,
            reference_volume_outflow_m3_s=rate
            * x.reference_compressibility_factor
            * gas_constant
            * x.reference_temperature_K
            / x.reference_pressure_Pa,
            fluid_id=x.fluid_id,
            property_provider_id=x.property_provider_id,
            property_provider_version=x.property_provider_version,
            property_state_digest=x.property_state_digest,
        ),
        notes=(
            "One gas and a rigid equilibrated volume; negative net outflow is retained. Desorption, permeation, thermal gradients and actual leak-path physics are not identified by endpoint inventory loss.",
        ),
    )


class VacuumRise(Contract):
    rigid_volume_m3: Positive
    initial_absolute_pressure_Pa: Nonnegative
    final_absolute_pressure_Pa: Nonnegative
    duration_s: Positive
    background_throughput_Pa_m3_s: Nonnegative
    constant_temperature_declared: bool


def vacuum_rise(x: VacuumRise) -> Calculation:
    if not x.constant_temperature_declared:
        return Calculation(
            status="out_of_scope",
            values={},
            notes=("This pressure-rise model requires constant temperature.",),
        )
    total = x.rigid_volume_m3 * (x.final_absolute_pressure_Pa - x.initial_absolute_pressure_Pa) / x.duration_s
    return Calculation(
        values=dict(
            total_gas_load_Pa_m3_s=total,
            background_corrected_throughput_Pa_m3_s=total - x.background_throughput_Pa_m3_s,
        ),
        notes=(
            "Isolated rigid chamber; measured gas load includes leakage and outgassing. A negative background-corrected value is not clipped.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.offset_yield",
            OffsetYield,
            offset_yield,
            {"offset_yield_stress_Pa": "Pa", "intersection_strain": "1", "bracket_indices": "index"},
            (
                "Caller supplies extensometer strain, corrected monotonic stress data, elastic modulus and offset.",
            ),
            ("offset_intersection",),
        ),
        ModelSpec(
            "inspection.tofd_depth",
            ToFDDepth,
            tofd_depth,
            {"tip_depth_m": "m", "remaining_backwall_ligament_m": "m"},
            ("Straight longitudinal paths in a homogeneous flat section and a centred tip.",),
            ("twi_tofd",),
        ),
        ModelSpec(
            "testing.vickers",
            VickersIndent,
            vickers_indent,
            {"indentation_hardness_Pa": "Pa", "conventional_HV": "kgf/mm^2"},
            ("Opposite-face diamond angle is 136 degrees; both measured diagonals are explicit.",),
            ("indentation_geometry",),
        ),
        ModelSpec(
            "testing.brinell",
            BrinellIndent,
            brinell_indent,
            {"indentation_hardness_Pa": "Pa", "conventional_HBW": "kgf/mm^2"},
            ("Spherical indentation geometry; force and dimensions are SI inputs.",),
            ("indentation_geometry",),
        ),
        ModelSpec(
            "testing.rockwell_depth",
            RockwellDepth,
            rockwell_depth,
            {
                "permanent_depth_increment_m": "m",
                "hardness_number": "1",
                "scale_id": "1",
                "scale_definition_basis": "1",
            },
            (
                "Caller-defined scale constants and common preliminary-force depth reference; no automatic scale selection.",
            ),
            ("declared_rockwell_depth_scale",),
        ),
        ModelSpec(
            "testing.knoop",
            KnoopIndent,
            knoop_indent,
            {
                "projected_area_m2": "m^2",
                "ideal_short_diagonal_m": "m",
                "indentation_hardness_Pa": "Pa",
                "conventional_HK": "kgf/mm^2",
                "indenter_geometry_basis": "1",
            },
            (
                "Ideal rhombic projected area from explicitly declared indenter edge angles and measured long diagonal.",
            ),
            ("indentation_geometry",),
        ),
        ModelSpec(
            "inspection.boil_off_calorimetry",
            BoilOffCalorimetry,
            boil_off_calorimetry,
            {
                "liquid_to_vapor_mass_rate_kg_s": "kg/s",
                "vapor_accumulation_mass_rate_kg_s": "kg/s",
                "escaping_flow_correction_factor": "1",
                "vaporization_enthalpy_J_kg": "J/kg",
                "total_bath_heat_input_W": "W",
                "residual_heat_input_W": "W",
                "fluid_id": "1",
                "pressure_Pa": "Pa",
                "temperature_K": "K",
                "provider_id": "1",
                "provider_version": "1",
                "provider_revision": "1",
                "provider_state_digest": "1",
            },
            (
                "Isobaric saturated liquid bath; explicitly declared level/makeup mode and negligible unmodelled energy terms.",
            ),
            ("saturated_bath_boil_off_energy_balance",),
        ),
        ModelSpec(
            "inspection.gas_pressure_decay",
            GasPressureDecay,
            gas_pressure_decay,
            {
                "net_molar_outflow_mol_s": "mol/s",
                "reference_volume_outflow_m3_s": "m^3/s",
                "fluid_id": "1",
                "property_provider_id": "1",
                "property_provider_version": "1",
                "property_state_digest": "1",
            },
            (
                "Known compressibility at both equilibrated endpoints and an explicit reporting reference state.",
            ),
            ("gas_inventory_balance",),
        ),
        ModelSpec(
            "inspection.vacuum_rise",
            VacuumRise,
            vacuum_rise,
            {"total_gas_load_Pa_m3_s": "Pa*m^3/s", "background_corrected_throughput_Pa_m3_s": "Pa*m^3/s"},
            ("Isothermal pressure rise with declared background gas load; no material leak limit bundled.",),
            ("gas_inventory_balance",),
        ),
    ]
