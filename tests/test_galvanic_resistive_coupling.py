import json

import pytest

from matintegrity.models.galvanic_resistive_coupling import (
    ResistiveGalvanicCoupling,
    resistive_galvanic_coupling,
    specifications,
)

EVIDENCE = {
    "source_id": "authored-resistive-fixture",
    "origin": "synthetic",
    "citation": "Independent finite-resistance circuit fixture",
}
DIGEST = "b" * 64


def curve(curve_id, currents):
    return {
        "curve_id": curve_id,
        "surface_condition_id": f"surface-{curve_id}",
        "protocol_id": "steady-branch",
        "electrolyte_id": "bath",
        "reference_electrode_id": "reference",
        "temperature_K": 298.15,
        "point_ids": [f"{curve_id}-left", f"{curve_id}-right"],
        "potential_V": [-1.0, 0.0],
        "signed_net_current_density_A_m2": currents,
        "evidence": [EVIDENCE],
    }


def request():
    return {
        "assessment_id": "resistive-couple-1",
        "asset_id": "asset-1",
        "location_id": "location-1",
        "environment": {
            "environment_id": "environment-1",
            "electrolyte_id": "bath",
            "electrolyte_description": "authored electrolyte",
            "temperature_K": 298.15,
            "reference_electrode_id": "reference",
            "condition_digest": DIGEST,
        },
        "electrodes": [
            {
                "electrode_id": "electrode-a",
                "metal_id": "metal-a",
                "material_condition_id": "condition-a",
                "exposed_area_m2": 1.0,
                "polarization_curve": curve("curve-a", [-2.0, 8.0]),
                "curve_provider_id": "provider-a",
                "curve_provider_revision": "1",
                "curve_input_digest": DIGEST,
                "curve_result_digest": DIGEST,
                "curve_support_reviewed": True,
            },
            {
                "electrode_id": "electrode-b",
                "metal_id": "metal-b",
                "material_condition_id": "condition-b",
                "exposed_area_m2": 1.0,
                "polarization_curve": curve("curve-b", [-7.0, 3.0]),
                "curve_provider_id": "provider-b",
                "curve_provider_revision": "2",
                "curve_input_digest": DIGEST,
                "curve_result_digest": DIGEST,
                "curve_support_reviewed": True,
            },
        ],
        "connection": {
            "connection_id": "connection-1",
            "components": [
                {
                    "component_id": "electrolyte-path",
                    "component_kind": "electrolyte",
                    "resistance_ohm": 0.08,
                    "basis": "caller four-terminal result",
                    "evidence": [EVIDENCE],
                },
                {
                    "component_id": "contact-path",
                    "component_kind": "contact",
                    "resistance_ohm": 0.02,
                    "basis": "caller contact measurement",
                    "evidence": [EVIDENCE],
                },
            ],
            "declared_total_series_resistance_ohm": 0.1,
            "component_sum_tolerance_ohm": 1e-12,
            "connection_reviewed": True,
        },
        "solver_id": "matintegrity.two_electrode_piecewise_resistive_balance.v1",
        "solver_revision": "1",
        "quasi_steady_reviewed": True,
        "condition_compatibility_reviewed": True,
        "common_reference_reviewed": True,
        "anodic_positive_net_current_reviewed": True,
        "caller_reviewed": True,
        "evidence": [EVIDENCE],
    }


def parse(data):
    return ResistiveGalvanicCoupling.model_validate_json(json.dumps(data))


def test_finite_resistance_solution_closes_current_and_voltage_balances():
    model = parse(request())
    first = resistive_galvanic_coupling(model)
    second = resistive_galvanic_coupling(model)
    assert first == second
    assert first.status == "computed"
    assert first.values["electrode_interface_potential_V"] == pytest.approx(
        [-0.6333333333333333, -0.4666666666666667]
    )
    assert first.values["signed_net_electrode_current_A"] == pytest.approx(
        [1.6666666666666667, -1.6666666666666667]
    )
    assert first.values["series_voltage_drop_V"] == pytest.approx(1 / 6)
    assert "not_partial_dissolution" in first.values["current_meaning"]
    assert specifications()[0].model_id == "degradation.galvanic_resistive_coupling"


def test_review_component_sum_environment_and_support_gates_are_explicit():
    data = request()
    data["caller_reviewed"] = False
    result = resistive_galvanic_coupling(parse(data))
    assert result.status == "needs_data"
    assert result.values["reason"] == "unreviewed_applicability"

    data = request()
    data["connection"]["components"][0]["resistance_ohm"] = 0.07
    result = resistive_galvanic_coupling(parse(data))
    assert result.status == "needs_data"
    assert result.values["reason"] == "resistance_component_sum_mismatch"

    data = request()
    data["electrodes"][1]["polarization_curve"]["electrolyte_id"] = "other"
    result = resistive_galvanic_coupling(parse(data))
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "curve_environment_mismatch"

    data = request()
    data["electrodes"][0]["polarization_curve"]["signed_net_current_density_A_m2"] = [1.0, 2.0]
    data["electrodes"][1]["polarization_curve"]["signed_net_current_density_A_m2"] = [3.0, 4.0]
    result = resistive_galvanic_coupling(parse(data))
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "no_equilibrium_within_both_curve_supports"
