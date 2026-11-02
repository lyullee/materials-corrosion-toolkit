"""Compute von Mises equivalent stress from an imported FE tensor and compare a caller limit."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Positive, canonical_digest
from ..j2_prager_strain_history import _deviator as _j2_deviator, _q_equivalent as _j2_q_equivalent
from ..registry import ModelSpec

MODEL_ID = "integration.gasket_fe_von_mises_caller_limit_screen"
IMPORT_MODEL_ID = "integration.external_gasket_fe_field_import"


class TensorComponentBinding(Contract):
    tensor_component: Literal["xx", "yy", "zz", "xy", "yz", "zx"]
    provider_component_id: str = Field(min_length=1)


class GasketFEVonMisesCallerLimitScreen(Contract):
    schema_version: Literal["matintegrity.gasket_fe_von_mises_caller_limit_screen.v1"] = (
        "matintegrity.gasket_fe_von_mises_caller_limit_screen.v1"
    )
    assessment_id: str = Field(min_length=1)
    imported_fe_result: AssessmentResult
    imported_fe_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_asset_id: str = Field(min_length=1)
    expected_location_id: str = Field(min_length=1)
    expected_joint_id: str = Field(min_length=1)
    expected_physical_scope_id: str = Field(min_length=1)
    expected_provider_component_id: str = Field(min_length=1)
    expected_coordinate_frame_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    temperature_K: Positive
    tensor_component_mapping: tuple[TensorComponentBinding, ...] = Field(min_length=6, max_length=6)
    maximum_caller_von_mises_stress_Pa: Positive
    criterion_id: str = Field(min_length=1)
    criterion_basis_description: str = Field(min_length=1)
    criterion_source_id: str = Field(min_length=1)
    criterion_provider_revision: str = Field(min_length=1)
    criterion_record_id: str = Field(min_length=1)
    criterion_record_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    criterion_usage_license_id: str = Field(min_length=1)
    criterion_evidence: tuple[Evidence, ...] = Field(min_length=1)
    tensor_component_frame_and_sign_reviewed: bool
    single_temperature_material_state_reviewed: bool
    averaging_basis_and_hotspot_scope_reviewed: bool
    caller_limit_applicability_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_binding_and_criterion(self):
        if {row.tensor_component for row in self.tensor_component_mapping} != {"xx", "yy", "zz", "xy", "yz", "zx"}:
            raise ValueError("tensor component map must define each symmetric 3D stress component exactly once")
        if len({row.provider_component_id for row in self.tensor_component_mapping}) != 6:
            raise ValueError("provider tensor component IDs must be unique")
        result = self.imported_fe_result
        if result.model_id != IMPORT_MODEL_ID or result.status != "computed":
            raise ValueError("a computed result from the external gasket FE field importer is required")
        if canonical_digest(result.model_dump(mode="json")) != self.imported_fe_result_sha256:
            raise ValueError("imported FE AssessmentResult digest does not match")
        if (result.context.asset_id, result.context.location_id) != (self.expected_asset_id, self.expected_location_id):
            raise ValueError("imported FE asset/location do not match the requested stress screen scope")
        inputs, values = result.inputs, result.values
        if (inputs.get("joint_id"), inputs.get("physical_scope_id"), inputs.get("provider_component_id")) != (
            self.expected_joint_id, self.expected_physical_scope_id, self.expected_provider_component_id
        ):
            raise ValueError("imported FE joint, physical scope or provider component mismatch")
        selection = values.get("field_selection_by_target", {}).get("gasket_stress_tensor")
        if not isinstance(selection, dict):
            raise ValueError("imported FE result has no explicit gasket stress tensor field")
        if (selection.get("unit_token") != "Pa" or selection.get("coordinate_frame_id") != self.expected_coordinate_frame_id
                or selection.get("result_location") not in {"node", "element", "face"}):
            raise ValueError("imported tensor units, frame or result location do not match the declared screen basis")
        if set(selection.get("component_ids", [])) != {row.provider_component_id for row in self.tensor_component_mapping}:
            raise ValueError("provider component mapping must cover the imported stress tensor components exactly")
        criterion_record = {
            "criterion_id": self.criterion_id,
            "basis_description": self.criterion_basis_description,
            "provider_id": self.criterion_source_id,
            "provider_revision": self.criterion_provider_revision,
            "record_id": self.criterion_record_id,
            "material_condition_id": self.material_condition_id,
            "temperature_K": self.temperature_K,
            "maximum_von_mises_stress_Pa": self.maximum_caller_von_mises_stress_Pa,
            "scope": {
                "asset_id": self.expected_asset_id,
                "location_id": self.expected_location_id,
                "joint_id": self.expected_joint_id,
                "physical_scope_id": self.expected_physical_scope_id,
                "provider_component_id": self.expected_provider_component_id,
            },
        }
        if canonical_digest(criterion_record) != self.criterion_record_sha256:
            raise ValueError("caller limit digest must bind limit, material/temperature and physical scope")
        if not any(row.source_id == self.criterion_source_id and row.sha256 == self.criterion_record_sha256
                   and row.license_id == self.criterion_usage_license_id for row in self.criterion_evidence):
            raise ValueError("criterion Evidence must bind the source record, limit digest and usage license")
        return self


def _von_mises(stress: dict[str, float]) -> float:
    components = [stress[key] for key in ("xx", "yy", "zz", "xy", "yz", "zx")]
    deviatoric, _ = _j2_deviator(components)
    equivalent = _j2_q_equivalent(deviatoric)
    if not math.isfinite(equivalent):
        raise OverflowError("von Mises invariant is outside finite numeric support")
    return equivalent


def evaluate_gasket_fe_von_mises_caller_limit_screen(
    request: GasketFEVonMisesCallerLimitScreen,
) -> Calculation:
    """Postprocess imported stress components and compare only with a caller-defined scalar threshold."""
    result = request.imported_fe_result
    digest = canonical_digest(request.model_dump(mode="json"))
    base = {
        "assessment_id": request.assessment_id,
        "model_id": MODEL_ID,
        "joint_id": request.expected_joint_id,
        "physical_scope_id": request.expected_physical_scope_id,
        "imported_fe_result_sha256": request.imported_fe_result_sha256,
        "criterion_record_sha256": request.criterion_record_sha256,
        "input_sha256": digest,
        "physical_acceptance": False,
        "code_stress_check": False,
    }
    reviews = {
        "tensor_component_frame_and_sign_reviewed": request.tensor_component_frame_and_sign_reviewed,
        "single_temperature_material_state_reviewed": request.single_temperature_material_state_reviewed,
        "averaging_basis_and_hotspot_scope_reviewed": request.averaging_basis_and_hotspot_scope_reviewed,
        "caller_limit_applicability_reviewed": request.caller_limit_applicability_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [name for name, accepted in reviews.items() if not accepted]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing})

    mapping = {row.provider_component_id: row.tensor_component for row in request.tensor_component_mapping}
    snapshots = result.values.get("history", [])
    findings = []
    try:
        for snapshot in snapshots:
            for field_row in snapshot.get("response_field", []):
                raw_components = field_row.get("gasket_stress_components_Pa")
                if not isinstance(raw_components, dict) or set(raw_components) != set(mapping):
                    return Calculation(status="needs_data", values=base | {
                        "reason": "stress_tensor_component_data_missing_or_incomplete",
                        "snapshot_id": snapshot.get("snapshot_id"),
                        "contact_node_id": field_row.get("node_id"),
                    })
                stress = {mapping[source_id]: float(value) for source_id, value in raw_components.items()}
                vm = _von_mises(stress)
                margin = request.maximum_caller_von_mises_stress_Pa - vm
                if not math.isfinite(margin):
                    raise OverflowError("caller stress margin is nonfinite")
                findings.append({
                    "snapshot_id": snapshot.get("snapshot_id"),
                    "load_case_id": snapshot.get("load_case_id"),
                    "step_id": snapshot.get("step_id"),
                    "time_s": snapshot.get("time_s"),
                    "contact_node_id": field_row.get("node_id"),
                    "provider_location_id": field_row.get("provider_location_id"),
                    "averaging_basis": snapshot.get("field_lineage", {}).get("gasket_stress_tensor", {}).get("averaging_basis"),
                    "stress_tensor_components_Pa": stress,
                    "von_mises_equivalent_stress_Pa": vm,
                    "caller_limit_Pa": request.maximum_caller_von_mises_stress_Pa,
                    "margin_Pa": margin,
                    "utilization_fraction": vm / request.maximum_caller_von_mises_stress_Pa,
                    "caller_threshold_relation": "at_or_below" if margin >= 0 else "above",
                })
    except (ArithmeticError, OverflowError, TypeError, ValueError) as error:
        return Calculation(status="out_of_scope", values=base | {
            "reason": "imported_stress_postprocessing_outside_finite_support",
            "detail": str(error),
        })
    if not findings:
        return Calculation(status="needs_data", values=base | {"reason": "imported_stress_history_is_empty"})
    maximum = max(findings, key=lambda row: row["von_mises_equivalent_stress_Pa"])
    return Calculation(status="computed", values=base | {
        "criterion_id": request.criterion_id,
        "criterion_basis_description": request.criterion_basis_description,
        "material_condition_id": request.material_condition_id,
        "temperature_K": request.temperature_K,
        "maximum_caller_von_mises_stress_Pa": request.maximum_caller_von_mises_stress_Pa,
        "findings": findings,
        "maximum_stress_witness": maximum,
        "all_locations_at_or_below_caller_limit": all(row["margin_Pa"] >= 0 for row in findings),
        "interpretation": "deterministic caller-defined von Mises scalar-threshold screen only",
        "limitations": [
            "The input is the explicitly imported 3D stress tensor at caller-declared node, element or face locations; no stress recovery, extrapolation, smoothing or averaging is performed by this screen.",
            "Von Mises equivalent stress is computed in the explicitly mapped common Cartesian frame; it does not establish a gasket-specific failure or yield mechanism.",
            "The caller-owned scalar threshold is compared at one declared material condition and temperature; it is not an embedded code allowable or design acceptance criterion.",
            "No stress uncertainty, hot-spot correction, fatigue, local notch, plasticity, creep, damage, failure probability or qualification is inferred.",
        ],
    })


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        MODEL_ID,
        GasketFEVonMisesCallerLimitScreen,
        evaluate_gasket_fe_von_mises_caller_limit_screen,
        {
            "temperature_K": "K",
            "maximum_caller_von_mises_stress_Pa": "Pa",
            "findings[].time_s": "s",
            "findings[].von_mises_equivalent_stress_Pa": "Pa",
            "findings[].caller_limit_Pa": "Pa",
            "findings[].margin_Pa": "Pa",
            "maximum_stress_witness.von_mises_equivalent_stress_Pa": "Pa",
        },
        (
            "Six imported symmetric Cauchy stress components in one caller-mapped Cartesian frame are reduced by the J2/von Mises invariant.",
            "The computed scalar is compared with an explicitly supplied evidence-bound caller limit at one declared material state and temperature.",
            "A passing threshold relation is not code stress acceptance, material qualification or proof of physical integrity.",
        ),
        (
            "imported_gasket_fe_stress_tensor_components_and_frame",
            "three_dimensional_j2_von_mises_equivalent_stress_invariant",
            "caller_material_condition_temperature_and_equivalent_stress_limit",
        ),
        qualification="engineering_screening",
    )]
