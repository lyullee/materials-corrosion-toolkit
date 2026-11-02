"""Caller-profile assessment of high-temperature exposure and measured response histories."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, ValidationInfo, model_validator

from .contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest

Mechanism = Literal["oxidation", "sulfidation", "carburization", "nitriding", "metallurgical_aging"]


class HighTemperatureExposureInterval(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    record_status: Literal["reported", "missing", "invalid"]
    temperature_K: Positive | None = None
    temperature_expanded_uncertainty_K: Nonnegative | None = None
    pressure_Pa_abs: Positive | None = None
    pressure_expanded_uncertainty_Pa: Nonnegative | None = None
    gas_chemistry_descriptor_id: str | None = None
    gas_chemistry_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    activity_status: Literal["reported", "not_applicable", "missing", "invalid"]
    activity_quantity_id: str | None = None
    activity_basis: str | None = None
    activity_value: float | None = None
    activity_expanded_uncertainty: Nonnegative | None = None
    activity_unit_token: str | None = None
    activity_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    interval_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("high-temperature exposure intervals require positive duration")
        core = (
            self.temperature_K,
            self.temperature_expanded_uncertainty_K,
            self.gas_chemistry_descriptor_id,
            self.gas_chemistry_record_digest,
        )
        if self.record_status == "reported" and any(value is None for value in core):
            raise ValueError("reported high-temperature intervals require temperature and gas evidence")
        if self.record_status != "reported" and not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid high-temperature intervals require a basis")
        if (self.pressure_Pa_abs is None) != (self.pressure_expanded_uncertainty_Pa is None):
            raise ValueError("pressure value and uncertainty must be supplied together")
        activity = (
            self.activity_quantity_id,
            self.activity_basis,
            self.activity_value,
            self.activity_expanded_uncertainty,
            self.activity_unit_token,
            self.activity_record_digest,
        )
        if self.activity_status == "reported" and any(value is None for value in activity):
            raise ValueError(
                "reported activity requires identity, basis, value, unit, uncertainty and digest"
            )
        if self.activity_status == "not_applicable" and any(value is not None for value in activity):
            raise ValueError("not-applicable activity cannot carry activity values")
        if self.activity_status in {"missing", "invalid"} and not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid activity requires a basis")
        return self


class HighTemperatureMeasurementEvidence(Contract):
    measurement_id: str = Field(min_length=1)
    measurement_kind: Literal["scale_thickness", "affected_depth", "property"]
    quantity_id: str = Field(min_length=1)
    status: Literal["reported", "missing", "invalid"]
    value: float | None = None
    expanded_uncertainty: Nonnegative | None = None
    unit_token: str = Field(min_length=1)
    measurement_time_s: Nonnegative
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    measurement_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    invalid_or_missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_measurement(self):
        if self.status == "reported":
            if self.value is None or self.expanded_uncertainty is None:
                raise ValueError("reported high-temperature measurements require value and uncertainty")
        elif self.value is not None or self.expanded_uncertainty is not None:
            raise ValueError("missing or invalid measurements cannot carry numeric results")
        elif not self.invalid_or_missing_basis:
            raise ValueError("missing or invalid measurements require a basis")
        return self


class HighTemperatureMeasurementCriterion(Contract):
    criterion_id: str = Field(min_length=1)
    measurement_kind: Literal["scale_thickness", "affected_depth", "property"]
    quantity_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    minimum_acceptable: float | None = None
    maximum_acceptable: float | None = None
    minimum_reported_measurements: int = Field(ge=1)
    criterion_basis: str = Field(min_length=1)
    criterion_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.minimum_acceptable is None and self.maximum_acceptable is None:
            raise ValueError("measurement criterion requires at least one caller bound")
        if (
            self.minimum_acceptable is not None
            and self.maximum_acceptable is not None
            and self.minimum_acceptable > self.maximum_acceptable
        ):
            raise ValueError("measurement criterion bounds must be ordered")
        return self


class HighTemperatureCallerProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    mechanism: Mechanism
    supported_material_ids: tuple[str, ...] = Field(min_length=1)
    supported_material_condition_ids: tuple[str, ...] = Field(min_length=1)
    supported_gas_chemistry_descriptor_ids: tuple[str, ...] = Field(min_length=1)
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    maximum_cumulative_exposure_s: Positive
    pressure_required: bool
    minimum_pressure_Pa_abs: Positive | None = None
    maximum_pressure_Pa_abs: Positive | None = None
    activity_required: bool
    activity_quantity_id: str | None = None
    activity_basis: str | None = None
    activity_unit_token: str | None = None
    minimum_activity: float | None = None
    maximum_activity: float | None = None
    measurement_criteria: tuple[HighTemperatureMeasurementCriterion, ...] = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_profile(self):
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("profile temperature support must be ordered")
        pressure = (self.minimum_pressure_Pa_abs, self.maximum_pressure_Pa_abs)
        if self.pressure_required and any(value is None for value in pressure):
            raise ValueError("pressure-required profiles need ordered pressure bounds")
        if not self.pressure_required and any(value is not None for value in pressure):
            raise ValueError("pressure-optional profiles cannot carry hidden pressure bounds")
        if all(value is not None for value in pressure) and pressure[0] > pressure[1]:
            raise ValueError("profile pressure support must be ordered")
        activity = (
            self.activity_quantity_id,
            self.activity_basis,
            self.activity_unit_token,
            self.minimum_activity,
            self.maximum_activity,
        )
        if self.activity_required and any(value is None for value in activity):
            raise ValueError("activity-required profiles need identity, basis, unit and bounds")
        if not self.activity_required and any(value is not None for value in activity):
            raise ValueError("activity-optional profiles cannot carry hidden activity bounds")
        if self.activity_required and self.minimum_activity > self.maximum_activity:
            raise ValueError("profile activity support must be ordered")
        keys = [(row.measurement_kind, row.quantity_id) for row in self.measurement_criteria]
        if len(set(keys)) != len(keys):
            raise ValueError("high-temperature measurement criteria must be unique by quantity")
        return self

    @property
    def deterministic_digest(self):
        return canonical_digest(self.model_dump(mode="json"))


class HighTemperatureHistoryAssessment(Contract):
    schema_version: Literal["matintegrity.high_temperature_history.v1"] = (
        "matintegrity.high_temperature_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    mechanism: Mechanism
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    material_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    exposure_intervals: tuple[HighTemperatureExposureInterval, ...] = Field(min_length=1)
    measurements: tuple[HighTemperatureMeasurementEvidence, ...] = Field(min_length=1)
    caller_profile: HighTemperatureCallerProfile
    exposure_clock_temperature_gas_and_activity_reviewed: bool
    material_state_and_measurement_lineage_reviewed: bool
    caller_profile_and_missing_evidence_policy_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)
    payload_digest: str = Field(pattern=r"^[a-f0-9]{64}$")

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"payload_digest"})

    @model_validator(mode="after")
    def linked_history(self, info: ValidationInfo):
        if self.mechanism != self.caller_profile.mechanism:
            raise ValueError("assessment mechanism must match the caller profile")
        for values, label in (
            ([row.interval_id for row in self.exposure_intervals], "exposure interval"),
            ([row.measurement_id for row in self.measurements], "measurement"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"high-temperature {label} identifiers must be unique")
        for left, right in zip(self.exposure_intervals, self.exposure_intervals[1:], strict=False):
            if right.start_time_s < left.end_time_s:
                raise ValueError("high-temperature exposure intervals must be ordered and nonoverlapping")
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.payload_digest
        ):
            raise ValueError("high-temperature history payload digest mismatch")
        return self


def high_temperature_history_assessment(**payload) -> HighTemperatureHistoryAssessment:
    unsigned = HighTemperatureHistoryAssessment.model_validate(
        {**payload, "payload_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return HighTemperatureHistoryAssessment.model_validate(
        {**payload, "payload_digest": canonical_digest(unsigned.digest_payload())}
    )


class HighTemperatureFinding(Contract):
    record_id: str
    criterion_id: str
    outcome: Literal["within", "outside", "boundary_overlap", "missing", "invalid", "mismatch"]
    basis: str


class HighTemperatureHistoryReport(Contract):
    assessment_id: str
    mechanism: Mechanism
    decision: Literal["accept", "reject", "review", "insufficient_evidence"]
    cumulative_exposure_s: float
    findings: tuple[HighTemperatureFinding, ...]
    input_digest: str
    profile_digest: str
    report_digest: str
    qualification_claim: Literal[False] = False
    rate_constant_inferred: Literal[False] = False
    remaining_life_inferred: Literal[False] = False
    failure_probability_inferred: Literal[False] = False

    def digest_payload(self):
        return self.model_dump(mode="json", exclude={"report_digest"})

    @model_validator(mode="after")
    def bound_digest(self):
        if canonical_digest(self.digest_payload()) != self.report_digest:
            raise ValueError("high-temperature history report digest mismatch")
        return self


def assess_high_temperature_history(x: HighTemperatureHistoryAssessment) -> HighTemperatureHistoryReport:
    profile = x.caller_profile
    findings = []
    reviews = (
        x.exposure_clock_temperature_gas_and_activity_reviewed,
        x.material_state_and_measurement_lineage_reviewed,
        x.caller_profile_and_missing_evidence_policy_reviewed,
    )
    if x.material_id not in profile.supported_material_ids:
        findings.append(
            _finding("material", "material", "mismatch", "Material identity is outside the caller profile.")
        )
    if x.material_condition_id not in profile.supported_material_condition_ids:
        findings.append(
            _finding(
                "material_condition",
                "material_condition",
                "mismatch",
                "Material condition is outside the caller profile.",
            )
        )
    cumulative = sum(row.end_time_s - row.start_time_s for row in x.exposure_intervals)
    if cumulative > profile.maximum_cumulative_exposure_s:
        findings.append(
            _finding(
                "history", "cumulative_exposure", "outside", "Cumulative exposure exceeds the caller profile."
            )
        )

    for interval in x.exposure_intervals:
        if interval.record_status != "reported":
            findings.append(
                _finding(
                    interval.interval_id,
                    "exposure_record",
                    interval.record_status,
                    "Exposure record is missing or invalid.",
                )
            )
            continue
        _interval_findings(interval, profile, findings)

    by_key: dict[tuple[str, str], list[HighTemperatureMeasurementEvidence]] = {}
    for row in x.measurements:
        by_key.setdefault((row.measurement_kind, row.quantity_id), []).append(row)
    for criterion in profile.measurement_criteria:
        records = by_key.get((criterion.measurement_kind, criterion.quantity_id), [])
        reported = [row for row in records if row.status == "reported"]
        if len(reported) < criterion.minimum_reported_measurements:
            findings.append(
                _finding(
                    "measurements",
                    criterion.criterion_id,
                    "missing",
                    "Too few reported measurements for the caller criterion.",
                )
            )
        for row in records:
            if row.status != "reported":
                findings.append(
                    _finding(
                        row.measurement_id,
                        criterion.criterion_id,
                        row.status,
                        "Measurement is missing or invalid.",
                    )
                )
            elif row.unit_token != criterion.unit_token:
                findings.append(
                    _finding(
                        row.measurement_id,
                        criterion.criterion_id,
                        "mismatch",
                        "Measurement unit differs from the caller criterion.",
                    )
                )
            else:
                outcome = _compare(
                    row.value,
                    row.expanded_uncertainty,
                    criterion.minimum_acceptable,
                    criterion.maximum_acceptable,
                )
                findings.append(
                    _finding(
                        row.measurement_id,
                        criterion.criterion_id,
                        outcome,
                        "Measurement uncertainty interval compared with caller bounds.",
                    )
                )

    outcomes = {row.outcome for row in findings}
    if not all(reviews) or outcomes & {"missing", "invalid", "mismatch"}:
        decision = "insufficient_evidence"
    elif "outside" in outcomes:
        decision = "reject"
    elif "boundary_overlap" in outcomes:
        decision = "review"
    else:
        decision = "accept"
    payload = {
        "assessment_id": x.assessment_id,
        "mechanism": x.mechanism,
        "decision": decision,
        "cumulative_exposure_s": cumulative,
        "findings": [row.model_dump(mode="json") for row in findings],
        "input_digest": x.payload_digest,
        "profile_digest": profile.deterministic_digest,
        "qualification_claim": False,
        "rate_constant_inferred": False,
        "remaining_life_inferred": False,
        "failure_probability_inferred": False,
    }
    return HighTemperatureHistoryReport.model_validate(
        {**payload, "findings": tuple(findings), "report_digest": canonical_digest(payload)}
    )


def _interval_findings(interval, profile, findings):
    checks = (
        (
            "temperature",
            interval.temperature_K,
            interval.temperature_expanded_uncertainty_K,
            profile.minimum_temperature_K,
            profile.maximum_temperature_K,
        ),
    )
    for name, value, uncertainty, minimum, maximum in checks:
        findings.append(
            _finding(
                interval.interval_id,
                name,
                _compare(value, uncertainty, minimum, maximum),
                "Exposure uncertainty interval compared with caller support.",
            )
        )
    gas_outcome = (
        "within"
        if interval.gas_chemistry_descriptor_id in profile.supported_gas_chemistry_descriptor_ids
        else "outside"
    )
    findings.append(
        _finding(
            interval.interval_id,
            "gas_chemistry",
            gas_outcome,
            "Exact gas-chemistry identity compared with caller support.",
        )
    )
    if profile.pressure_required:
        if interval.pressure_Pa_abs is None:
            findings.append(
                _finding(
                    interval.interval_id,
                    "pressure",
                    "missing",
                    "Caller profile requires absolute pressure evidence.",
                )
            )
        else:
            findings.append(
                _finding(
                    interval.interval_id,
                    "pressure",
                    _compare(
                        interval.pressure_Pa_abs,
                        interval.pressure_expanded_uncertainty_Pa,
                        profile.minimum_pressure_Pa_abs,
                        profile.maximum_pressure_Pa_abs,
                    ),
                    "Pressure uncertainty interval compared with caller support.",
                )
            )
    if profile.activity_required:
        if interval.activity_status != "reported":
            findings.append(
                _finding(
                    interval.interval_id,
                    "activity",
                    interval.activity_status if interval.activity_status != "not_applicable" else "missing",
                    "Caller profile requires activity evidence.",
                )
            )
        elif (interval.activity_quantity_id, interval.activity_basis, interval.activity_unit_token) != (
            profile.activity_quantity_id,
            profile.activity_basis,
            profile.activity_unit_token,
        ):
            findings.append(
                _finding(
                    interval.interval_id,
                    "activity",
                    "mismatch",
                    "Activity identity, basis, or unit differs from the caller profile.",
                )
            )
        else:
            findings.append(
                _finding(
                    interval.interval_id,
                    "activity",
                    _compare(
                        interval.activity_value,
                        interval.activity_expanded_uncertainty,
                        profile.minimum_activity,
                        profile.maximum_activity,
                    ),
                    "Activity uncertainty interval compared with caller support.",
                )
            )


def _compare(value, uncertainty, minimum, maximum):
    lower, upper = value - uncertainty, value + uncertainty
    inside = (minimum is None or lower >= minimum) and (maximum is None or upper <= maximum)
    outside = (minimum is not None and upper < minimum) or (maximum is not None and lower > maximum)
    return "within" if inside else "outside" if outside else "boundary_overlap"


def _finding(record_id, criterion_id, outcome, basis):
    return HighTemperatureFinding(
        record_id=record_id, criterion_id=criterion_id, outcome=outcome, basis=basis
    )
