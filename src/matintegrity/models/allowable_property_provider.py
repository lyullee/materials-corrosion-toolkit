"""Audited orchestration of caller-supplied temperature-dependent property tables."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from ..contracts import Calculation, Contract, Evidence, canonical_digest
from ..providers import DesignPropertyTable, PropertyQuery, TabulatedPropertyProvider
from ..registry import ModelSpec


class AllowablePropertyTableRecord(Contract):
    """One caller-controlled table and its provider/applicability lineage."""

    table_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    provider_revision: str = Field(min_length=1)
    provider_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    rights_basis: Literal["caller_owned", "caller_licensed"]
    entitlement_id: str = Field(min_length=1)
    applicability_id: str = Field(min_length=1)
    applicability_statement: str = Field(min_length=1)
    table: DesignPropertyTable

    @property
    def deterministic_digest(self) -> str:
        return canonical_digest(self.model_dump(mode="json"))


class AllowablePropertyQueryRecord(Contract):
    query_id: str = Field(min_length=1)
    applicability_id: str = Field(min_length=1)
    query: PropertyQuery
    query_source_id: str = Field(min_length=1)
    query_record_digest: str = Field(pattern=r"^[a-f0-9]{64}$")
    evidence: tuple[Evidence, ...] = Field(min_length=1)


class AllowablePropertyProviderAudit(Contract):
    audit_id: str = Field(min_length=1)
    provider_set_id: str = Field(min_length=1)
    provider_set_revision: str = Field(min_length=1)
    tables: tuple[AllowablePropertyTableRecord, ...] = Field(min_length=1)
    queries: tuple[AllowablePropertyQueryRecord, ...] = Field(min_length=1)
    material_product_condition_orientation_and_edition_reviewed: bool
    provider_revision_rights_and_provenance_reviewed: bool
    applicability_units_and_temperature_support_reviewed: bool
    query_identity_units_and_digests_reviewed: bool
    evidence: tuple[Evidence, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_records(self):
        table_ids = [row.table_id for row in self.tables]
        query_ids = [row.query_id for row in self.queries]
        identities = [canonical_digest(row.table.identity.model_dump(mode="json")) for row in self.tables]
        if len(set(table_ids)) != len(table_ids):
            raise ValueError("property table identifiers must be unique")
        if len(set(query_ids)) != len(query_ids):
            raise ValueError("property query identifiers must be unique")
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate exact property identity; reconcile provider tables explicitly")
        return self


def allowable_property_provider_audit(x: AllowablePropertyProviderAudit) -> Calculation:
    """Audit lineage and resolve only exact, in-support lower-level provider queries."""

    review_fields = (
        "material_product_condition_orientation_and_edition_reviewed",
        "provider_revision_rights_and_provenance_reviewed",
        "applicability_units_and_temperature_support_reviewed",
        "query_identity_units_and_digests_reviewed",
    )
    missing_reviews = [name for name in review_fields if not getattr(x, name)]
    table_audit_rows = [
        {
            "table_id": row.table_id,
            "provider_id": row.provider_id,
            "provider_revision": row.provider_revision,
            "provider_record_digest": row.provider_record_digest,
            "rights_basis": row.rights_basis,
            "entitlement_id": row.entitlement_id,
            "applicability_id": row.applicability_id,
            "applicability_statement": row.applicability_statement,
            "property_identity": row.table.identity.model_dump(mode="json"),
            "property_identity_digest": canonical_digest(row.table.identity.model_dump(mode="json")),
            "property_unit": row.table.temperature_table.y_unit,
            "temperature_unit": row.table.temperature_table.x_unit,
            "temperature_support_K": [
                row.table.temperature_table.x[0],
                row.table.temperature_table.x[-1],
            ],
            "interpolation": row.table.temperature_table.interpolation,
            "evidence": row.table.evidence.model_dump(mode="json"),
            "table_record_digest": row.deterministic_digest,
        }
        for row in x.tables
    ]
    common = {
        "audit_id": x.audit_id,
        "provider_set_id": x.provider_set_id,
        "provider_set_revision": x.provider_set_revision,
        "table_audit_rows": table_audit_rows,
        "missing_reviews": missing_reviews,
        "extrapolation_performed": False,
        "embedded_standard_table_used": False,
        "allowable_stress_generated": False,
        "automatic_acceptance_performed": False,
        "input_digest": canonical_digest(x.model_dump(mode="json")),
    }
    if missing_reviews:
        body = {**common, "query_result_rows": [], "audit_outcome": "insufficient_review"}
        body["report_digest"] = canonical_digest(body)
        return Calculation(
            status="needs_data",
            values=body,
            notes=("All caller review gates are required before property queries are resolved.",),
        )

    provider = TabulatedPropertyProvider([row.table for row in x.tables])
    by_identity = {canonical_digest(row.table.identity.model_dump(mode="json")): row for row in x.tables}
    query_rows = []
    for query_record in x.queries:
        identity_digest = canonical_digest(query_record.query.identity.model_dump(mode="json"))
        table_record = by_identity.get(identity_digest)
        if table_record is None:
            answer = provider.resolve(query_record.query)
        elif table_record.applicability_id != query_record.applicability_id:
            answer = {
                "status": "out_of_scope",
                "value": None,
                "unit": query_record.query.requested_unit,
                "reason": "Query applicability does not exactly match the supplied table applicability.",
            }
        else:
            answer = provider.resolve(query_record.query)

        row = {
            "query_id": query_record.query_id,
            "query_source_id": query_record.query_source_id,
            "query_record_digest": query_record.query_record_digest,
            "applicability_id": query_record.applicability_id,
            "query": query_record.query.model_dump(mode="json"),
            "query_identity_digest": identity_digest,
            "status": answer["status"],
            "value": answer.get("value"),
            "unit": answer["unit"],
            "reason": answer.get("reason"),
            "table_id": table_record.table_id if table_record else None,
            "provider_id": table_record.provider_id if table_record else None,
            "provider_revision": table_record.provider_revision if table_record else None,
            "provider_record_digest": (table_record.provider_record_digest if table_record else None),
            "table_record_digest": (table_record.deterministic_digest if table_record else None),
            "resolved_table_digest": answer.get("table_digest"),
            "lower_level_query_digest": answer.get("query_digest"),
            "temperature_support_K": (
                [
                    table_record.table.temperature_table.x[0],
                    table_record.table.temperature_table.x[-1],
                ]
                if table_record
                else None
            ),
            "interpolation": (table_record.table.temperature_table.interpolation if table_record else None),
        }
        row["result_digest"] = canonical_digest(row)
        query_rows.append(row)

    counts = {
        status: sum(row["status"] == status for row in query_rows)
        for status in ("computed", "needs_data", "out_of_scope")
    }
    status = (
        "needs_data" if counts["needs_data"] else "out_of_scope" if counts["out_of_scope"] else "computed"
    )
    body = {
        **common,
        "query_result_rows": query_rows,
        "query_status_counts": counts,
        "audit_outcome": "queries_resolved" if status == "computed" else status,
    }
    body["report_digest"] = canonical_digest(body)
    return Calculation(
        status=status,
        values=body,
        notes=(
            "Values are composed from the existing exact-identity table provider and remain caller-supplied property data.",
            "Interpolation is limited to the declared support; no standard table, allowable stress, extrapolation or acceptance rule is generated.",
        ),
    )


def specifications():
    return [
        ModelSpec(
            "materials.allowable_property_provider",
            AllowablePropertyProviderAudit,
            allowable_property_provider_audit,
            {
                "audit_id": "1",
                "provider_set_id": "1",
                "provider_set_revision": "1",
                "table_audit_rows": "mixed",
                "query_result_rows": "mixed",
                "query_status_counts": "count",
                "audit_outcome": "1",
                "missing_reviews": "1",
                "extrapolation_performed": "1",
                "embedded_standard_table_used": "1",
                "allowable_stress_generated": "1",
                "automatic_acceptance_performed": "1",
                "input_digest": "1",
                "report_digest": "1",
            },
            (
                "Property identity, edition, applicability and provider lineage are exact caller declarations.",
                "The supplied table is licensed or caller-owned and its declared temperature support has been reviewed.",
                "Results are property lookups only and establish no design acceptance or material qualification.",
            ),
            ("authored_allowable_property_provider_profile_audit",),
            version="1.0.1",
        )
    ]
