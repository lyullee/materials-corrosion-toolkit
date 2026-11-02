"""Profile-set audit built on the exact lower-level specification alias resolver."""

from __future__ import annotations

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..registry import ModelSpec
from ..specification_aliases import (
    SpecificationDesignation,
    SpecificationProfile,
    resolve_specification_alias,
)


class SpecificationAliasQuery(Contract):
    query_id: str = Field(min_length=1)
    designation: SpecificationDesignation
    query_source_id: str = Field(min_length=1)
    query_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class SpecificationProfileMaterialBinding(Contract):
    """Caller-owned material metadata attached to one exact alias profile."""

    profile_id: str = Field(min_length=1)
    material_family_id: str = Field(min_length=1)
    material_condition_id: str = Field(min_length=1)
    binding_source_id: str = Field(min_length=1)
    binding_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @property
    def deterministic_digest(self) -> str:
        return canonical_digest(self.model_dump(mode="json"))


class SpecificationAliasProfileSetAudit(Contract):
    audit_id: str = Field(min_length=1)
    profile_set_id: str = Field(min_length=1)
    profile_set_revision: str = Field(min_length=1)
    profiles: tuple[SpecificationProfile, ...] = Field(min_length=1)
    material_bindings: tuple[SpecificationProfileMaterialBinding, ...] = Field(min_length=1)
    queries: tuple[SpecificationAliasQuery, ...] = Field(min_length=1)
    exact_namespace_designation_edition_form_and_condition_reviewed: bool
    profile_authorities_sources_evidence_and_digests_reviewed: bool
    duplicate_ambiguity_and_unregistered_policy_reviewed: bool
    query_sources_and_record_digests_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_inputs(self):
        profile_ids = [row.profile_id for row in self.profiles]
        binding_ids = [row.profile_id for row in self.material_bindings]
        query_ids = [row.query_id for row in self.queries]
        if len(set(profile_ids)) != len(profile_ids):
            raise ValueError("specification alias profile identifiers must be unique")
        if len(set(query_ids)) != len(query_ids):
            raise ValueError("specification alias query identifiers must be unique")
        if len(set(binding_ids)) != len(binding_ids):
            raise ValueError("material binding profile identifiers must be unique")
        if set(binding_ids) != set(profile_ids):
            raise ValueError("each specification profile requires exactly one material binding")
        return self


def specification_alias_profile_set_audit(x: SpecificationAliasProfileSetAudit) -> Calculation:
    missing_reviews = [
        name
        for name in (
            "exact_namespace_designation_edition_form_and_condition_reviewed",
            "profile_authorities_sources_evidence_and_digests_reviewed",
            "duplicate_ambiguity_and_unregistered_policy_reviewed",
            "query_sources_and_record_digests_reviewed",
        )
        if not getattr(x, name)
    ]
    profile_digests = {row.profile_id: row.deterministic_digest for row in x.profiles}
    binding_by_profile = {row.profile_id: row for row in x.material_bindings}
    binding_digests = {row.profile_id: row.deterministic_digest for row in x.material_bindings}
    profile_identity_index: dict[str, list[dict[str, str]]] = {}
    for profile in x.profiles:
        canonical_key = canonical_digest(profile.canonical_designation.model_dump(mode="json"))
        profile_identity_index.setdefault(canonical_key, []).append(
            {"profile_id": profile.profile_id, "match_kind": "canonical"}
        )
        for alias in profile.aliases:
            alias_key = canonical_digest(alias.designation.model_dump(mode="json"))
            profile_identity_index.setdefault(alias_key, []).append(
                {"profile_id": profile.profile_id, "match_kind": "declared_alias"}
            )
    ambiguous_profile_identities = [
        {
            "designation_digest": key,
            "candidate_profile_ids": sorted({row["profile_id"] for row in rows}),
            "match_kinds": sorted({row["match_kind"] for row in rows}),
        }
        for key, rows in sorted(profile_identity_index.items())
        if len({row["profile_id"] for row in rows}) > 1
    ]
    if missing_reviews:
        body = {
            "audit_id": x.audit_id,
            "profile_set_id": x.profile_set_id,
            "audit_outcome": "insufficient_evidence",
            "missing_reviews": missing_reviews,
            "profile_digests": profile_digests,
            "material_binding_digests": binding_digests,
            "ambiguous_profile_identities": ambiguous_profile_identities,
            "fuzzy_matching_performed": False,
            "standard_equivalence_claim": False,
            "automatic_acceptance_claim": False,
            "input_digest": canonical_digest(x.model_dump(mode="json")),
        }
        body["report_digest"] = canonical_digest(body)
        return Calculation(
            status="needs_data",
            values=body,
            notes=("The profile set and exact query lineage require caller review before resolution.",),
        )

    rows = []
    for query in x.queries:
        resolution = resolve_specification_alias(query.designation, x.profiles)
        binding = binding_by_profile[resolution.profile_id] if resolution.profile_id is not None else None
        rows.append(
            {
                "query_id": query.query_id,
                "query_source_id": query.query_source_id,
                "query_record_digest": query.query_record_digest,
                "query_designation": query.designation.model_dump(mode="json"),
                "resolution_status": resolution.status,
                "profile_id": resolution.profile_id,
                "candidate_profile_ids": list(resolution.candidate_profile_ids),
                "matched_alias_ids": list(resolution.matched_alias_ids),
                "canonical_designation": (
                    resolution.canonical_designation.model_dump(mode="json")
                    if resolution.canonical_designation is not None
                    else None
                ),
                "profile_digest": resolution.profile_digest,
                "material_family_id": binding.material_family_id if binding else None,
                "material_condition_id": binding.material_condition_id if binding else None,
                "material_binding_source_id": binding.binding_source_id if binding else None,
                "material_binding_record_digest": (binding.binding_record_digest if binding else None),
                "material_binding_digest": (binding.deterministic_digest if binding else None),
                "resolution_digest": resolution.resolution_digest,
                "resolution_basis": resolution.basis,
            }
        )
    counts = {
        status: sum(row["resolution_status"] == status for row in rows)
        for status in ("exact", "resolved_alias", "unknown", "ambiguous")
    }
    coverage_fraction = (counts["exact"] + counts["resolved_alias"]) / len(rows)
    body = {
        "audit_id": x.audit_id,
        "profile_set_id": x.profile_set_id,
        "profile_set_revision": x.profile_set_revision,
        "audit_outcome": (
            "ambiguous"
            if counts["ambiguous"] or ambiguous_profile_identities
            else "incomplete_coverage"
            if counts["unknown"]
            else "exactly_resolved"
        ),
        "query_resolution_rows": rows,
        "resolution_counts": counts,
        "resolved_query_fraction": coverage_fraction,
        "profile_digests": profile_digests,
        "material_binding_digests": binding_digests,
        "ambiguous_profile_identities": ambiguous_profile_identities,
        "fuzzy_matching_performed": False,
        "standard_equivalence_claim": False,
        "automatic_acceptance_claim": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        values=body,
        notes=(
            "Resolution delegates to the lower-level exact alias resolver; strings are not normalized or fuzzily matched.",
            "Coverage, ambiguity and provenance are profile-set audit results, not standard or material equivalence claims.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.specification_aliases",
            SpecificationAliasProfileSetAudit,
            specification_alias_profile_set_audit,
            {
                "audit_id": "1",
                "profile_set_id": "1",
                "profile_set_revision": "1",
                "audit_outcome": "1",
                "query_resolution_rows": "mixed",
                "resolution_counts": "count",
                "resolved_query_fraction": "1",
                "profile_digests": "1",
                "material_binding_digests": "1",
                "ambiguous_profile_identities": "mixed",
                "fuzzy_matching_performed": "1",
                "standard_equivalence_claim": "1",
                "automatic_acceptance_claim": "1",
                "input_digest": "1",
                "report_digest": "1",
            },
            (
                "The existing exact resolver compares namespace, designation, edition, form and condition without normalization.",
                "Profile-set audit preserves canonical designations, caller authorities, evidence and deterministic digests.",
                "Ambiguous and unregistered queries remain explicit and create no equivalence or acceptance claim.",
            ),
            ("authored_exact_specification_alias_profile_set_audit",),
        )
    ]
