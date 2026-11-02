"""Circumferential connected-contact and open-arc descriptors for gasket joints."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec


MODEL_ID = "fabrication.gasket_circumferential_contact_continuity"
SOURCE_ID = "caller_gasket_circumferential_contact_threshold"
STATIC_MODELS = {
    "fabrication.flange_contact_field",
    "fabrication.flange_nonlinear_contact_field",
}
HISTORY_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class CircumferentialContactNode(Contract):
    node_id: str = Field(min_length=1)
    angle_rad: float


class GasketCircumferentialContactContinuity(Contract):
    """Map a computed pressure field to circular Voronoi contact/open arc measures."""

    schema_version: Literal["matintegrity.gasket_circumferential_contact_continuity.v1"] = (
        "matintegrity.gasket_circumferential_contact_continuity.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    contact_result: AssessmentResult
    contact_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    selected_time_s: Nonnegative | None = None
    contact_nodes: tuple[CircumferentialContactNode, ...] = Field(min_length=3, max_length=100000)
    geometry_provider_id: str = Field(min_length=1)
    geometry_provider_revision: str = Field(min_length=1)
    ring_radius_m: Positive
    geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_usage_license_id: str = Field(min_length=1)
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1)
    minimum_contact_pressure_Pa: Nonnegative
    criterion_provider_id: str = Field(min_length=1)
    criterion_provider_revision: str = Field(min_length=1)
    criterion_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    criterion_usage_license_id: str = Field(min_length=1)
    criterion_evidence: tuple[Evidence, ...] = Field(min_length=1)
    physical_scope_and_exact_time_reviewed: bool
    ring_geometry_and_orientation_reviewed: bool
    pressure_definition_and_threshold_applicability_reviewed: bool
    contact_field_resolution_reviewed: bool
    lineage_license_and_computational_use_reviewed: bool

    @model_validator(mode="after")
    def coherent_contact_geometry_and_evidence(self):
        result = self.contact_result
        if result.status != "computed" or result.model_id not in STATIC_MODELS | HISTORY_MODELS:
            raise ValueError("a computed supported flange contact field/history is required")
        if canonical_digest(result.model_dump(mode="json")) != self.contact_result_sha256:
            raise ValueError("contact result digest does not match")
        if result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("contact result physical scope does not match")
        if result.model_id in STATIC_MODELS and self.selected_time_s is not None:
            raise ValueError("static contact results do not accept a selected time")
        if result.model_id in HISTORY_MODELS and self.selected_time_s is None:
            raise ValueError("a contact history requires an exact selected time knot")
        if len({row.node_id for row in self.contact_nodes}) != len(self.contact_nodes):
            raise ValueError("contact geometry node IDs must be unique")
        if any(not math.isfinite(row.angle_rad) for row in self.contact_nodes):
            raise ValueError("contact node angles must be finite")
        geometry_record = {
            "provider_id": self.geometry_provider_id,
            "provider_revision": self.geometry_provider_revision,
            "physical_scope_id": self.physical_scope_id,
            "ring_radius_m": self.ring_radius_m,
            "angle_basis": "counterclockwise_radians_about_caller_defined_zero",
            "nodes": [row.model_dump(mode="json") for row in self.contact_nodes],
        }
        if canonical_digest(geometry_record) != self.geometry_record_sha256:
            raise ValueError("geometry record digest does not match declared radius and angular positions")
        if not any(
            row.source_id == self.geometry_provider_id
            and row.sha256 == self.geometry_record_sha256
            and row.license_id == self.geometry_usage_license_id
            for row in self.geometry_evidence
        ):
            raise ValueError("geometry Evidence must pin the declared node coordinates and usage license")
        criterion_record = {
            "provider_id": self.criterion_provider_id,
            "provider_revision": self.criterion_provider_revision,
            "physical_scope_id": self.physical_scope_id,
            "contact_result_sha256": self.contact_result_sha256,
            "selected_time_s": self.selected_time_s,
            "minimum_contact_pressure_Pa": self.minimum_contact_pressure_Pa,
        }
        if canonical_digest(criterion_record) != self.criterion_record_sha256:
            raise ValueError("criterion digest does not match contact field/time and pressure threshold")
        if not any(
            row.source_id == self.criterion_provider_id
            and row.sha256 == self.criterion_record_sha256
            and row.license_id == self.criterion_usage_license_id
            for row in self.criterion_evidence
        ):
            raise ValueError("criterion Evidence must pin the caller threshold and usage license")
        return self


def _selected_field(request: GasketCircumferentialContactContinuity) -> list[dict] | None:
    result = request.contact_result
    if result.model_id in STATIC_MODELS:
        field = result.values.get("response_field")
        return field if isinstance(field, list) else None
    history = result.values.get("time_history")
    if not isinstance(history, list):
        return None
    knot = next((row for row in history if isinstance(row, dict) and row.get("time_s") == request.selected_time_s), None)
    field = knot.get("response_field") if knot is not None else None
    return field if isinstance(field, list) else None


def _circular_open_runs(rows: list[dict]) -> list[dict]:
    """Return runs over sorted circular Voronoi cells, joining a run across zero angle."""
    count = len(rows)
    if all(row["open"] for row in rows):
        return [{
            "start_angle_rad": rows[0]["left_rad"],
            "end_angle_rad": rows[0]["left_rad"] + 2.0 * math.pi,
            "angular_extent_rad": 2.0 * math.pi,
            "node_ids": [row["node_id"] for row in rows],
            "wraps_zero_angle": True,
        }]
    runs = []
    for index, row in enumerate(rows):
        previous = rows[(index - 1) % count]
        if not row["open"] or previous["open"]:
            continue
        cursor = index
        node_ids = []
        extent = 0.0
        while rows[cursor]["open"]:
            node_ids.append(rows[cursor]["node_id"])
            extent += rows[cursor]["cell_width_rad"]
            cursor = (cursor + 1) % count
        start = row["left_rad"]
        runs.append({
            "start_angle_rad": start,
            "end_angle_rad": start + extent,
            "angular_extent_rad": extent,
            "node_ids": node_ids,
            "wraps_zero_angle": start + extent > 2.0 * math.pi,
        })
    return runs


def evaluate_gasket_circumferential_contact_continuity(
    request: GasketCircumferentialContactContinuity,
) -> Calculation:
    """Quantify thresholded connected open/closed arcs from caller-supplied ring geometry."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "contact_result_model_id": request.contact_result.model_id,
        "contact_result_sha256": request.contact_result_sha256,
        "selected_time_s": request.selected_time_s,
        "geometry_record_sha256": request.geometry_record_sha256,
        "criterion_record_sha256": request.criterion_record_sha256,
        "input_sha256": input_digest,
    }
    reviews = (
        request.physical_scope_and_exact_time_reviewed,
        request.ring_geometry_and_orientation_reviewed,
        request.pressure_definition_and_threshold_applicability_reviewed,
        request.contact_field_resolution_reviewed,
        request.lineage_license_and_computational_use_reviewed,
    )
    if not all(reviews):
        return Calculation(status="needs_data", values=base | {"missing_review_count": sum(not value for value in reviews)})
    expected_unit = (
        "response_field.mean_contact_pressure_Pa"
        if request.contact_result.model_id in STATIC_MODELS
        else "time_history[].response_field[].mean_contact_pressure_Pa"
    )
    if request.contact_result.units.get(expected_unit) != "Pa":
        return Calculation(status="out_of_scope", values=base, notes=("Upstream pressure unit must be explicitly Pa.",))
    field = _selected_field(request)
    if not field:
        return Calculation(status="out_of_scope", values=base, notes=("Contact response field or exact history knot is missing.",))
    geometry_by_id = {row.node_id: row for row in request.contact_nodes}
    upstream_ids = [row.get("node_id") for row in field if isinstance(row, dict)]
    if len(upstream_ids) != len(field) or len(set(upstream_ids)) != len(upstream_ids):
        return Calculation(status="out_of_scope", values=base, notes=("Contact field node records must be valid and unique.",))
    if set(upstream_ids) != set(geometry_by_id):
        return Calculation(status="out_of_scope", values=base | {
            "missing_geometry_node_ids": sorted(set(upstream_ids) - set(geometry_by_id)),
            "unused_geometry_node_ids": sorted(set(geometry_by_id) - set(upstream_ids)),
        }, notes=("Geometry must cover exactly the selected field node set.",))
    pressures = {}
    for row in field:
        pressure = row.get("mean_contact_pressure_Pa")
        if isinstance(pressure, bool) or not isinstance(pressure, (int, float)) or not math.isfinite(pressure) or pressure < 0:
            return Calculation(status="out_of_scope", values=base | {"invalid_node_id": row["node_id"]}, notes=("Contact pressures must be finite and nonnegative.",))
        pressures[row["node_id"]] = float(pressure)

    two_pi = 2.0 * math.pi
    cells = []
    for node_id, node in geometry_by_id.items():
        angle = node.angle_rad % two_pi
        cells.append({"node_id": node_id, "angle_rad": angle, "pressure_Pa": pressures[node_id]})
    cells.sort(key=lambda row: row["angle_rad"])
    angles = [row["angle_rad"] for row in cells]
    gaps = [(angles[(i + 1) % len(angles)] - angles[i]) % two_pi for i in range(len(angles))]
    if any(gap <= 0.0 for gap in gaps):
        return Calculation(status="out_of_scope", values=base, notes=("Circumferential node angles must be distinct modulo 2π.",))
    for i, row in enumerate(cells):
        previous_gap = gaps[(i - 1) % len(gaps)]
        next_gap = gaps[i]
        width = 0.5 * (previous_gap + next_gap)
        row["cell_width_rad"] = width
        row["left_rad"] = (row["angle_rad"] - 0.5 * previous_gap) % two_pi
        row["open"] = row["pressure_Pa"] < request.minimum_contact_pressure_Pa
    open_runs = _circular_open_runs(cells)
    open_angle = math.fsum(row["cell_width_rad"] for row in cells if row["open"])
    circumference = two_pi * request.ring_radius_m
    open_length = open_angle * request.ring_radius_m
    closed_length = circumference - open_length
    if not all(math.isfinite(value) for value in (open_angle, circumference, open_length, closed_length)):
        return Calculation(status="out_of_scope", values=base, notes=("Arc integration exceeded finite numeric support.",))
    for run in open_runs:
        run["arc_length_m"] = run["angular_extent_rad"] * request.ring_radius_m
    return Calculation(values=base | {
        "ring_radius_m": request.ring_radius_m,
        "circumference_m": circumference,
        "minimum_contact_pressure_Pa": request.minimum_contact_pressure_Pa,
        "node_count": len(cells),
        "contact_coverage_angle_rad": two_pi - open_angle,
        "contact_coverage_length_m": closed_length,
        "contact_coverage_fraction": closed_length / circumference,
        "open_arc_angle_rad": open_angle,
        "open_arc_length_m": open_length,
        "open_arc_fraction": open_length / circumference,
        "below_threshold_component_count": len(open_runs),
        "longest_below_threshold_arc_m": max((row["arc_length_m"] for row in open_runs), default=0.0),
        "below_threshold_arcs": open_runs,
        "node_cells": [{
            "node_id": row["node_id"],
            "angle_rad": row["angle_rad"],
            "cell_width_rad": row["cell_width_rad"],
            "mean_contact_pressure_Pa": row["pressure_Pa"],
            "open_below_caller_threshold": row["open"],
        } for row in cells],
        "interpretation": "circumferential_voronoi_cell_threshold_descriptors_only",
    }, notes=(
        "Node pressures are assigned to periodic angular Voronoi cells; open arcs are discretization-based geometric descriptors.",
        "The caller threshold does not define universal seal acceptance; this model does not infer leakage, local contact between nodes, damage, qualification or probability.",
    ))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketCircumferentialContactContinuity,
        evaluate_gasket_circumferential_contact_continuity,
        {
            "ring_radius_m": "m",
            "circumference_m": "m",
            "minimum_contact_pressure_Pa": "Pa",
            "contact_coverage_angle_rad": "rad",
            "contact_coverage_length_m": "m",
            "contact_coverage_fraction": "1",
            "open_arc_angle_rad": "rad",
            "open_arc_length_m": "m",
            "open_arc_fraction": "1",
            "longest_below_threshold_arc_m": "m",
            "below_threshold_arcs[].arc_length_m": "m",
        },
        (
            "A computed gasket contact-pressure field is classified against a caller-evidenced minimum pressure and caller-evidenced periodic ring geometry.",
            "Each node is assigned a periodic Voronoi angular cell; connected open arcs are resolved on this finite discretization and wrap-around runs are joined.",
            "Coverage and arc lengths are geometric summaries only; no leakage, seal acceptance, local between-node field, qualification or probability is inferred.",
        ),
        (SOURCE_ID, "caller_periodic_voronoi_contact_partition"),
        qualification="engineering_screening",
    )]
