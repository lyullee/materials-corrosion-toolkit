import pytest
from pydantic import ValidationError

from matintegrity.contracts import RunContext
from matintegrity.models.welding_residual_stress import (
    ResidualStressEvidenceAssessment,
    residual_stress_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored residual-stress test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64
DIGEST_E = "e" * 64


def payload(**updates):
    value = {
        "assessment_id": "rs-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "weld_id": "weld-1",
        "material_condition_id": "condition-1",
        "records": (
            {
                "record_id": "record-1",
                "method_kind": "modelled",
                "provider_id": "solver-a",
                "provider_version": "1.0",
                "provider_state_digest": DIGEST_A,
                "record_digest": DIGEST_B,
                "partition": "application",
                "source_group_id": "application-run-1",
                "component_definition": "axial normal stress",
                "coordinate_frame_id": "weld-local",
                "coordinate_frame_definition_sha256": DIGEST_D,
                "coordinate_names": ("distance_along_weld", "depth"),
                "coordinates_m": (0.01, 0.002),
                "stress_Pa": 120e6,
                "expanded_uncertainty_Pa": 10e6,
                "coverage_factor": 2.0,
                "uncertainty_basis": "caller uncertainty model",
                "evidence": (EVIDENCE,),
            },
        ),
        "candidate_supports": (
            {
                "support_id": "support-1",
                "method_kind": "modelled",
                "provider_id": "solver-a",
                "provider_version": "1.0",
                "provider_state_digest": DIGEST_A,
                "component_definition": "axial normal stress",
                "coordinate_frame_id": "weld-local",
                "coordinate_frame_definition_sha256": DIGEST_D,
                "coordinate_names": ("distance_along_weld", "depth"),
                "minimum_coordinates_m": (0.0, 0.0),
                "maximum_coordinates_m": (1.0, 0.02),
                "minimum_supported_stress_Pa": -300e6,
                "maximum_supported_stress_Pa": 300e6,
                "maximum_supported_expanded_uncertainty_Pa": 30e6,
                "applicability_basis": "caller provider qualification",
                "qualification": {
                    "qualification_id": "qualification-1",
                    "calibration_dataset_digest": DIGEST_B,
                    "holdout_dataset_digest": DIGEST_C,
                    "calibration_observation_count": 24,
                    "holdout_observation_count": 8,
                    "holdout_metric_definition": "root mean square stress difference",
                    "holdout_metric_value": 12e6,
                    "holdout_metric_unit": "Pa",
                    "maximum_supported_holdout_metric": 20e6,
                    "maximum_supported_holdout_metric_unit": "Pa",
                    "calibration_and_holdout_independent": True,
                    "qualification_basis": "caller validation plan",
                    "evidence": (EVIDENCE,),
                },
                "evidence": (EVIDENCE,),
            },
        ),
        "weld_and_material_identity_reviewed": True,
        "coordinate_frames_and_components_reviewed": True,
        "units_and_uncertainty_reviewed": True,
        "provider_identity_and_state_reviewed": True,
        "record_digests_reviewed": True,
        "calibration_and_holdout_reviewed": True,
        "support_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return ResidualStressEvidenceAssessment(**value)


def test_application_record_is_mapped_to_reviewed_support():
    result = residual_stress_evidence(payload())
    assert result.status == "computed"
    assert result.values["all_application_records_within_declared_support"] is True
    row = result.values["record_comparisons"][0]
    assert row["uncertainty_interval_minimum_Pa"] == pytest.approx(110e6)
    assert row["uncertainty_interval_maximum_Pa"] == pytest.approx(130e6)
    assert row["source_group_id"] == "application-run-1"
    assert row["provider_state_digest"] == DIGEST_A
    assert row["record_digest"] == DIGEST_B
    assert row["record_evidence"][0]["citation"] == "authored residual-stress test"
    assert row["support_evidence"][0]["source_id"] == "authored"
    assert row["calibration_dataset_digest"] == DIGEST_B
    assert row["holdout_dataset_digest"] == DIGEST_C


def test_application_coordinate_outside_support_has_explicit_reason_and_id():
    base = payload()
    record = base.records[0].model_copy(update={"coordinates_m": (0.01, 0.03)})
    result = residual_stress_evidence(payload(records=(record,)))
    row = result.values["record_comparisons"][0]
    assert row["coordinates_within_declared_support"] is False
    assert "coordinates_outside_declared_support" in row["support_exclusion_reasons"]
    assert result.values["unsupported_application_record_ids"] == ["record-1"]
    assert result.values["all_application_records_within_declared_support"] is False


def test_application_coordinate_dimension_mismatch_has_explicit_reason():
    base = payload()
    record = base.records[0].model_copy(update={"coordinates_m": (0.01,)})
    with pytest.raises(ValidationError, match="coordinate names and values must have equal dimensions"):
        payload(records=(record,))


def test_same_coordinate_frame_with_reordered_axes_is_not_treated_as_matching():
    base = payload()
    record = base.records[0].model_copy(
        update={"coordinate_names": ("depth", "distance_along_weld"), "coordinates_m": (0.002, 0.01)}
    )
    result = residual_stress_evidence(payload(records=(record,)))
    row = result.values["record_comparisons"][0]
    assert row["coordinate_frame_id"] == "weld-local"
    assert row["coordinate_axes_match_in_order"] is False
    assert row["coordinates_within_declared_support"] is False
    assert row["support_exclusion_reasons"] == ["coordinate_axis_order_mismatch"]
    assert result.values["unsupported_application_record_ids"] == ["record-1"]


def test_same_frame_id_with_different_frame_definition_is_not_comparable():
    base = payload()
    record = base.records[0].model_copy(update={"coordinate_frame_definition_sha256": DIGEST_E})
    result = residual_stress_evidence(payload(records=(record,)))
    row = result.values["record_comparisons"][0]
    assert row["coordinate_frame_id"] == "weld-local"
    assert row["coordinate_frame_definition_matches"] is False
    assert row["coordinates_within_declared_support"] is False
    assert row["support_exclusion_reasons"] == ["coordinate_frame_definition_mismatch"]


def test_component_definition_mismatch_is_reported_for_application_record():
    base = payload()
    record = base.records[0].model_copy(update={"component_definition": "transverse normal stress"})
    result = residual_stress_evidence(payload(records=(record,)))
    assert result.values["unmatched_application_record_ids"] == ["record-1"]
    assert result.values["record_match_issue_reasons"] == {"record-1": "component_definition_mismatch"}
    assert result.values["unsupported_application_record_ids"] == ["record-1"]


def test_ambiguous_application_support_candidates_fail_coverage_with_reason():
    base = payload()
    second_support = base.candidate_supports[0].model_copy(update={"support_id": "support-2"})
    result = residual_stress_evidence(
        payload(candidate_supports=(base.candidate_supports[0], second_support))
    )
    assert result.status == "needs_data"
    assert result.values["application_record_count"] == 1
    assert result.values["application_compared_record_count"] == 0
    assert result.values["ambiguous_application_record_ids"] == ["record-1"]
    assert result.values["record_match_issue_reasons"] == {"record-1": "ambiguous_provider_support_match"}
    assert result.values["unsupported_application_record_ids"] == ["record-1"]


def test_unmatched_application_record_is_counted_and_flagged():
    base = payload()
    record = base.records[0].model_copy(update={"provider_id": "unknown-provider"})
    result = residual_stress_evidence(payload(records=(record,)))
    assert result.values["application_record_count"] == 1
    assert result.values["application_compared_record_count"] == 0
    assert result.values["unmatched_application_record_ids"] == ["record-1"]
    assert result.values["unsupported_application_record_ids"] == ["record-1"]
    assert result.values["all_application_records_within_declared_support"] is False
    assert result.values["record_source_lineage"][0]["record_digest"] == DIGEST_B
    assert result.values["record_source_lineage"][0]["evidence"][0]["citation"] == (
        "authored residual-stress test"
    )


def test_outside_value_is_visible_without_acceptance_claim():
    base = payload()
    record = base.records[0].model_copy(update={"stress_Pa": 400e6})
    result = residual_stress_evidence(base.model_copy(update={"records": (record,)}))
    assert result.status == "computed"
    assert result.values["all_application_records_within_declared_support"] is False


def test_uncertainty_interval_outside_stress_support_is_flagged():
    base = payload()
    record = base.records[0].model_copy(update={"stress_Pa": 280e6, "expanded_uncertainty_Pa": 30e6})
    result = residual_stress_evidence(base.model_copy(update={"records": (record,)}))
    row = result.values["record_comparisons"][0]
    assert row["stress_within_declared_provider_support"] is True
    assert row["uncertainty_interval_within_declared_stress_support"] is False
    assert row["record_within_declared_support"] is False
    assert result.values["unsupported_record_ids"] == ["record-1"]
    assert result.values["unsupported_application_record_ids"] == ["record-1"]


def test_unreviewed_or_unqualified_provider_needs_data():
    assert (
        residual_stress_evidence(payload(provider_identity_and_state_reviewed=False)).status == "needs_data"
    )
    base = payload()
    qualification = base.candidate_supports[0].qualification.model_copy(update={"holdout_metric_value": 25e6})
    support = base.candidate_supports[0].model_copy(update={"qualification": qualification})
    result = residual_stress_evidence(base.model_copy(update={"candidate_supports": (support,)}))
    assert result.status == "needs_data"
    assert result.values["invalid_qualification_support_ids"] == ["support-1"]


def test_holdout_metric_value_and_limit_must_use_same_unit():
    value = payload().model_dump(mode="python")
    value["candidate_supports"][0]["qualification"]["maximum_supported_holdout_metric_unit"] = "MPa"
    with pytest.raises(ValueError, match="must use the same unit"):
        ResidualStressEvidenceAssessment(**value)


def test_source_groups_cannot_leak_across_calibration_holdout_and_application():
    base = payload()
    application = base.records[0].model_copy(update={"record_id": "application-1"})
    calibration = application.model_copy(
        update={"record_id": "calibration-1", "partition": "calibration", "source_group_id": "shared-run"}
    )
    application = application.model_copy(update={"source_group_id": "shared-run"})
    with pytest.raises(ValueError, match="disjoint across data partitions"):
        payload(records=(calibration, application))


def test_application_record_ids_remain_separate_from_calibration_and_holdout():
    base = payload()
    application = base.records[0].model_copy(update={"record_id": "application-1"})
    calibration = application.model_copy(
        update={
            "record_id": "calibration-1",
            "partition": "calibration",
            "source_group_id": "calibration-run",
            "stress_Pa": 400e6,
        }
    )
    holdout = application.model_copy(
        update={
            "record_id": "holdout-1",
            "partition": "holdout",
            "source_group_id": "holdout-run",
            "stress_Pa": 400e6,
        }
    )
    result = residual_stress_evidence(payload(records=(calibration, holdout, application)))
    assert result.values["partition_record_ids"] == {
        "calibration": ["calibration-1"],
        "holdout": ["holdout-1"],
        "application": ["application-1"],
    }
    assert result.values["unsupported_record_ids"] == ["calibration-1", "holdout-1"]
    assert result.values["unsupported_application_record_ids"] == []
    assert [row["partition"] for row in result.values["record_source_lineage"]] == [
        "calibration",
        "holdout",
        "application",
    ]
    assert result.values["provider_support_lineage"][0]["qualification"]["qualification_id"] == (
        "qualification-1"
    )


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.residual_stress_evidence",
            payload(),
            RunContext(asset_id="other", location_id="joint-1", time_basis="authored"),
        )
