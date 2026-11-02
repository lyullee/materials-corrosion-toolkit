"""Finite-volume restricted 1D transport with optional advection and local wall ledgers."""

import math
import re
from collections.abc import Callable
from types import SimpleNamespace

import numpy as np
from pydantic import Field, model_validator

from .contracts import AssessmentResult, Contract, Nonnegative, Positive, canonical_digest


class _TransportActivityCallbackFailure(RuntimeError):
    """Sanitized failure boundary for caller activity-coefficient providers."""

    def __init__(self, provider_error_type: str):
        super().__init__("external transport activity callback failed")
        self.provider_error_type = provider_error_type


class RestrictedTransportRequest(Contract):
    simulation_id: str = Field(min_length=1)
    species_ids: tuple[str, ...] = Field(min_length=1)
    length_m: Positive
    cell_count: int = Field(ge=2, le=2000)
    cell_widths_m: tuple[Positive, ...] | None = None
    cell_cross_section_m2: tuple[Positive, ...] | None = None
    face_cross_section_m2: tuple[Positive, ...] | None = None
    cell_cross_section_history_m2: tuple[tuple[Positive, ...], ...] | None = None
    face_cross_section_history_m2: tuple[tuple[Positive, ...], ...] | None = None
    reference_cross_section_m2: Positive | None = None
    variable_area_one_dimensional_reduction_reviewed: bool = False
    moving_geometry_interpolation_reviewed: bool = False
    moving_geometry_inventory_dilution_reviewed: bool = False
    moving_geometry_provider_id: str | None = Field(default=None, min_length=1)
    moving_geometry_configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    moving_geometry_source_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    moving_geometry_time_basis_id: str | None = Field(default=None, min_length=1)
    axial_advection_velocity_m_s: tuple[float, ...] | None = None
    axial_advection_provider_id: str | None = Field(default=None, min_length=1)
    axial_advection_configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    axial_advection_source_result_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    axial_advection_source_time_s: Nonnegative | None = None
    axial_advection_source_time_basis_id: str | None = Field(default=None, min_length=1)
    axial_advection_and_flow_continuity_reviewed: bool = False
    time_varying_axial_advection_reviewed: bool = False
    axial_flow_reversal_and_tip_boundary_reviewed: bool = False
    tip_advection_inflow_mol_m3: tuple[Nonnegative, ...] | None = None
    diffusivity_m2_s: tuple[Positive, ...]
    initial_concentration_mol_m3: tuple[tuple[Nonnegative, ...], ...]
    mouth_concentration_mol_m3: tuple[Nonnegative, ...]
    output_times_s: tuple[Nonnegative, ...] = Field(min_length=2)
    mouth_concentration_history_mol_m3: tuple[tuple[Nonnegative, ...], ...] | None = None
    mouth_history_interpolation_reviewed: bool = False
    reaction_provider_id: str = Field(min_length=1)
    reaction_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_diffusion_reaction_basis_reviewed: bool
    charge_numbers: tuple[int, ...] | None = None
    prescribed_potential_V: tuple[float, ...] | None = None
    migration_temperature_K: Positive | None = None
    prescribed_field_migration_reviewed: bool = False
    poisson_permittivity_F_m: Positive | None = None
    poisson_mouth_potential_V: float = 0.0
    fixed_charge_mol_charge_m3: tuple[float, ...] | None = None
    poisson_boundary_and_charge_reviewed: bool = False
    tip_surface_provider_id: str | None = None
    tip_surface_configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    tip_surface_flux_basis_reviewed: bool = False
    activity_provider_id: str | None = Field(default=None, min_length=1)
    activity_configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    activity_chemical_potential_and_tracer_diffusivity_reviewed: bool = False
    wall_area_per_volume_m2_m3: tuple[Nonnegative, ...] | None = None
    wall_area_per_volume_history_m2_m3: tuple[tuple[Nonnegative, ...], ...] | None = None
    wall_surface_provider_id: str | None = Field(default=None, min_length=1)
    wall_surface_configuration_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    wall_surface_flux_basis_reviewed: bool = False
    inventory_absolute_tolerance_mol_m2: Positive = 1e-8
    inventory_relative_tolerance: Positive = 1e-6
    solver_relative_tolerance: float = Field(default=1e-7, gt=0, le=0.01)
    concentration_absolute_tolerance_mol_m3: Positive = 1e-10
    integrated_amount_absolute_tolerance_mol_m2: Positive = 1e-10
    maximum_solver_step_s: Positive | None = None
    callbacks_cell_locality_reviewed: bool = False
    maximum_dense_state_count: int = Field(default=4000, ge=10, le=20000)

    @model_validator(mode="after")
    def arrays(self):
        n = len(self.species_ids)
        geometry_history_supplied = (
            self.cell_cross_section_history_m2 is not None
            or self.face_cross_section_history_m2 is not None
            or self.wall_area_per_volume_history_m2_m3 is not None
        )
        if (self.cell_cross_section_history_m2 is None) != (self.face_cross_section_history_m2 is None):
            raise ValueError("moving geometry requires both cell and face cross-section histories")
        if geometry_history_supplied:
            if self.cell_cross_section_history_m2 is None or self.face_cross_section_history_m2 is None:
                raise ValueError("moving geometry requires aligned cell and face area histories")
            if not (self.moving_geometry_interpolation_reviewed and self.moving_geometry_inventory_dilution_reviewed):
                raise ValueError("moving geometry requires reviewed interpolation and inventory dilution semantics")
            if not (self.moving_geometry_provider_id and self.moving_geometry_configuration_sha256
                    and self.moving_geometry_time_basis_id):
                raise ValueError("moving geometry requires provider, configuration digest and time-basis lineage")
            if len(self.cell_cross_section_history_m2) != len(self.output_times_s) or any(
                len(row) != self.cell_count for row in self.cell_cross_section_history_m2
            ):
                raise ValueError("cell cross-section history must align with output times and cells")
            if len(self.face_cross_section_history_m2) != len(self.output_times_s) or any(
                len(row) != self.cell_count + 1 for row in self.face_cross_section_history_m2
            ):
                raise ValueError("face cross-section history must align with output times and cell faces")
            if any(
                not math.isfinite(float(value)) or value <= 0
                for row in (*self.cell_cross_section_history_m2, *self.face_cross_section_history_m2)
                for value in row
            ):
                raise ValueError("moving cell and face cross sections must be finite and positive")
            if self.cell_cross_section_m2 != self.cell_cross_section_history_m2[0]:
                raise ValueError("static cell cross-section must equal the first moving-geometry history row")
            if self.face_cross_section_m2 != self.face_cross_section_history_m2[0]:
                raise ValueError("static face cross-section must equal the first moving-geometry history row")
            if self.wall_area_per_volume_history_m2_m3 is not None:
                if len(self.wall_area_per_volume_history_m2_m3) != len(self.output_times_s) or any(
                    len(row) != self.cell_count for row in self.wall_area_per_volume_history_m2_m3
                ):
                    raise ValueError("wall-area-density history must align with output times and cells")
                if any(
                    not math.isfinite(float(value)) or value < 0
                    for row in self.wall_area_per_volume_history_m2_m3
                    for value in row
                ):
                    raise ValueError("moving wall-area densities must be finite and nonnegative")
                if self.wall_area_per_volume_m2_m3 != self.wall_area_per_volume_history_m2_m3[0]:
                    raise ValueError("static wall-area density must equal the first history row")
                if self.wall_surface_provider_id is None:
                    raise ValueError("moving wall-area density requires a declared wall-surface provider")
            elif self.wall_surface_provider_id is not None:
                raise ValueError("moving geometry with wall flux requires a time-aligned wall-area-density history")
            if (self.axial_advection_velocity_m_s is not None
                    and not self.time_varying_axial_advection_reviewed):
                raise ValueError("moving geometry with static advection requires explicit time-varying-flow review")
        elif any((
            self.moving_geometry_interpolation_reviewed,
            self.moving_geometry_inventory_dilution_reviewed,
            self.moving_geometry_provider_id,
            self.moving_geometry_configuration_sha256,
            self.moving_geometry_source_result_sha256,
            self.moving_geometry_time_basis_id,
        )):
            raise ValueError("moving-geometry lineage and review fields require geometry histories")
        if self.moving_geometry_source_result_sha256 is not None and not geometry_history_supplied:
            raise ValueError("moving-geometry source result requires geometry histories")
        area_fields = (
            self.cell_cross_section_m2,
            self.face_cross_section_m2,
            self.reference_cross_section_m2,
        )
        if any(value is not None for value in area_fields):
            if any(value is None for value in area_fields):
                raise ValueError("variable area requires cell, face and reference cross sections")
            if (
                len(self.cell_cross_section_m2) != self.cell_count
                or len(self.face_cross_section_m2) != self.cell_count + 1
            ):
                raise ValueError("cell and face cross sections must match the transport grid")
        if (self.axial_advection_provider_id is None) != (self.axial_advection_configuration_sha256 is None):
            raise ValueError("axial advection provider and configuration digest must be supplied together")
        if self.axial_advection_source_result_sha256 is not None and self.axial_advection_provider_id is None:
            raise ValueError("advection source-result digest requires a provider identity")
        if (self.axial_advection_source_time_s is None) != (self.axial_advection_source_time_basis_id is None):
            raise ValueError("advection source time and time-basis identity must be supplied together")
        if self.axial_advection_source_time_s is not None and self.axial_advection_provider_id is None:
            raise ValueError("advection source time requires a provider identity")
        if self.axial_advection_velocity_m_s is not None:
            if self.axial_advection_provider_id is None:
                raise ValueError("static axial advection requires provider and configuration digest")
            if len(self.axial_advection_velocity_m_s) != self.cell_count + 1:
                raise ValueError("axial advection velocity requires one value per cell face")
        elif self.axial_advection_provider_id is not None and not self.time_varying_axial_advection_reviewed:
            raise ValueError("provider-only advection requires a reviewed time-varying Python velocity callback")
        if self.tip_advection_inflow_mol_m3 is not None and len(self.tip_advection_inflow_mol_m3) != n:
            raise ValueError("tip advection boundary must align with species order")
        if self.axial_flow_reversal_and_tip_boundary_reviewed and self.tip_advection_inflow_mol_m3 is None:
            raise ValueError("reviewed flow reversal requires an explicit distal inflow concentration")
        if self.tip_advection_inflow_mol_m3 is not None and not self.axial_flow_reversal_and_tip_boundary_reviewed:
            raise ValueError("distal advective inflow requires a reviewed boundary basis")
        if self.cell_widths_m is not None:
            if len(self.cell_widths_m) != self.cell_count or not math.isclose(
                math.fsum(self.cell_widths_m), self.length_m, rel_tol=1e-12, abs_tol=0.0
            ):
                raise ValueError("cell widths must align with cells and sum to the declared length")
        if self.mouth_concentration_history_mol_m3 is not None:
            history = self.mouth_concentration_history_mol_m3
            if len(history) != len(self.output_times_s) or any(len(row) != n for row in history):
                raise ValueError("mouth history must align with output times and species order")
            if history[0] != self.mouth_concentration_mol_m3:
                raise ValueError("mouth history initial row must match the explicit initial boundary")
        if (
            self.wall_area_per_volume_m2_m3 is not None
            and len(self.wall_area_per_volume_m2_m3) != self.cell_count
        ):
            raise ValueError("wall surface-area density must align with cells")
        if (self.activity_provider_id is None) != (self.activity_configuration_sha256 is None):
            raise ValueError("activity provider and configuration digest must be supplied together")
        wall_fields = (
            self.wall_area_per_volume_m2_m3,
            self.wall_area_per_volume_history_m2_m3,
            self.wall_surface_provider_id,
            self.wall_surface_configuration_sha256,
        )
        if any(value is not None for value in wall_fields) and any(value is None for value in wall_fields):
            raise ValueError("wall flux requires explicit area density, provider and configuration digest")
        # Three global ledgers (mouth, tip, homogeneous reaction) plus one
        # wall-source ledger for every species/cell pair.
        state_count = n * (2 * self.cell_count + 3)
        if state_count > 50000 or n * self.cell_count * len(self.output_times_s) > 2_000_000:
            raise ValueError("transport state or output budget exceeded; reduce cells/species/output times")
        sparse_eligible = self.callbacks_cell_locality_reviewed and self.poisson_permittivity_F_m is None
        if not sparse_eligible and state_count > self.maximum_dense_state_count:
            raise ValueError(
                "dense transport state budget exceeded; Poisson/nonlocal callback structure cannot assume local sparsity"
            )
        if (
            len(set(self.species_ids)) != n
            or len(self.diffusivity_m2_s) != n
            or len(self.mouth_concentration_mol_m3) != n
            or len(self.initial_concentration_mol_m3) != n
        ):
            raise ValueError("species arrays must align with unique species IDs")
        if any(len(row) != self.cell_count for row in self.initial_concentration_mol_m3):
            raise ValueError("initial concentrations must have species by cell shape")
        if self.poisson_permittivity_F_m is not None:
            if self.prescribed_potential_V is not None:
                raise ValueError("select prescribed potential or Poisson closure, not both")
            if (
                self.charge_numbers is None
                or self.migration_temperature_K is None
                or len(self.charge_numbers) != n
            ):
                raise ValueError("Poisson transport requires aligned species charges and temperature")
            if (
                self.fixed_charge_mol_charge_m3 is not None
                and len(self.fixed_charge_mol_charge_m3) != self.cell_count
            ):
                raise ValueError("fixed charge must align with cells")
        elif self.fixed_charge_mol_charge_m3 is not None:
            raise ValueError("fixed charge requires Poisson closure")
        migration = (
            (self.charge_numbers, self.prescribed_potential_V, self.migration_temperature_K)
            if self.poisson_permittivity_F_m is None
            else (None, None, None)
        )
        if any(value is not None for value in migration):
            if any(value is None for value in migration):
                raise ValueError("migration requires charges, mouth-plus-cell potentials and temperature")
            if len(self.charge_numbers) != n or len(self.prescribed_potential_V) != self.cell_count + 1:
                raise ValueError("migration arrays must align with species and mouth-plus-cell coordinates")
        if self.output_times_s[0] != 0 or any(
            b <= a for a, b in zip(self.output_times_s[:-1], self.output_times_s[1:], strict=True)
        ):
            raise ValueError("output clock must begin at zero and increase")
        return self


def bind_planar_slit_hydraulic_snapshot(
    request: RestrictedTransportRequest,
    hydraulic_history_result: AssessmentResult | dict,
    hydraulic_history_result_sha256: str,
    snapshot_index: int,
) -> RestrictedTransportRequest:
    """Bind one digest-pinned steady hydraulic snapshot to a transport request.

    The caller still supplies boundary concentrations and continuity reviews.
    A snapshot supplies only the signed velocity field and its provider lineage.
    """
    if not isinstance(snapshot_index, int) or isinstance(snapshot_index, bool) or snapshot_index < 0:
        raise ValueError("snapshot_index must be a nonnegative integer")
    if not isinstance(hydraulic_history_result, AssessmentResult):
        hydraulic_history_result = AssessmentResult.model_validate(hydraulic_history_result)
    result = hydraulic_history_result
    if result.model_id != "corrosion.planar_slit_hydraulic_history" or result.status != "computed":
        raise ValueError("a computed planar-slit hydraulic-history AssessmentResult is required")
    expected_input_digest = canonical_digest({
        "model_id": result.model_id,
        "model_version": result.model_version,
        "inputs": result.inputs,
        "context": result.context.model_dump(mode="json"),
    })
    if result.input_digest != expected_input_digest:
        raise ValueError("hydraulic-history assessment input digest mismatch")
    if canonical_digest(result.model_dump(mode="json")) != hydraulic_history_result_sha256:
        raise ValueError("hydraulic-history result digest mismatch")
    snapshots = result.values.get("flow_snapshots")
    if not isinstance(snapshots, list) or snapshot_index >= len(snapshots):
        raise ValueError("snapshot_index must identify a retained flow snapshot")
    snapshot = snapshots[snapshot_index]
    if not isinstance(snapshot, dict) or snapshot.get("status") != "computed":
        raise ValueError("selected hydraulic snapshot is not computed")
    velocity = snapshot.get("transport_face_velocity_m_s")
    flow_id = snapshot.get("flow_id")
    configuration_sha256 = snapshot.get("input_sha256")
    source_time_s = snapshot.get("elapsed_time_s")
    if (
        not isinstance(velocity, list)
        or len(velocity) != request.cell_count + 1
        or not isinstance(flow_id, str)
        or not isinstance(configuration_sha256, str)
        or re.fullmatch(r"[a-f0-9]{64}", configuration_sha256) is None
        or isinstance(source_time_s, bool)
        or not isinstance(source_time_s, (int, float))
        or not math.isfinite(source_time_s)
        or source_time_s < 0.0
    ):
        raise ValueError("selected flow snapshot lacks aligned face velocities or provider lineage")
    if (
        request.axial_advection_velocity_m_s is not None
        or request.axial_advection_provider_id is not None
        or request.axial_advection_source_result_sha256 is not None
        or request.axial_advection_source_time_s is not None
        or request.axial_advection_source_time_basis_id is not None
    ):
        raise ValueError("transport request already declares a different advection source")
    if any(value < 0.0 for value in velocity) and not (
        request.axial_flow_reversal_and_tip_boundary_reviewed
        and request.tip_advection_inflow_mol_m3 is not None
    ):
        raise ValueError("reverse flow requires reviewed reversal and explicit distal inflow concentrations")
    payload = request.model_dump(mode="json")
    payload.update({
        "axial_advection_velocity_m_s": velocity,
        "axial_advection_provider_id": flow_id,
        "axial_advection_configuration_sha256": configuration_sha256,
        "axial_advection_source_result_sha256": hydraulic_history_result_sha256,
        "axial_advection_source_time_s": source_time_s,
        "axial_advection_source_time_basis_id": result.context.time_basis,
    })
    return RestrictedTransportRequest.model_validate(payload)


def bind_planar_slit_hydraulic_history_series(
    transport_segment_requests: tuple[RestrictedTransportRequest, ...],
    hydraulic_history_result: AssessmentResult | dict,
    hydraulic_history_result_sha256: str,
) -> tuple[RestrictedTransportRequest, ...]:
    """Bind one exact starting hydraulic snapshot to every adjacent transport segment.

    Segment requests use local clocks beginning at zero and must span exactly
    the corresponding adjacent hydraulic-history knot interval.
    """
    if not isinstance(hydraulic_history_result, AssessmentResult):
        hydraulic_history_result = AssessmentResult.model_validate(hydraulic_history_result)
    result = hydraulic_history_result
    times = result.values.get("elapsed_time_s")
    snapshots = result.values.get("flow_snapshots")
    if (
        not isinstance(times, list)
        or len(times) < 2
        or not isinstance(snapshots, list)
        or len(snapshots) != len(times)
        or len(transport_segment_requests) != len(times) - 1
    ):
        raise ValueError("one transport segment is required for each adjacent hydraulic-history knot pair")
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in times
    ) or any(right <= left for left, right in zip(times[:-1], times[1:], strict=True)):
        raise ValueError("hydraulic-history clock must be finite and strictly increasing")
    bound = []
    for index, request in enumerate(transport_segment_requests):
        if not math.isclose(
            request.output_times_s[0], 0.0, rel_tol=0.0, abs_tol=1e-12
        ) or not math.isclose(
            request.output_times_s[-1], times[index + 1] - times[index], rel_tol=1e-12, abs_tol=1e-12
        ):
            raise ValueError("each local transport clock must exactly span its hydraulic knot interval")
        if not isinstance(snapshots[index], dict) or snapshots[index].get("elapsed_time_s") != times[index]:
            raise ValueError("hydraulic snapshot time differs from its declared history knot")
        bound.append(bind_planar_slit_hydraulic_snapshot(
            request,
            result,
            hydraulic_history_result_sha256,
            index,
        ))
    return tuple(bound)


def _bind_planar_slit_transient_hydraulic_interval_impl(
    request: RestrictedTransportRequest,
    hydraulic_history_result: AssessmentResult | dict,
    hydraulic_history_result_sha256: str,
    interval_index: int,
    *,
    face_aperture_interpolation_reviewed: bool,
    result_is_verified: bool = False,
) -> tuple[RestrictedTransportRequest, Callable[[float], np.ndarray]]:
    """Bind one exact transient slit-flow interval to a local transport request.

    The returned callback analytically evaluates the interval's lumped flow
    state and maps it to transport-face velocity. Interior face apertures use
    the same width-weighted linear reconstruction used by the steady slit
    solver; callers must explicitly review that spatial mapping.
    """
    if not isinstance(interval_index, int) or isinstance(interval_index, bool) or interval_index < 0:
        raise ValueError("interval_index must be a nonnegative integer")
    if face_aperture_interpolation_reviewed is not True:
        raise ValueError("cell-to-face aperture mapping requires explicit review")
    if not isinstance(hydraulic_history_result, AssessmentResult):
        hydraulic_history_result = AssessmentResult.model_validate(hydraulic_history_result)
    result = hydraulic_history_result
    if result.model_id != "corrosion.planar_slit_transient_hydraulic_history" or result.status != "computed":
        raise ValueError("a computed transient planar-slit hydraulic AssessmentResult is required")
    if not result_is_verified:
        expected_input_digest = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input_digest:
            raise ValueError("transient hydraulic assessment input digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != hydraulic_history_result_sha256:
            raise ValueError("transient hydraulic result digest mismatch")

    inputs = result.inputs
    values = result.values
    if (
        inputs.get("asset_id") != result.context.asset_id
        or inputs.get("location_id") != result.context.location_id
        or inputs.get("time_basis") != result.context.time_basis
    ):
        raise ValueError("hydraulic result input scope and RunContext identities must agree")
    times = inputs.get("time_s")
    cell_widths = inputs.get("cell_widths_m")
    apertures_by_interval = inputs.get("aperture_by_interval_m")
    interval_rows = values.get("interval_results")
    if (
        not isinstance(times, list)
        or len(times) < 2
        or not isinstance(cell_widths, list)
        or not isinstance(apertures_by_interval, list)
        or not isinstance(interval_rows, list)
        or len(interval_rows) != len(times) - 1
        or interval_index >= len(interval_rows)
        or len(cell_widths) != request.cell_count
        or len(apertures_by_interval) != len(interval_rows)
    ):
        raise ValueError("transient hydraulic history does not align with this transport interval")
    start, end = times[interval_index], times[interval_index + 1]
    duration = end - start
    if (
        not math.isfinite(duration)
        or duration <= 0.0
        or not math.isclose(request.output_times_s[0], 0.0, rel_tol=0.0, abs_tol=1e-12)
        or not math.isclose(request.output_times_s[-1], duration, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise ValueError("local transport clock must span exactly one transient hydraulic interval")
    interval = interval_rows[interval_index]
    gaps = apertures_by_interval[interval_index]
    if (
        not isinstance(interval, dict)
        or not isinstance(gaps, list)
        or len(gaps) != request.cell_count
        or interval.get("start_time_s") != start
        or interval.get("end_time_s") != end
    ):
        raise ValueError("selected hydraulic interval metadata is inconsistent")
    flow_history = values.get("volumetric_flow_history_m3_s")
    output_times = values.get("time_s")
    output_cell_ids = values.get("cell_ids")
    pressure_history = inputs.get("pressure_drop_by_interval_Pa")
    if (
        not isinstance(flow_history, list)
        or len(flow_history) != len(times)
        or output_times != times
        or output_cell_ids != inputs.get("cell_ids")
        or not isinstance(pressure_history, list)
        or len(pressure_history) != len(interval_rows)
        or interval.get("cell_aperture_m") != gaps
        or interval.get("pressure_drop_Pa") != pressure_history[interval_index]
    ):
        raise ValueError("transient hydraulic result rows do not reproduce their ordered input history")
    width = float(inputs["transverse_width_m"])
    lengths = tuple(float(value) for value in cell_widths)
    gaps = tuple(float(value) for value in gaps)
    if any(not math.isfinite(value) or value <= 0.0 for value in (*lengths, *gaps)):
        raise ValueError("slit cell lengths and interval apertures must be finite and positive")
    if not math.isfinite(width) or width <= 0.0:
        raise ValueError("transverse slit width must be finite and positive")

    face_gaps = [gaps[0]]
    for index in range(1, len(gaps)):
        left_half = lengths[index - 1] / 2.0
        right_half = lengths[index] / 2.0
        face_gaps.append((gaps[index - 1] * right_half + gaps[index] * left_half) / (left_half + right_half))
    face_gaps.append(gaps[-1])
    if any(not math.isfinite(value) or value <= 0.0 for value in face_gaps):
        raise ValueError("reconstructed slit face apertures must be finite and positive")

    start_flow = float(interval["start_volumetric_flow_m3_s"])
    equilibrium_flow = float(interval["equilibrium_volumetric_flow_m3_s"])
    rate = float(interval["momentum_relaxation_rate_s_inv"])
    end_flow = float(interval["end_volumetric_flow_m3_s"])
    if any(not math.isfinite(value) for value in (start_flow, equilibrium_flow, rate, end_flow)) or rate <= 0.0:
        raise ValueError("transient hydraulic interval contains invalid flow state data")
    viscosity = float(inputs["dynamic_viscosity_Pa_s"])
    density = float(inputs["density_kg_m3"])
    expected_resistance = math.fsum(
        12.0 * viscosity * length / (width * gap**3)
        for length, gap in zip(lengths, gaps, strict=True)
    )
    expected_inertance = math.fsum(
        density * length / (width * gap)
        for length, gap in zip(lengths, gaps, strict=True)
    )
    expected_equilibrium_flow = float(pressure_history[interval_index]) / expected_resistance
    expected_start_flow = (
        float(inputs["initial_volumetric_flow_m3_s"])
        if interval_index == 0
        else float(flow_history[interval_index])
    )
    expected_end_flow = expected_equilibrium_flow + (expected_start_flow - expected_equilibrium_flow) * math.exp(
        -rate * duration
    )
    scalar_checks = (
        (interval.get("series_resistance_Pa_s_m3"), expected_resistance),
        (interval.get("series_inertance_Pa_s2_m3"), expected_inertance),
        (rate, expected_resistance / expected_inertance),
        (equilibrium_flow, expected_equilibrium_flow),
        (start_flow, expected_start_flow),
        (end_flow, expected_end_flow),
        (float(flow_history[interval_index]), expected_start_flow),
        (float(flow_history[interval_index + 1]), expected_end_flow),
    )
    if any(
        isinstance(actual, bool)
        or not isinstance(actual, (int, float))
        or not math.isfinite(float(actual))
        or not math.isclose(float(actual), expected, rel_tol=1e-12, abs_tol=1e-18)
        for actual, expected in scalar_checks
    ):
        raise ValueError("transient hydraulic output is inconsistent with its declared slit momentum inputs")
    if min(start_flow, end_flow) < 0.0 and not (
        request.axial_flow_reversal_and_tip_boundary_reviewed
        and request.tip_advection_inflow_mol_m3 is not None
    ):
        raise ValueError("reverse flow requires a reviewed distal inflow composition")
    if (
        request.axial_advection_velocity_m_s is not None
        or request.axial_advection_provider_id is not None
        or request.axial_advection_source_result_sha256 is not None
    ):
        raise ValueError("transport request already declares a different axial-advection source")
    if not (
        request.axial_advection_and_flow_continuity_reviewed
        and request.time_varying_axial_advection_reviewed
    ):
        raise ValueError("time-varying axial-advection and flow-continuity reviews are required")

    provider_id = "matintegrity.transient_planar_slit_hydraulic_history"
    configuration_sha256 = canonical_digest({
        "hydraulic_result_sha256": hydraulic_history_result_sha256,
        "interval_index": interval_index,
        "interval_start_time_s": start,
        "interval_end_time_s": end,
        "face_aperture_mapping": "steady_slit_width_weighted_linear_cell_to_face_reconstruction_v1",
    })

    def velocity_at(local_time_s: float) -> np.ndarray:
        if isinstance(local_time_s, bool) or not math.isfinite(float(local_time_s)):
            raise ValueError("local transport time must be finite")
        local_time = float(local_time_s)
        tolerance = max(1e-15, duration * 1e-12)
        if local_time < -tolerance or local_time > duration + tolerance:
            raise ValueError("transient hydraulic callback cannot extrapolate beyond its interval")
        local_time = min(max(local_time, 0.0), duration)
        flow = equilibrium_flow + (start_flow - equilibrium_flow) * math.exp(-rate * local_time)
        velocity = np.asarray([flow / (width * gap) for gap in face_gaps], dtype=float)
        if not np.isfinite(velocity).all():
            raise ArithmeticError("transient slit face velocity exceeded finite numeric support")
        return velocity

    velocity_at.configuration_sha256 = configuration_sha256
    payload = request.model_dump(mode="json")
    payload.update({
        "axial_advection_provider_id": provider_id,
        "axial_advection_configuration_sha256": configuration_sha256,
        "axial_advection_source_result_sha256": hydraulic_history_result_sha256,
        "axial_advection_source_time_s": start,
        "axial_advection_source_time_basis_id": result.context.time_basis,
    })
    return RestrictedTransportRequest.model_validate(payload), velocity_at


def bind_planar_slit_transient_hydraulic_interval(
    request: RestrictedTransportRequest,
    hydraulic_history_result: AssessmentResult | dict,
    hydraulic_history_result_sha256: str,
    interval_index: int,
    *,
    face_aperture_interpolation_reviewed: bool,
) -> tuple[RestrictedTransportRequest, Callable[[float], np.ndarray]]:
    """Bind one digest-verified transient slit-flow interval to transport."""
    return _bind_planar_slit_transient_hydraulic_interval_impl(
        request,
        hydraulic_history_result,
        hydraulic_history_result_sha256,
        interval_index,
        face_aperture_interpolation_reviewed=face_aperture_interpolation_reviewed,
    )


def bind_planar_slit_transient_hydraulic_history_series(
    transport_segment_requests: tuple[RestrictedTransportRequest, ...],
    hydraulic_history_result: AssessmentResult | dict,
    hydraulic_history_result_sha256: str,
    *,
    face_aperture_interpolation_reviewed: bool,
) -> tuple[tuple[RestrictedTransportRequest, Callable[[float], np.ndarray]], ...]:
    """Bind every transport segment to adjacent transient hydraulic intervals.

    The upstream assessment digest is verified once, then reused across the
    ordered interval bindings. Each request must use a local clock spanning
    its corresponding hydraulic interval.
    """
    if not isinstance(hydraulic_history_result, AssessmentResult):
        hydraulic_history_result = AssessmentResult.model_validate(hydraulic_history_result)
    result = hydraulic_history_result
    if result.model_id != "corrosion.planar_slit_transient_hydraulic_history" or result.status != "computed":
        raise ValueError("a computed transient planar-slit hydraulic AssessmentResult is required")
    expected_input_digest = canonical_digest({
        "model_id": result.model_id,
        "model_version": result.model_version,
        "inputs": result.inputs,
        "context": result.context.model_dump(mode="json"),
    })
    if result.input_digest != expected_input_digest:
        raise ValueError("transient hydraulic assessment input digest mismatch")
    if canonical_digest(result.model_dump(mode="json")) != hydraulic_history_result_sha256:
        raise ValueError("transient hydraulic result digest mismatch")
    times = result.inputs.get("time_s")
    if not isinstance(times, list) or len(times) < 2 or len(transport_segment_requests) != len(times) - 1:
        raise ValueError("one local transport request is required per adjacent hydraulic-history interval")
    bound = []
    for index, request in enumerate(transport_segment_requests):
        bound.append(_bind_planar_slit_transient_hydraulic_interval_impl(
            request,
            result,
            hydraulic_history_result_sha256,
            index,
            face_aperture_interpolation_reviewed=face_aperture_interpolation_reviewed,
            result_is_verified=True,
        ))
    return tuple(bound)


def solve_restricted_transport(
    request: RestrictedTransportRequest,
    reaction: Callable[[float, np.ndarray], np.ndarray],
    tip_surface_flux: Callable[[float, np.ndarray, float | None], np.ndarray] | None = None,
    wall_surface_flux: Callable[[float, np.ndarray, np.ndarray | None], np.ndarray] | None = None,
    activity_coefficients: Callable[[float, np.ndarray], np.ndarray] | None = None,
    axial_advection_velocity: Callable[[float], np.ndarray] | None = None,
) -> dict:
    """Conservative planar transport with explicit mouth and optional reactive-tip boundaries."""
    activity_callback_lineage = None
    if activity_coefficients is not None:
        lineage_attributes = (
            "provider_id",
            "provider_revision",
            "configuration_sha256",
            "record_sha256",
            "source_request_sha256",
            "normalized_activity_table_sha256",
            "activity_table_source_record_lineage_sha256",
            "activity_table_evidence_sha256",
            "sit_interaction_parameter_sha256",
            "sit_evidence_sha256",
            "sit_provider_configuration_sha256",
            "interpolation_method",
            "species_ids",
            "temperature_K",
            "single_ion_activity_convention_id",
        )
        activity_callback_lineage = {
            name: list(value) if isinstance((value := getattr(activity_coefficients, name, None)), tuple) else value
            for name in lineage_attributes
            if getattr(activity_coefficients, name, None) is not None
        }
        runtime_trace = getattr(activity_coefficients, "runtime_trace", None)
        if isinstance(runtime_trace, dict):
            # Keep the live trace object so every provider evaluation becomes
            # part of the final AssessmentResult; hash immutable config fields.
            static_lineage = dict(activity_callback_lineage)
            activity_callback_lineage["runtime_trace"] = runtime_trace
            activity_callback_lineage["callback_lineage_sha256"] = canonical_digest(static_lineage)
        elif activity_callback_lineage:
            activity_callback_lineage["callback_lineage_sha256"] = canonical_digest(activity_callback_lineage)
    base = dict(
        simulation_id=request.simulation_id,
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        status="needs_data",
        activity_callback_lineage=activity_callback_lineage,
    )
    if not request.geometry_diffusion_reaction_basis_reviewed:
        return base
    if (
        (request.axial_advection_velocity_m_s is not None or axial_advection_velocity is not None)
        and not request.axial_advection_and_flow_continuity_reviewed
    ):
        return base
    if request.axial_advection_velocity_m_s is not None and axial_advection_velocity is not None:
        raise ValueError("select a static advection profile or a time-varying callback, not both")
    if request.axial_advection_velocity_m_s is not None and any(
        velocity < 0.0 for velocity in request.axial_advection_velocity_m_s
    ) and not request.axial_flow_reversal_and_tip_boundary_reviewed:
        return base | dict(reason="Static reverse flow requires reviewed reversal and a distal inflow boundary")
    if axial_advection_velocity is not None:
        if not (request.time_varying_axial_advection_reviewed and request.axial_advection_provider_id):
            return base | dict(reason="Time-varying advection provider and review are required")
        callback_digest = getattr(axial_advection_velocity, "configuration_sha256", None)
        if callback_digest is not None and callback_digest != request.axial_advection_configuration_sha256:
            raise ValueError("advection callback configuration digest differs from request")
    elif request.axial_advection_provider_id is not None and request.axial_advection_velocity_m_s is None:
        return base | dict(reason="Declared time-varying advection provider callback is unavailable")
    if (
        request.cell_cross_section_m2 is not None
        and not request.variable_area_one_dimensional_reduction_reviewed
    ):
        return base
    if (
        request.mouth_concentration_history_mol_m3 is not None
        and not request.mouth_history_interpolation_reviewed
    ):
        return base
    callback_digest = getattr(reaction, "configuration_sha256", None)
    if callback_digest is not None and callback_digest != request.reaction_configuration_sha256:
        raise ValueError("reaction callback configuration digest differs from transport request")
    if request.prescribed_potential_V is not None and not request.prescribed_field_migration_reviewed:
        return base
    if request.poisson_permittivity_F_m is not None and not request.poisson_boundary_and_charge_reviewed:
        return base
    if tip_surface_flux is not None and not (
        request.tip_surface_provider_id
        and request.tip_surface_configuration_sha256
        and request.tip_surface_flux_basis_reviewed
    ):
        return base
    if tip_surface_flux is None and request.tip_surface_provider_id is not None:
        raise ValueError("declared surface provider requires its callback")
    if wall_surface_flux is not None:
        if not (
            request.wall_area_per_volume_m2_m3 is not None
            and request.wall_surface_provider_id
            and request.wall_surface_configuration_sha256
            and request.wall_surface_flux_basis_reviewed
        ):
            return base
        digest = getattr(wall_surface_flux, "configuration_sha256", None)
        if digest is not None and digest != request.wall_surface_configuration_sha256:
            raise ValueError("wall callback configuration digest differs from request")
    elif request.wall_surface_provider_id is not None:
        return base | dict(reason="Declared wall surface provider callback is unavailable")
    if activity_coefficients is not None:
        if not (
            request.activity_provider_id
            and request.activity_configuration_sha256
            and request.activity_chemical_potential_and_tracer_diffusivity_reviewed
        ):
            return base
        digest = getattr(activity_coefficients, "configuration_sha256", None)
        if digest is not None and digest != request.activity_configuration_sha256:
            raise ValueError("activity callback configuration digest differs from request")
        callback_provider_id = getattr(activity_coefficients, "provider_id", None)
        if callback_provider_id is not None and callback_provider_id != request.activity_provider_id:
            raise ValueError("activity callback provider ID differs from the restricted transport request")
        callback_species = getattr(activity_coefficients, "species_ids", None)
        if callback_species is not None and tuple(callback_species) != tuple(request.species_ids):
            raise ValueError("activity callback species order must match the restricted transport request")
    elif request.activity_provider_id is not None:
        return base | dict(reason="Declared activity provider callback is unavailable")
    from scipy.integrate import solve_ivp

    count = request.cell_count
    species = len(request.species_ids)
    widths = np.asarray(
        request.cell_widths_m if request.cell_widths_m is not None else (request.length_m / count,) * count,
        dtype=float,
    )
    face_distances = np.concatenate(([widths[0] * 0.5], (widths[:-1] + widths[1:]) * 0.5))
    centers = np.cumsum(widths) - widths * 0.5
    geometry_clock = np.asarray(request.output_times_s, dtype=float)
    cell_area_history = (
        np.asarray(request.cell_cross_section_history_m2, dtype=float) / request.reference_cross_section_m2
        if request.cell_cross_section_history_m2 is not None
        else None
    )
    face_area_history = (
        np.asarray(request.face_cross_section_history_m2, dtype=float) / request.reference_cross_section_m2
        if request.face_cross_section_history_m2 is not None
        else None
    )
    wall_density_history = (
        np.asarray(request.wall_area_per_volume_history_m2_m3, dtype=float)
        if request.wall_area_per_volume_history_m2_m3 is not None
        else None
    )
    relative_cell_area = (
        cell_area_history[0].copy()
        if cell_area_history is not None
        else (
            np.asarray(request.cell_cross_section_m2) / request.reference_cross_section_m2
            if request.cell_cross_section_m2 is not None
            else np.ones(count)
        )
    )
    relative_face_area = (
        face_area_history[0].copy()
        if face_area_history is not None
        else (
            np.asarray(request.face_cross_section_m2) / request.reference_cross_section_m2
            if request.face_cross_section_m2 is not None
            else np.ones(count + 1)
        )
    )
    volume_per_reference_area = relative_cell_area * widths
    if not (
        np.isfinite(relative_cell_area).all()
        and np.isfinite(relative_face_area).all()
        and np.isfinite(volume_per_reference_area).all()
        and np.all(volume_per_reference_area > 0)
        and np.all(relative_face_area > 0)
    ):
        return base | dict(status="out_of_scope", reason="Area normalization exceeds numeric range")
    static_velocity = (
        np.asarray(request.axial_advection_velocity_m_s, dtype=float)
        if request.axial_advection_velocity_m_s is not None
        else None
    )
    tip_advection_inflow = (
        np.asarray(request.tip_advection_inflow_mol_m3, dtype=float)
        if request.tip_advection_inflow_mol_m3 is not None
        else None
    )
    advection_velocity_history = []

    def geometry_at(time_s):
        if cell_area_history is None:
            return relative_cell_area, relative_face_area, volume_per_reference_area
        cell = np.asarray([
            np.interp(time_s, geometry_clock, cell_area_history[:, index])
            for index in range(count)
        ])
        face = np.asarray([
            np.interp(time_s, geometry_clock, face_area_history[:, index])
            for index in range(count + 1)
        ])
        return cell, face, cell * widths

    def cell_volume_rate_at(time_s):
        if cell_area_history is None:
            return np.zeros(count)
        interval = int(np.searchsorted(geometry_clock, time_s, side="right") - 1)
        interval = min(max(interval, 0), len(geometry_clock) - 2)
        duration = geometry_clock[interval + 1] - geometry_clock[interval]
        return (
            (cell_area_history[interval + 1] - cell_area_history[interval])
            / duration
            * widths
        )

    def wall_density_at(time_s):
        if wall_density_history is None:
            return (
                np.asarray(request.wall_area_per_volume_m2_m3, dtype=float)
                if request.wall_area_per_volume_m2_m3 is not None
                else None
            )
        return np.asarray([
            np.interp(time_s, geometry_clock, wall_density_history[:, index])
            for index in range(count)
        ])

    def velocity_at(time):
        if axial_advection_velocity is None:
            return static_velocity
        velocity = np.asarray(axial_advection_velocity(float(time)), dtype=float)
        if velocity.shape != (count + 1,) or not np.isfinite(velocity).all():
            raise ValueError("time-varying advection callback must return one finite signed velocity per face")
        if np.any(velocity < 0) and not request.axial_flow_reversal_and_tip_boundary_reviewed:
            raise ValueError("negative face velocity requires reviewed flow reversal and distal inflow boundary")
        return velocity
    wall_area_over_reference_area = None
    wall_area_over_reference_area_history = None
    if request.wall_area_per_volume_m2_m3 is not None:
        wall_areas = (
            wall_density_history * (cell_area_history * widths[None, :])
            if wall_density_history is not None and cell_area_history is not None
            else np.asarray(request.wall_area_per_volume_m2_m3, dtype=float)[None, :] * volume_per_reference_area[None, :]
        )
        wall_terms = wall_areas[0]
        if not np.isfinite(wall_terms).all():
            return base | dict(status="out_of_scope", reason="Reactive wall area normalization exceeds numeric range")
        wall_area_over_reference_area = math.fsum(float(value) for value in wall_terms)
        if not math.isfinite(wall_area_over_reference_area) or wall_area_over_reference_area <= 0:
            return base | dict(status="out_of_scope", reason="Reactive wall area must be finite and positive")
        wall_area_over_reference_area_history = np.sum(wall_areas, axis=1)
        if not np.isfinite(wall_area_over_reference_area_history).all() or np.any(wall_area_over_reference_area_history <= 0):
            return base | dict(status="out_of_scope", reason="Moving reactive wall area is nonfinite or nonpositive")

    def poisson_potential(concentrations, time_s):
        from .transport_potential import reconstruct_transport_potential

        if request.reference_cross_section_m2 is None:
            return reconstruct_transport_potential(request, concentrations)
        cell_area, face_area, _ = geometry_at(float(time_s))
        return reconstruct_transport_potential(
            request,
            concentrations,
            cell_cross_section_m2=cell_area * request.reference_cross_section_m2,
            face_cross_section_m2=face_area * request.reference_cross_section_m2,
        )

    diffusion = np.asarray(request.diffusivity_m2_s)[:, None]
    mouth = np.asarray(request.mouth_concentration_mol_m3)
    mouth_history = (
        np.asarray(request.mouth_concentration_history_mol_m3)
        if request.mouth_concentration_history_mol_m3 is not None
        else None
    )

    def bernoulli(value):
        if abs(value) < 1e-5:
            return 1.0 - value * 0.5 + value * value / 12.0
        if value > 50:
            return value * math.exp(-value)
        if value < -50:
            return -value
        return value / math.expm1(value)

    migration_weights = None
    if request.prescribed_potential_V is not None:
        differences = np.diff(np.asarray(request.prescribed_potential_V))
        psi = (
            np.asarray(request.charge_numbers)[:, None]
            * 96485.33212
            * differences[None, :]
            / (8.31446261815324 * request.migration_temperature_K)
        )
        migration_weights = (np.vectorize(bernoulli)(psi), np.vectorize(bernoulli)(-psi))

    def derivative(time, flat):
        _, face_area, current_volume_per_reference_area = geometry_at(float(time))
        volume_rate_per_reference_area = cell_volume_rate_at(float(time))
        boundary_mouth = (
            mouth
            if mouth_history is None
            else np.array(
                [np.interp(time, request.output_times_s, mouth_history[:, index]) for index in range(species)]
            )
        )
        concentrations = flat[: species * count].reshape(species, count)
        supplied = concentrations.copy()
        supplied.setflags(write=False)
        source = np.asarray(reaction(time, supplied), dtype=float)
        if source.shape != concentrations.shape or not np.isfinite(source).all():
            raise ValueError("reaction source must be finite and match species by cell shape")
        flux = np.zeros((species, count + 1))
        flux[:, 0] = (
            np.asarray(request.diffusivity_m2_s) * (boundary_mouth - concentrations[:, 0]) / face_distances[0]
        )
        flux[:, 1:count] = -diffusion * (concentrations[:, 1:] - concentrations[:, :-1]) / face_distances[1:]
        potential = (
            np.asarray(request.prescribed_potential_V[1:], dtype=float)
            if request.prescribed_potential_V is not None
            else None
        )
        weights = migration_weights
        tip_potential = (
            request.prescribed_potential_V[-1] if request.prescribed_potential_V is not None else None
        )
        if request.poisson_permittivity_F_m is not None:
            potential = poisson_potential(concentrations, float(time))
            tip_potential = float(potential[-1])
            differences = np.diff(np.concatenate(([request.poisson_mouth_potential_V], potential)))
            psi = (
                np.asarray(request.charge_numbers)[:, None]
                * 96485.33212
                * differences[None, :]
                / (8.31446261815324 * request.migration_temperature_K)
            )
            weights = (np.vectorize(bernoulli)(psi), np.vectorize(bernoulli)(-psi))
        if activity_coefficients is not None:
            complete_state = np.column_stack((boundary_mouth, concentrations))
            complete_state.setflags(write=False)
            try:
                gamma = np.asarray(activity_coefficients(time, complete_state), dtype=float)
            except Exception as error:
                raise _TransportActivityCallbackFailure(type(error).__name__) from None
            if gamma.shape != complete_state.shape or not np.isfinite(gamma).all() or np.any(gamma <= 0):
                raise _TransportActivityCallbackFailure("invalid_gamma_shape_or_values")
            total_psi = np.diff(np.log(gamma), axis=1)
            if potential is not None:
                mouth_potential = (
                    request.prescribed_potential_V[0]
                    if request.prescribed_potential_V is not None
                    else request.poisson_mouth_potential_V
                )
                electrical_difference = np.diff(np.concatenate(([mouth_potential], potential)))
                total_psi += (
                    np.asarray(request.charge_numbers)[:, None]
                    * 96485.33212
                    * electrical_difference[None, :]
                    / (8.31446261815324 * request.migration_temperature_K)
                )
            weights = (np.vectorize(bernoulli)(total_psi), np.vectorize(bernoulli)(-total_psi))
        if weights is not None:
            forward, backward = weights
            flux[:, 0] = (
                np.asarray(request.diffusivity_m2_s)
                * (forward[:, 0] * boundary_mouth - backward[:, 0] * concentrations[:, 0])
                / face_distances[0]
            )
            flux[:, 1:count] = (
                diffusion
                * (forward[:, 1:] * concentrations[:, :-1] - backward[:, 1:] * concentrations[:, 1:])
                / face_distances[1:]
            )
        velocity = velocity_at(time)
        if velocity is not None:
            mouth_inward = np.where(velocity[0] >= 0, boundary_mouth, concentrations[:, 0])
            advective_flux = np.empty((species, count + 1), dtype=float)
            advective_flux[:, 0] = velocity[0] * mouth_inward
            if count > 1:
                positive_faces = velocity[1:count] >= 0
                advective_flux[:, 1:count] = velocity[None, 1:count] * np.where(
                    positive_faces[None, :], concentrations[:, :-1], concentrations[:, 1:]
                )
            distal_upwind = (
                concentrations[:, -1]
                if velocity[-1] >= 0
                else tip_advection_inflow
            )
            if distal_upwind is None:
                # A negative terminal velocity can occur later even if it is zero at the initial clock.
                raise ValueError("negative distal face velocity requires reviewed tip inflow concentrations")
            advective_flux[:, -1] = velocity[-1] * distal_upwind
            flux += advective_flux
        if tip_surface_flux is not None:
            surface_state = concentrations[:, -1].copy()
            surface_state.setflags(write=False)
            inward = np.asarray(tip_surface_flux(time, surface_state, tip_potential), dtype=float)
            if inward.shape != (species,) or not np.isfinite(inward).all():
                raise ValueError("tip surface callback must return finite inward molar flux per species")
            flux[:, -1] -= inward
        wall_source = np.zeros_like(concentrations)
        if wall_surface_flux is not None:
            supplied_potential = potential.copy() if potential is not None else None
            if supplied_potential is not None:
                supplied_potential.setflags(write=False)
            wall_flux = np.asarray(wall_surface_flux(time, supplied, supplied_potential), dtype=float)
            if wall_flux.shape != concentrations.shape or not np.isfinite(wall_flux).all():
                raise ValueError("wall callback must return finite inward molar flux per species and cell")
            current_wall_density = wall_density_at(float(time))
            if current_wall_density is None:
                raise ValueError("wall-surface flux requires a time-supported area-density field")
            wall_source = wall_flux * current_wall_density
        # Convert local-face flux densities to amounts per fixed reference cross section.
        reference_flux = flux * face_area
        concentration_rates = (
            (reference_flux[:, :-1] - reference_flux[:, 1:]) / current_volume_per_reference_area
            + source
            + wall_source
            - concentrations * volume_rate_per_reference_area[None, :] / current_volume_per_reference_area[None, :]
        ).ravel()
        # Integrate signed reservoir, surface and volumetric reaction amounts on the solver clock.
        wall_amount_rate = wall_source * current_volume_per_reference_area
        return np.concatenate(
            (
                concentration_rates,
                reference_flux[:, 0],
                -reference_flux[:, -1],
                (source * current_volume_per_reference_area).sum(axis=1),
                wall_amount_rate.ravel(),
            )
        )

    initial = np.asarray(request.initial_concentration_mol_m3, dtype=float)
    jacobian_sparsity = None
    if request.callbacks_cell_locality_reviewed and request.poisson_permittivity_F_m is None:
        from scipy.sparse import lil_matrix

        size = species * (2 * count + 3)
        structure = lil_matrix((size, size), dtype=int)
        for cell in range(count):
            for first in range(species):
                row = first * count + cell
                for second in range(species):
                    structure[row, second * count + cell] = 1
                if cell > 0:
                    structure[row, row - 1] = 1
                if cell + 1 < count:
                    structure[row, row + 1] = 1
        structure[species * count :, : species * count] = 1
        jacobian_sparsity = structure.tocsc()
    absolute_tolerance = np.concatenate(
        (
            np.full(species * count, request.concentration_absolute_tolerance_mol_m3),
            np.full(3 * species + species * count, request.integrated_amount_absolute_tolerance_mol_m2),
        )
    )
    initial_state = np.concatenate((initial.ravel(), np.zeros(3 * species + species * count)))
    solver_options = dict(
        method="BDF",
        rtol=request.solver_relative_tolerance,
        atol=absolute_tolerance,
        max_step=request.maximum_solver_step_s if request.maximum_solver_step_s is not None else np.inf,
        jac_sparsity=jacobian_sparsity,
    )
    if cell_area_history is None:
        try:
            solution = solve_ivp(
                derivative,
                (0, request.output_times_s[-1]),
                initial_state,
                t_eval=request.output_times_s,
                **solver_options,
            )
        except _TransportActivityCallbackFailure as error:
            return base | dict(
                status="out_of_scope",
                reason="external_activity_callback_failed_during_transport_integration",
                provider_error_type=error.provider_error_type,
                completed_output_time_count=0,
            )
    else:
        # Area slopes change at supplied knots. Stop the implicit integrator
        # at each knot so no BDF step straddles a discontinuity in dV/dt.
        states = [initial_state]
        current_state = initial_state
        nfev = njev = nlu = 0
        messages = []
        for segment_index, (left, right) in enumerate(
            zip(request.output_times_s[:-1], request.output_times_s[1:], strict=True)
        ):
            try:
                segment_solution = solve_ivp(
                    derivative,
                    (left, right),
                    current_state,
                    t_eval=(right,),
                    **solver_options,
                )
            except _TransportActivityCallbackFailure as error:
                return base | dict(
                    status="out_of_scope",
                    reason="external_activity_callback_failed_during_transport_integration",
                    provider_error_type=error.provider_error_type,
                    failed_geometry_segment_index=segment_index,
                    failed_interval_time_s={"start": left, "end": right},
                    completed_geometry_segment_count=len(states) - 1,
                )
            nfev += segment_solution.nfev
            njev += segment_solution.njev or 0
            nlu += segment_solution.nlu or 0
            messages.append(segment_solution.message)
            if not segment_solution.success or segment_solution.y.shape[1] != 1:
                return base | dict(
                    status="out_of_scope",
                    failed_geometry_segment_index=segment_index,
                    solver_message=segment_solution.message,
                    completed_geometry_segment_count=len(states) - 1,
                )
            current_state = segment_solution.y[:, -1]
            states.append(current_state)
        solution = SimpleNamespace(
            t=np.asarray(request.output_times_s, dtype=float),
            y=np.column_stack(states),
            success=True,
            message="; ".join(messages),
            nfev=nfev,
            njev=njev,
            nlu=nlu,
        )
    if not solution.success:
        return base | dict(status="out_of_scope", solver_message=solution.message)
    fields = solution.y[: species * count].T.reshape(-1, species, count)
    if not np.isfinite(fields).all() or np.any(fields < 0):
        return base | dict(
            status="out_of_scope", reason="Nonphysical or nonfinite concentration; values were not clipped."
        )
    potential_history = None
    if request.prescribed_potential_V is not None:
        potential_history = [list(request.prescribed_potential_V[1:]) for _ in solution.t]
    elif request.poisson_permittivity_F_m is not None:
        potential_history = [
            poisson_potential(concentrations, float(time_s)).tolist()
            for time_s, concentrations in zip(solution.t, fields, strict=True)
        ]
    ledger = solution.y[species * count :].T
    global_amounts = ledger[:, : 3 * species].reshape(-1, 3, species)
    wall_amounts_by_cell = ledger[:, 3 * species :].reshape(-1, species, count)
    wall_amounts = wall_amounts_by_cell.sum(axis=2)
    amounts = np.concatenate((global_amounts, wall_amounts[:, None, :]), axis=1)
    if static_velocity is not None or axial_advection_velocity is not None:
        try:
            advection_velocity_history = [velocity_at(time).tolist() for time in solution.t]
        except ValueError as error:
            return base | dict(status="out_of_scope", reason=str(error))
    volume_history_per_reference_area = np.asarray([
        geometry_at(float(time_s))[2] for time_s in solution.t
    ])
    inventory = (fields * volume_history_per_reference_area[:, None, :]).sum(axis=2)
    if not (
        np.isfinite(amounts).all()
        and np.isfinite(inventory).all()
        and (potential_history is None or np.isfinite(potential_history).all())
    ):
        return base | dict(
            status="out_of_scope", reason="Nonfinite inventory, accumulated amount or potential"
        )
    residual = inventory - inventory[0] - amounts.sum(axis=1)
    balance_scale = np.maximum(np.abs(inventory), np.abs(inventory[0]) + np.abs(amounts).sum(axis=1))
    balance_limit = (
        request.inventory_absolute_tolerance_mol_m2 + request.inventory_relative_tolerance * balance_scale
    )
    if not (np.isfinite(residual).all() and np.isfinite(balance_limit).all()):
        return base | dict(status="out_of_scope", reason="Inventory-balance arithmetic exceeds numeric range")
    balance_within_tolerance = bool(np.all(np.abs(residual) <= balance_limit))
    return base | dict(
        status="computed" if balance_within_tolerance else "out_of_scope",
        elapsed_time_s=solution.t.tolist(),
        species_ids=list(request.species_ids),
        mouth_concentration_history_mol_m3=mouth_history.tolist() if mouth_history is not None else None,
        mouth_boundary_interpolation="piecewise_linear_on_output_clock"
        if mouth_history is not None
        else "constant",
        concentration_mol_m3=fields.tolist(),
        solution_potential_V=potential_history,
        cell_centers_m=centers.tolist(),
        cell_widths_m=widths.tolist(),
        cell_cross_section_m2=list(request.cell_cross_section_m2)
        if request.cell_cross_section_m2 is not None
        else None,
        cell_cross_section_history_m2=(
            np.asarray(request.cell_cross_section_history_m2, dtype=float).tolist()
            if request.cell_cross_section_history_m2 is not None
            else None
        ),
        face_cross_section_m2=list(request.face_cross_section_m2)
        if request.face_cross_section_m2 is not None
        else None,
        face_cross_section_history_m2=(
            np.asarray(request.face_cross_section_history_m2, dtype=float).tolist()
            if request.face_cross_section_history_m2 is not None
            else None
        ),
        reference_cross_section_m2=request.reference_cross_section_m2,
        moving_geometry_provider_id=request.moving_geometry_provider_id,
        moving_geometry_configuration_sha256=request.moving_geometry_configuration_sha256,
        moving_geometry_source_result_sha256=request.moving_geometry_source_result_sha256,
        moving_geometry_time_basis_id=request.moving_geometry_time_basis_id,
        moving_geometry_interpolation="piecewise_linear_on_requested_output_clock"
        if cell_area_history is not None
        else "static",
        moving_geometry_inventory_dilution_reviewed=request.moving_geometry_inventory_dilution_reviewed,
        inventory_area_basis="fixed_reference_axial_cross_section"
        if request.reference_cross_section_m2 is not None
        else "uniform_unit_axial_area",
        tip_area_over_reference_area=float(relative_face_area[-1]),
        mouth_area_over_reference_area=float(relative_face_area[0]),
        mouth_area_over_reference_area_history=[
            float(geometry_at(float(time_s))[1][0]) for time_s in solution.t
        ],
        tip_area_over_reference_area_history=[
            float(geometry_at(float(time_s))[1][-1]) for time_s in solution.t
        ],
        inventory_per_unit_area_mol_m2=inventory.tolist(),
        cumulative_mouth_inward_mol_m2=amounts[:, 0, :].tolist(),
        cumulative_tip_inward_mol_m2=amounts[:, 1, :].tolist(),
        cumulative_homogeneous_source_mol_m2=amounts[:, 2, :].tolist(),
        cumulative_wall_inward_mol_m2=amounts[:, 3, :].tolist(),
        cumulative_wall_inward_by_cell_mol_m2=wall_amounts_by_cell.tolist(),
        wall_area_per_volume_m2_m3=list(request.wall_area_per_volume_m2_m3)
        if request.wall_area_per_volume_m2_m3 is not None
        else None,
        wall_area_per_volume_history_m2_m3=(
            np.asarray(request.wall_area_per_volume_history_m2_m3, dtype=float).tolist()
            if request.wall_area_per_volume_history_m2_m3 is not None
            else None
        ),
        activity_provider_id=request.activity_provider_id,
        activity_configuration_sha256=request.activity_configuration_sha256,
        wall_area_over_reference_area=wall_area_over_reference_area,
        wall_area_over_reference_area_history_m2_m2=wall_area_over_reference_area_history.tolist()
        if wall_area_over_reference_area_history is not None
        else None,
        axial_advection_velocity_m_s=list(request.axial_advection_velocity_m_s)
        if request.axial_advection_velocity_m_s is not None
        else None,
        axial_advection_velocity_history_m_s=advection_velocity_history or None,
        axial_advection_provider_id=request.axial_advection_provider_id,
        axial_advection_configuration_sha256=request.axial_advection_configuration_sha256,
        axial_advection_source_result_sha256=request.axial_advection_source_result_sha256,
        axial_advection_source_time_s=request.axial_advection_source_time_s,
        axial_advection_source_time_basis_id=request.axial_advection_source_time_basis_id,
        flow_reversal_supported=request.axial_flow_reversal_and_tip_boundary_reviewed,
        species_inventory_balance_residual_mol_m2=residual.tolist(),
        inventory_balance_within_declared_tolerance=balance_within_tolerance,
        solver_configuration=dict(
            method="BDF",
            relative_tolerance=request.solver_relative_tolerance,
            concentration_absolute_tolerance_mol_m3=request.concentration_absolute_tolerance_mol_m3,
            integrated_amount_absolute_tolerance_mol_m2=request.integrated_amount_absolute_tolerance_mol_m2,
            maximum_step_s=request.maximum_solver_step_s,
            jacobian_structure="reviewed_cell_local" if jacobian_sparsity is not None else "dense_nonlocal",
            function_evaluations=solution.nfev,
            jacobian_evaluations=solution.njev,
            linear_factorizations=solution.nlu,
        ),
        basis="One-dimensional transport on uniform/nonuniform cells and explicit optional variable cross sections; prescribed or Poisson potential, Scharfetter-Gummel migration, explicit homogeneous sources, static nonnegative or caller-callback signed time-varying upwind advection, and reactive tip. A caller-prescribed cross-section history may vary piecewise-linearly at requested output knots; the concentration equation includes the conservative inventory dilution/expansion term implied by d(cell volume)/dt, and inventory is evaluated with each output-time geometry. Moving geometry remains prescribed and is not fed back from chemistry or wall flux; pressure/momentum continuity, geometry provider quality, activity calibration, wall kinetics, mesh registration, material qualification and acceptance remain external.",
    )
