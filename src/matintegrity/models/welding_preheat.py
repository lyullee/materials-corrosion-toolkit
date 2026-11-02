"""Weld preheat and interpass records checked against caller-owned procedure envelopes."""

from __future__ import annotations

from fractions import Fraction
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, canonical_digest
from ..registry import ModelSpec
from .engineering_correlations import CorrelationRequest


class DeclaredPreheatProcedureEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    consumable_condition_id: str = Field(min_length=1)
    hydrogen_control_descriptor: str = Field(min_length=1)
    restraint_descriptor: str = Field(min_length=1)
    minimum_thickness_m: Positive
    maximum_thickness_m: Positive
    minimum_net_heat_input_J_m: Positive
    maximum_net_heat_input_J_m: Positive
    minimum_required_preheat_temperature_K: Positive
    maximum_supported_interpass_temperature_K: Positive
    minimum_supported_interpass_temperature_K: Positive | None = None
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_ranges(self):
        for lower, upper, name in (
            (self.minimum_thickness_m, self.maximum_thickness_m, "thickness"),
            (self.minimum_net_heat_input_J_m, self.maximum_net_heat_input_J_m, "heat-input"),
        ):
            if upper < lower:
                raise ValueError(f"preheat-envelope {name} bounds must be ordered")
        if (
            self.minimum_supported_interpass_temperature_K is not None
            and self.minimum_supported_interpass_temperature_K
            > self.maximum_supported_interpass_temperature_K
        ):
            raise ValueError("declared interpass bounds must be ordered")
        return self


class WeldPreheatProcedureAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    weld_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    joint_configuration_id: str = Field(min_length=1)
    welding_process_id: str = Field(min_length=1)
    consumable_condition_id: str = Field(min_length=1)
    hydrogen_control_descriptor: str = Field(min_length=1)
    restraint_descriptor: str = Field(min_length=1)
    governing_thickness_m: Positive
    net_heat_input_J_m: Positive
    minimum_recorded_preheat_temperature_K: Positive
    maximum_recorded_interpass_temperature_K: Positive
    below_preheat_duration_s: Nonnegative
    above_interpass_duration_s: Nonnegative
    minimum_recorded_interpass_temperature_K: Positive | None = None
    below_interpass_duration_s: Nonnegative | None = None
    candidate_envelopes: tuple[DeclaredPreheatProcedureEnvelope, ...] = Field(min_length=1)
    material_and_joint_identity_reviewed: bool
    consumable_and_hydrogen_control_reviewed: bool
    restraint_reviewed: bool
    thickness_and_heat_input_reviewed: bool
    temperature_records_reviewed: bool
    procedure_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_envelopes(self):
        if (
            self.minimum_recorded_interpass_temperature_K is not None
            and self.minimum_recorded_interpass_temperature_K > self.maximum_recorded_interpass_temperature_K
        ):
            raise ValueError("recorded interpass extrema must be ordered")
        identifiers = [row.envelope_id for row in self.candidate_envelopes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("preheat envelope identifiers must be unique")
        return self


def _identity(envelope: DeclaredPreheatProcedureEnvelope):
    return (
        envelope.material_condition_id,
        envelope.joint_configuration_id,
        envelope.welding_process_id,
        envelope.consumable_condition_id,
        envelope.hydrogen_control_descriptor,
        envelope.restraint_descriptor,
    )


def weld_preheat_procedure_envelope(x: WeldPreheatProcedureAssessment) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_and_joint_identity_reviewed",
            "consumable_and_hydrogen_control_reviewed",
            "restraint_reviewed",
            "thickness_and_heat_input_reviewed",
            "temperature_records_reviewed",
            "procedure_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    target_identity = (
        x.material_condition_id,
        x.joint_configuration_id,
        x.welding_process_id,
        x.consumable_condition_id,
        x.hydrogen_control_descriptor,
        x.restraint_descriptor,
    )
    identity_matches = [row for row in x.candidate_envelopes if _identity(row) == target_identity]
    supported = [
        row
        for row in identity_matches
        if row.minimum_thickness_m <= x.governing_thickness_m <= row.maximum_thickness_m
        and row.minimum_net_heat_input_J_m <= x.net_heat_input_J_m <= row.maximum_net_heat_input_J_m
    ]
    if missing_reviews or not identity_matches or len(supported) > 1:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in identity_matches],
                "supported_envelope_ids": [row.envelope_id for row in supported],
                "missing_reviews": missing_reviews,
            },
            notes=("A unique reviewed caller-owned procedure envelope is required.",),
        )
    if not supported:
        return Calculation(
            status="out_of_scope",
            values={
                "assessment_id": x.assessment_id,
                "identity_matching_envelope_ids": [row.envelope_id for row in identity_matches],
                "supported_envelope_ids": [],
                "missing_reviews": missing_reviews,
            },
            notes=("Thickness or heat input is outside the matching procedure envelope.",),
        )

    envelope = supported[0]
    if envelope.minimum_supported_interpass_temperature_K is not None and (
        x.minimum_recorded_interpass_temperature_K is None or x.below_interpass_duration_s is None
    ):
        return Calculation(
            status="needs_data",
            values={"assessment_id": x.assessment_id, "selected_envelope_id": envelope.envelope_id},
            notes=(
                "Declared interpass minimum requires its own measured minimum and excursion duration; preheat is not substituted.",
            ),
        )
    minimum_interpass_margin = (
        None
        if envelope.minimum_supported_interpass_temperature_K is None
        else x.minimum_recorded_interpass_temperature_K - envelope.minimum_supported_interpass_temperature_K
    )
    preheat_margin = (
        x.minimum_recorded_preheat_temperature_K - envelope.minimum_required_preheat_temperature_K
    )
    interpass_margin = (
        envelope.maximum_supported_interpass_temperature_K - x.maximum_recorded_interpass_temperature_K
    )
    record_within = (
        preheat_margin >= 0
        and interpass_margin >= 0
        and x.below_preheat_duration_s == 0
        and x.above_interpass_duration_s == 0
        and (
            minimum_interpass_margin is None
            or (minimum_interpass_margin >= 0 and x.below_interpass_duration_s == 0)
        )
    )
    return Calculation(
        values={
            "assessment_id": x.assessment_id,
            "selected_envelope_id": envelope.envelope_id,
            "preheat_temperature_margin_K": preheat_margin,
            "interpass_temperature_margin_K": interpass_margin,
            "below_preheat_duration_s": x.below_preheat_duration_s,
            "above_interpass_duration_s": x.above_interpass_duration_s,
            "minimum_interpass_temperature_margin_K": minimum_interpass_margin,
            "below_interpass_duration_s": x.below_interpass_duration_s,
            "minimum_interpass_requirement_declared": envelope.minimum_supported_interpass_temperature_K
            is not None,
            "record_within_declared_procedure_envelope": record_within,
        },
        notes=(
            "Temperature requirements and applicability are caller-owned; no welding-code preheat table or selection rule is bundled.",
            "A procedure-envelope match does not establish weldability, hydrogen-cracking resistance, mechanical properties or production acceptance.",
        ),
    )


class PreheatProcedureTemplate(WeldPreheatProcedureAssessment):
    minimum_recorded_preheat_temperature_K: None = None
    maximum_recorded_interpass_temperature_K: None = None
    below_preheat_duration_s: None = None
    above_interpass_duration_s: None = None
    minimum_recorded_interpass_temperature_K: None = None
    below_interpass_duration_s: None = None


class PreheatMeasurementIdentity(Contract):
    sensor_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    weld_id: str = Field(min_length=1)
    surface: Literal["inner", "outer", "other_declared"]
    coordinate_frame_id: str = Field(min_length=1)
    position_m: tuple[float, float, float]
    placement_basis_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)


class PreheatMeasurementTrace(PreheatMeasurementIdentity):
    time_s: tuple[Nonnegative, ...] = Field(min_length=2)
    temperature_K: tuple[Positive, ...] = Field(min_length=2)
    trace_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def trace_support(self):
        if len(self.time_s) != len(self.temperature_K) or any(
            b <= a for a, b in zip(self.time_s[:-1], self.time_s[1:], strict=True)
        ):
            raise ValueError("preheat trace needs aligned, strictly increasing samples")
        if self.trace_sha256 != canonical_digest(
            {"time_s": self.time_s, "temperature_K": self.temperature_K}
        ):
            raise ValueError("preheat trace digest must pin normalized time and temperature arrays")
        return self


class PreheatMeasurementWindow(Contract):
    window_id: str = Field(min_length=1)
    phase: Literal["preheat", "interpass"]
    start_time_s: Nonnegative
    end_time_s: Positive

    @model_validator(mode="after")
    def positive_window(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("preheat measurement windows require positive duration")
        return self


class PreheatHistoryBinding(CorrelationRequest):
    template: PreheatProcedureTemplate
    required_channels: tuple[PreheatMeasurementIdentity, ...] = Field(min_length=1, max_length=256)
    traces: tuple[PreheatMeasurementTrace, ...] = Field(max_length=256)
    windows: tuple[PreheatMeasurementWindow, ...] = Field(min_length=2, max_length=10000)
    placement_phase_windows_and_clock_reviewed: bool
    maximum_sample_gap_s: Positive
    maximum_segment_evaluations: int = Field(default=1000000, ge=1, le=10000000)

    @model_validator(mode="after")
    def coherent_membership(self):
        for rows, key in (
            (self.required_channels, "sensor_id"),
            (self.traces, "sensor_id"),
            (self.windows, "window_id"),
        ):
            if len({getattr(r, key) for r in rows}) != len(rows):
                raise ValueError("preheat channel and window identities must be unique")
        expected = {r.sensor_id: r for r in self.required_channels}
        for channel in self.required_channels:
            if (channel.location_id, channel.weld_id) != (self.template.location_id, self.template.weld_id):
                raise ValueError("required channel location and weld must match the template")
        if len({r.clock_id for r in self.required_channels}) != 1:
            raise ValueError("preheat measurement channels must share an explicit clock")
        for trace in self.traces:
            identity = trace.model_dump(include=set(PreheatMeasurementIdentity.model_fields))
            if trace.sensor_id not in expected or identity != expected[trace.sensor_id].model_dump():
                raise ValueError(
                    "trace surface, placement, physical scope and clock must match its required channel"
                )
        if {r.phase for r in self.windows} != {"preheat", "interpass"}:
            raise ValueError("both preheat and interpass windows must be explicitly declared")
        if any(
            b.start_time_s < a.end_time_s for a, b in zip(self.windows[:-1], self.windows[1:], strict=True)
        ):
            raise ValueError("preheat/interpass windows must be ordered and nonoverlapping")
        return self


def _union_duration(intervals):
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return sum((b - a for a, b in merged), Fraction(0))


def _excursion_segment(a, b, ya, yb, limit, *, below):
    outside_a = ya < limit if below else ya > limit
    outside_b = yb < limit if below else yb > limit
    if outside_a and outside_b:
        return (a, b)
    if outside_a != outside_b:
        crossing = a + (b - a) * (limit - ya) / (yb - ya)
        return (a, crossing) if outside_a else (crossing, b)
    return None


def preheat_history_binding(x: PreheatHistoryBinding) -> Calculation:
    base = {
        "assessment_id": x.template.assessment_id,
        "input_sha256": canonical_digest(x.model_dump(mode="json")),
    }
    missing = sorted({r.sensor_id for r in x.required_channels} - {r.sensor_id for r in x.traces})
    if missing or not x.placement_phase_windows_and_clock_reviewed:
        return Calculation(
            status="needs_data",
            values=base | {"missing_sensor_ids": missing},
            notes=("Required sensor records and reviewed phase/placement/clock mapping are necessary.",),
        )
    envelopes = [
        r
        for r in x.template.candidate_envelopes
        if _identity(r) == _identity(x.template)
        and r.minimum_thickness_m <= x.template.governing_thickness_m <= r.maximum_thickness_m
        and r.minimum_net_heat_input_J_m <= x.template.net_heat_input_J_m <= r.maximum_net_heat_input_J_m
    ]
    if len(envelopes) != 1:
        return Calculation(
            status="needs_data" if len(envelopes) > 1 else "out_of_scope",
            values=base,
            notes=("History binding requires exactly one supported procedure envelope.",),
        )
    envelope = envelopes[0]
    excursions = {"preheat": [], "interpass": [], "interpass_minimum": []}
    extrema = {"preheat": [], "interpass": []}
    evaluations = 0
    for window in x.windows:
        ws, we = Fraction(window.start_time_s), Fraction(window.end_time_s)
        limit = Fraction(
            envelope.minimum_required_preheat_temperature_K
            if window.phase == "preheat"
            else envelope.maximum_supported_interpass_temperature_K
        )
        for trace in x.traces:
            if window.start_time_s < trace.time_s[0] or window.end_time_s > trace.time_s[-1]:
                return Calculation(
                    status="needs_data",
                    values=base,
                    notes=(
                        "A required trace does not cover every declared window; no extrapolation is used.",
                    ),
                )
            for t0, t1, y0, y1 in zip(
                trace.time_s[:-1],
                trace.time_s[1:],
                trace.temperature_K[:-1],
                trace.temperature_K[1:],
                strict=True,
            ):
                evaluations += 1
                if evaluations > x.maximum_segment_evaluations:
                    return Calculation(
                        status="out_of_scope", values=base, notes=("Preheat history work budget exceeded.",)
                    )
                a, b = max(ws, Fraction(t0)), min(we, Fraction(t1))
                if b <= a:
                    continue
                dt = Fraction(t1) - Fraction(t0)
                if dt > Fraction(x.maximum_sample_gap_s):
                    return Calculation(
                        status="needs_data",
                        values=base,
                        notes=(
                            "A monitored sample gap exceeds caller support; no gap interpolation is used.",
                        ),
                    )
                ya = Fraction(y0) + (Fraction(y1) - Fraction(y0)) * (a - Fraction(t0)) / dt
                yb = Fraction(y0) + (Fraction(y1) - Fraction(y0)) * (b - Fraction(t0)) / dt
                extrema[window.phase].extend((ya, yb))
                interval = _excursion_segment(a, b, ya, yb, limit, below=window.phase == "preheat")
                if interval is not None:
                    excursions[window.phase].append(interval)
                if (
                    window.phase == "interpass"
                    and envelope.minimum_supported_interpass_temperature_K is not None
                ):
                    interval = _excursion_segment(
                        a, b, ya, yb, Fraction(envelope.minimum_supported_interpass_temperature_K), below=True
                    )
                    if interval is not None:
                        excursions["interpass_minimum"].append(interval)
    exact = {
        "minimum_recorded_preheat_temperature_K": min(extrema["preheat"]),
        "maximum_recorded_interpass_temperature_K": max(extrema["interpass"]),
        "minimum_recorded_interpass_temperature_K": min(extrema["interpass"]),
        "below_preheat_duration_s": _union_duration(excursions["preheat"]),
        "above_interpass_duration_s": _union_duration(excursions["interpass"]),
    }
    if envelope.minimum_supported_interpass_temperature_K is not None:
        exact["below_interpass_duration_s"] = _union_duration(excursions["interpass_minimum"])
    try:
        derived = {k: float(v) for k, v in exact.items()}
        if any(v and derived[k] == 0 for k, v in exact.items()):
            raise OverflowError
    except OverflowError:
        return Calculation(
            status="out_of_scope",
            values=base,
            notes=("Derived temperature or nonzero excursion duration exceeds numeric support.",),
        )
    derived.setdefault("below_interpass_duration_s", None)
    payload = {k: getattr(x.template, k) for k in WeldPreheatProcedureAssessment.model_fields}
    payload.update(derived)
    assessment = WeldPreheatProcedureAssessment(**payload)
    result = weld_preheat_procedure_envelope(assessment)
    return Calculation(
        status=result.status,
        values=base
        | result.values
        | {
            "derived_metrics": derived,
            "derived_assessment": assessment.model_dump(mode="json"),
            "derived_assessment_sha256": canonical_digest(assessment.model_dump(mode="json")),
            "channel_manifest": [r.model_dump(mode="json") for r in x.required_channels],
            "trace_sha256": {r.sensor_id: r.trace_sha256 for r in x.traces},
            "segment_evaluations": evaluations,
        },
        notes=result.notes
        + (
            "Excursion duration is the temporal union across required sensors, not a sum of sensor-seconds. Piecewise-linear recorded support only; no unsampled spatial/through-wall temperature, gap repair or welding qualification is inferred.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if isinstance(x, PreheatHistoryBinding):
            x = x.template
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("preheat-assessment asset and location must match the run context")

    binding_spec = ModelSpec(
        "welding.preheat_history_binding",
        PreheatHistoryBinding,
        preheat_history_binding,
        {
            "derived_metrics.minimum_recorded_preheat_temperature_K": "K",
            "derived_metrics.maximum_recorded_interpass_temperature_K": "K",
            "derived_metrics.below_preheat_duration_s": "s",
            "derived_metrics.above_interpass_duration_s": "s",
            "derived_metrics.minimum_recorded_interpass_temperature_K": "K",
            "derived_metrics.below_interpass_duration_s": "s",
        },
        (
            "Exact required sensor surface/placement/scope/clock roles and explicit phase windows; caller-owned unique procedure envelope.",
        ),
        ("caller_parameterized_engineering_correlation_arithmetic",),
        context_validator=same_identity,
        version="0.1.1",
    )
    return [
        ModelSpec(
            "welding.preheat_procedure_envelope",
            WeldPreheatProcedureAssessment,
            weld_preheat_procedure_envelope,
            {
                "assessment_id": "1",
                "selected_envelope_id": "1",
                "preheat_temperature_margin_K": "K",
                "interpass_temperature_margin_K": "K",
                "minimum_interpass_temperature_margin_K": "K",
                "below_interpass_duration_s": "s",
                "below_preheat_duration_s": "s",
                "above_interpass_duration_s": "s",
                "record_within_declared_procedure_envelope": "1",
            },
            (
                "Material, joint, process, consumable, hydrogen-control and restraint identities match exactly.",
                "Thickness, heat-input and temperature requirements are supplied by a reviewed caller-owned procedure envelope.",
            ),
            ("declared_weld_preheat_procedure_envelope",),
            context_validator=same_identity,
            version="0.1.1",
        ),
        binding_spec,
    ]
