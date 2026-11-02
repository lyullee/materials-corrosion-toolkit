import pytest

from matintegrity.adapters import under_insulation_inputs_from_condensation_result
from matintegrity.contracts import Evidence, RunContext
from matintegrity.models.insulation_condensation import (
    InsulationCondensationExposure,
    InsulationCondensationInterval,
)
from matintegrity.models.under_insulation import (
    DeclaredUnderInsulationExposure,
    UnderInsulationExposureHistory,
    under_insulation_exposure_history,
)
from matintegrity.registry import default_registry

EVIDENCE = Evidence(source_id="synthetic", origin="synthetic", citation="adapter test")


def condensation_result(*, reviewed=True):
    model = InsulationCondensationExposure(
        assessment_id="case",
        asset_id="asset",
        location_id="location",
        insulation_system_id="system",
        outer_surface_location_definition="outer weather barrier",
        dew_point_definition="reviewed ambient dew point",
        dew_point_provider_state_digest="a" * 64,
        clock_id="clock",
        horizon_start_s=0.0,
        horizon_end_s=20.0,
        intervals=(
            InsulationCondensationInterval(
                interval_id="cold",
                start_time_s=0.0,
                end_time_s=10.0,
                outer_surface_temperature_K=280.0,
                ambient_dew_point_temperature_K=281.0,
                weather_barrier_state_id="open",
                record_valid=True,
                evidence=(EVIDENCE,),
            ),
            InsulationCondensationInterval(
                interval_id="warm",
                start_time_s=10.0,
                end_time_s=20.0,
                outer_surface_temperature_K=290.0,
                ambient_dew_point_temperature_K=281.0,
                weather_barrier_state_id="open",
                record_valid=True,
                evidence=(EVIDENCE,),
            ),
        ),
        barrier_states_allowing_external_moisture=("open",),
        temperature_measurement_uncertainty_K=0.2,
        dew_point_uncertainty_K=0.2,
        temperature_and_dew_point_units_reviewed=reviewed,
        surface_location_reviewed=True,
        clock_and_coverage_reviewed=True,
        weather_barrier_mapping_reviewed=True,
        uncertainty_basis_reviewed=True,
        evidence=(EVIDENCE,),
    )
    return default_registry().run(
        "fabrication.insulation_condensation_exposure",
        model,
        RunContext(asset_id="asset", location_id="location", time_basis="elapsed seconds"),
    )


def definition():
    return DeclaredUnderInsulationExposure(
        definition_id="caller-cui-screen",
        minimum_surface_temperature_K=270.0,
        maximum_surface_temperature_K=300.0,
        included_wetness_state_ids=("thermodynamic_condensation_possible",),
        included_insulation_condition_ids=("damaged",),
        definition_basis="caller screening definition",
        evidence=(EVIDENCE,),
    )


def test_adapter_preserves_scope_digest_and_conservative_state():
    inputs = under_insulation_inputs_from_condensation_result(
        condensation_result(),
        record_id="cui-from-condensation",
        insulation_condition_id_by_interval={"cold": "damaged", "warm": "damaged"},
        exposure_definition=definition(),
    )
    model = UnderInsulationExposureHistory.model_validate(inputs)
    result = under_insulation_exposure_history(model)
    assert result.status == "computed"
    assert result.values["classified_exposure_duration_s"] == 10.0
    assert result.values["classified_exposure_interval_ids"] == ["cold"]
    assert len(result.values["source_result_digest"]) == 64
    assert "not measured" in result.values["wetness_state_semantics"]


def test_adapter_rejects_incomplete_condensation_or_mapping():
    with pytest.raises(ValueError, match="complete computed"):
        under_insulation_inputs_from_condensation_result(
            condensation_result(reviewed=False),
            record_id="x",
            insulation_condition_id_by_interval={"cold": "damaged", "warm": "damaged"},
            exposure_definition=definition(),
        )
    with pytest.raises(ValueError, match="cover exactly"):
        under_insulation_inputs_from_condensation_result(
            condensation_result(),
            record_id="x",
            insulation_condition_id_by_interval={"cold": "damaged"},
            exposure_definition=definition(),
        )


def test_adapter_rejects_wrong_result_type():
    with pytest.raises(ValueError, match="condensation model"):
        other = default_registry().run(
            "thermal.lumped_temperature",
            {
                "initial_temperature_K": 300.0,
                "ambient_temperature_K": 290.0,
                "heat_capacity_J_K": 1000.0,
                "surface_area_m2": 1.0,
                "convection_W_m2_K": 10.0,
                "solid_conductivity_W_m_K": 50.0,
                "characteristic_length_m": 0.01,
                "maximum_declared_biot": 0.1,
                "exposure_s": 1.0,
            },
            RunContext(asset_id="asset", location_id="location", time_basis="elapsed seconds"),
        )
        under_insulation_inputs_from_condensation_result(
            other,
            record_id="x",
            insulation_condition_id_by_interval={},
            exposure_definition=definition(),
        )
