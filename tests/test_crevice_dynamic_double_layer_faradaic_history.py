from math import exp

import pytest

from matintegrity.contracts import Evidence, canonical_digest
from matintegrity.crevice_component_state_bdf import (
    DYNAMIC_DOUBLE_LAYER_INITIAL_STATE_SOURCE_ID,
    CreviceBDFDoubleLayerCapacitance,
    _double_layer_potential_from_charge_density,
)
from matintegrity.crevice_dynamic_double_layer_faradaic_history import (
    SOURCE_ID,
    CreviceDynamicDoubleLayerFaradaicHistoryRequest,
    DynamicDoubleLayerPolarizationBranch,
    _integrated_capacitance_charge,
    solve_crevice_dynamic_double_layer_faradaic_history,
)


def pinned_evidence(payload):
    digest = canonical_digest(payload)
    evidence = Evidence(
        source_id=SOURCE_ID,
        origin="synthetic",
        citation="Project-authored analytical RC fixture",
        license_id="synthetic-example-only",
        sha256=digest,
    )
    return digest, (evidence,)


def test_constant_capacitance_linear_faraday_matches_closed_form():
    times = (0.0, 1.0)
    cell_ids = ("cell-1",)
    areas = ((1.0,), (1.0,))
    current = ((1.0,), (1.0,))

    area_payload = {
        "time_s": list(times),
        "cell_ids": list(cell_ids),
        "active_area_m2_by_knot_and_cell": [list(row) for row in areas],
        "reference_potential_V_by_cell": [0.0],
    }
    area_digest, area_evidence = pinned_evidence(area_payload)
    current_payload = {
        "time_s": list(times),
        "cell_ids": list(cell_ids),
        "total_current_A_by_knot_and_cell": [list(row) for row in current],
    }
    current_digest, current_evidence = pinned_evidence(current_payload)
    capacitance_axis = (-1.0, 1.0)
    capacitance_values = (1.0, 1.0)
    capacitance_payload = {
        "potential_axis_V": list(capacitance_axis),
        "differential_capacitance_F_m2": list(capacitance_values),
    }
    capacitance_digest, capacitance_evidence = pinned_evidence(capacitance_payload)
    branch_payload = {
        "branch_id": "linear-faradaic",
        "overpotential_axis_V": [-1.0, 1.0],
        "signed_current_density_A_m2_by_cell_and_overpotential": [[-2.0, 2.0]],
        "equilibrium_potential_V_by_knot_and_cell": [[0.0], [0.0]],
    }
    branch_digest, branch_evidence = pinned_evidence(branch_payload)
    branch = DynamicDoubleLayerPolarizationBranch(
        branch_id="linear-faradaic",
        overpotential_axis_V=(-1.0, 1.0),
        signed_current_density_A_m2_by_cell_and_overpotential=((-2.0, 2.0),),
        equilibrium_potential_V_by_knot_and_cell=((0.0,), (0.0,)),
        curve_sha256=branch_digest,
        evidence=branch_evidence,
    )
    request = CreviceDynamicDoubleLayerFaradaicHistoryRequest(
        assessment_id="analytic-rc",
        time_s=times,
        cell_ids=cell_ids,
        initial_potential_V_by_cell=(0.0,),
        reference_potential_V_by_cell=(0.0,),
        active_area_m2_by_knot_and_cell=areas,
        active_area_record_sha256=area_digest,
        active_area_evidence=area_evidence,
        total_current_A_by_knot_and_cell=current,
        total_current_record_sha256=current_digest,
        total_current_evidence=current_evidence,
        differential_capacitance_potential_axis_V=capacitance_axis,
        differential_capacitance_F_m2=capacitance_values,
        differential_capacitance_curve_sha256=capacitance_digest,
        capacitance_evidence=capacitance_evidence,
        faradaic_branches=(branch,),
        relative_potential_tolerance=1e-9,
        absolute_potential_tolerance_V=1e-11,
        curve_linearity_and_no_extrapolation_reviewed=True,
        current_sign_and_external_boundary_reviewed=True,
        lumped_cell_independence_and_no_ionic_transport_reviewed=True,
        parameter_applicability_reviewed=True,
        computation_budget_reviewed=True,
        computational_use_authorized=True,
    )

    result = solve_crevice_dynamic_double_layer_faradaic_history(request)

    assert result.status == "computed", result.values
    expected = 0.5 * (1.0 - exp(-2.0))
    observed = result.values["potential_V_by_knot_and_cell"][-1][0]
    assert observed == pytest.approx(expected, abs=2e-9)
    assert result.values["maximum_absolute_current_closure_residual_A"] == pytest.approx(0.0, abs=1e-12)


def test_component_bdf_inverts_piecewise_linear_capacitance_charge_without_extrapolation():
    axis = (-0.5, 0.0, 0.5)
    capacitance = (1.0, 2.0, 3.0)
    cumulative = (0.0, 0.75, 2.0)
    for expected in (-0.4, -0.1, 0.0, 0.2, 0.45):
        charge = _integrated_capacitance_charge(expected, -0.25, axis, capacitance)
        actual = _double_layer_potential_from_charge_density(
            charge, -0.25, axis, capacitance, cumulative
        )
        assert actual == pytest.approx(expected, abs=2e-14)
    with pytest.raises(ArithmeticError, match="outside_capacitance_support"):
        _double_layer_potential_from_charge_density(100.0, -0.25, axis, capacitance, cumulative)


def test_component_bdf_double_layer_contract_pins_cdl_and_initial_state():
    axis = (-0.5, 0.0, 0.5)
    capacitance = (1.0, 2.0, 3.0)
    curve_payload = {
        "potential_axis_V": list(axis),
        "differential_capacitance_F_m2": list(capacitance),
    }
    curve_digest, curve_evidence = pinned_evidence(curve_payload)
    initial_payload = {
        "cell_ids": ["left", "right"],
        "initial_interfacial_potential_V_by_cell": [-0.1, 0.1],
        "reference_interfacial_potential_V_by_cell": [-0.25, -0.25],
        "capacitance_curve_sha256": curve_digest,
    }
    initial_digest = canonical_digest(initial_payload)
    initial_evidence = (Evidence(
        source_id=DYNAMIC_DOUBLE_LAYER_INITIAL_STATE_SOURCE_ID,
        origin="synthetic",
        citation="Project-authored initial interfacial state fixture",
        license_id="synthetic-example-only",
        sha256=initial_digest,
    ),)
    request = CreviceBDFDoubleLayerCapacitance(
        cell_ids=("left", "right"),
        initial_interfacial_potential_V_by_cell=(-0.1, 0.1),
        reference_interfacial_potential_V_by_cell=(-0.25, -0.25),
        differential_capacitance_potential_axis_V=axis,
        differential_capacitance_F_m2=capacitance,
        capacitance_curve_sha256=curve_digest,
        capacitance_evidence=curve_evidence,
        initial_state_record_sha256=initial_digest,
        initial_state_evidence=initial_evidence,
        initial_state_and_reference_reviewed=True,
        differential_curve_interpretation_reviewed=True,
        closed_electrolyte_boundary_and_charge_sign_reviewed=True,
        parameter_applicability_reviewed=True,
        computational_use_authorized=True,
    )
    assert request.initial_state_record_sha256 == initial_digest
