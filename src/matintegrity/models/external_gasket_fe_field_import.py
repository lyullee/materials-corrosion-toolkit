"""Import explicit provider gasket FE contact/stress fields without running FE."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec
from ..structural_provider_acceptance import StructuralProviderResultReceipt

MODEL_ID = "integration.external_gasket_fe_field_import"


class GasketFEFieldSelection(Contract):
    field_id: str = Field(min_length=1)
    target_field_id: Literal[
        "gasket_normal_contact_pressure",
        "gasket_normal_contact_force",
        "gasket_contact_gap",
        "gasket_compression",
        "gasket_stress_tensor",
    ]
    quantity_id: str = Field(min_length=1)
    quantity_definition: str = Field(min_length=1)
    unit_token: Literal["Pa", "N", "m"]
    result_location: Literal["node", "element", "face"]
    component_ids: tuple[str, ...] = Field(min_length=1, max_length=6)

    @model_validator(mode="after")
    def semantic_units(self):
        expected = {
            "gasket_normal_contact_pressure": ("Pa", 1),
            "gasket_normal_contact_force": ("N", 1),
            "gasket_contact_gap": ("m", 1),
            "gasket_compression": ("m", 1),
            "gasket_stress_tensor": ("Pa", 6),
        }[self.target_field_id]
        if self.unit_token != expected[0] or len(self.component_ids) != expected[1]:
            raise ValueError("selected FE field unit and component count are incompatible with target semantics")
        if len(set(self.component_ids)) != len(self.component_ids):
            raise ValueError("selected FE field component IDs must be unique and ordered")
        return self


class GasketFEContactLocation(Contract):
    contact_node_id: str = Field(min_length=1)
    provider_location_id: str = Field(min_length=1)
    tributary_contact_area_m2: Positive
    circumferential_coordinate_rad: float


class GasketFENormalizedFieldArray(Contract):
    field_id: str = Field(min_length=1)
    provider_array_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_location_ids: tuple[str, ...] = Field(min_length=1, max_length=10000)
    component_ids: tuple[str, ...] = Field(min_length=1, max_length=6)
    values: tuple[tuple[float, ...], ...] = Field(min_length=1, max_length=10000)
    normalized_values_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def array_shape_and_digest(self):
        if len(self.provider_location_ids) != len(self.values):
            raise ValueError("normalized FE values must align with provider location IDs")
        if len(set(self.provider_location_ids)) != len(self.provider_location_ids):
            raise ValueError("provider location IDs must be unique and ordered")
        if any(len(row) != len(self.component_ids) for row in self.values):
            raise ValueError("each FE location row must align with its ordered components")
        if any(not math.isfinite(value) for row in self.values for value in row):
            raise ValueError("normalized FE field values must be finite")
        payload = {
            "field_id": self.field_id,
            "provider_array_content_sha256": self.provider_array_content_sha256,
            "provider_location_ids": list(self.provider_location_ids),
            "component_ids": list(self.component_ids),
            "values": [list(row) for row in self.values],
        }
        if canonical_digest(payload) != self.normalized_values_sha256:
            raise ValueError("normalized field digest must bind raw provider digest, exact mapping and values")
        return self


class GasketFESupportObservation(Contract):
    support_id: str = Field(min_length=1)
    mesh_node_id: str = Field(min_length=1)
    component_id: Literal[
        "translation_x", "translation_y", "translation_z", "rotation_x", "rotation_y", "rotation_z"
    ]
    prescribed_value: float
    prescribed_unit_token: Literal["m", "rad"]
    reaction_value: float | None = None
    reaction_unit_token: Literal["N", "N*m"] | None = None

    @model_validator(mode="after")
    def dof_units(self):
        translation = self.component_id.startswith("translation_")
        expected_value_unit = "m" if translation else "rad"
        expected_reaction_unit = "N" if translation else "N*m"
        if self.prescribed_unit_token != expected_value_unit:
            raise ValueError("support prescribed-value unit must match translational or rotational DOF")
        if self.reaction_value is None:
            if self.reaction_unit_token is not None:
                raise ValueError("reaction unit cannot be present when the reaction value is missing")
        elif self.reaction_unit_token != expected_reaction_unit:
            raise ValueError("support reaction unit must match translational or rotational DOF")
        return self


class GasketFEContactSnapshot(Contract):
    snapshot_id: str = Field(min_length=1)
    load_case_id: str = Field(min_length=1)
    step_id: str = Field(min_length=1)
    time_s: Nonnegative
    time_binding_source_id: str = Field(min_length=1)
    time_binding_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    time_binding_usage_license_id: str = Field(min_length=1)
    time_binding_evidence: tuple[Evidence, ...] = Field(min_length=1)
    provider_receipt: StructuralProviderResultReceipt
    provider_data_usage_license_id: str = Field(min_length=1)
    provider_data_usage_evidence: tuple[Evidence, ...] = Field(min_length=1)
    field_arrays: tuple[GasketFENormalizedFieldArray, ...] = Field(min_length=1, max_length=32)
    support_observations: tuple[GasketFESupportObservation, ...] = ()
    support_source_id: str | None = None
    support_record_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    support_usage_license_id: str | None = None
    support_evidence: tuple[Evidence, ...] = ()

    @model_validator(mode="after")
    def support_lineage_complete(self):
        receipt = self.provider_receipt
        if not any(row.source_id == receipt.provider_id and row.sha256 == receipt.provider_result_digest
                   and row.license_id == self.provider_data_usage_license_id
                   for row in self.provider_data_usage_evidence):
            raise ValueError("provider-use Evidence must bind the exact solver result digest and declared use license")
        has_support = bool(self.support_observations)
        if has_support != all((self.support_source_id, self.support_record_sha256, self.support_usage_license_id,
                               self.support_evidence)):
            raise ValueError("support rows and their source/digest/license/Evidence must be supplied together")
        if has_support:
            record = {
                "provider_id": self.provider_receipt.provider_id,
                "provider_revision": self.provider_receipt.provider_revision,
                "mesh_content_digest": self.provider_receipt.mesh.mesh_content_digest,
                "analysis_id": self.provider_receipt.analysis_id,
                "load_case_id": self.load_case_id,
                "step_id": self.step_id,
                "support_observations": [row.model_dump(mode="json") for row in self.support_observations],
            }
            if canonical_digest(record) != self.support_record_sha256:
                raise ValueError("support digest must bind the FE mesh, load step and explicit support observations")
            if not any(row.source_id == self.support_source_id and row.sha256 == self.support_record_sha256
                       and row.license_id == self.support_usage_license_id for row in self.support_evidence):
                raise ValueError("support Evidence must bind its source, support digest and computational-use license")
        elif any((self.support_source_id, self.support_record_sha256, self.support_usage_license_id)):
            raise ValueError("support source metadata cannot be supplied without support observations")
        return self


class ExternalGasketFEFieldImportRequest(Contract):
    schema_version: Literal["matintegrity.external_gasket_fe_field_import.v1"] = (
        "matintegrity.external_gasket_fe_field_import.v1"
    )
    assessment_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    provider_component_id: str = Field(min_length=1)
    run_context: RunContext
    node_ids: tuple[str, ...] = Field(min_length=2, max_length=10000)
    gasket_contact_area_m2: tuple[Positive, ...] = Field(min_length=2, max_length=10000)
    contact_locations: tuple[GasketFEContactLocation, ...] = Field(min_length=2, max_length=10000)
    field_selections: tuple[GasketFEFieldSelection, ...] = Field(min_length=1, max_length=32)
    snapshots: tuple[GasketFEContactSnapshot, ...] = Field(min_length=1, max_length=1000)
    geometry_source_id: str = Field(min_length=1)
    geometry_provider_revision: str = Field(min_length=1)
    geometry_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    geometry_usage_license_id: str = Field(min_length=1)
    geometry_evidence: tuple[Evidence, ...] = Field(min_length=1)
    coordinate_and_contact_area_mapping_reviewed: bool
    exact_solver_step_to_time_mapping_reviewed: bool
    field_quantity_frame_and_unit_mapping_reviewed: bool
    provider_field_array_normalization_reviewed: bool
    pressure_area_to_nodal_force_projection_reviewed: bool
    contact_field_semantics_and_sign_reviewed: bool
    support_condition_mapping_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_receipts_and_maps(self):
        location_ids = [row.contact_node_id for row in self.contact_locations]
        provider_ids = [row.provider_location_id for row in self.contact_locations]
        if tuple(location_ids) != self.node_ids or tuple(row.tributary_contact_area_m2 for row in self.contact_locations) != self.gasket_contact_area_m2:
            raise ValueError("node_ids and gasket_contact_area_m2 must exactly mirror the ordered contact-location map")
        if len(set(location_ids)) != len(location_ids) or len(set(provider_ids)) != len(provider_ids):
            raise ValueError("contact location IDs and provider location IDs must each be unique")
        geometry_record = {
            "joint_id": self.joint_id,
            "physical_scope_id": self.physical_scope_id,
            "provider_component_id": self.provider_component_id,
            "provider_revision": self.geometry_provider_revision,
            "contact_locations": [row.model_dump(mode="json") for row in self.contact_locations],
        }
        if canonical_digest(geometry_record) != self.geometry_record_sha256:
            raise ValueError("geometry digest must bind joint scope, provider revision and ordered contact mapping")
        if not any(row.source_id == self.geometry_source_id and row.sha256 == self.geometry_record_sha256
                   and row.license_id == self.geometry_usage_license_id for row in self.geometry_evidence):
            raise ValueError("geometry Evidence must bind the explicit location/area mapping and its license")
        targets = [row.target_field_id for row in self.field_selections]
        if len(targets) != len(set(targets)):
            raise ValueError("each target field semantic can be mapped only once")
        if len({row.result_location for row in self.field_selections}) > 1:
            raise ValueError("all selected fields must use one common direct result-location basis")
        if not ("gasket_normal_contact_pressure" in targets or "gasket_normal_contact_force" in targets):
            raise ValueError("at least one explicit normal contact pressure or force field is required")
        if len({row.snapshot_id for row in self.snapshots}) != len(self.snapshots):
            raise ValueError("snapshot IDs must be unique")
        if len({row.step_id for row in self.snapshots}) != len(self.snapshots):
            raise ValueError("solver step IDs must be unique in this imported history")
        if any(right.time_s <= left.time_s for left, right in zip(self.snapshots[:-1], self.snapshots[1:], strict=True)):
            if len(self.snapshots) > 1:
                raise ValueError("snapshot times must strictly increase in the declared order")
        first = self.snapshots[0].provider_receipt
        stable_fields = ("provider_id", "provider_revision", "model_id", "model_revision", "asset_id",
                         "component_id", "location_id", "physical_scope_id")
        stable_receipt = tuple(getattr(first, name) for name in stable_fields)
        if (first.asset_id, first.location_id) != (self.run_context.asset_id, self.run_context.location_id):
            raise ValueError("run context asset and location must match the FE provider receipt")
        if first.component_id != self.provider_component_id or first.physical_scope_id != self.physical_scope_id:
            raise ValueError("provider component and physical scope must exactly match the FE receipt")
        for snapshot in self.snapshots:
            receipt = snapshot.provider_receipt
            if receipt.analysis_kind != "finite_element":
                raise ValueError("only finite-element provider receipts may be imported")
            if tuple(getattr(receipt, name) for name in stable_fields) != stable_receipt:
                raise ValueError("all history snapshots must retain provider/model revision and physical asset scope")
            if receipt.mesh.mesh_content_digest != first.mesh.mesh_content_digest:
                raise ValueError("all imported snapshots must share the same exact provider mesh digest")
            if snapshot.load_case_id not in receipt.load_case_ids:
                raise ValueError("snapshot load case is absent from provider receipt")
            time_record = {
                "provider_id": receipt.provider_id,
                "provider_revision": receipt.provider_revision,
                "analysis_id": receipt.analysis_id,
                "load_case_id": snapshot.load_case_id,
                "step_id": snapshot.step_id,
                "time_s": snapshot.time_s,
            }
            if canonical_digest(time_record) != snapshot.time_binding_record_sha256:
                raise ValueError("time-binding digest must pin provider analysis, load case, step and exact time")
            if not any(row.source_id == snapshot.time_binding_source_id
                       and row.sha256 == snapshot.time_binding_record_sha256
                       and row.license_id == snapshot.time_binding_usage_license_id
                       for row in snapshot.time_binding_evidence):
                raise ValueError("time-binding Evidence must pin the exact solver step/time assignment and license")
            arrays = {row.field_id: row for row in snapshot.field_arrays}
            if len(arrays) != len(snapshot.field_arrays):
                raise ValueError("field array IDs must be unique within each snapshot")
            if set(arrays) != {row.field_id for row in self.field_selections}:
                raise ValueError("each snapshot must provide exactly the selected result fields")
            for selection in self.field_selections:
                matches = [row for row in receipt.result_fields if row.field_id == selection.field_id
                           and row.load_case_id == snapshot.load_case_id and row.step_id == snapshot.step_id]
                if len(matches) != 1:
                    raise ValueError("each selected field must resolve exactly once for its load case and solver step")
                field = matches[0]
                data = arrays[selection.field_id]
                if (field.quantity_id != selection.quantity_id
                        or field.quantity_definition != selection.quantity_definition
                        or field.unit_token != selection.unit_token
                        or field.result_location != selection.result_location
                        or field.component_ids != selection.component_ids
                        or field.coordinate_frame_id != receipt.mesh.coordinate_frame_id):
                    raise ValueError("selected FE field quantity, definition, unit, location, components or frame mismatch")
                if field.array_content_digest != data.provider_array_content_sha256:
                    raise ValueError("normalized field does not pin the provider array content digest")
                if data.provider_location_ids != tuple(provider_ids) or data.component_ids != selection.component_ids:
                    raise ValueError("field values must align exactly with the declared contact map and component order")
                expected_shape = (len(provider_ids),) if len(selection.component_ids) == 1 else (
                    len(provider_ids), len(selection.component_ids)
                )
                if field.array_shape not in (expected_shape, (len(provider_ids), len(selection.component_ids))):
                    raise ValueError("provider receipt field array shape does not match the mapped result data")
                if selection.target_field_id in (
                    "gasket_normal_contact_pressure", "gasket_normal_contact_force", "gasket_contact_gap",
                    "gasket_compression",
                ) and any(value < 0 for row in data.values for value in row):
                    raise ValueError("compression-only contact pressure/force/gap/compression fields must be nonnegative")
        return self


def evaluate_external_gasket_fe_field_import(request: ExternalGasketFEFieldImportRequest) -> Calculation:
    """Normalize and lineage-bind explicit FE fields; calculate no structural response."""
    input_digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "joint_id": request.joint_id,
        "physical_scope_id": request.physical_scope_id,
        "provider_component_id": request.provider_component_id,
        "model_id": MODEL_ID,
        "input_sha256": input_digest,
        "provider_id": request.snapshots[0].provider_receipt.provider_id,
        "provider_revision": request.snapshots[0].provider_receipt.provider_revision,
        "mesh_id": request.snapshots[0].provider_receipt.mesh.mesh_id,
        "mesh_revision": request.snapshots[0].provider_receipt.mesh.mesh_revision,
        "mesh_content_digest": request.snapshots[0].provider_receipt.mesh.mesh_content_digest,
    }
    reviews = {
        "coordinate_and_contact_area_mapping_reviewed": request.coordinate_and_contact_area_mapping_reviewed,
        "exact_solver_step_to_time_mapping_reviewed": request.exact_solver_step_to_time_mapping_reviewed,
        "field_quantity_frame_and_unit_mapping_reviewed": request.field_quantity_frame_and_unit_mapping_reviewed,
        "provider_field_array_normalization_reviewed": request.provider_field_array_normalization_reviewed,
        "pressure_area_to_nodal_force_projection_reviewed": request.pressure_area_to_nodal_force_projection_reviewed,
        "contact_field_semantics_and_sign_reviewed": request.contact_field_semantics_and_sign_reviewed,
        "support_condition_mapping_reviewed": request.support_condition_mapping_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    selections = {row.target_field_id: row for row in request.field_selections}
    history = []
    for snapshot in request.snapshots:
        arrays = {row.field_id: row for row in snapshot.field_arrays}
        field_values = {}
        field_lineage = {}
        for selection in request.field_selections:
            array = arrays[selection.field_id]
            field_values[selection.target_field_id] = [list(row) for row in array.values]
            field_lineage[selection.target_field_id] = {
                "field_id": selection.field_id,
                "quantity_id": selection.quantity_id,
                "quantity_definition": selection.quantity_definition,
                "unit_token": selection.unit_token,
                "result_location": selection.result_location,
                "coordinate_frame_id": snapshot.provider_receipt.mesh.coordinate_frame_id,
                "averaging_basis": next(row.averaging_basis for row in snapshot.provider_receipt.result_fields
                    if row.field_id == selection.field_id and row.load_case_id == snapshot.load_case_id
                    and row.step_id == snapshot.step_id),
                "region_id": next(row.region_id for row in snapshot.provider_receipt.result_fields
                    if row.field_id == selection.field_id and row.load_case_id == snapshot.load_case_id
                    and row.step_id == snapshot.step_id),
                "provider_array_content_sha256": array.provider_array_content_sha256,
                "normalized_values_sha256": array.normalized_values_sha256,
                "provider_record_digest": next(row.result_record_digest for row in snapshot.provider_receipt.result_fields
                    if row.field_id == selection.field_id and row.load_case_id == snapshot.load_case_id
                    and row.step_id == snapshot.step_id),
            }
        response_field = []
        pressure_map = field_values.get("gasket_normal_contact_pressure")
        force_map = field_values.get("gasket_normal_contact_force")
        gap_map = field_values.get("gasket_contact_gap")
        compression_map = field_values.get("gasket_compression")
        for index, location in enumerate(request.contact_locations):
            pressure = None if pressure_map is None else pressure_map[index][0]
            if force_map is None:
                if pressure is None:
                    return Calculation(status="needs_data", values=base | {
                        "reason": "no_contact_pressure_or_force_field_selected",
                    })
                force = pressure * location.tributary_contact_area_m2
                force_basis = "caller_supplied_tributary_area_times_provider_pressure_field"
            else:
                force = force_map[index][0]
                force_basis = "provider_normal_contact_force_field"
            if not math.isfinite(force):
                return Calculation(status="out_of_scope", values=base | {
                    "reason": "pressure_area_force_projection_nonfinite",
                    "snapshot_id": snapshot.snapshot_id,
                    "contact_node_id": location.contact_node_id,
                })
            row = {
                "node_id": location.contact_node_id,
                "provider_location_id": location.provider_location_id,
                "circumferential_coordinate_rad": location.circumferential_coordinate_rad,
                "contact_state": "closed" if force > 0.0 else "open",
                "contact_force_N": force,
                "mean_contact_pressure_Pa": pressure if pressure is not None else force / location.tributary_contact_area_m2,
                "contact_area_m2": location.tributary_contact_area_m2,
                "contact_force_mapping_basis": force_basis,
            }
            if gap_map is not None:
                row["contact_gap_m"] = gap_map[index][0]
            if compression_map is not None:
                row["gasket_compression_m"] = compression_map[index][0]
            if "gasket_stress_tensor" in field_values:
                row["gasket_stress_components_Pa"] = {
                    component: value for component, value in zip(
                        selections["gasket_stress_tensor"].component_ids,
                        field_values["gasket_stress_tensor"][index], strict=True
                    )
                }
            response_field.append(row)
        history.append({
            "snapshot_id": snapshot.snapshot_id,
            "load_case_id": snapshot.load_case_id,
            "step_id": snapshot.step_id,
            "time_s": snapshot.time_s,
            "time_binding_record_sha256": snapshot.time_binding_record_sha256,
            "provider_receipt_sha256": snapshot.provider_receipt.payload_digest,
            "field_lineage": field_lineage,
            "response_field": response_field,
            "support_record_sha256": snapshot.support_record_sha256,
            "support_observations": [row.model_dump(mode="json") for row in snapshot.support_observations],
        })
    values = base | {
        "context": request.run_context.model_dump(mode="json"),
        "provider_model_id": request.snapshots[0].provider_receipt.model_id,
        "provider_model_revision": request.snapshots[0].provider_receipt.model_revision,
        "provider_analysis_ids": [row.provider_receipt.analysis_id for row in request.snapshots],
        "contact_node_ids": [row.contact_node_id for row in request.contact_locations],
        "gasket_contact_area_m2": [row.tributary_contact_area_m2 for row in request.contact_locations],
        "circumferential_coordinate_rad": [row.circumferential_coordinate_rad for row in request.contact_locations],
        "field_selection_by_target": {
            key: value.model_dump(mode="json") | {
                "coordinate_frame_id": request.snapshots[0].provider_receipt.mesh.coordinate_frame_id,
                "averaging_basis": next(row.averaging_basis for row in request.snapshots[0].provider_receipt.result_fields
                    if row.field_id == value.field_id and row.load_case_id == request.snapshots[0].load_case_id
                    and row.step_id == request.snapshots[0].step_id),
            }
            for key, value in selections.items()
        },
        "geometry_record_sha256": request.geometry_record_sha256,
        "history": history,
        "pressure_to_force_projection": "pressure_times_caller_tributary_contact_area" if "gasket_normal_contact_force" not in selections else "provider_force_field",
        "limitations": [
            "This bridge imports normalized FE result fields and caller support observations; it does not execute or reproduce the structural solver.",
            "Only exact one-to-one declared result-location mappings are accepted; no spatial interpolation, averaging or coordinate-based remapping is performed.",
            "When provider contact force is absent, pressure times caller tributary area is a declared lumped projection, not an FE integration of the pressure field.",
            "Stress tensor components are preserved in their declared order; no equivalent stress, code stress, local stress acceptance, seal criterion or qualification is inferred.",
            "Time histories contain only exact caller-bound solver steps; no temporal interpolation or hidden transition search is performed.",
        ],
    }
    if len(history) == 1:
        values["response_field"] = history[0]["response_field"]
    else:
        values["steps"] = history
    return Calculation(status="computed", values=values)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        ExternalGasketFEFieldImportRequest,
        evaluate_external_gasket_fe_field_import,
        {
            "history[].time_s": "s",
            "history[].response_field[].contact_force_N": "N",
            "history[].response_field[].mean_contact_pressure_Pa": "Pa",
            "history[].response_field[].contact_area_m2": "m^2",
            "history[].response_field[].contact_gap_m": "m",
            "history[].response_field[].gasket_compression_m": "m",
            "history[].response_field[].gasket_stress_components_Pa": "Pa",
        },
        (
            "The adapter validates caller-supplied field metadata, array digests, direct location mapping, support data and exact solver-step time bindings against a structural provider receipt.",
            "It preserves only selected pressure, force, gap, compression and stress-tensor fields; it does not solve FE equations, interpolate fields or infer acceptance criteria.",
            "Pressure-to-force multiplication is used only when the caller supplies tributary area and reviews that lumped projection basis.",
        ),
        (
            "caller_finite_element_gasket_field_receipt_and_normalized_arrays",
            "caller_mesh_contact_location_area_and_coordinate_mapping",
            "caller_solver_step_time_and_support_boundary_records",
        ),
        qualification="data_import",
    )]
