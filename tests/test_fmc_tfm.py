import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.fmc_tfm import (
    FmcElement,
    FmcTimeTrace,
    HomogeneousFmcTfm,
    TfmImagePoint,
    homogeneous_fmc_tfm,
)
from matintegrity.registry import default_registry


def trace(tx, rx, samples=None):
    samples = tuple(float(max(0, 1 - abs(i - 10))) for i in range(21)) if samples is None else tuple(samples)
    return FmcTimeTrace(
        trace_id=tx + rx,
        transmit_element_id=tx,
        receive_element_id=rx,
        signed_samples=samples,
        samples_sha256=canonical_digest(samples),
    )


def request(**updates):
    raw = dict(
        acquisition_id="synthetic-fmc",
        physical_specimen_id="synthetic-coupon",
        physical_scope_id="coupon-volume",
        source_group_id="authored-source-group",
        material_condition_id="authored-medium",
        probe_id="probe",
        coordinate_frame_id="cartesian",
        sample_clock_id="authored-clock",
        time_zero_basis_id="authored-t0",
        velocity_basis_id="authored-c",
        raw_record_sha256="a" * 64,
        amplitude_unit="authored-unit",
        propagation_model="homogeneous_isotropic_direct_longitudinal",
        aggregation="coherent_sum",
        excitation_time_origin_s=0.0,
        longitudinal_velocity_m_s=1.0,
        time_s=tuple(float(i) for i in range(21)),
        elements=(
            {"element_id": "a", "position_m": (-3.0, 0.0, 0.0)},
            {"element_id": "b", "position_m": (3.0, 0.0, 0.0)},
        ),
        traces=(trace("b", "b"), trace("a", "b"), trace("b", "a"), trace("a", "a")),
        image_points=(
            {"point_id": "focus", "position_m": (0.0, 0.0, 4.0)},
            {"point_id": "off-focus", "position_m": (0.0, 0.0, 0.0)},
        ),
    )
    raw.update(updates)
    raw["elements"] = tuple(FmcElement.model_validate(row) for row in raw["elements"])
    raw["image_points"] = tuple(TfmImagePoint.model_validate(row) for row in raw["image_points"])
    # Normalize nested contracts/defaults before binding the complete request.
    unbound = HomogeneousFmcTfm.model_construct(**raw)
    digest = canonical_digest(unbound.model_dump(mode="json", exclude={"basis"}))
    return HomogeneousFmcTfm(
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
                    citation="Authored FMC geometry and pulses.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def amplitudes(result):
    return [row["coherent_amplitude"] for row in result.values["image"]]


def test_analytic_three_four_five_focus_and_off_focus():
    result = homogeneous_fmc_tfm(request())
    assert result.status == "computed"
    assert amplitudes(result) == [4.0, 0.0]
    assert result.values["trace_ids"] == ["bb", "ab", "ba", "aa"]
    assert result.values["physical_specimen_id"] == "synthetic-coupon"
    assert result.values["source_group_id"] == "authored-source-group"
    assert [
        (row["transmit_element_id"], row["receive_element_id"]) for row in result.values["trace_records"]
    ] == [("b", "b"), ("a", "b"), ("b", "a"), ("a", "a")]


def test_coherent_mean_has_explicit_normalization():
    assert amplitudes(homogeneous_fmc_tfm(request(aggregation="coherent_mean"))) == [1.0, 0.0]


def test_linear_interpolation_is_applied_at_declared_clock():
    assert amplitudes(homogeneous_fmc_tfm(request(excitation_time_origin_s=0.5))) == [2.0, 0.0]


def test_common_clock_origin_shift_preserves_image():
    result = homogeneous_fmc_tfm(
        request(time_s=tuple(float(i + 1000) for i in range(21)), excitation_time_origin_s=1000.0)
    )
    assert amplitudes(result) == [4.0, 0.0]


def test_signed_rf_is_not_an_envelope_or_intensity():
    traces = tuple(
        trace(tx, rx, (-value for value in trace(tx, rx).signed_samples))
        for tx, rx in (("b", "b"), ("a", "b"), ("b", "a"), ("a", "a"))
    )
    assert amplitudes(homogeneous_fmc_tfm(request(traces=traces))) == [-4.0, 0.0]


def test_outside_clock_support_withholds_whole_image():
    result = homogeneous_fmc_tfm(request(image_points=({"point_id": "far", "position_m": (0.0, 0.0, 30.0)},)))
    assert result.status == "out_of_scope"
    assert result.values["unsupported_point_ids"] == ["far"]
    assert "image" not in result.values


@pytest.mark.parametrize(
    "traces",
    [
        (trace("a", "a"), trace("a", "b"), trace("b", "a")),
        (trace("a", "a"), trace("a", "b"), trace("b", "a"), trace("a", "a")),
    ],
)
def test_missing_or_duplicate_fmc_pairs_are_rejected(traces):
    with pytest.raises(ValueError):
        request(traces=traces)


def test_sample_digest_tamper_is_rejected():
    raw = trace("a", "a").model_dump()
    raw["signed_samples"] = (1.0,) * 21
    with pytest.raises(ValueError, match="sample digest"):
        FmcTimeTrace.model_validate(raw)


def test_misaligned_sample_clock_is_rejected():
    with pytest.raises(ValueError, match="align"):
        request(time_s=(0.0, 1.0))


def test_caller_evaluation_budget_is_not_silent_subsampling():
    result = homogeneous_fmc_tfm(request(maximum_point_trace_evaluations=3))
    assert result.status == "out_of_scope"
    assert "image" not in result.values


def test_exact_last_sample_is_inside_support():
    result = homogeneous_fmc_tfm(
        request(
            elements=({"element_id": "a", "position_m": (0.0, 0.0, 0.0)},),
            traces=(trace("a", "a", (0.0,) * 20 + (3.0,)),),
            image_points=({"point_id": "end", "position_m": (0.0, 0.0, 10.0)},),
        )
    )
    assert amplitudes(result) == [3.0]


def test_nonfinite_geometry_is_withheld():
    result = homogeneous_fmc_tfm(
        request(image_points=({"point_id": "huge", "position_m": (0.0, 0.0, 1.7e308)},))
    )
    assert result.status == "out_of_scope"
    assert "image" not in result.values


@pytest.mark.parametrize(
    "aggregation,status", [("coherent_sum", "out_of_scope"), ("coherent_mean", "computed")]
)
def test_extreme_amplitude_sum_and_mean_have_distinct_numeric_support(aggregation, status):
    traces = tuple(
        trace(tx, rx, (1e308,) * 21) for tx, rx in (("b", "b"), ("a", "b"), ("b", "a"), ("a", "a"))
    )
    result = homogeneous_fmc_tfm(request(traces=traces, aggregation=aggregation))
    assert result.status == status
    if status == "computed":
        assert amplitudes(result) == [1e308, 1e308]


def test_time_origin_change_breaks_request_digest():
    raw = request().model_dump()
    raw["excitation_time_origin_s"] = 1.0
    with pytest.raises(ValueError, match="pin the complete"):
        HomogeneousFmcTfm.model_validate(raw)


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="coupon", time_basis="authored-clock")
    a = registry.run("inspection.homogeneous_fmc_tfm", x, context)
    b = registry.run_json("inspection.homogeneous_fmc_tfm", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
