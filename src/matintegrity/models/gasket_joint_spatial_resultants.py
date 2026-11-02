"""Resultant-force, overturning-moment and contact-area descriptors for one gasket joint knot."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


MODEL_ID = "integration.gasket_joint_spatial_resultant_balance"
SOURCE_ID = "caller_gasket_joint_spatial_resultant_balance"
MULTI_BOLT_MODEL_ID = "fabrication.gasket_multi_bolt_sector_equilibrium"
CONTACT_MODEL_IDS = {
    "fabrication.flange_contact_field",
    "fabrication.flange_nonlinear_contact_field",
    "integration.external_gasket_fe_field_import",
}


class GasketBoltPlanarPosition(Contract):
    bolt_id: str = Field(min_length=1)
    x_from_reference_center_m: float
    y_from_reference_center_m: float


class GasketContactNodePlanarPosition(Contract):
    node_id: str = Field(min_length=1)
    x_from_reference_center_m: float
    y_from_reference_center_m: float


class GasketJointSpatialResultantBalance(Contract):
    """Reconcile compressive contact and bolt resultants without making acceptance claims."""

    schema_version: Literal["matintegrity.gasket_joint_spatial_resultant_balance.v1"] = (
        "matintegrity.gasket_joint_spatial_resultant_balance.v1"
    )
    assessment_id: str = Field(min_length=1)
    bolt_load_result: AssessmentResult
    bolt_load_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_step_id: str = Field(min_length=1)
    contact_result: AssessmentResult
    contact_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contact_evaluation_time_s: Nonnegative
    contact_time_alignment_source_id: str = Field(min_length=1)
    contact_time_alignment_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    contact_time_alignment_usage_license_id: str = Field(min_length=1)
    contact_time_alignment_evidence: tuple[Evidence, ...] = Field(min_length=1)
    bolt_positions: tuple[GasketBoltPlanarPosition, ...] = Field(min_length=2, max_length=256)
    contact_node_positions: tuple[GasketContactNodePlanarPosition, ...] = Field(min_length=2, max_length=256)
    geometry_provider_id: str = Field(min_length=1)
    geometry_provider_revision: str = Field(min_length=1)
    reference_center_id: str = Field(min_length=1)
    geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_usage_license_id: str = Field(min_length=1)
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1)
    external_moment_Mx_Nm: float
    external_moment_My_Nm: float
    external_moment_provider_id: str = Field(min_length=1)
    external_moment_provider_revision: str = Field(min_length=1)
    external_moment_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    external_moment_usage_license_id: str = Field(min_length=1)
    external_moment_evidence: tuple[Evidence, ...] = Field(min_length=1)
    force_balance_tolerance_N: Positive
    moment_balance_tolerance_Nm: Positive
    bolt_contact_scope_reviewed: bool
    exact_knot_time_alignment_reviewed: bool
    planar_coordinate_and_sign_convention_reviewed: bool
    external_moment_not_double_counted_reviewed: bool
    geometry_lineage_and_license_reviewed: bool
    external_moment_lineage_and_license_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_results_geometry_and_lineage(self):
        bolt_result = self.bolt_load_result
        contact_result = self.contact_result
        if bolt_result.model_id != MULTI_BOLT_MODEL_ID or bolt_result.status != "computed":
            raise ValueError("a computed multi-bolt joint result is required")
        if contact_result.model_id not in CONTACT_MODEL_IDS or contact_result.status != "computed":
            raise ValueError("a computed static flange contact result is required")
        if canonical_digest(bolt_result.model_dump(mode="json")) != self.bolt_load_result_sha256:
            raise ValueError("bolt-load AssessmentResult digest does not match")
        if canonical_digest(contact_result.model_dump(mode="json")) != self.contact_result_sha256:
            raise ValueError("contact AssessmentResult digest does not match")
        for result in (bolt_result, contact_result):
            if (result.context.asset_id, result.context.location_id) != (
                bolt_result.context.asset_id,
                bolt_result.context.location_id,
            ):
                raise ValueError("bolt and contact results must identify the same asset and location")
        bolt_values = bolt_result.values
        contact_values = contact_result.values
        if bolt_values.get("joint_id") != contact_result.inputs.get("joint_id"):
            raise ValueError("bolt and contact results must identify the same joint")
        if bolt_values.get("physical_scope_id") != contact_result.inputs.get("physical_scope_id"):
            raise ValueError("bolt and contact results must identify the same physical scope")
        steps = bolt_values.get("steps")
        selected = [row for row in steps if isinstance(row, dict) and row.get("step_id") == self.selected_step_id] if isinstance(steps, list) else []
        if len(selected) != 1:
            raise ValueError("the selected bolt-load knot must appear exactly once")
        if selected[0].get("time_s") != self.contact_evaluation_time_s:
            raise ValueError("contact field and bolt result must use the exact same selected time knot")
        time_binding = {
            "contact_result_sha256": self.contact_result_sha256,
            "bolt_load_result_sha256": self.bolt_load_result_sha256,
            "joint_id": bolt_values.get("joint_id"),
            "physical_scope_id": bolt_values.get("physical_scope_id"),
            "selected_step_id": self.selected_step_id,
            "contact_evaluation_time_s": self.contact_evaluation_time_s,
        }
        if canonical_digest(time_binding) != self.contact_time_alignment_record_sha256:
            raise ValueError("contact-time alignment digest does not bind both results and the selected knot")
        if not any(
            row.source_id == self.contact_time_alignment_source_id
            and row.sha256 == self.contact_time_alignment_record_sha256
            and row.license_id == self.contact_time_alignment_usage_license_id
            for row in self.contact_time_alignment_evidence
        ):
            raise ValueError("contact-time alignment Evidence must pin the result/time binding and license")
        rows = selected[0].get("bolts")
        if not isinstance(rows, list):
            raise ValueError("selected bolt knot must contain per-bolt force rows")
        bolt_ids = [row.get("bolt_id") for row in rows if isinstance(row, dict)]
        if len(bolt_ids) != len(rows) or len(set(bolt_ids)) != len(bolt_ids):
            raise ValueError("selected bolt rows must have unique IDs")
        if set(bolt_ids) != {position.bolt_id for position in self.bolt_positions}:
            raise ValueError("bolt position geometry must cover the selected result bolts exactly")
        if len({position.bolt_id for position in self.bolt_positions}) != len(self.bolt_positions):
            raise ValueError("bolt position IDs must be unique")

        contact_input = contact_result.inputs
        if contact_result.model_id == "integration.external_gasket_fe_field_import":
            snapshots = contact_input.get("snapshots")
            if (
                not isinstance(snapshots, list)
                or len(snapshots) != 1
                or not isinstance(snapshots[0], dict)
                or snapshots[0].get("time_s") != self.contact_evaluation_time_s
            ):
                raise ValueError("imported FE contact snapshot must be the single exact selected time knot")
        contact_node_ids = contact_input.get("node_ids")
        contact_areas = contact_input.get("gasket_contact_area_m2")
        field = contact_values.get("response_field")
        if not isinstance(contact_node_ids, list) or not isinstance(contact_areas, list) or not isinstance(field, list):
            raise ValueError("contact result must contain its ordered request nodes, areas and static response field")
        if contact_node_ids != [position.node_id for position in self.contact_node_positions]:
            raise ValueError("contact-node coordinates must align exactly with upstream node order")
        if len(contact_areas) != len(contact_node_ids) or len(field) != len(contact_node_ids):
            raise ValueError("contact node IDs, areas, geometry and output field must align")
        if len({position.node_id for position in self.contact_node_positions}) != len(self.contact_node_positions):
            raise ValueError("contact-node geometry IDs must be unique")

        geometry_record = {
            "provider_id": self.geometry_provider_id,
            "provider_revision": self.geometry_provider_revision,
            "joint_id": bolt_values.get("joint_id"),
            "physical_scope_id": bolt_values.get("physical_scope_id"),
            "reference_center_id": self.reference_center_id,
            "bolt_positions": [row.model_dump(mode="json") for row in self.bolt_positions],
            "contact_node_positions": [row.model_dump(mode="json") for row in self.contact_node_positions],
        }
        if canonical_digest(geometry_record) != self.geometry_record_sha256:
            raise ValueError("geometry digest does not match provider, reference center and ordered coordinates")
        if not any(
            row.source_id == self.geometry_provider_id
            and row.sha256 == self.geometry_record_sha256
            and row.license_id == self.geometry_usage_license_id
            for row in self.geometry_evidence
        ):
            raise ValueError("geometry Evidence must pin the declared coordinate record and license")
        moment_record = {
            "provider_id": self.external_moment_provider_id,
            "provider_revision": self.external_moment_provider_revision,
            "joint_id": bolt_values.get("joint_id"),
            "physical_scope_id": bolt_values.get("physical_scope_id"),
            "step_id": self.selected_step_id,
            "time_s": self.contact_evaluation_time_s,
            "reference_center_id": self.reference_center_id,
            "Mx_Nm": self.external_moment_Mx_Nm,
            "My_Nm": self.external_moment_My_Nm,
        }
        if canonical_digest(moment_record) != self.external_moment_record_sha256:
            raise ValueError("external moment digest does not match provider, scope, time and signed values")
        if not any(
            row.source_id == self.external_moment_provider_id
            and row.sha256 == self.external_moment_record_sha256
            and row.license_id == self.external_moment_usage_license_id
            for row in self.external_moment_evidence
        ):
            raise ValueError("external-moment Evidence must pin the declared values and license")
        if not all(math.isfinite(value) for value in (
            self.contact_evaluation_time_s,
            self.external_moment_Mx_Nm,
            self.external_moment_My_Nm,
            *[point for row in self.bolt_positions for point in (row.x_from_reference_center_m, row.y_from_reference_center_m)],
            *[point for row in self.contact_node_positions for point in (row.x_from_reference_center_m, row.y_from_reference_center_m)],
        )):
            raise ValueError("time, geometry and moment values must be finite")
        return self


def evaluate_gasket_joint_spatial_resultant_balance(
    request: GasketJointSpatialResultantBalance,
) -> Calculation:
    """Compute force closure, planar overturning resultants and finite-node area descriptors."""
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "joint_id": request.bolt_load_result.values.get("joint_id"),
        "physical_scope_id": request.bolt_load_result.values.get("physical_scope_id"),
        "selected_step_id": request.selected_step_id,
        "selected_time_s": request.contact_evaluation_time_s,
        "bolt_load_result_sha256": request.bolt_load_result_sha256,
        "contact_result_sha256": request.contact_result_sha256,
        "contact_time_alignment_record_sha256": request.contact_time_alignment_record_sha256,
        "geometry_record_sha256": request.geometry_record_sha256,
        "external_moment_record_sha256": request.external_moment_record_sha256,
        "input_sha256": digest,
    }
    reviews = (
        request.bolt_contact_scope_reviewed,
        request.exact_knot_time_alignment_reviewed,
        request.planar_coordinate_and_sign_convention_reviewed,
        request.external_moment_not_double_counted_reviewed,
        request.geometry_lineage_and_license_reviewed,
        request.external_moment_lineage_and_license_reviewed,
        request.computational_use_authorized,
    )
    if not all(reviews):
        return Calculation(
            status="needs_data",
            values=base | {"missing_review_count": sum(not flag for flag in reviews)},
            notes=("Scope, time, sign, external-load and rights reviews are required.",),
        )

    step = next(
        row for row in request.bolt_load_result.values["steps"]
        if row["step_id"] == request.selected_step_id
    )
    bolt_forces: dict[str, float] = {}
    for row in step["bolts"]:
        value = row.get("tensile_force_N")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
            return Calculation(status="out_of_scope", values=base, notes=("Bolt axial-force result must be finite and nonnegative.",))
        bolt_forces[row["bolt_id"]] = float(value)
    bolt_positions = {row.bolt_id: row for row in request.bolt_positions}
    bolt_force_sum = math.fsum(bolt_forces.values())
    bolt_mx = math.fsum(
        bolt_positions[bolt_id].y_from_reference_center_m * force
        for bolt_id, force in bolt_forces.items()
    )
    bolt_my = -math.fsum(
        bolt_positions[bolt_id].x_from_reference_center_m * force
        for bolt_id, force in bolt_forces.items()
    )

    contact_input = request.contact_result.inputs
    areas = contact_input["gasket_contact_area_m2"]
    contact_rows = request.contact_result.values["response_field"]
    contact_positions = {row.node_id: row for row in request.contact_node_positions}
    contact_force_by_node: dict[str, float] = {}
    pressure_by_node: dict[str, float] = {}
    closed_area_values = []
    for index, row in enumerate(contact_rows):
        node_id = row["node_id"]
        force = row.get("contact_force_N")
        pressure = row.get("mean_contact_pressure_Pa")
        if (
            not isinstance(force, (int, float)) or isinstance(force, bool) or not math.isfinite(force) or force < 0
            or not isinstance(pressure, (int, float)) or isinstance(pressure, bool) or not math.isfinite(pressure) or pressure < 0
        ):
            return Calculation(status="out_of_scope", values=base | {"invalid_contact_node_id": node_id}, notes=("Contact result contains a nonfinite or tensile force/pressure.",))
        area = areas[index]
        expected_pressure = force / area
        pressure_tolerance = max(1e-8, 1e-10 * max(abs(expected_pressure), abs(float(pressure))))
        if abs(float(pressure) - expected_pressure) > pressure_tolerance:
            return Calculation(status="out_of_scope", values=base | {"invalid_contact_node_id": node_id}, notes=("Contact force, pressure and declared area do not close.",))
        contact_force_by_node[node_id] = float(force)
        pressure_by_node[node_id] = float(pressure)
        if force > 0:
            closed_area_values.append(area)
    contact_force_sum = math.fsum(contact_force_by_node.values())
    contact_mx = math.fsum(
        contact_positions[node_id].y_from_reference_center_m * force
        for node_id, force in contact_force_by_node.items()
    )
    contact_my = -math.fsum(
        contact_positions[node_id].x_from_reference_center_m * force
        for node_id, force in contact_force_by_node.items()
    )
    external_force = step.get("external_separating_force_N")
    if not isinstance(external_force, (int, float)) or isinstance(external_force, bool) or not math.isfinite(external_force):
        return Calculation(status="out_of_scope", values=base, notes=("Upstream external separating force is missing or nonfinite.",))
    force_residual = bolt_force_sum - contact_force_sum - float(external_force)
    moment_residual_x = bolt_mx - contact_mx - request.external_moment_Mx_Nm
    moment_residual_y = bolt_my - contact_my - request.external_moment_My_Nm
    total_area = math.fsum(areas)
    closed_area = math.fsum(closed_area_values)
    pressures = list(pressure_by_node.values())
    cp_x = -contact_my / contact_force_sum if contact_force_sum > 0 else None
    cp_y = contact_mx / contact_force_sum if contact_force_sum > 0 else None
    numbers = (
        bolt_force_sum, bolt_mx, bolt_my, contact_force_sum, contact_mx, contact_my,
        force_residual, moment_residual_x, moment_residual_y, total_area, closed_area,
        *(pressures),
    )
    if not all(math.isfinite(value) for value in numbers):
        return Calculation(status="out_of_scope", values=base, notes=("Resultant or area summary exceeded finite numeric range.",))
    return Calculation(
        values=base | {
            "reference_center_id": request.reference_center_id,
            "bolt_closing_force_sum_N": bolt_force_sum,
            "gasket_compressive_contact_force_sum_N": contact_force_sum,
            "external_separating_force_N": float(external_force),
            "axial_force_balance_residual_N": force_residual,
            "bolt_closing_moment_Mx_Nm": bolt_mx,
            "bolt_closing_moment_My_Nm": bolt_my,
            "gasket_contact_opening_moment_Mx_Nm": contact_mx,
            "gasket_contact_opening_moment_My_Nm": contact_my,
            "external_separating_moment_Mx_Nm": request.external_moment_Mx_Nm,
            "external_separating_moment_My_Nm": request.external_moment_My_Nm,
            "moment_balance_residual_Mx_Nm": moment_residual_x,
            "moment_balance_residual_My_Nm": moment_residual_y,
            "gasket_contact_center_of_pressure_xy_m": {"x": cp_x, "y": cp_y} if cp_x is not None else None,
            "finite_node_total_area_m2": total_area,
            "finite_node_contact_area_m2": closed_area,
            "finite_node_contact_area_fraction": closed_area / total_area,
            "maximum_nodal_mean_contact_pressure_Pa": max(pressures, default=0.0),
            "force_balance_tolerance_N": request.force_balance_tolerance_N,
            "moment_balance_tolerance_Nm": request.moment_balance_tolerance_Nm,
            "within_caller_force_balance_tolerance": abs(force_residual) <= request.force_balance_tolerance_N,
            "within_caller_moment_balance_tolerance": (
                abs(moment_residual_x) <= request.moment_balance_tolerance_Nm
                and abs(moment_residual_y) <= request.moment_balance_tolerance_Nm
            ),
            "interpretation": "deterministic force_moment_and_finite_node_area_reconciliation_only",
        },
        notes=(
            "Finite-node area fraction and pressure resultants describe only the caller-supplied contact discretization.",
            "Residual comparisons use caller-evidenced external moments and the scalar external separating force from the selected bolt-load result; tolerance flags are not a code acceptance or seal qualification.",
            "Local stress, leakage, hidden contact states, continuous-field pressure integrals and failure probability are not inferred.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            GasketJointSpatialResultantBalance,
            evaluate_gasket_joint_spatial_resultant_balance,
            {
                "selected_time_s": "s",
                "bolt_closing_force_sum_N": "N",
                "gasket_compressive_contact_force_sum_N": "N",
                "axial_force_balance_residual_N": "N",
                "bolt_closing_moment_Mx_Nm": "N*m",
                "bolt_closing_moment_My_Nm": "N*m",
                "gasket_contact_opening_moment_Mx_Nm": "N*m",
                "gasket_contact_opening_moment_My_Nm": "N*m",
                "moment_balance_residual_Mx_Nm": "N*m",
                "moment_balance_residual_My_Nm": "N*m",
                "gasket_contact_center_of_pressure_xy_m": "m",
                "finite_node_total_area_m2": "m^2",
                "finite_node_contact_area_m2": "m^2",
                "finite_node_contact_area_fraction": "1",
                "maximum_nodal_mean_contact_pressure_Pa": "Pa",
            },
            (
                "Only exact-knot per-bolt forces from one computed multi-bolt joint result are reconciled with one computed static unilateral contact field.",
                "Planar moment arms are caller-evidenced coordinates relative to one named reference center; Mx=Σ(yF), My=−Σ(xF) for declared force magnitudes.",
                "External moment values and their sign convention are caller-supplied and digest-bound; upstream scalar separating force is used exactly once.",
                "Finite-node contact-area fraction and nodal pressure resultants are descriptors of the supplied mesh/discretization, not continuous-field integrals.",
                "Residual tolerance indicators are descriptive; no seal acceptance, local stress, leakage, code compliance, life or probability is inferred.",
            ),
            (SOURCE_ID,),
            qualification="engineering_screening",
        )
    ]
