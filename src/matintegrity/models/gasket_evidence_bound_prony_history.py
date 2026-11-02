"""Evidence- and temperature-bounded API over the existing gasket Prony solver."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Positive, canonical_digest
from ..gasket_relaxation import (
    GasketViscoelasticHistoryRequest,
    GasketViscoelasticMaterial,
    evaluate_gasket_viscoelastic_history,
)
from ..registry import ModelSpec


MODEL_ID = "fabrication.gasket_evidence_bound_prony_history"
SOURCE_ID = "caller_evidence_bound_gasket_prony_parameter_lineage"
METHOD_SOURCE_ID = "caller_gasket_prony_constitutive_response"


class EvidenceBoundGasketViscoelasticMaterial(GasketViscoelasticMaterial):
    """Backward-compatible extension of the legacy Prony material contract."""

    temperature_support_min_K: Positive
    temperature_support_max_K: Positive
    temperature_support_reviewed: bool
    usage_license_id: str = Field(min_length=1)
    source_and_condition_lineage_reviewed: bool
    license_and_computational_use_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bounded_condition_and_provenance(self):
        if self.temperature_support_max_K < self.temperature_support_min_K:
            raise ValueError("material temperature support must be ordered")
        evidence_by_source = {row.source_id: row for row in self.evidence}
        if len(evidence_by_source) != len(self.evidence):
            raise ValueError("each Evidence source_id must be unique")
        if not any(row.sha256 == self.source_sha256 for row in self.evidence):
            raise ValueError("source_sha256 must be pinned by a supplied Evidence record")
        if not any(row.sha256 == self.condition_sha256 for row in self.evidence):
            raise ValueError("condition_sha256 must be pinned by a supplied Evidence record")
        if not any(
            row.license_id == self.usage_license_id and row.sha256 == self.source_sha256
            for row in self.evidence
        ):
            raise ValueError("source Evidence must identify the declared data-use license")
        return self


class EvidenceBoundGasketViscoelasticHistoryRequest(GasketViscoelasticHistoryRequest):
    """Typed, license-aware input using the existing generalized-Maxwell solver."""

    schema_version: Literal["matintegrity.gasket_evidence_bound_prony_history.v1"] = (
        "matintegrity.gasket_evidence_bound_prony_history.v1"
    )
    material: EvidenceBoundGasketViscoelasticMaterial


def evaluate_evidence_bound_gasket_prony_history(
    request: EvidenceBoundGasketViscoelasticHistoryRequest,
) -> Calculation:
    """Validate provenance/support, then delegate mechanics to the existing solver."""
    material = request.material
    input_digest = canonical_digest(request.model_dump(mode="json"))
    common_values = {
        "request_id": request.request_id,
        "material_condition_id": material.material_condition_id,
        "physical_specimen_id": material.physical_specimen_id,
        "source_group_id": material.source_group_id,
        "source_sha256": material.source_sha256,
        "condition_sha256": material.condition_sha256,
        "provider_id": material.provider_id,
        "provider_revision": material.provider_revision,
        "temperature_K": material.temperature_K,
        "temperature_support_K": [material.temperature_support_min_K, material.temperature_support_max_K],
        "usage_license_id": material.usage_license_id,
        "evidence": [row.model_dump(mode="json") for row in material.evidence],
        "input_sha256": input_digest,
    }
    if not material.temperature_support_min_K <= material.temperature_K <= material.temperature_support_max_K:
        return Calculation(
            status="out_of_scope",
            values=common_values,
            notes=("Declared calibration temperature is outside the caller-reviewed material support interval.",),
        )
    if not all((
        material.temperature_support_reviewed,
        material.source_and_condition_lineage_reviewed,
        material.license_and_computational_use_reviewed,
    )):
        return Calculation(
            status="needs_data",
            values=common_values,
            notes=("Temperature support, source/condition lineage, license and computational-use review are required.",),
        )

    legacy_result = evaluate_gasket_viscoelastic_history(request)
    result_status = legacy_result["status"]
    if result_status not in {"computed", "out_of_scope", "needs_data"}:
        return Calculation(
            status="out_of_scope",
            values=common_values,
            notes=("The underlying generalized-Maxwell evaluator returned an unknown status.",),
        )
    response = legacy_result.get("response_history")
    values = common_values | {
        "response_history": response,
        "branch_ids": [branch.branch_id for branch in material.prony_branches],
        "strain_path_interpretation": "piecewise_linear_between_declared_knots",
        "mechanics_input_sha256": legacy_result.get("input_sha256"),
        "support_time_s": legacy_result.get("support_time_s"),
        "first_unsupported_time_s": legacy_result.get("first_unsupported_time_s"),
        "reason": legacy_result.get("reason"),
    }
    return Calculation(
        status=result_status,
        values=values,
        notes=(
            "Constitutive response is evaluated by the existing generalized-Maxwell implementation; this API adds typed Evidence, license, and temperature-support gates without duplicating the branch update.",
            "Prony parameters are caller-provided and are not fit, interpolated across temperature, or transferred to another material condition.",
        ),
    )


def specifications() -> list[ModelSpec]:
    return [
        ModelSpec(
            MODEL_ID,
            EvidenceBoundGasketViscoelasticHistoryRequest,
            evaluate_evidence_bound_gasket_prony_history,
            {
                "temperature_K": "K",
                "temperature_support_K": "K",
                "elapsed_time_s": "s",
                "compressive_strain": "1",
                "equilibrium_stress_Pa": "Pa",
                "branch_stress_Pa": "Pa",
                "total_compressive_stress_Pa": "Pa",
                "compressive_force_N": "N",
            },
            (
                "The underlying caller-calibrated generalized-Maxwell strain update is reused unchanged; this adapter adds source/license/temperature support requirements.",
                "Positive branch moduli and relaxation times, finite inputs/states and nonnegative total compressive response are required by the underlying contract and evaluator.",
                "One isothermal material condition is evaluated. No temperature interpolation or condition transfer is performed.",
                "The output is a one-dimensional constitutive stress/force history and is not a multi-bolt joint equilibrium, flange field or seal decision.",
            ),
            (SOURCE_ID, METHOD_SOURCE_ID),
            qualification="user_model",
        )
    ]
