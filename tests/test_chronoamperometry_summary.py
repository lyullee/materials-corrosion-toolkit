import json

import pytest
from pydantic import ValidationError

from matintegrity.adapters import seccm_chronoamperometry_summary_inputs
from matintegrity.contracts import RunContext
from matintegrity.models.electrochemistry import (
    ChronoamperometryWindowSummary,
    chronoamperometry_window_summary,
)
from matintegrity.registry import default_registry
from matintegrity.seccm_data import SeccmChronoamperometryTrace


def request(**changes):
    data = dict(
        trace_id="authored-trace",
        physical_specimen_id="authored-specimen",
        source_group_id="authored-program",
        source_trace_sha256="a" * 64,
        time_s=[0.0, 1.0, 3.0, 4.0],
        current_A=[-2.0, 0.0, 4.0, 6.0],
        analysis_window_s=[0.5, 3.5],
        baseline_window_s=[0.0, 1.0],
        boundary_policy="piecewise_linear",
        sample_order_reviewed=True,
        time_unit_reviewed_as_seconds=True,
        current_unit_reviewed_as_amperes=True,
        current_sign_basis="authored signed instrument-current convention",
        current_sign_reviewed=True,
    )
    data.update(changes)
    return ChronoamperometryWindowSummary.model_validate(data)


def test_piecewise_linear_affine_trace_matches_closed_form_integrals_and_baseline():
    result = chronoamperometry_window_summary(request())
    assert result.status == "computed"
    # I(t) = 2t - 2 over [0.5, 3.5].
    assert result.values["signed_charge_C"] == pytest.approx(6.0)
    assert result.values["absolute_charge_C"] == pytest.approx(6.5)
    assert result.values["positive_polarity_charge_C"] == pytest.approx(6.25)
    assert result.values["negative_polarity_charge_C"] == pytest.approx(0.25)
    assert result.values["time_mean_current_A"] == pytest.approx(2.0)
    assert result.values["baseline_signed_charge_C"] == pytest.approx(-1.0)
    assert result.values["baseline_time_mean_current_A"] == pytest.approx(-1.0)
    assert result.values["minimum_current_A"] == pytest.approx(-1.0)
    assert result.values["maximum_current_A"] == pytest.approx(5.0)
    assert result.values["minimum_minus_baseline_A"] == pytest.approx(0.0)
    assert result.values["maximum_minus_baseline_A"] == pytest.approx(6.0)


def test_absolute_charge_inserts_zero_crossing_for_piecewise_linear_signal():
    definition = request(
        time_s=[0.0, 2.0],
        current_A=[-2.0, 2.0],
        analysis_window_s=[0.0, 2.0],
        baseline_window_s=None,
        boundary_policy="exact_samples",
    )
    result = chronoamperometry_window_summary(definition)
    assert result.values["signed_charge_C"] == pytest.approx(0.0)
    assert result.values["absolute_charge_C"] == pytest.approx(2.0)
    assert result.values["positive_polarity_charge_C"] == pytest.approx(1.0)
    assert result.values["negative_polarity_charge_C"] == pytest.approx(1.0)
    assert result.values["baseline_time_mean_current_A"] is None


def test_polarity_charges_are_separately_integrated_at_an_internal_sign_change():
    result = chronoamperometry_window_summary(
        request(
            time_s=[0.0, 2.0],
            current_A=[-2.0, 2.0],
            analysis_window_s=[0.0, 2.0],
            baseline_window_s=None,
            boundary_policy="exact_samples",
        )
    )
    assert result.values["positive_polarity_charge_C"] == pytest.approx(1.0)
    assert result.values["negative_polarity_charge_C"] == pytest.approx(1.0)
    assert result.values["positive_polarity_charge_C"] + result.values[
        "negative_polarity_charge_C"
    ] == pytest.approx(result.values["absolute_charge_C"])


def test_plateau_extrema_retain_first_and_last_times_without_event_classification():
    result = chronoamperometry_window_summary(
        request(
            time_s=[0.0, 1.0, 2.0, 3.0],
            current_A=[1.0, 3.0, 3.0, 1.0],
            analysis_window_s=[0.0, 3.0],
            baseline_window_s=None,
            boundary_policy="exact_samples",
        )
    )
    assert result.values["maximum_time_first_s"] == 1.0
    assert result.values["maximum_time_last_s"] == 2.0
    assert result.values["interpretation"] == "descriptive_trace_summary_only"
    assert not any("probability" in key or "pit" in key for key in result.values)


@pytest.mark.parametrize(
    "flag",
    [
        "sample_order_reviewed",
        "time_unit_reviewed_as_seconds",
        "current_unit_reviewed_as_amperes",
        "current_sign_reviewed",
    ],
)
def test_unreviewed_trace_basis_stops_calculation(flag):
    result = chronoamperometry_window_summary(request(**{flag: False}))
    assert result.status == "needs_data"
    assert result.values["unreviewed"] == [flag]


def test_exact_sample_policy_rejects_unsampled_boundaries_without_interpolation():
    result = chronoamperometry_window_summary(request(boundary_policy="exact_samples"))
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "analysis_window_endpoints_not_sampled"


def test_windows_outside_support_remain_out_of_scope():
    result = chronoamperometry_window_summary(request(analysis_window_s=[-1.0, 2.0]))
    assert result.status == "out_of_scope"
    assert result.values["reason"] == "analysis_window_outside_trace_support"


@pytest.mark.parametrize(
    "changes",
    [
        {"time_s": [0.0, 1.0], "current_A": [1.0]},
        {"time_s": [0.0, 0.0], "current_A": [1.0, 2.0]},
        {"time_s": [0.0, float("nan")], "current_A": [1.0, 2.0]},
        {"analysis_window_s": [2.0, 1.0]},
    ],
)
def test_invalid_trace_contracts_are_rejected(changes):
    with pytest.raises(ValidationError):
        request(**changes)


def test_registry_json_path_preserves_provenance_and_units():
    definition = request()
    result = default_registry().run_json(
        "corrosion.chronoamperometry_window_summary",
        definition.model_dump_json(),
        RunContext(asset_id="authored", location_id="map-1", time_basis="declared hold"),
    )
    assert result.status == "computed"
    assert result.values["source_trace_sha256"] == "a" * 64
    assert result.units["signed_charge_C"] == "C"
    assert len(result.input_digest) == 64
    assert json.loads(result.model_dump_json())["probability_semantics"] == {}


def test_seccm_adapter_preserves_reader_identities_and_builds_array_digest():
    metadata = SeccmChronoamperometryTrace(
        dataset_id="seccm-ebsd-316l-pitting-v1",
        physical_specimen_id="provider-map-scope-unresolved",
        source_group_id="provider-map-1031-c",
        map_id=7,
        map_point_label="MAP_Point_7",
        provider_signal_label="I_Substrate_A_LN_7",
        source_archive_sha256="b" * 64,
        source_member_sha256="c" * 64,
        sample_count=3,
        unit_basis="authored fixture matching the reviewed provider header contract",
        provider_code_commit="d" * 40,
        provider_code_sha256="e" * 64,
    )
    payload = seccm_chronoamperometry_summary_inputs(
        {"metadata": metadata, "time_s": [0.0, 1.0, 2.0], "substrate_current_A": [1e-9, 2e-9, 3e-9]},
        analysis_window_s=[0.0, 2.0],
        current_sign_basis="caller-reviewed provider substrate-current sign",
        current_sign_reviewed=True,
    )
    assert payload["trace_id"].endswith("map-7")
    assert payload["source_archive_sha256"] == "b" * 64
    assert payload["source_member_sha256"] == "c" * 64
    assert len(payload["source_trace_sha256"]) == 64
    result = default_registry().run(
        "corrosion.chronoamperometry_window_summary",
        payload,
        RunContext(asset_id="provider-map-scope-unresolved", location_id="map-7", time_basis="hold"),
    )
    assert result.status == "computed"
    assert result.values["signed_charge_C"] == pytest.approx(4e-9)


def test_seccm_adapter_rejects_misaligned_reader_payload():
    with pytest.raises((ValidationError, ValueError)):
        seccm_chronoamperometry_summary_inputs(
            {"metadata": {}, "time_s": [0.0], "substrate_current_A": []},
            analysis_window_s=[0.0, 1.0],
            current_sign_basis="reviewed",
            current_sign_reviewed=True,
        )
