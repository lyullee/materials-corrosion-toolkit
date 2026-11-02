import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.pull_off_adhesion import (
    PullOffAdhesionCalibration,
    pull_off_adhesion_calibration,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64


def observation(identifier, partition, specimen, source, force, provider_stress, difference_shift=0.0):
    area = 0.0001
    force_area_stress = force / area
    return {
        "observation_id": identifier,
        "physical_specimen_id": specimen,
        "source_group_id": source,
        "independence_group_id": f"ind-{specimen}",
        "partition": partition,
        "dolly_id": f"dolly-{identifier}",
        "physical_location_id": f"location-{identifier}",
        "location_definition": "authored coating location",
        "coating_layer_stack_id": "layers-1",
        "substrate_condition_id": "substrate-1",
        "surface_preparation_id": "prep-1",
        "cure_condition_id": "cure-1",
        "exposure_condition_id": "exposure-1",
        "adhesive_condition_id": "adhesive-1",
        "caller_break_mode_id": "mixed-caller-mode",
        "break_mode_components": (
            {
                "component_id": "component-a",
                "caller_descriptor": "caller layer A",
                "reported_area_fraction": 0.6,
            },
            {
                "component_id": "component-b",
                "caller_descriptor": "caller layer B",
                "reported_area_fraction": 0.4,
            },
        ),
        "measurement_basis": "both",
        "force_calibration_id": "force-cal-1",
        "pull_force_N": force,
        "pull_force_unit_token": "N",
        "pull_force_expanded_uncertainty_N": 2.0,
        "dolly_area_m2": area,
        "dolly_area_unit_token": "m^2",
        "dolly_area_expanded_uncertainty_m2": 1e-6,
        "provider_stress_Pa": provider_stress or force_area_stress + 100000.0 + difference_shift,
        "provider_stress_unit_token": "Pa",
        "provider_stress_expanded_uncertainty_Pa": 50000.0,
        "provider_id": "provider-1",
        "provider_revision": "1",
        "provider_configuration_digest": DIGEST_A,
        "input_digest": DIGEST_B,
        "result_digest": DIGEST_C,
        "nominal_weight": 1.0,
        "record_valid": True,
        "evidence": (EVIDENCE,),
    }


def observations():
    return (
        observation("cal-1", "calibration", "spec-cal-1", "source-cal-a", 400.0, None, -20000.0),
        observation("cal-2", "calibration", "spec-cal-2", "source-cal-a", 450.0, None, 30000.0),
        observation("cal-3", "calibration", "spec-cal-3", "source-cal-b", 500.0, None, -10000.0),
        observation("cal-4", "calibration", "spec-cal-4", "source-cal-b", 550.0, None, 10000.0),
        observation("hold-1", "holdout", "spec-hold-1", "source-hold", 425.0, None, 20000.0),
        observation("hold-2", "holdout", "spec-hold-2", "source-hold", 525.0, None, -20000.0),
    )


def payload(**updates):
    value = {
        "calibration_id": "pull-off-1",
        "asset_id": "asset-1",
        "location_id": "coating-scope-1",
        "physical_scope_id": "coating-physical-scope-1",
        "coating_system_id": "coating-system-1",
        "coating_layer_stack_id": "layers-1",
        "substrate_condition_id": "substrate-1",
        "surface_preparation_id": "prep-1",
        "cure_condition_id": "cure-1",
        "exposure_condition_id": "exposure-1",
        "adhesive_condition_id": "adhesive-1",
        "force_calibrations": (
            {
                "calibration_id": "force-cal-1",
                "force_instrument_id": "force-instrument-1",
                "instrument_configuration_id": "configuration-1",
                "force_unit_token": "N",
                "minimum_supported_force_N": 100.0,
                "maximum_supported_force_N": 1000.0,
                "expanded_uncertainty_N": 2.0,
                "provider_id": "calibration-provider",
                "provider_revision": "1",
                "configuration_digest": DIGEST_A,
                "result_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "observations": observations(),
        "caller_thresholds": (
            {
                "threshold_id": "threshold-1",
                "stress_basis": "force_area",
                "minimum_stress_Pa": 3e6,
                "authority_basis": "authored caller threshold",
                "evidence": (EVIDENCE,),
            },
        ),
        "minimum_paired_calibration_record_count": 3,
        "dollies_locations_layers_and_substrate_reviewed": True,
        "surface_preparation_cure_exposure_and_adhesive_reviewed": True,
        "force_area_and_provider_stress_units_reviewed": True,
        "force_calibration_and_uncertainty_reviewed": True,
        "break_mode_descriptors_and_fractions_reviewed": True,
        "specimen_source_and_independence_partitions_reviewed": True,
        "provider_revision_configuration_and_digests_reviewed": True,
        "caller_threshold_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return PullOffAdhesionCalibration(**value)


def test_force_area_stress_provider_bias_and_threshold_margin_compute():
    result = pull_off_adhesion_calibration(payload())
    assert result.status == "computed"
    assert result.values["provider_minus_force_area_bias_Pa"] == pytest.approx(102500.0)
    first = result.values["observation_rows"][0]
    assert first["force_area_stress_Pa"] == pytest.approx(4e6)
    assert first["break_mode_components"][0]["reported_area_fraction"] == pytest.approx(0.6)
    assert result.values["caller_threshold_margins"][0][
        "signed_margin_reported_minus_threshold_Pa"
    ] == pytest.approx(1e6)


def test_missing_review_or_identity_mismatch_needs_data():
    assert (
        pull_off_adhesion_calibration(payload(break_mode_descriptors_and_fractions_reviewed=False)).status
        == "needs_data"
    )
    rows = list(observations())
    rows[0] = {**rows[0], "cure_condition_id": "other"}
    result = pull_off_adhesion_calibration(payload(observations=tuple(rows)))
    assert result.status == "needs_data"
    assert result.values["identity_mismatch_observation_ids"] == ["cal-1"]


def test_force_outside_calibration_support_is_not_extrapolated():
    rows = list(observations())
    rows[0] = observation("cal-1", "calibration", "spec-cal-1", "source-cal-a", 1200.0, None)
    result = pull_off_adhesion_calibration(payload(observations=tuple(rows)))
    assert result.status == "out_of_scope"
    assert result.values["outside_force_calibration_support_observation_ids"] == ["cal-1"]


def test_partition_leakage_and_context_identity_are_enforced():
    rows = list(observations())
    rows[4] = {**rows[4], "source_group_id": "source-cal-a"}
    with pytest.raises(ValueError, match="source group"):
        payload(observations=tuple(rows))
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "fabrication.pull_off_adhesion_calibration",
            payload(),
            RunContext(asset_id="other", location_id="coating-scope-1", time_basis="authored"),
        )
