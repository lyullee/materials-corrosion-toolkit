import copy
import json

import pytest

from matintegrity.models.galvanic_coupling import (
    GalvanicCouplingAssessment,
    galvanic_coupling,
    specifications,
)

EVIDENCE = {
    "source_id": "authored-fixture",
    "origin": "synthetic",
    "citation": "Independent galvanic coupling test fixture",
}
DIGEST = "a" * 64


def curve(curve_id, currents, *, lower=-1.0, upper=0.0, electrolyte="bath"):
    return {
        "curve_id": curve_id,
        "surface_condition_id": f"surface-{curve_id}",
        "protocol_id": "steady-scan",
        "electrolyte_id": electrolyte,
        "reference_electrode_id": "ref",
        "temperature_K": 298.15,
        "point_ids": [f"{curve_id}-0", f"{curve_id}-1"],
        "potential_V": [lower, upper],
        "signed_net_current_density_A_m2": currents,
        "evidence": [EVIDENCE],
    }


def request():
    return {
        "assessment_id": "couple-1",
        "asset_id": "asset-1",
        "location_id": "joint-1",
        "environment": {
            "environment_id": "environment-1",
            "electrolyte_id": "bath",
            "electrolyte_description": "authored test electrolyte",
            "temperature_K": 298.15,
            "reference_electrode_id": "ref",
            "condition_digest": DIGEST,
        },
        "electrodes": [
            {
                "electrode_id": "steel",
                "metal_id": "metal-steel",
                "material_condition_id": "condition-a",
                "exposed_area_m2": 1e-4,
                "polarization_curve": curve("curve-steel", [-2.0, 8.0]),
                "curve_provider_id": "provider-a",
                "curve_provider_revision": "1",
                "curve_input_digest": DIGEST,
                "curve_result_digest": DIGEST,
                "curve_support_reviewed": True,
            },
            {
                "electrode_id": "alloy",
                "metal_id": "metal-alloy",
                "material_condition_id": "condition-b",
                "exposed_area_m2": 3e-4,
                "polarization_curve": curve("curve-alloy", [-7.0, 3.0]),
                "curve_provider_id": "provider-b",
                "curve_provider_revision": "2",
                "curve_input_digest": DIGEST,
                "curve_result_digest": DIGEST,
                "curve_support_reviewed": True,
            },
        ],
        "connection": {
            "connection_id": "connection-1",
            "state": "connected",
            "total_resistance_ohm": 0.01,
            "resistance_basis": "four-wire measurement",
            "resistance_reviewed": True,
            "maximum_negligible_resistance_ohm": 0.1,
        },
        "partial_dissolution_observations": [
            {
                "observation_id": "dissolution-1",
                "electrode_id": "steel",
                "species_id": "Fe2+",
                "partial_dissolution_current_density_A_m2": 9.0,
                "method_id": "caller-speciation",
                "provider_id": "lab-1",
                "result_digest": DIGEST,
                "evidence": [EVIDENCE],
            }
        ],
        "solver_id": "matintegrity.corrosion.mixed_potential.v1",
        "solver_revision": "1",
        "quasi_steady_reviewed": True,
        "condition_compatibility_reviewed": True,
        "anodic_positive_net_current_reviewed": True,
        "caller_reviewed": True,
        "evidence": [EVIDENCE],
    }


def parse(data):
    return GalvanicCouplingAssessment.model_validate_json(json.dumps(data))


def test_bounded_coupling_reuses_signed_mixed_potential_without_dissolution_inference():
    model = parse(request())
    first = galvanic_coupling(model)
    second = galvanic_coupling(model)
    assert first == second
    assert first.status == "computed"
    assert first.values["mixed_potential_V"] == pytest.approx(-0.425)
    assert sum(first.values["signed_net_electrode_current_A"]) == pytest.approx(0.0, abs=1e-18)
    partial = first.values["partial_dissolution_observations"][0]
    assert partial["partial_dissolution_current_density_A_m2"] == 9.0
    assert "not_partial_dissolution" in first.values["current_meaning"]
    assert specifications()[0].model_id == "degradation.galvanic_coupling"


def test_review_resistance_condition_and_curve_support_gates_are_explicit():
    data = request()
    data["caller_reviewed"] = False
    result = galvanic_coupling(parse(data))
    assert result.status == "needs_data"
    assert result.values["reason"] == "unreviewed_applicability"

    data = request()
    data["connection"]["total_resistance_ohm"] = 1.0
    result = galvanic_coupling(parse(data))
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "connection_resistance_not_negligible"

    data = request()
    data["electrodes"][1]["polarization_curve"] = curve("curve-alloy", [-70.0, -10.0], lower=-0.9, upper=-0.2)
    result = galvanic_coupling(parse(data))
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "mixed_potential:no_equilibrium_in_common_support"

    data = request()
    data["electrodes"][1]["polarization_curve"]["electrolyte_id"] = "other-bath"
    result = galvanic_coupling(parse(data))
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "curve_environment_mismatch"


def test_identity_links_are_strict():
    data = request()
    duplicate = copy.deepcopy(data["electrodes"][0])
    duplicate["polarization_curve"]["curve_id"] = "curve-third"
    data["electrodes"].append(duplicate)
    with pytest.raises(ValueError, match="electrode identities"):
        parse(data)

    data = request()
    data["partial_dissolution_observations"][0]["electrode_id"] = "unknown"
    with pytest.raises(ValueError, match="reference an electrode"):
        parse(data)
