"""Recorded chemical-cleaning exposure against caller-owned compatibility envelopes."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, Nonnegative, Positive
from ..registry import ModelSpec


class ChemicalCleaningStep(Contract):
    step_id: str = Field(min_length=1)
    envelope_id: str = Field(min_length=1)
    solution_id: str = Field(min_length=1)
    chemical_family: str = Field(min_length=1)
    start_time_s: Nonnegative
    end_time_s: Positive
    concentration_mass_fraction: Fraction
    temperature_K: Positive
    pH: float = Field(ge=0, le=14)
    record_valid: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end_time_s <= self.start_time_s:
            raise ValueError("each cleaning step must have positive duration")
        return self


class CleaningCompatibilityEnvelope(Contract):
    envelope_id: str = Field(min_length=1)
    material_condition_id: str | None = Field(default=None, min_length=1)
    solution_id: str = Field(min_length=1)
    chemical_family: str = Field(min_length=1)
    minimum_concentration_mass_fraction: Fraction
    maximum_concentration_mass_fraction: Fraction
    minimum_temperature_K: Positive
    maximum_temperature_K: Positive
    minimum_pH: float = Field(ge=0, le=14)
    maximum_pH: float = Field(ge=0, le=14)
    maximum_single_exposure_s: Positive
    maximum_cumulative_exposure_s: Positive
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def ordered_bounds(self):
        pairs = (
            (
                self.minimum_concentration_mass_fraction,
                self.maximum_concentration_mass_fraction,
                "concentration",
            ),
            (self.minimum_temperature_K, self.maximum_temperature_K, "temperature"),
            (self.minimum_pH, self.maximum_pH, "pH"),
        )
        for lower, upper, name in pairs:
            if upper < lower:
                raise ValueError(f"{name} envelope bounds must be ordered")
        if self.maximum_cumulative_exposure_s < self.maximum_single_exposure_s:
            raise ValueError("cumulative exposure bound cannot be below the single-step bound")
        return self


class ChemicalCleaningRecord(Contract):
    cleaning_record_id: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    clock_id: str = Field(min_length=1)
    steps: tuple[ChemicalCleaningStep, ...] = Field(min_length=1)
    compatibility_envelopes: tuple[CleaningCompatibilityEnvelope, ...] = Field(min_length=1)
    record_completeness_reviewed: bool
    sequence_and_clock_reviewed: bool
    material_identity_reviewed: bool
    compatibility_envelopes_reviewed: bool

    @model_validator(mode="after")
    def identities_and_clock(self):
        step_ids = [step.step_id for step in self.steps]
        envelope_ids = [envelope.envelope_id for envelope in self.compatibility_envelopes]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("cleaning step identifiers must be unique")
        if len(envelope_ids) != len(set(envelope_ids)):
            raise ValueError("compatibility envelope identifiers must be unique")
        for first, second in zip(self.steps, self.steps[1:], strict=False):
            if second.start_time_s < first.end_time_s:
                raise ValueError("cleaning steps must be ordered and cannot overlap")
        return self


def chemical_cleaning_envelope(x: ChemicalCleaningRecord) -> Calculation:
    missing_reviews = [
        name
        for name, reviewed in (
            ("record_completeness", x.record_completeness_reviewed),
            ("sequence_and_clock", x.sequence_and_clock_reviewed),
            ("material_identity", x.material_identity_reviewed),
            ("compatibility_envelopes", x.compatibility_envelopes_reviewed),
        )
        if not reviewed
    ]
    invalid_steps = [step.step_id for step in x.steps if not step.record_valid]
    envelopes = {envelope.envelope_id: envelope for envelope in x.compatibility_envelopes}
    unmatched_steps = [step.step_id for step in x.steps if step.envelope_id not in envelopes]
    if missing_reviews or invalid_steps or unmatched_steps:
        return Calculation(
            status="needs_data",
            values={
                "cleaning_record_id": x.cleaning_record_id,
                "missing_reviews": missing_reviews,
                "invalid_step_ids": invalid_steps,
                "unmatched_step_ids": unmatched_steps,
            },
            notes=(
                "Exposure comparison is withheld until every step is valid, mapped and independently reviewed.",
            ),
        )

    unbound_envelopes = sorted(
        {step.envelope_id for step in x.steps if envelopes[step.envelope_id].material_condition_id is None}
    )
    mismatched_steps = [
        step.step_id
        for step in x.steps
        if envelopes[step.envelope_id].material_condition_id not in (None, x.material_condition_id)
    ]
    if unbound_envelopes or mismatched_steps:
        return Calculation(
            status="out_of_scope" if mismatched_steps else "needs_data",
            values={
                "cleaning_record_id": x.cleaning_record_id,
                "unbound_material_envelope_ids": unbound_envelopes,
                "material_mismatch_step_ids": mismatched_steps,
            },
            notes=(
                "Every used compatibility envelope must bind the exact reviewed material condition; an unbound legacy record cannot establish compatibility.",
            ),
        )
    cumulative_by_envelope = {identifier: 0.0 for identifier in envelopes}
    step_rows = []
    violating_steps = []
    for step in x.steps:
        envelope = envelopes[step.envelope_id]
        duration = step.end_time_s - step.start_time_s
        cumulative_by_envelope[step.envelope_id] += duration
        violations = []
        if step.solution_id != envelope.solution_id:
            violations.append("solution_identity")
        if step.chemical_family != envelope.chemical_family:
            violations.append("chemical_family_identity")
        if not (
            envelope.minimum_concentration_mass_fraction
            <= step.concentration_mass_fraction
            <= envelope.maximum_concentration_mass_fraction
        ):
            violations.append("concentration")
        if not envelope.minimum_temperature_K <= step.temperature_K <= envelope.maximum_temperature_K:
            violations.append("temperature")
        if not envelope.minimum_pH <= step.pH <= envelope.maximum_pH:
            violations.append("pH")
        if duration > envelope.maximum_single_exposure_s:
            violations.append("single_exposure_duration")
        if violations:
            violating_steps.append(step.step_id)
        step_rows.append(
            {
                "step_id": step.step_id,
                "envelope_id": step.envelope_id,
                "duration_s": duration,
                "violations": violations,
                "within_declared_step_envelope": not violations,
            }
        )

    cumulative_rows = []
    violating_envelopes = []
    for identifier, envelope in envelopes.items():
        duration = cumulative_by_envelope[identifier]
        within = duration <= envelope.maximum_cumulative_exposure_s
        if not within:
            violating_envelopes.append(identifier)
        cumulative_rows.append(
            {
                "envelope_id": identifier,
                "cumulative_exposure_s": duration,
                "maximum_cumulative_exposure_s": envelope.maximum_cumulative_exposure_s,
                "remaining_cumulative_exposure_s": envelope.maximum_cumulative_exposure_s - duration,
                "within_declared_cumulative_envelope": within,
            }
        )

    within = not violating_steps and not violating_envelopes
    return Calculation(
        values={
            "cleaning_record_id": x.cleaning_record_id,
            "step_comparisons": step_rows,
            "cumulative_exposure_by_envelope": cumulative_rows,
            "violating_step_ids": violating_steps,
            "violating_envelope_ids": violating_envelopes,
            "declared_envelope_outcome": "within" if within else "outside",
        },
        notes=(
            "The outcome compares records only with caller-supplied envelopes; it is not a code or procedure acceptance decision.",
            "Chemical reaction, solution mixing, local concentration, corrosion rate, residue and rinse effectiveness are not predicted.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("chemical cleaning asset and location must match the run context")

    return [
        ModelSpec(
            "fabrication.chemical_cleaning_envelope",
            ChemicalCleaningRecord,
            chemical_cleaning_envelope,
            {
                "cleaning_record_id": "1",
                "step_comparisons": "1",
                "cumulative_exposure_by_envelope": "1",
                "violating_step_ids": "1",
                "violating_envelope_ids": "1",
                "declared_envelope_outcome": "1",
            },
            (
                "Each recorded step has uniform declared solution properties and maps to one caller-owned material compatibility envelope.",
                "Exposure durations use a reviewed common clock; no unrecorded interval is inferred.",
                "The model performs range and duration bookkeeping only and contains no embedded cleaning or material acceptance rule.",
            ),
            ("declared_chemical_compatibility_envelope",),
            version="1.1.0",
            context_validator=same_identity,
        )
    ]
