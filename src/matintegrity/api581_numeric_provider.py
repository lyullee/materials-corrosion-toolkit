"""Optional numeric-frequency adapter for a pinned API 581 consumer implementation."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .api581_exchange import Api581DamageExchangeRecord
from .contracts import Contract, Nonnegative, Positive, canonical_digest


class Api581NumericFrequencySettings(Contract):
    schema_version: Literal["matintegrity.api581_numeric_frequency_settings.v1"] = (
        "matintegrity.api581_numeric_frequency_settings.v1"
    )
    generic_frequency_per_year: Nonnegative
    generic_frequency_basis: str = Field(min_length=1)
    generic_frequency_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    management_factor: Positive
    management_factor_basis: str = Field(min_length=1)
    management_factor_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    seconds_per_year: Positive
    caller_reviewed_damage_factor_mapping: bool
    caller_reviewed_constant_rate_poisson_assumption: bool


class Api581NumericFrequencyReport(Contract):
    schema_version: Literal["matintegrity.api581_numeric_frequency_report.v1"] = (
        "matintegrity.api581_numeric_frequency_report.v1"
    )
    exchange_id: str
    api581_commit: str = Field(pattern=r"^[a-f0-9]{40}$")
    adjusted_calculation_id: Literal["frequency/adjusted"]
    probability_calculation_id: Literal["reliability/poisson-probability"]
    total_damage_factor: Nonnegative
    annual_failure_frequency_per_year: Nonnegative
    duration_years: Nonnegative
    period_failure_probability: float = Field(ge=0, le=1)
    probability_semantics: Literal["conditional_first_failure_in_period"]
    adjusted_receipt_input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    probability_receipt_input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    engine_code_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    settings_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    report_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    numeric_pof_provider_executed: Literal[True] = True
    physical_validation_claimed: Literal[False] = False
    engineering_qualification_claimed: Literal[False] = False
    limitations: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bound_digest(self):
        payload = self.model_dump(mode="json", exclude={"report_digest"})
        if canonical_digest(payload) != self.report_digest:
            raise ValueError("API 581 numeric-frequency report digest mismatch")
        return self


def run_pinned_api581_numeric_frequency(
    record: Api581DamageExchangeRecord,
    settings: Api581NumericFrequencySettings,
) -> Api581NumericFrequencyReport:
    """Run explicit GFF×DF×FMS and Poisson endpoints without inferring any input factor."""

    if not settings.caller_reviewed_damage_factor_mapping:
        raise ValueError("caller review of damage-factor mapping is required")
    if not settings.caller_reviewed_constant_rate_poisson_assumption:
        raise ValueError("caller review of the constant-rate Poisson assumption is required")
    if record.damage_factor is None:
        raise ValueError("a caller/provider damage factor is required; no factor is inferred")
    if record.status != "computed":
        raise ValueError("only a computed damage exchange record can enter the numeric provider")
    try:
        from api581.api.frequency import AdjustedInput, adjusted
        from api581.api.reliability import PoissonProbabilityInput, poisson_probability
    except ImportError as exc:
        raise ImportError(
            "the pinned api581-risk-analysis package must be installed or on PYTHONPATH"
        ) from exc

    adjusted_receipt = adjusted(
        AdjustedInput(
            generic_frequency_per_year=settings.generic_frequency_per_year,
            total_damage_factor=record.damage_factor,
            management_factor=settings.management_factor,
        )
    )
    duration_years = (record.horizon_end_s - record.horizon_start_s) / settings.seconds_per_year
    probability_receipt = poisson_probability(
        PoissonProbabilityInput(
            annual_failure_frequency=adjusted_receipt.outputs.annual_failure_frequency,
            duration_years=duration_years,
        )
    )
    expected = -math.expm1(-adjusted_receipt.outputs.annual_failure_frequency * duration_years)
    if not math.isclose(
        probability_receipt.outputs.period_failure_probability,
        expected,
        rel_tol=1e-12,
        abs_tol=1e-15,
    ):
        raise ValueError("external Poisson result failed independent identity check")
    if adjusted_receipt.code_fingerprint != probability_receipt.code_fingerprint:
        raise ValueError("API 581 calculation fingerprints differ")
    payload = {
        "exchange_id": record.exchange_id,
        "api581_commit": "7c8badb829f84b19c7b84d07fbc476601d9194eb",
        "adjusted_calculation_id": adjusted_receipt.calculation_id,
        "probability_calculation_id": probability_receipt.calculation_id,
        "total_damage_factor": record.damage_factor,
        "annual_failure_frequency_per_year": adjusted_receipt.outputs.annual_failure_frequency,
        "duration_years": duration_years,
        "period_failure_probability": probability_receipt.outputs.period_failure_probability,
        "probability_semantics": "conditional_first_failure_in_period",
        "adjusted_receipt_input_hash": adjusted_receipt.input_hash,
        "probability_receipt_input_hash": probability_receipt.input_hash,
        "engine_code_fingerprint": adjusted_receipt.code_fingerprint,
        "settings_digest": canonical_digest(settings.model_dump(mode="json")),
        "numeric_pof_provider_executed": True,
        "physical_validation_claimed": False,
        "engineering_qualification_claimed": False,
        "limitations": (
            "Generic frequency, damage factor and management factor are caller/provider inputs.",
            "Period probability assumes one constant-rate Poisson process over the declared horizon.",
            "Software execution is not applicability review, physical validation or qualification.",
        ),
    }
    return Api581NumericFrequencyReport(
        **payload,
        report_digest=canonical_digest(
            {"schema_version": "matintegrity.api581_numeric_frequency_report.v1", **payload}
        ),
    )
