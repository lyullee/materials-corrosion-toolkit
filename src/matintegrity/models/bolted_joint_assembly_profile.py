"""Caller-profile QA assessment for gasketed flange and bolted-joint histories."""

from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Contract, Evidence, Fraction, Nonnegative, Positive, canonical_digest

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "fabrication.bolted_joint_assembly_history_profile_assessment"


class AssemblyBoltPreload(Contract):
    bolt_id: str = Field(min_length=1)
    bolt_position_id: str = Field(min_length=1)
    preload_n: Positive | None = None
    preload_unit_token: Literal["N"] = "N"
    standard_uncertainty_n: Nonnegative | None = None
    status: Literal["available", "missing", "invalid"]
    measurement_method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_status(self):
        if self.status == "available":
            if self.preload_n is None or self.standard_uncertainty_n is None or self.result_digest is None:
                raise ValueError("available bolt preload requires value, uncertainty and digest")
        elif (
            self.preload_n is not None
            or self.standard_uncertainty_n is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid bolt preload requires a basis and no numeric value")
        return self


class FlangeFaceAlignmentObservation(Contract):
    observation_id: str = Field(min_length=1)
    flange_face_pair_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    alignment_metric_id: str = Field(min_length=1)
    alignment_metric_definition: str = Field(min_length=1)
    alignment_m: Nonnegative | None = None
    alignment_unit_token: Literal["m"] = "m"
    standard_uncertainty_m: Nonnegative | None = None
    status: Literal["available", "missing", "invalid"]
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    missing_or_invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_status(self):
        if self.status == "available":
            if self.alignment_m is None or self.standard_uncertainty_m is None or self.result_digest is None:
                raise ValueError("available flange alignment requires value, uncertainty and digest")
        elif (
            self.alignment_m is not None
            or self.standard_uncertainty_m is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid flange alignment requires a basis and no numeric value")
        return self


class GasketAssemblyMeasurement(Contract):
    measurement_id: str = Field(min_length=1)
    initial_thickness_m: Positive
    assembled_thickness_m: Positive
    thickness_standard_uncertainty_m: Nonnegative
    recovery_fraction: Fraction | None = None
    recovery_standard_uncertainty_fraction: Nonnegative | None = None
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def physical_and_complete(self):
        if self.assembled_thickness_m > self.initial_thickness_m:
            raise ValueError("assembled gasket thickness cannot exceed initial thickness")
        if (self.recovery_fraction is None) != (self.recovery_standard_uncertainty_fraction is None):
            raise ValueError("gasket recovery and uncertainty must be supplied together")
        return self


class JointThermalPressureCycle(Contract):
    cycle_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    clock_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    temperature_unit_token: Literal["K"] = "K"
    minimum_absolute_pressure_pa: Nonnegative
    maximum_absolute_pressure_pa: Nonnegative
    pressure_unit_token: Literal["Pa_abs"] = "Pa_abs"
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_cycle(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("joint load cycles require positive duration")
        if self.maximum_temperature_k < self.minimum_temperature_k:
            raise ValueError("joint cycle temperature range must be ordered")
        if self.maximum_absolute_pressure_pa < self.minimum_absolute_pressure_pa:
            raise ValueError("joint cycle pressure range must be ordered")
        return self


class JointLeakageObservation(Contract):
    observation_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    medium_id: str = Field(min_length=1)
    detection_status: Literal["detected", "not_detected", "not_examined", "invalid"]
    leakage_rate: Nonnegative | None = None
    leakage_unit_token: str = Field(min_length=1)
    standard_uncertainty: Nonnegative | None = None
    detection_limit: Nonnegative | None = None
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    status_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_detection(self):
        if self.detection_status == "detected":
            if self.leakage_rate is None or self.standard_uncertainty is None or self.result_digest is None:
                raise ValueError("detected leakage requires rate, uncertainty and digest")
        elif self.detection_status == "not_detected":
            if self.leakage_rate is not None or self.detection_limit is None or self.result_digest is None:
                raise ValueError("non-detection requires detection limit, no rate and a digest")
        elif not self.status_basis:
            raise ValueError("not-examined or invalid leakage observations require a basis")
        return self


class CallerGasketCompressionRecoveryEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    minimum_compression_fraction: Fraction
    maximum_compression_fraction: Fraction
    minimum_recovery_fraction: Fraction | None = None
    maximum_recovery_fraction: Fraction | None = None
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    missing_recovery_disposition: Literal["review", "insufficient_evidence"]
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_envelope(self):
        if self.maximum_compression_fraction < self.minimum_compression_fraction:
            raise ValueError("gasket compression envelope must be ordered")
        recovery = (self.minimum_recovery_fraction, self.maximum_recovery_fraction)
        if any(value is not None for value in recovery) and not all(value is not None for value in recovery):
            raise ValueError("gasket recovery envelope must provide both bounds")
        if all(value is not None for value in recovery) and recovery[1] < recovery[0]:
            raise ValueError("gasket recovery envelope must be ordered")
        return self


class CallerBoltedJointProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_flange_geometry_ids: tuple[str, ...] = Field(min_length=1)
    permitted_flange_face_condition_ids: tuple[str, ...] = Field(min_length=1)
    permitted_gasket_condition_ids: tuple[str, ...] = Field(min_length=1)
    permitted_bolt_condition_ids: tuple[str, ...] = Field(min_length=1)
    minimum_bolt_preload_n: Positive
    maximum_bolt_preload_n: Positive
    maximum_preload_coefficient_of_variation: Nonnegative
    preload_uncertainty_policy: Literal["point_value", "interval_must_fit"]
    preload_uncertainty_coverage_factor: Positive = 1.0
    maximum_flange_alignment_m: Nonnegative
    alignment_uncertainty_policy: Literal["point_value", "interval_must_fit"]
    alignment_uncertainty_coverage_factor: Positive = 1.0
    gasket_envelope: CallerGasketCompressionRecoveryEnvelope
    minimum_supported_temperature_k: Positive
    maximum_supported_temperature_k: Positive
    maximum_supported_absolute_pressure_pa: Nonnegative
    leakage_unit_token: str = Field(min_length=1)
    maximum_leakage_rate: Nonnegative
    detected_leak_disposition: Literal["reject", "review"]
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_profile(self):
        if self.maximum_bolt_preload_n < self.minimum_bolt_preload_n:
            raise ValueError("caller bolt preload envelope must be ordered")
        if self.maximum_supported_temperature_k < self.minimum_supported_temperature_k:
            raise ValueError("caller cycle temperature envelope must be ordered")
        return self


class BoltedJointAssemblyAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    joint_id: str = Field(min_length=1)
    flange_geometry_id: str = Field(min_length=1)
    flange_face_pair_id: str = Field(min_length=1)
    flange_face_condition_id: str = Field(min_length=1)
    gasket_condition_id: str = Field(min_length=1)
    gasket_lot_id: str = Field(min_length=1)
    bolt_condition_id: str = Field(min_length=1)
    bolt_lot_id: str = Field(min_length=1)
    assembly_procedure_id: str = Field(min_length=1)
    assembly_procedure_revision: str = Field(min_length=1)
    bolt_preloads: tuple[AssemblyBoltPreload, ...] = Field(min_length=2)
    flange_alignment: tuple[FlangeFaceAlignmentObservation, ...] = Field(min_length=1)
    gasket_measurement: GasketAssemblyMeasurement
    load_cycles: tuple[JointThermalPressureCycle, ...] = Field(min_length=1)
    leakage_observations: tuple[JointLeakageObservation, ...] = Field(min_length=1)
    profile: CallerBoltedJointProfile
    assembly_identity_lots_and_procedure_reviewed: bool
    preload_method_units_uncertainty_and_positions_reviewed: bool
    flange_faces_alignment_metric_and_uncertainty_reviewed: bool
    gasket_measurement_and_caller_envelope_reviewed: bool
    load_history_clock_temperature_and_pressure_reviewed: bool
    leakage_status_units_limits_and_lineage_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_unique_history(self):
        for values, label in (
            ([row.bolt_id for row in self.bolt_preloads], "bolt"),
            ([row.bolt_position_id for row in self.bolt_preloads], "bolt position"),
            ([row.observation_id for row in self.flange_alignment], "alignment observation"),
            ([row.cycle_id for row in self.load_cycles], "load cycle"),
            ([row.observation_id for row in self.leakage_observations], "leakage observation"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} identifiers must be unique")
        if any(row.flange_face_pair_id != self.flange_face_pair_id for row in self.flange_alignment):
            raise ValueError("alignment observations must reference the declared flange-face pair")
        positions = [row.sequence_position for row in self.load_cycles]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("joint load cycles require consecutive sequence positions")
        for first, second in zip(self.load_cycles, self.load_cycles[1:], strict=False):
            if second.start_time_s < first.end_time_s or second.clock_id != first.clock_id:
                raise ValueError("joint load cycles require one nonoverlapping ordered clock")
        if any(row.clock_id != self.load_cycles[0].clock_id for row in self.leakage_observations):
            raise ValueError("leakage observations must use the load-history clock")
        return self


class JointAssemblyRuleFinding(Contract):
    rule_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str = Field(min_length=1)


class BoltedJointAssemblyAssessmentResult(Contract):
    schema_version: Literal["matintegrity.bolted_joint_assembly_profile.v1"] = (
        "matintegrity.bolted_joint_assembly_profile.v1"
    )
    model_id: Literal["fabrication.bolted_joint_assembly_history_profile_assessment"] = MODEL_ID
    assessment_id: str
    joint_id: str
    profile_id: str
    profile_revision: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[JointAssemblyRuleFinding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    code_or_standard_qualification_claim: Literal[False] = False
    physical_validation_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def bound_digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("bolted-joint assembly result digest does not match its content")
        return self


def _bounded(value, uncertainty, lower, upper, policy, factor):
    span = factor * uncertainty if policy == "interval_must_fit" else 0.0
    evaluated_lower, evaluated_upper = value - span, value + span
    return lower <= evaluated_lower and evaluated_upper <= upper, evaluated_lower, evaluated_upper


def assess_bolted_joint_assembly(
    x: BoltedJointAssemblyAssessment,
) -> BoltedJointAssemblyAssessmentResult:
    """Apply only caller profile limits; no torque conversion or joint solver is performed."""

    p = x.profile
    reviews, insufficient, findings = [], [], []
    for reviewed, reason in (
        (p.profile_reviewed, "caller assembly profile was not reviewed"),
        (
            x.assembly_identity_lots_and_procedure_reviewed,
            "assembly identities, lots or procedure were not reviewed",
        ),
        (
            x.preload_method_units_uncertainty_and_positions_reviewed,
            "preload method, units, uncertainty or positions were not reviewed",
        ),
        (
            x.flange_faces_alignment_metric_and_uncertainty_reviewed,
            "flange faces or alignment evidence was not reviewed",
        ),
        (
            x.gasket_measurement_and_caller_envelope_reviewed,
            "gasket measurement or caller envelope was not reviewed",
        ),
        (
            x.load_history_clock_temperature_and_pressure_reviewed,
            "load history clock, temperature or pressure was not reviewed",
        ),
        (
            x.leakage_status_units_limits_and_lineage_reviewed,
            "leakage status, units, limits or lineage were not reviewed",
        ),
    ):
        if not reviewed:
            insufficient.append(reason)
    identities = (
        (x.flange_geometry_id, p.permitted_flange_geometry_ids, "flange_geometry"),
        (x.flange_face_condition_id, p.permitted_flange_face_condition_ids, "flange_face_condition"),
        (x.gasket_condition_id, p.permitted_gasket_condition_ids, "gasket_condition"),
        (x.bolt_condition_id, p.permitted_bolt_condition_ids, "bolt_condition"),
    )
    for observed, allowed, rule_id in identities:
        findings.append(
            JointAssemblyRuleFinding(
                rule_id=rule_id,
                target_id=x.joint_id,
                outcome="pass" if observed in allowed else "review",
                observed_value=observed,
                unit_token="identity",
                basis="caller permitted-identity list",
            )
        )
        if observed not in allowed:
            reviews.append(f"{rule_id} outside caller profile")
    available = [row for row in x.bolt_preloads if row.status == "available"]
    if len(available) != len(x.bolt_preloads):
        insufficient.append("one or more bolt preload measurements are missing or invalid")
    for row in available:
        passed, low, high = _bounded(
            row.preload_n,
            row.standard_uncertainty_n,
            p.minimum_bolt_preload_n,
            p.maximum_bolt_preload_n,
            p.preload_uncertainty_policy,
            p.preload_uncertainty_coverage_factor,
        )
        findings.append(
            JointAssemblyRuleFinding(
                rule_id="individual_bolt_preload",
                target_id=row.bolt_id,
                outcome="pass" if passed else "fail",
                observed_value=row.preload_n,
                unit_token="N",
                evaluated_lower=low,
                evaluated_upper=high,
                basis=f"caller preload envelope with {p.preload_uncertainty_policy}",
            )
        )
    if available:
        values = [row.preload_n for row in available]
        cv = pstdev(values) / fmean(values)
        findings.append(
            JointAssemblyRuleFinding(
                rule_id="preload_coefficient_of_variation",
                target_id=x.joint_id,
                outcome="pass" if cv <= p.maximum_preload_coefficient_of_variation else "fail",
                observed_value=cv,
                unit_token="1",
                basis="population standard deviation divided by mean direct preload",
            )
        )
    for row in x.flange_alignment:
        if row.status != "available":
            insufficient.append(f"alignment observation {row.observation_id} is unavailable")
            continue
        span = (
            p.alignment_uncertainty_coverage_factor * row.standard_uncertainty_m
            if p.alignment_uncertainty_policy == "interval_must_fit"
            else 0.0
        )
        high = row.alignment_m + span
        findings.append(
            JointAssemblyRuleFinding(
                rule_id="flange_alignment",
                target_id=row.observation_id,
                outcome="pass" if high <= p.maximum_flange_alignment_m else "fail",
                observed_value=row.alignment_m,
                unit_token="m",
                evaluated_lower=max(0.0, row.alignment_m - span),
                evaluated_upper=high,
                basis=f"caller alignment envelope with {p.alignment_uncertainty_policy}",
            )
        )
    g = x.gasket_measurement
    compression = (g.initial_thickness_m - g.assembled_thickness_m) / g.initial_thickness_m
    compression_u = math.sqrt(2.0) * g.thickness_standard_uncertainty_m / g.initial_thickness_m
    e = p.gasket_envelope
    passed, low, high = _bounded(
        compression,
        compression_u,
        e.minimum_compression_fraction,
        e.maximum_compression_fraction,
        e.uncertainty_policy,
        e.uncertainty_coverage_factor,
    )
    findings.append(
        JointAssemblyRuleFinding(
            rule_id="gasket_compression",
            target_id=g.measurement_id,
            outcome="pass" if passed else "fail",
            observed_value=compression,
            unit_token="1",
            evaluated_lower=low,
            evaluated_upper=high,
            basis=f"caller gasket envelope with {e.uncertainty_policy}",
        )
    )
    if e.minimum_recovery_fraction is not None:
        if g.recovery_fraction is None:
            outcome = e.missing_recovery_disposition
            (reviews if outcome == "review" else insufficient).append("gasket recovery evidence is missing")
            findings.append(
                JointAssemblyRuleFinding(
                    rule_id="gasket_recovery",
                    target_id=g.measurement_id,
                    outcome=outcome,
                    observed_value=None,
                    unit_token="1",
                    basis="caller profile requires recovery evidence",
                )
            )
        else:
            passed, low, high = _bounded(
                g.recovery_fraction,
                g.recovery_standard_uncertainty_fraction,
                e.minimum_recovery_fraction,
                e.maximum_recovery_fraction,
                e.uncertainty_policy,
                e.uncertainty_coverage_factor,
            )
            findings.append(
                JointAssemblyRuleFinding(
                    rule_id="gasket_recovery",
                    target_id=g.measurement_id,
                    outcome="pass" if passed else "fail",
                    observed_value=g.recovery_fraction,
                    unit_token="1",
                    evaluated_lower=low,
                    evaluated_upper=high,
                    basis=f"caller gasket recovery envelope with {e.uncertainty_policy}",
                )
            )
    for row in x.load_cycles:
        within = (
            p.minimum_supported_temperature_k <= row.minimum_temperature_k
            and row.maximum_temperature_k <= p.maximum_supported_temperature_k
            and row.maximum_absolute_pressure_pa <= p.maximum_supported_absolute_pressure_pa
        )
        findings.append(
            JointAssemblyRuleFinding(
                rule_id="thermal_pressure_cycle",
                target_id=row.cycle_id,
                outcome="pass" if within else "fail",
                observed_value=row.maximum_absolute_pressure_pa,
                unit_token="Pa_abs",
                basis="caller temperature and absolute-pressure cycle envelope",
            )
        )
    for row in x.leakage_observations:
        if row.leakage_unit_token != p.leakage_unit_token:
            insufficient.append(f"leakage observation {row.observation_id} unit differs from caller profile")
            continue
        if row.detection_status in {"not_examined", "invalid"}:
            insufficient.append(f"leakage observation {row.observation_id} is {row.detection_status}")
            continue
        if row.detection_status == "not_detected":
            outcome = "pass" if row.detection_limit <= p.maximum_leakage_rate else "review"
            if outcome == "review":
                reviews.append(f"leakage detection limit exceeds profile for {row.observation_id}")
            value = row.detection_limit
        else:
            outcome = "pass" if row.leakage_rate <= p.maximum_leakage_rate else p.detected_leak_disposition
            if outcome == "review":
                reviews.append(f"detected leakage exceeds profile for {row.observation_id}")
            value = row.leakage_rate
        findings.append(
            JointAssemblyRuleFinding(
                rule_id="leakage_observation",
                target_id=row.observation_id,
                outcome=outcome if outcome != "reject" else "fail",
                observed_value=value,
                unit_token=row.leakage_unit_token,
                basis="caller leakage-rate envelope or detection-limit comparison",
            )
        )
    if insufficient:
        disposition: Disposition = "insufficient_evidence"
    elif any(row.outcome == "fail" for row in findings):
        disposition = "reject"
    elif reviews or any(row.outcome == "review" for row in findings):
        disposition = "review"
    else:
        disposition = "accept"
    values = {
        "assessment_id": x.assessment_id,
        "joint_id": x.joint_id,
        "profile_id": p.profile_id,
        "profile_revision": p.profile_revision,
        "disposition": disposition,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        "findings": tuple(findings),
        "review_reasons": tuple(dict.fromkeys(reviews)),
        "insufficient_evidence_reasons": tuple(dict.fromkeys(insufficient)),
        "notes": (
            "Only caller profile limits are applied; no torque-to-preload conversion, flange solver, code table or built-in allowable is used.",
            "Assembly identities, direct preload uncertainty, face alignment, gasket response, ordered cycles and leakage evidence remain traceable.",
            "The disposition is not code qualification, physical validation, remaining life or failure probability.",
        ),
    }
    unsigned = BoltedJointAssemblyAssessmentResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return BoltedJointAssemblyAssessmentResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )
