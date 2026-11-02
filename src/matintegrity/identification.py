"""Explicit designation aliases and interval-valued chemical identification evidence."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, model_validator

from .contracts import Calculation, Contract, Evidence, Fraction, canonical_digest

ElementSymbol = Annotated[str, Field(pattern=r"^[A-Z][a-z]?$")]


class MaterialDesignation(Contract):
    namespace: str = Field(min_length=1)
    specification: str = Field(min_length=1)
    edition: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    product_form: str = Field(min_length=1)
    condition: str = Field(min_length=1)


class DesignationAlias(Contract):
    alias: MaterialDesignation
    canonical: MaterialDesignation
    evidence: Evidence
    permitted_use_note: str = Field(min_length=1)


class DesignationResolver:
    """One reviewed directed alias, without fuzzy matching or inferred substitution."""

    def __init__(self, aliases: list[DesignationAlias]):
        self._aliases = {}
        for entry in aliases:
            if not entry.evidence.license_id:
                raise ValueError("a declared alias-data license or entitlement identifier is required")
            key = canonical_digest(entry.alias.model_dump(mode="json"))
            if key in self._aliases:
                raise ValueError("ambiguous alias; reconcile conditions and editions explicitly")
            self._aliases[key] = entry.model_copy(deep=True)

    def resolve(self, designation: MaterialDesignation) -> dict:
        if not isinstance(designation, MaterialDesignation):
            raise TypeError("an explicit complete MaterialDesignation is required")
        key = canonical_digest(designation.model_dump(mode="json"))
        entry = self._aliases.get(key)
        if entry is None:
            return dict(
                status="needs_data",
                canonical=None,
                reason="No exact reviewed alias for this namespace, edition, grade, form and condition.",
            )
        return dict(
            schema_version="matintegrity.designation_alias.v1",
            status="resolved",
            requested=designation.model_dump(mode="json"),
            canonical=entry.canonical.model_dump(mode="json"),
            evidence=entry.evidence.model_dump(mode="json"),
            permitted_use_note=entry.permitted_use_note,
            mapping_digest=canonical_digest(entry.model_dump(mode="json")),
            meaning="Caller-reviewed naming relation only; no inferred material substitution or transitive equivalence.",
        )


class FractionInterval(Contract):
    lower: Fraction
    upper: Fraction

    @model_validator(mode="after")
    def ordered(self):
        if self.upper < self.lower:
            raise ValueError("mass-fraction interval bounds are reversed")
        return self


class ChemistryRecord(Contract):
    record_id: str = Field(min_length=1)
    physical_scope_id: str = Field(min_length=1)
    heat_id: str | None = None
    designation: MaterialDesignation | None = None
    method_id: str = Field(min_length=1)
    element_intervals: dict[ElementSymbol, FractionInterval | None]
    interval_interpretation: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def composition(self):
        if sum(value.lower for value in self.element_intervals.values() if value is not None) > 1 + 1e-12:
            raise ValueError("reported elemental lower fractions cannot sum above one")
        return self


class ChemistryRequirements(Contract):
    requirements_id: str = Field(min_length=1)
    designation: MaterialDesignation
    element_limits: dict[ElementSymbol, FractionInterval] = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def feasible_lower_composition(self):
        if sum(v.lower for v in self.element_limits.values()) > 1 + 1e-12:
            raise ValueError("required elemental lower fractions cannot sum above one")
        return self


class ChemistryReconciliation(Contract):
    certificate: ChemistryRecord
    verification: ChemistryRecord
    requirements: ChemistryRequirements
    require_matching_heat_ids: bool
    require_verification_designation: bool
    require_certificate_verification_interval_overlap: bool

    @model_validator(mode="after")
    def scope(self):
        if self.certificate.physical_scope_id != self.verification.physical_scope_id:
            raise ValueError("certificate and verification must refer to the same declared physical scope")
        return self


def reconcile_chemistry(x: ChemistryReconciliation) -> Calculation:
    checks = []
    elements = []

    def check(identifier, outcome, reason):
        checks.append(dict(check_id=identifier, outcome=outcome, reason=reason))

    def identity(record, identifier, required):
        if not required:
            return
        outcome = (
            "unknown"
            if record.designation is None
            else "satisfied"
            if record.designation == x.requirements.designation
            else "not_satisfied"
        )
        check(
            identifier,
            outcome,
            "Exact namespace, specification, edition, grade, product and condition comparison.",
        )

    identity(x.certificate, "certificate_designation", True)
    identity(x.verification, "verification_designation", x.require_verification_designation)
    if x.require_matching_heat_ids:
        heat_a, heat_b = x.certificate.heat_id, x.verification.heat_id
        outcome = (
            "unknown"
            if heat_a is None or heat_b is None
            else "satisfied"
            if heat_a == heat_b
            else "not_satisfied"
        )
        check(
            "heat_traceability",
            outcome,
            "Heat identifiers are compared as supplied; missing IDs are not a match.",
        )

    def compare(value, limit):
        if value is None:
            return "unknown"
        if value.lower >= limit.lower and value.upper <= limit.upper:
            return "satisfied"
        if value.upper < limit.lower or value.lower > limit.upper:
            return "not_satisfied"
        return "unknown"

    for element, limit in x.requirements.element_limits.items():
        certified = x.certificate.element_intervals.get(element)
        measured = x.verification.element_intervals.get(element)
        states = {"certificate": compare(certified, limit), "verification": compare(measured, limit)}
        overlap = (
            "unknown"
            if certified is None or measured is None
            else "satisfied"
            if max(certified.lower, measured.lower) <= min(certified.upper, measured.upper)
            else "not_satisfied"
        )
        for label, state in states.items():
            check(
                f"{element}.{label}",
                state,
                "Supplied interval entirely within, entirely outside, or crossing the supplied limits.",
            )
        if x.require_certificate_verification_interval_overlap:
            check(
                f"{element}.consistency",
                overlap,
                "Interval overlap is the caller-declared consistency criterion; it is not a chemical homogeneity model.",
            )
        elements.append(
            dict(
                element=element,
                limits=limit.model_dump(),
                certificate_outcome=states["certificate"],
                verification_outcome=states["verification"],
                interval_overlap_outcome=overlap,
            )
        )
    outcomes = [row["outcome"] for row in checks]
    overall = (
        "not_satisfied"
        if "not_satisfied" in outcomes
        else "unknown"
        if "unknown" in outcomes
        else "satisfied"
    )
    return Calculation(
        values=dict(
            outcome=overall,
            checks=checks,
            elements=elements,
            physical_scope_id=x.certificate.physical_scope_id,
            requirements_id=x.requirements.requirements_id,
        ),
        notes=(
            "Missing or unmeasurable chemistry remains unknown; method labels do not manufacture measured elements or material heat-treatment evidence.",
            "Conformance is limited to the supplied identity, intervals and policy. Mechanical properties, specimen representativeness, certificate authenticity and unprovided standard requirements are separate evidence.",
        ),
    )
