"""Validate caller-declared species transfers across WCO2 workflow stages."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, StrictInt, model_validator

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec


class SpeciesComposition(Contract):
    """Caller-owned formula and formal charge for one stage-local species ID."""

    species_id: str = Field(min_length=1)
    charge_number: StrictInt
    element_counts: dict[str, StrictInt] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_composition(self):
        if any(not key.strip() for key in self.element_counts):
            raise ValueError("element symbols must be nonempty")
        if any(value < 0 for value in self.element_counts.values()):
            raise ValueError("element counts cannot be negative")
        return self


class StoichiometricTransferTerm(Contract):
    species_id: str = Field(min_length=1)
    coefficient: StrictInt = Field(ge=1)


class SpeciesTransferRule(Contract):
    transfer_id: str = Field(min_length=1)
    transfer_kind: Literal["identity", "renamed", "reaction_transformed"]
    source_terms: tuple[StoichiometricTransferTerm, ...] = Field(min_length=1, max_length=100)
    target_terms: tuple[StoichiometricTransferTerm, ...] = Field(min_length=1, max_length=100)
    reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class ExcludedSpecies(Contract):
    species_id: str = Field(min_length=1)
    exclusion_reason: str = Field(min_length=1)
    reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class Wco2SpeciesTransferAuditRequest(Contract):
    """Audit element/charge closure of a declared chemistry-stage handoff."""

    schema_version: Literal["matintegrity.wco2_species_transfer_audit.v1"] = "matintegrity.wco2_species_transfer_audit.v1"
    upstream_species: tuple[SpeciesComposition, ...] = Field(min_length=1, max_length=1000)
    downstream_species: tuple[SpeciesComposition, ...] = Field(min_length=1, max_length=1000)
    transfers: tuple[SpeciesTransferRule, ...] = Field(min_length=1, max_length=1000)
    excluded_upstream_species: tuple[ExcludedSpecies, ...] = ()

    @model_validator(mode="after")
    def validate_mapping(self):
        upstream = {row.species_id: row for row in self.upstream_species}
        downstream = {row.species_id: row for row in self.downstream_species}
        if len(upstream) != len(self.upstream_species) or len(downstream) != len(self.downstream_species):
            raise ValueError("species IDs must be unique within each stage")
        if len({row.transfer_id for row in self.transfers}) != len(self.transfers):
            raise ValueError("transfer IDs must be unique")
        referenced_source: set[str] = set()
        referenced_target: set[str] = set()
        for rule in self.transfers:
            if not rule.reviewed:
                raise ValueError("each transfer requires caller review")
            src = [row.species_id for row in rule.source_terms]
            dst = [row.species_id for row in rule.target_terms]
            if len(src) != len(set(src)) or len(dst) != len(set(dst)):
                raise ValueError("species terms must be unique within a transfer side")
            if not set(src) <= set(upstream) or not set(dst) <= set(downstream):
                raise ValueError("transfer terms reference undeclared stage-local species")
            referenced_source.update(src)
            referenced_target.update(dst)
            if rule.transfer_kind in {"identity", "renamed"}:
                if len(rule.source_terms) != 1 or len(rule.target_terms) != 1:
                    raise ValueError("identity/rename rules require exactly one source and target species")
                a, b = rule.source_terms[0], rule.target_terms[0]
                if a.coefficient != 1 or b.coefficient != 1:
                    raise ValueError("identity/rename rules require unit stoichiometry")
                if rule.transfer_kind == "identity" and a.species_id != b.species_id:
                    raise ValueError("identity transfer must preserve species ID")
                if rule.transfer_kind == "renamed" and a.species_id == b.species_id:
                    raise ValueError("renamed transfer must declare distinct IDs")
            left_charge = sum(term.coefficient * upstream[term.species_id].charge_number for term in rule.source_terms)
            right_charge = sum(term.coefficient * downstream[term.species_id].charge_number for term in rule.target_terms)
            if left_charge != right_charge:
                raise ValueError(f"transfer {rule.transfer_id} does not conserve formal charge")
            elements = set().union(*(upstream[t.species_id].element_counts for t in rule.source_terms),
                                   *(downstream[t.species_id].element_counts for t in rule.target_terms))
            for element in elements:
                left = sum(t.coefficient * upstream[t.species_id].element_counts.get(element, 0)
                           for t in rule.source_terms)
                right = sum(t.coefficient * downstream[t.species_id].element_counts.get(element, 0)
                            for t in rule.target_terms)
                if left != right:
                    raise ValueError(f"transfer {rule.transfer_id} does not conserve declared element {element}")
        excluded = [row.species_id for row in self.excluded_upstream_species]
        if len(excluded) != len(set(excluded)) or not set(excluded) <= set(upstream):
            raise ValueError("excluded species must be unique declared upstream species")
        if any(not row.reviewed for row in self.excluded_upstream_species):
            raise ValueError("every upstream exclusion requires caller review")
        if referenced_source & set(excluded):
            raise ValueError("an upstream species cannot be both transferred and excluded")
        if referenced_source | set(excluded) != set(upstream):
            raise ValueError("each upstream species must occur in a transfer or an explicit exclusion")
        if referenced_target != set(downstream):
            raise ValueError("every downstream species must occur in at least one declared transfer")
        return self


def audit_wco2_species_transfer(request: Wco2SpeciesTransferAuditRequest) -> Calculation:
    payload = request.model_dump(mode="json")
    rules = []
    upstream = {row.species_id: row for row in request.upstream_species}
    downstream = {row.species_id: row for row in request.downstream_species}
    for rule in request.transfers:
        rules.append({
            "transfer_id": rule.transfer_id,
            "transfer_kind": rule.transfer_kind,
            "source_terms": [row.model_dump(mode="json") for row in rule.source_terms],
            "target_terms": [row.model_dump(mode="json") for row in rule.target_terms],
            "element_charge_balanced": True,
            "source_composition_sha256": canonical_digest([upstream[row.species_id].model_dump(mode="json") for row in rule.source_terms]),
            "target_composition_sha256": canonical_digest([downstream[row.species_id].model_dump(mode="json") for row in rule.target_terms]),
            "evidence": [row.model_dump(mode="json") for row in rule.evidence],
        })
    return Calculation(values={
        "model_id": "integration.wco2_species_transfer_audit",
        "status": "computed",
        "request_sha256": canonical_digest(payload),
        "transfer_rules": rules,
        "excluded_upstream_species": [row.model_dump(mode="json") for row in request.excluded_upstream_species],
        "upstream_species_count": len(request.upstream_species),
        "downstream_species_count": len(request.downstream_species),
        "interpretation_limit": "caller-declared element/charge bookkeeping only; no reaction mechanism, equilibrium, standard-state conversion, kinetics, transport, or corrosion is inferred",
    }, notes=("A balanced transfer record checks only its declared formulas and coefficients; it does not prove that the transformation occurs in the represented process.",))


def specifications() -> list[ModelSpec]:
    return [ModelSpec(
        model_id="integration.wco2_species_transfer_audit",
        input_type=Wco2SpeciesTransferAuditRequest,
        evaluator=audit_wco2_species_transfer,
        units={"upstream_species_count": "1", "downstream_species_count": "1"},
        assumptions=("Species formulas, formal charges, transfer coefficients and Evidence are caller supplied.", "Balanced bookkeeping does not establish mechanistic or thermodynamic applicability."),
        source_ids=("caller_wco2_species_transfer_audit",),
        qualification="user_model",
    )]
