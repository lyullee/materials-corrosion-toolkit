"""Caller-owned material specification profiles and exact alias resolution."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from .contracts import Contract, Evidence, canonical_digest


class SpecificationDesignation(Contract):
    namespace: str = Field(min_length=1)
    designation: str = Field(min_length=1)
    edition: str = Field(min_length=1)
    product_form: str = Field(min_length=1)
    condition: str = Field(min_length=1)


class SpecificationAlias(Contract):
    alias_id: str = Field(min_length=1)
    designation: SpecificationDesignation
    mapping_basis: str = Field(min_length=1)
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class SpecificationProfile(Contract):
    profile_id: str = Field(min_length=1)
    canonical_designation: SpecificationDesignation
    aliases: tuple[SpecificationAlias, ...] = ()
    profile_revision: str = Field(min_length=1)
    profile_authority_id: str = Field(min_length=1)
    profile_source_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_aliases(self):
        identities = [row.designation for row in self.aliases]
        if len({canonical_digest(row.model_dump(mode="json")) for row in identities}) != len(identities):
            raise ValueError("aliases within a specification profile must be unique")
        if self.canonical_designation in identities:
            raise ValueError("canonical designation must not be repeated as an alias")
        return self

    @property
    def deterministic_digest(self) -> str:
        return canonical_digest(self.model_dump(mode="json"))


class SpecificationAliasResolution(Contract):
    observed_designation: SpecificationDesignation
    status: Literal["exact", "resolved_alias", "unknown", "ambiguous"]
    profile_id: str | None = None
    canonical_designation: SpecificationDesignation | None = None
    matched_alias_ids: tuple[str, ...] = ()
    candidate_profile_ids: tuple[str, ...] = ()
    evidence_state: Literal["matched", "unknown", "conflicting"]
    basis: str = Field(min_length=1)
    profile_digest: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    resolution_digest: str = Field(pattern=r"^[a-f0-9]{64}$")


def resolve_specification_alias(
    observed: SpecificationDesignation,
    profiles: tuple[SpecificationProfile, ...],
) -> SpecificationAliasResolution:
    """Resolve exact caller declarations only; no fuzzy or cross-edition inference."""

    if not profiles:
        raise ValueError("at least one caller specification profile is required")
    profile_ids = [row.profile_id for row in profiles]
    if len(set(profile_ids)) != len(profile_ids):
        raise ValueError("specification profile identifiers must be unique")

    matches: list[tuple[SpecificationProfile, str, str | None]] = []
    for profile in profiles:
        if observed == profile.canonical_designation:
            matches.append((profile, "exact", None))
        for alias in profile.aliases:
            if observed == alias.designation:
                matches.append((profile, "resolved_alias", alias.alias_id))

    candidates = tuple(sorted({row[0].profile_id for row in matches}))
    if not matches:
        payload = {
            "observed_designation": observed.model_dump(mode="json"),
            "status": "unknown",
            "candidate_profile_ids": (),
            "basis": "No exact canonical designation or caller-declared alias matched.",
        }
        return SpecificationAliasResolution(
            observed_designation=observed,
            status="unknown",
            candidate_profile_ids=(),
            evidence_state="unknown",
            basis=payload["basis"],
            resolution_digest=canonical_digest(payload),
        )
    if len(candidates) != 1:
        payload = {
            "observed_designation": observed.model_dump(mode="json"),
            "status": "ambiguous",
            "candidate_profile_ids": candidates,
            "matched_alias_ids": tuple(sorted(row[2] for row in matches if row[2] is not None)),
            "basis": "The same exact identity maps to more than one caller profile.",
        }
        return SpecificationAliasResolution(
            observed_designation=observed,
            status="ambiguous",
            matched_alias_ids=payload["matched_alias_ids"],
            candidate_profile_ids=candidates,
            evidence_state="conflicting",
            basis=payload["basis"],
            resolution_digest=canonical_digest(payload),
        )

    profile = matches[0][0]
    status = "exact" if any(row[1] == "exact" for row in matches) else "resolved_alias"
    alias_ids = tuple(sorted(row[2] for row in matches if row[2] is not None))
    payload = {
        "observed_designation": observed.model_dump(mode="json"),
        "status": status,
        "profile_id": profile.profile_id,
        "canonical_designation": profile.canonical_designation.model_dump(mode="json"),
        "matched_alias_ids": alias_ids,
        "profile_digest": profile.deterministic_digest,
    }
    return SpecificationAliasResolution(
        observed_designation=observed,
        status=status,
        profile_id=profile.profile_id,
        canonical_designation=profile.canonical_designation,
        matched_alias_ids=alias_ids,
        candidate_profile_ids=(profile.profile_id,),
        evidence_state="matched",
        basis="Exact caller-owned specification profile mapping.",
        profile_digest=profile.deterministic_digest,
        resolution_digest=canonical_digest(payload),
    )
