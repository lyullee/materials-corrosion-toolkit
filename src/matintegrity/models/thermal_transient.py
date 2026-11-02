"""One-dimensional transient heat flow and elastic section stress.

All material curves, boundaries and mechanical limits are supplied by the caller.
The heat solver uses a cell-centred finite-volume balance with backward Euler
time integration.  The stress solver integrates a piecewise-linear section; it
does not embed a pressure-vessel code rule or a material-property table.
"""

from __future__ import annotations

import math
from typing import Annotated, Literal

from pydantic import Field, model_validator

from ..contracts import (
    AssessmentResult,
    Calculation,
    Contract,
    Evidence,
    Fraction,
    Nonnegative,
    Positive,
    RunContext,
    canonical_digest,
)
from ..registry import ModelSpec

FinitePoisson = Annotated[float, Field(gt=-1.0, lt=0.5)]


class ThermalMaterialProperties(Contract):
    material_id: str = Field(min_length=1)
    material_condition_id: str | None = Field(default=None, min_length=1)
    temperature_K: list[Positive] = Field(min_length=1, max_length=200)
    conductivity_W_m_K: list[Positive] = Field(min_length=1, max_length=200)
    volumetric_heat_capacity_J_m3_K: list[Positive] = Field(min_length=1, max_length=200)
    property_provider_id: str | None = Field(default=None, min_length=1)
    property_provider_revision: str | None = Field(default=None, min_length=1)
    property_record_id: str | None = Field(default=None, min_length=1)
    property_source_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    property_evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def aligned_curves(self):
        count = len(self.temperature_K)
        if len(self.conductivity_W_m_K) != count or len(self.volumetric_heat_capacity_J_m3_K) != count:
            raise ValueError("thermal-property vectors must align")
        if count > 1 and any(
            right <= left for left, right in zip(self.temperature_K, self.temperature_K[1:], strict=False)
        ):
            raise ValueError("thermal-property temperatures must strictly increase")
        lineage = (
            self.property_provider_id,
            self.property_provider_revision,
            self.property_record_id,
            self.property_source_sha256,
        )
        if any(value is not None for value in lineage):
            if any(value is None for value in lineage) or not self.property_evidence:
                raise ValueError("thermal property lineage requires provider revision, record, source digest and Evidence")
            if not any(
                row.source_id == self.property_provider_id and row.sha256 == self.property_source_sha256
                for row in self.property_evidence
            ):
                raise ValueError("thermal property provider and source digest must match a declared Evidence record")
        elif self.property_evidence:
            raise ValueError("thermal property Evidence requires complete provider and record lineage")
        return self


class ThermalBoundary(Contract):
    boundary_id: str = Field(min_length=1)
    kind: Literal["adiabatic", "prescribed_temperature", "prescribed_heat_flux", "convection_radiation"]
    temperature_K: list[Positive] | None = None
    heat_flux_into_solid_W_m2: list[float] | None = None
    convection_W_m2_K: list[Nonnegative] | None = None
    ambient_temperature_K: list[Positive] | None = None
    emissivity: Fraction | None = None
    radiative_environment_temperature_K: list[Positive] | None = None

    @model_validator(mode="after")
    def fields_for_kind(self):
        active = {
            "temperature_K": self.temperature_K,
            "heat_flux_into_solid_W_m2": self.heat_flux_into_solid_W_m2,
            "convection_W_m2_K": self.convection_W_m2_K,
            "ambient_temperature_K": self.ambient_temperature_K,
            "emissivity": self.emissivity,
            "radiative_environment_temperature_K": self.radiative_environment_temperature_K,
        }
        required = {
            "adiabatic": set(),
            "prescribed_temperature": {"temperature_K"},
            "prescribed_heat_flux": {"heat_flux_into_solid_W_m2"},
            "convection_radiation": {
                "convection_W_m2_K",
                "ambient_temperature_K",
                "emissivity",
                "radiative_environment_temperature_K",
            },
        }[self.kind]
        present = {key for key, value in active.items() if value is not None}
        if present != required:
            raise ValueError(f"{self.kind} boundary requires exactly {sorted(required)}")
        return self


class DistributedHeatExchange(Contract):
    area_per_volume_m_inv: list[Nonnegative] = Field(min_length=1, max_length=500)
    convection_W_m2_K: list[Nonnegative] = Field(min_length=2, max_length=5000)
    ambient_temperature_K: list[Positive] = Field(min_length=2, max_length=5000)
    emissivity: Fraction | None = None
    emissivity_history: list[Fraction] | None = Field(default=None, min_length=2, max_length=5000)
    radiative_environment_temperature_K: list[Positive] | None = None
    radiation_exchange_basis_reviewed: bool = False

    @model_validator(mode="after")
    def radiation_pair(self):
        emissivity_count = int(self.emissivity is not None) + int(self.emissivity_history is not None)
        supplied = emissivity_count > 0 or self.radiative_environment_temperature_K is not None
        if supplied and (emissivity_count != 1 or self.radiative_environment_temperature_K is None):
            raise ValueError("distributed radiation requires one emissivity input and radiative-environment temperatures")
        if supplied != self.radiation_exchange_basis_reviewed:
            raise ValueError("distributed radiation inputs and applicability review must be supplied together")
        if self.radiative_environment_temperature_K is not None and len(
            self.radiative_environment_temperature_K
        ) != len(self.convection_W_m2_K):
            raise ValueError("radiative-environment history must align with the distributed-exchange clock")
        if self.emissivity_history is not None and len(self.emissivity_history) != len(
            self.convection_W_m2_K
        ):
            raise ValueError("emissivity history must align with the distributed-exchange clock")
        return self


class TransientConduction1D(Contract):
    schema_version: Literal["matintegrity.transient_conduction_1d.v1"] = (
        "matintegrity.transient_conduction_1d.v1"
    )
    geometry: Literal["planar", "cylindrical"]
    cell_edges_m: list[Nonnegative] = Field(min_length=3, max_length=501)
    planar_area_m2: Positive | None = None
    cylinder_length_m: Positive | None = None
    materials: list[ThermalMaterialProperties] = Field(min_length=1, max_length=100)
    cell_material_ids: list[str] = Field(min_length=2, max_length=500)
    initial_temperature_K: list[Positive] = Field(min_length=2, max_length=500)
    time_s: list[Nonnegative] = Field(min_length=2, max_length=5000)
    left_boundary: ThermalBoundary
    right_boundary: ThermalBoundary
    volumetric_heat_generation_W_m3: list[list[float]] | None = None
    distributed_exchange: DistributedHeatExchange | None = None
    maximum_step_s: Positive
    nonlinear_absolute_tolerance_K: Positive = 1e-8
    nonlinear_relative_tolerance: Positive = 1e-10
    maximum_nonlinear_iterations: int = Field(default=80, ge=2, le=500)
    maximum_relative_energy_balance_error: Positive = 1e-7
    one_dimensional_geometry_reviewed: bool
    material_property_support_reviewed: bool
    boundary_conditions_reviewed: bool
    phase_change_absent_or_included_in_capacity_reviewed: bool

    @model_validator(mode="after")
    def aligned_model(self):
        cells = len(self.cell_edges_m) - 1
        times = len(self.time_s)
        if cells != len(self.cell_material_ids) or cells != len(self.initial_temperature_K):
            raise ValueError("cell edges, material assignments and initial temperatures must align")
        if cells * times > 200_000:
            raise ValueError("requested temperature history exceeds 200000 cell-time values")
        if any(right <= left for left, right in zip(self.cell_edges_m, self.cell_edges_m[1:], strict=False)):
            raise ValueError("cell edges must strictly increase")
        if any(right <= left for left, right in zip(self.time_s, self.time_s[1:], strict=False)):
            raise ValueError("thermal clock must strictly increase")
        if self.geometry == "planar":
            if self.planar_area_m2 is None or self.cylinder_length_m is not None:
                raise ValueError("planar geometry requires area and no cylinder length")
        elif self.cylinder_length_m is None or self.planar_area_m2 is not None or self.cell_edges_m[0] <= 0:
            raise ValueError("cylindrical geometry requires positive radii and length only")
        material_ids = [item.material_id for item in self.materials]
        if len(material_ids) != len(set(material_ids)):
            raise ValueError("thermal material IDs must be unique")
        if any(identifier not in set(material_ids) for identifier in self.cell_material_ids):
            raise ValueError("every cell material ID must resolve exactly")
        for boundary in (self.left_boundary, self.right_boundary):
            for field in (
                boundary.temperature_K,
                boundary.heat_flux_into_solid_W_m2,
                boundary.convection_W_m2_K,
                boundary.ambient_temperature_K,
                boundary.radiative_environment_temperature_K,
            ):
                if field is not None and len(field) != times:
                    raise ValueError("boundary histories must align to the thermal clock")
        if self.volumetric_heat_generation_W_m3 is not None and (
            len(self.volumetric_heat_generation_W_m3) != times
            or any(len(row) != cells for row in self.volumetric_heat_generation_W_m3)
        ):
            raise ValueError("volumetric heat-generation rows must align to time and cells")
        if self.distributed_exchange is not None and (
            len(self.distributed_exchange.area_per_volume_m_inv) != cells
            or len(self.distributed_exchange.convection_W_m2_K) != times
            or len(self.distributed_exchange.ambient_temperature_K) != times
            or (
                self.distributed_exchange.radiative_environment_temperature_K is not None
                and len(self.distributed_exchange.radiative_environment_temperature_K) != times
            )
            or (
                self.distributed_exchange.emissivity_history is not None
                and len(self.distributed_exchange.emissivity_history) != times
            )
        ):
            raise ValueError("distributed heat-exchange histories must align to time and cells")
        substeps = sum(
            math.ceil((right - left) / self.maximum_step_s)
            for left, right in zip(self.time_s, self.time_s[1:], strict=False)
        )
        if substeps > 200_000:
            raise ValueError("requested maximum step creates more than 200000 implicit steps")
        return self


class ThermalStressPropertyEvidence(Contract):
    """Caller provenance for one through-wall mechanical-property profile."""

    quantity: Literal[
        "secant_thermal_expansion_1_K",
        "elastic_modulus_Pa",
        "poisson_ratio",
        "elastic_limit_Pa",
    ]
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def source_is_evidenced(self):
        if not any(
            item.source_id == self.provider_id and item.sha256 == self.source_sha256
            for item in self.evidence
        ):
            raise ValueError("mechanical property provider and digest must match declared Evidence")
        return self


class ThroughWallThermalStress(Contract):
    schema_version: Literal["matintegrity.through_wall_thermal_stress.v1"] = (
        "matintegrity.through_wall_thermal_stress.v1"
    )
    profile_id: str = Field(min_length=1)
    material_condition_id: str | None = Field(default=None, min_length=1)
    position_m: list[float] = Field(min_length=2, max_length=1000)
    temperature_K: list[Positive] = Field(min_length=2, max_length=1000)
    temperature_source_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    temperature_source_model_id: str | None = None
    temperature_source_model_version: str | None = None
    temperature_source_time_index: int | None = Field(default=None, ge=0)
    temperature_source_time_s: Nonnegative | None = None
    temperature_source_time_basis_id: str | None = None
    temperature_source_asset_id: str | None = None
    temperature_source_location_id: str | None = None
    temperature_to_section_mapping_reviewed: bool = False
    reference_temperature_K: Positive
    secant_thermal_expansion_1_K: list[float] = Field(min_length=2, max_length=1000)
    elastic_modulus_Pa: list[Positive] = Field(min_length=2, max_length=1000)
    poisson_ratio: list[FinitePoisson] = Field(min_length=2, max_length=1000)
    elastic_limit_Pa: list[Positive] = Field(min_length=2, max_length=1000)
    property_profile_evidence: tuple[ThermalStressPropertyEvidence, ...] = ()
    plane_condition: Literal["uniaxial_plane_stress", "equi_biaxial_plane_stress"]
    control: Literal["resultant_controlled", "kinematic_controlled"]
    membrane_force_N_m: float | None = None
    bending_moment_N: float | None = None
    midplane_total_strain: float | None = None
    curvature_1_m: float | None = None
    plane_sections_reviewed: bool
    linear_elastic_response_reviewed: bool
    property_profiles_reviewed: bool
    applied_resultants_or_kinematics_reviewed: bool

    @model_validator(mode="after")
    def aligned_section(self):
        count = len(self.position_m)
        vectors = (
            self.temperature_K,
            self.secant_thermal_expansion_1_K,
            self.elastic_modulus_Pa,
            self.poisson_ratio,
            self.elastic_limit_Pa,
        )
        if any(len(values) != count for values in vectors):
            raise ValueError("all through-wall property profiles must align")
        if any(right <= left for left, right in zip(self.position_m, self.position_m[1:], strict=False)):
            raise ValueError("through-wall positions must strictly increase")
        quantities = [item.quantity for item in self.property_profile_evidence]
        if len(quantities) != len(set(quantities)):
            raise ValueError("each mechanical property profile may have at most one provenance record")
        if self.property_profile_evidence and self.material_condition_id is None:
            raise ValueError("evidence-linked mechanical properties require a material condition ID")
        resultants = (self.membrane_force_N_m, self.bending_moment_N)
        kinematics = (self.midplane_total_strain, self.curvature_1_m)
        if self.control == "resultant_controlled":
            if any(value is None for value in resultants) or any(value is not None for value in kinematics):
                raise ValueError("resultant control requires force and moment only")
        elif any(value is None for value in kinematics) or any(value is not None for value in resultants):
            raise ValueError("kinematic control requires midplane strain and curvature only")
        source_lineage = (
            self.temperature_source_result_sha256,
            self.temperature_source_model_id,
            self.temperature_source_model_version,
            self.temperature_source_time_index,
            self.temperature_source_time_s,
            self.temperature_source_time_basis_id,
            self.temperature_source_asset_id,
            self.temperature_source_location_id,
        )
        if any(value is not None for value in source_lineage):
            if any(value is None for value in source_lineage) or not self.temperature_to_section_mapping_reviewed:
                raise ValueError("temperature-field lineage requires complete source identity, time and section mapping review")
            if self.temperature_source_model_id != "thermal.transient_conduction_1d":
                raise ValueError("temperature source model must be transient one-dimensional conduction")
        elif self.temperature_to_section_mapping_reviewed:
            raise ValueError("temperature mapping review requires a linked thermal source result")
        return self


def bind_thermal_temperature_profile(
    stress_request: ThroughWallThermalStress,
    thermal_result: AssessmentResult | dict,
    thermal_result_sha256: str,
    time_index: int,
    *,
    temperature_to_section_mapping_reviewed: bool,
) -> ThroughWallThermalStress:
    """Bind one exact thermal cell-centre temperature row to an elastic section request."""
    if isinstance(time_index, bool) or not isinstance(time_index, int) or time_index < 0:
        raise ValueError("thermal output time_index must be a nonnegative integer")
    if not isinstance(thermal_result, AssessmentResult):
        thermal_result = AssessmentResult.model_validate(thermal_result)
    source = thermal_result
    if source.model_id != "thermal.transient_conduction_1d" or source.status != "computed":
        raise ValueError("a computed transient-conduction AssessmentResult is required")
    expected_input_digest = canonical_digest({
        "model_id": source.model_id,
        "model_version": source.model_version,
        "inputs": source.inputs,
        "context": source.context.model_dump(mode="json"),
    })
    if source.input_digest != expected_input_digest:
        raise ValueError("thermal assessment input digest mismatch")
    if canonical_digest(source.model_dump(mode="json")) != thermal_result_sha256:
        raise ValueError("complete thermal result digest mismatch")
    times = source.inputs.get("time_s")
    centers = source.values.get("cell_centers_m")
    history = source.values.get("temperature_history_K")
    if (
        not isinstance(times, list)
        or not isinstance(centers, list)
        or not isinstance(history, list)
        or len(history) != len(times)
        or time_index >= len(times)
        or len(centers) != len(stress_request.position_m)
        or len(history[time_index]) != len(centers)
    ):
        raise ValueError("thermal output row and section coordinates must have exact matching dimensions")
    if tuple(float(value) for value in stress_request.position_m) != tuple(float(value) for value in centers):
        raise ValueError("thermal cell centres must exactly match section profile coordinates; no interpolation is performed")
    if not temperature_to_section_mapping_reviewed:
        raise ValueError("caller must review thermal-cell to section-coordinate and orientation mapping")
    payload = stress_request.model_dump(mode="json")
    payload.update({
        "temperature_K": history[time_index],
        "temperature_source_result_sha256": thermal_result_sha256,
        "temperature_source_model_id": source.model_id,
        "temperature_source_model_version": source.model_version,
        "temperature_source_time_index": time_index,
        "temperature_source_time_s": times[time_index],
        "temperature_source_time_basis_id": source.context.time_basis,
        "temperature_source_asset_id": source.context.asset_id,
        "temperature_source_location_id": source.context.location_id,
        "temperature_to_section_mapping_reviewed": True,
    })
    return ThroughWallThermalStress.model_validate(payload)


def _validate_temperature_source_context(x: ThroughWallThermalStress, context: RunContext) -> None:
    if x.temperature_source_result_sha256 is None:
        return
    if (
        context.time_basis != x.temperature_source_time_basis_id
        or context.asset_id != x.temperature_source_asset_id
        or context.location_id != x.temperature_source_location_id
    ):
        raise ValueError("thermal stress run context must match the linked temperature source asset, location and clock")


class _PropertySupportError(ValueError):
    pass


def _curve_value(temperature: float, knots: list[float], values: list[float]) -> float:
    if len(knots) == 1:
        return values[0]
    if temperature < knots[0] or temperature > knots[-1]:
        raise _PropertySupportError(
            f"temperature {temperature:.12g} K lies outside property support [{knots[0]}, {knots[-1]}] K"
        )
    index = min(max(0, _right_index(knots, temperature) - 1), len(knots) - 2)
    fraction = (temperature - knots[index]) / (knots[index + 1] - knots[index])
    return values[index] + fraction * (values[index + 1] - values[index])


def _right_index(values: list[float], target: float) -> int:
    low, high = 0, len(values)
    while low < high:
        middle = (low + high) // 2
        if target < values[middle]:
            high = middle
        else:
            low = middle + 1
    return low


def _enthalpy_density(temperature: float, material: ThermalMaterialProperties) -> float:
    knots = material.temperature_K
    capacity = material.volumetric_heat_capacity_J_m3_K
    if len(knots) == 1:
        return capacity[0] * (temperature - knots[0])
    if temperature < knots[0] or temperature > knots[-1]:
        raise _PropertySupportError(
            f"temperature {temperature:.12g} K lies outside heat-capacity support [{knots[0]}, {knots[-1]}] K"
        )
    total = 0.0
    for index in range(len(knots) - 1):
        left, right = knots[index], knots[index + 1]
        if temperature <= left:
            break
        upper = min(temperature, right)
        slope = (capacity[index + 1] - capacity[index]) / (right - left)
        width = upper - left
        total += capacity[index] * width + 0.5 * slope * width * width
        if temperature <= right:
            break
    return total


def _effective_capacity(old: float, trial: float, material: ThermalMaterialProperties) -> float:
    if math.isclose(old, trial, rel_tol=0.0, abs_tol=1e-12):
        return _curve_value(old, material.temperature_K, material.volumetric_heat_capacity_J_m3_K)
    return (_enthalpy_density(trial, material) - _enthalpy_density(old, material)) / (trial - old)


def _geometry(x: TransientConduction1D):
    import numpy as np

    edges = np.asarray(x.cell_edges_m, dtype=float)
    if x.geometry == "planar":
        centers = 0.5 * (edges[:-1] + edges[1:])
        face_areas = np.full(len(edges), float(x.planar_area_m2))
        volumes = float(x.planar_area_m2) * np.diff(edges)
    else:
        centers = np.sqrt(0.5 * (edges[:-1] ** 2 + edges[1:] ** 2))
        face_areas = 2 * math.pi * float(x.cylinder_length_m) * edges
        volumes = math.pi * float(x.cylinder_length_m) * (edges[1:] ** 2 - edges[:-1] ** 2)
    return edges, centers, face_areas, volumes


def _conduction_resistance(
    geometry: str, left: float, right: float, area: float, conductivity: float, length: float | None
) -> float:
    if geometry == "planar":
        return (right - left) / (conductivity * area)
    return math.log(right / left) / (2 * math.pi * float(length) * conductivity)


def _history_value(values: list[float], interval: int, fraction: float) -> float:
    return values[interval] + fraction * (values[interval + 1] - values[interval])


def _distributed_emissivity(exchange: DistributedHeatExchange, interval: int, fraction: float) -> float | None:
    if exchange.emissivity_history is not None:
        return _history_value(exchange.emissivity_history, interval, fraction)
    return None if exchange.emissivity is None else float(exchange.emissivity)


def _radiative_heat_rate(emissivity: float, exchange_area, environment_temperature: float, cell_temperature):
    """Return exact net gray-surface radiation from surroundings into cells."""
    import numpy as np

    if emissivity == 0.0:
        return 0.0
    environment = float(environment_temperature)
    cell = np.asarray(cell_temperature, dtype=float)
    with np.errstate(over="ignore", invalid="ignore"):
        temperature_difference_fourth = (
            (environment - cell)
            * (environment + cell)
            * (environment**2 + cell**2)
        )
        rates = emissivity * 5.670374419e-8 * np.asarray(exchange_area) * temperature_difference_fourth
    if not np.isfinite(rates).all():
        raise _PropertySupportError("distributed radiative heat rate exceeds finite numeric support")
    return float(np.sum(rates))


def _radiative_exchange_conductance(emissivity: float, exchange_area, environment_temperature: float, cell_temperature):
    """Return the finite secant conductance for a linearized gray-radiation term."""
    import numpy as np

    area = np.asarray(exchange_area, dtype=float)
    if emissivity == 0.0:
        return np.zeros_like(area)
    environment = np.float64(environment_temperature)
    cell = np.asarray(cell_temperature, dtype=float)
    with np.errstate(over="ignore", invalid="ignore"):
        conductance = (
            emissivity
            * 5.670374419e-8
            * area
            * (environment + cell)
            * (np.square(environment) + np.square(cell))
        )
    if not np.isfinite(conductance).all():
        raise _PropertySupportError("distributed radiative exchange exceeds finite numeric support")
    return conductance


def _solve_tridiagonal(lower, diagonal, upper, right_hand):
    """Solve one strictly diagonally dominant tridiagonal system in linear work."""
    import numpy as np

    diagonal = np.asarray(diagonal, dtype=float).copy()
    right_hand = np.asarray(right_hand, dtype=float).copy()
    lower = np.asarray(lower, dtype=float)
    upper = np.asarray(upper, dtype=float)
    for index in range(1, len(diagonal)):
        if diagonal[index - 1] <= 0 or not math.isfinite(diagonal[index - 1]):
            raise _PropertySupportError("nonpositive or nonfinite thermal-system pivot")
        factor = lower[index - 1] / diagonal[index - 1]
        diagonal[index] -= factor * upper[index - 1]
        right_hand[index] -= factor * right_hand[index - 1]
    if diagonal[-1] <= 0 or not math.isfinite(diagonal[-1]):
        raise _PropertySupportError("nonpositive or nonfinite thermal-system pivot")
    solution = np.empty_like(right_hand)
    solution[-1] = right_hand[-1] / diagonal[-1]
    for index in range(len(diagonal) - 2, -1, -1):
        solution[index] = (right_hand[index] - upper[index] * solution[index + 1]) / diagonal[index]
    return solution


def _boundary_terms(
    x: TransientConduction1D,
    boundary: ThermalBoundary,
    side: Literal["left", "right"],
    interval: int,
    fraction: float,
    cell_temperature: float,
    conductivity: float,
    edges,
    centers,
    face_areas,
):
    cell = 0 if side == "left" else len(centers) - 1
    face = 0 if side == "left" else len(edges) - 1
    a, b = sorted((float(edges[face]), float(centers[cell])))
    resistance = _conduction_resistance(
        x.geometry, a, b, float(face_areas[face]), conductivity, x.cylinder_length_m
    )
    if boundary.kind == "adiabatic":
        return 0.0, 0.0, cell_temperature, resistance
    if boundary.kind == "prescribed_heat_flux":
        flux = _history_value(boundary.heat_flux_into_solid_W_m2, interval, fraction)
        rate = flux * float(face_areas[face])
        return 0.0, rate, cell_temperature + rate * resistance, resistance
    if boundary.kind == "prescribed_temperature":
        environment = _history_value(boundary.temperature_K, interval, fraction)
        conductance = 1.0 / resistance
        return conductance, conductance * environment, environment, resistance

    convection = _history_value(boundary.convection_W_m2_K, interval, fraction)
    ambient = _history_value(boundary.ambient_temperature_K, interval, fraction)
    radiation_temperature = _history_value(boundary.radiative_environment_temperature_K, interval, fraction)
    area = float(face_areas[face])
    surface = cell_temperature
    sigma = 5.670374419e-8
    for _ in range(30):
        radiation = (
            float(boundary.emissivity)
            * sigma
            * (surface + radiation_temperature)
            * (surface * surface + radiation_temperature * radiation_temperature)
        )
        total = convection + radiation
        if total == 0:
            return 0.0, 0.0, cell_temperature, resistance
        effective_environment = (convection * ambient + radiation * radiation_temperature) / total
        conductance = 1.0 / (resistance + 1.0 / (total * area))
        updated = cell_temperature + conductance * (effective_environment - cell_temperature) * resistance
        if abs(updated - surface) <= 1e-11 * max(1.0, abs(updated)):
            surface = updated
            break
        surface = updated
    radiation = (
        float(boundary.emissivity)
        * sigma
        * (surface + radiation_temperature)
        * (surface * surface + radiation_temperature * radiation_temperature)
    )
    total = convection + radiation
    effective_environment = (convection * ambient + radiation * radiation_temperature) / total
    conductance = 1.0 / (resistance + 1.0 / (total * area))
    return conductance, conductance * effective_environment, surface, resistance


def _thermal_material_property_lineage(material: ThermalMaterialProperties) -> dict:
    table = {
        "material_id": material.material_id,
        "material_condition_id": material.material_condition_id,
        "temperature_K": material.temperature_K,
        "conductivity_W_m_K": material.conductivity_W_m_K,
        "volumetric_heat_capacity_J_m3_K": material.volumetric_heat_capacity_J_m3_K,
    }
    return {
        **table,
        "property_table_sha256": canonical_digest(table),
        "property_provider_id": material.property_provider_id,
        "property_provider_revision": material.property_provider_revision,
        "property_record_id": material.property_record_id,
        "property_source_sha256": material.property_source_sha256,
        "property_evidence": [row.model_dump(mode="json") for row in material.property_evidence],
        "lineage_status": "provider_evidenced" if material.property_provider_id is not None else "caller_supplied_without_provider_evidence",
    }


def transient_conduction_1d(x: TransientConduction1D) -> Calculation:
    import numpy as np

    material_property_lineage = [_thermal_material_property_lineage(row) for row in x.materials]
    reviews = (
        x.one_dimensional_geometry_reviewed,
        x.material_property_support_reviewed,
        x.boundary_conditions_reviewed,
        x.phase_change_absent_or_included_in_capacity_reviewed,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={"material_property_lineage": material_property_lineage},
            notes=(
                "Geometry, property support, boundaries and phase-change treatment require explicit review.",
            ),
        )
    edges, centers, face_areas, volumes = _geometry(x)
    material_map = {item.material_id: item for item in x.materials}
    cell_materials = [material_map[identifier] for identifier in x.cell_material_ids]
    temperature = np.asarray(x.initial_temperature_K, dtype=float)
    history = [temperature.tolist()]
    boundary_rate_history = []
    boundary_surface_history = []
    distributed_rate_history = []
    generation_rate_history = []
    cumulative_boundary = np.zeros(2)
    cumulative_distributed = 0.0
    cumulative_generation = 0.0
    maximum_balance = 0.0
    maximum_relative_balance = 0.0
    maximum_iterations = 0
    total_steps = 0

    def properties(values):
        conductivity = np.empty(len(values))
        for index, (value, material) in enumerate(zip(values, cell_materials, strict=True)):
            conductivity[index] = _curve_value(
                float(value), material.temperature_K, material.conductivity_W_m_K
            )
        return conductivity

    def rates(values, interval, fraction, conductivity):
        rates_at_boundaries = []
        surfaces = []
        for side, boundary in (("left", x.left_boundary), ("right", x.right_boundary)):
            conductance, source, surface, _ = _boundary_terms(
                x,
                boundary,
                side,
                interval,
                fraction,
                float(values[0 if side == "left" else -1]),
                float(conductivity[0 if side == "left" else -1]),
                edges,
                centers,
                face_areas,
            )
            rates_at_boundaries.append(
                source
                if boundary.kind == "prescribed_heat_flux"
                else source - conductance * float(values[0 if side == "left" else -1])
            )
            surfaces.append(surface)
        if x.distributed_exchange is None:
            distributed = 0.0
        else:
            coefficient = _history_value(x.distributed_exchange.convection_W_m2_K, interval, fraction)
            ambient = _history_value(x.distributed_exchange.ambient_temperature_K, interval, fraction)
            exchange_area = np.asarray(x.distributed_exchange.area_per_volume_m_inv) * volumes
            distributed = float(np.sum(coefficient * exchange_area * (ambient - values)))
            emissivity = _distributed_emissivity(x.distributed_exchange, interval, fraction)
            if emissivity is not None:
                radiation_environment = _history_value(
                    x.distributed_exchange.radiative_environment_temperature_K, interval, fraction
                )
                radiation = _radiative_heat_rate(
                    emissivity,
                    exchange_area,
                    radiation_environment,
                    values,
                )
                distributed += radiation
        if x.volumetric_heat_generation_W_m3 is None:
            generation = 0.0
        else:
            start = np.asarray(x.volumetric_heat_generation_W_m3[interval], dtype=float)
            end = np.asarray(x.volumetric_heat_generation_W_m3[interval + 1], dtype=float)
            generation = float(np.sum((start + fraction * (end - start)) * volumes))
        return np.asarray(rates_at_boundaries), surfaces, distributed, generation

    try:
        initial_conductivity = properties(temperature)
        initial_rates = rates(temperature, 0, 0.0, initial_conductivity)
        boundary_rate_history.append(initial_rates[0].tolist())
        boundary_surface_history.append(initial_rates[1])
        distributed_rate_history.append(initial_rates[2])
        generation_rate_history.append(initial_rates[3])
        for interval, (start, stop) in enumerate(zip(x.time_s, x.time_s[1:], strict=False)):
            steps = math.ceil((stop - start) / x.maximum_step_s)
            dt = (stop - start) / steps
            for step in range(steps):
                fraction = (step + 1) / steps
                old = temperature.copy()
                trial = old.copy()
                converged = False
                for iteration in range(1, x.maximum_nonlinear_iterations + 1):
                    conductivity = properties(trial)
                    capacity = np.asarray(
                        [
                            _effective_capacity(float(previous), float(current), material)
                            for previous, current, material in zip(old, trial, cell_materials, strict=True)
                        ]
                    )
                    storage = capacity * volumes / dt
                    diagonal = storage.copy()
                    lower = np.zeros(len(storage) - 1)
                    upper = np.zeros(len(storage) - 1)
                    right_hand = storage * old
                    for face in range(1, len(edges) - 1):
                        resistance = _conduction_resistance(
                            x.geometry,
                            float(centers[face - 1]),
                            float(edges[face]),
                            float(face_areas[face]),
                            float(conductivity[face - 1]),
                            x.cylinder_length_m,
                        ) + _conduction_resistance(
                            x.geometry,
                            float(edges[face]),
                            float(centers[face]),
                            float(face_areas[face]),
                            float(conductivity[face]),
                            x.cylinder_length_m,
                        )
                        conductance = 1.0 / resistance
                        left, right = face - 1, face
                        diagonal[left] += conductance
                        diagonal[right] += conductance
                        upper[left] -= conductance
                        lower[left] -= conductance
                    for side, boundary in (("left", x.left_boundary), ("right", x.right_boundary)):
                        cell = 0 if side == "left" else len(trial) - 1
                        conductance, source, _, _ = _boundary_terms(
                            x,
                            boundary,
                            side,
                            interval,
                            fraction,
                            float(trial[cell]),
                            float(conductivity[cell]),
                            edges,
                            centers,
                            face_areas,
                        )
                        diagonal[cell] += conductance
                        right_hand[cell] += source
                    if x.distributed_exchange is not None:
                        coefficient = _history_value(
                            x.distributed_exchange.convection_W_m2_K, interval, fraction
                        )
                        ambient = _history_value(
                            x.distributed_exchange.ambient_temperature_K, interval, fraction
                        )
                        exchange = (
                            coefficient * np.asarray(x.distributed_exchange.area_per_volume_m_inv) * volumes
                        )
                        distributed_source = exchange * ambient
                        emissivity = _distributed_emissivity(x.distributed_exchange, interval, fraction)
                        if emissivity is not None:
                            radiation_environment = _history_value(
                                x.distributed_exchange.radiative_environment_temperature_K, interval, fraction
                            )
                            radiative_exchange = _radiative_exchange_conductance(
                                emissivity,
                                np.asarray(x.distributed_exchange.area_per_volume_m_inv) * volumes,
                                radiation_environment,
                                trial,
                            )
                            exchange += radiative_exchange
                            distributed_source += radiative_exchange * radiation_environment
                            if not np.isfinite(distributed_source).all():
                                raise _PropertySupportError("distributed thermal source exceeds finite numeric support")
                        diagonal += exchange
                        right_hand += distributed_source
                    if x.volumetric_heat_generation_W_m3 is not None:
                        start_generation = np.asarray(
                            x.volumetric_heat_generation_W_m3[interval], dtype=float
                        )
                        stop_generation = np.asarray(
                            x.volumetric_heat_generation_W_m3[interval + 1], dtype=float
                        )
                        right_hand += (
                            start_generation + fraction * (stop_generation - start_generation)
                        ) * volumes
                    updated = _solve_tridiagonal(lower, diagonal, upper, right_hand)
                    if np.any(updated <= 0) or not np.all(np.isfinite(updated)):
                        raise _PropertySupportError("implicit step produced a nonphysical temperature")
                    error = float(np.max(np.abs(updated - trial)))
                    tolerance = x.nonlinear_absolute_tolerance_K + x.nonlinear_relative_tolerance * float(
                        np.max(np.abs(updated))
                    )
                    trial = updated
                    if error <= tolerance:
                        converged = True
                        maximum_iterations = max(maximum_iterations, iteration)
                        break
                if not converged:
                    return Calculation(
                        status="out_of_scope",
                        values={
                            "completed_internal_steps": total_steps,
                            "material_property_lineage": material_property_lineage,
                        },
                        notes=("Nonlinear heat step did not converge within the declared iteration limit.",),
                    )
                temperature = trial
                conductivity = properties(temperature)
                boundary_rates, _, distributed_rate, generation_rate = rates(
                    temperature, interval, fraction, conductivity
                )
                cell_energy_changes = [
                    float(volume)
                    * (
                        _enthalpy_density(float(current), material)
                        - _enthalpy_density(float(previous), material)
                    )
                    for volume, current, previous, material in zip(
                        volumes, temperature, old, cell_materials, strict=True
                    )
                ]
                energy_change = sum(cell_energy_changes)
                input_energy = dt * (float(np.sum(boundary_rates)) + distributed_rate + generation_rate)
                residual = energy_change - input_energy
                gross_energy_scale = dt * (
                    float(np.sum(np.abs(boundary_rates))) + abs(distributed_rate) + abs(generation_rate)
                )
                internal_redistribution_scale = sum(abs(value) for value in cell_energy_changes)
                scale = max(abs(energy_change), gross_energy_scale, internal_redistribution_scale, 1e-30)
                maximum_balance = max(maximum_balance, abs(residual))
                maximum_relative_balance = max(maximum_relative_balance, abs(residual) / scale)
                cumulative_boundary += dt * boundary_rates
                cumulative_distributed += dt * distributed_rate
                cumulative_generation += dt * generation_rate
                total_steps += 1
            history.append(temperature.tolist())
            conductivity = properties(temperature)
            output_rates = rates(temperature, interval, 1.0, conductivity)
            boundary_rate_history.append(output_rates[0].tolist())
            boundary_surface_history.append(output_rates[1])
            distributed_rate_history.append(output_rates[2])
            generation_rate_history.append(output_rates[3])
    except _PropertySupportError as error:
        return Calculation(
            status="out_of_scope",
            values={"material_property_lineage": material_property_lineage},
            notes=(str(error),),
        )

    status = (
        "computed" if maximum_relative_balance <= x.maximum_relative_energy_balance_error else "out_of_scope"
    )
    return Calculation(
        status=status,
        values=dict(
            material_property_lineage=material_property_lineage,
            cell_centers_m=centers.tolist(),
            temperature_history_K=history,
            boundary_surface_temperature_K=boundary_surface_history,
            boundary_heat_rate_into_solid_W=boundary_rate_history,
            distributed_heat_rate_into_solid_W=distributed_rate_history,
            volumetric_generation_rate_W=generation_rate_history,
            cumulative_boundary_energy_into_solid_J=cumulative_boundary.tolist(),
            cumulative_distributed_energy_into_solid_J=cumulative_distributed,
            cumulative_generated_energy_J=cumulative_generation,
            maximum_absolute_discrete_energy_balance_error_J=maximum_balance,
            maximum_relative_discrete_energy_balance_error=maximum_relative_balance,
            internal_steps=total_steps,
            maximum_nonlinear_iterations_used=maximum_iterations,
        ),
        notes=(
            "Cell-average backward-Euler finite-volume solution. Property curves are linearly interpolated without extrapolation and heat capacity is integrated as enthalpy.",
            "Boundary heat is positive into the solid. Numerical convergence and discrete energy balance do not qualify geometry, material properties or experimental agreement.",
        ),
    )


def _section_integrals(x: ThroughWallThermalStress):
    import numpy as np

    points, weights = np.polynomial.legendre.leggauss(12)
    centre = 0.5 * (x.position_m[0] + x.position_m[-1])
    values = {key: 0.0 for key in ("a", "b", "d", "nt", "mt")}
    for index, (left, right) in enumerate(zip(x.position_m, x.position_m[1:], strict=False)):
        half = 0.5 * (right - left)
        middle = 0.5 * (right + left)
        for point, weight in zip(points, weights, strict=True):
            position = middle + half * point
            fraction = (position - left) / (right - left)
            young = x.elastic_modulus_Pa[index] + fraction * (
                x.elastic_modulus_Pa[index + 1] - x.elastic_modulus_Pa[index]
            )
            poisson = x.poisson_ratio[index] + fraction * (
                x.poisson_ratio[index + 1] - x.poisson_ratio[index]
            )
            modulus = young if x.plane_condition == "uniaxial_plane_stress" else young / (1 - poisson)
            temperature = x.temperature_K[index] + fraction * (
                x.temperature_K[index + 1] - x.temperature_K[index]
            )
            expansion = x.secant_thermal_expansion_1_K[index] + fraction * (
                x.secant_thermal_expansion_1_K[index + 1] - x.secant_thermal_expansion_1_K[index]
            )
            thermal_strain = expansion * (temperature - x.reference_temperature_K)
            z = position - centre
            factor = half * weight
            values["a"] += factor * modulus
            values["b"] += factor * modulus * z
            values["d"] += factor * modulus * z * z
            values["nt"] += factor * modulus * thermal_strain
            values["mt"] += factor * modulus * thermal_strain * z
    return values, centre


def through_wall_thermal_stress(x: ThroughWallThermalStress) -> Calculation:
    import numpy as np

    temperature_field_lineage = {
        "source_result_sha256": x.temperature_source_result_sha256,
        "source_model_id": x.temperature_source_model_id,
        "source_model_version": x.temperature_source_model_version,
        "source_time_index": x.temperature_source_time_index,
        "source_time_s": x.temperature_source_time_s,
        "source_time_basis_id": x.temperature_source_time_basis_id,
        "source_asset_id": x.temperature_source_asset_id,
        "source_location_id": x.temperature_source_location_id,
        "temperature_to_section_mapping_reviewed": x.temperature_to_section_mapping_reviewed,
        "input_profile_sha256": canonical_digest({
            "position_m": x.position_m,
            "temperature_K": x.temperature_K,
        }),
    }
    property_values = {
        "secant_thermal_expansion_1_K": x.secant_thermal_expansion_1_K,
        "elastic_modulus_Pa": x.elastic_modulus_Pa,
        "poisson_ratio": x.poisson_ratio,
        "elastic_limit_Pa": x.elastic_limit_Pa,
    }
    property_provenance = {item.quantity: item for item in x.property_profile_evidence}
    mechanical_property_lineage = {
        quantity: {
            "profile_sha256": canonical_digest({
                "material_condition_id": x.material_condition_id,
                "position_m": x.position_m,
                "quantity": quantity,
                "values": values,
            }),
            "material_condition_id": x.material_condition_id,
            "provenance": (
                property_provenance[quantity].model_dump(mode="json")
                if quantity in property_provenance
                else None
            ),
            "provenance_status": (
                "caller_evidence_linked" if quantity in property_provenance else "caller_supplied_unprovenanced"
            ),
        }
        for quantity, values in property_values.items()
    }
    reviews = (
        x.plane_sections_reviewed,
        x.linear_elastic_response_reviewed,
        x.property_profiles_reviewed,
        x.applied_resultants_or_kinematics_reviewed,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values={"temperature_field_lineage": temperature_field_lineage,
                    "mechanical_property_lineage": mechanical_property_lineage},
            notes=("Section kinematics, elastic response, property profiles and loading require review.",),
        )
    integrals, centre = _section_integrals(x)
    if x.control == "resultant_controlled":
        right_force = float(x.membrane_force_N_m) + integrals["nt"]
        right_moment = float(x.bending_moment_N) + integrals["mt"]
        determinant = integrals["a"] * integrals["d"] - integrals["b"] ** 2
        midplane = (right_force * integrals["d"] - right_moment * integrals["b"]) / determinant
        curvature = (integrals["a"] * right_moment - integrals["b"] * right_force) / determinant
    else:
        midplane = float(x.midplane_total_strain)
        curvature = float(x.curvature_1_m)

    def state(position, temperature, expansion, young, poisson, limit):
        free = expansion * (temperature - x.reference_temperature_K)
        modulus = young if x.plane_condition == "uniaxial_plane_stress" else young / (1 - poisson)
        value = modulus * (midplane + curvature * (position - centre) - free)
        return free, value, abs(value) / limit

    stress = []
    thermal_strain = []
    utilization = []
    for values in zip(
        x.position_m,
        x.temperature_K,
        x.secant_thermal_expansion_1_K,
        x.elastic_modulus_Pa,
        x.poisson_ratio,
        x.elastic_limit_Pa,
        strict=True,
    ):
        free, value, ratio = state(*values)
        thermal_strain.append(free)
        stress.append(value)
        utilization.append(ratio)
    evaluated_stress = list(stress)
    evaluated_utilization = list(utilization)
    points, _ = np.polynomial.legendre.leggauss(12)
    for index, (left, right) in enumerate(zip(x.position_m, x.position_m[1:], strict=False)):
        for point in points:
            fraction = 0.5 * (float(point) + 1.0)
            interpolated = [
                values[index] + fraction * (values[index + 1] - values[index])
                for values in (
                    x.temperature_K,
                    x.secant_thermal_expansion_1_K,
                    x.elastic_modulus_Pa,
                    x.poisson_ratio,
                    x.elastic_limit_Pa,
                )
            ]
            _, value, ratio = state(left + fraction * (right - left), *interpolated)
            evaluated_stress.append(value)
            evaluated_utilization.append(ratio)
    force = integrals["a"] * midplane + integrals["b"] * curvature - integrals["nt"]
    moment = integrals["b"] * midplane + integrals["d"] * curvature - integrals["mt"]
    maximum = max(evaluated_utilization)
    status = "computed" if maximum <= 1.0 else "out_of_scope"
    target_force = float(x.membrane_force_N_m) if x.control == "resultant_controlled" else force
    target_moment = float(x.bending_moment_N) if x.control == "resultant_controlled" else moment
    return Calculation(
        status=status,
        values=dict(
            temperature_field_lineage=temperature_field_lineage,
            mechanical_property_lineage=mechanical_property_lineage,
            section_midpoint_m=centre,
            free_thermal_strain=thermal_strain,
            midplane_total_strain=midplane,
            curvature_1_m=curvature,
            stress_Pa=stress,
            membrane_force_N_m=force,
            bending_moment_N=moment,
            membrane_force_residual_N_m=force - target_force,
            bending_moment_residual_N=moment - target_moment,
            elastic_limit_utilization_at_profile_points=utilization,
            maximum_evaluated_elastic_limit_utilization=maximum,
            maximum_evaluated_tensile_stress_Pa=max(evaluated_stress),
            minimum_evaluated_compressive_stress_Pa=min(evaluated_stress),
            section_quadrature_order=12,
        ),
        notes=(
            "Piecewise-linear through-thickness input profiles with 12-point Gauss-Legendre integration in each interval.",
            "Stress and elastic-limit ratios are returned at supplied profile points; the reported extrema also sample the section quadrature points and are not a proof against unresolved between-point peaks.",
            "The output is a one-direction or equi-biaxial linear-elastic section stress. Pressure, discontinuity, plasticity, creep, residual stress, fracture and code classification are excluded.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "thermal.transient_conduction_1d",
            TransientConduction1D,
            transient_conduction_1d,
            {
                "cell_centers_m": "m",
                "temperature_history_K": "K",
                "boundary_surface_temperature_K": "K",
                "boundary_heat_rate_into_solid_W": "W",
                "distributed_heat_rate_into_solid_W": "W",
                "volumetric_generation_rate_W": "W",
                "cumulative_boundary_energy_into_solid_J": "J",
                "cumulative_distributed_energy_into_solid_J": "J",
                "cumulative_generated_energy_J": "J",
                "maximum_absolute_discrete_energy_balance_error_J": "J",
                "maximum_relative_discrete_energy_balance_error": "1",
                "internal_steps": "1",
                "maximum_nonlinear_iterations_used": "1",
            },
            (
                "One-dimensional planar or radial conduction with caller-supplied property curves, boundaries, distributed convection/gray radiation and heat generation.",
            ),
            ("transient_fvm_enthalpy",),
        ),
        ModelSpec(
            "mechanics.through_wall_thermal_stress",
            ThroughWallThermalStress,
            through_wall_thermal_stress,
            {
                "section_midpoint_m": "m",
                "free_thermal_strain": "1",
                "midplane_total_strain": "1",
                "curvature_1_m": "1/m",
                "stress_Pa": "Pa",
                "membrane_force_N_m": "N/m",
                "bending_moment_N": "N",
                "membrane_force_residual_N_m": "N/m",
                "bending_moment_residual_N": "N",
                "elastic_limit_utilization_at_profile_points": "1",
                "maximum_evaluated_elastic_limit_utilization": "1",
                "maximum_evaluated_tensile_stress_Pa": "Pa",
                "minimum_evaluated_compressive_stress_Pa": "Pa",
                "section_quadrature_order": "1",
            },
            (
                "Linear-elastic plane-section thermal stress under explicit resultants or explicit membrane strain and curvature.",
            ),
            ("thermoelastic_section_resultants",),
            context_validator=_validate_temperature_source_context,
        ),
    ]
