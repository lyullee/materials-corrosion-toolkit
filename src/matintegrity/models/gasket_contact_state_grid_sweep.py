"""Probe a caller-declared time grid with an external contact-state provider."""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec

_HISTORY_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class GasketContactStateGridSweep(Contract):
    """Bind a finite ordered probe grid to one source contact-history context."""

    schema_version: Literal["matintegrity.gasket_contact_state_grid_sweep.v1"] = (
        "matintegrity.gasket_contact_state_grid_sweep.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    source_contact_history: AssessmentResult
    source_contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str = Field(min_length=1)
    probe_times_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=100_000)
    maximum_probe_gap_s: Positive
    maximum_evaluations: int = Field(default=100_000, ge=2, le=100_000)
    physical_scope_and_time_basis_reviewed: bool
    provider_identity_and_configuration_reviewed: bool
    probe_grid_resolution_reviewed: bool
    computational_use_authorized: bool
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def coherent_support_and_budget(self):
        if len(self.probe_times_s) > self.maximum_evaluations:
            raise ValueError("probe grid exceeds the maximum provider evaluation count")
        if any(right <= left for left, right in zip(self.probe_times_s[:-1], self.probe_times_s[1:])):
            raise ValueError("probe times must be strictly increasing")
        gaps = [right - left for left, right in zip(self.probe_times_s[:-1], self.probe_times_s[1:])]
        if any(not math.isfinite(gap) or gap > self.maximum_probe_gap_s for gap in gaps):
            raise ValueError("a probe interval exceeds the reviewed maximum time gap")

        source = self.source_contact_history
        if source.model_id not in _HISTORY_MODELS or source.status != "computed":
            raise ValueError("a computed supported flange contact history is required")
        if canonical_digest(source.model_dump(mode="json")) != self.source_contact_history_sha256:
            raise ValueError("source contact-history digest mismatch")
        expected_input = canonical_digest({
            "model_id": source.model_id,
            "model_version": source.model_version,
            "inputs": source.inputs,
            "context": source.context.model_dump(mode="json"),
        })
        if source.input_digest != expected_input:
            raise ValueError("source contact-history input/context digest mismatch")
        if source.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("source contact history does not match the declared physical scope")
        if source.units.get("time_history[].time_s") != "s":
            raise ValueError("source contact history must declare seconds")
        history = source.values.get("time_history")
        if not isinstance(history, list) or len(history) < 2:
            raise ValueError("source contact history needs at least two computed knots")
        source_times = []
        for row in history:
            if not isinstance(row, dict) or row.get("status") not in (None, "computed"):
                raise ValueError("source contact history contains an incomplete knot")
            time_s = row.get("time_s")
            if (isinstance(time_s, bool) or not isinstance(time_s, (float, int))
                    or not math.isfinite(time_s) or time_s < 0):
                raise ValueError("source contact history contains an invalid time")
            field = row.get("response_field")
            if not isinstance(field, list):
                raise ValueError("source contact history knot has no response field")
            matches = [entry for entry in field if isinstance(entry, dict) and entry.get("node_id") == self.node_id]
            state = matches[0].get("contact_state") if len(matches) == 1 else None
            if not isinstance(state, str) or state not in {"open", "closed"}:
                raise ValueError("the requested node must have one recognized state at every source knot")
            source_times.append(float(time_s))
        if any(right <= left for left, right in zip(source_times[:-1], source_times[1:])):
            raise ValueError("source contact-history knots must increase strictly")
        if self.probe_times_s[0] != source_times[0] or self.probe_times_s[-1] != source_times[-1]:
            raise ValueError("probe grid endpoints must match the exact source-history support")
        return self


class ExternalContactStateGridQuery(Contract):
    """Exact time-grid query sent to a caller-owned external solver callback."""

    schema_version: Literal["matintegrity.external_contact_state_grid_query.v1"] = (
        "matintegrity.external_contact_state_grid_query.v1"
    )
    assessment_id: str
    source_contact_history_sha256: str
    physical_scope_id: str
    asset_id: str
    location_id: str
    time_basis: str
    context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str
    query_time_s: float = Field(ge=0)
    provider_id: str
    provider_revision: str
    provider_configuration_sha256: str
    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_digest(self):
        if not math.isfinite(self.query_time_s):
            raise ValueError("provider query time must be finite")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"query_sha256"}))
        if self.query_sha256 != expected:
            raise ValueError("provider query digest mismatch")
        return self


class ExternalContactStateGridResponse(Contract):
    """One provider state observation bound to its exact query and context."""

    schema_version: Literal["matintegrity.external_contact_state_grid_response.v1"] = (
        "matintegrity.external_contact_state_grid_response.v1"
    )
    query_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    physical_scope_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    context_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str = Field(min_length=1)
    time_s: float = Field(ge=0)
    contact_state: Literal["open", "closed"]
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    result_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def verify_response_digest(self):
        if not math.isfinite(self.time_s):
            raise ValueError("provider response time must be finite")
        expected = canonical_digest(self.model_dump(mode="json", exclude={"result_sha256"}))
        if self.result_sha256 != expected:
            raise ValueError("provider response digest mismatch")
        return self


ContactStateGridProvider = Callable[[ExternalContactStateGridQuery], ExternalContactStateGridResponse | dict]


def evaluate_gasket_contact_state_grid_sweep(
    request: GasketContactStateGridSweep,
    *,
    contact_state_provider: ContactStateGridProvider,
) -> Calculation:
    """Evaluate every caller grid time and report only transitions visible in those samples."""

    source = request.source_contact_history
    context_dict = source.context.model_dump(mode="json")
    context_digest = canonical_digest(context_dict)
    base = {
        "assessment_id": request.assessment_id,
        "asset_id": source.context.asset_id,
        "location_id": source.context.location_id,
        "time_basis": source.context.time_basis,
        "physical_scope_id": request.physical_scope_id,
        "source_model_id": source.model_id,
        "source_contact_history_sha256": request.source_contact_history_sha256,
        "source_input_digest": source.input_digest,
        "node_id": request.node_id,
        "provider_id": request.provider_id,
        "provider_revision": request.provider_revision,
        "provider_configuration_sha256": request.provider_configuration_sha256,
        "context_sha256": context_digest,
        "probe_times_s": list(request.probe_times_s),
        "maximum_probe_gap_s": request.maximum_probe_gap_s,
        "observed_transition_times_claimed": False,
        "hidden_transitions_excluded": False,
        "contact_completeness_claimed": False,
        "seal_acceptance_or_leakage_inferred": False,
        "failure_probability_inferred": False,
    }
    reviews = {
        "physical_scope_and_time_basis_reviewed": request.physical_scope_and_time_basis_reviewed,
        "provider_identity_and_configuration_reviewed": request.provider_identity_and_configuration_reviewed,
        "probe_grid_resolution_reviewed": request.probe_grid_resolution_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing_reviews = [name for name, reviewed in reviews.items() if not reviewed]
    if missing_reviews:
        return Calculation(status="needs_data", values=base | {
            "missing_reviews": missing_reviews,
            "evaluation_prefix": [],
            "completed_evaluation_count": 0,
            "first_failure": {"reason": "required_review_missing"},
        })
    if not callable(contact_state_provider):
        return Calculation(status="needs_data", values=base | {
            "evaluation_prefix": [],
            "completed_evaluation_count": 0,
            "first_failure": {"reason": "provider_callback_not_callable"},
        })

    samples: list[dict] = []
    for index, time_s in enumerate(request.probe_times_s):
        query_body = {
            "schema_version": "matintegrity.external_contact_state_grid_query.v1",
            "assessment_id": request.assessment_id,
            "source_contact_history_sha256": request.source_contact_history_sha256,
            "physical_scope_id": request.physical_scope_id,
            "asset_id": source.context.asset_id,
            "location_id": source.context.location_id,
            "time_basis": source.context.time_basis,
            "context_sha256": context_digest,
            "node_id": request.node_id,
            "query_time_s": float(time_s),
            "provider_id": request.provider_id,
            "provider_revision": request.provider_revision,
            "provider_configuration_sha256": request.provider_configuration_sha256,
        }
        query = ExternalContactStateGridQuery(**(query_body | {"query_sha256": canonical_digest(query_body)}))
        try:
            response = ExternalContactStateGridResponse.model_validate(contact_state_provider(query))
        except Exception as exc:
            return _incomplete_sweep(base, samples, {
                "reason": "provider_call_or_response_validation_failed",
                "probe_index": index,
                "query_time_s": float(time_s),
                "query_sha256": query.query_sha256,
                "error_type": type(exc).__name__,
            })
        problem = _response_problem(request, query, response)
        if problem:
            return _incomplete_sweep(base, samples, problem | {
                "probe_index": index,
                "query_time_s": float(time_s),
                "query_sha256": query.query_sha256,
            })
        samples.append({
            "probe_index": index,
            "time_s": float(time_s),
            "contact_state": response.contact_state,
            "query_sha256": query.query_sha256,
            "provider_response_sha256": response.result_sha256,
            "evidence": [row.model_dump(mode="json") for row in response.evidence],
        })

    transitions = []
    for left, right in zip(samples[:-1], samples[1:], strict=True):
        if left["contact_state"] == right["contact_state"]:
            continue
        transitions.append({
            "node_id": request.node_id,
            "from_state": left["contact_state"],
            "to_state": right["contact_state"],
            "transition_kind": "opening" if left["contact_state"] == "closed" else "closing",
            "lower_time_s": left["time_s"],
            "upper_time_s": right["time_s"],
            "bracket_width_s": right["time_s"] - left["time_s"],
            "lower_query_sha256": left["query_sha256"],
            "upper_query_sha256": right["query_sha256"],
            "event_time_s": None,
        })
    return Calculation(values=base | {
        "state_samples": samples,
        "observed_transition_brackets": transitions,
        "observed_transition_count": len(transitions),
        "multiple_transitions_observed": len(transitions) > 1,
        "unobserved_transitions_may_exist_inside_probe_intervals": True,
        "solver_evaluation_count": len(samples),
        "event_time_method": "no root solve; only caller-grid state-change brackets are reported",
        "meaning": "finite provider state sweep at caller-selected times; it does not establish transition completeness",
    }, notes=(
        "Every reported transition is a change between adjacent returned provider states on the caller-declared finite time grid.",
        "Transitions may be missed between probe times; the maximum probe gap is a caller-selected resolution, not an error bound or completeness proof.",
        "The callback provider supplies the contact-state calculations; this package does not implement FE response generation.",
    ))


def _response_problem(
    request: GasketContactStateGridSweep,
    query: ExternalContactStateGridQuery,
    response: ExternalContactStateGridResponse,
) -> dict | None:
    if response.query_sha256 != query.query_sha256:
        return {"reason": "provider_query_digest_mismatch"}
    if response.source_contact_history_sha256 != request.source_contact_history_sha256:
        return {"reason": "provider_source_history_digest_mismatch"}
    if response.provider_id != request.provider_id:
        return {"reason": "provider_identity_mismatch"}
    if response.provider_revision != request.provider_revision:
        return {"reason": "provider_revision_mismatch"}
    if response.provider_configuration_sha256 != request.provider_configuration_sha256:
        return {"reason": "provider_configuration_digest_mismatch"}
    if response.node_id != request.node_id:
        return {"reason": "provider_node_identity_mismatch"}
    if response.time_s != query.query_time_s:
        return {"reason": "provider_time_does_not_match_exact_query"}
    if (response.physical_scope_id != request.physical_scope_id
            or response.asset_id != query.asset_id
            or response.location_id != query.location_id
            or response.time_basis != query.time_basis
            or response.context_sha256 != query.context_sha256):
        return {"reason": "provider_response_context_mismatch"}
    if not any(item.source_id == request.provider_id for item in response.evidence):
        return {"reason": "provider_evidence_missing_declared_provider_identity"}
    return None


def _incomplete_sweep(base: dict, samples: list[dict], failure: dict) -> Calculation:
    transitions = []
    for left, right in zip(samples[:-1], samples[1:], strict=True):
        if left["contact_state"] != right["contact_state"]:
            transitions.append({
                "node_id": base["node_id"],
                "from_state": left["contact_state"],
                "to_state": right["contact_state"],
                "transition_kind": "opening" if left["contact_state"] == "closed" else "closing",
                "lower_time_s": left["time_s"],
                "upper_time_s": right["time_s"],
                "bracket_width_s": right["time_s"] - left["time_s"],
                "lower_query_sha256": left["query_sha256"],
                "upper_query_sha256": right["query_sha256"],
                "event_time_s": None,
            })
    return Calculation(status="needs_data", values=base | {
        "state_sample_prefix": samples,
        "observed_transition_brackets_in_prefix": transitions,
        "completed_evaluation_count": len(samples),
        "first_failure": failure,
        "sweep_complete": False,
        "event_time_s": None,
    }, notes=(
        "The sweep stopped at the first failed provider query; prior valid state samples are retained as a prefix.",
        "No transition completeness or exact event time is claimed.",
    ))


def _validate_context(request: GasketContactStateGridSweep, context: RunContext) -> None:
    source = request.source_contact_history.context
    if (context.asset_id, context.location_id, context.time_basis) != (
        source.asset_id, source.location_id, source.time_basis,
    ):
        raise ValueError("sweep RunContext must match the source contact-history context")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_contact_state_grid_sweep",
        GasketContactStateGridSweep,
        evaluate_gasket_contact_state_grid_sweep,
        {
            "probe_times_s[]": "s",
            "maximum_probe_gap_s": "s",
            "state_samples[].time_s": "s",
            "observed_transition_brackets[].lower_time_s": "s",
            "observed_transition_brackets[].upper_time_s": "s",
            "observed_transition_brackets[].bracket_width_s": "s",
        },
        (
            "Query a caller-declared finite time grid through an explicit external contact-state provider and preserve every provider response digest and Evidence.",
            "Only changes visible between adjacent grid times are reported; the provider is not implemented here and hidden transitions, exact event times, seal performance and acceptance are not inferred.",
        ),
        ("caller_external_flange_contact_state_provider",),
        qualification="user_model",
        context_validator=_validate_context,
        runtime_dependency_names=("contact_state_provider",),
    )]
