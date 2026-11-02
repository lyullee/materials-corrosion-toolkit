import pytest
from test_welding_preheat import payload

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.welding_preheat import (
    PreheatHistoryBinding,
    PreheatMeasurementIdentity,
    PreheatMeasurementTrace,
    PreheatMeasurementWindow,
    PreheatProcedureTemplate,
    preheat_history_binding,
)
from matintegrity.registry import default_registry


def trace(identity, temperatures=(350.0, 390.0, 450.0), times=(0.0, 10.0, 20.0)):
    raw = dict(time_s=times, temperature_K=temperatures)
    return PreheatMeasurementTrace(**identity.model_dump(), **raw, trace_sha256=canonical_digest(raw))


def request(**updates):
    template = payload().model_dump()
    for name in (
        "minimum_recorded_preheat_temperature_K",
        "maximum_recorded_interpass_temperature_K",
        "below_preheat_duration_s",
        "above_interpass_duration_s",
    ):
        template[name] = None
    channels = tuple(
        PreheatMeasurementIdentity(
            sensor_id=name,
            physical_scope_id="scope",
            location_id="joint-1",
            weld_id="weld-1",
            surface=surface,
            coordinate_frame_id="frame",
            position_m=(0.0, 0.0, z),
            placement_basis_id="authored",
            clock_id="clock",
        )
        for name, surface, z in [("a", "inner", 0.0), ("b", "outer", 0.02)]
    )
    raw = dict(
        template=PreheatProcedureTemplate(**template),
        required_channels=channels,
        traces=tuple(trace(r) for r in channels),
        windows=(
            PreheatMeasurementWindow(window_id="pre", phase="preheat", start_time_s=0.0, end_time_s=10.0),
            PreheatMeasurementWindow(
                window_id="inter", phase="interpass", start_time_s=10.0, end_time_s=20.0
            ),
        ),
        placement_phase_windows_and_clock_reviewed=True,
        maximum_sample_gap_s=10.0,
        maximum_segment_evaluations=1000,
    )
    raw.update(updates)
    digest = canonical_digest(
        PreheatHistoryBinding.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return PreheatHistoryBinding(
        **raw,
        basis=dict(
            source_id="authored",
            revision="1",
            license_id="authored-test",
            record_sha256=digest,
            applicability_and_units_reviewed=True,
            computational_use_authorized=True,
            evidence=(
                dict(
                    source_id="authored",
                    origin="synthetic",
                    citation="Authored linear crossing.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def test_analytic_crossing_and_sensor_time_union():
    result = preheat_history_binding(request())
    assert result.status == "computed"
    assert result.values["derived_metrics"]["below_preheat_duration_s"] == 5.0
    assert result.values["derived_metrics"]["minimum_recorded_preheat_temperature_K"] == 350.0
    assert result.values["record_within_declared_procedure_envelope"] is False
    assert result.values["derived_assessment"]["below_preheat_duration_s"] == 5.0


def test_history_derives_independent_interpass_minimum_and_duration():
    x = request()
    envelope = x.template.candidate_envelopes[0].model_copy(
        update={"minimum_supported_interpass_temperature_K": 420.0}
    )
    template = x.template.model_copy(update={"candidate_envelopes": (envelope,)})
    result = preheat_history_binding(request(template=template))
    assert result.values["derived_metrics"]["minimum_recorded_interpass_temperature_K"] == 390.0
    assert result.values["derived_metrics"]["below_interpass_duration_s"] == 5.0
    assert result.values["minimum_interpass_temperature_margin_K"] == -30.0


def test_absent_interpass_minimum_is_not_filled_from_preheat():
    result = preheat_history_binding(request())
    assert result.values["minimum_interpass_requirement_declared"] is False
    assert result.values["derived_metrics"]["below_interpass_duration_s"] is None


def test_interpass_crossing_uses_only_interpass_window():
    x = request()
    traces = tuple(trace(r, (380.0, 390.0, 490.0)) for r in x.required_channels)
    result = preheat_history_binding(request(traces=traces))
    assert result.values["derived_metrics"]["below_preheat_duration_s"] == 0.0
    assert result.values["derived_metrics"]["above_interpass_duration_s"] == 3.0


def test_different_sample_knots_on_same_clock_use_temporal_union():
    x = request()
    second = trace(x.required_channels[1], (390.0, 350.0, 450.0), (0.0, 5.0, 20.0))
    result = preheat_history_binding(request(traces=(x.traces[0], second), maximum_sample_gap_s=15.0))
    assert result.values["derived_metrics"]["below_preheat_duration_s"] == 8.0


def test_exact_thresholds_have_no_excursion_duration():
    x = request()
    result = preheat_history_binding(
        request(traces=tuple(trace(r, (370.0, 370.0, 460.0)) for r in x.required_channels))
    )
    assert result.values["record_within_declared_procedure_envelope"] is True


@pytest.mark.parametrize(
    "field,value", [("surface", "outer"), ("clock_id", "other"), ("position_m", (1.0, 0.0, 0.0))]
)
def test_mismatched_measurement_roles_rejected(field, value):
    x = request()
    traces = (x.traces[0].model_copy(update={field: value}), x.traces[1])
    with pytest.raises(ValueError, match="must match its required channel"):
        request(traces=traces)


def test_missing_sensor_needs_data_without_derived_assessment():
    result = preheat_history_binding(request(traces=request().traces[:1]))
    assert result.status == "needs_data"
    assert result.values["missing_sensor_ids"] == ["b"]
    assert "derived_assessment" not in result.values


def test_missing_time_support_and_long_sample_gap_are_not_filled():
    x = request()
    traces = tuple(trace(r, (380.0, 390.0), (0.0, 10.0)) for r in x.required_channels)
    assert preheat_history_binding(request(traces=traces)).status == "needs_data"
    assert preheat_history_binding(request(maximum_sample_gap_s=9.0)).status == "needs_data"


def test_overlapping_phase_windows_rejected():
    x = request()
    windows = (x.windows[0], x.windows[1].model_copy(update={"start_time_s": 9.0}))
    with pytest.raises(ValueError, match="nonoverlapping"):
        request(windows=windows)


def test_derived_input_cannot_be_overridden_by_template():
    raw = request().template.model_dump()
    raw["below_preheat_duration_s"] = 0.0
    with pytest.raises(ValueError):
        PreheatProcedureTemplate(**raw)


def test_work_budget_withholds_partial_result():
    result = preheat_history_binding(request(maximum_segment_evaluations=1))
    assert result.status == "out_of_scope"
    assert "derived_assessment" not in result.values


def test_python_json_exchange_and_context_identity():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="asset-1", location_id="joint-1", time_basis="synthetic")
    a = registry.run("welding.preheat_history_binding", x.model_dump(), context)
    b = registry.run_json("welding.preheat_history_binding", x.model_dump_json(), context)
    assert a.values == b.values
    with pytest.raises(ValueError, match="must match"):
        registry.run(
            "welding.preheat_history_binding",
            x.model_dump(),
            context.model_copy(update={"location_id": "other"}),
        )
