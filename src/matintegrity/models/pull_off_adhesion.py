"""Partitioned pull-off adhesion evidence and provider-stress calibration."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class PullOffForceCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    force_instrument_id: str = Field(min_length=1)
    instrument_configuration_id: str = Field(min_length=1)
    force_unit_token: Literal["N"]
    minimum_supported_force_N: Nonnegative
    maximum_supported_force_N: Positive
    expanded_uncertainty_N: Nonnegative
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_valid_calibration(self):
        if self.maximum_supported_force_N <= self.minimum_supported_force_N:
            raise ValueError("pull-off force-calibration support must have positive width")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid pull-off force calibration requires a basis")
        return self


class PullOffBreakModeComponent(Contract):
    component_id: str = Field(min_length=1)
    caller_descriptor: str = Field(min_length=1)
    reported_area_fraction: Fraction


class PullOffObservation(Contract):
    observation_id: str = Field(min_length=1)
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    independence_group_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    dolly_id: str = Field(min_length=1)
    physical_location_id: str = Field(min_length=1)
    location_definition: str = Field(min_length=1)
    coating_layer_stack_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    surface_preparation_id: str = Field(min_length=1)
    cure_condition_id: str = Field(min_length=1)
    exposure_condition_id: str = Field(min_length=1)
    adhesive_condition_id: str = Field(min_length=1)
    caller_break_mode_id: str = Field(min_length=1)
    break_mode_components: tuple[PullOffBreakModeComponent, ...] = Field(min_length=1)
    measurement_basis: Literal["force_area", "provider_stress", "both"]
    force_calibration_id: str | None = None
    pull_force_N: Positive | None = None
    pull_force_unit_token: Literal["N"] | None = None
    pull_force_expanded_uncertainty_N: Nonnegative | None = None
    dolly_area_m2: Positive | None = None
    dolly_area_unit_token: Literal["m^2"] | None = None
    dolly_area_expanded_uncertainty_m2: Nonnegative | None = None
    provider_stress_Pa: Positive | None = None
    provider_stress_unit_token: Literal["Pa"] | None = None
    provider_stress_expanded_uncertainty_Pa: Nonnegative | None = None
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_configuration_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    input_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    nominal_weight: Positive = 1.0
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_measurement(self):
        component_ids = [row.component_id for row in self.break_mode_components]
        if len(component_ids) != len(set(component_ids)):
            raise ValueError("pull-off break-mode component identifiers must be unique")
        if abs(sum(row.reported_area_fraction for row in self.break_mode_components) - 1.0) > 1e-9:
            raise ValueError("caller-reported pull-off break-mode fractions must sum to one")
        force_fields = (
            self.force_calibration_id,
            self.pull_force_N,
            self.pull_force_unit_token,
            self.pull_force_expanded_uncertainty_N,
            self.dolly_area_m2,
            self.dolly_area_unit_token,
            self.dolly_area_expanded_uncertainty_m2,
        )
        provider_fields = (
            self.provider_stress_Pa,
            self.provider_stress_unit_token,
            self.provider_stress_expanded_uncertainty_Pa,
        )
        requires_force = self.measurement_basis in {"force_area", "both"}
        requires_provider = self.measurement_basis in {"provider_stress", "both"}
        if requires_force != all(value is not None for value in force_fields):
            raise ValueError("force-area pull-off records require the complete explicit N and m^2 path")
        if requires_provider != all(value is not None for value in provider_fields):
            raise ValueError("provider-stress pull-off records require the complete explicit Pa path")
        if not requires_force and any(value is not None for value in force_fields):
            raise ValueError("provider-only pull-off records cannot carry partial force-area fields")
        if not requires_provider and any(value is not None for value in provider_fields):
            raise ValueError("force-area-only pull-off records cannot carry provider-stress fields")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid pull-off observation requires a basis")
        return self


class CallerPullOffThreshold(Contract):
    threshold_id: str = Field(min_length=1)
    stress_basis: Literal["force_area", "provider_stress"]
    minimum_stress_Pa: Positive
    authority_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class PullOffAdhesionCalibration(Contract):
    calibration_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    coating_system_id: str = Field(min_length=1)
    coating_layer_stack_id: str = Field(min_length=1)
    substrate_condition_id: str = Field(min_length=1)
    surface_preparation_id: str = Field(min_length=1)
    cure_condition_id: str = Field(min_length=1)
    exposure_condition_id: str = Field(min_length=1)
    adhesive_condition_id: str = Field(min_length=1)
    force_calibrations: tuple[PullOffForceCalibration, ...] = Field(min_length=1)
    observations: tuple[PullOffObservation, ...] = Field(min_length=4)
    caller_thresholds: tuple[CallerPullOffThreshold, ...] = ()
    minimum_paired_calibration_record_count: int = Field(ge=3)
    dollies_locations_layers_and_substrate_reviewed: bool
    surface_preparation_cure_exposure_and_adhesive_reviewed: bool
    force_area_and_provider_stress_units_reviewed: bool
    force_calibration_and_uncertainty_reviewed: bool
    break_mode_descriptors_and_fractions_reviewed: bool
    specimen_source_and_independence_partitions_reviewed: bool
    provider_revision_configuration_and_digests_reviewed: bool
    caller_threshold_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_partitioned_records(self):
        for values, label in (
            ([row.calibration_id for row in self.force_calibrations], "force calibration"),
            ([row.observation_id for row in self.observations], "observation"),
            ([row.dolly_id for row in self.observations], "dolly"),
            ([row.threshold_id for row in self.caller_thresholds], "threshold"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"pull-off {label} identifiers must be unique")
        for attribute, label in (
            ("physical_specimen_id", "physical specimen"),
            ("source_group_id", "source group"),
            ("independence_group_id", "independence group"),
        ):
            calibration = {
                getattr(row, attribute) for row in self.observations if row.partition == "calibration"
            }
            holdout = {getattr(row, attribute) for row in self.observations if row.partition == "holdout"}
            if calibration & holdout:
                raise ValueError(f"pull-off {label} cannot cross calibration and holdout")
        return self


def _force_area_values(row: PullOffObservation) -> tuple[float, float]:
    stress = row.pull_force_N / row.dolly_area_m2
    uncertainty = math.sqrt(
        (row.pull_force_expanded_uncertainty_N / row.dolly_area_m2) ** 2
        + (row.pull_force_N * row.dolly_area_expanded_uncertainty_m2 / row.dolly_area_m2**2) ** 2
    )
    return stress, uncertainty


def pull_off_adhesion_calibration(x: PullOffAdhesionCalibration) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "dollies_locations_layers_and_substrate_reviewed",
            "surface_preparation_cure_exposure_and_adhesive_reviewed",
            "force_area_and_provider_stress_units_reviewed",
            "force_calibration_and_uncertainty_reviewed",
            "break_mode_descriptors_and_fractions_reviewed",
            "specimen_source_and_independence_partitions_reviewed",
            "provider_revision_configuration_and_digests_reviewed",
            "caller_threshold_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    invalid_calibration_ids = [row.calibration_id for row in x.force_calibrations if not row.record_valid]
    invalid_observation_ids = [row.observation_id for row in x.observations if not row.record_valid]
    identity_mismatch_ids = [
        row.observation_id
        for row in x.observations
        if row.coating_layer_stack_id != x.coating_layer_stack_id
        or row.substrate_condition_id != x.substrate_condition_id
        or row.surface_preparation_id != x.surface_preparation_id
        or row.cure_condition_id != x.cure_condition_id
        or row.exposure_condition_id != x.exposure_condition_id
        or row.adhesive_condition_id != x.adhesive_condition_id
    ]
    force_calibration_by_id = {row.calibration_id: row for row in x.force_calibrations}
    unlinked_force_record_ids = [
        row.observation_id
        for row in x.observations
        if row.measurement_basis in {"force_area", "both"}
        and row.force_calibration_id not in force_calibration_by_id
    ]
    if (
        missing_reviews
        or invalid_calibration_ids
        or invalid_observation_ids
        or identity_mismatch_ids
        or unlinked_force_record_ids
    ):
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "missing_reviews": missing_reviews,
                "invalid_force_calibration_ids": invalid_calibration_ids,
                "invalid_observation_ids": invalid_observation_ids,
                "identity_mismatch_observation_ids": identity_mismatch_ids,
                "unlinked_force_record_ids": unlinked_force_record_ids,
            },
            notes=(
                "Reviewed exact coating identities, measurement paths and calibration records are required.",
            ),
        )
    outside_force_support_ids = [
        row.observation_id
        for row in x.observations
        if row.measurement_basis in {"force_area", "both"}
        and not force_calibration_by_id[row.force_calibration_id].minimum_supported_force_N
        <= row.pull_force_N
        <= force_calibration_by_id[row.force_calibration_id].maximum_supported_force_N
    ]
    if outside_force_support_ids:
        return Calculation(
            status="out_of_scope",
            values={
                "calibration_id": x.calibration_id,
                "outside_force_calibration_support_observation_ids": outside_force_support_ids,
            },
            notes=("Force calibration support is not extrapolated.",),
        )

    rows = []
    paired_calibration = []
    for observation in x.observations:
        force_area_stress = None
        force_area_uncertainty = None
        provider_minus_force_area = None
        if observation.measurement_basis in {"force_area", "both"}:
            force_area_stress, force_area_uncertainty = _force_area_values(observation)
        if observation.measurement_basis == "both":
            provider_minus_force_area = observation.provider_stress_Pa - force_area_stress
            if observation.partition == "calibration":
                paired_calibration.append((observation, provider_minus_force_area))
        rows.append(
            {
                "observation_id": observation.observation_id,
                "partition": observation.partition,
                "dolly_id": observation.dolly_id,
                "physical_location_id": observation.physical_location_id,
                "measurement_basis": observation.measurement_basis,
                "force_area_stress_Pa": force_area_stress,
                "force_area_expanded_uncertainty_Pa": force_area_uncertainty,
                "provider_stress_Pa": observation.provider_stress_Pa,
                "provider_stress_expanded_uncertainty_Pa": (
                    observation.provider_stress_expanded_uncertainty_Pa
                ),
                "provider_minus_force_area_stress_Pa": provider_minus_force_area,
                "caller_break_mode_id": observation.caller_break_mode_id,
                "break_mode_components": [
                    component.model_dump(mode="json") for component in observation.break_mode_components
                ],
            }
        )
    if len(paired_calibration) < x.minimum_paired_calibration_record_count:
        return Calculation(
            status="needs_data",
            values={
                "calibration_id": x.calibration_id,
                "paired_calibration_record_count": len(paired_calibration),
                "observation_rows": rows,
            },
            notes=("The caller-declared minimum paired force-area/provider calibration count is unmet.",),
        )
    weights = [row.nominal_weight for row, _ in paired_calibration]
    differences = [difference for _, difference in paired_calibration]
    weight_sum = sum(weights)
    provider_bias = (
        sum(weight * difference for weight, difference in zip(weights, differences, strict=True)) / weight_sum
    )
    provider_repeatability = math.sqrt(
        sum(
            weight * (difference - provider_bias) ** 2
            for weight, difference in zip(weights, differences, strict=True)
        )
        / weight_sum
    )
    holdout_comparisons = []
    for observation, row in zip(x.observations, rows, strict=True):
        if observation.partition != "holdout" or observation.measurement_basis != "both":
            continue
        bias_corrected_provider_stress = observation.provider_stress_Pa - provider_bias
        holdout_comparisons.append(
            {
                "observation_id": observation.observation_id,
                "force_area_stress_Pa": row["force_area_stress_Pa"],
                "provider_stress_Pa": observation.provider_stress_Pa,
                "bias_corrected_provider_stress_Pa": bias_corrected_provider_stress,
                "bias_corrected_provider_minus_force_area_Pa": (
                    bias_corrected_provider_stress - row["force_area_stress_Pa"]
                ),
            }
        )
    threshold_margins = []
    for threshold in x.caller_thresholds:
        for observation, row in zip(x.observations, rows, strict=True):
            value = (
                row["force_area_stress_Pa"]
                if threshold.stress_basis == "force_area"
                else observation.provider_stress_Pa
            )
            if value is None:
                continue
            threshold_margins.append(
                {
                    "threshold_id": threshold.threshold_id,
                    "observation_id": observation.observation_id,
                    "stress_basis": threshold.stress_basis,
                    "reported_stress_Pa": value,
                    "minimum_stress_Pa": threshold.minimum_stress_Pa,
                    "signed_margin_reported_minus_threshold_Pa": (value - threshold.minimum_stress_Pa),
                }
            )
    return Calculation(
        status="computed",
        values={
            "calibration_id": x.calibration_id,
            "physical_scope_id": x.physical_scope_id,
            "coating_system_id": x.coating_system_id,
            "paired_calibration_record_count": len(paired_calibration),
            "provider_minus_force_area_bias_Pa": provider_bias,
            "provider_minus_force_area_repeatability_Pa": provider_repeatability,
            "observation_rows": rows,
            "holdout_provider_comparisons": holdout_comparisons,
            "caller_threshold_margins": threshold_margins,
        },
        notes=(
            "Force divided by dolly area is calculated only for explicit N and m^2 inputs; uncertainty uses first-order independent propagation.",
            "Provider stress remains an independent reported result and is compared with force-area stress without replacing either record.",
            "Caller break-mode components are preserved without interpreting mixed modes; threshold margins are not pass/fail decisions.",
            "No specification table, coating life, acceptance or failure probability is produced.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("pull-off adhesion calibration asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.pull_off_adhesion_calibration",
            PullOffAdhesionCalibration,
            pull_off_adhesion_calibration,
            {
                "calibration_id": "1",
                "physical_scope_id": "1",
                "coating_system_id": "1",
                "paired_calibration_record_count": "1",
                "provider_minus_force_area_bias_Pa": "Pa",
                "provider_minus_force_area_repeatability_Pa": "Pa",
                "observation_rows": "mixed",
                "holdout_provider_comparisons": "mixed",
                "caller_threshold_margins": "mixed",
            },
            (
                "Force-area stress requires explicit newtons and square metres and is kept separate from provider stress.",
                "Calibration and holdout specimen, source and independence groups are disjoint.",
                "Break-mode descriptions and fractions are caller records and are not interpreted by the model.",
            ),
            ("authored_partitioned_pull_off_adhesion_evidence_calibration",),
            context_validator=same_identity,
        )
    ]
