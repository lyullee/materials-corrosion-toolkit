"""Digest-bound scalar feature handoff from tensor cycles to integer blocks."""

from __future__ import annotations

import math
import json
from typing import Literal

from pydantic import Field, model_validator

from .adaptive_cycle_block_damage import (
    AdaptiveCycleBlockDamageRequest,
    CycleBlockLawParameter,
    IntegerCycleDamageBlock,
)
from .contracts import AssessmentResult, Calculation, Contract, Evidence, canonical_digest
from .models.multiaxial_work_life import ClosedTensorCycle
from .registry import ModelSpec

FEATURE_UNITS = {
    "normal_stress_max_Pa": "Pa",
    "normal_stress_min_Pa": "Pa",
    "normal_stress_range_Pa": "Pa",
    "normal_strain_range": "1",
    "normal_strain_amplitude": "1",
    "engineering_shear_strain_range": "1",
    "engineering_shear_strain_amplitude": "1",
}


class FiniteCyclePlane(Contract):
    plane_id: str = Field(min_length=1)
    normal: tuple[float, float, float]
    engineering_shear_direction: tuple[float, float, float]

    @model_validator(mode="after")
    def orthonormal_plane_basis(self):
        if any(not math.isfinite(value) for value in (*self.normal, *self.engineering_shear_direction)):
            raise ValueError("finite-plane vectors must be finite")
        normal_length = math.sqrt(math.fsum(value * value for value in self.normal))
        shear_length = math.sqrt(math.fsum(value * value for value in self.engineering_shear_direction))
        dot = math.fsum(a * b for a, b in zip(self.normal, self.engineering_shear_direction, strict=True))
        if not math.isclose(normal_length, 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("plane normal must be a unit vector")
        if not math.isclose(shear_length, 1.0, rel_tol=0.0, abs_tol=1e-10):
            raise ValueError("in-plane shear direction must be a unit vector")
        if abs(dot) > 1e-10:
            raise ValueError("in-plane shear direction must be orthogonal to plane normal")
        return self


class CycleBlockFeatureBinding(Contract):
    plane_id: str = Field(min_length=1)
    feature_id: Literal[
        "normal_stress_max_Pa",
        "normal_stress_min_Pa",
        "normal_stress_range_Pa",
        "normal_strain_range",
        "normal_strain_amplitude",
        "engineering_shear_strain_range",
        "engineering_shear_strain_amplitude",
    ]
    parameter_id: str = Field(min_length=1)


class TensorCycleBlockFeatureInput(Contract):
    block_id: str = Field(min_length=1)
    cycle_population_id: str = Field(min_length=1)
    loading_state_id: str = Field(min_length=1)
    cycle_count: int = Field(ge=1, le=2**53, strict=True)
    source_record_id: str = Field(min_length=1)
    source_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    cycle: ClosedTensorCycle
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def representative_cycle_source(self):
        if not any(
            row.source_id == self.source_record_id and row.sha256 == self.source_record_sha256
            for row in self.evidence
        ):
            raise ValueError("cycle source record ID and digest must match declared Evidence")
        if self.cycle.allocated_cycle_count != 1.0:
            raise ValueError("each block must provide one representative tensor cycle; cycle_count supplies repetitions")
        return self


class CycleBlockFeatureHandoffRequest(Contract):
    """Caller cycle histories and exact feature-to-block parameter bindings."""

    schema_version: Literal["matintegrity.cycle_block_feature_handoff.v1"] = (
        "matintegrity.cycle_block_feature_handoff.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    cycle_count_basis_id: str = Field(min_length=1)
    history_provider_id: str = Field(min_length=1)
    history_provider_revision: str = Field(min_length=1)
    history_provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_provider_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    stress_history_source_id: str = Field(min_length=1)
    stress_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_history_source_id: str = Field(min_length=1)
    strain_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    strain_shear_convention: Literal["tensor", "engineering"]
    maximum_stress_closure_error_Pa: float = Field(ge=0.0)
    maximum_strain_closure_error: float = Field(ge=0.0)
    finite_planes: tuple[FiniteCyclePlane, ...] = Field(min_length=1, max_length=10000)
    blocks: tuple[TensorCycleBlockFeatureInput, ...] = Field(min_length=1, max_length=10000)
    parameter_bindings: tuple[CycleBlockFeatureBinding, ...] = Field(min_length=1, max_length=1000)
    tensor_order_units_and_shear_convention_reviewed: bool
    closed_cycle_and_representative_repetition_reviewed: bool
    finite_plane_selection_and_feature_mapping_reviewed: bool
    feature_parameter_semantics_reviewed: bool
    source_evidence_and_usage_rights_reviewed: bool
    downstream_caller_law_remains_external_reviewed: bool
    computational_use_authorized: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_handoff(self):
        planes = {row.plane_id for row in self.finite_planes}
        if len(planes) != len(self.finite_planes):
            raise ValueError("finite-plane IDs must be unique")
        if len({row.block_id for row in self.blocks}) != len(self.blocks):
            raise ValueError("cycle block IDs must be unique")
        if len({row.cycle.cycle_id for row in self.blocks}) != len(self.blocks):
            raise ValueError("representative cycle IDs must be unique across blocks")
        if sum(row.cycle_count for row in self.blocks) > 2**53:
            raise ValueError("total integer cycle count exceeds exact representation support")
        if sum(len(row.cycle.sample_ids) * len(planes) for row in self.blocks) > 2_000_000:
            raise ValueError("cycle-by-plane sample budget exceeded")
        parameter_ids = [row.parameter_id for row in self.parameter_bindings]
        if len(parameter_ids) != len(set(parameter_ids)):
            raise ValueError("downstream parameter IDs must be unique")
        binding_keys = [(row.plane_id, row.feature_id) for row in self.parameter_bindings]
        if len(binding_keys) != len(set(binding_keys)):
            raise ValueError("each plane feature may be mapped only once")
        if any(row.plane_id not in planes for row in self.parameter_bindings):
            raise ValueError("every feature binding must select one declared finite plane")
        source_hashes = {(row.source_id, row.sha256) for row in self.evidence}
        if (self.history_provider_id, self.history_provider_record_sha256) not in source_hashes:
            raise ValueError("history provider record ID and digest must map to declared Evidence")
        if (self.stress_history_source_id, self.stress_history_sha256) not in source_hashes:
            raise ValueError("stress history source and digest must map to declared Evidence")
        if (self.strain_history_source_id, self.strain_history_sha256) not in source_hashes:
            raise ValueError("strain history source and digest must map to declared Evidence")
        return self


def _tensor(components: tuple[float, ...] | list[float], *, engineering_shear: bool = False):
    xx, yy, zz, xy, yz, zx = (float(value) for value in components)
    factor = 0.5 if engineering_shear else 1.0
    xy *= factor
    yz *= factor
    zx *= factor
    return ((xx, xy, zx), (xy, yy, yz), (zx, yz, zz))


def _matvec(matrix, vector):
    result = []
    for i in range(3):
        products = [matrix[i][j] * vector[j] for j in range(3)]
        if any(not math.isfinite(value) for value in products):
            raise ArithmeticError("tensor projection exceeded finite numeric support")
        projected = math.fsum(products)
        if not math.isfinite(projected):
            raise ArithmeticError("tensor projection exceeded finite numeric support")
        result.append(projected)
    return tuple(result)


def _dot(left, right):
    products = [a * b for a, b in zip(left, right, strict=True)]
    if any(not math.isfinite(value) for value in products):
        raise ArithmeticError("plane feature exceeded finite numeric support")
    value = math.fsum(products)
    if not math.isfinite(value):
        raise ArithmeticError("plane feature exceeded finite numeric support")
    return value


def cycle_block_feature_handoff(request: CycleBlockFeatureHandoffRequest) -> Calculation:
    """Calculate explicit per-cycle plane features and construct callback blocks.

    This performs no fatigue damage, state evolution or life calculation. Each
    block's representative closed tensor cycle is used for its declared integer
    cycle count only because the caller explicitly reviews that interpretation.
    """

    input_sha256 = canonical_digest(request.model_dump(mode="json"))
    common = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "material_condition_id": request.material_condition_id,
        "location_id": request.location_id,
        "cycle_count_basis_id": request.cycle_count_basis_id,
        "history_provider_id": request.history_provider_id,
        "history_provider_revision": request.history_provider_revision,
        "history_provider_configuration_sha256": request.history_provider_configuration_sha256,
        "history_provider_record_sha256": request.history_provider_record_sha256,
        "stress_history_source_id": request.stress_history_source_id,
        "stress_history_sha256": request.stress_history_sha256,
        "strain_history_source_id": request.strain_history_source_id,
        "strain_history_sha256": request.strain_history_sha256,
        "strain_shear_convention": request.strain_shear_convention,
        "input_sha256": input_sha256,
    }
    reviews = {
        "tensor_order_units_and_shear_convention_reviewed": request.tensor_order_units_and_shear_convention_reviewed,
        "closed_cycle_and_representative_repetition_reviewed": request.closed_cycle_and_representative_repetition_reviewed,
        "finite_plane_selection_and_feature_mapping_reviewed": request.finite_plane_selection_and_feature_mapping_reviewed,
        "feature_parameter_semantics_reviewed": request.feature_parameter_semantics_reviewed,
        "source_evidence_and_usage_rights_reviewed": request.source_evidence_and_usage_rights_reviewed,
        "downstream_caller_law_remains_external_reviewed": request.downstream_caller_law_remains_external_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=common | {"missing_reviews": missing})

    planes = {row.plane_id: row for row in request.finite_planes}
    block_rows = []
    downstream_blocks = []
    for block in request.blocks:
        cycle = block.cycle
        stress_start = cycle.stress_tensor_components_Pa[0]
        stress_end = cycle.stress_tensor_components_Pa[-1]
        strain_start = cycle.strain_tensor_components[0]
        strain_end = cycle.strain_tensor_components[-1]
        stress_closure = max(abs(a - b) for a, b in zip(stress_start, stress_end, strict=True))
        strain_closure = max(abs(a - b) for a, b in zip(strain_start, strain_end, strict=True))
        if (stress_closure > request.maximum_stress_closure_error_Pa
                or strain_closure > request.maximum_strain_closure_error):
            return Calculation(
                status="out_of_scope",
                values=common | {
                    "failed_block_id": block.block_id,
                    "stress_closure_error_Pa": stress_closure,
                    "strain_closure_error": strain_closure,
                    "reason": "representative tensor cycle exceeds caller closure tolerances",
                    "computed_block_prefix": block_rows,
                },
                notes=("No integer cycle block is emitted for the failing or later input block.",),
            )

        per_plane = {}
        try:
            for plane_id, plane in planes.items():
                normal_stress = []
                normal_strain = []
                engineering_shear_strain = []
                for stress_components, strain_components in zip(
                    cycle.stress_tensor_components_Pa,
                    cycle.strain_tensor_components,
                    strict=True,
                ):
                    stress_tensor = _tensor(stress_components)
                    strain_tensor = _tensor(
                        strain_components,
                        engineering_shear=request.strain_shear_convention == "engineering",
                    )
                    stress_normal_traction = _matvec(stress_tensor, plane.normal)
                    strain_normal_vector = _matvec(strain_tensor, plane.normal)
                    normal_stress.append(_dot(plane.normal, stress_normal_traction))
                    normal_strain.append(_dot(plane.normal, strain_normal_vector))
                    shear_value = 2.0 * _dot(plane.engineering_shear_direction, strain_normal_vector)
                    if not math.isfinite(shear_value):
                        raise ArithmeticError("resolved engineering shear strain exceeded finite support")
                    engineering_shear_strain.append(shear_value)
                smax, smin = max(normal_stress), min(normal_stress)
                en_max, en_min = max(normal_strain), min(normal_strain)
                gs_max, gs_min = max(engineering_shear_strain), min(engineering_shear_strain)
                feature_values = {
                    "normal_stress_max_Pa": smax,
                    "normal_stress_min_Pa": smin,
                    "normal_stress_range_Pa": smax - smin,
                    "normal_strain_range": en_max - en_min,
                    "normal_strain_amplitude": 0.5 * (en_max - en_min),
                    "engineering_shear_strain_range": gs_max - gs_min,
                    "engineering_shear_strain_amplitude": 0.5 * (gs_max - gs_min),
                }
                if any(not math.isfinite(value) for value in feature_values.values()):
                    raise ArithmeticError("finite-plane scalar feature exceeded finite numeric support")
                per_plane[plane_id] = feature_values
        except (ArithmeticError, OverflowError, ValueError) as error:
            return Calculation(
                status="out_of_scope",
                values=common | {
                    "failed_block_id": block.block_id,
                    "reason": str(error),
                    "computed_block_prefix": block_rows,
                },
                notes=("No integer block is emitted for the failing or later input block.",),
            )

        parameters = []
        for binding in request.parameter_bindings:
            parameters.append(CycleBlockLawParameter(
                parameter_id=binding.parameter_id,
                value=per_plane[binding.plane_id][binding.feature_id],
                unit=FEATURE_UNITS[binding.feature_id],
            ))
        feature_payload = {
            "block_id": block.block_id,
            "cycle_population_id": block.cycle_population_id,
            "loading_state_id": block.loading_state_id,
            "cycle_count": block.cycle_count,
            "source_record_id": block.source_record_id,
            "source_record_sha256": block.source_record_sha256,
            "cycle_id": cycle.cycle_id,
            "cycle_input_sha256": canonical_digest(cycle.model_dump(mode="json")),
            "stress_closure_error_Pa": stress_closure,
            "strain_closure_error": strain_closure,
            "selected_plane_features": per_plane,
            "parameter_bindings": [
                {
                    "plane_id": binding.plane_id,
                    "feature_id": binding.feature_id,
                    "parameter_id": binding.parameter_id,
                    "unit": FEATURE_UNITS[binding.feature_id],
                    "value": per_plane[binding.plane_id][binding.feature_id],
                }
                for binding in request.parameter_bindings
            ],
        }
        derived_source_sha = canonical_digest({
            "handoff_input_sha256": input_sha256,
            "source_record_sha256": block.source_record_sha256,
            "block_feature_payload": feature_payload,
        })
        downstream = IntegerCycleDamageBlock(
            block_id=block.block_id,
            cycle_population_id=block.cycle_population_id,
            loading_state_id=block.loading_state_id,
            cycle_count=block.cycle_count,
            source_sha256=derived_source_sha,
            parameters=tuple(parameters),
        )
        block_rows.append(feature_payload | {
            "derived_block_source_sha256": derived_source_sha,
            "integer_cycle_block_sha256": canonical_digest(downstream.model_dump(mode="json")),
        })
        downstream_blocks.append(downstream)

    block_payloads = [row.model_dump(mode="json") for row in downstream_blocks]
    block_sha256 = canonical_digest(block_payloads)
    receipt_sha256 = canonical_digest({
        "input_sha256": input_sha256,
        "integer_cycle_blocks_sha256": block_sha256,
        "physical_scope_id": request.physical_scope_id,
        "material_condition_id": request.material_condition_id,
        "cycle_count_basis_id": request.cycle_count_basis_id,
    })
    return Calculation(values=common | {
        "block_feature_ledger": block_rows,
        "block_feature_ledger_sha256": canonical_digest(block_rows),
        "integer_cycle_blocks": block_payloads,
        "integer_cycle_blocks_sha256": block_sha256,
        "handoff_receipt_sha256": receipt_sha256,
        "cycle_block_count": len(block_rows),
        "total_integer_cycle_count": sum(row.cycle_count for row in request.blocks),
        "missing_reviews": [],
    }, notes=(
        "Tensor histories are reduced to explicitly selected finite-plane scalar features and bound to existing integer cycle blocks with a digest of the exact derived parameter payload.",
        "This adapter does not calculate a fatigue criterion, material-state evolution, damage rate, failure life, cycle count, acceptance or probability; the downstream adaptive callback remains caller-owned.",
    ))


def bind_cycle_features_to_adaptive_request(
    adaptive_request: AdaptiveCycleBlockDamageRequest,
    handoff_result: AssessmentResult,
) -> AdaptiveCycleBlockDamageRequest:
    """Bind a computed handoff receipt into an existing adaptive cycle request."""

    if handoff_result.model_id != "integration.cycle_block_feature_handoff" or handoff_result.status != "computed":
        raise ValueError("a computed cycle-block feature handoff AssessmentResult is required")
    expected_input_digest = canonical_digest({
        "model_id": handoff_result.model_id,
        "model_version": handoff_result.model_version,
        "inputs": handoff_result.inputs,
        "context": handoff_result.context.model_dump(mode="json"),
    })
    if handoff_result.input_digest != expected_input_digest:
        raise ValueError("handoff assessment input digest mismatch")
    values = handoff_result.values
    if values.get("input_sha256") != canonical_digest(handoff_result.inputs):
        raise ValueError("handoff model input digest mismatch")
    block_values = values.get("integer_cycle_blocks")
    if not isinstance(block_values, list) or not block_values:
        raise ValueError("handoff result lacks its ordered adaptive block list")
    if canonical_digest(block_values) != values.get("integer_cycle_blocks_sha256"):
        raise ValueError("integer cycle block payload digest mismatch")
    expected_receipt = canonical_digest({
        "input_sha256": values["input_sha256"],
        "integer_cycle_blocks_sha256": values["integer_cycle_blocks_sha256"],
        "physical_scope_id": values["physical_scope_id"],
        "material_condition_id": values["material_condition_id"],
        "cycle_count_basis_id": values["cycle_count_basis_id"],
    })
    if expected_receipt != values.get("handoff_receipt_sha256"):
        raise ValueError("handoff receipt digest mismatch")
    if (adaptive_request.physical_scope_id, adaptive_request.material_condition_id,
            adaptive_request.cycle_count_basis_id) != (
            values["physical_scope_id"], values["material_condition_id"], values["cycle_count_basis_id"]):
        raise ValueError("adaptive request scope, material condition or cycle-count basis differs from handoff")
    # AssessmentResult values are JSON-native, so tuple-valued strict contracts
    # must be reconstructed through the JSON validator rather than dict coercion.
    blocks = tuple(
        IntegerCycleDamageBlock.model_validate_json(
            json.dumps(row, ensure_ascii=False, allow_nan=False)
        )
        for row in block_values
    )
    existing = adaptive_request.blocks
    if len(existing) != len(blocks):
        raise ValueError("adaptive request block count differs from the handoff")
    for before, after in zip(existing, blocks, strict=True):
        if (before.block_id, before.cycle_population_id, before.loading_state_id, before.cycle_count) != (
            after.block_id, after.cycle_population_id, after.loading_state_id, after.cycle_count,
        ):
            raise ValueError("adaptive request block order or identity differs from handoff")
    payload = adaptive_request.model_dump(mode="json")
    payload["blocks"] = [row.model_dump(mode="json") for row in blocks]
    return AdaptiveCycleBlockDamageRequest.model_validate_json(
        json.dumps(payload, ensure_ascii=False, allow_nan=False)
    )


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.cycle_block_feature_handoff",
        CycleBlockFeatureHandoffRequest,
        cycle_block_feature_handoff,
        {
            "block_feature_ledger[].stress_closure_error_Pa": "Pa",
            "block_feature_ledger[].strain_closure_error": "1",
            "block_feature_ledger[].selected_plane_features.*.normal_stress_max_Pa": "Pa",
            "block_feature_ledger[].selected_plane_features.*.normal_stress_min_Pa": "Pa",
            "block_feature_ledger[].selected_plane_features.*.normal_stress_range_Pa": "Pa",
            "block_feature_ledger[].selected_plane_features.*.normal_strain_range": "1",
            "block_feature_ledger[].selected_plane_features.*.normal_strain_amplitude": "1",
            "block_feature_ledger[].selected_plane_features.*.engineering_shear_strain_range": "1",
            "block_feature_ledger[].selected_plane_features.*.engineering_shear_strain_amplitude": "1",
            "integer_cycle_blocks[].parameters[].value": "mixed",
            "total_integer_cycle_count": "1",
        },
        (
            "Extract exact finite-plane scalar stress/strain features from each caller representative closed tensor cycle and map selected values, units, cycle population and integer repetition count into the adaptive cycle-block contract.",
            "Features are descriptors only. No named fatigue law, damage, life or material state is inferred; the adaptive cycle callback remains caller-owned.",
        ),
        ("caller_multiaxial_cycle_block_feature_handoff",),
        qualification="user_model",
    )]
