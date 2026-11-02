"""Bind an external FE tangent stiffness receipt to the flange compliance reducer."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec
from ..structural_provider_acceptance import StructuralProviderResultReceipt
from .flange_compliance_reduction import (
    FlangeComplianceReductionHistoryRequest,
    FlangeComplianceReductionRequest,
    reduce_flange_contact_compliance,
    reduce_flange_contact_compliance_history,
)


class ExternalFlangeComplianceBinding(Contract):
    """Solver-neutral FE matrix, DOF, load-case and contact mapping receipt."""

    binding_id: str = Field(min_length=1)
    provider_receipt: StructuralProviderResultReceipt
    load_case_id: str = Field(min_length=1)
    boundary_condition_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stiffness_field_id: str = Field(min_length=1)
    stiffness_quantity_id: Literal["incremental_stiffness_matrix"]
    stiffness_array_content_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stiffness_array_order: Literal["C", "F"]
    mesh_node_id_map_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    dof_basis_transform_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stiffness_matrix_N_m: tuple[tuple[float, ...], ...] = Field(min_length=2, max_length=128)
    normalized_stiffness_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    coordinate_frame_id: str = Field(min_length=1)
    displacement_unit: Literal["m"]
    force_unit: Literal["N"]
    matrix_unit: Literal["N/m"]
    global_dof_node_ids: tuple[str, ...] = Field(min_length=2, max_length=128)
    global_dof_component_ids: tuple[Literal["translation_x", "translation_y", "translation_z"], ...] = Field(
        min_length=2, max_length=128
    )
    fixed_incremental_dof_indices: tuple[int, ...] = ()
    contact_node_ids: tuple[str, ...] = Field(min_length=2, max_length=64)
    contact_normal_dof_indices: tuple[int, ...] = Field(min_length=2, max_length=64)
    contact_closure_signs: tuple[Literal[-1, 1], ...] = Field(min_length=2, max_length=64)
    stiffness_units_and_scaling_reviewed: bool
    load_case_and_boundary_conditions_reviewed: bool
    mesh_frame_and_dof_order_reviewed: bool
    dof_basis_transform_reviewed: bool
    contact_normal_mapping_reviewed: bool
    incremental_linear_elastic_applicability_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def receipt_and_mapping_agree(self):
        receipt = self.provider_receipt
        if receipt.analysis_kind != "finite_element":
            raise ValueError("a finite-element provider receipt is required")
        if self.load_case_id not in receipt.load_case_ids:
            raise ValueError("selected load case is absent from the provider receipt")
        if self.boundary_condition_sha256 != receipt.load_case_digest:
            raise ValueError("boundary-condition/load-case digest differs from the provider receipt")
        if self.coordinate_frame_id != receipt.mesh.coordinate_frame_id:
            raise ValueError("stiffness DOFs and provider mesh must use the exact same coordinate frame")
        fields = [row for row in receipt.result_fields if row.field_id == self.stiffness_field_id]
        if len(fields) != 1:
            raise ValueError("stiffness field ID must resolve to exactly one provider result field")
        field = fields[0]
        dof_count = len(self.global_dof_node_ids)
        if len(self.stiffness_matrix_N_m) != dof_count or any(
            len(row) != dof_count for row in self.stiffness_matrix_N_m
        ):
            raise ValueError("normalized stiffness matrix must be square and align with the retained DOF map")
        if len(self.global_dof_component_ids) != dof_count:
            raise ValueError("one translational component identity is required per matrix DOF")
        if len(set(zip(self.global_dof_node_ids, self.global_dof_component_ids, strict=True))) != dof_count:
            raise ValueError("global node/component DOF identities must be unique and ordered")
        if field.load_case_id != self.load_case_id:
            raise ValueError("stiffness result field belongs to a different load case")
        if (field.quantity_id != self.stiffness_quantity_id or field.unit_token != self.matrix_unit
                or field.result_location != "global" or field.coordinate_frame_id != self.coordinate_frame_id):
            raise ValueError("stiffness result field quantity, unit, location or frame is incompatible")
        if field.array_shape != (dof_count, dof_count):
            raise ValueError("provider field array shape must match the declared reduced DOF matrix")
        if field.array_content_digest != self.stiffness_array_content_sha256:
            raise ValueError("normalized input array digest does not match the provider field receipt")
        if field.array_order != self.stiffness_array_order:
            raise ValueError("stiffness matrix reshape order differs from the provider result receipt")
        if canonical_digest(self.stiffness_matrix_N_m) != self.normalized_stiffness_sha256:
            raise ValueError("normalized stiffness matrix digest mismatch")
        count = len(self.contact_node_ids)
        if len(set(self.contact_node_ids)) != count:
            raise ValueError("contact node IDs must be unique and retain their declared order")
        if len(self.contact_normal_dof_indices) != count or len(self.contact_closure_signs) != count:
            raise ValueError("each contact node needs exactly one normal DOF and closure sign")
        if len(set(self.contact_normal_dof_indices)) != count:
            raise ValueError("contact normal DOFs must be unique")
        if any(index < 0 or index >= dof_count for index in (*self.fixed_incremental_dof_indices,
                                                              *self.contact_normal_dof_indices)):
            raise ValueError("fixed/contact DOF index is outside the retained stiffness matrix")
        if len(set(self.fixed_incremental_dof_indices)) != len(self.fixed_incremental_dof_indices):
            raise ValueError("fixed DOF indices must be unique")
        if set(self.fixed_incremental_dof_indices) & set(self.contact_normal_dof_indices):
            raise ValueError("contact response DOFs cannot also be fixed")
        if any(self.global_dof_node_ids[dof] != node for node, dof in zip(
            self.contact_node_ids, self.contact_normal_dof_indices, strict=True
        )):
            raise ValueError("contact node order must match the node identity of each selected normal DOF")
        if len(self.contact_node_ids) > dof_count - len(set(self.fixed_incremental_dof_indices)):
            raise ValueError("retained FE operator has fewer free DOFs than requested contact nodes")
        gates = (
            self.stiffness_units_and_scaling_reviewed,
            self.load_case_and_boundary_conditions_reviewed,
            self.mesh_frame_and_dof_order_reviewed,
            self.dof_basis_transform_reviewed,
            self.contact_normal_mapping_reviewed,
            self.incremental_linear_elastic_applicability_reviewed,
            self.computational_use_authorized,
        )
        if not all(gates):
            raise ValueError("all solver mapping, boundary, applicability and computational-use reviews are required")
        return self


class ExternalFlangeComplianceHistoryBinding(Contract):
    """Bind one ordered sequence of provider receipts to a compliance history."""

    history_id: str = Field(min_length=1)
    times_s: tuple[float, ...] = Field(min_length=2, max_length=1000)
    bindings: tuple[ExternalFlangeComplianceBinding, ...] = Field(min_length=2, max_length=1000)
    receipt_times_reviewed: bool
    symmetry_relative_tolerance: float = Field(default=1e-10, gt=0, le=1e-5)
    minimum_positive_stiffness_eigenvalue_N_m: float = Field(default=1e-12, gt=0)
    maximum_free_operator_condition_number: float = Field(default=1e12, ge=1, le=1e14)

    @model_validator(mode="after")
    def ordered_receipts_share_operator_contract(self):
        if len(self.times_s) != len(self.bindings):
            raise ValueError("each caller-declared time requires exactly one external structural receipt")
        if self.times_s[0] != 0 or any(not math.isfinite(value) for value in self.times_s) or any(
            right <= left for left, right in zip(self.times_s[:-1], self.times_s[1:], strict=True)
        ):
            raise ValueError("receipt-bound compliance history needs a finite zero-based increasing time vector")
        first = self.bindings[0]
        stable = (
            "provider_id", "provider_revision", "model_id", "model_revision", "asset_id",
            "component_id", "location_id", "physical_scope_id",
        )
        first_receipt = first.provider_receipt
        first_values = tuple(getattr(first_receipt, field) for field in stable)
        mapping_fields = (
            "coordinate_frame_id", "displacement_unit", "force_unit", "matrix_unit",
            "global_dof_node_ids", "global_dof_component_ids", "fixed_incremental_dof_indices",
            "contact_node_ids", "contact_normal_dof_indices", "contact_closure_signs",
        )
        first_mapping = tuple(getattr(first, field) for field in mapping_fields)
        for binding in self.bindings[1:]:
            receipt = binding.provider_receipt
            if tuple(getattr(receipt, field) for field in stable) != first_values:
                raise ValueError("all history receipts must retain provider/model revision and physical asset scope")
            if tuple(getattr(binding, field) for field in mapping_fields) != first_mapping:
                raise ValueError("all history receipts must retain the exact ordered translational DOF/contact mapping")
        return self


def flange_compliance_request_from_external_receipt(
    binding: ExternalFlangeComplianceBinding,
) -> FlangeComplianceReductionRequest:
    """Convert a validated solver receipt into the existing unit-load compliance request."""
    receipt = binding.provider_receipt
    return FlangeComplianceReductionRequest(
        reduction_id=binding.binding_id,
        upstream_solver_id=f"{receipt.provider_id}:{receipt.model_id}",
        upstream_solver_revision=f"{receipt.provider_revision}:{receipt.model_revision}",
        stiffness_source_sha256=binding.normalized_stiffness_sha256,
        stiffness_matrix_N_m=binding.stiffness_matrix_N_m,
        fixed_incremental_dof_indices=binding.fixed_incremental_dof_indices,
        contact_node_ids=binding.contact_node_ids,
        contact_normal_dof_indices=binding.contact_normal_dof_indices,
        contact_closure_signs=binding.contact_closure_signs,
        stiffness_units_and_scaling_reviewed=binding.stiffness_units_and_scaling_reviewed,
        fixed_supports_and_boundary_dofs_reviewed=binding.load_case_and_boundary_conditions_reviewed,
        contact_normal_dof_mapping_reviewed=binding.contact_normal_mapping_reviewed,
        incremental_linear_elastic_applicability_reviewed=binding.incremental_linear_elastic_applicability_reviewed,
        computational_use_authorized=binding.computational_use_authorized,
    )


def reduce_external_flange_contact_compliance(
    binding: ExternalFlangeComplianceBinding,
) -> Calculation:
    """Run the existing reducer and attach full external solver/mesh/DOF lineage."""
    request = flange_compliance_request_from_external_receipt(binding)
    calculation = reduce_flange_contact_compliance(request)
    receipt = binding.provider_receipt
    stiffness_field = next(row for row in receipt.result_fields if row.field_id == binding.stiffness_field_id)
    lineage = {
        "external_solver_receipt_sha256": receipt.payload_digest,
        "provider_id": receipt.provider_id,
        "provider_revision": receipt.provider_revision,
        "provider_analysis_id": receipt.analysis_id,
        "provider_input_digest": receipt.provider_input_digest,
        "provider_result_digest": receipt.provider_result_digest,
        "stiffness_field_record_digest": stiffness_field.result_record_digest,
        "mesh_id": receipt.mesh.mesh_id,
        "mesh_revision": receipt.mesh.mesh_revision,
        "mesh_digest": receipt.mesh.mesh_content_digest,
        "coordinate_frame_id": binding.coordinate_frame_id,
        "load_case_id": binding.load_case_id,
        "boundary_condition_sha256": binding.boundary_condition_sha256,
        "stiffness_field_id": binding.stiffness_field_id,
        "provider_array_content_sha256": binding.stiffness_array_content_sha256,
        "provider_array_order": binding.stiffness_array_order,
        "mesh_node_id_map_sha256": binding.mesh_node_id_map_sha256,
        "dof_basis_transform_sha256": binding.dof_basis_transform_sha256,
        "normalized_stiffness_sha256": binding.normalized_stiffness_sha256,
        "global_dof_node_ids": list(binding.global_dof_node_ids),
        "global_dof_component_ids": list(binding.global_dof_component_ids),
    }
    return Calculation(
        status=calculation.status,
        values=calculation.values | {"external_solver_lineage": lineage},
        notes=calculation.notes + (
            "The external FE result was consumed only after exact receipt, matrix-field, load-case, boundary, frame and translational DOF checks.",
            "This adapter does not assemble or solve the external FE model, recover mixed rotational/translational operators, or establish structural or sealing qualification.",
        ),
    )


def reduce_external_flange_contact_compliance_history(
    binding: ExternalFlangeComplianceHistoryBinding,
) -> Calculation:
    """Reduce receipt-bound tangent matrices while retaining per-knot provenance."""
    receipt_digests = [item.provider_receipt.payload_digest for item in binding.bindings]
    input_digest = canonical_digest(binding.model_dump(mode="json"))
    if not binding.receipt_times_reviewed:
        return Calculation(status="needs_data", values={
            "history_id": binding.history_id,
            "input_sha256": input_digest,
            "times_s": list(binding.times_s),
            "receipt_times_reviewed": False,
            "receipt_payload_digests": receipt_digests,
            "operator_history": [],
            "missing_reviews": ["receipt_times_reviewed"],
            "basis": "Provider receipts do not contain a canonical physical time field; caller-to-receipt time correspondence must be reviewed before reduction.",
        })
    first = binding.bindings[0]
    first_receipt = first.provider_receipt
    request = FlangeComplianceReductionHistoryRequest(
        history_id=binding.history_id,
        upstream_solver_id=f"{first_receipt.provider_id}:{first_receipt.model_id}",
        upstream_solver_revision=f"{first_receipt.provider_revision}:{first_receipt.model_revision}",
        times_s=binding.times_s,
        stiffness_source_sha256=tuple(item.normalized_stiffness_sha256 for item in binding.bindings),
        stiffness_matrices_N_m=tuple(item.stiffness_matrix_N_m for item in binding.bindings),
        fixed_incremental_dof_indices=first.fixed_incremental_dof_indices,
        contact_node_ids=first.contact_node_ids,
        contact_normal_dof_indices=first.contact_normal_dof_indices,
        contact_closure_signs=first.contact_closure_signs,
        symmetry_relative_tolerance=binding.symmetry_relative_tolerance,
        minimum_positive_stiffness_eigenvalue_N_m=binding.minimum_positive_stiffness_eigenvalue_N_m,
        maximum_free_operator_condition_number=binding.maximum_free_operator_condition_number,
        stiffness_units_and_scaling_reviewed=all(item.stiffness_units_and_scaling_reviewed for item in binding.bindings),
        fixed_supports_and_boundary_dofs_reviewed=all(
            item.load_case_and_boundary_conditions_reviewed for item in binding.bindings
        ),
        contact_normal_dof_mapping_reviewed=all(item.contact_normal_mapping_reviewed for item in binding.bindings),
        incremental_linear_elastic_applicability_reviewed=all(
            item.incremental_linear_elastic_applicability_reviewed for item in binding.bindings
        ),
        computational_use_authorized=all(item.computational_use_authorized for item in binding.bindings),
    )
    calculation = reduce_flange_contact_compliance_history(request)
    rows = calculation.values.get("operator_history", [])
    enriched = []
    for index, row in enumerate(rows):
        item = binding.bindings[index]
        receipt = item.provider_receipt
        field = next(value for value in receipt.result_fields if value.field_id == item.stiffness_field_id)
        enriched.append(row | {
            "receipt_id": receipt.receipt_id,
            "external_solver_receipt_sha256": receipt.payload_digest,
            "provider_analysis_id": receipt.analysis_id,
            "provider_input_digest": receipt.provider_input_digest,
            "provider_result_digest": receipt.provider_result_digest,
            "stiffness_field_record_digest": field.result_record_digest,
            "mesh_id": receipt.mesh.mesh_id,
            "mesh_revision": receipt.mesh.mesh_revision,
            "mesh_digest": receipt.mesh.mesh_content_digest,
            "load_case_id": item.load_case_id,
            "boundary_condition_sha256": item.boundary_condition_sha256,
            "stiffness_field_id": item.stiffness_field_id,
            "provider_array_content_sha256": item.stiffness_array_content_sha256,
            "provider_array_order": item.stiffness_array_order,
            "mesh_node_id_map_sha256": item.mesh_node_id_map_sha256,
            "dof_basis_transform_sha256": item.dof_basis_transform_sha256,
        })
    base = calculation.values | {
        "receipt_times_reviewed": binding.receipt_times_reviewed,
        "receipt_payload_digests": receipt_digests,
        "provider_receipts": enriched,
        "input_sha256": input_digest,
    }
    return Calculation(status=calculation.status, values=base, notes=calculation.notes + (
        "Each caller-declared time is linked to one digest-verified FE result receipt and its normalized stiffness matrix.",
        "Time labels and receipt-to-time correspondence are user-provided and require review; this adapter does not interpolate or solve FE response between receipts.",
    ))


def _context_matches_receipt(x: ExternalFlangeComplianceBinding, context: RunContext) -> None:
    receipt = x.provider_receipt
    if context.asset_id != receipt.asset_id or context.location_id != receipt.location_id:
        raise ValueError("RunContext asset/location must match the structural provider receipt")


def _context_matches_receipt_history(x: ExternalFlangeComplianceHistoryBinding, context: RunContext) -> None:
    for binding in x.bindings:
        _context_matches_receipt(binding, context)


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.external_flange_compliance_receipt",
        ExternalFlangeComplianceBinding,
        reduce_external_flange_contact_compliance,
        {
            "flange_relative_compliance_matrix_m_N": "m/N",
            "minimum_free_stiffness_eigenvalue_N_m": "N/m",
            "free_stiffness_condition_number": "1",
        },
        (
            "A digest-pinned finite-element receipt must identify the selected load case, mesh, coordinate frame, stiffness result field, explicit translational DOF map and contact-normal signs before reduction.",
            "This interface consumes an already reduced incremental stiffness matrix; it does not assemble/solve FE, transform mixed rotational DOFs, model nonlinear gasket response or qualify sealing.",
        ),
        ("external_flange_fe_compliance_receipt",),
        qualification="user_model",
        context_validator=_context_matches_receipt,
    ), ModelSpec(
        "integration.external_flange_compliance_history",
        ExternalFlangeComplianceHistoryBinding,
        reduce_external_flange_contact_compliance_history,
        {
            "times_s": "s",
            "operator_history[].values.flange_relative_compliance_matrix_m_N": "m/N",
        },
        (
            "Every caller-declared knot is paired with a digest-verified external FE stiffness receipt using a stable provider revision, asset scope and ordered translational contact mapping.",
            "The adapter reduces each supplied matrix independently; it does not infer receipt timestamps, interpolate matrices, solve FE, model nonlinear contact or qualify sealing.",
        ),
        ("external_flange_fe_compliance_receipt_history",),
        qualification="user_model",
        context_validator=_context_matches_receipt_history,
    )]
