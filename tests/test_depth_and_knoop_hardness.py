import pytest
from pydantic import ValidationError

from matintegrity.models.testmethods import KnoopIndent, RockwellDepth, knoop_indent, rockwell_depth


def depth(**changes):
    return RockwellDepth(
        **(
            dict(
                initial_depth_m=0.001,
                final_depth_m=0.00108,
                scale_id="HRC",
                scale_offset=100.0,
                depth_per_scale_unit_m=2e-6,
                scale_definition_basis="Synthetic NIST depth-scale example",
                applicability_reviewed=True,
            )
            | changes
        )
    )


def indent(**changes):
    return KnoopIndent(
        **(
            dict(
                test_force_N=9.80665,
                long_diagonal_m=0.001,
                longitudinal_edge_angle_deg=172.5,
                transverse_edge_angle_deg=130.0,
                indenter_geometry_basis="Declared ideal geometry",
            )
            | changes
        )
    )


def test_depth_number_and_datum_translation():
    result = rockwell_depth(depth())
    assert result.values["hardness_number"] == pytest.approx(60.0)
    shifted = rockwell_depth(depth(initial_depth_m=0.101, final_depth_m=0.10108))
    assert shifted.values["hardness_number"] == pytest.approx(result.values["hardness_number"])


def test_depth_missing_review_and_reversed_reading():
    assert rockwell_depth(depth(applicability_reviewed=False)).status == "needs_data"
    result = rockwell_depth(depth(final_depth_m=0.0009))
    assert result.status == "out_of_scope"
    assert result.values["permanent_depth_increment_m"] < 0


def test_knoop_geometry_and_force_area_scaling():
    result = knoop_indent(indent())
    # Independently published rounded ideal-geometry coefficient; not a material datum.
    assert result.values["conventional_HK"] == pytest.approx(14.229, rel=1e-4)
    assert result.values["projected_area_m2"] == pytest.approx(
        0.5 * 0.001 * result.values["ideal_short_diagonal_m"]
    )
    scaled = knoop_indent(indent(test_force_N=4 * 9.80665, long_diagonal_m=0.002))
    assert scaled.values["indentation_hardness_Pa"] == pytest.approx(result.values["indentation_hardness_Pa"])


@pytest.mark.parametrize(
    "changes",
    [
        dict(transverse_edge_angle_deg=175.0),
        dict(long_diagonal_m=0.0),
        dict(longitudinal_edge_angle_deg=180.0),
    ],
)
def test_knoop_invalid_geometry(changes):
    with pytest.raises(ValidationError):
        indent(**changes)


@pytest.mark.parametrize(
    "model_id,inputs", [("testing.rockwell_depth", depth()), ("testing.knoop", indent())]
)
def test_registered_python_json_exchange(model_id, inputs):
    from matintegrity.contracts import RunContext
    from matintegrity.registry import default_registry

    registry = default_registry()
    context = RunContext(asset_id="synthetic", location_id="indent-1", time_basis="test")
    python_result = registry.run(model_id, inputs, context)
    json_result = registry.run_json(model_id, inputs.model_dump_json(), context)
    assert python_result.status == json_result.status == "computed"
    assert python_result.values == json_result.values
    assert python_result.units == json_result.units
    assert python_result.input_digest == json_result.input_digest
    assert python_result.context == json_result.context == context
