import pytest

from matintegrity.contracts import Evidence
from matintegrity.models.coating_qualification import (
    CoatingQualificationAssessment,
    CoatingQualificationMeasurement,
    CoatingQualificationSpecimen,
    DeclaredCoatingRequirement,
    coating_qualification_assessment,
)

EVIDENCE = Evidence(source_id="authored", origin="synthetic", citation="authored test")


def specimen(identifier, partition, group):
    return CoatingQualificationSpecimen(
        specimen_id=identifier,
        coating_system_id="system-1",
        coating_lot_id=f"lot-{partition}",
        substrate_condition_id="prepared-steel",
        exposure_id="salt-exposure",
        source_group_id=group,
        partition=partition,
        evidence=[EVIDENCE],
    )


def measurement(identifier, specimen_id, value=200.0, valid=True):
    return CoatingQualificationMeasurement(
        measurement_id=identifier,
        specimen_id=specimen_id,
        metric_id="dft",
        metric_kind="dry_film_thickness",
        value=value,
        expanded_uncertainty=5.0,
        unit_token="um",
        measurement_valid=valid,
        missing_or_invalid_basis=None if valid else "instrument flag",
        method_id="dft-method",
        evidence=[EVIDENCE],
    )


def request(**updates):
    payload = {
        "qualification_id": "qualification-1",
        "coating_system_id": "system-1",
        "protocol_id": "protocol-1",
        "protocol_revision": "A",
        "specimens": [
            specimen("cal-1", "calibration", "group-cal"),
            specimen("hold-1", "holdout", "group-hold"),
        ],
        "measurements": [measurement("m-cal", "cal-1"), measurement("m-hold", "hold-1", 210.0)],
        "declared_requirements": [
            DeclaredCoatingRequirement(
                requirement_id="dft-min",
                metric_id="dft",
                comparator="minimum",
                limit_value=190.0,
                unit_token="um",
                applicability_description="authored example system",
                authority_basis="caller-owned requirement",
                evidence=[EVIDENCE],
            )
        ],
        "specimen_identity_reviewed": True,
        "coating_lot_traceability_reviewed": True,
        "exposure_identity_reviewed": True,
        "measurement_methods_reviewed": True,
        "uncertainty_basis_reviewed": True,
        "partition_independence_reviewed": True,
        "requirement_authority_reviewed": True,
        "evidence": [EVIDENCE],
    }
    payload.update(updates)
    return CoatingQualificationAssessment(**payload)


def test_partitions_are_summarized_and_compared_separately():
    result = coating_qualification_assessment(request())
    assert result.status == "computed"
    assert result.values["specimen_count_by_partition"] == {"calibration": 1, "holdout": 1}
    rows = result.values["declared_requirement_rows"]
    assert [row["partition"] for row in rows] == ["calibration", "holdout"]
    assert all(row["all_valid_measurements_satisfy_declared_requirement"] for row in rows)


def test_source_group_leakage_and_unit_mismatch_are_rejected():
    with pytest.raises(ValueError, match="cannot cross"):
        request(specimens=[specimen("cal-1", "calibration", "same"), specimen("hold-1", "holdout", "same")])
    wrong = measurement("m-hold", "hold-1", 210.0).model_copy(update={"unit_token": "mm"})
    with pytest.raises(ValueError, match="units must match"):
        request(measurements=[measurement("m-cal", "cal-1"), wrong])


def test_invalid_measurement_and_missing_review_remain_needs_data():
    invalid = measurement("m-hold", "hold-1", 210.0, valid=False)
    result = coating_qualification_assessment(
        request(
            measurements=[measurement("m-cal", "cal-1"), invalid],
            uncertainty_basis_reviewed=False,
        )
    )
    assert result.status == "needs_data"
    assert result.values["incomplete_requirement_partition_ids"] == ["dft-min:holdout"]
    assert (
        result.values["declared_requirement_rows"][1]["all_valid_measurements_satisfy_declared_requirement"]
        is None
    )
