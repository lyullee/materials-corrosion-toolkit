import math

from matintegrity.models.fire_protection import (
    FireProtectionBoundaryHistory,
    fire_protection_boundary_history,
)
from matintegrity.models.thermal_transient import ThermalBoundary

SHA = "a" * 64
EVIDENCE = {
    "source_id": "authored-fire-transfer",
    "origin": "user_declared",
    "citation": "Caller-reviewed fire-protection transfer record",
}


def payload(**updates):
    values = {
        "history_id": "fire-01",
        "asset_id": "asset-01",
        "location_id": "shell-east",
        "clock_id": "fire-clock",
        "thermal_boundary_id": "outside-shell",
        "elapsed_time_s": [0.0, 10.0],
        "incident_heat_flux_W_m2": [100.0, 200.0],
        "transmitted_flux_fraction": [0.2, 0.4],
        "protection_state_ids": ["intact", "intact"],
        "transfer_record_digests": [SHA, SHA],
        "exposed_area_m2": 2.0,
        "transfer_support": {
            "support_id": "support-01",
            "provider_id": "provider-01",
            "provider_version": "1",
            "provider_digest": SHA,
            "incident_flux_min_W_m2": 0.0,
            "incident_flux_max_W_m2": 300.0,
            "supported_protection_state_ids": ["intact"],
            "calibration_basis": "Caller-owned calibration record",
            "evidence": [EVIDENCE],
        },
        "clock_alignment_reviewed": True,
        "incident_flux_basis_reviewed": True,
        "protection_state_history_reviewed": True,
        "transfer_provider_and_calibration_reviewed": True,
        "thermal_boundary_orientation_reviewed": True,
        "evidence": [EVIDENCE],
    }
    values.update(updates)
    return values


def test_exact_product_integral_and_thermal_boundary_contract():
    result = fire_protection_boundary_history(FireProtectionBoundaryHistory(**payload()))
    assert result.status == "computed"
    assert result.values["transmitted_heat_flux_into_solid_W_m2"] == [20.0, 80.0]
    assert math.isclose(result.values["total_transmitted_energy_J_m2"], 1400.0 / 3.0)
    ThermalBoundary(**result.values["thermal_boundary_contract"])


def test_outside_declared_support_emits_no_boundary():
    result = fire_protection_boundary_history(
        FireProtectionBoundaryHistory(**payload(protection_state_ids=["intact", "damaged"]))
    )
    assert result.status == "out_of_scope"
    assert "thermal_boundary_contract" not in result.values


def test_incomplete_review_emits_no_boundary():
    result = fire_protection_boundary_history(
        FireProtectionBoundaryHistory(**payload(thermal_boundary_orientation_reviewed=False))
    )
    assert result.status == "needs_data"
    assert "thermal_boundary_contract" not in result.values
