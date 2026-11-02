"""Versioned contracts shared by calculators and external adapters."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Positive = Annotated[float, Field(gt=0)]
Nonnegative = Annotated[float, Field(ge=0)]
Fraction = Annotated[float, Field(ge=0, le=1)]
ProbabilityMeaning = Literal[
    "conditional_first_failure_in_period",
    "point_in_time_state_probability",
    "posterior_parameter_probability",
    "model_implied_input_uncertainty_probability",
    "spatial_size_exceedance_at_one_exposure",
    "detection_given_flaw_and_procedure",
    "unscoped_event_probability",
    "fault_tree_top_event_probability",
]


def check_finite(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are not valid contract values")
    if isinstance(value, dict):
        for item in value.values():
            check_finite(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            check_finite(item)
    return value


def canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False, strict=True)


class Evidence(Contract):
    source_id: str = Field(min_length=1)
    origin: Literal["measured", "open_dataset", "model_prediction", "user_declared", "synthetic"]
    citation: str = Field(min_length=1)
    license_id: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class RunContext(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    time_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = ()
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("metadata")
    @classmethod
    def finite_metadata(cls, value):
        check_finite(value)
        json.dumps(value, allow_nan=False)
        return value


class Calculation(Contract):
    values: dict[str, Any]
    status: Literal["computed", "out_of_scope", "needs_data"] = "computed"
    notes: tuple[str, ...] = ()

    @field_validator("values")
    @classmethod
    def finite_values(cls, value):
        check_finite(value)
        json.dumps(value, allow_nan=False)
        return value


class AssessmentResult(Contract):
    schema_version: Literal["matintegrity.assessment.v1"] = "matintegrity.assessment.v1"
    model_id: str
    model_version: str
    status: Literal["computed", "out_of_scope", "needs_data"]
    inputs: dict[str, Any]
    values: dict[str, Any]
    units: dict[str, str]
    assumptions: tuple[str, ...]
    notes: tuple[str, ...]
    context: RunContext
    input_digest: str
    source_ids: tuple[str, ...]
    qualification: Literal["engineering_screening", "user_model", "data_import"]
    runtime: dict[str, str]
    probability_semantics: dict[str, ProbabilityMeaning] = Field(default_factory=dict)


class EventProbability(Contract):
    schema_version: Literal["matintegrity.event_probability.v1"] = "matintegrity.event_probability.v1"
    event_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    failure_mode: str = Field(min_length=1)
    horizon_start_s: Nonnegative
    horizon_end_s: Positive
    probability_given_survival: Fraction
    conditioning: str = Field(min_length=1)
    model_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    common_cause_groups: tuple[str, ...] = ()

    @field_validator("horizon_end_s")
    @classmethod
    def ordered_horizon(cls, value, info):
        if value <= info.data.get("horizon_start_s", 0):
            raise ValueError("event horizon must have positive duration")
        return value
