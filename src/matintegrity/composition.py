"""Parameter profiles and ordered model composition without expression strings."""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field, TypeAdapter

from .contracts import Contract, RunContext, canonical_digest, check_finite
from .registry import ModelRegistry


class ParameterProfile(Contract):
    profile_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    parameters: dict[str, Any]
    source_id: str = Field(min_length=1)
    domain: str = Field(min_length=1)

    def run(
        self,
        registry: ModelRegistry,
        observations: dict,
        context: RunContext,
        *,
        overrides: dict | None = None,
    ):
        overrides = overrides or {}
        if not set(overrides) <= set(self.parameters):
            raise ValueError("profile overrides must name existing parameters")
        if set(observations) & set(self.parameters):
            raise ValueError("use explicit overrides to change profile parameters")
        check_finite(self.parameters)
        inputs = {**self.parameters, **overrides, **observations}
        metadata = {
            **context.metadata,
            "parameter_profile": self.model_dump(mode="json"),
            "parameter_profile_digest": canonical_digest(self.model_dump(mode="json")),
            "parameter_overrides": overrides,
        }
        return registry.run_json(
            self.model_id, _json_inputs(inputs), context.model_copy(update={"metadata": metadata}, deep=True)
        )


def _json_inputs(inputs: dict) -> str:
    native = TypeAdapter(dict[str, Any]).dump_python(inputs, mode="json")
    return json.dumps(native, ensure_ascii=False, allow_nan=False)


class OutputBinding(Contract):
    step_id: str = Field(min_length=1)
    output_key: str = Field(min_length=1)


class SatisfactionGate(Contract):
    output_key: str = Field(default="outcome", min_length=1)


class WorkflowStep(Contract):
    id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    inputs: dict[str, Any]
    bindings: dict[str, OutputBinding] = Field(default_factory=dict)
    satisfaction_gate: SatisfactionGate | None = None


def run_workflow(registry: ModelRegistry, steps: list[WorkflowStep], context: RunContext) -> dict:
    if not steps or len({step.id for step in steps}) != len(steps):
        raise ValueError("ordered workflow requires unique nonempty step identifiers")
    results = {}
    request = {
        "steps": [step.model_dump(mode="json") for step in steps],
        "context": context.model_dump(mode="json"),
    }
    request_digest = canonical_digest(request)
    for step in steps:
        inputs = dict(step.inputs)
        for target, binding in step.bindings.items():
            if target in inputs:
                raise ValueError("a workflow input cannot have both a literal and binding")
            if binding.step_id not in results:
                raise ValueError("workflow bindings must reference an earlier step")
            source = results[binding.step_id]
            if (
                source.status != "computed"
                or binding.output_key not in source.values
                or source.values[binding.output_key] is None
            ):
                return dict(
                    schema_version="matintegrity.workflow.v1",
                    status="needs_data",
                    request=request,
                    request_digest=request_digest,
                    halted_before=step.id,
                    steps={name: value.model_dump(mode="json") for name, value in results.items()},
                )
            inputs[target] = source.values[binding.output_key]
        result = registry.run_json(step.model_id, _json_inputs(inputs), context)
        results[step.id] = result
        if result.status != "computed":
            return dict(
                schema_version="matintegrity.workflow.v1",
                status=result.status,
                request=request,
                request_digest=request_digest,
                halted_after=step.id,
                steps={name: value.model_dump(mode="json") for name, value in results.items()},
            )
        if step.satisfaction_gate is not None:
            key = step.satisfaction_gate.output_key
            actual = result.values.get(key)
            if actual != "satisfied":
                outcome = "not_satisfied" if actual == "not_satisfied" else "unknown"
                return dict(
                    schema_version="matintegrity.workflow.v1",
                    status="out_of_scope" if outcome == "not_satisfied" else "needs_data",
                    request=request,
                    request_digest=request_digest,
                    halted_after=step.id,
                    policy_gate=dict(
                        output_key=key, required_outcome="satisfied", observed_value=actual, outcome=outcome
                    ),
                    steps={name: value.model_dump(mode="json") for name, value in results.items()},
                )
    return dict(
        schema_version="matintegrity.workflow.v1",
        status="computed",
        request=request,
        request_digest=request_digest,
        steps={name: value.model_dump(mode="json") for name, value in results.items()},
    )
