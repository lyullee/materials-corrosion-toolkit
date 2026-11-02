"""Threshold-event audit for one node in a computed gasket contact history."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import AssessmentResult, Calculation, Contract, Evidence, Nonnegative, RunContext, canonical_digest
from ..registry import ModelSpec

_HISTORY_MODELS = {
    "fabrication.flange_viscoelastic_contact_history",
    "fabrication.flange_nonlinear_viscoelastic_contact_history",
}


class GasketContactPressureWindowEvents(Contract):
    """Audit exact-knot pressure excursions against a caller-declared window."""

    schema_version: Literal["matintegrity.gasket_contact_pressure_window_events.v1"] = (
        "matintegrity.gasket_contact_pressure_window_events.v1"
    )
    assessment_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    contact_history: AssessmentResult
    contact_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    node_id: str = Field(min_length=1)
    minimum_contact_pressure_Pa: Nonnegative
    maximum_contact_pressure_Pa: Nonnegative | None = None
    criterion_provider_id: str = Field(min_length=1)
    criterion_provider_revision: str = Field(min_length=1)
    criterion_record_id: str = Field(min_length=1)
    criterion_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    criterion_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_rights_evidence: tuple[Evidence, ...] = Field(min_length=1)
    usage_license_id: str = Field(min_length=1)
    physical_scope_and_time_basis_reviewed: bool
    criterion_applicability_reviewed: bool
    interpolation_basis_reviewed: bool
    pressure_basis_and_units_reviewed: bool
    usage_rights_reviewed: bool
    computational_use_authorized: bool

    @model_validator(mode="after")
    def coherent_history(self):
        result = self.contact_history
        if canonical_digest(result.model_dump(mode="json")) != self.contact_history_sha256:
            raise ValueError("contact history digest does not match the AssessmentResult")
        if result.status != "computed" or result.model_id not in _HISTORY_MODELS:
            raise ValueError("a computed supported flange contact history is required")
        payload = {
            "model_id": result.model_id,
            "model_version": result.model_version,
            "inputs": result.inputs,
            "context": result.context.model_dump(mode="json"),
        }
        if canonical_digest(payload) != result.input_digest:
            raise ValueError("contact history input/context digest does not verify")
        if result.inputs.get("physical_scope_id") != self.physical_scope_id:
            raise ValueError("contact history physical scope does not match the requested scope")
        if self.maximum_contact_pressure_Pa is not None and self.maximum_contact_pressure_Pa < self.minimum_contact_pressure_Pa:
            raise ValueError("pressure-window maximum must not be below its minimum")
        basis = {
            "criterion_provider_id": self.criterion_provider_id,
            "criterion_provider_revision": self.criterion_provider_revision,
            "criterion_record_id": self.criterion_record_id,
            "physical_scope_id": self.physical_scope_id,
            "node_id": self.node_id,
            "minimum_contact_pressure_Pa": self.minimum_contact_pressure_Pa,
            "maximum_contact_pressure_Pa": self.maximum_contact_pressure_Pa,
        }
        if canonical_digest(basis) != self.criterion_sha256:
            raise ValueError("criterion digest does not match node, scope and bounds")
        if not any(row.source_id == self.criterion_provider_id for row in self.criterion_evidence):
            raise ValueError("criterion provider must be represented by declared Evidence")
        if not any(row.license_id == self.usage_license_id for row in self.usage_rights_evidence):
            raise ValueError("usage rights Evidence must identify the declared license")
        return self


def _outside_intervals(times: list[float], pressures: list[float], bound: float, *, below: bool) -> list[dict[str, float | bool]]:
    """Exact crossing times for a piecewise-linear signal and one strict bound."""
    margins = [pressure - bound for pressure in pressures]
    is_outside = (lambda value: value < 0.0) if below else (lambda value: value > 0.0)
    left_censored = is_outside(margins[0])
    active_start = times[0] if left_censored else None
    intervals: list[dict[str, float | bool]] = []
    for i, (t0, t1) in enumerate(zip(times[:-1], times[1:], strict=True)):
        d0, d1 = margins[i], margins[i + 1]
        outside0, outside1 = is_outside(d0), is_outside(d1)
        crossing: float | None = None
        if (d0 < 0.0 < d1) or (d1 < 0.0 < d0):
            # Magnitude-ratio form avoids overflow in d1-d0.
            a, b = abs(d0), abs(d1)
            if a >= b:
                fraction = 1.0 / (1.0 + b / a)
            else:
                ratio = a / b
                fraction = ratio / (1.0 + ratio)
            crossing = t0 + (t1 - t0) * fraction
        if not outside0 and outside1:
            active_start = t0 if d0 == 0.0 else (crossing if crossing is not None else t1)
            left_censored = False
        elif outside0 and not outside1:
            end = t1 if d1 == 0.0 else (crossing if crossing is not None else t1)
            start = active_start if active_start is not None else t0
            intervals.append({
                "start_time_s": start,
                "end_time_s": end,
                "duration_s": end - start,
                "left_censored": left_censored,
                "right_censored": False,
            })
            active_start = None
            left_censored = False
    if active_start is not None:
        end = times[-1]
        intervals.append({
            "start_time_s": active_start,
            "end_time_s": end,
            "duration_s": end - active_start,
            "left_censored": left_censored,
            "right_censored": True,
        })
    return intervals


def audit_gasket_contact_pressure_window_events(request: GasketContactPressureWindowEvents) -> Calculation:
    result = request.contact_history
    values = result.values
    base = {
        "assessment_id": request.assessment_id,
        "physical_scope_id": request.physical_scope_id,
        "contact_history_model_id": result.model_id,
        "contact_history_sha256": request.contact_history_sha256,
        "contact_history_input_digest": result.input_digest,
        "node_id": request.node_id,
        "minimum_contact_pressure_Pa": request.minimum_contact_pressure_Pa,
        "maximum_contact_pressure_Pa": request.maximum_contact_pressure_Pa,
        "criterion_provider_id": request.criterion_provider_id,
        "criterion_provider_revision": request.criterion_provider_revision,
        "criterion_record_id": request.criterion_record_id,
        "criterion_sha256": request.criterion_sha256,
        "usage_license_id": request.usage_license_id,
        "criterion_evidence": [row.model_dump(mode="json") for row in request.criterion_evidence],
        "usage_rights_evidence": [row.model_dump(mode="json") for row in request.usage_rights_evidence],
        "contact_history_context": result.context.model_dump(mode="json"),
        "seal_acceptance_or_leakage_inferred": False,
    }
    reviews = {
        "physical_scope_and_time_basis_reviewed": request.physical_scope_and_time_basis_reviewed,
        "criterion_applicability_reviewed": request.criterion_applicability_reviewed,
        "interpolation_basis_reviewed": request.interpolation_basis_reviewed,
        "pressure_basis_and_units_reviewed": request.pressure_basis_and_units_reviewed,
        "usage_rights_reviewed": request.usage_rights_reviewed,
        "computational_use_authorized": request.computational_use_authorized,
    }
    missing = [key for key, approved in reviews.items() if not approved]
    if missing:
        return Calculation(status="needs_data", values=base | {"missing_reviews": missing, "review_flags": reviews})
    if result.units.get("time_history[].response_field[].mean_contact_pressure_Pa") != "Pa":
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "upstream_pressure_unit_not_explicitly_pascal"})
    history = values.get("time_history")
    if not isinstance(history, list) or len(history) < 2:
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "upstream_time_history_missing_or_too_short"})
    times: list[float] = []
    pressures: list[float] = []
    for index, row in enumerate(history):
        if not isinstance(row, dict) or row.get("status") not in (None, "computed"):
            return Calculation(status="needs_data", values=base | {"out_of_scope_reason": "incomplete_contact_history_prefix", "failed_knot_index": index})
        time_s = row.get("time_s")
        field = row.get("response_field")
        if isinstance(time_s, bool) or not isinstance(time_s, (float, int)) or not math.isfinite(time_s) or time_s < 0:
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "invalid_history_time", "failed_knot_index": index})
        if not isinstance(field, list):
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "contact_field_missing", "failed_knot_index": index})
        selected = [entry for entry in field if isinstance(entry, dict) and entry.get("node_id") == request.node_id]
        if len(selected) != 1:
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "selected_node_missing_or_duplicated", "failed_knot_index": index, "node_match_count": len(selected)})
        pressure = selected[0].get("mean_contact_pressure_Pa")
        if isinstance(pressure, bool) or not isinstance(pressure, (float, int)) or not math.isfinite(pressure) or pressure < 0:
            return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "invalid_contact_pressure", "failed_knot_index": index})
        times.append(float(time_s))
        pressures.append(float(pressure))
    if any(t1 <= t0 for t0, t1 in zip(times[:-1], times[1:], strict=True)):
        return Calculation(status="out_of_scope", values=base | {"out_of_scope_reason": "contact_history_times_not_strictly_increasing"})

    below = _outside_intervals(times, pressures, request.minimum_contact_pressure_Pa, below=True)
    above = [] if request.maximum_contact_pressure_Pa is None else _outside_intervals(
        times, pressures, request.maximum_contact_pressure_Pa, below=False,
    )
    return Calculation(values=base | {
        "time_points_s": times,
        "pressure_points_Pa": pressures,
        "below_minimum_intervals": below,
        "below_minimum_duration_s": math.fsum(float(row["duration_s"]) for row in below),
        "above_maximum_intervals": above,
        "above_maximum_duration_s": math.fsum(float(row["duration_s"]) for row in above),
        "interpolation": "piecewise_linear_between_computed_contact_knots",
        "outside_window_is_seal_failure": False,
        "leakage_or_failure_probability_inferred": False,
    }, notes=(
        "The output describes caller-declared pressure-window excursion time for one node using exact computed contact knots and reviewed linear interpolation.",
        "It does not determine gasket sealing acceptance, leakage, failure causation, probability, or qualification.",
    ))


def _validate_context(request: GasketContactPressureWindowEvents, context: RunContext) -> None:
    source = request.contact_history.context
    if (context.asset_id, context.location_id, context.time_basis) != (source.asset_id, source.location_id, source.time_basis):
        raise ValueError("gasket contact event RunContext must match the source contact history")


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        "fabrication.gasket_contact_pressure_window_events",
        GasketContactPressureWindowEvents,
        audit_gasket_contact_pressure_window_events,
        {
            "minimum_contact_pressure_Pa": "Pa",
            "maximum_contact_pressure_Pa": "Pa",
            "time_points_s[]": "s",
            "below_minimum_duration_s": "s",
            "above_maximum_duration_s": "s",
        },
        (
            "Audit exact computed gasket contact-pressure knots against a caller-declared node pressure window using reviewed piecewise-linear interpolation.",
            "Pressure-window excursion time is descriptive and does not establish seal acceptance, leakage, failure causation, probability, or qualification.",
        ),
        ("caller_gasket_contact_pressure_time_window_event_audit",),
        qualification="user_model",
        context_validator=_validate_context,
    )]
