"""Explicit constant-aperture planar slit reduction for restricted transport."""

import math
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, Nonnegative, Positive, canonical_digest


class PlanarSlitEndpointVelocityPath(Contract):
    """Digest-bound local-time path between two reviewed steady slit-flow states."""

    path_id: str = Field(min_length=1)
    global_start_time_s: Nonnegative
    global_end_time_s: Positive
    start_face_velocity_m_s: tuple[float, ...] = Field(min_length=3, max_length=2001)
    end_face_velocity_m_s: tuple[float, ...] = Field(min_length=3, max_length=2001)
    start_hydraulic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    end_hydraulic_input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    end_hydraulic_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    end_pressure_drop_Pa: float
    pressure_history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    fluid_property_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    end_pressure_interpolation_lineage: dict
    endpoint_velocity_interpolation_reviewed: bool

    @model_validator(mode="after")
    def aligned_endpoint_states(self):
        if self.global_end_time_s <= self.global_start_time_s:
            raise ValueError("hydraulic endpoint path requires a strictly increasing global time interval")
        if len(self.start_face_velocity_m_s) != len(self.end_face_velocity_m_s):
            raise ValueError("hydraulic endpoint vectors must use the same ordered face grid")
        if not all(
            math.isfinite(value)
            for value in (*self.start_face_velocity_m_s, *self.end_face_velocity_m_s)
        ):
            raise ValueError("hydraulic endpoint velocities must be finite")
        if not self.endpoint_velocity_interpolation_reviewed:
            raise ValueError("linear endpoint velocity interpolation requires explicit caller review")
        lineage = self.end_pressure_interpolation_lineage
        policy = lineage.get("interpolation_policy")
        left_time = lineage.get("source_start_time_s")
        right_time = lineage.get("source_end_time_s")
        fraction = lineage.get("interpolation_fraction")
        left_index = lineage.get("source_start_index")
        right_index = lineage.get("source_end_index")
        if policy not in {"exact_requested_knots", "piecewise_linear"}:
            raise ValueError("pressure lineage must identify an explicit interpolation policy")
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in (left_index, right_index)
        ):
            raise ValueError("pressure lineage must identify nonnegative integer source indices")
        if any(
            isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
            for value in (left_time, right_time, fraction, self.end_pressure_drop_Pa)
        ):
            raise ValueError("pressure and interpolation lineage values must be finite numbers")
        if not 0.0 <= fraction <= 1.0 or not left_time <= self.global_end_time_s <= right_time:
            raise ValueError("pressure lineage bracket must cover the endpoint without extrapolation")
        if policy == "exact_requested_knots" and not (
            left_time == right_time == self.global_end_time_s
            and left_index == right_index
            and fraction == 0.0
        ):
            raise ValueError("exact pressure-knot lineage must identify one matching source knot")
        if policy == "piecewise_linear" and (
            right_time <= left_time or right_index != left_index + 1
        ):
            raise ValueError("piecewise pressure lineage must identify adjacent ordered knots")
        if policy == "piecewise_linear":
            expected_fraction = (self.global_end_time_s - left_time) / (right_time - left_time)
            if not math.isclose(fraction, expected_fraction, rel_tol=1e-12, abs_tol=1e-15):
                raise ValueError("pressure interpolation fraction does not match the endpoint time")
        return self

    @property
    def provider_id(self) -> str:
        return "matintegrity.crevice_geometry.planar_slit_endpoint_velocity_path"

    @property
    def source_sha256(self) -> str:
        return canonical_digest({
            "start_hydraulic_result_sha256": self.start_hydraulic_result_sha256,
            "end_hydraulic_input_sha256": self.end_hydraulic_input_sha256,
            "end_hydraulic_result_sha256": self.end_hydraulic_result_sha256,
        })

    @property
    def configuration_sha256(self) -> str:
        return canonical_digest({
            "provider_id": self.provider_id,
            "path": self.model_dump(mode="json"),
            "source_sha256": self.source_sha256,
        })

    def __call__(self, local_elapsed_time_s: float) -> tuple[float, ...]:
        """Return face velocities at segment-local elapsed seconds without extrapolation."""
        if isinstance(local_elapsed_time_s, bool):
            raise ValueError("local elapsed time must be numeric, not boolean")
        try:
            local = float(local_elapsed_time_s)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("local elapsed time must be finite and numeric") from error
        duration = self.global_end_time_s - self.global_start_time_s
        if not math.isfinite(local) or local < 0.0 or local > duration:
            raise ValueError("local elapsed time is outside the reviewed hydraulic path")
        fraction = local / duration
        return tuple(
            start + fraction * (end - start)
            for start, end in zip(self.start_face_velocity_m_s, self.end_face_velocity_m_s, strict=True)
        )


class PlanarSlitGeometry(Contract):
    geometry_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cell_widths_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    aperture_m: Positive
    transverse_width_m: Positive
    reactive_broad_face_count: int = Field(ge=0, le=2)
    constant_aperture_cross_section_and_transverse_uniformity_reviewed: bool

    @model_validator(mode="after")
    def finite_geometry(self):
        length = math.fsum(self.cell_widths_m)
        area = self.aperture_m * self.transverse_width_m
        if not math.isfinite(length) or not math.isfinite(area) or area <= 0:
            raise ValueError("finite positive slit dimensions and cross section are required")
        if not math.isfinite(self.reactive_broad_face_count / self.aperture_m):
            raise ValueError("wall area density must be finite")
        return self


def planar_slit_transport_geometry(request: PlanarSlitGeometry) -> dict:
    base = dict(
        geometry_id=request.geometry_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        source_sha256=request.source_sha256,
    )

    if not request.constant_aperture_cross_section_and_transverse_uniformity_reviewed:
        return base
    area = request.aperture_m * request.transverse_width_m
    volumes = [area * width for width in request.cell_widths_m]
    wall_areas = [
        request.reactive_broad_face_count * request.transverse_width_m * width
        for width in request.cell_widths_m
    ]
    if not all(math.isfinite(value) for value in volumes + wall_areas):
        return base | dict(status="out_of_scope", reason="Nonfinite cell volume or wall area")
    return base | dict(
        status="computed",
        length_m=math.fsum(request.cell_widths_m),
        cell_count=len(request.cell_widths_m),
        cell_widths_m=list(request.cell_widths_m),
        axial_cross_section_m2=area,
        cell_volume_m3=volumes,
        reactive_broad_wall_area_m2=wall_areas,
        wall_area_per_volume_m2_m3=[request.reactive_broad_face_count / request.aperture_m] * len(volumes),
        basis="Constant-area planar slit; supplied broad faces only. Edge walls, aperture evolution, transverse gradients, hydraulic advection and wall kinetics are excluded. Transport mol/m2 ledgers use axial cross-sectional area, not reactive wall area.",
    )


class PlanarSlitApertureHistory(Contract):
    """Sequentially update a slit geometry from a reviewed cumulative wall-recession history."""

    geometry_id: str = Field(min_length=1)
    geometry_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    wall_loss_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cell_widths_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    initial_cell_aperture_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    transverse_width_m: Positive
    reference_cross_section_m2: Positive
    reactive_broad_face_count: Literal[1, 2]
    elapsed_time_s: tuple[Nonnegative, ...] | None = Field(default=None, min_length=2, max_length=5000)
    cumulative_signed_cell_average_recession_m: tuple[tuple[float, ...], ...] | None = Field(
        default=None, min_length=2, max_length=5000
    )
    wall_loss_result: dict | None = None
    supported_minimum_aperture_m: Positive
    supported_maximum_aperture_m: Positive
    wall_recession_is_per_combined_reactive_area_reviewed: bool
    opposing_face_recession_is_equal_reviewed: bool = False
    cell_center_to_face_mapping_reviewed: bool
    geometry_basis_reviewed: bool

    @model_validator(mode="after")
    def aligned_geometry_history(self):
        count = len(self.cell_widths_m)
        if len(self.initial_cell_aperture_m) != count:
            raise ValueError("one initial aperture is required per axial cell")
        direct_history_supplied = (
            self.elapsed_time_s is not None or self.cumulative_signed_cell_average_recession_m is not None
        )
        if direct_history_supplied == (self.wall_loss_result is not None):
            raise ValueError("provide either a direct recession history or a wall-loss result, not both")
        if direct_history_supplied:
            if self.elapsed_time_s is None or self.cumulative_signed_cell_average_recession_m is None:
                raise ValueError("direct recession history requires both elapsed times and cell rows")
            if len(self.elapsed_time_s) != len(self.cumulative_signed_cell_average_recession_m):
                raise ValueError("recession rows must align with the geometry clock")
            if self.elapsed_time_s[0] != 0 or any(
                right <= left
                for left, right in zip(self.elapsed_time_s[:-1], self.elapsed_time_s[1:], strict=True)
            ):
                raise ValueError("geometry history requires zero-based, strictly increasing elapsed time")
            self._validate_recession_rows(self.cumulative_signed_cell_average_recession_m, count)
        if self.supported_maximum_aperture_m <= self.supported_minimum_aperture_m:
            raise ValueError("supported aperture bounds must be strictly ordered")
        if any(
            aperture < self.supported_minimum_aperture_m or aperture > self.supported_maximum_aperture_m
            for aperture in self.initial_cell_aperture_m
        ):
            raise ValueError("initial cell apertures must lie within the declared provider range")
        return self

    @staticmethod
    def _validate_recession_rows(rows, cell_count):
        if len(rows) < 2 or len(rows) > 5000:
            raise ValueError("recession history must contain between two and 5000 rows")
        if any(len(row) != cell_count for row in rows):
            raise ValueError("each recession row must contain one value per axial cell")
        if any(not math.isfinite(value) for row in rows for value in row):
            raise ValueError("cumulative signed recession values must be finite numbers")
        if any(value != 0 for value in rows[0]):
            raise ValueError("the initial cumulative recession row must be zero")


def planar_slit_aperture_history(request: PlanarSlitApertureHistory) -> dict:
    """Produce remapped cell geometry; a caller must rerun transport at each geometry state."""
    base = dict(
        geometry_id=request.geometry_id,
        status="needs_data",
        input_sha256=canonical_digest(request.model_dump(mode="json")),
        geometry_source_sha256=request.geometry_source_sha256,
        wall_loss_source_sha256=request.wall_loss_source_sha256,
    )
    if not (
        request.wall_recession_is_per_combined_reactive_area_reviewed
        and request.geometry_basis_reviewed
        and request.cell_center_to_face_mapping_reviewed
        and (request.reactive_broad_face_count == 1 or request.opposing_face_recession_is_equal_reviewed)
    ):
        return base

    elapsed_time_s = request.elapsed_time_s
    recession_history = request.cumulative_signed_cell_average_recession_m
    wall_loss_selection_sha256 = None
    face_count = request.reactive_broad_face_count
    if request.wall_loss_result is not None:
        if canonical_digest(request.wall_loss_result) != request.wall_loss_source_sha256:
            raise ValueError("wall-loss result digest differs from the caller-pinned value")
        loss_record = request.wall_loss_result
        status = loss_record.get("status")
        values = loss_record.get("values", loss_record)
        if status != "computed" or not isinstance(values, dict):
            return base | dict(
                status=status if status in {"needs_data", "out_of_scope"} else "needs_data",
                reason="A computed wall-loss result is required for geometry remapping",
            )
        wall_loss = values.get("wall_metal_loss")
        if not isinstance(wall_loss, dict) or not isinstance(wall_loss.get("cellwise_history"), list):
            return base | dict(
                status="needs_data",
                reason="The pinned wall-loss result must contain a reviewed cellwise recession history",
            )
        if wall_loss.get("reference_cross_section_m2") != request.reference_cross_section_m2:
            return base | dict(
                status="out_of_scope",
                reason="Geometry reference cross section differs from the pinned wall-loss calculation",
            )
        expected_cell_wall_area_ratios = [
            face_count * request.transverse_width_m * width / request.reference_cross_section_m2
            for width in request.cell_widths_m
        ]
        reported_total_wall_area_ratio = wall_loss.get("reactive_wall_area_over_reference_area")
        if (
            isinstance(reported_total_wall_area_ratio, bool)
            or not isinstance(reported_total_wall_area_ratio, (int, float))
            or not math.isfinite(reported_total_wall_area_ratio)
            or not math.isclose(
                reported_total_wall_area_ratio,
                math.fsum(expected_cell_wall_area_ratios),
                rel_tol=1e-8,
                abs_tol=1e-12,
            )
        ):
            return base | dict(
                status="out_of_scope",
                reason="Reactive wall area does not match the declared slit faces and cell widths",
            )
        if any(not isinstance(row, dict) for row in wall_loss["cellwise_history"]):
            return base | dict(status="needs_data", reason="Wall-loss history rows must be objects")
        elapsed_time_s = tuple(row.get("elapsed_time_s") for row in wall_loss["cellwise_history"])
        extracted_rows = []
        for row in wall_loss["cellwise_history"]:
            cells = row.get("cells")
            if not isinstance(cells, list) or len(cells) != len(request.cell_widths_m):
                return base | dict(
                    status="needs_data", reason="Cellwise wall-loss records do not match slit cell count"
                )
            if any(
                not isinstance(cell, dict)
                or isinstance(cell.get("cell_index"), bool)
                or not isinstance(cell.get("cell_index"), int)
                or cell.get("cell_index") != index
                or isinstance(cell.get("signed_local_cell_average_recession_m"), bool)
                or not isinstance(cell.get("signed_local_cell_average_recession_m"), (int, float))
                or not math.isfinite(cell.get("signed_local_cell_average_recession_m"))
                or isinstance(cell.get("reactive_wall_area_over_reference_area"), bool)
                or not isinstance(cell.get("reactive_wall_area_over_reference_area"), (int, float))
                or not math.isclose(
                    cell.get("reactive_wall_area_over_reference_area"),
                    expected_cell_wall_area_ratios[index],
                    rel_tol=1e-8,
                    abs_tol=1e-12,
                )
                for index, cell in enumerate(cells)
            ):
                return base | dict(
                    status="needs_data",
                    reason="Cellwise recession values, order or geometry area basis are invalid",
                )
            extracted_rows.append(tuple(cell["signed_local_cell_average_recession_m"] for cell in cells))
        try:
            invalid_clock_value = any(
                isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in elapsed_time_s
            )
            nonincreasing_clock = not invalid_clock_value and any(
                right <= left for left, right in zip(elapsed_time_s[:-1], elapsed_time_s[1:], strict=True)
            )
            if (
                len(elapsed_time_s) < 2
                or elapsed_time_s[0] != 0
                or invalid_clock_value
                or nonincreasing_clock
            ):
                return base | dict(
                    status="needs_data", reason="Wall-loss clock must start at zero and increase strictly"
                )
            PlanarSlitApertureHistory._validate_recession_rows(extracted_rows, len(request.cell_widths_m))
        except (TypeError, ValueError):
            return base | dict(status="needs_data", reason="Wall-loss time and cell rows are not aligned")
        recession_history = tuple(extracted_rows)
        wall_loss_selection_sha256 = values.get("selection_sha256")

    if elapsed_time_s is None or recession_history is None:
        return base | dict(status="needs_data", reason="A complete cellwise recession history is required")

    geometry_states = []

    def failed_geometry_state(reason: str, elapsed: float, cell_indices: list[int] | None = None) -> dict:
        interval_start = geometry_states[-1]["elapsed_time_s"] if geometry_states else None
        failure = base | dict(
            status="out_of_scope",
            reason=reason,
            geometry_states=geometry_states,
            computed_prefix_geometry_states=geometry_states,
            computed_prefix_interval_count=max(0, len(geometry_states) - 1),
            failed_elapsed_time_s=elapsed,
            failed_interval_time_s=(
                {"start": interval_start, "end": elapsed} if interval_start is not None else None
            ),
        )
        if cell_indices is not None:
            failure["first_out_of_range_elapsed_time_s"] = elapsed
            failure["first_out_of_range_cell_indices"] = cell_indices
        return failure

    for elapsed, recession_row in zip(elapsed_time_s, recession_history, strict=True):
        apertures = [
            # Signed recession uses the shared convention: positive means
            # metal removed, so opposing-face loss increases the gap.
            initial + face_count * recession
            for initial, recession in zip(request.initial_cell_aperture_m, recession_row, strict=True)
        ]
        if any(
            not math.isfinite(aperture)
            or aperture < request.supported_minimum_aperture_m
            or aperture > request.supported_maximum_aperture_m
            for aperture in apertures
        ):
            return failed_geometry_state(
                "Aperture left the caller-declared provider range; geometry update stops at the first unsupported state",
                elapsed,
                [
                    index
                    for index, aperture in enumerate(apertures)
                    if not math.isfinite(aperture)
                    or aperture < request.supported_minimum_aperture_m
                    or aperture > request.supported_maximum_aperture_m
                ],
            )
        cross_sections = [aperture * request.transverse_width_m for aperture in apertures]
        face_cross_sections = [cross_sections[0]]
        for index in range(1, len(cross_sections)):
            left_half_width = request.cell_widths_m[index - 1] / 2
            right_half_width = request.cell_widths_m[index] / 2
            face_cross_sections.append(
                (cross_sections[index - 1] * right_half_width + cross_sections[index] * left_half_width)
                / (left_half_width + right_half_width)
            )
        face_cross_sections.append(cross_sections[-1])
        volumes = [area * width for area, width in zip(cross_sections, request.cell_widths_m, strict=True)]
        wall_areas = [face_count * request.transverse_width_m * width for width in request.cell_widths_m]
        if not all(
            math.isfinite(value) and value > 0
            for value in cross_sections + face_cross_sections + volumes + wall_areas
        ):
            return failed_geometry_state(
                "Updated cell geometry exceeded numeric range",
                elapsed,
            )
        transport_geometry = dict(
            cell_count=len(request.cell_widths_m),
            length_m=math.fsum(request.cell_widths_m),
            cell_widths_m=list(request.cell_widths_m),
            cell_cross_section_m2=cross_sections,
            face_cross_section_m2=face_cross_sections,
            reference_cross_section_m2=request.reference_cross_section_m2,
            wall_area_per_volume_m2_m3=[
                area / volume for area, volume in zip(wall_areas, volumes, strict=True)
            ],
        )
        geometry_states.append(
            dict(
                elapsed_time_s=elapsed,
                cell_aperture_m=apertures,
                axial_cross_section_m2=cross_sections,
                cell_cross_section_m2=cross_sections,
                face_cross_section_m2=face_cross_sections,
                cell_volume_m3=volumes,
                reactive_broad_wall_area_m2=wall_areas,
                wall_area_per_volume_m2_m3=[
                    area / volume for area, volume in zip(wall_areas, volumes, strict=True)
                ],
                cumulative_signed_cell_average_recession_m=list(recession_row),
                restricted_transport_geometry=transport_geometry,
            )
        )
    return base | dict(
        status="computed",
        cell_count=len(request.cell_widths_m),
        cell_widths_m=list(request.cell_widths_m),
        transverse_width_m=request.transverse_width_m,
        reference_cross_section_m2=request.reference_cross_section_m2,
        reactive_broad_face_count=face_count,
        face_area_interpolation_basis=(
            "Linear interpolation of cross section between nonuniform cell centers; boundary faces use constant extrapolation from the nearest cell."
        ),
        wall_loss_selection_sha256=wall_loss_selection_sha256,
        geometry_states=geometry_states,
        basis=(
            "Sequential fixed-length planar slit update. Signed recession is positive metal loss and negative deposition. "
            "For two reactive broad faces, equal recession on opposing faces is assumed only when reviewed. "
            "This remaps geometry for caller-controlled subsequent transport; it does not couple flow, chemistry, "
            "stress, deposits, roughness, or time integration within an interval."
        ),
    )


class PlanarSlitHydraulicFlow(Contract):
    """Steady laminar Newtonian flow through a caller-declared variable-gap slit."""

    flow_id: str = Field(min_length=1)
    geometry_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    aperture_history_result: dict | None = None
    cell_widths_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    cell_aperture_m: tuple[Positive, ...] = Field(min_length=2, max_length=2000)
    transverse_width_m: Positive
    fluid_property_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pressure_drop_Pa: float
    dynamic_viscosity_Pa_s: Positive
    density_kg_m3: Positive
    minimum_width_to_aperture_ratio: Positive = Field(default=20.0, ge=20.0, le=1000.0)
    maximum_reviewed_reynolds_number: Positive = Field(default=1000.0, le=1000.0)
    geometry_and_boundary_pressures_reviewed: bool
    incompressible_newtonian_fluid_properties_reviewed: bool
    laminar_fully_developed_slit_assumption_reviewed: bool

    @model_validator(mode="after")
    def aligned_slit_cells(self):
        if len(self.cell_widths_m) != len(self.cell_aperture_m):
            raise ValueError("slit cell widths and apertures must have equal lengths")
        if self.aperture_history_result is not None:
            if canonical_digest(self.aperture_history_result) != self.geometry_source_sha256:
                raise ValueError("aperture history digest differs from the caller-pinned geometry result")
            values = self.aperture_history_result.get("values", self.aperture_history_result)
            states = values.get("geometry_states") if isinstance(values, dict) else None
            if not isinstance(states, list) or not states:
                raise ValueError("pinned aperture history must contain geometry_states")
            last = states[-1]
            declared_widths = values.get("cell_widths_m") if isinstance(values, dict) else None
            declared_apertures = last.get("cell_aperture_m") if isinstance(last, dict) else None
            if declared_widths != list(self.cell_widths_m) or declared_apertures != list(
                self.cell_aperture_m
            ):
                raise ValueError("hydraulic cell dimensions must match the pinned final aperture state")
        return self


def evaluate_planar_slit_hydraulic_flow(request: PlanarSlitHydraulicFlow) -> dict:
    """Calculate a steady series-resistance flow and face velocities for transport coupling.

    Uses the wide, parallel-plate slit relation. It does not solve transient pressure,
    compressible flow, inertia, entrance effects, roughness, or coupled aperture motion.
    """
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "flow_id": request.flow_id,
        "status": "needs_data",
        "input_sha256": input_digest,
        "geometry_source_sha256": request.geometry_source_sha256,
        "fluid_property_source_sha256": request.fluid_property_source_sha256,
        "basis": "Steady incompressible Newtonian laminar flow in a wide planar slit; cell hydraulic resistances are in series.",
    }
    reviews = {
        "geometry_and_boundary_pressures_reviewed": request.geometry_and_boundary_pressures_reviewed,
        "incompressible_newtonian_fluid_properties_reviewed": request.incompressible_newtonian_fluid_properties_reviewed,
        "laminar_fully_developed_slit_assumption_reviewed": request.laminar_fully_developed_slit_assumption_reviewed,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return base | {"missing_reviews": missing}

    width = float(request.transverse_width_m)
    gaps = np.asarray(request.cell_aperture_m, dtype=float)
    lengths = np.asarray(request.cell_widths_m, dtype=float)
    aspect = width / gaps
    if not np.isfinite(aspect).all() or np.any(aspect < request.minimum_width_to_aperture_ratio):
        return base | {
            "status": "out_of_scope",
            "reason": "At least one cell is too narrow for the declared parallel-plate slit approximation",
            "minimum_width_to_aperture_ratio": request.minimum_width_to_aperture_ratio,
            "minimum_observed_width_to_aperture_ratio": float(np.min(aspect)),
        }

    viscosity = float(request.dynamic_viscosity_Pa_s)
    resistance = 12.0 * viscosity * lengths / (width * gaps**3)
    total_resistance = float(math.fsum(float(value) for value in resistance))
    flow = float(request.pressure_drop_Pa) / total_resistance
    if not math.isfinite(total_resistance) or total_resistance <= 0 or not math.isfinite(flow):
        return base | {
            "status": "out_of_scope",
            "reason": "Slit hydraulic resistance or flow exceeded finite numeric support",
        }

    cross_sections = width * gaps
    cell_velocity = flow / cross_sections
    face_gaps = np.empty(len(gaps) + 1, dtype=float)
    face_gaps[0], face_gaps[-1] = gaps[0], gaps[-1]
    for i in range(1, len(gaps)):
        left_half = lengths[i - 1] / 2.0
        right_half = lengths[i] / 2.0
        face_gaps[i] = (gaps[i - 1] * right_half + gaps[i] * left_half) / (left_half + right_half)
    face_velocity = flow / (width * face_gaps)
    hydraulic_diameter = 2.0 * width * gaps / (width + gaps)
    reynolds = float(request.density_kg_m3) * np.abs(cell_velocity) * hydraulic_diameter / viscosity
    pressure_drop_cells = resistance * flow
    pressure_nodes = [float(request.pressure_drop_Pa)]
    for drop in pressure_drop_cells:
        pressure_nodes.append(pressure_nodes[-1] - float(drop))
    if not (
        np.isfinite(cell_velocity).all()
        and np.isfinite(face_velocity).all()
        and np.isfinite(reynolds).all()
        and np.isfinite(pressure_nodes).all()
    ):
        return base | {
            "status": "out_of_scope",
            "reason": "Derived slit flow field exceeded finite numeric support",
        }
    exceeds_reviewed_laminar_range = bool(np.any(reynolds > request.maximum_reviewed_reynolds_number))
    return base | {
        "status": "out_of_scope" if exceeds_reviewed_laminar_range else "computed",
        "reason": "At least one cell exceeds the caller-declared laminar Reynolds-number limit"
        if exceeds_reviewed_laminar_range
        else None,
        "volume_flow_rate_m3_s": flow,
        "total_hydraulic_resistance_Pa_s_m3": total_resistance,
        "cell_pressure_drop_Pa": pressure_drop_cells.tolist(),
        "cell_boundary_pressure_Pa": pressure_nodes,
        "cell_mean_velocity_m_s": cell_velocity.tolist(),
        "transport_face_velocity_m_s": face_velocity.tolist(),
        "cell_hydraulic_diameter_m": hydraulic_diameter.tolist(),
        "cell_reynolds_number_based_on_hydraulic_diameter": reynolds.tolist(),
        "maximum_cell_reynolds_number": float(np.max(reynolds)),
        "pressure_drop_closure_residual_Pa": float(
            math.fsum(float(value) for value in pressure_drop_cells) - request.pressure_drop_Pa
        ),
        "transport_coupling_contract": {
            "field": "axial_advection_velocity_m_s",
            "provider_id": request.flow_id,
            "configuration_sha256": input_digest,
            "flow_continuity_reviewed_required": True,
        },
        "scope": "Steady mouth-to-tip flow only; caller must separately map the signed direction, boundary concentrations and time dependence.",
    }


class PlanarSlitHydraulicHistory(Contract):
    """Recompute steady slit flow at each state of a pinned aperture history."""

    flow_history_id: str = Field(min_length=1)
    aperture_history_result: dict
    aperture_history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pressure_history_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pressure_drop_Pa: tuple[float, ...] = Field(min_length=2, max_length=5000)
    fluid_property_source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dynamic_viscosity_Pa_s: Positive
    density_kg_m3: Positive
    minimum_width_to_aperture_ratio: Positive = Field(default=20.0, ge=20.0, le=1000.0)
    maximum_reviewed_reynolds_number: Positive = Field(default=1000.0, le=1000.0)
    geometry_and_boundary_pressures_reviewed: bool
    incompressible_newtonian_fluid_properties_reviewed: bool
    laminar_fully_developed_slit_assumption_reviewed: bool
    pressure_history_and_geometry_time_alignment_reviewed: bool

    @model_validator(mode="after")
    def validate_bound_history(self):
        if canonical_digest(self.aperture_history_result) != self.aperture_history_source_sha256:
            raise ValueError("aperture history digest differs from the caller-pinned value")
        values = self.aperture_history_result.get("values", self.aperture_history_result)
        states = values.get("geometry_states") if isinstance(values, dict) else None
        if not isinstance(states, list) or len(states) != len(self.pressure_drop_Pa):
            raise ValueError("pressure samples must match the complete aperture history state count")
        if len(states) < 2 or len(states) > 5000:
            raise ValueError("aperture history must contain between two and 5000 states")
        times = [row.get("elapsed_time_s") for row in states if isinstance(row, dict)]
        if (
            len(times) != len(states)
            or times[0] != 0
            or any(
                isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
                for value in times
            )
            or any(right <= left for left, right in zip(times[:-1], times[1:], strict=True))
        ):
            raise ValueError("aperture history clock must be finite, zero-based, and strictly increasing")
        cell_count = len(values.get("cell_widths_m", ())) if isinstance(values, dict) else 0
        if cell_count < 2 or cell_count * len(states) > 2_000_000:
            raise ValueError("aperture state-by-cell budget exceeded or source grid is missing")
        if any(
            not isinstance(row.get("cell_aperture_m"), list)
            or len(row["cell_aperture_m"]) != cell_count
            or any(
                isinstance(gap, bool)
                or not isinstance(gap, (int, float))
                or not math.isfinite(gap)
                or gap <= 0
                for gap in row["cell_aperture_m"]
            )
            for row in states
        ):
            raise ValueError("every aperture state must contain one finite positive gap per cell")
        result_status = self.aperture_history_result.get("status", values.get("status", "computed"))
        if result_status != "computed":
            raise ValueError("a computed aperture history is required")
        return self


def evaluate_planar_slit_hydraulic_history(request: PlanarSlitHydraulicHistory) -> dict:
    """Recalculate steady flow for each aligned aperture and pressure state.

    This supplies a sequential operator-split coupling: each output face-velocity
    row can drive one transport solve on the corresponding fixed geometry.
    """
    digest = canonical_digest(request.model_dump(mode="json"))
    history = request.aperture_history_result
    values = history.get("values", history)
    states = values["geometry_states"]
    widths = tuple(values["cell_widths_m"])
    times = [float(row["elapsed_time_s"]) for row in states]
    base = {
        "flow_history_id": request.flow_history_id,
        "status": "needs_data",
        "input_sha256": digest,
        "aperture_history_source_sha256": request.aperture_history_source_sha256,
        "pressure_history_source_sha256": request.pressure_history_source_sha256,
        "fluid_property_source_sha256": request.fluid_property_source_sha256,
        "geometry_source_sha256": values.get("geometry_source_sha256"),
        "elapsed_time_s": times,
    }
    reviews = {
        "geometry_and_boundary_pressures_reviewed": request.geometry_and_boundary_pressures_reviewed,
        "incompressible_newtonian_fluid_properties_reviewed": request.incompressible_newtonian_fluid_properties_reviewed,
        "laminar_fully_developed_slit_assumption_reviewed": request.laminar_fully_developed_slit_assumption_reviewed,
        "pressure_history_and_geometry_time_alignment_reviewed": request.pressure_history_and_geometry_time_alignment_reviewed,
    }
    missing = [key for key, value in reviews.items() if not value]
    if missing:
        return base | {"missing_reviews": missing}
    geometry_sha = values.get("geometry_source_sha256")
    if not isinstance(geometry_sha, str) or len(geometry_sha) != 64:
        return base | {"status": "out_of_scope", "reason": "Aperture history lacks a source geometry digest"}

    snapshots = []
    for index, (state, delta_p) in enumerate(zip(states, request.pressure_drop_Pa, strict=True)):
        flow_request = PlanarSlitHydraulicFlow(
            flow_id=f"{request.flow_history_id}:{index}",
            geometry_source_sha256=geometry_sha,
            cell_widths_m=widths,
            cell_aperture_m=tuple(state["cell_aperture_m"]),
            transverse_width_m=values["transverse_width_m"],
            fluid_property_source_sha256=request.fluid_property_source_sha256,
            pressure_drop_Pa=delta_p,
            dynamic_viscosity_Pa_s=request.dynamic_viscosity_Pa_s,
            density_kg_m3=request.density_kg_m3,
            minimum_width_to_aperture_ratio=request.minimum_width_to_aperture_ratio,
            maximum_reviewed_reynolds_number=request.maximum_reviewed_reynolds_number,
            geometry_and_boundary_pressures_reviewed=True,
            incompressible_newtonian_fluid_properties_reviewed=True,
            laminar_fully_developed_slit_assumption_reviewed=True,
        )
        result = evaluate_planar_slit_hydraulic_flow(flow_request)
        snapshots.append({"elapsed_time_s": times[index], **result})
    status = "computed" if all(row["status"] == "computed" for row in snapshots) else "out_of_scope"
    return base | {
        "status": status,
        "flow_snapshots": snapshots,
        "transport_coupling_contract": {
            "velocity_field": "transport_face_velocity_m_s -> RestrictedTransportRequest.axial_advection_velocity_m_s",
            "configuration_sha256_per_snapshot": "each row input_sha256",
            "operator_split_review_required": True,
        },
        "basis": "At each declared aperture-history knot, solve a separate steady laminar slit flow using the aligned caller pressure difference. No within-interval momentum or simultaneous corrosion/flow solve is performed.",
    }
