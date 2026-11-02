import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.acid_dissolution import (
    AcidDissolutionHistory,
    AcidDissolutionRateInterval,
    AcidDissolutionRateSupport,
    acid_dissolution_history,
)

EVIDENCE = Evidence(source_id="authored", origin="synthetic", citation="authored test")


def support(**updates):
    payload = {
        "support_id": "support-1",
        "material_condition_id": "alloy-A",
        "acid_species_id": "acid-A",
        "concentration_min": 1.0,
        "concentration_max": 10.0,
        "concentration_unit_token": "mass_percent",
        "concentration_basis": "caller analytical definition",
        "temperature_min_K": 290.0,
        "temperature_max_K": 350.0,
        "applicable_flow_mass_transfer_descriptors": ["stirred-A"],
        "rate_provider_id": "provider-A",
        "rate_provider_version": "1",
        "rate_provider_digest": "a" * 64,
        "calibration_basis": "caller calibration records",
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return AcidDissolutionRateSupport(**payload)


def interval(identifier, rate, temperature=320.0, valid=True):
    return AcidDissolutionRateInterval(
        interval_id=identifier,
        support_id="support-1",
        concentration=5.0,
        temperature_K=temperature,
        flow_mass_transfer_descriptor="stirred-A",
        dissolution_rate_m_s=rate,
        rate_record_digest=(identifier[0] * 64),
        rate_valid=valid,
        missing_or_invalid_basis=None if valid else "provider invalid flag",
        evidence=[EVIDENCE],
    )


def request(**updates):
    payload = {
        "history_id": "acid-history-1",
        "asset_id": "asset-1",
        "location_id": "coupon-1",
        "clock_id": "elapsed-clock-1",
        "material_condition_id": "alloy-A",
        "acid_species_id": "acid-A",
        "concentration_unit_token": "mass_percent",
        "concentration_basis": "caller analytical definition",
        "elapsed_time_s": [0.0, 100.0, 300.0],
        "rate_intervals": [interval("a-interval", 1e-8), interval("b-interval", 2e-8)],
        "rate_supports": [support()],
        "material_and_acid_identity_reviewed": True,
        "concentration_definition_reviewed": True,
        "temperature_history_reviewed": True,
        "flow_mass_transfer_history_reviewed": True,
        "rate_provider_and_calibration_reviewed": True,
        "clock_and_interval_alignment_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return AcidDissolutionHistory(**payload)


def test_external_interval_rates_integrate_exactly():
    result = acid_dissolution_history(request())
    assert result.status == "computed"
    assert result.values["interval_metal_loss_m"] == pytest.approx([1e-6, 4e-6])
    assert result.values["cumulative_metal_loss_m"] == pytest.approx([0.0, 1e-6, 5e-6])


def test_reviewed_condition_outside_support_is_out_of_scope_without_loss():
    result = acid_dissolution_history(
        request(rate_intervals=[interval("a-interval", 1e-8), interval("b-interval", 2e-8, 360.0)])
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_support_interval_ids"] == ["b-interval"]
    assert "total_metal_loss_m" not in result.values


def test_identity_mismatch_invalid_rate_or_missing_review_needs_data():
    mismatch = acid_dissolution_history(request(concentration_unit_token="volume_percent"))
    assert mismatch.status == "needs_data"
    bad = interval("b-interval", 2e-8, valid=False)
    invalid = acid_dissolution_history(request(rate_intervals=[interval("a-interval", 1e-8), bad]))
    assert invalid.status == "needs_data"
    unreviewed = acid_dissolution_history(request(rate_provider_and_calibration_reviewed=False))
    assert unreviewed.status == "needs_data"


def test_alignment_and_provider_digest_are_strict():
    with pytest.raises(ValueError, match="one caller-provided"):
        request(rate_intervals=[interval("a-interval", 1e-8)])
    with pytest.raises(ValueError, match="[Ss]tring should match pattern"):
        support(rate_provider_digest="not-a-digest")
