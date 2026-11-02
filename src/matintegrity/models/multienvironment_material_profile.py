"""Caller-profile assessment of polymer, seal and composite exposure evidence."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, ValidationInfo, model_validator

from ..contracts import Contract, Evidence, Nonnegative, Positive, canonical_digest

Disposition = Literal["accept", "reject", "review", "insufficient_evidence"]
MODEL_ID = "materials.multienvironment_material_state_profile_assessment"


class MaterialStateIdentity(Contract):
    material_state_id: str = Field(min_length=1)
    material_kind: Literal["polymer", "seal", "composite"]
    material_grade_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    material_lot_id: str = Field(min_length=1)
    resin_id: str | None = None
    matrix_id: str | None = None
    fiber_id: str | None = None
    reinforcement_id: str | None = None
    layup_id: str | None = None
    seal_geometry_id: str | None = None
    manufacturing_condition_id: str = Field(min_length=1)
    identity_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def kind_identity(self):
        if self.material_kind == "composite" and (
            (self.resin_id is None and self.matrix_id is None)
            or (self.fiber_id is None and self.reinforcement_id is None)
            or self.layup_id is None
        ):
            raise ValueError("composite identity requires matrix/resin, reinforcement/fiber and layup")
        if self.material_kind == "seal" and self.seal_geometry_id is None:
            raise ValueError("seal identity requires a seal geometry ID")
        return self


class MediaComponentConcentration(Contract):
    component_id: str = Field(min_length=1)
    concentration: Nonnegative
    unit_token: str = Field(min_length=1)


class MaterialExposureInterval(Contract):
    exposure_id: str = Field(min_length=1)
    sequence_position: int = Field(ge=1)
    clock_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    environment_id: str = Field(min_length=1)
    media_id: str = Field(min_length=1)
    media_components: tuple[MediaComponentConcentration, ...] = Field(min_length=1)
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    temperature_unit_token: Literal["K"] = "K"
    minimum_absolute_pressure_pa: Nonnegative
    maximum_absolute_pressure_pa: Nonnegative
    pressure_unit_token: Literal["Pa_abs"] = "Pa_abs"
    mechanical_state_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_unique_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("material exposure intervals require positive duration")
        if self.maximum_temperature_k < self.minimum_temperature_k:
            raise ValueError("exposure temperature range must be ordered")
        if self.maximum_absolute_pressure_pa < self.minimum_absolute_pressure_pa:
            raise ValueError("exposure pressure range must be ordered")
        keys = [(row.component_id, row.unit_token) for row in self.media_components]
        if len(keys) != len(set(keys)):
            raise ValueError("media component and unit keys must be unique per exposure")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid material exposure requires a basis")
        return self


class MaterialPropertyObservation(Contract):
    observation_id: str = Field(min_length=1)
    material_state_id: str = Field(min_length=1)
    linked_exposure_ids: tuple[str, ...] = Field(min_length=1)
    exposure_time_s: Nonnegative
    metric_kind: Literal[
        "property_retention",
        "swelling",
        "mass_change",
        "strength",
        "user_defined",
    ]
    metric_id: str = Field(min_length=1)
    metric_definition: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    status: Literal["available", "missing", "invalid"]
    value: float | None = None
    standard_uncertainty: Nonnegative | None = None
    missing_or_invalid_basis: str | None = None
    method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_status(self):
        if len(self.linked_exposure_ids) != len(set(self.linked_exposure_ids)):
            raise ValueError("property observation exposure links must be unique")
        if self.status == "available":
            if self.value is None or self.standard_uncertainty is None or self.result_digest is None:
                raise ValueError("available property observations require value, uncertainty and digest")
        elif (
            self.value is not None
            or self.standard_uncertainty is not None
            or not self.missing_or_invalid_basis
        ):
            raise ValueError("missing or invalid property observations require a basis and no value")
        return self


class CallerEnvironmentEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    media_id: str = Field(min_length=1)
    component_id: str = Field(min_length=1)
    concentration_unit_token: str = Field(min_length=1)
    minimum_concentration: Nonnegative
    maximum_concentration: Nonnegative
    minimum_temperature_k: Positive
    maximum_temperature_k: Positive
    minimum_absolute_pressure_pa: Nonnegative
    maximum_absolute_pressure_pa: Nonnegative
    maximum_interval_duration_s: Positive
    allowed_mechanical_state_ids: tuple[str, ...] = Field(min_length=1)
    mismatch_disposition: Literal["reject", "review"]

    @model_validator(mode="after")
    def ordered_envelope(self):
        for lower, upper, label in (
            (self.minimum_concentration, self.maximum_concentration, "concentration"),
            (self.minimum_temperature_k, self.maximum_temperature_k, "temperature"),
            (self.minimum_absolute_pressure_pa, self.maximum_absolute_pressure_pa, "pressure"),
        ):
            if upper < lower:
                raise ValueError(f"environment {label} envelope must be ordered")
        return self


class PropertyEnvelopePoint(Contract):
    exposure_time_s: Nonnegative
    minimum_inclusive: float | None = None
    maximum_inclusive: float | None = None

    @model_validator(mode="after")
    def nonempty_ordered(self):
        if self.minimum_inclusive is None and self.maximum_inclusive is None:
            raise ValueError("property envelope points require at least one bound")
        if (
            self.minimum_inclusive is not None
            and self.maximum_inclusive is not None
            and self.maximum_inclusive < self.minimum_inclusive
        ):
            raise ValueError("property envelope point bounds must be ordered")
        return self


class CallerPropertyRule(Contract):
    rule_id: str = Field(min_length=1)
    metric_kind: Literal[
        "property_retention",
        "swelling",
        "mass_change",
        "strength",
        "user_defined",
    ]
    metric_id: str = Field(min_length=1)
    unit_token: str = Field(min_length=1)
    points: tuple[PropertyEnvelopePoint, ...] = Field(min_length=1)
    interpolation_policy: Literal["none", "linear"]
    uncertainty_policy: Literal["point_value", "interval_must_fit"]
    uncertainty_coverage_factor: Positive = 1.0
    missing_or_unsupported_disposition: Literal["review", "insufficient_evidence"]
    rule_description: str = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_points(self):
        times = [row.exposure_time_s for row in self.points]
        if times != sorted(times) or len(times) != len(set(times)):
            raise ValueError("property envelope point times must be unique and ordered")
        if self.interpolation_policy == "linear" and len(self.points) < 2:
            raise ValueError("linear property interpolation requires at least two points")
        return self


class CallerMaterialStateProfile(Contract):
    profile_id: str = Field(min_length=1)
    profile_revision: str = Field(min_length=1)
    source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    permitted_material_state_ids: tuple[str, ...] = Field(min_length=1)
    environment_envelopes: tuple[CallerEnvironmentEnvelope, ...] = Field(min_length=1)
    property_rules: tuple[CallerPropertyRule, ...] = Field(min_length=1)
    profile_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_profile(self):
        for values, label in (
            ([row.envelope_id for row in self.environment_envelopes], "environment envelope"),
            ([row.rule_id for row in self.property_rules], "property rule"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")
        return self


class MultiEnvironmentMaterialAssessment(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_state: MaterialStateIdentity
    exposures: tuple[MaterialExposureInterval, ...] = Field(min_length=1)
    property_observations: tuple[MaterialPropertyObservation, ...] = Field(min_length=1)
    profile: CallerMaterialStateProfile
    material_resin_matrix_fiber_reinforcement_layup_or_seal_identity_reviewed: bool
    exposure_clock_media_concentration_temperature_pressure_and_time_reviewed: bool
    property_metric_units_uncertainty_and_lineage_reviewed: bool
    caller_profile_authority_envelopes_rules_and_interpolation_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def linked_ordered_records(self):
        exposure_ids = [row.exposure_id for row in self.exposures]
        observation_ids = [row.observation_id for row in self.property_observations]
        if len(exposure_ids) != len(set(exposure_ids)):
            raise ValueError("material exposure IDs must be unique")
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("material property observation IDs must be unique")
        positions = [row.sequence_position for row in self.exposures]
        if positions != list(range(1, len(positions) + 1)):
            raise ValueError("material exposures require consecutive sequence positions")
        for first, second in zip(self.exposures, self.exposures[1:], strict=False):
            if second.start_time_s < first.end_time_s or second.clock_id != first.clock_id:
                raise ValueError("material exposures require one nonoverlapping ordered clock")
        known = set(exposure_ids)
        for row in self.property_observations:
            if row.material_state_id != self.material_state.material_state_id:
                raise ValueError("property observations must reference the material state")
            if set(row.linked_exposure_ids) - known:
                raise ValueError("property observations must link declared exposures")
        return self


class MaterialProfileFinding(Contract):
    rule_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    outcome: Literal["pass", "fail", "review", "insufficient_evidence"]
    observed_value: float | str | None
    unit_token: str
    evaluated_lower: float | None = None
    evaluated_upper: float | None = None
    basis: str = Field(min_length=1)


class MultiEnvironmentMaterialAssessmentResult(Contract):
    schema_version: Literal["matintegrity.multienvironment_material_profile.v1"] = (
        "matintegrity.multienvironment_material_profile.v1"
    )
    model_id: Literal["materials.multienvironment_material_state_profile_assessment"] = MODEL_ID
    assessment_id: str
    material_state_id: str
    profile_id: str
    profile_revision: str
    disposition: Disposition
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    findings: tuple[MaterialProfileFinding, ...]
    review_reasons: tuple[str, ...]
    insufficient_evidence_reasons: tuple[str, ...]
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    compatibility_table_or_standard_limit_claim: Literal[False] = False
    qualification_or_physical_validation_claim: Literal[False] = False
    notes: tuple[str, ...] = Field(min_length=1)

    def digest_payload(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude={"result_digest"})

    @model_validator(mode="after")
    def bound_digest(self, info: ValidationInfo):
        if (
            not (isinstance(info.context, dict) and info.context.get("allow_unbound_digest"))
            and canonical_digest(self.digest_payload()) != self.result_digest
        ):
            raise ValueError("multi-environment material result digest does not match its content")
        return self


def _bounds(rule: CallerPropertyRule, time_s: float):
    exact = next((row for row in rule.points if row.exposure_time_s == time_s), None)
    if exact is not None:
        return exact.minimum_inclusive, exact.maximum_inclusive, "exact caller table point"
    if rule.interpolation_policy == "none":
        return None
    for left, right in zip(rule.points, rule.points[1:], strict=False):
        if left.exposure_time_s < time_s < right.exposure_time_s:
            fraction = (time_s - left.exposure_time_s) / (right.exposure_time_s - left.exposure_time_s)

            def interpolate(a, b, interpolation_fraction=fraction):
                return None if a is None or b is None else a + interpolation_fraction * (b - a)

            return (
                interpolate(left.minimum_inclusive, right.minimum_inclusive),
                interpolate(left.maximum_inclusive, right.maximum_inclusive),
                "explicit caller linear interpolation",
            )
    return None


def assess_multienvironment_material(
    x: MultiEnvironmentMaterialAssessment,
) -> MultiEnvironmentMaterialAssessmentResult:
    """Aggregate exposure evidence and apply only caller-provided envelopes and interpolation."""

    p = x.profile
    reviews, insufficient, findings = [], [], []
    for reviewed, reason in (
        (x.material_state.identity_reviewed, "material-state identity was not reviewed"),
        (p.profile_reviewed, "caller material profile was not reviewed"),
        (
            x.material_resin_matrix_fiber_reinforcement_layup_or_seal_identity_reviewed,
            "material constituent, layup or seal identity was not reviewed",
        ),
        (
            x.exposure_clock_media_concentration_temperature_pressure_and_time_reviewed,
            "exposure history was not reviewed",
        ),
        (x.property_metric_units_uncertainty_and_lineage_reviewed, "property observations were not reviewed"),
        (
            x.caller_profile_authority_envelopes_rules_and_interpolation_reviewed,
            "profile authority, rules or interpolation were not reviewed",
        ),
    ):
        if not reviewed:
            insufficient.append(reason)
    if x.material_state.material_state_id not in p.permitted_material_state_ids:
        reviews.append("material-state identity is outside the caller profile")
    for exposure in x.exposures:
        if not exposure.record_valid:
            insufficient.append(f"exposure {exposure.exposure_id} is invalid")
            continue
        candidates = [
            row
            for row in p.environment_envelopes
            if row.environment_id == exposure.environment_id and row.media_id == exposure.media_id
        ]
        if len(candidates) != 1:
            insufficient.append(f"exposure {exposure.exposure_id} lacks one exact environment envelope")
            continue
        envelope = candidates[0]
        component = next(
            (
                row
                for row in exposure.media_components
                if row.component_id == envelope.component_id
                and row.unit_token == envelope.concentration_unit_token
            ),
            None,
        )
        if component is None:
            insufficient.append(f"exposure {exposure.exposure_id} lacks exact component/unit evidence")
            continue
        duration = exposure.end_time_s - exposure.start_time_s
        within = (
            envelope.minimum_concentration <= component.concentration <= envelope.maximum_concentration
            and envelope.minimum_temperature_k <= exposure.minimum_temperature_k
            and exposure.maximum_temperature_k <= envelope.maximum_temperature_k
            and envelope.minimum_absolute_pressure_pa <= exposure.minimum_absolute_pressure_pa
            and exposure.maximum_absolute_pressure_pa <= envelope.maximum_absolute_pressure_pa
            and duration <= envelope.maximum_interval_duration_s
            and exposure.mechanical_state_id in envelope.allowed_mechanical_state_ids
        )
        outcome = "pass" if within else envelope.mismatch_disposition
        if outcome == "review":
            reviews.append(f"exposure {exposure.exposure_id} is outside its caller envelope")
        findings.append(
            MaterialProfileFinding(
                rule_id=envelope.envelope_id,
                target_id=exposure.exposure_id,
                outcome=outcome if outcome != "reject" else "fail",
                observed_value=component.concentration,
                unit_token=component.unit_token,
                basis="caller multi-environment state envelope",
            )
        )
    for rule in p.property_rules:
        matches = [
            row
            for row in x.property_observations
            if row.metric_kind == rule.metric_kind
            and row.metric_id == rule.metric_id
            and row.unit_token == rule.unit_token
        ]
        if not matches:
            insufficient.append(f"{rule.rule_id} lacks an exact metric/unit observation")
            continue
        for row in matches:
            if row.status != "available":
                outcome = rule.missing_or_unsupported_disposition
                (reviews if outcome == "review" else insufficient).append(
                    f"{rule.rule_id}:{row.observation_id} is unavailable"
                )
                findings.append(
                    MaterialProfileFinding(
                        rule_id=rule.rule_id,
                        target_id=row.observation_id,
                        outcome=outcome,
                        observed_value=None,
                        unit_token=rule.unit_token,
                        basis="property observation unavailable",
                    )
                )
                continue
            bounds = _bounds(rule, row.exposure_time_s)
            if bounds is None:
                outcome = rule.missing_or_unsupported_disposition
                (reviews if outcome == "review" else insufficient).append(
                    f"{rule.rule_id}:{row.observation_id} time is unsupported"
                )
                findings.append(
                    MaterialProfileFinding(
                        rule_id=rule.rule_id,
                        target_id=row.observation_id,
                        outcome=outcome,
                        observed_value=row.value,
                        unit_token=rule.unit_token,
                        basis="no exact point and interpolation not explicitly supported",
                    )
                )
                continue
            minimum, maximum, basis = bounds
            span = (
                rule.uncertainty_coverage_factor * row.standard_uncertainty
                if rule.uncertainty_policy == "interval_must_fit"
                else 0.0
            )
            low, high = row.value - span, row.value + span
            within = (minimum is None or low >= minimum) and (maximum is None or high <= maximum)
            findings.append(
                MaterialProfileFinding(
                    rule_id=rule.rule_id,
                    target_id=row.observation_id,
                    outcome="pass" if within else "fail",
                    observed_value=row.value,
                    unit_token=rule.unit_token,
                    evaluated_lower=low,
                    evaluated_upper=high,
                    basis=f"{basis}; {rule.uncertainty_policy}",
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
        "material_state_id": x.material_state.material_state_id,
        "profile_id": p.profile_id,
        "profile_revision": p.profile_revision,
        "disposition": disposition,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
        "findings": tuple(findings),
        "review_reasons": tuple(dict.fromkeys(reviews)),
        "insufficient_evidence_reasons": tuple(dict.fromkeys(insufficient)),
        "notes": (
            "Only caller-owned environment and property envelopes are applied; interpolation occurs only when explicitly set to linear.",
            "Polymer, seal and composite constituent identities, ordered exposures and measured facts retain exact units, uncertainty and lineage.",
            "No compatibility table, standard limit, qualification, degradation forecast, service life or failure probability is claimed.",
        ),
    }
    unsigned = MultiEnvironmentMaterialAssessmentResult.model_validate(
        {**values, "result_digest": "0" * 64}, context={"allow_unbound_digest": True}
    )
    return MultiEnvironmentMaterialAssessmentResult.model_validate(
        {**values, "result_digest": canonical_digest(unsigned.digest_payload())}
    )
