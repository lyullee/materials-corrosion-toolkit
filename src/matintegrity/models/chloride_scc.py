"""Chloride-SCC applicability against caller-owned qualification evidence."""

from __future__ import annotations

import math
from bisect import bisect_right
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive, RunContext, canonical_digest
from ..registry import ModelSpec


class ChlorideSCCExposure(Contract):
    exposure_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    chloride_concentration: Nonnegative
    chloride_unit: str = Field(min_length=1)
    temperature_K: Positive
    pH: float = Field(ge=0, le=14)
    oxidizing_basis: Literal["dissolved_oxygen", "descriptor"]
    dissolved_oxygen_concentration: Nonnegative | None = None
    dissolved_oxygen_unit: str | None = None
    oxidizing_state_descriptor: str | None = None
    applied_stress_descriptor: str = Field(min_length=1)
    residual_stress_descriptor: str = Field(min_length=1)
    record_valid: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def duration_and_oxidizing_basis(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("chloride-SCC exposure interval must have positive duration")
        if self.oxidizing_basis == "dissolved_oxygen":
            if self.dissolved_oxygen_concentration is None or not self.dissolved_oxygen_unit:
                raise ValueError("dissolved-oxygen basis requires a concentration and exact unit")
            if self.oxidizing_state_descriptor is not None:
                raise ValueError("dissolved-oxygen and descriptor bases cannot be mixed")
        else:
            if not self.oxidizing_state_descriptor:
                raise ValueError("descriptor basis requires an oxidizing-state descriptor")
            if self.dissolved_oxygen_concentration is not None or self.dissolved_oxygen_unit is not None:
                raise ValueError("descriptor and dissolved-oxygen bases cannot be mixed")
        return self


class ChlorideSCCTestEvidence(Contract):
    evidence_record_id: str = Field(min_length=1)
    test_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    record_valid: bool
    supports_declared_envelope: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ChlorideSCCEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    chloride_unit: str = Field(min_length=1)
    minimum_chloride_concentration: Nonnegative
    maximum_chloride_concentration: Nonnegative
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pH: float = Field(ge=0, le=14)
    maximum_pH: float = Field(ge=0, le=14)
    oxidizing_basis: Literal["dissolved_oxygen", "descriptor"]
    dissolved_oxygen_unit: str | None = None
    minimum_dissolved_oxygen_concentration: Nonnegative | None = None
    maximum_dissolved_oxygen_concentration: Nonnegative | None = None
    supported_oxidizing_state_descriptors: tuple[str, ...] = ()
    supported_applied_stress_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_residual_stress_descriptors: tuple[str, ...] = Field(min_length=1)
    maximum_cumulative_exposure_s: Positive
    test_evidence: tuple[ChlorideSCCTestEvidence, ...] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bounds_and_basis(self):
        for lower, upper, name in (
            (
                self.minimum_chloride_concentration,
                self.maximum_chloride_concentration,
                "chloride",
            ),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_pH, self.maximum_pH, "pH"),
        ):
            if upper < lower:
                raise ValueError(f"{name} envelope bounds must be ordered")
        if self.oxidizing_basis == "dissolved_oxygen":
            if (
                not self.dissolved_oxygen_unit
                or self.minimum_dissolved_oxygen_concentration is None
                or self.maximum_dissolved_oxygen_concentration is None
            ):
                raise ValueError("dissolved-oxygen envelope requires bounds and an exact unit")
            if self.maximum_dissolved_oxygen_concentration < self.minimum_dissolved_oxygen_concentration:
                raise ValueError("dissolved-oxygen envelope bounds must be ordered")
            if self.supported_oxidizing_state_descriptors:
                raise ValueError("dissolved-oxygen envelope cannot also contain state descriptors")
        else:
            if not self.supported_oxidizing_state_descriptors:
                raise ValueError("descriptor envelope requires at least one supported state")
            if (
                self.dissolved_oxygen_unit is not None
                or self.minimum_dissolved_oxygen_concentration is not None
                or self.maximum_dissolved_oxygen_concentration is not None
            ):
                raise ValueError("descriptor envelope cannot contain dissolved-oxygen bounds")
        record_ids = [record.evidence_record_id for record in self.test_evidence]
        specimen_ids = [record.specimen_id for record in self.test_evidence]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("chloride-SCC evidence record identifiers must be unique")
        if len(specimen_ids) != len(set(specimen_ids)):
            raise ValueError("chloride-SCC specimen identifiers must be unique")
        return self


class ChlorideSCCApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    exposures: tuple[ChlorideSCCExposure, ...] = Field(min_length=1)
    qualification_envelope: ChlorideSCCEnvelope
    material_and_metallurgy_reviewed: bool
    concentration_units_reviewed: bool
    environment_records_reviewed: bool
    stress_descriptors_reviewed: bool
    clock_and_duration_reviewed: bool
    qualification_evidence_reviewed: bool

    @model_validator(mode="after")
    def exposure_clock(self):
        identifiers = [exposure.exposure_id for exposure in self.exposures]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("chloride-SCC exposure identifiers must be unique")
        for first, second in zip(self.exposures, self.exposures[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("chloride-SCC exposure intervals must be ordered and cannot overlap")
        return self


def chloride_scc_applicability(x: ChlorideSCCApplicability) -> Calculation:
    envelope = x.qualification_envelope
    missing_reviews = [
        name
        for name, reviewed in (
            ("material_and_metallurgy", x.material_and_metallurgy_reviewed),
            ("concentration_units", x.concentration_units_reviewed),
            ("environment_records", x.environment_records_reviewed),
            ("stress_descriptors", x.stress_descriptors_reviewed),
            ("clock_and_duration", x.clock_and_duration_reviewed),
            ("qualification_evidence", x.qualification_evidence_reviewed),
        )
        if not reviewed
    ]
    identity_mismatches = []
    if x.material_condition_id != envelope.material_condition_id:
        identity_mismatches.append("material_condition_id")
    if x.metallurgy_id != envelope.metallurgy_id:
        identity_mismatches.append("metallurgy_id")
    invalid_exposure_ids = [exposure.exposure_id for exposure in x.exposures if not exposure.record_valid]
    unit_or_basis_mismatches = []
    for exposure in x.exposures:
        fields = []
        if exposure.chloride_unit != envelope.chloride_unit:
            fields.append("chloride_unit")
        if exposure.oxidizing_basis != envelope.oxidizing_basis:
            fields.append("oxidizing_basis")
        elif exposure.oxidizing_basis == "dissolved_oxygen":
            if exposure.dissolved_oxygen_unit != envelope.dissolved_oxygen_unit:
                fields.append("dissolved_oxygen_unit")
        if fields:
            unit_or_basis_mismatches.append({"exposure_id": exposure.exposure_id, "fields": fields})

    invalid_evidence_ids = []
    evidence_identity_mismatches = []
    for record in envelope.test_evidence:
        if not record.record_valid or not record.supports_declared_envelope:
            invalid_evidence_ids.append(record.evidence_record_id)
        fields = []
        if record.material_condition_id != envelope.material_condition_id:
            fields.append("material_condition_id")
        if record.metallurgy_id != envelope.metallurgy_id:
            fields.append("metallurgy_id")
        if fields:
            evidence_identity_mismatches.append(
                {"evidence_record_id": record.evidence_record_id, "fields": fields}
            )

    if (
        missing_reviews
        or identity_mismatches
        or invalid_exposure_ids
        or unit_or_basis_mismatches
        or invalid_evidence_ids
        or evidence_identity_mismatches
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatches,
                "invalid_exposure_ids": invalid_exposure_ids,
                "unit_or_basis_mismatches": unit_or_basis_mismatches,
                "invalid_test_evidence_ids": invalid_evidence_ids,
                "test_evidence_identity_mismatches": evidence_identity_mismatches,
            },
            notes=(
                "Applicability is withheld until identities, exact units, records and test evidence are complete.",
            ),
        )

    comparisons = []
    outside_exposure_ids = []
    cumulative_exposure = 0.0
    for exposure in x.exposures:
        duration = exposure.end_time_s - exposure.start_time_s
        cumulative_exposure += duration
        unsupported = []
        if not (
            envelope.minimum_chloride_concentration
            <= exposure.chloride_concentration
            <= envelope.maximum_chloride_concentration
        ):
            unsupported.append("chloride_concentration")
        if not envelope.minimum_temperature_K <= exposure.temperature_K <= envelope.maximum_temperature_K:
            unsupported.append("temperature")
        if not envelope.minimum_pH <= exposure.pH <= envelope.maximum_pH:
            unsupported.append("pH")
        if envelope.oxidizing_basis == "dissolved_oxygen":
            if not (
                envelope.minimum_dissolved_oxygen_concentration
                <= exposure.dissolved_oxygen_concentration
                <= envelope.maximum_dissolved_oxygen_concentration
            ):
                unsupported.append("dissolved_oxygen_concentration")
        elif exposure.oxidizing_state_descriptor not in envelope.supported_oxidizing_state_descriptors:
            unsupported.append("oxidizing_state_descriptor")
        if exposure.applied_stress_descriptor not in envelope.supported_applied_stress_descriptors:
            unsupported.append("applied_stress_descriptor")
        if exposure.residual_stress_descriptor not in envelope.supported_residual_stress_descriptors:
            unsupported.append("residual_stress_descriptor")
        if unsupported:
            outside_exposure_ids.append(exposure.exposure_id)
        comparisons.append(
            {
                "exposure_id": exposure.exposure_id,
                "duration_s": duration,
                "unsupported_fields": unsupported,
                "within_declared_support": not unsupported,
            }
        )

    cumulative_supported = cumulative_exposure <= envelope.maximum_cumulative_exposure_s
    values = {
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "exposure_comparisons": comparisons,
        "cumulative_exposure_s": cumulative_exposure,
        "remaining_supported_exposure_s": envelope.maximum_cumulative_exposure_s - cumulative_exposure,
        "cumulative_exposure_within_support": cumulative_supported,
        "outside_support_exposure_ids": outside_exposure_ids,
        "test_evidence_summary": {
            "record_ids": [record.evidence_record_id for record in envelope.test_evidence],
            "test_ids": sorted({record.test_id for record in envelope.test_evidence}),
            "specimen_ids": [record.specimen_id for record in envelope.test_evidence],
            "source_group_ids": sorted({record.source_group_id for record in envelope.test_evidence}),
        },
    }
    if outside_exposure_ids or not cumulative_supported:
        return Calculation(
            status="out_of_scope",
            values=values,
            notes=(
                "At least one reviewed service condition lies outside the caller-declared qualification support.",
                "No SCC initiation, crack growth, lifetime, probability or acceptance conclusion is produced.",
            ),
        )
    values["declared_applicability_outcome"] = "within_support"
    return Calculation(
        values=values,
        notes=(
            "Within-support means only that reviewed inputs lie inside the caller-owned evidence envelope.",
            "No SCC initiation, crack growth, lifetime, probability or acceptance conclusion is produced.",
        ),
    )


SCC_CRACK_VELOCITY_SOURCE_ID = "caller_reviewed_scc_crack_velocity_time_integration"
SCC_CRACK_VELOCITY_MAX_OPERATIONS = 2_000_000


class SCCCrackVelocityLaw(Contract):
    """Caller-owned mode-I crack-velocity curve for one material/environment state."""

    curve_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    loading_basis_id: str = Field(min_length=1)
    threshold_K_I_Pa_sqrt_m: Nonnegative
    K_I_Pa_sqrt_m: tuple[Nonnegative, ...] = Field(min_length=2, max_length=1000)
    crack_velocity_m_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=1000)
    source_file_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    table_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    rights_boundary: Literal["local_only", "caller_authorized_open_distribution"]
    rights_authorization_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    applicability_review_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_curve(self):
        if any(not value.strip() for value in (
            self.curve_id, self.source_group_id, self.material_condition_id,
            self.metallurgy_id, self.environment_id, self.loading_basis_id,
            self.applicability_review_id,
        )):
            raise ValueError("curve and applicability identity fields cannot be blank")
        if len(self.K_I_Pa_sqrt_m) != len(self.crack_velocity_m_s):
            raise ValueError("K_I and crack-velocity arrays must have identical length")
        if any(b <= a for a, b in zip(self.K_I_Pa_sqrt_m[:-1], self.K_I_Pa_sqrt_m[1:], strict=True)):
            raise ValueError("K_I table must be strictly increasing")
        if self.threshold_K_I_Pa_sqrt_m != self.K_I_Pa_sqrt_m[0] or self.crack_velocity_m_s[0] != 0.0:
            raise ValueError("first curve point must be the declared zero-velocity SCC threshold")
        table = {
            "curve_id": self.curve_id,
            "source_group_id": self.source_group_id,
            "material_condition_id": self.material_condition_id,
            "metallurgy_id": self.metallurgy_id,
            "environment_id": self.environment_id,
            "loading_basis_id": self.loading_basis_id,
            "threshold_K_I_Pa_sqrt_m": self.threshold_K_I_Pa_sqrt_m,
            "K_I_Pa_sqrt_m": list(self.K_I_Pa_sqrt_m),
            "crack_velocity_m_s": list(self.crack_velocity_m_s),
        }
        if canonical_digest(table) != self.table_sha256:
            raise ValueError("table_sha256 must bind the ordered curve and applicability identities")
        if not any(
            row.source_id == SCC_CRACK_VELOCITY_SOURCE_ID
            and row.sha256 == self.source_file_sha256
            and row.license_id
            for row in self.evidence
        ):
            raise ValueError("curve Evidence must pin the source file and carry a license identifier")
        if self.rights_boundary == "caller_authorized_open_distribution" and not self.rights_authorization_sha256:
            raise ValueError("open distribution requires a caller-supplied rights authorization digest")
        if self.rights_boundary == "local_only" and self.rights_authorization_sha256 is not None:
            raise ValueError("local-only data cannot carry an open-distribution authorization digest")
        if not self.applicability_review_id.strip():
            raise ValueError("a material/environment applicability review ID is required")
        return self


class SCCCrackVelocityHistoryRequest(Contract):
    """Finite-time integration of a tabulated SCC da/dt law over caller-supplied K_I."""

    schema_version: Literal["matintegrity.scc_crack_velocity_history.v1"] = (
        "matintegrity.scc_crack_velocity_history.v1"
    )
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    specimen_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    metallurgy_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    loading_basis_id: str = Field(min_length=1)
    initial_crack_advance_m: Nonnegative = 0.0
    time_s: tuple[Nonnegative, ...] = Field(min_length=2, max_length=20_000)
    K_I_Pa_sqrt_m: tuple[Nonnegative, ...] = Field(min_length=2, max_length=20_000)
    K_I_history_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    history_evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    law: SCCCrackVelocityLaw
    stress_intensity_history_piecewise_linear_reviewed: bool
    interpolation_linear_in_K_I_and_velocity_reviewed: bool
    fixed_environment_and_loading_state_reviewed: bool
    crack_geometry_feedback_excluded_reviewed: bool
    maximum_operations: int = Field(gt=0, le=SCC_CRACK_VELOCITY_MAX_OPERATIONS)
    computation_budget_reviewed: bool

    @model_validator(mode="after")
    def validate_history(self):
        if any(not value.strip() for value in (
            self.assessment_id, self.asset_id, self.location_id, self.physical_scope_id,
            self.specimen_id, self.clock_id, self.material_condition_id,
            self.metallurgy_id, self.environment_id, self.loading_basis_id,
        )):
            raise ValueError("assessment, physical and service identity fields cannot be blank")
        if len(self.time_s) != len(self.K_I_Pa_sqrt_m):
            raise ValueError("time and K_I arrays must align")
        if self.time_s[0] != 0.0 or any(
            b <= a for a, b in zip(self.time_s[:-1], self.time_s[1:], strict=True)
        ):
            raise ValueError("time knots must start at zero and increase strictly")
        history = {
            "asset_id": self.asset_id,
            "location_id": self.location_id,
            "physical_scope_id": self.physical_scope_id,
            "specimen_id": self.specimen_id,
            "clock_id": self.clock_id,
            "time_s": list(self.time_s),
            "K_I_Pa_sqrt_m": list(self.K_I_Pa_sqrt_m),
        }
        if canonical_digest(history) != self.K_I_history_sha256:
            raise ValueError("K_I_history_sha256 must bind ordered scope/specimen/clock/time/K_I records")
        if not any(
            row.source_id == SCC_CRACK_VELOCITY_SOURCE_ID
            and row.sha256 == self.K_I_history_sha256
            and row.license_id
            for row in self.history_evidence
        ):
            raise ValueError("history Evidence must pin the K_I record and carry a license identifier")
        for name in ("material_condition_id", "metallurgy_id", "environment_id", "loading_basis_id"):
            if getattr(self, name) != getattr(self.law, name):
                raise ValueError(f"history {name} must exactly match the crack-velocity law")
        if (len(self.time_s) - 1) * len(self.law.K_I_Pa_sqrt_m) > self.maximum_operations:
            raise ValueError("time-by-curve operation estimate exceeds the declared budget")
        if not all((
            self.stress_intensity_history_piecewise_linear_reviewed,
            self.interpolation_linear_in_K_I_and_velocity_reviewed,
            self.fixed_environment_and_loading_state_reviewed,
            self.crack_geometry_feedback_excluded_reviewed,
            self.computation_budget_reviewed,
        )):
            raise ValueError("history, interpolation, state, geometry and budget reviews are required")
        return self


def _scc_velocity_at_K_I(law: SCCCrackVelocityLaw, value: float) -> float:
    if value <= law.threshold_K_I_Pa_sqrt_m:
        return 0.0
    axis, rates = law.K_I_Pa_sqrt_m, law.crack_velocity_m_s
    if value > axis[-1]:
        raise ValueError("K_I lies above the tabulated crack-velocity support")
    index = min(bisect_right(axis, value) - 1, len(axis) - 2)
    fraction = (value - axis[index]) / (axis[index + 1] - axis[index])
    return rates[index] + fraction * (rates[index + 1] - rates[index])


def scc_crack_velocity_history(x: SCCCrackVelocityHistoryRequest) -> Calculation:
    """Integrate caller-owned SCC velocity data along a fixed-state finite K_I history."""
    digest = canonical_digest(x.model_dump(mode="json"))
    upper = x.law.K_I_Pa_sqrt_m[-1]
    outside = [i for i, value in enumerate(x.K_I_Pa_sqrt_m) if value > x.law.threshold_K_I_Pa_sqrt_m and value > upper]
    if outside:
        return Calculation(status="out_of_scope", values={
            "model_id": "degradation.scc_crack_velocity_history",
            "assessment_id": x.assessment_id,
            "request_sha256": digest,
            "unsupported_K_I_history_indices": outside,
            "curve_support_maximum_Pa_sqrt_m": upper,
            "committed": False,
        }, notes=("No extrapolation beyond the supplied curve is performed; no partial growth is returned.",))

    advance = x.initial_crack_advance_m
    advance_by_knot = [advance]
    results = []
    axis = x.law.K_I_Pa_sqrt_m
    for j, (t0, t1, k0, k1) in enumerate(zip(
        x.time_s[:-1], x.time_s[1:], x.K_I_Pa_sqrt_m[:-1], x.K_I_Pa_sqrt_m[1:], strict=True
    )):
        duration = t1 - t0
        fractions = [0.0, 1.0]
        if k1 != k0:
            low, high = min(k0, k1), max(k0, k1)
            fractions.extend((knot - k0) / (k1 - k0) for knot in axis if low < knot < high)
        fractions.sort()
        increment = 0.0
        for u0, u1 in zip(fractions[:-1], fractions[1:], strict=True):
            left_K, right_K = k0 + (k1 - k0) * u0, k0 + (k1 - k0) * u1
            left_v, right_v = _scc_velocity_at_K_I(x.law, left_K), _scc_velocity_at_K_I(x.law, right_K)
            increment += duration * (u1 - u0) * (left_v + right_v) * 0.5
        if not math.isfinite(increment) or increment < 0.0:
            return Calculation(status="out_of_scope", values={
                "model_id": "degradation.scc_crack_velocity_history",
                "assessment_id": x.assessment_id,
                "request_sha256": digest,
                "failed_interval_index": j,
                "reason": "nonfinite_or_negative_growth_increment",
                "committed": False,
            })
        advance += increment
        advance_by_knot.append(advance)
        results.append({
            "interval_index": j,
            "start_time_s": t0,
            "end_time_s": t1,
            "K_I_start_Pa_sqrt_m": k0,
            "K_I_end_Pa_sqrt_m": k1,
            "crack_advance_increment_m": increment,
            "mean_crack_velocity_m_s": increment / duration,
            "cumulative_crack_advance_m": advance,
        })
    return Calculation(values={
        "model_id": "degradation.scc_crack_velocity_history",
        "assessment_id": x.assessment_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "request_sha256": digest,
        "curve_id": x.law.curve_id,
        "table_sha256": x.law.table_sha256,
        "K_I_history_sha256": x.K_I_history_sha256,
        "material_condition_id": x.material_condition_id,
        "metallurgy_id": x.metallurgy_id,
        "environment_id": x.environment_id,
        "loading_basis_id": x.loading_basis_id,
        "time_s": list(x.time_s),
        "K_I_Pa_sqrt_m": list(x.K_I_Pa_sqrt_m),
        "crack_advance_m_by_knot": advance_by_knot,
        "interval_results": results,
        "table_interpolation": "piecewise_linear_K_I_and_velocity",
        "time_history_interpolation": "piecewise_linear_K_I",
        "geometry_feedback_included": False,
        "growth_probability_inferred": False,
        "qualification_claimed": False,
    }, notes=(
        "Within each time interval, piecewise-linear K_I history is split at every crossed law knot; the resulting piecewise-linear velocity is integrated exactly by trapezoids.",
        "No crack geometry feedback, environment transition, extrapolation, SCC initiation, toughness, probability, life qualification or acceptance is inferred.",
        "Below threshold only this caller-supplied SCC growth branch is zero; this does not imply absence of other degradation.",
    ))


def _validate_scc_crack_velocity_context(
    request: SCCCrackVelocityHistoryRequest, context: RunContext
) -> None:
    if (request.asset_id, request.location_id, request.clock_id) != (
        context.asset_id, context.location_id, context.time_basis
    ):
        raise ValueError("SCC crack-velocity request asset, location and clock must match RunContext")


def specifications():
    return [
        ModelSpec(
            "degradation.chloride_scc_applicability",
            ChlorideSCCApplicability,
            chloride_scc_applicability,
            {
                "assessment_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "exposure_comparisons": "1",
                "cumulative_exposure_s": "s",
                "remaining_supported_exposure_s": "s",
                "cumulative_exposure_within_support": "1",
                "outside_support_exposure_ids": "1",
                "test_evidence_summary": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Material condition and metallurgy identities must match the caller-owned test envelope exactly.",
                "Chloride and dissolved-oxygen values are compared only when their unit tokens match exactly; no hidden conversion is performed.",
                "Applied and residual stress states are caller-defined descriptors, not calculated stresses or thresholds.",
            ),
            ("declared_chloride_scc_qualification_envelope",),
        ),
        ModelSpec(
            "degradation.scc_crack_velocity_history",
            SCCCrackVelocityHistoryRequest,
            scc_crack_velocity_history,
            {
                "time_s": "s",
                "K_I_Pa_sqrt_m": "Pa*sqrt(m)",
                "crack_advance_m_by_knot[]": "m",
                "interval_results[].crack_advance_increment_m": "m",
                "interval_results[].mean_crack_velocity_m_s": "m/s",
            },
            (
                "One caller-owned material/metallurgy/environment/loading state and thresholded K_I-to-da/dt law apply over the finite history.",
                "K_I is supplied by the caller and linearly interpolated between knots; crack geometry and K_I are not updated from computed advance.",
                "Crack velocity is interpolated linearly in K_I without extrapolation and remains a user model rather than qualified service behavior.",
            ),
            (SCC_CRACK_VELOCITY_SOURCE_ID,),
            qualification="user_model",
            context_validator=_validate_scc_crack_velocity_context,
        )
    ]
