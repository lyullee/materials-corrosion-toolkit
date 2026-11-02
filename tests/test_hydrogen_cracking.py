import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.hydrogen_cracking import (
    HydrogenCrackingProviderEvidence,
    hydrogen_cracking_provider_evidence,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def qualification(record_id, specimen, group, partition):
    return {
        "evidence_record_id": record_id,
        "physical_specimen_id": specimen,
        "source_group_id": group,
        "partition": partition,
        "supported_toughness_endpoint_definition_ids": ("K-endpoint-1",),
        "supported_driving_metric_definition_ids": ("K-driving-1",),
        "provider_id": "qualification-provider",
        "provider_revision": "1",
        "provider_state_digest": DIGEST_A,
        "result_digest": DIGEST_B,
        "record_valid": True,
        "supports_declared_envelope": True,
        "evidence": (EVIDENCE,),
    }


def envelope(**updates):
    value = {
        "envelope_id": "envelope-1",
        "material_condition_id": "material-1",
        "heat_id": "heat-1",
        "hydrogen_state_id": "hydrogen-gas-1",
        "pressure_or_fugacity_basis": "absolute_fugacity",
        "pressure_or_fugacity_unit_token": "Pa",
        "minimum_pressure_or_fugacity_value": 100000.0,
        "maximum_pressure_or_fugacity_value": 5000000.0,
        "minimum_temperature_K": 280.0,
        "maximum_temperature_K": 350.0,
        "maximum_cumulative_exposure_s": 10000.0,
        "supported_crack_geometry_ids": ("crack-geometry-1",),
        "supported_crack_location_ids": ("location-geometry-1",),
        "supported_crack_orientation_ids": ("orientation-1",),
        "toughness_endpoint_kind": "K",
        "toughness_endpoint_definition_id": "K-endpoint-1",
        "toughness_unit_token": "Pa*sqrt(m)",
        "minimum_supported_toughness_value": 10000000.0,
        "maximum_supported_toughness_value": 200000000.0,
        "maximum_toughness_expanded_uncertainty": 10000000.0,
        "toughness_provider_id": "toughness-provider",
        "toughness_provider_revision": "1",
        "toughness_provider_state_digest": DIGEST_A,
        "driving_metric_kind": "K",
        "driving_metric_definition_id": "K-driving-1",
        "driving_unit_token": "Pa*sqrt(m)",
        "minimum_supported_driving_value": 0.0,
        "maximum_supported_driving_value": 150000000.0,
        "maximum_driving_expanded_uncertainty": 10000000.0,
        "driving_provider_id": "driving-provider",
        "driving_provider_revision": "1",
        "driving_provider_configuration_digest": DIGEST_B,
        "qualification_evidence": (
            qualification("q-cal", "specimen-cal", "source-cal", "calibration"),
            qualification("q-hold", "specimen-hold", "source-hold", "holdout"),
        ),
        "qualification_basis": "authored qualification",
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return value


def payload(**updates):
    value = {
        "assessment_id": "assessment-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "clock_id": "clock-1",
        "material_condition_id": "material-1",
        "heat_id": "heat-1",
        "crack_geometry_id": "crack-geometry-1",
        "crack_location_id": "location-geometry-1",
        "crack_orientation_id": "orientation-1",
        "exposure_intervals": (
            {
                "interval_id": "interval-1",
                "start_time_s": 0.0,
                "end_time_s": 3600.0,
                "hydrogen_state_id": "hydrogen-gas-1",
                "pressure_or_fugacity_basis": "absolute_fugacity",
                "pressure_or_fugacity_value": 2000000.0,
                "pressure_or_fugacity_unit_token": "Pa",
                "temperature_K": 300.0,
                "record_digest": DIGEST_A,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "toughness_result": {
            "result_id": "toughness-1",
            "physical_specimen_id": "specimen-application",
            "source_group_id": "source-application",
            "partition": "application",
            "endpoint_kind": "K",
            "endpoint_definition_id": "K-endpoint-1",
            "reported_value": 100000000.0,
            "unit_token": "Pa*sqrt(m)",
            "expanded_uncertainty": 5000000.0,
            "provider_id": "toughness-provider",
            "provider_revision": "1",
            "provider_state_digest": DIGEST_A,
            "input_digest": DIGEST_B,
            "result_digest": DIGEST_C,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
        "crack_driving_result": {
            "result_id": "driving-1",
            "load_case_id": "load-case-1",
            "metric_kind": "K",
            "metric_definition_id": "K-driving-1",
            "reported_value": 50000000.0,
            "unit_token": "Pa*sqrt(m)",
            "expanded_uncertainty": 5000000.0,
            "provider_id": "driving-provider",
            "provider_revision": "1",
            "provider_configuration_digest": DIGEST_B,
            "input_digest": DIGEST_A,
            "result_digest": DIGEST_C,
            "record_valid": True,
            "evidence": (EVIDENCE,),
        },
        "candidate_envelopes": (envelope(),),
        "material_condition_and_heat_reviewed": True,
        "hydrogen_state_pressure_or_fugacity_basis_reviewed": True,
        "temperature_exposure_clock_reviewed": True,
        "crack_geometry_location_and_orientation_reviewed": True,
        "toughness_endpoint_units_uncertainty_and_provider_reviewed": True,
        "driving_metric_load_case_units_and_provider_reviewed": True,
        "physical_specimens_source_groups_and_partitions_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return HydrogenCrackingProviderEvidence(**value)


def test_reviewed_results_are_within_support_without_acceptance_inference():
    result = hydrogen_cracking_provider_evidence(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["cumulative_exposure_s"] == pytest.approx(3600.0)


def test_exposure_and_driving_ranges_exit_support():
    base = payload()
    exposure = base.exposure_intervals[0].model_copy(update={"temperature_K": 400.0})
    driving = base.crack_driving_result.model_copy(update={"reported_value": 200000000.0})
    result = hydrogen_cracking_provider_evidence(
        base.model_copy(update={"exposure_intervals": (exposure,), "crack_driving_result": driving})
    )
    assert result.status == "out_of_scope"
    assert result.values["outside_support_reasons"] == [
        "hydrogen_exposure_range",
        "driving_result_range_or_uncertainty",
    ]


def test_missing_review_or_mixed_toughness_endpoint_needs_data():
    assert (
        hydrogen_cracking_provider_evidence(payload(provider_lineage_and_digests_reviewed=False)).status
        == "needs_data"
    )
    base = payload()
    mixed = base.toughness_result.model_copy(
        update={"endpoint_kind": "J", "endpoint_definition_id": "J-endpoint", "unit_token": "J/m^2"}
    )
    result = hydrogen_cracking_provider_evidence(base.model_copy(update={"toughness_result": mixed}))
    assert result.status == "needs_data"
    assert result.values["toughness_endpoint_and_provider_compatible"] is False


def test_partition_leakage_and_context_identity_are_enforced():
    with pytest.raises(ValueError, match="disjoint"):
        payload(
            candidate_envelopes=(
                envelope(
                    qualification_evidence=(
                        qualification("q-cal", "specimen-cal", "same-source", "calibration"),
                        qualification("q-hold", "specimen-hold", "same-source", "holdout"),
                    )
                ),
            )
        )
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.hydrogen_cracking_provider_evidence",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
