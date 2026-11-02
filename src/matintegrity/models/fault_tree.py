"""Minimal-cut-set probability for caller-declared independent basic events."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Fraction, canonical_digest
from ..consequence_exchange import IntegrityEventBasis
from ..registry import ModelSpec

FaultTreeProbabilityMeaning = Literal[
    "conditional_first_failure_in_period",
    "point_in_time_state_probability",
    "spatial_size_exceedance_at_one_exposure",
    "detection_given_flaw_and_procedure",
    "unscoped_event_probability",
]


class FaultTreeBasicEvent(Contract):
    event_id: str = Field(min_length=1)
    probability: Fraction
    probability_meaning: FaultTreeProbabilityMeaning
    conditioning: str = Field(min_length=1)
    probability_scope_id: str = Field(min_length=1)
    evidence_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    integrity_event_basis: IntegrityEventBasis | None = None

    @model_validator(mode="after")
    def reconcile_integrity_event(self):
        basis = self.integrity_event_basis
        if basis is not None and (
            basis.event_id != self.event_id
            or basis.event_probability != self.probability
            or basis.probability_semantics != self.probability_meaning
            or basis.probability_conditioning != self.conditioning
            or basis.integrity_result_digest != self.evidence_digest
        ):
            raise ValueError("basic-event fields must exactly match the supplied integrity event basis")
        return self


class FaultTreeAssessment(Contract):
    schema_version: Literal["matintegrity.fault_tree_assessment.v1"] = "matintegrity.fault_tree_assessment.v1"
    top_event_id: str = Field(min_length=1)
    basic_events: tuple[FaultTreeBasicEvent, ...] = Field(min_length=1, max_length=128)
    # Each cut set is an AND gate of event IDs; the top event is the OR of cut sets.
    minimal_cut_sets: tuple[tuple[str, ...], ...] = Field(min_length=1, max_length=4096)
    independence_reviewed: bool = False
    common_cause_reviewed: bool = False
    cut_set_overlap_reviewed: bool = False
    event_scope_reviewed: bool = False

    @model_validator(mode="after")
    def coherent_tree(self):
        ids = [event.event_id for event in self.basic_events]
        if len(ids) != len(set(ids)):
            raise ValueError("basic event identifiers must be unique")
        known = set(ids)
        normalized = []
        for cut in self.minimal_cut_sets:
            if not cut or len(cut) != len(set(cut)):
                raise ValueError("each cut set must contain unique basic event IDs")
            if not set(cut) <= known:
                raise ValueError("cut sets may reference only declared basic events")
            normalized.append(frozenset(cut))
        if len(set(normalized)) != len(normalized):
            raise ValueError("cut sets must be unique")
        for index, cut in enumerate(normalized):
            if any(other < cut for j, other in enumerate(normalized) if j != index):
                raise ValueError("declared cut sets must be minimal; a cut cannot contain another cut")
        if len({event.probability_meaning for event in self.basic_events}) != 1:
            raise ValueError("basic-event probabilities must use one shared probability meaning")
        if len({event.conditioning for event in self.basic_events}) != 1:
            raise ValueError("basic-event probabilities must use one shared conditioning statement")
        if len({event.probability_scope_id for event in self.basic_events}) != 1:
            raise ValueError("basic-event probabilities must use one shared probability scope ID")
        integrity_bases = [event.integrity_event_basis for event in self.basic_events if event.integrity_event_basis]
        if len({(basis.clock_id, basis.horizon_start_s, basis.horizon_end_s) for basis in integrity_bases}) > 1:
            raise ValueError("embedded integrity events must share the same clock and horizon")
        return self


def assess_fault_tree(x: FaultTreeAssessment) -> Calculation:
    """Compute an exact top-event probability only under explicit independence reviews."""
    if not all((x.independence_reviewed, x.common_cause_reviewed, x.cut_set_overlap_reviewed, x.event_scope_reviewed)):
        return Calculation(
            status="needs_data",
            values={},
            notes=("Review basic-event independence, common-cause completeness, cut-set overlap and event scope before quantifying this tree.",),
        )
    probabilities = {event.event_id: float(event.probability) for event in x.basic_events}
    cut_probabilities = [
        math.prod(probabilities[event_id] for event_id in cut)
        for cut in x.minimal_cut_sets
    ]
    # For independent basic events, use inclusion-exclusion over cut-set intersections.
    # This is exact for up to 16 cut sets; beyond that require a reviewed BDD/provider.
    if len(cut_probabilities) > 16:
        return Calculation(status="out_of_scope", values={"minimal_cut_set_count": len(cut_probabilities)}, notes=("Exact inclusion-exclusion is bounded to 16 cut sets; use a separately reviewed BDD/provider for larger trees.",))
    cuts = [frozenset(cut) for cut in x.minimal_cut_sets]

    def probability_for(event_probabilities: dict[str, float]) -> float:
        result = 0.0
        for mask in range(1, 1 << len(cuts)):
            joint_event_union: set[str] = set()
            terms = 0
            for index, cut in enumerate(cuts):
                if mask & (1 << index):
                    terms += 1
                    joint_event_union.update(cut)
            joint = math.prod(event_probabilities[event_id] for event_id in joint_event_union)
            result += joint if terms % 2 else -joint
        return min(1.0, max(0.0, result))

    top_probability = probability_for(probabilities)
    birnbaum = {}
    for event_id in probabilities:
        at_zero = dict(probabilities)
        at_one = dict(probabilities)
        at_zero[event_id] = 0.0
        at_one[event_id] = 1.0
        # The Boolean structure is multilinear in each independent basic-event probability.
        importance = probability_for(at_one) - probability_for(at_zero)
        birnbaum[event_id] = {
            "birnbaum_importance": importance,
            "local_probability_sensitivity": importance,
            "probability_weighted_importance": probabilities[event_id] * importance,
        }
    return Calculation(
        values={
            "top_event_id": x.top_event_id,
            "top_event_probability": top_probability,
            "probability_scope_id": x.basic_events[0].probability_scope_id,
            "input_basic_event_probability_meaning": x.basic_events[0].probability_meaning,
            "probability_conditioning": x.basic_events[0].conditioning,
            "minimal_cut_set_probabilities": cut_probabilities,
            "basic_event_importance": birnbaum,
            "minimal_cut_sets": [list(cut) for cut in x.minimal_cut_sets],
            "basic_event_probability_semantics": {event.event_id: event.probability_meaning for event in x.basic_events},
            "integrity_event_lineage": {
                event.event_id: event.integrity_event_basis.model_dump(mode="json")
                for event in x.basic_events
                if event.integrity_event_basis is not None
            },
            "input_digest": canonical_digest(x.model_dump(mode="json")),
        },
        notes=(
            "The top event is the OR of declared minimal cut sets; each cut set is an AND gate. Inclusion-exclusion is exact under mutually independent basic events, including overlapping cut sets.",
            "Birnbaum importance is the exact conditional change in top-event probability when a basic-event probability changes from zero to one, holding the other probabilities fixed. Probability-weighted importance multiplies this derivative by the supplied basic-event probability; it is a ranking aid, not an additive risk allocation.",
            "This calculation does not infer event probabilities, time horizon compatibility, dependencies, common causes, initiating-event frequency, repair or risk acceptance. The caller owns and reviews all event scopes and probability meanings.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "reliability.fault_tree_minimal_cut_sets",
            FaultTreeAssessment,
            assess_fault_tree,
            {"top_event_probability": "1", "minimal_cut_set_probabilities": "1"},
            ("Caller-declared minimal cut sets; AND within each cut, OR across cuts; exact inclusion-exclusion under reviewed independent basic events.",),
            ("independent_basic_event_minimal_cut_sets",),
            probability_semantics={"top_event_probability": "fault_tree_top_event_probability"},
        )
    ]
