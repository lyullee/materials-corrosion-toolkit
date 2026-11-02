"""High-temperature hydrogen applicability against caller-owned evidence support."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class MaterialCompositionEntry(Contract):
    constituent_id: str = Field(min_length=1)
    reported_value: Nonnegative
    unit: str = Field(min_length=1)
    result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class MaterialCompositionSupport(Contract):
    constituent_id: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    minimum_supported_value: Nonnegative
    maximum_supported_value: Nonnegative

    @model_validator(mode="after")
    def ordered_support(self):
        if self.maximum_supported_value < self.minimum_supported_value:
            raise ValueError("material-composition support bounds must be ordered")
        return self


class HighTemperatureHydrogenExposure(Contract):
    interval_id: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    hydrogen_species: str = Field(min_length=1)
    pressure_basis: Literal["absolute_partial_pressure"]
    hydrogen_partial_pressure_Pa_abs: Nonnegative
    temperature_K: Positive
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_interval(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("high-temperature hydrogen interval must have positive duration")
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("an invalid hydrogen exposure record requires a basis")
        return self


class HydrogenMicrostructureEvidence(Contract):
    record_id: str = Field(min_length=1)
    physical_source_group_id: str = Field(min_length=1)
    inspection_location: str = Field(min_length=1)
    inspection_method_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    microstructure_descriptor: str | None = None
    result_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    record_available: bool
    missing_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent_record(self):
        if self.record_available and (self.microstructure_descriptor is None or self.result_digest is None):
            raise ValueError("available microstructure evidence requires a descriptor and result digest")
        if not self.record_available and not self.missing_basis:
            raise ValueError("unavailable microstructure evidence requires a missingness basis")
        if not self.record_available and (
            self.microstructure_descriptor is not None or self.result_digest is not None
        ):
            raise ValueError("unavailable microstructure evidence cannot carry a result")
        return self


class HydrogenProviderQualification(Contract):
    qualification_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_version: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    holdout_dataset_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_physical_source_group_count: int = Field(ge=1)
    holdout_physical_source_group_count: int = Field(ge=1)
    calibration_and_holdout_independent: bool
    validation_metric_definition: str = Field(min_length=1)
    validation_metric_value: Nonnegative
    validation_metric_unit: str = Field(min_length=1)
    maximum_supported_validation_metric: Positive
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class HighTemperatureHydrogenEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_treatment_id: str = Field(min_length=1)
    supported_hydrogen_species: tuple[str, ...] = Field(min_length=1)
    pressure_basis: Literal["absolute_partial_pressure"]
    minimum_hydrogen_partial_pressure_Pa_abs: Nonnegative
    maximum_hydrogen_partial_pressure_Pa_abs: Nonnegative
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    maximum_cumulative_exposure_s: Positive
    composition_support: tuple[MaterialCompositionSupport, ...] = Field(min_length=1)
    supported_microstructure_descriptors: tuple[str, ...] = Field(min_length=1)
    supported_inspection_method_ids: tuple[str, ...] = Field(min_length=1)
    minimum_physical_source_group_count: int = Field(ge=1)
    provider_qualification: HydrogenProviderQualification
    applicability_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_and_unique_support(self):
        if self.maximum_hydrogen_partial_pressure_Pa_abs < self.minimum_hydrogen_partial_pressure_Pa_abs:
            raise ValueError("hydrogen partial-pressure support bounds must be ordered")
        if self.maximum_temperature_K < self.minimum_temperature_K:
            raise ValueError("hydrogen temperature support bounds must be ordered")
        for values, name in (
            (self.supported_hydrogen_species, "hydrogen species"),
            (self.supported_microstructure_descriptors, "microstructure descriptor"),
            (self.supported_inspection_method_ids, "inspection method"),
            ([row.constituent_id for row in self.composition_support], "composition constituent"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"supported {name} values must be unique")
        return self


class HighTemperatureHydrogenApplicability(Contract):
    assessment_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    heat_treatment_id: str = Field(min_length=1)
    composition: tuple[MaterialCompositionEntry, ...] = Field(min_length=1)
    exposures: tuple[HighTemperatureHydrogenExposure, ...] = Field(min_length=1)
    microstructure_evidence: tuple[HydrogenMicrostructureEvidence, ...] = Field(min_length=1)
    qualification_envelope: HighTemperatureHydrogenEnvelope
    material_identity_composition_and_heat_treatment_reviewed: bool
    hydrogen_species_and_absolute_partial_pressure_reviewed: bool
    temperature_pressure_clock_and_time_reviewed: bool
    microstructure_locations_and_source_groups_reviewed: bool
    inspection_method_and_provider_lineage_reviewed: bool
    record_and_result_digests_reviewed: bool
    missingness_reviewed: bool
    qualification_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_and_ordered_records(self):
        for values, name in (
            ([row.constituent_id for row in self.composition], "composition constituent"),
            ([row.interval_id for row in self.exposures], "hydrogen exposure"),
            ([row.record_id for row in self.microstructure_evidence], "microstructure evidence"),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{name} identifiers must be unique")
        for first, second in zip(self.exposures, self.exposures[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("hydrogen exposure intervals must be ordered and cannot overlap")
        return self


def high_temperature_hydrogen_applicability(x: HighTemperatureHydrogenApplicability) -> Calculation:
    envelope = x.qualification_envelope
    missing_reviews = [
        name
        for name in (
            "material_identity_composition_and_heat_treatment_reviewed",
            "hydrogen_species_and_absolute_partial_pressure_reviewed",
            "temperature_pressure_clock_and_time_reviewed",
            "microstructure_locations_and_source_groups_reviewed",
            "inspection_method_and_provider_lineage_reviewed",
            "record_and_result_digests_reviewed",
            "missingness_reviewed",
            "qualification_envelope_authority_reviewed",
        )
        if not getattr(x, name)
    ]
    identity_mismatch_fields = [
        name
        for name in ("material_condition_id", "heat_treatment_id")
        if getattr(x, name) != getattr(envelope, name)
    ]
    invalid_exposure_ids = [row.interval_id for row in x.exposures if not row.record_valid]
    unavailable_microstructure_record_ids = [
        row.record_id for row in x.microstructure_evidence if not row.record_available
    ]
    qualification = envelope.provider_qualification
    qualification_supported = (
        qualification.calibration_and_holdout_independent
        and qualification.validation_metric_value <= qualification.maximum_supported_validation_metric
    )
    if (
        missing_reviews
        or identity_mismatch_fields
        or invalid_exposure_ids
        or unavailable_microstructure_record_ids
        or not qualification_supported
    ):
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_reviews": missing_reviews,
                "identity_mismatch_fields": identity_mismatch_fields,
                "invalid_exposure_ids": invalid_exposure_ids,
                "unavailable_microstructure_record_ids": unavailable_microstructure_record_ids,
                "provider_qualification_supported": qualification_supported,
            },
            notes=(
                "Applicability is withheld until identities, records, provider qualification and reviews are complete.",
            ),
        )

    composition_by_id = {row.constituent_id: row for row in x.composition}
    composition_comparisons = []
    missing_composition_constituent_ids = []
    composition_unit_mismatch_ids = []
    composition_outside_support_ids = []
    for support in envelope.composition_support:
        entry = composition_by_id.get(support.constituent_id)
        if entry is None:
            missing_composition_constituent_ids.append(support.constituent_id)
            continue
        if entry.unit != support.unit:
            composition_unit_mismatch_ids.append(entry.constituent_id)
            continue
        within = support.minimum_supported_value <= entry.reported_value <= support.maximum_supported_value
        if not within:
            composition_outside_support_ids.append(entry.constituent_id)
        composition_comparisons.append(
            {
                "constituent_id": entry.constituent_id,
                "reported_value": entry.reported_value,
                "unit": entry.unit,
                "within_declared_support": within,
            }
        )
    if missing_composition_constituent_ids or composition_unit_mismatch_ids:
        return Calculation(
            status="needs_data",
            values={
                "assessment_id": x.assessment_id,
                "missing_composition_constituent_ids": missing_composition_constituent_ids,
                "composition_unit_mismatch_ids": composition_unit_mismatch_ids,
                "composition_comparisons": composition_comparisons,
            },
            notes=("Exact caller-declared composition identities and unit tokens are required.",),
        )

    cumulative_exposure_s = 0.0
    exposure_comparisons = []
    outside_exposure_ids = []
    for exposure in x.exposures:
        duration_s = exposure.end_time_s - exposure.start_time_s
        cumulative_exposure_s += duration_s
        unsupported_fields = []
        if exposure.hydrogen_species not in envelope.supported_hydrogen_species:
            unsupported_fields.append("hydrogen_species")
        if exposure.pressure_basis != envelope.pressure_basis:
            unsupported_fields.append("pressure_basis")
        if not (
            envelope.minimum_hydrogen_partial_pressure_Pa_abs
            <= exposure.hydrogen_partial_pressure_Pa_abs
            <= envelope.maximum_hydrogen_partial_pressure_Pa_abs
        ):
            unsupported_fields.append("hydrogen_partial_pressure_Pa_abs")
        if not envelope.minimum_temperature_K <= exposure.temperature_K <= envelope.maximum_temperature_K:
            unsupported_fields.append("temperature_K")
        if unsupported_fields:
            outside_exposure_ids.append(exposure.interval_id)
        exposure_comparisons.append(
            {
                "interval_id": exposure.interval_id,
                "duration_s": duration_s,
                "hydrogen_species": exposure.hydrogen_species,
                "pressure_basis": exposure.pressure_basis,
                "hydrogen_partial_pressure_Pa_abs": exposure.hydrogen_partial_pressure_Pa_abs,
                "temperature_K": exposure.temperature_K,
                "unsupported_fields": unsupported_fields,
                "within_declared_support": not unsupported_fields,
            }
        )

    microstructure_comparisons = []
    outside_microstructure_record_ids = []
    for record in x.microstructure_evidence:
        unsupported_fields = []
        if record.inspection_method_id not in envelope.supported_inspection_method_ids:
            unsupported_fields.append("inspection_method_id")
        if record.microstructure_descriptor not in envelope.supported_microstructure_descriptors:
            unsupported_fields.append("microstructure_descriptor")
        if (
            record.provider_id != qualification.provider_id
            or record.provider_version != qualification.provider_version
            or record.provider_state_digest != qualification.provider_state_digest
        ):
            unsupported_fields.append("provider_identity_or_state")
        if unsupported_fields:
            outside_microstructure_record_ids.append(record.record_id)
        microstructure_comparisons.append(
            {
                "record_id": record.record_id,
                "physical_source_group_id": record.physical_source_group_id,
                "inspection_method_id": record.inspection_method_id,
                "microstructure_descriptor": record.microstructure_descriptor,
                "unsupported_fields": unsupported_fields,
                "within_declared_support": not unsupported_fields,
            }
        )
    physical_source_group_count = len({row.physical_source_group_id for row in x.microstructure_evidence})
    source_group_support = physical_source_group_count >= envelope.minimum_physical_source_group_count
    cumulative_exposure_support = cumulative_exposure_s <= envelope.maximum_cumulative_exposure_s
    outside_support = (
        composition_outside_support_ids
        or outside_exposure_ids
        or outside_microstructure_record_ids
        or not source_group_support
        or not cumulative_exposure_support
    )
    return Calculation(
        status="out_of_scope" if outside_support else "computed",
        values={
            "assessment_id": x.assessment_id,
            "physical_scope_id": x.physical_scope_id,
            "clock_id": x.clock_id,
            "envelope_id": envelope.envelope_id,
            "composition_comparisons": composition_comparisons,
            "composition_outside_support_ids": composition_outside_support_ids,
            "exposure_comparisons": exposure_comparisons,
            "outside_support_exposure_ids": outside_exposure_ids,
            "cumulative_exposure_s": cumulative_exposure_s,
            "cumulative_exposure_within_declared_support": cumulative_exposure_support,
            "microstructure_comparisons": microstructure_comparisons,
            "outside_support_microstructure_record_ids": outside_microstructure_record_ids,
            "physical_source_group_count": physical_source_group_count,
            "physical_source_group_count_within_declared_support": source_group_support,
            "declared_applicability_outcome": ("outside_support" if outside_support else "within_support"),
        },
        notes=(
            "Applicability is an evidence-range comparison against a caller-owned provider qualification envelope.",
            "No industry curve, hydrogen reaction kinetics, property loss, cracking or damage rate, remaining life, probability or acceptance criterion is embedded.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError(
                "high-temperature hydrogen assessment asset and location must match the run context"
            )

    return [
        ModelSpec(
            "degradation.high_temperature_hydrogen_applicability",
            HighTemperatureHydrogenApplicability,
            high_temperature_hydrogen_applicability,
            {
                "assessment_id": "1",
                "physical_scope_id": "1",
                "clock_id": "1",
                "envelope_id": "1",
                "composition_comparisons": "mixed",
                "composition_outside_support_ids": "1",
                "exposure_comparisons": "mixed",
                "outside_support_exposure_ids": "1",
                "cumulative_exposure_s": "s",
                "cumulative_exposure_within_declared_support": "1",
                "microstructure_comparisons": "mixed",
                "outside_support_microstructure_record_ids": "1",
                "physical_source_group_count": "1",
                "physical_source_group_count_within_declared_support": "1",
                "declared_applicability_outcome": "1",
            },
            (
                "Hydrogen pressure is an absolute partial pressure in pascals; gauge or total pressure is not silently substituted.",
                "Material condition, composition and heat treatment match caller-owned evidence identities and unit tokens.",
                "Microstructure descriptors and provider qualification bounds are reviewed caller inputs.",
            ),
            ("reviewed_high_temperature_hydrogen_qualification_envelope",),
            context_validator=same_identity,
        )
    ]
