"""Solve a caller-reviewed candidate-network workflow with existing mass-action speciation."""

from __future__ import annotations

import json

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, RunContext, canonical_digest
from ..registry import ModelSpec
from .aqueous_mass_action import AqueousMassActionSystem, aqueous_mass_action_speciation
from .aqueous_candidate_network_workflow import AqueousCandidateNetworkWorkflow


class AqueousCandidateNetworkSpeciation(Contract):
    """Digest-pinned handoff from assembled candidate network to aqueous solver."""

    assessment_id: str = Field(min_length=1)
    candidate_workflow_result: AssessmentResult
    candidate_workflow_result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    computational_use_authorized: bool

    @model_validator(mode="after")
    def pinned_assembled_workflow(self):
        result = self.candidate_workflow_result
        if result.model_id != "integration.aqueous_candidate_network_workflow" or result.status != "computed":
            raise ValueError("a computed candidate-network workflow AssessmentResult is required")
        expected_input = canonical_digest({
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        })
        if result.input_digest != expected_input:
            raise ValueError("candidate-network workflow input/context digest mismatch")
        if canonical_digest(result.model_dump(mode="json")) != self.candidate_workflow_result_sha256:
            raise ValueError("candidate-network workflow result digest mismatch")
        workflow = AqueousCandidateNetworkWorkflow.model_validate_json(json.dumps(result.inputs))
        if result.values.get("workflow_sha256") != canonical_digest(workflow.model_dump(mode="json")):
            raise ValueError("candidate workflow configuration digest mismatch")
        if result.values.get("workflow_id") != workflow.workflow_id:
            raise ValueError("candidate workflow identity mismatch")
        for stage in ("enumeration", "binding", "assembly"):
            stage_result = result.values.get(stage)
            if not isinstance(stage_result, dict) or stage_result.get("status") != "computed":
                raise ValueError(f"candidate workflow {stage} must be computed")
            if canonical_digest(stage_result) != result.values.get(f"{stage}_result_sha256"):
                raise ValueError(f"candidate workflow {stage} result digest mismatch")
            expected_stage_input = canonical_digest(getattr(workflow, stage).model_dump(mode="json"))
            if result.values.get(f"{stage}_input_sha256") != expected_stage_input:
                raise ValueError(f"candidate workflow {stage} input digest mismatch")
        assembly = result.values.get("assembly")
        if not isinstance(assembly, dict) or assembly.get("status") != "computed":
            raise ValueError("candidate-network workflow must contain a computed assembly stage")
        values = assembly.get("values")
        if not isinstance(values, dict):
            raise ValueError("computed assembly stage values are missing")
        raw_system = values.get("mass_action_system")
        system_digest = values.get("mass_action_system_sha256")
        if not isinstance(raw_system, dict) or not isinstance(system_digest, str):
            raise ValueError("assembled mass-action system and digest are required")
        if canonical_digest(raw_system) != system_digest:
            raise ValueError("assembled mass-action system digest mismatch")
        system = AqueousMassActionSystem.model_validate_json(json.dumps(raw_system))
        if system.temperature_K != values.get("temperature_K"):
            raise ValueError("assembled system temperature differs from assembly lineage")
        if system.activity_standard_state != values.get("activity_standard_state"):
            raise ValueError("assembled system activity standard state differs from assembly lineage")
        if not self.computational_use_authorized:
            raise ValueError("computational use must be explicitly authorized")
        return self


def solve_aqueous_candidate_network_speciation(x: AqueousCandidateNetworkSpeciation) -> Calculation:
    """Pass only the assembled explicit system to the established speciation solver."""
    result = x.candidate_workflow_result
    assembly = result.values["assembly"]
    assembly_values = assembly["values"]
    system_payload = assembly_values["mass_action_system"]
    system = AqueousMassActionSystem.model_validate_json(json.dumps(system_payload))
    speciation = aqueous_mass_action_speciation(system)
    return Calculation(status=speciation.status, values={
        "assessment_id": x.assessment_id,
        "candidate_workflow_result_sha256": x.candidate_workflow_result_sha256,
        "candidate_workflow_input_digest": result.input_digest,
        "candidate_workflow_id": result.values.get("workflow_id"),
        "candidate_workflow_sha256": result.values.get("workflow_sha256"),
        "enumeration_input_sha256": result.values.get("enumeration_input_sha256"),
        "enumeration_result_sha256": result.values.get("enumeration_result_sha256"),
        "binding_input_sha256": result.values.get("binding_input_sha256"),
        "binding_result_sha256": result.values.get("binding_result_sha256"),
        "assembly_input_sha256": result.values.get("assembly_input_sha256"),
        "assembly_result_sha256": result.values.get("assembly_result_sha256"),
        "mass_action_system_sha256": assembly_values["mass_action_system_sha256"],
        "temperature_K": system.temperature_K,
        "activity_standard_state": system.activity_standard_state,
        "speciation_result_sha256": canonical_digest(speciation.model_dump(mode="json")),
        "speciation": speciation.model_dump(mode="json"),
        "computational_use_authorized": x.computational_use_authorized,
        "scope": "explicit single-phase aqueous mass-action solve after caller-reviewed candidate selection and assembly; no reaction discovery, phase discovery, kinetics, corrosion or material qualification",
    }, notes=(
        "The existing aqueous mass-action solver is invoked only for the exact digest-pinned system assembled upstream.",
        "AssessmentResult context is retained by ModelRegistry and can be audited as a downstream chemistry stage; caller must align subsequent state, time and temperature explicitly.",
    ))


def _validate_context(x: AqueousCandidateNetworkSpeciation, context: RunContext) -> None:
    source = x.candidate_workflow_result.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis
    ):
        raise ValueError("speciation RunContext must match candidate-workflow asset/location/time basis")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "integration.aqueous_candidate_network_speciation",
        AqueousCandidateNetworkSpeciation,
        solve_aqueous_candidate_network_speciation,
        {"temperature_K": "K", "speciation.species[].dimensionless_activity": "1",
         "speciation.species[].concentration_mol_L": "mol/L"},
        (
            "Only the exact computed mass-action system assembled by a digest-pinned candidate workflow is passed to the established aqueous speciation solver.",
            "Species inventory, reaction direction, equilibrium constants, constraints, temperature and activity standard state remain caller selected and Evidence backed upstream.",
            "This composition does not discover reactions or phases, infer kinetics, predict corrosion, or qualify material performance.",
        ),
        ("caller_composed_aqueous_candidate_network_speciation",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
