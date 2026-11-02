import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen_fatigue_provider import (
    HydrogenFatigueProviderEvidenceAssessment,
    hydrogen_fatigue_provider_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def qualification_record(identifier, partition, source, independence, **updates):
    value = {
        "evidence_record_id": identifier,
        "partition": partition,
        "physical_specimen_id": f"specimen-{identifier}",
        "source_group_id": source,
        "independence_group_id": independence,
        "material_condition_id": "condition-1",
        "hydrogen_species": "H2",
        "exposure_quantity_kind": "absolute_partial_pressure",
        "exposure_quantity_unit_token": "Pa_abs",
        "delta_k_definition": "caller range definition",
        "delta_k_unit_token": "custom-delta-k",
        "growth_rate_definition": "caller cycle growth definition",
        "growth_rate_unit_token": "custom-length-per-cycle",
        "provider_id": "provider-1",
        "provider_revision": "revision-1",
        "provider_configuration_digest": DIGEST_A,
        "input_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "hydrogen_species": "H2",
        "exposure_quantity_kind": "absolute_partial_pressure",
        "exposure_quantity_unit_token": "Pa_abs",
        "minimum_exposure_quantity_value": 100000.0,
        "maximum_exposure_quantity_value": 5000000.0,
        "minimum_temperature_K": 250.0,
        "maximum_temperature_K": 350.0,
        "minimum_load_ratio": 0.0,
        "maximum_load_ratio": 0.8,
        "minimum_frequency_Hz": 0.1,
        "maximum_frequency_Hz": 10.0,
        "supported_waveform_descriptors": ("sine",),
        "delta_k_definition": "caller range definition",
        "delta_k_unit_token": "custom-delta-k",
        "minimum_delta_k_value": 5.0,
        "maximum_delta_k_value": 30.0,
        "growth_rate_definition": "caller cycle growth definition",
        "growth_rate_unit_token": "custom-length-per-cycle",
        "supported_result_kinds": ("tabulated_growth_curve", "predicted_growth_rate"),
        "solver_or_method_id": "method-1",
        "solver_or_method_revision": "method-revision-1",
        "provider_id": "provider-1",
        "provider_revision": "revision-1",
        "provider_configuration_digest": DIGEST_A,
        "qualification_evidence": (
            qualification_record("cal-1", "calibration", "source-cal", "ind-cal"),
            qualification_record("hold-1", "holdout", "source-hold", "ind-hold"),
        ),
        "minimum_calibration_source_group_count": 1,
        "minimum_holdout_source_group_count": 1,
        "minimum_holdout_independence_group_count": 1,
        "qualification_basis": "caller validation plan",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def provider_result(**updates):
    value = {
        "result_record_id": "result-1",
        "curve_or_result_id": "curve-1",
        "result_kind": "tabulated_growth_curve",
        "material_condition_id": "condition-1",
        "hydrogen_species": "H2",
        "exposure_quantity_kind": "absolute_partial_pressure",
        "exposure_quantity_value": 2000000.0,
        "exposure_quantity_unit_token": "Pa_abs",
        "temperature_K": 293.15,
        "load_ratio": 0.1,
        "frequency_Hz": 1.0,
        "waveform_descriptor": "sine",
        "delta_k_definition": "caller range definition",
        "delta_k_unit_token": "custom-delta-k",
        "growth_rate_definition": "caller cycle growth definition",
        "growth_rate_unit_token": "custom-length-per-cycle",
        "points": (
            {
                "point_id": "point-1",
                "delta_k_value": 10.0,
                "growth_rate_value": 1e-8,
                "expanded_growth_rate_uncertainty": 1e-9,
                "uncertainty_coverage_factor": 2.0,
                "evidence": (EVIDENCE,),
            },
            {
                "point_id": "point-2",
                "delta_k_value": 20.0,
                "growth_rate_value": 4e-8,
                "expanded_growth_rate_uncertainty": 4e-9,
                "uncertainty_coverage_factor": 2.0,
                "evidence": (EVIDENCE,),
            },
        ),
        "solver_or_method_id": "method-1",
        "solver_or_method_revision": "method-revision-1",
        "provider_id": "provider-1",
        "provider_revision": "revision-1",
        "provider_configuration_digest": DIGEST_A,
        "input_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "crack-1",
        "material_id": "material-1",
        "material_condition_id": "condition-1",
        "hydrogen_species": "H2",
        "exposure_quantity_kind": "absolute_partial_pressure",
        "exposure_quantity_value": 2000000.0,
        "exposure_quantity_unit_token": "Pa_abs",
        "temperature_K": 293.15,
        "load_ratio": 0.1,
        "frequency_Hz": 1.0,
        "waveform_descriptor": "sine",
        "provider_result": provider_result(),
        "candidate_envelopes": (envelope(),),
        "material_and_condition_reviewed": True,
        "hydrogen_species_quantity_basis_and_units_reviewed": True,
        "temperature_load_ratio_frequency_and_waveform_reviewed": True,
        "crack_growth_definitions_units_and_uncertainty_reviewed": True,
        "specimen_source_and_independence_partitions_reviewed": True,
        "solver_provider_revision_and_digests_reviewed": True,
        "calibration_holdout_qualification_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
    }
    value.update(updates)
    return HydrogenFatigueProviderEvidenceAssessment(**value)


def test_qualified_curve_is_preserved_without_life_integration():
    calculated = hydrogen_fatigue_provider_evidence(payload())
    assert calculated.status == "computed"
    assert calculated.values["declared_applicability_outcome"] == "within_support"
    assert [row["point_id"] for row in calculated.values["provider_growth_points"]] == [
        "point-1",
        "point-2",
    ]
    assert calculated.values["holdout_independence_group_ids"] == ["ind-hold"]


def test_condition_or_delta_k_outside_support_is_out_of_scope():
    assessment = payload()
    assert hydrogen_fatigue_provider_evidence(payload(frequency_Hz=20.0)).status == "needs_data"

    outside_point = assessment.provider_result.points[1].model_copy(update={"delta_k_value": 40.0})
    outside_result = assessment.provider_result.model_copy(
        update={"points": (assessment.provider_result.points[0], outside_point)}
    )
    calculated = hydrogen_fatigue_provider_evidence(
        assessment.model_copy(update={"provider_result": outside_result})
    )
    assert calculated.status == "out_of_scope"
    assert calculated.values["outside_delta_k_point_ids"] == ["point-2"]


def test_pressure_fugacity_identity_is_not_converted():
    calculated = hydrogen_fatigue_provider_evidence(
        payload(exposure_quantity_kind="fugacity", exposure_quantity_unit_token="Pa_fugacity")
    )
    assert calculated.status == "out_of_scope"
    assert calculated.values["identity_matching_envelope_ids"] == []


def test_provider_mismatch_or_missing_holdout_needs_data():
    assert (
        hydrogen_fatigue_provider_evidence(
            payload(provider_result=provider_result(provider_revision="other"))
        ).status
        == "needs_data"
    )
    only_calibration = envelope(
        qualification_evidence=(qualification_record("cal-1", "calibration", "source-cal", "ind-cal"),)
    )
    calculated = hydrogen_fatigue_provider_evidence(payload(candidate_envelopes=(only_calibration,)))
    assert calculated.status == "needs_data"
    assert calculated.values["qualification_partition_counts_sufficient"] is False


def test_curve_order_and_context_identity_are_enforced():
    bad_points = (
        provider_result()["points"][1],
        provider_result()["points"][0],
    )
    with pytest.raises(ValueError, match="strictly increasing"):
        payload(provider_result=provider_result(points=bad_points))

    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.hydrogen_fatigue_provider_evidence",
            payload(),
            RunContext(asset_id="other", location_id="crack-1", time_basis="authored"),
        )
