import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.high_temperature_hydrogen import (
    HighTemperatureHydrogenApplicability,
    high_temperature_hydrogen_applicability,
    specifications,
)
from matintegrity.registry import ModelRegistry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "authored hydrogen test"}
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64
DIGEST_C = "c" * 64
DIGEST_D = "d" * 64


def payload(**updates):
    value = {
        "assessment_id": "hth-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "clock_id": "clock-1",
        "material_condition_id": "condition-1",
        "heat_treatment_id": "treatment-1",
        "composition": (
            {
                "constituent_id": "constituent-a",
                "reported_value": 0.01,
                "unit": "mass_fraction",
                "result_digest": DIGEST_A,
                "evidence": (EVIDENCE,),
            },
        ),
        "exposures": (
            {
                "interval_id": "interval-1",
                "start_time_s": 0.0,
                "end_time_s": 3600.0,
                "hydrogen_species": "H2",
                "pressure_basis": "absolute_partial_pressure",
                "hydrogen_partial_pressure_Pa_abs": 2e6,
                "temperature_K": 700.0,
                "record_digest": DIGEST_B,
                "record_valid": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "microstructure_evidence": (
            {
                "record_id": "micro-1",
                "physical_source_group_id": "sample-1",
                "inspection_location": "caller mapped location",
                "inspection_method_id": "inspection-1",
                "provider_id": "provider-1",
                "provider_version": "1.0",
                "provider_state_digest": DIGEST_C,
                "microstructure_descriptor": "caller-descriptor-a",
                "result_digest": DIGEST_D,
                "record_available": True,
                "evidence": (EVIDENCE,),
            },
        ),
        "qualification_envelope": {
            "envelope_id": "envelope-1",
            "material_condition_id": "condition-1",
            "heat_treatment_id": "treatment-1",
            "supported_hydrogen_species": ("H2",),
            "pressure_basis": "absolute_partial_pressure",
            "minimum_hydrogen_partial_pressure_Pa_abs": 1e5,
            "maximum_hydrogen_partial_pressure_Pa_abs": 3e6,
            "minimum_temperature_K": 600.0,
            "maximum_temperature_K": 750.0,
            "maximum_cumulative_exposure_s": 7200.0,
            "composition_support": (
                {
                    "constituent_id": "constituent-a",
                    "unit": "mass_fraction",
                    "minimum_supported_value": 0.005,
                    "maximum_supported_value": 0.02,
                },
            ),
            "supported_microstructure_descriptors": ("caller-descriptor-a",),
            "supported_inspection_method_ids": ("inspection-1",),
            "minimum_physical_source_group_count": 1,
            "provider_qualification": {
                "qualification_id": "qualification-1",
                "provider_id": "provider-1",
                "provider_version": "1.0",
                "provider_state_digest": DIGEST_C,
                "qualification_result_digest": DIGEST_D,
                "calibration_dataset_digest": DIGEST_A,
                "holdout_dataset_digest": DIGEST_B,
                "calibration_physical_source_group_count": 8,
                "holdout_physical_source_group_count": 3,
                "calibration_and_holdout_independent": True,
                "validation_metric_definition": "caller mismatch fraction",
                "validation_metric_value": 0.05,
                "validation_metric_unit": "1",
                "maximum_supported_validation_metric": 0.10,
                "qualification_basis": "caller validation plan",
                "evidence": (EVIDENCE,),
            },
            "applicability_basis": "caller qualification programme",
            "evidence": (EVIDENCE,),
        },
        "material_identity_composition_and_heat_treatment_reviewed": True,
        "hydrogen_species_and_absolute_partial_pressure_reviewed": True,
        "temperature_pressure_clock_and_time_reviewed": True,
        "microstructure_locations_and_source_groups_reviewed": True,
        "inspection_method_and_provider_lineage_reviewed": True,
        "record_and_result_digests_reviewed": True,
        "missingness_reviewed": True,
        "qualification_envelope_authority_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    value.update(updates)
    return HighTemperatureHydrogenApplicability(**value)


def test_reviewed_history_is_within_caller_owned_support():
    result = high_temperature_hydrogen_applicability(payload())
    assert result.status == "computed"
    assert result.values["declared_applicability_outcome"] == "within_support"
    assert result.values["cumulative_exposure_s"] == pytest.approx(3600.0)


def test_pressure_outside_support_is_out_of_scope_without_damage_inference():
    base = payload()
    exposure = base.exposures[0].model_copy(update={"hydrogen_partial_pressure_Pa_abs": 4e6})
    result = high_temperature_hydrogen_applicability(base.model_copy(update={"exposures": (exposure,)}))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_exposure_ids"] == ["interval-1"]


def test_missing_review_or_inspection_record_needs_data():
    assert (
        high_temperature_hydrogen_applicability(payload(record_and_result_digests_reviewed=False)).status
        == "needs_data"
    )
    base = payload()
    unavailable = base.microstructure_evidence[0].model_copy(
        update={
            "microstructure_descriptor": None,
            "result_digest": None,
            "record_available": False,
            "missing_basis": "inspection result unavailable",
        }
    )
    assert (
        high_temperature_hydrogen_applicability(
            base.model_copy(update={"microstructure_evidence": (unavailable,)})
        ).status
        == "needs_data"
    )


def test_context_identity_is_enforced():
    registry = ModelRegistry()
    registry.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "degradation.high_temperature_hydrogen_applicability",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="authored"),
        )
