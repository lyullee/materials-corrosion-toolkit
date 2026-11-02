"""Potential reconstruction on the same fixed finite-volume transport geometry."""

import numpy as np

from .restricted_transport import RestrictedTransportRequest


def reconstruct_transport_potential(
    request: RestrictedTransportRequest,
    concentrations: np.ndarray,
    *,
    cell_cross_section_m2: np.ndarray | None = None,
    face_cross_section_m2: np.ndarray | None = None,
):
    values = np.asarray(concentrations, dtype=float)
    if values.shape != (len(request.species_ids), request.cell_count) or not np.isfinite(values).all():
        raise ValueError("potential reconstruction requires finite species-by-cell concentrations")
    if request.prescribed_potential_V is not None:
        if not request.prescribed_field_migration_reviewed:
            raise ValueError("prescribed potential requires its basis review")
        return np.asarray(request.prescribed_potential_V[1:], dtype=float)
    if request.poisson_permittivity_F_m is None:
        return None
    if not request.poisson_boundary_and_charge_reviewed:
        raise ValueError("Poisson potential requires boundary/charge review")
    from scipy.linalg import solve_banded

    count = request.cell_count
    widths = np.asarray(
        request.cell_widths_m if request.cell_widths_m is not None else (request.length_m / count,) * count
    )
    distances = np.concatenate(([widths[0] * 0.5], (widths[:-1] + widths[1:]) * 0.5))
    cell_area = cell_cross_section_m2 if cell_cross_section_m2 is not None else request.cell_cross_section_m2
    face_area = face_cross_section_m2 if face_cross_section_m2 is not None else request.face_cross_section_m2
    cells = (
        np.asarray(cell_area) / request.reference_cross_section_m2
        if cell_area is not None
        else np.ones(count)
    )
    faces = (
        np.asarray(face_area) / request.reference_cross_section_m2
        if face_area is not None
        else np.ones(count + 1)
    )
    conductance = faces[:-1] / distances
    band = np.zeros((3, count))
    band[0, 1:] = -conductance[1:]
    band[2, :-1] = -conductance[1:]
    band[1, :] = conductance
    band[1, :-1] += conductance[1:]
    charge = np.asarray(request.charge_numbers) @ values
    if request.fixed_charge_mol_charge_m3 is not None:
        charge += np.asarray(request.fixed_charge_mol_charge_m3)
    rhs = 96485.33212 * charge * cells * widths / request.poisson_permittivity_F_m
    rhs[0] += conductance[0] * request.poisson_mouth_potential_V
    if not np.isfinite(band).all() or not np.isfinite(rhs).all():
        raise ValueError("potential operator exceeds numeric range")
    result = solve_banded((1, 1), band, rhs)
    if not np.isfinite(result).all():
        raise ValueError("potential reconstruction is nonfinite")
    return result
