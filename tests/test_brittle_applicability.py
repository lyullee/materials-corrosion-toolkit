import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.brittle_applicability import (
    BrittleApplicabilityEvidenceAssessment,
    brittle_applicability_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def digest(character):
    return character * 64


def evidence_record(record_id, specimen_id, source_group, value):
    return {
        "record_id": record_id,
        "physical_specimen_id": specimen_id,
        "source_group_id": source_group,
        "independence_group_id": source_group,
        "test_kind": "impact",
        "result_name": "absorbed_energy",
        "result_value": value,
        "result_unit_token": "J",
        "expanded_uncertainty": 1.5,
        "uncertainty_coverage_factor": 2.0,
        "test_temperature_K": 250.0,
        "specimen_orientation_id": "transverse",
        "specimen_thickness_m": 0.01,
        "method_id": "caller-impact-method",
        "provider_id": "caller-laboratory",
        "provider_version": "2",
        "configuration_digest": digest("a"),
        "data_digest": digest("b"),
        "result_digest": digest(record_id[-1]),
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def payload(**updates):
    envelope = {
        "envelope_id": "brittle-envelope-1",
        "material_specification_id": "spec-1",
        "product_form_id": "plate",
        "material_condition_id": "condition-1",
        "minimum_thickness_m": 0.005,
        "maximum_thickness_m": 0.05,
        "minimum_supported_service_temperature_K": 220.0,
        "maximum_supported_service_temperature_K": 300.0,
        "applicable_orientation_ids": ("transverse",),
        "loading_descriptors": ("membrane-plus-bending",),
        "loading_rate_descriptors": ("quasi-static",),
        "evidence_requirements": (
            {
                "requirement_id": "impact-evidence",
                "test_kind": "impact",
                "result_name": "absorbed_energy",
                "result_unit_token": "J",
                "applicable_orientation_ids": ("transverse",),
                "minimum_test_temperature_K": 240.0,
                "maximum_test_temperature_K": 260.0,
                "minimum_record_count": 2,
                "requirement_basis": "caller evidence plan",
            },
        ),
        "provider_id": "caller-envelope-provider",
        "provider_version": "1",
        "configuration_digest": digest("c"),
        "data_digest": digest("d"),
        "result_digest": digest("e"),
        "applicability_basis": "caller-reviewed material program",
        "evidence": (EVIDENCE,),
    }
    value = {
        "assessment_id": "brittle-1",
        "asset_id": "asset-1",
        "location_id": "course-1",
        "material_id": "heat-1",
        "material_specification_id": "spec-1",
        "product_form_id": "plate",
        "material_condition_id": "condition-1",
        "governing_thickness_m": 0.02,
        "governing_orientation_id": "transverse",
        "minimum_service_temperature_K": 240.0,
        "loading_descriptor": "membrane-plus-bending",
        "loading_rate_descriptor": "quasi-static",
        "test_records": (
            evidence_record("record-1", "specimen-1", "source-a", 35.0),
            evidence_record("record-2", "specimen-2", "source-b", 40.0),
        ),
        "candidate_envelopes": (envelope,),
        "material_specification_and_condition_reviewed": True,
        "product_form_thickness_and_orientation_reviewed": True,
        "service_temperature_reviewed": True,
        "loading_and_rate_descriptors_reviewed": True,
        "specimen_and_source_group_partitions_reviewed": True,
        "method_and_units_reviewed": True,
        "uncertainty_basis_reviewed": True,
        "provider_and_digest_lineage_reviewed": True,
        "applicability_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return BrittleApplicabilityEvidenceAssessment(**value)


def test_evidence_requirements_and_source_partitions_are_reported():
    result = brittle_applicability_evidence(payload())
    assert result.status == "computed"
    assert result.values["missing_evidence_requirement_ids"] == []
    assert len(result.values["source_and_independence_group_partitions"]) == 2


def test_insufficient_evidence_and_missing_review_need_data():
    assessment = payload()
    result = brittle_applicability_evidence(
        assessment.model_copy(update={"test_records": assessment.test_records[:1]})
    )
    assert result.status == "needs_data"
    assert result.values["missing_evidence_requirement_ids"] == ["impact-evidence"]
    assert brittle_applicability_evidence(payload(method_and_units_reviewed=False)).status == "needs_data"


def test_service_case_outside_caller_envelope_is_out_of_scope():
    result = brittle_applicability_evidence(payload(minimum_service_temperature_K=210.0))
    assert result.status == "out_of_scope"


def test_specimen_partition_and_context_identity_are_enforced():
    assessment = payload()
    conflicting = assessment.test_records[1].model_copy(update={"physical_specimen_id": "specimen-1"})
    with pytest.raises(ValueError, match="cannot cross"):
        BrittleApplicabilityEvidenceAssessment(
            **assessment.model_dump(exclude={"test_records"}),
            test_records=(assessment.test_records[0], conflicting),
        )

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "materials.brittle_applicability_evidence",
            assessment,
            RunContext(asset_id="other", location_id="course-1", time_basis="authored"),
        )
