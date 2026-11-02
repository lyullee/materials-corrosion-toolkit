import pytest
from pydantic import ValidationError

from matintegrity.contracts import Evidence
from matintegrity.data import TabulatedProperty
from matintegrity.models.allowable_property_provider import (
    AllowablePropertyProviderAudit,
    AllowablePropertyQueryRecord,
    AllowablePropertyTableRecord,
    allowable_property_provider_audit,
    specifications,
)
from matintegrity.providers import DesignPropertyTable, PropertyIdentity, PropertyQuery

D = "a" * 64
E = Evidence(
    source_id="caller-table-source",
    origin="user_declared",
    citation="Caller-controlled property table record",
    license_id="caller-entitlement-1",
    sha256=D,
)


def identity(**updates):
    values = {
        "material_id": "material-A",
        "product_form": "plate",
        "material_condition": "normalized",
        "orientation": "longitudinal",
        "property_id": "caller_property",
        "basis_id": "caller-basis",
        "basis_edition": "2026-A",
    }
    values.update(updates)
    return PropertyIdentity(**values)


def table_record(**updates):
    ident = updates.pop("identity", identity())
    curve = TabulatedProperty(
        property_id=ident.property_id,
        x=[100.0, 300.0],
        y=[200.0, 100.0],
        x_unit="K",
        y_unit="MPa",
        source_id=E.source_id,
        interpolation="linear",
    )
    values = {
        "table_id": "table-1",
        "provider_id": "caller-provider",
        "provider_revision": "rev-1",
        "provider_record_digest": D,
        "rights_basis": "caller_licensed",
        "entitlement_id": "caller-entitlement-1",
        "applicability_id": "scope-1",
        "applicability_statement": "Caller-reviewed plate property scope.",
        "table": DesignPropertyTable(
            identity=ident,
            temperature_table=curve,
            evidence=E,
            permitted_use_note="Use under the caller-controlled entitlement only.",
        ),
    }
    values.update(updates)
    return AllowablePropertyTableRecord(**values)


def query_record(*, temperature=200.0, applicability_id="scope-1", ident=None):
    return AllowablePropertyQueryRecord(
        query_id="query-1",
        applicability_id=applicability_id,
        query=PropertyQuery(
            identity=ident or identity(),
            temperature_K=temperature,
            requested_unit="Pa",
        ),
        query_source_id="caller-query-source",
        query_record_digest="b" * 64,
        evidence=(E,),
    )


def audit(*, tables=None, queries=None, **updates):
    values = {
        "audit_id": "audit-1",
        "provider_set_id": "provider-set-1",
        "provider_set_revision": "1",
        "tables": tables or (table_record(),),
        "queries": queries or (query_record(),),
        "material_product_condition_orientation_and_edition_reviewed": True,
        "provider_revision_rights_and_provenance_reviewed": True,
        "applicability_units_and_temperature_support_reviewed": True,
        "query_identity_units_and_digests_reviewed": True,
        "evidence": (E,),
    }
    values.update(updates)
    return AllowablePropertyProviderAudit(**values)


def test_exact_in_support_query_composes_existing_provider_and_provenance():
    result = allowable_property_provider_audit(audit())
    row = result.values["query_result_rows"][0]
    assert result.status == "computed"
    assert row["value"] == pytest.approx(150e6)
    assert row["unit"] == "Pa"
    assert row["provider_revision"] == "rev-1"
    assert row["temperature_support_K"] == [100.0, 300.0]
    assert len(row["resolved_table_digest"]) == 64
    assert len(row["result_digest"]) == 64
    assert result.values["extrapolation_performed"] is False
    assert result.values["allowable_stress_generated"] is False
    assert result.values["automatic_acceptance_performed"] is False


def test_support_applicability_and_exact_edition_are_not_inferred():
    outside = allowable_property_provider_audit(audit(queries=(query_record(temperature=400.0),)))
    wrong_scope = allowable_property_provider_audit(
        audit(queries=(query_record(applicability_id="scope-other"),))
    )
    wrong_edition = allowable_property_provider_audit(
        audit(queries=(query_record(ident=identity(basis_edition="2025")),))
    )
    assert outside.status == "out_of_scope"
    assert outside.values["query_result_rows"][0]["value"] is None
    assert wrong_scope.status == "out_of_scope"
    assert wrong_edition.status == "needs_data"
    assert wrong_edition.values["query_result_rows"][0]["table_id"] is None


def test_review_gates_and_duplicate_exact_identity_are_strict():
    unreviewed = allowable_property_provider_audit(
        audit(provider_revision_rights_and_provenance_reviewed=False)
    )
    assert unreviewed.status == "needs_data"
    assert unreviewed.values["query_result_rows"] == []
    with pytest.raises(ValidationError, match="duplicate exact property identity"):
        audit(tables=(table_record(), table_record(table_id="table-2")))


def test_model_specification_is_local_and_has_independent_source_id():
    spec = specifications()[0]
    assert spec.model_id == "materials.allowable_property_provider"
    assert spec.input_type is AllowablePropertyProviderAudit
    assert spec.source_ids == ("authored_allowable_property_provider_profile_audit",)


def test_one_unsupported_query_prevents_a_computed_batch():
    outside = query_record(temperature=400).model_copy(update={"query_id": "outside"})
    result = allowable_property_provider_audit(audit(queries=(query_record(), outside)))
    assert result.status == "out_of_scope"
    assert result.values["query_status_counts"] == {"computed": 1, "needs_data": 0, "out_of_scope": 1}
    assert result.values["audit_outcome"] != "queries_resolved"
    assert result.values["query_result_rows"][0]["value"] == 150e6
    assert result.values["query_result_rows"][1]["value"] is None


def test_missing_identity_in_mixed_batch_stays_missing():
    missing = query_record(ident=identity(basis_edition="other")).model_copy(update={"query_id": "missing"})
    result = allowable_property_provider_audit(audit(queries=(query_record(), missing)))
    assert result.status == "needs_data"


@pytest.mark.parametrize(
    "unit,values,requested,status,expected",
    [
        ("Pa", [1e-320, 1e-320], "TPa", "out_of_scope", None),
        ("K", [273.15, 273.15], "degC", "computed", 0),
    ],
)
def test_unit_range_loss_is_distinct_from_legitimate_affine_zero(unit, values, requested, status, expected):
    record = table_record()
    curve = record.table.temperature_table.model_copy(update={"y": values, "y_unit": unit})
    source = record.model_copy(update={"table": record.table.model_copy(update={"temperature_table": curve})})
    q = query_record()
    q = q.model_copy(update={"query": q.query.model_copy(update={"requested_unit": requested})})
    result = allowable_property_provider_audit(audit(tables=(source,), queries=(q,)))
    assert result.status == status
    assert result.values["query_result_rows"][0]["value"] == expected


def test_registered_mixed_batch_status_and_version_exchange():
    from matintegrity.contracts import RunContext
    from matintegrity.registry import default_registry

    registry = default_registry()
    outside = query_record(temperature=400).model_copy(update={"query_id": "outside"})
    x = audit(queries=(query_record(), outside))
    context = RunContext(asset_id="authored", location_id="sample", time_basis="synthetic")
    model = "materials.allowable_property_provider"
    direct = registry.run(model, x, context)
    encoded = registry.run_json(model, x.model_dump_json(), context)
    assert direct.model_dump() == encoded.model_dump()
    assert direct.model_version == "1.0.1"
    assert direct.status == "out_of_scope"
