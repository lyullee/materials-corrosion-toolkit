"""Local first-order covariance propagation through gasket joint equilibrium."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..registry import ModelSpec
from .gasket_multi_bolt_sector_equilibrium import (
    GasketMultiBoltSectorEquilibrium,
    evaluate_gasket_multi_bolt_sector_equilibrium,
)

MODEL_ID = "integration.gasket_joint_equilibrium_local_covariance"


class JointLoadCovarianceCoordinate(Contract):
    """One uncertain scalar at a non-reference load step."""

    step_index: int = Field(ge=1, le=9999)
    quantity: Literal["external_separating_force_N", "bolt_free_length_change_m", "gasket_free_thickness_change_m"]
    component_index: int | None = Field(default=None, ge=0, le=255)
    finite_difference_step: Positive


class GasketJointEquilibriumLocalCovariance(Contract):
    schema_version: Literal["matintegrity.gasket_joint_equilibrium_local_covariance.v1"] = (
        "matintegrity.gasket_joint_equilibrium_local_covariance.v1"
    )
    assessment_id: str = Field(min_length=1)
    joint_request: GasketMultiBoltSectorEquilibrium
    coordinates: tuple[JointLoadCovarianceCoordinate, ...] = Field(min_length=1, max_length=32)
    input_covariance: tuple[tuple[float, ...], ...] = Field(min_length=1, max_length=32)
    covariance_source_id: str = Field(min_length=1)
    covariance_provider_revision: str = Field(min_length=1)
    covariance_record_id: str = Field(min_length=1)
    covariance_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    covariance_usage_license_id: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    covariance_coordinate_order_reviewed: bool
    local_smoothness_and_fd_step_reviewed: bool
    contact_active_set_stability_reviewed: bool
    covariance_basis_and_clock_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def validate_covariance_input(self):
        size = len(self.coordinates)
        if len(self.input_covariance) != size or any(len(row) != size for row in self.input_covariance):
            raise ValueError("input covariance must be square and match coordinate order")
        if any(not math.isfinite(value) for row in self.input_covariance for value in row):
            raise ValueError("input covariance values must be finite")
        scale = max(abs(value) for row in self.input_covariance for value in row)
        tolerance = max(1e-30, 1e-10 * scale)
        for i in range(size):
            for j in range(size):
                if abs(self.input_covariance[i][j] - self.input_covariance[j][i]) > tolerance:
                    raise ValueError("input covariance must be symmetric within scale-aware tolerance")
        if not _is_positive_semidefinite(self.input_covariance, tolerance):
            raise ValueError("input covariance must be positive semidefinite")
        ids = set()
        for coordinate in self.coordinates:
            joint = self.joint_request
            if coordinate.step_index >= len(joint.load_steps):
                raise ValueError("uncertain coordinate step index is outside load history")
            if coordinate.quantity == "external_separating_force_N":
                if coordinate.component_index is not None:
                    raise ValueError("external force coordinates do not use a component index")
            elif coordinate.quantity == "bolt_free_length_change_m":
                if coordinate.component_index is None or coordinate.component_index >= len(joint.bolts):
                    raise ValueError("bolt free-length coordinate needs a valid ordered bolt index")
            elif coordinate.quantity == "gasket_free_thickness_change_m":
                if coordinate.component_index is None or coordinate.component_index >= len(joint.gasket_sectors):
                    raise ValueError("gasket free-thickness coordinate needs a valid ordered sector index")
            key = (coordinate.step_index, coordinate.quantity, coordinate.component_index)
            if key in ids:
                raise ValueError("uncertain coordinates must be unique")
            ids.add(key)
        record = {
            "source_id": self.covariance_source_id,
            "provider_revision": self.covariance_provider_revision,
            "record_id": self.covariance_record_id,
            "coordinates": [row.model_dump(mode="json") for row in self.coordinates],
            "covariance": [list(row) for row in self.input_covariance],
        }
        if canonical_digest(record) != self.covariance_sha256:
            raise ValueError("covariance digest must bind record identity, ordered coordinates and matrix")
        if not any(
            row.source_id == self.covariance_source_id
            and row.sha256 == self.covariance_sha256
            and row.license_id == self.covariance_usage_license_id
            for row in self.evidence
        ):
            raise ValueError("Evidence must bind the covariance source, digest and computational-use license")
        return self


def _is_positive_semidefinite(matrix: tuple[tuple[float, ...], ...], tolerance: float) -> bool:
    """Check PSD by symmetric Jacobi diagonalization without mandatory NumPy."""
    a = [list(row) for row in matrix]
    n = len(a)
    for i in range(n):
        for j in range(i):
            value = 0.5 * (a[i][j] + a[j][i])
            a[i][j] = a[j][i] = value
    for _ in range(max(1, 50 * n * n)):
        p, q, largest = 0, 0, 0.0
        for i in range(n):
            for j in range(i + 1, n):
                if abs(a[i][j]) > largest:
                    p, q, largest = i, j, abs(a[i][j])
        if largest <= tolerance:
            return min(a[i][i] for i in range(n)) >= -tolerance
        angle = 0.5 * math.atan2(2.0 * a[p][q], a[q][q] - a[p][p])
        cosine, sine = math.cos(angle), math.sin(angle)
        app, aqq, apq = a[p][p], a[q][q], a[p][q]
        a[p][p] = cosine * cosine * app - 2.0 * sine * cosine * apq + sine * sine * aqq
        a[q][q] = sine * sine * app + 2.0 * sine * cosine * apq + cosine * cosine * aqq
        a[p][q] = a[q][p] = 0.0
        for k in range(n):
            if k in (p, q):
                continue
            akp, akq = a[k][p], a[k][q]
            a[k][p] = a[p][k] = cosine * akp - sine * akq
            a[k][q] = a[q][k] = sine * akp + cosine * akq
    return min(a[i][i] for i in range(n)) >= -tolerance


def _apply_coordinate(request_dump: dict, coordinate: JointLoadCovarianceCoordinate, delta: float) -> dict:
    updated = {**request_dump, "load_steps": [dict(row) for row in request_dump["load_steps"]]}
    step = updated["load_steps"][coordinate.step_index]
    if coordinate.quantity == "external_separating_force_N":
        step[coordinate.quantity] += delta
    else:
        values = list(step[coordinate.quantity])
        values[coordinate.component_index] += delta
        step[coordinate.quantity] = values
    return updated


def _output_vector(result: Calculation, bolt_count: int, sector_count: int) -> tuple[list[float], list[str]]:
    history = result.values.get("steps", [])
    vector: list[float] = []
    labels: list[str] = []
    for step in history:
        step_id = step.get("step_id", f"step_{len(labels)}")
        vector.append(float(step["opening_m"]))
        labels.append(f"{step_id}.opening_m")
        bolts = step.get("bolts", [])
        sectors = step.get("gasket_sectors", [])
        if len(bolts) != bolt_count or len(sectors) != sector_count:
            raise ValueError("underlying equilibrium result component counts do not match request")
        for row in bolts:
            vector.append(float(row["tensile_force_N"]))
            labels.append(f"{step_id}.bolt[{row['bolt_id']}].tensile_force_N")
        for row in sectors:
            vector.append(float(row["mean_contact_pressure_Pa"]))
            labels.append(f"{step_id}.sector[{row['sector_id']}].mean_contact_pressure_Pa")
    if not all(math.isfinite(value) for value in vector):
        raise ValueError("underlying equilibrium output contains nonfinite values")
    return vector, labels


def _active_signature(result: Calculation) -> tuple[tuple[bool, ...], ...]:
    return tuple(
        tuple(
            [bool(row["tension_active"]) for row in step.get("bolts", [])]
            + [bool(row["contact_active"]) for row in step.get("gasket_sectors", [])]
        )
        for step in result.values.get("steps", [])
    )


def evaluate_gasket_joint_equilibrium_local_covariance(
    request: GasketJointEquilibriumLocalCovariance,
) -> Calculation:
    """Propagate caller load covariance through local finite-difference sensitivities."""
    joint = request.joint_request
    base = {
        "assessment_id": request.assessment_id,
        "joint_id": joint.joint_id,
        "model_id": MODEL_ID,
        "input_sha256": canonical_digest(request.model_dump(mode="json")),
        "covariance_sha256": request.covariance_sha256,
    }
    reviews = {
        "covariance_coordinate_order_reviewed": request.covariance_coordinate_order_reviewed,
        "local_smoothness_and_fd_step_reviewed": request.local_smoothness_and_fd_step_reviewed,
        "contact_active_set_stability_reviewed": request.contact_active_set_stability_reviewed,
        "covariance_basis_and_clock_reviewed": request.covariance_basis_and_clock_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, value in reviews.items() if not value]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})
    nominal = evaluate_gasket_multi_bolt_sector_equilibrium(joint)
    if nominal.status != "computed":
        return Calculation(status=nominal.status, values=base | {
            "nominal_status": nominal.status,
            "nominal_result": nominal.values,
            "nominal_notes": list(nominal.notes),
        })
    try:
        y0, output_labels = _output_vector(nominal, len(joint.bolts), len(joint.gasket_sectors))
    except (KeyError, TypeError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {"reason": str(error)})
    n_inputs = len(request.coordinates)
    jacobian = [[0.0] * n_inputs for _ in y0]
    original = joint.model_dump(mode="json")
    for column, coordinate in enumerate(request.coordinates):
        try:
            plus_request = GasketMultiBoltSectorEquilibrium.model_validate(
                _apply_coordinate(original, coordinate, coordinate.finite_difference_step)
            )
            minus_request = GasketMultiBoltSectorEquilibrium.model_validate(
                _apply_coordinate(original, coordinate, -coordinate.finite_difference_step)
            )
        except Exception as error:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_difference_perturbation_invalidates_joint_contract",
                "coordinate_index": column,
                "detail": str(error),
            })
        plus = evaluate_gasket_multi_bolt_sector_equilibrium(plus_request)
        minus = evaluate_gasket_multi_bolt_sector_equilibrium(minus_request)
        if plus.status != "computed" or minus.status != "computed":
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_difference_perturbation_left_equilibrium_support",
                "coordinate_index": column,
                "plus_status": plus.status,
                "minus_status": minus.status,
                "plus_notes": list(plus.notes),
                "minus_notes": list(minus.notes),
            })
        nominal_active = _active_signature(nominal)
        if _active_signature(plus) != nominal_active or _active_signature(minus) != nominal_active:
            return Calculation(status="out_of_scope", values=base | {
                "reason": "finite_difference_stencil_crosses_contact_or_bolt_active_set",
                "coordinate_index": column,
            })
        try:
            y_plus, labels_plus = _output_vector(plus, len(joint.bolts), len(joint.gasket_sectors))
            y_minus, labels_minus = _output_vector(minus, len(joint.bolts), len(joint.gasket_sectors))
        except (KeyError, TypeError, ValueError) as error:
            return Calculation(status="out_of_scope", values=base | {"reason": str(error)})
        if labels_plus != output_labels or labels_minus != output_labels:
            return Calculation(status="out_of_scope", values=base | {"reason": "finite_difference_output_shape_changed"})
        denominator = 2.0 * coordinate.finite_difference_step
        for row in range(len(y0)):
            jacobian[row][column] = (y_plus[row] - y_minus[row]) / denominator
    covariance = request.input_covariance
    output_covariance = []
    for i in range(len(y0)):
        row = []
        for j in range(len(y0)):
            value = math.fsum(
                jacobian[i][a] * covariance[a][b] * jacobian[j][b]
                for a in range(n_inputs) for b in range(n_inputs)
            )
            if not math.isfinite(value):
                return Calculation(status="out_of_scope", values=base | {"reason": "propagated_covariance_nonfinite"})
            row.append(value)
        output_covariance.append(row)
    for i in range(len(y0)):
        for j in range(i):
            value = 0.5 * (output_covariance[i][j] + output_covariance[j][i])
            output_covariance[i][j] = output_covariance[j][i] = value
    return Calculation(status="computed", values=base | {
        "nominal_result_sha256": canonical_digest(nominal.model_dump(mode="json")),
        "nominal_output_vector": y0,
        "output_labels": output_labels,
        "input_coordinate_order": [row.model_dump(mode="json") for row in request.coordinates],
        "input_covariance": [list(row) for row in covariance],
        "sensitivity_jacobian": jacobian,
        "output_covariance": output_covariance,
        "output_standard_uncertainty": [math.sqrt(max(0.0, output_covariance[i][i])) for i in range(len(y0))],
        "propagation_method": "central_finite_difference_local_delta_method",
        "limitations": [
            "Covariance applies only to explicitly selected non-reference load and free-expansion coordinates; preload, curve, geometry, temperature and calibration uncertainty are excluded.",
            "The local delta method assumes a differentiable response in the selected neighborhood; contact active-set changes, curve knots and support boundaries can invalidate the linearization.",
            "This is not a probability-of-failure, seal acceptance, qualification or global nonlinear uncertainty bound.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketJointEquilibriumLocalCovariance,
        evaluate_gasket_joint_equilibrium_local_covariance,
        {
            "nominal_output_vector[].opening_m": "m",
            "nominal_output_vector[].tensile_force_N": "N",
            "nominal_output_vector[].mean_contact_pressure_Pa": "Pa",
            "output_standard_uncertainty[]": "varies_by_output_label",
            "output_covariance[][]": "varies_by_output_labels",
        },
        (
            "Caller-supplied covariance is propagated as J Sigma J^T using central finite differences of the existing multi-bolt sector equilibrium API.",
            "Only explicit non-reference load and free-expansion coordinates are uncertain; the nominal gasket/bolt constitutive model and active contact regime are held fixed locally.",
            "No distribution, nonlinear envelope, failure probability, seal acceptance or material qualification is inferred.",
        ),
        (
            "caller_covariance_for_ordered_joint_load_coordinates",
            "central_finite_difference_local_sensitivity_of_quasistatic_gasket_equilibrium",
            "first_order_covariance_pushforward_joint_contact_outputs",
        ),
        qualification="user_model",
    )]
