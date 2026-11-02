import copy
import json
import math

import numpy as np
import pytest

from matintegrity.contracts import RunContext
from matintegrity.models.electrochemistry import (
    MixedPotential,
    MixedPotentialEquilibrium,
    PolarizationCurve,
    mixed_potential,
)
from matintegrity.registry import default_registry

EVIDENCE = {"source_id": "authored", "origin": "synthetic", "citation": "Authored current-balance fixture"}


def curve(name, potential, current):
    return dict(
        curve_id=name,
        surface_condition_id=name,
        protocol_id="authored-steady",
        electrolyte_id="authored-bath",
        reference_electrode_id="authored-reference",
        temperature_K=298.15,
        point_ids=[f"{name}-{i}" for i in range(len(potential))],
        potential_V=list(potential),
        signed_net_current_density_A_m2=list(current),
        evidence=[EVIDENCE],
    )


def request(curves=None, areas=None, **changes):
    curves = curves or [curve("A", [-1.0, 0.0], [-2.0, 8.0]), curve("B", [-1.0, 0.0], [-7.0, 3.0])]
    areas = areas or [1e-4, 3e-4]
    data = dict(
        electrodes=[
            dict(electrode_id=f"electrode-{i}", exposed_area_m2=area, curve=definition)
            for i, (area, definition) in enumerate(zip(areas, curves, strict=True))
        ],
        quasi_steady_reviewed=True,
        negligible_ohmic_drop_reviewed=True,
        condition_compatibility_reviewed=True,
        anodic_positive_reviewed=True,
    )
    data.update(changes)
    return MixedPotential.model_validate_json(json.dumps(data))


def test_mixed_potential_matches_independent_linear_circuit_and_area_weighting():
    definition = request()
    result = mixed_potential(definition)
    assert result.status == "computed"
    expected_potential = (1e-4 * -0.8 / 0.1 + 3e-4 * -0.3 / 0.1) / (1e-4 / 0.1 + 3e-4 / 0.1)
    expected_current = (-0.3 + 0.8) / (0.1 / 1e-4 + 0.1 / 3e-4)
    assert result.values["mixed_potential_V"] == pytest.approx(expected_potential)
    assert result.values["electrode_net_current_A"] == pytest.approx([expected_current, -expected_current])
    assert result.values["total_positive_net_current_A"] == pytest.approx(expected_current)
    root = result.values["equilibria"][0]
    assert root["slope_diagnostic"] == "positive"
    assert root["residual_within_tolerance"]
    assert "metal_dissolution" in result.values["current_meaning"]


def test_changing_area_changes_potential_and_preserves_current_conservation():
    equal_area = mixed_potential(request(areas=[1e-4, 1e-4]))
    unequal = mixed_potential(request())
    assert equal_area.values["mixed_potential_V"] == pytest.approx(-0.55)
    assert unequal.values["mixed_potential_V"] > equal_area.values["mixed_potential_V"]
    assert math.fsum(unequal.values["electrode_net_current_A"]) == pytest.approx(0.0, abs=1e-18)


def test_nonmatching_knots_use_common_support_without_extrapolation():
    curves = [
        curve("A", [-2.0, -1.0, 0.0], [-12.0, -2.0, 8.0]),
        curve("B", [-0.9, -0.6, -0.2], [-6.0, -3.0, 1.0]),
    ]
    result = mixed_potential(request(curves))
    assert result.status == "computed"
    assert result.values["common_potential_interval_V"] == [-0.9, -0.2]
    assert result.values["mixed_potential_V"] == pytest.approx(-0.425)


def test_three_electrodes_balance_without_assigning_pairwise_path_currents():
    curves = [
        curve(str(i), [-1.0, 1.0], [-1.0 - offset, 1.0 - offset]) for i, offset in enumerate([-0.5, 0.0, 0.5])
    ]
    result = mixed_potential(request(curves, areas=[1.0, 2.0, 3.0]))
    assert result.status == "computed"
    assert result.values["mixed_potential_V"] == pytest.approx(1 / 6)
    assert math.fsum(result.values["electrode_net_current_A"]) == pytest.approx(0.0, abs=1e-14)


def test_all_active_passive_intersections_are_retained_without_automatic_stability_selection():
    result = mixed_potential(
        request(
            [curve("A", [0.0, 1.0, 2.0, 3.0], [0.0, 2.0, 0.0, 2.0]), curve("B", [0.0, 3.0], [-1.0, -1.0])],
            areas=[1.0, 1.0],
        )
    )
    assert result.status == "needs_data"
    assert result.values["reason"] == "multiple_equilibria"
    assert [root["potential_V"] for root in result.values["equilibria"]] == pytest.approx([0.5, 1.5, 2.5])
    assert [root["slope_diagnostic"] for root in result.values["equilibria"]] == [
        "positive",
        "negative",
        "positive",
    ]
    assert result.values["mixed_potential_V"] is None


def test_adjacent_flat_balance_intervals_merge_and_endpoint_roots_are_not_duplicated():
    result = mixed_potential(
        request(
            [
                curve("A", [0.0, 1.0, 1.5, 2.0, 3.0], [0.0, 1.0, 1.0, 1.0, 2.0]),
                curve("B", [0.0, 3.0], [-1.0, -1.0]),
            ],
            areas=[1.0, 1.0],
        )
    )
    assert result.status == "needs_data"
    assert result.values["zero_balance_intervals_V"] == [[1.0, 2.0]]
    assert result.values["equilibria"] == []


def test_all_zero_currents_have_nonunique_potential_instead_of_a_zero_potential_guess():
    result = mixed_potential(
        request([curve("A", [-1.0, 1.0], [0.0, 0.0]), curve("B", [-1.0, 1.0], [0.0, 0.0])])
    )
    assert result.status == "needs_data"
    assert result.values["mixed_potential_V"] is None
    assert result.values["zero_balance_intervals_V"] == [[-1.0, 1.0]]


def test_unique_knot_root_is_reported_once_with_one_sided_slope_diagnostics():
    result = mixed_potential(
        request(
            [curve("A", [-1.0, 0.0, 1.0], [-1.0, 0.0, 2.0]), curve("B", [-1.0, 1.0], [0.0, 0.0])],
            areas=[1.0, 1.0],
        )
    )
    assert result.status == "computed"
    assert len(result.values["equilibria"]) == 1
    root = result.values["equilibria"][0]
    assert root["balance_slope_left_A_V"] == pytest.approx(1.0)
    assert root["balance_slope_right_A_V"] == pytest.approx(2.0)


def test_tangent_root_and_support_endpoint_do_not_claim_dynamic_stability():
    tangent = mixed_potential(
        request([curve("A", [-1.0, 0.0, 1.0], [1.0, 0.0, 1.0]), curve("B", [-1.0, 1.0], [0.0, 0.0])])
    )
    assert tangent.values["equilibria"][0]["slope_diagnostic"] == "mixed_or_tangent"
    boundary = mixed_potential(
        request([curve("A", [0.0, 1.0], [0.0, 1.0]), curve("B", [0.0, 1.0], [0.0, 2.0])])
    )
    assert boundary.status == "computed"
    assert boundary.values["equilibria"][0]["slope_diagnostic"] == "support_boundary"
    assert boundary.values["total_positive_net_current_A"] == 0.0


@pytest.mark.parametrize("kind", ["no_span", "no_root"])
def test_unsupported_equilibrium_is_not_extrapolated(kind):
    curves = (
        [curve("A", [-2.0, -1.0], [-1.0, 1.0]), curve("B", [0.0, 1.0], [-1.0, 1.0])]
        if kind == "no_span"
        else [curve("A", [0.0, 1.0], [1.0, 2.0]), curve("B", [0.0, 1.0], [1.0, 2.0])]
    )
    result = mixed_potential(request(curves))
    assert result.status == "out_of_scope"
    assert result.values["mixed_potential_V"] is None


@pytest.mark.parametrize(
    "flag",
    [
        "quasi_steady_reviewed",
        "negligible_ohmic_drop_reviewed",
        "condition_compatibility_reviewed",
        "anodic_positive_reviewed",
    ],
)
def test_unreviewed_physical_assumptions_stop_before_computing_a_potential(flag):
    result = mixed_potential(request(**{flag: False}))
    assert result.status == "needs_data"
    assert result.values["unreviewed"] == [flag]
    assert not result.values["equilibria"]


@pytest.mark.parametrize(
    "field,other",
    [
        ("reference_electrode_id", "another-reference"),
        ("electrolyte_id", "another-bath"),
        ("temperature_K", 300.0),
    ],
)
def test_missing_or_mismatched_conditions_are_preserved(field, other):
    data = request().model_dump(mode="json")
    data["electrodes"][1]["curve"][field] = None
    missing = mixed_potential(MixedPotential.model_validate_json(json.dumps(data)))
    assert missing.status == "needs_data"
    data["electrodes"][1]["curve"][field] = other
    mismatch = mixed_potential(MixedPotential.model_validate_json(json.dumps(data)))
    assert mismatch.status == "out_of_scope"
    assert mismatch.values["condition"] == field


@pytest.mark.parametrize(
    "change",
    [
        dict(potential_V=[0.0, -1.0]),
        dict(potential_V=[0.0, 0.0]),
        dict(point_ids=["same", "same"]),
        dict(signed_net_current_density_A_m2=[1.0]),
    ],
)
def test_cyclic_duplicate_or_unaligned_branches_are_not_sorted_or_repaired(change):
    data = curve("A", [-1.0, 0.0], [-2.0, 8.0]) | change
    with pytest.raises(ValueError):
        PolarizationCurve.model_validate_json(json.dumps(data))


def test_json_round_trip_registry_and_evidence_snapshot():
    definition = request()
    context = RunContext(asset_id="authored", location_id="pair", time_basis="static interpolant")
    result = default_registry().run_json("corrosion.mixed_potential", definition.model_dump_json(), context)
    assert result.status == "computed"
    assert result.inputs["electrodes"][0]["curve"]["evidence"][0]["source_id"] == "authored"
    assert MixedPotential.model_validate_json(json.dumps(result.inputs)) == definition
    assert result.probability_semantics == {}


def test_potential_reference_shift_and_common_current_scaling_preserve_physics():
    baseline = mixed_potential(request())
    for factor in (1e-200, 1e200):
        data = request().model_dump(mode="json")
        for electrode in data["electrodes"]:
            electrode["curve"]["potential_V"] = [value + 0.237 for value in electrode["curve"]["potential_V"]]
            electrode["curve"]["signed_net_current_density_A_m2"] = [
                value * factor for value in electrode["curve"]["signed_net_current_density_A_m2"]
            ]
        result = mixed_potential(MixedPotential.model_validate_json(json.dumps(data)))
        assert result.status == "computed"
        assert result.values["mixed_potential_V"] == pytest.approx(
            baseline.values["mixed_potential_V"] + 0.237
        )
        assert np.asarray(result.values["electrode_net_current_A"]) / factor == pytest.approx(
            baseline.values["electrode_net_current_A"]
        )


def test_large_opposing_currents_with_unresolved_balance_slope_need_data():
    delta = 1e-15
    curves = [curve("A", [-1.0, 1.0], [1.0 - delta, 1.0 + delta]), curve("B", [-1.0, 1.0], [-1.0, -1.0])]
    result = mixed_potential(request(curves, areas=[1.0, 1.0]))
    assert result.status == "needs_data"
    assert result.values["equilibria"][0]["numerical_quality"] == "cancellation_limited"


def test_unrepresentable_current_and_potential_ranges_stop_with_finite_outputs():
    data = request().model_dump(mode="json")
    data["electrodes"][0]["exposed_area_m2"] = 1e308
    result = mixed_potential(MixedPotential.model_validate_json(json.dumps(data)))
    assert result.status == "out_of_scope"
    data = request().model_dump(mode="json")
    for electrode in data["electrodes"]:
        electrode["curve"]["potential_V"] = [-1e308, 1e308]
    result = mixed_potential(MixedPotential.model_validate_json(json.dumps(data)))
    assert result.values["reason"] == "potential_interval_not_representable"


def test_nonlinear_symmetric_reaction_balance_converges_to_independent_closed_form():
    k, e0, density, areas = 11.0, np.array([-0.8, -0.3]), np.array([0.03, 0.01]), np.array([1e-4, 3e-4])
    expected = math.log(
        np.sum(areas * density * np.exp(k * e0)) / np.sum(areas * density * np.exp(-k * e0))
    ) / (2 * k)
    errors = []
    for count in (17, 65, 257, 1025):
        potential = np.linspace(-1.0, 0.0, count)
        definitions = [
            curve(str(i), potential, 2 * density[i] * np.sinh(k * (potential - e0[i]))) for i in range(2)
        ]
        result = mixed_potential(request(definitions, areas=areas.tolist()))
        assert result.status == "computed"
        errors.append(abs(result.values["mixed_potential_V"] - expected))
    assert errors[-1] < 1e-7
    assert errors[0] / errors[-1] > 1000


def test_duplicate_electrode_identity_is_refused_without_mutating_input():
    data = request().model_dump(mode="json")
    original = copy.deepcopy(data)
    data["electrodes"][1]["electrode_id"] = data["electrodes"][0]["electrode_id"]
    with pytest.raises(ValueError):
        MixedPotential.model_validate_json(json.dumps(data))
    assert original["electrodes"][0]["electrode_id"] != original["electrodes"][1]["electrode_id"]


def test_unreviewed_source_current_sign_is_not_relabelled_by_a_global_review_flag():
    data = request().model_dump(mode="json")
    data["electrodes"][0]["curve"]["current_convention"] = "unreviewed_signed_net"
    result = mixed_potential(MixedPotential.model_validate_json(json.dumps(data)))
    assert result.status == "needs_data"
    assert result.values["reason"] == "unreviewed_current_convention"


def test_external_equilibrium_contract_refuses_unaligned_ids_or_an_unsupported_potential():
    original = mixed_potential(request()).values["equilibria"][0]
    for change in (
        dict(electrode_net_current_A=[0.0]),
        dict(electrode_ids=["same", "same"]),
        dict(potential_V=99.0),
    ):
        with pytest.raises(ValueError):
            MixedPotentialEquilibrium.model_validate_json(json.dumps(original | change))
