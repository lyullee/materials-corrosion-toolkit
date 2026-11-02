"""Declared load-to-life relations and cycle counting adapters."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .mechanics import Cylinder, lame_cylinder


class NeuberNotchStrainAmplitude(Contract):
    """Caller-qualified scalar notch data for a stabilized cyclic estimate."""

    nominal_stress_amplitude_Pa: Positive
    elastic_stress_concentration_factor: Positive = Field(ge=1.0)
    elastic_modulus_Pa: Positive
    cyclic_strength_coefficient_Pa: Positive
    cyclic_strain_hardening_exponent: Positive = Field(le=1.0)
    all_inputs_reviewed: bool
    max_iterations: int = Field(default=100, ge=10, le=200)
    relative_tolerance: Positive = Field(default=1e-12, le=1e-6)


def neuber_notch_strain_amplitude(x: NeuberNotchStrainAmplitude) -> Calculation:
    """Solve scalar Neuber/Ramberg–Osgood compatibility by bounded bisection."""
    if not x.all_inputs_reviewed:
        return Calculation(status="needs_data", values={"reason": "caller_review_required"})

    target = (
        x.elastic_stress_concentration_factor**2 * x.nominal_stress_amplitude_Pa**2 / x.elastic_modulus_Pa
    )

    lower = 0.0
    upper = x.elastic_stress_concentration_factor * x.nominal_stress_amplitude_Pa
    iterations = 0
    for iteration in range(1, x.max_iterations + 1):
        iterations = iteration
        local_stress = (lower + upper) / 2
        local_strain = local_stress / x.elastic_modulus_Pa + (
            local_stress / x.cyclic_strength_coefficient_Pa
        ) ** (1 / x.cyclic_strain_hardening_exponent)
        residual = local_stress * local_strain - target
        if abs(residual) <= x.relative_tolerance * target:
            break
        if residual < 0:
            lower = local_stress
        else:
            upper = local_stress
        if upper - lower <= x.relative_tolerance * upper:
            local_stress = (lower + upper) / 2
            local_strain = local_stress / x.elastic_modulus_Pa + (
                local_stress / x.cyclic_strength_coefficient_Pa
            ) ** (1 / x.cyclic_strain_hardening_exponent)
            residual = local_stress * local_strain - target
            break

    elastic_strain = local_stress / x.elastic_modulus_Pa
    plastic_strain = local_strain - elastic_strain
    converged = abs(residual) <= x.relative_tolerance * 10 * target
    return Calculation(
        status="computed" if converged else "out_of_scope",
        values={
            "local_stress_amplitude_Pa": local_stress,
            "local_strain_amplitude": local_strain,
            "elastic_strain_amplitude": elastic_strain,
            "plastic_strain_amplitude": plastic_strain,
            "neuber_target_Pa": target,
            "neuber_product_Pa": local_stress * local_strain,
            "relative_neuber_residual": abs(residual) / target,
            "iterations": iterations,
            "converged": converged,
        },
        notes=(
            "Scalar uniaxial stabilized cyclic estimate using caller-supplied elastic notch factor and cyclic Ramberg–Osgood properties.",
            "This result provides strain amplitude for downstream strain-life calculations; it does not predict life or cover multiaxiality, residual stress, cyclic transients, notch gradients or acceptance criteria.",
            "A failed numeric convergence is reported as out_of_scope and must not be passed to a downstream life model.",
        ),
    )


class NeuberStrainLifeChain(Contract):
    """Composable scalar notch estimate followed by a calibrated strain-life relation."""

    notch: NeuberNotchStrainAmplitude
    fatigue_strength_coefficient_Pa: Positive
    fatigue_strength_exponent: float = Field(lt=0)
    fatigue_ductility_coefficient: Positive
    fatigue_ductility_exponent: float = Field(lt=0)
    minimum_valid_cycles: Positive
    maximum_valid_cycles: Positive

    @model_validator(mode="after")
    def cycle_interval(self):
        if self.maximum_valid_cycles <= self.minimum_valid_cycles:
            raise ValueError("a nonempty calibrated cycle interval is required")
        return self


def neuber_strain_life_chain(x: NeuberStrainLifeChain) -> Calculation:
    """Pass the computed notch-root strain amplitude into the calibrated strain-life solver."""
    from .constitutive import StrainLife, strain_life

    notch = neuber_notch_strain_amplitude(x.notch)
    common = {
        "local_stress_amplitude_Pa": notch.values.get("local_stress_amplitude_Pa"),
        "local_strain_amplitude": notch.values.get("local_strain_amplitude"),
        "elastic_strain_amplitude": notch.values.get("elastic_strain_amplitude"),
        "plastic_strain_amplitude": notch.values.get("plastic_strain_amplitude"),
        "relative_neuber_residual": notch.values.get("relative_neuber_residual"),
        "neuber_iterations": notch.values.get("iterations"),
        "neuber_converged": notch.values.get("converged", False),
        "neuber_status": notch.status,
        "notch_reason": notch.values.get("reason"),
        "strain_life_status": "not_evaluated",
        "cycles_to_failure": None,
        "reversals_to_failure": None,
    }
    if notch.status != "computed":
        return Calculation(
            status=notch.status,
            values=common,
            notes=notch.notes
            + ("The strain-life calculation was not run because the notch solution was not computed.",),
        )

    life = strain_life(
        StrainLife.model_validate(
            {
                "strain_amplitude": notch.values["local_strain_amplitude"],
                "elastic_modulus_Pa": x.notch.elastic_modulus_Pa,
                "fatigue_strength_coefficient_Pa": x.fatigue_strength_coefficient_Pa,
                "fatigue_strength_exponent": x.fatigue_strength_exponent,
                "fatigue_ductility_coefficient": x.fatigue_ductility_coefficient,
                "fatigue_ductility_exponent": x.fatigue_ductility_exponent,
                "minimum_valid_cycles": x.minimum_valid_cycles,
                "maximum_valid_cycles": x.maximum_valid_cycles,
            }
        )
    )
    return Calculation(
        status=life.status,
        values=common
        | {
            "strain_life_status": life.status,
            "cycles_to_failure": life.values.get("cycles_to_failure"),
            "reversals_to_failure": life.values.get("reversals_to_failure"),
        },
        notes=notch.notes
        + life.notes
        + (
            "The strain-life stage uses only the notch-stage local strain amplitude and the supplied calibrated life coefficients and cycle interval.",
        ),
    )


class PressurizedAnnulusLoadState(Contract):
    reference_section_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    inner_radius_m: Positive
    outer_radius_m: Positive
    pressure_evaluation_radius_m: Positive
    external_axial_force_mean_N: float
    external_axial_force_amplitude_N: Nonnegative
    torque_mean_N_m: float
    torque_amplitude_N_m: Nonnegative
    axial_torsion_phase_rad: float = Field(ge=0.0, le=2 * math.pi)
    internal_pressure_Pa: Nonnegative
    external_pressure_Pa: Nonnegative = 0.0
    closed_ends: bool

    @model_validator(mode="after")
    def geometry(self):
        if not self.inner_radius_m < self.outer_radius_m:
            raise ValueError("positive annular thickness required")
        if not self.inner_radius_m <= self.pressure_evaluation_radius_m <= self.outer_radius_m:
            raise ValueError("pressure evaluation point must lie inside the annular wall")
        return self


def pressurized_annulus_load_state(x: PressurizedAnnulusLoadState) -> Calculation:
    """Resolve nominal axial/torsional loads and Lamé pressure stresses without predicting life."""
    a, b = x.inner_radius_m, x.outer_radius_m
    area = math.pi * (b * b - a * a)
    polar_moment = math.pi * (b**4 - a**4) / 2
    pressure = lame_cylinder(
        Cylinder(
            inner_radius_m=a,
            outer_radius_m=b,
            internal_pressure_Pa=x.internal_pressure_Pa,
            external_pressure_Pa=x.external_pressure_Pa,
            evaluation_radius_m=x.pressure_evaluation_radius_m,
            closed_ends=x.closed_ends,
        )
    ).values
    external_axial_mean = x.external_axial_force_mean_N / area
    external_axial_amplitude = x.external_axial_force_amplitude_N / area
    torsional_mean = x.torque_mean_N_m * b / polar_moment
    torsional_amplitude = x.torque_amplitude_N_m * b / polar_moment
    pressure_axial = pressure["axial_stress_Pa"]
    return Calculation(
        values={
            "reference_area_m2": area,
            "polar_second_moment_m4": polar_moment,
            "external_axial_mean_Pa": external_axial_mean,
            "external_axial_amplitude_Pa": external_axial_amplitude,
            "external_axial_minimum_Pa": external_axial_mean - external_axial_amplitude,
            "external_axial_maximum_Pa": external_axial_mean + external_axial_amplitude,
            "torsional_shear_mean_Pa": torsional_mean,
            "torsional_shear_amplitude_Pa": torsional_amplitude,
            "torsional_shear_minimum_Pa": torsional_mean - torsional_amplitude,
            "torsional_shear_maximum_Pa": torsional_mean + torsional_amplitude,
            "pressure_hoop_mean_Pa": pressure["hoop_stress_Pa"],
            "pressure_radial_mean_Pa": pressure["radial_stress_Pa"],
            "pressure_axial_mean_Pa": pressure_axial,
            "combined_axial_mean_Pa": external_axial_mean + pressure_axial,
            "axial_torsion_phase_rad": x.axial_torsion_phase_rad,
        },
        notes=(
            "The reference axial and torsional stresses use the declared annular section; torsional shear is evaluated at its outer radius.",
            "Pressure stresses are static Lamé components at the declared wall radius. The externally applied axial amplitude excludes pressure-induced axial stress.",
            "This is a stress-state preparation step, not a notch-root solution, fatigue criterion, fatigue-strength estimate, life prediction or acceptance decision.",
        ),
    )


class FatigueLoadingSegment(Contract):
    """Reviewed valid loading cycles for one physical specimen and load case."""

    segment_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    valid_loading_cycles: Nonnegative
    cycle_count_basis: Literal[
        "provider_cumulative_difference",
        "segment_local_counter",
        "reviewed_manual",
    ]


class PressureLossFatigueEndpoint(Contract):
    segments: list[FatigueLoadingSegment] = Field(min_length=1)
    initial_pressure_Pa: Positive
    observed_pressure_drop_Pa: Nonnegative
    declared_drop_fraction_threshold: float = Field(gt=0.0, le=1.0)
    event_origin: Literal["none", "specimen", "pressure_system", "instrumentation", "unresolved"]
    specimen_event_kind: Literal["none", "through_wall_crack", "rupture", "other"]
    specimen_pressure_loss_confirmed: bool
    same_physical_specimen_across_segments_declared: bool
    loading_history_reconstructable: bool
    runout_limit_cycles: Positive
    observation_window_closed: bool

    @model_validator(mode="after")
    def consistent_event_record(self):
        segment_ids = [segment.segment_id for segment in self.segments]
        if len(set(segment_ids)) != len(segment_ids):
            raise ValueError("loading segment identifiers must be unique")
        load_case_ids = {segment.load_case_id for segment in self.segments}
        if len(load_case_ids) != 1:
            raise ValueError("cumulative valid cycles require one common load case")
        specimen_ids = {segment.physical_specimen_id for segment in self.segments}
        if self.same_physical_specimen_across_segments_declared and len(specimen_ids) != 1:
            raise ValueError("declared same-specimen segments must share one physical specimen identifier")
        if self.observed_pressure_drop_Pa > self.initial_pressure_Pa:
            raise ValueError("observed pressure drop cannot exceed initial pressure")
        if self.event_origin != "specimen" and (
            self.specimen_event_kind != "none" or self.specimen_pressure_loss_confirmed
        ):
            raise ValueError("specimen confirmation fields require a specimen-origin event")
        return self


def pressure_loss_fatigue_endpoint(x: PressureLossFatigueEndpoint) -> Calculation:
    """Classify a pressure-loss fatigue-test endpoint without inferring fatigue strength or life."""
    cumulative_cycles = sum(segment.valid_loading_cycles for segment in x.segments)
    drop_fraction = x.observed_pressure_drop_Pa / x.initial_pressure_Pa
    threshold_met = drop_fraction >= x.declared_drop_fraction_threshold
    runout_reached = cumulative_cycles >= x.runout_limit_cycles
    same_specimen = len({segment.physical_specimen_id for segment in x.segments}) == 1
    history_usable = (
        x.same_physical_specimen_across_segments_declared
        and same_specimen
        and x.loading_history_reconstructable
    )

    status: Literal["computed", "needs_data"] = "computed"
    classification = "ongoing_or_incomplete"
    resume_eligible = False
    usable_observation = False
    censoring_role = "none"
    cycles_at_endpoint = None

    if not history_usable:
        status = "needs_data"
        classification = "invalid_or_ambiguous_history"
    elif x.event_origin == "specimen":
        qualified_kind = x.specimen_event_kind in {"through_wall_crack", "rupture"}
        if x.specimen_pressure_loss_confirmed and threshold_met and qualified_kind:
            classification = "confirmed_specimen_pressure_loss_endpoint"
            usable_observation = True
            censoring_role = "failure_endpoint"
            cycles_at_endpoint = cumulative_cycles
        else:
            status = "needs_data"
            classification = "specimen_event_needs_review"
    elif x.event_origin in {"pressure_system", "instrumentation"}:
        classification = "system_or_instrument_interruption"
        resume_eligible = True
    elif x.event_origin == "unresolved":
        status = "needs_data"
        classification = "unresolved_event_origin"
    elif threshold_met:
        status = "needs_data"
        classification = "unresolved_pressure_loss"
    elif x.observation_window_closed and runout_reached:
        classification = "runout"
        usable_observation = True
        censoring_role = "right_censored_runout"
    else:
        status = "needs_data"

    return Calculation(
        status=status,
        values={
            "cumulative_valid_cycles": cumulative_cycles,
            "pressure_drop_fraction": drop_fraction,
            "declared_threshold_fraction": x.declared_drop_fraction_threshold,
            "pressure_drop_margin_Pa": (
                x.initial_pressure_Pa * x.declared_drop_fraction_threshold - x.observed_pressure_drop_Pa
            ),
            "threshold_met": threshold_met,
            "runout_reached": runout_reached,
            "endpoint_classification": classification,
            "resume_eligible": resume_eligible,
            "usable_as_fatigue_observation": usable_observation,
            "censoring_role": censoring_role,
            "cycles_at_confirmed_endpoint": cycles_at_endpoint,
            "segment_count": len(x.segments),
        },
        notes=(
            "A pressure-drop threshold alone does not establish specimen failure; event origin and specimen confirmation remain separate evidence.",
            "Only reviewed valid cycles from one declared physical specimen and one load case are accumulated. System and instrumentation interruptions are not runouts.",
            "A runout is a right-censored test observation, not a fatigue-strength value, life prediction, acceptance decision or period failure probability.",
        ),
    )


class CriticalPlaneCandidate(Contract):
    """One caller-declared plane normal and one shear direction in that plane."""

    plane_id: str = Field(min_length=1)
    normal: list[float] = Field(min_length=3, max_length=3)
    in_plane_direction: list[float] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def orthonormal_frame(self):
        normal_norm = math.sqrt(sum(value * value for value in self.normal))
        direction_norm = math.sqrt(sum(value * value for value in self.in_plane_direction))
        dot = sum(
            normal * direction for normal, direction in zip(self.normal, self.in_plane_direction, strict=True)
        )
        if not math.isclose(normal_norm, 1.0, rel_tol=0.0, abs_tol=1e-8):
            raise ValueError("critical-plane normal must be a supplied unit vector")
        if not math.isclose(direction_norm, 1.0, rel_tol=0.0, abs_tol=1e-8):
            raise ValueError("in-plane direction must be a supplied unit vector")
        if not math.isclose(dot, 0.0, rel_tol=0.0, abs_tol=1e-8):
            raise ValueError("critical-plane normal and in-plane direction must be orthogonal")
        return self


class HemispherePlaneGrid(Contract):
    """Deterministic angular candidate grid for unoriented material planes."""

    grid_id: str = Field(min_length=1)
    polar_divisions: int = Field(ge=1)
    azimuthal_divisions: int = Field(ge=4)

    @model_validator(mode="after")
    def even_azimuthal_count(self):
        if self.azimuthal_divisions % 2:
            raise ValueError("an even azimuthal division count is required to deduplicate equatorial planes")
        return self


class AreaUniformFibonacciPlaneGrid(Contract):
    """Area-stratified golden-angle candidates for unoriented material planes."""

    grid_id: str = Field(min_length=1)
    candidate_count: int = Field(ge=4)
    azimuth_phase_rad: float = Field(default=0.0, ge=0.0, lt=2 * math.pi)


def _canonical_in_plane_direction(normal: list[float]) -> list[float]:
    axes = ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0])
    reference = min(axes, key=lambda axis: abs(sum(a * b for a, b in zip(axis, normal, strict=True))))
    direction = _cross(normal, reference)
    norm = math.sqrt(sum(value * value for value in direction))
    return [value / norm for value in direction]


def hemisphere_plane_grid(x: HemispherePlaneGrid) -> Calculation:
    """Generate a reproducible finite grid of unoriented plane normals and local frames."""
    polar_step = math.pi / (2 * x.polar_divisions)
    azimuthal_step = 2 * math.pi / x.azimuthal_divisions
    candidates = []
    candidate_angles = []
    for polar_index in range(x.polar_divisions + 1):
        theta = polar_index * polar_step
        if polar_index == 0:
            azimuthal_indices = range(1)
        elif polar_index == x.polar_divisions:
            azimuthal_indices = range(x.azimuthal_divisions // 2)
        else:
            azimuthal_indices = range(x.azimuthal_divisions)
        for azimuthal_index in azimuthal_indices:
            phi = azimuthal_index * azimuthal_step
            normal = [
                math.sin(theta) * math.cos(phi),
                math.sin(theta) * math.sin(phi),
                math.cos(theta),
            ]
            normal = [0.0 if abs(value) < 1e-15 else value for value in normal]
            plane_id = f"{x.grid_id}:polar-{polar_index:04d}:azimuth-{azimuthal_index:04d}"
            candidates.append(
                {
                    "plane_id": plane_id,
                    "normal": normal,
                    "in_plane_direction": _canonical_in_plane_direction(normal),
                }
            )
            candidate_angles.append(
                {
                    "plane_id": plane_id,
                    "polar_angle_rad": theta,
                    "azimuthal_angle_rad": phi,
                }
            )
    return Calculation(
        values={
            "grid_id": x.grid_id,
            "candidate_count": len(candidates),
            "polar_divisions": x.polar_divisions,
            "azimuthal_divisions": x.azimuthal_divisions,
            "polar_step_rad": polar_step,
            "azimuthal_step_rad": azimuthal_step,
            "candidate_planes": candidates,
            "candidate_angles": candidate_angles,
        },
        notes=(
            "Plane normals are unoriented: n and -n describe the same material plane. The upper hemisphere includes one pole and only half of the equatorial azimuths to remove those exact sign duplicates.",
            "This latitude-azimuth grid is deterministic but not equal-area and does not prove angular coverage or convergence. Compare explicitly refined grids before using a maximum as numerically resolved.",
            "The generated in-plane direction is a deterministic orthonormal frame choice for downstream scalar or vector-path projection; it has no material-direction meaning unless the caller assigns one.",
        ),
    )


def area_uniform_fibonacci_plane_grid(x: AreaUniformFibonacciPlaneGrid) -> Calculation:
    """Generate equal-solid-angle-stratified plane candidates with golden-angle azimuths."""
    golden_angle = math.pi * (3 - math.sqrt(5))
    nominal_weight = 2 * math.pi / x.candidate_count
    candidates = []
    sampling_positions = []
    for index in range(x.candidate_count):
        z = (index + 0.5) / x.candidate_count
        phi = (x.azimuth_phase_rad + index * golden_angle) % (2 * math.pi)
        radial = math.sqrt(max(0.0, 1 - z * z))
        normal = [radial * math.cos(phi), radial * math.sin(phi), z]
        normal = [0.0 if abs(value) < 1e-15 else value for value in normal]
        plane_id = f"{x.grid_id}:fibonacci-{index:06d}"
        candidates.append(
            {
                "plane_id": plane_id,
                "normal": normal,
                "in_plane_direction": _canonical_in_plane_direction(normal),
            }
        )
        sampling_positions.append(
            {
                "plane_id": plane_id,
                "sequence_index": index,
                "equal_area_coordinate_z": z,
                "polar_angle_rad": math.acos(z),
                "azimuthal_angle_rad": phi,
                "nominal_solid_angle_weight_sr": nominal_weight,
            }
        )
    return Calculation(
        values={
            "grid_id": x.grid_id,
            "candidate_count": x.candidate_count,
            "azimuth_phase_rad": x.azimuth_phase_rad,
            "golden_angle_rad": golden_angle,
            "nominal_solid_angle_weight_sr": nominal_weight,
            "nominal_weight_sum_sr": nominal_weight * x.candidate_count,
            "candidate_planes": candidates,
            "sampling_positions": sampling_positions,
        },
        notes=(
            "Unoriented planes are represented by normals strictly inside the positive-z hemisphere; one midpoint is placed in each equal-area z stratum and golden-angle azimuths reduce meridional alignment.",
            "The equal nominal weights are quadrature metadata, not measured Voronoi-cell areas. This finite deterministic sequence does not prove a covering radius, exact equal-area tessellation, nested refinement or a continuous-plane optimum.",
            "The generated in-plane direction is a coordinate-frame choice only. Compare phase shifts, candidate counts and another grid family before treating a sampled maximum as numerically stable.",
        ),
    )


class CriticalPlaneHistory(Contract):
    """Reviewed local tensor history for a declared representative cycle."""

    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    load_case_id: str | None = Field(default=None, min_length=1)
    tensor_provider_id: str | None = Field(default=None, min_length=1)
    tensor_provider_version: str | None = Field(default=None, min_length=1)
    solver_name: str | None = Field(default=None, min_length=1)
    solver_version: str | None = Field(default=None, min_length=1)
    analysis_id: str | None = Field(default=None, min_length=1)
    solution_revision: str | None = Field(default=None, min_length=1)
    mesh_id: str | None = Field(default=None, min_length=1)
    field_location_kind: Literal["node", "integration_point", "surface_point", "user_defined"] | None = None
    field_location_id: str | None = Field(default=None, min_length=1)
    spatial_averaging: Literal["none", "nodal_averaged", "element_averaged", "other"] | None = None
    coordinate_frame_id: str | None = Field(default=None, min_length=1)
    coordinate_basis_vectors_global: list[list[float]] | None = None
    stress_measure: Literal["cauchy"] | None = None
    strain_measure: Literal["infinitesimal"] | None = None
    input_strain_shear_convention: Literal["tensor", "engineering"] | None = None
    source_content_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    provider_configuration_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    tensor_history_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    sample_ids: list[str] = Field(min_length=3)
    sample_times_s: list[Nonnegative] | None = None
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3)
    strain_tensor_components: list[list[float]] = Field(min_length=3)
    candidate_planes: list[CriticalPlaneCandidate] = Field(min_length=1)
    representative_cycle_declared: bool
    maximum_stress_closure_error_Pa: Nonnegative
    maximum_strain_closure_error: Nonnegative
    fatemi_socie_coefficient: Nonnegative
    normalization_stress_Pa: Positive

    @model_validator(mode="after")
    def aligned_history(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample identifiers must be unique and preserve path order")
        if self.sample_times_s is not None:
            if len(self.sample_times_s) != count:
                raise ValueError("sample identifiers and times must align")
            if any(
                later <= earlier
                for earlier, later in zip(self.sample_times_s, self.sample_times_s[1:], strict=False)
            ):
                raise ValueError("sample times must be strictly increasing")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample, stress-tensor and strain-tensor histories must align")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        if self.coordinate_basis_vectors_global is not None:
            if len(self.coordinate_basis_vectors_global) != 3 or any(
                len(axis) != 3 for axis in self.coordinate_basis_vectors_global
            ):
                raise ValueError("coordinate-frame basis needs three three-component vectors")
        plane_ids = [plane.plane_id for plane in self.candidate_planes]
        if len(set(plane_ids)) != len(plane_ids):
            raise ValueError("candidate plane identifiers must be unique")
        return self


def _symmetric_tensor_frobenius_difference(last: list[float], first: list[float]) -> float:
    difference = [end - start for end, start in zip(last, first, strict=True)]
    return math.sqrt(
        difference[0] ** 2
        + difference[1] ** 2
        + difference[2] ** 2
        + 2 * (difference[3] ** 2 + difference[4] ** 2 + difference[5] ** 2)
    )


def _tensor_product(left: list[float], tensor: list[float], right: list[float]) -> float:
    xx, yy, zz, xy, yz, zx = tensor
    return (
        left[0] * (xx * right[0] + xy * right[1] + zx * right[2])
        + left[1] * (xy * right[0] + yy * right[1] + yz * right[2])
        + left[2] * (zx * right[0] + yz * right[1] + zz * right[2])
    )


def _cross(left: list[float], right: list[float]) -> list[float]:
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def _maximum_pairwise_chord(
    points: list[tuple[float, float]], sample_ids: list[str]
) -> tuple[float, str, str]:
    maximum_squared = -1.0
    endpoint_indices = (0, 1)
    for first in range(len(points) - 1):
        for second in range(first + 1, len(points)):
            squared = sum(
                (right - left) ** 2 for left, right in zip(points[first], points[second], strict=True)
            )
            if squared > maximum_squared:
                maximum_squared = squared
                endpoint_indices = (first, second)
    first, second = endpoint_indices
    return math.sqrt(maximum_squared), sample_ids[first], sample_ids[second]


def _minimum_enclosing_circle(
    points: list[tuple[float, float]], sample_ids: list[str]
) -> tuple[tuple[float, float], float, list[str]]:
    """Return the exact finite-point circle from a deterministic incremental construction."""

    def contains(circle, point):
        center, radius, _ = circle
        distance_squared = (point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2
        radius_squared = radius * radius
        tolerance = 1e-12 * max(radius_squared, distance_squared, 1e-300)
        return distance_squared <= radius_squared + tolerance

    def point_circle(index):
        return points[index], 0.0, [index]

    def diameter_circle(first, second):
        center = (
            (points[first][0] + points[second][0]) / 2,
            (points[first][1] + points[second][1]) / 2,
        )
        radius = math.hypot(points[first][0] - center[0], points[first][1] - center[1])
        return center, radius, [first, second]

    def three_point_circle(first, second, third):
        a, b, c = points[first], points[second], points[third]
        determinant = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
        span_squared = max(
            (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2,
            (a[0] - c[0]) ** 2 + (a[1] - c[1]) ** 2,
            (b[0] - c[0]) ** 2 + (b[1] - c[1]) ** 2,
        )
        if abs(determinant) <= 1e-14 * max(span_squared, 1e-300):
            pairs = ((first, second), (first, third), (second, third))
            return max(
                (diameter_circle(left, right) for left, right in pairs),
                key=lambda circle: circle[1],
            )
        a_squared = a[0] ** 2 + a[1] ** 2
        b_squared = b[0] ** 2 + b[1] ** 2
        c_squared = c[0] ** 2 + c[1] ** 2
        center = (
            (a_squared * (b[1] - c[1]) + b_squared * (c[1] - a[1]) + c_squared * (a[1] - b[1])) / determinant,
            (a_squared * (c[0] - b[0]) + b_squared * (a[0] - c[0]) + c_squared * (b[0] - a[0])) / determinant,
        )
        radius = math.hypot(a[0] - center[0], a[1] - center[1])
        return center, radius, [first, second, third]

    circle = point_circle(0)
    for first in range(1, len(points)):
        if contains(circle, points[first]):
            continue
        circle = point_circle(first)
        for second in range(first):
            if contains(circle, points[second]):
                continue
            circle = diameter_circle(first, second)
            for third in range(second):
                if not contains(circle, points[third]):
                    circle = three_point_circle(first, second, third)
    center, radius, support_indices = circle
    support_ids = [sample_ids[index] for index in dict.fromkeys(support_indices)]
    return center, radius, support_ids


def critical_plane_factors(x: CriticalPlaneHistory) -> Calculation:
    """Resolve FS and SWT factors on declared planes without predicting fatigue life."""
    stress_closure = _symmetric_tensor_frobenius_difference(
        x.stress_tensor_components_Pa[-1], x.stress_tensor_components_Pa[0]
    )
    strain_closure = _symmetric_tensor_frobenius_difference(
        x.strain_tensor_components[-1], x.strain_tensor_components[0]
    )
    cycle_usable = (
        x.representative_cycle_declared
        and stress_closure <= x.maximum_stress_closure_error_Pa
        and strain_closure <= x.maximum_strain_closure_error
    )
    common_values = {
        "history_id": x.history_id,
        "material_condition_id": x.material_condition_id,
        "location_id": x.location_id,
        "tensor_source_id": x.tensor_source_id,
        "sample_count": len(x.sample_ids),
        "candidate_count": len(x.candidate_planes),
        "stress_closure_error_Pa": stress_closure,
        "strain_closure_error": strain_closure,
        "representative_cycle_usable": cycle_usable,
    }
    notes = (
        "Input strain components are tensor shear strains, so resolved engineering shear strain is twice m dot epsilon dot n.",
        "Only the supplied orthonormal plane/direction pairs are evaluated; this is not a continuous orientation search or a path-dependent maximum-shear-range algorithm.",
        "The factors are not fatigue strength, life, acceptance, damage accumulation or period failure probability; calibration and independent experimental validation remain separate.",
    )
    if not cycle_usable:
        return Calculation(
            status="needs_data",
            values=common_values
            | {
                "candidate_factors": [],
                "maximum_fatemi_socie_factor": None,
                "fatemi_socie_plane_id": None,
                "maximum_swt_factor_Pa": None,
                "swt_plane_id": None,
            },
            notes=notes
            + (
                "A declared complete representative cycle within both endpoint-closure tolerances is required before ranges are evaluated.",
            ),
        )

    candidates = []
    for plane in x.candidate_planes:
        normal_stress = [
            _tensor_product(plane.normal, tensor, plane.normal) for tensor in x.stress_tensor_components_Pa
        ]
        normal_strain = [
            _tensor_product(plane.normal, tensor, plane.normal) for tensor in x.strain_tensor_components
        ]
        shear_stress = [
            _tensor_product(plane.in_plane_direction, tensor, plane.normal)
            for tensor in x.stress_tensor_components_Pa
        ]
        engineering_shear_strain = [
            2 * _tensor_product(plane.in_plane_direction, tensor, plane.normal)
            for tensor in x.strain_tensor_components
        ]
        maximum_normal_stress = max(normal_stress)
        maximum_tensile_normal_stress = max(maximum_normal_stress, 0.0)
        shear_strain_amplitude = (max(engineering_shear_strain) - min(engineering_shear_strain)) / 2
        normal_strain_amplitude = (max(normal_strain) - min(normal_strain)) / 2
        shear_stress_amplitude = (max(shear_stress) - min(shear_stress)) / 2
        fs_factor = shear_strain_amplitude * (
            1 + x.fatemi_socie_coefficient * maximum_tensile_normal_stress / x.normalization_stress_Pa
        )
        swt_factor = maximum_tensile_normal_stress * normal_strain_amplitude
        candidates.append(
            {
                "plane_id": plane.plane_id,
                "shear_strain_amplitude": shear_strain_amplitude,
                "shear_stress_amplitude_Pa": shear_stress_amplitude,
                "normal_strain_amplitude": normal_strain_amplitude,
                "maximum_normal_stress_Pa": maximum_normal_stress,
                "maximum_tensile_normal_stress_Pa": maximum_tensile_normal_stress,
                "fatemi_socie_factor": fs_factor,
                "swt_factor_Pa": swt_factor,
            }
        )
    fs_critical = max(candidates, key=lambda row: row["fatemi_socie_factor"])
    swt_critical = max(candidates, key=lambda row: row["swt_factor_Pa"])
    return Calculation(
        values=common_values
        | {
            "candidate_factors": candidates,
            "maximum_fatemi_socie_factor": fs_critical["fatemi_socie_factor"],
            "fatemi_socie_plane_id": fs_critical["plane_id"],
            "maximum_swt_factor_Pa": swt_critical["swt_factor_Pa"],
            "swt_plane_id": swt_critical["plane_id"],
        },
        notes=notes,
    )


def critical_plane_minimum_enclosing_circle_factors(x: CriticalPlaneHistory) -> Calculation:
    """Resolve sampled shear-path enclosing-circle factors on declared planes."""
    stress_closure = _symmetric_tensor_frobenius_difference(
        x.stress_tensor_components_Pa[-1], x.stress_tensor_components_Pa[0]
    )
    strain_closure = _symmetric_tensor_frobenius_difference(
        x.strain_tensor_components[-1], x.strain_tensor_components[0]
    )
    cycle_usable = (
        x.representative_cycle_declared
        and stress_closure <= x.maximum_stress_closure_error_Pa
        and strain_closure <= x.maximum_strain_closure_error
    )
    common_values = {
        "history_id": x.history_id,
        "material_condition_id": x.material_condition_id,
        "location_id": x.location_id,
        "tensor_source_id": x.tensor_source_id,
        "sample_count": len(x.sample_ids),
        "candidate_count": len(x.candidate_planes),
        "stress_closure_error_Pa": stress_closure,
        "strain_closure_error": strain_closure,
        "representative_cycle_usable": cycle_usable,
        "shear_path_range_method": "minimum_enclosing_circle_radius",
        "comparison_range_method": "half_maximum_pairwise_euclidean_chord",
    }
    notes = (
        "Each plane uses the supplied in-plane direction and its cross-product complement; the enclosing-circle radius is invariant to rotation, reversal and translation of this coordinate frame, while reported center coordinates remain frame components.",
        "The finite sampled shear path is enclosed by a deterministic incremental minimum circle supported by up to three samples. Path order is retained in sample identities but does not affect this range definition after cycle-closure review.",
        "The enclosing-circle radius and half maximum pairwise chord are reported separately. Neither definition bounds an unsampled continuous path, performs cycle counting, proves a continuous-plane optimum or supplies fatigue-life calibration.",
    )
    if not cycle_usable:
        return Calculation(
            status="needs_data",
            values=common_values
            | {
                "candidate_factors": [],
                "maximum_fatemi_socie_factor": None,
                "fatemi_socie_plane_id": None,
                "maximum_swt_factor_Pa": None,
                "swt_plane_id": None,
            },
            notes=notes
            + (
                "A declared complete representative cycle within both endpoint-closure tolerances is required before enclosing circles are evaluated.",
            ),
        )

    candidates = []
    for plane in x.candidate_planes:
        second_direction = _cross(plane.normal, plane.in_plane_direction)
        normal_stress = [
            _tensor_product(plane.normal, tensor, plane.normal) for tensor in x.stress_tensor_components_Pa
        ]
        normal_strain = [
            _tensor_product(plane.normal, tensor, plane.normal) for tensor in x.strain_tensor_components
        ]
        shear_stress_path = [
            (
                _tensor_product(plane.in_plane_direction, tensor, plane.normal),
                _tensor_product(second_direction, tensor, plane.normal),
            )
            for tensor in x.stress_tensor_components_Pa
        ]
        engineering_shear_strain_path = [
            (
                2 * _tensor_product(plane.in_plane_direction, tensor, plane.normal),
                2 * _tensor_product(second_direction, tensor, plane.normal),
            )
            for tensor in x.strain_tensor_components
        ]
        strain_center, strain_radius, strain_support = _minimum_enclosing_circle(
            engineering_shear_strain_path, x.sample_ids
        )
        stress_center, stress_radius, stress_support = _minimum_enclosing_circle(
            shear_stress_path, x.sample_ids
        )
        strain_chord, _, _ = _maximum_pairwise_chord(engineering_shear_strain_path, x.sample_ids)
        stress_chord, _, _ = _maximum_pairwise_chord(shear_stress_path, x.sample_ids)
        strain_chord_amplitude = strain_chord / 2
        stress_chord_amplitude = stress_chord / 2
        maximum_normal_stress = max(normal_stress)
        maximum_tensile_normal_stress = max(maximum_normal_stress, 0.0)
        normal_strain_amplitude = (max(normal_strain) - min(normal_strain)) / 2
        fs_factor = strain_radius * (
            1 + x.fatemi_socie_coefficient * maximum_tensile_normal_stress / x.normalization_stress_Pa
        )
        swt_factor = maximum_tensile_normal_stress * normal_strain_amplitude
        candidates.append(
            {
                "plane_id": plane.plane_id,
                "shear_strain_minimum_enclosing_circle_amplitude": strain_radius,
                "shear_strain_circle_center": list(strain_center),
                "shear_strain_circle_support_sample_ids": strain_support,
                "shear_strain_vector_chord_amplitude": strain_chord_amplitude,
                "shear_strain_circle_to_chord_amplitude_ratio": (
                    strain_radius / strain_chord_amplitude if strain_chord_amplitude > 0.0 else 1.0
                ),
                "shear_stress_minimum_enclosing_circle_amplitude_Pa": stress_radius,
                "shear_stress_circle_center_Pa": list(stress_center),
                "shear_stress_circle_support_sample_ids": stress_support,
                "shear_stress_vector_chord_amplitude_Pa": stress_chord_amplitude,
                "shear_stress_circle_to_chord_amplitude_ratio": (
                    stress_radius / stress_chord_amplitude if stress_chord_amplitude > 0.0 else 1.0
                ),
                "normal_strain_amplitude": normal_strain_amplitude,
                "maximum_normal_stress_Pa": maximum_normal_stress,
                "maximum_tensile_normal_stress_Pa": maximum_tensile_normal_stress,
                "fatemi_socie_factor": fs_factor,
                "swt_factor_Pa": swt_factor,
            }
        )
    fs_critical = max(candidates, key=lambda row: row["fatemi_socie_factor"])
    swt_critical = max(candidates, key=lambda row: row["swt_factor_Pa"])
    return Calculation(
        values=common_values
        | {
            "candidate_factors": candidates,
            "maximum_fatemi_socie_factor": fs_critical["fatemi_socie_factor"],
            "fatemi_socie_plane_id": fs_critical["plane_id"],
            "maximum_swt_factor_Pa": swt_critical["swt_factor_Pa"],
            "swt_plane_id": swt_critical["plane_id"],
        },
        notes=notes,
    )


def critical_plane_vector_path_factors(x: CriticalPlaneHistory) -> Calculation:
    """Resolve basis-invariant in-plane shear-vector chord factors on declared planes."""
    stress_closure = _symmetric_tensor_frobenius_difference(
        x.stress_tensor_components_Pa[-1], x.stress_tensor_components_Pa[0]
    )
    strain_closure = _symmetric_tensor_frobenius_difference(
        x.strain_tensor_components[-1], x.strain_tensor_components[0]
    )
    cycle_usable = (
        x.representative_cycle_declared
        and stress_closure <= x.maximum_stress_closure_error_Pa
        and strain_closure <= x.maximum_strain_closure_error
    )
    common_values = {
        "history_id": x.history_id,
        "material_condition_id": x.material_condition_id,
        "location_id": x.location_id,
        "tensor_source_id": x.tensor_source_id,
        "sample_count": len(x.sample_ids),
        "candidate_count": len(x.candidate_planes),
        "stress_closure_error_Pa": stress_closure,
        "strain_closure_error": strain_closure,
        "representative_cycle_usable": cycle_usable,
        "shear_path_range_method": "maximum_pairwise_euclidean_chord",
    }
    notes = (
        "Each plane uses the supplied in-plane unit direction and its cross-product complement as a two-dimensional basis; Euclidean chord length is invariant to rotation or reversal of that basis.",
        "The shear-strain amplitude is half the maximum pairwise chord of the sampled engineering-shear vector. This exact O(sample_count squared) discrete calculation is not a minimum-enclosing-circle, continuous-time extremum or cycle-counting method.",
        "Only the supplied plane normals are searched. The factors are not fatigue strength, life, acceptance, damage accumulation or period failure probability.",
    )
    if not cycle_usable:
        return Calculation(
            status="needs_data",
            values=common_values
            | {
                "candidate_factors": [],
                "maximum_fatemi_socie_factor": None,
                "fatemi_socie_plane_id": None,
                "maximum_swt_factor_Pa": None,
                "swt_plane_id": None,
            },
            notes=notes
            + (
                "A declared complete representative cycle within both endpoint-closure tolerances is required before path chords are evaluated.",
            ),
        )

    candidates = []
    for plane in x.candidate_planes:
        second_direction = _cross(plane.normal, plane.in_plane_direction)
        normal_stress = [
            _tensor_product(plane.normal, tensor, plane.normal) for tensor in x.stress_tensor_components_Pa
        ]
        normal_strain = [
            _tensor_product(plane.normal, tensor, plane.normal) for tensor in x.strain_tensor_components
        ]
        shear_stress_path = [
            (
                _tensor_product(plane.in_plane_direction, tensor, plane.normal),
                _tensor_product(second_direction, tensor, plane.normal),
            )
            for tensor in x.stress_tensor_components_Pa
        ]
        engineering_shear_strain_path = [
            (
                2 * _tensor_product(plane.in_plane_direction, tensor, plane.normal),
                2 * _tensor_product(second_direction, tensor, plane.normal),
            )
            for tensor in x.strain_tensor_components
        ]
        shear_strain_range, strain_start, strain_end = _maximum_pairwise_chord(
            engineering_shear_strain_path, x.sample_ids
        )
        shear_stress_range, stress_start, stress_end = _maximum_pairwise_chord(
            shear_stress_path, x.sample_ids
        )
        maximum_normal_stress = max(normal_stress)
        maximum_tensile_normal_stress = max(maximum_normal_stress, 0.0)
        shear_strain_amplitude = shear_strain_range / 2
        normal_strain_amplitude = (max(normal_strain) - min(normal_strain)) / 2
        fs_factor = shear_strain_amplitude * (
            1 + x.fatemi_socie_coefficient * maximum_tensile_normal_stress / x.normalization_stress_Pa
        )
        swt_factor = maximum_tensile_normal_stress * normal_strain_amplitude
        candidates.append(
            {
                "plane_id": plane.plane_id,
                "shear_strain_vector_chord_amplitude": shear_strain_amplitude,
                "shear_strain_chord_start_sample_id": strain_start,
                "shear_strain_chord_end_sample_id": strain_end,
                "shear_stress_vector_chord_amplitude_Pa": shear_stress_range / 2,
                "shear_stress_chord_start_sample_id": stress_start,
                "shear_stress_chord_end_sample_id": stress_end,
                "normal_strain_amplitude": normal_strain_amplitude,
                "maximum_normal_stress_Pa": maximum_normal_stress,
                "maximum_tensile_normal_stress_Pa": maximum_tensile_normal_stress,
                "fatemi_socie_factor": fs_factor,
                "swt_factor_Pa": swt_factor,
            }
        )
    fs_critical = max(candidates, key=lambda row: row["fatemi_socie_factor"])
    swt_critical = max(candidates, key=lambda row: row["swt_factor_Pa"])
    return Calculation(
        values=common_values
        | {
            "candidate_factors": candidates,
            "maximum_fatemi_socie_factor": fs_critical["fatemi_socie_factor"],
            "fatemi_socie_plane_id": fs_critical["plane_id"],
            "maximum_swt_factor_Pa": swt_critical["swt_factor_Pa"],
            "swt_plane_id": swt_critical["plane_id"],
        },
        notes=notes,
    )


class CriticalPlaneGridRefinement(Contract):
    """One reviewed tensor cycle evaluated on an explicitly ordered grid sequence."""

    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    sample_ids: list[str] = Field(min_length=3)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3)
    strain_tensor_components: list[list[float]] = Field(min_length=3)
    representative_cycle_declared: bool
    maximum_stress_closure_error_Pa: Nonnegative
    maximum_strain_closure_error: Nonnegative
    fatemi_socie_coefficient: Nonnegative
    normalization_stress_Pa: Positive
    refinement_levels: list[HemispherePlaneGrid] = Field(min_length=2)
    declared_maximum_relative_factor_change: Nonnegative
    declared_maximum_plane_rotation_rad: float = Field(ge=0.0, le=math.pi / 2)

    @model_validator(mode="after")
    def aligned_history_and_ordered_grids(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample identifiers must be unique and preserve path order")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample, stress-tensor and strain-tensor histories must align")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        grid_ids = [level.grid_id for level in self.refinement_levels]
        if len(set(grid_ids)) != len(grid_ids):
            raise ValueError("refinement grid identifiers must be unique")
        for coarse, fine in zip(self.refinement_levels, self.refinement_levels[1:], strict=False):
            coarse_count = (
                1
                + (coarse.polar_divisions - 1) * coarse.azimuthal_divisions
                + coarse.azimuthal_divisions // 2
            )
            fine_count = (
                1 + (fine.polar_divisions - 1) * fine.azimuthal_divisions + fine.azimuthal_divisions // 2
            )
            if (
                fine.polar_divisions < coarse.polar_divisions
                or fine.azimuthal_divisions < coarse.azimuthal_divisions
                or fine_count <= coarse_count
            ):
                raise ValueError(
                    "each refinement level must be nondecreasing in both divisions and increase candidate count"
                )
        return self


def _relative_change(previous: float, current: float) -> float:
    scale = max(abs(previous), abs(current))
    return 0.0 if scale == 0.0 else abs(current - previous) / scale


def _unoriented_plane_rotation(first: list[float], second: list[float]) -> float:
    alignment = abs(sum(a * b for a, b in zip(first, second, strict=True)))
    return math.acos(min(1.0, max(0.0, alignment)))


def critical_plane_grid_refinement(x: CriticalPlaneGridRefinement) -> Calculation:
    """Compare sampled vector-path maxima over an explicit finite-grid refinement sequence."""
    level_rows = []
    previous = None
    for level in x.refinement_levels:
        grid = hemisphere_plane_grid(level).values
        candidates = [CriticalPlaneCandidate.model_validate(row) for row in grid["candidate_planes"]]
        history = CriticalPlaneHistory(
            history_id=x.history_id,
            material_condition_id=x.material_condition_id,
            location_id=x.location_id,
            tensor_source_id=x.tensor_source_id,
            sample_ids=x.sample_ids,
            stress_tensor_components_Pa=x.stress_tensor_components_Pa,
            strain_tensor_components=x.strain_tensor_components,
            candidate_planes=candidates,
            representative_cycle_declared=x.representative_cycle_declared,
            maximum_stress_closure_error_Pa=x.maximum_stress_closure_error_Pa,
            maximum_strain_closure_error=x.maximum_strain_closure_error,
            fatemi_socie_coefficient=x.fatemi_socie_coefficient,
            normalization_stress_Pa=x.normalization_stress_Pa,
        )
        factors = critical_plane_vector_path_factors(history)
        if factors.status != "computed":
            return Calculation(
                status=factors.status,
                values={
                    "history_id": x.history_id,
                    "material_condition_id": x.material_condition_id,
                    "location_id": x.location_id,
                    "tensor_source_id": x.tensor_source_id,
                    "refinement_level_count": len(x.refinement_levels),
                    "evaluated_level_count": 0,
                    "levels": [],
                    "final_transition_within_declared_tolerances": None,
                    "all_transitions_within_declared_tolerances": None,
                },
                notes=factors.notes
                + (
                    "Grid refinement is not evaluated until the supplied history qualifies as one closed representative cycle.",
                ),
            )
        candidate_by_id = {row.plane_id: row for row in candidates}
        fs_plane_id = factors.values["fatemi_socie_plane_id"]
        swt_plane_id = factors.values["swt_plane_id"]
        row = {
            "grid_id": level.grid_id,
            "polar_divisions": level.polar_divisions,
            "azimuthal_divisions": level.azimuthal_divisions,
            "candidate_count": grid["candidate_count"],
            "polar_step_rad": grid["polar_step_rad"],
            "azimuthal_step_rad": grid["azimuthal_step_rad"],
            "maximum_fatemi_socie_factor": factors.values["maximum_fatemi_socie_factor"],
            "fatemi_socie_plane_id": fs_plane_id,
            "fatemi_socie_plane_normal": candidate_by_id[fs_plane_id].normal,
            "maximum_swt_factor_Pa": factors.values["maximum_swt_factor_Pa"],
            "swt_plane_id": swt_plane_id,
            "swt_plane_normal": candidate_by_id[swt_plane_id].normal,
            "transition_from_previous": None,
        }
        if previous is not None:
            transition = {
                "previous_grid_id": previous["grid_id"],
                "fatemi_socie_relative_change": _relative_change(
                    previous["maximum_fatemi_socie_factor"], row["maximum_fatemi_socie_factor"]
                ),
                "fatemi_socie_plane_rotation_rad": _unoriented_plane_rotation(
                    previous["fatemi_socie_plane_normal"], row["fatemi_socie_plane_normal"]
                ),
                "swt_relative_change": _relative_change(
                    previous["maximum_swt_factor_Pa"], row["maximum_swt_factor_Pa"]
                ),
                "swt_plane_rotation_rad": _unoriented_plane_rotation(
                    previous["swt_plane_normal"], row["swt_plane_normal"]
                ),
            }
            transition["within_declared_tolerances"] = (
                transition["fatemi_socie_relative_change"] <= x.declared_maximum_relative_factor_change
                and transition["swt_relative_change"] <= x.declared_maximum_relative_factor_change
                and transition["fatemi_socie_plane_rotation_rad"] <= x.declared_maximum_plane_rotation_rad
                and transition["swt_plane_rotation_rad"] <= x.declared_maximum_plane_rotation_rad
            )
            row["transition_from_previous"] = transition
        level_rows.append(row)
        previous = row
    transitions = [row["transition_from_previous"] for row in level_rows[1:]]
    return Calculation(
        values={
            "history_id": x.history_id,
            "material_condition_id": x.material_condition_id,
            "location_id": x.location_id,
            "tensor_source_id": x.tensor_source_id,
            "refinement_level_count": len(x.refinement_levels),
            "evaluated_level_count": len(level_rows),
            "declared_maximum_relative_factor_change": x.declared_maximum_relative_factor_change,
            "declared_maximum_plane_rotation_rad": x.declared_maximum_plane_rotation_rad,
            "levels": level_rows,
            "final_transition_within_declared_tolerances": transitions[-1]["within_declared_tolerances"],
            "all_transitions_within_declared_tolerances": all(
                transition["within_declared_tolerances"] for transition in transitions
            ),
            "range_method": "maximum_pairwise_euclidean_chord",
        },
        notes=(
            "Successive changes compare only the declared finite latitude-azimuth grids and the sampled tensor path; the user-supplied tolerances are diagnostics, not an automatic convergence proof.",
            "Plane rotation uses the acute angle between unoriented normals. Equivalent or near-equal maxima can switch planes and produce a large reported rotation without a large factor change.",
            "A stable final transition does not establish a continuous-plane optimum, time-sampling convergence, fatigue-life calibration, acceptance or independent experimental validation.",
        ),
    )


class CriticalPlaneGridFamilyComparison(Contract):
    """One tensor cycle evaluated on declared latitude and/or Fibonacci grids."""

    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    sample_ids: list[str] = Field(min_length=3)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3)
    strain_tensor_components: list[list[float]] = Field(min_length=3)
    grid_definitions: list[HemispherePlaneGrid | AreaUniformFibonacciPlaneGrid] = Field(min_length=2)
    reference_grid_id: str = Field(min_length=1)
    representative_cycle_declared: bool
    maximum_stress_closure_error_Pa: Nonnegative
    maximum_strain_closure_error: Nonnegative
    fatemi_socie_coefficient: Nonnegative
    normalization_stress_Pa: Positive
    declared_maximum_relative_factor_change: Nonnegative
    declared_maximum_plane_rotation_rad: float = Field(ge=0.0, le=math.pi / 2)

    @model_validator(mode="after")
    def aligned_history_and_unique_grids(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample identifiers must be unique and preserve path order")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample, stress-tensor and strain-tensor histories must align")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        grid_ids = [definition.grid_id for definition in self.grid_definitions]
        if len(set(grid_ids)) != len(grid_ids):
            raise ValueError("grid identifiers must be unique across the comparison")
        if self.reference_grid_id not in grid_ids:
            raise ValueError("reference grid identifier must name one supplied grid")
        return self


def _generate_declared_plane_grid(
    definition: HemispherePlaneGrid | AreaUniformFibonacciPlaneGrid,
) -> tuple[str, Calculation]:
    if isinstance(definition, HemispherePlaneGrid):
        return "latitude_azimuth", hemisphere_plane_grid(definition)
    return "area_uniform_fibonacci", area_uniform_fibonacci_plane_grid(definition)


def critical_plane_grid_family_comparison(x: CriticalPlaneGridFamilyComparison) -> Calculation:
    """Compare finite-grid family, count and phase sensitivity for one sampled cycle."""
    grid_rows = []
    for definition in x.grid_definitions:
        family, grid_result = _generate_declared_plane_grid(definition)
        candidates = [
            CriticalPlaneCandidate.model_validate(row) for row in grid_result.values["candidate_planes"]
        ]
        history = CriticalPlaneHistory(
            history_id=x.history_id,
            material_condition_id=x.material_condition_id,
            location_id=x.location_id,
            tensor_source_id=x.tensor_source_id,
            sample_ids=x.sample_ids,
            stress_tensor_components_Pa=x.stress_tensor_components_Pa,
            strain_tensor_components=x.strain_tensor_components,
            candidate_planes=candidates,
            representative_cycle_declared=x.representative_cycle_declared,
            maximum_stress_closure_error_Pa=x.maximum_stress_closure_error_Pa,
            maximum_strain_closure_error=x.maximum_strain_closure_error,
            fatemi_socie_coefficient=x.fatemi_socie_coefficient,
            normalization_stress_Pa=x.normalization_stress_Pa,
        )
        factors = critical_plane_vector_path_factors(history)
        if factors.status != "computed":
            return Calculation(
                status=factors.status,
                values={
                    "history_id": x.history_id,
                    "material_condition_id": x.material_condition_id,
                    "location_id": x.location_id,
                    "tensor_source_id": x.tensor_source_id,
                    "reference_grid_id": x.reference_grid_id,
                    "grid_count": len(x.grid_definitions),
                    "evaluated_grid_count": 0,
                    "grids": [],
                    "all_comparisons_within_declared_tolerances": None,
                },
                notes=factors.notes
                + (
                    "Grid-family comparison is not evaluated until the supplied history qualifies as one closed representative cycle.",
                ),
            )
        candidate_by_id = {row.plane_id: row for row in candidates}
        fs_plane_id = factors.values["fatemi_socie_plane_id"]
        swt_plane_id = factors.values["swt_plane_id"]
        grid_rows.append(
            {
                "grid_id": definition.grid_id,
                "grid_family": family,
                "grid_definition": definition.model_dump(mode="json"),
                "candidate_count": len(candidates),
                "maximum_fatemi_socie_factor": factors.values["maximum_fatemi_socie_factor"],
                "fatemi_socie_plane_id": fs_plane_id,
                "fatemi_socie_plane_normal": candidate_by_id[fs_plane_id].normal,
                "maximum_swt_factor_Pa": factors.values["maximum_swt_factor_Pa"],
                "swt_plane_id": swt_plane_id,
                "swt_plane_normal": candidate_by_id[swt_plane_id].normal,
                "comparison_to_reference": None,
            }
        )
    reference = next(row for row in grid_rows if row["grid_id"] == x.reference_grid_id)
    comparisons = []
    for row in grid_rows:
        if row is reference:
            continue
        comparison = {
            "reference_grid_id": x.reference_grid_id,
            "fatemi_socie_relative_change": _relative_change(
                reference["maximum_fatemi_socie_factor"], row["maximum_fatemi_socie_factor"]
            ),
            "fatemi_socie_plane_rotation_rad": _unoriented_plane_rotation(
                reference["fatemi_socie_plane_normal"], row["fatemi_socie_plane_normal"]
            ),
            "swt_relative_change": _relative_change(
                reference["maximum_swt_factor_Pa"], row["maximum_swt_factor_Pa"]
            ),
            "swt_plane_rotation_rad": _unoriented_plane_rotation(
                reference["swt_plane_normal"], row["swt_plane_normal"]
            ),
        }
        comparison["within_declared_tolerances"] = (
            comparison["fatemi_socie_relative_change"] <= x.declared_maximum_relative_factor_change
            and comparison["swt_relative_change"] <= x.declared_maximum_relative_factor_change
            and comparison["fatemi_socie_plane_rotation_rad"] <= x.declared_maximum_plane_rotation_rad
            and comparison["swt_plane_rotation_rad"] <= x.declared_maximum_plane_rotation_rad
        )
        row["comparison_to_reference"] = comparison
        comparisons.append(comparison)
    return Calculation(
        values={
            "history_id": x.history_id,
            "material_condition_id": x.material_condition_id,
            "location_id": x.location_id,
            "tensor_source_id": x.tensor_source_id,
            "reference_grid_id": x.reference_grid_id,
            "grid_count": len(x.grid_definitions),
            "evaluated_grid_count": len(grid_rows),
            "declared_maximum_relative_factor_change": x.declared_maximum_relative_factor_change,
            "declared_maximum_plane_rotation_rad": x.declared_maximum_plane_rotation_rad,
            "grids": grid_rows,
            "all_comparisons_within_declared_tolerances": all(
                comparison["within_declared_tolerances"] for comparison in comparisons
            ),
            "range_method": "maximum_pairwise_euclidean_chord",
        },
        notes=(
            "All grids evaluate the same sampled tensor cycle with the same vector-chord factor convention; differences isolate declared candidate-family, count and Fibonacci phase choices.",
            "Comparisons are relative to the explicitly named finite reference grid. Agreement with that grid does not establish a continuous-plane optimum or an orientation-error bound.",
            "A small cross-grid difference does not qualify time sampling, local tensor provenance, fatigue-life calibration, acceptance or independent experimental validity.",
        ),
    )


class CriticalPlaneAdaptiveSearch(Contract):
    """Greedy local orientation refinement seeded by one declared finite plane grid."""

    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    sample_ids: list[str] = Field(min_length=3)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3)
    strain_tensor_components: list[list[float]] = Field(min_length=3)
    seed_grid: HemispherePlaneGrid | AreaUniformFibonacciPlaneGrid
    representative_cycle_declared: bool
    maximum_stress_closure_error_Pa: Nonnegative
    maximum_strain_closure_error: Nonnegative
    fatemi_socie_coefficient: Nonnegative
    normalization_stress_Pa: Positive
    refinement_rounds: int = Field(ge=1)
    ring_points: int = Field(ge=4)
    initial_radius_rad: float = Field(gt=0.0, lt=math.pi / 2)
    radius_reduction_factor: float = Field(gt=0.0, lt=1.0)
    declared_maximum_final_relative_factor_change: Nonnegative
    declared_maximum_final_plane_rotation_rad: float = Field(ge=0.0, le=math.pi / 2)

    @model_validator(mode="after")
    def aligned_history(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample identifiers must be unique and preserve path order")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample, stress-tensor and strain-tensor histories must align")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        return self


def _canonicalize_unoriented_normal(normal: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in normal))
    normalized = [value / norm for value in normal]
    for value in (normalized[2], normalized[1], normalized[0]):
        if abs(value) > 1e-14:
            if value < 0.0:
                normalized = [-component for component in normalized]
            break
    return [0.0 if abs(value) < 1e-15 else value for value in normalized]


def _adaptive_ring_candidates(
    center: list[float], objective: str, round_index: int, radius_rad: float, ring_points: int
) -> list[CriticalPlaneCandidate]:
    tangent_u = _canonical_in_plane_direction(center)
    tangent_v = _cross(center, tangent_u)
    normals = [center]
    for index in range(ring_points):
        phase = 2 * math.pi * index / ring_points
        normal = [
            math.cos(radius_rad) * center[axis]
            + math.sin(radius_rad) * (math.cos(phase) * tangent_u[axis] + math.sin(phase) * tangent_v[axis])
            for axis in range(3)
        ]
        normals.append(_canonicalize_unoriented_normal(normal))
    candidates = []
    seen = set()
    for index, normal in enumerate(normals):
        key = tuple(round(value, 14) for value in normal)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(
            CriticalPlaneCandidate(
                plane_id=f"adaptive:{objective}:round-{round_index:04d}:candidate-{index:04d}",
                normal=normal,
                in_plane_direction=_canonical_in_plane_direction(normal),
            )
        )
    return candidates


def critical_plane_adaptive_search(x: CriticalPlaneAdaptiveSearch) -> Calculation:
    """Refine separate FS and SWT orientations around finite-grid seed maxima."""
    grid_family, grid_result = _generate_declared_plane_grid(x.seed_grid)
    seed_candidates = [
        CriticalPlaneCandidate.model_validate(row) for row in grid_result.values["candidate_planes"]
    ]

    def evaluate(candidates: list[CriticalPlaneCandidate]) -> Calculation:
        return critical_plane_vector_path_factors(
            CriticalPlaneHistory(
                history_id=x.history_id,
                material_condition_id=x.material_condition_id,
                location_id=x.location_id,
                tensor_source_id=x.tensor_source_id,
                sample_ids=x.sample_ids,
                stress_tensor_components_Pa=x.stress_tensor_components_Pa,
                strain_tensor_components=x.strain_tensor_components,
                candidate_planes=candidates,
                representative_cycle_declared=x.representative_cycle_declared,
                maximum_stress_closure_error_Pa=x.maximum_stress_closure_error_Pa,
                maximum_strain_closure_error=x.maximum_strain_closure_error,
                fatemi_socie_coefficient=x.fatemi_socie_coefficient,
                normalization_stress_Pa=x.normalization_stress_Pa,
            )
        )

    seed_factors = evaluate(seed_candidates)
    common = {
        "history_id": x.history_id,
        "material_condition_id": x.material_condition_id,
        "location_id": x.location_id,
        "tensor_source_id": x.tensor_source_id,
        "seed_grid_id": x.seed_grid.grid_id,
        "seed_grid_family": grid_family,
        "seed_candidate_count": len(seed_candidates),
        "refinement_rounds": x.refinement_rounds,
        "ring_points": x.ring_points,
        "initial_radius_rad": x.initial_radius_rad,
        "radius_reduction_factor": x.radius_reduction_factor,
        "range_method": "maximum_pairwise_euclidean_chord",
    }
    if seed_factors.status != "computed":
        return Calculation(
            status=seed_factors.status,
            values=common
            | {
                "evaluated_refinement_rounds": 0,
                "fatemi_socie_search": None,
                "swt_search": None,
                "both_final_transitions_within_declared_tolerances": None,
            },
            notes=seed_factors.notes
            + (
                "Adaptive orientation refinement is not evaluated until the supplied history qualifies as one closed representative cycle.",
            ),
        )

    seed_by_id = {candidate.plane_id: candidate for candidate in seed_candidates}

    def refine(objective: Literal["fatemi_socie", "swt"]):
        factor_key = "maximum_fatemi_socie_factor" if objective == "fatemi_socie" else "maximum_swt_factor_Pa"
        plane_key = "fatemi_socie_plane_id" if objective == "fatemi_socie" else "swt_plane_id"
        seed_plane_id = seed_factors.values[plane_key]
        center = seed_by_id[seed_plane_id].normal
        factor = seed_factors.values[factor_key]
        trace = []
        radius = x.initial_radius_rad
        for round_index in range(1, x.refinement_rounds + 1):
            candidates = _adaptive_ring_candidates(center, objective, round_index, radius, x.ring_points)
            local = evaluate(candidates)
            local_by_id = {candidate.plane_id: candidate for candidate in candidates}
            selected_id = local.values[plane_key]
            selected_normal = local_by_id[selected_id].normal
            selected_factor = local.values[factor_key]
            relative_change = _relative_change(factor, selected_factor)
            plane_rotation = _unoriented_plane_rotation(center, selected_normal)
            trace.append(
                {
                    "round_index": round_index,
                    "search_radius_rad": radius,
                    "candidate_count": len(candidates),
                    "selected_plane_id": selected_id,
                    "selected_plane_normal": selected_normal,
                    "factor": selected_factor,
                    "relative_factor_change": relative_change,
                    "plane_rotation_rad": plane_rotation,
                    "improved": selected_factor > factor,
                    "within_declared_tolerances": relative_change
                    <= x.declared_maximum_final_relative_factor_change
                    and plane_rotation <= x.declared_maximum_final_plane_rotation_rad,
                }
            )
            center = selected_normal
            factor = selected_factor
            radius *= x.radius_reduction_factor
        return {
            "seed_plane_id": seed_plane_id,
            "seed_plane_normal": seed_by_id[seed_plane_id].normal,
            "seed_factor": seed_factors.values[factor_key],
            "rounds": trace,
            "final_plane_normal": center,
            "final_factor": factor,
            "final_transition_within_declared_tolerances": trace[-1]["within_declared_tolerances"],
        }

    fs_search = refine("fatemi_socie")
    swt_search = refine("swt")
    return Calculation(
        values=common
        | {
            "evaluated_refinement_rounds": x.refinement_rounds,
            "declared_maximum_final_relative_factor_change": x.declared_maximum_final_relative_factor_change,
            "declared_maximum_final_plane_rotation_rad": x.declared_maximum_final_plane_rotation_rad,
            "fatemi_socie_search": fs_search,
            "swt_search": swt_search,
            "both_final_transitions_within_declared_tolerances": fs_search[
                "final_transition_within_declared_tolerances"
            ]
            and swt_search["final_transition_within_declared_tolerances"],
        },
        notes=(
            "FS and SWT are refined independently from their own finite-grid seed maxima by retaining the center and evaluating one deterministic tangent ring per round.",
            "This is a greedy local search. Its result depends on the seed grid, initial radius, ring count and radius schedule and is not a global continuous-orientation optimum or convergence proof.",
            "Declared final-step tolerances are diagnostics only; they do not qualify tensor provenance, time sampling, fatigue-life calibration, acceptance or independent experimental validity.",
        ),
    )


class CriticalPlaneContinuousBound(Contract):
    """Closed sampled cycle and budgets for a Lipschitz-bounded plane search."""

    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    tensor_history_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    sample_ids: list[str] = Field(min_length=3)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3)
    strain_tensor_components: list[list[float]] = Field(min_length=3)
    representative_cycle_declared: bool
    maximum_stress_closure_error_Pa: Nonnegative
    maximum_strain_closure_error: Nonnegative
    fatemi_socie_coefficient: Nonnegative
    normalization_stress_Pa: Positive
    maximum_refinement_level: int = Field(default=4, ge=0, le=5)
    maximum_candidate_evaluations: int = Field(default=15000, ge=12, le=20000)
    maximum_sample_pair_plane_work: int = Field(default=30_000_000, ge=1)
    fatemi_socie_bound_gap_tolerance: Nonnegative = 0.0
    swt_bound_gap_tolerance_Pa: Nonnegative = 0.0

    @model_validator(mode="after")
    def aligned_closed_history(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample identifiers must be unique and preserve path order")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample, stress-tensor and strain-tensor histories must align")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        return self


def _icosphere_vertices_and_faces(level: int) -> tuple[list[list[float]], list[tuple[int, int, int]]]:
    """Create a deterministic unit-sphere triangulation by normalized edge subdivision."""
    golden = (1 + math.sqrt(5.0)) / 2
    raw = [
        (-1, golden, 0), (1, golden, 0), (-1, -golden, 0), (1, -golden, 0),
        (0, -1, golden), (0, 1, golden), (0, -1, -golden), (0, 1, -golden),
        (golden, 0, -1), (golden, 0, 1), (-golden, 0, -1), (-golden, 0, 1),
    ]
    vertices = []
    for vector in raw:
        norm = math.sqrt(math.fsum(component * component for component in vector))
        vertices.append([component / norm for component in vector])
    faces = [
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
    ]
    for _ in range(level):
        midpoint_cache: dict[tuple[int, int], int] = {}

        def midpoint(left: int, right: int) -> int:
            edge = (min(left, right), max(left, right))
            if edge not in midpoint_cache:
                a, b = vertices[left], vertices[right]
                point = [a[axis] + b[axis] for axis in range(3)]
                norm = math.sqrt(math.fsum(component * component for component in point))
                midpoint_cache[edge] = len(vertices)
                vertices.append([component / norm for component in point])
            return midpoint_cache[edge]

        subdivided = []
        for a, b, c in faces:
            ab, bc, ca = midpoint(a, b), midpoint(b, c), midpoint(c, a)
            subdivided.extend(((a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)))
        faces = subdivided
    return vertices, faces


def _tensor_frobenius_norm(components: list[float]) -> float:
    return math.sqrt(
        components[0] ** 2 + components[1] ** 2 + components[2] ** 2
        + 2 * (components[3] ** 2 + components[4] ** 2 + components[5] ** 2)
    )


def critical_plane_continuous_bound(x: CriticalPlaneContinuousBound) -> Calculation:
    """Bound the continuous-plane maximum from a fully evaluated icosphere vertex net."""
    history_common = dict(
        history_id=x.history_id,
        material_condition_id=x.material_condition_id,
        location_id=x.location_id,
        tensor_source_id=x.tensor_source_id,
        sample_ids=x.sample_ids,
        stress_tensor_components_Pa=x.stress_tensor_components_Pa,
        strain_tensor_components=x.strain_tensor_components,
        representative_cycle_declared=x.representative_cycle_declared,
        maximum_stress_closure_error_Pa=x.maximum_stress_closure_error_Pa,
        maximum_strain_closure_error=x.maximum_strain_closure_error,
        fatemi_socie_coefficient=x.fatemi_socie_coefficient,
        normalization_stress_Pa=x.normalization_stress_Pa,
    )
    stress_closure = _symmetric_tensor_frobenius_difference(
        x.stress_tensor_components_Pa[-1], x.stress_tensor_components_Pa[0]
    )
    strain_closure = _symmetric_tensor_frobenius_difference(
        x.strain_tensor_components[-1], x.strain_tensor_components[0]
    )
    if not (
        x.representative_cycle_declared
        and stress_closure <= x.maximum_stress_closure_error_Pa
        and strain_closure <= x.maximum_strain_closure_error
    ):
        return Calculation(
            status="needs_data",
            values={
                "history_id": x.history_id,
                "tensor_history_record_digest": x.tensor_history_record_digest,
                "stress_closure_error_Pa": stress_closure,
                "strain_closure_error": strain_closure,
                "continuous_plane_bounds": None,
            },
            notes=("A reviewed closed representative tensor cycle is required before plane factors or bounds are evaluated.",),
        )

    strain_norm = max(_tensor_frobenius_norm(row) for row in x.strain_tensor_components)
    stress_norm = max(_tensor_frobenius_norm(row) for row in x.stress_tensor_components_Pa)
    # Bounds below use Euclidean chord amplitude for engineering shear and
    # operator projection bounds no larger than the symmetric-tensor Frobenius norm.
    fs_lipschitz = 6 * strain_norm * (1 + x.fatemi_socie_coefficient * stress_norm / x.normalization_stress_Pa)
    fs_lipschitz += 4 * strain_norm * x.fatemi_socie_coefficient * stress_norm / x.normalization_stress_Pa
    swt_lipschitz = 4 * stress_norm * strain_norm
    sample_pair_count = len(x.sample_ids) * (len(x.sample_ids) - 1) // 2
    seen_normals: set[tuple[float, float, float]] = set()
    best_fs = -math.inf
    best_swt = -math.inf
    best_fs_plane = None
    best_swt_plane = None
    evaluated = 0
    pair_plane_work = 0
    levels = []
    budget_exhausted = False

    for level in range(x.maximum_refinement_level + 1):
        vertices, faces = _icosphere_vertices_and_faces(level)
        new_planes = []
        for index, vertex in enumerate(vertices):
            normal = _canonicalize_unoriented_normal(vertex)
            key = tuple(round(value, 12) for value in normal)
            if key in seen_normals:
                continue
            seen_normals.add(key)
            new_planes.append(
                CriticalPlaneCandidate(
                    plane_id="icosphere:" + ":".join(f"{value:+.12f}" for value in normal),
                    normal=normal,
                    in_plane_direction=_canonical_in_plane_direction(normal),
                )
            )
        incremental_work = len(new_planes) * sample_pair_count
        if (
            evaluated + len(new_planes) > x.maximum_candidate_evaluations
            or pair_plane_work + incremental_work > x.maximum_sample_pair_plane_work
        ):
            budget_exhausted = True
            if not levels:
                return Calculation(
                    status="out_of_scope",
                    values={"history_id": x.history_id, "evaluated_candidate_count": 0, "continuous_plane_bounds": None},
                    notes=("Declared evaluation budgets do not permit even the base icosphere level.",),
                )
            break
        candidate_factors = critical_plane_vector_path_factors(
            CriticalPlaneHistory(candidate_planes=new_planes, **history_common)
        )
        if candidate_factors.status != "computed":
            return candidate_factors
        evaluated += len(new_planes)
        pair_plane_work += incremental_work
        for row in candidate_factors.values["candidate_factors"]:
            if row["fatemi_socie_factor"] > best_fs:
                best_fs = row["fatemi_socie_factor"]
                best_fs_plane = row["plane_id"]
            if row["swt_factor_Pa"] > best_swt:
                best_swt = row["swt_factor_Pa"]
                best_swt_plane = row["plane_id"]
        maximum_edge_angle = 0.0
        for a, b, c in faces:
            for left, right in ((a, b), (b, c), (c, a)):
                cosine = math.fsum(vertices[left][axis] * vertices[right][axis] for axis in range(3))
                maximum_edge_angle = max(maximum_edge_angle, math.acos(min(1.0, max(-1.0, cosine))))
        fs_gap = fs_lipschitz * maximum_edge_angle
        swt_gap = swt_lipschitz * maximum_edge_angle
        levels.append(
            dict(
                refinement_level=level,
                unique_unoriented_vertex_count=len(seen_normals),
                newly_evaluated_plane_count=len(new_planes),
                maximum_spherical_edge_angle_rad=maximum_edge_angle,
                sampled_maximum_fatemi_socie_factor=best_fs,
                fatemi_socie_continuous_upper_bound=best_fs + fs_gap,
                fatemi_socie_bound_gap=fs_gap,
                sampled_maximum_swt_factor_Pa=best_swt,
                swt_continuous_upper_bound_Pa=best_swt + swt_gap,
                swt_bound_gap_Pa=swt_gap,
            )
        )
        if (
            fs_gap <= x.fatemi_socie_bound_gap_tolerance
            and swt_gap <= x.swt_bound_gap_tolerance_Pa
        ):
            break

    final = levels[-1]
    fs_within = final["fatemi_socie_bound_gap"] <= x.fatemi_socie_bound_gap_tolerance
    swt_within = final["swt_bound_gap_Pa"] <= x.swt_bound_gap_tolerance_Pa
    return Calculation(
        values=dict(
            history_id=x.history_id,
            material_condition_id=x.material_condition_id,
            location_id=x.location_id,
            fatemi_socie_coefficient=x.fatemi_socie_coefficient,
            normalization_stress_Pa=x.normalization_stress_Pa,
            tensor_source_id=x.tensor_source_id,
            tensor_history_record_digest=x.tensor_history_record_digest,
            stress_closure_error_Pa=stress_closure,
            strain_closure_error=strain_closure,
            sampled_maximum_fatemi_socie_factor=best_fs,
            fatemi_socie_plane_id=best_fs_plane,
            fatemi_socie_continuous_upper_bound=final["fatemi_socie_continuous_upper_bound"],
            fatemi_socie_bound_gap=final["fatemi_socie_bound_gap"],
            fatemi_socie_bound_gap_tolerance=x.fatemi_socie_bound_gap_tolerance,
            fatemi_socie_bound_within_tolerance=fs_within,
            sampled_maximum_swt_factor_Pa=best_swt,
            swt_plane_id=best_swt_plane,
            swt_continuous_upper_bound_Pa=final["swt_continuous_upper_bound_Pa"],
            swt_bound_gap_Pa=final["swt_bound_gap_Pa"],
            swt_bound_gap_tolerance_Pa=x.swt_bound_gap_tolerance_Pa,
            swt_bound_within_tolerance=swt_within,
            all_bounds_within_tolerance=fs_within and swt_within,
            bound_is_certified_for_continuous_plane_over_supplied_sampled_cycle=True,
            budget_exhausted=budget_exhausted,
            evaluated_candidate_count=evaluated,
            sample_pair_plane_work=pair_plane_work,
            refinement_levels=levels,
            maximum_refinement_level=x.maximum_refinement_level,
        ),
        notes=(
            "Each icosphere level is a full unit-sphere triangulation; every point lies in a spherical face whose distance to a vertex is no larger than the maximum face-edge angle. Antipodal vertices are identified because a material plane is unoriented.",
            "The supplied engineering-shear chord amplitude, maximum tensile normal stress and normal-strain amplitude are bounded by tensor Frobenius norms. The returned Lipschitz gap is a conservative continuous-orientation upper bound for the sampled closed cycle, conditional on these implemented factor definitions.",
            "This does not bound unsampled time extrema, arbitrary cycle counting, local tensor-field discretization error, calibration uncertainty, material transfer, acceptance or physical-model error. A budget-limited result still has the reported valid upper bound from its last fully evaluated level.",
        ),
    )


class CriticalPlaneTimeSampling(Contract):
    """One ordered sampling of the same declared local tensor cycle."""

    sampling_id: str = Field(min_length=1)
    sample_ids: list[str] = Field(min_length=3)
    sample_times_s: list[Nonnegative] = Field(min_length=3)
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3)
    strain_tensor_components: list[list[float]] = Field(min_length=3)

    @model_validator(mode="after")
    def aligned_ordered_sampling(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample identifiers must be unique and preserve path order")
        if (
            len(self.sample_times_s) != count
            or len(self.stress_tensor_components_Pa) != count
            or len(self.strain_tensor_components) != count
        ):
            raise ValueError("sample identifiers, times and tensor histories must align")
        if any(
            later <= earlier
            for earlier, later in zip(self.sample_times_s, self.sample_times_s[1:], strict=False)
        ):
            raise ValueError("sample times must be strictly increasing")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        return self


def _maximum_nested_time_match_error(coarse: list[float], fine: list[float]) -> float:
    maximum_error = 0.0
    fine_index = 0
    for coarse_time in coarse:
        while fine_index + 1 < len(fine) and fine[fine_index + 1] <= coarse_time:
            fine_index += 1
        error = abs(fine[fine_index] - coarse_time)
        if fine_index + 1 < len(fine):
            error = min(error, abs(fine[fine_index + 1] - coarse_time))
        maximum_error = max(maximum_error, error)
    return maximum_error


class CriticalPlaneTimeRefinement(Contract):
    """Fixed-plane critical-factor comparison over nested cycle samplings."""

    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    candidate_planes: list[CriticalPlaneCandidate] = Field(min_length=1)
    sampling_levels: list[CriticalPlaneTimeSampling] = Field(min_length=2)
    representative_cycle_declared: bool
    maximum_stress_closure_error_Pa: Nonnegative
    maximum_strain_closure_error: Nonnegative
    maximum_nested_time_match_error_s: Nonnegative
    fatemi_socie_coefficient: Nonnegative
    normalization_stress_Pa: Positive
    declared_maximum_relative_factor_change: Nonnegative
    declared_maximum_plane_rotation_rad: float = Field(ge=0.0, le=math.pi / 2)

    @model_validator(mode="after")
    def ordered_nested_samplings(self):
        plane_ids = [plane.plane_id for plane in self.candidate_planes]
        if len(set(plane_ids)) != len(plane_ids):
            raise ValueError("candidate plane identifiers must be unique")
        sampling_ids = [level.sampling_id for level in self.sampling_levels]
        if len(set(sampling_ids)) != len(sampling_ids):
            raise ValueError("sampling identifiers must be unique")
        reference_start = self.sampling_levels[0].sample_times_s[0]
        reference_end = self.sampling_levels[0].sample_times_s[-1]
        for level in self.sampling_levels[1:]:
            if (
                abs(level.sample_times_s[0] - reference_start) > self.maximum_nested_time_match_error_s
                or abs(level.sample_times_s[-1] - reference_end) > self.maximum_nested_time_match_error_s
            ):
                raise ValueError("all sampling levels must cover the same cycle time interval")
        for coarse, fine in zip(self.sampling_levels, self.sampling_levels[1:], strict=False):
            if len(fine.sample_ids) <= len(coarse.sample_ids):
                raise ValueError("each time-refinement level must increase sample count")
            if (
                _maximum_nested_time_match_error(coarse.sample_times_s, fine.sample_times_s)
                > self.maximum_nested_time_match_error_s
            ):
                raise ValueError("each coarse sample time must be represented in the next refinement level")
        return self


def critical_plane_time_refinement(x: CriticalPlaneTimeRefinement) -> Calculation:
    """Compare fixed-plane sampled vector-path maxima over nested time histories."""
    candidate_by_id = {row.plane_id: row for row in x.candidate_planes}
    level_rows = []
    previous = None
    for level in x.sampling_levels:
        history = CriticalPlaneHistory(
            history_id=x.history_id,
            material_condition_id=x.material_condition_id,
            location_id=x.location_id,
            tensor_source_id=x.tensor_source_id,
            sample_ids=level.sample_ids,
            stress_tensor_components_Pa=level.stress_tensor_components_Pa,
            strain_tensor_components=level.strain_tensor_components,
            candidate_planes=x.candidate_planes,
            representative_cycle_declared=x.representative_cycle_declared,
            maximum_stress_closure_error_Pa=x.maximum_stress_closure_error_Pa,
            maximum_strain_closure_error=x.maximum_strain_closure_error,
            fatemi_socie_coefficient=x.fatemi_socie_coefficient,
            normalization_stress_Pa=x.normalization_stress_Pa,
        )
        factors = critical_plane_vector_path_factors(history)
        if factors.status != "computed":
            return Calculation(
                status=factors.status,
                values={
                    "history_id": x.history_id,
                    "material_condition_id": x.material_condition_id,
                    "location_id": x.location_id,
                    "tensor_source_id": x.tensor_source_id,
                    "candidate_count": len(x.candidate_planes),
                    "refinement_level_count": len(x.sampling_levels),
                    "evaluated_level_count": 0,
                    "levels": [],
                    "final_transition_within_declared_tolerances": None,
                    "all_transitions_within_declared_tolerances": None,
                },
                notes=factors.notes
                + (
                    "Time refinement is not evaluated until every supplied sampling qualifies as the declared closed representative cycle.",
                ),
            )
        fs_plane_id = factors.values["fatemi_socie_plane_id"]
        swt_plane_id = factors.values["swt_plane_id"]
        time_steps = [
            later - earlier
            for earlier, later in zip(level.sample_times_s, level.sample_times_s[1:], strict=False)
        ]
        row = {
            "sampling_id": level.sampling_id,
            "sample_count": len(level.sample_ids),
            "cycle_start_s": level.sample_times_s[0],
            "cycle_end_s": level.sample_times_s[-1],
            "minimum_time_step_s": min(time_steps),
            "maximum_time_step_s": max(time_steps),
            "maximum_fatemi_socie_factor": factors.values["maximum_fatemi_socie_factor"],
            "fatemi_socie_plane_id": fs_plane_id,
            "fatemi_socie_plane_normal": candidate_by_id[fs_plane_id].normal,
            "maximum_swt_factor_Pa": factors.values["maximum_swt_factor_Pa"],
            "swt_plane_id": swt_plane_id,
            "swt_plane_normal": candidate_by_id[swt_plane_id].normal,
            "transition_from_previous": None,
        }
        if previous is not None:
            transition = {
                "previous_sampling_id": previous["sampling_id"],
                "sample_count_ratio": row["sample_count"] / previous["sample_count"],
                "maximum_nested_time_match_error_s": _maximum_nested_time_match_error(
                    previous["sample_times_s"], level.sample_times_s
                ),
                "fatemi_socie_relative_change": _relative_change(
                    previous["maximum_fatemi_socie_factor"], row["maximum_fatemi_socie_factor"]
                ),
                "fatemi_socie_plane_rotation_rad": _unoriented_plane_rotation(
                    previous["fatemi_socie_plane_normal"], row["fatemi_socie_plane_normal"]
                ),
                "swt_relative_change": _relative_change(
                    previous["maximum_swt_factor_Pa"], row["maximum_swt_factor_Pa"]
                ),
                "swt_plane_rotation_rad": _unoriented_plane_rotation(
                    previous["swt_plane_normal"], row["swt_plane_normal"]
                ),
            }
            transition["within_declared_tolerances"] = (
                transition["fatemi_socie_relative_change"] <= x.declared_maximum_relative_factor_change
                and transition["swt_relative_change"] <= x.declared_maximum_relative_factor_change
                and transition["fatemi_socie_plane_rotation_rad"] <= x.declared_maximum_plane_rotation_rad
                and transition["swt_plane_rotation_rad"] <= x.declared_maximum_plane_rotation_rad
            )
            row["transition_from_previous"] = transition
        row["sample_times_s"] = level.sample_times_s
        level_rows.append(row)
        previous = row
    for row in level_rows:
        row.pop("sample_times_s")
    transitions = [row["transition_from_previous"] for row in level_rows[1:]]
    return Calculation(
        values={
            "history_id": x.history_id,
            "material_condition_id": x.material_condition_id,
            "location_id": x.location_id,
            "tensor_source_id": x.tensor_source_id,
            "candidate_count": len(x.candidate_planes),
            "refinement_level_count": len(x.sampling_levels),
            "evaluated_level_count": len(level_rows),
            "declared_maximum_relative_factor_change": x.declared_maximum_relative_factor_change,
            "declared_maximum_plane_rotation_rad": x.declared_maximum_plane_rotation_rad,
            "levels": level_rows,
            "final_transition_within_declared_tolerances": transitions[-1]["within_declared_tolerances"],
            "all_transitions_within_declared_tolerances": all(
                transition["within_declared_tolerances"] for transition in transitions
            ),
            "range_method": "maximum_pairwise_euclidean_chord",
        },
        notes=(
            "All levels use the same declared finite plane set and nested time coordinates over one cycle, isolating sampled-path resolution from orientation-grid changes.",
            "Successive factor and selected-plane changes are user-threshold diagnostics. They do not bound extrema between the finest samples or prove temporal convergence.",
            "A stable final transition does not establish a continuous-time or continuous-plane optimum, fatigue-life calibration, acceptance or independent experimental validity.",
        ),
    )


class CriticalPlanePiecewiseLinearTimeHistory(Contract):
    """Critical-plane factors for a caller-declared piecewise-linear tensor path."""

    history: CriticalPlaneHistory
    shear_range_method: Literal["maximum_pairwise_euclidean_chord", "minimum_enclosing_circle_radius"] = (
        "maximum_pairwise_euclidean_chord"
    )
    piecewise_linear_tensor_interpolation_reviewed: bool
    interpolation_scope_and_time_units_reviewed: bool
    maximum_sample_plane_work: int = Field(default=5_000_000, ge=1, le=50_000_000)

    @model_validator(mode="after")
    def require_timed_history(self):
        if self.history.sample_times_s is None:
            raise ValueError("piecewise-linear time calculation requires sample times")
        if len(self.history.sample_times_s) < 3:
            raise ValueError("at least three timed tensor samples are required")
        return self


def critical_plane_piecewise_linear_time_history(
    x: CriticalPlanePiecewiseLinearTimeHistory,
) -> Calculation:
    """Evaluate declared plane factors exactly over the piecewise-linear tensor reconstruction."""
    history = x.history
    times = history.sample_times_s
    assert times is not None
    sample_count = len(times)
    if x.shear_range_method == "maximum_pairwise_euclidean_chord":
        work = 2 * len(history.candidate_planes) * sample_count * (sample_count - 1) // 2
    else:
        work = 2 * len(history.candidate_planes) * sample_count**3
    input_sha256 = canonical_digest(x.model_dump(mode="json"))
    time_steps = [later - earlier for earlier, later in zip(times[:-1], times[1:], strict=True)]
    if work > x.maximum_sample_plane_work:
        return Calculation(
            status="out_of_scope",
            values={
                "history_id": history.history_id,
                "input_sha256": input_sha256,
                "sample_plane_work": work,
                "maximum_sample_plane_work": x.maximum_sample_plane_work,
                "continuous_time_extrema_exact_for_declared_interpolation": None,
            },
            notes=("Reduce the sample or plane count, or explicitly raise the caller-selected work budget.",),
        )
    if not (
        x.piecewise_linear_tensor_interpolation_reviewed
        and x.interpolation_scope_and_time_units_reviewed
    ):
        return Calculation(
            status="needs_data",
            values={
                "history_id": history.history_id,
                "input_sha256": input_sha256,
                "sample_plane_work": work,
                "continuous_time_extrema_exact_for_declared_interpolation": None,
            },
            notes=("The tensor interpolation rule and its time-domain meaning require caller review.",),
        )

    factors = (
        critical_plane_vector_path_factors(history)
        if x.shear_range_method == "maximum_pairwise_euclidean_chord"
        else critical_plane_minimum_enclosing_circle_factors(history)
    )
    rates = []
    for index, (earlier, later) in enumerate(zip(times[:-1], times[1:], strict=True)):
        duration = later - earlier
        stress_rate = _symmetric_tensor_frobenius_difference(
            history.stress_tensor_components_Pa[index + 1], history.stress_tensor_components_Pa[index]
        ) / duration
        strain_rate = _symmetric_tensor_frobenius_difference(
            history.strain_tensor_components[index + 1], history.strain_tensor_components[index]
        ) / duration
        if not math.isfinite(stress_rate) or not math.isfinite(strain_rate):
            return Calculation(
                status="out_of_scope",
                values={
                    "history_id": history.history_id,
                    "input_sha256": input_sha256,
                    "sample_plane_work": work,
                    "continuous_time_extrema_exact_for_declared_interpolation": None,
                },
                notes=("Tensor segment rate exceeded the numeric range; no time-rate history is returned.",),
            )
        rates.append(
            {
                "start_sample_id": history.sample_ids[index],
                "end_sample_id": history.sample_ids[index + 1],
                "start_time_s": earlier,
                "end_time_s": later,
                "tensor_stress_frobenius_rate_Pa_s": stress_rate,
                "tensor_strain_frobenius_rate_s_inverse": strain_rate,
            }
        )
    interpolation_note = (
        "For the reviewed piecewise-linear reconstruction of the supplied closed tensor cycle, scalar normal extrema occur at vertices; each shear-path segment lies inside the convex hull of its endpoints. Therefore the selected finite-plane FS/SWT factors and declared chord or enclosing-circle ranges are exact for this interpolation, without claiming that the interpolation matches unobserved physical behavior."
        if factors.status == "computed"
        else "Piecewise-linear vertex exactness applies only after the tensor history satisfies the declared representative-cycle closure checks; no fatigue-factor extrema are asserted for this result."
    )
    values = factors.values | {
        "input_sha256": input_sha256,
        "sample_plane_work": work,
        "time_interpolation_method": "piecewise_linear_tensor_components",
        "shear_range_method": x.shear_range_method,
        "continuous_time_extrema_exact_for_declared_interpolation": (
            True if factors.status == "computed" else None
        ),
        "cycle_start_s": times[0],
        "cycle_end_s": times[-1],
        "minimum_time_step_s": min(time_steps),
        "maximum_time_step_s": max(time_steps),
        "segment_tensor_frobenius_rates": rates,
    }
    return Calculation(
        status=factors.status,
        values=values,
        notes=factors.notes
        + (
            interpolation_note,
            "The result does not search continuous plane orientation, pair multiaxial rainflow cycles, accumulate variable-amplitude damage, predict fatigue life, or bound solver, measurement, calibration or model-form error.",
        ),
    )


class BasquinLife(Contract):
    stress_range_Pa: Positive
    reference_range_Pa: Positive
    reference_cycles: Positive
    exponent: Positive


def basquin_life(x: BasquinLife) -> Calculation:
    try:
        life = x.reference_cycles * (x.reference_range_Pa / x.stress_range_Pa) ** x.exponent
    except OverflowError:
        life = math.inf
    if not (math.isfinite(life) and life > 0):
        try:
            life = math.exp(math.log(x.reference_cycles) + x.exponent*(math.log(x.reference_range_Pa)-math.log(x.stress_range_Pa)))
        except OverflowError:
            life = math.inf
    if not (math.isfinite(life) and life > 0):
        return Calculation(status="out_of_scope",values={"reason":"positive_fatigue_life_outside_numeric_support"})
    return Calculation(values={"cycles_to_failure":life})


class MinerDamage(Contract):
    cycle_counts: list[Nonnegative] = Field(min_length=1)
    cycles_to_failure: list[Positive] = Field(min_length=1)
    declared_damage_limit: Positive

    @model_validator(mode="after")
    def align(self):
        if len(self.cycle_counts) != len(self.cycles_to_failure):
            raise ValueError("counts and fatigue lives must align")
        return self


def miner_damage(x: MinerDamage) -> Calculation:
    damage = sum(n / N for n, N in zip(x.cycle_counts, x.cycles_to_failure, strict=True))
    return Calculation(
        values=dict(
            damage=damage,
            damage_margin=x.declared_damage_limit - damage,
            fraction_of_declared_limit=damage / x.declared_damage_limit,
        )
    )


class GoodmanCorrection(Contract):
    alternating_stress_Pa: Nonnegative
    mean_stress_Pa: Nonnegative
    ultimate_tensile_strength_Pa: Positive


def goodman(x: GoodmanCorrection) -> Calculation:
    if x.mean_stress_Pa >= x.ultimate_tensile_strength_Pa:
        return Calculation(
            status="out_of_scope", values={}, notes=("Mean stress reaches the supplied tensile strength.",)
        )
    return Calculation(
        values={
            "equivalent_fully_reversed_amplitude_Pa": x.alternating_stress_Pa
            / (1 - x.mean_stress_Pa / x.ultimate_tensile_strength_Pa)
        }
    )


class ParisLife(Contract):
    initial_depth_m: Positive
    terminal_depth_m: Positive
    stress_range_Pa: Positive
    geometry_factor: Positive
    coefficient_m_cycle_per_Pa_sqrt_m_power: Positive
    exponent: Positive

    @model_validator(mode="after")
    def growth(self):
        if self.terminal_depth_m < self.initial_depth_m:
            raise ValueError("terminal depth must not precede initial depth")
        return self


def paris_life(x: ParisLife) -> Calculation:
    a0, a1 = x.initial_depth_m, x.terminal_depth_m
    prefactor = (
        x.coefficient_m_cycle_per_Pa_sqrt_m_power
        * (x.geometry_factor * x.stress_range_Pa * math.sqrt(math.pi)) ** x.exponent
    )
    power = 1 - x.exponent / 2
    integral = (
        math.log(a1 / a0) if abs(power) < 1e-10 else a0**power * math.expm1(power * math.log(a1 / a0)) / power
    )
    return Calculation(
        values=dict(
            cycles_to_terminal_depth=integral / prefactor,
            initial_delta_K_Pa_sqrt_m=x.geometry_factor * x.stress_range_Pa * math.sqrt(math.pi * a0),
            terminal_delta_K_Pa_sqrt_m=x.geometry_factor * x.stress_range_Pa * math.sqrt(math.pi * a1),
        )
    )


class RainflowHistory(Contract):
    values: list[float] = Field(min_length=3)
    quantity_unit: str = Field(min_length=1)


def rainflow_history(x: RainflowHistory) -> Calculation:
    import rainflow

    rows = [
        dict(range=float(r), mean=float(m), count=float(c), start_index=int(i), end_index=int(j))
        for r, m, c, i, j in rainflow.extract_cycles(x.values)
    ]
    return Calculation(
        values=dict(cycles=rows, cycle_count=sum(r["count"] for r in rows), quantity_unit=x.quantity_unit)
    )


class CriticalPlaneProjectedRainflow(Contract):
    """Explicit scalar projections of an ordered multiaxial tensor record."""

    history_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    tensor_source_id: str = Field(min_length=1)
    tensor_history_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    sample_ids: list[str] = Field(min_length=3, max_length=50000)
    sample_times_s: list[Nonnegative] | None = None
    stress_tensor_components_Pa: list[list[float]] = Field(min_length=3, max_length=50000)
    strain_tensor_components: list[list[float]] = Field(min_length=3, max_length=50000)
    input_strain_shear_convention: Literal["tensor", "engineering"]
    candidate_planes: list[CriticalPlaneCandidate] = Field(min_length=1, max_length=1000)
    projections: list[
        Literal[
            "normal_stress",
            "normal_strain",
            "shear_stress_directional_component",
            "engineering_shear_strain_directional_component",
            "shear_stress_vector_magnitude",
            "engineering_shear_strain_vector_magnitude",
        ]
    ] = Field(min_length=1)
    tensor_basis_and_order_reviewed: bool
    path_boundary_and_sample_order_reviewed: bool
    projection_method_and_use_reviewed: bool
    maximum_projection_sample_work: int = Field(default=5_000_000, ge=1, le=50_000_000)

    @model_validator(mode="after")
    def aligned_path(self):
        count = len(self.sample_ids)
        if len(set(self.sample_ids)) != count:
            raise ValueError("sample identifiers must be unique and preserve recorded path order")
        if len(self.stress_tensor_components_Pa) != count or len(self.strain_tensor_components) != count:
            raise ValueError("sample IDs and stress/strain tensor histories must align")
        if any(len(row) != 6 for row in self.stress_tensor_components_Pa):
            raise ValueError("each stress tensor needs [xx, yy, zz, xy, yz, zx]")
        if any(len(row) != 6 for row in self.strain_tensor_components):
            raise ValueError("each strain tensor needs [xx, yy, zz, xy, yz, zx]")
        if self.sample_times_s is not None:
            if len(self.sample_times_s) != count or any(
                later <= earlier for earlier, later in zip(self.sample_times_s, self.sample_times_s[1:], strict=False)
            ):
                raise ValueError("optional sample times must align and strictly increase")
        plane_ids = [plane.plane_id for plane in self.candidate_planes]
        if len(set(plane_ids)) != len(plane_ids):
            raise ValueError("candidate plane IDs must be unique")
        if len(set(self.projections)) != len(self.projections):
            raise ValueError("projection choices must be unique")
        return self


def critical_plane_projected_rainflow(x: CriticalPlaneProjectedRainflow) -> Calculation:
    """Count caller-selected scalar rainflow projections without cross-channel pairing."""
    work = len(x.sample_ids) * len(x.candidate_planes) * len(x.projections)
    base = dict(
        history_id=x.history_id,
        material_condition_id=x.material_condition_id,
        location_id=x.location_id,
        tensor_source_id=x.tensor_source_id,
        tensor_history_record_digest=x.tensor_history_record_digest,
        input_sha256=canonical_digest(x.model_dump(mode="json")),
        projection_sample_work=work,
        projection_cycle_results=None,
    )
    if work > x.maximum_projection_sample_work:
        return Calculation(
            status="out_of_scope",
            values=base | {"reason": "Projection-plane-sample budget exceeded"},
            notes=("Reduce samples, plane candidates or requested projection channels, or explicitly raise the work budget.",),
        )
    if not (
        x.tensor_basis_and_order_reviewed
        and x.path_boundary_and_sample_order_reviewed
        and x.projection_method_and_use_reviewed
    ):
        return Calculation(
            status="needs_data",
            values=base | {"reason": "Tensor basis, sample path and projection interpretation reviews are required"},
        )
    import rainflow

    stress = x.stress_tensor_components_Pa
    strain = [list(row) for row in x.strain_tensor_components]
    if x.input_strain_shear_convention == "engineering":
        for row in strain:
            row[3] *= 0.5
            row[4] *= 0.5
            row[5] *= 0.5
    rows = []
    for plane in x.candidate_planes:
        normal = plane.normal
        direction_a = plane.in_plane_direction
        direction_b = _cross(normal, direction_a)
        projected = {}
        for projection in x.projections:
            signal = []
            if projection == "normal_stress":
                signal = [_tensor_product(normal, tensor, normal) for tensor in stress]
                unit = "Pa"
                interpretation = "signed_normal_stress"
            elif projection == "normal_strain":
                signal = [_tensor_product(normal, tensor, normal) for tensor in strain]
                unit = "1"
                interpretation = "signed_normal_strain"
            elif projection == "shear_stress_directional_component":
                signal = [_tensor_product(direction_a, tensor, normal) for tensor in stress]
                unit = "Pa"
                interpretation = "signed_shear_component_along_supplied_in_plane_direction"
            elif projection == "engineering_shear_strain_directional_component":
                signal = [2 * _tensor_product(direction_a, tensor, normal) for tensor in strain]
                unit = "1"
                interpretation = "signed_engineering_shear_component_along_supplied_in_plane_direction"
            elif projection == "shear_stress_vector_magnitude":
                signal = [
                    math.hypot(
                        _tensor_product(direction_a, tensor, normal),
                        _tensor_product(direction_b, tensor, normal),
                    )
                    for tensor in stress
                ]
                unit = "Pa"
                interpretation = "nonnegative_in_plane_shear_traction_magnitude_direction_lost"
            else:
                signal = [
                    2
                    * math.hypot(
                        _tensor_product(direction_a, tensor, normal),
                        _tensor_product(direction_b, tensor, normal),
                    )
                    for tensor in strain
                ]
                unit = "1"
                interpretation = "nonnegative_engineering_shear_vector_magnitude_direction_lost"
            cycles = []
            for value_range, mean, count, start, end in rainflow.extract_cycles(signal):
                row = dict(
                    range=float(value_range),
                    mean=float(mean),
                    count=float(count),
                    start_index=int(start),
                    end_index=int(end),
                    start_sample_id=x.sample_ids[int(start)],
                    end_sample_id=x.sample_ids[int(end)],
                )
                if x.sample_times_s is not None:
                    row["start_time_s"] = x.sample_times_s[int(start)]
                    row["end_time_s"] = x.sample_times_s[int(end)]
                cycles.append(row)
            projected[projection] = dict(
                quantity_unit=unit,
                projection_interpretation=interpretation,
                cycle_count_equivalents=math.fsum(row["count"] for row in cycles),
                cycles=cycles,
            )
        rows.append(
            dict(
                plane_id=plane.plane_id,
                plane_normal=plane.normal,
                in_plane_direction=plane.in_plane_direction,
                orthogonal_in_plane_direction=direction_b,
                projections=projected,
            )
        )
    return Calculation(
        status="computed",
        values=base
        | dict(
            sample_count=len(x.sample_ids),
            candidate_plane_count=len(x.candidate_planes),
            input_strain_shear_convention=x.input_strain_shear_convention,
            sample_times_s=x.sample_times_s,
            projection_cycle_results=rows,
            counting_library="rainflow",
            residual_excursions_retained_as_half_cycles=True,
        ),
        notes=(
            "Each selected scalar projection is rainflow-counted independently over the supplied ordered record; residual excursions remain half cycles and sample indices map directly to caller IDs.",
            "No cycle matching, phase pairing, normal-stress/shear pairing, damage parameter, multiaxial life, closure correction, turning-point preprocessing, acceptance or probability is inferred. Vector-magnitude projections discard in-plane direction and must be interpreted accordingly.",
            "The result covers only the supplied sample path and caller-selected plane/projection set; plane search and continuous-time extrema are separate calculations.",
        ),
    )


class LarsonMiller(Contract):
    temperature_K: Positive
    constant: float
    rupture_time_s: Positive


def larson_miller(x: LarsonMiller) -> Calculation:
    return Calculation(
        values={"parameter_K": x.temperature_K * (x.constant + math.log10(x.rupture_time_s / 3600))}
    )


class RobinsonDamage(Contract):
    exposure_s: list[Nonnegative] = Field(min_length=1)
    rupture_life_s: list[Positive] = Field(min_length=1)

    @model_validator(mode="after")
    def align(self):
        if len(self.exposure_s) != len(self.rupture_life_s):
            raise ValueError("aligned creep intervals and rupture lives required")
        return self


def robinson(x: RobinsonDamage) -> Calculation:
    return Calculation(
        values={
            "time_fraction_damage": sum(t / tr for t, tr in zip(x.exposure_s, x.rupture_life_s, strict=True))
        }
    )


class HysteresisPath(Contract):
    stress_Pa: list[float] = Field(min_length=3)
    strain_fraction: list[float] = Field(min_length=3)
    cycle_boundary_declared: bool
    linear_closure_declared: bool
    maximum_endpoint_stress_difference_Pa: Nonnegative
    maximum_endpoint_strain_difference: Nonnegative

    @model_validator(mode="after")
    def align(self):
        if len(self.stress_Pa) != len(self.strain_fraction):
            raise ValueError("stress and strain path observations must align")
        return self


def hysteresis_path(x: HysteresisPath) -> Calculation:
    import numpy as np

    stress_gap = x.stress_Pa[-1] - x.stress_Pa[0]
    strain_gap = x.strain_fraction[-1] - x.strain_fraction[0]
    work = float(np.trapezoid(x.stress_Pa, x.strain_fraction))
    acceptable = (
        abs(stress_gap) <= x.maximum_endpoint_stress_difference_Pa
        and abs(strain_gap) <= x.maximum_endpoint_strain_difference
    )
    closed_work = None
    if (
        acceptable
        and x.cycle_boundary_declared
        and ((stress_gap == 0 and strain_gap == 0) or x.linear_closure_declared)
    ):
        closed_work = work - (x.stress_Pa[-1] + x.stress_Pa[0]) * strain_gap / 2
    return Calculation(
        values=dict(
            signed_recorded_path_work_J_m3=work,
            signed_closed_cycle_work_J_m3=closed_work,
            endpoint_stress_difference_Pa=stress_gap,
            endpoint_strain_difference=strain_gap,
            endpoints_within_declared_tolerances=acceptable,
        ),
        notes=(
            "Path order, not a rounded time derivative, defines the stress-strain line integral. Work sign is preserved.",
            "Closed-cycle work needs a declared complete cycle and endpoint tolerances; a linear closing segment is used only when explicitly declared. Open path work is not automatically dissipated heat or fatigue damage.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "fatigue.neuber_strain_life_chain",
            NeuberStrainLifeChain,
            neuber_strain_life_chain,
            {
                "local_stress_amplitude_Pa": "Pa",
                "local_strain_amplitude": "1",
                "elastic_strain_amplitude": "1",
                "plastic_strain_amplitude": "1",
                "relative_neuber_residual": "1",
                "neuber_iterations": "1",
                "neuber_converged": "1",
                "neuber_status": "1",
                "notch_reason": "1",
                "strain_life_status": "1",
                "cycles_to_failure": "cycle",
                "reversals_to_failure": "reversal",
            },
            (
                "Runs the reviewed scalar stabilized notch-root estimate first, then evaluates the local strain amplitude with caller-supplied strain-life coefficients and cycle support.",
                "The strain-life stage is skipped unless the notch stage has a computed, converged result; neither stage establishes code acceptance or experimental qualification.",
            ),
            ("neuber_local_strain_compatibility", "ramberg_osgood_cyclic_relation", "comsol_strain_life"),
        ),
        ModelSpec(
            "fatigue.neuber_notch_strain_amplitude",
            NeuberNotchStrainAmplitude,
            neuber_notch_strain_amplitude,
            {
                "local_stress_amplitude_Pa": "Pa",
                "local_strain_amplitude": "1",
                "elastic_strain_amplitude": "1",
                "plastic_strain_amplitude": "1",
                "neuber_target_Pa": "Pa",
                "neuber_product_Pa": "Pa",
                "relative_neuber_residual": "1",
                "iterations": "1",
                "converged": "1",
            },
            (
                "Caller-reviewed scalar uniaxial nominal stress amplitude, elastic concentration factor, modulus and stabilized cyclic Ramberg–Osgood parameters are required.",
                "The bounded bisection solution estimates local strain amplitude only; multiaxiality, residual stress, cyclic transients, notch gradients, fatigue life and acceptance are outside scope.",
            ),
            ("neuber_local_strain_compatibility", "ramberg_osgood_cyclic_relation"),
        ),
        ModelSpec(
            "fatigue.pressurized_annulus_load_state",
            PressurizedAnnulusLoadState,
            pressurized_annulus_load_state,
            {
                "reference_area_m2": "m^2",
                "polar_second_moment_m4": "m^4",
                "external_axial_mean_Pa": "Pa",
                "external_axial_amplitude_Pa": "Pa",
                "external_axial_minimum_Pa": "Pa",
                "external_axial_maximum_Pa": "Pa",
                "torsional_shear_mean_Pa": "Pa",
                "torsional_shear_amplitude_Pa": "Pa",
                "torsional_shear_minimum_Pa": "Pa",
                "torsional_shear_maximum_Pa": "Pa",
                "pressure_hoop_mean_Pa": "Pa",
                "pressure_radial_mean_Pa": "Pa",
                "pressure_axial_mean_Pa": "Pa",
                "combined_axial_mean_Pa": "Pa",
                "axial_torsion_phase_rad": "rad",
            },
            (
                "Long homogeneous isotropic linear-elastic annulus with static pressure, nominal axial force and Saint-Venant torsion; end, notch, fixture, residual-stress and inelastic effects are excluded.",
                "The caller declares the reference section, load case, pressure evaluation radius, end condition and axial-torsion phase; no fatigue-life or strength relationship is inferred.",
            ),
            ("annular_section_equilibrium", "cambridge_lame", "fabest_hcf_protocol_v2_1_2"),
        ),
        ModelSpec(
            "fatigue.pressure_loss_endpoint",
            PressureLossFatigueEndpoint,
            pressure_loss_fatigue_endpoint,
            {
                "cumulative_valid_cycles": "cycle",
                "pressure_drop_fraction": "1",
                "declared_threshold_fraction": "1",
                "pressure_drop_margin_Pa": "Pa",
                "cycles_at_confirmed_endpoint": "cycle",
                "segment_count": "1",
            },
            (
                "The caller supplies a reviewed pressure-drop threshold, event origin, physical-specimen continuity, load-case identity and valid-cycle accounting; the calculator does not infer them from a pressure trace.",
                "Runout requires a closed observation window and the declared cycle limit without a confirmed specimen endpoint; interruption and unresolved history remain distinct.",
            ),
            ("fabest_hcf_protocol_v2_1_2", "cumulative_loading_segments"),
        ),
        ModelSpec(
            "fatigue.hemisphere_plane_grid",
            HemispherePlaneGrid,
            hemisphere_plane_grid,
            {
                "candidate_count": "1",
                "polar_divisions": "1",
                "azimuthal_divisions": "1",
                "polar_step_rad": "rad",
                "azimuthal_step_rad": "rad",
            },
            (
                "Unoriented planes are sampled on a deterministic upper-hemisphere latitude-azimuth grid; exact pole and equatorial sign duplicates are removed.",
                "The grid is finite and non-equal-area. Its angular increments are metadata, not a coverage-error bound or proof of convergence.",
            ),
            ("hemisphere_plane_grid_derivation",),
        ),
        ModelSpec(
            "fatigue.area_uniform_fibonacci_plane_grid",
            AreaUniformFibonacciPlaneGrid,
            area_uniform_fibonacci_plane_grid,
            {
                "candidate_count": "1",
                "azimuth_phase_rad": "rad",
                "golden_angle_rad": "rad",
                "nominal_solid_angle_weight_sr": "sr",
                "nominal_weight_sum_sr": "sr",
            },
            (
                "Unoriented plane normals use midpoint-stratified positive-z coordinates with equal nominal solid-angle weights and a deterministic golden-angle azimuth sequence.",
                "The points are not asserted to be an exact equal-area Voronoi tessellation, a nested grid, a covering-radius guarantee or a continuous orientation optimum.",
                "Candidate count and azimuth phase are caller-controlled diagnostics; downstream factors still require a qualified local tensor history and independent material calibration.",
            ),
            ("area_uniform_fibonacci_plane_grid_derivation",),
        ),
        ModelSpec(
            "fatigue.critical_plane_factors",
            CriticalPlaneHistory,
            critical_plane_factors,
            {
                "sample_count": "1",
                "candidate_count": "1",
                "stress_closure_error_Pa": "Pa",
                "strain_closure_error": "1",
                "maximum_fatemi_socie_factor": "1",
                "maximum_swt_factor_Pa": "Pa",
            },
            (
                "The caller supplies a reviewed closed representative local cycle as aligned symmetric Cauchy-stress and small-strain tensors, using tensor rather than engineering shear components.",
                "The caller supplies orthonormal plane/direction candidates, a qualified Fatemi-Socie coefficient and normalization stress; only this finite candidate set is searched.",
                "Maximum tensile normal stress is used in the reported screening factors; compressive-only normal histories receive zero tensile contribution rather than a life inference.",
            ),
            (
                "fatemi_socie_1988",
                "smith_watson_topper_1970",
                "critical_plane_tensor_projection",
            ),
        ),
        ModelSpec(
            "fatigue.critical_plane_vector_path_factors",
            CriticalPlaneHistory,
            critical_plane_vector_path_factors,
            {
                "sample_count": "1",
                "candidate_count": "1",
                "stress_closure_error_Pa": "Pa",
                "strain_closure_error": "1",
                "maximum_fatemi_socie_factor": "1",
                "maximum_swt_factor_Pa": "Pa",
            },
            (
                "The caller supplies a reviewed closed representative local cycle as aligned symmetric Cauchy-stress and small-strain tensors, using tensor rather than engineering shear components.",
                "Each caller-supplied orthonormal plane frame defines a two-dimensional in-plane shear-vector path; amplitude is half its maximum sampled pairwise Euclidean chord.",
                "The finite sampled path and finite plane set do not qualify continuous-time extrema, a minimum-enclosing-circle method, continuous orientation optimization or fatigue-life calibration.",
            ),
            (
                "fatemi_socie_1988",
                "smith_watson_topper_1970",
                "critical_plane_vector_chord_projection",
            ),
        ),
        ModelSpec(
            "fatigue.critical_plane_minimum_enclosing_circle_factors",
            CriticalPlaneHistory,
            critical_plane_minimum_enclosing_circle_factors,
            {
                "sample_count": "1",
                "candidate_count": "1",
                "stress_closure_error_Pa": "Pa",
                "strain_closure_error": "1",
                "maximum_fatemi_socie_factor": "1",
                "maximum_swt_factor_Pa": "Pa",
            },
            (
                "The caller supplies a reviewed closed local tensor cycle, tensor-shear components, finite orthonormal plane frames and qualified FS parameters.",
                "For each plane, the sampled two-component engineering-shear path amplitude is the radius of its deterministic minimum enclosing circle; up to three support-sample identities and the half-maximum-chord comparison remain explicit.",
                "This finite point-set range ignores path order after closure review and does not qualify an unsampled continuous path, cycle counting, a continuous orientation optimum, fatigue life, acceptance or experiment agreement.",
            ),
            (
                "fatemi_socie_1988",
                "smith_watson_topper_1970",
                "critical_plane_minimum_enclosing_circle_projection",
            ),
        ),
        ModelSpec(
            "fatigue.critical_plane_grid_refinement",
            CriticalPlaneGridRefinement,
            critical_plane_grid_refinement,
            {
                "refinement_level_count": "1",
                "evaluated_level_count": "1",
                "declared_maximum_relative_factor_change": "1",
                "declared_maximum_plane_rotation_rad": "rad",
            },
            (
                "The caller supplies one reviewed closed local tensor cycle, at least two explicitly ordered hemisphere grids and diagnostic factor-change and plane-rotation tolerances.",
                "Each level uses the sampled maximum-pairwise shear-vector chord and reports both FS and SWT maxima; only successive finite grids are compared.",
                "Meeting a declared diagnostic tolerance does not prove continuous orientation or time convergence, fatigue-life calibration, acceptance or independent experimental validity.",
            ),
            (
                "hemisphere_plane_grid_derivation",
                "critical_plane_vector_chord_projection",
                "critical_plane_grid_refinement_diagnostic",
            ),
        ),
        ModelSpec(
            "fatigue.critical_plane_grid_family_comparison",
            CriticalPlaneGridFamilyComparison,
            critical_plane_grid_family_comparison,
            {
                "grid_count": "1",
                "evaluated_grid_count": "1",
                "declared_maximum_relative_factor_change": "1",
                "declared_maximum_plane_rotation_rad": "rad",
            },
            (
                "The caller supplies one reviewed closed local tensor cycle, at least two uniquely identified latitude-azimuth and/or area-stratified Fibonacci grids, an explicit finite reference grid and diagnostic tolerances.",
                "All grids use the same sampled maximum-pairwise shear-vector chord; candidate family, count and Fibonacci phase are compared without changing the tensor history.",
                "Agreement with the declared finite reference does not prove an orientation-error bound, continuous-plane/time convergence, fatigue-life calibration, acceptance or experimental validity.",
            ),
            (
                "hemisphere_plane_grid_derivation",
                "area_uniform_fibonacci_plane_grid_derivation",
                "critical_plane_vector_chord_projection",
                "critical_plane_grid_family_comparison_diagnostic",
            ),
        ),
        ModelSpec(
            "fatigue.critical_plane_time_refinement",
            CriticalPlaneTimeRefinement,
            critical_plane_time_refinement,
            {
                "candidate_count": "1",
                "refinement_level_count": "1",
                "evaluated_level_count": "1",
                "declared_maximum_relative_factor_change": "1",
                "declared_maximum_plane_rotation_rad": "rad",
            },
            (
                "The caller supplies one reviewed cycle at two or more strictly increasing nested time samplings, a fixed finite plane set and explicit time-match and diagnostic tolerances.",
                "Every level uses the sampled maximum-pairwise shear-vector chord. Factor and selected-plane changes isolate temporal sampling only within the fixed candidate set.",
                "Meeting a declared diagnostic tolerance does not bound extrema between samples or prove continuous-time/orientation convergence, fatigue-life calibration, acceptance or experimental validity.",
            ),
            (
                "critical_plane_vector_chord_projection",
                "critical_plane_time_refinement_diagnostic",
            ),
        ),
        ModelSpec(
            "fatigue.critical_plane_piecewise_linear_time_history",
            CriticalPlanePiecewiseLinearTimeHistory,
            critical_plane_piecewise_linear_time_history,
            {
                "cycle_start_s": "s",
                "cycle_end_s": "s",
                "minimum_time_step_s": "s",
                "maximum_time_step_s": "s",
                "segment_tensor_frobenius_rates.tensor_stress_frobenius_rate_Pa_s": "Pa/s",
                "segment_tensor_frobenius_rates.tensor_strain_frobenius_rate_s_inverse": "1/s",
            },
            (
                "The caller supplies one timed, reviewed closed tensor cycle and explicitly declares piecewise-linear interpolation of the tensor components.",
                "For the selected finite plane set and chord or enclosing-circle definitions, extrema of the reconstructed path are exactly represented by the sample vertices; this is conditional on the declared interpolation.",
                "The model does not infer physical behavior between measurements, continuous-plane optima, multiaxial cycle pairing, damage accumulation, fatigue life or experimental validity.",
            ),
            ("critical_plane_piecewise_linear_time_extrema",),
        ),
        ModelSpec(
            "fatigue.critical_plane_adaptive_search",
            CriticalPlaneAdaptiveSearch,
            critical_plane_adaptive_search,
            {
                "seed_candidate_count": "1",
                "refinement_rounds": "1",
                "ring_points": "1",
                "initial_radius_rad": "rad",
                "radius_reduction_factor": "1",
                "declared_maximum_final_relative_factor_change": "1",
                "declared_maximum_final_plane_rotation_rad": "rad",
            },
            (
                "The caller supplies one reviewed closed local tensor cycle, one finite seed grid and an explicit tangent-ring refinement schedule.",
                "FS and SWT orientations are refined independently with the sampled maximum-pairwise shear-vector chord; every round retains its current center so the sampled objective cannot decrease.",
                "This greedy local diagnostic can miss another maximum and does not prove continuous orientation/time convergence, fatigue-life calibration, acceptance or experimental validity.",
            ),
            (
                "critical_plane_vector_chord_projection",
                "critical_plane_adaptive_search_diagnostic",
            ),
        ),
        ModelSpec(
            "fatigue.critical_plane_continuous_bound",
            CriticalPlaneContinuousBound,
            critical_plane_continuous_bound,
            {
                "sampled_maximum_fatemi_socie_factor": "1",
                "fatemi_socie_continuous_upper_bound": "1",
                "fatemi_socie_bound_gap": "1",
                "sampled_maximum_swt_factor_Pa": "Pa",
                "swt_continuous_upper_bound_Pa": "Pa",
                "swt_bound_gap_Pa": "Pa",
                "evaluated_candidate_count": "1",
                "maximum_refinement_level": "1",
            },
            (
                "The caller supplies one reviewed closed local tensor cycle, calibrated Fatemi-Socie coefficient and normalization stress, plus explicit orientation and work budgets.",
                "A fully evaluated icosphere vertex net and tensor-norm Lipschitz constants yield conservative continuous-plane upper bounds for the implemented FS and SWT sampled-cycle factors.",
                "The bound covers orientation over the supplied discrete cycle only; it does not bound time interpolation, arbitrary cycle counting, calibration, local fields, physical-model error or acceptance.",
            ),
            ("critical_plane_continuous_lipschitz_bound",),
        ),
        ModelSpec(
            "fatigue.critical_plane_projected_rainflow",
            CriticalPlaneProjectedRainflow,
            critical_plane_projected_rainflow,
            {
                "projection_cycle_results.projections.cycle_count_equivalents": "cycle",
                "projection_cycle_results.projections.cycles.range": "input_quantity_unit",
                "projection_cycle_results.projections.cycles.mean": "input_quantity_unit",
                "projection_cycle_results.projections.cycles.count": "cycle",
                "projection_cycle_results.projections.cycles.start_time_s": "s",
                "projection_cycle_results.projections.cycles.end_time_s": "s",
            },
            (
                "The caller supplies ordered multiaxial stress/strain tensors, finite plane frames, explicit scalar projection choices, path boundary, tensor basis and interpretation reviews.",
                "Rainflow is applied independently to each declared scalar projection; residual excursions remain half cycles and cycle endpoints retain caller sample identities.",
                "No cross-projection pairing, multiaxial damage parameter, life, closure correction, continuous-plane search, acceptance or probability is inferred.",
            ),
            ("critical_plane_projected_rainflow_decomposition", "rainflow_library"),
        ),
        ModelSpec(
            "fatigue.hysteresis_path",
            HysteresisPath,
            hysteresis_path,
            {
                "signed_recorded_path_work_J_m3": "J/m^3",
                "signed_closed_cycle_work_J_m3": "J/m^3",
                "endpoint_stress_difference_Pa": "Pa",
                "endpoint_strain_difference": "1",
            },
            ("Ordered uniaxial stress-strain path with explicit cycle boundaries and closure quality.",),
            ("mechanical_path_work",),
        ),
        ModelSpec(
            "fatigue.basquin",
            BasquinLife,
            basquin_life,
            {"cycles_to_failure": "cycle"},
            (
                "Stress-range convention, constant amplitude, calibrated user coefficients; no endurance plateau.",
            ),
            ("basquin_relation",),
        ),
        ModelSpec(
            "fatigue.miner",
            MinerDamage,
            miner_damage,
            {"damage": "1", "damage_margin": "1", "fraction_of_declared_limit": "1"},
            (
                "Linear accumulation omits load sequence and damage interaction; limit is explicitly declared.",
            ),
            ("miner_accumulation",),
        ),
        ModelSpec(
            "fatigue.goodman",
            GoodmanCorrection,
            goodman,
            {"equivalent_fully_reversed_amplitude_Pa": "Pa"},
            ("Tensile mean stress only; empirical correction needs material qualification.",),
            ("goodman_relation",),
        ),
        ModelSpec(
            "fracture.paris_constant_amplitude",
            ParisLife,
            paris_life,
            {
                "cycles_to_terminal_depth": "cycle",
                "initial_delta_K_Pa_sqrt_m": "Pa*m^0.5",
                "terminal_delta_K_Pa_sqrt_m": "Pa*m^0.5",
            },
            (
                "Constant stress range and geometry factor; Paris region only, no initiation, closure, threshold or toughness termination inference.",
            ),
            ("nasa_paris",),
        ),
        ModelSpec(
            "fatigue.rainflow",
            RainflowHistory,
            rainflow_history,
            {"cycle_count": "cycle"},
            (
                "Uses the installed rainflow library; output range unit matches input, residual excursions remain half cycles.",
            ),
            ("rainflow_library",),
        ),
        ModelSpec(
            "creep.larson_miller",
            LarsonMiller,
            larson_miller,
            {"parameter_K": "K"},
            (
                "Base-10 logarithm uses hours and temperature uses Kelvin; constant is not supplied by the library.",
            ),
            ("larson_miller_relation",),
        ),
        ModelSpec(
            "creep.time_fraction",
            RobinsonDamage,
            robinson,
            {"time_fraction_damage": "1"},
            ("Linear life fractions with supplied rupture lives; creep-fatigue interaction excluded.",),
            ("robinson_time_fraction",),
        ),
    ]
