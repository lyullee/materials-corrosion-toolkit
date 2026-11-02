import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.welding_duplex_phase_balance import (
    DuplexPhaseBalanceAssessment,
    duplex_phase_balance,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def observation(observation_id, region_id, region_kind, phase_id, value):
    return {
        "observation_id": observation_id,
        "sample_id": f"sample-{region_id}",
        "region_id": region_id,
        "region_kind": region_kind,
        "phase_id": phase_id,
        "fraction_definition": "volume_fraction",
        "measured_fraction": value,
        "expanded_uncertainty_fraction": 0.02,
        "uncertainty_coverage_factor": 2.0,
        "method_id": "image-analysis",
        "method_provider_id": "caller-laboratory",
        "method_provider_version": "3",
        "method_state_digest": DIGEST_A,
        "record_state_digest": DIGEST_B,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def phase_range(range_id, region_id, region_kind, phase_id, lower, upper):
    return {
        "range_id": range_id,
        "region_id": region_id,
        "region_kind": region_kind,
        "phase_id": phase_id,
        "fraction_definition": "volume_fraction",
        "minimum_fraction": lower,
        "maximum_fraction": upper,
        "range_basis": "caller phase envelope",
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    observations = (
        observation("w-a", "wm", "weld_metal", "phase-a", 0.55),
        observation("w-b", "wm", "weld_metal", "phase-b", 0.45),
        observation("h-a", "haz", "heat_affected_zone", "phase-a", 0.52),
        observation("h-b", "haz", "heat_affected_zone", "phase-b", 0.48),
        observation("b-a", "base", "base_material", "phase-a", 0.50),
        observation("b-b", "base", "base_material", "phase-b", 0.50),
    )
    ranges = tuple(
        phase_range(
            f"range-{row['observation_id']}",
            row["region_id"],
            row["region_kind"],
            row["phase_id"],
            0.40,
            0.60,
        )
        for row in observations
    )
    envelope = {
        "envelope_id": "duplex-envelope-1",
        "material_condition_id": "duplex-condition-1",
        "welding_process_id": "process-1",
        "process_history_id": "process-history-1",
        "heat_history_id": "heat-history-1",
        "regional_ranges": ranges,
        "envelope_provider_id": "caller-envelope-store",
        "envelope_provider_version": "1",
        "envelope_state_digest": DIGEST_C,
        "applicability_basis": "caller-reviewed qualification",
        "evidence": (EVIDENCE,),
    }
    value = {
        "assessment_id": "duplex-phase-1",
        "asset_id": "asset-1",
        "location_id": "weld-1",
        "weld_id": "weld-1",
        "material_condition_id": "duplex-condition-1",
        "welding_process_id": "process-1",
        "process_history_id": "process-history-1",
        "heat_history_id": "heat-history-1",
        "observations": observations,
        "candidate_envelopes": (envelope,),
        "weld_and_region_mapping_reviewed": True,
        "material_and_process_identity_reviewed": True,
        "heat_history_identity_reviewed": True,
        "phase_and_fraction_definitions_reviewed": True,
        "method_applicability_reviewed": True,
        "uncertainty_basis_reviewed": True,
        "provider_state_digests_reviewed": True,
        "envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return DuplexPhaseBalanceAssessment(**value)


def test_weld_haz_and_base_uncertainty_intervals_are_compared():
    result = duplex_phase_balance(payload())
    assert result.status == "computed"
    assert {row["region_kind"] for row in result.values["comparison_rows"]} == {
        "weld_metal",
        "heat_affected_zone",
        "base_material",
    }
    assert result.values["all_uncertainty_intervals_within_declared_phase_envelope"] is True


def test_outside_interval_is_reported_without_acceptance_inference():
    assessment = payload()
    changed = assessment.observations[0].model_copy(update={"measured_fraction": 0.65})
    result = duplex_phase_balance(
        assessment.model_copy(update={"observations": (changed, *assessment.observations[1:])})
    )
    assert result.status == "computed"
    assert result.values["outside_declared_envelope_observation_ids"] == ["w-a"]


def test_missing_review_invalid_record_or_missing_range_needs_data():
    assert duplex_phase_balance(payload(uncertainty_basis_reviewed=False)).status == "needs_data"
    assessment = payload()
    invalid = assessment.observations[0].model_copy(
        update={"record_valid": False, "invalid_basis": "image unavailable"}
    )
    assert (
        duplex_phase_balance(
            assessment.model_copy(update={"observations": (invalid, *assessment.observations[1:])})
        ).status
        == "needs_data"
    )
    envelope = assessment.candidate_envelopes[0]
    incomplete = envelope.model_copy(update={"regional_ranges": envelope.regional_ranges[:-1]})
    assert (
        duplex_phase_balance(assessment.model_copy(update={"candidate_envelopes": (incomplete,)})).status
        == "needs_data"
    )


def test_fraction_sum_and_context_identity_are_enforced():
    assessment = payload()
    excessive = assessment.observations[1].model_copy(update={"measured_fraction": 0.55})
    with pytest.raises(ValueError, match="cannot exceed one"):
        DuplexPhaseBalanceAssessment(
            **assessment.model_dump(exclude={"observations"}),
            observations=(assessment.observations[0], excessive, *assessment.observations[2:]),
        )

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.duplex_phase_balance",
            assessment,
            RunContext(asset_id="other", location_id="weld-1", time_basis="authored"),
        )
