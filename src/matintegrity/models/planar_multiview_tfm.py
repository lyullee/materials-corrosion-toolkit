"""FMC views using Fermat transmission at a plane and optional same-mode backwall reflection."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Nonnegative, Positive
from ..registry import ModelSpec
from .engineering_correlations import SOURCE_ID
from .fmc_tfm import HomogeneousFmcTfm, _fmc_from_times, _fmc_lineage


class PlanarTfmView(Contract):
    view_id: str = Field(min_length=1)
    transmit_material_mode: Literal["longitudinal", "shear"]
    receive_material_mode: Literal["longitudinal", "shear"]
    transmit_backwall_reflection: bool
    receive_backwall_reflection: bool


class PlanarMultiviewFmcTfm(HomogeneousFmcTfm):
    propagation_model: Literal["planar_two_medium_transmission_and_same_mode_backwall"]
    couplant_condition_id: str = Field(min_length=1)
    couplant_velocity_basis_id: str = Field(min_length=1)
    interface_geometry_basis_id: str = Field(min_length=1)
    interface_z_m: float
    couplant_longitudinal_velocity_m_s: Positive
    material_shear_velocity_m_s: Positive | None = None
    material_shear_velocity_basis_id: str | None = Field(default=None, min_length=1)
    backwall_z_m: float | None = None
    views: tuple[PlanarTfmView, ...] = Field(min_length=1, max_length=32)
    ray_fraction_tolerance: Positive = Field(default=1e-10, le=0.01)
    maximum_normalized_snell_residual: Nonnegative = 1e-8
    maximum_ray_iterations: int = Field(default=80, ge=1, le=256)

    @model_validator(mode="after")
    def supported_half_spaces(self):
        if any(row.position_m[2] >= self.interface_z_m for row in self.elements):
            raise ValueError("elements must lie strictly above the z-normal planar interface")
        if any(row.position_m[2] <= self.interface_z_m for row in self.image_points):
            raise ValueError("image points must lie strictly inside the lower material half-space")
        if len({view.view_id for view in self.views}) != len(self.views):
            raise ValueError("TFM view IDs must be unique")
        shear = any(
            "shear" in (view.transmit_material_mode, view.receive_material_mode) for view in self.views
        )
        if shear and (
            self.material_shear_velocity_m_s is None or self.material_shear_velocity_basis_id is None
        ):
            raise ValueError("shear views require explicit shear velocity and basis")
        if (
            self.material_shear_velocity_m_s is not None
            and self.material_shear_velocity_m_s >= self.longitudinal_velocity_m_s
        ):
            raise ValueError("isotropic material shear velocity must be below its longitudinal velocity")
        reflected = any(
            view.transmit_backwall_reflection or view.receive_backwall_reflection for view in self.views
        )
        if reflected and self.backwall_z_m is None:
            raise ValueError("reflected views require a declared parallel planar backwall")
        if self.backwall_z_m is not None and any(
            row.position_m[2] >= self.backwall_z_m for row in self.image_points
        ):
            raise ValueError("image points must lie strictly above the declared backwall")
        return self


def _plane_transmitted_ray(
    element,
    point,
    *,
    interface_z,
    couplant_speed,
    material_speed,
    reflected_backwall_z,
    fraction_tolerance,
    residual_tolerance,
    maximum_iterations,
):
    dx, dy = point[0] - element[0], point[1] - element[1]
    rho = math.hypot(dx, dy)
    h1 = interface_z - element[2]
    h2 = (
        point[2] - interface_z
        if reflected_backwall_z is None
        else (reflected_backwall_z - interface_z) + (reflected_backwall_z - point[2])
    )
    if not all(math.isfinite(value) for value in (rho, h1, h2)) or min(h1, h2) <= 0:
        raise ArithmeticError("ray geometry exceeds numeric support")
    scale = max(couplant_speed, material_speed)
    c1, c2 = couplant_speed / scale, material_speed / scale
    if min(c1, c2) <= 0:
        raise ArithmeticError("relative wave speeds exceed numeric support")
    lo, hi = 0.0, 1.0
    iterations = 0
    if rho == 0.0:
        fraction = 0.0
        residual = 0.0
        width = 0.0
    else:
        for _ in range(maximum_iterations):
            iterations += 1
            middle = lo + (hi - lo) / 2.0
            a, b = middle * rho, (1 - middle) * rho
            derivative = c2 * (a / math.hypot(h1, a)) - c1 * (b / math.hypot(h2, b))
            if derivative > 0.0:
                hi = middle
            elif derivative < 0.0:
                lo = middle
            else:
                lo = hi = middle
            if hi - lo <= fraction_tolerance:
                break
        else:
            raise ArithmeticError("ray bisection iteration budget exhausted")
        fraction = lo + (hi - lo) / 2.0
        a, b = fraction * rho, (1 - fraction) * rho
        residual = c2 * (a / math.hypot(h1, a)) - c1 * (b / math.hypot(h2, b))
        width = hi - lo
    a, b = fraction * rho, (1 - fraction) * rho
    travel = math.hypot(h1, a) / couplant_speed + math.hypot(h2, b) / material_speed
    if not math.isfinite(travel) or travel <= 0.0 or abs(residual) > residual_tolerance:
        raise ArithmeticError("ray time or normalized Snell residual is unsupported")
    interface_point = (element[0] + fraction * dx, element[1] + fraction * dy, interface_z)
    if not all(math.isfinite(value) for value in interface_point):
        raise ArithmeticError("interface intersection exceeds numeric support")
    return dict(
        travel_time_s=travel,
        interface_position_m=interface_point,
        normalized_snell_residual=residual,
        fraction_bracket_width=width,
        iterations=iterations,
    )


def _planar_multiview_from_reader(x, *, sample_reader=None, image_points=None) -> Calculation:
    import numpy as np

    base = dict(
        acquisition_id=x.acquisition_id,
        physical_specimen_id=x.physical_specimen_id,
        physical_scope_id=x.physical_scope_id,
        source_group_id=x.source_group_id,
        record_sha256=x.basis.record_sha256,
        interface_geometry_basis_id=x.interface_geometry_basis_id,
        couplant_condition_id=x.couplant_condition_id,
        couplant_velocity_basis_id=x.couplant_velocity_basis_id,
        material_shear_velocity_basis_id=x.material_shear_velocity_basis_id,
    )
    base = _fmc_lineage(x) | base
    points = x.image_points if image_points is None else image_points
    total = len(x.views) * len(points) * len(x.traces)
    if total > x.maximum_point_trace_evaluations:
        return Calculation(
            status="out_of_scope", values=base, notes=("The total multiview point/trace budget is exceeded.",)
        )
    requested = {(view.transmit_material_mode, view.transmit_backwall_reflection) for view in x.views} | {
        (view.receive_material_mode, view.receive_backwall_reflection) for view in x.views
    }
    lookups = {}
    summaries = []
    for mode, reflected in sorted(requested):
        speed = x.longitudinal_velocity_m_s if mode == "longitudinal" else x.material_shear_velocity_m_s
        matrix = np.empty((len(points), len(x.elements)))
        max_residual, max_width, max_iterations = 0.0, 0.0, 0
        for pi, point in enumerate(points):
            for ei, element in enumerate(x.elements):
                try:
                    ray = _plane_transmitted_ray(
                        element.position_m,
                        point.position_m,
                        interface_z=x.interface_z_m,
                        couplant_speed=x.couplant_longitudinal_velocity_m_s,
                        material_speed=speed,
                        reflected_backwall_z=x.backwall_z_m if reflected else None,
                        fraction_tolerance=x.ray_fraction_tolerance,
                        residual_tolerance=x.maximum_normalized_snell_residual,
                        maximum_iterations=x.maximum_ray_iterations,
                    )
                except ArithmeticError as exc:
                    return Calculation(
                        status="out_of_scope",
                        values=base
                        | {
                            "unsupported_point_id": point.point_id,
                            "unsupported_element_id": element.element_id,
                            "unsupported_mode": mode,
                            "unsupported_reflection": reflected,
                        },
                        notes=(str(exc),),
                    )
                matrix[pi, ei] = ray["travel_time_s"]
                max_residual = max(max_residual, abs(ray["normalized_snell_residual"]))
                max_width = max(max_width, ray["fraction_bracket_width"])
                max_iterations = max(max_iterations, ray["iterations"])
        lookups[mode, reflected] = matrix
        summaries.append(
            dict(
                material_mode=mode,
                backwall_reflection=reflected,
                maximum_normalized_snell_residual=max_residual,
                maximum_fraction_bracket_width=max_width,
                maximum_iterations_used=max_iterations,
                minimum_one_way_time_s=float(np.min(matrix)),
                maximum_one_way_time_s=float(np.max(matrix)),
            )
        )
    output = []
    common = None
    for view in x.views:
        result = _fmc_from_times(
            x,
            lookups[view.transmit_material_mode, view.transmit_backwall_reflection],
            lookups[view.receive_material_mode, view.receive_backwall_reflection],
            path_notes=(),
            sample_reader=sample_reader,
            image_points=points,
        )
        if result.status != "computed":
            values = dict(result.values)
            values.pop("image", None)
            return Calculation(
                status=result.status,
                values=values | base | {"unsupported_view_id": view.view_id},
                notes=result.notes,
            )
        common = {
            key: value
            for key, value in result.values.items()
            if key not in ("image", "point_trace_evaluations")
        }
        output.append(
            dict(
                view_id=view.view_id,
                transmit_material_mode=view.transmit_material_mode,
                receive_material_mode=view.receive_material_mode,
                transmit_backwall_reflection=view.transmit_backwall_reflection,
                receive_backwall_reflection=view.receive_backwall_reflection,
                image=result.values["image"],
            )
        )
    return Calculation(
        values=common
        | base
        | {"views": output, "ray_summaries": summaries, "point_trace_evaluations": total},
        notes=(
            "Fermat/Snell transmission at an infinite z-normal planar interface; same-mode optional reflection uses an image point across a parallel planar backwall.",
            "Each material leg has a declared longitudinal or shear mode. These are geometric delay views, not transmission/reflection amplitude or polarization predictions.",
            "No curved interfaces, repeated bounces, mode conversion at the backwall, anisotropy, attenuation, directivity, flaw detection/sizing, POD or examination qualification is inferred.",
        ),
    )


def planar_multiview_fmc_tfm(x: PlanarMultiviewFmcTfm) -> Calculation:
    if x.propagation_model != "planar_two_medium_transmission_and_same_mode_backwall":
        return Calculation(
            status="out_of_scope",
            values=_fmc_lineage(x),
            notes=("The in-memory planar evaluator does not accept another propagation/storage model.",),
        )
    return _planar_multiview_from_reader(x)


def specifications():
    return [
        ModelSpec(
            "inspection.planar_multiview_fmc_tfm",
            PlanarMultiviewFmcTfm,
            planar_multiview_fmc_tfm,
            {
                "views[].image[].position_m": "m",
                "views[].image[].coherent_amplitude": "caller_declared",
                "ray_summaries[].minimum_one_way_time_s": "s",
                "ray_summaries[].maximum_one_way_time_s": "s",
                "ray_summaries[].maximum_normalized_snell_residual": "1",
                "point_trace_evaluations": "1",
            },
            (
                "Elements and image points occupy opposite sides of one explicit planar interface in the reviewed common coordinate frame.",
                "Each ray is bracketed with caller fractional-position and normalized Snell residual tolerances; unsupported rays or views withhold the whole output.",
                "Optional backwall reflection keeps the selected material mode and uses a parallel infinite plane; amplitudes remain unweighted signed RF.",
            ),
            (SOURCE_ID,),
            qualification="user_model",
        )
    ]
