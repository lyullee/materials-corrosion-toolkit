import json

import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.atmospheric_multiyear import (
    AtmosphericMultiYearLossHistory,
    atmospheric_multi_year_loss_history,
    specifications,
)
from matintegrity.registry import ModelRegistry

E = {"source_id": "authored", "origin": "synthetic", "citation": "authored test"}
D = "a" * 64


def payload(**updates):
    rec = lambda i, p, g: {
        "record_id": i,
        "partition": p,
        "physical_specimen_id": "s-" + i,
        "source_group_id": g,
        "exposure_zone_id": "zone-1",
        "material_condition_id": "condition-1",
        "surface_condition_id": "surface-1",
        "climate_pollutant_descriptor_id": "climate-1",
        "provider_result_digest": D,
        "record_valid": True,
        "evidence": [E],
    }
    v = {
        "history_id": "h-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "physical_scope_id": "scope-1",
        "exposure_zone_id": "zone-1",
        "material_condition_id": "condition-1",
        "surface_condition_id": "surface-1",
        "climate_pollutant_descriptor_id": "climate-1",
        "first_year_loss": 0.0001,
        "loss_unit_token": "m",
        "first_year_loss_provider_id": "provider-first",
        "first_year_loss_result_digest": D,
        "time_exponent": 0.6,
        "elapsed_time_years": [0.0, 1.0, 2.0, 5.0],
        "transfer_envelope": {
            "envelope_id": "e-1",
            "exposure_zone_id": "zone-1",
            "material_condition_id": "condition-1",
            "surface_condition_id": "surface-1",
            "climate_pollutant_descriptor_id": "climate-1",
            "loss_unit_token": "m",
            "time_unit_token": "year",
            "minimum_first_year_loss": 0.00001,
            "maximum_first_year_loss": 0.001,
            "minimum_time_exponent": 0.2,
            "maximum_time_exponent": 1.0,
            "maximum_supported_elapsed_years": 10.0,
            "provider_id": "provider-transfer",
            "provider_revision": "1",
            "provider_state_digest": D,
            "qualification_records": [rec("1", "calibration", "g1"), rec("2", "holdout", "g2")],
            "qualification_basis": "authored",
            "evidence": [E],
        },
        "exposure_material_surface_and_environment_identity_reviewed": True,
        "first_year_endpoint_value_and_unit_reviewed": True,
        "time_exponent_definition_and_support_reviewed": True,
        "clock_and_ordered_time_knots_reviewed": True,
        "provider_lineage_and_digests_reviewed": True,
        "qualification_partitions_and_source_groups_reviewed": True,
        "transfer_envelope_authority_reviewed": True,
        "evidence": [E],
    }
    v.update(updates)
    return AtmosphericMultiYearLossHistory.model_validate_json(json.dumps(v))


def test_history():
    r = atmospheric_multi_year_loss_history(payload())
    assert r.status == "computed"
    assert r.values["cumulative_loss"][1] == pytest.approx(0.0001)


def test_outside():
    assert atmospheric_multi_year_loss_history(payload(time_exponent=1.2)).status == "out_of_scope"


def test_needs():
    assert (
        atmospheric_multi_year_loss_history(payload(first_year_endpoint_value_and_unit_reviewed=False)).status
        == "needs_data"
    )


def test_knots_context():
    with pytest.raises(ValueError, match="first-year anchor"):
        payload(elapsed_time_years=[0.0, 2.0])
    r = ModelRegistry()
    r.register(specifications()[0])
    with pytest.raises(ValueError, match="must match"):
        r.run(
            "degradation.atmospheric_multi_year_loss_history",
            payload(),
            RunContext(asset_id="other", location_id="location-1", time_basis="years"),
        )
