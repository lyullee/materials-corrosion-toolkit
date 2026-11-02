"""Integrate caller-calibrated acid dissolution rates within explicit support."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Nonnegative, Positive
from ..registry import ModelSpec


class AcidDissolutionRateSupport(Contract):
    support_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    acid_species_id: str = Field(min_length=1)
    concentration_min: Nonnegative
    concentration_max: Nonnegative
    concentration_unit_token: str = Field(min_length=1)
    concentration_basis: str = Field(min_length=1)
    temperature_min_K: Positive
    temperature_max_K: Positive
    applicable_flow_mass_transfer_descriptors: list[str] = Field(min_length=1)
    rate_provider_id: str = Field(min_length=1)
    rate_provider_version: str = Field(min_length=1)
    rate_provider_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    calibration_basis: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_support(self):
        if self.concentration_max < self.concentration_min:
            raise ValueError("acid dissolution concentration support must be ordered")
        if self.temperature_max_K < self.temperature_min_K:
            raise ValueError("acid dissolution temperature support must be ordered")
        descriptors = self.applicable_flow_mass_transfer_descriptors
        if len(set(descriptors)) != len(descriptors):
            raise ValueError("flow or mass-transfer descriptors must be unique")
        return self


class AcidDissolutionRateInterval(Contract):
    interval_id: str = Field(min_length=1)
    support_id: str = Field(min_length=1)
    concentration: Nonnegative
    temperature_K: Positive
    flow_mass_transfer_descriptor: str = Field(min_length=1)
    dissolution_rate_m_s: Nonnegative | None = None
    rate_record_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    rate_valid: bool
    missing_or_invalid_basis: str | None = None
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_rate_record(self):
        if self.dissolution_rate_m_s is None or self.rate_record_digest is None:
            if self.rate_valid or not self.missing_or_invalid_basis:
                raise ValueError("missing dissolution rate or digest requires an invalid record and basis")
        if not self.rate_valid and not self.missing_or_invalid_basis:
            raise ValueError("an invalid dissolution rate requires a basis")
        return self


class AcidDissolutionHistory(Contract):
    history_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    acid_species_id: str = Field(min_length=1)
    concentration_unit_token: str = Field(min_length=1)
    concentration_basis: str = Field(min_length=1)
    elapsed_time_s: list[Nonnegative] = Field(min_length=2)
    rate_intervals: list[AcidDissolutionRateInterval] = Field(min_length=1)
    rate_supports: list[AcidDissolutionRateSupport] = Field(min_length=1)
    material_and_acid_identity_reviewed: bool
    concentration_definition_reviewed: bool
    temperature_history_reviewed: bool
    flow_mass_transfer_history_reviewed: bool
    rate_provider_and_calibration_reviewed: bool
    clock_and_interval_alignment_reviewed: bool
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def align_and_identify(self):
        if any(b <= a for a, b in zip(self.elapsed_time_s, self.elapsed_time_s[1:], strict=False)):
            raise ValueError("acid dissolution clock must increase")
        if len(self.rate_intervals) != len(self.elapsed_time_s) - 1:
            raise ValueError("one caller-provided dissolution rate is required per time interval")
        interval_ids = [item.interval_id for item in self.rate_intervals]
        support_ids = [item.support_id for item in self.rate_supports]
        if len(set(interval_ids)) != len(interval_ids):
            raise ValueError("acid dissolution interval IDs must be unique")
        if len(set(support_ids)) != len(support_ids):
            raise ValueError("acid dissolution support IDs must be unique")
        return self


def acid_dissolution_history(x: AcidDissolutionHistory) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "material_and_acid_identity_reviewed",
            "concentration_definition_reviewed",
            "temperature_history_reviewed",
            "flow_mass_transfer_history_reviewed",
            "rate_provider_and_calibration_reviewed",
            "clock_and_interval_alignment_reviewed",
        )
        if not getattr(x, name)
    ]
    supports = {item.support_id: item for item in x.rate_supports}
    diagnostics = []
    invalid_or_unmatched = []
    outside_support = []
    for interval in x.rate_intervals:
        support = supports.get(interval.support_id)
        if support is None:
            diagnostics.append(
                {
                    "interval_id": interval.interval_id,
                    "support_id": interval.support_id,
                    "support_supplied": False,
                    "identity_match": False,
                    "within_support": None,
                    "rate_valid": interval.rate_valid,
                }
            )
            invalid_or_unmatched.append(interval.interval_id)
            continue
        identity = {
            "material_condition_id": x.material_condition_id == support.material_condition_id,
            "acid_species_id": x.acid_species_id == support.acid_species_id,
            "concentration_unit_token": (x.concentration_unit_token == support.concentration_unit_token),
            "concentration_basis": x.concentration_basis == support.concentration_basis,
            "flow_mass_transfer_descriptor": (
                interval.flow_mass_transfer_descriptor in support.applicable_flow_mass_transfer_descriptors
            ),
        }
        ranges = {
            "concentration": support.concentration_min <= interval.concentration <= support.concentration_max,
            "temperature_K": support.temperature_min_K <= interval.temperature_K <= support.temperature_max_K,
        }
        identity_ok = all(identity.values())
        range_ok = all(ranges.values())
        rate_ok = (
            interval.rate_valid
            and interval.dissolution_rate_m_s is not None
            and interval.rate_record_digest is not None
        )
        diagnostics.append(
            {
                "interval_id": interval.interval_id,
                "support_id": interval.support_id,
                "support_supplied": True,
                "identity_checks": identity,
                "range_checks": ranges,
                "identity_match": identity_ok,
                "within_support": range_ok,
                "rate_valid": rate_ok,
                "rate_provider_id": support.rate_provider_id,
                "rate_provider_version": support.rate_provider_version,
                "rate_provider_digest": support.rate_provider_digest,
                "rate_record_digest": interval.rate_record_digest,
            }
        )
        if not identity_ok or not rate_ok:
            invalid_or_unmatched.append(interval.interval_id)
        elif not range_ok:
            outside_support.append(interval.interval_id)

    status = "computed"
    if missing_reviews or invalid_or_unmatched:
        status = "needs_data"
    elif outside_support:
        status = "out_of_scope"
    if status != "computed":
        return Calculation(
            status=status,
            values={
                "history_id": x.history_id,
                "asset_id": x.asset_id,
                "location_id": x.location_id,
                "clock_id": x.clock_id,
                "interval_diagnostics": diagnostics,
                "invalid_or_unmatched_interval_ids": invalid_or_unmatched,
                "outside_support_interval_ids": outside_support,
                "missing_reviews": missing_reviews,
            },
            notes=("No cumulative metal loss is emitted when any interval is invalid or outside support.",),
        )

    interval_losses = []
    cumulative = [0.0]
    for start, end, interval in zip(
        x.elapsed_time_s[:-1], x.elapsed_time_s[1:], x.rate_intervals, strict=True
    ):
        loss = interval.dissolution_rate_m_s * (end - start)
        interval_losses.append(loss)
        cumulative.append(cumulative[-1] + loss)
    return Calculation(
        values={
            "history_id": x.history_id,
            "asset_id": x.asset_id,
            "location_id": x.location_id,
            "clock_id": x.clock_id,
            "interval_metal_loss_m": interval_losses,
            "cumulative_metal_loss_m": cumulative,
            "total_metal_loss_m": cumulative[-1],
            "interval_diagnostics": diagnostics,
            "invalid_or_unmatched_interval_ids": [],
            "outside_support_interval_ids": [],
            "missing_reviews": [],
        },
        notes=(
            "Each interval uses the caller-provided constant dissolution rate without interpolation or coefficient generation.",
            "Reaction chemistry, inhibitor depletion, localized attack, lifetime and acceptance are outside this model.",
            "The integrated loss is a provider-conditioned exposure result, not an independent corrosion-rate prediction.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "degradation.acid_dissolution_history",
            AcidDissolutionHistory,
            acid_dissolution_history,
            {
                "history_id": "1",
                "asset_id": "1",
                "location_id": "1",
                "clock_id": "1",
                "interval_metal_loss_m": "m",
                "cumulative_metal_loss_m": "m",
                "total_metal_loss_m": "m",
                "interval_diagnostics": "mixed",
                "invalid_or_unmatched_interval_ids": "1",
                "outside_support_interval_ids": "1",
                "missing_reviews": "1",
            },
            (
                "Dissolution rates are externally calibrated, explicitly supplied and constant within each declared interval.",
                "Material, acid, concentration unit and basis, and flow or mass-transfer descriptors require exact matching.",
                "No extrapolation, automatic unit conversion or hidden empirical coefficient is used.",
            ),
            ("caller_calibrated_acid_dissolution_rate_integration",),
        )
    ]
