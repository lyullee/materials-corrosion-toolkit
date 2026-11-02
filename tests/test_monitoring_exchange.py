from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity import evaluate
from matintegrity.adapters import MonitoringAssessmentRecord, monitoring_record
from matintegrity.contracts import RunContext

CONTEXT = RunContext(
    asset_id="synthetic-asset",
    location_id="synthetic-location",
    time_basis="authored elapsed seconds",
)


def assessment():
    return evaluate(
        "structural.pressure_temperature_envelope",
        {
            "envelope_id": "monitoring-exchange-example",
            "applicability_basis": "authored exchange test only",
            "source_sha256": "1" * 64,
            "knots": [
                {"temperature_K": 250.0, "allowable_pressure_Pa": 12.0e6},
                {"temperature_K": 350.0, "allowable_pressure_Pa": 8.0e6},
            ],
            "operating_points": [{"point_id": "snapshot", "temperature_K": 300.0, "pressure_Pa": 9.0e6}],
            "applicability_reviewed": True,
            "operating_points_reviewed": True,
        },
        CONTEXT,
    )


def test_monitoring_record_round_trips_complete_assessment_identity():
    source = assessment()
    record = monitoring_record(source)
    restored = MonitoringAssessmentRecord.model_validate_json(
        MonitoringAssessmentRecord.model_validate(record).model_dump_json()
    )

    assert restored.model_id == source.model_id
    assert restored.input_digest == source.input_digest
    assert restored.context == source.context.model_dump(mode="json")
    assert restored.values == source.values
    assert restored.assumptions == list(source.assumptions)
    assert restored.qualification == source.qualification
    assert restored.source_digest != source.input_digest


@pytest.mark.parametrize(
    ("path", "replacement"),
    [
        (("values", "minimum_pressure_margin_Pa"), -123.0),
        (("model_version",), "tampered"),
        (("probability_semantics",), {"invented": "conditional_first_failure_in_period"}),
    ],
)
def test_monitoring_record_digest_rejects_tampered_assessment_fields(path, replacement):
    record = deepcopy(monitoring_record(assessment()))
    target = record
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement

    with pytest.raises(ValidationError, match="digest does not match"):
        MonitoringAssessmentRecord.model_validate(record)


def test_monitoring_record_rejects_flat_identity_different_from_context():
    record = monitoring_record(assessment())
    record["asset_id"] = "different-asset"
    with pytest.raises(ValidationError, match="identity and time basis"):
        MonitoringAssessmentRecord.model_validate(record)


def test_needs_data_is_not_relabelled_as_normal_or_alarm():
    result = evaluate(
        "reliability.independent_gate",
        {"probabilities": [0.1, 0.2], "gate": "OR", "independence_declared": False},
        CONTEXT,
    )
    record = monitoring_record(result)

    assert record["status"] == "needs_data"
    assert "alarm" not in record and "normal" not in record
    assert record["probability_semantics"] == {"probability": "unscoped_event_probability"}
