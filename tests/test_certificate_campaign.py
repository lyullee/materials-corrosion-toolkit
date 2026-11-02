import pytest
from pydantic import ValidationError

from matintegrity.models.certificate_campaign import CertificateCampaign, certificate_campaign

S = "a" * 64
E = {"source_id": "caller", "origin": "user_declared", "citation": "caller evidence"}


def lower(maximum=0.003):
    return {
        "reconciliation_id": "lower-1",
        "asset_id": "asset",
        "location_id": "location",
        "physical_scope_id": "scope",
        "heat_id": "heat",
        "lot_id": "lot",
        "material_condition_id": "condition",
        "requirement_set_id": "requirements",
        "requirement_authority_digest": S,
        "requirements": (
            {
                "requirement_id": "carbon",
                "quantity_kind": "chemistry_mass_fraction",
                "quantity_id": "C",
                "unit_basis": "mass_fraction",
                "unit_token": "mass_fraction",
                "minimum_allowed_value": 0.001,
                "maximum_allowed_value": maximum,
                "comparison_policy": "reported_uncertainty_interval_against_requirement",
                "requirement_basis": "caller",
                "evidence": (E,),
            },
        ),
        "records": (
            {
                "record_id": "certificate",
                "record_role": "certificate",
                "heat_id": "heat",
                "lot_id": "lot",
                "reported_material_identity_id": "reported",
                "alias_resolution_status": "exact",
                "resolved_material_condition_id": "condition",
                "alias_resolution_basis": "exact",
                "physical_sample_id": "sample",
                "source_group_id": "source",
                "provider_id": "provider",
                "provider_revision": "1",
                "record_digest": S,
                "measurements": (
                    {
                        "measurement_id": "C",
                        "quantity_kind": "chemistry_mass_fraction",
                        "quantity_id": "C",
                        "unit_basis": "mass_fraction",
                        "unit_token": "mass_fraction",
                        "reported_value": 0.002,
                        "expanded_uncertainty": 0.0001,
                        "uncertainty_coverage_factor": 2.0,
                        "method_id": "method",
                        "result_digest": S,
                        "evidence": (E,),
                    },
                ),
                "record_valid": True,
                "evidence": (E,),
            },
        ),
        "heat_lot_and_material_condition_reviewed": True,
        "alias_resolution_status_and_mapping_reviewed": True,
        "requirement_authority_and_bounds_reviewed": True,
        "chemistry_mass_fraction_basis_reviewed": True,
        "property_si_units_reviewed": True,
        "physical_samples_and_source_groups_reviewed": True,
        "methods_uncertainties_and_coverage_factors_reviewed": True,
        "provider_lineage_and_result_digests_reviewed": True,
        "duplicate_contradiction_and_missingness_policy_reviewed": True,
        "evidence": (E,),
    }


def coverage(category, status="pass", record_id=None):
    return {
        "record_id": record_id or category,
        "document_id": "document",
        "heat_id": "heat",
        "product_id": "product",
        "traceability_id": "trace",
        "category": category,
        "status": status,
        "caller_criterion_id": f"criterion-{category}",
        "result_digest": S,
        "evidence": (E,),
    }


def campaign(required=("chemistry", "mechanical"), rows=None, **updates):
    data = {
        "assessment_id": "campaign",
        "asset_id": "asset",
        "location_id": "location",
        "purchase_requirement_set_id": "purchase",
        "expected_product_id": "product",
        "expected_traceability_id": "trace",
        "product_and_traceability_binding_reviewed": True,
        "lower_level": lower(),
        "coverage": tuple(rows or (coverage("chemistry"), coverage("mechanical"))),
        "required_categories": required,
        "caller_criteria_reviewed": True,
        "evidence": (E,),
    }
    data.update(updates)
    return CertificateCampaign.model_validate(data)


@pytest.mark.parametrize("field,wrong", [("product_id", "other-product"), ("traceability_id", "other-trace")])
def test_coverage_cannot_borrow_another_product_or_trace(field, wrong):
    mixed = coverage("mechanical") | {field: wrong}
    with pytest.raises(ValueError, match="product and traceability"):
        campaign(rows=(coverage("chemistry"), mixed))


def test_legacy_unbound_identity_requires_data():
    result = certificate_campaign(
        campaign(
            expected_product_id=None,
            expected_traceability_id=None,
            product_and_traceability_binding_reviewed=False,
        )
    )
    assert result.status == "needs_data"
    assert result.values["disposition"] == "insufficient_evidence"


def test_runtime_asset_identity_and_json_exchange():
    from matintegrity.contracts import RunContext
    from matintegrity.models.certificate_campaign import specifications
    from matintegrity.registry import ModelRegistry

    registry = ModelRegistry()
    registry.register(specifications()[0])
    context = RunContext(asset_id="asset", location_id="location", time_basis="test")
    inputs = campaign()
    direct = registry.run("materials.certificate_reconciliation", inputs, context)
    serialized = registry.run_json("materials.certificate_reconciliation", inputs.model_dump_json(), context)
    assert direct.model_dump() == serialized.model_dump()
    with pytest.raises(ValueError, match="run context"):
        registry.run(
            "materials.certificate_reconciliation",
            inputs,
            RunContext(asset_id="other", location_id="location", time_basis="test"),
        )


def test_pass_reject_and_missing_are_distinct_and_deterministic():
    passed = certificate_campaign(campaign())
    assert passed.values["disposition"] == "pass"
    assert passed == certificate_campaign(campaign())
    assert (
        certificate_campaign(campaign(rows=(coverage("chemistry", "fail"), coverage("mechanical")))).values[
            "disposition"
        ]
        == "reject"
    )
    missing = certificate_campaign(campaign(rows=(coverage("chemistry"),)))
    assert missing.values["disposition"] == "insufficient_evidence"
    assert missing.values["category_findings"]["mechanical"] == "missing"


def test_identity_mismatch_and_uniqueness_are_rejected():
    with pytest.raises(ValidationError, match="identity must match"):
        campaign(asset_id="other")
    with pytest.raises(ValidationError, match="record IDs"):
        campaign(rows=(coverage("chemistry", record_id="same"), coverage("mechanical", record_id="same")))
    with pytest.raises(ValidationError, match="categories must be unique"):
        campaign(required=("chemistry", "chemistry"))
