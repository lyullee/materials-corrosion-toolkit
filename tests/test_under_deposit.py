import pytest

from matintegrity.contracts import RunContext
from matintegrity.local_environment_history import (
    LocalEnvironmentExposureState,
    LocalEnvironmentFact,
    LocalEnvironmentHistoryCriterion,
    local_environment_history_assessment,
)
from matintegrity.models.under_deposit import (
    UnderDepositExposureHistory,
    UnderDepositLocalEnvironmentInput,
    specifications,
    under_deposit_exposure_history,
    under_deposit_local_environment_review,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored deposit test"}


def payload(**updates):
    value = {
        "assessment_id": "deposit-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "clock_id": "exposure-clock",
        "material_condition_id": "material-1",
        "environment_id": "environment-1",
        "assessed_surface_area_m2": 10.0,
        "intervals": (
            {
                "interval_id": "i1",
                "start_time_s": 0.0,
                "end_time_s": 100.0,
                "temperature_K": 320.0,
                "deposit_coverage_fraction": 0.2,
                "stagnation_descriptor": "stagnant",
                "differential_aeration_descriptor": "differential-a",
                "calibrated_local_loss_rate_m_s": 1e-9,
                "rate_provider_id": "provider-1",
                "rate_provider_state_digest": "1" * 64,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
            {
                "interval_id": "i2",
                "start_time_s": 100.0,
                "end_time_s": 300.0,
                "temperature_K": 330.0,
                "deposit_coverage_fraction": 0.5,
                "stagnation_descriptor": "stagnant",
                "differential_aeration_descriptor": "differential-a",
                "calibrated_local_loss_rate_m_s": 2e-9,
                "rate_provider_id": "provider-1",
                "rate_provider_state_digest": "2" * 64,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "rate_support": {
            "support_id": "support-1",
            "material_condition_id": "material-1",
            "environment_id": "environment-1",
            "rate_provider_id": "provider-1",
            "minimum_temperature_K": 300.0,
            "maximum_temperature_K": 350.0,
            "minimum_deposit_coverage_fraction": 0.0,
            "maximum_deposit_coverage_fraction": 0.8,
            "supported_stagnation_descriptors": ("stagnant",),
            "supported_differential_aeration_descriptors": ("differential-a",),
            "support_basis": "caller calibration",
            "evidence": (EVIDENCE,),
        },
        "material_and_environment_reviewed": True,
        "clock_and_interval_completeness_reviewed": True,
        "deposit_coverage_reviewed": True,
        "stagnation_and_aeration_mapping_reviewed": True,
        "calibrated_rate_provider_reviewed": True,
    }
    value.update(updates)
    return UnderDepositExposureHistory(**value)


def test_rate_and_area_time_integrals_are_exact():
    result = under_deposit_exposure_history(payload())
    assert result.status == "computed"
    assert result.values["cumulative_calibrated_local_loss_m"] == pytest.approx(5e-7)
    assert result.values["deposit_covered_area_time_m2_s"] == pytest.approx(1200.0)


def test_invalid_provider_or_review_needs_data():
    row = payload().intervals[0].model_copy(update={"rate_provider_id": "other"})
    assert (
        under_deposit_exposure_history(payload(intervals=(row, payload().intervals[1]))).status
        == "needs_data"
    )
    assert under_deposit_exposure_history(payload(deposit_coverage_reviewed=False)).status == "needs_data"


def test_state_outside_support_is_out_of_scope():
    row = payload().intervals[0].model_copy(update={"temperature_K": 400.0})
    result = under_deposit_exposure_history(payload(intervals=(row, payload().intervals[1])))
    assert result.status == "out_of_scope"


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[1])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.under_deposit_calibrated_loss",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )


def environment_history(domain="under_deposit", status="reported"):
    fact = LocalEnvironmentFact(
        fact_id="deposit-pH",
        fact_kind="pH",
        quantity_id="deposit_pH",
        status=status,
        value=6.5 if status == "reported" else None,
        expanded_uncertainty=0.2 if status == "reported" else None,
        unit_token="pH",
        method_id="synthetic-meter",
        fact_record_digest="a" * 64,
        invalid_or_missing_basis=None if status == "reported" else "not collected",
        evidence=(EVIDENCE,),
    )
    state = LocalEnvironmentExposureState(
        state_id="state-1",
        start_time_s=0.0,
        end_time_s=3600.0,
        material_condition_id="material-1",
        environment_id="environment-1",
        state_descriptors={"deposit": "observed"},
        facts=(fact,),
        state_record_digest="b" * 64,
        evidence=(EVIDENCE,),
    )
    criterion = LocalEnvironmentHistoryCriterion(
        criterion_id="pH-range",
        applicable_domain=domain,
        fact_kind="pH",
        quantity_id="deposit_pH",
        unit_token="pH",
        minimum_acceptable=6.0,
        maximum_acceptable=7.0,
        criterion_basis="synthetic caller rule",
        criterion_source_digest="c" * 64,
        evidence=(EVIDENCE,),
    )
    return local_environment_history_assessment(
        assessment_id="environment-history-1",
        domain=domain,
        asset_id="asset-1",
        location_id="location-1",
        physical_scope_id="surface-1",
        clock_id="clock-1",
        states=(state,),
        criteria=(criterion,),
        clock_state_and_identity_reviewed=True,
        units_references_methods_and_uncertainties_reviewed=True,
        caller_rules_and_missing_evidence_policy_reviewed=True,
        evidence=(EVIDENCE,),
    )


def test_local_environment_adapter_preserves_caller_rule_and_never_infers_rate():
    result = under_deposit_local_environment_review(
        UnderDepositLocalEnvironmentInput(history=environment_history())
    )
    assert result.status == "computed"
    assert result.values["decision"] == "accept"
    assert result.values["complete_evidence_fraction"] == 1.0
    assert result.values["calibrated_loss_integrated"] is False
    assert result.values["corrosion_rate_inferred"] is False


def test_local_environment_adapter_keeps_missing_and_wrong_domain_explicit():
    missing = under_deposit_local_environment_review(
        UnderDepositLocalEnvironmentInput(history=environment_history(status="missing"))
    )
    wrong_domain = under_deposit_local_environment_review(
        UnderDepositLocalEnvironmentInput(history=environment_history(domain="crevice_chemistry"))
    )
    assert missing.status == "needs_data"
    assert missing.values["decision"] == "insufficient_evidence"
    assert wrong_domain.status == "needs_data"
    assert wrong_domain.values["provided_domain"] == "crevice_chemistry"
