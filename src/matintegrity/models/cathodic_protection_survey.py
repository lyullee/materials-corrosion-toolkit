"""Cathodic-protection field survey evidence and arithmetic summaries."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class ReferenceElectrodeCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    reference_electrode_id: str = Field(min_length=1)
    reference_electrode_type_id: str = Field(min_length=1)
    minimum_supported_temperature_K: Positive
    maximum_supported_temperature_K: Positive
    reported_offset_V: float
    expanded_uncertainty_V: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_calibration(self):
        if self.maximum_supported_temperature_K < self.minimum_supported_temperature_K:
            raise ValueError("reference-electrode calibration temperature bounds must be ordered")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid reference-electrode calibration requires a basis")
        return self


class CathodicPotentialObservation(Contract):
    observation_id: str = Field(min_length=1)
    structure_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    measurement_location_id: str = Field(min_length=1)
    location_definition: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    potential_convention: Literal["native", "on", "off", "instant_off"]
    reference_electrode_id: str = Field(min_length=1)
    calibration_id: str = Field(min_length=1)
    potential_V: float | None = None
    expanded_uncertainty_V: Nonnegative | None = None
    ir_drop_handling_status: Literal[
        "not_applicable",
        "not_corrected",
        "caller_corrected",
        "instant_off_used",
        "unknown",
    ]
    specimen_temperature_K: Positive
    electrolyte_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    record_status: Literal["observed", "missing", "invalid"]
    missing_or_invalid_basis: str | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_observation(self):
        if self.record_status == "observed":
            if self.potential_V is None or self.expanded_uncertainty_V is None or self.result_digest is None:
                raise ValueError("observed cathodic potential records require value, uncertainty and digest")
        else:
            if self.potential_V is not None or self.expanded_uncertainty_V is not None:
                raise ValueError("missing or invalid cathodic potential records cannot carry a value")
            if not self.missing_or_invalid_basis:
                raise ValueError("missing or invalid cathodic potential records require a basis")
        return self


class CathodicCurrentObservation(Contract):
    observation_id: str = Field(min_length=1)
    structure_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    source_kind: Literal["rectifier", "anode"]
    source_id: str = Field(min_length=1)
    measurement_location_id: str = Field(min_length=1)
    elapsed_time_s: Nonnegative
    current_A: float | None = None
    expanded_uncertainty_A: Nonnegative | None = None
    current_sign_basis: str = Field(min_length=1)
    specimen_temperature_K: Positive
    electrolyte_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    record_status: Literal["observed", "missing", "invalid"]
    missing_or_invalid_basis: str | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_observation(self):
        if self.record_status == "observed":
            if self.current_A is None or self.expanded_uncertainty_A is None or self.result_digest is None:
                raise ValueError("observed cathodic current records require value, uncertainty and digest")
        else:
            if self.current_A is not None or self.expanded_uncertainty_A is not None:
                raise ValueError("missing or invalid cathodic current records cannot carry a value")
            if not self.missing_or_invalid_basis:
                raise ValueError("missing or invalid cathodic current records require a basis")
        return self


class CallerPotentialThreshold(Contract):
    threshold_id: str = Field(min_length=1)
    potential_convention: Literal["native", "on", "off", "instant_off"]
    reference_electrode_id: str = Field(min_length=1)
    comparison_direction: Literal["at_or_more_negative", "at_or_more_positive"]
    threshold_V: float
    threshold_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class CathodicProtectionFieldSurvey(Contract):
    survey_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    structure_id: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    electrolyte_id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    reference_calibrations: tuple[ReferenceElectrodeCalibration, ...] = Field(min_length=1)
    potential_observations: tuple[CathodicPotentialObservation, ...] = Field(min_length=1)
    current_observations: tuple[CathodicCurrentObservation, ...] = ()
    caller_thresholds: tuple[CallerPotentialThreshold, ...] = ()
    structure_zone_reference_and_location_identity_reviewed: bool
    reference_electrode_calibrations_reviewed: bool
    potential_conventions_and_clock_reviewed: bool
    rectifier_anode_current_and_sign_basis_reviewed: bool
    ir_drop_handling_status_reviewed: bool
    temperature_electrolyte_and_environment_reviewed: bool
    uncertainty_provider_and_result_digests_reviewed: bool
    missing_and_invalid_records_reviewed: bool
    caller_threshold_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_ordered_records(self):
        for values, label in (
            ([row.calibration_id for row in self.reference_calibrations], "calibration"),
            ([row.observation_id for row in self.potential_observations], "potential observation"),
            ([row.observation_id for row in self.current_observations], "current observation"),
            ([row.threshold_id for row in self.caller_thresholds], "threshold"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"cathodic-protection {label} identifiers must be unique")
        for records, label in (
            (self.potential_observations, "potential"),
            (self.current_observations, "current"),
        ):
            times = [row.elapsed_time_s for row in records]
            if any(second < first for first, second in zip(times, times[1:], strict=False)):
                raise ValueError(f"cathodic-protection {label} records must be time ordered")
        return self


def cathodic_protection_field_survey(x: CathodicProtectionFieldSurvey) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "structure_zone_reference_and_location_identity_reviewed",
            "reference_electrode_calibrations_reviewed",
            "potential_conventions_and_clock_reviewed",
            "rectifier_anode_current_and_sign_basis_reviewed",
            "ir_drop_handling_status_reviewed",
            "temperature_electrolyte_and_environment_reviewed",
            "uncertainty_provider_and_result_digests_reviewed",
            "missing_and_invalid_records_reviewed",
            "caller_threshold_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_calibration_ids = [row.calibration_id for row in x.reference_calibrations if not row.record_valid]
    missing_or_invalid_potential_ids = [
        row.observation_id for row in x.potential_observations if row.record_status != "observed"
    ]
    missing_or_invalid_current_ids = [
        row.observation_id for row in x.current_observations if row.record_status != "observed"
    ]
    identity_mismatch_ids = [
        row.observation_id
        for row in (*x.potential_observations, *x.current_observations)
        if row.structure_id != x.structure_id
        or row.zone_id != x.zone_id
        or row.electrolyte_id != x.electrolyte_id
        or row.environment_id != x.environment_id
    ]
    calibration_by_id = {row.calibration_id: row for row in x.reference_calibrations}
    unlinked_potential_ids = [
        row.observation_id
        for row in x.potential_observations
        if row.calibration_id not in calibration_by_id
        or (
            row.calibration_id in calibration_by_id
            and row.reference_electrode_id != calibration_by_id[row.calibration_id].reference_electrode_id
        )
    ]
    if (
        missing_reviews
        or invalid_calibration_ids
        or missing_or_invalid_potential_ids
        or missing_or_invalid_current_ids
        or identity_mismatch_ids
        or unlinked_potential_ids
    ):
        return Calculation(
            status="needs_data",
            values={
                "survey_id": x.survey_id,
                "missing_reviews": missing_reviews,
                "invalid_calibration_ids": invalid_calibration_ids,
                "missing_or_invalid_potential_ids": missing_or_invalid_potential_ids,
                "missing_or_invalid_current_ids": missing_or_invalid_current_ids,
                "identity_mismatch_observation_ids": identity_mismatch_ids,
                "unlinked_potential_observation_ids": unlinked_potential_ids,
            },
            notes=(
                "Missing and invalid field records remain explicit and prevent a complete survey summary.",
            ),
        )

    outside_calibration_temperature_ids = [
        row.observation_id
        for row in x.potential_observations
        if not calibration_by_id[row.calibration_id].minimum_supported_temperature_K
        <= row.specimen_temperature_K
        <= calibration_by_id[row.calibration_id].maximum_supported_temperature_K
    ]
    if outside_calibration_temperature_ids:
        return Calculation(
            status="out_of_scope",
            values={
                "survey_id": x.survey_id,
                "outside_calibration_temperature_observation_ids": outside_calibration_temperature_ids,
            },
            notes=("Reference-electrode calibration temperature support is not extrapolated.",),
        )

    potential_summary = []
    for convention in ("native", "on", "off", "instant_off"):
        rows = [row for row in x.potential_observations if row.potential_convention == convention]
        if not rows:
            continue
        values = [row.potential_V for row in rows]
        potential_summary.append(
            {
                "potential_convention": convention,
                "observation_count": len(rows),
                "arithmetic_mean_potential_V": sum(values) / len(values),
                "minimum_potential_V": min(values),
                "maximum_potential_V": max(values),
                "observation_ids": [row.observation_id for row in rows],
            }
        )
    current_summary = []
    for source_kind in ("rectifier", "anode"):
        rows = [row for row in x.current_observations if row.source_kind == source_kind]
        if not rows:
            continue
        values = [row.current_A for row in rows]
        current_summary.append(
            {
                "source_kind": source_kind,
                "observation_count": len(rows),
                "arithmetic_mean_current_A": sum(values) / len(values),
                "minimum_current_A": min(values),
                "maximum_current_A": max(values),
                "observation_ids": [row.observation_id for row in rows],
            }
        )
    threshold_margins = []
    for threshold in x.caller_thresholds:
        for row in x.potential_observations:
            if (
                row.potential_convention != threshold.potential_convention
                or row.reference_electrode_id != threshold.reference_electrode_id
            ):
                continue
            margin = (
                threshold.threshold_V - row.potential_V
                if threshold.comparison_direction == "at_or_more_negative"
                else row.potential_V - threshold.threshold_V
            )
            threshold_margins.append(
                {
                    "threshold_id": threshold.threshold_id,
                    "observation_id": row.observation_id,
                    "potential_convention": row.potential_convention,
                    "comparison_direction": threshold.comparison_direction,
                    "observed_potential_V": row.potential_V,
                    "threshold_V": threshold.threshold_V,
                    "signed_margin_toward_declared_direction_V": margin,
                }
            )
    return Calculation(
        status="computed",
        values={
            "survey_id": x.survey_id,
            "physical_scope_id": x.physical_scope_id,
            "structure_id": x.structure_id,
            "zone_id": x.zone_id,
            "clock_id": x.clock_id,
            "potential_summary_by_native_convention": potential_summary,
            "current_summary_by_source_kind": current_summary,
            "potential_threshold_margins": threshold_margins,
            "ir_drop_handling_records": [
                {
                    "observation_id": row.observation_id,
                    "potential_convention": row.potential_convention,
                    "ir_drop_handling_status": row.ir_drop_handling_status,
                }
                for row in x.potential_observations
            ],
        },
        notes=(
            "Native, on, off and instant-off potentials remain separate native conventions; no IR-drop correction is invented.",
            "Caller thresholds produce signed arithmetic margins only, not automatic compliance or a built-in protection criterion.",
            "Potential/current summaries do not infer coating condition, remaining life or failure probability.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("cathodic-protection survey asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.cathodic_protection_field_survey",
            CathodicProtectionFieldSurvey,
            cathodic_protection_field_survey,
            {
                "survey_id": "1",
                "physical_scope_id": "1",
                "structure_id": "1",
                "zone_id": "1",
                "clock_id": "1",
                "potential_summary_by_native_convention": "mixed",
                "current_summary_by_source_kind": "mixed",
                "potential_threshold_margins": "mixed",
                "ir_drop_handling_records": "mixed",
            },
            (
                "Field potential conventions, reference-electrode calibration and IR-drop status remain explicit.",
                "Current signs, source identities, clock and environment are caller-reviewed records.",
                "Thresholds are caller inputs and yield margins only, without compliance inference.",
            ),
            ("authored_cathodic_protection_field_survey_summary",),
            context_validator=same_identity,
        )
    ]
