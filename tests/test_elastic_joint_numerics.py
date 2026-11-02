import json

import pytest

from matintegrity.assembly_calculations import ElasticJointLoad, elastic_joint_load
from matintegrity.contracts import RunContext
from matintegrity.registry import default_registry


def payload(scale=1.0, **updates):
    return ElasticJointLoad(
        initial_bolt_force_N=1000.0,
        bolt_stiffness_N_m=scale,
        clamped_stiffness_N_m=3 * scale,
        external_separating_force_N=400.0,
        free_clamped_minus_bolt_expansion_m=1 / scale,
        linear_contact_applicability_reviewed=True,
        **updates,
    )


@pytest.mark.parametrize("scale", [1e-200, 1.0, 1e200])
def test_series_stiffness_avoids_intermediate_product_overflow_and_underflow(scale):
    result = elastic_joint_load(payload(scale))
    assert result["status"] == "computed"
    assert result["thermal_preload_change_N"] == pytest.approx(0.75)
    assert result["bolt_force_N"] == pytest.approx(1100.75)
    assert result["clamp_force_N"] == pytest.approx(700.75)
    assert result["bolt_force_N"] - result["clamp_force_N"] == pytest.approx(400.0)
    json.dumps(result, allow_nan=False)


def test_stiffness_sum_need_not_be_representable_when_response_is_finite():
    value = payload().model_copy(
        update={
            "bolt_stiffness_N_m": 1e308,
            "clamped_stiffness_N_m": 1e308,
            "free_clamped_minus_bolt_expansion_m": 1e-307,
        }
    )
    result = elastic_joint_load(value)
    assert result["status"] == "computed"
    assert result["thermal_preload_change_N"] == pytest.approx(5.0)
    assert result["bolt_force_N"] == pytest.approx(1205.0)


def test_contact_loss_review_and_true_numeric_range_are_explicit():
    value = payload()
    assert (
        elastic_joint_load(value.model_copy(update={"linear_contact_applicability_reviewed": False}))[
            "status"
        ]
        == "needs_data"
    )
    assert (
        elastic_joint_load(value.model_copy(update={"external_separating_force_N": 4000.0}))["status"]
        == "out_of_scope"
    )
    result = elastic_joint_load(
        value.model_copy(
            update={
                "bolt_stiffness_N_m": 1e308,
                "clamped_stiffness_N_m": 1e308,
                "free_clamped_minus_bolt_expansion_m": 1e308,
            }
        )
    )
    assert result["status"] == "out_of_scope"
    json.dumps(result, allow_nan=False)


def test_default_registry_python_json():
    registry = default_registry()
    value = payload(1e200)
    context = RunContext(asset_id="asset", location_id="joint", time_basis="synthetic")
    direct = registry.run("fabrication.elastic_joint_load", value, context)
    assert direct.status == "computed"
    assert direct.model_version == "1.0.1"
    assert (
        direct.model_dump()
        == registry.run_json("fabrication.elastic_joint_load", value.model_dump_json(), context).model_dump()
    )
