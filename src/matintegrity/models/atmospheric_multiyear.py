"""Multi-year atmospheric loss from caller-qualified first-year loss and time exponent."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AtmosphericTransferQualificationRecord(Contract):
    record_id: str = Field(min_length=1)
    partition: Literal["calibration", "holdout"]
    physical_specimen_id: str = Field(min_length=1)
    source_group_id: str = Field(min_length=1)
    exposure_zone_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    climate_pollutant_descriptor_id: str = Field(min_length=1)
    provider_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    record_valid: bool
    invalid_basis: str | None = None
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validity(self):
        if not self.record_valid and not self.invalid_basis:
            raise ValueError("invalid atmospheric transfer records require a basis")
        return self


class AtmosphericTimeTransferEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    exposure_zone_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    climate_pollutant_descriptor_id: str = Field(min_length=1)
    loss_unit_token: str = Field(min_length=1)
    time_unit_token: Literal["year"] = "year"
    minimum_first_year_loss: Positive
    maximum_first_year_loss: Positive
    minimum_time_exponent: Positive
    maximum_time_exponent: Positive
    maximum_supported_elapsed_years: Positive
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_state_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    qualification_records: tuple[AtmosphericTransferQualificationRecord, ...] = Field(min_length=2)
    qualification_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support_and_partitions(self):
        if self.maximum_first_year_loss < self.minimum_first_year_loss:
            raise ValueError("first-year loss support must be ordered")
        if self.maximum_time_exponent < self.minimum_time_exponent:
            raise ValueError("time-exponent support must be ordered")
        if self.maximum_supported_elapsed_years < 1.0:
            raise ValueError("multi-year support must include the first-year anchor")
        valid = [row for row in self.qualification_records if row.record_valid]
        if {row.partition for row in valid} != {"calibration", "holdout"}:
            raise ValueError("atmospheric transfer qualification requires calibration and holdout")
        groups = {}
        for row in self.qualification_records:
            prior = groups.setdefault(row.source_group_id, row.partition)
            if prior != row.partition:
                raise ValueError("atmospheric source groups cannot cross partitions")
        return self


class AtmosphericMultiYearLossHistory(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    exposure_zone_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    surface_condition_id: str = Field(min_length=1)
    climate_pollutant_descriptor_id: str = Field(min_length=1)
    first_year_loss: Positive
    loss_unit_token: str = Field(min_length=1)
    first_year_loss_provider_id: str = Field(min_length=1)
    first_year_loss_result_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    time_exponent: Positive
    elapsed_time_years: tuple[Nonnegative, ...] = Field(min_length=2)
    transfer_envelope: AtmosphericTimeTransferEnvelope
    exposure_material_surface_and_environment_identity_reviewed: bool
    first_year_endpoint_value_and_unit_reviewed: bool
    time_exponent_definition_and_support_reviewed: bool
    clock_and_ordered_time_knots_reviewed: bool
    provider_lineage_and_digests_reviewed: bool
    qualification_partitions_and_source_groups_reviewed: bool
    transfer_envelope_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_knots(self):
        if self.elapsed_time_years[0] != 0.0:
            raise ValueError("atmospheric loss history must start at zero elapsed years")
        if any(b <= a for a, b in zip(self.elapsed_time_years, self.elapsed_time_years[1:], strict=False)):
            raise ValueError("atmospheric time knots must be strictly increasing")
        if 1.0 not in self.elapsed_time_years:
            raise ValueError("atmospheric time knots must retain the first-year anchor")
        return self


def atmospheric_multi_year_loss_history(x: AtmosphericMultiYearLossHistory) -> Calculation:
    e = x.transfer_envelope
    reviews = (
        "exposure_material_surface_and_environment_identity_reviewed",
        "first_year_endpoint_value_and_unit_reviewed",
        "time_exponent_definition_and_support_reviewed",
        "clock_and_ordered_time_knots_reviewed",
        "provider_lineage_and_digests_reviewed",
        "qualification_partitions_and_source_groups_reviewed",
        "transfer_envelope_authority_reviewed",
    )
    missing_reviews = [name for name in reviews if not getattr(x, name)]
    identities = (
        "exposure_zone_id",
        "material_condition_id",
        "surface_condition_id",
        "climate_pollutant_descriptor_id",
        "loss_unit_token",
    )
    mismatches = [name for name in identities if getattr(x, name) != getattr(e, name)]
    invalid_records = [row.record_id for row in e.qualification_records if not row.record_valid]
    record_identity_mismatches = []
    for row in e.qualification_records:
        fields = [name for name in identities[:-1] if getattr(row, name) != getattr(e, name)]
        if fields:
            record_identity_mismatches.append({"record_id": row.record_id, "fields": fields})
    if missing_reviews or mismatches or invalid_records or record_identity_mismatches:
        return Calculation(
            status="needs_data",
            values={
                "history_id": x.history_id,
                "missing_reviews": missing_reviews,
                "identity_or_unit_mismatch_fields": mismatches,
                "invalid_qualification_record_ids": invalid_records,
                "qualification_identity_mismatches": record_identity_mismatches,
            },
            notes=(
                "Multi-year transfer is withheld until identity, units and qualification lineage are complete.",
            ),
        )
    reasons = []
    if not e.minimum_first_year_loss <= x.first_year_loss <= e.maximum_first_year_loss:
        reasons.append("first_year_loss")
    if not e.minimum_time_exponent <= x.time_exponent <= e.maximum_time_exponent:
        reasons.append("time_exponent")
    if x.elapsed_time_years[-1] > e.maximum_supported_elapsed_years:
        reasons.append("elapsed_time")
    values = {
        "history_id": x.history_id,
        "asset_id": x.asset_id,
        "location_id": x.location_id,
        "physical_scope_id": x.physical_scope_id,
        "transfer_envelope_id": e.envelope_id,
        "outside_support_reasons": reasons,
        "elapsed_time_years": list(x.elapsed_time_years),
        "cumulative_loss": [
            0.0 if t == 0 else x.first_year_loss * t**x.time_exponent for t in x.elapsed_time_years
        ],
        "loss_increment": [0.0]
        + [
            (x.first_year_loss * b**x.time_exponent) - (x.first_year_loss * a**x.time_exponent)
            for a, b in zip(x.elapsed_time_years, x.elapsed_time_years[1:], strict=False)
        ],
        "time_exponent": x.time_exponent,
        "qualification_partition_counts": {
            p: sum(r.partition == p for r in e.qualification_records) for p in ("calibration", "holdout")
        },
    }
    notes = (
        "Loss history is only the caller-qualified first-year anchor multiplied by elapsed_years raised to the supplied exponent.",
        "No climate or pollutant descriptor is converted into a corrosion rate and support is never extrapolated.",
        "This average cumulative loss is not localized penetration, remaining life, acceptance or failure probability.",
    )
    if reasons:
        return Calculation(status="out_of_scope", values=values, notes=notes)
    values["declared_transfer_outcome"] = "within_support"
    return Calculation(values=values, notes=notes)


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("atmospheric history asset and location must match the run context")

    return [
        ModelSpec(
            "degradation.atmospheric_multi_year_loss_history",
            AtmosphericMultiYearLossHistory,
            atmospheric_multi_year_loss_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "physical_scope_id": "1",
                "transfer_envelope_id": "1",
                "outside_support_reasons": "1",
                "elapsed_time_years": "year",
                "cumulative_loss": "caller_unit",
                "loss_increment": "caller_unit",
                "time_exponent": "1",
                "qualification_partition_counts": "count",
                "declared_transfer_outcome": "1",
            },
            (
                "First-year loss and time exponent are externally supplied, reviewed quantities in exact caller units.",
                "Exposure zone, material, surface and climate/pollutant descriptor identities are constant over the history.",
                "The power transfer is evaluated only inside a caller-qualified envelope and is not a general atmospheric corrosion law.",
            ),
            ("reviewed_atmospheric_first_year_time_transfer_envelope",),
            context_validator=same_identity,
        )
    ]
