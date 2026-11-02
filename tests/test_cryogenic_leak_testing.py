import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.cryogenic_leak_testing import (
    CryogenicLeakTestAssessment,
    cryogenic_leak_test_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def payload(**updates):
    value = {
        "assessment_id": "cryo-1",
        "asset_id": "asset-1",
        "location_id": "valve-1",
        "test_article_id": "article-1",
        "test_medium_id": "medium-1",
        "pressure_basis": "absolute",
        "clock_id": "clock-1",
        "cycles": (
            {
                "cycle_id": "cycle-1",
                "start_time_s": 0.0,
                "end_time_s": 100.0,
                "minimum_temperature_K": 80.0,
                "maximum_temperature_K": 300.0,
                "minimum_pressure_Pa": 100000.0,
                "maximum_pressure_Pa": 200000.0,
                "temperature_provider_id": "temperature-logger",
                "pressure_provider_id": "pressure-logger",
                "acquisition_state_digest": DIGEST_A,
                "data_digest": DIGEST_B,
                "thermal_stabilization_basis": "caller-reviewed plateau",
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "leak_observations": (
            {
                "observation_id": "leak-1",
                "cycle_id": "cycle-1",
                "physical_location_id": "seat-1",
                "source_group_id": "run-1",
                "observation_role": "test",
                "method_id": "method-1",
                "metric_id": "leak-rate",
                "metric_definition": "caller calibrated leak-rate signal",
                "unit_token": "Pa*m^3/s",
                "reporting_status": "below_detection",
                "detection_limit": 1e-7,
                "provider_id": "detector-1",
                "provider_version": "1",
                "provider_state_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_envelopes": (
            {
                "envelope_id": "envelope-1",
                "test_medium_id": "medium-1",
                "pressure_basis": "absolute",
                "minimum_supported_temperature_K": 70.0,
                "maximum_supported_temperature_K": 310.0,
                "minimum_supported_pressure_Pa": 90000.0,
                "maximum_supported_pressure_Pa": 210000.0,
                "supported_method_ids": ("method-1",),
                "metric_id": "leak-rate",
                "metric_definition": "caller calibrated leak-rate signal",
                "unit_token": "Pa*m^3/s",
                "maximum_conservative_value": 2e-7,
                "minimum_valid_cycles": 1,
                "minimum_test_locations_per_cycle": 1,
                "envelope_provider_id": "caller-envelope",
                "envelope_provider_version": "1",
                "envelope_state_digest": DIGEST_A,
                "authority_basis": "caller test plan",
                "evidence": (EVIDENCE,),
            },
        ),
        "article_and_medium_identity_reviewed": True,
        "clock_and_cycle_alignment_reviewed": True,
        "temperature_and_pressure_basis_reviewed": True,
        "thermal_stabilization_reviewed": True,
        "leak_methods_and_locations_reviewed": True,
        "uncertainty_and_detection_limits_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return CryogenicLeakTestAssessment(**value)


def test_below_detection_uses_limit_not_zero():
    result = cryogenic_leak_test_evidence(payload())
    assert result.status == "computed"
    row = result.values["leak_observation_comparisons"][0]
    assert row["conservative_value"] == pytest.approx(1e-7)
    assert row["within_caller_declared_maximum"] is True


def test_outside_thermal_support_is_out_of_scope():
    assessment = payload()
    cycle = assessment.cycles[0].model_copy(update={"minimum_temperature_K": 60.0})
    result = cryogenic_leak_test_evidence(assessment.model_copy(update={"cycles": (cycle,)}))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_cycle_ids"] == ["cycle-1"]


def test_missing_observation_and_definition_mismatch_need_data():
    assessment = payload()
    missing = assessment.leak_observations[0].model_copy(
        update={
            "reporting_status": "missing",
            "detection_limit": None,
            "result_digest": None,
            "missing_basis": "detector record absent",
        }
    )
    assert (
        cryogenic_leak_test_evidence(assessment.model_copy(update={"leak_observations": (missing,)})).status
        == "needs_data"
    )
    mismatch = assessment.leak_observations[0].model_copy(update={"unit_token": "different"})
    assert (
        cryogenic_leak_test_evidence(assessment.model_copy(update={"leak_observations": (mismatch,)})).status
        == "needs_data"
    )


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "inspection.cryogenic_leak_test_evidence",
            payload(),
            RunContext(asset_id="other", location_id="valve-1", time_basis="authored"),
        )
