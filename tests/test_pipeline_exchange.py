from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.pipeline_exchange import PipelineAssessmentRecord, pipeline_assessment_record


def source_result():
    return {
        "schema_version": "pipeline_integrity.result.v1",
        "model_id": "geometry.pipe",
        "model_version": "1.0.0",
        "status": "computed",
        "inputs": {"inner_diameter_m": 0.5},
        "values": {"flow_area_m2": 0.19634954084936207},
        "input_units": {"inner_diameter_m": "m"},
        "output_units": {"flow_area_m2": "m2"},
        "assumptions": ["authored exchange fixture"],
        "notes": [],
        "source_ids": ["authored"],
        "context": {
            "asset_id": "pipe-1",
            "scenario_id": "normal-operation",
            "clock_id": "elapsed-s",
            "origin": "synthetic",
            "evidence": [
                {
                    "id": "geometry-source",
                    "citation": "authored exchange fixture",
                    "origin": "synthetic",
                    "locator": "",
                    "sha256": None,
                    "license_id": None,
                    "limitations": [],
                }
            ],
            "metadata": {},
        },
        "input_digest": "1" * 64,
        "model_source_digest": "2" * 64,
        "runtime": {"python": "3.12"},
        "qualification": "engineering_screening",
    }


def record():
    return pipeline_assessment_record(
        provider_id="pipeline-integrity-toolkit",
        provider_package_version="0.1.0.dev0",
        provider_source_tree_sha256="3" * 64,
        provider_source_file_count=100,
        source_result=source_result(),
        limitations=["Synthetic exchange fixture; not field or design acceptance."],
    )


def test_pipeline_result_round_trip_preserves_units_context_and_qualification():
    restored = PipelineAssessmentRecord.model_validate_json(record().model_dump_json())
    assert restored.output_units == {"flow_area_m2": "m2"}
    assert restored.clock_id == "elapsed-s"
    assert restored.qualification == "engineering_screening"
    assert not restored.field_or_design_acceptance_claim


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("model_id",), "other"),
        (("source_result", "output_units"), {"flow_area_m2": "Pa"}),
        (("source_result", "context", "clock_id"), "foreign-clock"),
        (("provider_source_tree_sha256",), "4" * 64),
    ],
)
def test_pipeline_result_rejects_tampering(path, replacement):
    payload = deepcopy(record().model_dump(mode="json"))
    target = payload
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    with pytest.raises(ValidationError):
        PipelineAssessmentRecord.model_validate(payload)


def test_pipeline_result_rejects_duplicate_evidence_ids():
    source = source_result()
    source["context"]["evidence"].append(deepcopy(source["context"]["evidence"][0]))
    with pytest.raises(ValidationError, match="unique"):
        pipeline_assessment_record(
            provider_id="pipeline-integrity-toolkit",
            provider_package_version="0.1.0.dev0",
            provider_source_tree_sha256="5" * 64,
            provider_source_file_count=100,
            source_result=source,
            limitations=["negative control"],
        )


def test_pipeline_result_cannot_claim_field_or_design_acceptance():
    payload = record().model_dump(mode="json")
    payload["field_or_design_acceptance_claim"] = True
    with pytest.raises(ValidationError):
        PipelineAssessmentRecord.model_validate(payload)
