import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.classification_assignment import (
    ClassificationContext,
    ClassificationQuery,
    ClassificationWPSBinding,
    DeclaredClassificationAssignment,
    DeclaredClassificationRecord,
    classification_to_wps_variable,
    declared_classification_assignment,
)
from matintegrity.registry import default_registry
from matintegrity.specification_aliases import SpecificationDesignation


def designation(**updates):
    return SpecificationDesignation(
        **(
            dict(
                namespace="authored-material",
                designation="alloy-X",
                edition="material-edition",
                product_form="plate",
                condition="condition",
            )
            | updates
        )
    )


def context(**updates):
    return ClassificationContext(
        **(
            dict(
                code_namespace="authored-code",
                code_edition="edition-1",
                classification_scheme_id="authored-scheme",
                process_id="authored-process",
                subject_kind="base_material",
                qualification_purpose_id="authored-purpose",
            )
            | updates
        )
    )


def record(**updates):
    raw = dict(
        record_id="record",
        designation=designation(),
        context=context(),
        assignment_status="assigned",
        assignment_token="X7B",
        unknown_basis=None,
        assignment_basis="Authored assignment",
        authority_id="authored-authority",
        revision="1",
        source_record_sha256="a" * 64,
        authority_and_assignment_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        DeclaredClassificationRecord.model_construct(**raw).model_dump(
            mode="json", exclude={"assignment_sha256", "evidence"}
        )
    )
    return DeclaredClassificationRecord(
        **raw,
        assignment_sha256=digest,
        evidence=(
            dict(
                source_id="authored",
                origin="synthetic",
                citation="Authored assignment",
                license_id="authored-test",
                sha256=digest,
            ),
        ),
    )


def query(**updates):
    return ClassificationQuery(
        **(
            dict(
                query_id="query",
                physical_item_id="physical-item",
                designation=designation(),
                context=context(),
            )
            | updates
        )
    )


def request(**updates):
    raw = dict(
        lookup_id="lookup",
        queries=(query(),),
        records=(record(),),
        item_designations_and_conditions_reviewed=True,
        classification_authority_and_scope_reviewed=True,
    )
    raw.update(updates)
    digest = canonical_digest(
        DeclaredClassificationAssignment.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return DeclaredClassificationAssignment(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored query set",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_exact_assignment_preserves_token_and_authority():
    result = declared_classification_assignment(request())
    row = result.values["assignment_findings"][0]
    assert row["assignment_token"] == "X7B"
    assert row["selected_evidence"]["authority_id"] == "authored-authority"
    assert not result.values["material_equivalence_established"]


@pytest.mark.parametrize(
    "updates",
    [
        dict(code_edition="other"),
        dict(process_id="other"),
        dict(qualification_purpose_id="other"),
        dict(subject_kind="weld_deposit"),
        dict(classification_scheme_id="other"),
    ],
)
def test_no_context_transfer(updates):
    result = declared_classification_assignment(request(queries=(query(context=context(**updates)),)))
    assert result.status == "needs_data"
    assert result.values["assignment_findings"][0]["assignment_status"] == "unknown"


@pytest.mark.parametrize(
    "updates", [dict(edition="other"), dict(product_form="bar"), dict(condition="other")]
)
def test_no_product_or_condition_equivalence(updates):
    result = declared_classification_assignment(request(queries=(query(designation=designation(**updates)),)))
    assert result.status == "needs_data"


@pytest.mark.parametrize("state,status", [("unassigned", "computed"), ("unknown", "needs_data")])
def test_explicit_unassigned_is_distinct_from_missing(state, status):
    item = record(
        assignment_status=state,
        assignment_token=None,
        unknown_basis="not established" if state == "unknown" else None,
    )
    result = declared_classification_assignment(request(records=(item,)))
    assert result.status == status
    assert result.values["assignment_findings"][0]["assignment_status"] == state


def test_even_identical_tokens_from_multiple_records_stay_ambiguous():
    result = declared_classification_assignment(request(records=(record(), record(record_id="other"))))
    assert result.values["assignment_findings"][0]["assignment_status"] == "ambiguous"
    assert result.values["assignment_findings"][0]["assignment_token"] is None


@pytest.mark.parametrize(
    "updates",
    [
        dict(classification_authority_and_scope_reviewed=False),
        dict(records=(record(authority_and_assignment_reviewed=False),)),
    ],
)
def test_missing_authority_review_withholds_token(updates):
    result = declared_classification_assignment(request(**updates))
    assert result.status == "needs_data"
    assert result.values["assignment_findings"][0]["assignment_token"] is None


def test_assignment_tampering_breaks_evidence_binding():
    raw = record().model_dump()
    raw["assignment_token"] = "altered"
    with pytest.raises(ValueError, match="pin the exact"):
        DeclaredClassificationRecord(**raw)


def test_wps_binding_preserves_exact_categorical_token_and_input_evidence():
    x = request()
    bound = classification_to_wps_variable(
        x, "query", variable_id="caller-variable", production_record_id="production"
    )
    assert bound.physical_item_id == "physical-item"
    assert bound.query_id == "query"
    assert bound.lookup_input_sha256 == x.basis.record_sha256
    assert bound.production_variable.categorical_value_token == "X7B"
    assert bound.production_variable.variable_kind == "categorical"
    assert bound.production_variable.unit_token == "1"
    assert bound.production_variable.evidence == (*x.records[0].evidence, *x.basis.evidence)


def test_wps_binding_cannot_silently_change_physical_item():
    bound = classification_to_wps_variable(
        request(), "query", variable_id="variable", production_record_id="production"
    )
    raw = bound.model_dump()
    raw["physical_item_id"] = "another-item"
    with pytest.raises(ValueError, match="binding digest"):
        ClassificationWPSBinding(**raw)


@pytest.mark.parametrize("state", ["unassigned", "unknown"])
def test_unresolved_or_unassigned_cannot_become_valid_wps_variable(state):
    item = record(
        assignment_status=state,
        assignment_token=None,
        unknown_basis="not established" if state == "unknown" else None,
    )
    with pytest.raises(ValueError, match="requires one reviewed"):
        classification_to_wps_variable(
            request(records=(item,)), "query", variable_id="variable", production_record_id="production"
        )


def test_ambiguous_query_cannot_be_bound_to_wps():
    with pytest.raises(ValueError, match="requires one reviewed"):
        classification_to_wps_variable(
            request(records=(record(), record(record_id="other"))),
            "query",
            variable_id="variable",
            production_record_id="production",
        )


def test_same_physical_item_cannot_change_designation_in_same_context():
    with pytest.raises(ValueError, match="conflicting designations"):
        request(queries=(query(), query(query_id="second", designation=designation(condition="other"))))


def test_default_registry_python_json_exchange():
    registry = default_registry()
    x = request()
    model = "materials.declared_classification_assignment"
    run_context = RunContext(asset_id="asset", location_id="location", time_basis="synthetic")
    assert (
        registry.run(model, x, run_context).model_dump()
        == registry.run_json(model, x.model_dump_json(), run_context).model_dump()
    )
