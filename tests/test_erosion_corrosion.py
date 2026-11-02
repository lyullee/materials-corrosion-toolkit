import pytest

from matintegrity.models.erosion_corrosion import (
    ErosionCorrosionLoss,
    erosion_corrosion_loss,
)

EVIDENCE = {
    "source_id": "caller-erosion-corrosion",
    "origin": "model_prediction",
    "citation": "caller-controlled calibrated loss-rate record",
}
DIGEST = "1" * 64


def support(**updates):
    values = {
        "provider_support_id": "support-1",
        "provider_id": "provider-1",
        "provider_version": "1",
        "provider_model_digest": DIGEST,
        "material_condition_id": "material-1",
        "geometry_id": "elbow-geometry-1",
        "location_id": "elbow-extrados-1",
        "minimum_flow_velocity_m_s": 0.0,
        "maximum_flow_velocity_m_s": 10.0,
        "particle_loading_unit": "kg/m^3",
        "minimum_particle_loading": 0.0,
        "maximum_particle_loading": 1.0,
        "supported_particle_size_descriptors": ("distribution-a",),
        "supported_fluid_chemistry_descriptors": ("chemistry-a",),
        "minimum_temperature_K": 280.0,
        "maximum_temperature_K": 350.0,
        "minimum_calibrated_net_loss_rate_m_s": 0.0,
        "maximum_calibrated_net_loss_rate_m_s": 1e-8,
        "maximum_cumulative_exposure_s": 3000.0,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def interval(identifier, start, end, rate=1e-9, **updates):
    values = {
        "interval_id": identifier,
        "provider_support_id": "support-1",
        "start_time_s": start,
        "end_time_s": end,
        "flow_velocity_m_s": 5.0,
        "particle_loading": 0.2,
        "particle_loading_unit": "kg/m^3",
        "particle_size_descriptor": "distribution-a",
        "fluid_chemistry_descriptor": "chemistry-a",
        "temperature_K": 310.0,
        "calibrated_net_loss_rate_m_s": rate,
        "provider_state_digest": "2" * 64,
        "record_valid": True,
        "provider_state_reviewed": True,
        "rate_calibration_reviewed": True,
        "evidence": (EVIDENCE,),
    }
    values.update(updates)
    return values


def request(**updates):
    values = {
        "assessment_id": "erosion-corrosion-1",
        "asset_id": "asset-1",
        "location_id": "elbow-extrados-1",
        "physical_scope_id": "grid-cell-a",
        "clock_id": "service-clock-1",
        "material_condition_id": "material-1",
        "geometry_condition_id": "geometry-condition-1",
        "geometry_id": "elbow-geometry-1",
        "intervals": (interval("i1", 0.0, 1000.0), interval("i2", 1000.0, 2000.0, 2e-9)),
        "provider_support": support(),
        "material_geometry_and_location_reviewed": True,
        "interval_clock_and_units_reviewed": True,
        "flow_particle_and_chemistry_records_reviewed": True,
        "provider_identity_and_support_reviewed": True,
        "net_loss_rates_reviewed": True,
    }
    values.update(updates)
    return ErosionCorrosionLoss(**values)


def test_supported_piecewise_constant_rates_integrate_exactly():
    result = erosion_corrosion_loss(request())
    assert result.status == "computed"
    assert result.values["cumulative_thickness_loss_m"] == pytest.approx(3e-6)
    assert result.values["interval_loss"][0]["thickness_loss_m"] == pytest.approx(1e-6)


def test_reviewed_state_outside_support_withholds_integration():
    result = erosion_corrosion_loss(request(intervals=(interval("i1", 0.0, 1000.0, flow_velocity_m_s=20.0),)))
    assert result.status == "out_of_scope"
    assert result.values["outside_support_interval_ids"] == ["i1"]
    assert "cumulative_thickness_loss_m" not in result.values


def test_invalid_unit_identity_provider_or_review_needs_data():
    assert (
        erosion_corrosion_loss(
            request(intervals=(interval("i1", 0.0, 10.0, particle_loading_unit="mg/L"),))
        ).status
        == "needs_data"
    )
    assert erosion_corrosion_loss(request(location_id="different")).status == "needs_data"
    assert (
        erosion_corrosion_loss(request(intervals=(interval("i1", 0.0, 10.0, record_valid=False),))).status
        == "needs_data"
    )
    assert erosion_corrosion_loss(request(net_loss_rates_reviewed=False)).status == "needs_data"


def test_interval_clock_and_support_bounds_are_strict():
    with pytest.raises(ValueError, match="cannot overlap"):
        request(intervals=(interval("i1", 0.0, 20.0), interval("i2", 10.0, 30.0)))
    with pytest.raises(ValueError, match="velocity provider-support"):
        request(provider_support=support(minimum_flow_velocity_m_s=20.0))
