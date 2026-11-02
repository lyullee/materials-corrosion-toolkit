import pytest
from pydantic import ValidationError

from matintegrity.local_environment_history import (
    ElectrodeMaterialCouple,
    LocalEnvironmentExposureState,
    LocalEnvironmentFact,
    LocalEnvironmentHistoryCriterion,
    assess_local_environment_history,
    local_environment_history_assessment,
)

E = {"source_id": "campaign", "origin": "measured", "citation": "caller campaign record"}
D = "e" * 64


def fact(value=0.1, status="reported", reference="ref-1"):
    return LocalEnvironmentFact(
        fact_id="potential-a",
        fact_kind="potential",
        quantity_id="electrode_a_potential",
        status=status,
        value=value if status == "reported" else None,
        expanded_uncertainty=0.01 if status == "reported" else None,
        unit_token="V",
        reference_electrode_id=reference,
        method_id="meter-1",
        fact_record_digest=D,
        invalid_or_missing_basis=None if status == "reported" else "not recorded",
        evidence=(E,),
    )


def couple():
    return ElectrodeMaterialCouple(
        couple_id="couple-1",
        electrode_a_material_id="alloy-a",
        electrode_a_surface_condition_id="surface-a",
        electrode_a_exposed_area_m2=1.0,
        electrode_b_material_id="alloy-b",
        electrode_b_surface_condition_id="surface-b",
        electrode_b_exposed_area_m2=2.0,
        electrical_connection_definition="caller confirmed conductive connection",
        geometry_record_digest=D,
        evidence=(E,),
    )


def state(observation=None):
    return LocalEnvironmentExposureState(
        state_id="state-1",
        start_time_s=0.0,
        end_time_s=10.0,
        material_condition_id="condition-1",
        environment_id="environment-1",
        couple_id="couple-1",
        state_descriptors={"deposit": "reported absent"},
        facts=(observation or fact(),),
        state_record_digest=D,
        evidence=(E,),
    )


def criterion(maximum=0.2):
    return LocalEnvironmentHistoryCriterion(
        criterion_id="potential-rule",
        applicable_domain="galvanic_coupling",
        fact_kind="potential",
        quantity_id="electrode_a_potential",
        unit_token="V",
        reference_electrode_id="ref-1",
        maximum_acceptable=maximum,
        criterion_basis="caller rule",
        criterion_source_digest=D,
        evidence=(E,),
    )


def assessment(**updates):
    value = {
        "assessment_id": "history-1",
        "domain": "galvanic_coupling",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "clock_id": "clock-1",
        "couples": (couple(),),
        "states": (state(),),
        "criteria": (criterion(),),
        "clock_state_and_identity_reviewed": True,
        "units_references_methods_and_uncertainties_reviewed": True,
        "caller_rules_and_missing_evidence_policy_reviewed": True,
        "evidence": (E,),
    }
    value.update(updates)
    return local_environment_history_assessment(**value)


def test_accept_reject_review_and_area_identity_are_caller_driven():
    accepted = assess_local_environment_history(assessment())
    rejected = assess_local_environment_history(assessment(criteria=(criterion(0.05),)))
    reviewed = assess_local_environment_history(assessment(criteria=(criterion(0.105),)))
    assert (accepted.decision, rejected.decision, reviewed.decision) == ("accept", "reject", "review")
    assert accepted.area_ratios_b_to_a == {"couple-1": 2.0}
    assert accepted.corrosion_rate_inferred is False
    assert accepted.failure_probability_inferred is False
    assert accepted == assess_local_environment_history(assessment())


def test_missing_fact_or_reference_mismatch_is_insufficient_evidence():
    missing = assess_local_environment_history(assessment(states=(state(fact(status="missing")),)))
    mismatch = assess_local_environment_history(assessment(states=(state(fact(reference="other")),)))
    assert missing.decision == mismatch.decision == "insufficient_evidence"
    assert missing.complete_evidence_fraction == 0.0


def test_history_and_report_digests_detect_tampering():
    item = assessment()
    changed = item.model_dump(mode="python")
    changed["clock_id"] = "other"
    with pytest.raises(ValidationError, match="payload digest mismatch"):
        item.model_validate(changed)
    report = assess_local_environment_history(item)
    changed_report = report.model_dump(mode="python")
    changed_report["decision"] = "review"
    with pytest.raises(ValidationError, match="report digest mismatch"):
        report.model_validate(changed_report)


def test_potential_requires_exact_reference_and_unit():
    with pytest.raises(ValidationError, match="reference-electrode"):
        LocalEnvironmentFact(
            fact_id="bad",
            fact_kind="potential",
            quantity_id="potential",
            status="reported",
            value=0.0,
            expanded_uncertainty=0.0,
            unit_token="mV",
            reference_electrode_id=None,
            method_id="meter",
            fact_record_digest=D,
            evidence=(E,),
        )


@pytest.mark.parametrize("domain", ["crevice_chemistry", "under_deposit"])
def test_local_environment_domains_accept_measured_ph_without_rate_inference(domain):
    ph = LocalEnvironmentFact(
        fact_id="ph-1",
        fact_kind="pH",
        quantity_id="local_ph",
        status="reported",
        value=6.0,
        expanded_uncertainty=0.1,
        unit_token="pH",
        method_id="probe-1",
        fact_record_digest=D,
        evidence=(E,),
    )
    local_state = state(ph).model_copy(update={"couple_id": None})
    rule = LocalEnvironmentHistoryCriterion(
        criterion_id="ph-rule",
        applicable_domain=domain,
        fact_kind="pH",
        quantity_id="local_ph",
        unit_token="pH",
        minimum_acceptable=5.0,
        criterion_basis="caller local-environment rule",
        criterion_source_digest=D,
        evidence=(E,),
    )
    item = assessment(domain=domain, couples=(), states=(local_state,), criteria=(rule,))
    result = assess_local_environment_history(item)
    assert result.decision == "accept"
    assert result.corrosion_rate_inferred is False
