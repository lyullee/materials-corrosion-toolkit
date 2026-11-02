import math

import pytest

from matintegrity.contracts import RunContext, canonical_digest
from matintegrity.models.fmc_tfm import FmcElement, FmcTimeTrace, TfmImagePoint, homogeneous_fmc_tfm
from matintegrity.models.planar_multiview_tfm import (
    PlanarMultiviewFmcTfm,
    PlanarTfmView,
    _plane_transmitted_ray,
    planar_multiview_fmc_tfm,
)
from matintegrity.registry import default_registry


def view(identifier="LL", tx="longitudinal", rx="longitudinal", tb=False, rb=False):
    return PlanarTfmView(
        view_id=identifier,
        transmit_material_mode=tx,
        receive_material_mode=rx,
        transmit_backwall_reflection=tb,
        receive_backwall_reflection=rb,
    )


def request(**updates):
    samples = updates.pop("samples", (0.0, 1.0, 0.0))
    raw = dict(
        acquisition_id="synthetic",
        physical_specimen_id="coupon",
        physical_scope_id="volume",
        source_group_id="authored-group",
        material_condition_id="isotropic",
        probe_id="probe",
        coordinate_frame_id="plane-frame",
        sample_clock_id="clock",
        time_zero_basis_id="t0",
        velocity_basis_id="material-L",
        raw_record_sha256="a" * 64,
        amplitude_unit="authored",
        propagation_model="planar_two_medium_transmission_and_same_mode_backwall",
        aggregation="coherent_sum",
        excitation_time_origin_s=0.0,
        longitudinal_velocity_m_s=4.0,
        time_s=(0.0, 35 / 6, 20.0),
        elements=(FmcElement(element_id="a", position_m=(-3.0, 0.0, -4.0)),),
        traces=(
            FmcTimeTrace(
                trace_id="aa",
                transmit_element_id="a",
                receive_element_id="a",
                signed_samples=samples,
                samples_sha256=canonical_digest(samples),
            ),
        ),
        image_points=(TfmImagePoint(point_id="target", position_m=(4.0, 0.0, 3.0)),),
        couplant_condition_id="couplant",
        couplant_velocity_basis_id="couplant-L",
        interface_geometry_basis_id="plane-z-zero",
        interface_z_m=0.0,
        couplant_longitudinal_velocity_m_s=3.0,
        views=(view(),),
    )
    raw.update(updates)
    digest = canonical_digest(
        PlanarMultiviewFmcTfm.model_construct(**raw).model_dump(mode="json", exclude={"basis"})
    )
    return PlanarMultiviewFmcTfm(
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
                    citation="Authored two-medium paths.",
                    license_id="authored-test",
                    sha256=digest,
                ),
            ),
        ),
    )


def normal(**updates):
    raw = dict(
        elements=(FmcElement(element_id="a", position_m=(0.0, 0.0, -3.0)),),
        image_points=(TfmImagePoint(point_id="target", position_m=(0.0, 0.0, 2.0)),),
        couplant_longitudinal_velocity_m_s=1.0,
        longitudinal_velocity_m_s=2.0,
    )
    raw.update(updates)
    return request(**raw)


def image_amplitudes(result):
    return [row["image"][0]["coherent_amplitude"] for row in result.values["views"]]


def test_known_refracted_three_four_five_path_satisfies_snell():
    ray = _plane_transmitted_ray(
        (-3.0, 0.0, -4.0),
        (4.0, 0.0, 3.0),
        interface_z=0.0,
        couplant_speed=3.0,
        material_speed=4.0,
        reflected_backwall_z=None,
        fraction_tolerance=1e-12,
        residual_tolerance=1e-10,
        maximum_iterations=80,
    )
    assert ray["interface_position_m"] == pytest.approx((0.0, 0.0, 0.0), abs=1e-10)
    assert ray["travel_time_s"] == pytest.approx(35 / 12, rel=1e-12)
    assert abs(ray["normalized_snell_residual"]) < 1e-10


def test_normal_incidence_has_analytic_time_without_iterations():
    result = planar_multiview_fmc_tfm(
        normal(
            image_points=(TfmImagePoint(point_id="target", position_m=(0.0, 0.0, 4.0)),),
            time_s=(0.0, 10.0, 20.0),
        )
    )
    assert result.status == "computed"
    assert image_amplitudes(result) == [1.0]
    assert result.values["ray_summaries"][0]["maximum_iterations_used"] == 0


def test_equal_wave_speeds_reduce_to_straight_line_time():
    delay = 7 * math.sqrt(2) / 2
    result = planar_multiview_fmc_tfm(
        request(couplant_longitudinal_velocity_m_s=4.0, time_s=(0.0, delay, 20.0))
    )
    assert image_amplitudes(result) == pytest.approx([1.0], abs=1e-10)


def test_backwall_image_paths_have_independent_tx_rx_delays():
    result = planar_multiview_fmc_tfm(
        normal(
            backwall_z_m=5.0,
            time_s=(0.0, 30.0, 60.0),
            samples=(0.0, 30.0, 60.0),
            views=(view("DD"), view("DR", rb=True), view("RD", tb=True), view("RR", tb=True, rb=True)),
        )
    )
    assert image_amplitudes(result) == [8.0, 11.0, 11.0, 14.0]


def test_material_longitudinal_shear_views_use_declared_speeds():
    result = planar_multiview_fmc_tfm(
        normal(
            material_shear_velocity_m_s=1.0,
            material_shear_velocity_basis_id="S",
            time_s=(0.0, 30.0, 60.0),
            samples=(0.0, 30.0, 60.0),
            views=(
                view("LL"),
                view("LS", rx="shear"),
                view("SL", tx="shear"),
                view("SS", tx="shear", rx="shear"),
            ),
        )
    )
    assert image_amplitudes(result) == [8.0, 9.0, 9.0, 10.0]


def test_unsupported_view_withholds_all_previously_computed_views():
    result = planar_multiview_fmc_tfm(
        normal(backwall_z_m=5.0, time_s=(0.0, 6.0, 12.0), views=(view("DD"), view("RR", tb=True, rb=True)))
    )
    assert result.status == "out_of_scope"
    assert result.values["unsupported_view_id"] == "RR"
    assert "views" not in result.values


def test_global_view_budget_is_not_a_per_view_budget():
    result = planar_multiview_fmc_tfm(normal(maximum_point_trace_evaluations=1, views=(view("a"), view("b"))))
    assert result.status == "out_of_scope"


@pytest.mark.parametrize(
    "updates",
    [
        dict(elements=(FmcElement(element_id="a", position_m=(0.0, 0.0, 0.0)),)),
        dict(image_points=(TfmImagePoint(point_id="target", position_m=(0.0, 0.0, 0.0)),)),
        dict(backwall_z_m=2.0),
    ],
)
def test_unsupported_half_space_and_backwall_geometry(updates):
    with pytest.raises(ValueError):
        request(**updates)


def test_shear_mode_without_shear_basis_is_rejected():
    with pytest.raises(ValueError, match="shear views"):
        request(views=(view("S", tx="shear"),))


def test_duplicate_view_identity_is_rejected():
    with pytest.raises(ValueError, match="view IDs"):
        request(views=(view(), view()))


def test_iteration_exhaustion_does_not_use_an_unconverged_ray():
    result = planar_multiview_fmc_tfm(request(maximum_ray_iterations=1, ray_fraction_tolerance=1e-15))
    assert result.status == "out_of_scope"
    assert "views" not in result.values


def test_unrepresentable_ray_geometry_is_withheld():
    result = planar_multiview_fmc_tfm(
        request(
            elements=(FmcElement(element_id="a", position_m=(-1.7e308, 0.0, -4.0)),),
            image_points=(TfmImagePoint(point_id="target", position_m=(1.7e308, 0.0, 3.0)),),
        )
    )
    assert result.status == "out_of_scope"


def test_homogeneous_evaluator_rejects_a_different_propagation_contract():
    assert homogeneous_fmc_tfm(request()).status == "out_of_scope"


def test_public_python_json_exchange():
    x = request()
    registry = default_registry()
    context = RunContext(asset_id="authored", location_id="coupon", time_basis="clock")
    a = registry.run("inspection.planar_multiview_fmc_tfm", x, context)
    b = registry.run_json("inspection.planar_multiview_fmc_tfm", x.model_dump_json(), context)
    assert a.status == b.status == "computed"
    assert a.model_dump() == b.model_dump()
