from copy import deepcopy

import pytest
from pydantic import ValidationError

from matintegrity.models.bolted_joint_assembly_profile import (
    BoltedJointAssemblyAssessment,
    BoltedJointAssemblyAssessmentResult,
    assess_bolted_joint_assembly,
)

SHA = "a" * 64


def ev(label):
    return {"source_id": label, "origin": "user_declared", "citation": label, "sha256": SHA}


def payload(**changes):
    data = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "flange-location-1",
        "joint_id": "joint-1",
        "flange_geometry_id": "flange-geometry-1",
        "flange_face_pair_id": "face-pair-1",
        "flange_face_condition_id": "face-condition-1",
        "gasket_condition_id": "gasket-condition-1",
        "gasket_lot_id": "gasket-lot-1",
        "bolt_condition_id": "bolt-condition-1",
        "bolt_lot_id": "bolt-lot-1",
        "assembly_procedure_id": "assembly-procedure-1",
        "assembly_procedure_revision": "1",
        "bolt_preloads": tuple(
            {
                "bolt_id": f"bolt-{index}",
                "bolt_position_id": f"position-{index}",
                "preload_n": value,
                "standard_uncertainty_n": 100.0,
                "status": "available",
                "measurement_method_id": "direct-method",
                "provider_id": "assembly-provider",
                "provider_revision": "1",
                "result_digest": SHA,
                "evidence": (ev(f"bolt-{index}"),),
            }
            for index, value in enumerate((10_000.0, 10_200.0), start=1)
        ),
        "flange_alignment": (
            {
                "observation_id": "alignment-1",
                "flange_face_pair_id": "face-pair-1",
                "location_id": "clock-12",
                "alignment_metric_id": "axial-gap",
                "alignment_metric_definition": "caller axial face gap",
                "alignment_m": 0.0002,
                "standard_uncertainty_m": 0.00002,
                "status": "available",
                "provider_id": "alignment-provider",
                "provider_revision": "1",
                "result_digest": SHA,
                "evidence": (ev("alignment"),),
            },
        ),
        "gasket_measurement": {
            "measurement_id": "gasket-measurement-1",
            "initial_thickness_m": 0.004,
            "assembled_thickness_m": 0.0032,
            "thickness_standard_uncertainty_m": 0.00001,
            "recovery_fraction": 0.5,
            "recovery_standard_uncertainty_fraction": 0.01,
            "method_id": "thickness-method",
            "provider_id": "gasket-provider",
            "provider_revision": "1",
            "result_digest": SHA,
            "evidence": (ev("gasket-measurement"),),
        },
        "load_cycles": (
            {
                "cycle_id": "cycle-1",
                "sequence_position": 1,
                "clock_id": "service-clock-1",
                "start_time_s": 0.0,
                "end_time_s": 1000.0,
                "minimum_temperature_k": 300.0,
                "maximum_temperature_k": 400.0,
                "minimum_absolute_pressure_pa": 100_000.0,
                "maximum_absolute_pressure_pa": 1_000_000.0,
                "provider_id": "history-provider",
                "provider_revision": "1",
                "result_digest": SHA,
                "evidence": (ev("cycle-1"),),
            },
        ),
        "leakage_observations": (
            {
                "observation_id": "leak-1",
                "clock_id": "service-clock-1",
                "elapsed_time_s": 500.0,
                "medium_id": "medium-1",
                "detection_status": "not_detected",
                "leakage_unit_token": "kg/s",
                "detection_limit": 1e-7,
                "method_id": "leak-method",
                "provider_id": "leak-provider",
                "provider_revision": "1",
                "result_digest": SHA,
                "evidence": (ev("leak-1"),),
            },
        ),
        "profile": {
            "profile_id": "profile-1",
            "profile_revision": "1",
            "source_digest": SHA,
            "permitted_flange_geometry_ids": ("flange-geometry-1",),
            "permitted_flange_face_condition_ids": ("face-condition-1",),
            "permitted_gasket_condition_ids": ("gasket-condition-1",),
            "permitted_bolt_condition_ids": ("bolt-condition-1",),
            "minimum_bolt_preload_n": 9000.0,
            "maximum_bolt_preload_n": 11000.0,
            "maximum_preload_coefficient_of_variation": 0.05,
            "preload_uncertainty_policy": "interval_must_fit",
            "preload_uncertainty_coverage_factor": 2.0,
            "maximum_flange_alignment_m": 0.0003,
            "alignment_uncertainty_policy": "interval_must_fit",
            "alignment_uncertainty_coverage_factor": 2.0,
            "gasket_envelope": {
                "envelope_id": "gasket-envelope-1",
                "minimum_compression_fraction": 0.15,
                "maximum_compression_fraction": 0.25,
                "minimum_recovery_fraction": 0.4,
                "maximum_recovery_fraction": 0.6,
                "uncertainty_policy": "interval_must_fit",
                "uncertainty_coverage_factor": 2.0,
                "missing_recovery_disposition": "insufficient_evidence",
                "source_digest": SHA,
                "evidence": (ev("gasket-envelope"),),
            },
            "minimum_supported_temperature_k": 280.0,
            "maximum_supported_temperature_k": 450.0,
            "maximum_supported_absolute_pressure_pa": 2_000_000.0,
            "leakage_unit_token": "kg/s",
            "maximum_leakage_rate": 1e-6,
            "detected_leak_disposition": "reject",
            "profile_reviewed": True,
            "evidence": (ev("profile"),),
        },
        "assembly_identity_lots_and_procedure_reviewed": True,
        "preload_method_units_uncertainty_and_positions_reviewed": True,
        "flange_faces_alignment_metric_and_uncertainty_reviewed": True,
        "gasket_measurement_and_caller_envelope_reviewed": True,
        "load_history_clock_temperature_and_pressure_reviewed": True,
        "leakage_status_units_limits_and_lineage_reviewed": True,
        "evidence": (ev("assessment"),),
    }
    data.update(changes)
    return BoltedJointAssemblyAssessment.model_validate(data)


def test_caller_profile_accepts_complete_assembly_history():
    result = assess_bolted_joint_assembly(payload())
    assert result.disposition == "accept"
    assert all(row.outcome == "pass" for row in result.findings)
    assert not result.code_or_standard_qualification_claim
    assert not result.physical_validation_claim


def test_preload_uncertainty_alignment_cycle_and_leakage_can_reject():
    base = payload()
    bolt = base.bolt_preloads[0].model_copy(update={"preload_n": 8800.0})
    result = assess_bolted_joint_assembly(
        base.model_copy(update={"bolt_preloads": (bolt, base.bolt_preloads[1])})
    )
    assert result.disposition == "reject"
    assert any(row.rule_id == "individual_bolt_preload" and row.outcome == "fail" for row in result.findings)

    leak = base.leakage_observations[0].model_copy(
        update={
            "detection_status": "detected",
            "leakage_rate": 2e-6,
            "standard_uncertainty": 1e-7,
            "detection_limit": None,
        }
    )
    assert (
        assess_bolted_joint_assembly(base.model_copy(update={"leakage_observations": (leak,)})).disposition
        == "reject"
    )


def test_identity_mismatch_is_review_and_missing_evidence_is_insufficient():
    reviewed = assess_bolted_joint_assembly(payload(flange_face_condition_id="unlisted-face"))
    assert reviewed.disposition == "review"

    base = payload()
    missing = base.bolt_preloads[0].model_copy(
        update={
            "status": "missing",
            "preload_n": None,
            "standard_uncertainty_n": None,
            "result_digest": None,
            "missing_or_invalid_basis": "not measured",
        }
    )
    result = assess_bolted_joint_assembly(
        base.model_copy(update={"bolt_preloads": (missing, base.bolt_preloads[1])})
    )
    assert result.disposition == "insufficient_evidence"


def test_clock_identity_units_and_sequence_are_strict():
    base = payload()
    leak = base.leakage_observations[0].model_copy(update={"clock_id": "other"})
    with pytest.raises(ValidationError, match="load-history clock"):
        payload(leakage_observations=(leak,))

    bad = base.leakage_observations[0].model_copy(update={"leakage_unit_token": "mol/s"})
    result = assess_bolted_joint_assembly(payload(leakage_observations=(bad,)))
    assert result.disposition == "insufficient_evidence"


def test_result_digest_is_deterministic_and_tamper_evident():
    first = assess_bolted_joint_assembly(payload())
    second = assess_bolted_joint_assembly(payload())
    assert first.input_digest == second.input_digest
    assert first.result_digest == second.result_digest
    assert BoltedJointAssemblyAssessmentResult.model_validate_json(first.model_dump_json()) == first

    changed = deepcopy(first.model_dump(mode="python"))
    changed["disposition"] = "reject"
    with pytest.raises(ValidationError, match="digest"):
        BoltedJointAssemblyAssessmentResult.model_validate(changed)
