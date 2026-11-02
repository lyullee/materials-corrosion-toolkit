"""Independent-seed subset-simulation repeatability summaries."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .contracts import Contract, canonical_digest
from .reliability_sampling import SubsetSimulationRequest, SubsetSimulationResult, run_subset_simulation


class SubsetReplicateRequest(Contract):
    analysis_id: str = Field(min_length=1)
    template: SubsetSimulationRequest
    seeds: tuple[int, ...] = Field(min_length=3, max_length=100)
    target_relative_standard_error: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def distinct_seeds(self):
        if len(set(self.seeds)) != len(self.seeds) or any(
            seed < 0 or seed > 2**64 - 1 for seed in self.seeds
        ):
            raise ValueError("replicate seeds must be unique unsigned 64-bit integers")
        return self


class SubsetReplicateResult(Contract):
    analysis_id: str
    request_sha256: str
    runs: tuple[SubsetSimulationResult, ...]
    complete_run_count: int
    mean_probability: float | None
    between_run_standard_deviation: float | None
    standard_error_of_replicate_mean: float | None
    coefficient_of_variation: float | None
    status: Literal["computed", "needs_data"]
    log_mean_probability: float | None
    log_standard_error_of_replicate_mean: float | None
    relative_standard_error_of_replicate_mean: float | None
    declared_precision_target_met: bool | None
    uncertainty_basis: str


def run_subset_replicates(
    limit_state: Callable[[np.ndarray], float], request: SubsetReplicateRequest
) -> SubsetReplicateResult:
    runs = tuple(
        run_subset_simulation(limit_state, task.request) for task in build_subset_replicate_tasks(request)
    )
    return summarize_subset_replicates(request, runs)


def summarize_subset_replicates(
    request: SubsetReplicateRequest, runs: tuple[SubsetSimulationResult, ...]
) -> SubsetReplicateResult:
    tasks = build_subset_replicate_tasks(request)
    if len(runs) != len(tasks):
        raise ValueError("all subset replicates must be supplied exactly once")
    for task, result in zip(tasks, runs, strict=True):
        request_fields = task.request.model_dump(mode="json")
        result_fields = result.model_dump(mode="json")
        for key in request_fields.keys() & result_fields.keys() - {"schema_version"}:
            if request_fields[key] != result_fields[key]:
                raise ValueError(f"replicate result differs from its requested {key}")
        if result.status == "computed" and (
            result.probability_estimate is None or result.log_probability_estimate is None
        ):
            raise ValueError("completed replicate must retain probability and log probability")
        if result.status == "computed":
            log_probability = result.log_probability_estimate
            if log_probability > 0 or not math.isclose(
                result.probability_estimate,
                math.exp(log_probability),
                rel_tol=1e-10,
                abs_tol=math.ulp(0.0) * max(result.level_count, 1),
            ):
                raise ValueError("replicate probability and log probability are inconsistent")
        if result.level_count != len(result.levels):
            raise ValueError("replicate level count differs from its retained level records")
    if len({result.numpy_version for result in runs}) != 1:
        raise ValueError("replicates must use one recorded NumPy version")
    complete = [
        run.probability_estimate
        for run in runs
        if run.status == "computed" and run.probability_estimate is not None
    ]
    mean = sd = standard_error = cv = None
    log_mean = log_se = relative_se = None
    precision_met = None
    # Failed replicates are never silently dropped from the numerical summary.
    if len(complete) == len(runs):
        mean = math.fsum(complete) / len(complete)
        sd = math.sqrt(math.fsum((value - mean) ** 2 for value in complete) / (len(complete) - 1))
        standard_error = sd / math.sqrt(len(complete))
        cv = sd / mean if mean > 0 else None
        logs = [run.log_probability_estimate for run in runs]
        if all(value is not None for value in logs):
            scale = max(logs)
            normalized = [math.exp(value - scale) for value in logs]
            normalized_mean = math.fsum(normalized) / len(normalized)
            normalized_sd = math.sqrt(
                math.fsum((value - normalized_mean) ** 2 for value in normalized) / (len(normalized) - 1)
            )
            log_mean = scale + math.log(normalized_mean)
            relative_se = normalized_sd / (math.sqrt(len(normalized)) * normalized_mean)
            cv = normalized_sd / normalized_mean
            log_se = (
                scale + math.log(normalized_sd / math.sqrt(len(normalized))) if normalized_sd > 0 else None
            )
            if request.target_relative_standard_error is not None:
                precision_met = relative_se <= request.target_relative_standard_error
    return SubsetReplicateResult(
        analysis_id=request.analysis_id,
        request_sha256=canonical_digest(request.model_dump(mode="json")),
        runs=runs,
        complete_run_count=len(complete),
        mean_probability=mean,
        between_run_standard_deviation=sd,
        standard_error_of_replicate_mean=standard_error,
        coefficient_of_variation=cv,
        status="computed" if len(complete) == len(runs) else "needs_data",
        log_mean_probability=log_mean,
        log_standard_error_of_replicate_mean=log_se,
        relative_standard_error_of_replicate_mean=relative_se,
        declared_precision_target_met=precision_met,
        uncertainty_basis="Independent random-stream replicate dispersion only; no bias, physical-model uncertainty, confidence interval or convergence certification.",
    )


class SubsetReplicateTask(Contract):
    task_id: str = Field(min_length=1)
    parent_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    request: SubsetSimulationRequest

    @model_validator(mode="after")
    def input_digest(self):
        if canonical_digest(self.request.model_dump(mode="json")) != self.input_sha256:
            raise ValueError("replicate task input digest differs from its request")
        return self


class SubsetReplicateTaskResult(Contract):
    task_id: str = Field(min_length=1)
    parent_request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    result: SubsetSimulationResult

    @model_validator(mode="after")
    def result_digest(self):
        if canonical_digest(self.result.model_dump(mode="json")) != self.result_sha256:
            raise ValueError("replicate result digest differs from its contents")
        return self


def build_subset_replicate_tasks(request: SubsetReplicateRequest) -> tuple[SubsetReplicateTask, ...]:
    """Build independent seed tasks without sampling or calling a limit-state evaluator."""
    parent_digest = canonical_digest(request.model_dump(mode="json"))
    tasks = []
    for index, seed in enumerate(request.seeds):
        payload = request.template.model_dump(mode="python")
        payload.update(random_seed=seed, estimate_id=f"{request.template.estimate_id}:replicate:{index}")
        inputs = SubsetSimulationRequest.model_validate(payload)
        tasks.append(
            SubsetReplicateTask(
                task_id=f"{request.analysis_id}:replicate:{index}",
                parent_request_sha256=parent_digest,
                input_sha256=canonical_digest(inputs.model_dump(mode="json")),
                request=inputs,
            )
        )
    return tuple(tasks)


def run_subset_replicate_task(
    limit_state: Callable[[np.ndarray], float], task: SubsetReplicateTask
) -> SubsetReplicateTaskResult:
    result = run_subset_simulation(limit_state, task.request)
    return SubsetReplicateTaskResult(
        task_id=task.task_id,
        parent_request_sha256=task.parent_request_sha256,
        input_sha256=task.input_sha256,
        result_sha256=canonical_digest(result.model_dump(mode="json")),
        result=result,
    )


def reduce_subset_replicate_tasks(
    request: SubsetReplicateRequest, results: tuple[SubsetReplicateTaskResult, ...]
) -> SubsetReplicateResult:
    """Reorder by the exact manifest; missing/duplicate/mixed-request results are rejected."""
    tasks = build_subset_replicate_tasks(request)
    by_id = {row.task_id: row for row in results}
    if len(by_id) != len(results) or set(by_id) != {task.task_id for task in tasks}:
        raise ValueError("replicate results must cover the exact unique task manifest")
    ordered = []
    for task in tasks:
        row = by_id[task.task_id]
        if row.parent_request_sha256 != task.parent_request_sha256 or row.input_sha256 != task.input_sha256:
            raise ValueError("replicate task parent or input digest differs from manifest")
        ordered.append(row.result)
    return summarize_subset_replicates(request, tuple(ordered))
