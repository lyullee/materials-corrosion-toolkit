import pytest

from matintegrity.contracts import canonical_digest
from matintegrity.exchange_receipt import (
    ExchangeCompatibilityReceipt,
    build_exchange_compatibility_receipt,
)

CONFIGURATION_DIGEST = "c" * 64


def endpoint(repository, schema, commit):
    return {
        "repository_id": repository,
        "schema_id": schema,
        "schema_version": "1.2.0",
        "provider_id": f"{repository}-provider",
        "provider_commit": commit,
        "provider_revision": "release-1",
    }


def accepted_checks():
    return (
        {
            "check_id": "schema-check",
            "category": "schema",
            "status": "passed",
            "paths": ("/asset/id",),
            "expected_descriptor": "consumer asset identifier string",
            "observed_descriptor": "producer asset identifier string",
            "basis": "reviewed schema mapping",
        },
        {
            "check_id": "unit-check",
            "category": "unit",
            "status": "passed",
            "paths": ("/temperature/unit",),
            "expected_descriptor": "K",
            "observed_descriptor": "K",
            "basis": "exact unit token match",
        },
        {
            "check_id": "identity-check",
            "category": "identity",
            "status": "passed",
            "paths": ("/asset/id",),
            "expected_descriptor": "asset-A",
            "observed_descriptor": "asset-A",
            "basis": "exact identity match",
        },
        {
            "check_id": "probability-check",
            "category": "probability_semantics",
            "status": "passed",
            "paths": ("/probability/semantics",),
            "expected_descriptor": "conditional_first_failure_in_period",
            "observed_descriptor": "conditional_first_failure_in_period",
            "basis": "exact probability-semantics token match",
        },
    )


def accepted_decisions():
    return (
        {
            "path": "/asset/id",
            "status": "accepted",
            "check_categories": ("schema", "identity"),
            "basis": "schema and identity checks passed",
        },
        {
            "path": "/temperature/unit",
            "status": "accepted",
            "check_categories": ("unit",),
            "basis": "unit check passed",
        },
        {
            "path": "/probability/semantics",
            "status": "accepted",
            "check_categories": ("probability_semantics",),
            "basis": "probability semantics check passed",
        },
    )


def payload():
    return {
        "asset": {"id": "asset-A"},
        "temperature": {"value": 300.0, "unit": "K"},
        "probability": {
            "value": 0.1,
            "semantics": "conditional_first_failure_in_period",
        },
    }


def build(**updates):
    arguments = {
        "producer": endpoint("producer-repo", "producer.temperature", "a" * 40),
        "consumer": endpoint("consumer-repo", "consumer.temperature", "b" * 40),
        "payload": payload(),
        "configuration_digest": CONFIGURATION_DIGEST,
        "checks": accepted_checks(),
        "field_decisions": accepted_decisions(),
        "compatibility_scope": "reviewed JSON field mapping only",
        "limitations": (
            "This receipt is not a digital signature or network delivery acknowledgement.",
            "Schema checks do not establish physical-model validity.",
        ),
    }
    arguments.update(updates)
    return build_exchange_compatibility_receipt(**arguments)


def test_builder_is_canonical_and_deterministic_across_mapping_order():
    first = build()
    reordered = {
        "probability": {
            "semantics": "conditional_first_failure_in_period",
            "value": 0.1,
        },
        "temperature": {"unit": "K", "value": 300.0},
        "asset": {"id": "asset-A"},
    }
    second = build(payload=reordered)
    assert first == second
    assert first.payload_canonical_sha256 == canonical_digest(payload())
    assert first.status == "accepted"
    assert first.accepted_paths == (
        "/asset/id",
        "/probability/semantics",
        "/temperature/unit",
    )
    assert first.rejected_paths == ()
    assert first.signature_verified is False
    assert first.network_transfer_executed is False
    assert first.physical_validation_claimed is False


def test_failed_probability_semantics_derives_rejection_and_path():
    checks = list(accepted_checks())
    checks[-1] = {
        **checks[-1],
        "status": "failed",
        "observed_descriptor": "point_in_time_state_probability",
        "basis": "probability semantics differ",
    }
    decisions = list(accepted_decisions())
    decisions[-1] = {
        **decisions[-1],
        "status": "rejected",
        "basis": "probability semantics are not interchangeable",
    }
    receipt = build(checks=tuple(checks), field_decisions=tuple(decisions))
    assert receipt.status == "rejected"
    assert receipt.rejected_paths == ("/probability/semantics",)
    assert receipt.checks[-1].category == "probability_semantics"
    assert receipt.checks[-1].status == "failed"


def test_status_path_summaries_identifier_and_digest_are_self_bound():
    receipt = build()
    data = receipt.model_dump()
    data["status"] = "rejected"
    with pytest.raises(ValueError, match="status must be derived"):
        ExchangeCompatibilityReceipt.model_validate(data)

    data = receipt.model_dump()
    data["accepted_paths"] = ()
    with pytest.raises(ValueError, match="path summaries must match"):
        ExchangeCompatibilityReceipt.model_validate(data)

    data = receipt.model_dump()
    data["receipt_digest"] = "0" * 64
    with pytest.raises(ValueError, match="digest does not match"):
        ExchangeCompatibilityReceipt.model_validate(data)


def test_builder_rejects_unresolved_or_invalid_payload_paths_and_nonfinite_json():
    decisions = list(accepted_decisions())
    decisions[0] = {**decisions[0], "path": "/asset/missing"}
    with pytest.raises(ValueError, match="does not resolve"):
        build(field_decisions=tuple(decisions))

    checks = list(accepted_checks())
    checks[0] = {**checks[0], "paths": ("$.asset.id",)}
    with pytest.raises(ValueError, match="RFC 6901"):
        build(checks=tuple(checks))

    bad_payload = payload()
    bad_payload["temperature"]["value"] = float("nan")
    with pytest.raises(ValueError, match="non-finite"):
        build(payload=bad_payload)


def test_exact_check_categories_and_failed_path_consistency_are_strict():
    with pytest.raises(ValueError, match="exactly schema, unit, identity"):
        build(checks=accepted_checks()[:-1])

    checks = list(accepted_checks())
    checks[1] = {
        **checks[1],
        "status": "failed",
        "observed_descriptor": "degC",
        "basis": "unit mismatch",
    }
    with pytest.raises(ValueError, match="accepted field decisions cannot correspond to failed checks"):
        build(checks=tuple(checks))
