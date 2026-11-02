import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.brazing_bonding import (
    BrazingBondingQualification,
    brazing_bonding_qualification,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}


def qualification_record(**updates):
    value = {
        "evidence_record_id": "record-1",
        "physical_specimen_id": "specimen-1",
        "source_group_id": "source-1",
        "independence_group_id": "independent-1",
        "member_material_ids": ("member-a", "member-b"),
        "member_surface_condition_ids": ("surface-a", "surface-b"),
        "bonding_material_id": "filler-1",
        "bonding_material_lot_id": "filler-lot-q",
        "process_id": "vacuum-braze",
        "flux_id": "no-flux",
        "joint_clearance_value": 0.1,
        "joint_clearance_unit_token": "custom-length",
        "overlap_value": 5.0,
        "overlap_unit_token": "custom-length",
        "observations": (
            {
                "observation_id": "observation-1",
                "observation_kind": "mechanical",
                "metric_id": "caller-strength",
                "metric_definition": "authored mechanical endpoint",
                "method_id": "method-1",
                "reported_value": 100.0,
                "unit_token": "custom-strength",
                "expanded_uncertainty": 5.0,
                "coverage_factor": 2.0,
                "result_digest": "a" * 64,
                "record_available": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "provider_id": "laboratory-1",
        "provider_revision": "1",
        "provider_state_digest": "b" * 64,
        "input_digest": "c" * 64,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "member_material_ids": ("member-a", "member-b"),
        "member_surface_condition_ids": ("surface-a", "surface-b"),
        "supported_bonding_material_ids": ("filler-1",),
        "supported_process_ids": ("vacuum-braze",),
        "supported_flux_ids": ("no-flux",),
        "supported_atmosphere_descriptors": ("vacuum-a",),
        "minimum_joint_clearance_value": 0.05,
        "maximum_joint_clearance_value": 0.2,
        "joint_clearance_unit_token": "custom-length",
        "minimum_overlap_value": 4.0,
        "maximum_overlap_value": 6.0,
        "overlap_unit_token": "custom-length",
        "minimum_temperature_K": 300.0,
        "maximum_temperature_K": 1100.0,
        "minimum_pressure_value": 0.0,
        "maximum_pressure_value": 1.0,
        "pressure_unit_token": "custom-pressure",
        "maximum_cycle_duration_s": 1000.0,
        "evidence_requirements": (
            {
                "requirement_id": "mechanical-1",
                "observation_kind": "mechanical",
                "metric_id": "caller-strength",
                "metric_definition": "authored mechanical endpoint",
                "unit_token": "custom-strength",
                "minimum_record_count": 1,
                "requirement_basis": "caller evidence plan",
            },
        ),
        "qualification_records": (qualification_record(),),
        "qualification_basis": "caller qualification programme",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def segment(identifier="segment-1", **updates):
    value = {
        "segment_id": identifier,
        "start_time_s": 0.0,
        "end_time_s": 300.0,
        "minimum_temperature_K": 300.0,
        "maximum_temperature_K": 1000.0,
        "minimum_pressure_value": 0.0,
        "maximum_pressure_value": 0.5,
        "pressure_unit_token": "custom-pressure",
        "atmosphere_descriptor": "vacuum-a",
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def joint(**updates):
    value = {
        "joint_id": "joint-1",
        "member_material_ids": ("member-a", "member-b"),
        "member_surface_condition_ids": ("surface-a", "surface-b"),
        "bonding_material_id": "filler-1",
        "bonding_material_lot_id": "lot-production-1",
        "process_id": "vacuum-braze",
        "flux_id": "no-flux",
        "joint_clearance_value": 0.1,
        "joint_clearance_unit_token": "custom-length",
        "overlap_value": 5.0,
        "overlap_unit_token": "custom-length",
        "cycle_segments": (segment(),),
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "bonding-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "joints": (joint(),),
        "qualification_envelope": envelope(),
        "member_material_and_surface_conditions_reviewed": True,
        "bonding_material_and_lot_reviewed": True,
        "process_atmosphere_and_flux_reviewed": True,
        "clearance_overlap_and_geometry_reviewed": True,
        "heat_pressure_cycle_and_clock_reviewed": True,
        "physical_specimen_and_source_group_partitions_reviewed": True,
        "observation_metrics_units_and_uncertainty_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return BrazingBondingQualification(**value)


def test_supported_joint_computes_without_acceptance_claim():
    result = brazing_bonding_qualification(payload())
    assert result.status == "computed"
    assert result.values["declared_qualification_outcome"] == "within_support"
    assert result.values["evidence_requirement_counts"] == {"mechanical-1": 1}


def test_reviewed_outside_cycle_and_geometry_are_out_of_scope():
    result = brazing_bonding_qualification(
        payload(
            joints=(
                joint(
                    overlap_value=7.0,
                    cycle_segments=(segment(maximum_temperature_K=1200.0),),
                ),
            )
        )
    )
    assert result.status == "out_of_scope"
    assert result.values["joint_comparisons"][0]["outside_support_reasons"] == [
        "overlap",
        "temperature:segment-1",
    ]


def test_missing_review_unit_or_evidence_needs_data():
    assert (
        brazing_bonding_qualification(payload(heat_pressure_cycle_and_clock_reviewed=False)).status
        == "needs_data"
    )
    assert (
        brazing_bonding_qualification(
            payload(joints=(joint(cycle_segments=(segment(pressure_unit_token="other"),)),))
        ).status
        == "needs_data"
    )
    missing = envelope(
        evidence_requirements=(
            {
                "requirement_id": "nde-1",
                "observation_kind": "nde",
                "metric_id": "coverage",
                "metric_definition": "authored NDE coverage",
                "unit_token": "fraction",
                "minimum_record_count": 1,
                "requirement_basis": "caller evidence plan",
            },
        )
    )
    result = brazing_bonding_qualification(payload(qualification_envelope=missing))
    assert result.status == "needs_data"
    assert result.values["missing_evidence_requirement_ids"] == ["nde-1"]


def test_ordering_specimen_identity_and_context_are_strict():
    with pytest.raises(ValueError, match="cannot overlap"):
        payload(
            joints=(
                joint(
                    cycle_segments=(
                        segment("segment-1", start_time_s=0.0, end_time_s=20.0),
                        segment("segment-2", start_time_s=10.0, end_time_s=30.0),
                    )
                ),
            )
        )
    duplicate = qualification_record()
    second = qualification_record(evidence_record_id="record-2")
    with pytest.raises(ValueError, match="physical specimen"):
        payload(qualification_envelope=envelope(qualification_records=(duplicate, second)))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.brazing_bonding_qualification",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
