"""Explicit physical-lot coverage under caller-defined inspection escalation rules."""

from fractions import Fraction as Rational
from math import ceil
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, Fraction, canonical_digest
from ..registry import ModelSpec


class InspectionUnitOutcome(Contract):
    record_id: str = Field(min_length=1)
    physical_unit_id: str = Field(min_length=1)
    stage: Literal["initial", "expanded"]
    outcome: Literal["pass", "fail", "inconclusive", "missing"]
    unresolved_basis: str | None = None
    record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unresolved_has_basis(self):
        if self.outcome in ("inconclusive", "missing") and not self.unresolved_basis:
            raise ValueError("missing or inconclusive unit outcomes require a basis")
        return self


class InspectionSamplingPlan(Contract):
    plan_id: str = Field(min_length=1)
    initial_sample_fraction: Fraction
    minimum_initial_sample_count: int = Field(ge=0)
    failure_count_trigger: int = Field(ge=1)
    expanded_inspection_fraction: Fraction
    reuse_initial_definitive_outcomes_for_expanded_coverage: bool
    basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def expanded_not_smaller(self):
        if self.expanded_inspection_fraction < self.initial_sample_fraction:
            raise ValueError("expanded inspection fraction cannot be smaller than the initial fraction")
        return self


class InspectionLotSampling(Contract):
    asset_id: str = Field(min_length=1)
    location_id: str = Field(min_length=1)
    lot_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    criterion_id: str = Field(min_length=1)
    physical_unit_ids: tuple[str, ...] = Field(min_length=1)
    selected_initial_unit_ids: tuple[str, ...]
    mandatory_initial_unit_ids: tuple[str, ...] = ()
    outcomes: tuple[InspectionUnitOutcome, ...] = ()
    selected_plan: InspectionSamplingPlan
    physical_lot_membership_and_sample_selection_reviewed: bool
    common_method_criterion_and_outcome_authority_reviewed: bool
    sampling_plan_and_escalation_authority_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def membership(self):
        population = set(self.physical_unit_ids)
        for name in ("physical_unit_ids", "selected_initial_unit_ids", "mandatory_initial_unit_ids"):
            values = getattr(self, name)
            if len(set(values)) != len(values) or any(not value.strip() for value in values):
                raise ValueError("lot and sample identities must be unique and nonblank")
            if not set(values) <= population:
                raise ValueError("sample identities must belong to the declared physical lot")
        record_ids = [row.record_id for row in self.outcomes]
        keys = [(row.physical_unit_id, row.stage) for row in self.outcomes]
        if len(set(record_ids)) != len(record_ids) or len(set(keys)) != len(keys):
            raise ValueError("outcome records and per-unit per-stage results must be unique")
        for row in self.outcomes:
            if row.physical_unit_id not in population:
                raise ValueError("outcome unit must belong to the declared lot")
            if row.stage == "initial" and row.physical_unit_id not in self.selected_initial_unit_ids:
                raise ValueError("initial-stage outcome must belong to the selected initial sample")
        return self


def inspection_lot_sampling(x: InspectionLotSampling) -> Calculation:
    plan = x.selected_plan
    count = len(x.physical_unit_ids)
    # Fractions use their round-trip decimal spelling; binary products cannot add a spurious unit.
    initial_required = max(
        plan.minimum_initial_sample_count, ceil(Rational(str(plan.initial_sample_fraction)) * count)
    )
    expanded_required = max(initial_required, ceil(Rational(str(plan.expanded_inspection_fraction)) * count))
    failed = sorted({row.physical_unit_id for row in x.outcomes if row.outcome == "fail"})
    escalated = len(failed) >= plan.failure_count_trigger
    lookup = {(row.physical_unit_id, row.stage): row for row in x.outcomes}
    definitive = ("pass", "fail")
    initial_complete = {
        unit
        for unit in x.selected_initial_unit_ids
        if (row := lookup.get((unit, "initial"))) is not None and row.outcome in definitive
    }
    expanded_complete = {
        row.physical_unit_id for row in x.outcomes if row.stage == "expanded" and row.outcome in definitive
    }
    if plan.reuse_initial_definitive_outcomes_for_expanded_coverage:
        expanded_complete |= initial_complete
    missing_initial = [unit for unit in x.selected_initial_unit_ids if unit not in initial_complete]
    missing_mandatory = [unit for unit in x.mandatory_initial_unit_ids if unit not in initial_complete]
    reviews_complete = (
        x.physical_lot_membership_and_sample_selection_reviewed
        and x.common_method_criterion_and_outcome_authority_reviewed
        and x.sampling_plan_and_escalation_authority_reviewed
    )
    initial_sufficient = (
        len(initial_complete) >= initial_required and not missing_initial and not missing_mandatory
    )
    expanded_sufficient = not escalated or len(expanded_complete) >= expanded_required
    complete = reviews_complete and initial_sufficient and expanded_sufficient
    status = "out_of_scope" if initial_required > count else "computed" if complete else "needs_data"
    return Calculation(
        status=status,
        values={
            "lot_id": x.lot_id,
            "method_id": x.method_id,
            "criterion_id": x.criterion_id,
            "population_count": count,
            "required_initial_count": initial_required,
            "required_expanded_count_if_triggered": expanded_required,
            "definitive_initial_count": len(initial_complete),
            "definitive_expanded_coverage_count": len(expanded_complete),
            "reported_failed_unit_ids": failed,
            "reported_failure_trigger_reached": escalated,
            "missing_or_inconclusive_initial_unit_ids": missing_initial,
            "missing_mandatory_initial_unit_ids": missing_mandatory,
            "expanded_units_without_definitive_coverage": [
                unit for unit in x.physical_unit_ids if unit not in expanded_complete
            ]
            if escalated
            else [],
            "required_inspection_coverage_complete": complete,
            "plan_digest": canonical_digest(plan.model_dump(mode="json")),
            "lot_snapshot_digest": canonical_digest(x.model_dump(mode="json")),
        },
        notes=(
            "Counts refer to explicit physical units for one reviewed method and criterion. Definitive failures count as inspected, never as passing.",
            "This is deterministic coverage accounting, not random selection, statistical acceptance sampling, POD, failure probability or product acceptance.",
            "Any recorded failure is retained across stages; later passing observations do not erase escalation. Missing or inconclusive observations do not count as definitive coverage.",
        ),
    )


def specifications():
    def same_identity(x, context):
        if (x.asset_id, x.location_id) != (context.asset_id, context.location_id):
            raise ValueError("inspection lot asset and location must match the run context")

    return [
        ModelSpec(
            "inspection.lot_sampling_escalation",
            InspectionLotSampling,
            inspection_lot_sampling,
            {
                "lot_id": "1",
                "method_id": "1",
                "criterion_id": "1",
                "population_count": "count",
                "required_initial_count": "count",
                "required_expanded_count_if_triggered": "count",
                "definitive_initial_count": "count",
                "definitive_expanded_coverage_count": "count",
                "reported_failed_unit_ids": "1",
                "reported_failure_trigger_reached": "1",
                "missing_or_inconclusive_initial_unit_ids": "1",
                "missing_mandatory_initial_unit_ids": "1",
                "expanded_units_without_definitive_coverage": "1",
                "required_inspection_coverage_complete": "1",
                "plan_digest": "1",
                "lot_snapshot_digest": "1",
            },
            (
                "Explicit physical population and caller-authorized sample/escalation plan for one method and criterion.",
            ),
            ("caller_lot_inspection_coverage_escalation",),
            context_validator=same_identity,
        )
    ]
